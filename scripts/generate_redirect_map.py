"""Redirect map generator: candidate old->new URL mapping for migrations.

Takes a list of OLD URLs (pre-migration crawl or GSC export) and a list
of NEW URLs (staging crawl, new-site crawl, or sitemap) and proposes a
redirect map through staged matching:

  Stage 1  same-path      old path exists in the new set. Same host too
                          means no redirect is needed (OK_UNCHANGED);
                          different host is a high-confidence match.
  Stage 2  slug           last path segment matches exactly ONE new URL.
  Stage 3  structural     token-set + sequence similarity on the path.
                          Auto-assigns only when the best score clears
                          the threshold AND beats the runner-up by a
                          margin; otherwise falls through.
  Stage 4  semantic       optional, needs OPENROUTER_API_KEY. Embeds the
                          humanized paths (reusing the semantic_site_map
                          embedder + its parquet cache) and matches on
                          cosine similarity.

Anything that survives all four stages is STRANDED: the row ships with
an empty target and the closest candidate for a human to judge. There
is deliberately NO homepage fallback — bulk redirects to the homepage
are treated as soft 404s by Google, and an unmapped URL is a decision
(map it properly or 410 it), not a default.

THE OUTPUT IS A CANDIDATE MAP, NOT A DELIVERABLE. Every proposed target
must pass Rule 12 verification (scripts/verify_urls.py or the
live-url-verifier subagent) before it ships, and the implemented map is
checked afterwards with /validate-redirects.

Usage:
    python scripts/generate_redirect_map.py \
        --old old_urls.csv --new new_crawl.csv
    python scripts/generate_redirect_map.py --old gsc_pages.csv \
        --new-sitemap https://staging.example.com/sitemap.xml

Outputs (to --output-dir, default: the --old file's folder):
    redirect_map_candidates_<YYYY-MM-DD>.csv
    redirect_map_candidates_<YYYY-MM-DD>.json   (summary + settings)
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verify_urls import UA  # noqa: E402

URL_COL_CANDIDATES = [
    "address", "url", "page", "landing page", "current url", "source",
    "top pages", "page url",
]
STRIP_EXTENSIONS = (".html", ".htm", ".php", ".asp", ".aspx")
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
MAX_CHILD_SITEMAPS = 50

CONFIDENCE = {"same-path": "high", "slug": "high",
              "structural": "medium", "semantic": "low"}
REVIEW = {"same-path": "NO", "slug": "SPOT-CHECK",
          "structural": "YES", "semantic": "YES"}


@dataclass
class Candidate:
    source: str
    status: str            # OK_UNCHANGED | MATCHED | STRANDED
    target: str = ""
    method: str = ""       # same-path | slug | structural | semantic
    confidence: str = ""
    review: str = ""
    score: Optional[float] = None            # the winning match's score
    closest_alternative: str = ""            # STRANDED rows only
    alternative_score: Optional[float] = None


# --------------------------------------------------------------- URL handling

def path_key(url: str) -> str:
    """Comparison key for a URL's path: lowercase, no trailing slash,
    common file extensions stripped, query and fragment dropped."""
    path = urlsplit(url.strip()).path.lower().rstrip("/")
    for ext in STRIP_EXTENSIONS:
        if path.endswith(ext):
            path = path[: -len(ext)]
            break
    return path or "/"


def slug_of(url: str) -> str:
    """Last non-empty path segment of the comparison key."""
    key = path_key(url)
    return key.rsplit("/", 1)[-1] if key != "/" else ""


def tokens_of(url: str) -> frozenset[str]:
    """Word tokens across all path segments. A trailing 's' is stripped
    so /services/ and /service/ token-match (singular/plural is the most
    common slug drift in a restructure)."""
    raw = (t for t in re.split(r"[^a-z0-9]+", path_key(url)) if t)
    return frozenset(
        t[:-1] if t.endswith("s") and len(t) > 3 else t for t in raw
    )


def humanize(url: str) -> str:
    """Path rendered as words for embedding: '/services/water-heater/'
    becomes 'services / water heater'."""
    segments = [s for s in path_key(url).split("/") if s]
    return " / ".join(
        " ".join(t for t in re.split(r"[^a-z0-9]+", s) if t)
        for s in segments
    ) or "homepage"


def structural_score(old_url: str, new_url: str) -> float:
    """0..1 similarity of two URL paths: half token-set overlap, half
    character-sequence similarity."""
    tok_old, tok_new = tokens_of(old_url), tokens_of(new_url)
    if tok_old or tok_new:
        jaccard = len(tok_old & tok_new) / len(tok_old | tok_new)
    else:
        jaccard = 0.0
    seq = SequenceMatcher(
        None, path_key(old_url), path_key(new_url)
    ).ratio()
    return 0.5 * jaccard + 0.5 * seq


def best_with_margin(
    scores: list[float], threshold: float, margin: float
) -> Optional[tuple[int, float, float]]:
    """Index/score of the best candidate, plus the runner-up score,
    when the best clears the threshold AND the margin over the
    runner-up. None means no confident winner."""
    if not scores:
        return None
    order = sorted(range(len(scores)), key=lambda i: scores[i],
                   reverse=True)
    best_i = order[0]
    runner = scores[order[1]] if len(order) > 1 else 0.0
    if scores[best_i] >= threshold and scores[best_i] - runner >= margin:
        return best_i, scores[best_i], runner
    return None


# --------------------------------------------------------------- input loading

def detect_url_column(headers: list[str]) -> Optional[str]:
    lowered = {h.strip().lower(): h for h in headers}
    return next(
        (lowered[c] for c in URL_COL_CANDIDATES if c in lowered), None
    )


def load_url_list(path: Path, base_url: Optional[str]) -> list[str]:
    """URLs from a .txt (one per line) or .csv (auto-detected column).
    Deduplicates by path key, preserving first-seen order."""
    urls: list[str] = []
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            col = detect_url_column(reader.fieldnames or [])
            if not col:
                raise SystemExit(
                    f"ERROR: no URL column found in {path.name} headers "
                    f"{reader.fieldnames}. Expected one of "
                    f"{URL_COL_CANDIDATES}."
                )
            urls = [
                (row.get(col) or "").strip()
                for row in reader if (row.get(col) or "").strip()
            ]
    else:
        urls = [
            line.strip() for line in
            path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    resolved, seen = [], set()
    for u in urls:
        if not u.startswith(("http://", "https://")):
            if not base_url:
                raise SystemExit(
                    f"ERROR: relative URL {u!r} in {path.name} but no "
                    "--base-url given"
                )
            u = urljoin(base_url.rstrip("/") + "/", u.lstrip("/"))
        key = path_key(u)
        if key not in seen:
            seen.add(key)
            resolved.append(u)
    return resolved


def fetch_sitemap_urls(sitemap_url: str, timeout: int = 30) -> list[str]:
    """URLs from a sitemap.xml, following one level of sitemap index."""
    def fetch(url: str) -> ElementTree.Element:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        r.raise_for_status()
        return ElementTree.fromstring(r.content)

    root = fetch(sitemap_url)
    urls: list[str] = []
    if root.tag == f"{SITEMAP_NS}sitemapindex":
        children = [
            loc.text.strip()
            for loc in root.iter(f"{SITEMAP_NS}loc") if loc.text
        ][:MAX_CHILD_SITEMAPS]
        for child in children:
            urls.extend(
                loc.text.strip()
                for loc in fetch(child).iter(f"{SITEMAP_NS}loc")
                if loc.text
            )
    else:
        urls = [
            loc.text.strip()
            for loc in root.iter(f"{SITEMAP_NS}loc") if loc.text
        ]
    return urls


# ------------------------------------------------------------------- matching

def match_urls(
    old_urls: list[str],
    new_urls: list[str],
    structural_threshold: float,
    structural_margin: float,
    semantic_threshold: float,
    semantic_margin: float,
    embed_fn: Optional[Callable[[list[str]], "object"]] = None,
) -> list[Candidate]:
    """Run the four matching stages. embed_fn(texts) -> row-wise
    embedding matrix; pass None to skip the semantic stage."""
    new_by_path: dict[str, str] = {}
    slug_counts: dict[str, list[str]] = {}
    for nu in new_urls:
        new_by_path.setdefault(path_key(nu), nu)
        slug = slug_of(nu)
        if slug:
            slug_counts.setdefault(slug, []).append(nu)

    results: list[Candidate] = []
    unresolved: list[str] = []

    for ou in old_urls:
        key = path_key(ou)
        if key in new_by_path:
            nu = new_by_path[key]
            if urlsplit(ou).netloc.lower() == urlsplit(nu).netloc.lower():
                results.append(Candidate(
                    source=ou, status="OK_UNCHANGED", target=nu,
                    method="same-path", confidence="high", review="NO",
                ))
            else:
                results.append(Candidate(
                    source=ou, status="MATCHED", target=nu,
                    method="same-path",
                    confidence=CONFIDENCE["same-path"],
                    review=REVIEW["same-path"],
                ))
            continue
        slug = slug_of(ou)
        if slug and len(slug_counts.get(slug, [])) == 1:
            results.append(Candidate(
                source=ou, status="MATCHED",
                target=slug_counts[slug][0], method="slug",
                confidence=CONFIDENCE["slug"], review=REVIEW["slug"],
            ))
            continue
        unresolved.append(ou)

    still_unresolved: list[str] = []
    structural_best: dict[str, tuple[str, float]] = {}
    for ou in unresolved:
        scores = [structural_score(ou, nu) for nu in new_urls]
        pick = best_with_margin(
            scores, structural_threshold, structural_margin
        )
        if pick:
            i, score, runner = pick
            results.append(Candidate(
                source=ou, status="MATCHED", target=new_urls[i],
                method="structural",
                confidence=CONFIDENCE["structural"],
                review=REVIEW["structural"],
                score=round(score, 3),
            ))
        else:
            if scores:
                top = max(range(len(scores)), key=lambda i: scores[i])
                structural_best[ou] = (
                    new_urls[top], round(scores[top], 3)
                )
            still_unresolved.append(ou)

    if still_unresolved and embed_fn is not None and new_urls:
        old_vecs = embed_fn([humanize(u) for u in still_unresolved])
        new_vecs = embed_fn([humanize(u) for u in new_urls])
        import numpy as np
        old_n = old_vecs / np.linalg.norm(
            old_vecs, axis=1, keepdims=True
        )
        new_n = new_vecs / np.linalg.norm(
            new_vecs, axis=1, keepdims=True
        )
        sims = old_n @ new_n.T
        remaining: list[str] = []
        for row_i, ou in enumerate(still_unresolved):
            pick = best_with_margin(
                list(sims[row_i]), semantic_threshold, semantic_margin
            )
            if pick:
                i, score, runner = pick
                results.append(Candidate(
                    source=ou, status="MATCHED", target=new_urls[i],
                    method="semantic",
                    confidence=CONFIDENCE["semantic"],
                    review=REVIEW["semantic"],
                    score=round(float(score), 3),
                ))
            else:
                top = int(np.argmax(sims[row_i]))
                best_struct = structural_best.get(ou)
                alt_url = new_urls[top]
                alt_score = round(float(sims[row_i][top]), 3)
                if best_struct and best_struct[1] > alt_score:
                    alt_url, alt_score = best_struct
                structural_best[ou] = (alt_url, alt_score)
                remaining.append(ou)
        still_unresolved = remaining

    for ou in still_unresolved:
        alt = structural_best.get(ou, ("", None))
        results.append(Candidate(
            source=ou, status="STRANDED", review="YES",
            closest_alternative=alt[0],
            alternative_score=alt[1],
        ))

    order = {u: i for i, u in enumerate(old_urls)}
    results.sort(key=lambda c: order[c.source])
    return results


# ------------------------------------------------------------------- outputs

def write_outputs(
    results: list[Candidate], out_dir: Path, settings: dict
) -> tuple[Path, Path]:
    import json

    stamp = date.today().isoformat()
    csv_path = out_dir / f"redirect_map_candidates_{stamp}.csv"
    json_path = out_dir / f"redirect_map_candidates_{stamp}.json"
    out_dir.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "Status", "Source URL", "Proposed Target", "Match Method",
            "Confidence", "Review", "Match Score",
            "Closest Alternative (stranded rows)",
        ])
        for c in results:
            alt = c.closest_alternative
            if alt and c.alternative_score is not None:
                alt = f"{alt} ({c.alternative_score})"
            w.writerow([
                c.status, c.source, c.target, c.method, c.confidence,
                c.review, "" if c.score is None else c.score, alt,
            ])

    counts = {
        s: sum(1 for c in results if c.status == s)
        for s in ("OK_UNCHANGED", "MATCHED", "STRANDED")
    }
    methods = {
        m: sum(1 for c in results if c.method == m)
        for m in ("same-path", "slug", "structural", "semantic")
    }
    summary = {
        "generated_on": date.today().isoformat(),
        "note": (
            "CANDIDATE MAP ONLY. Every proposed target must pass "
            "Rule 12 verification (verify_urls.py / live-url-verifier) "
            "before the map ships. STRANDED rows need a human decision "
            "(map properly or 410); never redirect them to the homepage."
        ),
        "counts": counts,
        "match_methods": methods,
        "settings": settings,
        "results_csv": str(csv_path),
    }
    json_path.write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return csv_path, json_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0]
    )
    parser.add_argument("--old", type=Path, required=True,
                        help="Old URL list (.csv or .txt)")
    parser.add_argument("--new", type=Path,
                        help="New URL list (.csv or .txt)")
    parser.add_argument("--new-sitemap",
                        help="Fetch new URLs from this sitemap.xml "
                             "instead of --new")
    parser.add_argument("--base-url",
                        help="Base URL for resolving relative paths")
    parser.add_argument("--output-dir", type=Path,
                        help="Output folder (default: the --old "
                             "file's folder)")
    parser.add_argument("--structural-threshold", type=float,
                        default=0.75)
    parser.add_argument("--structural-margin", type=float, default=0.10)
    parser.add_argument("--semantic-threshold", type=float, default=0.80)
    parser.add_argument("--semantic-margin", type=float, default=0.02)
    parser.add_argument("--no-semantic", action="store_true",
                        help="Skip the embedding stage even if an "
                             "OpenRouter key is configured")
    args = parser.parse_args()

    if not args.new and not args.new_sitemap:
        raise SystemExit("ERROR: provide --new or --new-sitemap")

    old_urls = load_url_list(args.old, args.base_url)
    if args.new:
        new_urls = load_url_list(args.new, args.base_url)
    else:
        print(f"Fetching sitemap: {args.new_sitemap}", file=sys.stderr)
        new_urls = fetch_sitemap_urls(args.new_sitemap)
    if not old_urls or not new_urls:
        raise SystemExit("ERROR: old or new URL list is empty")
    print(f"{len(old_urls)} old URLs, {len(new_urls)} new URLs",
          file=sys.stderr)

    embed_fn = None
    semantic_active = False
    if not args.no_semantic:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if api_key:
            import pandas as pd

            from Skills.semantic_site_map.embedder import embed_pages
            cache_dir = (
                args.output_dir or args.old.parent
            ) / "_cache_redirect_map"

            def _embed(texts: list[str]):
                df = pd.DataFrame({"url": texts, "text": texts})
                return embed_pages(df, cache_dir, api_key)

            embed_fn = _embed
            semantic_active = True
        else:
            print(
                "WARNING: OPENROUTER_API_KEY not set; skipping the "
                "semantic stage. Unmatched URLs after the structural "
                "stage will be STRANDED.",
                file=sys.stderr,
            )

    results = match_urls(
        old_urls, new_urls,
        structural_threshold=args.structural_threshold,
        structural_margin=args.structural_margin,
        semantic_threshold=args.semantic_threshold,
        semantic_margin=args.semantic_margin,
        embed_fn=embed_fn,
    )

    settings = {
        "structural_threshold": args.structural_threshold,
        "structural_margin": args.structural_margin,
        "semantic_threshold": args.semantic_threshold,
        "semantic_margin": args.semantic_margin,
        "semantic_stage_active": semantic_active,
        "old_input": str(args.old),
        "new_input": str(args.new or args.new_sitemap),
    }
    out_dir = args.output_dir or args.old.parent
    csv_path, json_path = write_outputs(results, out_dir, settings)

    counts = {
        s: sum(1 for c in results if c.status == s)
        for s in ("OK_UNCHANGED", "MATCHED", "STRANDED")
    }
    print(f"Saved: {csv_path}", file=sys.stderr)
    print(f"Saved: {json_path}", file=sys.stderr)
    print(
        f"Summary: {counts['MATCHED']} matched / "
        f"{counts['OK_UNCHANGED']} unchanged / "
        f"{counts['STRANDED']} stranded",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
