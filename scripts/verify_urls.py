"""Live URL verifier.

Given a list of URLs (typically proposed redirect targets, canonical
targets, or "link to X instead of Y" recommendations), verify each
against the live site and return a structured PASS/FAIL report.

Catches the kind of upstream errors that bit us on Superior's Nov 24
GSC redirect corrections — wrong target URL becomes a 301-cemented
mistake the moment the developer implements it.

Usage:
    python scripts/verify_urls.py --input urls.txt --output report.json
    python scripts/verify_urls.py --urls https://example.com/a/ https://example.com/b/

Input file format (urls.txt): one URL per line, optional comment after a tab:
    https://example.com/a/    proposed canonical target for finding 7
    https://example.com/b/    redirect target for /old-slug/

Output JSON contains, per URL:
  - status_code (final, after redirects)
  - final_url (after redirect chain)
  - redirect_chain (list of intermediate URLs)
  - indexable (true if 200 + meta robots is index/follow)
  - meta_robots
  - canonical
  - title
  - verdict: PASS / WARN / FAIL with reason
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


@dataclass
class UrlReport:
    url: str
    note: str = ""
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    redirect_chain: list[str] = field(default_factory=list)
    redirect_count: int = 0
    title: Optional[str] = None
    meta_robots: Optional[str] = None
    canonical: Optional[str] = None
    indexable: Optional[bool] = None
    verdict: str = "UNKNOWN"
    reason: str = ""


def extract_meta(html: str) -> dict:
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    title = title_m.group(1).strip() if title_m else None

    robots_m = re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    robots = robots_m.group(1).strip() if robots_m else None

    canon_m = re.search(
        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    canonical = canon_m.group(1).strip() if canon_m else None

    return {"title": title, "meta_robots": robots, "canonical": canonical}


def is_indexable(status_code: int, meta_robots: Optional[str]) -> bool:
    if status_code != 200:
        return False
    if meta_robots is None:
        return True  # default = indexable
    r = meta_robots.lower()
    if "noindex" in r:
        return False
    return True


def verdict_for(report: UrlReport) -> tuple[str, str]:
    if report.status_code is None:
        return "FAIL", "Could not fetch URL (network error or blocked)"
    if report.status_code == 404:
        return "FAIL", "Returns 404 — URL does not exist on live site"
    if report.status_code == 410:
        return "FAIL", "Returns 410 Gone — URL was permanently removed"
    if 500 <= report.status_code < 600:
        return "FAIL", f"Returns {report.status_code} server error"
    if report.status_code in (301, 302, 307, 308):
        return "WARN", f"Returns {report.status_code} redirect — propose the final destination ({report.final_url}) as the target instead"
    if report.redirect_count > 0:
        return "WARN", f"Reached final URL via {report.redirect_count} redirect(s) — confirm the final URL ({report.final_url}) is the intended target, not the input URL"
    if report.indexable is False:
        return "WARN", f"Returns 200 but is NOT indexable (meta robots: {report.meta_robots}) — using as a canonical/redirect target may waste link equity"
    if report.status_code == 200 and report.indexable:
        return "PASS", "200 OK, indexable, no redirect chain"
    return "WARN", f"Status {report.status_code} — manual review recommended"


def verify_url(url: str, note: str = "", timeout: int = 15) -> UrlReport:
    report = UrlReport(url=url, note=note)
    try:
        r = requests.get(
            url,
            headers={"User-Agent": UA},
            timeout=timeout,
            allow_redirects=True,
        )
        report.status_code = r.status_code
        report.final_url = r.url
        report.redirect_chain = [resp.url for resp in r.history]
        report.redirect_count = len(r.history)

        meta = extract_meta(r.text)
        report.title = meta["title"]
        report.meta_robots = meta["meta_robots"]
        report.canonical = meta["canonical"]
        report.indexable = is_indexable(r.status_code, meta["meta_robots"])

    except requests.exceptions.Timeout:
        report.reason = "Request timed out"
    except requests.exceptions.ConnectionError as e:
        report.reason = f"Connection error: {str(e)[:120]}"
    except Exception as e:
        report.reason = f"Error: {str(e)[:120]}"

    if not report.reason:
        report.verdict, report.reason = verdict_for(report)
    else:
        report.verdict = "FAIL"

    return report


def parse_input_file(path: Path) -> list[tuple[str, str]]:
    """One URL per line. Optional tab-separated note. Skip blank lines and comments."""
    urls: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            url, note = line.split("\t", 1)
            urls.append((url.strip(), note.strip()))
        else:
            urls.append((line, ""))
    return urls


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="Path to file with one URL per line")
    parser.add_argument("--urls", nargs="+", help="URLs to verify (alternative to --input)")
    parser.add_argument("--output", type=Path, help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    pairs: list[tuple[str, str]] = []
    if args.input:
        pairs.extend(parse_input_file(args.input))
    if args.urls:
        pairs.extend([(u, "") for u in args.urls])

    if not pairs:
        print("ERROR: provide --input or --urls", file=sys.stderr)
        sys.exit(1)

    print(f"Verifying {len(pairs)} URL(s)...", file=sys.stderr)
    reports = [verify_url(u, note) for u, note in pairs]

    pass_count = sum(1 for r in reports if r.verdict == "PASS")
    warn_count = sum(1 for r in reports if r.verdict == "WARN")
    fail_count = sum(1 for r in reports if r.verdict == "FAIL")

    output = {
        "verified_at": datetime.utcnow().isoformat() + "Z",
        "total": len(reports),
        "pass": pass_count,
        "warn": warn_count,
        "fail": fail_count,
        "results": [asdict(r) for r in reports],
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(f"Saved: {args.output}", file=sys.stderr)
        print(f"Summary: {pass_count} PASS / {warn_count} WARN / {fail_count} FAIL", file=sys.stderr)
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
