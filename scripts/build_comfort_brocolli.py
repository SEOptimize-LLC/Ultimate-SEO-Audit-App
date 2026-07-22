"""Build Comfort Solutions /brocolli-button-test/ resolution plan."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Comfort/Full SEO Audit/"
out = base + "comfort_brocolli_test_page_resolution.xlsx"

wb = Workbook()
ws = wb.active
ws.title = "Test Page Resolution"

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
subtitle_font = Font(name="Calibri", size=10, italic=True, color="595959")
cell_font = Font(name="Calibri", size=10)
section_fill = PatternFill("solid", fgColor="DDEBF7")
red_fill = PatternFill("solid", fgColor="F8CBAD")
yellow_fill = PatternFill("solid", fgColor="FFF2CC")
green_fill = PatternFill("solid", fgColor="C6E0B4")

thin = Side(border_style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="top", wrap_text=True)

ws["A1"] = "Comfort Solutions \u2014 /brocolli-button-test/ Resolution"
ws["A1"].font = title_font
ws.merge_cells("A1:C1")
ws["A2"] = (
    "Roadmap item: Delete or noindex /brocolli-button-test/ "
    "(test page, 100% identical to real service pages)"
)
ws["A2"].font = subtitle_font
ws.merge_cells("A2:C2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

# =========================================================================
# Current state table
# =========================================================================
ws["A4"] = "CURRENT STATE (verified live 2026-04-20)"
ws["A4"].fill = section_fill
ws["A4"].font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
ws.merge_cells("A4:C4")
ws.row_dimensions[4].height = 22

state_rows = [
    ("Check", "Current Value", "Status"),
    ("URL", "https://www.comfortsolutionsutah.com/brocolli-button-test/", ""),
    ("Live HTTP status", "404 Not Found", "GOOD \u2014 page removed from WordPress"),
    ("GSC Coverage", "Submitted and indexed", "STALE \u2014 Google has not re-crawled since deletion"),
    ("GSC Last Crawled", "2026-02-07", "Over 2 months old"),
    ("GSC Page Fetch", "SUCCESSFUL (historical snapshot)", "Google still sees old cached 200 response"),
    ("GSC Indexing State", "INDEXING_ALLOWED", "STALE \u2014 based on pre-deletion crawl"),
    ("Sitemap reference", "https://www.comfortsolutionsutah.com/page-sitemap.xml",
     "PROBLEM \u2014 URL still listed in sitemap per GSC 'Referring URLs'"),
    ("Robots.txt", "ALLOWED", "Expected \u2014 no robots.txt block needed"),
    ("Rich Results", "Breadcrumbs detected",
     "INFO \u2014 will drop automatically after de-indexing"),
]

for r, (c1, c2, c3) in enumerate(state_rows, 5):
    cell_a = ws.cell(row=r, column=1, value=c1)
    cell_b = ws.cell(row=r, column=2, value=c2)
    cell_c = ws.cell(row=r, column=3, value=c3)
    if r == 5:
        for c in (cell_a, cell_b, cell_c):
            c.fill = header_fill
            c.font = header_font
            c.alignment = center
            c.border = border
    else:
        for c in (cell_a, cell_b, cell_c):
            c.font = cell_font
            c.border = border
            c.alignment = left
        cell_a.font = Font(name="Calibri", size=10, bold=True)
        # Color status column
        status_lower = c3.lower()
        if "good" in status_lower or "expected" in status_lower:
            cell_c.fill = green_fill
        elif "stale" in status_lower or "problem" in status_lower:
            cell_c.fill = red_fill
        elif "info" in status_lower:
            cell_c.fill = yellow_fill

ws.column_dimensions["A"].width = 24
ws.column_dimensions["B"].width = 62
ws.column_dimensions["C"].width = 55

for r in range(6, 6 + len(state_rows) - 1):
    ws.row_dimensions[r].height = 30

# =========================================================================
# Action plan
# =========================================================================
action_start_row = 5 + len(state_rows) + 2
ws.cell(row=action_start_row, column=1, value="ACTION PLAN").fill = section_fill
ws.cell(row=action_start_row, column=1).font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
ws.merge_cells(start_row=action_start_row, start_column=1, end_row=action_start_row, end_column=3)
ws.row_dimensions[action_start_row].height = 22

actions_header_row = action_start_row + 1
actions = [
    ("#", "Action", "Details"),
    (1, "Remove URL from XML sitemap",
     "The URL is still listed in page-sitemap.xml per GSC. This is a conflicting signal \u2014 sitemap says 'index this' while server returns 404. WordPress usually auto-removes deleted pages from Yoast-generated sitemaps, but verify manually. Fetch https://www.comfortsolutionsutah.com/page-sitemap.xml and confirm /brocolli-button-test/ is NOT listed. If it still is, the page may be 'deleted' from admin but exists in trash or as a draft \u2014 permanently delete it."),
    (2, "Keep serving 404 (do NOT redirect)",
     "Current 404 is correct. Do NOT 301-redirect this URL anywhere \u2014 redirecting a test page to a real service page would send a misleading signal about URL equivalence. A clean 404 is the fastest way to get it de-indexed. WordPress may auto-301 to nearest match \u2014 check that it's not currently doing that."),
    (3, "Request removal via GSC (optional accelerator)",
     "Google Search Console \u2192 Removals \u2192 New Request \u2192 Temporary removals \u2192 submit https://www.comfortsolutionsutah.com/brocolli-button-test/. This hides the URL from SERPs within 24 hours. It's a 6-month block \u2014 but by then the 404 will be permanent. Shortcut if the URL is visible in SERPs right now."),
    (4, "Request re-indexing (force recrawl)",
     "GSC \u2192 URL Inspection \u2192 paste the URL \u2192 'Request Indexing'. Google will attempt a fresh crawl within a few days, see the 404, and drop the URL from the index. Faster than waiting for organic recrawl."),
    (5, "Verify at 2 weeks + 4 weeks",
     "Run GSC URL Inspection again. Expected progression: Week 1-2 \u2192 'Submitted and indexed' (stale, unchanged). Week 2-4 \u2192 'Not found (404)' in Coverage. Week 4+ \u2192 URL no longer appears in the URL Inspection tool at all (fully dropped)."),
]

for r_offset, row_data in enumerate(actions):
    r = actions_header_row + r_offset
    for col_idx, val in enumerate(row_data, 1):
        c = ws.cell(row=r, column=col_idx, value=val)
        c.border = border
        c.alignment = left if col_idx == 3 else center
        if r_offset == 0:
            c.fill = header_fill
            c.font = header_font
            c.alignment = center
        else:
            c.font = cell_font if col_idx != 2 else Font(name="Calibri", size=10, bold=True)
    if r_offset > 0:
        ws.row_dimensions[r].height = 75

ws.row_dimensions[actions_header_row].height = 28

# =========================================================================
# Why NOT "noindex" or "delete + redirect"
# =========================================================================
notes_start = actions_header_row + len(actions) + 2
ws.cell(row=notes_start, column=1, value="DECISION RATIONALE").fill = section_fill
ws.cell(row=notes_start, column=1).font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
ws.merge_cells(start_row=notes_start, start_column=1, end_row=notes_start, end_column=3)
ws.row_dimensions[notes_start].height = 22

notes = [
    ("Decision", "Reasoning"),
    ("Delete (404) CHOSEN",
     "The page is already deleted (confirmed via live HTTP 404). This is the cleanest path. A 404 tells Google clearly 'this URL does not exist' \u2014 no ambiguity, no signal conflict, fast de-indexing."),
    ("Noindex REJECTED",
     "Noindex requires a crawlable page with a valid response. Since the page is already 404 (and should stay that way), noindex is moot. Adding noindex would require undeleting the page, which defeats the purpose."),
    ("301 redirect REJECTED",
     "Redirecting /brocolli-button-test/ to a real service page would tell Google these two URLs are equivalent. The test page had 100% identical content to real service pages \u2014 so Google might already be confused about which is canonical. A redirect preserves that confusion. A 404 cleanly terminates the URL."),
    ("Robots.txt block REJECTED",
     "Blocking in robots.txt prevents crawling. Google can't see the 404 if it can't crawl. Worst case: the URL stays indexed as a title-less entry. Leave the URL crawlable so Google can process the 404."),
]

for r_offset, row_data in enumerate(notes):
    r = notes_start + 1 + r_offset
    for col_idx, val in enumerate(row_data, 1):
        if col_idx == 2:
            ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
        c = ws.cell(row=r, column=col_idx, value=val)
        c.border = border
        c.alignment = left
        if r_offset == 0:
            c.fill = header_fill
            c.font = header_font
            c.alignment = center
        else:
            c.font = Font(name="Calibri", size=10, bold=True) if col_idx == 1 else cell_font
            # Color the decision cell
            if col_idx == 1:
                if "CHOSEN" in val:
                    c.fill = green_fill
                elif "REJECTED" in val:
                    c.fill = red_fill
    if r_offset > 0:
        ws.row_dimensions[r].height = 65

ws.row_dimensions[notes_start + 1].height = 28

# =========================================================================
# Expected outcome
# =========================================================================
outcome_start = notes_start + 1 + len(notes) + 2
ws.cell(row=outcome_start, column=1, value="EXPECTED OUTCOME").fill = section_fill
ws.cell(row=outcome_start, column=1).font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
ws.merge_cells(start_row=outcome_start, start_column=1, end_row=outcome_start, end_column=3)
ws.row_dimensions[outcome_start].height = 22

outcomes = [
    ("Week 1", "404 continues, sitemap cleaned, removal request submitted to GSC."),
    ("Week 2", "GSC URL Inspection should show fresh crawl. Coverage may still read 'Submitted and indexed' momentarily \u2014 normal."),
    ("Week 3\u20134", "Coverage flips to 'Not found (404)'. URL removed from SERPs if Removal request was used."),
    ("Week 4+", "URL fully dropped from index. Stops appearing in SF crawls (if crawled from the sitemap). Duplicate-with-real-service-pages signal eliminated \u2014 positive side effect for the 97% near-duplicate issue on the real service pages."),
]

for r_offset, (when, what) in enumerate(outcomes):
    r = outcome_start + 1 + r_offset
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    c1 = ws.cell(row=r, column=1, value=when)
    c2 = ws.cell(row=r, column=2, value=what)
    c1.font = Font(name="Calibri", size=10, bold=True)
    c2.font = cell_font
    c1.border = border
    c2.border = border
    c1.alignment = center
    c2.alignment = left
    ws.row_dimensions[r].height = 40

# =========================================================================
# Priority / effort summary
# =========================================================================
summary_start = outcome_start + 1 + len(outcomes) + 2
ws.cell(row=summary_start, column=1, value="SUMMARY").fill = section_fill
ws.cell(row=summary_start, column=1).font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
ws.merge_cells(start_row=summary_start, start_column=1, end_row=summary_start, end_column=3)
ws.row_dimensions[summary_start].height = 22

summary = [
    ("Roadmap Priority", "P2 (item #7)"),
    ("Status", "50% complete \u2014 page 404'd, but still indexed and possibly still in sitemap"),
    ("Remaining effort", "~10 minutes (sitemap check + GSC removal + re-index request)"),
    ("Risk", "Near-zero \u2014 just finishing what's been started"),
    ("Bonus benefit", "Removes one source of content duplication confusion. This test page shared 100% content with real service pages \u2014 Google may have been choosing it over legitimate pages as the canonical."),
]

for r_offset, (k, v) in enumerate(summary):
    r = summary_start + 1 + r_offset
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    c1 = ws.cell(row=r, column=1, value=k)
    c2 = ws.cell(row=r, column=2, value=v)
    c1.font = Font(name="Calibri", size=10, bold=True)
    c2.font = cell_font
    c1.border = border
    c2.border = border
    c1.alignment = left
    c2.alignment = left
    ws.row_dimensions[r].height = 32

wb.save(out)
print(f"Saved: {out}")
