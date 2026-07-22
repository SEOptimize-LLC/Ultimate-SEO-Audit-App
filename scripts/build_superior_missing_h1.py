"""Superior Water & Air — Missing H1 action plan (verified against live HTML).

Audit finding: 7 pages missing H1.
Live verification reveals:
- 5 PPC landing pages (scope filter excludes — should noindex, not fix H1)
- 1 test page (should delete or noindex)
- 1 testimonials hub (FALSE POSITIVE — H1 already exists on live page)

Also discovered: /furnace-ppc-001/ and /test-lead-form/ are currently INDEXABLE
(misconfigured — other PPCs are correctly noindexed).
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = (r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/"
        r"Claude/Claude Code + VS Code/SEO/Projects/Projects/"
        r"Ultimate SEO Auditor/Clients/Superior/Full SEO Audit/")
out = base + "superior_missing_h1_plan.xlsx"

# Per-URL action plan based on live verification
rows_data = [
    {
        "url": "https://superiorwaterandair.com/testimonials/",
        "page_type": "Testimonials Hub",
        "live_h1_count": 1,
        "live_h1": "Testimonials",
        "robots": "index, follow",
        "sf_finding": "Missing H1",
        "verified_status": "FALSE POSITIVE",
        "action": "NO ACTION NEEDED",
        "rationale": (
            "Live HTML shows H1 'Testimonials' exists. Screaming Frog crawl "
            "(March 2026) missed it — likely added in the interim or JS-injected. "
            "No fix required. Optional: strengthen H1 to 'Customer Testimonials — "
            "Superior Water & Air' for better topical signal."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/plumbing-ppc-001/",
        "page_type": "PPC Landing Page",
        "live_h1_count": 0,
        "live_h1": "",
        "robots": "follow, noindex",
        "sf_finding": "Missing H1",
        "verified_status": "CONFIRMED MISSING (but correctly noindexed)",
        "action": "NO H1 FIX NEEDED",
        "rationale": (
            "PPC landing page — correctly noindexed ('follow, noindex'). "
            "Per scope filter, PPC pages don't need SEO optimization including H1. "
            "Already set up correctly — leave as-is."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/air-conditioner-ppc-001/",
        "page_type": "PPC Landing Page",
        "live_h1_count": 0,
        "live_h1": "",
        "robots": "follow, noindex",
        "sf_finding": "Missing H1",
        "verified_status": "CONFIRMED MISSING (but correctly noindexed)",
        "action": "NO H1 FIX NEEDED",
        "rationale": (
            "PPC landing page — correctly noindexed. Scope filter excludes. "
            "No action needed."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/air-quality-ppc-001/",
        "page_type": "PPC Landing Page",
        "live_h1_count": 0,
        "live_h1": "",
        "robots": "follow, noindex",
        "sf_finding": "Missing H1",
        "verified_status": "CONFIRMED MISSING (but correctly noindexed)",
        "action": "NO H1 FIX NEEDED",
        "rationale": (
            "PPC landing page — correctly noindexed. Scope filter excludes. "
            "No action needed."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/waterheater-ppc-001/",
        "page_type": "PPC Landing Page",
        "live_h1_count": 0,
        "live_h1": "",
        "robots": "follow, noindex",
        "sf_finding": "Missing H1",
        "verified_status": "CONFIRMED MISSING (but correctly noindexed)",
        "action": "NO H1 FIX NEEDED",
        "rationale": (
            "PPC landing page — correctly noindexed. Scope filter excludes. "
            "No action needed."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/furnace-ppc-001/",
        "page_type": "PPC Landing Page",
        "live_h1_count": 0,
        "live_h1": "",
        "robots": "index, follow",
        "sf_finding": "Missing H1",
        "verified_status": "MISCONFIGURED — currently indexable",
        "action": "ADD NOINDEX (not H1)",
        "rationale": (
            "PPC landing page but CURRENTLY INDEXABLE (robots: 'index, follow'). "
            "The other 4 PPC pages are correctly noindexed ('follow, noindex') — "
            "this one is an inconsistency. Fix: apply same noindex rule as other "
            "PPC pages via Rank Math/Yoast. DO NOT add H1 — PPC pages should "
            "never be indexed in the first place."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/test-lead-form/",
        "page_type": "Test/Internal Page",
        "live_h1_count": 0,
        "live_h1": "",
        "robots": "index, follow",
        "sf_finding": "Missing H1",
        "verified_status": "MISCONFIGURED — test page is indexable",
        "action": "DELETE or NOINDEX",
        "rationale": (
            "Test page (slug '/test-lead-form/') — likely a dev/internal test that "
            "was never taken down. Currently indexable. Options: (A) delete the "
            "page entirely if no longer needed; (B) noindex if it serves a "
            "purpose but shouldn't rank. Either way, DO NOT add H1 — this is "
            "not content meant for organic search."
        ),
    },
]


# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()
ws = wb.active
ws.title = "Missing H1 Verified Plan"

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1F4E78")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="595959")
CELL_FONT = Font(name="Calibri", size=10)
CELL_FONT_SM = Font(name="Calibri", size=9)
SECTION_FILL = PatternFill("solid", fgColor="DDEBF7")
RED_FILL = PatternFill("solid", fgColor="F8CBAD")
YELLOW_FILL = PatternFill("solid", fgColor="FFF2CC")
GREEN_FILL = PatternFill("solid", fgColor="C6E0B4")
GRAY_FILL = PatternFill("solid", fgColor="E7E6E6")
BLUE_FILL = PatternFill("solid", fgColor="D9E1F2")
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)

status_fill = {
    "FALSE POSITIVE":                            GREEN_FILL,
    "CONFIRMED MISSING (but correctly noindexed)": GRAY_FILL,
    "MISCONFIGURED — currently indexable":       RED_FILL,
    "MISCONFIGURED — test page is indexable":    RED_FILL,
}
action_fill = {
    "NO ACTION NEEDED":    GREEN_FILL,
    "NO H1 FIX NEEDED":    GRAY_FILL,
    "ADD NOINDEX (not H1)": YELLOW_FILL,
    "DELETE or NOINDEX":   RED_FILL,
}

ws["A1"] = "Superior Water & Air — Missing H1 Plan (Live-Verified)"
ws["A1"].font = TITLE_FONT
ws.merge_cells("A1:H1")
ws["A2"] = (
    "SF flagged 7 pages missing H1 | LIVE VERIFIED against current HTML | "
    "RESULT: 0 pages actually need H1 work. 1 false positive, 4 correctly "
    "noindexed PPCs, 2 misconfigurations to fix (noindex, not H1)."
)
ws["A2"].font = SUBTITLE_FONT
ws.merge_cells("A2:H2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 40

# Executive summary box
ws.cell(row=4, column=1, value="KEY FINDING").fill = SECTION_FILL
ws.cell(row=4, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells("A4:H4")
ws.row_dimensions[4].height = 22

summary_lines = [
    ("The audit said", "Add H1 tags to 7 pages missing them"),
    ("The reality",
     "0 pages need H1 fixes. Every URL in this list is either: "
     "(a) already has H1 that SF missed (1 page), "
     "(b) a PPC page that shouldn't have H1 because it shouldn't be indexed "
     "(4 pages, already correctly noindexed), OR "
     "(c) a misconfigured PPC/test page that needs NOINDEX, not H1 (2 pages)."),
    ("Real work",
     "2 URLs need a noindex config change. That's it. No H1 work at all."),
    ("Time to fix",
     "~5 minutes total (2 URLs × Rank Math/Yoast noindex toggle)"),
]
for r_off, (k, v) in enumerate(summary_lines):
    r = 5 + r_off
    c1 = ws.cell(row=r, column=1, value=k)
    c1.font = Font(name="Calibri", size=10, bold=True)
    c1.alignment = LEFT
    c1.border = BORDER
    c2 = ws.cell(row=r, column=2, value=v)
    c2.font = CELL_FONT
    c2.alignment = LEFT
    c2.border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    ws.row_dimensions[r].height = 46

# Main table
table_start = 5 + len(summary_lines) + 2
ws.cell(row=table_start, column=1, value="PER-URL DETAIL").fill = SECTION_FILL
ws.cell(row=table_start, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells(start_row=table_start, start_column=1,
                end_row=table_start, end_column=8)
ws.row_dimensions[table_start].height = 22

headers = [
    "#", "URL", "Page Type",
    "Live H1 Found?", "Current Robots Meta",
    "Verified Status", "Action", "Rationale",
]
for col, h in enumerate(headers, 1):
    c = ws.cell(row=table_start + 1, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER
ws.row_dimensions[table_start + 1].height = 38

for i, row in enumerate(rows_data):
    r = table_start + 2 + i
    h1_display = ("Yes: " + row["live_h1"]) if row["live_h1_count"] > 0 else "No"
    values = [
        i + 1,
        row["url"],
        row["page_type"],
        h1_display,
        row["robots"],
        row["verified_status"],
        row["action"],
        row["rationale"],
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = CELL_FONT_SM if col in (2, 5, 8) else CELL_FONT
        c.border = BORDER
        if col in (1, 3, 4):
            c.alignment = CENTER
        else:
            c.alignment = LEFT
        if col == 4:
            if row["live_h1_count"] > 0:
                c.fill = GREEN_FILL
            else:
                c.fill = GRAY_FILL
        if col == 6:
            c.fill = status_fill.get(row["verified_status"], GRAY_FILL)
            c.font = Font(name="Calibri", size=10, bold=True)
        if col == 7:
            c.fill = action_fill.get(row["action"], GRAY_FILL)
            c.font = Font(name="Calibri", size=10, bold=True)
    ws.row_dimensions[r].height = 110

# Post-table implementation
impl_start = table_start + 2 + len(rows_data) + 2
ws.cell(row=impl_start, column=1,
         value="IMPLEMENTATION (2 URLS, ~5 MIN)").fill = SECTION_FILL
ws.cell(row=impl_start, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells(start_row=impl_start, start_column=1,
                end_row=impl_start, end_column=8)
ws.row_dimensions[impl_start].height = 22

impl_rows = [
    ("/furnace-ppc-001/",
     "WP admin → edit page → Rank Math/Yoast meta box → Advanced tab → "
     "Robots Meta → check 'No Index'. OR: bulk apply via Rank Math → Titles "
     "& Meta → Post Types → (the post type containing PPC pages) → set "
     "'No Index' to ON."),
    ("/test-lead-form/",
     "Decide with client: (A) if still needed for lead-form testing, noindex "
     "it the same way as the PPC fix above. (B) if no longer needed, delete "
     "the page entirely — let it 404."),
    ("Verification",
     "After applying: open each URL, View Source, confirm "
     "<meta name=\"robots\" content=\"...noindex...\"> is present. "
     "2 weeks later: GSC URL Inspection should show 'Excluded by noindex tag'."),
]
for r_off, (k, v) in enumerate(impl_rows):
    r = impl_start + 1 + r_off
    c1 = ws.cell(row=r, column=1, value=k)
    c1.font = Font(name="Calibri", size=10, bold=True)
    c1.alignment = LEFT
    c1.border = BORDER
    c2 = ws.cell(row=r, column=2, value=v)
    c2.font = CELL_FONT
    c2.alignment = LEFT
    c2.border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    ws.row_dimensions[r].height = 52

# Why not add H1 to PPC pages section
why_start = impl_start + len(impl_rows) + 3
ws.cell(row=why_start, column=1,
         value="WHY NOT JUST ADD H1 TO ALL 7 PAGES?").fill = SECTION_FILL
ws.cell(row=why_start, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells(start_row=why_start, start_column=1,
                end_row=why_start, end_column=8)
ws.row_dimensions[why_start].height = 22

why_notes = [
    ("Scope filter rule (from framework)",
     "Pages without SEO value (PPC, coupons, tests, legal, testimonials hubs, "
     "archives) don't need on-page SEO optimization. Their job is conversion "
     "or internal function, not ranking."),
    ("PPC pages specifically",
     "Adding H1 to a noindexed PPC page does nothing for SEO (it's noindexed — "
     "won't rank) and nothing for conversion (paid traffic doesn't care about "
     "H1 for ranking; it cares about design + offer clarity, which is a CRO "
     "issue, not SEO)."),
    ("Test pages",
     "Shouldn't be indexed, period. H1 is irrelevant — the fix is noindex or "
     "delete."),
    ("Testimonials hub",
     "Already has H1 per live verification. SF was wrong. No action needed."),
    ("Lesson for future audits",
     "When an SF finding flags 'missing H1', always verify against live HTML "
     "before adding to the deliverable. Applied this lesson from the Beehive "
     "H1 audit — 13 of 41 flagged pages had H1 that SF missed."),
]
for r_off, (k, v) in enumerate(why_notes):
    r = why_start + 1 + r_off
    c1 = ws.cell(row=r, column=1, value=k)
    c1.font = Font(name="Calibri", size=10, bold=True)
    c1.alignment = LEFT
    c1.border = BORDER
    c2 = ws.cell(row=r, column=2, value=v)
    c2.font = CELL_FONT
    c2.alignment = LEFT
    c2.border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    ws.row_dimensions[r].height = 50

widths = {
    "A": 28, "B": 50, "C": 20, "D": 18, "E": 22,
    "F": 30, "G": 22, "H": 55,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

wb.save(out)
print(f"Saved: {out}")
print()
print("Real work: 2 URLs need noindex (not H1 fixes)")
print("  /furnace-ppc-001/      → apply noindex")
print("  /test-lead-form/       → delete or noindex")
