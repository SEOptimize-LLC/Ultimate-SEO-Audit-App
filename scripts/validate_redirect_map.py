"""Redirect map validator: post-implementation check.

Given a CSV mapping of source URLs to their intended redirect targets,
fire a live request at every source, follow the chain, and report
PASS/WARN/FAIL per row on whether the shipped redirect actually lands
where the deliverable said it should.

This is the closing-the-loop counterpart to verify_urls.py:
  - verify_urls.py runs BEFORE the deliverable ships (Rule 12: is the
    proposed target a live, indexable 200?)
  - validate_redirect_map.py runs AFTER the developer implements the
    map (did every source actually get redirected to that target?)

Accepted input layouts (columns auto-detected, case-insensitive):
  - Generic:    "Current URL" / "Target URL", "Source URL" / "Destination",
                "Old URL" / "New URL", "Redirect From" / "Redirect To", etc.
  - Rank Math:  "source" / "destination" export/import CSVs. Rows whose
    destination is DELETE, whose matching is not "exact", or whose status
    is "inactive" are skipped and counted, not validated.
  - Relative paths resolve against --base-url.

Normalization (trailing slash and http->https are usually the first
source of redirects, so both are lenient by default):
  - A final URL that differs from the expected target only by trailing
    slash or scheme counts as a MATCH. Disable with --strict-slash /
    --strict-scheme.
  - A chain hop that only normalizes scheme, trailing slash, or www is
    a "trivial hop" and does not trigger the multi-hop warning; the
    http->https hop is site-wide infrastructure, not a mapping error.

Usage:
    python scripts/validate_redirect_map.py --input map.csv \
        --output report.json
    python scripts/validate_redirect_map.py --input rankmath.csv \
        --base-url https://example.com --csv report.csv --workers 10

Output JSON mirrors verify_urls.py: summary counts + per-row results
(verdict, reason, match_type, hop statuses, final URL, indexability).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests

from verify_urls import UA, extract_meta, is_indexable

PERMANENT_STATUSES = (301, 308)
REDIRECT_STATUSES = (301, 302, 303, 307, 308)

SOURCE_COL_CANDIDATES = [
    "current url",
    "source url",
    "source",
    "old url",
    "redirect from",
    "from url",
    "from",
]
TARGET_COL_CANDIDATES = [
    "target url (redirect to this url)",
    "target url",
    "destination",
    "target",
    "new url",
    "new target",
    "proposed new target",
    "redirect to",
    "should point to",
    "to url",
    "to",
]


@dataclass
class RowResult:
    source: str
    expected: str
    status_code: Optional[int] = None
    first_hop_status: Optional[int] = None
    final_url: Optional[str] = None
    redirect_chain: list[str] = field(default_factory=list)
    hop_statuses: list[int] = field(default_factory=list)
    hop_count: int = 0
    substantive_hops: int = 0
    match_type: str = ""
    meta_robots: Optional[str] = None
    indexable: Optional[bool] = None
    verdict: str = "UNKNOWN"
    reason: str = ""


# --------------------------------------------------------------- normalization

def _normalize(url: str, ignore_slash: bool, ignore_scheme: bool,
               ignore_www: bool = False) -> str:
    """Canonical comparison form of a URL. Host is always lowercased and
    the fragment always dropped; slash/scheme/www only when requested."""
    parts = urlsplit(url.strip())
    scheme = "https" if ignore_scheme else parts.scheme.lower()
    host = parts.netloc.lower()
    if ignore_www and host.startswith("www."):
        host = host[4:]
    path = parts.path
    if ignore_slash and path.endswith("/"):
        path = path.rstrip("/")
    if path == "":
        path = "/" if not ignore_slash else ""
    return urlunsplit((scheme, host, path, parts.query, ""))


def classify_match(final_url: str, expected: str,
                   strict_slash: bool, strict_scheme: bool) -> str:
    """How does the final URL relate to the expected target?

    Returns: exact | slash | scheme | slash+scheme | mismatch.
    Normalized forms only count as a match when the toggle allows it.
    """
    if _normalize(final_url, False, False) == _normalize(
        expected, False, False
    ):
        return "exact"
    slash_ok = not strict_slash and (
        _normalize(final_url, True, False) == _normalize(expected, True, False)
    )
    scheme_ok = not strict_scheme and (
        _normalize(final_url, False, True) == _normalize(expected, False, True)
    )
    if slash_ok:
        return "slash"
    if scheme_ok:
        return "scheme"
    if not strict_slash and not strict_scheme and (
        _normalize(final_url, True, True) == _normalize(expected, True, True)
    ):
        return "slash+scheme"
    return "mismatch"


def is_trivial_hop(from_url: str, to_url: str) -> bool:
    """True when a hop only normalizes scheme, trailing slash, or www:
    the site-wide canonicalization redirects every request passes through."""
    return _normalize(from_url, True, True, ignore_www=True) == _normalize(
        to_url, True, True, ignore_www=True
    )


# -------------------------------------------------------------------- verdicts

def verdict_for_row(r: RowResult) -> tuple[str, str]:
    if r.status_code is None:
        return "FAIL", r.reason or "Could not fetch source URL"

    if r.hop_count == 0:
        if r.match_type != "mismatch" and r.status_code == 200:
            return "WARN", (
                "Source already resolves as the target (200, no redirect), "
                "so the row is self-referential and unnecessary"
            )
        if r.status_code == 200:
            return "FAIL", (
                "No redirect fired: source still returns 200 as itself "
                "instead of redirecting to the expected target"
            )
        return "FAIL", f"Source returns {r.status_code} with no redirect"

    if r.match_type == "mismatch":
        return "FAIL", (
            f"Redirects to {r.final_url} instead of the expected target "
            f"{r.expected}"
        )

    if r.status_code != 200:
        return "FAIL", (
            f"Redirects to the expected target but it returns "
            f"{r.status_code}, not 200"
        )

    issues: list[str] = []
    if r.first_hop_status not in PERMANENT_STATUSES:
        issues.append(
            f"first hop is {r.first_hop_status} (temporary), should be 301"
        )
    if r.substantive_hops > 1:
        issues.append(
            f"{r.hop_count}-hop chain with {r.substantive_hops} substantive "
            "hops; the source should redirect to the target in one step"
        )
    if r.indexable is False:
        issues.append(
            f"target is not indexable (meta robots: {r.meta_robots}), "
            "so redirecting here may waste link equity"
        )

    note = ""
    if r.match_type != "exact":
        pretty = {
            "slash": "trailing slash",
            "scheme": "http/https scheme",
            "slash+scheme": "trailing slash and scheme",
        }[r.match_type]
        note = f" (matched ignoring {pretty})"

    if issues:
        return "WARN", "; ".join(issues) + note
    return "PASS", "Redirects to the expected target" + note


# -------------------------------------------------------------------- fetching

def validate_row(source: str, expected: str, timeout: int,
                 strict_slash: bool, strict_scheme: bool) -> RowResult:
    r = RowResult(source=source, expected=expected)
    try:
        resp = requests.get(
            source,
            headers={"User-Agent": UA},
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.exceptions.Timeout:
        r.reason, r.verdict = "Request timed out", "FAIL"
        return r
    except requests.exceptions.RequestException as e:
        r.reason, r.verdict = f"Fetch error: {str(e)[:120]}", "FAIL"
        return r

    r.status_code = resp.status_code
    r.final_url = resp.url
    r.redirect_chain = [h.url for h in resp.history]
    r.hop_statuses = [h.status_code for h in resp.history]
    r.hop_count = len(resp.history)
    r.first_hop_status = resp.history[0].status_code if resp.history else None

    hops = [h.url for h in resp.history] + [resp.url]
    r.substantive_hops = sum(
        1 for a, b in zip(hops, hops[1:]) if not is_trivial_hop(a, b)
    )

    r.match_type = classify_match(
        resp.url, expected, strict_slash, strict_scheme
    )
    if resp.status_code == 200:
        meta = extract_meta(resp.text)
        r.meta_robots = meta["meta_robots"]
        r.indexable = is_indexable(resp.status_code, meta["meta_robots"])

    r.verdict, r.reason = verdict_for_row(r)
    return r


# --------------------------------------------------------------- input parsing

def detect_columns(headers: list[str]) -> tuple[Optional[str], Optional[str]]:
    lowered = {h.strip().lower(): h for h in headers}
    src = next(
        (lowered[c] for c in SOURCE_COL_CANDIDATES if c in lowered), None
    )
    tgt = next(
        (lowered[c] for c in TARGET_COL_CANDIDATES if c in lowered), None
    )
    return src, tgt


def resolve_url(value: str, base_url: Optional[str]) -> str:
    value = value.strip()
    if value.startswith(("http://", "https://")):
        return value
    if not base_url:
        raise ValueError(
            f"Relative URL {value!r} in map but no --base-url given"
        )
    return urljoin(base_url.rstrip("/") + "/", value.lstrip("/"))


def load_map(path: Path, source_col: Optional[str], target_col: Optional[str],
             base_url: Optional[str]) -> tuple[list[tuple[str, str]], dict]:
    """Returns (pairs, skip_stats). Dedupes by source URL (SF-style exports
    store relationships as rows, per Rule 10) and skips Rank Math rows that
    are not validatable single URLs."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if not source_col or not target_col:
            auto_src, auto_tgt = detect_columns(headers)
            source_col = source_col or auto_src
            target_col = target_col or auto_tgt
        if not source_col or not target_col:
            raise SystemExit(
                f"ERROR: could not detect source/target columns in {headers}. "
                "Pass --source-col and --target-col explicitly."
            )

        matching_col = next(
            (h for h in headers if h.strip().lower() == "matching"), None
        )
        status_col = next(
            (h for h in headers if h.strip().lower() == "status"), None
        )

        pairs: list[tuple[str, str]] = []
        seen: set[str] = set()
        skipped = {"delete_rows": 0, "non_exact_matching": 0,
                   "inactive": 0, "empty": 0, "duplicate_sources": 0}

        for row in reader:
            src_raw = (row.get(source_col) or "").strip()
            tgt_raw = (row.get(target_col) or "").strip()
            if not src_raw or not tgt_raw:
                skipped["empty"] += 1
                continue
            if tgt_raw == "DELETE":
                skipped["delete_rows"] += 1
                continue
            matching = (row.get(matching_col) or "").strip().lower() \
                if matching_col else ""
            if matching not in ("", "exact"):
                skipped["non_exact_matching"] += 1
                continue
            status = (row.get(status_col) or "").strip().lower() \
                if status_col else ""
            if status == "inactive":
                skipped["inactive"] += 1
                continue

            source = resolve_url(src_raw, base_url)
            target = resolve_url(tgt_raw, base_url)
            key = _normalize(source, False, False)
            if key in seen:
                skipped["duplicate_sources"] += 1
                continue
            seen.add(key)
            pairs.append((source, target))

    return pairs, skipped


# ------------------------------------------------------------------------ main

def write_csv(path: Path, results: list[RowResult]) -> None:
    # utf-8-sig so Excel opens the report without mangling non-ASCII.
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "Verdict", "Source URL", "Expected Target", "Final URL",
            "HTTP Chain", "Match Type", "Reason",
        ])
        for r in results:
            statuses = r.hop_statuses + (
                [r.status_code] if r.status_code else []
            )
            chain = " -> ".join(str(s) for s in statuses)
            w.writerow([
                r.verdict, r.source, r.expected, r.final_url or "",
                chain, r.match_type, r.reason,
            ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, required=True,
                        help="CSV redirect map (source -> expected target)")
    parser.add_argument("--source-col", help="Override source column name")
    parser.add_argument("--target-col", help="Override target column name")
    parser.add_argument("--base-url",
                        help="Base URL for resolving relative paths "
                             "(required for Rank Math exports)")
    parser.add_argument("--strict-slash", action="store_true",
                        help="Trailing-slash difference counts as a mismatch")
    parser.add_argument("--strict-scheme", action="store_true",
                        help="http/https difference counts as a mismatch")
    parser.add_argument("--workers", type=int, default=10,
                        help="Concurrent requests (default 10)")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--limit", type=int,
                        help="Validate only the first N rows (smoke test)")
    parser.add_argument("--output", type=Path,
                        help="JSON report path (default: stdout)")
    parser.add_argument("--csv", type=Path, dest="csv_out",
                        help="Also write a flat CSV report")
    args = parser.parse_args()

    pairs, skipped = load_map(
        args.input, args.source_col, args.target_col, args.base_url
    )
    if args.limit:
        pairs = pairs[: args.limit]
    if not pairs:
        raise SystemExit("ERROR: no validatable rows found in the input CSV")

    print(f"Validating {len(pairs)} redirect(s) "
          f"with {args.workers} workers...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(
            lambda p: validate_row(
                p[0], p[1], args.timeout,
                args.strict_slash, args.strict_scheme,
            ),
            pairs,
        ))

    counts = {v: sum(1 for r in results if r.verdict == v)
              for v in ("PASS", "WARN", "FAIL")}
    output = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "input": str(args.input),
        "total": len(results),
        "pass": counts["PASS"],
        "warn": counts["WARN"],
        "fail": counts["FAIL"],
        "skipped_rows": skipped,
        "normalization": {
            "trailing_slash_lenient": not args.strict_slash,
            "scheme_lenient": not args.strict_scheme,
        },
        "results": [asdict(r) for r in results],
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"Saved: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(output, indent=2))

    if args.csv_out:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        write_csv(args.csv_out, results)
        print(f"Saved: {args.csv_out}", file=sys.stderr)

    print(f"Summary: {counts['PASS']} PASS / {counts['WARN']} WARN / "
          f"{counts['FAIL']} FAIL", file=sys.stderr)
    if counts["FAIL"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
