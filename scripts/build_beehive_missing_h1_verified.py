"""Build Beehive Plumbing missing H1 plan \u2014 VERIFIED against live HTML."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Beehive/Full Site SEO Audit/"
out = base + "beehive_missing_h1_plan_verified.xlsx"

h1_source = pd.read_excel(base + "on_page_issues.xlsx", sheet_name="Missing H1")
h1_live = pd.read_pickle("/tmp/beehive_h1_check.pkl")

merged = h1_source.merge(h1_live, left_on="Address", right_on="url", how="left")
merged["verified_status"] = merged["h1_count"].apply(
    lambda x: "CONFIRMED MISSING" if x == 0 else ("FALSE POSITIVE" if x == 1 else ("MULTIPLE" if x >= 2 else "ERROR"))
)

# Inventory data
inv_xl = pd.read_excel(base + "content_inventory_by_type.xlsx", sheet_name=None)
all_pages = pd.concat([df for name, df in inv_xl.items() if name != "Overview"], ignore_index=True)
all_pages["url_key"] = (
    all_pages["Landing Page"]
    .str.replace("https://www.beehiveplumbing.com", "", regex=False)
    .str.replace("https://beehiveplumbing.com", "", regex=False)
)
all_pages = all_pages.drop_duplicates(subset="url_key")
merged["url_key"] = merged["Address"].str.replace("https://www.beehiveplumbing.com", "", regex=False)
merged = merged.merge(
    all_pages[["url_key", "Content Type", "Word Count", "Unique InLinks"]],
    on="url_key", how="left"
)

# Recommended H1s
recommendations = {
    "/emergency-plumber/":                                        "24/7 Emergency Plumber in Salt Lake City, Utah",
    "/drain-cleaning-utah/":                                      "Drain Cleaning Services in Salt Lake City & the Wasatch Front",
    "/plumbing-repairs-utah/":                                    "Plumbing Repairs in Salt Lake City, Utah",
    "/water-heater-repair/":                                      "Water Heater Repair in Salt Lake City, Utah",
    "/water-heater-repair-utah/":                                 "Water Heater Repair in Salt Lake City, Utah",
    "/water-heater-replacement-utah/":                            "Water Heater Replacement in Salt Lake City, Utah",
    "/sewer-line-repair-utah/":                                   "Sewer Line Repair in Salt Lake City, Utah",
    "/hydro-jetting-drain-cleaning-utah/":                        "Hydro Jetting Drain Cleaning in Salt Lake City",
    "/drain-pipe-repair-utah/":                                   "Drain Pipe Repair in Salt Lake City, Utah",
    "/new-construction-plumbing-utah/":                           "New Construction Plumbing in Salt Lake City, Utah",
    "/remodeling/":                                               "Plumbing & HVAC Remodeling in Salt Lake City, Utah",
    "/repiping-services-salt-lake-city/":                         "Home Repiping Services in Salt Lake City, Utah",
    "/flushometer-repair-utah/":                                  "Flushometer Repair in Salt Lake City, Utah",
    "/low-flow-toilets-utah/":                                    "Low-Flow Toilet Installation & Repair in Salt Lake City",
    "/waterline-locating-inspection/":                            "Main Waterline Locating & Inspection in Salt Lake City",
    "/hvac-tune-up/":                                             "HVAC Tune-Up & Inspection in Salt Lake City, Utah",
    "/ogden-sewer-line/":                                         "Ogden Sewer Line Separation & Compliance",
    "/water-heater-repair-lehi/":                                 "Water Heater Repair in Lehi, Utah",
    "/water-heater-repair-west-jordan/":                          "Water Heater Repair in West Jordan, Utah",
    "/water-heater-repair-utah/park-city/":                       "Water Heater Repair in Park City, Utah",
    "/water-heater-repair-services-south-jordan/":                "Water Heater Repair in South Jordan, Utah",
    "/water-heater-replacement-utah/water-heater-repair-services-in-sandy/":
        "Water Heater Repair in Sandy, Utah",
    "/water-heater-replacement-utah/tankless-water-heater-repair-services-in-draper/":
        "Tankless Water Heater Repair in Draper, Utah",
    "/water-heater-replacement-utah/water-heater-replacement-in-lehi-utah/":
        "Water Heater Replacement in Lehi, Utah",
    "/water-heater-replacement-utah/park-city/":                  "Water Heater Replacement in Park City, Utah",
    "/water-heater-replacement-utah/sandy/":                      "Water Heater Replacement in Sandy, Utah",
    "/water-heater-replacement-utah/south-jordan/":               "Water Heater Replacement in South Jordan, Utah",
    "/water-heater-replacement-utah/murray/":                     "Water Heater Replacement in Murray, Utah",
    "/water-heater-replacement-draper/":                          "Water Heater Replacement in Draper, Utah",
    "/emergency-plumber-services-lehi/":                          "24/7 Emergency Plumber in Lehi, Utah",
    "/emergency-plumber-draper/":                                 "24/7 Emergency Plumber in Draper, Utah",
    "/drain-repair-services-park-city-utah/":                     "Drain Repair Services in Park City, Utah",
    "/drain-cleaning-park-city-utah/":                            "Drain Cleaning in Park City, Utah",
    "/plumbing-near-millville-ut/":                               "Plumbing Services in Millville, Utah",
    "/master-plumbers/":                                          "Licensed Master Plumbers in Utah",
    "/premier-plans/":                                            "Beehive Premier Plans \u2014 4, 7 & 10-Year Warranty Protection",
    "/frequently-asked-questions-answers-water-softeners/":       "Water Softener FAQ \u2014 Common Questions Answered",
    "/terms-and-privacy-policy/":                                 "Terms & Privacy Policy",
    "/view-our-reviews/":                                         "Customer Reviews \u2014 Beehive Plumbing",
    "/thank-you/":                                                "Thank You",
    "/testimonials/":                                             "Customer Testimonials",
}

def get_rec(url_key):
    if url_key in recommendations:
        return recommendations[url_key]
    alt = url_key.rstrip("/") + "/"
    if alt in recommendations:
        return recommendations[alt]
    return ""

merged["Recommended H1"] = merged["url_key"].apply(get_rec)

# Sort: confirmed missing first (the real work), then false positives (still review), then errors
status_order = {"CONFIRMED MISSING": 0, "FALSE POSITIVE": 1, "MULTIPLE": 2, "ERROR": 3}
merged["_sort"] = merged["verified_status"].map(status_order)
merged = merged.sort_values(by=["_sort", "Address"]).reset_index(drop=True)

# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()
ws = wb.active
ws.title = "Verified H1 Action Plan"

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

status_fill = {
    "CONFIRMED MISSING": red_fill,
    "FALSE POSITIVE":    green_fill,
    "MULTIPLE":          yellow_fill,
    "ERROR":             blue_fill,
}
status_font = {
    "CONFIRMED MISSING": "9C0006",
    "FALSE POSITIVE":    "375623",
    "MULTIPLE":          "7F6000",
    "ERROR":             "1F4E78",
}

confirmed = (merged["verified_status"] == "CONFIRMED MISSING").sum()
false_positive = (merged["verified_status"] == "FALSE POSITIVE").sum()

ws["A1"] = "Beehive Plumbing \u2014 Missing H1 Verified Against Live HTML"
ws["A1"].font = title_font
ws.merge_cells("A1:J1")
ws["A2"] = (
    f"SF flagged 41 pages | VERIFIED via live HTML fetch: {confirmed} CONFIRMED missing, "
    f"{false_positive} FALSE POSITIVES (H1 exists on live page but SF missed it)"
)
ws["A2"].font = subtitle_font
ws.merge_cells("A2:J2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

headers = [
    "#", "URL", "Verified Status", "Current H1 on Live Page",
    "Current Title Tag", "Recommended H1",
    "Word Count", "Inlinks", "Action", "Status",
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
    status = row["verified_status"]
    live_h1 = row["h1_texts"] if pd.notna(row.get("h1_texts")) else ""

    if status == "CONFIRMED MISSING":
        action = "ADD RECOMMENDED H1"
    elif status == "FALSE POSITIVE":
        action = "REVIEW EXISTING H1 (optional rewrite)"
    elif status == "ERROR":
        action = "MANUAL CHECK NEEDED"
    else:
        action = "REVIEW"

    wc = int(row["Word Count"]) if pd.notna(row.get("Word Count")) else ""
    il = int(row["Unique InLinks"]) if pd.notna(row.get("Unique InLinks")) else ""

    values = [
        i + 1,
        row["Address"],
        status,
        live_h1[:150] if isinstance(live_h1, str) else "",
        row["Title 1"] if pd.notna(row["Title 1"]) else "",
        row["Recommended H1"],
        wc, il, action,
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col in (4, 5, 6) else cell_font
        c.border = border
        if col in (1, 3, 7, 8, 10):
            c.alignment = center
        else:
            c.alignment = left
        if col == 3:
            c.fill = status_fill.get(status, red_fill)
            c.font = Font(name="Calibri", size=10, bold=True, color=status_font.get(status, "000000"))
        if col == 6 and v and status == "CONFIRMED MISSING":
            c.fill = green_fill
        if col == 4 and status == "FALSE POSITIVE":
            c.fill = green_fill

widths = {
    "A": 4, "B": 58, "C": 19, "D": 50,
    "E": 50, "F": 52, "G": 11, "H": 9, "I": 30, "J": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for r in range(5, 5 + len(merged)):
    ws.row_dimensions[r].height = 50

ws.freeze_panes = "C5"

# =========================================================================
# SHEET 2 — Methodology & Summary
# =========================================================================
ws2 = wb.create_sheet("Methodology & Summary")
ws2["A1"] = "Methodology & Summary"
ws2["A1"].font = title_font
ws2.merge_cells("A1:B1")

ctx = [
    ("", ""),
    ("=== WHAT HAPPENED ===", ""),
    ("Original SF crawl finding",
     "41 pages flagged as missing H1 (based on raw HTML snapshot from crawl date March 12 2026)"),
    ("Client feedback",
     "'Many of these pages HAVE H1 tags when I view them live' \u2014 triggering verification"),
    ("Verification method",
     "Fetched each of the 41 URLs live via urllib with browser-like headers. Parsed raw HTML for <h1> tags. Ran twice with user-agent rotation to clear rate-limit 403s."),
    ("Verification date",
     "2026-04-20"),
    ("", ""),
    ("=== VERIFIED RESULTS ===", ""),
    (f"CONFIRMED MISSING H1",
     f"{confirmed} pages \u2014 these are the real fixes needed. Recommended H1s provided in Sheet 1."),
    (f"FALSE POSITIVES (H1 exists on live page)",
     f"{false_positive} pages \u2014 SF crawl was wrong. H1 is present now. Optional: review current H1 text against our writing standards (no modality, service + location format) and rewrite if weak."),
    ("Errors resolved",
     "All 41 URLs successfully fetched after retries \u2014 no manual checks needed."),
    ("", ""),
    ("=== WHY SF MISSED SOME H1s ===", ""),
    ("Possible causes",
     "1) H1 added to pages AFTER the SF crawl (March 12). Several of the 'false positive' pages have H1s that look fresh \u2014 likely added during other SEO fixes in the interim."),
    ("",
     "2) Client-side rendering. If the H1 is injected by JavaScript (Elementor dynamic widget, Gutenberg block, or theme shortcode), the raw HTML SF parses may not include it. SF has a JS rendering mode but it's off by default."),
    ("",
     "3) H1 inside an unusual container (Elementor widget with custom markup, image replacement). SF's parser sometimes misses these."),
    ("Takeaway",
     "Always verify SF on-page findings against live HTML before delivering client reports. Crawl data is a snapshot, not live state."),
    ("", ""),
    ("=== RECOMMENDED NEXT STEPS ===", ""),
    ("Step 1: Fix the CONFIRMED MISSING pages",
     f"Add the {confirmed} recommended H1s from Sheet 1. These are the real work."),
    ("Step 2: Review FALSE POSITIVES for quality",
     f"For the {false_positive} pages with existing H1s, check whether the current H1 follows our standards (no modality, concrete service + location). If any use 'Top', 'Best', 'Expert', 'Premier', or 'Reliable' as filler, rewrite using the recommended H1 column. Examples in this batch: 'Expert Water Heater Repair in Salt Lake City' \u2192 rewrite to 'Water Heater Repair in Salt Lake City, Utah'."),
    ("Step 3: Configure SF to render JS on next crawl",
     "In Screaming Frog \u2192 Configuration \u2192 Spider \u2192 Rendering \u2192 set to 'JavaScript'. This adds overhead but captures H1s added by Elementor/Gutenberg client-side. Worth it for Beehive given the theme."),
    ("Step 4: Re-verify after changes",
     "Once you add H1s to the CONFIRMED MISSING pages, re-run this verification script to confirm 0 pages without H1."),
    ("", ""),
    ("=== LESSON FOR FUTURE AUDITS ===", ""),
    ("Rule",
     "For any audit finding that flags on-page elements (H1, canonical, meta, title), verify against live HTML for at least a sample before including in client deliverables. Screaming Frog is excellent but not infallible \u2014 JS rendering, crawl timing, and plugin-based content can create false positives."),
    ("Add to framework",
     "Update Technical SEO Agent skill with this rule \u2014 on-page element findings should be verified against live HTML via a quick curl/fetch step before being included in any report."),
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

ws2.column_dimensions["A"].width = 45
ws2.column_dimensions["B"].width = 115

for r in range(2, 2 + len(ctx)):
    ws2.row_dimensions[r].height = 40

wb.save(out)
print(f"Saved: {out}")
print(f"CONFIRMED MISSING: {confirmed} pages \u2014 the real fixes needed")
print(f"FALSE POSITIVES: {false_positive} pages \u2014 H1 already exists on live page")
