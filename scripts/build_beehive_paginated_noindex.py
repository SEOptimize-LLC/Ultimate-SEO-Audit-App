"""Build Beehive Plumbing paginated category pages noindex action plan."""
import pandas as pd
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Beehive/Full Site SEO Audit/"
out = base + "beehive_paginated_noindex_plan.xlsx"

df = pd.read_excel(base + "not_indexed_pages.xlsx")
paginated = df[df["Content Type"].astype(str).str.lower().str.contains("paginat", na=False)].copy()


def extract_category(url):
    m = re.search(r"/category/([^/]+)/page/", url)
    if m:
        return m.group(1).replace("-", " ").title()
    if "/locations/page/" in url:
        return "Locations"
    return "Other"


def extract_page_num(url):
    m = re.search(r"/page/(\d+)/", url)
    return int(m.group(1)) if m else 0


paginated["Category"] = paginated["Landing Page"].apply(extract_category)
paginated["Page Num"] = paginated["Landing Page"].apply(extract_page_num)
paginated = paginated.sort_values(by=["Category", "Page Num"]).reset_index(drop=True)

# =========================================================================
# BUILD WORKBOOK
# =========================================================================

wb = Workbook()
ws = wb.active
ws.title = "Paginated Pages Noindex"

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
subtitle_font = Font(name="Calibri", size=10, italic=True, color="595959")
cell_font = Font(name="Calibri", size=10)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)
thin = Side(border_style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

red_fill = PatternFill("solid", fgColor="F8CBAD")
yellow_fill = PatternFill("solid", fgColor="FFF2CC")
green_fill = PatternFill("solid", fgColor="C6E0B4")
section_fill = PatternFill("solid", fgColor="DDEBF7")

ws["A1"] = "Beehive Plumbing \u2014 Paginated Category Pages Noindex Plan"
ws["A1"].font = title_font
ws.merge_cells("A1:H1")
ws["A2"] = (
    "35 paginated pages currently 'Unknown to Google' | All /category/*/page/N/ URLs | "
    "Roadmap item #8 (P1) | Crawl budget waste with zero ranking potential"
)
ws["A2"].font = subtitle_font
ws.merge_cells("A2:H2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

headers = [
    "#", "URL", "Category", "Page #",
    "Word Count", "Crawl Depth", "Inlinks", "Action",
]

for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 30

for i, row in paginated.iterrows():
    r = i + 5
    wc = int(row["Word Count"]) if pd.notna(row["Word Count"]) else 0
    cd = int(row["Crawl Depth"]) if pd.notna(row["Crawl Depth"]) else "N/A"
    il = int(row["Unique InLinks"]) if pd.notna(row["Unique InLinks"]) else 0
    values = [
        i + 1,
        row["Landing Page"],
        row["Category"],
        row["Page Num"],
        wc,
        cd,
        il,
        "NOINDEX + Remove from Sitemap",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font
        c.border = border
        if col in (1, 3, 4, 5, 6, 7):
            c.alignment = center
        else:
            c.alignment = left
        # Flag extreme depths + zero-word pages
        if col == 6 and isinstance(v, int) and v >= 10:
            c.fill = red_fill
        elif col == 6 and isinstance(v, int) and v >= 7:
            c.fill = yellow_fill
        if col == 5 and isinstance(v, int) and v < 100:
            c.fill = red_fill
        if col == 7 and isinstance(v, int) and v == 0:
            c.fill = red_fill
        if col == 8:
            c.fill = yellow_fill
            c.font = Font(name="Calibri", size=10, bold=True, color="7F6000")

widths = {
    "A": 4, "B": 58, "C": 22, "D": 7,
    "E": 11, "F": 11, "G": 9, "H": 32,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for r in range(5, 5 + len(paginated)):
    ws.row_dimensions[r].height = 22

ws.freeze_panes = "C5"

# =========================================================================
# SHEET 2 — Category Rollup
# =========================================================================
ws2 = wb.create_sheet("Category Rollup")
ws2["A1"] = "Affected Categories"
ws2["A1"].font = title_font
ws2.merge_cells("A1:D1")

rollup = paginated.groupby("Category").agg(
    pages=("Landing Page", "count"),
    max_page=("Page Num", "max"),
    avg_depth=("Crawl Depth", "mean"),
).reset_index().sort_values("pages", ascending=False)

rollup_headers = ["Category", "Paginated Pages Affected", "Max Page #", "Avg Crawl Depth"]
for col, h in enumerate(rollup_headers, 1):
    c = ws2.cell(row=3, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws2.row_dimensions[3].height = 30

for i, row in rollup.iterrows():
    r = i + 4
    values = [
        row["Category"],
        int(row["pages"]),
        int(row["max_page"]),
        round(row["avg_depth"], 1) if pd.notna(row["avg_depth"]) else "N/A",
    ]
    for col, v in enumerate(values, 1):
        c = ws2.cell(row=r, column=col, value=v)
        c.font = cell_font
        c.border = border
        c.alignment = center if col > 1 else left

ws2.column_dimensions["A"].width = 30
ws2.column_dimensions["B"].width = 25
ws2.column_dimensions["C"].width = 14
ws2.column_dimensions["D"].width = 18

# =========================================================================
# SHEET 3 — Implementation Guide
# =========================================================================
ws3 = wb.create_sheet("Implementation Guide")
ws3["A1"] = "Implementation Guide \u2014 Paginated Noindex"
ws3["A1"].font = title_font
ws3.merge_cells("A1:B1")

ctx = [
    ("", ""),
    ("=== THE PROBLEM ===", ""),
    ("Issue",
     "35 paginated category pages (/category/*/page/N/) are 'Unknown to Google' in GSC"),
    ("Why it matters",
     "These URLs exist in the site crawl but Google has not discovered or indexed them. They consume crawl budget if/when Google does find them, without providing ranking value."),
    ("Categories affected",
     "13 blog categories + 1 locations taxonomy (conserve-water, plumbing, drain-cleaning, water-heaters, plumbing-maintenance, plumbing-repairs, plumbing-leaks, emergency-plumbing, plumbing-service, plumbing-company, water-softeners, blog, locations)"),
    ("Deepest URLs",
     "4 pages buried at crawl depth 12-14 (effectively unreachable by users, minimal crawl priority from Google). 2 URLs have 0 words and 0 inlinks \u2014 completely stranded."),
    ("", ""),
    ("=== WHY NOINDEX (not rewrite) ===", ""),
    ("These are pagination pages, not content pages",
     "They list post excerpts from one category. They do not produce unique rankable content. Writing unique titles/metas for 35 pagination URLs is wasted effort."),
    ("Per our internal scope filter rule",
     "Exclude pages without SEO value. Pagination falls into this bucket along with coupons, testimonials, WP archives, PPC pages."),
    ("Google's stance on pagination",
     "Google deprecated rel=prev/next in 2019. Current best practice: noindex,follow pagination OR leave indexed with self-referencing canonicals. For blog category pagination with thin content, noindex,follow is the cleaner choice."),
    ("Reference",
     "See Skills/technical-seo-agent/references/robots-txt-ecommerce-framework.md for the three-tool framework (robots.txt / noindex / canonical)."),
    ("", ""),
    ("=== THE FIX (3 STEPS) ===", ""),
    ("Step 1: Noindex all /page/N/ URLs via Rank Math",
     "Rank Math SEO \u2192 Titles & Meta \u2192 Misc Pages \u2192 'Noindex Paginated Pages' toggle ON. This applies site-wide to all paginated archives in one config change. Est. 5 minutes."),
    ("Step 2: Remove paginated URLs from XML sitemap",
     "Rank Math usually excludes noindexed URLs automatically \u2014 verify by opening the sitemap after Step 1 and searching for '/page/'. Should return zero matches."),
    ("Step 3: Validate",
     "Inspect a sample URL (e.g., /category/plumbing/page/2/) via GSC URL Inspection. Should show 'Excluded by noindex tag' after Google's next crawl (typically 2-4 weeks)."),
    ("", ""),
    ("=== DO NOT DO THESE (common mistakes) ===", ""),
    ("Do NOT block in robots.txt",
     "If you block pagination in robots.txt AND add noindex, Google can't crawl the page to see the noindex \u2014 defeats the purpose. These are currently 'Unknown to Google' which means Google has not crawled them. Keep them crawlable so Google CAN see the noindex directive once applied."),
    ("Do NOT canonical page/N/ back to page/1/",
     "Canonicalizing pagination to the hub signals duplicate content when it's actually a series. Google ignores the signal and it creates crawl confusion. Use noindex,follow instead."),
    ("Do NOT delete or 404 them",
     "These URLs exist because WordPress auto-generates them from category archives. Deleting individual pagination URLs isn't possible without breaking the archive structure."),
    ("Do NOT write unique titles/metas for each",
     "Per scope filter rule \u2014 these are pagination pages with no SEO value. Effort is better spent on actual ranking pages."),
    ("", ""),
    ("=== EXPECTED OUTCOME ===", ""),
    ("Crawl budget",
     "After noindex is applied and Google re-crawls, these URLs drop out of the 'to be indexed' queue. Crawl budget redistributes to actual content."),
    ("GSC Coverage report",
     "Within 4 weeks: 35 URLs move from 'Unknown to Google' to 'Excluded by noindex tag' (or disappear entirely). Both are good outcomes."),
    ("Bigger picture fix (optional, P2)",
     "The root cause is that blog categories have too many posts (10+ pages of pagination on /conserve-water/ and /plumbing/) driven by 515 total blog posts. The 'Blog content consolidation' roadmap item (P2) \u2014 noindexing ~400 zero-traffic blog posts \u2014 will collapse category pagination to 1-3 pages per category, making the pagination noindex moot."),
    ("", ""),
    ("=== EFFORT & PRIORITY ===", ""),
    ("Priority", "P1 (per combined roadmap)"),
    ("Effort", "Low \u2014 single config toggle in Rank Math"),
    ("Risk", "Near-zero \u2014 noindex on pagination is a site-wide best practice"),
    ("Verification timeline", "2-4 weeks for Google to recrawl and reflect changes in GSC Coverage report"),
]

for r, (k, v) in enumerate(ctx, 2):
    c1 = ws3.cell(row=r, column=1, value=k)
    c2 = ws3.cell(row=r, column=2, value=v)
    if k.startswith("==="):
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    elif k and not v:
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    else:
        c1.font = Font(name="Calibri", size=10, bold=True)
        c2.font = cell_font
        c2.alignment = Alignment(wrap_text=True, vertical="top")

ws3.column_dimensions["A"].width = 45
ws3.column_dimensions["B"].width = 110

for r in range(2, 2 + len(ctx)):
    ws3.row_dimensions[r].height = 34

wb.save(out)
print(f"Saved: {out}")
print(f"Rows: {len(paginated)}")
