"""
Build Excel action plan for Superior Water & Air — orphan pages in sitemaps.

Data source: Clients/Superior/Superior - Technical Audit.xlsx
  - Tab 'sitemaps_orphan_urls' (106 rows total; 34 indexable HTML, 32 truly orphan after excluding self-links)
  - Tab 'all_inlinks' (used to verify inlink counts, excluding self-links)

The audit doc cited "53 orphaned pages" from a SEMrush data pull. The Screaming Frog
crawl data available here shows 32 genuinely orphaned indexable HTML pages after
filtering out broken images, asset files, non-indexable URLs, and self-links from
headers/footers. We report the real count and flag the discrepancy.

Output: Clients/Superior/Full SEO Audit/superior_orphan_pages_plan.xlsx
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
SRC = os.path.join(ROOT, "Clients/Superior/Superior - Technical Audit.xlsx")
OUT = os.path.join(ROOT, "Clients/Superior/Full SEO Audit/superior_orphan_pages_plan.xlsx")

ASSET_EXTS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff",
    ".woff", ".woff2", ".ttf", ".otf", ".css", ".js", ".mp4", ".pdf",
)
PATH_EXCLUDES = ("/wp-content/", "/cdn-cgi/", "/wp-admin/", "/wp-includes/")


def is_asset(url: str) -> bool:
    a = url.lower()
    return any(a.endswith(e) for e in ASSET_EXTS) or any(p in a for p in PATH_EXCLUDES)


def classify_page(url: str) -> tuple[str, str, str, str]:
    """
    Return (category, recommended_action, priority, rationale).
    """
    path = urlparse(url).path.lower()

    if "-ppc-" in path or path.rstrip("/").endswith("ppc"):
        return (
            "PPC landing page",
            "Remove from sitemap + noindex",
            "High",
            "PPC landing pages have no SEO value. They inflate sitemap noise and shouldn't be in organic search results.",
        )
    if path in ("/thank-you/", "/application-form/", "/test-lead-form/", "/404-error/"):
        return (
            "Utility page",
            "Remove from sitemap + noindex",
            "High",
            "Utility page (form submission, error page, or internal test page). Has no SEO value and shouldn't be indexed.",
        )

    # Detect "/<service-hub>/<keyword>-<city>/" pattern
    # Parent hubs: /hvac/, /water/, /water/water-heaters/, /water/water-treatment/
    parts = [p for p in path.strip("/").split("/") if p]
    if not parts:
        return ("Other", "Review manually", "Medium", "Could not classify automatically.")

    # Try to extract city from slug
    slug = parts[-1]
    city_hint = ""
    utah_cities = [
        "salt-lake-city", "salt-lake", "ogden", "orem", "provo", "sandy",
        "park-city", "lehi", "draper", "bluffdale", "midvale", "kearns",
        "springville", "south-jordan", "spanish-fork", "cedar-city",
        "north-ogden", "north-salt-lake", "millcreek", "herriman", "highland",
        "salem", "tooele", "st-george", "west-valley", "west-jordan", "layton",
    ]
    for city in sorted(utah_cities, key=len, reverse=True):
        if city in slug:
            city_hint = city.replace("-", " ").title()
            break

    # Parent hub for linking decision
    if parts[0] == "hvac":
        hub = "/hvac/"
        service_type = "HVAC"
    elif parts[0] == "water" and len(parts) >= 2 and parts[1] == "water-heaters":
        hub = "/water/water-heaters/"
        service_type = "Water Heaters"
    elif parts[0] == "water" and len(parts) >= 2 and parts[1] == "water-treatment":
        hub = "/water/water-treatment/"
        service_type = "Water Treatment"
    elif parts[0] == "water":
        hub = "/water/"
        service_type = "Water (general)"
    elif parts[0] == "plumbing-services":
        hub = "/plumbing-services/"
        service_type = "Plumbing"
    else:
        hub = "(unknown)"
        service_type = "Other"

    city_area = f"/service-areas/{city_hint.lower().replace(' ', '-')}-utah/" if city_hint else "(no city detected)"

    rationale = (
        f"City-specific service page ({service_type} in {city_hint or 'unknown city'}). "
        f"Link from: (1) parent hub {hub}, and (2) the city's service-area page {city_area} "
        f"if it exists. Use descriptive anchor text, not 'click here'."
    )
    return ("City service page", "Add internal links", "Medium", rationale)


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


def load_orphans():
    """Return list of truly-orphan indexable HTML pages (no non-self inlinks)."""
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["sitemaps_orphan_urls"]
    candidates = set()
    status_by_url = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        addr = row[0]
        if not addr:
            continue
        if is_asset(addr):
            continue
        if row[4] != "Indexable":
            continue
        candidates.add(addr)
        status_by_url[addr] = {"status_code": row[2], "indexability": row[4]}

    # Count non-self hyperlink inlinks from all_inlinks
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

    truly_orphan = [u for u in candidates if real_inlinks[u] == 0]
    wb.close()
    return truly_orphan, status_by_url


def build_summary(wb, rows_data):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — Orphan Pages Action Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "Context"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "Orphan pages are URLs listed in the XML sitemaps that have no internal links pointing "
        "to them from the rest of the site. Google can still find them via the sitemap, but the "
        "absence of internal links signals low importance — they receive minimal crawl priority, "
        "rank poorly, and often sit outside the site's topical silo structure."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 80

    ws["A7"] = "Note on the count"
    ws["A7"].font = Font(bold=True, size=11)
    ws["A8"] = (
        "The original technical audit cited '53 orphaned pages in sitemaps' from a SEMrush data pull. "
        "Pulling from the Screaming Frog crawl data and excluding broken images, asset files (CSS/JS/fonts), "
        "non-indexable URLs, and self-links from site-wide header/footer navigation, the true count of "
        "indexable HTML pages with zero real inlinks is 32. Of those, 22 are legitimate service pages needing "
        "internal linking, and 10 are utility/PPC pages that should be removed from the sitemap entirely."
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
    ws["C11"] = "Action"
    ws["D11"] = "Priority"
    style_header(ws, 11, 4)

    rows_display = [
        ("City service page", "Add internal links from parent hub + city page", "Medium"),
        ("PPC landing page", "Remove from sitemap + noindex", "High"),
        ("Utility page", "Remove from sitemap + noindex", "High"),
        ("Other", "Review manually", "Medium"),
    ]
    r = 12
    for cat, action, prio in rows_display:
        ws.cell(row=r, column=1, value=cat)
        ws.cell(row=r, column=2, value=cat_counts.get(cat, 0))
        ws.cell(row=r, column=3, value=action)
        ws.cell(row=r, column=4, value=prio)
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Total orphan pages").font = Font(bold=True)
    ws.cell(row=r, column=2, value=len(rows_data))

    r += 2
    ws.cell(row=r, column=1, value="How to use this file").font = Font(bold=True, size=12)
    r += 1
    ws.cell(
        row=r,
        column=1,
        value=(
            "1. Start with the 'Remove From Sitemap' tab — 10 utility/PPC pages that should be purged. "
            "This is the fastest win (remove them from Rank Math's sitemap exclusion settings + add noindex).\n"
            "2. Move to 'Link From Site' tab — 22 city service pages that need internal links. "
            "Each row lists the parent hub and the matching /service-areas/<city>-utah/ page. "
            "Add contextual links from both.\n"
            "3. Use descriptive anchor text (e.g., 'furnace repair in Park City') — don't use 'click here' or the raw URL."
        ),
    )
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 135

    set_column_widths(ws, {1: 32, 2: 12, 3: 48, 4: 12, 5: 15, 6: 15})


def build_link_from_site_sheet(wb, rows_data):
    ws = wb.create_sheet("Link From Site")
    headers = [
        "#",
        "Orphan URL (needs inlinks)",
        "Service Type",
        "Detected City",
        "Primary Link Source (parent hub)",
        "Secondary Link Source (city page)",
        "Recommended Anchor Text",
        "Priority",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    i = 1
    for r in rows_data:
        if r["category"] != "City service page":
            continue
        ws.append(
            [
                i,
                r["url"],
                r["service_type"],
                r["city"] or "—",
                r["parent_hub"],
                r["city_page"],
                r["recommended_anchor"],
                r["priority"],
            ]
        )
        i += 1

    set_column_widths(ws, {1: 5, 2: 62, 3: 18, 4: 20, 5: 30, 6: 40, 7: 45, 8: 12})
    wrap(ws)


def build_remove_from_sitemap_sheet(wb, rows_data):
    ws = wb.create_sheet("Remove From Sitemap")
    headers = ["#", "URL", "Category", "Action", "Rationale"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    i = 1
    for r in rows_data:
        if r["category"] not in ("PPC landing page", "Utility page", "Other"):
            continue
        ws.append(
            [
                i,
                r["url"],
                r["category"],
                r["action"],
                r["rationale"],
            ]
        )
        i += 1

    set_column_widths(ws, {1: 5, 2: 62, 3: 22, 4: 32, 5: 60})
    wrap(ws)


def build_all_orphans_sheet(wb, rows_data):
    ws = wb.create_sheet("All Orphans")
    headers = [
        "#",
        "URL",
        "Category",
        "Action",
        "Priority",
        "Rationale / Linking Guidance",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    cat_order = {"City service page": 0, "PPC landing page": 1, "Utility page": 2, "Other": 3}
    sorted_rows = sorted(rows_data, key=lambda r: (cat_order.get(r["category"], 9), r["url"]))
    for i, r in enumerate(sorted_rows, start=1):
        ws.append(
            [
                i,
                r["url"],
                r["category"],
                r["action"],
                r["priority"],
                r["rationale"],
            ]
        )
    set_column_widths(ws, {1: 5, 2: 62, 3: 22, 4: 38, 5: 12, 6: 60})
    wrap(ws)


def main():
    orphan_urls, _status = load_orphans()
    print(f"Truly-orphan indexable HTML pages: {len(orphan_urls)}")

    rows_data = []
    for url in orphan_urls:
        category, action, priority, rationale = classify_page(url)
        # Extract city + service + hub for linking guidance
        path = urlparse(url).path.lower()
        parts = [p for p in path.strip("/").split("/") if p]

        city = ""
        service_type = ""
        parent_hub = ""
        city_page = ""
        anchor = ""

        if category == "City service page":
            # Detect city
            utah_cities = [
                "salt-lake-city", "salt-lake", "ogden", "orem", "provo", "sandy",
                "park-city", "lehi", "draper", "bluffdale", "midvale", "kearns",
                "springville", "south-jordan", "spanish-fork", "cedar-city",
                "north-ogden", "north-salt-lake", "millcreek", "herriman",
                "highland", "salem", "tooele", "st-george",
            ]
            slug = parts[-1] if parts else ""
            for c in sorted(utah_cities, key=len, reverse=True):
                if c in slug:
                    city = c.replace("-", " ").title()
                    break

            if parts[0] == "hvac":
                parent_hub = "https://superiorwaterandair.com/hvac/"
                service_type = "HVAC"
            elif parts[0] == "water" and len(parts) >= 2 and parts[1] == "water-heaters":
                parent_hub = "https://superiorwaterandair.com/water/water-heaters/"
                service_type = "Water Heaters"
            elif parts[0] == "water" and len(parts) >= 2 and parts[1] == "water-treatment":
                parent_hub = "https://superiorwaterandair.com/water/water-treatment/"
                service_type = "Water Treatment"
            elif parts[0] == "water":
                parent_hub = "https://superiorwaterandair.com/water/"
                service_type = "Water"
            else:
                parent_hub = "(determine manually)"
                service_type = "Other"

            if city:
                city_slug = city.lower().replace(" ", "-")
                city_page = f"https://superiorwaterandair.com/service-areas/{city_slug}-utah/"
            else:
                city_page = "(no city detected — manual review)"

            # Build anchor text from slug
            slug_words = slug.replace("-utah", "").replace("-", " ")
            anchor = slug_words.strip()
            if city and city.lower() in anchor:
                anchor = anchor.title()
            else:
                anchor = (anchor + (f" in {city}" if city else "")).strip().title()

        rows_data.append(
            {
                "url": url,
                "category": category,
                "action": action,
                "priority": priority,
                "rationale": rationale,
                "service_type": service_type,
                "city": city,
                "parent_hub": parent_hub,
                "city_page": city_page,
                "recommended_anchor": anchor,
            }
        )

    # Summary
    cat_counts = defaultdict(int)
    for r in rows_data:
        cat_counts[r["category"]] += 1
    for cat, count in cat_counts.items():
        print(f"  {count:3d} | {cat}")

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
