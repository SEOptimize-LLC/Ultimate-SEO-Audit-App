"""
Build Excel action plan for Superior Water & Air — sitemap cleanup.

Data source: Clients/Superior/superior_sitemaps_all.xlsx
  - 513 total URLs in the Rank Math sitemaps
  - 289 flagged non-indexable by Screaming Frog (audit doc cited "284")

Breakdown of non-indexable URLs:
  - 83 x 404 (broken image URLs under /wp-content/uploads/)
  - 68 x 301 (redirects that shouldn't be in the sitemap)
  - 135 x 429 (rate-limited during crawl — NOT actual problems, need re-crawl)
  - 2 x canonicalized
  - 1 x other

The 429s are crawl artifacts, not real non-indexable URLs. True cleanup work is
~153 URLs (83 + 68 + 2). This Excel surfaces the full 289 but separates confirmed
problems from crawl-artifact rows that need re-verification.

Output: Clients/Superior/Full SEO Audit/superior_sitemap_cleanup_plan.xlsx
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
SRC = os.path.join(ROOT, "Clients/Superior/superior_sitemaps_all.xlsx")
OUT = os.path.join(ROOT, "Clients/Superior/Full SEO Audit/superior_sitemap_cleanup_plan.xlsx")

IMAGE_EXTS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff",
)


def classify_url(url: str, status_code, indexability, indexability_status):
    """
    Return (action_category, recommended_action, priority, rationale, which_sitemap).
    """
    path = urlparse(url).path.lower()
    a = url.lower()
    is_image = any(a.endswith(e) for e in IMAGE_EXTS)

    # Determine likely source sitemap
    if "/wp-content/uploads/" in a and is_image:
        sitemap = "image sitemap (or image reference in post/page sitemap)"
    elif "/service-areas/" in path:
        sitemap = "page sitemap (service-areas)"
    elif "/hvac/" in path or "/water/" in path or "/plumbing-services/" in path:
        sitemap = "page sitemap (services)"
    elif path.startswith("/20") and path.count("/") >= 3:
        sitemap = "post sitemap (dated blog archive)"
    elif any(
        seg in path
        for seg in ("/blog/", "/category/", "/tag/", "/author/", "/page/")
    ):
        sitemap = "post sitemap or archive sitemap"
    else:
        sitemap = "post sitemap"

    # Classify by status code + context
    if status_code == 404:
        if is_image:
            return (
                "Remove broken image from sitemap",
                "Remove from image sitemap + delete the broken image reference",
                "Medium",
                "Image file returns 404. Shouldn't be in any sitemap. Also covered in the 'broken images' plan — fixing that plan resolves this automatically.",
                sitemap,
            )
        return (
            "Remove 404 from sitemap",
            "Remove from sitemap + decide: restore page or 301 to a relevant URL",
            "High",
            "HTML page returns 404 but is still listed in the sitemap. Remove immediately and decide whether to restore or redirect.",
            sitemap,
        )
    if status_code == 301:
        return (
            "Remove redirect from sitemap",
            "Remove from sitemap — only the final destination URL should be listed",
            "High",
            "URL 301-redirects to a different destination. Sitemaps should only contain final, canonical, indexable URLs — not redirect sources.",
            sitemap,
        )
    if indexability_status == "Canonicalised":
        return (
            "Remove canonicalized URL from sitemap",
            "Remove from sitemap — list only the canonical URL",
            "High",
            "URL has a canonical tag pointing to a different URL. Only the canonical should be in the sitemap.",
            sitemap,
        )
    if status_code == 429:
        return (
            "Re-crawl to verify",
            "Re-crawl — status was 429 (rate-limited), not a confirmed problem",
            "Low",
            "Screaming Frog received a 429 (Too Many Requests) during the crawl. This is a crawl artifact, not a real non-indexable URL. Re-run the crawl with a slower rate to get a real status code.",
            sitemap,
        )
    return (
        "Review manually",
        "Review and decide",
        "Medium",
        "Could not classify automatically. Review the URL and its response manually.",
        sitemap,
    )


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


def load_rows():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["1 - All"]
    rows = []
    total = 0
    indexable = 0
    non_indexable = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        addr = row[0]
        if not addr:
            continue
        total += 1
        indexability = row[4]
        if indexability == "Indexable":
            indexable += 1
            continue
        non_indexable += 1
        status_code = int(row[2]) if row[2] else None
        category, action, priority, rationale, sitemap = classify_url(
            addr, status_code, indexability, row[5]
        )
        rows.append(
            {
                "url": addr,
                "status_code": status_code,
                "indexability_status": row[5],
                "category": category,
                "action": action,
                "priority": priority,
                "rationale": rationale,
                "likely_sitemap": sitemap,
            }
        )
    wb.close()
    return rows, {"total": total, "indexable": indexable, "non_indexable": non_indexable}


def build_summary(wb, rows, stats):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — Sitemap Cleanup Action Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "Context"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "The Rank Math sitemaps currently list 513 URLs. 289 of those (56%) are non-indexable — "
        "they return 404s, 301s, or are canonicalized to other URLs. Sitemaps should only contain "
        "final, indexable, canonical URLs. Non-indexable entries waste crawl budget, confuse search "
        "engines, and dilute the authority signal the sitemap is supposed to send."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 85

    ws["A7"] = "Note on the count"
    ws["A7"].font = Font(bold=True, size=11)
    ws["A8"] = (
        "The original audit cited '284 non-indexable URLs (55% of sitemap)'. The full sitemap data "
        "pulled for this plan shows 289 non-indexable URLs — a close match (the 5-row difference is "
        "likely a recount variance). However, 135 of those 289 returned HTTP 429 (Too Many Requests) "
        "during the Screaming Frog crawl — those are crawl artifacts, not confirmed non-indexable URLs. "
        "The real cleanup workload is ~154 confirmed-bad URLs, plus 135 that need a re-crawl to verify."
    )
    ws["A8"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A8:F8")
    ws.row_dimensions[8].height = 110

    ws["A10"] = "Sitemap Health Snapshot"
    ws["A10"].font = Font(bold=True, size=12)
    ws["A11"] = "Total sitemap URLs"
    ws["B11"] = stats["total"]
    ws["A12"] = "Indexable (correct)"
    ws["B12"] = stats["indexable"]
    ws["A13"] = "Non-indexable (to clean up)"
    ws["B13"] = stats["non_indexable"]
    ws["A14"] = "% Non-indexable"
    ws["B14"] = f"{stats['non_indexable'] / stats['total'] * 100:.1f}%"

    ws["A16"] = "Breakdown by Action Category"
    ws["A16"].font = Font(bold=True, size=12)
    cat_counts = defaultdict(int)
    for r in rows:
        cat_counts[r["category"]] += 1

    ws["A17"] = "Category"
    ws["B17"] = "Count"
    ws["C17"] = "Priority"
    ws["D17"] = "Action"
    style_header(ws, 17, 4)

    display = [
        ("Remove 404 from sitemap", "High", "Remove + decide: restore or 301"),
        ("Remove redirect from sitemap", "High", "Remove — only final URL belongs in sitemap"),
        ("Remove canonicalized URL from sitemap", "High", "Remove — list only canonical"),
        ("Remove broken image from sitemap", "Medium", "Remove from image sitemap"),
        ("Re-crawl to verify", "Low", "Re-run crawl with slower rate; these 429s aren't confirmed issues"),
        ("Review manually", "Medium", "Case-by-case review"),
    ]
    r = 18
    for cat, prio, action in display:
        ws.cell(row=r, column=1, value=cat)
        ws.cell(row=r, column=2, value=cat_counts.get(cat, 0))
        ws.cell(row=r, column=3, value=prio)
        ws.cell(row=r, column=4, value=action)
        ws.cell(row=r, column=4).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1

    r += 1
    confirmed = sum(
        cat_counts.get(c, 0)
        for c in (
            "Remove 404 from sitemap",
            "Remove redirect from sitemap",
            "Remove canonicalized URL from sitemap",
            "Remove broken image from sitemap",
        )
    )
    needs_recrawl = cat_counts.get("Re-crawl to verify", 0)
    ws.cell(row=r, column=1, value="Confirmed cleanup workload").font = Font(bold=True)
    ws.cell(row=r, column=2, value=confirmed)
    r += 1
    ws.cell(row=r, column=1, value="Needs re-crawl to verify (429)").font = Font(bold=True)
    ws.cell(row=r, column=2, value=needs_recrawl)

    r += 2
    ws.cell(row=r, column=1, value="How to use this file").font = Font(bold=True, size=12)
    r += 1
    ws.cell(
        row=r,
        column=1,
        value=(
            "The Rank Math sitemap is auto-generated based on post/page content and Rank Math's "
            "per-URL indexability settings. You can't 'delete' a URL from the sitemap manually — "
            "instead:\n\n"
            "1. For 301 redirects: the redirect itself should already remove the source from the sitemap. "
            "If the source URL still appears, check Rank Math → SEO meta → Robots meta → Disable indexing.\n"
            "2. For 404s: delete the page from WordPress, or create a proper 301 redirect to a relevant URL.\n"
            "3. For canonicalized URLs: review the canonical tag — the wrong URL is being submitted.\n"
            "4. For broken images: covered in the broken-images plan. Fixing those removes them from the image sitemap.\n"
            "5. After each cleanup batch, re-submit sitemaps in Google Search Console to speed up re-crawl.\n"
            "6. For 'Re-crawl to verify' rows: ignore for now — re-run Screaming Frog with slower rate limits before taking action."
        ),
    )
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 220

    set_column_widths(ws, {1: 38, 2: 15, 3: 12, 4: 50, 5: 15, 6: 15})


def build_category_sheet(wb, rows, name, categories):
    ws = wb.create_sheet(name)
    headers = [
        "#",
        "URL",
        "Status Code",
        "Indexability Status",
        "Likely Sitemap Source",
        "Priority",
        "Rationale",
        "Action",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    i = 1
    for r in rows:
        if r["category"] not in categories:
            continue
        ws.append(
            [
                i,
                r["url"],
                r["status_code"],
                r["indexability_status"],
                r["likely_sitemap"],
                r["priority"],
                r["rationale"],
                r["action"],
            ]
        )
        i += 1
    set_column_widths(ws, {1: 5, 2: 62, 3: 10, 4: 18, 5: 32, 6: 10, 7: 50, 8: 45})
    wrap(ws)


def main():
    rows, stats = load_rows()
    print(f"Total sitemap URLs: {stats['total']}")
    print(f"Indexable: {stats['indexable']}")
    print(f"Non-indexable: {stats['non_indexable']}")

    cat_counts = defaultdict(int)
    for r in rows:
        cat_counts[r["category"]] += 1
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:4d} | {cat}")

    # Sort rows: confirmed cleanups first by priority, then 429s, then manual review
    category_order = {
        "Remove 404 from sitemap": 0,
        "Remove redirect from sitemap": 1,
        "Remove canonicalized URL from sitemap": 2,
        "Remove broken image from sitemap": 3,
        "Review manually": 4,
        "Re-crawl to verify": 5,
    }
    rows.sort(key=lambda r: (category_order.get(r["category"], 9), r["url"]))

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary(wb, rows, stats)
    build_category_sheet(
        wb, rows, "Remove 404s",
        {"Remove 404 from sitemap", "Remove broken image from sitemap"},
    )
    build_category_sheet(
        wb, rows, "Remove Redirects",
        {"Remove redirect from sitemap"},
    )
    build_category_sheet(
        wb, rows, "Remove Canonicalized",
        {"Remove canonicalized URL from sitemap"},
    )
    build_category_sheet(
        wb, rows, "Re-crawl Needed",
        {"Re-crawl to verify"},
    )
    build_category_sheet(
        wb, rows, "All Non-Indexable",
        set(cat_counts.keys()),
    )

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    wb.save(OUT)
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
