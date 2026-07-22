"""
Live verification of the 113 NOT-INDEXED SameDay blog posts.

Mirrors the survivors-verify script but reads the not-indexed URL list.
Used to confirm or refute the audit's "0 posts ever updated, median age 9.6 years"
claim against current live JSON-LD.
"""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

# Reuse logic from the survivors script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sameday_blog_survivors_verify import fetch  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
URL_FILE = ROOT / "Clients" / "SameDay" / "Full SEO Audit" / "_notindexed_113_urls.txt"
OUT_FILE = ROOT / "Clients" / "SameDay" / "Full SEO Audit" / "_notindexed_113_verification.csv"


def main():
    urls = [u.strip() for u in URL_FILE.read_text().splitlines() if u.strip()]
    print(f"Verifying {len(urls)} not-indexed URLs ...", flush=True)

    rows = []
    for i, u in enumerate(urls, 1):
        print(f"[{i:03d}/{len(urls)}] {u}", flush=True)
        rec = fetch(u)
        rec.pop("_links", None)
        rows.append(rec)
        time.sleep(0.5)

    cols = [
        "url", "status", "final_url", "schema_type",
        "datePublished", "dateModified", "dates_match",
        "author", "visible_updated_text",
        "word_count_main", "outbound_internal_links",
        "error",
    ]
    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    print(f"\nWrote: {OUT_FILE}")
    print(f"Rows: {len(rows)}")


if __name__ == "__main__":
    sys.exit(main())
