"""Build Beehive Plumbing missing H1 tags action plan with recommended H1s."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Beehive/Full Site SEO Audit/"
out = base + "beehive_missing_h1_plan.xlsx"

h1_df = pd.read_excel(base + "on_page_issues.xlsx", sheet_name="Missing H1")
inv_xl = pd.read_excel(base + "content_inventory_by_type.xlsx", sheet_name=None)

# Combine inventory
all_pages = pd.concat(
    [df for name, df in inv_xl.items() if name != "Overview"],
    ignore_index=True,
)
all_pages["url_key"] = (
    all_pages["Landing Page"]
    .str.replace("https://www.beehiveplumbing.com", "", regex=False)
    .str.replace("https://beehiveplumbing.com", "", regex=False)
)
all_pages = all_pages.drop_duplicates(subset="url_key")

h1_df["url_key"] = h1_df["Address"].str.replace(
    "https://www.beehiveplumbing.com", "", regex=False
)
merged = h1_df.merge(
    all_pages[["url_key", "Content Type", "Word Count", "Unique InLinks", "Clicks", "Imps"]],
    on="url_key",
    how="left",
)

# =========================================================================
# Recommended H1 per URL
# =========================================================================
# Principles:
# - Primary keyword + location modifier where applicable
# - Benefit or service type, not generic "Welcome to..."
# - No modality ("most trusted", "best") per semantic audit rules
# - Max ~65 chars (H1 doesn't have hard limit but concise is better)
# =========================================================================

h1_recommendations = {
    # === MAIN SERVICE HUBS ===
    "/emergency-plumber/":
        "24/7 Emergency Plumber in Salt Lake City, Utah",
    "/drain-cleaning-utah/":
        "Drain Cleaning Services in Salt Lake City & the Wasatch Front",
    "/plumbing-repairs-utah/":
        "Plumbing Repairs in Salt Lake City, Utah",
    "/water-heater-repair/":
        "Water Heater Repair in Salt Lake City, Utah",
    "/water-heater-repair-utah/":
        "Water Heater Repair in Salt Lake City, Utah",
    "/water-heater-replacement-utah/":
        "Water Heater Replacement in Salt Lake City, Utah",
    "/sewer-line-repair-utah/":
        "Sewer Line Repair in Salt Lake City, Utah",
    "/hydro-jetting-drain-cleaning-utah/":
        "Hydro Jetting Drain Cleaning in Salt Lake City",
    "/drain-pipe-repair-utah/":
        "Drain Pipe Repair in Salt Lake City, Utah",
    "/new-construction-plumbing-utah/":
        "New Construction Plumbing in Salt Lake City, Utah",
    "/remodeling/":
        "Plumbing & HVAC Remodeling in Salt Lake City, Utah",
    "/repiping-services-salt-lake-city/":
        "Home Repiping Services in Salt Lake City, Utah",
    "/flushometer-repair-utah/":
        "Flushometer Repair in Salt Lake City, Utah",
    "/low-flow-toilets-utah/":
        "Low-Flow Toilet Installation & Repair in Salt Lake City",
    "/waterline-locating-inspection/":
        "Main Waterline Locating & Inspection in Salt Lake City",
    "/hvac-tune-up/":
        "HVAC Tune-Up & Inspection in Salt Lake City, Utah",
    "/ogden-sewer-line/":
        "Ogden Sewer Line Separation & Compliance",

    # === CITY-SPECIFIC WATER HEATER REPAIR ===
    "/water-heater-repair-lehi/":
        "Water Heater Repair in Lehi, Utah",
    "/water-heater-repair-west-jordan/":
        "Water Heater Repair in West Jordan, Utah",
    "/water-heater-repair-utah/park-city/":
        "Water Heater Repair in Park City, Utah",
    "/water-heater-repair-services-south-jordan/":
        "Water Heater Repair in South Jordan, Utah",
    "/water-heater-replacement-utah/water-heater-repair-services-in-sandy/":
        "Water Heater Repair in Sandy, Utah",
    "/water-heater-replacement-utah/tankless-water-heater-repair-services-in-draper/":
        "Tankless Water Heater Repair in Draper, Utah",

    # === CITY-SPECIFIC WATER HEATER REPLACEMENT ===
    "/water-heater-replacement-utah/water-heater-replacement-in-lehi-utah/":
        "Water Heater Replacement in Lehi, Utah",
    "/water-heater-replacement-utah/park-city/":
        "Water Heater Replacement in Park City, Utah",
    "/water-heater-replacement-utah/sandy/":
        "Water Heater Replacement in Sandy, Utah",
    "/water-heater-replacement-utah/south-jordan/":
        "Water Heater Replacement in South Jordan, Utah",
    "/water-heater-replacement-utah/murray/":
        "Water Heater Replacement in Murray, Utah",
    "/water-heater-replacement-draper/":
        "Water Heater Replacement in Draper, Utah",

    # === CITY-SPECIFIC EMERGENCY / DRAIN ===
    "/emergency-plumber-services-lehi/":
        "24/7 Emergency Plumber in Lehi, Utah",
    "/emergency-plumber-draper/":
        "24/7 Emergency Plumber in Draper, Utah",
    "/drain-repair-services-park-city-utah/":
        "Drain Repair Services in Park City, Utah",
    "/drain-cleaning-park-city-utah/":
        "Drain Cleaning in Park City, Utah",
    "/plumbing-near-millville-ut/":
        "Plumbing Services in Millville, Utah",

    # === COMPANY / FAQ / SUPPORT ===
    "/master-plumbers/":
        "Licensed Master Plumbers in Utah",
    "/premier-plans/":
        "Beehive Premier Plans \u2014 4, 7 & 10-Year Warranty Protection",
    "/frequently-asked-questions-answers-water-softeners/":
        "Water Softener FAQ \u2014 Common Questions Answered",

    # === LOW SEO VALUE (still need H1 for accessibility + semantics) ===
    "/terms-and-privacy-policy/":
        "Terms & Privacy Policy",
    "/view-our-reviews/":
        "Customer Reviews \u2014 Beehive Plumbing",
    "/thank-you/":
        "Thank You",
    "/testimonials/":
        "Customer Testimonials",
}


def get_recommended_h1(url_key):
    # Exact match
    if url_key in h1_recommendations:
        return h1_recommendations[url_key]
    # Trailing slash variant
    alt = url_key.rstrip("/") + "/"
    if alt in h1_recommendations:
        return h1_recommendations[alt]
    return ""


merged["Recommended H1"] = merged["url_key"].apply(get_recommended_h1)
merged["H1 Length"] = merged["Recommended H1"].str.len()


# Classify by SEO priority
def classify(row):
    ct = row.get("Content Type", "")
    url = row["url_key"].lower()
    if any(p in url for p in ["/thank-you", "/terms", "/privacy"]):
        return "Utility (Low SEO Value)"
    if ct == "Legal Page":
        return "Utility (Low SEO Value)"
    if "testimonial" in url or "review" in url:
        return "Trust Signal (Medium)"
    if ct == "Service Page":
        # Determine if it's a main hub or a city variant
        # Main hubs: shallow URL, high inlinks
        inlinks = row.get("Unique InLinks", 0)
        if pd.isna(inlinks):
            inlinks = 0
        if inlinks > 30:
            return "Service Hub (P0)"
        elif inlinks > 5:
            return "Service Page (P0)"
        else:
            return "City Service Page (P0)"
    return "Other"


merged["Priority"] = merged.apply(classify, axis=1)


# Sort: P0 service hubs first, then service pages, then city pages, then trust, then utility
priority_order = {
    "Service Hub (P0)": 0,
    "Service Page (P0)": 1,
    "City Service Page (P0)": 2,
    "Trust Signal (Medium)": 3,
    "Utility (Low SEO Value)": 4,
    "Other": 5,
}
merged["_sort"] = merged["Priority"].map(priority_order).fillna(5)
merged = merged.sort_values(by=["_sort", "Address"]).reset_index(drop=True)

# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()
ws = wb.active
ws.title = "Missing H1 Action Plan"

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
blue_fill = PatternFill("solid", fgColor="D9E1F2")
section_fill = PatternFill("solid", fgColor="DDEBF7")

priority_colors = {
    "Service Hub (P0)":       PatternFill("solid", fgColor="F8CBAD"),
    "Service Page (P0)":      PatternFill("solid", fgColor="FFD9B3"),
    "City Service Page (P0)": PatternFill("solid", fgColor="FFF2CC"),
    "Trust Signal (Medium)":  PatternFill("solid", fgColor="D9E1F2"),
    "Utility (Low SEO Value)": PatternFill("solid", fgColor="E7E6E6"),
}

ws["A1"] = "Beehive Plumbing \u2014 Missing H1 Tags Action Plan"
ws["A1"].font = title_font
ws.merge_cells("A1:I1")
ws["A2"] = (
    "41 pages missing H1 (17% of indexable pages) | 36 are service pages with real SEO value | "
    "All 41 pre-drafted H1s included, ready to paste | Roadmap item #10 (P1)"
)
ws["A2"].font = subtitle_font
ws.merge_cells("A2:I2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

headers = [
    "#", "URL", "Current Title Tag", "Priority",
    "Recommended H1", "H1 Length", "Word Count", "Inlinks", "Status",
]
for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 36

for i, row in merged.iterrows():
    r = i + 5
    wc = int(row["Word Count"]) if pd.notna(row["Word Count"]) else ""
    il = int(row["Unique InLinks"]) if pd.notna(row["Unique InLinks"]) else ""
    h1_len = int(row["H1 Length"]) if pd.notna(row["H1 Length"]) and row["H1 Length"] > 0 else ""
    priority = row["Priority"]
    values = [
        i + 1,
        row["Address"],
        row["Title 1"] if pd.notna(row["Title 1"]) else "",
        priority,
        row["Recommended H1"],
        h1_len,
        wc,
        il,
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col in (3, 5) else cell_font
        c.border = border
        if col in (1, 4, 6, 7, 8, 9):
            c.alignment = center
        else:
            c.alignment = left
        # Priority coloring
        if col == 4 and priority in priority_colors:
            c.fill = priority_colors[priority]
            c.font = Font(name="Calibri", size=10, bold=True)
        # Highlight recommended H1 in green
        if col == 5 and v:
            c.fill = green_fill
        # Flag inlinks
        if col == 8 and isinstance(v, int) and v <= 2:
            c.fill = red_fill

widths = {
    "A": 4, "B": 58, "C": 55, "D": 22,
    "E": 55, "F": 10, "G": 11, "H": 9, "I": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for r in range(5, 5 + len(merged)):
    ws.row_dimensions[r].height = 42

ws.freeze_panes = "C5"

# =========================================================================
# SHEET 2 — Implementation Guide
# =========================================================================
ws2 = wb.create_sheet("Implementation Guide")
ws2["A1"] = "Implementation Guide \u2014 Missing H1 Tags"
ws2["A1"].font = title_font
ws2.merge_cells("A1:B1")

priority_counts = merged["Priority"].value_counts()

ctx = [
    ("", ""),
    ("=== OVERVIEW ===", ""),
    ("Total URLs missing H1", "41"),
    ("% of indexable pages", "17%"),
    ("Source", "SF crawl \u2014 H1-1 column empty"),
    ("Roadmap priority", "P1 (item #10 in combined roadmap)"),
    ("", ""),
    ("=== PRIORITY BREAKDOWN ===", ""),
    *[(p, f"{int(c)} pages") for p, c in priority_counts.items()],
    ("", ""),
    ("=== WHY H1 TAGS MATTER ===", ""),
    ("Primary ranking signal",
     "H1 is one of the strongest on-page signals for page topic. Missing H1 means Google must infer the topic from title tag + body content alone."),
    ("Accessibility compliance",
     "Screen readers use H1 as the primary page heading. Missing H1 is a WCAG 2.1 violation (Success Criterion 1.3.1)."),
    ("User experience",
     "H1 is usually the first visible heading on the page. Missing H1 creates visual confusion about what the page is about."),
    ("AI Overview / SGE signal",
     "LLM-based search features weight H1 heavily when generating answer boxes. Missing H1 reduces citation likelihood."),
    ("", ""),
    ("=== H1 WRITING STANDARDS ===", ""),
    ("Format",
     "[Service] + [in] + [Location] + [optional qualifier]. Example: 'Water Heater Repair in Salt Lake City, Utah'"),
    ("Length",
     "~30-65 characters ideal. No hard maximum but keep it scannable."),
    ("No modality",
     "Per semantic audit rules: avoid 'Top', 'Best', 'Most Trusted', 'Reliable', 'Expert'. These are marketing words, not ranking words. Stick to concrete service + location."),
    ("Unique from title tag",
     "H1 should NOT be identical to title tag. Title tag optimizes SERP CTR (can be longer, more descriptive); H1 is the on-page heading (cleaner, service-first)."),
    ("One H1 per page",
     "Multiple H1s dilute the signal. If the current theme has H1 in the logo/header, remove it and promote the actual page heading."),
    ("", ""),
    ("=== HOW TO ADD H1 IN WORDPRESS ===", ""),
    ("Option A: Direct theme edit (most reliable)",
     "Ensure the page title (the_title()) renders as <h1> in the template. Typically single.php, page.php, or a custom service-page template. Check current theme for where pages render \u2014 fix there."),
    ("Option B: Per-page H1 via Gutenberg/Elementor",
     "Open each page in editor, add a Heading block at the top, set level to H1, insert the recommended H1 text. Time: ~30 seconds per page. 41 pages \u2248 20 minutes."),
    ("Option C: Rank Math / Yoast schema",
     "Rank Math can enforce H1 through page-level schema if configured. Verify current Rank Math settings \u2014 unlikely to be the best approach for a quick fix."),
    ("Recommended approach for Beehive",
     "Option A (theme edit) is best if all missing-H1 pages use the same template. Option B is the fallback if pages are scattered across templates. Start by inspecting 3-5 of the affected pages in the WP editor to determine which template they use."),
    ("", ""),
    ("=== DUPLICATE URL HEADS-UP ===", ""),
    ("/water-heater-repair/ AND /water-heater-repair-utah/",
     "BOTH are in the list. These are the 97% near-duplicate pair (roadmap item #6). DO NOT add H1 to both \u2014 consolidate FIRST (pick a canonical, 301 the other), then add H1 to the survivor only."),
    ("", ""),
    ("=== VERIFICATION ===", ""),
    ("Step 1: Verify template change",
     "After fixing the template, inspect 3-5 pages via 'View Source' in the browser. Search for '<h1>'. Confirm exactly one H1 per page and that it matches the recommended text."),
    ("Step 2: Re-crawl",
     "Run Screaming Frog again. Missing H1 count should drop to near-zero. Any remaining missing-H1 URLs need manual per-page edits."),
    ("Step 3: GSC URL Inspection",
     "For top 5 service pages (drain-cleaning-utah, emergency-plumber, water-heater-repair-utah, sewer-line-repair-utah, plumbing-repairs-utah) run URL Inspection to confirm Google re-crawled and sees the new H1."),
    ("Expected timeline",
     "H1 changes take effect immediately on-page. Google re-crawl typically 1-2 weeks. Ranking signal response: 2-4 weeks."),
    ("", ""),
    ("=== EXPECTED OUTCOME ===", ""),
    ("SEO",
     "36 service pages gain a primary ranking signal. Expect modest position improvement (1-3 spots) on head terms over 4-8 weeks, especially for city-specific pages currently ranking positions 11-20."),
    ("Accessibility",
     "WCAG 2.1 compliance gap closed for 41 pages."),
    ("AI Overviews",
     "Improved citation likelihood on query-matching service + city terms."),
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

ws2.column_dimensions["A"].width = 48
ws2.column_dimensions["B"].width = 115

for r in range(2, 2 + len(ctx)):
    ws2.row_dimensions[r].height = 36

wb.save(out)
print(f"Saved: {out}")
print(f"Total URLs: {len(merged)}")
print(f"Missing H1 recommendations provided: {(merged['Recommended H1'] != '').sum()}")
print()
print("Priority breakdown:")
for p, c in priority_counts.items():
    print(f"  {p}: {c}")
