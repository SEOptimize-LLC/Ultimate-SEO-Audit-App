"""Build Comfort Solutions truncated titles shortening plan."""
import pandas as pd
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Comfort/Full SEO Audit/"
out = base + "comfort_truncated_titles_plan.xlsx"

df = pd.read_excel(base + "truncated_titles.xlsx")


# Classification
def classify(url):
    u = url.lower()
    if "/coupons/" in u:
        return "Coupon (NOINDEX)"
    if "/services-type/" in u or "/testimonials/" in u:
        return "WP Archive (NOINDEX)"
    if "/category/" in u:
        return "Category Archive (NOINDEX)"
    if "brocolli" in u or "home-elementor" in u:
        return "Test Page (DELETE)"
    if "homeshow" in u:
        return "Event Page (NOINDEX)"
    if "-ppc-" in u:
        return "PPC Landing (NOINDEX)"
    if u.count("/") <= 4 and "/services/" in u:
        return "Main Service Page"
    if "/services/" in u:
        return "Service Page"
    # City-specific slugs w/o /services/ prefix
    cities = ["park-city", "sandy", "ogden", "orem", "lehi", "davis-county",
              "salt-lake-city", "south-salt-lake", "layton", "draper", "millville"]
    if any(c in u for c in cities):
        return "City Service Page"
    return "Blog Post"


df["Classification"] = df["Address"].apply(classify)


# =========================================================================
# Recommended shortened titles
# =========================================================================
# Rules:
# - Max 60 chars (stay under SERP truncation point)
# - Remove redundant " - Comfort Solutions" suffix where not fitting
# - Remove modality ("Top", "Best", "Reliable", "Expert") per semantic audit rules
# - Keep primary keyword + location where applicable
# - For blog posts: keep topic focus, drop brand suffix if over limit
# =========================================================================

recommendations = {
    # === MAIN SERVICE HUBS (shallow /services/ paths) ===
    "/services/hvac-systems/furnace-replacement-upgrade/":
        "Furnace Replacement & Upgrade | Sandy, Ogden, SLC",
    "/services/hvac-systems/heating/":
        "Heating Services | Sandy, Ogden & Salt Lake City",
    "/services/hvac-systems/furnace-repair-service/":
        "Furnace Repair & Service | Sandy, Ogden, SLC",
    "/services/hvac-systems/ac-upgrade-replacement/":
        "AC Upgrade & Replacement | Sandy, Ogden, SLC",
    "/services/hvac-systems/air-conditioning/":
        "AC Services | Sandy, Ogden & Salt Lake City",
    "/services/hvac-systems/ac-repair-service/":
        "AC Repair | Sandy, Ogden & Salt Lake City",

    # === CITY SERVICE PAGES (furnace repair/install/tune-up by city) ===
    "/expert-ac-repair-davis-county/":
        "AC Repair in Davis County, Utah | Comfort Solutions",
    "/furnace-installation-park-city/":
        "Furnace Installation in Park City, Utah",
    "/electric-fireplace-south-salt-lake-city/":
        "Electric Fireplace in South Salt Lake City, Utah",
    "/furnace-repair-sandy/":
        "Furnace Repair in Sandy, Utah | Comfort Solutions",
    "/furnace-installation-services-in-sandy/":
        "Furnace Installation in Sandy, Utah",
    "/outdoor-fireplace-contractor-in-sandy/":
        "Outdoor Fireplace Contractor in Sandy, Utah",
    "/emergency-furnace-repair-salt-lake-city/":
        "Emergency Furnace Repair in Salt Lake City",
    "/furnace-installation-services-in-salt-lake-city/":
        "Furnace Installation in Salt Lake City, Utah",
    "/furnace-repair-services-in-ogden/":
        "Furnace Repair in Ogden, Utah | Comfort Solutions",
    "/gas-fireplace-inserts-in-south-salt-lake-city/":
        "Gas Fireplace Inserts in South Salt Lake City",
    "/furnace-repair-services-in-orem/":
        "Furnace Repair in Orem, Utah | Comfort Solutions",
    "/fireplace-inserts-contractor-in-ogden/":
        "Fireplace Inserts Contractor in Ogden, Utah",
    "/fireplace-contractor-in-layton/":
        "Fireplace Contractor in Layton, Utah",
    "/fireplace-service-salt-lake-city/":
        "Fireplace Service in Salt Lake City, Utah",
    "/gas-fireplace-contractor-in-davis-county/":
        "Gas Fireplace Contractor in Davis County",
    "/furnace-replacement-park-city/":
        "Furnace Replacement in Park City, Utah",
    "/furnace-replacement-salt-lake-city/":
        "Furnace Replacement in Salt Lake City, Utah",
    "/furnace-replacement-services-ogden/":
        "Furnace Replacement in Ogden, Utah",
    "/furnace-repair-salt-lake-city/":
        "Furnace Repair in Salt Lake City, Utah",
    "/gas-fireplace-inserts-sandy/":
        "Gas Fireplace Inserts in Sandy, Utah",
    "/electric-fireplace-services-in-sandy/":
        "Electric Fireplace in Sandy, Utah",
    "/gas-fireplace-repair-services-in-salt-lake-city/":
        "Gas Fireplace Repair in Salt Lake City, Utah",
    "/furnace-cleaning-park-city/":
        "Furnace Cleaning in Park City, Utah",

    # === BLOG POSTS ===
    "/how-a-fireplace-insert-can-boost-home-heating-efficiency/":
        "How a Fireplace Insert Boosts Heating Efficiency",
    "/is-summer-a-good-time-to-have-furnace-maintenance-done/":
        "Is Summer a Good Time for Furnace Maintenance?",
    "/6-reasons-why-expectant-couples-should-upgrade-their-ac/":
        "6 Reasons Expectant Couples Should Upgrade Their AC",
    "/what-to-consider-when-selecting-a-newair-conditioner/":
        "What to Consider When Selecting a New AC",
    "/3-types-of-central-ac-systems-that-should-be-upgraded/":
        "3 Central AC Systems That Should Be Upgraded",
    "/misconceptions-about-furnace-repairs-and-replacement/":
        "Misconceptions About Furnace Repairs & Replacement",
    "/zoned-heating-customized-comfort-for-your-utah-home/":
        "Zoned Heating: Customized Comfort for Utah Homes",
    "/air-conditioning-filters-which-is-the-best-for-you/":
        "AC Filters: Which Is the Best for You?",
    "/common-reasons-your-furnace-isn-t-warming-your-house/":
        "Common Reasons Your Furnace Isn't Warming Your House",
    "/hvac-buying-tips-select-the-best-unit-for-your-home/":
        "HVAC Buying Tips: Select the Right Unit for Your Home",
    "/signs-your-home-needs-a-humidifier-or-a-dehumidifier/":
        "Signs Your Home Needs a Humidifier or Dehumidifier",
    "/do-6-things-this-spring-for-an-energy-efficient-home/":
        "6 Spring Tips for an Energy-Efficient Home",
    "/4-reasons-to-consider-replacing-your-air-conditioner/":
        "4 Reasons to Consider Replacing Your AC",
    "/what-to-know-about-proper-condenser-unit-protection/":
        "What to Know About Condenser Unit Protection",
    "/what-to-consider-before-you-hire-an-hvac-contractor/":
        "What to Consider Before Hiring an HVAC Contractor",
    "/smoke-in-your-eyes-check-the-fireplace-and-airflow/":
        "Smoke in Your Eyes? Check Fireplace & Airflow",
    "/what-should-you-know-about-your-hvac-control-board/":
        "What to Know About Your HVAC Control Board",
    "/upgrading-your-heating-system-what-components-should-you/":
        "Upgrading Your Heating System: What to Change First",
    "/4-signs-of-central-air-unit-ice-problems-comfort-solutions/":
        "4 Signs of Central AC Ice & Frost Problems",
    "/beyond-low-energy-bills-further-benefits-of-efficient-hvac/":
        "Benefits of Efficient HVAC Beyond Lower Energy Bills",
    "/mold-and-air-conditioning-questions-and-answers/":
        "Mold & Air Conditioning: Questions Answered",
    "/furnace-heating-guide-repair-installation/":
        "Furnace Heating Guide: Repair & Installation",
    "/everything-the-first-time-ac-buyer-needs-to-know/":
        "What First-Time AC Buyers Need to Know",
    "/how-to-get-the-best-out-of-your-hvac-thermostat/":
        "How to Get the Best Out of Your HVAC Thermostat",
    "/why-is-my-air-conditioner-not-working-properly/":
        "Why Isn't My Air Conditioner Working Properly?",
    "/what-do-professionals-do-during-an-ac-tune-up/":
        "What Professionals Do During an AC Tune-Up",
    "/essential-hvac-maintenance-tasks-for-the-first-time-homeowner/":
        "Essential HVAC Maintenance for New Homeowners",
    "/4-ways-to-integrate-hvac-components-with-interior-design/":
        "4 Ways to Integrate HVAC with Interior Design",
    "/common-hvac-odors-what-do-these-smells-mean/":
        "Common HVAC Odors: What Do These Smells Mean?",
    "/do-your-air-ducts-need-repair-or-replacement-3-warning-signs/":
        "Air Duct Repair or Replacement: 3 Warning Signs",
    "/utahs-indoor-air-quality-issues-and-how-to-deal-with-them/":
        "Utah Indoor Air Quality: Issues & Solutions",
    "/air-conditioner-cooling-guide/":
        "Home Cooling Guide: Installation, Repair & Tips",
    "/an-overview-of-gas-furnace-ignition-systems/":
        "An Overview of Gas Furnace Ignition Systems",
    "/is-fall-an-ideal-time-to-upgrade-your-hvac/":
        "Is Fall the Ideal Time to Upgrade Your HVAC?",
    "/garages-and-home-heating-what-to-consider/":
        "Garages and Home Heating: What to Consider",
    "/causes-and-prevention-of-overheating-air-conditioner-compressors/":
        "AC Compressor Overheating: Causes & Prevention",
    "/6-reasons-you-shouldn-t-partially-replace-your-central-ac/":
        "6 Reasons Not to Partially Replace Your Central AC",
    "/advice-to-extend-the-life-of-your-furnace/":
        "Advice to Extend the Life of Your Furnace",
    "/understanding-your-central-heating-system/":
        "Understanding Your Central Heating System",
    "/pets-and-your-hvac-what-you-need-to-know/":
        "Pets and Your HVAC: What You Need to Know",
    "/keep-your-home-warm-when-the-heater-won-t/":
        "Keep Your Home Warm When the Heater Won't",
    "/hvac-fall-maintenance-tips-to-facilitate-the-transition/":
        "HVAC Fall Maintenance Tips for Homeowners",
    "/install-a-ductless-mini-split-hvac-system-for-flexibility/":
        "Install a Ductless Mini-Split HVAC System",
    "/the-benefits-of-upgrading-to-a-high-efficiency-hvac-system/":
        "Benefits of Upgrading to a High-Efficiency HVAC System",

    # === COUPONS (should be noindex, not rewrite) ===
    "/coupons/free-smokeless-fire-pit-with-the-purchase-of-a-new-fireplace/":
        "(NOINDEX \u2014 do not rewrite)",
    "/coupons/59-off-any-ac-or-heating-repair-or-replacement/":
        "(NOINDEX \u2014 do not rewrite)",
}


def get_rec(url):
    # Strip domain
    key = url.replace("https://www.comfortsolutionsutah.com", "")
    if key in recommendations:
        return recommendations[key]
    # Try with trailing slash variant
    alt = key.rstrip("/") + "/"
    if alt in recommendations:
        return recommendations[alt]
    return ""


df["Recommended Title"] = df["Address"].apply(get_rec)
df["New Length"] = df["Recommended Title"].apply(
    lambda x: len(x) if x and not x.startswith("(") else 0
)


def get_action(row):
    cls = row["Classification"]
    if "NOINDEX" in cls or "DELETE" in cls:
        return "NOINDEX (no rewrite)"
    return "REWRITE"


df["Action"] = df.apply(get_action, axis=1)

# Sort by priority: Main Service > Service Page > City Service > Blog Post > NOINDEX
priority_order = {
    "Main Service Page":          0,
    "Service Page":               1,
    "City Service Page":          2,
    "Blog Post":                  3,
    "Category Archive (NOINDEX)": 4,
    "Coupon (NOINDEX)":           5,
    "WP Archive (NOINDEX)":       5,
    "Event Page (NOINDEX)":       5,
    "PPC Landing (NOINDEX)":      5,
    "Test Page (DELETE)":         6,
}
df["_sort"] = df["Classification"].map(priority_order).fillna(9)
df["_title_len_sort"] = -df["Title 1 Length"]
df = df.sort_values(by=["_sort", "_title_len_sort", "Address"]).reset_index(drop=True)

# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()
ws = wb.active
ws.title = "Title Shortening Plan"

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
subtitle_font = Font(name="Calibri", size=10, italic=True, color="595959")
cell_font = Font(name="Calibri", size=10)
cell_font_small = Font(name="Calibri", size=9)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)
thin = Side(border_style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

red_fill = PatternFill("solid", fgColor="F8CBAD")
yellow_fill = PatternFill("solid", fgColor="FFF2CC")
green_fill = PatternFill("solid", fgColor="C6E0B4")
gray_fill = PatternFill("solid", fgColor="E7E6E6")
blue_fill = PatternFill("solid", fgColor="D9E1F2")

classification_colors = {
    "Main Service Page":          PatternFill("solid", fgColor="F8CBAD"),
    "Service Page":               PatternFill("solid", fgColor="FFD9B3"),
    "City Service Page":          PatternFill("solid", fgColor="FFF2CC"),
    "Blog Post":                  PatternFill("solid", fgColor="D9E1F2"),
    "Coupon (NOINDEX)":           gray_fill,
    "WP Archive (NOINDEX)":       gray_fill,
    "Category Archive (NOINDEX)": gray_fill,
    "Event Page (NOINDEX)":       gray_fill,
    "PPC Landing (NOINDEX)":      gray_fill,
    "Test Page (DELETE)":         red_fill,
}

ws["A1"] = "Comfort Solutions \u2014 Truncated Titles Shortening Plan"
ws["A1"].font = title_font
ws.merge_cells("A1:H1")

rewrites = (df["Action"] == "REWRITE").sum()
noindex_count = (df["Action"] == "NOINDEX (no rewrite)").sum()
ws["A2"] = (
    f"75 pages with titles >60 chars | VERIFIED live (titles unchanged since SF crawl). "
    f"Plan: {rewrites} rewrites + {noindex_count} NOINDEX (non-SEO pages)"
)
ws["A2"].font = subtitle_font
ws.merge_cells("A2:H2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

headers = [
    "#", "URL", "Classification", "Current Title", "Curr Len",
    "Recommended Title", "New Len", "Status",
]
for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 36

for i, row in df.iterrows():
    r = i + 5
    new_len = int(row["New Length"]) if pd.notna(row["New Length"]) and row["New Length"] > 0 else ""
    values = [
        i + 1,
        row["Address"],
        row["Classification"],
        row["Title 1"],
        int(row["Title 1 Length"]),
        row["Recommended Title"],
        new_len,
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col in (4, 6) else cell_font
        c.border = border
        if col in (1, 5, 7, 8):
            c.alignment = center
        else:
            c.alignment = left
        # Classification color
        if col == 3:
            cls_color = classification_colors.get(row["Classification"], gray_fill)
            c.fill = cls_color
            c.font = Font(name="Calibri", size=10, bold=True)
        # Current length red if >70
        if col == 5:
            if isinstance(v, int) and v > 70:
                c.fill = red_fill
            elif isinstance(v, int) and v > 60:
                c.fill = yellow_fill
        # New length green if <=60
        if col == 7:
            if isinstance(v, int) and v <= 60:
                c.fill = green_fill
            elif isinstance(v, int) and v > 60:
                c.fill = yellow_fill
        # Highlight recommended title col
        if col == 6 and row["Action"] == "REWRITE":
            c.fill = green_fill

widths = {
    "A": 4, "B": 55, "C": 24, "D": 50, "E": 9,
    "F": 52, "G": 9, "H": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for r in range(5, 5 + len(df)):
    ws.row_dimensions[r].height = 40

ws.freeze_panes = "C5"

# =========================================================================
# SHEET 2 — Writing Standards & Implementation
# =========================================================================
ws2 = wb.create_sheet("Writing Standards")
ws2["A1"] = "Title Writing Standards & Implementation Guide"
ws2["A1"].font = title_font
ws2.merge_cells("A1:B1")

ctx = [
    ("", ""),
    ("=== SCOPE BREAKDOWN ===", ""),
    ("Total URLs flagged", "75"),
    ("Pre-drafted REWRITES", f"{rewrites} (all provided in Sheet 1 column F)"),
    ("NOINDEX instead of rewrite", f"{noindex_count} (coupons \u2014 per scope filter, don't need SEO-optimized titles)"),
    ("Verification", "Live fetch confirmed titles unchanged from SF crawl (March 2026). Minor HTML entity differences (&#039; \u2192 ') but same length category."),
    ("", ""),
    ("=== TITLE WRITING RULES (applied consistently) ===", ""),
    ("Max length", "60 characters (SERP truncation point on desktop). Mobile truncates earlier (~50 chars) so shorter is safer."),
    ("Format preference",
     "[Primary keyword] [in/| location] [optional qualifier]. Example: 'Furnace Repair in Salt Lake City, Utah' (41 chars)."),
    ("Pipe vs dash",
     "Pipe ('|') signals equal weight between elements, dash ('-') signals subordination. Use pipe for brand/city separators: 'AC Repair | Sandy, Ogden & SLC'. Use dash for descriptor: 'How to Thaw Frozen Pipes - Utility Guide'."),
    ("Brand suffix",
     "Drop ' - Comfort Solutions' from ALL blog posts and city-specific pages. The H1 + site branding carry the brand. Keep brand only on main service hubs and home."),
    ("No modality",
     "Remove 'Top', 'Best', 'Reliable', 'Expert', 'Premier', 'Trusted' \u2014 these are marketing words, not ranking words. Per semantic audit rules."),
    ("Concrete > generic",
     "'Furnace Repair in Sandy, Utah' beats 'Top Furnace Repair Services in Sandy: Reliable Solutions for Your Home'."),
    ("", ""),
    ("=== PRIORITY EXECUTION ORDER ===", ""),
    ("P0 \u2014 Main Service Hubs (6 URLs)",
     "Highest leverage \u2014 these rank for head commercial terms. Start with /services/hvac-systems/heating/, /ac-repair-service/, /air-conditioning/, /furnace-repair-service/, /ac-upgrade-replacement/, /furnace-replacement-upgrade/."),
    ("P1 \u2014 City Service Pages (~25 URLs)",
     "Individual city variants for furnace repair/installation, fireplace repair/installation, AC repair. High-value local SEO signal."),
    ("P2 \u2014 Blog Posts (~40 URLs)",
     "Blog titles with redundant brand suffix. Low-effort batch rewrites \u2014 mostly just strip ' - Comfort Solutions' from the end."),
    ("P3 \u2014 Coupons (2 URLs)",
     "Do NOT rewrite. Apply noindex via Rank Math \u2192 Post Types \u2192 Coupons \u2192 No Index (already covered in thin_pages + missing_meta plans). This overlaps with multiple audit items \u2014 one noindex config fixes all of them."),
    ("", ""),
    ("=== RANK MATH EDITING WORKFLOW ===", ""),
    ("Per-page edit",
     "WordPress admin \u2192 edit page/post \u2192 Rank Math meta box (bottom of editor) \u2192 General tab \u2192 'SEO Title' field \u2192 paste new title \u2192 Publish/Update."),
    ("Bulk edit alternative",
     "Rank Math PRO supports bulk title editing via Rank Math \u2192 Dashboard \u2192 Bulk Actions. If available, export all 75 to CSV, update SEO Title column, re-import. Saves ~1 hour."),
    ("Verify after save",
     "Rank Math shows a character counter below the title field \u2014 make sure it's green (<60) before saving. The plugin will also preview how it appears in a Google SERP."),
    ("Do NOT update H1 in this sweep",
     "H1 and Title are separate fields. H1 can be longer/more descriptive (it's the on-page heading). Only the Title (title tag) goes into SERPs. Check H1 separately via the missing_h1 plan if applicable."),
    ("", ""),
    ("=== EXPECTED OUTCOME ===", ""),
    ("SERP CTR",
     "Titles under 60 chars don't get truncated (...) \u2014 better CTR for all 73 rewritten pages. Estimate 5-15% CTR lift on existing impressions."),
    ("Ranking signal",
     "Title tag is one of the strongest on-page ranking signals. Removing modality + tightening to primary keyword + location may yield 1-3 position improvements on city-level queries over 4-8 weeks."),
    ("Cross-plan wins",
     "This sweep overlaps with the H1 plan for city service pages \u2014 many pages need BOTH H1 and Title rewrites. Coordinate to avoid doing the work twice: while in Rank Math editing the title, also add/fix the H1 in the same save."),
]

for r, (k, v) in enumerate(ctx, 2):
    c1 = ws2.cell(row=r, column=1, value=k)
    c2 = ws2.cell(row=r, column=2, value=v)
    if k.startswith("==="):
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    elif k and not v:
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    else:
        c1.font = Font(name="Calibri", size=10, bold=True)
        c2.font = cell_font
        c2.alignment = Alignment(wrap_text=True, vertical="top")

ws2.column_dimensions["A"].width = 42
ws2.column_dimensions["B"].width = 120

for r in range(2, 2 + len(ctx)):
    ws2.row_dimensions[r].height = 38

wb.save(out)
print(f"Saved: {out}")
print(f"Rewrites: {rewrites} | NOINDEX: {noindex_count}")
