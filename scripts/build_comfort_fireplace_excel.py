"""Build the Comfort Solutions Fireplace Pages Strategy Excel deliverable.

Output: Clients/Comfort/Full SEO Audit/comfort_fireplace_pages_consolidation.xlsx
Tabs:
  1. Summary             - Cluster KPIs + the structural-not-missing finding
  2. The 42 Fireplace Pages - Complete inventory sorted by impressions
  3. Parent Page Decision - 3 competing parents side-by-side
  4. Repair Consolidation - 5 repair pages -> 2 canonical
  5. Hub-and-Spoke Architecture - Recommended structure
  6. Pages To Create     - 3 genuinely missing sub-pages
  7. Supporting Blogs    - 6 high-traffic blogs to link from
  8. Implementation Order- Phase-by-phase plan
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Clients" / "Comfort" / "Comfort Solutions - Content Audit Report Sheet.xlsx"
OUTPUT = ROOT / "Clients" / "Comfort" / "Full SEO Audit" / "comfort_fireplace_pages_consolidation.xlsx"


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
DECISION_FILL = PatternFill("solid", fgColor="2E7D32")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


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


def wrap(ws, start_row=2, wrap_cols: list[int] | None = None):
    """Apply wrap_text only to specific columns (1-indexed). All others stay single-line.

    If wrap_cols is None, no wrapping is applied. Pass e.g. [3, 5] to wrap only those columns.
    """
    if not wrap_cols:
        return
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            if cell.column in wrap_cols:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            else:
                cell.alignment = Alignment(wrap_text=False, vertical="center")


def main():
    src = openpyxl.load_workbook(SOURCE, data_only=True)
    page_audit_ws = src["Page-Level Audit"]
    rows = list(page_audit_ws.iter_rows(values_only=True))
    data = rows[1:]
    fp = [r for r in data if r[0] and "fireplace" in str(r[0]).lower()]

    wb = Workbook()

    # ---------- Summary ----------
    ws = wb.active
    ws.title = "Summary"
    total_imp = sum(r[15] or 0 for r in fp)
    total_clk = sum(r[14] or 0 for r in fp)
    summary = [
        ("Item", "Value", "Notes"),
        ("Task", "Create dedicated fireplace service pages", "Roadmap Item #15 (P2)"),
        ("Audit framing", "'Missing dedicated pages'", "Live verification: 42 fireplace pages already exist - structural problem not missing pages"),
        ("Total fireplace URLs", 42, "Per Comfort Content Audit Report"),
        ("Combined impressions (90d)", int(total_imp), ""),
        ("Combined clicks (90d)", int(total_clk), ""),
        ("Cluster CTR", f"{total_clk/total_imp*100:.2f}%" if total_imp else "n/a", ""),
        ("Top page (by imps)", "/smoke-in-your-eyes-check-the-fireplace-and-airflow/", "Blog post - 7,426 imps pos 3.5"),
        ("Top commercial page", "/fireplaces/", "1,477 imps pos 10.1"),
        ("Competing parent pages", 3, "/fireplaces/, /services/fireplace/, /fireplace-utah-homepage/"),
        ("Recommended canonical parent", "/services/fireplace/", "Has Breadcrumbs rich result, fits service hierarchy"),
        ("Pages to actually CREATE (net-new)", 3, "Installation, Inserts hub, Maintenance"),
        ("Pages to CONSOLIDATE", 7, "3 parent pages + 5 repair pages -> 2 canonical"),
        ("Pages to NOINDEX", 1, "/services-type/fireplace/ - empty category archive"),
        ("Fireplace pages with 0 imps", 13, "31% of cluster invisible to Google"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=80)

    # ---------- The 42 Fireplace Pages ----------
    ws = wb.create_sheet("The 42 Fireplace Pages")
    ws.append(
        [
            "URL",
            "Composite Score",
            "Grade",
            "Action (audit)",
            "Impressions (90d)",
            "Clicks (90d)",
            "Avg Position",
            "Word Count",
            "Indexed",
            "Type",
            "Recommendation",
        ]
    )
    # Categorize each
    def categorize(url):
        u = url.lower()
        if u in ('https://www.comfortsolutionsutah.com/fireplaces/',
                 'https://www.comfortsolutionsutah.com/services/fireplace/',
                 'https://www.comfortsolutionsutah.com/fireplace-utah-homepage/'):
            return 'COMPETING PARENT'
        if 'repair' in u or 'service-salt-lake' in u:
            return 'REPAIR (consolidate)'
        if '/coupons/' in u:
            return 'Coupon'
        if '/services-type/' in u:
            return 'Empty category archive (noindex)'
        if 'showroom' in u or 'gallery' in u or 'videos' in u:
            return 'Showroom/visual'
        if 'free-estimate' in u or 'specials' in u or 'reviews' in u or 'products' in u or 'blog-fireplace' in u or 'build-your' in u:
            return 'Brand/conversion asset'
        if 'sandy' in u or 'south-salt' in u or 'davis-county' in u or 'layton' in u or 'ogden' in u or 'park-city' in u or '/service-areas/' in u:
            return 'City-level service'
        if 'mantel' in u or 'electric-fireplaces' in u or 'modern-gas-fireplaces' in u or 'contemporary' in u or 'custom' in u or 'truflame' in u or 'traditional-gas' in u:
            return 'Product/style'
        if 'maintenance' in u or 'tune-up' in u or 'efficiency' in u:
            return 'Maintenance'
        if 'insert' in u and 'inserts-' not in u and 'sandy' not in u and 'south-salt' not in u and 'ogden' not in u:
            return 'Inserts'
        if 'smoke' in u or 'heat-producing' in u or 'how-a-fireplace' in u or 'keep-your-fireplace' in u:
            return 'Blog (high-traffic)'
        return 'Other'

    def recommend(url, action_audit):
        u = url.lower()
        if u == 'https://www.comfortsolutionsutah.com/services/fireplace/':
            return 'KEEP as canonical parent hub'
        if u == 'https://www.comfortsolutionsutah.com/fireplaces/':
            return 'DECISION - merge into /services/fireplace/ OR repurpose as showroom-led brand page'
        if u == 'https://www.comfortsolutionsutah.com/fireplace-utah-homepage/':
            return '301 to canonical parent - already de-indexed by Google'
        if u == 'https://www.comfortsolutionsutah.com/services-type/fireplace/':
            return 'NOINDEX - empty category archive'
        if 'fireplace-repair-salt-lake-city' in u:
            return 'KEEP as SLC city-level repair page (resolve user-canonical conflict)'
        if 'gas-fireplace-repair-services-in-salt-lake-city' in u:
            return '301 to /fireplace-repair-salt-lake-city/'
        if u == 'https://www.comfortsolutionsutah.com/fireplace-service-salt-lake-city/':
            return '301 to /fireplace-repair-salt-lake-city/'
        if u == 'https://www.comfortsolutionsutah.com/fireplace-repair-service/':
            return 'KEEP as statewide (Utah) repair hub - rename to /services/fireplace/repair/'
        if '/coupons/' in u and 'imps' not in u:
            return 'Consider consolidating into /specials-fireplace-utah/ if 0 traffic'
        return 'Refresh + link from canonical parent'

    fp_sorted = sorted(fp, key=lambda r: r[15] or 0, reverse=True)
    for r in fp_sorted:
        url = r[0] or ''
        ws.append([
            url,
            r[2] or 0,
            r[3] or '',
            r[10] or '',
            int(r[15] or 0),
            int(r[14] or 0),
            r[17] or '',
            int(r[22] or 0),
            'Yes' if r[39] else 'No',
            categorize(url),
            recommend(url, r[10] or ''),
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Parent Page Decision ----------
    ws = wb.create_sheet("Parent Page Decision")
    ws.append(["Signal", "/services/fireplace/", "/fireplaces/", "/fireplace-utah-homepage/"])
    parents = [
        ("HTTP status", "200", "200", "200"),
        ("Indexed in Google", "Yes (last crawled Apr 27)", "Yes (last crawled Apr 28)", "NO - Crawled, currently not indexed (last Dec 17, 2025)"),
        ("Title tag", "Fireplace - Comfort Solutions", "Fireplaces - Comfort Solutions", "Fireplace Utah Homepage - Comfort Solutions"),
        ("H1", "Fireplaces in Ogden and Salt Lake City, UT", "Utah's Best Choice For Fireplaces", "Utah's Premier Fireplace Showroom & Installation"),
        ("Composite score", "38.8 D", "40.4 C (highest of 3)", "28.2 D"),
        ("Word count", 1268, 1013, 698),
        ("Impressions (90d)", 985, 1477, 13),
        ("Avg position", 9.6, 10.1, ""),
        ("Breadcrumbs rich result", "Yes - active", "No", "No"),
        ("In sitemap", "Yes", "Yes", "Yes (but de-indexed)"),
        ("Recommendation", "RECOMMENDED canonical - has Breadcrumbs schema, fits /services/ hierarchy", "Alternative canonical - higher score + impressions, but no rich result", "301 to canonical - Google already chose to de-index"),
    ]
    for row in parents:
        ws.append(row)
    style_header(ws, decision=True)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Repair Consolidation ----------
    ws = wb.create_sheet("Repair Consolidation")
    ws.append(["URL", "Imps (90d)", "Score", "Top Query Winning", "Recommendation"])
    repair = [
        (
            "https://www.comfortsolutionsutah.com/fireplace-repair-salt-lake-city/",
            109,
            "36.2 D",
            "fireplace repair salt lake city - 69 imps pos 19.4",
            "KEEP as SLC city-level repair page (resolve user-canonical conflict)",
        ),
        (
            "https://www.comfortsolutionsutah.com/gas-fireplace-repair-services-in-salt-lake-city/",
            178,
            "32.7 D",
            "Fragmented across many gas-repair queries",
            "301 redirect to /fireplace-repair-salt-lake-city/",
        ),
        (
            "https://www.comfortsolutionsutah.com/fireplace-repair-service/",
            9,
            "35.1 D",
            "Catchall repair page - 1 click",
            "KEEP as statewide (Utah) repair hub - rename to /services/fireplace/repair/",
        ),
        (
            "https://www.comfortsolutionsutah.com/fireplace-service-salt-lake-city/",
            0,
            "30.6 D",
            "No traffic, content-thin (1,473 wc but 0 imps)",
            "301 redirect to /fireplace-repair-salt-lake-city/",
        ),
        (
            "https://www.comfortsolutionsutah.com/service-areas/salt-lake-city-utah/fireplace-repair/",
            "n/a",
            "n/a",
            "Listed as User Canonical of /fireplace-repair-salt-lake-city/ but Google ignored",
            "DECIDE - either make canonical (with 301 from older URL) or delete",
        ),
    ]
    for row in repair:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    wrap(ws)

    # ---------- Hub-and-Spoke Architecture ----------
    ws = wb.create_sheet("Hub-and-Spoke")
    ws.append(["Tier", "URL or Type", "Status", "Action"])
    arch = [
        ("HUB", "/services/fireplace/ (canonical parent)", "Exists - keep", "Make canonical parent. Absorb /fireplaces/ + /fireplace-utah-homepage/."),
        ("Sub-page (Product)", "/electric-fireplaces/", "Exists", "Refresh + link from hub"),
        ("Sub-page (Product)", "/modern-gas-fireplaces/", "Exists", "Refresh + link from hub"),
        ("Sub-page (Product)", "/contemporary-fireplaces/", "Exists", "Refresh + link from hub"),
        ("Sub-page (Product)", "/custom-fireplaces/", "Exists", "Refresh + link from hub"),
        ("Sub-page (Product)", "/fireplace-mantels/", "Exists", "Refresh + link from hub"),
        ("Sub-page (Product)", "/truflame-direct-vent-luxury-fireplaces/", "Exists", "Refresh + link from hub"),
        ("Sub-page (Product)", "/services/fireplace/inserts/", "DOES NOT EXIST - CREATE", "New - parent for city-level inserts pages"),
        ("Sub-page (Service)", "/services/fireplace/installation/", "DOES NOT EXIST - CREATE", "New - dedicated installation page"),
        ("Sub-page (Service)", "/services/fireplace/repair/", "Rename existing /fireplace-repair-service/", "Statewide (Utah) repair hub - anchored to Wasatch Front service area"),
        ("Sub-page (Service)", "/services/fireplace/maintenance/", "Rename or create", "Either rename /hvac-fireplace-maintenance/ or create new page"),
        ("Sub-page (Showroom)", "/showrooms-fireplace-utah/", "Exists", "Keep as showroom hub"),
        ("Sub-page (Showroom)", "/gallery-fireplace-utah/", "Exists - 0 imps", "Refresh with photos + link from showroom"),
        ("Sub-page (Showroom)", "/videos-fireplace-utah/", "Exists - flagged for consolidation", "Decision: consolidate or refresh"),
        ("City Service", "/service-areas/salt-lake-city-utah/fireplace-repair/", "Exists", "Resolve canonical conflict (see Repair Consolidation tab)"),
        ("City Service", "/service-areas/salt-lake-city-utah/fireplace-service/", "Exists", "Define role vs repair page"),
        ("City Service", "/service-areas/salt-lake-city-utah/gas-fireplace-repair/", "Exists", "Refresh"),
        ("City Service", "/service-areas/salt-lake-city-utah/traditional-gas-fireplaces/", "Exists", "Refresh"),
        ("City Service", "/service-areas/davis-county-utah/gas-fireplace/", "Exists", "Refresh"),
        ("City Service", "/service-areas/layton-utah/fireplace/", "Exists", "Refresh"),
        ("City Service", "/service-areas/ogden-utah/fireplace-inserts/", "Exists", "Refresh + link from /services/fireplace/inserts/ (after creation)"),
        ("City Service", "/service-areas/south-salt-lake-utah/electric-fireplace/", "Exists", "Refresh"),
        ("City Service", "/service-areas/south-salt-lake-utah/gas-fireplace-inserts/", "Exists", "Refresh"),
        ("Brand Asset", "/products-fireplace-utah/", "Exists - 22 imps", "Refresh"),
        ("Brand Asset", "/specials-fireplace-utah/", "Exists - 0 imps", "Consolidate 4 fireplace coupons here"),
        ("Brand Asset", "/reviews-fireplace-utah/", "Exists - 0 imps", "Refresh with current reviews"),
        ("Brand Asset", "/free-estimate-fireplace-utah/", "Exists - 0 imps", "Lead form - keep, link from all commercial pages"),
        ("NOINDEX", "/services-type/fireplace/", "Empty category archive", "Add noindex meta - it's a WordPress category page, not a service page"),
    ]
    for row in arch:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    wrap(ws)

    # ---------- Pages To Create ----------
    ws = wb.create_sheet("Pages To Create")
    ws.append(["URL", "Role", "Target Query Family", "Required Sections", "Word Count Target", "Internal Links Required"])
    create = [
        (
            "https://www.comfortsolutionsutah.com/services/fireplace/installation/",
            "Dedicated installation hub",
            "fireplace installation utah, fireplace installation near me, fireplace installation salt lake city, gas fireplace installation, electric fireplace installation",
            "What's involved / Gas vs electric installation differences / Permits & inspections in Utah / Cost ranges / Timeline / Brands installed (Napoleon, etc.) / Showroom CTA / FAQ",
            1500,
            "Hub /services/fireplace/, all product pages, showroom, free estimate form",
        ),
        (
            "https://www.comfortsolutionsutah.com/services/fireplace/inserts/",
            "Fireplace inserts product hub",
            "fireplace inserts, gas fireplace inserts, electric fireplace inserts, fireplace inserts near me, fireplace inserts utah",
            "What inserts are / Gas vs electric inserts / Energy efficiency / Sizing / Installation process / Cost / Brands / FAQ",
            1500,
            "Hub /services/fireplace/, all city-level inserts pages, /how-a-fireplace-insert-can-boost-home-heating-efficiency/ blog post",
        ),
        (
            "https://www.comfortsolutionsutah.com/services/fireplace/maintenance/",
            "Fireplace maintenance & tune-up",
            "fireplace tune-up, fireplace maintenance, gas fireplace cleaning, fireplace inspection, annual fireplace service",
            "Why annual maintenance / What's included / Pre-season tune-up / Cleaning frequency / Cost / Tune-up coupon CTA / FAQ",
            1200,
            "Hub /services/fireplace/, /smoke-in-your-eyes-check-the-fireplace-and-airflow/, /keep-your-fireplace-and-hvac-in-winter/ blog posts, tune-up coupon",
        ),
    ]
    for row in create:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Supporting Blogs ----------
    ws = wb.create_sheet("Supporting Blogs")
    ws.append(["Rank", "URL", "Imps (90d)", "Clicks", "Position", "Internal Link Target", "Why"])
    blogs = [
        (1, "https://www.comfortsolutionsutah.com/smoke-in-your-eyes-check-the-fireplace-and-airflow/", 7426, 14, 3.5, "Fireplace repair page", "Smoke = repair intent. Strongest blog in cluster - position 3.5."),
        (2, "https://www.comfortsolutionsutah.com/how-a-fireplace-insert-can-boost-home-heating-efficiency/", 2767, 5, 7.9, "Fireplace inserts hub (after creation)", "Direct intent match for inserts product hub."),
        (3, "https://www.comfortsolutionsutah.com/heat-producing-fireplace-decorative/", 1669, 12, 7.2, "Gas vs electric vs traditional product pages", "Comparison content - feeds product pages."),
        (4, "https://www.comfortsolutionsutah.com/keep-your-fireplace-and-hvac-in-winter/", 338, 2, 10.8, "Maintenance page + repair page", "Seasonal intent - links to both maintenance and repair."),
        (5, "https://www.comfortsolutionsutah.com/fireplace-maintenance-efficiency-saves-money-homeowners/", 70, 0, 12.7, "Maintenance page", "Direct match for maintenance hub."),
        (6, "https://www.comfortsolutionsutah.com/hvac-fireplace-maintenance/", 472, 0, 26.5, "Reframe as the maintenance page", "Currently positioned as service but operates as blog - clarify role."),
    ]
    for row in blogs:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    wrap(ws)

    # ---------- Implementation Order ----------
    ws = wb.create_sheet("Implementation Order")
    ws.append(["Phase", "Week", "Action", "Pages Affected", "Effort Estimate"])
    impl = [
        ("Phase 0", "Week 1", "Pick canonical parent (/services/fireplace/ recommended). Confirm URL pattern for new sub-pages. Verify Comfort offers each service at the level new pages would imply.", "Stakeholder decisions", "4-6 hrs"),
        ("Phase 1", "Week 2", "Consolidate parent pages: 301 /fireplace-utah-homepage/ to canonical (already de-indexed). 301 the non-chosen of /fireplaces/ vs /services/fireplace/. Submit URL Inspection.", "3 parent pages", "2-3 hrs"),
        ("Phase 2", "Weeks 3-4", "Consolidate repair cluster: pick statewide (Utah) repair hub canonical at /services/fireplace/repair/. 301 /gas-fireplace-repair-services-in-SLC/ and /fireplace-service-SLC/ to surviving /service-areas/salt-lake-city-utah/fireplace-repair/. Resolve user-canonical conflict. Build per-city repair spokes for cities with demand (Davis County, Sandy, Layton, South SL, Ogden) where pages don't already exist.", "5 repair pages -> hub + city spokes", "6-8 hrs"),
        ("Phase 3", "Weeks 5-6", "Create /services/fireplace/installation/, /services/fireplace/inserts/, /services/fireplace/maintenance/. Each needs ~1,500 words + schema.", "3 new pages", "16-20 hrs"),
        ("Phase 4", "Week 7", "Internal linking pass: hub-to-subs, subs-to-hub, top 5 blogs to commercial pages, city pages link up to the statewide hub.", "All cluster", "4-6 hrs"),
        ("Phase 5", "Week 8", "Noindex /services-type/fireplace/ empty category. Decide fate of /fireplace-utah-homepage/ (recommend 301). Review 4 fireplace coupons (consolidate into /specials-fireplace-utah/ if 0 traffic).", "Cleanup", "2-3 hrs"),
        ("Phase 6", "Weeks 9-12", "Monitor: position on 'fireplace' family on consolidated parent, position consolidation on consolidated repair cluster, CTR target 1%+ from 0.29% baseline, indexation of 3 new pages.", "All cluster", "Ongoing"),
    ]
    for row in impl:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    wrap(ws)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")
    print(f"  Total fireplace pages: {len(fp)}")
    print(f"  Total impressions: {int(total_imp)}")
    print(f"  Total clicks: {int(total_clk)}")


if __name__ == "__main__":
    main()
