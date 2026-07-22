"""Build the SameDay Water Heater Cluster Excel deliverable.

Output: Clients/SameDay/Full SEO Audit/sameday_water_heater_cluster.xlsx
Tabs:
  1. Summary           - Cluster KPIs and key findings
  2. Keywords          - All 192 water-heater queries from GSC (full list)
  3. Target Pages      - Inventory + on-page status + verification result
  4. Striking Distance - Subset of queries currently ranking pos 4-20
  5. Supporting Blogs  - Existing + recommended new articles
  6. On-Page Fixes     - Specific tasks per cluster URL
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
CLIENT_DIR = ROOT / "Clients" / "SameDay"
GSC_CSV = CLIENT_DIR / "gsc_api_data.csv"
OUTPUT = CLIENT_DIR / "Full SEO Audit" / "sameday_water_heater_cluster.xlsx"


# Style helpers
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


def load_gsc():
    rows = []
    with GSC_CSV.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def is_branded_gbp(page: str) -> bool:
    return "utm_source=" in page


def main():
    wb = Workbook()
    rows = load_gsc()
    wh_rows = [r for r in rows if "water heater" in r["query"].lower()]

    # ---------- Tab 1: Summary ----------
    ws = wb.active
    ws.title = "Summary"
    summary = [
        ("Metric", "Value", "Notes"),
        ("Cluster", "Water Heater", ""),
        ("Source audit", "Technical & On-Page Audit Apr 8 2026 - Roadmap Item #10", ""),
        ("Data window", "GSC export Apr 21 2026 (last 90 days)", ""),
        (
            "Total water-heater queries",
            len({r["query"] for r in wh_rows if not is_branded_gbp(r["page"])}),
            "Excludes branded GBP UTM URLs",
        ),
        (
            "Total impressions",
            sum(int(r["impressions"]) for r in wh_rows if not is_branded_gbp(r["page"])),
            "",
        ),
        (
            "Total clicks",
            sum(int(r["clicks"]) for r in wh_rows if not is_branded_gbp(r["page"])),
            "",
        ),
        ("Cluster CTR", "0.02%", "Calculated from above"),
        ("Primary target page", "https://samedayutah.com/plumbing/water-heaters/", "Verified 200 OK"),
        ("Primary page avg position", "59.2", "Page 6 of Google"),
        ("Top query", "water heater repair", "3,323 impressions, position 76.2"),
        (
            "Pages flagged by Content Audit",
            "/plumbing/water-heaters/, /plumbing/tankless-water-heaters/",
            "R10 - Content Consistency",
        ),
        ("Existing supporting blog posts", 3, "Of which 2 are not indexed"),
        ("Dead URLs in cluster", 1, "/plumbing/tankless-water-heater-installation-salt-lake-city/ - 404"),
        ("URL typos in cluster", 1, "/plumbing/water-heater-replacement-murray-utath/"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=70)

    # ---------- Tab 2: Keywords ----------
    ws = wb.create_sheet("Keywords")
    ws.append(
        [
            "Query",
            "Top Page",
            "Page Status (Apr 29)",
            "Impressions",
            "Clicks",
            "CTR",
            "Position",
        ]
    )

    # Aggregate per query, then take the top page per query
    by_query = defaultdict(lambda: {"clicks": 0, "impr": 0, "pos_w": 0, "pages": defaultdict(int)})
    for r in wh_rows:
        if is_branded_gbp(r["page"]):
            continue
        q = r["query"]
        by_query[q]["clicks"] += int(r["clicks"])
        by_query[q]["impr"] += int(r["impressions"])
        by_query[q]["pos_w"] += float(r["position"]) * int(r["impressions"])
        by_query[q]["pages"][r["page"]] += int(r["impressions"])

    page_status = {
        "https://samedayutah.com/plumbing/water-heaters/": "200 OK",
        "https://samedayutah.com/plumbing/water-heaters/repair/": "200 OK",
        "https://samedayutah.com/plumbing/water-heaters/replacement/": "200 OK",
        "https://samedayutah.com/plumbing/water-heaters/installation/": "200 OK (not indexed)",
        "https://samedayutah.com/plumbing/tankless-water-heaters/": "200 OK",
        "https://samedayutah.com/plumbing/tankless-water-heater-installation-salt-lake-city/": "404 - DEAD",
        "https://samedayutah.com/plumbing/tankless-water-heaters/installation-services-in-orem-utah/": "200 OK",
    }

    for q, d in sorted(by_query.items(), key=lambda x: x[1]["impr"], reverse=True):
        top_page = max(d["pages"].items(), key=lambda x: x[1])[0]
        avg_pos = d["pos_w"] / d["impr"] if d["impr"] else 0
        ctr = d["clicks"] / d["impr"] if d["impr"] else 0
        ws.append(
            [
                q,
                top_page,
                page_status.get(top_page, "Not verified"),
                d["impr"],
                d["clicks"],
                f"{ctr*100:.2f}%",
                round(avg_pos, 1),
            ]
        )
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 3: Target Pages ----------
    ws = wb.create_sheet("Target Pages")
    ws.append(
        [
            "URL",
            "Live Status",
            "Indexed",
            "Composite Score",
            "Grade",
            "Total Impressions",
            "Total Clicks",
            "Avg Position (weighted)",
            "Recommended Action",
        ]
    )

    # Aggregate impressions / clicks per page from the wh_rows
    by_page = defaultdict(lambda: {"clicks": 0, "impr": 0, "pos_w": 0})
    for r in wh_rows:
        p = r["page"]
        by_page[p]["clicks"] += int(r["clicks"])
        by_page[p]["impr"] += int(r["impressions"])
        by_page[p]["pos_w"] += float(r["position"]) * int(r["impressions"])

    target_pages = [
        # (url, live, indexed, score, grade, action)
        ("https://samedayutah.com/plumbing/water-heaters/", "200", "Yes", 39.8, "D", "Update - primary cluster hub"),
        ("https://samedayutah.com/plumbing/water-heaters/repair/", "200", "Yes", 35.3, "D", "Update"),
        ("https://samedayutah.com/plumbing/water-heaters/replacement/", "200", "Yes", 35.4, "D", "Update"),
        ("https://samedayutah.com/plumbing/water-heaters/installation/", "200", "No", 30.8, "D", "Update + reindex"),
        ("https://samedayutah.com/plumbing/tankless-water-heaters/", "200", "Yes", 37.4, "D", "Update - resolve R10 flag"),
        (
            "https://samedayutah.com/plumbing/tankless-water-heater-installation-salt-lake-city/",
            "404",
            "No",
            30.8,
            "D",
            "DECISION NEEDED - restore or 301",
        ),
        (
            "https://samedayutah.com/plumbing/tankless-water-heaters/installation-services-in-orem-utah/",
            "200",
            "Yes",
            29.3,
            "D",
            "Update",
        ),
        (
            "https://samedayutah.com/plumbing/water-heaters/installation-orem/",
            "200",
            "No",
            34.2,
            "D",
            "Reindex",
        ),
        (
            "https://samedayutah.com/plumbing/water-heaters/installation-lehi-utah/",
            "200",
            "No",
            31.6,
            "D",
            "Reindex",
        ),
        ("https://samedayutah.com/plumbing/water-heaters/repair-sandy/", "200", "No", 32.8, "D", "Reindex"),
        (
            "https://samedayutah.com/plumbing/water-heater-replacement-murray-utath/",
            "200",
            "No",
            31.8,
            "D",
            "Fix typo - create /water-heater-replacement-murray-utah/, 301 the typo URL",
        ),
        (
            "https://samedayutah.com/ppc-plumbing-offer-water-heater/",
            "200",
            "No",
            32.6,
            "D",
            "PPC landing - exclude from organic strategy",
        ),
    ]
    for url, live, indexed, score, grade, action in target_pages:
        d = by_page.get(url, {"clicks": 0, "impr": 0, "pos_w": 0})
        avg_pos = d["pos_w"] / d["impr"] if d["impr"] else 0
        ws.append(
            [
                url,
                live,
                indexed,
                score,
                grade,
                d["impr"],
                d["clicks"],
                round(avg_pos, 1) if avg_pos else "",
                action,
            ]
        )
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 4: Striking Distance ----------
    ws = wb.create_sheet("Striking Distance")
    ws.append(
        [
            "Query",
            "Page",
            "Impressions",
            "Clicks",
            "Position",
            "Why this matters",
        ]
    )
    striking = [
        (
            "water heater repair salt lake city",
            "https://samedayutah.com/plumbing/water-heaters/",
            125,
            0,
            11.0,
            "Top of page 2 - most actionable lift",
        ),
        (
            "service for tankless water heater",
            "https://samedayutah.com/plumbing/tankless-water-heaters/",
            64,
            0,
            5.7,
            "Already top 6 - strengthen content to push to top 3",
        ),
        (
            "salt lake city tankless water heater conversion",
            "https://samedayutah.com/plumbing/tankless-water-heaters/",
            31,
            0,
            6.6,
            "Niche commercial-investigation query, low effort to win",
        ),
        (
            "best tankless water heater installation companies salt lake city",
            "https://samedayutah.com/plumbing/tankless-water-heaters/installation-services-in-orem-utah/",
            32,
            0,
            13.9,
            "URL is Orem but query is SLC - canonical mismatch",
        ),
        (
            "same-day water heater replacement west bountiful utah",
            "Various",
            29,
            0,
            12.3,
            "No dedicated west bountiful page - decide if worth creating",
        ),
        (
            "salt lake city water heater installation tankless conversion",
            "Various",
            22,
            0,
            14.7,
            "Long-tail variant of the SLC tankless conversion query",
        ),
        (
            "sandy water heater replacement",
            "https://samedayutah.com/service-area/plumbing/sandy-ut/",
            21,
            0,
            13.6,
            "Sandy plumbing service-area page is the best target",
        ),
        (
            "gas water heater repair salt lake city",
            "Various",
            21,
            0,
            14.6,
            "Gas-specific content gap - fold into main /repair/ page",
        ),
        (
            "hot water heater repair salt lake city",
            "Various",
            45,
            0,
            14.8,
            "'hot water heater' phrasing - add to title/H2 variations",
        ),
    ]
    for row in striking:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 5: Supporting Blogs ----------
    ws = wb.create_sheet("Supporting Blogs")
    ws.append(
        [
            "Type",
            "Title / Topic",
            "URL (existing) or Target Query (new)",
            "Status",
            "Score",
            "Impressions",
            "Recommended Action",
        ]
    )
    blogs = [
        (
            "Existing",
            "Plumbing Repair Guide",
            "https://samedayutah.com/blog/plumbing-repair-guide/",
            "Indexed",
            "30.0 D",
            88,
            "Refresh with 2026 content, add water heater section, link to /plumbing/water-heaters/",
        ),
        (
            "Existing",
            "Maintain Hot Water Heater",
            "https://samedayutah.com/blog/maintain-hot-water-heater/",
            "Not indexed",
            "28.1 D",
            0,
            "Refresh content first, then submit to GSC. Target query: water heater maintenance",
        ),
        (
            "Existing",
            "Simple Hot Water Heater Maintenance",
            "https://samedayutah.com/blog/simple-hot-water-heater-maintenance/",
            "Not indexed",
            "31.6 D",
            0,
            "Overlaps with /maintain-hot-water-heater/ - decision: consolidate or differentiate",
        ),
        (
            "New",
            "Emergency Water Heater Repair: When to Call vs DIY",
            "Target: emergency hot water heater repair",
            "Net new",
            "-",
            316,
            "Cluster has 6 pages competing for this query. New blog clarifies intent.",
        ),
        (
            "New",
            "Water Heater Repair Cost in Salt Lake City: 2026 Pricing Guide",
            "Target: water heater repair salt lake city + cost queries",
            "Net new",
            "-",
            323,
            "No pricing content exists. Captures commercial-investigation intent.",
        ),
        (
            "New",
            "Tankless vs Tank Water Heater: Which is Right for Utah Homes?",
            "Target: tankless water heater near me + comparison queries",
            "Net new",
            "-",
            150,
            "Bridges /water-heaters/ and /tankless-water-heaters/. Resolves cannibalization.",
        ),
        (
            "New",
            "How Long Does a Water Heater Last? Replacement Signs in Hard-Water Utah",
            "Target: water heater replacement near me + lifespan queries",
            "Net new",
            "-",
            50,
            "Hard-water angle is unique to Utah. Supports /replacement/ page.",
        ),
        (
            "New",
            "Gas Water Heater Repair: Common Problems and Costs",
            "Target: gas water heater repair + variants",
            "Net new",
            "-",
            250,
            "Gas-specific content gap - 5+ separate query phrasings at avg position 22",
        ),
    ]
    for row in blogs:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 6: On-Page Fixes ----------
    ws = wb.create_sheet("On-Page Fixes")
    ws.append(
        [
            "URL",
            "Title",
            "H1",
            "H2 Structure",
            "Meta Description",
            "Body Content",
            "Internal Links",
        ]
    )
    fixes = [
        (
            "https://samedayutah.com/plumbing/water-heaters/",
            "Add Salt Lake City + primary keyword. Currently generic.",
            "Lead with entity: 'Water Heater Repair, Replacement & Installation in Salt Lake City'",
            "Add sections: Repair / Replacement / Installation / Tankless / Common Problems / Pricing / Service Area",
            "Include service-area phrase + CTR differentiator (24/7, same-day, NATE-certified)",
            "Resolve R10 inconsistency. Cause likely: residential/commercial mixed without distinction OR inconsistent service-hours quoted across sections",
            "Add explicit links to all 4 sub-pages and 3 city-specific water-heater pages",
        ),
        (
            "https://samedayutah.com/plumbing/water-heaters/repair/",
            "Include emergency + same-day language - currently misses high-volume queries",
            "Add 'Emergency' to H1 - 316 impressions/year on emergency-related queries",
            "Add Gas / Electric / Tankless repair sections - 5+ separate query types match",
            "Optimize - currently failing CTR check",
            "Add Utah hard-water failure mode content - unique angle",
            "Link up to parent /plumbing/water-heaters/ and across to /replacement/ and /installation/",
        ),
        (
            "https://samedayutah.com/plumbing/water-heaters/replacement/",
            "Already optimized per Striking Distance Analysis",
            "Already optimized",
            "Add H2 sections for: When to Replace / Lifespan / Cost / Brands / Permits",
            "Already optimized",
            "Already optimized per audit. Add Utah hard-water lifespan context.",
            "Currently weak - link to /repair/ (when replacement isn't needed) and /installation/",
        ),
        (
            "https://samedayutah.com/plumbing/tankless-water-heaters/",
            "Optimize - currently fails check",
            "Optimize - currently fails check",
            "Add: Tankless vs Tank / Conversion / Maintenance / Brands / SLC-specific content",
            "Optimize - include conversion + Utah-specific phrasing",
            "Resolve R10 inconsistency flag from Content Audit. Sample for contradictions on capacity, sizing recommendations, or pricing.",
            "Link to /water-heaters/ as sibling, NOT as parent",
        ),
    ]
    for row in fixes:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    # Wrap text on long-form columns
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # Save
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
