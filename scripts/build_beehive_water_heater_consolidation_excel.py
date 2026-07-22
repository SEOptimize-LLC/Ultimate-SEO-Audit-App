"""Build the Beehive Water Heater Repair Consolidation Excel deliverable.

Output: Clients/Beehive/Full Site SEO Audit/beehive_water_heater_repair_consolidation.xlsx
Tabs:
  1. Summary             - The decision and the evidence behind it
  2. The Decision        - Side-by-side signal comparison of the two URLs
  3. Cluster Pages       - All water heater service pages with impressions/backlinks
  4. Cannibalized Queries- Water heater repair queries split across multiple pages
  5. Implementation Steps- 301 redirect plan + internal link cleanup
  6. Supporting Blogs    - Top 10 articles to refresh + 3 consolidation pairs
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
CLIENT_DIR = ROOT / "Clients" / "Beehive"
OUTPUT = CLIENT_DIR / "Full Site SEO Audit" / "beehive_water_heater_repair_consolidation.xlsx"


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


def wrap_data_rows(ws, start_row=2):
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def main():
    wb = Workbook()

    # ---------- Tab 1: Summary ----------
    ws = wb.active
    ws.title = "Summary"
    summary = [
        ("Item", "Value", "Notes"),
        ("Task", "Consolidate water heater repair duplicate pages", "Roadmap Item #7 (P1)"),
        ("Source audit", "Beehive Plumbing Full Site SEO Audit, Apr 8 2026", ""),
        ("Recommended action", "301 redirect /water-heater-repair/ -> /water-heater-repair-utah/", ""),
        ("Risk level", "Low", "Redirected URL has zero indexed traffic, zero backlinks"),
        ("Content similarity", "97%", "From near-duplicates report"),
        ("Both pages canonical to themselves", "Yes", "Confirmed live verification April 29, 2026"),
        ("Indexed: /water-heater-repair-utah/", "Yes", "Submitted and indexed (GSC URL Inspection)"),
        ("Indexed: /water-heater-repair/", "No", "Discovered, currently not indexed (GSC URL Inspection)"),
        ("Backlinks: /water-heater-repair-utah/", "14 from 8 referring domains", "Beehive Content Audit Sheet, Backlinks tab"),
        ("Backlinks: /water-heater-repair/", "0", "Not present in backlinks data"),
        ("Impressions (90 days): /water-heater-repair-utah/", 3785, "GSC search analytics"),
        ("Impressions (90 days): /water-heater-repair/", 0, "GSC search analytics"),
        ("Queries (90 days): /water-heater-repair-utah/", 145, ""),
        ("Queries (90 days): /water-heater-repair/", 0, ""),
        ("FAQ rich result on /water-heater-repair-utah/", "Active", "Detected in URL Inspection"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=70)

    # ---------- Tab 2: The Decision ----------
    ws = wb.create_sheet("The Decision")
    ws.append(["Signal", "/water-heater-repair-utah/", "/water-heater-repair/", "Winner"])
    decision = [
        ("Live HTTP status", "200 OK", "200 OK", "Tie"),
        ("Title tag", "Top Water Heater Repair in Salt Lake City - Fast and Reliable Service", "Top Water Heater Repair in Salt Lake City - Fast and Reliable Service (identical)", "Tie - identical"),
        ("H1", "Expert Water Heater Repair in Salt Lake City", "Expert Water Heater Repair in Salt Lake City (identical)", "Tie - identical"),
        ("Canonical tag", "Self-referencing (same URL)", "Self-referencing (same URL)", "Tie - both wrong"),
        ("Approximate word count", "12,381", "12,389", "Tie - 0.06% difference"),
        ("Indexed in Google", "Yes - submitted and indexed", "No - Discovered, currently not indexed", "/water-heater-repair-utah/"),
        ("Last crawled by Google", "2026-04-21", "Unknown", "/water-heater-repair-utah/"),
        ("Queries appearing for (90 days)", 145, 0, "/water-heater-repair-utah/"),
        ("Total impressions (90 days)", 3785, 0, "/water-heater-repair-utah/"),
        ("Backlinks", 14, 0, "/water-heater-repair-utah/"),
        ("Referring domains", 8, 0, "/water-heater-repair-utah/"),
        ("FAQ rich result enabled", "Yes", "No", "/water-heater-repair-utah/"),
        ("URL fits site URL pattern (-utah suffix)", "Yes - matches /water-heater-replacement-utah/, /water-heaters-utah/", "No - shorter form, outlier", "/water-heater-repair-utah/"),
        ("Final recommendation", "KEEP - this is the canonical", "REDIRECT - 301 to /water-heater-repair-utah/", ""),
    ]
    for row in decision:
        ws.append(row)
    style_header(ws, decision=True)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap_data_rows(ws)

    # ---------- Tab 3: Cluster Pages ----------
    ws = wb.create_sheet("Cluster Pages")
    ws.append(
        [
            "URL",
            "Live Status",
            "Indexed",
            "Word Count",
            "Internal Inlinks",
            "Backlinks",
            "Referring Domains",
            "Queries (90d)",
            "Impressions (90d)",
            "Role in Cluster",
        ]
    )
    cluster = [
        (
            "https://www.beehiveplumbing.com/water-heater-repair-utah/",
            "200",
            "Yes",
            1438,
            5,
            14,
            8,
            145,
            3785,
            "PRIMARY - Repair canonical (consolidate target)",
        ),
        (
            "https://www.beehiveplumbing.com/water-heater-repair/",
            "200",
            "No",
            1444,
            3,
            0,
            0,
            0,
            0,
            "DUPLICATE - 97% match - 301 to /water-heater-repair-utah/",
        ),
        (
            "https://www.beehiveplumbing.com/water-heater-installation-services-utah/",
            "200",
            "Yes",
            "(parses as 0)",
            0,
            9,
            5,
            581,
            686498,
            "Installation - currently capturing repair queries (separate optimization)",
        ),
        (
            "https://www.beehiveplumbing.com/water-heater-replacement-utah/",
            "200",
            "Yes",
            1209,
            4,
            4,
            4,
            27,
            497,
            "Replacement service",
        ),
        (
            "https://www.beehiveplumbing.com/water-heaters-utah/",
            "200",
            "Yes",
            449,
            130,
            26,
            8,
            57,
            441,
            "Cluster hub by inlinks - content-thin (449 words)",
        ),
        (
            "https://www.beehiveplumbing.com/tankless-water-heaters-utah/",
            "200",
            "Yes",
            2081,
            4,
            33,
            14,
            45,
            2851,
            "Tankless service - strongest in cluster by backlinks",
        ),
        (
            "https://www.beehiveplumbing.com/gas-water-heater-utah/",
            "200",
            "Yes",
            2081,
            1,
            18,
            5,
            83,
            1087,
            "Gas-specific service",
        ),
        (
            "https://www.beehiveplumbing.com/electric-water-heaters/",
            "200",
            "Yes",
            2067,
            1,
            14,
            2,
            53,
            646,
            "Electric-specific service",
        ),
        (
            "https://www.beehiveplumbing.com/commercial-water-heater-repair-salt-lake-city-utah/",
            "200",
            "Yes",
            2103,
            1,
            0,
            0,
            136,
            4101,
            "Commercial repair - high impressions, no backlinks",
        ),
        (
            "https://www.beehiveplumbing.com/commercial-water-heater-installation-utah/",
            "200",
            "Yes",
            1618,
            1,
            2,
            2,
            36,
            1229,
            "Commercial installation",
        ),
        (
            "https://www.beehiveplumbing.com/commercial-water-heater-replacement-salt-lake-city-utah/",
            "200",
            "Yes",
            1599,
            1,
            0,
            0,
            9,
            136,
            "Commercial replacement",
        ),
    ]
    for row in cluster:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 4: Cannibalized Queries ----------
    ws = wb.create_sheet("Cannibalized Queries")
    ws.append(["Query", "Page", "Impressions (28d)", "Position", "Cannibalization Note"])
    queries = [
        # Top queries split across multiple pages
        ("hot water heater repair near me", "https://www.beehiveplumbing.com/water-heater-installation-services-utah/", 172, 15.2, "Should land on repair page, lands on install"),
        ("hot water heater repair near me", "https://www.beehiveplumbing.com/water-heater-repair-utah/", 65, 44.6, "Correct destination but ranking lower"),
        ("hot water heater repair near me", "https://www.beehiveplumbing.com/plumbing-south-jordan-utah/", 31, 9.0, "Local plumbing page winning over service page"),
        ("hot water heater repair near me", "https://www.beehiveplumbing.com/plumbing-orem-ut/", 30, 15.6, "Local plumbing page in mix"),
        ("hot water heater repair near me", "https://www.beehiveplumbing.com/plumbing-draper-ut/", 27, 10.4, "Local plumbing page in mix"),

        ("salt lake city water heater repair", "https://www.beehiveplumbing.com/water-heater-installation-services-utah/", 110, 41.1, "Install page captures SLC repair query"),
        ("salt lake city water heater repair", "https://www.beehiveplumbing.com/water-heater-repair-utah/", 97, 57.6, "Correct URL but page 6 position"),
        ("salt lake city water heater repair", "https://www.beehiveplumbing.com/electric-water-heaters/", 93, 24.9, "Electric page captures generic SLC repair"),

        ("commercial water heater repair", "https://www.beehiveplumbing.com/commercial-water-heater-repair-salt-lake-city-utah/", 159, 17.4, "Correct destination - keep"),
        ("commercial water heater repair", "https://www.beehiveplumbing.com/commercial-water-heater-installation-utah/", 36, 28.5, "Install page splitting commercial repair query"),
        ("commercial water heater repair", "https://www.beehiveplumbing.com/water-heater-installation-services-utah/", 35, 18.1, "Install page splitting commercial repair query"),

        ("hot water heater repair", "https://www.beehiveplumbing.com/water-heater-repair-utah/", 58, 20.8, "Correct destination but page 2"),
        ("hot water heater repair", "https://www.beehiveplumbing.com/water-heater-installation-services-utah/", 10, 29.9, "Install page taking share"),

        ("emergency water heater repair", "https://www.beehiveplumbing.com/water-heater-repair-utah/", 56, 26.9, "Correct destination but page 3"),
        ("emergency water heater repair", "https://www.beehiveplumbing.com/water-heater-installation-services-utah/", 27, 15.1, "Install page outranks repair page"),
        ("emergency water heater repair", "https://www.beehiveplumbing.com/tankless-water-heaters-utah/", 13, 31.8, "Tankless page in mix"),

        ("hot water heater repair service near me", "https://www.beehiveplumbing.com/water-heater-installation-services-utah/", 46, 12.1, "Install page outranks repair page"),
        ("hot water heater repair service near me", "https://www.beehiveplumbing.com/water-heater-repair-utah/", 17, 35.9, "Repair page on page 4"),

        ("plumber for water heater repair", "https://www.beehiveplumbing.com/water-heater-installation-services-utah/", 33, 16.1, "Install page winning"),
        ("plumber for water heater repair", "https://www.beehiveplumbing.com/water-heater-repair-utah/", 26, 44.4, "Repair page well below"),
    ]
    for row in queries:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Tab 5: Implementation Steps ----------
    ws = wb.create_sheet("Implementation Steps")
    ws.append(["#", "Step", "Owner", "How", "Verification"])
    steps = [
        (
            1,
            "Add 301 redirect: /water-heater-repair/ -> /water-heater-repair-utah/",
            "Developer",
            "WordPress: Redirection plugin OR server-level (.htaccess for Apache, nginx config). Prefer server-level when available - faster, no PHP dependency.",
            "curl -I https://www.beehiveplumbing.com/water-heater-repair/ should return 301 with Location: header pointing to /water-heater-repair-utah/",
        ),
        (
            2,
            "Update internal links pointing to /water-heater-repair/",
            "Developer",
            "Search WordPress content + theme for href=\"/water-heater-repair/\" or full URL. Update to /water-heater-repair-utah/. Check: main nav, footer, /water-heaters-utah/, /services/water-heater/, blog posts, local pages (Lehi, Sandy, West Jordan, South Jordan, Park City, Draper).",
            "Re-crawl with Screaming Frog after fix - should find zero internal links pointing to /water-heater-repair/",
        ),
        (
            3,
            "Submit URL Inspection request in GSC",
            "SEO",
            "GSC -> URL Inspection -> /water-heater-repair-utah/ -> Request Indexing. This forces a fresh crawl after the redirect.",
            "Check GSC URL Inspection 7-14 days later - last crawl date should update",
        ),
        (
            4,
            "Resubmit XML sitemap",
            "SEO",
            "Confirm sitemap does NOT include /water-heater-repair/. Submit fresh sitemap via GSC.",
            "GSC -> Sitemaps -> sitemap shows updated submission date",
        ),
        (
            5,
            "Update internal links FROM the supporting blogs TO /water-heater-repair-utah/",
            "Content / SEO",
            "10 blog posts identified in Supporting Blogs tab. Add 1-2 contextual links per post pointing to the consolidated page.",
            "Spot check 3-5 blog posts after update to confirm links are live",
        ),
        (
            6,
            "Monitor for 30 days",
            "SEO",
            "Track GSC: position movement on top 10 water heater repair queries, watch for any spike in 404s referencing the old URL, compare CTR before/after.",
            "30-day report comparing Apr 1-29 baseline vs May 30-Jun 28 post-redirect",
        ),
        (
            7,
            "Optional follow-up: rewrite the surviving page",
            "Content",
            "Once the duplicate is gone, the canonical /water-heater-repair-utah/ should be rewritten to capture the repair queries currently leaking to /water-heater-installation-services-utah/. Definition-first opening, repair-specific H2s, FAQ schema.",
            "Position improvement on emergency hot water heater repair, salt lake city water heater repair, hot water heater repair near me",
        ),
    ]
    for row in steps:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap_data_rows(ws)

    # ---------- Tab 6: Supporting Blogs ----------
    ws = wb.create_sheet("Supporting Blogs")
    ws.append(["Rank", "URL", "Impressions (90d)", "Clicks", "Why include"])
    blogs = [
        (1, "https://www.beehiveplumbing.com/is-it-worth-getting-a-tankless-water-heater/", 350454, 107, "Site #1 traffic blog. Add link to repair page for users whose tankless unit fails."),
        (2, "https://www.beehiveplumbing.com/things-you-should-know-when-switching-to-a-tankless-water-heater/", 26483, 2, "High-impression decision-stage content. Add repair page link."),
        (3, "https://www.beehiveplumbing.com/how-long-should-a-water-heater-last-understanding-the-lifespan-of-your-unit/", 6891, 0, "High-intent for 'should I repair or replace' decisions. Direct funnel into repair and replacement."),
        (4, "https://www.beehiveplumbing.com/conventional-tank-water-heaters-vs-tankless-water-heaters/", 4439, 2, "Comparison content. CTA to repair page for users keeping current unit."),
        (5, "https://www.beehiveplumbing.com/do-you-need-a-water-heater-expansion-tank/", 2983, 1, "Technical/troubleshooting. Direct repair-intent connection."),
        (6, "https://www.beehiveplumbing.com/steps-homeowners-should-take-when-they-notice-their-water-heater-is-leaking-and-may-require-a-water-heater-repair/", 2161, 0, "Highest-intent emergency repair article. Cornerstone supporting blog for the consolidated page."),
        (7, "https://www.beehiveplumbing.com/can-i-install-a-hot-water-heater-by-myself/", 1469, 1, "Reframes DIY users into call-a-pro funnel. Strong CTA candidate."),
        (8, "https://www.beehiveplumbing.com/why-is-my-tankless-water-heater-making-beeping-sounds/", 1120, 2, "Specific troubleshooting. Direct symptom-to-repair connection."),
        (9, "https://www.beehiveplumbing.com/how-long-do-water-heaters-last-everything-you-need-to-know/", 1109, 0, "Lifespan content overlapping #3 - consider consolidating these two."),
        (10, "https://www.beehiveplumbing.com/5-water-heater-repair-scenarios-that-lead-to-your-hot-water-running-out-too-quickly/", 455, 1, "Direct match on 'water heater repair' phrasing. Cornerstone supporting article."),
    ]
    for row in blogs:
        ws.append(row)

    # Add separator + consolidation pairs
    ws.append(["", "", "", "", ""])
    ws.append(["CONSOLIDATION PAIRS", "Pages covering the same intent - keep stronger, 301 weaker", "", "", ""])
    pairs = [
        (
            "Pair A",
            "/how-long-should-a-water-heater-last-understanding-the-lifespan-of-your-unit/ (6,891 imp) vs /how-long-do-water-heaters-last-everything-you-need-to-know/ (1,109 imp)",
            "",
            "",
            "Keep the 6,891 impression version, 301 the smaller one",
        ),
        (
            "Pair B",
            "/comparing-traditional-tankless-water-heaters/ (1 imp) vs /conventional-tank-water-heaters-vs-tankless-water-heaters/ (4,439 imp) vs /tankless-water-heater-vs-tank-whats-the-difference/ (87 imp)",
            "",
            "",
            "Keep the 4,439 impression version, 301 the other two",
        ),
    ]
    for row in pairs:
        ws.append(row)

    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    wrap_data_rows(ws)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
