"""
Build Excel action plan for Superior Water & Air — GSC audit redirect corrections.

Data source: Clients/Superior/Superior Water & Air - GSC Audit (Nov 24th 2025).xlsx
  - Tab 'Page with redirect' (113 rows; 60+ with action items requiring correction)

Output: Clients/Superior/Full SEO Audit/superior_gsc_redirect_corrections_plan.xlsx

The original audit doc summarized the "redirect correction" work as
"7 typo slugs, 3 service page redirects, 3 location redirects." This script
pulls the full raw data — which actually contains 7 typo, 12 service, 10 location
corrections plus a few singletons. The Excel file reflects the real counts.
"""
from __future__ import annotations

import os
import re
from collections import Counter
from datetime import date

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
SRC = os.path.join(ROOT, "Clients/Superior/Superior Water & Air - GSC Audit (Nov 24th 2025).xlsx")
OUT = os.path.join(ROOT, "Clients/Superior/Full SEO Audit/superior_gsc_redirect_corrections_plan.xlsx")

URL_IN_ACTION = re.compile(r"https?://superiorwaterandair\.com[^\s,)\]]*")


def extract_new_target(action: str) -> str:
    """Pull the URL referenced in the action item (the proposed new redirect target)."""
    if not action:
        return ""
    matches = URL_IN_ACTION.findall(action)
    return matches[-1].rstrip(".,;") if matches else ""


def classify_action(action: str) -> tuple[str, str]:
    """
    Return (bucket, simplified_instruction).

    Buckets:
      - Typo slug → service areas
      - Service redirect → specific service page
      - Location redirect → specific city page
      - Other correction (testimonials, deeper investigation, noindex, etc.)
      - No action (leave as-is / redirect correct)
    """
    if not action:
        return ("No action", "Leave as-is")
    a = action.strip().lower()

    if a.startswith("nothing to do"):
        return ("No action", "Leave as-is")
    if a.startswith("redirect is supposed to be here"):
        return ("No action", "Redirect is correct — no change needed")
    if "implement a noindex" in a:
        return ("Noindex", "Implement a noindex tag on this URL")
    if "dive deeper" in a:
        return ("Investigate", "Investigate why this blog has a redirect")
    if "typo on the slug" in a or "main service area page" in a:
        return (
            "Typo slug → /service-areas/",
            "Typo in original slug — update 301 to point to /service-areas/",
        )
    if "top-level page" in a:
        return (
            "Build new page",
            "Service needs a dedicated top-level page — decide whether to build one",
        )
    # City-specific redirects — detect "service-areas/<city>-utah/"
    if re.search(r"service-areas/[a-z\-]+-utah/", a):
        return (
            "Location redirect → city page",
            "Update 301 to point to the city's dedicated service-area page",
        )
    # Service-specific (hvac/, water/, plumbing-services/) when not service-areas
    if re.search(r"/(hvac|water|plumbing-services)/", a):
        return (
            "Service redirect → service page",
            "Update 301 to point to the dedicated service page",
        )
    if "/testimonials/" in a:
        return (
            "Other correction",
            "Update redirect to point to /testimonials/",
        )
    return ("Other correction", action.strip())


def priority_for(bucket: str) -> str:
    mapping = {
        "Typo slug → /service-areas/": "Medium",
        "Service redirect → service page": "High",
        "Location redirect → city page": "High",
        "Build new page": "Low (strategic decision)",
        "Noindex": "Medium",
        "Investigate": "Low",
        "Other correction": "Medium",
        "No action": "—",
    }
    return mapping.get(bucket, "Medium")


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


def set_column_widths(ws, widths: dict[int, int]):
    for col, width in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = width


def wrap_all(ws):
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def load_rows() -> list[dict]:
    wb = openpyxl.load_workbook(SRC, data_only=True)
    ws = wb["Page with redirect"]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        original, status_code, status, current_target, action = row
        if not original:
            continue
        # Normalize encoding issues (the source file has mojibake on apostrophes)
        action_clean = (action or "").replace("�", "'").strip()
        bucket, instruction = classify_action(action_clean)
        rows.append(
            {
                "original_url": original,
                "status_code": int(status_code) if status_code else None,
                "current_redirect_target": current_target or "",
                "proposed_new_target": extract_new_target(action_clean),
                "bucket": bucket,
                "instruction": instruction,
                "priority": priority_for(bucket),
                "original_action_text": action_clean,
            }
        )
    wb.close()
    return rows


def build_summary_sheet(wb, rows: list[dict], bucket_counts: Counter):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — GSC Audit Redirect Corrections Action Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}  |  Source: Nov 24, 2025 GSC Audit"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "Context"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "The Nov 2025 GSC audit reviewed 112 URLs flagged as 'Page with redirect' in Search Console. "
        "60+ have action items requiring a redirect correction — typo slugs, service redirects pointing "
        "to the homepage instead of the correct service page, and location redirects that should point "
        "to a specific city's service-area page."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 70

    ws["A7"] = "Note on counts"
    ws["A7"].font = Font(bold=True, size=11)
    ws["A8"] = (
        "The technical audit summary described this as '7 typo slugs, 3 service page redirects, "
        "3 location redirects' — that was a simplified summary of action-item categories, not the raw "
        "row count. Pulling the full GSC audit data reveals more corrections than the summary implied. "
        "This Excel reflects the real numbers."
    )
    ws["A8"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A8:F8")
    ws.row_dimensions[8].height = 60

    ws["A10"] = "Breakdown by Correction Type"
    ws["A10"].font = Font(bold=True, size=12)

    ws["A11"] = "Bucket"
    ws["B11"] = "Count"
    ws["C11"] = "Priority"
    ws["D11"] = "What to do"
    style_header(ws, 11, 4)

    bucket_info = [
        (
            "Typo slug → /service-areas/",
            "Medium",
            "Original URL has a typo. Update 301 to point to /service-areas/.",
        ),
        (
            "Service redirect → service page",
            "High",
            "Redirect currently points to homepage. Update to point to the correct service page (water heaters, furnace, etc.).",
        ),
        (
            "Location redirect → city page",
            "High",
            "Redirect currently points to homepage or generic service-areas. Update to the city's dedicated page.",
        ),
        (
            "Other correction",
            "Medium",
            "Miscellaneous redirect updates (e.g., testimonials).",
        ),
        (
            "Build new page",
            "Low (strategic)",
            "Service needs its own top-level page — product decision, not a redirect fix.",
        ),
        (
            "Noindex",
            "Medium",
            "Apply noindex tag instead of redirecting.",
        ),
        (
            "Investigate",
            "Low",
            "Blog post has an unexplained redirect — dig in before acting.",
        ),
        (
            "No action",
            "—",
            "Redirect is already correct, or URL should be left as-is.",
        ),
    ]
    r = 12
    for bucket, prio, desc in bucket_info:
        ws.cell(row=r, column=1, value=bucket)
        ws.cell(row=r, column=2, value=bucket_counts.get(bucket, 0))
        ws.cell(row=r, column=3, value=prio)
        ws.cell(row=r, column=4, value=desc)
        ws.cell(row=r, column=4).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1

    r += 1
    total_corrections = sum(
        bucket_counts.get(b, 0)
        for b in bucket_counts
        if b not in ("No action", "Investigate")
    )
    ws.cell(row=r, column=1, value="Total URLs in GSC audit").font = Font(bold=True)
    ws.cell(row=r, column=2, value=len(rows))
    r += 1
    ws.cell(row=r, column=1, value="Total requiring correction").font = Font(bold=True)
    ws.cell(row=r, column=2, value=total_corrections)

    r += 2
    ws.cell(row=r, column=1, value="Tabs in this file").font = Font(bold=True, size=12)
    r += 1
    ws.cell(
        row=r,
        column=1,
        value=(
            "1. Summary — this sheet\n"
            "2. All Corrections — every URL needing a 301 update, with the exact new target\n"
            "3. Typo Slugs — subset routed to /service-areas/\n"
            "4. Service Redirects — redirects that should point to a specific service page\n"
            "5. Location Redirects — redirects that should point to a specific city page\n"
            "6. Other / Investigate — noindex, testimonials, blog investigations, strategic decisions\n"
            "7. Leave As-Is — URLs the audit confirmed need no change (reference only)"
        ),
    )
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 130

    set_column_widths(ws, {1: 38, 2: 12, 3: 20, 4: 55, 5: 15, 6: 15})


def build_corrections_sheet(wb, name: str, rows: list[dict], include_buckets: set[str] | None = None):
    ws = wb.create_sheet(name)
    headers = [
        "#",
        "Original URL (redirect source)",
        "Current Redirect Target",
        "Proposed New Target",
        "Correction Type",
        "Priority",
        "Instruction",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))
    i = 1
    for row in rows:
        if include_buckets is not None and row["bucket"] not in include_buckets:
            continue
        ws.append(
            [
                i,
                row["original_url"],
                row["current_redirect_target"],
                row["proposed_new_target"],
                row["bucket"],
                row["priority"],
                row["instruction"],
            ]
        )
        i += 1
    set_column_widths(ws, {1: 5, 2: 55, 3: 50, 4: 50, 5: 32, 6: 18, 7: 55})
    wrap_all(ws)


def build_leave_as_is_sheet(wb, rows: list[dict]):
    ws = wb.create_sheet("Leave As-Is")
    headers = ["#", "URL", "Current Redirect Target", "Why No Action"]
    ws.append(headers)
    style_header(ws, 1, len(headers))
    i = 1
    for row in rows:
        if row["bucket"] != "No action":
            continue
        ws.append(
            [
                i,
                row["original_url"],
                row["current_redirect_target"],
                row["instruction"],
            ]
        )
        i += 1
    set_column_widths(ws, {1: 5, 2: 60, 3: 55, 4: 50})
    wrap_all(ws)


def main():
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    rows = load_rows()
    bucket_counts = Counter(r["bucket"] for r in rows)

    print("Bucket breakdown:")
    for bucket, count in bucket_counts.most_common():
        print(f"  {count:3d} | {bucket}")
    print(f"Total rows: {len(rows)}")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary_sheet(wb, rows, bucket_counts)

    # Sort rows: corrections first (by priority then bucket), leave-as-is last
    priority_order = {"High": 0, "Medium": 1, "Low (strategic decision)": 2, "Low": 3, "—": 4}
    correction_rows = [r for r in rows if r["bucket"] != "No action"]
    correction_rows.sort(
        key=lambda r: (priority_order.get(r["priority"], 5), r["bucket"], r["original_url"])
    )

    build_corrections_sheet(wb, "All Corrections", correction_rows)
    build_corrections_sheet(
        wb, "Typo Slugs", correction_rows, include_buckets={"Typo slug → /service-areas/"}
    )
    build_corrections_sheet(
        wb,
        "Service Redirects",
        correction_rows,
        include_buckets={"Service redirect → service page"},
    )
    build_corrections_sheet(
        wb,
        "Location Redirects",
        correction_rows,
        include_buckets={"Location redirect → city page"},
    )
    build_corrections_sheet(
        wb,
        "Other & Investigate",
        correction_rows,
        include_buckets={"Other correction", "Build new page", "Noindex", "Investigate"},
    )
    build_leave_as_is_sheet(wb, rows)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
