"""Build the Beehive Tankless Cluster Optimization Excel deliverable.

Output: Clients/Beehive/Full Site SEO Audit/beehive_tankless_cluster_optimization.xlsx
Tabs:
  1. Summary             - Cluster KPIs + the surprise (blog outranks service page)
  2. Cluster Pages       - All 8 tankless pages with role + metrics
  3. Flagship Queries    - 7 high-volume queries from striking distance
  4. CTR Fix Plan        - Page-by-page changes
  5. Internal Linking    - Funnel structure between pages
  6. Implementation Order- Phase-by-phase plan
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "beehive_tankless_cluster_optimization.xlsx"


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


def wrap(ws, start_row=2):
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def main():
    wb = Workbook()

    # ---------- Summary ----------
    ws = wb.active
    ws.title = "Summary"
    summary = [
        ("Item", "Value", "Notes"),
        ("Task", "Optimize tankless water heater keyword cluster", "Roadmap Item #18 (P3)"),
        ("Flagship queries (per Striking Distance)", 7, ""),
        ("Combined impressions (flagship)", 365683, "Audit window"),
        ("Combined clicks (flagship)", 109, ""),
        ("Cluster CTR (flagship)", "0.03%", ""),
        ("Top page in cluster", "https://www.beehiveplumbing.com/is-it-worth-getting-a-tankless-water-heater/", "Blog post - 0 backlinks"),
        ("Commercial service page", "https://www.beehiveplumbing.com/tankless-water-heaters-utah/", "33 backlinks, 14 RDs - underperforms"),
        ("Pages in cluster", 8, "1 service + 1 dominant blog + 6 supporting"),
        ("Duplicate comparison content", 3, "Pages cover the same vs-tank question - consolidate to one"),
        ("Position range (flagship queries)", "5.1 - 10.9", "Already on page 1-2 - depth + linking pushes higher"),
        ("Recovery target", "0.5% CTR", "From 0.03% baseline = ~1,800 additional clicks/90d"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=80)

    # ---------- Cluster Pages ----------
    ws = wb.create_sheet("Cluster Pages")
    ws.append(
        [
            "URL",
            "Role in Funnel",
            "Indexed",
            "Word Count",
            "Backlinks",
            "Referring Domains",
            "Impressions (90d)",
            "Clicks (90d)",
            "Action",
        ]
    )
    pages = [
        (
            "https://www.beehiveplumbing.com/is-it-worth-getting-a-tankless-water-heater/",
            "Top of funnel - informational",
            "Yes (Apr 25)",
            799,
            0,
            0,
            350454,
            107,
            "PHASE 1 - Title/meta/CTA fix - highest leverage in cluster",
        ),
        (
            "https://www.beehiveplumbing.com/tankless-water-heaters-utah/",
            "Bottom of funnel - commercial service",
            "Yes (Apr 25)",
            2081,
            33,
            14,
            2851,
            7,
            "PHASE 2 - Add city sections, pricing transparency, comparison table, schema",
        ),
        (
            "https://www.beehiveplumbing.com/things-you-should-know-when-switching-to-a-tankless-water-heater/",
            "Mid-funnel - decision/comparison",
            "Yes",
            825,
            0,
            0,
            26483,
            2,
            "PHASE 3 - Add internal link to service page",
        ),
        (
            "https://www.beehiveplumbing.com/conventional-tank-water-heaters-vs-tankless-water-heaters/",
            "Mid-funnel - comparison",
            "Yes",
            627,
            0,
            0,
            4439,
            2,
            "PHASE 4 - Keep as primary comparison, absorb 2 duplicates",
        ),
        (
            "https://www.beehiveplumbing.com/4-ways-a-tankless-water-heater-increases-your-homes-property-value/",
            "Top of funnel - 'why care'",
            "Yes",
            825,
            0,
            0,
            155,
            0,
            "PHASE 3 - Internal link from /is-it-worth/ + to service page",
        ),
        (
            "https://www.beehiveplumbing.com/why-is-my-tankless-water-heater-making-beeping-sounds/",
            "Maintenance/repair intent",
            "Yes",
            1021,
            0,
            0,
            1120,
            2,
            "PHASE 3 - Link to /water-heater-repair-utah/ (per Report 1)",
        ),
        (
            "https://www.beehiveplumbing.com/how-to-determine-the-tankless-water-heater-size-you-need/",
            "Pre-purchase technical",
            "Yes",
            927,
            0,
            0,
            99,
            0,
            "PHASE 3 - Link to service page CTA",
        ),
        (
            "https://www.beehiveplumbing.com/tankless-water-heater-vs-tank-whats-the-difference/",
            "Comparison (DUPLICATE of /conventional-tank.../)",
            "Yes",
            1109,
            0,
            0,
            87,
            0,
            "PHASE 4 - 301 redirect to /conventional-tank-water-heaters-vs-tankless-water-heaters/",
        ),
        (
            "https://www.beehiveplumbing.com/comparing-traditional-tankless-water-heaters/",
            "Comparison (DUPLICATE of /conventional-tank.../)",
            "Yes",
            897,
            0,
            0,
            1,
            0,
            "PHASE 4 - 301 redirect to /conventional-tank-water-heaters-vs-tankless-water-heaters/",
        ),
    ]
    for row in pages:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    wrap(ws)

    # ---------- Flagship Queries ----------
    ws = wb.create_sheet("Flagship Queries")
    ws.append(["Query", "Clicks", "Impressions", "Position", "CTR", "Top Page", "Note"])
    queries = [
        ("tankless water heater", 69, 255504, 5.1, "0.03%", "/is-it-worth-getting-a-tankless-water-heater/", "Highest single opportunity in entire cluster"),
        ("tankless gas water heater", 8, 42466, 9.3, "0.02%", "/is-it-worth-getting-a-tankless-water-heater/", ""),
        ("instant hot water heater", 9, 24098, 8.7, "0.04%", "/is-it-worth-getting-a-tankless-water-heater/", ""),
        ("tankless hot water heater", 3, 13427, 10.9, "0.02%", "/is-it-worth-getting-a-tankless-water-heater/", "Page 2 - close to page 1"),
        ("gas tankless water heater", 5, 12804, 5.9, "0.04%", "/is-it-worth-getting-a-tankless-water-heater/", ""),
        ("tankless water heater gas", 12, 11588, 5.3, "0.10%", "/is-it-worth-getting-a-tankless-water-heater/", "Highest CTR in cluster - the format works for this query"),
        ("on demand hot water heater", 3, 5796, 6.8, "0.05%", "/is-it-worth-getting-a-tankless-water-heater/", ""),
        ("TOTAL", 109, 365683, "—", "0.03%", "—", ""),
    ]
    for row in queries:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- CTR Fix Plan ----------
    ws = wb.create_sheet("CTR Fix Plan")
    ws.append(["Page", "Change", "Current", "Proposed", "Why"])
    fixes = [
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "Title tag",
            "Is It Worth Getting A Tankless Water Heater?",
            "Is a Tankless Water Heater Worth It in Utah? Cost, Lifespan & Pros Explained (2026)",
            "Adds Utah qualifier (local relevance) + year + answer hook for SERP snippet",
        ),
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "Meta description",
            "Generic description",
            "Tankless water heaters cost more upfront but can save Utah homeowners $X/year. Pros, cons, and when it's worth the switch.",
            "Specific value claim + local frame + clear next step",
        ),
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "Definition-first opening",
            "Waffles in first paragraph",
            "For most Utah homeowners, a tankless water heater is worth the upfront investment if [specific conditions]. Here's the math, the trade-offs, and when it doesn't pay off.",
            "Audit's #1 content rule - definitive answer in opening",
        ),
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "Internal links to service page",
            "0 links",
            "3 contextual links to /tankless-water-heaters-utah/",
            "Currently the dominant page has no path to commercial conversion",
        ),
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "Closing CTA block",
            "None",
            "Block at end: 'Ready to install? See our tankless water heater services in Utah' + button to /tankless-water-heaters-utah/",
            "Captures users who decide yes after reading",
        ),
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "Schema markup",
            "None",
            "FAQ schema on the question-style sections",
            "Page already structured Q&A - schema unlocks rich result eligibility",
        ),
        (
            "/tankless-water-heaters-utah/",
            "City sections",
            "Generic Utah",
            "Add 5 city sections (SLC, Park City, Lehi, Sandy, Murray) - 100-150 words each with local entity references",
            "Captures '[city] tankless installation' query family currently absent",
        ),
        (
            "/tankless-water-heaters-utah/",
            "Pricing transparency",
            "No pricing",
            "'What does tankless installation cost in Utah?' section with realistic ranges ($2,500-$5,000+)",
            "Captures cost-intent queries currently leaking elsewhere",
        ),
        (
            "/tankless-water-heaters-utah/",
            "Comparison table",
            "Mentioned in prose",
            "Inline comparison table: tank vs tankless, upfront cost, annual ops, lifespan, footprint, recovery rate",
            "Reinforces topical match for comparison queries currently going to blog",
        ),
        (
            "/tankless-water-heaters-utah/",
            "Schema markup",
            "Limited",
            "Add LocalBusiness + Service schema with priceRange",
            "Reinforces commercial signal for queries with installation/cost intent",
        ),
    ]
    for row in fixes:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Internal Linking ----------
    ws = wb.create_sheet("Internal Linking")
    ws.append(["From Page", "To Page", "Anchor Text Style", "Why"])
    links = [
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "/tankless-water-heaters-utah/",
            "tankless water heater installation services in Utah",
            "Convert informational reader to commercial intent (PRIMARY funnel link)",
        ),
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "/conventional-tank-water-heaters-vs-tankless-water-heaters/",
            "see how tankless compares to traditional tank water heaters",
            "Support undecided users",
        ),
        (
            "/is-it-worth-getting-a-tankless-water-heater/",
            "/4-ways-a-tankless-water-heater-increases-your-homes-property-value/",
            "the home value benefits",
            "Top-of-funnel cross-link",
        ),
        (
            "/things-you-should-know-when-switching-to-a-tankless-water-heater/",
            "/tankless-water-heaters-utah/",
            "Beehive's tankless installation services",
            "Mid-funnel to commercial",
        ),
        (
            "/things-you-should-know-when-switching-to-a-tankless-water-heater/",
            "/how-to-determine-the-tankless-water-heater-size-you-need/",
            "how to size your tankless unit",
            "Mid-funnel cross-link",
        ),
        (
            "/conventional-tank-water-heaters-vs-tankless-water-heaters/",
            "/tankless-water-heaters-utah/",
            "tankless installation in Utah",
            "Decision-stage to commercial",
        ),
        (
            "/conventional-tank-water-heaters-vs-tankless-water-heaters/",
            "/water-heater-replacement-utah/",
            "traditional water heater replacement",
            "Decision-stage alternative path",
        ),
        (
            "/4-ways-a-tankless-water-heater-increases-your-homes-property-value/",
            "/tankless-water-heaters-utah/",
            "see our tankless installation services",
            "Top-of-funnel to commercial",
        ),
        (
            "/4-ways-a-tankless-water-heater-increases-your-homes-property-value/",
            "/is-it-worth-getting-a-tankless-water-heater/",
            "is a tankless water heater worth it?",
            "Top-of-funnel cross-link",
        ),
        (
            "/why-is-my-tankless-water-heater-making-beeping-sounds/",
            "/water-heater-repair-utah/",
            "tankless water heater repair in Utah",
            "Repair intent to repair service page (per Report 1)",
        ),
        (
            "/how-to-determine-the-tankless-water-heater-size-you-need/",
            "/tankless-water-heaters-utah/",
            "professional tankless installation",
            "Pre-purchase technical to commercial",
        ),
        (
            "/tankless-water-heaters-utah/",
            "/is-it-worth-getting-a-tankless-water-heater/",
            "still deciding? read our tankless guide",
            "Commercial back to informational for undecided visitors",
        ),
        (
            "/tankless-water-heaters-utah/",
            "/water-heater-replacement-utah/",
            "traditional water heater replacement",
            "Cross-sell adjacent service",
        ),
    ]
    for row in links:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Implementation Order ----------
    ws = wb.create_sheet("Implementation Order")
    ws.append(["Phase", "Week", "Action", "Pages", "Effort"])
    impl = [
        ("Phase 1", "Weeks 1-2", "CTR fix on /is-it-worth-getting-a-tankless-water-heater/ - title, meta, opening, internal links, CTA, schema", "1 page", "4-6 hours"),
        ("Phase 2", "Weeks 3-4", "Service page rewrite - city sections, pricing, comparison table, schema on /tankless-water-heaters-utah/", "1 page", "12-16 hours"),
        ("Phase 3", "Week 5", "Cluster internal linking - build the funnel between all 8 pages per the Internal Linking tab", "8 pages", "4-6 hours"),
        ("Phase 4", "Week 6", "Consolidate duplicate comparison content - 301 redirect 2 weaker comparison pages to the strongest", "2 redirects", "2 hours"),
        ("Phase 5", "Weeks 7-12", "Monitor: position on 'tankless water heater' (target 3 from 5.1), CTR (target 0.5% from 0.03%), cluster click volume", "Ongoing", "30-day report"),
    ]
    for row in impl:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
