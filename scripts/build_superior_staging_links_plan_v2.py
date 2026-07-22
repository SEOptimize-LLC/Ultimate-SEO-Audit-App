"""
Superior Water & Air — Staging Links Plan v2.

Regenerates the staging-links-to-fix list with target URLs UPDATED to
reflect the new URL architecture migrated this week. The original
staging links plan proposed targets like /plumbing-services/service-and-repair/
which now redirects to /services/plumbing/service-and-repair/ — so the
VA's edits should point at the final destination, not the intermediate hop.

This is a content-edit task (find-and-replace inside WordPress page HTML),
NOT a Rank Math CSV import.

Output:
    Clients/Superior/Full SEO Audit/superior_staging_links_plan_v2.xlsx
"""
from __future__ import annotations

import io
import os
import sys
from collections import defaultdict
from datetime import date

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
SRC = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_staging_links_plan.xlsx"
)
OUT = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_staging_links_plan_v2.xlsx"
)

DOMAIN = "https://superiorwaterandair.com"

# Mapping: original-plan proposed target -> updated final target under
# the new architecture. Empty string means "no change to original".
TARGET_OVERRIDES = {
    f"{DOMAIN}/plumbing-services/service-and-repair/":
        f"{DOMAIN}/services/plumbing/service-and-repair/",
    f"{DOMAIN}/emergency-services/plumbing-repair/":
        f"{DOMAIN}/services/emergency/plumbing-repair/",
    f"{DOMAIN}/how-does-a-reverse-osmosis-water-purifier-work/":
        f"{DOMAIN}/blog/how-does-a-reverse-osmosis-water-purifier-work/",
    f"{DOMAIN}/how-does-a-water-softener-work/":
        f"{DOMAIN}/blog/how-does-a-water-softener-work/",
    f"{DOMAIN}/hvac/furnace-repair/":
        f"{DOMAIN}/services/hvac/furnace-repair/",
}


def load_action_plan():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["Action Plan"]
    headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[1]:
            continue
        rows.append(dict(zip(headers, row)))
    wb.close()
    return rows


NAVY = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HFONT = Font(bold=True, color="FFFFFF", size=11)


def style_header(ws, row, n):
    for c in range(1, n + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = NAVY
        cell.font = HFONT
        cell.alignment = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )
    ws.row_dimensions[row].height = 28


def widths(ws, w):
    for c, n in w.items():
        ws.column_dimensions[get_column_letter(c)].width = n


def wrap(ws):
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def main() -> None:
    rows = load_action_plan()
    print(f"Loaded {len(rows)} staging-link rows from original plan.")

    # Apply target overrides
    updated_count = 0
    for r in rows:
        original_target = r["Proposed Production URL"]
        new_target = TARGET_OVERRIDES.get(original_target)
        if new_target:
            r["Updated Final Target"] = new_target
            r["Target Changed"] = "YES"
            updated_count += 1
        else:
            r["Updated Final Target"] = original_target
            r["Target Changed"] = ""

    print(f"  Targets updated to reflect new architecture: {updated_count}")
    print(f"  Targets unchanged: {len(rows) - updated_count}")

    # Build workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary(wb, rows)
    build_action_plan_v2(wb, rows)
    build_by_source_page_v2(wb, rows)
    wb.save(OUT)
    print(f"\nSaved: {OUT}")


def build_summary(wb, rows):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — Staging Links Plan v2"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "What this is"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "20 internal links across the site point at the old WP Engine staging "
        "domain (https://superiorwatair.wpengine.com/...). These need to be "
        "edited in the WordPress page content to point at the production URLs. "
        "This is a CONTENT EDIT task, not a redirect — Rank Math cannot fix "
        "hardcoded <a href> values inside post HTML."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 80

    ws["A7"] = "Why v2 exists"
    ws["A7"].font = Font(bold=True, size=12)
    ws["A8"] = (
        "The original staging-links plan proposed targets like "
        "/plumbing-services/service-and-repair/ — which is correct against "
        "the OLD architecture. After this week's URL migration, those same "
        "targets now redirect to new URLs like "
        "/services/plumbing/service-and-repair/. If we edit links to point at "
        "the old targets, every fixed link will go through a 301 hop, leaking "
        "internal link equity. v2 updates the targets to point at the FINAL "
        "destination URLs under the new architecture."
    )
    ws["A8"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A8:F8")
    ws.row_dimensions[8].height = 110

    ws["A10"] = "Scope"
    ws["A10"].font = Font(bold=True, size=12)
    by_source = defaultdict(int)
    for r in rows:
        by_source[r["Source Page (edit this)"]] += 1
    ws["A11"] = "Total staging links to fix"
    ws["B11"] = len(rows)
    ws["A12"] = "Unique source pages to edit"
    ws["B12"] = len(by_source)

    high = sum(1 for r in rows if r["Confidence"] == "High")
    med = sum(1 for r in rows if r["Confidence"] == "Medium")
    low = sum(1 for r in rows if r["Confidence"] == "Low")
    ws["A13"] = "High-confidence fixes (direct swap)"
    ws["B13"] = high
    ws["A14"] = "Medium-confidence (verify HTML context)"
    ws["B14"] = med
    ws["A15"] = (
        "Low-confidence (fallback to homepage — verify intent in HTML)"
    )
    ws["B15"] = low

    ws["A17"] = "How to use this file"
    ws["A17"].font = Font(bold=True, size=12)
    ws["A18"] = (
        "1. Open 'By Source Page' tab — it groups the 20 links by the "
        "WordPress page that contains them. Edit one page at a time.\n"
        "2. For each source page, open it in the WordPress editor.\n"
        "3. Switch to the HTML/Code/Text view (or use the 'Find and Replace' "
        "feature in Better Search Replace plugin if available).\n"
        "4. For each staging URL listed: replace the entire URL with the "
        "'Updated Final Target' from this sheet.\n"
        "5. Save the page.\n"
        "6. After all 20 are done, run a quick crawl of the site (or use "
        "Screaming Frog free version) and confirm zero results when "
        "searching for 'superiorwatair.wpengine.com'."
    )
    ws["A18"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A18:F18")
    ws.row_dimensions[18].height = 200

    widths(ws, {1: 45, 2: 15, 3: 15, 4: 15, 5: 15, 6: 15})


def build_action_plan_v2(wb, rows):
    ws = wb.create_sheet("Action Plan v2")
    ws.append([
        "#", "Source Page (edit this)", "Current Staging URL in HTML",
        "Updated Final Target (use this)", "Target Changed?",
        "Confidence", "Notes",
    ])
    style_header(ws, 1, 7)
    for r in rows:
        ws.append([
            r["#"], r["Source Page (edit this)"],
            r["Current Staging URL in HTML"],
            r["Updated Final Target"], r["Target Changed"],
            r["Confidence"], r["Rationale / Action"],
        ])
    widths(ws, {1: 5, 2: 38, 3: 58, 4: 50, 5: 14, 6: 12, 7: 50})
    wrap(ws)


def build_by_source_page_v2(wb, rows):
    ws = wb.create_sheet("By Source Page")
    ws.append([
        "Source Page", "# Links",
        "Current Staging URL", "Updated Final Target", "Target Changed?",
        "Confidence",
    ])
    style_header(ws, 1, 6)

    by_source = defaultdict(list)
    for r in rows:
        by_source[r["Source Page (edit this)"]].append(r)

    for src in sorted(by_source.keys()):
        items = by_source[src]
        for j, r in enumerate(items):
            ws.append([
                src if j == 0 else "",
                len(items) if j == 0 else "",
                r["Current Staging URL in HTML"],
                r["Updated Final Target"],
                r["Target Changed"],
                r["Confidence"],
            ])
    widths(ws, {1: 38, 2: 8, 3: 58, 4: 50, 5: 14, 6: 12})
    wrap(ws)


if __name__ == "__main__":
    main()
