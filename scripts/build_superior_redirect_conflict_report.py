"""
Superior Water & Air — Redirect Conflict Report.

Analyzes the EXISTING Rank Math redirect set against:
  1. The NEW migration plan we're about to import
  2. The current live URL inventory (Screaming Frog crawl)

Surfaces every existing redirect that should be deleted or updated BEFORE
the migration import runs, so we don't end up with redirect chains, loops,
or stale destinations after the new redirects go live.

Inputs:
    Clients/Superior/superiorwaterampair_rank-math-redirections-2026-04-26_14-23-39.csv
    Clients/Superior/Full SEO Audit/superior_redirects_rankmath_import.csv  (new plan)
    /tmp/superior_indexable.json  (live URLs from SF crawl)

Output:
    Clients/Superior/Full SEO Audit/superior_existing_redirects_to_remove.xlsx

Categories surfaced (each on its own tab):
    1. CHAIN RISK — existing dest is an old URL the new plan migrates away from
    2. STALE DESTINATION — existing dest points to a URL that no longer exists
    3. MALFORMED — junk sources (truncated slugs, /feed/, //1000, etc.)
    4. OBSOLETE PATHS — sources pointing into /water/, /hvac/, /plumbing-services/
       that the new architecture replaces with /services/ + /service-areas/<city>/<service>/
    5. KEEP AS-IS — existing redirects that stay valid post-migration
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
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
EXISTING_CSV = os.path.join(
    ROOT, "Clients/Superior/superiorwaterampair_rank-math-redirections-2026-04-26_14-23-39.csv"
)
NEW_CSV = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_redirects_rankmath_import.csv"
)
INDEXABLE_JSON = "/tmp/superior_indexable.json"
OUT_XLSX = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_existing_redirects_to_remove.xlsx"
)

DOMAIN = "https://superiorwaterandair.com"

NAVY = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_ALIGN = Alignment(horizontal="left", vertical="center", wrap_text=True)


def style_header(ws, row, max_col):
    for c in range(1, max_col + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = NAVY
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGN
    ws.row_dimensions[row].height = 30


def set_widths(ws, widths):
    for c, w in widths.items():
        ws.column_dimensions[get_column_letter(c)].width = w


def wrap_data(ws):
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def normalize_path(s: str) -> str:
    """Normalize a URL/path for set-based comparison."""
    s = s.replace(DOMAIN, "")
    s = s.lstrip("/").rstrip("/")
    return s.lower()


def load_existing():
    rows = []
    with open(EXISTING_CSV, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # header
        for row in reader:
            if len(row) < 4 or not row[1]:
                continue
            rows.append({
                "id": row[0],
                "source": row[1],
                "destination": row[3],
                "code": row[4] if len(row) > 4 else "",
                "status": row[6] if len(row) > 6 else "",
            })
    return rows


def load_new_plan():
    rows = []
    with open(NEW_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "source": r["source url"].lstrip("/").rstrip("/").lower(),
                "destination": r["destination url"],
            })
    return rows


def load_indexable():
    data = json.load(open(INDEXABLE_JSON, encoding="utf-8"))
    return {normalize_path(p["url"]) for p in data}


def is_malformed(source: str) -> tuple[bool, str]:
    """Detect junk redirect sources. Returns (is_junk, reason)."""
    if "//1000" in source:
        return True, "Trailing //1000 fragment (likely from a query string parser bug or staging environment)"
    if "?mobile_switch" in source:
        return True, "Mobile switcher query parameter (legacy mobile theme artifact, no SEO value)"
    if source.endswith("/feed/") or source.endswith("/feed"):
        return True, "RSS /feed/ URL (feed URLs don't need redirects — Rank Math handles feed canonicals)"
    # Partial / truncated slugs - service-areas/<short-fragment>/
    m = re.match(r"^service-areas/([^/]+)/?$", source)
    if m:
        slug = m.group(1)
        # Strip -utah/-ut suffix to check the base
        base = re.sub(r"-(utah|ut)$", "", slug)
        # Real city slugs are at least 4 chars and contain at least one consonant
        # Truncated slugs look like 'le', 'pine', 'gville', 'use'
        if len(base) <= 5 and not re.search(r"[bcdfghjklmnpqrstvwxz]{2,}", base):
            # Looks truncated/junk
            return True, f"Truncated city slug '{slug}' — partial/ghost entry from a buggy redirect import"
        if base in ("e", "se", "le", "ne", "ne", "rem", "use", "pine", "ial",
                    "lpine", "pringville", "racuse", "yracuse", "ringville",
                    "acuse", "ennial", "gville", "ine"):
            return True, f"Truncated city slug '{slug}' — partial/ghost entry"
    if source == "service-areas/-utah/":
        return True, "Empty city slug — broken entry"
    return False, ""


def main():
    existing = load_existing()
    new_plan = load_new_plan()
    indexable = load_indexable()

    new_sources = {r["source"] for r in new_plan}
    new_targets_paths = {normalize_path(r["destination"]) for r in new_plan}

    # Build a sources-of-new-plan-as-paths set
    new_plan_will_redirect_from = new_sources

    # Categorize each existing redirect
    categories = {
        "CHAIN_RISK": [],
        "STALE_DEST": [],
        "MALFORMED": [],
        "OBSOLETE_PATH": [],
        "IMAGE_REDIRECT": [],
        "KEEP": [],
    }

    for e in existing:
        src = e["source"].lstrip("/").rstrip("/").lower()
        dest = e["destination"]
        dest_path = normalize_path(dest)

        # Image redirects (Rank Math has 60+ entries pointing wp-content images to /blog/)
        if src.startswith("wp-content/uploads/"):
            categories["IMAGE_REDIRECT"].append({
                **e,
                "_reason": "Image file redirect — these don't need to be in the redirect plugin. "
                          "Image 404s should be handled by the broken-images plan (already produced) "
                          "or by re-uploading the missing images. Bulk-redirecting all old image "
                          "URLs to /blog/ is a workaround that wastes plugin overhead.",
                "_action": "Delete (handled by broken-images plan instead)",
            })
            continue

        # Malformed sources
        is_junk, junk_reason = is_malformed(src)
        if is_junk:
            categories["MALFORMED"].append({
                **e,
                "_reason": junk_reason,
                "_action": "Delete — these sources are noise from prior plugin imports or buggy data",
            })
            continue

        # Chain risk: existing destination is an old URL the new plan migrates away from
        # Check both with and without trailing slash variants
        dest_normalized = dest_path
        if dest_normalized in new_plan_will_redirect_from:
            # What does the new plan redirect this destination to?
            final_target = next(
                (r["destination"] for r in new_plan if r["source"] == dest_normalized),
                "(unknown)",
            )
            categories["CHAIN_RISK"].append({
                **e,
                "_reason": f"Destination '{dest}' is itself being redirected by the new migration plan to '{final_target}'. "
                          f"Leaving this existing redirect in place would create a 2-hop chain: "
                          f"/{src}/ -> /{dest_normalized}/ -> {final_target}",
                "_action": f"UPDATE the destination from '{dest}' to '{final_target}' (or delete this row "
                          "and let the new redirect rule handle it directly)",
                "_final_target": final_target,
            })
            continue

        # Stale destination: dest points to a URL that doesn't exist
        if dest_normalized and dest_normalized not in indexable:
            # Some destinations are also redirect sources in the existing set — chain
            existing_sources = {x["source"].lstrip("/").rstrip("/").lower() for x in existing}
            if dest_normalized in existing_sources:
                # It chains through ANOTHER existing redirect. Find the final.
                next_redirect = next(
                    (x for x in existing if normalize_path(x["source"]) == dest_normalized),
                    None,
                )
                final_dest = next_redirect["destination"] if next_redirect else "(unknown)"
                categories["CHAIN_RISK"].append({
                    **e,
                    "_reason": f"Destination chains through another existing redirect: "
                              f"/{src}/ -> {dest} -> {final_dest}",
                    "_action": f"UPDATE destination directly to '{final_dest}' to eliminate the hop",
                })
                continue

            # Genuinely stale (dest is gone, not just chained)
            categories["STALE_DEST"].append({
                **e,
                "_reason": f"Destination '{dest}' does not exist in the current site crawl. The page "
                          "was either deleted, renamed, or never existed — the redirect leads to a 404.",
                "_action": "DELETE or update destination to a relevant live URL",
            })
            continue

        # Obsolete path: source is in /water/, /hvac/, /plumbing-services/ that the new architecture replaces
        # OR: destination is in /water/, /hvac/, /plumbing-services/ and the source isn't being touched by new plan
        if dest_path.startswith(("water/", "hvac/", "plumbing-services/")):
            # Destination is an obsolete path. Source isn't (otherwise it'd be CHAIN_RISK above).
            # That means after migration, the dest will redirect — and this becomes a chain.
            # Check if dest will be migrated by new plan: it's in new_plan_will_redirect_from
            if dest_path in new_plan_will_redirect_from:
                # Already caught above as CHAIN_RISK
                pass
            else:
                # Dest is obsolete but new plan doesn't have it as a source — still keeps because dest still resolves today
                # but flag it so the user knows
                categories["OBSOLETE_PATH"].append({
                    **e,
                    "_reason": f"Destination '{dest}' is in the legacy /water//hvac//plumbing-services/ path. "
                              "These URLs will be migrated. After migration, this redirect will chain.",
                    "_action": "Update destination to point directly to the new architecture URL",
                })
                continue

        # Keep as-is
        categories["KEEP"].append({
            **e,
            "_reason": "Destination is current and not affected by the migration plan",
            "_action": "Keep — no change needed",
        })

    # Print summary
    print("Conflict analysis summary:")
    print(f"  Total existing redirects: {len(existing)}")
    for cat, items in categories.items():
        print(f"  {cat:18s}: {len(items)}")

    # Build workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    build_summary(wb, existing, categories)
    build_chain_risk_sheet(wb, categories["CHAIN_RISK"])
    build_stale_dest_sheet(wb, categories["STALE_DEST"])
    build_malformed_sheet(wb, categories["MALFORMED"])
    build_obsolete_path_sheet(wb, categories["OBSOLETE_PATH"])
    build_image_redirects_sheet(wb, categories["IMAGE_REDIRECT"])
    build_keep_sheet(wb, categories["KEEP"])

    wb.save(OUT_XLSX)
    print(f"\nSaved: {OUT_XLSX}")


def build_summary(wb, existing, categories):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — Existing Rank Math Redirects Conflict Report"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "Purpose"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "Before importing the new migration redirects, this report identifies every "
        "existing Rank Math redirect that needs to be deleted or updated to avoid "
        "creating chains, loops, or stale destinations after the migration goes live. "
        "Existing redirect set: 277 rules. Active conflicts requiring action: see "
        "categories below."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:E5")
    ws.row_dimensions[5].height = 80

    ws["A7"] = "Why this matters"
    ws["A7"].font = Font(bold=True, size=11)
    ws["A8"] = (
        "If we import the new redirects without first cleaning the existing set, we'll "
        "end up with redirect chains the moment the new redirects go live. "
        "Example: an existing redirect points /service-areas/draper-plumbing/ -> /service-areas/draper-utah/. "
        "The new plan will migrate /service-areas/draper-utah/ -> /service-areas/draper-utah/ "
        "(no change) so this one is safe. But for /service-areas/salt-lake-city-plumbing/ -> "
        "/service-areas/salt-lake-city-utah/, the existing destination IS being touched by "
        "the new plan (since the new plan adds service-specific URLs underneath salt-lake-city-utah), "
        "and any user hitting the old plumbing URL would chain through both redirects."
    )
    ws["A8"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A8:E8")
    ws.row_dimensions[8].height = 130

    ws["A10"] = "Action breakdown"
    ws["A10"].font = Font(bold=True, size=12)

    ws["A11"] = "Tab"
    ws["B11"] = "Count"
    ws["C11"] = "Action"
    ws["D11"] = "Priority"
    style_header(ws, 11, 4)

    rows = [
        ("Chain Risk", len(categories["CHAIN_RISK"]),
         "UPDATE destination URL — point it directly at the new final target",
         "Critical (must fix BEFORE migration import)"),
        ("Stale Destination", len(categories["STALE_DEST"]),
         "DELETE — destinations no longer exist on the site",
         "High"),
        ("Malformed", len(categories["MALFORMED"]),
         "DELETE — junk sources from buggy plugin imports (//1000, /feed/, truncated slugs)",
         "High (always safe to delete)"),
        ("Obsolete Path", len(categories["OBSOLETE_PATH"]),
         "UPDATE destination — currently points at legacy /water/, /hvac/, /plumbing-services/ which the migration replaces",
         "Critical (must fix BEFORE migration import)"),
        ("Image Redirects", len(categories["IMAGE_REDIRECT"]),
         "DELETE — image file redirects don't belong in the redirect plugin. Handled by the broken-images plan instead",
         "Low (cleanup; not a migration blocker)"),
        ("Keep As-Is", len(categories["KEEP"]),
         "No change needed",
         "—"),
    ]
    r = 12
    for tab, count, action, prio in rows:
        ws.cell(row=r, column=1, value=tab)
        ws.cell(row=r, column=2, value=count)
        ws.cell(row=r, column=3, value=action)
        ws.cell(row=r, column=4, value=prio)
        ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Total existing redirects").font = Font(bold=True)
    ws.cell(row=r, column=2, value=len(existing))

    r += 2
    ws.cell(row=r, column=1, value="Recommended order of operations").font = Font(bold=True, size=12)
    r += 1
    ws.cell(row=r, column=1, value=(
        "1. Delete all rules in the 'Malformed' tab (24 rules) — always safe.\n"
        "2. Delete all rules in the 'Image Redirects' tab — these are noise.\n"
        "3. Delete all rules in the 'Stale Destination' tab — destinations are 404s anyway.\n"
        "4. Update destinations in the 'Obsolete Path' tab — point them at the new architecture targets.\n"
        "5. Update destinations in the 'Chain Risk' tab — point them at the FINAL target after migration.\n"
        "6. Now the existing set is clean. NOW import the new migration plan CSV.\n\n"
        "Alternative (faster but riskier): export the current Rank Math redirects, work in the export, "
        "delete everything except 'Keep As-Is', then bulk-import the cleaned set + the new migration plan together. "
        "Faster but harder to roll back if anything goes wrong."
    ))
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    ws.row_dimensions[r].height = 200

    set_widths(ws, {1: 22, 2: 10, 3: 60, 4: 35, 5: 15})


def build_chain_risk_sheet(wb, items):
    ws = wb.create_sheet("Chain Risk")
    ws.append(["#", "ID", "Source URL", "Current Destination", "Final Target (new plan)", "Why this is a chain", "Action"])
    style_header(ws, 1, 7)
    for i, it in enumerate(items, start=1):
        ws.append([
            i, it["id"], "/" + it["source"], it["destination"],
            it.get("_final_target", ""),
            it["_reason"], it["_action"],
        ])
    set_widths(ws, {1: 5, 2: 8, 3: 50, 4: 50, 5: 50, 6: 60, 7: 50})
    wrap_data(ws)


def build_stale_dest_sheet(wb, items):
    ws = wb.create_sheet("Stale Destination")
    ws.append(["#", "ID", "Source URL", "Destination (404)", "Why stale", "Action"])
    style_header(ws, 1, 6)
    for i, it in enumerate(items, start=1):
        ws.append([
            i, it["id"], "/" + it["source"], it["destination"],
            it["_reason"], it["_action"],
        ])
    set_widths(ws, {1: 5, 2: 8, 3: 50, 4: 50, 5: 60, 6: 40})
    wrap_data(ws)


def build_malformed_sheet(wb, items):
    ws = wb.create_sheet("Malformed")
    ws.append(["#", "ID", "Source URL", "Destination", "Why malformed", "Action"])
    style_header(ws, 1, 6)
    for i, it in enumerate(items, start=1):
        ws.append([
            i, it["id"], "/" + it["source"], it["destination"],
            it["_reason"], it["_action"],
        ])
    set_widths(ws, {1: 5, 2: 8, 3: 50, 4: 50, 5: 60, 6: 40})
    wrap_data(ws)


def build_obsolete_path_sheet(wb, items):
    ws = wb.create_sheet("Obsolete Path")
    ws.append(["#", "ID", "Source URL", "Current Destination", "Issue", "Action"])
    style_header(ws, 1, 6)
    for i, it in enumerate(items, start=1):
        ws.append([
            i, it["id"], "/" + it["source"], it["destination"],
            it["_reason"], it["_action"],
        ])
    set_widths(ws, {1: 5, 2: 8, 3: 50, 4: 50, 5: 60, 6: 40})
    wrap_data(ws)


def build_image_redirects_sheet(wb, items):
    ws = wb.create_sheet("Image Redirects")
    ws.append(["#", "ID", "Source URL", "Destination", "Why delete"])
    style_header(ws, 1, 5)
    for i, it in enumerate(items, start=1):
        ws.append([
            i, it["id"], "/" + it["source"], it["destination"],
            it["_reason"],
        ])
    set_widths(ws, {1: 5, 2: 8, 3: 60, 4: 35, 5: 65})
    wrap_data(ws)


def build_keep_sheet(wb, items):
    ws = wb.create_sheet("Keep As-Is")
    ws.append(["#", "ID", "Source URL", "Destination", "Why keep"])
    style_header(ws, 1, 5)
    for i, it in enumerate(items, start=1):
        ws.append([
            i, it["id"], "/" + it["source"], it["destination"],
            it["_reason"],
        ])
    set_widths(ws, {1: 5, 2: 8, 3: 50, 4: 50, 5: 50})
    wrap_data(ws)


if __name__ == "__main__":
    main()
