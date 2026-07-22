"""
Comfort Solutions — 24 Title Rewrites (Bucket B from the truncated-titles audit).

These are the 24 page titles that are over 60 chars even WITHOUT the
| Comfort Solutions suffix. They need genuine rewrites — stripping
filler words ("Top," "Reliable," "Expert," "Find the Best") and
front-loading the primary query phrase.

Format follows the existing comfort_truncated_titles_plan.xlsx structure
so this Excel can be used directly by the VA without retraining.

Output:
    Clients/Comfort/Full SEO Audit/comfort_24_title_rewrites.xlsx
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import date

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
OUT_XLSX = os.path.join(
    ROOT, "Clients/Comfort/Full SEO Audit/comfort_24_title_rewrites.xlsx"
)

NAVY = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HFONT = Font(bold=True, color="FFFFFF", size=11)


# Manual rewrites — primary keyword front-loaded, filler stripped, length
# kept under 60 chars including the | Comfort Solutions suffix. Some
# rewrites match the existing recommendation in the audit Excel; others
# are fresh because the existing recommendation was either too generic
# or didn't match the page's intent.
REWRITES = [
    {
        "url": "https://www.comfortsolutionsutah.com/gas-fireplace-repair-services-in-salt-lake-city/",
        "current": "Gas Fireplace Repair Salt Lake City - Professional Service & Installation",
        "rewrite": "Gas Fireplace Repair in Salt Lake City | Comfort Solutions",
        "rationale": "Strip 'Professional Service & Installation' (generic filler — repair is the page's actual focus, not installation)",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-cleaning-park-city/",
        "current": "Furnace Cleaning Park City - Expert HVAC Services and Heating Solutions",
        "rewrite": "Furnace Cleaning in Park City, UT | Comfort Solutions",
        "rationale": "Strip 'Expert HVAC Services and Heating Solutions' (filler that dilutes the specific service)",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/electric-fireplace-south-salt-lake-city/",
        "current": "Electric Fireplace South Salt Lake City - Expert Installation Services",
        "rewrite": "Electric Fireplace Installation in South Salt Lake City",
        "rationale": "Page is specifically about installation — front-load that. Drop suffix to fit the long city name.",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/expert-ac-repair-davis-county/",
        "current": "Reliable AC Repair Davis | Affordable Solutions for Your Cooling Needs",
        "rewrite": "AC Repair in Davis County, UT | Comfort Solutions",
        "rationale": "Strip 'Reliable' and the entire 'Affordable Solutions' phrase. Add 'County' for clarity.",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-installation-park-city/",
        "current": "Top Furnace Installation in Park City: Reliable and Efficient Services",
        "rewrite": "Furnace Installation in Park City, UT | Comfort Solutions",
        "rationale": "Strip 'Top' and 'Reliable and Efficient Services' (zero ranking signal)",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-repair-sandy/",
        "current": "Top Furnace Repair Services in Sandy: Reliable Solutions for Your Home",
        "rewrite": "Furnace Repair in Sandy, UT | Comfort Solutions",
        "rationale": "Strip 'Top,' 'Services,' and the trailing filler clause",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-replacement-park-city/",
        "current": "Top Furnace Replacement in Park City: Reliable Solutions for Your Home",
        "rewrite": "Furnace Replacement in Park City, UT | Comfort Solutions",
        "rationale": "Strip 'Top' and the trailing filler clause",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/gas-fireplace-contractor-in-davis-county/",
        "current": "Top Gas Fireplace Contractor in Davis County for Quality Installations",
        "rewrite": "Gas Fireplace Contractor in Davis County, UT",
        "rationale": "Strip 'Top' and 'for Quality Installations'. Drop suffix to fit 'Davis County, UT'.",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/emergency-furnace-repair-salt-lake-city/",
        "current": "Reliable Emergency Furnace Repair in Salt Lake City – Fast Solutions!",
        "rewrite": "Emergency Furnace Repair in Salt Lake City | 24/7",
        "rationale": "Strip 'Reliable' and 'Fast Solutions'. Replace with '24/7' which signals urgency and is a real query qualifier.",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-installation-services-in-sandy/",
        "current": "Top Furnace Installation Services in Sandy for Comfort and Efficiency",
        "rewrite": "Furnace Installation in Sandy, UT | Comfort Solutions",
        "rationale": "Strip 'Top,' 'Services,' and the trailing 'for Comfort and Efficiency' clause",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/outdoor-fireplace-contractor-in-sandy/",
        "current": "Top Outdoor Fireplace Contractor in Sandy for Your Dream Installation",
        "rewrite": "Outdoor Fireplace Contractor in Sandy, UT",
        "rationale": "Strip 'Top' and 'for Your Dream Installation'. Drop suffix to fit.",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-installation-services-in-salt-lake-city/",
        "current": "Expert Furnace Installation in Salt Lake City: Quality You Can Trust",
        "rewrite": "Furnace Installation in Salt Lake City | Comfort Solutions",
        "rationale": "Strip 'Expert' and 'Quality You Can Trust'",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-repair-services-in-ogden/",
        "current": "Reliable Furnace Repair Services in Ogden for Your Home and Business",
        "rewrite": "Furnace Repair in Ogden, UT | Comfort Solutions",
        "rationale": "Strip 'Reliable,' 'Services,' and the trailing 'Home and Business' clause",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-repair-services-in-orem/",
        "current": "Top Furnace Repair Services in Orem for Quick and Reliable Solutions",
        "rewrite": "Furnace Repair in Orem, UT | Comfort Solutions",
        "rationale": "Strip 'Top,' 'Services,' and the trailing filler clause",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/gas-fireplace-inserts-in-south-salt-lake-city/",
        "current": "Top Gas Fireplace Inserts in South Salt Lake City: Comfort and Style",
        "rewrite": "Gas Fireplace Inserts in South Salt Lake City",
        "rationale": "Strip 'Top' and 'Comfort and Style'. Drop suffix — long city name eats the budget.",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/fireplace-contractor-in-layton/",
        "current": "Find the Best Fireplace Contractor in Layton for Your Home's Warmth",
        "rewrite": "Fireplace Contractor in Layton, UT | Comfort Solutions",
        "rationale": "Strip 'Find the Best' and the closing filler",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/fireplace-inserts-contractor-in-ogden/",
        "current": "Top Fireplace Inserts Contractor in Ogden for Quality Installations",
        "rewrite": "Fireplace Inserts Contractor in Ogden, UT",
        "rationale": "Strip 'Top' and 'for Quality Installations'. Drop suffix to fit.",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/fireplace-service-salt-lake-city/",
        "current": "Reliable Fireplace Service in Salt Lake City for Your Comfort Needs",
        "rewrite": "Fireplace Service in Salt Lake City | Comfort Solutions",
        "rationale": "Strip 'Reliable' and the closing filler clause",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-replacement-salt-lake-city/",
        "current": "Top Furnace Replacement in Salt Lake City: Expert Solutions Await",
        "rewrite": "Furnace Replacement in Salt Lake City | Comfort Solutions",
        "rationale": "Strip 'Top' and 'Expert Solutions Await'",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-repair-salt-lake-city/",
        "current": "Top Furnace Repair in Salt Lake City – Fast and Reliable Service",
        "rewrite": "Furnace Repair in Salt Lake City | Comfort Solutions",
        "rationale": "Strip 'Top' and 'Fast and Reliable Service'",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/furnace-replacement-services-ogden/",
        "current": "Top Furnace Replacement Ogden: Reliable and Affordable Solutions",
        "rewrite": "Furnace Replacement in Ogden, UT | Comfort Solutions",
        "rationale": "Strip 'Top' and 'Reliable and Affordable Solutions.' Add 'in' for natural reading.",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/gas-fireplace-inserts-sandy/",
        "current": "Discover the Best Gas Fireplace Inserts in Sandy for Cozy Living",
        "rewrite": "Gas Fireplace Inserts in Sandy, UT | Comfort Solutions",
        "rationale": "Strip 'Discover the Best' and 'for Cozy Living'",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/electric-fireplace-services-in-sandy/",
        "current": "Top Electric Fireplace Services in Sandy for Cozy Living Spaces",
        "rewrite": "Electric Fireplace Services in Sandy | Comfort Solutions",
        "rationale": "Strip 'Top' and 'for Cozy Living Spaces'",
    },
    {
        "url": "https://www.comfortsolutionsutah.com/how-a-fireplace-insert-can-boost-home-heating-efficiency/",
        "current": "Fireplace Insert Boosts Heating Efficiency - Comfort Solutions - Comfort Solutions",
        "rewrite": "How a Fireplace Insert Boosts Heating Efficiency",
        "rationale": "Duplicate-suffix bug: 'Comfort Solutions' appears twice. Restore the original 'How a' question framing — matches the URL slug and the article's actual purpose.",
    },
]


def style_header(ws, row, n):
    for c in range(1, n + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = NAVY
        cell.font = HFONT
        cell.alignment = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )
    ws.row_dimensions[row].height = 28


def widths(ws, w):
    for c, n in w.items():
        ws.column_dimensions[get_column_letter(c)].width = n


def main() -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Title Rewrites"

    ws["A1"] = "Comfort Solutions — 24 Title Rewrites"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = (
        f"Generated: {date.today().isoformat()} | "
        "Bucket B from truncated-titles audit (titles >60 chars even without "
        "the | Comfort Solutions suffix — genuine rewrites required)"
    )
    ws["A2"].font = Font(italic=True, color="666666")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:G2")
    ws.row_dimensions[2].height = 32

    ws["A4"] = "Common pattern this fixes"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "All 23 city service pages share the same anti-pattern: padding the "
        "title with filler adjectives ('Top,' 'Reliable,' 'Expert,' 'Find "
        "the Best,' 'Discover the Best') and trailing platitudes ('for Your "
        "Home,' 'for Cozy Living,' 'Quality You Can Trust'). These add zero "
        "ranking signal and push the title past the 60-char threshold. "
        "Strip them and the title fits naturally with the brand suffix. "
        "The 24th item (the blog post) has a duplicate-suffix bug — "
        "'Comfort Solutions' appears twice."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:G5")
    ws.row_dimensions[5].height = 110

    ws.append([])
    ws.append([
        "#", "URL", "Current Title", "Curr Len",
        "Recommended Rewrite", "New Len", "What Changed / Rationale",
    ])
    style_header(ws, 7, 7)

    for i, r in enumerate(REWRITES, start=1):
        ws.append([
            i, r["url"], r["current"], len(r["current"]),
            r["rewrite"], len(r["rewrite"]), r["rationale"],
        ])

    widths(ws, {1: 5, 2: 60, 3: 55, 4: 10, 5: 50, 6: 10, 7: 60})
    ws.freeze_panes = "A8"
    for row in ws.iter_rows(min_row=8, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # Implementation guide tab
    ws2 = wb.create_sheet("Implementation")
    ws2.append(["Step", "What to do"])
    style_header(ws2, 1, 2)
    steps = [
        ("1. For each row in 'Title Rewrites'", "Open the URL in WordPress (Pages or Posts)."),
        ("2. Locate the Rank Math SEO meta box", "Find the 'Title' field in the Rank Math snippet preview."),
        ("3. Replace with the Recommended Rewrite", "Paste the new title from column E exactly."),
        ("4. Save / Update the page", "Verify the snippet preview shows the updated title."),
        ("5. After all 24 are done", "Run a quick fetch on each URL (e.g., curl or browser View Source) and confirm the <title> tag matches the rewrite."),
        ("6. Estimated effort", "~5 minutes per page × 24 = ~2 hours total."),
        ("7. Verification timeline", "Google re-crawls and reflects new titles in SERPs within 1-3 weeks for active pages. Check GSC URL Inspection for any pages where the new title doesn't appear after 3 weeks."),
    ]
    for s in steps:
        ws2.append(list(s))
    widths(ws2, {1: 38, 2: 75})
    ws2.freeze_panes = "A2"
    for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
    wb.save(OUT_XLSX)

    # Verification: check all rewrites are under 60 chars
    over_limit = [r for r in REWRITES if len(r["rewrite"]) > 60]
    print(f"Total rewrites: {len(REWRITES)}")
    print(f"All within 60 chars: {len(REWRITES) - len(over_limit)}")
    if over_limit:
        print(f"WARNING: {len(over_limit)} rewrites still over 60 chars:")
        for r in over_limit:
            print(f"  {len(r['rewrite'])} | {r['rewrite']}")
    print(f"\nSaved: {OUT_XLSX}")


if __name__ == "__main__":
    main()
