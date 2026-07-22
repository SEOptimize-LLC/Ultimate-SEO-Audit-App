"""
Comfort Solutions — Content Funnel & Internal Linking Plan.

Maps every blog post to its best parent service page (topical cluster),
identifies cross-link siblings, classifies funnel stage, and recommends
in-content CTAs that drive readers to the right service hub.

Two-layer architecture (per client decision):
  Layer A — Topical clusters (hub-and-spoke):
    blog post -> primary parent service hub
    service hub -> top 5-10 most relevant blog posts (related-articles section)
  Layer B — Conversion CTAs:
    each blog post gets a funnel-stage tag (TOFU/MOFU/BOFU)
    each post gets a recommended CTA + target URL based on stage + topic

City detection: when a blog post mentions a target city (Sandy, Park City,
Bountiful, Draper, West Haven), the recommended CTA target is the matching
/service-areas/<city>/ page rather than the generic service hub.

Inputs:
    /tmp/comfort_indexable.json (212 indexable HTML pages from SF crawl)

Output:
    Clients/Comfort/Full SEO Audit/comfort_content_funnel_plan.xlsx
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from collections import defaultdict
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
INDEXABLE_JSON = "/tmp/comfort_indexable.json"
OUT_XLSX = os.path.join(
    ROOT, "Clients/Comfort/Full SEO Audit/comfort_content_funnel_plan.xlsx"
)

DOMAIN = "https://www.comfortsolutionsutah.com"


# =============================================================================
# SERVICE PAGE TAXONOMY
# =============================================================================
# Each service page maps to its primary topic + secondary keywords. Used to
# match blog posts to their topical parent.

SERVICE_TAXONOMY = {
    f"{DOMAIN}/services/hvac-systems/ac-repair-service/": {
        "label": "AC Repair Service",
        "primary_keywords": ["ac repair", "air conditioner repair", "ac broken",
                             "ac not working", "air conditioning repair",
                             "ac problems", "central air repair", "ac fix"],
        "secondary": ["ac coils", "compressor", "frozen", "ice", "thermostat",
                      "central air", "ac unit", "cooling problems"],
    },
    f"{DOMAIN}/services/hvac-systems/ac-upgrade-replacement/": {
        "label": "AC Upgrade & Replacement",
        "primary_keywords": ["ac upgrade", "ac replacement", "replace air conditioner",
                             "new air conditioner", "central ac replacement",
                             "ac system upgrade", "central ac systems"],
        "secondary": ["upgrade hvac", "replace ac", "new ac unit", "buyer",
                      "homebuyer", "new central ac", "replacement"],
    },
    f"{DOMAIN}/services/hvac-systems/air-conditioning/": {
        "label": "Air Conditioning (general)",
        "primary_keywords": ["air conditioning", "air conditioner",
                             "cooling", "ac maintenance",
                             "ac system", "central air conditioning"],
        "secondary": ["summer", "cooling costs", "ac filter", "cool home",
                      "ac mistakes", "cooling guide", "ac tune-up"],
    },
    f"{DOMAIN}/services/hvac-systems/furnace-repair-service/": {
        "label": "Furnace Repair Service",
        "primary_keywords": ["furnace repair", "furnace broken", "furnace not working",
                             "furnace problems", "fix furnace", "furnace issues",
                             "furnace warming", "blow cold air"],
        "secondary": ["heater making sick", "thermostat", "ignition", "control board",
                      "furnace cold", "furnace cleaning", "tune-up"],
    },
    f"{DOMAIN}/services/hvac-systems/furnace-replacement-upgrade/": {
        "label": "Furnace Replacement & Upgrade",
        "primary_keywords": ["furnace replacement", "replace furnace",
                             "new furnace", "furnace upgrade", "upgrade heating system"],
        "secondary": ["upgrade hvac", "high efficiency", "components", "heat load"],
    },
    f"{DOMAIN}/services/hvac-systems/heating/": {
        "label": "Heating",
        "primary_keywords": ["home heating", "heating system", "central heating",
                             "heating efficiency", "winter heating",
                             "heat pump", "radiant heating", "zoned heating"],
        "secondary": ["winter", "warm", "heating bill", "fall maintenance",
                      "transition to heating", "energy bill"],
    },
    f"{DOMAIN}/services/hvac-systems/residential-ac/": {
        "label": "Residential AC",
        "primary_keywords": ["residential ac", "home ac", "ductless ac",
                             "ductless mini split", "ductless air conditioner"],
        "secondary": ["benefits of ductless", "mini split", "flexibility"],
    },
    f"{DOMAIN}/services/hvac-systems/residential-heating/": {
        "label": "Residential Heating",
        "primary_keywords": ["residential heating", "home heating", "warm home",
                             "heat the house"],
        "secondary": ["heater wont", "warm when heater"],
    },
    f"{DOMAIN}/services/hvac-systems/": {
        "label": "HVAC Systems (catch-all hub)",
        "primary_keywords": ["hvac system", "hvac maintenance", "hvac efficiency",
                             "hvac contractor", "hvac thermostat",
                             "hvac filter", "hvac tips",
                             "hvac smell", "hvac odors", "hvac control board",
                             "hvac upgrade", "hvac components",
                             "types of hvac"],
        "secondary": ["benefits of efficient hvac", "homebuyer", "interior design",
                      "remote workers", "expectant", "first time"],
    },
    f"{DOMAIN}/services/emergency-services/": {
        "label": "Emergency Services",
        "primary_keywords": ["emergency", "urgent", "broken now",
                             "no heat winter"],
        "secondary": [],
    },
    f"{DOMAIN}/services/emergency-services/air-conditioner-repair/": {
        "label": "Emergency AC Repair",
        "primary_keywords": ["emergency ac", "ac dies", "stay cool when ac dies"],
        "secondary": [],
    },
    f"{DOMAIN}/services/emergency-services/furnace-repair/": {
        "label": "Emergency Furnace Repair",
        "primary_keywords": ["emergency furnace", "no heat", "emergency heating"],
        "secondary": [],
    },
    f"{DOMAIN}/services/fireplace/": {
        "label": "Fireplace",
        "primary_keywords": ["fireplace", "fireplace insert", "gas fireplace",
                             "wood fireplace", "electric fireplace",
                             "fireplace repair", "fireplace maintenance",
                             "fireplace mantel", "outdoor fireplace",
                             "fireplace contractor", "gas log", "wood stove",
                             "fireplace efficiency", "fireplace airflow"],
        "secondary": ["smoke in your eyes", "decorative", "heat producing",
                      "winter fireplace"],
    },
    f"{DOMAIN}/services/plumbing/": {
        "label": "Plumbing (general hub)",
        "primary_keywords": ["plumbing", "plumber"],
        "secondary": [],
    },
    f"{DOMAIN}/services/plumbing/drain-cleaning/": {
        "label": "Drain Cleaning",
        "primary_keywords": ["drain cleaning", "clogged drain", "drain"],
        "secondary": [],
    },
    f"{DOMAIN}/services/plumbing/emergency-plumbing/": {
        "label": "Emergency Plumbing",
        "primary_keywords": ["emergency plumbing", "burst pipe", "leak"],
        "secondary": [],
    },
    f"{DOMAIN}/services/plumbing/plumbing-repair/": {
        "label": "Plumbing Repair",
        "primary_keywords": ["plumbing repair", "fix plumbing"],
        "secondary": [],
    },
    f"{DOMAIN}/services/plumbing/tankless-water-heaters/": {
        "label": "Tankless Water Heaters",
        "primary_keywords": ["tankless water heater"],
        "secondary": [],
    },
    f"{DOMAIN}/services/plumbing/water-heater-installation/": {
        "label": "Water Heater Installation",
        "primary_keywords": ["water heater install", "water heater installation"],
        "secondary": [],
    },
    f"{DOMAIN}/services/plumbing/water-heater-repair/": {
        "label": "Water Heater Repair",
        "primary_keywords": ["water heater repair", "water heater"],
        "secondary": [],
    },
    f"{DOMAIN}/services/plumbing/water-treatment-systems/": {
        "label": "Water Treatment Systems",
        "primary_keywords": ["water treatment", "humidifier", "dehumidifier",
                             "indoor air quality", "air quality", "allergies clean air"],
        "secondary": ["mold and air conditioning"],
    },
}

CITY_PAGES = {
    "sandy": f"{DOMAIN}/service-areas/sandy-utah/",
    "park city": f"{DOMAIN}/service-areas/park-city/",
    "park-city": f"{DOMAIN}/service-areas/park-city/",
    "bountiful": f"{DOMAIN}/service-areas/bountiful/",
    "draper": f"{DOMAIN}/service-areas/draper/",
    "west haven": f"{DOMAIN}/service-areas/west-haven-utah/",
    "west-haven": f"{DOMAIN}/service-areas/west-haven-utah/",
}


# =============================================================================
# UTILITY / SCOPE-FILTER PATTERNS
# =============================================================================

UTILITY_PREFIXES = (
    "/about-us", "/contact-us", "/financing", "/financing-payment-options",
    "/comfort-solutions-membership-plan", "/cash-back-rebates", "/specials",
    "/coupons", "/testimonials", "/testimonials-2", "/reviews", "/privacy-policy",
    "/receive-free-estimate", "/free-estimate", "/post-title", "/brocolli-button-test",
    "/home-elementor", "/heating-ppc-001", "/air-conditioning-ppc-001",
    "/maintenance", "/tips", "/homeshow", "/category", "/services-type",
    "/blog-fireplace-utah", "/showrooms-fireplace-utah", "/reviews-fireplace-utah",
    "/free-estimate-fireplace-utah", "/build-your-fireplace-fireplace-utah",
    "/products-fireplace-utah", "/specials-fireplace-utah",
    "/gallery-fireplace-utah", "/videos-fireplace-utah",
    "/fireplace-utah-homepage", "/altitude-x-series", "/starfire-52",
    "/ascent-36", "/ascent-multi-view", "/plasmafire-vent-free",
    "/truflame-direct-vent-luxury-fireplaces", "/electric-fireplaces",
    "/modern-gas-fireplaces", "/contemporary-fireplaces", "/custom-fireplaces",
    "/gas-log-sets", "/gas-wood-inserts", "/gas-wood-stoves", "/fireplace-mantels",
    "/heat-producing-fireplace-decorative", "/outdoor-heating",
    "/fireplaces", "/blog/", "/services/", "/service-areas/",
)


def is_utility(path: str) -> bool:
    """True if a URL path is a utility/template page (not a blog post)."""
    p = path.lower().rstrip("/")
    if not p:
        return True  # homepage
    if any(p.startswith(u.rstrip("/")) for u in UTILITY_PREFIXES):
        return True
    return False


# =============================================================================
# SERVICE PAGE MATCHING
# =============================================================================

def score_blog_to_service(blog_title: str, blog_slug: str,
                          taxonomy: dict) -> tuple[str, int, str]:
    """Find the best service hub for a blog post.

    Returns (best_service_url, score, matched_keywords).
    Score is roughly: 3 points per primary keyword match, 1 per secondary.
    Score >= 3 = high confidence; 1-2 = medium; 0 = no match (orphan).
    """
    text = (blog_slug + " " + blog_title).lower()
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    # Normalize hyphens to spaces for keyword matching
    text_norm = text.replace("-", " ")

    best_score = 0
    best_url = ""
    best_matched: list[str] = []

    for url, meta in taxonomy.items():
        score = 0
        matched: list[str] = []
        for kw in meta["primary_keywords"]:
            if kw in text_norm:
                score += 3
                matched.append(kw)
        for kw in meta["secondary"]:
            if kw in text_norm:
                score += 1
                matched.append(kw)
        if score > best_score:
            best_score = score
            best_url = url
            best_matched = matched

    return best_url, best_score, ", ".join(best_matched[:5])


def detect_city_in_slug(blog_slug: str, blog_title: str) -> tuple[str, str]:
    """Return (matched_city_label, city_page_url) or ('', '')."""
    text = (blog_slug + " " + blog_title).lower()
    text_norm = text.replace("-", " ")
    for city, url in CITY_PAGES.items():
        if city in text_norm:
            return city.title(), url
    return "", ""


# =============================================================================
# FUNNEL STAGE CLASSIFIER
# =============================================================================
# TOFU (Top-of-Funnel): awareness — "what is X", "why does X happen", listicles,
#   tips, general education
# MOFU (Middle-of-Funnel): consideration — comparisons, "should I", buying guides,
#   "vs" content, decision frameworks
# BOFU (Bottom-of-Funnel): decision — "near me", local intent, repair urgency,
#   "how to fix X", emergency, specific service questions

TOFU_PATTERNS = [
    r"\bwhat\s+(is|are|do|does)\b", r"\bwhy\s+(do|does|is|are)\b",
    r"\bhow\s+does\b", r"\b\d+\s+(tips|ways|reasons|signs|things|mistakes)\b",
    r"\b(myths|misconceptions|truth|truths)\b", r"\bguide\b",
    r"\bunderstanding\b", r"\bbenefits\b", r"\boverview\b",
    r"\beverything\s+you\s+need\b", r"\bbeyond\b",
]

MOFU_PATTERNS = [
    r"\b(should\s+(i|you))\b", r"\b(vs|versus)\b", r"\b(buying|buyer)\b",
    r"\bhow\s+to\s+(choose|select|pick)\b",
    r"\b(consider|considering)\b", r"\b(replace|replacement)\b",
    r"\b(when\s+(to|should))\b", r"\b(upgrade|upgrading)\b",
    r"\b(pros\s+and\s+cons)\b",
]

BOFU_PATTERNS = [
    r"\b(repair|fixing|fix\b)\b",
    r"\bemergency\b", r"\bcontractor\b",
    r"\b(salt\s+lake\s+city|park\s+city|sandy|bountiful|draper|orem|ogden|utah)\b",
    r"\bmaintenance\b", r"\b(tune\s*-?\s*up)\b",
    r"\b(warning\s+signs|signs\s+(your|of))\b",
    r"\bnot\s+working\b", r"\bproblem\b", r"\bmaking\s+you\s+sick\b",
]


def classify_funnel(blog_title: str, blog_slug: str) -> str:
    """Return 'BOFU' / 'MOFU' / 'TOFU'.

    Order of evaluation matters: BOFU patterns (local + repair) win over MOFU
    over TOFU, because a 'how to repair X in Sandy' post is decision-stage
    even though 'how to' is a TOFU marker on its own.
    """
    text = (blog_slug + " " + blog_title).lower().replace("-", " ")
    for p in BOFU_PATTERNS:
        if re.search(p, text):
            return "BOFU"
    for p in MOFU_PATTERNS:
        if re.search(p, text):
            return "MOFU"
    for p in TOFU_PATTERNS:
        if re.search(p, text):
            return "TOFU"
    return "TOFU"  # default for educational content


# =============================================================================
# CTA RECOMMENDATIONS PER FUNNEL STAGE
# =============================================================================

def cta_recommendation(funnel: str, target_url: str, target_label: str) -> str:
    """Return a recommended CTA copy block for a blog post."""
    if funnel == "BOFU":
        return (
            f"Strong, prominent CTA. Place in the first third of the post "
            f"AND at the end. Suggested copy: \"Need {target_label.lower()} "
            f"in Utah? Get a free estimate from Comfort Solutions →\" "
            f"linking to {target_url}. Use the in-content callout box style, "
            f"not just a text link."
        )
    if funnel == "MOFU":
        return (
            f"Mid-strength CTA. Place at the end of the post. Suggested copy: "
            f"\"Considering {target_label.lower()}? Talk to a local "
            f"specialist about your options →\" linking to {target_url}. "
            f"Use a button or callout below the conclusion paragraph."
        )
    return (
        f"Soft CTA. Place at the end of the post. Suggested copy: "
        f"\"Questions about your {target_label.lower()}? Comfort Solutions "
        f"can help — \" linking to {target_url}. Use a single text link "
        f"in the conclusion, not a callout box."
    )


def cluster_anchor(blog_title: str, target_label: str) -> str:
    """Return a recommended anchor text for the contextual link inside the post.

    Distinct from the CTA — this is the natural-language link that appears
    inside the body of the blog post.
    """
    return target_label.lower()


# =============================================================================
# WORKBOOK BUILDERS
# =============================================================================

NAVY = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HFONT = Font(bold=True, color="FFFFFF", size=11)


def style_header(ws, row, n):
    for c in range(1, n + 1):
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


def build_summary(wb, blog_records, by_service, by_funnel, by_confidence):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Comfort Solutions — Content Funnel & Internal Linking Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "What this plan does"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "Two-layer content architecture. Layer A (topical clusters): every "
        "blog post is mapped to one parent service hub; every service hub "
        "gets a 'related articles' section that links to its 5-10 best blog "
        "posts. Layer B (conversion CTAs): every blog post gets a funnel "
        "stage (TOFU/MOFU/BOFU) and a recommended in-content CTA driving "
        "readers to the relevant service or city page. When a post mentions "
        "one of the 5 target cities (Sandy, Park City, Bountiful, Draper, "
        "West Haven), the CTA target is the matching /service-areas/<city>/ "
        "page instead of the generic service hub."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 130

    ws["A7"] = "Scope"
    ws["A7"].font = Font(bold=True, size=12)
    ws["A8"] = f"Blog posts mapped: {len(blog_records)}"
    ws["A9"] = f"Service hubs (parent targets): {len(by_service)}"
    ws["A10"] = f"Posts with high-confidence cluster match: {by_confidence['High']}"
    ws["A11"] = f"Posts with medium-confidence match: {by_confidence['Medium']}"
    ws["A12"] = f"Posts requiring manual review: {by_confidence['Low']}"

    ws["A14"] = "Funnel stage distribution"
    ws["A14"].font = Font(bold=True, size=12)
    r = 15
    for stage in ("TOFU", "MOFU", "BOFU"):
        ws.cell(row=r, column=1, value=stage)
        ws.cell(row=r, column=2, value=by_funnel.get(stage, 0))
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="Posts per service hub").font = Font(bold=True, size=12)
    r += 1
    ws.cell(row=r, column=1, value="Service hub")
    ws.cell(row=r, column=2, value="Post count")
    style_header(ws, r, 2)
    r += 1
    for url, items in sorted(by_service.items(), key=lambda kv: -len(kv[1])):
        label = SERVICE_TAXONOMY[url]["label"] if url in SERVICE_TAXONOMY else url
        ws.cell(row=r, column=1, value=label)
        ws.cell(row=r, column=2, value=len(items))
        r += 1

    r += 2
    ws.cell(row=r, column=1, value="Tabs in this file").font = Font(bold=True, size=12)
    r += 1
    ws.cell(row=r, column=1, value=(
        "1. Summary — this sheet\n"
        "2. Blog Cluster Map — every blog post with parent service, funnel stage, "
        "anchor text, and CTA recommendation\n"
        "3. Service Hub Inbound — for each service hub, the top 5-10 blog posts "
        "to feature in a 'Related Articles' section\n"
        "4. City Routing — blog posts that mention a target city; CTA goes to the "
        "matching /service-areas/<city>/ page\n"
        "5. Manual Review — low-confidence cluster assignments needing human "
        "decision before implementation\n"
        "6. Implementation Guide — step-by-step instructions for the WordPress edits"
    ))
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 160

    widths(ws, {1: 50, 2: 14, 3: 15, 4: 15, 5: 15, 6: 15})


def build_cluster_map(wb, records):
    ws = wb.create_sheet("Blog Cluster Map")
    ws.append([
        "#", "Blog Post URL", "Title", "Funnel Stage",
        "Parent Service Hub", "Service Label",
        "Match Confidence", "Matched Keywords",
        "City Detected", "CTA Target URL", "CTA Target Label",
        "Recommended Anchor (in-content link)",
        "Recommended CTA (callout/button)",
    ])
    style_header(ws, 1, 13)
    for i, r in enumerate(records, start=1):
        ws.append([
            i, r["url"], r["title"], r["funnel"],
            r["parent_url"], r["parent_label"],
            r["confidence"], r["matched_keywords"],
            r["city"] or "", r["cta_target"], r["cta_label"],
            r["anchor"], r["cta"],
        ])
    widths(ws, {1: 5, 2: 55, 3: 50, 4: 10, 5: 50, 6: 28,
                7: 12, 8: 35, 9: 12, 10: 50, 11: 28, 12: 30, 13: 60})
    wrap(ws)


def build_service_inbound(wb, by_service):
    """For each service hub, list the blog posts that should link TO it.

    Used to populate a 'Related Articles' section on each service hub.
    """
    ws = wb.create_sheet("Service Hub Inbound")
    ws.append([
        "Service Hub", "Service Label", "# Posts in Cluster",
        "Blog Post URL", "Title", "Funnel Stage", "Suggested for Related Articles?",
    ])
    style_header(ws, 1, 7)

    for url in sorted(by_service.keys()):
        items = by_service[url]
        if not items:
            continue
        # Sort by funnel stage (BOFU first — most useful for conversion)
        items_sorted = sorted(
            items,
            key=lambda r: ({"BOFU": 0, "MOFU": 1, "TOFU": 2}.get(r["funnel"], 3),
                          -len(r["title"])),
        )
        label = SERVICE_TAXONOMY[url]["label"] if url in SERVICE_TAXONOMY else url
        for j, r in enumerate(items_sorted):
            featured = "YES (top 8)" if j < 8 else ""
            ws.append([
                url if j == 0 else "",
                label if j == 0 else "",
                len(items_sorted) if j == 0 else "",
                r["url"], r["title"], r["funnel"], featured,
            ])
    widths(ws, {1: 50, 2: 28, 3: 12, 4: 55, 5: 50, 6: 10, 7: 18})
    wrap(ws)


def build_city_routing(wb, records):
    ws = wb.create_sheet("City Routing")
    ws.append([
        "#", "Blog Post URL", "Title", "City Detected",
        "City Page (CTA target)", "Funnel Stage",
        "Why route to city page",
    ])
    style_header(ws, 1, 7)
    i = 1
    for r in records:
        if not r["city"]:
            continue
        ws.append([
            i, r["url"], r["title"], r["city"], r["cta_target"], r["funnel"],
            f"Post mentions '{r['city']}' — routing CTA to the city's "
            "service-area page captures local intent better than the "
            "generic service hub.",
        ])
        i += 1
    widths(ws, {1: 5, 2: 55, 3: 50, 4: 14, 5: 50, 6: 10, 7: 60})
    wrap(ws)


def build_manual_review(wb, records):
    ws = wb.create_sheet("Manual Review")
    ws.append([
        "#", "Blog Post URL", "Title", "Auto-suggested Parent",
        "Match Confidence", "Why review needed",
    ])
    style_header(ws, 1, 6)
    i = 1
    for r in records:
        if r["confidence"] == "Low":
            ws.append([
                i, r["url"], r["title"], r["parent_label"],
                r["confidence"],
                "Auto-mapper found weak/no keyword match. Read the post and "
                "decide: (a) which service hub is the right parent, or (b) "
                "this post is off-topic for any service hub and should be "
                "considered for pruning instead.",
            ])
            i += 1
    widths(ws, {1: 5, 2: 55, 3: 50, 4: 28, 5: 12, 6: 60})
    wrap(ws)


def build_implementation_guide(wb):
    ws = wb.create_sheet("Implementation Guide")
    ws.append(["Step", "What to do", "Where", "Effort"])
    style_header(ws, 1, 4)

    steps = [
        ("1. Decide on the related-articles widget format",
         "Pick how you'll surface 'Related Articles' on each service hub. "
         "Recommended: a section near the bottom of the page with 5-8 article "
         "thumbnails or text links. Don't use a sidebar widget — those get "
         "ignored by users and partially discounted by Google compared to "
         "in-body links.",
         "Site-wide design decision",
         "1 hour (design), 1 hour (template implementation)"),

        ("2. Implement the related-articles section on each of the 22 service hubs",
         "Use the 'Service Hub Inbound' tab to find which blog posts should "
         "appear on each service hub. Top 8 (sorted BOFU first) are the "
         "starting recommendation. Anchor text should match the blog post title.",
         "WordPress page editor or theme template",
         "~10 min per service hub × 22 = ~4 hours"),

        ("3. Add in-content links from blog posts to their parent service hub",
         "For each blog post in the 'Blog Cluster Map' tab: open the post, "
         "find the most natural place in the body to mention the service "
         "(usually a problem-statement paragraph or a 'when to call a pro' "
         "section), and add a contextual link using the recommended anchor "
         "text. ONE link per post is enough — don't stuff multiple links to "
         "the same hub.",
         "WordPress post editor",
         "~5-7 min per post × ~117 = ~12 hours"),

        ("4. Add the recommended CTA to each blog post",
         "Use the 'Recommended CTA' column to add a callout/button at the "
         "specified position. BOFU posts get a strong CTA early AND late. "
         "MOFU posts get a mid-strength CTA at the end. TOFU posts get a "
         "soft text-link CTA. The CTA target URL is the parent service hub "
         "OR the matching city service-area page (see City Routing tab).",
         "WordPress post editor",
         "~5 min per post × ~117 = ~10 hours"),

        ("5. Resolve the Manual Review tab BEFORE editing those posts",
         "Posts with 'Low' confidence need human judgment on which service "
         "hub is the right parent. Either assign one, or mark the post as "
         "'no parent' and consider it for content pruning in a separate pass.",
         "Spreadsheet review",
         "~30 sec per post for the review judgments"),

        ("6. Update internal navigation hints",
         "On each service hub, also add a single sentence near the top "
         "linking to the most authoritative blog post in its cluster. "
         "Example: 'Wondering when it's time to replace your AC instead of "
         "repairing it? Read our guide on [3 Signs Your AC Needs Replacement].' "
         "This bidirectional linking is the strongest signal pattern.",
         "WordPress page editor",
         "~5 min per service hub × 22 = ~2 hours"),

        ("7. Verify after implementation",
         "Re-crawl the site (Screaming Frog) and check that every blog post "
         "now has at least 1 outlink to a service hub, and every service hub "
         "has at least 5 inlinks from blog posts. Use the 'Inlinks' column "
         "filtered to service-page URLs.",
         "Screaming Frog",
         "30 min crawl + 30 min review"),

        ("Total estimated effort", "—", "—", "~30 hours of WordPress work spread over 1-2 weeks"),
    ]

    for s in steps:
        ws.append(list(s))

    widths(ws, {1: 50, 2: 70, 3: 30, 4: 35})
    ws.freeze_panes = "A2"
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    pages = json.load(open(INDEXABLE_JSON, encoding="utf-8"))

    blog_records = []
    by_service: dict[str, list] = defaultdict(list)
    by_funnel: dict[str, int] = defaultdict(int)
    by_confidence: dict[str, int] = defaultdict(int)

    for p in pages:
        url = p["url"]
        path = urlparse(url).path
        if is_utility(path):
            continue
        # Skip the homepage and known navigation paths
        # We've already excluded /services/, /service-areas/, /blog/ above
        slug = path.strip("/")
        if not slug:
            continue

        # Score against service taxonomy
        parent_url, score, matched = score_blog_to_service(
            p.get("title", ""), slug, SERVICE_TAXONOMY,
        )
        if score >= 5:
            confidence = "High"
        elif score >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"
            # Default to HVAC Systems (catch-all hub) when no match
            parent_url = f"{DOMAIN}/services/hvac-systems/"

        parent_label = SERVICE_TAXONOMY.get(parent_url, {}).get(
            "label", "HVAC Systems"
        )
        funnel = classify_funnel(p.get("title", ""), slug)
        city, city_url = detect_city_in_slug(slug, p.get("title", ""))

        # CTA target: city page if city detected, else service hub
        cta_target = city_url if city_url else parent_url
        cta_label = (f"local services in {city.title()}"
                     if city_url else parent_label)

        anchor = cluster_anchor(p.get("title", ""), parent_label)
        cta = cta_recommendation(funnel, cta_target, cta_label)

        rec = {
            "url": url,
            "title": p.get("title", ""),
            "funnel": funnel,
            "parent_url": parent_url,
            "parent_label": parent_label,
            "confidence": confidence,
            "matched_keywords": matched,
            "city": city,
            "cta_target": cta_target,
            "cta_label": cta_label,
            "anchor": anchor,
            "cta": cta,
        }
        blog_records.append(rec)
        by_service[parent_url].append(rec)
        by_funnel[funnel] += 1
        by_confidence[confidence] += 1

    print(f"Blog posts mapped: {len(blog_records)}")
    print(f"By confidence: {dict(by_confidence)}")
    print(f"By funnel: {dict(by_funnel)}")
    print(f"Posts with city detected: {sum(1 for r in blog_records if r['city'])}")
    print()
    print("Posts per service hub:")
    for url, items in sorted(by_service.items(), key=lambda kv: -len(kv[1])):
        label = SERVICE_TAXONOMY.get(url, {}).get("label", url)
        print(f"  {len(items):3d}  {label}")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary(wb, blog_records, by_service, by_funnel, by_confidence)
    build_cluster_map(wb, blog_records)
    build_service_inbound(wb, by_service)
    build_city_routing(wb, blog_records)
    build_manual_review(wb, blog_records)
    build_implementation_guide(wb)

    os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
    wb.save(OUT_XLSX)
    print(f"\nSaved: {OUT_XLSX}")


if __name__ == "__main__":
    main()
