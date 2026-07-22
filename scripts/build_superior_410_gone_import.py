"""
Superior Water & Air — 410 Gone bulk import for broken image URLs.

Generates a Rank Math CSV that marks all 83 broken image URLs as
410 Gone, telling Google these resources are permanently removed and
should be deindexed faster than the default 404 timeline.

Format follows Rank Math's CSV import spec
(https://rankmath.com/kb/how-to-manage-redirects-via-csv/):
    - Comma-separated
    - Header: id, source, matching, destination, type, category, status, ignore
    - For 410: type=410, destination is required but ignored by Rank Math for 410s

Inputs:
    Clients/Superior/Superior - Technical Audit.xlsx
        Tab 'response_codes_internal_client_' — 83 image URLs returning 404

Output:
    Clients/Superior/Full SEO Audit/superior_410_gone_broken_images_import.csv
"""
from __future__ import annotations

import csv
import io
import os
import sys
from urllib.parse import urlparse

import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
SRC = os.path.join(
    ROOT, "Clients/Superior/Superior - Technical Audit.xlsx"
)
OUT = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_410_gone_broken_images_import.csv",
)

IMAGE_EXTS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".svg", ".bmp", ".tiff", ".ico",
)


def load_broken_images() -> list[str]:
    """Return the list of 83 image URLs that returned 404 in the SF crawl."""
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["response_codes_internal_client_"]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        addr = row[0]
        status = row[2]
        if not addr or status != 404:
            continue
        if not any(addr.lower().endswith(e) for e in IMAGE_EXTS):
            continue
        rows.append(addr)
    wb.close()
    # Dedupe just in case
    return list(dict.fromkeys(rows))


def main() -> None:
    images = load_broken_images()
    print(f"Broken image URLs to mark 410: {len(images)}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "source", "matching", "destination",
            "type", "category", "status", "ignore",
        ])
        for url in images:
            # Source is the relative path (Rank Math accepts both — relative
            # is more portable across staging/prod environments)
            path = urlparse(url).path.lstrip("/")
            writer.writerow([
                "",                    # empty ID = create new
                path,                  # source: relative path
                "exact",               # matching mode
                url,                   # destination (required by Rank Math
                                       # even for 410; not user-visible
                                       # because 410 sends Gone, not redirect)
                "410",                 # the actual fix: 410 Gone
                "Broken Images 2026",  # category for traceability
                "active",
                "",
            ])

    # Verify the output
    with open(OUT, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"\nSaved: {OUT}")
    print(f"Verification:")
    print(f"  Total rows in output: {len(rows)}")
    print(f"  Type=410 rows: {sum(1 for r in rows if r['type'] == '410')}")
    print(f"  Empty IDs (new rules): {sum(1 for r in rows if not r['id'])}")
    src_set = {r["source"] for r in rows}
    print(f"  Unique sources: {len(src_set)}")

    print(f"\nFirst 3 rows:")
    for r in rows[:3]:
        print(
            f"  id={r['id']!r:5s}  type={r['type']}  "
            f"source={r['source'][:60]:60s}"
        )


if __name__ == "__main__":
    main()
