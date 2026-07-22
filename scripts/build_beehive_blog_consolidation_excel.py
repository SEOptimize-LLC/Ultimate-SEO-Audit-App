"""Build the Beehive Blog Consolidation Excel deliverable.

Output: Clients/Beehive/Full Site SEO Audit/beehive_blog_consolidation.xlsx
Tabs:
  1. Summary             - 3-tier framework + numbers
  2. Tier 1 - Protect    - 61 posts with clicks (full list, sortable)
  3. Tier 2 - Optimize   - 101 posts >100 imps, 0 clicks
  4. Tier 3a - Noindex   - 249 indexed but zero-traffic posts
  5. Tier 3b - Redirect  - 77 not-indexed posts (decide redirect target)
  6. Tier 3c - Unpublish - 27 unknown-to-Google posts
  7. Implementation Order- Phase-by-phase plan
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
CLIENT_DIR = ROOT / "Clients" / "Beehive"
SOURCE = CLIENT_DIR / "Full Site SEO Audit" / "content_inventory_by_type.xlsx"
OUTPUT = CLIENT_DIR / "Full Site SEO Audit" / "beehive_blog_consolidation.xlsx"


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row=1):
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 32


def autosize(ws, min_w=10, max_w=80):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        longest = 0
        for cell in col:
            if cell.value is None:
                continue
            longest = max(longest, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(min_w, longest + 2), max_w)


def wrap_data_rows(ws, start_row=2):
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def main():
    src = openpyxl.load_workbook(SOURCE, data_only=True)
    blog_ws = src["Blog Post"]
    rows = list(blog_ws.iter_rows(values_only=True))
    data = [r for r in rows[1:] if r[0]]

    # Bucket
    protect = [r for r in data if r[8] and r[8] > 0]
    optimize = [r for r in data if (r[9] and r[9] > 100) and (not r[8] or r[8] == 0)]
    noindex_redirect = [r for r in data if (not r[8] or r[8] == 0) and (not r[9] or r[9] <= 100)]

    tier3a = [r for r in noindex_redirect if r[4] and "submitted and indexed" in str(r[4]).lower()]
    tier3b = [r for r in noindex_redirect if r[4] and "not indexed" in str(r[4]).lower()]
    tier3c = [r for r in noindex_redirect if not r[4] or "unknown" in str(r[4]).lower()]

    # Sort each tier by impressions descending (then clicks)
    protect.sort(key=lambda r: (r[8] or 0, r[9] or 0), reverse=True)
    optimize.sort(key=lambda r: r[9] or 0, reverse=True)
    tier3a.sort(key=lambda r: r[9] or 0, reverse=True)
    tier3b.sort(key=lambda r: r[9] or 0, reverse=True)
    tier3c.sort(key=lambda r: r[9] or 0, reverse=True)

    wb = Workbook()

    # ---------- Summary ----------
    ws = wb.active
    ws.title = "Summary"
    summary = [
        ("Item", "Value", "Notes"),
        ("Total blog posts", len(data), ""),
        ("Tier 1 - PROTECT (has clicks)", len(protect), "Keep, defend with internal links"),
        ("Tier 2 - OPTIMIZE (>100 imps, 0 clicks)", len(optimize), "Refresh title/meta/CTA - DO NOT delete"),
        ("Tier 3 - NOINDEX/REDIRECT total", len(noindex_redirect), "<=100 imps and 0 clicks"),
        ("  Tier 3a - Indexed but zero-traffic", len(tier3a), "Noindex via robots meta tag"),
        ("  Tier 3b - Not indexed by Google", len(tier3b), "301 redirect to relevant service page"),
        ("  Tier 3c - No clear indexation signal", len(tier3c), "15 blank Coverage + 12 'URL is unknown to Google' - Unpublish (revert to draft)"),
        ("", "", ""),
        ("Total Tier 1 clicks (90d)", sum(r[8] or 0 for r in protect), ""),
        ("Total Tier 1 impressions (90d)", sum(r[9] or 0 for r in protect), ""),
        ("Total Tier 2 impressions (90d)", sum(r[9] or 0 for r in optimize), "Currently 0 clicks - CTR fix opportunity"),
        ("Total Tier 3 impressions (90d)", sum(r[9] or 0 for r in noindex_redirect), "Negligible value, consuming crawl budget"),
        ("", "", ""),
        ("Note", "14 most-declining posts already covered in beehive_blog_recovery_plan_v2.xlsx", "This plan complements that work"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=70)

    # Helper to write a tier sheet
    def write_tier(name, rows_, action_col=False, header_extra=None):
        ws = wb.create_sheet(name)
        header = ["URL", "Word Count", "Crawl Depth", "Inlinks", "Clicks (90d)", "Impressions (90d)", "Coverage", "Indexed Status", "Published"]
        if header_extra:
            header.extend(header_extra)
        ws.append(header)
        for r in rows_:
            row = [
                r[0],
                r[5],
                r[6],
                r[7],
                r[8] or 0,
                r[9] or 0,
                r[4] or "",
                r[3] or "",
                r[10],
            ]
            if header_extra:
                row.extend([""] * len(header_extra))  # blank columns for human-filled fields
            ws.append(row)
        style_header(ws)
        ws.freeze_panes = "A2"
        autosize(ws, max_w=80)
        return ws

    # ---------- Tier 1 ----------
    ws = write_tier(
        "Tier 1 - Protect",
        protect,
        header_extra=["Internal Link Target (service page)", "Last Refreshed Date Decision", "Status"],
    )

    # ---------- Tier 2 ----------
    ws = write_tier(
        "Tier 2 - Optimize",
        optimize,
        header_extra=["New Title", "New Meta Description", "Service Page CTA Target", "Status"],
    )

    # ---------- Tier 3a ----------
    ws = write_tier(
        "Tier 3a - Noindex",
        tier3a,
        header_extra=["Date Noindexed", "Status"],
    )

    # ---------- Tier 3b ----------
    ws = write_tier(
        "Tier 3b - Redirect",
        tier3b,
        header_extra=["Redirect Target (service page)", "Date Redirected", "Status"],
    )

    # ---------- Tier 3c ----------
    ws = write_tier(
        "Tier 3c - Unpublish",
        tier3c,
        header_extra=["Date Unpublished", "Status"],
    )

    # ---------- Implementation Order ----------
    ws = wb.create_sheet("Implementation Order")
    ws.append(["Phase", "Week", "Action", "Owner", "Volume", "Effort Estimate"])
    impl = [
        ("Phase 0", "Week 1", "Confirm Tier 1 list with stakeholder; build Tier 3b redirect map", "SEO + Content owner", "61 + 77 decisions", "8-12 hours"),
        ("Phase 0", "Week 1", "Continue beehive_blog_recovery_plan_v2.xlsx for 14 declining posts (already in flight)", "Content writer", "14 posts", "Already scoped"),
        ("Phase 1", "Weeks 2-4", "Tier 2 CTR fixes - rewrite title, meta, add CTA on each post (top-down by impressions)", "Content editor", "101 posts", "~30 min/post = 50 hrs"),
        ("Phase 2", "Week 5", "Tier 3a noindex pass - add noindex meta to all 249 indexed-but-zero-traffic posts", "Developer + SEO", "249 posts", "Batch via plugin/theme = 4-8 hrs"),
        ("Phase 3", "Week 6", "Tier 3b redirects - implement 301 redirects per the redirect map built in Phase 0", "Developer", "77 redirects", "4-8 hrs"),
        ("Phase 3", "Week 6", "Tier 3c unpublish - revert 27 unknown-to-Google posts to Draft status in WordPress", "Content editor", "27 posts", "1-2 hrs"),
        ("Phase 4", "Weeks 7-8", "Tier 1 internal linking - add 1-2 contextual links from each protected post to relevant service page", "Content editor", "61 posts", "~20 min/post = 20 hrs"),
        ("Phase 5", "Weeks 9-12", "Monitor GSC: clicks on Tier 1, CTR on Tier 2, crawl stats reallocation, any ranking drops", "SEO", "Ongoing", "30-day report"),
    ]
    for row in impl:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap_data_rows(ws)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")
    print(f"  Tier 1 Protect:    {len(protect)} posts")
    print(f"  Tier 2 Optimize:   {len(optimize)} posts")
    print(f"  Tier 3a Noindex:   {len(tier3a)} posts")
    print(f"  Tier 3b Redirect:  {len(tier3b)} posts")
    print(f"  Tier 3c Unpublish: {len(tier3c)} posts")


if __name__ == "__main__":
    main()
