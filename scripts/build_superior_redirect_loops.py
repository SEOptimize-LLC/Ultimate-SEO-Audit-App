"""Superior Water & Air — Redirect Loops action plan (live-verified).

Audit: "Fix 11 redirect loops" — misleading framing.
Live verification reveals the real issue: 4 blog posts contain broken
external links (to defunct Google+ profile + dead Flickr short URLs).
The other 7 "loops" in the SF export are the external redirect chains
themselves — not loops on Superior's site.

Real work: remove 5 bad external anchors from 4 blog posts (~10 min).
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = (r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/"
        r"Claude/Claude Code + VS Code/SEO/Projects/Projects/"
        r"Ultimate SEO Auditor/Clients/Superior/Full SEO Audit/")
out = base + "superior_redirect_loops_plan.xlsx"


# Per-URL issues (live-verified 2026-04-21)
page_issues = [
    {
        "url": "https://superiorwaterandair.com/how-does-a-tankless-hot-water-heater-work/",
        "page_type": "Blog Post",
        "anchor_text": "+Cassie Costner",
        "bad_href": "https://plus.google.com/110691738932601525395?rel=author",
        "problem_type": "Defunct Google+ author byline",
        "chain": (
            "plus.google.com → workspaceupdates.googleblog.com (302) → "
            "dead destination (302 loop per SF report)"
        ),
        "fix": (
            "Remove the entire anchor. If you want to preserve author "
            "attribution, replace with plain text 'Cassie Costner' or link "
            "to an internal author archive page (/author/cassie-costner/) "
            "if one exists. Google+ shut down in 2019."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/why-is-duct-cleaning-important-for-your-home/",
        "page_type": "Blog Post",
        "anchor_text": "+Cassie Costner",
        "bad_href": "https://plus.google.com/110691738932601525395?rel=author",
        "problem_type": "Defunct Google+ author byline",
        "chain": (
            "plus.google.com → workspaceupdates.googleblog.com (302) → "
            "dead destination"
        ),
        "fix": (
            "Same fix as above: remove anchor or replace with plain text / "
            "internal author page link."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/clean-drinking-water-technologies/",
        "page_type": "Blog Post",
        "anchor_text": "(empty — image anchor)",
        "bad_href": "https://flic.kr/p/9tgBue",
        "problem_type": "Dead Flickr image attribution link",
        "chain": "flic.kr short URL → flickr.com/photo.gne (302, broken)",
        "fix": (
            "Remove the anchor wrapping the image OR update the image "
            "attribution. If image was hotlinked from Flickr (bad practice), "
            "host a local copy and remove the external link entirely."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/cleaning-your-air-conditioner-101/",
        "page_type": "Blog Post",
        "anchor_text": "(empty — image anchor)",
        "bad_href": "https://flic.kr/p/e3tKv3",
        "problem_type": "Dead Flickr image attribution link",
        "chain": "flic.kr → flickr.com/photo.gne (302, broken)",
        "fix": "Same as above — remove anchor or host image locally.",
    },
    {
        "url": "https://superiorwaterandair.com/cleaning-your-air-conditioner-101/",
        "page_type": "Blog Post",
        "anchor_text": "(empty — image anchor)",
        "bad_href": "https://flic.kr/p/5TeTqw",
        "problem_type": "Dead Flickr image attribution link",
        "chain": "flic.kr → flickr.com/photo.gne (302, broken)",
        "fix": "Same as above.",
    },
]


# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()
ws = wb.active
ws.title = "Redirect Loops Plan"

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1F4E78")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="595959")
CELL_FONT = Font(name="Calibri", size=10)
CELL_FONT_SM = Font(name="Calibri", size=9)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
SECTION_FILL = PatternFill("solid", fgColor="DDEBF7")
RED_FILL = PatternFill("solid", fgColor="F8CBAD")
YELLOW_FILL = PatternFill("solid", fgColor="FFF2CC")
GREEN_FILL = PatternFill("solid", fgColor="C6E0B4")
BLUE_FILL = PatternFill("solid", fgColor="D9E1F2")
GRAY_FILL = PatternFill("solid", fgColor="E7E6E6")
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)

ws["A1"] = "Superior Water & Air — Redirect Loops Action Plan"
ws["A1"].font = TITLE_FONT
ws.merge_cells("A1:F1")
ws["A2"] = (
    "SF flagged 11 'redirect loops' | LIVE VERIFIED: these are NOT loops on Superior's "
    "site — they're 5 broken external links across 4 blog posts (defunct Google+ + dead "
    "Flickr URLs). Real fix: remove 5 anchors. ~10 minutes."
)
ws["A2"].font = SUBTITLE_FONT
ws.merge_cells("A2:F2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 36

# Key finding box
ws.cell(row=4, column=1, value="KEY FINDING — WHY THE 11 IS MISLEADING").fill = SECTION_FILL
ws.cell(row=4, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells("A4:F4")
ws.row_dimensions[4].height = 22

summary_lines = [
    ("The audit said",
     "11 redirect loops to fix"),
    ("What the SF export actually contains",
     "4 rows where the Source is a Superior page (the real issue) + 7 rows "
     "where Source is the external URL in the redirect chain. Those 7 rows "
     "are NOT Superior problems — they're Flickr's and Google's redirect "
     "behavior being logged."),
    ("The real problem",
     "4 Superior blog posts link externally to dead URLs: "
     "(a) a defunct Google+ author profile (shut down in 2019) on 2 posts, "
     "(b) dead Flickr image attribution links on 2 posts."),
    ("What breaks",
     "When crawlers (Google, SF) follow these external links, the 302 "
     "redirect chain leads to a dead/loop destination. This doesn't cause "
     "a Google penalty, but it does waste crawl budget + hurts user "
     "experience (broken links in published content)."),
    ("Real work",
     "Remove 5 anchor tags from 4 blog posts. ~10 minutes total. Option to "
     "replace Google+ bylines with internal author page links if author "
     "archive exists."),
]
for r_off, (k, v) in enumerate(summary_lines):
    r = 5 + r_off
    c1 = ws.cell(row=r, column=1, value=k)
    c1.font = BOLD_FONT
    c1.alignment = LEFT
    c1.border = BORDER
    c2 = ws.cell(row=r, column=2, value=v)
    c2.font = CELL_FONT
    c2.alignment = LEFT
    c2.border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 60

# Per-issue table
table_start = 5 + len(summary_lines) + 2
ws.cell(row=table_start, column=1,
         value="PER-ISSUE FIX (5 ANCHORS ACROSS 4 BLOG POSTS)").fill = SECTION_FILL
ws.cell(row=table_start, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells(start_row=table_start, start_column=1,
                end_row=table_start, end_column=6)
ws.row_dimensions[table_start].height = 22

headers = [
    "#", "Superior Blog Post (Source)", "Anchor Text",
    "Bad External URL", "Problem Type", "Recommended Fix",
]
for col, h in enumerate(headers, 1):
    c = ws.cell(row=table_start + 1, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER
ws.row_dimensions[table_start + 1].height = 38

for i, issue in enumerate(page_issues):
    r = table_start + 2 + i
    values = [
        i + 1,
        issue["url"],
        issue["anchor_text"],
        issue["bad_href"],
        issue["problem_type"],
        issue["fix"],
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = CELL_FONT_SM if col in (2, 4, 6) else CELL_FONT
        c.border = BORDER
        c.alignment = CENTER if col == 1 else LEFT
        if col == 5:
            c.fill = YELLOW_FILL
    ws.row_dimensions[r].height = 90

# Implementation
impl_start = table_start + 2 + len(page_issues) + 2
ws.cell(row=impl_start, column=1, value="IMPLEMENTATION STEPS").fill = SECTION_FILL
ws.cell(row=impl_start, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells(start_row=impl_start, start_column=1,
                end_row=impl_start, end_column=6)
ws.row_dimensions[impl_start].height = 22

impl_rows = [
    ("Step 1 — Google+ bylines (2 posts)",
     "Edit /how-does-a-tankless-hot-water-heater-work/ and "
     "/why-is-duct-cleaning-important-for-your-home/. In Gutenberg/classic "
     "editor, find the '+Cassie Costner' author byline, delete the entire "
     "anchor. Replace with either: (a) plain text 'Cassie Costner', (b) "
     "link to /author/cassie-costner/ if an internal author archive exists, "
     "or (c) remove byline entirely."),
    ("Step 2 — Flickr image links (2 posts)",
     "Edit /clean-drinking-water-technologies/ and "
     "/cleaning-your-air-conditioner-101/. Find the images linked to "
     "flic.kr short URLs. Options: (a) if the image is still loading from "
     "Flickr, download and re-upload to WP media library, remove external "
     "link; (b) if the image is already hosted locally, just remove the "
     "anchor wrapping it; (c) if the image isn't appearing anyway, remove "
     "the whole thing."),
    ("Step 3 — Verify",
     "Re-crawl Superior with Screaming Frog after fixes. Expected result: "
     "redirect loops count drops from 11 to 0 (or close to it — some "
     "leftover external chains may remain, but the Superior-originated "
     "problems will be gone)."),
    ("Step 4 — Optional: audit for other stale externals",
     "Search the WP database for other instances of 'plus.google.com', "
     "'flic.kr', or any pre-2019 external references. Ancient blog "
     "migrations often have more of these."),
]
for r_off, (k, v) in enumerate(impl_rows):
    r = impl_start + 1 + r_off
    c1 = ws.cell(row=r, column=1, value=k)
    c1.font = BOLD_FONT
    c1.alignment = LEFT
    c1.border = BORDER
    c2 = ws.cell(row=r, column=2, value=v)
    c2.font = CELL_FONT
    c2.alignment = LEFT
    c2.border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 80

# Why not 11?
why_start = impl_start + len(impl_rows) + 3
ws.cell(row=why_start, column=1,
         value="WHY THE AUDIT COUNT SAYS 11 BUT REAL WORK IS 5").fill = SECTION_FILL
ws.cell(row=why_start, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells(start_row=why_start, start_column=1,
                end_row=why_start, end_column=6)
ws.row_dimensions[why_start].height = 22

why_notes = [
    ("How SF logs redirect chains",
     "When a Superior page links to https://flic.kr/p/X, SF follows: "
     "/flic.kr/X → flickr.com/photo.gne. It logs each hop as a separate "
     "row in the 'redirect chains' export. One bad external link on "
     "Superior's page = 2-3 rows in the report."),
    ("What counts as 'your site's problem'",
     "Only rows where the SOURCE is a Superior URL. The other rows are "
     "what Flickr / Google does — nothing we can fix. The 4 Superior-"
     "sourced rows + 1 multi-hop (/cleaning-your-air-conditioner-101/ has "
     "2 flic.kr links) = 5 actual anchors to fix."),
    ("Lesson",
     "Always examine redirect-chain audit exports before accepting the "
     "row count as 'pages to fix'. Same pattern applies to duplicate "
     "title/meta findings, missing H1 findings, etc. — always trace the "
     "row back to the actual page on the audited site."),
]
for r_off, (k, v) in enumerate(why_notes):
    r = why_start + 1 + r_off
    c1 = ws.cell(row=r, column=1, value=k)
    c1.font = BOLD_FONT
    c1.alignment = LEFT
    c1.border = BORDER
    c2 = ws.cell(row=r, column=2, value=v)
    c2.font = CELL_FONT
    c2.alignment = LEFT
    c2.border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 56

widths = {"A": 32, "B": 45, "C": 22, "D": 40, "E": 28, "F": 50}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

wb.save(out)
print(f"Saved: {out}")
print()
print("Real work: 5 anchor removals across 4 blog posts (~10 min)")
for i, issue in enumerate(page_issues, 1):
    short = issue["url"].replace("https://superiorwaterandair.com", "")
    print(f"  {i}. {short}  ← '{issue['anchor_text'][:25]}' → "
          f"{issue['bad_href'][:40]}")
