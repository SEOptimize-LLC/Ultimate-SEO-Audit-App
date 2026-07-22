"""
Verify the live status of every URL flagged in the original sitemap_cleanup_plan
'Remove Redirects', 'Remove 404s', and 'Remove Canonicalized' tabs.

Then merge with the previously-verified 'Re-crawl Needed' (429) results so we
have one consolidated, current truth about every non-indexable URL in the
sitemap.

Output:
    Clients/Superior/Full SEO Audit/superior_sitemap_cleanup_plan_v2.xlsx
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
from collections import Counter, defaultdict
from datetime import date

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
PLAN_XLSX = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_sitemap_cleanup_plan.xlsx"
)
PRIOR_429_JSON = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_429_verification_results.json"
)
OUT_XLSX = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_sitemap_cleanup_plan_v2.xlsx"
)

UA = (
    "Mozilla/5.0 (compatible; SEOptimizeAuditor/1.0; "
    "+https://seoptimizellc.com)"
)
DELAY = 0.4
TIMEOUT = 10

NAVY = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HFONT = Font(bold=True, color="FFFFFF", size=11)


def head_check(url: str) -> dict:
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return {"live_status": resp.status, "live_final": resp.url, "error": None}
    except urllib.error.HTTPError as e:
        return {"live_status": e.code, "live_final": getattr(e, "url", url), "error": None}
    except urllib.error.URLError as e:
        return {"live_status": None, "live_final": url, "error": f"URLError: {e.reason}"}
    except Exception as e:
        return {"live_status": None, "live_final": url, "error": f"{type(e).__name__}: {e}"}


def load_tab(name: str) -> list[dict]:
    wb = openpyxl.load_workbook(PLAN_XLSX, read_only=True, data_only=True)
    ws = wb[name]
    headers = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[1]:
            continue
        rec = dict(zip(headers, row))
        rec["_source_tab"] = name
        rows.append(rec)
    wb.close()
    return rows


def main() -> None:
    # Load the rows we want to live-check
    tabs_to_check = ["Remove Redirects", "Remove 404s", "Remove Canonicalized"]
    all_rows = []
    for t in tabs_to_check:
        rows = load_tab(t)
        print(f"  Loaded {len(rows)} rows from {t!r}")
        all_rows.extend(rows)

    print(f"\nTotal rows to live-verify: {len(all_rows)}")
    print(f"Estimated time: {len(all_rows) * DELAY / 60:.1f} minutes")
    print()

    # Live HEAD check each URL
    for i, rec in enumerate(all_rows, start=1):
        url = rec["URL"]
        info = head_check(url)
        rec.update(info)
        if i % 20 == 0 or i == len(all_rows):
            counts = Counter(r["live_status"] for r in all_rows[:i])
            print(f"  [{i:>3}/{len(all_rows)}] {dict(counts)}")
        time.sleep(DELAY)

    # Second pass: any URL that came back 403 is almost certainly WP Engine's
    # CDN rate-limiting our HEAD batch. Re-check them individually with a
    # longer pause so we get the real status.
    rate_limited_403s = [r for r in all_rows if r["live_status"] == 403]
    if rate_limited_403s:
        print(f"\n  Re-checking {len(rate_limited_403s)} URLs that returned 403 "
              "(likely CDN rate-limit)...")
        time.sleep(8.0)  # let the rate-limit window expire
        for i, rec in enumerate(rate_limited_403s, start=1):
            info = head_check(rec["URL"])
            rec.update(info)
            time.sleep(2.0)  # extra-slow re-check
            if i % 5 == 0 or i == len(rate_limited_403s):
                counts = Counter(r["live_status"] for r in rate_limited_403s[:i])
                print(f"    re-check [{i}/{len(rate_limited_403s)}]: {dict(counts)}")

    # Load prior 429 results
    if os.path.exists(PRIOR_429_JSON):
        prior_429 = json.load(open(PRIOR_429_JSON, encoding="utf-8"))
        print(f"\nLoaded {len(prior_429)} prior 429-verified URLs")
    else:
        prior_429 = []

    # Build full record list
    full_records = []
    for rec in all_rows:
        full_records.append({
            "url": rec["URL"],
            "original_status": rec.get("Status Code", ""),
            "original_category": rec.get("Category", rec.get("_source_tab", "")),
            "live_status": rec["live_status"],
            "live_final": rec["live_final"],
            "is_image": "/wp-content/uploads/" in rec["URL"],
            "source": "sitemap_cleanup_plan",
        })
    for rec in prior_429:
        full_records.append({
            "url": rec["url"],
            "original_status": 429,
            "original_category": "Re-crawl Needed (429)",
            "live_status": rec["status"],
            "live_final": rec.get("final_url", rec["url"]),
            "is_image": "/wp-content/uploads/" in rec["url"],
            "source": "429_verification",
        })

    # Categorize each by current live status
    def categorize(r):
        if r["live_status"] == 200:
            # Truly indexable now
            if r["original_status"] == 301:
                # Was a redirect, now resolves directly — likely because we
                # deleted the redirect rule. Re-evaluate whether the underlying
                # post should still exist.
                return "RECOVERED_200"
            return "TRULY_INDEXABLE"
        if r["live_status"] in (301, 302, 307, 308):
            return "REDIRECTING"
        if r["live_status"] == 404:
            if r["is_image"]:
                return "IMAGE_404"
            return "PAGE_404"
        if r["live_status"] == 410:
            return "ALREADY_410"
        if r["live_status"] is None:
            return "ERROR"
        return f"OTHER_{r['live_status']}"

    for r in full_records:
        r["bucket"] = categorize(r)

    # Stats
    cat_counts = Counter(r["bucket"] for r in full_records)
    print()
    print("Final categorization (live):")
    for cat, n in sorted(cat_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {cat:25s} : {n}")

    # Write the workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary(wb, full_records, cat_counts)
    build_action_tabs(wb, full_records)
    wb.save(OUT_XLSX)
    print(f"\nSaved: {OUT_XLSX}")


def style_header(ws, row, n_cols):
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = NAVY
        cell.font = HFONT
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 28


def widths(ws, w):
    for c, n in w.items():
        ws.column_dimensions[get_column_letter(c)].width = n


def wrap(ws):
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_summary(wb, records, counts):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — Sitemap Cleanup Plan v2 (Live-Verified)"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "Why this v2 exists"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "The original sitemap_cleanup_plan was based on a single Screaming Frog "
        "crawl. Many URLs marked 'redirect' (301) in that crawl now return 404 — "
        "the redirect rules were deleted as part of the URL migration cleanup, but "
        "the underlying WordPress posts are also gone. Other URLs marked 'rate-"
        "limited' (429) in the original crawl turned out to be truly broken once "
        "we did live HEAD checks. This v2 plan reflects the CURRENT live state."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 100

    ws["A7"] = "Live verification breakdown"
    ws["A7"].font = Font(bold=True, size=12)

    ws["A8"] = "Bucket"
    ws["B8"] = "Count"
    ws["C8"] = "Action"
    ws["D8"] = "Priority"
    style_header(ws, 8, 4)

    # Display in priority order
    display_order = [
        ("PAGE_404", "Add 301 → relevant live page (or 410 if no good target)", "High"),
        ("IMAGE_404", "Add to 410 Gone batch", "Medium"),
        ("REDIRECTING", "Either remove from sitemap, or remove the post entirely", "Medium"),
        ("RECOVERED_200", "Now resolves to 200 — verify it should be indexable; if not, add noindex", "Medium"),
        ("ALREADY_410", "Already correct — no action needed", "—"),
        ("TRULY_INDEXABLE", "Sitemap entry is correct — no action needed", "—"),
        ("ERROR", "Manual recheck", "Low"),
    ]
    r = 9
    for bucket, action, prio in display_order:
        if counts.get(bucket, 0) == 0:
            continue
        ws.cell(row=r, column=1, value=bucket)
        ws.cell(row=r, column=2, value=counts.get(bucket, 0))
        ws.cell(row=r, column=3, value=action)
        ws.cell(row=r, column=4, value=prio)
        ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Total URLs verified").font = Font(bold=True)
    ws.cell(row=r, column=2, value=len(records))

    r += 2
    ws.cell(row=r, column=1, value="Tabs in this file").font = Font(bold=True, size=12)
    r += 1
    ws.cell(row=r, column=1, value=(
        "1. Summary — this sheet\n"
        "2. Page 404s (301 candidates) — pages that returned 404 on live check; need 301 or 410\n"
        "3. Image 404s — broken images for the next 410 Gone batch\n"
        "4. Still Redirecting — URLs that 301 on live; should be removed from sitemap\n"
        "5. Recovered 200 — URLs that now resolve to 200; verify they should be indexable\n"
        "6. Errors — couldn't be checked, need manual review\n"
        "7. All Records — full live-verification dataset"
    ))
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 130

    widths(ws, {1: 22, 2: 10, 3: 65, 4: 12, 5: 15, 6: 15})


def build_action_tabs(wb, records):
    # Page 404s
    items = [r for r in records if r["bucket"] == "PAGE_404"]
    if items:
        ws = wb.create_sheet("Page 404s")
        ws.append(["#", "URL", "Original status (SF)", "Live status", "Suggested 301 target", "Action"])
        style_header(ws, 1, 6)
        for i, r in enumerate(items, start=1):
            suggestion = suggest_301_target(r["url"])
            action = "Add 301 to suggested target" if suggestion else "No clear target — 410 Gone OR redirect to /blog/"
            ws.append([i, r["url"], r["original_status"], r["live_status"], suggestion, action])
        widths(ws, {1: 5, 2: 60, 3: 18, 4: 12, 5: 50, 6: 45})
        wrap(ws)

    # Image 404s
    items = [r for r in records if r["bucket"] == "IMAGE_404"]
    if items:
        ws = wb.create_sheet("Image 404s")
        ws.append(["#", "URL", "Original status (SF)", "Live status", "Action"])
        style_header(ws, 1, 5)
        for i, r in enumerate(items, start=1):
            ws.append([i, r["url"], r["original_status"], r["live_status"],
                      "Add to 410 Gone batch — broken image, no source page references it"])
        widths(ws, {1: 5, 2: 70, 3: 18, 4: 12, 5: 50})
        wrap(ws)

    # Still Redirecting
    items = [r for r in records if r["bucket"] == "REDIRECTING"]
    if items:
        ws = wb.create_sheet("Still Redirecting")
        ws.append(["#", "URL", "Original status (SF)", "Live status", "Final destination", "Action"])
        style_header(ws, 1, 6)
        for i, r in enumerate(items, start=1):
            ws.append([i, r["url"], r["original_status"], r["live_status"], r["live_final"],
                      "Either delete underlying WP post (sitemap auto-cleans) OR mark URL noindex"])
        widths(ws, {1: 5, 2: 55, 3: 18, 4: 12, 5: 55, 6: 50})
        wrap(ws)

    # Recovered 200
    items = [r for r in records if r["bucket"] == "RECOVERED_200"]
    if items:
        ws = wb.create_sheet("Recovered 200")
        ws.append(["#", "URL", "Original status (SF)", "Live status", "Notes"])
        style_header(ws, 1, 5)
        for i, r in enumerate(items, start=1):
            note = (
                "URL now resolves directly (200 OK). The redirect rule that previously made it 301 "
                "was deleted in the redirect cleanup. Verify whether this URL should be indexable; "
                "if it represents a duplicate/legacy post, add noindex meta or delete the post."
            )
            ws.append([i, r["url"], r["original_status"], r["live_status"], note])
        widths(ws, {1: 5, 2: 60, 3: 18, 4: 12, 5: 65})
        wrap(ws)

    # Errors
    items = [r for r in records if r["bucket"] == "ERROR"]
    if items:
        ws = wb.create_sheet("Errors")
        ws.append(["#", "URL", "Original status (SF)", "Live status", "Notes"])
        style_header(ws, 1, 5)
        for i, r in enumerate(items, start=1):
            ws.append([i, r["url"], r["original_status"], r["live_status"], "Live check failed — recheck manually"])
        widths(ws, {1: 5, 2: 60, 3: 18, 4: 12, 5: 50})
        wrap(ws)

    # All Records
    ws = wb.create_sheet("All Records")
    ws.append(["#", "URL", "Original status (SF)", "Original category",
               "Live status", "Live final URL", "Bucket", "Source"])
    style_header(ws, 1, 8)
    for i, r in enumerate(records, start=1):
        ws.append([i, r["url"], r["original_status"], r["original_category"],
                   r["live_status"], r["live_final"], r["bucket"], r["source"]])
    widths(ws, {1: 5, 2: 55, 3: 12, 4: 22, 5: 10, 6: 55, 7: 18, 8: 22})
    wrap(ws)


def suggest_301_target(url: str) -> str:
    """Heuristic: if the URL contains a recognizable post slug, suggest /blog/<slug>/.

    The migration plan moves all blog posts to /blog/<slug>/. Pages that are
    legitimate blog content getting 404s should redirect there. For year-prefix
    URLs (/2017/06/post-slug/), strip the year/month prefix.
    """
    import re
    path = url.replace("https://superiorwaterandair.com", "").rstrip("/")
    # Pattern: /YYYY/MM/<slug> or /YYYY/MM/<slug>/feed or similar
    m = re.match(r"^/\d{4}/\d{2}/([^/]+)", path)
    if m:
        slug = m.group(1)
        return f"https://superiorwaterandair.com/blog/{slug}/"
    # Bare /post-slug/ that returned 404 — could still go to /blog/<slug>/
    m = re.match(r"^/([^/]+)$", path)
    if m:
        slug = m.group(1)
        # Don't suggest /blog/ for known service paths
        if not slug.startswith(("hvac", "water", "plumbing", "service", "emergency", "wp-content", "page", "category", "author")):
            return f"https://superiorwaterandair.com/blog/{slug}/"
    return ""


if __name__ == "__main__":
    main()
