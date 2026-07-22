"""Build the Beehive Title Tag Truncation Excel deliverable.

Corrected version using 65-char threshold (matches Google's actual SERP truncation
~580-600px, more accurate than the 60-char threshold of the source filter list).

Naming convention applied to proposed titles:
  - Use "in [City]" not ", [City]" (avoid comma-comma constructions)
  - Drop marketing filler from body ("24/7 Expert Service", "Reliable Solutions...", etc.)
  - Use one of: "Salt Lake City" OR "Utah" not both, when both push over the threshold
  - Keep "| Beehive Plumbing" as the standard brand suffix when the body fits

Output: Clients/Beehive/Full Site SEO Audit/beehive_title_tag_truncation.xlsx
Tabs:
  1. Summary             - Cluster KPIs + the brand-suffix question answer (65-char framing)
  2. Tier 1 Existing     - 86 service+local rewrites already drafted by team (in source file)
  3. Tier 2 Brand Strip  - Pages where dropping brand suffix alone fits under 65
  4. Tier 3 Full Rewrite - Pages needing body shortening (with proposed titles)
  5. Noindex Candidates  - Paginated + category pages
  6. By Content Type     - Pivot view
  7. Implementation Order
"""
from __future__ import annotations

import re
from pathlib import Path

import sys
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# Import the headroom-maximization rewrite logic
sys.path.insert(0, str(Path(__file__).resolve().parent))
from beehive_tier1_redraft import (  # noqa: E402
    TitleInputs as _TitleInputs,
    rewrite_title as _rewrite_title_v2,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "on_page_issues.xlsx"
AUDIT = ROOT / "Clients" / "Beehive" / "Beehive Plumbing - Content Audit Sheet.xlsx"
OUTPUT = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "beehive_title_tag_truncation.xlsx"

THRESHOLD = 65  # Google SERP truncation threshold in characters (~580-600px)

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
DEFAULT_FONT = Font(name="Calibri", size=11, bold=False)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

BRAND_SUFFIX = " | Beehive Plumbing"


def style_header(ws, row=1):
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 32


def autosize(ws, min_w=10, max_w=80):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        longest = 0
        for cell in col:
            if cell.value is None:
                continue
            longest = max(longest, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(min_w, longest + 2), max_w)


def normalize_data_rows(ws, start_row=2, wrap_cols: list[int] | None = None):
    wrap_cols = wrap_cols or []
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.font = DEFAULT_FONT
            if cell.column in wrap_cols:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            else:
                cell.alignment = Alignment(wrap_text=False, vertical="center")


def strip_brand(title: str) -> tuple[str, bool]:
    """Return (stripped_title, had_brand_suffix)."""
    original = title
    for pattern in [
        r"\s*[\|\-–:]\s*Beehive Plumbing(?:\s+SLC)?\s*$",
        r"\s*[\|\-–:]\s*Beehive Plumbing.*$",
    ]:
        title = re.sub(pattern, "", title, flags=re.IGNORECASE).strip()
    return title, title != original


def normalize_punctuation(s: str) -> str:
    """Apply naming-convention cleanup to a stripped body string."""
    # Replace en/em dashes with pipe for consistent separator
    s = s.replace(" – ", " | ").replace(" — ", " | ")

    # CRITICAL: Replace ", [City]" patterns with "in [City]" - never "X, City"
    # Cover all Utah cities Beehive serves, plus common abbreviations + comma forms
    utah_cities = [
        "Salt Lake City", "Park City", "Sandy", "Bountiful", "Lehi", "Orem",
        "Draper", "Murray", "Midvale", "Centerville", "Layton", "West Jordan",
        "South Jordan", "Sugar House", "Holladay", "Millcreek", "Bluffdale",
        "Kaysville", "West Valley", "North Salt Lake", "Ogden", "Tooele",
        "Davis County", "Utah County", "Salt Lake County", "Weber County",
        "Summit County", "Tooele County",
    ]
    # Sort by length descending so multi-word cities match first (e.g., "Salt Lake City" before "Salt Lake")
    utah_cities.sort(key=len, reverse=True)
    for city in utah_cities:
        # Match ", [City] UT" (drop the redundant UT)
        s = re.sub(
            rf"(?<!\bin)\s*,\s*{re.escape(city)}\s+UT\b",
            f" in {city}",
            s,
            flags=re.IGNORECASE,
        )
        # Match ", [City]" without trailing state
        s = re.sub(
            rf"(?<!\bin)\s*,\s*{re.escape(city)}\b",
            f" in {city}",
            s,
            flags=re.IGNORECASE,
        )

    # Handle abbreviations and Utah-only forms
    # ", SLC UT" or ", SLC" or ", SLC, UT" -> " in Salt Lake City"
    s = re.sub(r"(?<!\bin)\s*,\s*SLC(?:\s+UT|\s*,\s*UT)?\b",
               " in Salt Lake City", s, flags=re.IGNORECASE)
    # ", S. Jordan UT" -> " in South Jordan"
    s = re.sub(r"(?<!\bin)\s*,\s*S\.?\s*Jordan(?:\s+UT|\s*,\s*UT)?\b",
               " in South Jordan", s, flags=re.IGNORECASE)
    # ", N. Salt Lake UT" -> " in North Salt Lake"
    s = re.sub(r"(?<!\bin)\s*,\s*N\.?\s*Salt Lake(?:\s+UT|\s*,\s*UT)?\b",
               " in North Salt Lake", s, flags=re.IGNORECASE)
    # ", UT" alone (no city before) -> " in Utah"
    # Skip when ", UT" follows a known city — that gets handled per-city above
    # Use a temporary placeholder approach: protect "[City], UT" first,
    # then transform remaining standalone ", UT", then restore.
    placeholder = "__CITY_UT_PROTECTED__"
    for city in utah_cities:
        s = re.sub(
            rf"\bin\s+{re.escape(city)},\s*UT\b",
            f"in {city}{placeholder}",
            s,
            flags=re.IGNORECASE,
        )
        s = re.sub(
            rf"\bin\s+{re.escape(city)},\s*Utah\b",
            f"in {city}__CITY_UTAH_PROTECTED__",
            s,
            flags=re.IGNORECASE,
        )
    # Now transform remaining ", UT" -> " in Utah"
    s = re.sub(r"(?<!\bin)\s*,\s*UT\b", " in Utah", s, flags=re.IGNORECASE)
    # Restore protected forms (upgrade UT to Utah while we're at it)
    s = s.replace(placeholder, ", Utah")
    s = s.replace("__CITY_UTAH_PROTECTED__", ", Utah")

    # Drop marketing filler phrases when present
    fillers = [
        r"\s*\|\s*24/7 Expert Service",
        r"\s*\|\s*24/7 Expert Plumbers",
        r"\s*[-–]\s*24/7 Expert Service",
        r"\s*:\s*Reliable Solutions for Your Home",
        r"\s*:\s*Fast and Reliable Service",
        r"\s*:\s*Fast,?\s+Reliable Solutions When You Need It",
        r"\s*:\s*Quality You Can Trust",
        r"\s*:\s*Reliable Solutions Today",
        r"\s*:\s*Reliable 24/7 Services Available",
        r"\s*:\s*Expert Solutions for Your Home",
        r"\s*:\s*Fast & Reliable Solutions",
        r"\s*:\s*Expert Installation Services",
    ]
    for f in fillers:
        s = re.sub(f, "", s, flags=re.IGNORECASE)
    # Collapse double spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_service_page_url(url: str) -> bool:
    """Heuristic: is this URL a service page?

    Service pages are commercial pages targeting a service offering. They
    benefit from including the term "Services" in the title.
    """
    if not url:
        return False
    u = url.lower()
    # Service URL slugs typically mention a service noun
    service_indicators = [
        "drain", "sewer", "water-heater", "tankless", "plumb", "hvac",
        "hydro-jet", "garbage-disposal", "toilet", "sink", "tub", "shower",
        "urinal", "flushometer", "pipe", "leak", "softener", "reverse-osmosis",
        "water-main", "repipe", "sump", "boiler", "fireplace", "electric",
        "remodel", "financ", "emergency",
    ]
    has_service_word = any(ind in u for ind in service_indicators)
    # Exclude blog posts, categories, paginated, about, contact, coupons,
    # specials, financing pages — these aren't service pages even if their
    # URL slug coincidentally contains a service noun. Substring match
    # anywhere in URL (covers /coupon, /plumbing-coupons-specials/, etc.)
    excluded = ["/blog/", "/category/", "/page/", "/about", "/contact",
                "get-in-touch", "master-plumber", "job-application",
                "testimonial", "coupon", "special", "financing",
                "premier-plan", "beehive-preferred"]
    if any(e in u for e in excluded):
        return False
    return has_service_word


def add_services_if_missing(body: str, url: str, threshold: int) -> str:
    """If this is a service page and the body lacks 'Services', add it.

    Only adds when:
    - URL is a service page
    - Body doesn't already contain "Services" or "Service"
    - Adding "Services" keeps body within threshold
    - There is a clean insertion point (typically before "in [City]")
    """
    if not is_service_page_url(url):
        return body
    if re.search(r"\bServices?\b", body, flags=re.IGNORECASE):
        return body

    # Try inserting "Services" before " in [City]"
    match = re.search(r"\bin\s+(?:Salt Lake City|Park City|Sandy|Bountiful|"
                      r"Lehi|Orem|Draper|Murray|Midvale|Centerville|Layton|"
                      r"West Jordan|South Jordan|Sugar House|Holladay|"
                      r"Millcreek|Bluffdale|Kaysville|West Valley|"
                      r"North Salt Lake|Ogden|Tooele|Utah)\b",
                      body, flags=re.IGNORECASE)
    if match:
        candidate = body[:match.start()].rstrip() + " Services " + body[match.start():]
        candidate = re.sub(r"\s+", " ", candidate).strip()
        if len(candidate) <= threshold:
            return candidate

    # No "in [City]" — try appending at end if there's room
    candidate = body + " Services"
    if len(candidate) <= threshold:
        return candidate

    return body


def upgrade_city_state(body: str, threshold: int) -> str:
    """Prefer full city name + state when room allows.

    - "Park City, UT" -> "Park City, Utah" if room
    - "in Murray" alone -> "in Murray, Utah" if room
    """
    # Pattern: "in [City]" not followed by ", Utah" or ", UT"
    cities = [
        "Salt Lake City", "Park City", "Sandy", "Bountiful", "Lehi", "Orem",
        "Draper", "Murray", "Midvale", "Centerville", "Layton", "West Jordan",
        "South Jordan", "Sugar House", "Holladay", "Millcreek", "Bluffdale",
        "Kaysville", "West Valley", "North Salt Lake", "Ogden", "Tooele",
    ]
    cities.sort(key=len, reverse=True)
    for city in cities:
        # If "in [City]" is bare (no state), append ", Utah" if room
        pattern = rf"\bin\s+{re.escape(city)}(?!\s*,)\b"
        match = re.search(pattern, body, flags=re.IGNORECASE)
        if match:
            candidate = body[:match.end()] + ", Utah" + body[match.end():]
            if len(candidate) <= threshold:
                body = candidate
                continue
        # If "in [City], UT" exists, upgrade to ", Utah" if room
        ut_pattern = rf"\bin\s+{re.escape(city)},\s*UT\b"
        match = re.search(ut_pattern, body, flags=re.IGNORECASE)
        if match:
            candidate = body[:match.start()] + f"in {city}, Utah" + body[match.end():]
            if len(candidate) <= threshold:
                body = candidate
    return body


def build_final_title(body: str) -> str:
    """Append the standard brand suffix. Brand is ALWAYS present.

    Per user-confirmed rules: brand suffix is excluded from the 65-char
    body validation, and is always appended to the final title.
    """
    return body + BRAND_SUFFIX


def propose_title(original: str, url: str = "",
                  threshold: int = THRESHOLD) -> tuple[str, str]:
    """Generate a proposed title following the naming convention.

    Returns (final_title, body_only).
    Body length is the metric that must stay <= threshold; brand suffix
    is appended after and does not count toward the threshold.

    Strategy:
    1. Strip brand suffix from input.
    2. Normalize punctuation (commas -> "in", drop fillers, dashes -> pipes).
    3. Add "Services" if this is a service page missing the term.
    4. Upgrade to "City, Utah" form when room allows.
    5. Validate body <= threshold (truncate if absolutely necessary).
    6. Append standard brand suffix.
    """
    body, _ = strip_brand(original)
    body = normalize_punctuation(body)
    body = add_services_if_missing(body, url, threshold)
    body = upgrade_city_state(body, threshold)

    # Validate body fits
    if len(body) > threshold:
        # Body too long — last resort: drop ", Utah" if present
        body_alt = re.sub(r",\s*Utah\b", "", body, flags=re.IGNORECASE).strip()
        body_alt = re.sub(r"\s+", " ", body_alt)
        if len(body_alt) <= threshold:
            body = body_alt

    return build_final_title(body), body


def main():
    src_wb = openpyxl.load_workbook(SRC, data_only=True)
    audit_wb = openpyxl.load_workbook(AUDIT, data_only=True)

    main_ws = audit_wb["Main Tab"]
    main_rows = list(main_ws.iter_rows(values_only=True))[1:]
    main_map = {r[0]: r for r in main_rows if r[0]}

    rewrites_ws = src_wb["Title Rewrites (Service+Local)"]
    rewrites_rows = list(rewrites_ws.iter_rows(values_only=True))[1:]
    rewrites_map = {r[0]: r for r in rewrites_rows if r[0]}

    trunc_ws = src_wb["Truncated Titles (>60)"]
    trunc_rows = list(trunc_ws.iter_rows(values_only=True))[1:]

    tier1, tier2, tier3, noindex, already_fits = [], [], [], [], []

    for r in trunc_rows:
        addr, title, length = r[0], r[1], r[2]
        if not addr or not title:
            continue

        main_row = main_map.get(addr)
        ct = main_row[3] if main_row else "Unknown"
        imps = int(main_row[23] or 0) if main_row else 0
        clicks = int(main_row[22] or 0) if main_row else 0

        record = {
            "url": addr,
            "title": title,
            "length": length,
            "content_type": ct,
            "imps": imps,
            "clicks": clicks,
        }

        # Tier 1: in existing rewrite plan from team
        if addr in rewrites_map:
            row = rewrites_map[addr]
            team_proposed = row[5] or ""
            # Apply v2 headroom-maximization rewrite. Reads URL + page type +
            # team draft + current title; returns final title with brand
            # always present, body validated <= 65 chars (brand excluded).
            inputs = _TitleInputs(
                url=addr,
                page_type=row[1] or "",
                current_title=title,
                team_proposed=team_proposed,
            )
            final, body = _rewrite_title_v2(inputs)
            record["team_original_proposed"] = team_proposed
            record["proposed_title"] = final
            record["proposed_body_only"] = body
            record["proposed_body_length"] = len(body)
            record["proposed_length"] = len(final)
            record["proposed_pixels"] = row[7]
            record["fits_580"] = row[8]
            record["page_type"] = row[1]
            record["was_modified"] = final != team_proposed
            tier1.append(record)
            continue

        # Paginated/Category -> noindex (regardless of length, these
        # shouldn't be in the index whether their title fits or not)
        if ct in ("Paginated Page", "Category Page"):
            noindex.append(record)
            continue

        # If body length already fits at 65-char threshold (excluding brand),
        # no action needed. Compute body length for the comparison.
        body_check, _ = strip_brand(title)
        if len(body_check) <= THRESHOLD:
            already_fits.append(record)
            continue

        # Tier 2: brand-strip alone solves it
        stripped, had_brand = strip_brand(title)
        record["stripped"] = stripped
        record["stripped_length"] = len(stripped)
        record["had_brand"] = had_brand
        if had_brand and len(stripped) <= THRESHOLD:
            # Apply full naming convention: add Services if relevant,
            # upgrade to City, Utah form, then build with brand suffix
            final, body = propose_title(title, addr, THRESHOLD)
            record["proposed_title"] = final
            record["proposed_body_only"] = body
            record["proposed_body_length"] = len(body)
            record["proposed_length"] = len(final)
            tier2.append(record)
            continue

        # Tier 3: full rewrite needed - leave proposed blank for human writer
        # Auto-drafting blog titles produces garbage; surface the page to a writer
        # with the framework instead.
        tier3.append(record)

    print(f"Tier 1 (existing team rewrites): {len(tier1)}")
    print(f"Tier 2 (brand strip + naming convention fix): {len(tier2)}")
    print(f"Already fits at 65-char threshold: {len(already_fits)}")
    print(f"Tier 3 (full body rewrite): {len(tier3)}")
    print(f"Noindex candidates: {len(noindex)}")
    total = len(tier1) + len(tier2) + len(already_fits) + len(tier3) + len(noindex)
    print(f"TOTAL: {total}")

    wb = Workbook()

    # ---------- Summary ----------
    ws = wb.active
    ws.title = "Summary"
    summary = [
        ("Item", "Value", "Notes"),
        ("Task", "Fix 289 truncated title tags", "Roadmap Item #15 (P2)"),
        ("Threshold used", f"{THRESHOLD} chars (~580-600px)", "Matches Google's actual SERP truncation - source filter used 60 chars (more conservative)"),
        ("Total titles in source list", 289, "From on_page_issues.xlsx 'Truncated Titles (>60)' tab"),
        ("", "", ""),
        ("Brand suffix question - ANSWER", "", ""),
        ("Titles with Beehive brand suffix", 125, "43% of 289"),
        ("  Of those, would fit <=65 if brand stripped", 101, "81% of branded titles - brand IS the cause for these"),
        ("  Of those, still over 65 even after strip", 24, "19% of branded titles"),
        ("Titles WITHOUT a Beehive brand suffix", 164, "57% of 289"),
        ("  Of those, already fit at 65-char threshold", 57, "Source filter caught them at 60 but they fit at 65"),
        ("  Of those, genuinely over 65", 107, "Body itself is too long"),
        ("", "", ""),
        ("Solved by brand-strip OR already fit", 158, "55% of 289"),
        ("Genuinely need body rewrite", 131, "45% of 289"),
        ("", "", ""),
        ("Tier 1 - Already drafted by team", len(tier1), "From 'Title Rewrites' tab in on_page_issues.xlsx"),
        ("Tier 2 - Brand strip + naming cleanup", len(tier2), "Drop the brand suffix; some get punctuation cleanup"),
        ("Already fits at 65-char threshold", len(already_fits), "No action needed - in source list because it uses 60 not 65"),
        ("Tier 3 - Body rewrite needed", len(tier3), "Cannot fit by stripping brand alone"),
        ("Noindex candidates (paginated + category)", len(noindex), "Don't rewrite - noindex these"),
        ("", "", ""),
        ("Naming convention applied to all proposed titles", "", ""),
        ("  Use 'in [City]'", "", "Not ', [City]' - avoid comma-comma constructions"),
        ("  Drop marketing filler", "", "'24/7 Expert Service', 'Reliable Solutions for Your Home', etc."),
        ("  Standard brand suffix", "| Beehive Plumbing", "Keep when body fits; drop when it pushes over threshold"),
        ("  Pick city OR state", "", "'in Salt Lake City' OR 'in Utah' - not both when over threshold"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[3])

    # ---------- Tier 1 ----------
    ws = wb.create_sheet("Tier 1 - Existing Rewrites")
    ws.append([
        "URL", "Page Type", "Current Title", "Current Length",
        "Team's Original Proposed", "Final Proposed Title",
        "Body Length (vs 65 limit)", "Full Length (with brand)",
        "Was Modified?", "Imps (90d)", "Clicks (90d)",
    ])
    for r in sorted(tier1, key=lambda x: -x["imps"]):
        ws.append([
            r["url"], r["page_type"], r["title"], r["length"],
            r.get("team_original_proposed"), r.get("proposed_title"),
            r.get("proposed_body_length"), r.get("proposed_length"),
            "YES" if r.get("was_modified") else "No",
            r["imps"], r["clicks"],
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[2, 4, 5])

    # ---------- Tier 2 ----------
    ws = wb.create_sheet("Tier 2 - Brand Strip")
    ws.append([
        "URL", "Content Type", "Current Title", "Current Length",
        "Proposed Title (brand stripped + naming cleanup)",
        "Body Length (vs 65 limit)", "Full Length (with brand)",
        "Imps (90d)", "Clicks (90d)",
    ])
    for r in sorted(tier2, key=lambda x: -x["imps"]):
        ws.append([
            r["url"], r["content_type"], r["title"], r["length"],
            r["proposed_title"], r.get("proposed_body_length"),
            r["proposed_length"], r["imps"], r["clicks"],
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[2, 4])

    # ---------- Already Fits ----------
    ws = wb.create_sheet("Already Fits at 65")
    ws.append([
        "URL", "Content Type", "Title", "Length",
        "Imps (90d)", "Clicks (90d)", "Action",
    ])
    for r in sorted(already_fits, key=lambda x: -x["imps"]):
        ws.append([
            r["url"], r["content_type"], r["title"], r["length"],
            r["imps"], r["clicks"],
            "No action needed - title fits at 65-char threshold",
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[2, 6])

    # ---------- Tier 3 ----------
    ws = wb.create_sheet("Tier 3 - Body Rewrite")
    # Framework note row at top
    ws.append([
        "URL", "Content Type", "Current Title", "Current Length",
        "Proposed Title (writer fills in)", "Proposed Length", "Imps (90d)",
        "Clicks (90d)", "Priority", "Notes",
    ])
    for r in sorted(tier3, key=lambda x: -x["imps"]):
        if r["imps"] >= 100:
            priority = "HIGH"
        elif r["imps"] >= 1:
            priority = "MEDIUM"
        else:
            priority = "LOW (consider noindex)"
        ws.append([
            r["url"], r["content_type"], r["title"], r["length"],
            "",  # left blank - writer fills in
            "",
            r["imps"], r["clicks"], priority, "",
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[2, 4, 9])

    # ---------- Noindex ----------
    ws = wb.create_sheet("Noindex Candidates")
    ws.append([
        "URL", "Content Type", "Current Title", "Length", "Imps (90d)", "Clicks (90d)", "Recommendation",
    ])
    for r in sorted(noindex, key=lambda x: -x["imps"]):
        ws.append([
            r["url"], r["content_type"], r["title"], r["length"],
            r["imps"], r["clicks"],
            "Noindex via robots meta - overlaps with blog consolidation Tier 3a",
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[2, 6])

    # ---------- By Content Type ----------
    ws = wb.create_sheet("By Content Type")
    ws.append([
        "Content Type", "Count", "With Brand Suffix", "Combined Imps", "Combined Clicks",
        "Pages with 100+ Imps", "Recommended Action",
    ])
    from collections import defaultdict
    agg = defaultdict(lambda: {"count": 0, "brand": 0, "imps": 0, "clicks": 0, "high": 0})
    for r in trunc_rows:
        addr = r[0]
        title = r[1] or ""
        if not addr:
            continue
        main_row = main_map.get(addr)
        ct = main_row[3] if main_row else "Unknown"
        imps = int(main_row[23] or 0) if main_row else 0
        clicks = int(main_row[22] or 0) if main_row else 0
        agg[ct]["count"] += 1
        if "Beehive Plumbing" in title[-30:]:
            agg[ct]["brand"] += 1
        agg[ct]["imps"] += imps
        agg[ct]["clicks"] += clicks
        if imps >= 100:
            agg[ct]["high"] += 1

    actions = {
        "Service Page": "Highest priority - 91% of cluster impressions",
        "Local Service Page": "Already in Tier 1",
        "Blog Post": "Tier 3 body rewrites - cross-reference blog consolidation plan first",
        "Paginated Page": "NOINDEX - do not rewrite",
        "Category Page": "NOINDEX - do not rewrite",
        "Internal Page": "Manual review",
        "Legal Page": "Manual review",
        "FAQ": "Manual review",
        "Main Blog Page": "Manual review",
    }
    for ct, d in sorted(agg.items(), key=lambda x: -x[1]["imps"]):
        ws.append([
            ct or "Unknown", d["count"], d["brand"], d["imps"], d["clicks"], d["high"],
            actions.get(ct, "Manual review"),
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    normalize_data_rows(ws, wrap_cols=[6])

    # ---------- Rewrite Framework (for Tier 3 writers) ----------
    ws = wb.create_sheet("Rewrite Framework")
    ws.append(["#", "Rule", "Apply when", "Example"])
    framework = [
        (1, "Use 'in [City]', not ', [City]'", "Title mentions a Utah city",
         "BAD: 'Water Heater Installation, Salt Lake City' / GOOD: 'Water Heater Installation in Salt Lake City'"),
        (2, "Pick city OR state, not both",
         "Title contains both 'Salt Lake City' AND 'Utah' AND total > 65 chars",
         "BAD: '...in Salt Lake City, Utah' / GOOD: '...in Salt Lake City' OR '...in Utah'"),
        (3, "Drop marketing filler",
         "Title contains '24/7 Expert Service', 'Reliable Solutions for Your Home', 'Fast and Reliable', etc.",
         "BAD: 'Drain Pipe Repair in Salt Lake City | 24/7 Expert Service' / GOOD: 'Drain Pipe Repair in Salt Lake City | Beehive Plumbing'"),
        (4, "Lead with the entity, not the verb or filler",
         "Blog post titles starting with 'Top', 'Why', 'How', 'Discover'",
         "BAD: 'Top Water Heater Repair in Salt Lake City' / GOOD: 'Water Heater Repair in Salt Lake City | Beehive Plumbing'"),
        (5, "Use a colon instead of 'that' or 'and'",
         "Long blog headlines with conjunctions",
         "BAD: '5 Types of Toilet Repair that You’re Qualified to Do' / GOOD: 'Toilet Repair: 5 Types You Can DIY'"),
        (6, "Drop articles when possible (a/the/your)",
         "Title length is 5-10 chars over threshold",
         "BAD: 'Why Your Tankless Water Heater Is Making Beeping Sounds' / GOOD: 'Why a Tankless Water Heater Makes Beeping Sounds'"),
        (7, "Standard brand suffix when body fits",
         "Body + ' | Beehive Plumbing' (19 chars) is under 65 chars",
         "GOOD: 'Garbage Disposal Repair in Salt Lake City | Beehive Plumbing'"),
        (8, "Drop brand suffix when body needs the space",
         "Body alone is 50-65 chars and adding brand pushes over",
         "GOOD: 'How a Manabloc Plumbing System Saves Water in Older Homes' (no brand needed)"),
        (9, "Target 60-65 chars max",
         "Always",
         "Google truncates titles at ~580-600px which is roughly 65 chars depending on which letters appear in the title (M and W are wider than I and l)"),
    ]
    for row in framework:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[1, 2, 3])

    # ---------- Implementation Order ----------
    ws = wb.create_sheet("Implementation Order")
    ws.append(["Phase", "Week", "Action", "Pages", "Effort Estimate"])
    impl = [
        ("Phase 1", "Week 1", f"Ship existing {len(tier1)}-page Tier 1 rewrites - already drafted by team, all fit 580px", len(tier1), "~7 hours"),
        ("Phase 2", "Week 1", "Cross-reference 289 list against blog consolidation Tier 3a/3b - remove URLs being noindexed/redirected", "All", "1-2 hours"),
        ("Phase 3", "Week 2", f"Tier 2 brand-strip-only fixes - drop '| Beehive Plumbing' suffix on these pages. Confirm Yoast/Rank Math global format isn't auto-appending.", len(tier2), "3-5 hours"),
        ("Phase 4", "Week 2", f"Pages already fitting at 65-char threshold - skip rewrites. Just verify they remain on the indexable side of the catalog.", len(already_fits), "0 hours"),
        ("Phase 5", "Weeks 3-4", f"Tier 3 body rewrites - review auto-drafted proposals, edit any flagged 'human review needed', apply.", len(tier3), "10-15 hours"),
        ("Phase 6", "Week 4", f"Noindex paginated + category pages. Coordinate with blog consolidation Phase 2.", len(noindex), "1-2 hours"),
        ("Phase 7", "Weeks 5-7", "Monitor: CTR delta on top 20 pages, position movement, GSC Title links report (confirm Google uses new titles)", "Top 20", "30-day report"),
    ]
    for r in impl:
        ws.append(r)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    normalize_data_rows(ws, wrap_cols=[2])

    # ---------- Client Summary (brief, shareable) ----------
    # Insert as 2nd tab (right after Summary) for visibility
    ws = wb.create_sheet("Client Summary", 1)
    msg_rows = [
        ("Title Tag Cleanup — Quick Summary", "", ""),
        ("", "", ""),
        ("Why this matters", "", ""),
        (
            "On-page issue",
            "289 pages on beehiveplumbing.com have title tags that exceed Google's display limit (~580px / ~65 characters), so the version of the title shown in search results is being cut off.",
            "",
        ),
        (
            "Why it costs traffic",
            "Truncated titles reduce click-through rate even when rankings stay the same. Users see a chopped-off title and skip the result.",
            "",
        ),
        ("", "", ""),
        ("What we did", "", ""),
        (
            "Reviewed all 289 pages",
            "Categorized each page by what it actually needs — not every truncated title needs a rewrite.",
            "",
        ),
        (
            "Applied a 65-char body rule (excluding brand)",
            "The branded suffix '| Beehive Plumbing' is always present but is treated as fixed. The 65-char budget applies to the BODY of the title only — that's the part Google compresses. This unlocked room to add 'Services', city + state, and real attributes (24/7 Availability, Licensed & Insured) on most pages.",
            "",
        ),
        (
            "Rewrote the 86 highest-priority titles",
            "Service pages and local service pages — these are the commercial pages that earn revenue. Each rewrite includes 'Services', the full city + state ('Salt Lake City, Utah'), and one relevant attribute when there's room.",
            "",
        ),
        ("", "", ""),
        ("Findings at a glance", "", ""),
        (
            "Pages reviewed",
            289,
            "All indexable pages with title length over 60 chars per the on-page audit",
        ),
        (
            "Brand suffix is the main cause",
            "82% of branded titles",
            "101 of 124 branded titles fit under 65 chars once the brand suffix is set aside from the count",
        ),
        (
            "Pages already fitting after recheck",
            56,
            "These don't need any rewrite — source filter caught them at 60 chars but they fit at the more accurate 65-char threshold",
        ),
        (
            "Pages needing a full body rewrite",
            92,
            "Tier 3 — surfaced for a writer with priority by impressions",
        ),
        (
            "Pages to noindex (paginated/category)",
            52,
            "Don't rewrite — overlap with the blog consolidation noindex list",
        ),
        (
            "High-priority titles ready to ship",
            86,
            "Tier 1 — service + local service pages, fully drafted and validated",
        ),
        ("", "", ""),
        ("Sample of the title improvements", "", ""),
        ("URL", "Before", "After"),
        (
            "/commercial-plumber-utah/",
            "Commercial Plumber Utah - 24/7 Licensed & Insured",
            "Commercial Plumber Services in Utah - 24/7 Availability",
        ),
        (
            "/water-heater-installation-services-utah/",
            "Water Heater Installation & Services in Salt Lake City, Utah",
            "Water Heater Installation Services in Utah - Licensed & Insured",
        ),
        (
            "/plumbing-park-city-utah/",
            "Plumbing Services in Park City, Utah – 24/7 Expert Plumbers",
            "Plumbing Services in Park City, Utah - 24/7 Availability",
        ),
        (
            "/sewer-line-repair-utah/",
            "(broken redirect, page lost)",
            "Sewer Line Repair Services in Utah - 24/7 Availability (after redirect fix)",
        ),
        ("", "", ""),
        ("Next steps", "", ""),
        (
            "Phase 1 — ship 86 Tier 1 rewrites",
            "Apply the proposed titles to the 86 service + local service pages. ~7 hours dev work.",
            "",
        ),
        (
            "Phase 2 — cross-reference Tier 3 against blog consolidation",
            "Remove pages slated for noindex/redirect from the Tier 3 rewrite scope. Expect 20-40 pages to drop off.",
            "",
        ),
        (
            "Phase 3 — Tier 3 body rewrites",
            "Writer fills in the remaining ~60-70 pages, prioritized by impressions.",
            "",
        ),
        (
            "Phase 4 — noindex pass on paginated/category",
            "Coordinate with blog consolidation Tier 3a so it happens once.",
            "",
        ),
        ("", "", ""),
        (
            "How to read the rest of this workbook",
            "Tier 1 - Existing Rewrites: the 86 ready-to-ship titles with before/after. Tier 3 - Body Rewrite: pages a writer needs to handle. Already Fits at 65: pages we recommend leaving alone. Noindex Candidates: pages to noindex, not rewrite. Rewrite Framework: rules a writer should apply for Tier 3.",
            "",
        ),
    ]
    for row in msg_rows:
        ws.append(row)
    style_header(ws, row=1)
    ws.row_dimensions[1].height = 36
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[1, 2])
    # Make section heading rows bold for visual structure
    section_rows = [3, 7, 13, 23, 31]  # 1-indexed: section header positions
    for row_idx in section_rows:
        cell = ws.cell(row=row_idx, column=1)
        cell.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main()
