"""
Comfort Solutions — 24 Titles For Copywriter Rewrites.

Pulls only the 24 page titles from the truncated-titles audit that are
genuinely over the 60-char threshold even without the | Comfort Solutions
suffix. Provides URL + current title + length + page intent context for
the copywriter to draft rewrites.

No proposed rewrites included — handed off to the local SEO copywriter.

Output:
    Clients/Comfort/Full SEO Audit/comfort_24_titles_for_copywriter.xlsx
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from datetime import date
from urllib.parse import urlparse

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
SRC = os.path.join(
    ROOT,
    "Clients/Comfort/Full SEO Audit/comfort_truncated_titles_plan.xlsx",
)
OUT_XLSX = os.path.join(
    ROOT,
    "Clients/Comfort/Full SEO Audit/comfort_24_titles_for_copywriter.xlsx",
)

NAVY = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HFONT = Font(bold=True, color="FFFFFF", size=11)

SUFFIX_PATTERNS = [
    r"\s*\|\s*Comfort\s*Solutions\s*$",
    r"\s*-\s*Comfort\s*Solutions\s*$",
]


def strip_suffix(title: str) -> tuple[str, int]:
    for pat in SUFFIX_PATTERNS:
        m = re.search(pat, title, re.IGNORECASE)
        if m:
            return title[: m.start()].rstrip(), len(m.group(0))
    return title, 0


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


def detect_city(url: str, title: str) -> str:
    """Extract a city/area name from the URL or title for context."""
    cities = [
        ("salt lake city", "Salt Lake City, UT"),
        ("south salt lake", "South Salt Lake City, UT"),
        ("park city", "Park City, UT"),
        ("davis county", "Davis County, UT"),
        ("layton", "Layton, UT"),
        ("ogden", "Ogden, UT"),
        ("orem", "Orem, UT"),
        ("sandy", "Sandy, UT"),
    ]
    text = (urlparse(url).path + " " + title).lower().replace("-", " ")
    for slug, label in cities:
        if slug in text:
            return label
    return ""


def detect_service(url: str, title: str) -> str:
    """Extract the primary service from URL slug or title."""
    text = (urlparse(url).path + " " + title).lower()
    if "emergency-furnace-repair" in text or "emergency furnace" in text:
        return "Emergency Furnace Repair"
    if "furnace-installation" in text or "furnace installation" in text:
        return "Furnace Installation"
    if "furnace-repair" in text or "furnace repair" in text:
        return "Furnace Repair"
    if "furnace-replacement" in text or "furnace replacement" in text:
        return "Furnace Replacement"
    if "furnace-cleaning" in text or "furnace cleaning" in text:
        return "Furnace Cleaning"
    if "ac-repair" in text or "ac repair" in text:
        return "AC Repair"
    if "gas-fireplace-repair" in text or "gas fireplace repair" in text:
        return "Gas Fireplace Repair"
    if "gas-fireplace-contractor" in text or "gas fireplace contractor" in text:
        return "Gas Fireplace Contractor"
    if "gas-fireplace-inserts" in text or "gas fireplace inserts" in text:
        return "Gas Fireplace Inserts"
    if "outdoor-fireplace-contractor" in text or "outdoor fireplace contractor" in text:
        return "Outdoor Fireplace Contractor"
    if "fireplace-inserts-contractor" in text or "fireplace inserts contractor" in text:
        return "Fireplace Inserts Contractor"
    if "fireplace-contractor" in text or "fireplace contractor" in text:
        return "Fireplace Contractor"
    if "fireplace-service" in text or "fireplace service" in text:
        return "Fireplace Service"
    if "electric-fireplace-services" in text:
        return "Electric Fireplace Services"
    if "electric-fireplace" in text or "electric fireplace" in text:
        return "Electric Fireplace"
    if "fireplace-insert" in text or "fireplace insert" in text:
        return "Fireplace Insert"
    return ""


def main() -> None:
    wb_src = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws_src = wb_src["Title Shortening Plan"]
    rows = []
    headers = None
    for row in ws_src.iter_rows(min_row=4, values_only=True):
        if headers is None:
            headers = row
            continue
        if not row or not row[0]:
            continue
        rows.append(dict(zip(headers, row)))
    wb_src.close()

    # Filter to Bucket B: titles >60 chars even WITHOUT the suffix
    bucket_b = []
    for r in rows:
        title = r.get("Current Title", "") or ""
        stripped, suffix_len = strip_suffix(title)
        # Real rewrite needed if stripped length is still over 60
        if len(stripped) > 60:
            bucket_b.append(r)

    print(f"Bucket B (rewrites needed): {len(bucket_b)}")

    # Build the workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Titles To Rewrite"

    ws["A1"] = "Comfort Solutions — 24 Page Titles For Rewrite"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = (
        f"Generated: {date.today().isoformat()} | "
        "Pages where the title is over 60 characters even without the "
        "| Comfort Solutions suffix. Genuine rewrite needed — not just "
        "suffix removal."
    )
    ws["A2"].font = Font(italic=True, color="666666")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:H2")
    ws.row_dimensions[2].height = 45

    ws["A4"] = "Constraints for the rewrite"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "• Target length: 50-60 characters (max 60 including any brand "
        "suffix you choose to keep)\n"
        "• Front-load the primary keyword phrase\n"
        "• Include city/area when the page is location-specific (see "
        "'Detected City' column)\n"
        "• Avoid filler adjectives that add no ranking value: 'Top,' "
        "'Reliable,' 'Expert,' 'Find the Best,' 'Discover the Best'\n"
        "• Avoid trailing platitudes: 'for Your Home,' 'for Cozy Living,' "
        "'Quality You Can Trust,' 'Fast Solutions'\n"
        "• Branded suffix is optional — if including, use ' | Comfort "
        "Solutions' (consistent with site convention)"
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:H5")
    ws.row_dimensions[5].height = 145

    ws.append([])
    ws.append([
        "#", "URL", "Current Title", "Curr Len",
        "Detected Service", "Detected City", "Page Type",
        "New Title (copywriter to fill)",
    ])
    style_header(ws, 7, 8)

    for i, r in enumerate(bucket_b, start=1):
        url = r.get("URL", "")
        title = r.get("Current Title", "") or ""
        page_type = r.get("Classification", "")
        ws.append([
            i, url, title, len(title),
            detect_service(url, title),
            detect_city(url, title),
            page_type,
            "",  # left blank for copywriter
        ])

    widths(ws, {1: 5, 2: 60, 3: 55, 4: 10, 5: 28, 6: 22, 7: 18, 8: 50})
    ws.freeze_panes = "A8"
    for row in ws.iter_rows(min_row=8, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
    wb.save(OUT_XLSX)
    print(f"Saved: {OUT_XLSX}")


if __name__ == "__main__":
    main()
