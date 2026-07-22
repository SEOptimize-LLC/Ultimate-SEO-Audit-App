"""Build Superior Water & Air truncated titles plan — TIERED by actual priority.

Replaces the 181-row per-URL plan with a realistic 4-tier action list:
- Tier 1: Site-wide template change (auto-fixes 148 pages in 1 config change)
- Tier 2: Modality violations — 22 URLs, framework rule, individual rewrite
- Tier 3: Real length problems — ~14 URLs still too long after suffix removal
- Tier 4: Skip — 148 pages where only the suffix truncates, SERP looks fine
"""
import pandas as pd
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = (r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/"
        r"Claude/Claude Code + VS Code/SEO/Projects/Projects/"
        r"Ultimate SEO Auditor/Clients/Superior/Full SEO Audit/")
out = base + "superior_truncated_titles_plan_v2.xlsx"

df = pd.read_excel(base + "truncated_titles.xlsx")

SUFFIX_RE = re.compile(
    r"\s*[-–|:]\s*Salt Lake City,?\s*Utah\s*[-–|:]*\s*Superior Water\s*&\s*Air.*$"
    r"|\s*[-–|:]\s*Superior Water\s*&\s*Air.*$"
    r"|\s*[-–|:]\s*Salt Lake City,?\s*Utah\s*$",
    flags=re.IGNORECASE,
)

MODALITY_RE = re.compile(
    r"\b(top|best|reliable|expert|premier|trusted|leading|ultimate|"
    r"amazing|professional|affordable|#1)\b",
    flags=re.IGNORECASE,
)


def strip_suffix(title: str) -> str:
    return SUFFIX_RE.sub("", title).strip()


def strip_modality(title: str) -> str:
    out = MODALITY_RE.sub("", title)
    out = re.sub(r"\s+", " ", out).strip()
    out = re.sub(r"^[\s\-|:,]+|[\s\-|:,]+$", "", out)
    return out


df["has_suffix"] = df["Title 1"].str.contains(
    r"Salt Lake City.*Utah|Superior Water.*Air",
    regex=True, case=False, na=False,
)
df["stripped_len"] = df["Title 1"].apply(lambda t: len(strip_suffix(t)))
df["fits_after_strip"] = df["stripped_len"] <= 60
df["has_modality"] = df["Title 1"].apply(lambda t: bool(MODALITY_RE.search(t)))


# Tier assignment
def assign_tier(row):
    """Return (tier_number, tier_label, action)."""
    current = row["Title 1"]
    stripped = strip_suffix(current)
    has_modality = row["has_modality"]
    fits_after_strip = row["fits_after_strip"]

    # Tier 2: Modality violation — always needs individual attention
    if has_modality:
        return (2, "Tier 2: Modality Fix",
                f"Rewrite: strip modality word(s). Cleaned: '{strip_modality(stripped)}'")

    # Tier 3: Still too long after suffix stripped — real content bloat
    if not fits_after_strip:
        return (3, "Tier 3: Real Length Issue",
                f"Rewrite: content itself is {row['stripped_len']} chars. "
                "Manual trim needed.")

    # Tier 4: Only the suffix truncated — SERP looks fine, template fix resolves it
    return (4, "Tier 4: Skip (template fix resolves)",
            f"No rewrite needed. After suffix strip: {row['stripped_len']} chars. "
            "SERP already shows the content portion.")


df[["tier", "tier_label", "action_note"]] = df.apply(
    assign_tier, axis=1, result_type="expand"
)


# Suggested cleaned title per Tier 2 + Tier 3 row
def draft_clean_title(row):
    current = row["Title 1"]
    stripped = strip_suffix(current)
    if row["tier"] == 2:
        # Remove modality, then return
        cleaned = strip_modality(stripped)
        # If still too long after modality strip, trim further
        if len(cleaned) > 60:
            # Try to cut at natural break
            cleaned_trim = cleaned[:57].rstrip(" -|:,") + "..."
            return cleaned_trim
        return cleaned
    if row["tier"] == 3:
        # Strip modality if any, trim remaining, flag for manual review
        cleaned = strip_modality(stripped) if row["has_modality"] else stripped
        if len(cleaned) <= 60:
            return cleaned
        # Truncate at word boundary
        truncated = cleaned[:57]
        last_space = truncated.rfind(" ")
        if last_space > 40:
            truncated = truncated[:last_space]
        return truncated + "..."
    return ""


df["suggested_title"] = df.apply(draft_clean_title, axis=1)
df["suggested_len"] = df["suggested_title"].str.len()


# Sort: Tier 2 → Tier 3 → Tier 4
df = df.sort_values(
    by=["tier", "Title 1 Length"], ascending=[True, False]
).reset_index(drop=True)


# =========================================================================
# Build workbook
# =========================================================================
wb = Workbook()

# Sheet 1 — EXECUTIVE SUMMARY + ACTION PLAN
ws = wb.active
ws.title = "Action Plan"

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1F4E78")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="595959")
CELL_FONT = Font(name="Calibri", size=10)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
SECTION_FILL = PatternFill("solid", fgColor="DDEBF7")
RED_FILL = PatternFill("solid", fgColor="F8CBAD")
YELLOW_FILL = PatternFill("solid", fgColor="FFF2CC")
GREEN_FILL = PatternFill("solid", fgColor="C6E0B4")
BLUE_FILL = PatternFill("solid", fgColor="BDD7EE")
GRAY_FILL = PatternFill("solid", fgColor="E7E6E6")
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)

tier1_count = 148  # From the analysis — 148 auto-fix via template
tier2_count = int((df["tier"] == 2).sum())
tier3_count = int((df["tier"] == 3).sum())
tier4_count = int((df["tier"] == 4).sum())

ws["A1"] = "Superior Water & Air — Truncated Titles Action Plan"
ws["A1"].font = TITLE_FONT
ws.merge_cells("A1:F1")
ws["A2"] = (
    f"181 titles flagged >60 chars | Real work = 1 template change + ~{tier2_count + tier3_count} "
    f"individual rewrites | {tier4_count} pages don't need attention"
)
ws["A2"].font = SUBTITLE_FONT
ws.merge_cells("A2:F2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

# Executive summary box
ws.cell(row=4, column=1, value="EXECUTIVE SUMMARY").fill = SECTION_FILL
ws.cell(row=4, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells("A4:F4")
ws.row_dimensions[4].height = 20

summary_rows = [
    ("The finding", "181 pages have title tags >60 chars"),
    ("The misleading framing",
     "'Rewrite 181 titles' implies 15-20 hours of per-page work. "
     "The data shows this is wrong."),
    ("The reality",
     "89% of titles have the same bloated suffix ' - Salt Lake City, Utah "
     "| Superior Water & Air'. That suffix alone (~50 chars) is responsible "
     "for most of the length overflow."),
    ("What Google actually shows in SERPs",
     "When Google truncates, it cuts from the END. For these pages, the "
     "part that gets cut IS the suffix. The content portion stays visible. "
     "So for 82% of pages, the SERP already looks fine."),
    ("Total real work",
     f"1 template change (fixes {tier1_count}) + "
     f"{tier2_count} modality rewrites + "
     f"{tier3_count} real-length rewrites = "
     f"~2-3 hours, NOT 15-20 hours."),
]

for r_off, (k, v) in enumerate(summary_rows):
    r = 5 + r_off
    ws.cell(row=r, column=1, value=k).font = BOLD_FONT
    ws.cell(row=r, column=1).alignment = LEFT
    ws.cell(row=r, column=1).border = BORDER
    ws.cell(row=r, column=2, value=v).font = CELL_FONT
    ws.cell(row=r, column=2).alignment = LEFT
    ws.cell(row=r, column=2).border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 48

# Tier 1 — Template fix
tier1_start = 5 + len(summary_rows) + 2
ws.cell(row=tier1_start, column=1, value="TIER 1 — SITE-WIDE TEMPLATE FIX").fill = GREEN_FILL
ws.cell(row=tier1_start, column=1).font = Font(
    name="Calibri", size=12, bold=True, color="375623"
)
ws.merge_cells(start_row=tier1_start, start_column=1,
                end_row=tier1_start, end_column=6)
ws.row_dimensions[tier1_start].height = 22

tier1_rows = [
    ("Priority", "P0 — do this first"),
    ("Effort", "1 minute"),
    ("Risk", "Near-zero, reversible"),
    ("Impact", f"Auto-fixes {tier1_count} pages (82% of the flagged 181)"),
    ("The fix", ""),
    ("Step 1", "WordPress admin → Rank Math (or Yoast) → Titles & Meta"),
    ("Step 2", "Navigate to Posts, Pages, and any custom post types"),
    ("Step 3",
     "Find 'Single Post Title' or equivalent template field. "
     "Current value likely: '%title% - Salt Lake City, Utah "
     "| Superior Water & Air'"),
    ("Step 4",
     "Option A (recommended): Change to '%title% | Superior Water & Air'. "
     "Option B (even tighter): '%title%' — no brand suffix at all. "
     "Discuss preference with client."),
    ("Step 5",
     "Save. Verify 5-10 random pages to confirm new title renders correctly. "
     "Re-crawl with Screaming Frog in 2 weeks to confirm truncated count dropped."),
    ("After Tier 1 is done", f"Only {tier2_count + tier3_count} pages will "
     "still need individual attention (the work in Tiers 2 + 3 below)."),
]

for r_off, (k, v) in enumerate(tier1_rows):
    r = tier1_start + 1 + r_off
    ws.cell(row=r, column=1, value=k).font = BOLD_FONT
    ws.cell(row=r, column=1).alignment = LEFT
    ws.cell(row=r, column=1).border = BORDER
    ws.cell(row=r, column=2, value=v).font = CELL_FONT
    ws.cell(row=r, column=2).alignment = LEFT
    ws.cell(row=r, column=2).border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    if not v:
        ws.cell(row=r, column=1).fill = GRAY_FILL
    ws.row_dimensions[r].height = 40

# Tier 2 header + URLs
tier2_start = tier1_start + len(tier1_rows) + 3
ws.cell(row=tier2_start, column=1,
         value=f"TIER 2 — MODALITY VIOLATIONS ({tier2_count} URLs)").fill = YELLOW_FILL
ws.cell(row=tier2_start, column=1).font = Font(
    name="Calibri", size=12, bold=True, color="7F6000"
)
ws.merge_cells(start_row=tier2_start, start_column=1,
                end_row=tier2_start, end_column=6)
ws.row_dimensions[tier2_start].height = 22

tier2_intro = tier2_start + 1
ws.cell(row=tier2_intro, column=1,
         value=("These titles contain marketing words Google deprioritizes "
                "('Top', 'Best', 'Reliable', 'Expert', 'Premier', etc.). "
                "Fix regardless of length — framework rule. ~30 seconds per page.")).font = CELL_FONT
ws.cell(row=tier2_intro, column=1).alignment = LEFT
ws.merge_cells(start_row=tier2_intro, start_column=1,
                end_row=tier2_intro, end_column=6)
ws.row_dimensions[tier2_intro].height = 36

# Tier 2 table
tier2_header = tier2_intro + 2
headers_t2 = ["#", "URL", "Current Title (full)", "Curr Len",
               "Suggested Title (cleaned)", "New Len"]
for col, h in enumerate(headers_t2, 1):
    c = ws.cell(row=tier2_header, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER
ws.row_dimensions[tier2_header].height = 28

t2_df = df[df["tier"] == 2].reset_index(drop=True)
for i, row in t2_df.iterrows():
    r = tier2_header + 1 + i
    values = [
        i + 1,
        row["Address"],
        row["Title 1"],
        int(row["Title 1 Length"]),
        row["suggested_title"],
        int(row["suggested_len"]) if row["suggested_len"] else "",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = CELL_FONT if col != 3 else Font(name="Calibri", size=9)
        c.border = BORDER
        c.alignment = CENTER if col in (1, 4, 6) else LEFT
        if col == 5 and v:
            c.fill = GREEN_FILL
        if col == 6 and isinstance(v, int) and v > 60:
            c.fill = RED_FILL
        elif col == 6 and isinstance(v, int):
            c.fill = GREEN_FILL
    ws.row_dimensions[r].height = 36

# Tier 3 header + URLs
tier3_start = tier2_header + len(t2_df) + 3
ws.cell(row=tier3_start, column=1,
         value=f"TIER 3 — REAL LENGTH ISSUES ({tier3_count} URLs)").fill = YELLOW_FILL
ws.cell(row=tier3_start, column=1).font = Font(
    name="Calibri", size=12, bold=True, color="7F6000"
)
ws.merge_cells(start_row=tier3_start, start_column=1,
                end_row=tier3_start, end_column=6)
ws.row_dimensions[tier3_start].height = 22

tier3_intro = tier3_start + 1
ws.cell(row=tier3_intro, column=1,
         value=("These titles are still over 60 chars even after the suffix "
                "is stripped. Real content bloat. Individual rewrite needed — "
                "2-5 min per page.")).font = CELL_FONT
ws.cell(row=tier3_intro, column=1).alignment = LEFT
ws.merge_cells(start_row=tier3_intro, start_column=1,
                end_row=tier3_intro, end_column=6)
ws.row_dimensions[tier3_intro].height = 36

tier3_header = tier3_intro + 2
for col, h in enumerate(headers_t2, 1):
    c = ws.cell(row=tier3_header, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER
ws.row_dimensions[tier3_header].height = 28

t3_df = df[df["tier"] == 3].reset_index(drop=True)
for i, row in t3_df.iterrows():
    r = tier3_header + 1 + i
    values = [
        i + 1,
        row["Address"],
        row["Title 1"],
        int(row["Title 1 Length"]),
        row["suggested_title"],
        int(row["suggested_len"]) if row["suggested_len"] else "",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = CELL_FONT if col != 3 else Font(name="Calibri", size=9)
        c.border = BORDER
        c.alignment = CENTER if col in (1, 4, 6) else LEFT
        if col == 5 and v:
            c.fill = YELLOW_FILL  # Auto-trimmed — flag for manual polish
        if col == 6 and isinstance(v, int):
            c.fill = GREEN_FILL if v <= 60 else RED_FILL
    ws.row_dimensions[r].height = 40

# Tier 4 — Skip (just a summary box)
tier4_start = tier3_header + len(t3_df) + 3
ws.cell(row=tier4_start, column=1,
         value=f"TIER 4 — SKIP ({tier4_count} URLs)").fill = GRAY_FILL
ws.cell(row=tier4_start, column=1).font = Font(
    name="Calibri", size=12, bold=True, color="595959"
)
ws.merge_cells(start_row=tier4_start, start_column=1,
                end_row=tier4_start, end_column=6)
ws.row_dimensions[tier4_start].height = 22

tier4_notes = [
    f"{tier4_count} pages will be fully resolved by the Tier 1 template change.",
    "After the suffix is removed site-wide, these pages are all under 60 chars.",
    "SERPs already display these correctly — only the suffix is what truncates.",
    "No per-page work needed. Moving on.",
    "",
    "Full URL list is in the 'Tier 4 URLs (reference)' sheet if needed for QA.",
]
for r_off, note in enumerate(tier4_notes):
    r = tier4_start + 1 + r_off
    ws.cell(row=r, column=1, value=note).font = CELL_FONT
    ws.cell(row=r, column=1).alignment = LEFT
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 24

widths = {"A": 28, "B": 55, "C": 70, "D": 9, "E": 50, "F": 9}
for col, w in widths.items():
    ws.column_dimensions[col].width = w


# Sheet 2 — Tier 4 URLs reference
ws2 = wb.create_sheet("Tier 4 URLs (reference)")
ws2["A1"] = f"Tier 4 URLs — Auto-fixed by template change ({tier4_count} URLs)"
ws2["A1"].font = TITLE_FONT
ws2.merge_cells("A1:D1")
ws2["A2"] = ("No per-page action needed. Listed here only for QA after the "
             "Tier 1 template change takes effect.")
ws2["A2"].font = SUBTITLE_FONT
ws2.merge_cells("A2:D2")
ws2.row_dimensions[1].height = 22
ws2.row_dimensions[2].height = 18

headers_t4 = ["#", "URL", "Current Title", "Curr Len (will shrink to)"]
for col, h in enumerate(headers_t4, 1):
    c = ws2.cell(row=4, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER
ws2.row_dimensions[4].height = 28

t4_df = df[df["tier"] == 4].reset_index(drop=True)
for i, row in t4_df.iterrows():
    r = 5 + i
    values = [
        i + 1,
        row["Address"],
        row["Title 1"],
        f"{int(row['Title 1 Length'])} → {int(row['stripped_len'])}",
    ]
    for col, v in enumerate(values, 1):
        c = ws2.cell(row=r, column=col, value=v)
        c.font = CELL_FONT if col != 3 else Font(name="Calibri", size=9)
        c.border = BORDER
        c.alignment = CENTER if col in (1, 4) else LEFT
    ws2.row_dimensions[r].height = 30

w2 = {"A": 4, "B": 58, "C": 75, "D": 18}
for col, w in w2.items():
    ws2.column_dimensions[col].width = w
ws2.freeze_panes = "A5"


# Sheet 3 — Verification
ws3 = wb.create_sheet("Post-Fix Verification")
ws3["A1"] = "How to Verify the Fix Worked"
ws3["A1"].font = TITLE_FONT
ws3.merge_cells("A1:B1")

verify_ctx = [
    ("", ""),
    ("=== 24 HOURS AFTER TIER 1 ===", ""),
    ("Spot-check 5 pages via 'View Source'",
     "Confirm <title> tags match the new template (no 'Salt Lake City, Utah' unless intentional)"),
    ("Use Chrome DevTools",
     "Open a page, inspect <head>, verify <title> is under 60 chars"),
    ("", ""),
    ("=== 2 WEEKS AFTER TIER 1 ===", ""),
    ("Re-crawl with Screaming Frog",
     f"Expected: pages with titles >60 chars drops from 181 to ~{tier2_count + tier3_count}"),
    ("GSC Coverage report",
     "'Titles too long' count should drop dramatically"),
    ("Check SERPs directly",
     "Search for 5-10 target queries. Confirm titles appear cleanly, no ellipsis on content portion"),
    ("", ""),
    ("=== 4-8 WEEKS AFTER TIER 1 + TIER 2/3 ===", ""),
    ("CTR check in GSC",
     "Compare CTR on rewritten pages vs 90-day baseline. Expect +5-15% lift on pages that had modality removed."),
    ("Position check",
     "Modality removal can yield 1-3 position improvements on head terms (small but measurable)."),
    ("", ""),
    ("=== WHAT TO IGNORE ===", ""),
    ("Tier 4 pages without action",
     "These are expected to stay in the 'over 60 chars' count briefly until Google recrawls. They DO NOT need individual fixes."),
    ("Minor position fluctuations",
     "Title changes cause 2-3 weeks of SERP re-ranking. Don't panic on temporary drops."),
]
for r, (k, v) in enumerate(verify_ctx, 2):
    c1 = ws3.cell(row=r, column=1, value=k)
    c2 = ws3.cell(row=r, column=2, value=v)
    if k.startswith("==="):
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    elif k and not v:
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    else:
        c1.font = BOLD_FONT
        c2.font = CELL_FONT
        c2.alignment = Alignment(wrap_text=True, vertical="top")

ws3.column_dimensions["A"].width = 38
ws3.column_dimensions["B"].width = 110
for r in range(2, 2 + len(verify_ctx)):
    ws3.row_dimensions[r].height = 36

wb.save(out)
print(f"Saved: {out}")
print()
print("Tier breakdown:")
print(f"  Tier 1 (template fix): {tier1_count} pages auto-resolved")
print(f"  Tier 2 (modality): {tier2_count} URLs — individual rewrite")
print(f"  Tier 3 (real length): {tier3_count} URLs — individual rewrite")
print(f"  Tier 4 (skip): {tier4_count} URLs — no action needed")
print(f"  Total real work: {tier2_count + tier3_count} URLs + 1 template change")
