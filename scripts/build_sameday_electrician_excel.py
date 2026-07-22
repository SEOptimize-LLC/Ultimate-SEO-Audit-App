"""Build the SameDay Electrician SLC Cluster Excel deliverable.

Output: Clients/SameDay/Full SEO Audit/sameday_electrician_slc_cluster.xlsx
Tabs:
  1. Summary             - KPIs and the URL-404 finding
  2. URGENT - URL Fix    - The dead URL issue, isolated for visibility
  3. Keywords            - All 974 electrician/electrical queries
  4. Target Pages        - Cluster page inventory + verification
  5. Striking Distance   - 53 queries pos 4-15, ranked
  6. Supporting Blogs    - 10 existing + 4 net-new
  7. On-Page Fixes       - Per page
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
OUTPUT = CLIENT_DIR / "Full SEO Audit" / "sameday_electrician_slc_cluster.xlsx"


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
URGENT_FILL = PatternFill("solid", fgColor="C00000")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row=1, urgent=False):
    fill = URGENT_FILL if urgent else HEADER_FILL
    for cell in ws[row]:
        cell.fill = fill
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


def is_branded_gbp(p):
    return "utm_source=" in p


def is_electrician(q):
    ql = q.lower()
    if "and electrical" in ql or "plumbing and electrical" in ql or "plumbing, heating" in ql:
        return False
    return "electric" in ql


def main():
    wb = Workbook()
    rows = []
    with GSC_CSV.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    el_rows = [r for r in rows if is_electrician(r["query"]) and not is_branded_gbp(r["page"])]

    # ---------- Tab 1: Summary ----------
    ws = wb.active
    ws.title = "Summary"
    summary = [
        ("Metric", "Value", "Notes"),
        ("Cluster", "Electrician / Electrical Salt Lake City", ""),
        ("Source audit", "Technical & On-Page Audit Apr 8 2026 - Roadmap Item #11", ""),
        ("Data window", "GSC export Apr 21 2026 (last 90 days)", ""),
        (
            "Total electrician/electrical queries",
            len({r["query"] for r in el_rows}),
            "Excludes branded GBP UTM URLs and brand-name combos",
        ),
        ("Total impressions", sum(int(r["impressions"]) for r in el_rows), ""),
        ("Total clicks", sum(int(r["clicks"]) for r in el_rows), ""),
        ("Cluster CTR", "0.03%", "Calculated"),
        (
            "Audit's referenced URL",
            "https://samedayutah.com/service-area/electrical/salt-lake-city-ut/",
            "404 DEAD - see URGENT tab",
        ),
        (
            "Actual live SLC electrical URL",
            "https://samedayutah.com/service-area/salt-lake-city-ut/electrical/",
            "200 OK - inverse URL pattern",
        ),
        ("Striking distance queries (pos 4-15, >=30 impr)", 55, "Highest leverage post-fix"),
        ("Existing electrical blog posts", 24, "Strong supporting layer"),
        ("Top blog post (entire site)", "/blog/causes-of-low-voltage-in-residential-wiring/", "50 clicks, 16,216 impressions"),
        ("Cities with working URL pattern", "All except SLC", "/service-area/electrical/<city>/ - works for 14 cities"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=70)

    # ---------- Tab 2: URGENT - URL Fix ----------
    ws = wb.create_sheet("URGENT - URL Fix")
    ws.append(
        [
            "Issue",
            "Detail",
            "Recommendation",
        ]
    )
    urgent = [
        (
            "Dead URL: /service-area/electrical/salt-lake-city-ut/",
            "Returns 404 on live site as of Apr 29 2026. GSC still shows 11,545 impressions across 590 queries (page-level, all queries) - or 11,224/555 if filtered to electrician-only queries.",
            "Decision needed - restore the URL with content, OR 301 redirect to /service-area/salt-lake-city-ut/electrical/",
        ),
        (
            "URL pattern inconsistency",
            "All 14 other Utah cities use /service-area/electrical/<city>/ - SLC is the only city using /service-area/<city>/electrical/",
            "Standardize site-wide. Pick one pattern, redirect the other.",
        ),
        (
            "Internal links pointing to dead URL",
            "Unknown - needs developer audit",
            "Crawl site, identify in-content/nav/footer links pointing to the 404 URL, update to canonical",
        ),
        (
            "Lost canonical signal in Google",
            "GSC continues to attribute impressions to the dead URL. Until Google sees the new canonical, ranking will not consolidate.",
            "After URL decision, submit URL Inspection request in GSC for the canonical. Resubmit sitemap.",
        ),
        (
            "24 of top 30 cluster queries land on 404",
            "users who click any of these top results hit a 404 page",
            "This is the single highest-priority fix in the entire cluster. No keyword work matters until this is fixed.",
        ),
    ]
    for row in urgent:
        ws.append(row)
    style_header(ws, urgent=True)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # ---------- Tab 3: Keywords ----------
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
    by_query = defaultdict(lambda: {"clicks": 0, "impr": 0, "pos_w": 0, "pages": defaultdict(int)})
    for r in el_rows:
        q = r["query"]
        by_query[q]["clicks"] += int(r["clicks"])
        by_query[q]["impr"] += int(r["impressions"])
        by_query[q]["pos_w"] += float(r["position"]) * int(r["impressions"])
        by_query[q]["pages"][r["page"]] += int(r["impressions"])

    page_status_map = {
        "https://samedayutah.com/service-area/electrical/salt-lake-city-ut/": "404 DEAD",
        "https://samedayutah.com/service-area/salt-lake-city-ut/electrical/": "200 OK (live SLC)",
        "https://samedayutah.com/electrical/": "200 OK",
        "https://samedayutah.com/electrical/inspections-code-corrections/": "200 OK",
        "https://samedayutah.com/electrical/panels/upgrades/": "200 OK",
        "https://samedayutah.com/electrical/ceiling-fans/installation/": "200 OK",
    }

    def page_status(p):
        if p in page_status_map:
            return page_status_map[p]
        if "/service-area/electrical/" in p:
            return "200 OK (city pattern)"
        return "Not verified"

    for q, d in sorted(by_query.items(), key=lambda x: x[1]["impr"], reverse=True):
        top_page = max(d["pages"].items(), key=lambda x: x[1])[0]
        avg_pos = d["pos_w"] / d["impr"] if d["impr"] else 0
        ctr = d["clicks"] / d["impr"] if d["impr"] else 0
        ws.append(
            [
                q,
                top_page,
                page_status(top_page),
                d["impr"],
                d["clicks"],
                f"{ctr*100:.2f}%",
                round(avg_pos, 1),
            ]
        )
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 4: Target Pages ----------
    ws = wb.create_sheet("Target Pages")
    ws.append(
        [
            "URL",
            "Live Status",
            "Indexed",
            "URL Pattern",
            "Total Impressions",
            "Total Clicks",
            "Recommended Action",
        ]
    )

    by_page = defaultdict(lambda: {"clicks": 0, "impr": 0, "pos_w": 0})
    for r in el_rows:
        p = r["page"]
        by_page[p]["clicks"] += int(r["clicks"])
        by_page[p]["impr"] += int(r["impressions"])
        by_page[p]["pos_w"] += float(r["position"]) * int(r["impressions"])

    target_pages = [
        ("https://samedayutah.com/electrical/", "200", "Yes", "Service root", "Update - root cluster page"),
        (
            "https://samedayutah.com/service-area/electrical/salt-lake-city-ut/",
            "404",
            "Was indexed",
            "service/city (the audit's URL)",
            "URGENT - Restore or 301",
        ),
        (
            "https://samedayutah.com/service-area/salt-lake-city-ut/electrical/",
            "200",
            "Unknown",
            "city/service (live URL - SLC anomaly)",
            "Confirm Google has indexed - submit URL Inspection",
        ),
        (
            "https://samedayutah.com/electrical/inspections-code-corrections/",
            "200",
            "Yes",
            "Service sub",
            "Update - 415+ impressions on code corrections queries",
        ),
        ("https://samedayutah.com/electrical/panels/upgrades/", "200", "Yes", "Service sub", "Update - panel upgrade target"),
        ("https://samedayutah.com/electrical/ceiling-fans/installation/", "200", "Unknown", "Service sub", "Update - pos 12.5 for ceiling fan electrician"),
        ("https://samedayutah.com/service-area/electrical/north-salt-lake-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/south-salt-lake-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/ogden-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/sandy-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/west-jordan-ut/", "200", "Yes", "service/city", "Working pattern"),
        (
            "https://samedayutah.com/service-area/electrical/cottonwood-heights-ut/",
            "200",
            "Yes",
            "service/city",
            "Top performer - pos 4.0 for 'electrician cottonwood heights'",
        ),
        (
            "https://samedayutah.com/service-area/electrical/midvale-ut/",
            "200",
            "Yes",
            "service/city",
            "Pos 4.8 for 'midvale electrician'",
        ),
        ("https://samedayutah.com/service-area/electrical/holladay-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/murray-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/orem-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/provo-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/south-jordan-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/tooele-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/bountiful-ut/", "200", "Yes", "service/city", "Working pattern"),
        ("https://samedayutah.com/service-area/electrical/alpine-ut/", "200", "Yes", "service/city", "Pos 6.7 for 'electrician alpine'"),
    ]
    for url, live, indexed, pattern, action in target_pages:
        d = by_page.get(url, {"clicks": 0, "impr": 0, "pos_w": 0})
        ws.append([url, live, indexed, pattern, d["impr"], d["clicks"], action])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 5: Striking Distance ----------
    ws = wb.create_sheet("Striking Distance")
    ws.append(["Tier", "Query", "Top Page", "Impressions", "Position", "Note"])
    striking = [
        ("Tier 1", "electrician near me", "SLC electrical (post-restore)", 937, 11.3, "Highest single opportunity"),
        ("Tier 1", "emergency electrician", "SLC electrical (post-restore)", 437, 14.2, "Top of page 2"),
        ("Tier 1", "electrician", "SLC electrical (post-restore)", 316, 10.3, "Generic but high-volume"),
        ("Tier 1", "electrical services near me", "SLC electrical (post-restore)", 208, 10.8, ""),
        ("Tier 1", "residential electrical repair", "SLC electrical (post-restore)", 156, 13.9, ""),
        ("Tier 1", "residential electrical services", "SLC electrical (post-restore)", 149, 9.7, "Already top 10"),
        ("Tier 1", "emergency electrical service", "SLC electrical (post-restore)", 126, 11.6, ""),
        ("Tier 1", "electrician cottonwood heights", "/service-area/electrical/cottonwood-heights-ut/", 120, 4.0, "Already top 5 - protect"),
        ("Tier 1", "electrical repair", "SLC electrical (post-restore)", 108, 11.4, ""),
        ("Tier 1", "electrical repair near me", "SLC electrical (post-restore)", 107, 11.9, ""),
        ("Tier 1", "local electrician", "SLC electrical (post-restore)", 107, 11.2, ""),
        ("Tier 1", "electrician services near me", "/service-area/electrical/ogden-ut/", 103, 11.5, "Wrong page - SLC should rank"),
        ("Tier 1", "electrician to install ceiling fan", "/electrical/ceiling-fans/installation/", 93, 12.5, "Service sub-page"),
        ("Tier 1", "electricians near me", "SLC electrical (post-restore)", 86, 9.7, ""),
        ("Tier 2", "electrician midvale", "/service-area/electrical/midvale-ut/", 41, 4.8, "Hyperlocal, top 5"),
        ("Tier 2", "electrician alpine", "/service-area/electrical/alpine-ut/", 47, 6.7, "Hyperlocal, top 7"),
        ("Tier 2", "residential master electrician cottonwood heights", "/service-area/electrical/cottonwood-heights-ut/", 62, 6.5, ""),
        ("Tier 2", "residential master electrician holladay", "/service-area/electrical/holladay-ut/", 40, 6.9, ""),
        ("Tier 2", "electrician tooele ut", "/service-area/electrical/tooele-ut/", 30, 7.6, ""),
        ("Tier 2", "residential master electrician sandy", "/service-area/electrical/sandy-ut/", 44, 14.9, ""),
        ("Tier 2", "electrician north salt lake", "/service-area/electrical/north-salt-lake-ut/", 37, 13.1, ""),
        ("Tier 2", "electrician bountiful", "/service-area/electrical/bountiful-ut/", 38, 14.0, ""),
        ("Tier 3", "electrical safety inspections salt lake city ut", "/electrical/inspections-code-corrections/", 42, 13.5, "Service sub-page strengthen"),
        ("Tier 3", "home electrical safety inspection salt lake city", "/electrical/inspections-code-corrections/", 41, 11.7, ""),
        ("Tier 3", "electrical panel upgrade near me", "SLC electrical (post-restore)", 69, 12.4, "Or use /electrical/panels/upgrades/"),
        ("Tier 3", "electrician for electrical panel replacement", "SLC electrical (post-restore)", 58, 8.2, ""),
        ("Tier 3", "electrical installation service", "SLC electrical (post-restore)", 68, 10.0, ""),
    ]
    for row in striking:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 6: Supporting Blogs ----------
    ws = wb.create_sheet("Supporting Blogs")
    ws.append(
        [
            "Type",
            "Title / Topic",
            "URL (existing) or Target Query (new)",
            "Status",
            "Score",
            "Clicks",
            "Impressions",
            "Recommended Action",
        ]
    )
    blogs = [
        (
            "Existing - Protect",
            "Causes of Low Voltage in Residential Wiring",
            "https://samedayutah.com/blog/causes-of-low-voltage-in-residential-wiring/",
            "Indexed",
            "44.8 C",
            50,
            16216,
            "Site #1 traffic blog. Add internal link to SLC electrical page. Refresh date. Add author + E-E-A-T.",
        ),
        (
            "Existing - Protect",
            "Many Outlets Per Circuit",
            "https://samedayutah.com/blog/many-outlets-per-circuit/",
            "Indexed",
            "47.9 C",
            6,
            2479,
            "Strongest content score on entire blog. Add internal link to /electrical/panels/upgrades/.",
        ),
        (
            "Existing - Refresh",
            "Hire an Electrician for Whole-House Surge Protector",
            "https://samedayutah.com/blog/hire-an-electrician-to-install-a-whole-house-surge-protector/",
            "Indexed",
            "26.1 D",
            0,
            875,
            "High impressions, zero CTR. Likely title/meta issue. Link to /electrical/ root.",
        ),
        (
            "Existing - Refresh",
            "Inflation Reduction Act: Electrical & Plumbing Savings",
            "https://samedayutah.com/blog/inflation-reduction-act-electrical-plumbing-savings/",
            "Indexed",
            "35.3 D",
            0,
            779,
            "IRA content needs 2026 update. Add panel upgrade tax credit specifics.",
        ),
        (
            "Existing - Refresh",
            "Why is My Electric Bill So High?",
            "https://samedayutah.com/blog/why-is-my-electric-bill-so-high/",
            "Indexed",
            "33.4 D",
            0,
            5,
            "Add Utah-specific content (Rocky Mountain Power rates, time-of-use plans).",
        ),
        (
            "Existing - Refresh",
            "When to Call an Electrician",
            "https://samedayutah.com/blog/when-to-call-an-electrician/",
            "Indexed",
            "32.8 D",
            0,
            3,
            "Direct intent match for 'when to call an electrician' queries. Add SLC service mention.",
        ),
        (
            "Existing - Consolidate",
            "Top Signs You Need an Electrician",
            "https://samedayutah.com/blog/top-signs-you-need-an-electrician/",
            "Not indexed",
            "30.0 D",
            0,
            3,
            "Same intent as /when-to-call-an-electrician/ - decision: consolidate or differentiate",
        ),
        (
            "Existing - Refresh + Reindex",
            "Picking a Residential Electrician",
            "https://samedayutah.com/blog/picking-a-residential-electrician/",
            "Not indexed",
            "33.8 D",
            0,
            0,
            "Commercial-investigation query, supports /service-area/ pages. Refresh and resubmit to GSC.",
        ),
        (
            "Existing - Refresh",
            "Why It's Important to Hire a Professional Salt Lake City Electrician",
            "https://samedayutah.com/blog/why-its-important-to-hire-a-professional-salt-lake-city-electrician/",
            "Indexed",
            "32.0 D",
            0,
            15,
            "Already has SLC in URL - perfect supporting article for the SLC service page.",
        ),
        (
            "Existing - Refresh",
            "When Your New Home Automation System Requires an Electrician",
            "https://samedayutah.com/blog/when-your-new-home-automation-system-requires-an-electrician/",
            "Indexed",
            "33.1 D",
            0,
            5,
            "Bridges electrical and smart home. Update with 2026 home automation context.",
        ),
        (
            "New",
            "Electrical Panel Upgrade Cost in Salt Lake City: 2026 Guide",
            "Target: electrical panel upgrade salt lake city + cost queries",
            "Net new",
            "-",
            "-",
            280,
            "Service page exists but no pricing/info article. Captures investigation intent.",
        ),
        (
            "New",
            "Emergency Electrician Salt Lake City: When You Need 24/7 Service",
            "Target: emergency electrician + 24 hour electrician variants",
            "Net new",
            "-",
            "-",
            3000,
            "Cluster's biggest unaddressed query family. ~3,000 aggregated impressions.",
        ),
        (
            "New",
            "How to Find a Licensed Electrician in Salt Lake City",
            "Target: licensed electrician near me + variants",
            "Net new",
            "-",
            "-",
            80,
            "Trust/credentials angle ties to E-E-A-T weakness flagged in audit.",
        ),
        (
            "New",
            "EV Charger Installation Cost & Tax Credits in Utah (2026)",
            "Target: ev charger installation + IRA queries",
            "Net new",
            "-",
            "-",
            835,
            "EV is in audit's striking distance list at position 9.5. Low effort to win.",
        ),
    ]
    for row in blogs:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # ---------- Tab 7: On-Page Fixes ----------
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
            "/service-area/salt-lake-city-ut/electrical/ (post-restore canonical)",
            "Should include 'Salt Lake City' + primary service term",
            "City-led: 'Electrician in Salt Lake City, Utah'",
            "Sections required: Services / Emergency & 24/7 / Service Areas Within SLC / Pricing / Why Choose / FAQs",
            "Include city + 24/7 + NATE-certified",
            "Reference SLC neighborhoods (Sugar House, Avenues, Federal Heights, Rose Park). Rocky Mountain Power utility context. SLC permitting.",
            "Link to /electrical/panels/upgrades/, /electrical/inspections-code-corrections/, /electrical/ceiling-fans/installation/, /electrical/car-chargers/. Receive links from all 24 electrical blog posts.",
        ),
        (
            "/electrical/",
            "Already optimized per Striking Distance Analysis",
            "Already optimized",
            "Already optimized",
            "Already optimized",
            "Add SLC-specific intro paragraph that links to the SLC city page",
            "Link down to all 14 city service-area pages",
        ),
        (
            "/electrical/inspections-code-corrections/",
            "Add 'Salt Lake City' - 415 impressions/year on safety inspection queries",
            "Strengthen for 'electrical safety inspection' query family",
            "Add: Code Compliance Process / SLC Permitting / Common Violations / Cost",
            "Optimize for higher CTR - currently bottom of page 4",
            "Add Utah-specific code section (NEC + Utah amendments)",
            "Link from /electrical/ root and from blog posts about safety",
        ),
        (
            "/electrical/panels/upgrades/",
            "Add SLC + 2026 - panel upgrades have IRA tax credit relevance",
            "Already optimized",
            "Add: Signs You Need an Upgrade / 100A vs 200A / Cost / Tax Credits / Permitting",
            "Add 'free quote' or 'tax credit eligible' for CTR lift",
            "Add IRA tax credit content - federal credit + Rocky Mountain Power rebates",
            "Link to/from the IRA blog post and /electrical/car-chargers/ (panel upgrades often pair with EV install)",
        ),
        (
            "/service-area/electrical/<city>/ (template for all 14 working URLs)",
            "Add city + neighborhood/landmark for differentiation",
            "Strengthen H1 with 'Trusted/Licensed' qualifier",
            "Add: Service Areas Within City / Common Issues in [City] / Pricing / Same-Day Service",
            "Avoid the 19-page duplicate meta description issue flagged in audit",
            "Differentiate from homepage. Audit notes service pages 'render same content as homepage' - this is the fix.",
            "Link to /electrical/ root, sub-services, and 2-3 nearby city pages",
        ),
    ]
    for row in fixes:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
