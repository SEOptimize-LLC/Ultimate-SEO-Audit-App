"""Build the Comfort Solutions blog/category URL duplication implementation plan.

Generates: Clients/Comfort/Full SEO Audit/comfort_blog_category_duplication_plan.xlsx

Source issue (per comfort_technical_onpage_audit.md, P2 priority #2 + roadmap row #8):
    "Fix blog/category URL duplication — /blog/ and /category/blog/ serve identical content"
    Detected via Near Duplicates report (74 near-duplicate pairs). 10 pages affected.

Live verification (2026-04-27):
    /blog/* — 200, indexable, self-canonical (correct)
    /category/blog/* — 200, follow,noindex (already resolved during missing-meta fix)

Outcome: Issue is RESOLVED at the indexation level. No further action required.
"""

from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "Clients" / "Comfort" / "Full SEO Audit" / "comfort_blog_category_duplication_plan.xlsx"


def build_action_plan_data() -> list[list]:
    """Per-URL action rows for sheet 1."""
    header = [
        "#",
        "URL",
        "Action",
        "Live HTTP",
        "Current Robots Meta",
        "Current Canonical",
        "Rationale",
        "Status",
    ]

    rows = [
        # /blog/* — canonical (no action)
        [
            1,
            "https://www.comfortsolutionsutah.com/blog/",
            "KEEP (CANONICAL)",
            200,
            "follow, index, max-snippet:-1, max-video-preview:-1, max-image-preview:large",
            "https://www.comfortsolutionsutah.com/blog/",
            "Canonical version. Indexable, self-canonical. No change needed.",
            "Done",
        ],
        # /category/blog/ — already noindexed
        [
            2,
            "https://www.comfortsolutionsutah.com/category/blog/",
            "ALREADY FIXED",
            200,
            "follow, noindex",
            "(none / not set)",
            "Already NOINDEXED as part of missing-meta-descriptions fix. Google will drop from index. Duplication resolved.",
            "Done",
        ],
        # /blog/page/2-5 — canonical pagination
        *[
            [
                idx + 3,
                f"https://www.comfortsolutionsutah.com/blog/page/{n}/",
                "KEEP (CANONICAL)",
                200,
                "follow, index, max-snippet:-1, max-video-preview:-1, max-image-preview:large",
                f"https://www.comfortsolutionsutah.com/blog/page/{n}/",
                "Canonical pagination. Indexable, self-canonical. No change needed.",
                "Done",
            ]
            for idx, n in enumerate([2, 3, 4, 5])
        ],
        # /category/blog/page/2-5 — already noindexed
        *[
            [
                idx + 7,
                f"https://www.comfortsolutionsutah.com/category/blog/page/{n}/",
                "ALREADY FIXED",
                200,
                "follow, noindex",
                "(none / not set)",
                "Already NOINDEXED. Pagination duplicate resolved.",
                "Done",
            ]
            for idx, n in enumerate([2, 3, 4, 5])
        ],
    ]

    return [header, *rows]


def build_analysis_data() -> list[list[str]]:
    """Two-column analysis rows for sheet 2."""
    return [
        ["Comfort Solutions — Blog/Category URL Duplication Analysis"],
        [""],
        ["Source audit", "comfort_technical_onpage_audit.md (April 9, 2026), Section 7 Near Duplicates + P2 Priority #2"],
        ["Roadmap entry", "comfort_combined_roadmap.md row #8 (P2)"],
        ["Detection method", "Screaming Frog Near Duplicates report — 74 near-duplicate pairs detected site-wide; this issue accounts for 5 of them (1 hub + 4 pagination pairs)"],
        ["", ""],
        ["", ""],
        ["SF crawl finding", "/blog/ and /category/blog/ serve identical content (100% match). /blog/page/3-5/ each match their /category/blog/page/ equivalents at 100%. Total: 10 pages affected (5 canonical + 5 duplicate)."],
        ["Live verification (2026-04-27)", "ALREADY RESOLVED. All 5 /category/blog/* URLs are NOINDEXED with 'follow, noindex' robots meta. The 5 /blog/* canonical versions are indexable with proper self-canonical tags."],
        ["Verification method", "Live HTTP fetch + HTML parse for canonical link element and robots meta tag on all 10 URLs (2026-04-27, 18 days after the original audit)."],
        ["", ""],
        ["", ""],
        ["Decision", "No further action required. NOINDEX on /category/blog/* (applied during the missing-meta-descriptions fix on 2026-04-27) resolves the duplication at the indexation level. Google will drop the duplicate URLs from its index; only /blog/* remains as the indexable canonical version."],
        ["Why NOINDEX is sufficient", "/category/blog/* are auto-generated WordPress category archives. They have no inbound backlinks worth preserving and no organic traffic of their own (they were duplicating /blog/* signals). NOINDEX removes them from competition without needing 301 infrastructure. Adding a 301 would be additive cleanup, not a correction."],
        ["Why this matches existing framework", "Same pattern applied across Comfort: utility pages (pagination, taxonomy archives, category archives) get NOINDEX, not canonical-tag rewrites or 301 redirects. Cleaner, fewer moving parts, no redirect-chain risk."],
        ["", ""],
        ["", ""],
        ["Optional cleanup (low priority)", "If 301 redirects from /category/blog/* to /blog/* are desired for URL hygiene, they can be added later. NOT REQUIRED for SEO — NOINDEX already prevents indexation conflict. Skip unless URL hygiene is a stated priority."],
        ["Sitemap check", "Confirm /category/blog/* URLs are NOT included in any XML sitemap. Auto-generated by WordPress, so check Yoast/Rank Math sitemap output to confirm category archives are excluded. Sitemap mismatch (URL noindexed but listed in sitemap) wastes crawl budget."],
        ["", ""],
        ["", ""],
        ["Implementation status", "RESOLVED via missing-meta-descriptions fix (2026-04-27 verification confirmed)."],
        ["Related sister issue", "UTM parameter canonicalization on homepage variants (separate audit item, same theme — multiple URL variants serving identical content). 69% of homepage clicks currently go to UTM variants. Tracked separately on the roadmap."],
    ]


def write_workbook(action_data: list[list], analysis_data: list[list[str]]) -> None:
    """Write both sheets and apply formatting."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        # Sheet 1: pad to 8 columns, write headers as data rows so we control formatting
        max_cols = 8
        title_row = ["Comfort Solutions — Blog/Category URL Duplication (Verified)"] + [""] * (max_cols - 1)
        subtitle = (
            "SF flagged 10 pages where /blog/ and /category/blog/ serve 100% identical content. "
            "VERIFIED live (2026-04-27): the /category/blog/* side is ALREADY NOINDEXED. "
            "Duplication is resolved at the indexation level. No further action required."
        )
        subtitle_row = [subtitle] + [""] * (max_cols - 1)
        spacer = [""] * max_cols

        full_rows = [title_row, subtitle_row, spacer]
        for row in action_data:
            padded = list(row) + [""] * (max_cols - len(row))
            full_rows.append(padded)

        df_action = pd.DataFrame(full_rows)
        df_action.to_excel(
            writer,
            sheet_name="Blog Category Duplication Plan",
            index=False,
            header=False,
        )

        # Sheet 2: 2 columns
        rows2 = [list(r) + [""] * (2 - len(r)) for r in analysis_data]
        df_analysis = pd.DataFrame(rows2)
        df_analysis.to_excel(
            writer,
            sheet_name="Analysis & Implementation",
            index=False,
            header=False,
        )

    apply_formatting()


def apply_formatting() -> None:
    """Apply colors, borders, widths, heights to both sheets."""
    wb = load_workbook(OUTPUT_PATH)

    # ===== Sheet 1: Action Plan =====
    ws = wb["Blog Category Duplication Plan"]

    # Title
    ws.merge_cells("A1:H1")
    title = ws["A1"]
    title.font = Font(bold=True, size=14, color="FFFFFF")
    title.fill = PatternFill("solid", fgColor="1F4E78")
    title.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 28

    # Subtitle
    ws.merge_cells("A2:H2")
    subtitle = ws["A2"]
    subtitle.font = Font(italic=True, size=10)
    subtitle.fill = PatternFill("solid", fgColor="E7E6E6")
    subtitle.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[2].height = 50

    # Header row is row 4 (after title/subtitle/spacer)
    header_fill = PatternFill("solid", fgColor="2E75B6")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    for col_idx in range(1, 9):
        cell = ws.cell(row=4, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[4].height = 30

    # Data rows: 5..14 (10 data rows)
    thin = Side(border_style="thin", color="CCCCCC")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    action_colors = {
        "KEEP (CANONICAL)": "C6EFCE",   # green — no action needed
        "ALREADY FIXED":    "FFEB9C",   # yellow — already resolved
    }

    for row_idx in range(5, 5 + 10):
        action = ws.cell(row=row_idx, column=3).value
        fill_color = action_colors.get(action)
        for col_idx in range(1, 9):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            cell.font = Font(size=10)
            cell.border = border
            if col_idx == 3 and fill_color:
                cell.fill = PatternFill("solid", fgColor=fill_color)
                cell.font = Font(size=10, bold=True)

    # Column widths
    widths = {"A": 5, "B": 55, "C": 22, "D": 11, "E": 35, "F": 35, "G": 50, "H": 12}
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width

    for row_idx in range(5, 5 + 10):
        ws.row_dimensions[row_idx].height = 50

    # ===== Sheet 2: Analysis =====
    ws2 = wb["Analysis & Implementation"]
    ws2.merge_cells("A1:B1")
    t2 = ws2["A1"]
    t2.font = Font(bold=True, size=14, color="FFFFFF")
    t2.fill = PatternFill("solid", fgColor="1F4E78")
    t2.alignment = Alignment(horizontal="left", vertical="center")
    ws2.row_dimensions[1].height = 28

    # Bold labels in column A; wrap-format both columns
    last_row = ws2.max_row
    for row_idx in range(2, last_row + 1):
        label_cell = ws2.cell(row=row_idx, column=1)
        value_cell = ws2.cell(row=row_idx, column=2)
        if label_cell.value:
            label_cell.font = Font(bold=True, size=11)
            label_cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        if value_cell.value:
            value_cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            value_cell.font = Font(size=10)
            ws2.row_dimensions[row_idx].height = 50

    ws2.column_dimensions["A"].width = 32
    ws2.column_dimensions["B"].width = 95

    wb.save(OUTPUT_PATH)


def main() -> None:
    action_data = build_action_plan_data()
    analysis_data = build_analysis_data()
    write_workbook(action_data, analysis_data)
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Size:  {OUTPUT_PATH.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
