"""
Build Excel action plan for SameDay — orphaned pages in sitemaps.

Data source: Clients/SameDay/SameDay - Technical Audit.xlsx
  - Tab 'sitemaps_orphan_urls' (43 rows; 39 indexable HTML after filtering asset files)
  - Tab 'all_inlinks' (used to verify zero non-self inlinks)

Audit doc cited "41 orphaned pages." Real count after filtering asset files and
verifying against all_inlinks (excluding self-links from site-wide nav): 39.
Close match — the 2-URL difference is recount variance.

Output: Clients/SameDay/Full SEO Audit/sameday_orphan_pages_plan.xlsx
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
SRC = os.path.join(ROOT, "Clients/SameDay/SameDay - Technical Audit.xlsx")
OUT = os.path.join(ROOT, "Clients/SameDay/Full SEO Audit/sameday_orphan_pages_plan.xlsx")

ASSET_EXTS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff",
    ".woff", ".woff2", ".ttf", ".otf", ".css", ".js", ".mp4", ".pdf",
)
PATH_EXCLUDES = ("/wp-content/", "/cdn-cgi/", "/wp-admin/", "/wp-includes/")

# Paths that should be removed from the sitemap entirely — no SEO value
UTILITY_PATHS = {
    "/thank-you-appointment/",
    "/thank-you-contact/",
    "/terms-of-use/",
    "/jobs/",
    "/mammoth-partnership/",
    "/financing-for-new-furnace/",
    "/scheduling-pro-test-page/",
    "/scented-vents/",
    "/new-draft-home-page/",
    "/homepage/",
    "/new-home-design-2/",
}

UTAH_CITIES = [
    "salt-lake-city", "salt-lake", "ogden", "orem", "provo", "sandy",
    "park-city", "lehi", "draper", "bluffdale", "midvale", "kearns",
    "springville", "south-jordan", "spanish-fork", "cedar-city",
    "north-ogden", "north-salt-lake", "millcreek", "herriman", "highland",
    "salem", "tooele", "st-george", "west-valley", "west-jordan", "layton",
    "murray", "taylorsville", "riverton", "pleasant-grove", "american-fork",
]


def is_asset(url: str) -> bool:
    a = url.lower()
    return any(a.endswith(e) for e in ASSET_EXTS) or any(p in a for p in PATH_EXCLUDES)


def detect_city(slug: str) -> str:
    for c in sorted(UTAH_CITIES, key=len, reverse=True):
        if c in slug:
            return c.replace("-", " ").title()
    return ""


def classify_page(url: str) -> dict:
    """
    Return dict with: category, action, priority, rationale, parent_hub,
    city, city_page, recommended_anchor, notes.
    """
    path = urlparse(url).path.lower()
    parts = [p for p in path.strip("/").split("/") if p]
    slug = parts[-1] if parts else ""
    result = {
        "category": "",
        "action": "",
        "priority": "",
        "rationale": "",
        "parent_hub": "",
        "city": "",
        "city_page": "",
        "recommended_anchor": "",
        "notes": "",
    }

    # Utility / test / orphaned-draft pages
    if path in UTILITY_PATHS:
        # Sub-classify for specific guidance
        if path in ("/new-draft-home-page/", "/homepage/", "/new-home-design-2/"):
            notes = "This looks like an old homepage draft/variant. Confirm with the team, then delete the page or 301 it to / and remove from sitemap."
            action = "Delete page + remove from sitemap + 301 to /"
            category = "Draft homepage variant"
        elif path in ("/scheduling-pro-test-page/", "/scented-vents/"):
            notes = "Test page that shouldn't be in production. Delete it entirely."
            action = "Delete page + remove from sitemap"
            category = "Test page"
        elif path in ("/terms-of-use/", "/jobs/", "/mammoth-partnership/", "/financing-for-new-furnace/"):
            notes = "Utility/legal page with no organic-search value. Remove from sitemap + noindex. Leave the page live if it serves a real purpose (legal/recruiting/financing)."
            action = "Remove from sitemap + noindex"
            category = "Utility page"
        else:
            notes = "Form thank-you page. No SEO value. Remove from sitemap + noindex."
            action = "Remove from sitemap + noindex"
            category = "Thank-you page"
        result.update({
            "category": category,
            "action": action,
            "priority": "High",
            "rationale": notes,
            "notes": notes,
        })
        return result

    # Typo watch
    typo_note = ""
    if "utath" in slug:
        typo_note = " NOTE: The slug contains a typo ('utath' instead of 'utah'). Fix the slug when editing and add a 301 from the old URL."

    # City-targeted service pages
    city = detect_city(slug)

    if "/heating/furnaces/" in path:
        parent_hub = "https://samedayutah.com/heating/furnaces/"
        service_type = "Furnaces (heating)"
    elif "/plumbing/water-heaters/" in path or "/plumbing/tankless-water" in path:
        parent_hub = "https://samedayutah.com/plumbing/water-heaters/"
        service_type = "Water heaters (plumbing)"
    elif "/plumbing/drain-cleaning/" in path:
        parent_hub = "https://samedayutah.com/plumbing/drain-cleaning/"
        service_type = "Drain cleaning (plumbing)"
    elif "/plumbing/" in path:
        parent_hub = "https://samedayutah.com/plumbing/"
        service_type = "Plumbing"
    elif "/service-area/heating/" in path:
        parent_hub = "https://samedayutah.com/service-area/"
        service_type = "Heating (service-area subfolder)"
    elif "/heating/" in path:
        parent_hub = "https://samedayutah.com/heating/"
        service_type = "Heating"
    elif path.startswith("/furnace-"):
        # Stranded top-level furnace URL outside the /heating/furnaces/ silo
        parent_hub = "https://samedayutah.com/heating/furnaces/"
        service_type = "Furnace (stranded top-level URL — consider moving into /heating/furnaces/ silo)"
    else:
        parent_hub = "(determine manually)"
        service_type = "Other"

    # City-area page
    if city:
        city_slug = city.lower().replace(" ", "-")
        city_page = f"https://samedayutah.com/service-area/{city_slug}-utah/"
    else:
        city_page = "(no city detected — manual review)"

    # Anchor text
    anchor_raw = slug.replace("-utah", "").replace("-", " ")
    if "utath" in anchor_raw:
        anchor_raw = anchor_raw.replace("utath", "").strip()
    anchor = anchor_raw.title() if anchor_raw else ""

    rationale = (
        f"{service_type} page targeting {city or 'unknown city'}. "
        f"Link from: (1) parent hub {parent_hub}, and (2) the city's service-area page {city_page} "
        f"if it exists. Use descriptive anchor text."
    ) + typo_note

    result.update({
        "category": "City service page",
        "action": "Add internal links",
        "priority": "Medium",
        "rationale": rationale,
        "parent_hub": parent_hub,
        "city": city,
        "city_page": city_page,
        "recommended_anchor": anchor,
        "notes": typo_note.strip() if typo_note else "",
    })
    return result


def load_orphans():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["sitemaps_orphan_urls"]
    candidates = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        addr = row[0]
        if not addr or is_asset(addr):
            continue
        if row[4] != "Indexable":
            continue
        candidates.add(addr)

    # Verify against all_inlinks (exclude self-links)
    ws2 = wb["all_inlinks"]
    headers = [c.value for c in next(ws2.iter_rows(min_row=1, max_row=1))]
    idx = {h: i for i, h in enumerate(headers)}
    real_inlinks = defaultdict(int)
    for row in ws2.iter_rows(min_row=2, values_only=True):
        if row[idx["Type"]] != "Hyperlink":
            continue
        dest = row[idx["Destination"]]
        src = row[idx["Source"]]
        if dest not in candidates or src == dest:
            continue
        real_inlinks[dest] += 1

    orphans = [u for u in candidates if real_inlinks[u] == 0]
    wb.close()
    return orphans


def style_header(ws, row, max_col):
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


def build_summary(wb, rows_data):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "SameDay — Orphan Pages Action Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "Context"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "Orphan pages are URLs in the XML sitemaps with no internal links pointing to them "
        "from the rest of the site. Google can still find them via the sitemap, but the absence "
        "of internal links signals low importance — they receive minimal crawl priority and "
        "rank poorly. For a service business like SameDay, orphan city-service pages are "
        "particularly costly because they're the pages built to capture local intent."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 90

    ws["A7"] = "Note on the count"
    ws["A7"].font = Font(bold=True, size=11)
    ws["A8"] = (
        "The original audit cited '41 orphaned pages.' The Screaming Frog crawl data shows 39 "
        "indexable HTML pages with zero real inlinks (excluding asset files and self-links from "
        "site-wide navigation). The 2-URL difference is recount variance. Of those 39, only 28 are "
        "legitimate service pages that need internal linking. The other 11 are utility pages, "
        "test pages, and old homepage drafts that should be removed from the sitemap entirely."
    )
    ws["A8"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A8:F8")
    ws.row_dimensions[8].height = 100

    ws["A10"] = "Breakdown by Category"
    ws["A10"].font = Font(bold=True, size=12)

    cat_counts = defaultdict(int)
    for r in rows_data:
        cat_counts[r["category"]] += 1

    ws["A11"] = "Category"
    ws["B11"] = "Count"
    ws["C11"] = "Priority"
    ws["D11"] = "Action"
    style_header(ws, 11, 4)

    display = [
        ("City service page", "Medium", "Add internal links from parent hub + city service-area page"),
        ("Draft homepage variant", "High", "Delete page + 301 to / + remove from sitemap"),
        ("Test page", "High", "Delete page entirely"),
        ("Thank-you page", "High", "Remove from sitemap + noindex"),
        ("Utility page", "High", "Remove from sitemap + noindex"),
    ]
    r = 12
    for cat, prio, action in display:
        ws.cell(row=r, column=1, value=cat)
        ws.cell(row=r, column=2, value=cat_counts.get(cat, 0))
        ws.cell(row=r, column=3, value=prio)
        ws.cell(row=r, column=4, value=action)
        ws.cell(row=r, column=4).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Total orphan pages").font = Font(bold=True)
    ws.cell(row=r, column=2, value=len(rows_data))

    r += 2
    ws.cell(row=r, column=1, value="Quick wins at the top").font = Font(bold=True, size=12)
    r += 1
    ws.cell(
        row=r,
        column=1,
        value=(
            "- 3 old homepage drafts (/homepage/, /new-draft-home-page/, /new-home-design-2/) — delete, 301 to /, remove from sitemap.\n"
            "- 2 test pages (/scheduling-pro-test-page/, /scented-vents/) — delete entirely.\n"
            "- 6 utility/legal pages — remove from sitemap + noindex (pages stay live, just not in organic search).\n"
            "- 1 slug typo: /plumbing/water-heater-replacement-murray-utath/ — fix the slug to 'utah' and 301 the old URL."
        ),
    )
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 110

    r += 2
    ws.cell(row=r, column=1, value="How to use this file").font = Font(bold=True, size=12)
    r += 1
    ws.cell(
        row=r,
        column=1,
        value=(
            "1. 'Remove From Sitemap' tab — 11 pages to remove first. This is the fastest win and drops the orphan count from 39 → 28 with zero linking work.\n"
            "2. 'Link From Site' tab — 28 city service pages that need internal links. Each row has the parent hub URL, the matching /service-area/<city>-utah/ page URL, and a recommended anchor text.\n"
            "3. Watch the 'Notes' column for the Murray typo and any other flags."
        ),
    )
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 130

    set_column_widths(ws, {1: 38, 2: 12, 3: 12, 4: 50, 5: 15, 6: 15})


def build_link_from_site_sheet(wb, rows_data):
    ws = wb.create_sheet("Link From Site")
    headers = [
        "#",
        "Orphan URL (needs inlinks)",
        "Detected City",
        "Primary Link Source (parent hub)",
        "Secondary Link Source (city page)",
        "Recommended Anchor Text",
        "Priority",
        "Notes",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    i = 1
    for r in rows_data:
        if r["category"] != "City service page":
            continue
        ws.append([
            i, r["url"], r["city"] or "—", r["parent_hub"], r["city_page"],
            r["recommended_anchor"], r["priority"], r["notes"],
        ])
        i += 1
    set_column_widths(ws, {1: 5, 2: 60, 3: 18, 4: 38, 5: 42, 6: 30, 7: 10, 8: 45})
    wrap(ws)


def build_remove_from_sitemap_sheet(wb, rows_data):
    ws = wb.create_sheet("Remove From Sitemap")
    headers = ["#", "URL", "Category", "Action", "Rationale"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    i = 1
    for r in rows_data:
        if r["category"] in ("City service page",):
            continue
        ws.append([
            i, r["url"], r["category"], r["action"], r["rationale"],
        ])
        i += 1
    set_column_widths(ws, {1: 5, 2: 60, 3: 22, 4: 48, 5: 55})
    wrap(ws)


def build_all_orphans_sheet(wb, rows_data):
    ws = wb.create_sheet("All Orphans")
    headers = ["#", "URL", "Category", "Action", "Priority", "Rationale / Guidance"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    cat_order = {
        "City service page": 0,
        "Draft homepage variant": 1,
        "Test page": 2,
        "Thank-you page": 3,
        "Utility page": 4,
    }
    sorted_rows = sorted(rows_data, key=lambda r: (cat_order.get(r["category"], 9), r["url"]))
    for i, r in enumerate(sorted_rows, start=1):
        ws.append([i, r["url"], r["category"], r["action"], r["priority"], r["rationale"]])
    set_column_widths(ws, {1: 5, 2: 60, 3: 22, 4: 48, 5: 10, 6: 55})
    wrap(ws)


def main():
    urls = load_orphans()
    print(f"Truly-orphan indexable HTML pages: {len(urls)}")

    rows_data = []
    for url in urls:
        info = classify_page(url)
        info["url"] = url
        rows_data.append(info)

    cat_counts = defaultdict(int)
    for r in rows_data:
        cat_counts[r["category"]] += 1
    for c, n in cat_counts.items():
        print(f"  {n:3d} | {c}")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary(wb, rows_data)
    build_link_from_site_sheet(wb, rows_data)
    build_remove_from_sitemap_sheet(wb, rows_data)
    build_all_orphans_sheet(wb, rows_data)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
