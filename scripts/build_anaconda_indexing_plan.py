"""Build Anaconda — Not-Indexed Pages Implementation Plan.

Multi-tab Excel grouping the 42 'Discovered — currently not indexed' URLs
by Recommended Action Type for parallel team execution.
"""
import pandas as pd
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

src = (r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/"
       r"Claude/Claude Code + VS Code/SEO/Projects/Projects/"
       r"Ultimate SEO Auditor/Clients/Anaconda/Anaconda Indexing.xlsx")
out = (r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/"
       r"Claude/Claude Code + VS Code/SEO/Projects/Projects/"
       r"Ultimate SEO Auditor/Clients/Anaconda/"
       r"Anaconda_NotIndexed_Implementation_Plan.xlsx")

df = pd.read_excel(src, sheet_name="Discovered - currently not inde")


# =========================================================================
# Bucket classifier
# =========================================================================
def classify_bucket(action: str):
    """Return (bucket_key, bucket_label, execution_notes)."""
    if not isinstance(action, str):
        return ("unclassified", "Unclassified", "Manual review needed")
    a = action.lower()

    # Content writing bucket
    if "add 500" in a or "1000 words" in a or "optimze" in a or "optimize by add" in a:
        return (
            "content_writing",
            "1. Content Writing + Request Indexing",
            "Write 500-1000 words of unique content with internal linking and FAQ. "
            "Then request indexing in GSC. HIGH effort — 2-3 hours per URL.",
        )

    # A/B test variants
    if "a/b test variant" in a:
        return (
            "ab_variants",
            "2. A/B Test Variants — Delete or Noindex",
            "Decision gate FIRST: Is this A/B test still active? "
            "If YES → noindex via Shopify theme or SEO plugin. "
            "If NO → delete the page. ~2 min per URL after decision.",
        )

    # PR landing pages
    if "pr landing page" in a and "variant" not in a:
        return (
            "pr_landing_noindex",
            "3. PR Landing Pages — Noindex",
            "Keep page live for PR campaigns but set to NOINDEX. "
            "Batch apply via Shopify SEO app or theme edit. "
            "~1 min per URL.",
        )

    # Internal linking
    if "add internal link" in a and "words" not in a:
        return (
            "internal_linking",
            "4. Add Internal Links + Request Indexing",
            "Page already has content. Add 2 contextual internal links from "
            "the specified source pages. Then request indexing in GSC. "
            "~10 min per URL.",
        )

    # Test page / copy-of / duplicate → delete
    if (("test page" in a) or ("copy-of" in a.lower()) or
            ("can be deleted" in a and "duplicate" in a)):
        return (
            "delete_test_pages",
            "5. Delete Test / Duplicate Pages",
            "Delete the page entirely from Shopify admin. Test pages and "
            "'copy-of-' slugs serve no purpose. ~2 min per URL.",
        )

    # 301 redirect for duplicates
    if "301 redirect" in a or "add 301" in a:
        return (
            "redirect_duplicates",
            "6. 301 Redirect Duplicates",
            "Add 301 redirect in Shopify → URL Redirects. Point duplicate "
            "to the canonical product/page. ~5 min per URL.",
        )

    # Empty page / empty collection decisions
    if "empty" in a or "no products" in a:
        return (
            "empty_page_decision",
            "7. Empty Page / Collection — Decision Gate",
            "BUSINESS DECISION REQUIRED: Is this page/collection strategically "
            "important? If YES → populate with content/products. If NO → delete. "
            "Effort varies by decision.",
        )

    # A/B variants on PR pages (fallback catch)
    if "variant" in a:
        return (
            "ab_variants",
            "2. A/B Test Variants — Delete or Noindex",
            "A/B test artifact. Decide active/inactive, then delete or noindex.",
        )

    # Catch-all
    if "noindex" in a:
        return (
            "pr_landing_noindex",
            "3. PR Landing Pages — Noindex",
            "Set to NOINDEX. Review original action column for context.",
        )

    return ("unclassified", "8. Unclassified — Manual Review",
            "Review original action column. Classifier did not match a known pattern.")


df[["bucket_key", "bucket_label", "execution_notes"]] = df["Recommended Action"].apply(
    lambda a: pd.Series(classify_bucket(a))
)

# Custom order for tabs (by execution priority: quick wins first, content last)
bucket_order = [
    ("pr_landing_noindex", "3. PR Landing Pages — Noindex"),
    ("ab_variants", "2. A/B Test Variants — Delete or Noindex"),
    ("delete_test_pages", "5. Delete Test / Duplicate Pages"),
    ("redirect_duplicates", "6. 301 Redirect Duplicates"),
    ("internal_linking", "4. Add Internal Links + Request Indexing"),
    ("empty_page_decision", "7. Empty Page / Collection — Decision Gate"),
    ("content_writing", "1. Content Writing + Request Indexing"),
    ("unclassified", "8. Unclassified — Manual Review"),
]

# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1F4E78")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="595959")
CELL_FONT = Font(name="Calibri", size=10)
CELL_FONT_SM = Font(name="Calibri", size=9)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
SECTION_FILL = PatternFill("solid", fgColor="DDEBF7")
RED_FILL = PatternFill("solid", fgColor="F8CBAD")
ORANGE_FILL = PatternFill("solid", fgColor="FCE4D6")
YELLOW_FILL = PatternFill("solid", fgColor="FFF2CC")
GREEN_FILL = PatternFill("solid", fgColor="C6E0B4")
BLUE_FILL = PatternFill("solid", fgColor="D9E1F2")
GRAY_FILL = PatternFill("solid", fgColor="E7E6E6")
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)

# Bucket tab colors for visual distinction
bucket_colors = {
    "pr_landing_noindex":  GREEN_FILL,
    "ab_variants":         GREEN_FILL,
    "delete_test_pages":   GREEN_FILL,
    "redirect_duplicates": GREEN_FILL,
    "internal_linking":    YELLOW_FILL,
    "empty_page_decision": ORANGE_FILL,
    "content_writing":     RED_FILL,
    "unclassified":        GRAY_FILL,
}


# ==========================================================================
# Sheet 1 — Overview / Summary
# ==========================================================================
ws = wb.active
ws.title = "Overview"

ws["A1"] = "Anaconda — Not-Indexed Pages Implementation Plan"
ws["A1"].font = TITLE_FONT
ws.merge_cells("A1:E1")
ws["A2"] = (
    f"42 URLs from 'Discovered — currently not indexed' in GSC | "
    f"Grouped by Recommended Action Type across {len(bucket_order)} tabs"
)
ws["A2"].font = SUBTITLE_FONT
ws.merge_cells("A2:E2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

ws.cell(row=4, column=1, value="EXECUTION PRIORITY").fill = SECTION_FILL
ws.cell(row=4, column=1).font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
ws.merge_cells("A4:E4")
ws.row_dimensions[4].height = 20

headers_overview = ["Tab", "Action Type", "URLs", "Est. Effort", "Priority"]
for col, h in enumerate(headers_overview, 1):
    c = ws.cell(row=5, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER
ws.row_dimensions[5].height = 28

effort_lookup = {
    "pr_landing_noindex":  ("~10 min batch", "P1 — Quick Win"),
    "ab_variants":         ("~20 min after decision", "P1 — Quick Win"),
    "delete_test_pages":   ("~10 min", "P1 — Quick Win"),
    "redirect_duplicates": ("~5 min", "P1 — Quick Win"),
    "internal_linking":    ("~30 min total", "P2 — Fast Medium"),
    "empty_page_decision": ("Variable (decision gate)", "P2 — Decision"),
    "content_writing":     ("20-30 hours writing", "P3 — Heavy Lift"),
    "unclassified":        ("Manual review", "P0 — Review First"),
}

row_num = 6
for idx, (key, label) in enumerate(bucket_order, 1):
    bucket_df = df[df["bucket_key"] == key]
    if bucket_df.empty:
        continue
    effort, priority = effort_lookup.get(key, ("—", "—"))
    values = [
        f"Tab {idx}",
        label,
        len(bucket_df),
        effort,
        priority,
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=row_num, column=col, value=v)
        c.font = CELL_FONT
        c.border = BORDER
        c.alignment = CENTER if col in (1, 3) else LEFT
        if col == 2:
            c.fill = bucket_colors.get(key, GRAY_FILL)
            c.font = Font(name="Calibri", size=10, bold=True)
        if col == 5:
            if "P0" in v or "P1" in v:
                c.fill = GREEN_FILL
            elif "P2" in v:
                c.fill = YELLOW_FILL
            elif "P3" in v:
                c.fill = RED_FILL
    ws.row_dimensions[row_num].height = 32
    row_num += 1

# Recommended order section
order_start = row_num + 2
ws.cell(row=order_start, column=1, value="RECOMMENDED EXECUTION ORDER").fill = SECTION_FILL
ws.cell(row=order_start, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells(start_row=order_start, start_column=1, end_row=order_start, end_column=5)
ws.row_dimensions[order_start].height = 20

order_notes = [
    ("Step 1 — Quick wins (Tabs 3, 2, 5, 6, 4)",
     "Clear ~27 of 42 URLs in ~1-2 hours. PR noindex, A/B cleanup, test page "
     "deletion, 301 redirect, internal linking. All low-risk, low-effort."),
    ("Step 2 — Decision gate (Tab 7)",
     "2 empty page/collection decisions. 15-min review meeting: keep & "
     "populate, or delete. Assign owner."),
    ("Step 3 — Content writing (Tab 1)",
     "13 URLs each needing 500-1000 words. Heavy lift — batch across the "
     "content team. 2-3 hours per URL = 20-30 hours total. Can parallelize."),
    ("Step 4 — Request indexing in GSC",
     "After Steps 1-3 are done and content is live, submit updated URLs "
     "via GSC URL Inspection → Request Indexing. Google typically recrawls "
     "within 3-7 days."),
    ("Step 5 — Verify 2-4 weeks later",
     "Re-check GSC Coverage report. 'Discovered — currently not indexed' "
     "count should drop dramatically as content-expanded pages get crawled "
     "and noindexed pages are removed from the 'discovered' queue."),
]

for i, (k, v) in enumerate(order_notes, 1):
    r = order_start + i
    c1 = ws.cell(row=r, column=1, value=k)
    c1.font = BOLD_FONT
    c1.alignment = LEFT
    c1.border = BORDER
    c2 = ws.cell(row=r, column=2, value=v)
    c2.font = CELL_FONT
    c2.alignment = LEFT
    c2.border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    ws.row_dimensions[r].height = 48

ws.column_dimensions["A"].width = 14
ws.column_dimensions["B"].width = 48
ws.column_dimensions["C"].width = 8
ws.column_dimensions["D"].width = 26
ws.column_dimensions["E"].width = 22


# ==========================================================================
# Per-bucket tabs
# ==========================================================================
def build_bucket_tab(wb, tab_name, bucket_df, bucket_label, bucket_key):
    ws = wb.create_sheet(tab_name)
    ws["A1"] = bucket_label
    ws["A1"].font = TITLE_FONT
    ws.merge_cells("A1:E1")

    notes = bucket_df["execution_notes"].iloc[0] if len(bucket_df) else ""
    ws["A2"] = f"{len(bucket_df)} URL(s) | {notes}"
    ws["A2"].font = SUBTITLE_FONT
    ws.merge_cells("A2:E2")
    ws.row_dimensions[1].height = 22
    ws.row_dimensions[2].height = 40

    headers = ["#", "Type", "URL", "Specific Recommended Action", "Status"]
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=4, column=col, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER
    ws.row_dimensions[4].height = 28

    for i, (_, row) in enumerate(bucket_df.iterrows()):
        r = 5 + i
        values = [
            i + 1,
            row["Type"],
            row["URL"],
            row["Recommended Action"],
            "Not Started",
        ]
        for col, v in enumerate(values, 1):
            c = ws.cell(row=r, column=col, value=v)
            c.font = CELL_FONT_SM if col in (3, 4) else CELL_FONT
            c.border = BORDER
            c.alignment = CENTER if col in (1, 2, 5) else LEFT
            if col == 2:
                # Type-based color
                if v == "pages":
                    c.fill = BLUE_FILL
                elif v == "collections":
                    c.fill = ORANGE_FILL
                elif v == "blogs":
                    c.fill = GREEN_FILL
        ws.row_dimensions[r].height = 48

    widths = {"A": 4, "B": 14, "C": 75, "D": 70, "E": 13}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A5"


# Safe tab-name builder (Excel max 31 chars, no special chars)
def safe_tab_name(label, max_len=31):
    # Remove leading "N. " numbering for a cleaner tab title later if wanted
    name = re.sub(r'[\\/\[\]\*\?:]', '', label)
    return name[:max_len]


for idx, (key, label) in enumerate(bucket_order, 1):
    bucket_df = df[df["bucket_key"] == key]
    if bucket_df.empty:
        continue
    tab_name = safe_tab_name(label)
    build_bucket_tab(wb, tab_name, bucket_df, label, key)


wb.save(out)
print(f"Saved: {out}")
print()
print(f"Tabs created: {len([k for k, _ in bucket_order if not df[df['bucket_key'] == k].empty])}")
print()
print("Bucket summary:")
for key, label in bucket_order:
    bucket_df = df[df["bucket_key"] == key]
    if not bucket_df.empty:
        print(f"  {label}: {len(bucket_df)} URLs")
