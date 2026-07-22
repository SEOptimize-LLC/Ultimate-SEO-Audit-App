"""Build Beehive Plumbing duplicate meta descriptions action plan."""
import pandas as pd
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Beehive/Full Site SEO Audit/"
out = base + "beehive_duplicate_meta_descriptions_plan.xlsx"

df = pd.read_excel(base + "on_page_issues.xlsx", sheet_name="Duplicate Meta Desc")


def classify(url):
    u = url.lower()
    if "/category/" in u and "/page/" in u:
        return "Category Pagination"
    if "/category/" in u:
        return "Category Hub"
    if "water-heater-repair" in u:
        return "Service Page (Duplicate Pair)"
    return "Other"


def extract_page_num(url):
    m = re.search(r"/page/(\d+)/", url)
    return int(m.group(1)) if m else 1


df["Classification"] = df["Address"].apply(classify)
df["Page Num"] = df["Address"].apply(extract_page_num)

# =========================================================================
# Per-URL plan
# =========================================================================
# Actions:
#   NOINDEX   = pagination (same as paginated noindex plan)
#   REWRITE   = category hub has SEO potential, needs unique meta
#   CONSOLIDATE = service page near-duplicate pair (handled elsewhere on roadmap)
# =========================================================================

def get_action_and_new_meta(row):
    url = row["Address"]
    classification = row["Classification"]

    if classification == "Category Pagination":
        return (
            "NOINDEX",
            "(no rewrite \u2014 noindex instead)",
            "Pagination page. No SEO value. Handled via Rank Math site-wide 'Noindex Paginated Pages' toggle. Same fix as roadmap item #8.",
        )

    if classification == "Service Page (Duplicate Pair)":
        return (
            "CONSOLIDATE",
            "(see roadmap item #6 \u2014 consolidate the two pages first, then rewrite)",
            "/water-heater-repair/ and /water-heater-repair-utah/ are 97% near-duplicates (per Near Duplicates Report). Consolidating to one canonical URL resolves the duplicate meta issue automatically. Do NOT rewrite the meta on both \u2014 pick a winner, 301 the loser, then rewrite the meta on the survivor.",
        )

    # Category Hub pages \u2014 need unique, benefit-focused meta
    if classification == "Category Hub":
        # Per-category rewrites
        rewrites = {
            "/category/plumbing/":
                "Browse Beehive Plumbing's articles on general plumbing repairs, installation advice, and troubleshooting for Utah homeowners.",
            "/category/conserve-water/":
                "Read Beehive Plumbing's water conservation guides \u2014 leak detection, efficient fixtures, and bill-reduction tips for Utah homes.",
            "/category/drain-cleaning/":
                "Expert drain cleaning guides from Beehive Plumbing \u2014 clog prevention, tool selection, and maintenance tips for Utah plumbing systems.",
            "/category/water-heaters/":
                "Water heater articles from Beehive Plumbing \u2014 installation guides, repair walkthroughs, and energy-efficiency tips for Utah homes.",
            "/category/plumbing-maintenance/":
                "Preventive plumbing maintenance advice from Beehive Plumbing \u2014 inspection schedules, leak prevention, and upkeep tips for Utah homes.",
            "/category/plumbing-repairs/":
                "Plumbing repair articles from Beehive Plumbing \u2014 leak fixes, fixture replacement, and pipe repair guides for Utah homeowners.",
            "/category/emergency-plumbing/":
                "24/7 emergency plumbing guides from Beehive Plumbing \u2014 handling burst pipes, sewer backups, and urgent issues in Utah homes.",
            "/category/blog/":
                "Plumbing tips, repair guides, and maintenance advice from Beehive Plumbing \u2014 serving Utah homeowners since 1999.",
            "/category/plumbing-company/":
                "Learn more about Beehive Plumbing \u2014 Utah's trusted plumbing company for residential, commercial, and 24/7 emergency services since 1999.",
            "/category/plumbing-service/":
                "Plumbing service articles from Beehive Plumbing \u2014 repair, installation, and maintenance guidance for Utah residential and commercial clients.",
            "/category/plumbing-leaks/":
                "Leak detection and repair guides from Beehive Plumbing \u2014 protect your Utah home from water damage with expert diagnostic tips.",
            "/category/water-softeners/":
                "Water softener guides from Beehive Plumbing \u2014 hard water solutions, softener installation, and maintenance for Utah homeowners.",
        }
        key = None
        for k in rewrites:
            if url.rstrip("/").endswith(k.rstrip("/")):
                key = k
                break
        if key:
            return (
                "REWRITE",
                rewrites[key],
                "Category hub page. Rewrite with unique meta focused on the specific content cluster. Keep indexable \u2014 these hubs can rank for '[category] utah' style navigational queries and serve as topical signal hubs for the cluster.",
            )
        return ("REWRITE", "(write unique meta per category)", "Category hub \u2014 rewrite with unique content cluster description.")

    return ("REVIEW", "(manual review needed)", "Does not fit standard pattern \u2014 manual review.")


plans = df.apply(get_action_and_new_meta, axis=1, result_type="expand")
plans.columns = ["Action", "New Meta", "Rationale"]
df = pd.concat([df, plans], axis=1)

# Verify new meta lengths
df["New Meta Length"] = df["New Meta"].apply(
    lambda x: len(x) if isinstance(x, str) and not x.startswith("(") else 0
)

# Sort: REWRITE (by category) -> CONSOLIDATE -> NOINDEX (by category+page)
action_order = {"REWRITE": 0, "CONSOLIDATE": 1, "NOINDEX": 2, "REVIEW": 3}
df["_sort"] = df["Action"].map(action_order)
df = df.sort_values(by=["_sort", "Address"]).reset_index(drop=True)

# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()
ws = wb.active
ws.title = "Duplicate Meta Action Plan"

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
subtitle_font = Font(name="Calibri", size=10, italic=True, color="595959")
cell_font = Font(name="Calibri", size=10)
cell_font_small = Font(name="Calibri", size=9)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="top", wrap_text=True)
thin = Side(border_style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

red_fill = PatternFill("solid", fgColor="F8CBAD")
yellow_fill = PatternFill("solid", fgColor="FFF2CC")
green_fill = PatternFill("solid", fgColor="C6E0B4")
blue_fill = PatternFill("solid", fgColor="BDD7EE")
section_fill = PatternFill("solid", fgColor="DDEBF7")

action_colors = {
    "REWRITE":     green_fill,
    "NOINDEX":     yellow_fill,
    "CONSOLIDATE": blue_fill,
    "REVIEW":      red_fill,
}
action_font_colors = {
    "REWRITE":     "375623",
    "NOINDEX":     "7F6000",
    "CONSOLIDATE": "1F4E78",
    "REVIEW":      "9C0006",
}

ws["A1"] = "Beehive Plumbing \u2014 Duplicate Meta Descriptions Action Plan"
ws["A1"].font = title_font
ws.merge_cells("A1:I1")
ws["A2"] = (
    "46 URLs share 13 duplicate metas | Analysis: 12 category hubs to REWRITE, "
    "32 pagination pages to NOINDEX, 2 service pages to CONSOLIDATE"
)
ws["A2"].font = subtitle_font
ws.merge_cells("A2:I2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

headers = [
    "#", "URL", "Classification", "Current Meta (shared)",
    "Action", "New Meta (where applicable)", "New Length",
    "Rationale", "Status",
]

for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 38

for i, row in df.iterrows():
    r = i + 5
    current_meta = row["Meta Description 1"] if pd.notna(row["Meta Description 1"]) else ""
    new_meta = row["New Meta"]
    new_len = row["New Meta Length"] if row["New Meta Length"] > 0 else ""
    action = row["Action"]
    values = [
        i + 1,
        row["Address"],
        row["Classification"],
        current_meta,
        action,
        new_meta,
        new_len,
        row["Rationale"],
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col in (4, 6, 8) else cell_font
        c.border = border
        if col in (1, 5, 7, 9):
            c.alignment = center
        else:
            c.alignment = left
        # Action coloring
        if col == 5:
            c.fill = action_colors[action]
            c.font = Font(name="Calibri", size=10, bold=True, color=action_font_colors[action])
        # Highlight REWRITE rows
        if action == "REWRITE" and col == 6:
            c.fill = green_fill
        if action == "CONSOLIDATE" and col == 6:
            c.fill = blue_fill
        # Length flags
        if col == 7 and isinstance(v, int):
            if v > 155:
                c.fill = red_fill
            elif v < 120:
                c.fill = yellow_fill

widths = {
    "A": 4, "B": 52, "C": 22,
    "D": 55, "E": 13, "F": 60,
    "G": 10, "H": 60, "I": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

# Row heights
for i in range(len(df)):
    r = i + 5
    if df.iloc[i]["Action"] == "REWRITE":
        ws.row_dimensions[r].height = 75
    elif df.iloc[i]["Action"] == "CONSOLIDATE":
        ws.row_dimensions[r].height = 65
    else:
        ws.row_dimensions[r].height = 42

ws.freeze_panes = "C5"

# =========================================================================
# SHEET 2 — Duplicate Cluster Summary
# =========================================================================
ws2 = wb.create_sheet("Duplicate Clusters")
ws2["A1"] = "13 Shared Metas \u2014 Cluster Breakdown"
ws2["A1"].font = title_font
ws2.merge_cells("A1:D1")

clusters = df.groupby("Meta Description 1").agg(
    urls=("Address", "count"),
    classifications=("Classification", lambda x: ", ".join(sorted(set(x)))),
).reset_index().sort_values("urls", ascending=False)

cluster_headers = ["# of URLs", "Classification(s)", "Meta (shared)"]
for col, h in enumerate(cluster_headers, 1):
    c = ws2.cell(row=3, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws2.row_dimensions[3].height = 28

for i, row in clusters.iterrows():
    r = i + 4
    values = [
        int(row["urls"]),
        row["classifications"],
        row["Meta Description 1"],
    ]
    for col, v in enumerate(values, 1):
        c = ws2.cell(row=r, column=col, value=v)
        c.font = cell_font
        c.border = border
        if col == 1:
            c.alignment = center
        else:
            c.alignment = left
        if col == 1 and isinstance(v, int):
            if v >= 5:
                c.fill = red_fill
            elif v >= 3:
                c.fill = yellow_fill

ws2.column_dimensions["A"].width = 11
ws2.column_dimensions["B"].width = 35
ws2.column_dimensions["C"].width = 120

for r in range(4, 4 + len(clusters)):
    ws2.row_dimensions[r].height = 48

# =========================================================================
# SHEET 3 — Implementation Guide
# =========================================================================
ws3 = wb.create_sheet("Implementation Guide")
ws3["A1"] = "Implementation Guide \u2014 Duplicate Meta Fix"
ws3["A1"].font = title_font
ws3.merge_cells("A1:B1")

n_rewrite = (df["Action"] == "REWRITE").sum()
n_noindex = (df["Action"] == "NOINDEX").sum()
n_consolidate = (df["Action"] == "CONSOLIDATE").sum()

ctx = [
    ("", ""),
    ("=== THE DATA ===", ""),
    ("Total URLs flagged", "46"),
    ("Unique metas shared", "13"),
    ("Breakdown by action",
     f"REWRITE: {n_rewrite} | NOINDEX: {n_noindex} | CONSOLIDATE: {n_consolidate}"),
    ("Largest cluster", "'Articles about comprehensive plumbing services...' shared by 9 URLs (1 hub + 8 pagination)"),
    ("Second largest", "'Save Utah water with expert plumbing tips...' shared by 9 URLs (1 hub + 8 pagination)"),
    ("", ""),
    ("=== THE PATTERN ===", ""),
    ("What the audit flagged",
     "46 URLs sharing 13 duplicate meta descriptions"),
    ("What the data actually shows",
     "This is the same pattern as SameDay \u2014 mostly pagination inheritance. 32 of 46 URLs are /page/N/ pagination that inherits meta from the category hub."),
    ("The real issue",
     "12 category hubs (plumbing, conserve-water, drain-cleaning, etc.) each have a meta that gets duplicated across all their paginated children. Rewriting metas for pagination is wasted effort \u2014 the fix is to noindex pagination entirely."),
    ("Outlier \u2014 2 service pages",
     "/water-heater-repair/ and /water-heater-repair-utah/ are a separate known issue (97% near-duplicate pair per Near Duplicates Report). These need CONSOLIDATION, not meta rewrites \u2014 already on roadmap as P1 item #6."),
    ("", ""),
    ("=== THE FIX (3 STREAMS) ===", ""),
    ("Stream 1: NOINDEX 32 pagination pages",
     "Apply Rank Math site-wide 'Noindex Paginated Pages' toggle (Titles & Meta \u2192 Misc Pages). Same fix already planned for roadmap item #8 (the 35 paginated category pages). DOING BOTH AT ONCE solves 32 of these 46 duplicates automatically. 5 min."),
    ("Stream 2: REWRITE 12 category hub metas",
     "Write unique meta per category hub (12 rewrites in the main sheet). Focus on: what this cluster covers + Utah local angle + Beehive brand. Keep 150-155 chars. 30 min total."),
    ("Stream 3: CONSOLIDATE 2 water heater repair pages",
     "Follow roadmap item #6 FIRST (consolidate /water-heater-repair/ and /water-heater-repair-utah/ into one canonical). This automatically resolves the remaining duplicate meta issue \u2014 do NOT rewrite both separately."),
    ("", ""),
    ("=== EXECUTION ORDER ===", ""),
    ("1. Do Stream 1 first (5 min)",
     "Toggle pagination noindex \u2014 solves 32 of 46 duplicates. Also resolves roadmap item #8."),
    ("2. Do Stream 3 second (medium effort, separate item)",
     "Consolidate /water-heater-repair-utah/ \u2192 /water-heater-repair/ (or vice versa). Decide based on backlinks, traffic, and GSC performance data."),
    ("3. Do Stream 2 last (30 min)",
     "Rewrite 12 category hub metas using the drafts in the main sheet. Publish via Rank Math on each category taxonomy page."),
    ("", ""),
    ("=== RANK MATH CATEGORY META EDITING ===", ""),
    ("How to edit category hub meta in WP",
     "WordPress admin \u2192 Posts \u2192 Categories \u2192 hover over category name \u2192 Edit. Scroll to the Rank Math SEO section at the bottom. Fill the 'Meta Description' field."),
    ("Alternative (bulk)",
     "If your Rank Math version supports it: Rank Math \u2192 Titles & Meta \u2192 Taxonomies \u2192 Category \u2014 use a custom template. Only works if you want a consistent pattern; for 12 unique metas, edit each category individually."),
    ("", ""),
    ("=== WRITING STANDARDS FOR NEW METAS ===", ""),
    ("Length", "140\u2013155 characters (fits SERP window without truncation)"),
    ("Format", "[Content type/benefit] + [Utah local angle] + [Brand authority signal when relevant]"),
    ("Tone", "Direct, specific, benefit-first. No 'Welcome to our category' fluff. No 'Articles about...' openers (too generic)."),
    ("Brand voice",
     "Avoid 'most trusted' (modality violation per semantic audit). Prefer concrete claims: 'Serving Utah since 1999,' 'Licensed master plumbers,' 'Expert installation,' etc."),
    ("Keywords",
     "Each category should include the cluster term (drain cleaning, water heater, etc.) + 'Utah' modifier + benefit-oriented verb."),
    ("", ""),
    ("=== EXPECTED OUTCOME ===", ""),
    ("Within 4 weeks",
     "GSC 'Duplicate meta descriptions' count drops from 46 to 0. Pagination URLs either show 'Excluded by noindex tag' or disappear from the index entirely."),
    ("Bonus benefit",
     "Category hub metas become CTR assets \u2014 pages like /category/water-heaters/ and /category/drain-cleaning/ can rank for '[topic] utah' navigational queries and serve as topical hubs for the cluster."),
    ("Cross-reference",
     "This plan integrates with roadmap items #6 (water heater consolidation) and #8 (paginated noindex). Fixing those two in combination resolves 34 of the 46 duplicates automatically."),
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

ws3.column_dimensions["A"].width = 48
ws3.column_dimensions["B"].width = 115

for r in range(2, 2 + len(ctx)):
    ws3.row_dimensions[r].height = 36

wb.save(out)
print(f"Saved: {out}")
print(f"Total URLs: {len(df)}")
print(f"Distribution: REWRITE={n_rewrite}, NOINDEX={n_noindex}, CONSOLIDATE={n_consolidate}")
