"""
Build Excel action plan for Superior Water & Air — 20 WP Engine staging links.

Data source: Clients/Superior/Full SEO Audit/wpengine_staging_links.xlsx
  - 20 links in the live site HTML still point to the old superiorwatair.wpengine.com
    staging domain. These currently redirect (via the staging domain's blanket 301
    back to production) but the path often doesn't match, so users land on the
    homepage or on an incorrect service page instead of the intended destination.

Output: Clients/Superior/Full SEO Audit/superior_staging_links_plan.xlsx
"""
from __future__ import annotations

import io
import os
import sys
from collections import defaultdict
from datetime import date
from urllib.parse import urlparse

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
SRC = os.path.join(ROOT, "Clients/Superior/Full SEO Audit/wpengine_staging_links.xlsx")
OUT = os.path.join(ROOT, "Clients/Superior/Full SEO Audit/superior_staging_links_plan.xlsx")

PROD_ROOT = "https://superiorwaterandair.com"


def proposed_target(staging_url: str, current_resolved: str) -> tuple[str, str, str]:
    """
    Return (proposed_production_url, confidence, rationale).
    confidence: High | Medium | Low
    """
    path = urlparse(staging_url).path or "/"
    # Stripping /YYYY/MM/ blog prefix if present (old WordPress date-based permalinks)
    parts = [p for p in path.strip("/").split("/") if p]

    # Homepage-only staging link → intended homepage
    if path in ("", "/"):
        return (
            f"{PROD_ROOT}/",
            "High",
            "Staging URL was just the root — intent was homepage. Replace with production root.",
        )

    # Truncated / broken URL like /hvac/furnac
    if parts and parts[-1] in {"furnac"}:
        return (
            f"{PROD_ROOT}/hvac/furnace-repair/",
            "Medium",
            "Staging URL is truncated (/hvac/furnac). Most likely intended /hvac/furnace-repair/ based on service lineup. Verify in HTML before committing.",
        )

    # Date-prefixed blog URL like /2018/08/slug/
    if (
        len(parts) >= 3
        and parts[0].isdigit()
        and len(parts[0]) == 4
        and parts[1].isdigit()
        and len(parts[1]) == 2
    ):
        slug = "/".join(parts[2:])
        prod = f"{PROD_ROOT}/{slug}/"
        return (
            prod,
            "High",
            "Old WordPress date-based permalink. Production uses slug-only URLs — strip /YYYY/MM/.",
        )

    # If staging path resolves on production (same path exists), link should use it
    # Based on the current_resolved behavior:
    #   - If staging /X resolves to production /X → safe to swap
    #   - If staging /X resolves to production /Y (a 301 target) → the production
    #     URL /X probably doesn't exist or 301s. Use the RESOLVED URL as the target.
    staging_path = path
    direct_prod = f"{PROD_ROOT}{staging_path}"

    if current_resolved and current_resolved.rstrip("/") == direct_prod.rstrip("/"):
        return (
            direct_prod,
            "High",
            "Staging path exists identically on production. Swap the domain only.",
        )
    if current_resolved == f"{PROD_ROOT}/":
        # Staging path doesn't exist on production → resolves to homepage via 301.
        # Link equity is being lost. Manual judgment needed.
        return (
            f"{PROD_ROOT}/",
            "Low",
            f"Staging path '{staging_path}' does not exist on production (currently 301s to homepage). Manual decision needed: point to the closest relevant production page, or remove the link entirely.",
        )
    if current_resolved and current_resolved.startswith(PROD_ROOT):
        return (
            current_resolved,
            "High",
            "Staging path 301s to a specific production page. Use that production URL directly — skip the staging hop.",
        )
    return (
        f"{PROD_ROOT}/",
        "Low",
        "Could not determine intended target automatically. Manual review of the HTML context on the source page required.",
    )


def style_header(ws, row: int, max_col: int):
    fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    font = Font(bold=True, color="FFFFFF", size=11)
    align = Alignment(horizontal="left", vertical="center", wrap_text=True)
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = fill
        cell.font = font
        cell.alignment = align
    ws.row_dimensions[row].height = 28


def set_column_widths(ws, widths):
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width


def wrap(ws):
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def load_rows():
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb["Sheet1"]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        source_page, staging_url, resolved, status = row
        proposed, confidence, rationale = proposed_target(staging_url, resolved or "")
        rows.append(
            {
                "source_page": source_page,
                "staging_url": staging_url,
                "currently_resolves_to": resolved,
                "final_status": int(status) if status else None,
                "proposed_production_url": proposed,
                "confidence": confidence,
                "rationale": rationale,
            }
        )
    wb.close()
    return rows


def build_summary(wb, rows):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — WP Engine Staging Links Action Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "Context"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "The crawl found 20 internal links on the live site still pointing to the old WP Engine "
        "staging domain (superiorwatair.wpengine.com). The staging domain 301-redirects everything "
        "to the production site, so the links don't break visibly — but when the staging path doesn't "
        "exist on production, the redirect lands the user on the homepage instead of the intended page. "
        "This loses link equity, hurts internal linking, and creates a confusing user experience."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 90

    ws["A7"] = "Breakdown"
    ws["A7"].font = Font(bold=True, size=12)

    # Per-source counts
    by_source = defaultdict(int)
    for r in rows:
        by_source[r["source_page"]] += 1

    conf_counts = {"High": 0, "Medium": 0, "Low": 0}
    for r in rows:
        conf_counts[r["confidence"]] = conf_counts.get(r["confidence"], 0) + 1

    ws["A8"] = "Total staging links"
    ws["B8"] = len(rows)
    ws["A9"] = "Unique source pages to edit"
    ws["B9"] = len(by_source)
    ws["A10"] = "High-confidence fixes (direct swap)"
    ws["B10"] = conf_counts["High"]
    ws["A11"] = "Medium-confidence (verify HTML context first)"
    ws["B11"] = conf_counts["Medium"]
    ws["A12"] = "Low-confidence (manual decision required)"
    ws["B12"] = conf_counts["Low"]

    ws["A14"] = "Source Pages (by number of staging links to fix)"
    ws["A14"].font = Font(bold=True, size=12)
    ws["A15"] = "Source Page"
    ws["B15"] = "Links to Fix"
    style_header(ws, 15, 2)
    r = 16
    for source, count in sorted(by_source.items(), key=lambda x: (-x[1], x[0])):
        ws.cell(row=r, column=1, value=source)
        ws.cell(row=r, column=2, value=count)
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="How to use this file").font = Font(bold=True, size=12)
    r += 1
    ws.cell(
        row=r,
        column=1,
        value=(
            "1. Open the 'Action Plan' tab — one row per staging link, with the exact replacement URL.\n"
            "2. For High-confidence rows: replace the staging URL with the proposed production URL directly.\n"
            "3. For Medium/Low-confidence rows: open the source page in the CMS, find the link in the HTML, "
            "and decide the correct target based on surrounding context (anchor text, visual position).\n"
            "4. The 'By Source Page' tab groups links by the page that needs editing — use this for batched WordPress edits."
        ),
    )
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 110

    set_column_widths(ws, {1: 45, 2: 18, 3: 15, 4: 15, 5: 15, 6: 15})


def build_action_plan(wb, rows):
    ws = wb.create_sheet("Action Plan")
    headers = [
        "#",
        "Source Page (edit this)",
        "Current Staging URL in HTML",
        "Currently Resolves To",
        "Proposed Production URL",
        "Confidence",
        "Rationale / Action",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    conf_order = {"High": 0, "Medium": 1, "Low": 2}
    sorted_rows = sorted(
        rows,
        key=lambda r: (conf_order[r["confidence"]], r["source_page"], r["staging_url"]),
    )
    for i, r in enumerate(sorted_rows, start=1):
        ws.append(
            [
                i,
                r["source_page"],
                r["staging_url"],
                r["currently_resolves_to"],
                r["proposed_production_url"],
                r["confidence"],
                r["rationale"],
            ]
        )
    set_column_widths(ws, {1: 5, 2: 38, 3: 58, 4: 48, 5: 48, 6: 13, 7: 55})
    wrap(ws)


def build_by_source(wb, rows):
    ws = wb.create_sheet("By Source Page")
    headers = [
        "#",
        "Source Page",
        "# Links",
        "Current Staging URL",
        "Proposed Production URL",
        "Confidence",
        "Notes",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    # Group
    groups = defaultdict(list)
    for r in rows:
        groups[r["source_page"]].append(r)

    i = 1
    for source_page in sorted(groups.keys()):
        group = groups[source_page]
        for j, r in enumerate(group):
            ws.append(
                [
                    i,
                    source_page if j == 0 else "",
                    len(group) if j == 0 else "",
                    r["staging_url"],
                    r["proposed_production_url"],
                    r["confidence"],
                    r["rationale"],
                ]
            )
            i += 1
    set_column_widths(ws, {1: 5, 2: 38, 3: 10, 4: 58, 5: 48, 6: 13, 7: 55})
    wrap(ws)


def main():
    rows = load_rows()
    print(f"Loaded {len(rows)} staging links")
    conf = defaultdict(int)
    for r in rows:
        conf[r["confidence"]] += 1
    for c in ("High", "Medium", "Low"):
        print(f"  {conf[c]} | {c} confidence")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary(wb, rows)
    build_action_plan(wb, rows)
    build_by_source(wb, rows)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
