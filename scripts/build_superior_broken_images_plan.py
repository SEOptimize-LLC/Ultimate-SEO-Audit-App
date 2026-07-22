"""
Build Excel action plan for Superior Water & Air — 83 broken image references.

Data source: Clients/Superior/Superior - Technical Audit.xlsx
  - Tab 'response_codes_internal_client_' (83 image URLs returning 404)
  - Tab 'all_inlinks' (source pages that reference those images)

Output: Clients/Superior/Full SEO Audit/superior_broken_images_plan.xlsx
"""
from __future__ import annotations

import os
from collections import defaultdict
from datetime import date

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
SRC = os.path.join(ROOT, "Clients/Superior/Superior - Technical Audit.xlsx")
OUT = os.path.join(ROOT, "Clients/Superior/Full SEO Audit/superior_broken_images_plan.xlsx")

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".tiff", ".ico")


def load_broken_images() -> list[dict]:
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["response_codes_internal_client_"]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        addr, _redirect, status, *_ = row
        if not addr or status != 404:
            continue
        a = addr.lower()
        if not any(a.endswith(ext) for ext in IMAGE_EXTS):
            continue
        rows.append({"image_url": addr, "status_code": int(status)})
    wb.close()
    return rows


def load_inlink_map(target_urls: set[str]) -> dict[str, list[dict]]:
    """Return {image_url: [{source_page, alt_text, anchor, link_position}]}"""
    result: dict[str, list[dict]] = defaultdict(list)
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["all_inlinks"]
    headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    idx = {h: i for i, h in enumerate(headers)}
    for row in ws.iter_rows(min_row=2, values_only=True):
        dest = row[idx["Destination"]]
        if dest not in target_urls:
            continue
        result[dest].append(
            {
                "source_page": row[idx["Source"]],
                "alt_text": row[idx["Alt Text"]] or "",
                "anchor": row[idx["Anchor"]] or "",
                "link_position": row[idx["Link Position"]] or "",
                "link_path": row[idx["Link Path"]] or "",
                "type": row[idx["Type"]] or "",
            }
        )
    wb.close()
    return result


def classify_year(image_url: str) -> str:
    """Extract upload year from /wp-content/uploads/YYYY/MM/filename pattern."""
    parts = image_url.split("/wp-content/uploads/")
    if len(parts) < 2:
        return "Unknown"
    year_part = parts[1].split("/")[0]
    return year_part if year_part.isdigit() else "Unknown"


def recommended_action(source_count: int, source_pages: list[dict]) -> tuple[str, str]:
    """Return (action, rationale) for an image given its source pages."""
    if source_count == 0:
        return (
            "Orphan — no action needed",
            "Image file returns 404 but no live page references it. Only crawler-cached — no user impact. Safe to ignore.",
        )
    # Has source pages — need to decide based on source type
    source_urls = {s["source_page"] for s in source_pages}
    only_sitemap = all(
        s["type"] in ("XML Sitemap", "Sitemap XML") for s in source_pages
    )
    if only_sitemap:
        return (
            "Remove from sitemap",
            "Only referenced by XML sitemap — not embedded in any live page. Clean up sitemap export.",
        )
    # Source pages exist — remove or replace the <img> reference
    return (
        "Edit source pages — remove or replace <img> tag",
        f"Image is embedded in {source_count} page(s). Edit each page to remove the broken <img> reference or upload a replacement to the same path.",
    )


def priority_for(action: str, source_count: int) -> str:
    if action == "Orphan — no action needed":
        return "Low (ignore)"
    if action == "Remove from sitemap":
        return "Medium"
    if source_count >= 3:
        return "High"
    return "Medium"


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


def build_summary_sheet(wb, stats: dict):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — Broken Image References Action Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")
    ws["A4"] = "Context"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "Screaming Frog detected 83 internal image URLs returning 404. All are under "
        "/wp-content/uploads/ from 2012–2018 — broken images from old blog posts. "
        "These don't affect indexation but they create broken <img> tags on pages that "
        "still reference them (bad UX, hurts on-page quality signals)."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 60

    ws["A7"] = "Breakdown"
    ws["A7"].font = Font(bold=True, size=12)

    ws["A8"] = "Total broken image URLs"
    ws["B8"] = stats["total"]
    ws["A9"] = "Referenced by live pages (need fix)"
    ws["B9"] = stats["with_sources"]
    ws["A10"] = "Referenced only by XML sitemap (clean sitemap)"
    ws["B10"] = stats["sitemap_only"]
    ws["A11"] = "Orphan (no source — safe to ignore)"
    ws["B11"] = stats["orphan"]
    ws["A12"] = "Unique source pages needing edits"
    ws["B12"] = stats["unique_source_pages"]

    ws["A14"] = "By Upload Year"
    ws["A14"].font = Font(bold=True, size=12)
    row = 15
    for year in sorted(stats["by_year"].keys()):
        ws.cell(row=row, column=1, value=year)
        ws.cell(row=row, column=2, value=stats["by_year"][year])
        row += 1

    ws[f"A{row + 1}"] = "Tabs in this file"
    ws[f"A{row + 1}"].font = Font(bold=True, size=12)
    ws[f"A{row + 2}"] = (
        "1. Summary — this sheet\n"
        "2. Action Plan — full list of 83 broken images with recommended action\n"
        "3. By Source Page — grouped by the page that needs editing (use this to batch edits)\n"
        "4. Orphans — images with no live source (ignore list)"
    )
    ws[f"A{row + 2}"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(f"A{row + 2}:F{row + 2}")
    ws.row_dimensions[row + 2].height = 70

    set_column_widths(ws, {1: 45, 2: 15, 3: 15, 4: 15, 5: 15, 6: 15})


def build_action_plan_sheet(wb, images: list[dict], inlink_map: dict):
    ws = wb.create_sheet("Action Plan")
    headers = [
        "#",
        "Broken Image URL",
        "Upload Year",
        "Source Pages (count)",
        "Recommended Action",
        "Priority",
        "Rationale",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    for i, img in enumerate(images, start=1):
        sources = inlink_map.get(img["image_url"], [])
        source_count = len({s["source_page"] for s in sources})
        action, rationale = recommended_action(source_count, sources)
        priority = priority_for(action, source_count)
        ws.append(
            [
                i,
                img["image_url"],
                classify_year(img["image_url"]),
                source_count,
                action,
                priority,
                rationale,
            ]
        )

    set_column_widths(ws, {1: 5, 2: 70, 3: 12, 4: 18, 5: 38, 6: 15, 7: 50})
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_by_source_sheet(wb, images: list[dict], inlink_map: dict):
    ws = wb.create_sheet("By Source Page")
    # Invert: source_page -> list of broken images embedded on it
    by_source: dict[str, list[dict]] = defaultdict(list)
    for img in images:
        for s in inlink_map.get(img["image_url"], []):
            if s["type"] in ("XML Sitemap", "Sitemap XML"):
                continue  # sitemap refs handled separately
            by_source[s["source_page"]].append(
                {
                    "image_url": img["image_url"],
                    "alt_text": s["alt_text"],
                    "anchor": s["anchor"],
                    "link_path": s["link_path"],
                }
            )

    headers = [
        "#",
        "Source Page (edit this)",
        "Broken Image URL",
        "Alt Text",
        "Element XPath (for finding it in HTML)",
        "Recommended Edit",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    i = 1
    for source_page in sorted(by_source.keys()):
        refs = by_source[source_page]
        for ref in refs:
            has_alt = bool(ref["alt_text"].strip())
            edit = (
                "Remove the <img> tag OR upload replacement image to the same path. "
                f"Alt text is '{ref['alt_text']}' — if removing, also remove the surrounding caption/container."
                if has_alt
                else "Remove the <img> tag OR upload replacement image to the same path. No alt text was set."
            )
            ws.append(
                [
                    i,
                    source_page,
                    ref["image_url"],
                    ref["alt_text"] or "(none)",
                    ref["link_path"] or "",
                    edit,
                ]
            )
            i += 1

    set_column_widths(ws, {1: 5, 2: 55, 3: 70, 4: 30, 5: 50, 6: 55})
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    return len(by_source)


def build_orphans_sheet(wb, images: list[dict], inlink_map: dict):
    ws = wb.create_sheet("Orphans")
    headers = ["#", "Broken Image URL", "Upload Year", "Why Orphan"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    i = 1
    for img in images:
        sources = inlink_map.get(img["image_url"], [])
        if sources:
            continue
        ws.append(
            [
                i,
                img["image_url"],
                classify_year(img["image_url"]),
                "No internal page or sitemap references this image — only surfaced from crawler cache. Safe to ignore.",
            ]
        )
        i += 1

    set_column_widths(ws, {1: 5, 2: 70, 3: 12, 4: 60})
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def main():
    images = load_broken_images()
    assert len(images) == 83, f"Expected 83 broken images, got {len(images)}"

    image_urls = {img["image_url"] for img in images}
    inlink_map = load_inlink_map(image_urls)

    # Stats for summary
    stats = {
        "total": len(images),
        "with_sources": 0,
        "sitemap_only": 0,
        "orphan": 0,
        "unique_source_pages": 0,
        "by_year": defaultdict(int),
    }
    source_pages_set = set()
    for img in images:
        stats["by_year"][classify_year(img["image_url"])] += 1
        sources = inlink_map.get(img["image_url"], [])
        if not sources:
            stats["orphan"] += 1
            continue
        only_sitemap = all(
            s["type"] in ("XML Sitemap", "Sitemap XML") for s in sources
        )
        if only_sitemap:
            stats["sitemap_only"] += 1
        else:
            stats["with_sources"] += 1
            for s in sources:
                if s["type"] not in ("XML Sitemap", "Sitemap XML"):
                    source_pages_set.add(s["source_page"])
    stats["unique_source_pages"] = len(source_pages_set)

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary_sheet(wb, stats)
    build_action_plan_sheet(wb, images, inlink_map)
    build_by_source_sheet(wb, images, inlink_map)
    build_orphans_sheet(wb, images, inlink_map)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"Saved: {OUT}")
    print(f"  Total broken images: {stats['total']}")
    print(f"  With live source pages: {stats['with_sources']}")
    print(f"  Sitemap-only refs: {stats['sitemap_only']}")
    print(f"  Orphans: {stats['orphan']}")
    print(f"  Unique source pages needing edits: {stats['unique_source_pages']}")
    print(f"  By year: {dict(stats['by_year'])}")


if __name__ == "__main__":
    main()
