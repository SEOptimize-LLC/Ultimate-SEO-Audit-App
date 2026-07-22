"""
Comfort Solutions — Crawl Depth Reduction Plan.

Audits every indexable HTML page's crawl depth and produces a tiered action
plan to bring high-priority content within 3 clicks of the homepage.

Three diagnosis tiers:
  Tier 1 — Service hub pages too deep (revenue-driving pages buried at 5+ clicks)
  Tier 2 — Master nav hubs too deep (/services/, /service-areas/ at depth 4)
  Tier 3 — Blog posts buried (68 posts, only 7% within 3 clicks)
  Tier 4 — Pagination noindex (single Rank Math toggle, same as Beehive fix)

Inputs:
    /tmp/comfort_depth_data.json
    /tmp/comfort_indexable.json (for cluster mappings from previous content funnel work)

Output:
    Clients/Comfort/Full SEO Audit/comfort_depth_reduction_plan.xlsx
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
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
DATA_JSON = "/tmp/comfort_depth_data.json"
OUT_XLSX = os.path.join(
    ROOT, "Clients/Comfort/Full SEO Audit/comfort_depth_reduction_plan.xlsx"
)
DOMAIN = "https://www.comfortsolutionsutah.com"

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


# =============================================================================
# CATEGORIZATION
# =============================================================================

UTILITY_MARKERS = (
    "/about-us", "/contact-us", "/financing", "/financing-payment-options",
    "/comfort-solutions-membership-plan", "/cash-back-rebates", "/specials",
    "/coupons", "/testimonials", "/testimonials-2", "/reviews", "/privacy-policy",
    "/receive-free-estimate", "/free-estimate", "/post-title",
    "/brocolli-button-test", "/home-elementor", "/heating-ppc",
    "/air-conditioning-ppc", "/maintenance/", "/tips", "/homeshow",
    "/category", "/services-type",
    "/blog-fireplace-utah", "/showrooms-fireplace-utah", "/reviews-fireplace-utah",
    "/free-estimate-fireplace-utah", "/build-your-fireplace-fireplace-utah",
    "/products-fireplace-utah", "/specials-fireplace-utah",
    "/gallery-fireplace-utah", "/videos-fireplace-utah",
    "/fireplace-utah-homepage",
    # product/template pages
    "/altitude-x-series", "/starfire-52", "/ascent-36", "/ascent-multi-view",
    "/plasmafire-vent-free", "/truflame-direct-vent-luxury-fireplaces",
    "/electric-fireplaces", "/modern-gas-fireplaces", "/contemporary-fireplaces",
    "/custom-fireplaces", "/gas-log-sets", "/gas-wood-inserts", "/gas-wood-stoves",
    "/fireplace-mantels", "/heat-producing-fireplace-decorative",
    "/outdoor-heating", "/fireplaces",
)


def categorize(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    if path == "" or path == "/":
        return "homepage"
    if path.startswith("/services/") and "/page/" in path:
        return "pagination"
    if path.startswith("/services/"):
        return "service"
    if path.startswith("/service-areas/"):
        return "service-area"
    if path.startswith("/blog/page/"):
        return "pagination"
    if path.startswith("/blog/"):
        return "blog"
    if path == "/services" or path == "/services/":
        return "services-hub"
    if path == "/service-areas" or path == "/service-areas/":
        return "service-areas-hub"
    if path == "/blog" or path == "/blog/":
        return "blog-hub"
    if any(m in path for m in UTILITY_MARKERS):
        return "utility"
    return "root-blog"


# =============================================================================
# TIER BUILDERS
# =============================================================================

def build_summary(wb, pages, stats):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Comfort Solutions — Crawl Depth Reduction Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "What this fixes"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "The audit flagged median crawl depth of 5 across the site, with the "
        "goal of getting key content within 3 clicks of the homepage. This "
        "plan tackles the depth problem in 4 tiers, ordered by impact:\n\n"
        "Tier 1 — 7 plumbing service pages buried at depth 5 (revenue impact)\n"
        "Tier 2 — Master nav hubs (/services/, /service-areas/) at depth 4 "
        "(structural fix that helps all child pages)\n"
        "Tier 3 — Top 8-10 blog posts featured on the homepage (visibility)\n"
        "Tier 4 — Noindex paginated archives (single Rank Math toggle)"
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 175

    ws["A7"] = "Current state"
    ws["A7"].font = Font(bold=True, size=12)
    ws["A8"] = f"Indexable HTML pages with depth data: {stats['n']}"
    ws["A9"] = (
        f"Median depth: {stats['median']} | "
        f"Average: {stats['avg']:.2f} | "
        f"Max: {stats['max']}"
    )
    ws["A10"] = (
        f"Pages within 3 clicks: {stats['within_3']} "
        f"({stats['within_3_pct']}%)"
    )
    ws["A11"] = (
        f"Pages beyond 5 clicks (urgent): {stats['beyond_5']} "
        f"({stats['beyond_5_pct']}%)"
    )

    ws["A13"] = "Depth distribution by URL bucket"
    ws["A13"].font = Font(bold=True, size=12)
    ws["A14"] = "Bucket"
    ws["B14"] = "Pages"
    ws["C14"] = "Median Depth"
    ws["D14"] = "Within 3 Clicks"
    ws["E14"] = "Beyond 5 Clicks"
    style_header(ws, 14, 5)

    r = 15
    for bucket, info in sorted(stats["by_bucket"].items(),
                               key=lambda kv: -kv[1]["count"]):
        ws.cell(row=r, column=1, value=bucket)
        ws.cell(row=r, column=2, value=info["count"])
        ws.cell(row=r, column=3, value=info["median"])
        ws.cell(row=r, column=4,
                value=f"{info['within_3']} ({info['within_3_pct']}%)")
        ws.cell(row=r, column=5, value=info["beyond_5"])
        r += 1

    r += 2
    ws.cell(row=r, column=1, value="Tabs in this file").font = Font(
        bold=True, size=12
    )
    r += 1
    ws.cell(row=r, column=1, value=(
        "1. Summary — this sheet\n"
        "2. Tier 1 - Service Pages — 7 plumbing service pages at depth 5 "
        "and how to drop them to depth 3\n"
        "3. Tier 2 - Master Nav Hubs — /services/ and /service-areas/ depth fix\n"
        "4. Tier 3: Homepage Featured Posts — top 8-10 blog posts to feature "
        "on the homepage\n"
        "5. Tier 4 - Pagination Noindex — single Rank Math toggle\n"
        "6. All Pages — full depth dataset for reference\n"
        "7. Implementation Guide — step-by-step WordPress workflow\n"
        "8. Verification — how to confirm depth reduction after implementation"
    ))
    ws.cell(row=r, column=1).alignment = Alignment(
        wrap_text=True, vertical="top"
    )
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 175

    widths(ws, {1: 30, 2: 12, 3: 14, 4: 22, 5: 18, 6: 15})


def build_tier1_service_pages(wb, pages):
    """Plumbing service pages buried at depth 5."""
    ws = wb.create_sheet("Tier 1 - Service Pages")
    ws["A1"] = ("Tier 1 — Plumbing Service Pages At Depth 5 "
                "(highest priority — revenue impact)")
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = (
        "All 7 plumbing sub-service pages are buried at depth 5 with only "
        "3-4 internal links each. These are revenue-driving pages — drain "
        "cleaning, water heater repair, emergency plumbing, etc. Their depth "
        "issue stems from being children of /services/plumbing/ which is "
        "itself at depth 3 and only linked from a small set of pages."
    )
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:G2")
    ws.row_dimensions[2].height = 75

    ws.append([])
    ws.append([
        "#", "URL", "Current Depth", "Inlinks", "Target Depth",
        "Recommended Action", "Expected Impact",
    ])
    style_header(ws, 4, 7)

    plumbing = []
    for p in pages:
        path = urlparse(p["url"]).path.rstrip("/")
        if (path.startswith("/services/plumbing/")
                and not "/page/" in path
                and path != "/services/plumbing"):
            plumbing.append(p)
    plumbing.sort(key=lambda p: p["url"])

    for i, p in enumerate(plumbing, start=1):
        # Tailored recommendation per service
        slug = urlparse(p["url"]).path.strip("/").split("/")[-1]
        action = (
            "Add /services/plumbing/ as a top-level item in the main "
            "navigation menu (currently it appears to be only reachable via "
            "the /services/ hub or footer). After this fix, all 7 plumbing "
            "sub-service pages drop from depth 5 to depth 3 in one change."
        )
        impact = "Drops from depth 5 → depth 3 with the parent nav fix"
        ws.append([
            i, p["url"],
            int(p["depth"]) if p["depth"] else "?",
            int(p["inlinks"]) if p["inlinks"] else "?",
            3, action, impact,
        ])

    # Add the parent hub as #8
    parent = next(
        (p for p in pages
         if urlparse(p["url"]).path.rstrip("/") == "/services/plumbing"),
        None,
    )
    if parent:
        ws.append([
            len(plumbing) + 1, parent["url"],
            int(parent["depth"]) if parent["depth"] else "?",
            int(parent["inlinks"]) if parent["inlinks"] else "?",
            2,
            "PARENT HUB — Add to main navigation menu as a top-level item "
            "(or as a megamenu item under 'Services'). This is the keystone "
            "fix — adding the parent to nav drops all 7 children at once.",
            "Drops from depth 3 → depth 2; cascades to all children",
        ])

    widths(ws, {1: 5, 2: 60, 3: 14, 4: 10, 5: 14, 6: 60, 7: 35})
    ws.freeze_panes = "A5"
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_tier2_master_hubs(wb, pages):
    """Master /services/ and /service-areas/ hubs."""
    ws = wb.create_sheet("Tier 2 - Master Nav Hubs")
    ws["A1"] = "Tier 2 — Master Nav Hubs Buried Too Deep"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = (
        "The site has master 'index of all services' pages and the "
        "'index of all service areas' page. Both are at depth 4, which "
        "means anything they link to inherits depth ≥ 5. These hubs should "
        "be at depth 1 (in the main nav menu)."
    )
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:G2")
    ws.row_dimensions[2].height = 60

    ws.append([])
    ws.append([
        "#", "URL", "Current Depth", "Inlinks", "Target Depth",
        "Recommended Action", "Expected Impact",
    ])
    style_header(ws, 4, 7)

    targets = [
        f"{DOMAIN}/services/",
        f"{DOMAIN}/service-areas/",
    ]
    i = 1
    for url in targets:
        match = next(
            (p for p in pages
             if urlparse(p["url"]).path.rstrip("/")
                == urlparse(url).path.rstrip("/")),
            None,
        )
        if match:
            if "service-areas" in url:
                action = (
                    "Add 'Service Areas' as a top-level main nav item "
                    "(or under a 'Locations' nav group). Currently only "
                    "linked from a handful of pages — explains why this hub "
                    "with 6 inlinks is at depth 4 instead of depth 1."
                )
                impact = (
                    "Drops to depth 1; the 5 city pages underneath drop "
                    "from depth 3 → depth 2"
                )
            else:
                action = (
                    "Verify 'Services' is in the main nav menu and that the "
                    "menu item links directly to /services/, not to a "
                    "specific child page. With 21 inlinks at depth 4, this "
                    "hub is being linked from many pages but never from the "
                    "header nav — fix that."
                )
                impact = (
                    "Drops to depth 1; HVAC and Plumbing sub-hubs drop "
                    "from depth 3 → depth 2"
                )
            ws.append([
                i, match["url"],
                int(match["depth"]) if match["depth"] else "?",
                int(match["inlinks"]) if match["inlinks"] else "?",
                1, action, impact,
            ])
            i += 1

    # Add /services/plumbing/ — the buried sub-hub from Tier 1
    plumbing_hub = next(
        (p for p in pages
         if urlparse(p["url"]).path.rstrip("/") == "/services/plumbing"),
        None,
    )
    if plumbing_hub:
        ws.append([
            i, plumbing_hub["url"],
            int(plumbing_hub["depth"]) if plumbing_hub["depth"] else "?",
            int(plumbing_hub["inlinks"]) if plumbing_hub["inlinks"] else "?",
            2,
            "Add as a megamenu item under the main 'Services' nav item, "
            "alongside HVAC and Fireplace. See Tier 1 for the cascade impact.",
            "Drops to depth 2; all 7 plumbing children drop to depth 3",
        ])

    widths(ws, {1: 5, 2: 60, 3: 14, 4: 10, 5: 14, 6: 60, 7: 35})
    ws.freeze_panes = "A5"
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_tier3_homepage_features(wb, pages):
    """Top 8-10 blog posts to feature on the homepage."""
    ws = wb.create_sheet("Tier 3 - Homepage Features")
    ws["A1"] = "Tier 3 — Top 8-10 Blog Posts To Feature On The Homepage"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = (
        "These are the highest-value blog posts to feature on the homepage "
        "as a 'Latest Articles' or 'Resources' section. Selection criteria: "
        "high inlink count (proven internal popularity) + BOFU/MOFU funnel "
        "stage (decision-driving content) + current depth ≥ 4 (high room for "
        "improvement). Featuring these on the homepage drops them from "
        "depth 5-6 to depth 1."
    )
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:H2")
    ws.row_dimensions[2].height = 100

    ws.append([])
    ws.append([
        "#", "URL", "Title", "Current Depth", "Inlinks",
        "Selection Reason", "Suggested Anchor", "Priority",
    ])
    style_header(ws, 4, 8)

    # Score each blog post
    UTAH_CITIES_RE = re.compile(
        r"\b(salt[-\s]lake[-\s]city|park[-\s]city|sandy|bountiful|"
        r"draper|orem|ogden|west[-\s]haven|west[-\s]jordan|layton|"
        r"davis[-\s]county)\b",
        re.IGNORECASE,
    )
    BOFU_PATTERNS = [
        r"\brepair\b", r"\bemergency\b", r"\bcontractor\b",
        r"\bfix\b", r"\b(maintenance|tune\s*-?\s*up)\b",
        r"\b(warning\s+signs|signs\s+(your|of))\b",
        r"\bnot\s+working\b",
    ]
    MOFU_PATTERNS = [
        r"\b(should\s+(i|you))\b", r"\b(vs|versus)\b", r"\bbuying\b",
        r"\b(replace|replacement)\b", r"\b(upgrade|upgrading)\b",
        r"\b(consider|considering)\b", r"\b(when\s+(to|should))\b",
    ]

    candidates = []
    for p in pages:
        if categorize(p["url"]) != "root-blog":
            continue
        if not p["depth"] or p["depth"] < 4:
            continue
        slug = urlparse(p["url"]).path.strip("/")
        title = p.get("title", "")
        text = (slug + " " + title).lower().replace("-", " ")

        # Score: inlinks (most weight) + funnel stage + city mention
        score = 0
        reasons = []

        inlinks = p.get("inlinks") or 0
        if inlinks >= 20:
            score += 50
            reasons.append(f"{inlinks} inlinks (very high)")
        elif inlinks >= 10:
            score += 25
            reasons.append(f"{inlinks} inlinks (high)")
        elif inlinks >= 5:
            score += 10
            reasons.append(f"{inlinks} inlinks")

        is_bofu = any(re.search(pat, text) for pat in BOFU_PATTERNS)
        is_mofu = any(re.search(pat, text) for pat in MOFU_PATTERNS)
        if is_bofu:
            score += 15
            reasons.append("BOFU (decision)")
        elif is_mofu:
            score += 10
            reasons.append("MOFU (consideration)")

        if UTAH_CITIES_RE.search(text):
            score += 10
            reasons.append("local intent")

        if p["depth"] >= 5:
            score += 5
            reasons.append(f"deep ({int(p['depth'])} clicks)")

        candidates.append({
            **p, "_score": score,
            "_reason": ", ".join(reasons),
            "_funnel": "BOFU" if is_bofu else ("MOFU" if is_mofu else "TOFU"),
        })

    candidates.sort(key=lambda p: -p["_score"])
    top = candidates[:12]  # 12 candidates so user can pick 8-10

    for i, p in enumerate(top, start=1):
        priority = "Top tier (must-feature)" if i <= 5 else (
            "Strong (next tier)" if i <= 10 else "Optional"
        )
        anchor = p.get("title", "") or urlparse(p["url"]).path.strip("/")
        # Trim anchor to ~70 chars
        if len(anchor) > 70:
            anchor = anchor[:67] + "..."
        ws.append([
            i, p["url"], p.get("title", ""),
            int(p["depth"]) if p["depth"] else "?",
            int(p["inlinks"]) if p["inlinks"] else "?",
            p["_reason"], anchor, priority,
        ])

    widths(ws, {1: 5, 2: 55, 3: 50, 4: 14, 5: 10, 6: 38, 7: 50, 8: 22})
    ws.freeze_panes = "A5"
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_tier4_pagination(wb, pages):
    """Pagination noindex tier."""
    ws = wb.create_sheet("Tier 4 - Pagination Noindex")
    ws["A1"] = "Tier 4 — Pagination Pages (single Rank Math toggle fix)"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = (
        "Paginated archive pages (/blog/page/2/, /services/page/2/, etc.) "
        "are at depth 4-5 and have no unique content to rank. Same fix as "
        "Beehive: noindex,follow them sitewide via Rank Math. This doesn't "
        "directly reduce depth on the underlying blog posts, but it stops "
        "Google from wasting crawl budget on pagination URLs that will "
        "never rank."
    )
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:E2")
    ws.row_dimensions[2].height = 90

    ws.append([])
    ws.append(["#", "Pagination URL", "Current Depth", "Inlinks", "Action"])
    style_header(ws, 4, 5)

    pagination_pages = [
        p for p in pages
        if categorize(p["url"]) == "pagination"
    ]
    pagination_pages.sort(key=lambda p: p["url"])

    for i, p in enumerate(pagination_pages, start=1):
        ws.append([
            i, p["url"],
            int(p["depth"]) if p["depth"] else "?",
            int(p["inlinks"]) if p["inlinks"] else "?",
            "Will be auto-noindexed by the Rank Math 'Noindex Paginated "
            "Pages' toggle (Rank Math → Titles & Meta → Misc Pages)",
        ])

    ws.append([])
    ws.append([
        "", "", "", "",
        "Single config change: Rank Math SEO → Titles & Meta → Misc Pages "
        "→ 'Noindex Paginated Pages' toggle ON. ~5 minutes of work.",
    ])

    widths(ws, {1: 5, 2: 55, 3: 14, 4: 10, 5: 60})
    ws.freeze_panes = "A5"
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_all_pages(wb, pages):
    """Reference: every page with its current depth."""
    ws = wb.create_sheet("All Pages")
    ws.append(["#", "URL", "Title", "Bucket", "Depth", "Inlinks"])
    style_header(ws, 1, 6)
    pages_sorted = sorted(
        pages,
        key=lambda p: (p["depth"] is None, -(p["depth"] or 0)),
    )
    for i, p in enumerate(pages_sorted, start=1):
        ws.append([
            i, p["url"], p.get("title", ""),
            categorize(p["url"]),
            int(p["depth"]) if p["depth"] else "?",
            int(p["inlinks"]) if p["inlinks"] else "?",
        ])
    widths(ws, {1: 5, 2: 60, 3: 50, 4: 18, 5: 8, 6: 10})
    wrap(ws)


def build_implementation_guide(wb):
    ws = wb.create_sheet("Implementation Guide")
    ws.append(["Step", "Tier", "What to do", "Where", "Effort"])
    style_header(ws, 1, 5)

    steps = [
        ("1. Audit current main nav menu",
         "Tier 1 + 2",
         "Open Appearance → Menus in WordPress. Document the current menu "
         "structure. Confirm what's in the header nav vs footer vs sidebar. "
         "This is the diagnostic step before any changes.",
         "WP Admin → Appearance → Menus",
         "15 min"),

        ("2. Add /services/ as top-level nav item",
         "Tier 2",
         "If 'Services' is not already in the main nav at depth 1, add it "
         "as a top-level menu item. Link directly to /services/, not to a "
         "child service. This single change drops the master services hub "
         "from depth 4 to depth 1.",
         "WP Admin → Appearance → Menus",
         "10 min"),

        ("3. Add /services/plumbing/ as megamenu item under Services",
         "Tier 1",
         "Within the Services menu, add Plumbing as a sub-item alongside "
         "HVAC and Fireplace. This drops /services/plumbing/ to depth 2 "
         "and cascades all 7 plumbing sub-services from depth 5 → depth 3.",
         "WP Admin → Appearance → Menus (megamenu structure)",
         "20 min"),

        ("4. Add 'Service Areas' as top-level nav item",
         "Tier 2",
         "Add 'Service Areas' (or 'Locations') as a top-level menu item "
         "linked to /service-areas/. This drops the master service-areas "
         "hub from depth 4 to depth 1 and the 5 city pages from depth 3 "
         "to depth 2.",
         "WP Admin → Appearance → Menus",
         "10 min"),

        ("5. Verify menu changes are live",
         "Tier 1 + 2",
         "Visit the homepage in an incognito window. Confirm Services has "
         "a megamenu showing HVAC, Plumbing, Fireplace. Confirm Service "
         "Areas is in the nav. Click into /services/plumbing/ and one "
         "child page (e.g., drain-cleaning) to confirm they're reachable "
         "from the homepage in 2-3 clicks.",
         "Live site, incognito browser",
         "10 min"),

        ("6. Build 'Latest Articles' homepage section",
         "Tier 3",
         "Add a section near the bottom of the homepage that features the "
         "top 8-10 blog posts from Tier 3 tab. Use thumbnail + title "
         "format. Anchor text should match the blog post title. Avoid "
         "putting it in the sidebar — main column placement is more "
         "valuable for both crawl signals and user engagement.",
         "WP Admin → Pages → Homepage editor (Elementor or Gutenberg)",
         "1-2 hours including design work"),

        ("7. Toggle Pagination Noindex",
         "Tier 4",
         "Rank Math SEO → Titles & Meta → Misc Pages → 'Noindex "
         "Paginated Pages' toggle ON. Save. This noindexes all "
         "/page/N/ URLs sitewide. Same fix that worked for Beehive.",
         "WP Admin → Rank Math",
         "5 min"),

        ("8. Re-crawl and verify depth reduction",
         "Verification",
         "Run a new Screaming Frog crawl after all changes are live. Pull "
         "the depth column. Compare against the 'All Pages' tab in this "
         "plan. Target: median depth drops from 5 to 3, and all 22 "
         "service pages are within 3 clicks.",
         "Screaming Frog",
         "30 min crawl + 30 min review"),

        ("Total estimated effort", "—", "—", "—",
         "~3-4 hours total, 80% in step 6 (homepage design)"),
    ]

    for s in steps:
        ws.append(list(s))
    widths(ws, {1: 35, 2: 14, 3: 65, 4: 35, 5: 22})
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_verification(wb):
    ws = wb.create_sheet("Verification")
    ws.append([
        "Metric", "Current State", "Target After Implementation",
        "How to verify",
    ])
    style_header(ws, 1, 4)

    rows = [
        ("Median crawl depth", "5", "3 or lower",
         "Screaming Frog → Crawl Depth column → calculate median across "
         "indexable HTML pages"),
        ("Pages within 3 clicks of homepage", "~31% (~36 of 124 with depth data)",
         "≥60%",
         "Screaming Frog filter: Crawl Depth ≤ 3 AND Indexability = Indexable"),
        ("Plumbing service pages depth", "All 7 at depth 5",
         "All 7 at depth 3 or lower",
         "Filter to URLs starting with /services/plumbing/ — confirm depth ≤ 3"),
        ("/services/ master hub depth", "Depth 4",
         "Depth 1 (main nav)",
         "Filter to /services/ exactly — confirm depth = 1"),
        ("/service-areas/ master hub depth", "Depth 4",
         "Depth 1 (main nav)",
         "Same as above for /service-areas/"),
        ("Top 8-10 featured blog posts", "Depth 5-6 each",
         "Depth 1 (linked from homepage)",
         "Spot-check the 8-10 URLs from Tier 3 tab — confirm depth = 1"),
        ("Paginated /page/N/ URLs in index",
         "Currently indexable, contributing depth bloat",
         "Noindexed sitewide",
         "GSC URL Inspection on /blog/page/2/ — should show 'Excluded by "
         "noindex tag' within 2-4 weeks of toggle"),
    ]
    for r in rows:
        ws.append(list(r))
    widths(ws, {1: 30, 2: 30, 3: 30, 4: 50})
    wrap(ws)


def main() -> None:
    pages = json.load(open(DATA_JSON, encoding="utf-8"))

    # Compute stats
    depths = [p["depth"] for p in pages if p["depth"] is not None]
    sorted_d = sorted(depths)
    n = len(depths)
    median = sorted_d[n // 2]
    avg = sum(depths) / n
    max_d = int(max(depths))
    within_3 = sum(1 for d in depths if d <= 3)
    beyond_5 = sum(1 for d in depths if d > 5)

    by_bucket: dict[str, dict] = {}
    bucket_pages: dict[str, list] = defaultdict(list)
    for p in pages:
        if p["depth"] is None:
            continue
        b = categorize(p["url"])
        bucket_pages[b].append(p)
    for b, items in bucket_pages.items():
        ds = [p["depth"] for p in items]
        sd = sorted(ds)
        m = sd[len(sd) // 2]
        avg_d = sum(ds) / len(ds)
        w3 = sum(1 for d in ds if d <= 3)
        b5 = sum(1 for d in ds if d > 5)
        by_bucket[b] = {
            "count": len(ds),
            "median": m,
            "avg": avg_d,
            "within_3": w3,
            "within_3_pct": w3 * 100 // len(ds),
            "beyond_5": b5,
        }

    stats = {
        "n": n, "median": median, "avg": avg, "max": max_d,
        "within_3": within_3, "within_3_pct": within_3 * 100 // n,
        "beyond_5": beyond_5, "beyond_5_pct": beyond_5 * 100 // n,
        "by_bucket": by_bucket,
    }

    print(f"Indexable HTML pages with depth data: {n}")
    print(f"  Median depth: {median}")
    print(f"  Within 3 clicks: {within_3} ({stats['within_3_pct']}%)")
    print(f"  Beyond 5 clicks: {beyond_5}")
    print()
    print("By bucket:")
    for b, info in sorted(by_bucket.items(), key=lambda kv: -kv[1]["count"]):
        print(
            f"  {b:25s} n={info['count']:3d} median={info['median']} "
            f"within3={info['within_3']} beyond5={info['beyond_5']}"
        )

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary(wb, pages, stats)
    build_tier1_service_pages(wb, pages)
    build_tier2_master_hubs(wb, pages)
    build_tier3_homepage_features(wb, pages)
    build_tier4_pagination(wb, pages)
    build_all_pages(wb, pages)
    build_implementation_guide(wb)
    build_verification(wb)

    os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
    wb.save(OUT_XLSX)
    print(f"\nSaved: {OUT_XLSX}")


if __name__ == "__main__":
    main()
