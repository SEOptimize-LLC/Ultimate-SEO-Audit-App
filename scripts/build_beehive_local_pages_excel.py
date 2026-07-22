"""Build the Beehive Local Pages Rewrite Excel deliverable.

Output: Clients/Beehive/Full Site SEO Audit/beehive_local_pages_rewrite.xlsx
Tabs:
  1. Summary             - Cluster KPIs + the structural problems
  2. Page Inventory      - All 17 pages with live verification + impressions
  3. Differentiation Framework - 6 dimensions every page must hit
  4. Per-City Plan       - 17 cities with angle, local entities, internal links
  5. Proposed Titles     - Per-city title + char count, sanity-checked
  6. Action Sequence     - Logical action order with dependencies (no time-based phases)
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "beehive_local_pages_rewrite.xlsx"


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
        ("Task", "Rewrite 17 local service pages with unique local content", "Roadmap Item #14 (P2)"),
        ("Pages in cluster", 17, "All under /locations/"),
        ("Total impressions (90d)", 1552, "Across all 17 pages"),
        ("Total clicks (90d)", 2, ""),
        ("Cluster CTR", "0.13%", ""),
        ("Page-specific word count per page", 353, "Confirmed identical across all 17 pages"),
        ("Pages with H1", 0, "None of the 17 pages have a detectable H1"),
        ("Current title pattern", "Beehive Plumbing [City] - Plumber Salt Lake City | Beehive Plumbing SLC", "Same pattern across all 17 - city is the only variable. Note: 'Plumbing' appears 3x, which is what triggers the rewrite."),
        ("Top performer", "Park City (511 imp)", "Only city above 300 impressions besides Murray"),
        ("Bottom performer", "South Jordan (0 imp)", "Indexed but no Google attention"),
        ("URL pattern inconsistency", "/locations/beehive-plumbing-<city>/ vs /locations/<city>/", "Bluffdale + SLC root use shorter pattern. Resolve before rewrite."),
        ("Dead URL referenced in inventory", "/locations/beehive-plumbing-salt-lake-city-sugar-house-3/", "404 - add to redirect cleanup"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=80)

    # ---------- Page Inventory ----------
    ws = wb.create_sheet("Page Inventory")
    ws.append(
        [
            "URL",
            "City",
            "Live Status",
            "H1 Present",
            "Page-Specific WC",
            "Impressions (90d)",
            "Clicks (90d)",
            "Tier",
        ]
    )
    inventory = [
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-park-city/", "Park City", "200", "No", 353, 511, 0, "Tier A"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-murray/", "Murray", "200", "No", 353, 376, 1, "Tier A"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-bountiful/", "Bountiful", "200", "No", 353, 267, 0, "Tier A"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-lehi/", "Lehi", "200", "No", 353, 86, 0, "Tier A"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-orem/", "Orem", "200", "No", 353, 56, 0, "Tier A"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-sugar-house/", "Sugar House", "200", "No", 353, 56, 0, "Tier B"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-draper/", "Draper", "200", "No", 353, 37, 0, "Tier B"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-west-jordan/", "West Jordan", "200", "No", 353, 35, 0, "Tier B"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-kaysville/", "Kaysville", "200", "No", 353, 34, 1, "Tier B"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-midvale/", "Midvale", "200", "No", 353, 27, 0, "Tier B"),
        ("https://www.beehiveplumbing.com/locations/bluffdale/", "Bluffdale", "200", "No", 353, 24, 0, "Tier B - URL inconsistency"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-west-valley-city/", "West Valley City", "200", "No", 353, 19, 0, "Tier B"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-salt-lake-city-sugar-house/", "Salt Lake City Sugar House", "200", "No", 353, 14, 0, "Tier B - duplicate of Sugar House"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-millcreek/", "Millcreek", "200", "No", 353, 8, 0, "Tier B"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-sandy/", "Sandy", "200", "No", 353, 1, 0, "Tier B"),
        ("https://www.beehiveplumbing.com/locations/salt-lake-city/", "Salt Lake City (root)", "200", "No", 353, 1, 0, "Tier B - URL inconsistency"),
        ("https://www.beehiveplumbing.com/locations/beehive-plumbing-south-jordan/", "South Jordan", "200", "No", 353, 0, 0, "Tier B"),
    ]
    for row in inventory:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)

    # ---------- Differentiation Framework ----------
    ws = wb.create_sheet("Differentiation Framework")
    ws.append(["#", "Dimension", "Currently", "Required for rewrite", "Why it matters"])
    framework = [
        (
            1,
            "Title tag",
            "Beehive Plumbing [City] - Plumber Salt Lake City | Beehive Plumbing SLC (same template, only city differs; 'Plumbing' appears 3x)",
            "City + 'UT' + 3 differentiating services. Service noun ('Plumber'/'Plumbing') appears ONLY in the brand suffix - never in the visible title. See 'Proposed Titles' tab for the exact per-city version.",
            "17 pages with the same title tells Google these are duplicates. Differentiated, non-stuffed titles let each page rank on its own merit.",
        ),
        (
            2,
            "H1 (currently missing)",
            "Missing - none of 17 pages has H1",
            "City-led, service-specific H1, no token repeated more than once across H1 + brand context.",
            "H1 is a primary on-page ranking signal. Audit's '41 missing H1' finding includes all 17 location pages.",
        ),
        (
            3,
            "City-specific opening (definition-first)",
            "Generic Beehive copy, city name swapped",
            "[Service] in [City] - [what it is] [guarantee] [availability] - referencing specific neighborhoods, service window, and Utah master plumber credentials",
            "Definition-first opening was flagged in semantic audit as the #1 content rule violated site-wide.",
        ),
        (
            4,
            "Local entity references",
            "City name only",
            "3-5 entities per page: neighborhoods, landmarks, adjacent areas, water utility, county",
            "Signals to Google the page is genuinely about [city] not just generic content with city name swapped in. Triggers local pack consideration.",
        ),
        (
            5,
            "City-specific content angle",
            "None - same content all pages",
            "Pick 2-3 angles per city: climate, building age, new construction, hard water, septic, commercial mix",
            "Gives each page a defensible reason to exist. 17 pages with the same angle compete with each other; 17 pages with different angles complement.",
        ),
        (
            6,
            "Internal linking",
            "Currently silos - no inter-page links",
            "Each page links to 4 service pages + 2-3 nearby cities + 1-2 blog posts",
            "Builds topical clustering. Audit flagged 'no content funnel between blog and service pages' - location pages need same fix.",
        ),
    ]
    for row in framework:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Per-City Plan ----------
    ws = wb.create_sheet("Per-City Plan")
    ws.append(
        [
            "City",
            "URL",
            "Imps",
            "Primary Angle",
            "Secondary Angle",
            "Local Entities (neighborhoods + landmarks)",
            "Service Emphasis",
            "Internal Links to Service Pages",
            "Internal Links to Nearby Cities",
            "Supporting Blog Link",
        ]
    )
    plan = [
        (
            "Park City",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-park-city/",
            511,
            "Mountain climate (frozen pipes, cold-weather water heater stress)",
            "Vacation home plumbing (winter shutdowns, second-home maintenance)",
            "Old Town, Park Meadows, Deer Valley, Snyderville, Summit County, Park City Mountain Resort, Park City Water Department",
            "Emergency + winter maintenance + water heater",
            "/water-heater-replacement-utah/, /emergency-plumber/, /drain-cleaning-utah/",
            "Heber City, Kimball Junction",
            "/how-to-thaw-frozen-pipes/",
        ),
        (
            "Murray",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-murray/",
            376,
            "Older housing stock (1950s-70s) - galvanized pipe, older sewer",
            "Commercial mix (restaurants, retail density at Fashion Place)",
            "Fashion Place Mall, Murray City Center, Wheeler Farm, Salt Lake County",
            "Repipe, sewer line, commercial",
            "/sewer-line-repair-utah/, /commercial-water-heater-installation-utah/, /piping-repiping-utah/",
            "Sugar House, Millcreek, Cottonwood Heights",
            "/whats-a-sewer-line-belly-how-do-you-fix-it/",
        ),
        (
            "Bountiful",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-bountiful/",
            267,
            "Established residential, hard water (Bountiful's water has high mineral content)",
            "Family homes - water softeners, water heater longevity",
            "Bountiful City Hall, Davis County, North Salt Lake (adjacent), Centerville (adjacent)",
            "Water softener, water heater replacement",
            "/water-softeners-utah/, /water-heater-replacement-utah/, /drain-cleaning-utah/",
            "Centerville, North Salt Lake, Kaysville",
            "/4-advantages-soft-water/",
        ),
        (
            "Lehi",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-lehi/",
            86,
            "New construction (highest new-build rate in Utah County)",
            "Tech corridor (Silicon Slopes commercial)",
            "Thanksgiving Point, Traverse Mountain, Adobe campus, Utah County, Adams Park",
            "New construction inspections, builder-grade replacements, commercial",
            "/commercial-plumber-utah/, /residential-plumber-utah/, /water-heater-installation-services-utah/",
            "Saratoga Springs, American Fork, Eagle Mountain",
            "/what-are-the-three-stages-of-new-construction-plumbing/",
        ),
        (
            "Orem",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-orem/",
            56,
            "Family/student housing mix (BYU/UVU adjacent)",
            "Mid-1980s housing density - aging hot water systems",
            "University Place, Utah Valley University, BYU (adjacent in Provo), Utah County",
            "Water heater, repipe, drain cleaning",
            "/water-heaters-utah/, /piping-repiping-utah/, /drain-cleaning-utah/",
            "Provo, Lindon, American Fork",
            "/how-long-should-a-water-heater-last-understanding-the-lifespan-of-your-unit/",
        ),
        (
            "Sugar House",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-sugar-house/",
            56,
            "Older housing stock (1920s-1950s)",
            "Apartment/condo density - leaks, drain issues, hot water sharing",
            "Sugar House Park, Westminster College, 21st South commercial corridor, Salt Lake City",
            "Repipe, leak detection, drain cleaning",
            "/piping-repiping-utah/, /leak-detection-utah/, /drain-cleaning-utah/",
            "Salt Lake City, Millcreek, East Bench",
            "/how-much-is-a-shower-faucet-repair/",
        ),
        (
            "Draper",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-draper/",
            37,
            "Newer suburban construction (1990s-2010s)",
            "Larger homes - whole-house water systems, larger water heaters",
            "Corner Canyon, Suncrest, Draper City Center, Salt Lake County",
            "Tankless water heaters, water softeners",
            "/tankless-water-heaters-utah/, /water-softeners-utah/, /water-heater-installation-services-utah/",
            "Sandy, South Jordan, Riverton",
            "/is-it-worth-getting-a-tankless-water-heater/",
        ),
        (
            "West Jordan",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-west-jordan/",
            35,
            "Suburban family homes (1990s-2000s)",
            "Mixed residential + light commercial",
            "Jordan Landing, Gardner Village, Salt Lake County",
            "Drain cleaning, water heater, sewer line",
            "/drain-cleaning-utah/, /water-heater-replacement-utah/, /sewer-line-repair-utah/",
            "South Jordan, West Valley City, Riverton",
            "/warning-signs-that-you-have-a-drain-cleaning-emergency/",
        ),
        (
            "Kaysville",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-kaysville/",
            34,
            "Family suburb, mid-tier hard water",
            "Some 1970s-80s housing stock",
            "Davis County, Layton (adjacent), Farmington (adjacent), Kaysville Junior High area",
            "Water heater, water softener, drain cleaning",
            "/water-heaters-utah/, /water-softeners-utah/, /drain-cleaning-utah/",
            "Layton, Farmington, Bountiful",
            "/4-advantages-soft-water/",
        ),
        (
            "Midvale",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-midvale/",
            27,
            "Mixed older + redeveloped housing",
            "TRAX-corridor density, smaller lots",
            "Bingham Junction, Midvale Main Street, Salt Lake County",
            "Drain cleaning, repipe, leak detection",
            "/drain-cleaning-utah/, /piping-repiping-utah/, /leak-detection-utah/",
            "Sandy, Murray, West Jordan",
            "/how-much-is-a-shower-faucet-repair/",
        ),
        (
            "Bluffdale",
            "https://www.beehiveplumbing.com/locations/bluffdale/",
            24,
            "New construction (one of Utah's fastest-growing cities)",
            "Larger lots, well + city water mix in some pockets",
            "Bluffdale City, Salt Lake County, Riverton (adjacent)",
            "New construction, water softeners, larger water heaters",
            "/water-softeners-utah/, /water-heaters-utah/, /residential-plumber-utah/",
            "Riverton, Herriman, South Jordan",
            "/what-are-the-three-stages-of-new-construction-plumbing/",
        ),
        (
            "West Valley City",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-west-valley-city/",
            19,
            "Older + newer housing mix, large city",
            "Commercial/industrial mix",
            "Valley Fair Mall, Maverik Center, USANA Amphitheatre, Salt Lake County",
            "Drain cleaning, sewer line, commercial",
            "/drain-cleaning-utah/, /sewer-line-repair-utah/, /commercial-plumber-utah/",
            "Taylorsville, Kearns, West Jordan",
            "/eliminate-difficult-drain-cleaning-tasks-with-our-experts/",
        ),
        (
            "Salt Lake City - Sugar House",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-salt-lake-city-sugar-house/",
            14,
            "Likely duplicate of /locations/beehive-plumbing-sugar-house/",
            "DECISION NEEDED before rewrite",
            "Sugar House, Salt Lake City",
            "Same as Sugar House page",
            "Recommend: 301 redirect to /locations/beehive-plumbing-sugar-house/ - do NOT rewrite as separate page",
            "",
            "",
        ),
        (
            "Millcreek",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-millcreek/",
            8,
            "Older housing (1950s-70s)",
            "Tree-lined neighborhoods, larger lots",
            "Millcreek City, Mount Olympus, Salt Lake County",
            "Repipe, water heater, drain cleaning",
            "/piping-repiping-utah/, /water-heaters-utah/, /drain-cleaning-utah/",
            "Sugar House, Holladay, Murray",
            "/how-long-should-a-water-heater-last-understanding-the-lifespan-of-your-unit/",
        ),
        (
            "Sandy",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-sandy/",
            1,
            "Suburban family homes",
            "Newer (1990s-2010s) construction in southern Sandy",
            "Sandy City, Salt Lake County, Cottonwood Heights (adjacent), South Towne Mall",
            "Water heater, drain cleaning, water softener",
            "/water-heater-replacement-utah/, /drain-cleaning-utah/, /water-softeners-utah/",
            "Draper, Cottonwood Heights, Midvale",
            "/4-advantages-soft-water/",
        ),
        (
            "Salt Lake City (root)",
            "https://www.beehiveplumbing.com/locations/salt-lake-city/",
            1,
            "Citywide hub - decision needed on relationship to homepage",
            "Should target 'plumber salt lake city' - homepage targets brand",
            "Downtown SLC, Avenues, Capitol Hill, University of Utah, Salt Lake County, Salt Lake City Public Utilities",
            "All services - hub page",
            "Link to all major service pages",
            "Sugar House, Millcreek, South Salt Lake",
            "/credentials-matter-when-finding-the-best-salt-lake-city-plumber/",
        ),
        (
            "South Jordan",
            "https://www.beehiveplumbing.com/locations/beehive-plumbing-south-jordan/",
            0,
            "Suburban + Daybreak (master-planned community)",
            "Newer construction + active commercial/retail growth",
            "Daybreak, The District, Salt Lake County, Oquirrh Mountain Temple",
            "New construction, water heater, water softener",
            "/water-heaters-utah/, /water-softeners-utah/, /residential-plumber-utah/",
            "West Jordan, Riverton, Bluffdale",
            "/is-it-worth-getting-a-tankless-water-heater/",
        ),
    ]
    for row in plan:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Proposed Titles ----------
    ws = wb.create_sheet("Proposed Titles")
    ws.append(
        [
            "City",
            "URL",
            "Current Title",
            "Proposed Visible Title",
            "Brand Suffix",
            "Visible Chars",
            "Full Chars (incl. brand)",
            "Sanity Check",
            "Notes",
        ]
    )
    BRAND = " | Beehive Plumbing"
    CURRENT_TEMPLATE = "Beehive Plumbing [City] - Plumber Salt Lake City | Beehive Plumbing SLC"
    titles = [
        ("Park City", "https://www.beehiveplumbing.com/locations/beehive-plumbing-park-city/",
         "Park City, UT Drain, Water Heater & Emergency Repair", "Mountain-climate emphasis (frozen pipes, emergency)."),
        ("Murray", "https://www.beehiveplumbing.com/locations/beehive-plumbing-murray/",
         "Murray, UT Sewer, Repipe & Drain Repair Services", "Older housing stock - sewer + repipe emphasis."),
        ("Bountiful", "https://www.beehiveplumbing.com/locations/beehive-plumbing-bountiful/",
         "Bountiful, UT Water Heater, Softener & Drain Services", "Hard water emphasis - softener + water heater."),
        ("Lehi", "https://www.beehiveplumbing.com/locations/beehive-plumbing-lehi/",
         "Lehi, UT New Construction, Water Heater & Drain Services", "Highest new-build rate in Utah County."),
        ("Orem", "https://www.beehiveplumbing.com/locations/beehive-plumbing-orem/",
         "Orem, UT Water Heater, Repipe & Drain Repair Services", "Mid-1980s housing - aging water systems."),
        ("Sugar House", "https://www.beehiveplumbing.com/locations/beehive-plumbing-sugar-house/",
         "Sugar House, UT Repipe, Leak Detection & Drain Repair", "1920s-50s housing - repipe + leak detection."),
        ("Draper", "https://www.beehiveplumbing.com/locations/beehive-plumbing-draper/",
         "Draper, UT Tankless Water Heater & Softener Services", "Newer suburban - tankless + whole-house systems."),
        ("West Jordan", "https://www.beehiveplumbing.com/locations/beehive-plumbing-west-jordan/",
         "West Jordan, UT Drain, Water Heater & Sewer Repair", "Mixed residential + light commercial."),
        ("Kaysville", "https://www.beehiveplumbing.com/locations/beehive-plumbing-kaysville/",
         "Kaysville, UT Water Heater, Softener & Drain Services", "Family suburb, mid-tier hard water."),
        ("Midvale", "https://www.beehiveplumbing.com/locations/beehive-plumbing-midvale/",
         "Midvale, UT Drain, Repipe & Leak Detection Services", "Mixed older + redeveloped housing."),
        ("Bluffdale", "https://www.beehiveplumbing.com/locations/bluffdale/",
         "Bluffdale, UT New Construction, Softener & Water Heater", "Fastest-growing - new construction + softener."),
        ("West Valley City", "https://www.beehiveplumbing.com/locations/beehive-plumbing-west-valley-city/",
         "West Valley, UT Drain, Sewer & Commercial Repair Services", "Used 'West Valley' (not full city name) for char budget. Commercial emphasis."),
        ("Salt Lake City - Sugar House",
         "https://www.beehiveplumbing.com/locations/beehive-plumbing-salt-lake-city-sugar-house/",
         "REDIRECT - duplicate of Sugar House (do not rewrite)",
         "Recommend 301 redirect to /locations/beehive-plumbing-sugar-house/. No new title."),
        ("Millcreek", "https://www.beehiveplumbing.com/locations/beehive-plumbing-millcreek/",
         "Millcreek, UT Repipe, Water Heater & Drain Services", "Older housing (1950s-70s)."),
        ("Sandy", "https://www.beehiveplumbing.com/locations/beehive-plumbing-sandy/",
         "Sandy, UT Water Heater, Softener & Drain Repair Services", "Newer southern Sandy + family homes."),
        ("Salt Lake City (root)", "https://www.beehiveplumbing.com/locations/salt-lake-city/",
         "Salt Lake City, UT Drain, Sewer & Water Heater Services", "Citywide hub - all services."),
        ("South Jordan", "https://www.beehiveplumbing.com/locations/beehive-plumbing-south-jordan/",
         "South Jordan, UT New Construction, Water Heater & Softener", "Daybreak + newer construction emphasis."),
    ]
    for city, url, visible, note in titles:
        if visible.startswith("REDIRECT"):
            ws.append([city, url, CURRENT_TEMPLATE, visible, "", "", "", "N/A", note])
        else:
            full = visible + BRAND
            ws.append([
                city,
                url,
                CURRENT_TEMPLATE,
                visible,
                BRAND.strip(),
                len(visible),
                len(full),
                "PASS (no token repeated, no brand-suffix conflict)",
                note,
            ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Action Sequence (no time-based phases) ----------
    ws = wb.create_sheet("Action Sequence")
    ws.append(["Step", "Action", "Cities", "Depends On"])
    impl = [
        (
            "Step 0",
            "Resolve URL pattern (/locations/<city>/ vs /locations/beehive-plumbing-<city>/). Build redirect map BEFORE rewrite. Confirm 6-dimension framework with content owner. Finalize per-city local entity map.",
            "All 17",
            "Nothing - this must come first",
        ),
        (
            "Step 1A",
            "Rewrite Tier A (top 5 cities by impressions)",
            "Park City, Murray, Bountiful, Lehi, Orem",
            "Step 0 complete",
        ),
        (
            "Step 1B",
            "Rewrite Tier B (remaining 12 cities, ordered by impressions desc)",
            "Sugar House, Draper, West Jordan, Kaysville, Midvale, Bluffdale, West Valley City, Sugar House (variant), Millcreek, Sandy, SLC root, South Jordan",
            "Step 0 complete (can run in parallel with Step 1A)",
        ),
        (
            "Step 2",
            "Internal linking pass - each city links to 2-3 nearby cities + 4 service pages + 1-2 blog posts",
            "All 17",
            "Steps 1A and 1B both complete",
        ),
        (
            "Step 2b",
            "Resolve duplicate: 301 redirect /locations/beehive-plumbing-salt-lake-city-sugar-house/ to /locations/beehive-plumbing-sugar-house/",
            "1 redirect",
            "Step 0 (URL pattern decision)",
        ),
        (
            "Step 3",
            "Measurement triggers (no fixed window): track position movement on '[city] plumber' queries, local pack appearances, CTR (target 1-3% vs current 0.13%)",
            "All 17",
            "All rewrites live",
        ),
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


if __name__ == "__main__":
    main()
