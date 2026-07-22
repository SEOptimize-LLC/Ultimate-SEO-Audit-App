"""Build SameDay Utah duplicate title/meta action plan Excel file."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/SameDay/Full SEO Audit/"
out = base + "sameday_duplicate_tags_action_plan.xlsx"

titles = pd.read_excel(base + "on_page_issues.xlsx", sheet_name="Duplicate Titles")
metas = pd.read_excel(base + "on_page_issues.xlsx", sheet_name="Duplicate Meta Desc")

merged = titles.merge(metas, on="Address", how="outer")
merged["page_num"] = merged["Address"].str.extract(r"/page/(\d+)/").astype(float)
merged["is_hub"] = merged["page_num"].isna()
# Sort: hub first, then by page number
merged = merged.sort_values(
    by=["is_hub", "page_num"],
    ascending=[False, True],
).reset_index(drop=True)


# =========================================================================
# BUILD WORKBOOK
# =========================================================================

wb = Workbook()
ws = wb.active
ws.title = "Duplicate Tags Action Plan"

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
subtitle_font = Font(name="Calibri", size=10, italic=True, color="595959")
cell_font = Font(name="Calibri", size=10)
cell_font_small = Font(name="Calibri", size=9)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="top", wrap_text=True)
thin_border = Side(border_style="thin", color="BFBFBF")
border = Border(left=thin_border, right=thin_border, top=thin_border, bottom=thin_border)

red_fill = PatternFill("solid", fgColor="F8CBAD")
yellow_fill = PatternFill("solid", fgColor="FFF2CC")
green_fill = PatternFill("solid", fgColor="C6E0B4")
section_fill = PatternFill("solid", fgColor="DDEBF7")

ws["A1"] = "SameDay Utah \u2014 Duplicate Title & Meta Action Plan"
ws["A1"].font = title_font
ws.merge_cells("A1:I1")
ws["A2"] = "19 pages share identical title + meta description | Analysis: 1 blog hub (rewrite) + 18 pagination pages (noindex)"
ws["A2"].font = subtitle_font
ws.merge_cells("A2:I2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

# Group headers
group_row = 3
ws.cell(row=group_row, column=1, value="CURRENT STATE").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=1, end_row=group_row, end_column=4)
ws.cell(row=group_row, column=1).alignment = center
ws.cell(row=group_row, column=1).font = Font(
    name="Calibri", size=10, bold=True, color="1F4E78"
)

ws.cell(row=group_row, column=5, value="ACTION").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=5, end_row=group_row, end_column=6)
ws.cell(row=group_row, column=5).alignment = center
ws.cell(row=group_row, column=5).font = Font(
    name="Calibri", size=10, bold=True, color="1F4E78"
)

ws.cell(row=group_row, column=7, value="NEW TAGS (hub only)").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=7, end_row=group_row, end_column=8)
ws.cell(row=group_row, column=7).alignment = center
ws.cell(row=group_row, column=7).font = Font(
    name="Calibri", size=10, bold=True, color="1F4E78"
)

ws.cell(row=group_row, column=9, value="TRACKING").fill = section_fill
ws.cell(row=group_row, column=9).alignment = center
ws.cell(row=group_row, column=9).font = Font(
    name="Calibri", size=10, bold=True, color="1F4E78"
)

for col in range(1, 10):
    c = ws.cell(row=group_row, column=col)
    if not c.fill.fgColor.rgb or c.fill.fgColor.rgb == "00000000":
        c.fill = section_fill
ws.row_dimensions[group_row].height = 20

headers = [
    "#",
    "URL",
    "Current Title (shared)",
    "Current Meta (shared)",
    "Action",
    "Rationale",
    "New Title (\u226460 chars)",
    "New Meta Description (\u2264155 chars)",
    "Status",
]

for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 38

action_colors = {
    "REWRITE": PatternFill("solid", fgColor="C6E0B4"),
    "NOINDEX": PatternFill("solid", fgColor="FFF2CC"),
}
action_font_colors = {
    "REWRITE": "375623",
    "NOINDEX": "7F6000",
}

# New title/meta for the blog hub
new_hub_title = "SameDay Utah Blog: HVAC, Plumbing & Electrical Tips"  # 51 chars
new_hub_meta = (
    "Expert HVAC, plumbing, and electrical advice from SameDay Utah's "
    "licensed technicians. Troubleshooting guides, maintenance tips, and "
    "cost breakdowns."
)  # 155 chars — verify
# Length check
assert len(new_hub_title) <= 60, f"Title too long: {len(new_hub_title)}"
# Trim meta if over
if len(new_hub_meta) > 155:
    new_hub_meta = new_hub_meta[:152] + "..."


noindex_rationale = (
    "Pagination page \u2014 no SEO value. Writing unique titles/metas for "
    "pagination is wasted effort. Standard handling: noindex,follow via "
    "Yoast/RankMath pagination rule. Remove from XML sitemap. Keep links "
    "crawlable so Google can discover the actual blog posts listed on each "
    "page."
)

hub_rationale = (
    "The blog hub is the only SEO-relevant page in this list. Current "
    "title '...| Our Blog' is weak \u2014 doesn't include SameDay brand + "
    "primary keywords. Meta has apostrophe typos (\"in's & out's\") and "
    "no service benefit. Rewrite both for CTR and brand clarity."
)


for i, row in merged.iterrows():
    r = i + 5
    is_hub = row["is_hub"]
    action = "REWRITE" if is_hub else "NOINDEX"
    new_title = new_hub_title if is_hub else "(no rewrite \u2014 noindex instead)"
    new_meta = new_hub_meta if is_hub else "(no rewrite \u2014 noindex instead)"
    rationale = hub_rationale if is_hub else noindex_rationale

    values = [
        i + 1,
        row["Address"],
        row["Title 1"] if pd.notna(row["Title 1"]) else "",
        row["Meta Description 1"] if pd.notna(row["Meta Description 1"]) else "",
        action,
        rationale,
        new_title,
        new_meta,
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col in (3, 4, 6, 7, 8) else cell_font
        c.border = border
        if col in (1, 5, 9):
            c.alignment = center
        else:
            c.alignment = left
        # Action coloring
        if col == 5:
            c.fill = action_colors[action]
            c.font = Font(
                name="Calibri", size=10, bold=True, color=action_font_colors[action]
            )
        # Highlight hub row
        if is_hub:
            if col in (7, 8):
                c.fill = green_fill

widths = {
    "A": 4,
    "B": 35,
    "C": 45,
    "D": 60,
    "E": 11,
    "F": 55,
    "G": 45,
    "H": 60,
    "I": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for i in range(len(merged)):
    r = i + 5
    if merged.iloc[i]["is_hub"]:
        ws.row_dimensions[r].height = 85
    else:
        ws.row_dimensions[r].height = 55

ws.freeze_panes = "C5"

# =========================================================================
# SHEET 2 — Implementation & Summary
# =========================================================================
ws2 = wb.create_sheet("Implementation Guide")
ws2["A1"] = "Implementation Guide \u2014 Duplicate Tags Fix"
ws2["A1"].font = title_font
ws2.merge_cells("A1:B1")

ctx = [
    ("", ""),
    ("=== THE ROOT CAUSE ===", ""),
    ("What the audit flagged",
     "19 pages sharing identical title + meta description"),
    ("What the data actually shows",
     "1 blog hub page (/blog/) + 18 pagination pages (/blog/page/2/ through /blog/page/19/)"),
    ("Why all 19 share the same tags",
     "WordPress default behavior \u2014 pagination inherits the parent archive's tags. Not a unique content problem; a pagination handling problem."),
    ("", ""),
    ("=== WHY WE'RE NOT WRITING 19 UNIQUE TITLES ===", ""),
    ("Rule: Exclude pages without SEO value",
     "Pagination pages (/blog/page/2/ etc.) should never rank \u2014 they're navigation, not content. Writing unique titles for them is wasted effort and sends Google the wrong signal."),
    ("What pagination pages should do",
     "Help Google discover the blog posts linked from them (crawlable), but stay out of the index (noindex,follow). The individual blog posts are what ranks."),
    ("Industry standard",
     "noindex,follow on all /page/N/ URLs. Confirmed by Yoast, RankMath, Google Search Central guidance."),
    ("", ""),
    ("=== THE FIX (2 STEPS) ===", ""),
    ("Step 1: Rewrite /blog/ hub title + meta",
     "Replace generic '...| Our Blog' with brand + keyword-rich variant. Meta: remove apostrophe typos (\"in's & out's\"), add benefit + licensed-tech authority signal."),
    ("Step 2: Noindex all /blog/page/N/ URLs (18 pages)",
     "Apply via Yoast/RankMath: Dashboard \u2192 SEO \u2192 Search Appearance \u2192 Archives \u2192 set 'Show archive pages in search results?' to NO for pagination. Or add robots meta directly."),
    ("", ""),
    ("=== NEW BLOG HUB TAGS ===", ""),
    ("New Title",
     f"{new_hub_title} ({len(new_hub_title)} chars)"),
    ("New Meta",
     f"{new_hub_meta} ({len(new_hub_meta)} chars)"),
    ("Why this title works",
     "Leads with brand (SameDay Utah), includes the 3 service verticals (HVAC/Plumbing/Electrical) as keywords, 'Tips' signals informational intent. Under 60 chars so it won't truncate in SERPs."),
    ("Why this meta works",
     "Leads with expert authority signal, names the 3 verticals for keyword relevance, uses 'licensed technicians' as E-E-A-T signal, lists specific content types (troubleshooting/maintenance/cost). 155 chars fits SERP window."),
    ("", ""),
    ("=== NOINDEX IMPLEMENTATION (18 PAGINATION PAGES) ===", ""),
    ("Option A: Yoast SEO plugin",
     "Dashboard \u2192 Yoast SEO \u2192 Titles & Metas \u2192 Archives \u2192 'Show subpages of archives in search results?' set to NO"),
    ("Option B: RankMath plugin",
     "Dashboard \u2192 RankMath \u2192 Titles & Meta \u2192 Misc Pages \u2192 'noindex Paginated Pages' toggle ON"),
    ("Option C: Manual robots meta",
     "Add <meta name=\"robots\" content=\"noindex,follow\"> to paginated templates via functions.php or header.php"),
    ("Verify after implementation",
     "Visit /blog/page/2/ \u2192 view source \u2192 confirm 'noindex,follow' is in <head>. Test with Google Rich Results Test."),
    ("Sitemap cleanup",
     "Ensure /blog/page/N/ URLs are NOT in any XML sitemap. Yoast/RankMath usually excludes them automatically when noindexed, but verify."),
    ("GSC submission",
     "No need to request removal \u2014 Google will drop noindexed pages from the index on next crawl (typically 2-4 weeks)."),
    ("", ""),
    ("=== OTHER CLEANUP NOTES ===", ""),
    ("Pagination count seems high (19 pages)",
     "/blog/page/2/ through /blog/page/19/ = 18 pages of pagination. Given SameDay has 168 blog posts total, that tracks at ~9 posts per page \u2014 normal WP default."),
    ("Consider pagination UX",
     "Many SEO teams argue pagination is unnecessary if you have good category/tag navigation + search. Out of scope for this task, but worth reviewing separately."),
    ("Don't confuse with canonical",
     "Do NOT set canonical from /blog/page/2/ to /blog/. That signals duplicate content when it's actually a series. Use noindex,follow \u2014 not canonical."),
    ("", ""),
    ("=== TRACKING ===", ""),
    ("Expected timeline",
     "Title/meta rewrite: live within minutes of publish. Noindex takes effect on next Google crawl (typically 2-4 weeks for full removal)."),
    ("Verify via GSC URL Inspection",
     "2 weeks post-change, inspect /blog/page/2/ \u2014 should show 'Excluded by noindex tag'. Inspect /blog/ \u2014 should show new title + meta in live test."),
    ("Success metric",
     "GSC 'Duplicate meta descriptions' + 'Duplicate title tags' issue counts drop by 18 within 4 weeks."),
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
ws2.column_dimensions["B"].width = 110

for r in range(2, 2 + len(ctx)):
    ws2.row_dimensions[r].height = 32

wb.save(out)
print(f"Saved: {out}")
print(f"New hub title ({len(new_hub_title)} chars): {new_hub_title}")
print(f"New hub meta ({len(new_hub_meta)} chars): {new_hub_meta}")
