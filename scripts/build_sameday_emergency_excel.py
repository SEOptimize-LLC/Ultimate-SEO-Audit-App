"""Build the SameDay Emergency Pages Cluster Excel deliverable.

Output: Clients/SameDay/Full SEO Audit/sameday_emergency_pages_cluster.xlsx
Tabs:
  1. Summary             - Cluster KPIs and the stray-URL finding
  2. Decisions Needed    - 3 decisions before the local SEO agent can start
  3. Pages Inventory     - 4 legitimate + 1 stray + 1 proposed
  4. Keywords by Page    - Top queries assigned to each page (one row per query)
  5. Differentiation     - Per-page role + content boundaries
  6. Universal Elements  - 7 items every emergency page needs
  7. Supporting Blogs    - 3 existing + 5 net-new
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
OUTPUT = CLIENT_DIR / "Full SEO Audit" / "sameday_emergency_pages_cluster.xlsx"


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
DECISION_FILL = PatternFill("solid", fgColor="C00000")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

EMERGENCY_PAGES = {
    "https://samedayutah.com/emergency-services/": "Hub",
    "https://samedayutah.com/emergency-services/plumbing-repair/": "Emergency Plumbing",
    "https://samedayutah.com/emergency-services/air-conditioner-repair/": "Emergency AC",
    "https://samedayutah.com/emergency-services/furnace-repair/": "Emergency Heating",
    "https://samedayutah.com/new-emergency-services-page/": "STRAY DRAFT URL",
}


def style_header(ws, row=1, decision=False):
    fill = DECISION_FILL if decision else HEADER_FILL
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


def main():
    wb = Workbook()
    rows = []
    with GSC_CSV.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(r)

    # ---------- Tab 1: Summary ----------
    ws = wb.active
    ws.title = "Summary"
    page_metrics = {}
    for ep in EMERGENCY_PAGES:
        p_rows = [r for r in rows if r["page"] == ep]
        page_metrics[ep] = {
            "queries": len({r["query"] for r in p_rows}),
            "impr": sum(int(r["impressions"]) for r in p_rows),
            "clicks": sum(int(r["clicks"]) for r in p_rows),
        }

    total_impr = sum(d["impr"] for d in page_metrics.values())
    total_clicks = sum(d["clicks"] for d in page_metrics.values())

    summary = [
        ("Metric", "Value", "Notes"),
        ("Cluster", "Emergency Service Pages", ""),
        ("Source audit", "Technical & On-Page Audit Apr 8 2026 - Roadmap Item #12", ""),
        ("Data window", "GSC export Apr 21 2026 (last 90 days)", ""),
        ("Pages in cluster", 5, "4 legitimate + 1 stray draft URL"),
        ("Total impressions", total_impr, "Across all 5 pages"),
        ("Total clicks", total_clicks, ""),
        ("Cluster CTR", f"{(total_clicks/total_impr*100) if total_impr else 0:.2f}%", "Across all 5 pages"),
        ("Trades with emergency page", "Plumbing, AC, Heating", "Electrical missing"),
        (
            "Stray draft URL",
            "/new-emergency-services-page/",
            "3,186 impressions, top-10 for 7 same-day queries - DECISION NEEDED",
        ),
        (
            "Proposed new page",
            "/emergency-services/electrical-repair/",
            "1,179+ impressions on emergency electrical queries with no dedicated page",
        ),
        ("Existing supporting blogs", 3, "Of which 2 not indexed"),
        ("Pages with EmergencyService schema", 0, "All 5 pages need it"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=70)

    # ---------- Tab 2: Decisions Needed ----------
    ws = wb.create_sheet("Decisions Needed")
    ws.append(["#", "Decision", "Options", "Recommended", "Why this matters"])
    decisions = [
        (
            1,
            "What to do with /new-emergency-services-page/",
            "A) Adopt as /same-day-services/ + 301 from draft URL\nB) Merge into /emergency-services/ + 301\nC) Noindex and rebuild later",
            "Option A",
            "Page is already top-10 for 7 same-day queries (3,186 impressions). The URL is the only thing wrong. Don't waste the rankings.",
        ),
        (
            2,
            "Create /emergency-services/electrical-repair/?",
            "A) Yes - complete the trade set\nB) No - point emergency-electrical queries elsewhere",
            "Option A (Yes)",
            "1,179+ impressions across emergency-electrical queries currently routing to broken SLC electrical URL. Dedicated page closes the gap.",
        ),
        (
            3,
            "Service window for ALL emergency pages",
            "A) 24/7\nB) 6am-10pm same-day\nC) After-hours fee 7pm-7am\nD) Other",
            "Confirm with operations",
            "Audit flagged 'no emergency service differentiation content.' If the agent doesn't have this answer, it can't write the pages credibly.",
        ),
        (
            4,
            "Pricing transparency on emergency pages",
            "A) Disclose trip fee + after-hours rate\nB) 'Call for pricing'\nC) Range estimates",
            "Option A",
            "Currently 0% CTR across 19,896 impressions. Hidden pricing is a likely cause. Users abandon when they can't see costs.",
        ),
    ]
    for row in decisions:
        ws.append(row)
    style_header(ws, decision=True)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # ---------- Tab 3: Pages Inventory ----------
    ws = wb.create_sheet("Pages Inventory")
    ws.append(
        [
            "URL",
            "Role",
            "Live Status",
            "Indexed",
            "Composite Score",
            "Impressions",
            "Clicks",
            "# Queries",
            "Recommended Action",
        ]
    )
    inventory = [
        ("https://samedayutah.com/emergency-services/", "Hub", "200", "Yes", "36.0/100 D", "Update - serve as cluster hub, route to trade pages"),
        ("https://samedayutah.com/emergency-services/plumbing-repair/", "Emergency Plumbing", "200", "Yes", "39.0/100 D", "Update - clear differentiation from /plumbing/"),
        ("https://samedayutah.com/emergency-services/air-conditioner-repair/", "Emergency AC", "200", "Yes", "40.0/100 C", "Update - heat-emergency framing"),
        ("https://samedayutah.com/emergency-services/furnace-repair/", "Emergency Heating", "200", "Yes", "—", "Update - cold-emergency framing"),
        ("https://samedayutah.com/new-emergency-services-page/", "STRAY DRAFT", "200", "Yes", "29.3/100 D", "DECISION 1 - Adopt as /same-day-services/ recommended"),
        ("https://samedayutah.com/emergency-services/electrical-repair/", "PROPOSED", "Does not exist", "—", "—", "DECISION 2 - Recommended yes"),
    ]
    for url, role, live, indexed, score, action in inventory:
        m = page_metrics.get(url, {"impr": "", "clicks": "", "queries": ""})
        ws.append([url, role, live, indexed, score, m["impr"], m["clicks"], m["queries"], action])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # ---------- Tab 4: Keywords by Page ----------
    ws = wb.create_sheet("Keywords by Page")
    ws.append(
        [
            "Page",
            "Page Role",
            "Query",
            "Impressions",
            "Clicks",
            "Position",
        ]
    )
    for ep, role in EMERGENCY_PAGES.items():
        p_rows = sorted(
            [r for r in rows if r["page"] == ep],
            key=lambda x: int(x["impressions"]),
            reverse=True,
        )
        for r in p_rows[:25]:
            ws.append(
                [
                    ep,
                    role,
                    r["query"],
                    int(r["impressions"]),
                    int(r["clicks"]),
                    round(float(r["position"]), 1),
                ]
            )
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 5: Differentiation ----------
    ws = wb.create_sheet("Differentiation")
    ws.append(["Page", "Role", "Top Queries to Win", "Required Content", "Specifically NOT on this page", "Internal Links"])
    diff = [
        (
            "/emergency-services/",
            "Hub",
            "emergency heating repair (647), hvac emergency repair (224), emergency hvac service (212), boiler service 24 7 (71)",
            "Service window above the fold; trade routing blocks for plumbing/HVAC/electrical/furnace; coverage area (36 cities); response SLA; pricing (trip + after-hours + weekend); trust signals; emergency vs urgent vs scheduled definition",
            "Trade-specific repair details (those go on sub-pages); brand specifics; tech specs",
            "Down to all 3 (or 4) trade-specific sub-pages; up to /plumbing/, /heating/, /air-conditioning/, /electrical/; to /service-area/",
        ),
        (
            "/emergency-services/plumbing-repair/",
            "Emergency Plumbing",
            "emergency plumbing services (399), emergency plumber (324), emergency plumbing repair (310), emergency plumbing (291), same day plumber (241), 24 hour plumbers near me (193)",
            "What counts as plumbing emergency checklist; pre-arrival action steps (water main shutoff, electrical safety near water, photo for insurance); scenario-specific response (burst pipe, sewer backup, water heater leak, frozen pipes, slab leak); after-hours pricing; service area",
            "General plumbing overview (that's /plumbing/); water heater install (that's /plumbing/water-heaters/); drain cleaning education",
            "Up to /emergency-services/ hub; to /plumbing/ and /plumbing/water-heaters/ for non-emergency follow-up",
        ),
        (
            "/emergency-services/air-conditioner-repair/",
            "Emergency AC",
            "emergency ac repair (367), emergency air conditioner repair (346), emergency air conditioner repair near me (327), hvac emergency repair (193), emergency air conditioning repair (152)",
            "Heat-emergency framing (90F+ summers, vulnerable members); is-it-an-emergency thresholds; response SLA for heat; common emergency causes (refrigerant leak, compressor failure, tripped breaker, frozen coil); safe waiting actions (fan placement, water intake)",
            "AC install/replacement; maintenance/tune-up; brand-specific (Mitsubishi, etc.)",
            "Up to /emergency-services/ hub; to /air-conditioning/ and /air-conditioning/repair/ for non-emergency follow-up",
        ),
        (
            "/emergency-services/furnace-repair/",
            "Emergency Heating",
            "emergency furnace repair (126), emergency heater repair (110), emergency heating repair (24), 24 hour furnace repair (18), emergency boiler service near me (12)",
            "Cold-emergency framing (below-freezing nights, pipe-freeze risk, hypothermia); is-it-an-emergency thresholds; common causes (pilot ignition, blower motor, gas valve, no fuel); boiler-specific section; safe waiting actions (space heater safety, drip faucets, family centralization)",
            "Furnace install/replacement; heat pump or AC; maintenance/tune-up",
            "Up to /emergency-services/ hub; to /heating/furnaces/ and /heating/furnaces/repair/ for non-emergency follow-up",
        ),
        (
            "/emergency-services/electrical-repair/ (PROPOSED)",
            "Emergency Electrical",
            "emergency electrician near me (469), emergency electrician (437), emergency electrician salt lake city (147), emergency electrical service (126)",
            "Electrical emergency framing (sparking, no power, burning smell, breaker pattern); is-it-an-emergency criteria; safety (water near panels, when to shut main); common causes (panel failure, short, lost service drop, ground fault); after-hours pricing",
            "General electrical overview (that's /electrical/); EV charger install; ceiling fan install",
            "Up to /emergency-services/ hub; to /electrical/ and /electrical/panels/upgrades/ for non-emergency follow-up",
        ),
        (
            "/same-day-services/ (RECOMMENDED renaming of /new-emergency-services-page/)",
            "Same-Day Services",
            "same day plumber (182), same day hvac service near me (142), same day plumbing (118), same day heating (88), same day furnace repair (35)",
            "Same-day vs emergency distinction; service window for same-day; pricing model; what qualifies for same-day; coverage area; dispatch process",
            "Emergency-specific framing; trade education content",
            "Up to /; sideways to /emergency-services/ hub for after-hours emergencies",
        ),
    ]
    for row in diff:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # ---------- Tab 6: Universal Elements ----------
    ws = wb.create_sheet("Universal Elements")
    ws.append(["#", "Element", "Description", "Currently Present?"])
    universal = [
        (1, "Click-to-call CTA above the fold", "Phone visible without scrolling on mobile, click-to-call linked", "Unknown - audit"),
        (2, "Service window stated explicitly", "'24/7' or '6am-10pm' or 'same-day during business hours' - pick one and use everywhere", "No - inconsistent"),
        (3, "Trip fee + after-hours rate disclosure", "Single biggest CTR gap. Users want price BEFORE calling.", "No - missing"),
        (4, "Trust block", "NATE-certified + Mitsubishi Diamond Dealer + 8,500+ reviews + 1957 founding", "Partial - inconsistent across pages"),
        (5, "Service area listed", "6-8 primary cities + link to /service-area/", "Partial"),
        (6, "Schema markup (EmergencyService type)", "Structured data tells Google this is an emergency service", "No - missing on all 5 pages"),
        (7, "Author/technician attribution", "'Reviewed by [licensed technician name]' - emergency pages especially need this for E-E-A-T", "No - audit flagged 1 author credit site-wide"),
    ]
    for row in universal:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # ---------- Tab 7: Supporting Blogs ----------
    ws = wb.create_sheet("Supporting Blogs")
    ws.append(["Type", "Title / Topic", "URL or Target Query", "Status", "Score", "Impressions", "Recommended Action"])
    blogs = [
        (
            "Existing - Refresh",
            "Signs to Call an Emergency Plumber",
            "https://samedayutah.com/blog/signs-call-emergency-plumber/",
            "Indexed",
            "32.5 D",
            397,
            "Direct intent match. Internal link to /emergency-services/plumbing-repair/.",
        ),
        (
            "Existing - Refresh + Reindex",
            "Trenchless Sewer Replacements",
            "https://samedayutah.com/blog/trenchless-sewer-replacements/",
            "Not indexed",
            "33.4 D",
            0,
            "Useful for emergency-sewer scenarios. Refresh and resubmit to GSC.",
        ),
        (
            "Existing - Refresh + Reindex",
            "Trusted SLC Plumber for the Holidays",
            "https://samedayutah.com/blog/we-are-your-trusted-salt-lake-city-plumber-for-the-holidays/",
            "Not indexed",
            "29.9 D",
            0,
            "Holiday-emergency angle. Refresh with current year + reindex.",
        ),
        (
            "New",
            "Burst Pipe? Here's What to Do Before the Plumber Arrives",
            "Target: burst pipe + emergency plumber",
            "Net new",
            "-",
            600,
            "Pre-call action steps. High-intent supporting article for /emergency-services/plumbing-repair/.",
        ),
        (
            "New",
            "How to Tell if Your Furnace Failure is an Emergency (And When It Can Wait)",
            "Target: emergency furnace repair + variants",
            "Net new",
            "-",
            250,
            "Triage intent. Supporting article for /emergency-services/furnace-repair/.",
        ),
        (
            "New",
            "Emergency AC Repair Cost in Salt Lake City: 2026 Pricing",
            "Target: emergency ac repair cost + variants",
            "Net new",
            "-",
            200,
            "No pricing content anywhere in cluster. Captures investigation intent.",
        ),
        (
            "New",
            "Sparking Outlet or Burning Smell? When to Cut Power and Call an Electrician",
            "Target: sparking outlet + emergency electrician",
            "Net new",
            "-",
            150,
            "Safety-first framing. Pairs with proposed /emergency-services/electrical-repair/.",
        ),
        (
            "New",
            "Same-Day Plumber vs Emergency Plumber: What's the Difference and What Costs More",
            "Target: same day plumber + emergency plumber",
            "Net new",
            "-",
            430,
            "Resolves the same-day vs emergency cannibalization at the content layer.",
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

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
