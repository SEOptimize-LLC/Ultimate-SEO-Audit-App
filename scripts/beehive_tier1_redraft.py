"""Generate corrected Tier 1 titles for Beehive following user-confirmed rules.

Rules applied:
1. Brand suffix " | Beehive Plumbing" is ALWAYS appended; excluded from 65-char count
2. "Services" included on all service pages when room exists
3. Use "in [City]" not ", [City]" — never comma-comma constructions
4. Full city name + state ("Salt Lake City, Utah") preferred over abbreviations
5. Drop genuine filler ("24/7 Expert Service", "Reliable Solutions for Your Home")
6. Fix stuffing patterns ("24/7 Licensed & Insured" -> pick one attribute)
7. Maximize headroom — fill empty space with priority-ordered attributes when room

This script reads the team's source rewrites + URL paths and outputs new
titles per the rules. Run it, spot-check output, then integrate into the
main builder.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "on_page_issues.xlsx"

THRESHOLD = 65
BRAND_SUFFIX = " | Beehive Plumbing"
DEFAULT_STATE = "Utah"

# Cities Beehive serves — keep order from longest to shortest for matching
UTAH_CITIES = [
    "Salt Lake City", "Park City", "South Jordan", "West Jordan",
    "West Valley City", "North Salt Lake", "Sugar House",
    "Davis County", "Utah County", "Salt Lake County",
    "Cottonwood Heights", "Centerville", "Bountiful", "Kaysville",
    "Holladay", "Millcreek", "Bluffdale", "Midvale", "Murray",
    "Draper", "Sandy", "Orem", "Lehi", "Layton", "Tooele", "Ogden",
]
UTAH_CITIES_LOWER = [c.lower() for c in UTAH_CITIES]


@dataclass
class TitleInputs:
    url: str
    page_type: str  # "Service Page" | "Local Service Page" | "Utility Page"
    current_title: str
    team_proposed: str


def detect_city_from_url(url: str) -> str | None:
    """Extract a Utah city from URL slug. Match by checking slugified versions."""
    u = url.lower()
    # Sort cities longest-first so multi-word cities match before substrings
    for city in sorted(UTAH_CITIES, key=len, reverse=True):
        slug = city.lower().replace(" ", "-")
        if slug in u:
            return city
    return None


def detect_service_from_url(url: str) -> str | None:
    """Map URL slug fragment to a canonical service name."""
    u = url.lower()
    # Order matters — most specific first
    service_map = [
        # Most-specific local service patterns (sub-pages under
        # /water-heater-replacement-utah/...)
        ("tankless-water-heater-repair", "Tankless Water Heater Repair"),
        # Commercial-specific
        ("commercial-water-heater-installation", "Commercial Water Heater Installation"),
        ("commercial-water-heater-replacement", "Commercial Water Heater Replacement"),
        ("commercial-water-heater-repair", "Commercial Water Heater Repair"),
        ("commercial-toilet-repair", "Commercial Toilet Repair"),
        ("commercial-plumber", "Commercial Plumber"),
        # Residential-specific
        ("residential-urinal-installation-repair", "Residential Urinal Installation"),
        ("residential-plumber", "Residential Plumber"),
        # Tankless before generic water heater
        ("tankless-water-heater", "Tankless Water Heater Installation"),
        # Water heater variants — each gets its own service name
        ("water-heater-installation", "Water Heater Installation"),
        ("water-heater-replacement", "Water Heater Replacement"),
        ("water-heater-repair", "Water Heater Repair"),
        ("electric-water-heater", "Electric Water Heater"),
        ("gas-water-heater", "Gas Water Heater"),
        ("water-heaters-utah", "Water Heater"),
        # Water softener / treatment
        ("water-softener", "Water Softener"),
        ("water-main-replacement", "Water Main Replacement"),
        ("waterline-locating", "Waterline Locating & Inspection"),
        # Drain / sewer
        ("hydro-jetting-drain-cleaning", "Hydro Jetting"),
        ("ogden-sewer-line", "Sewer Line Repair"),
        ("drain-pipe-repair", "Drain Pipe Repair"),
        ("drain-cleaning", "Drain Cleaning"),
        ("sewer-line-repair", "Sewer Line Repair"),
        ("sewer-drain-services", "Sewer & Drain"),
        # Fixtures
        ("garbage-disposal", "Garbage Disposal"),
        ("flushometer-repair", "Flushometer Repair"),
        ("sink-plumbing-repair", "Sink Plumbing Repair"),
        ("sump-pumps", "Sump Pump Installation"),
        ("toilet-repair-replacement", "Toilet Repair"),
        ("low-flow-toilets", "Low-Flow Toilet"),
        ("urinal-services", "Urinal Services"),
        ("tub-shower-repair", "Tub & Shower Repair"),
        ("bidet-installation", "Bidet Installation & Repair"),
        # Pipe work
        ("pipe-inspection-camera", "Pipe Inspection Camera"),
        ("pipe-lining", "Pipe Lining"),
        ("repiping-a-house", "Repiping"),
        ("manabloc-plumbing-system", "Manabloc Plumbing System"),
        ("new-construction-plumbing", "New Construction Plumbing"),
        # General plumbing
        ("plumbing-repairs", "Plumbing Repair"),
        ("remodeling-plumber", "Remodeling Plumber"),
        ("emergency-plumber", "Emergency Plumber"),
        # HVAC
        ("hvac-tune-up", "HVAC Tune-Up"),
        ("hvac-services", "HVAC"),
        ("hydronics", "Hydronics Installation & Repair"),
        # Other
        ("reverse-osmosis", "Reverse Osmosis Systems"),
        ("financing-plumbing", "Plumbing Financing"),
        ("plumbing-coupons", "Plumbing Coupons & Specials"),
    ]
    for slug, name in service_map:
        if slug in u:
            return name
    # Default for /plumbing-<city>-ut/ etc.
    if "plumb" in u:
        return "Plumbing"
    return None


def is_service_page(page_type: str) -> bool:
    return page_type in ("Service Page", "Local Service Page")


def page_likes_24_7(service: str) -> bool:
    """Repair-on-call services where 24/7 is genuinely true.

    Per user rules: only repair / on-call / emergency services. Installation and
    replacement services should NOT use 24/7 — they use Licensed & Insured instead.
    """
    if not service:
        return False
    s = service.lower()
    # Explicitly exclude installation/replacement-only services
    if "installation" in s and "repair" not in s:
        return False
    if "replacement" in s and "repair" not in s:
        return False
    if "tune-up" in s:
        return False
    triggers = ["emergency", "drain", "sewer", "hydro jetting", "sump pump",
                "toilet repair", "garbage disposal", "plumbing repair",
                "tub & shower", "sink plumbing", "water heater repair",
                "flushometer repair", "drain pipe repair"]
    if any(t in s for t in triggers):
        return True
    # General "Plumber" / "Plumbing" pages (city-level) — repair-on-call signal
    if s in ("plumber", "plumbing", "commercial plumber", "residential plumber",
             "remodeling plumber"):
        return True
    return False


def page_likes_licensed_insured(service: str) -> bool:
    """Trust-signal attribute for installation/replacement and commercial pages.

    Per user-confirmed Q1=B: installation/replacement services append
    "- Licensed & Insured" rather than "- 24/7 Availability".
    """
    if not service:
        return False
    s = service.lower()
    # Installation, replacement, repipe — trust signal
    if any(k in s for k in ["installation", "replacement", "repiping",
                             "manabloc", "new construction", "hvac tune-up",
                             "pipe lining", "pipe inspection",
                             "waterline locating", "water main",
                             "low-flow", "urinal services",
                             "residential urinal", "bidet installation",
                             "electric water heater", "gas water heater",
                             "tankless water heater"]):
        return True
    # Hub-level service nouns ("Water Heater", "Water Softener") use trust signal
    if s in ("water heater", "water softener"):
        return True
    # Master credential
    if "master" in s:
        return True
    return False


def truncate_to_threshold(body: str, threshold: int = THRESHOLD) -> str:
    if len(body) <= threshold:
        return body
    # Try drop ", Utah" first
    alt = re.sub(r",\s*Utah\b", "", body, flags=re.IGNORECASE).strip()
    alt = re.sub(r"\s+", " ", alt)
    if len(alt) <= threshold:
        return alt
    return body  # caller decides what to do; we don't truncate-with-ellipsis


def build_service_title(
    service: str,
    city: str | None,
    state: str = DEFAULT_STATE,
    threshold: int = THRESHOLD,
    add_services_suffix: bool = True,
    can_24_7: bool = False,
    can_licensed: bool = False,
) -> str:
    """Build a service-page title body with priority-ordered headroom filling.

    Order of attempts (each shorter than the previous):
    1. [Service] Services in [City], [State] - 24/7 Availability
    2. [Service] Services in [City], [State] - Licensed & Insured
    3. [Service] Services in [City], [State]
    4. [Service] Services in [City]
    5. [Service] Services in [State]
    6. [Service] Services
    """
    # Some service names already end with "Services" — don't double up
    base_service = service
    if add_services_suffix and not re.search(r"\bServices?\b", service, flags=re.IGNORECASE):
        base = f"{base_service} Services"
    else:
        base = base_service

    # Build location qualifier
    if city and state:
        loc = f"in {city}, {state}"
    elif city:
        loc = f"in {city}"
    elif state:
        loc = f"in {state}"
    else:
        loc = ""

    # Try in priority order (longest first), keep the longest that fits
    candidates: list[str] = []
    if loc and can_24_7:
        candidates.append(f"{base} {loc} - 24/7 Availability")
    if loc and can_licensed:
        candidates.append(f"{base} {loc} - Licensed & Insured")
    if loc:
        candidates.append(f"{base} {loc}")
    # Fallback: drop state from "City, State"
    if city and state:
        candidates.append(f"{base} in {city}")
    if state and not city:
        candidates.append(f"{base} in {state}")
    candidates.append(base)

    for c in candidates:
        if len(c) <= threshold:
            return c
    # Last resort
    return truncate_to_threshold(candidates[-1], threshold)


def manual_overrides() -> dict[str, str]:
    """Hand-crafted titles for pages that don't fit the formulaic service pattern.

    Utility / brand / about / financing / coupon pages aren't service pages and
    need different language. Hand-craft these.
    """
    return {
        "https://www.beehiveplumbing.com/about-us/":
            "About Us - Utah Master Plumbers Since 1999 | Beehive Plumbing",
        "https://www.beehiveplumbing.com/get-in-touch/":
            "Contact Us - Plumbers in Salt Lake City, Utah | Beehive Plumbing",
        "https://www.beehiveplumbing.com/master-plumbers/":
            "Utah Master Plumbers - Licensed & Insured | Beehive Plumbing",
        "https://www.beehiveplumbing.com/job-application/":
            "Job Application - Join Our Utah Plumbing Team | Beehive Plumbing",
        "https://www.beehiveplumbing.com/beehive-preferred/":
            "Beehive Preferred - 10-Yr Warranty Program | Beehive Plumbing",
        "https://www.beehiveplumbing.com/premier-plans/":
            "Premier Plans - 4/7/10-Year Warranty | Beehive Plumbing",
        "https://www.beehiveplumbing.com/financing-plumbing-utah/":
            "Plumbing Financing in Salt Lake City, Utah | Beehive Plumbing",
        "https://www.beehiveplumbing.com/plumbing-coupons-specials/":
            "Plumbing Coupons & Specials in Salt Lake City, Utah | Beehive Plumbing",
        "https://www.beehiveplumbing.com/terms-and-privacy-policy/":
            "Terms of Service & Privacy Policy | Beehive Plumbing",
        "https://www.beehiveplumbing.com/remodeling/":
            "Plumbing & HVAC Remodeling Services in Utah | Beehive Plumbing",
        # Tankless: city pushes it over, drop city
        "https://www.beehiveplumbing.com/tankless-water-heaters-utah/":
            "Tankless Water Heater Installation Services in Utah | Beehive Plumbing",
        # Water-softener Utah-wide
        "https://www.beehiveplumbing.com/water-softeners-utah-hard-water/":
            "Water Softeners for Hard Water in Utah | Beehive Plumbing",
        # Q2 user-confirmed: RO uses singular form + "Installation"
        "https://www.beehiveplumbing.com/reverse-osmosis-systems-utah/":
            "Reverse Osmosis System Installation in Utah | Beehive Plumbing",
        # Q3 user-confirmed: HVAC descriptive list
        "https://www.beehiveplumbing.com/hvac-services/":
            "HVAC Services in Utah - Heating, Cooling & Air Quality | Beehive Plumbing",
        "https://www.beehiveplumbing.com/hvac-tune-up/":
            "HVAC Tune-Up Services in Utah - Licensed & Insured | Beehive Plumbing",
        "https://www.beehiveplumbing.com/hydronics-installation-and-repair/":
            "Hydronics Installation & Repair in Utah - Licensed & Insured | Beehive Plumbing",
    }


def rewrite_title(inputs: TitleInputs) -> tuple[str, str]:
    """Return (final_title_with_brand, body_only)."""
    overrides = manual_overrides()
    if inputs.url in overrides:
        final = overrides[inputs.url]
        body = final.replace(BRAND_SUFFIX, "").strip()
        return final, body

    # Detect service + city from URL
    service = detect_service_from_url(inputs.url)
    city = detect_city_from_url(inputs.url)

    # If utility page or no service detected, fall back to team's draft
    # cleaned of basic issues — this branch shouldn't be hit for the 86 since
    # they're all categorized service/local-service/utility, but guard.
    if not service:
        # Just clean the team's draft (strip filler, fix commas)
        body = inputs.team_proposed.replace(BRAND_SUFFIX, "").strip()
        body = re.sub(r"\s*[\|\-–:]\s*Beehive Plumbing(?:\s+SLC)?\s*$", "",
                      body, flags=re.IGNORECASE).strip()
        return body + BRAND_SUFFIX, body

    # Build using priority-ordered headroom filling
    body = build_service_title(
        service=service,
        city=city,
        state=DEFAULT_STATE,
        threshold=THRESHOLD,
        can_24_7=page_likes_24_7(service),
        can_licensed=page_likes_licensed_insured(service),
    )
    return body + BRAND_SUFFIX, body


def main():
    src = openpyxl.load_workbook(SRC, data_only=True)
    ws = src["Title Rewrites (Service+Local)"]
    rows = list(ws.iter_rows(values_only=True))[1:]

    print(f"{'#':>3} {'Body':>4}  Final title")
    print("=" * 110)
    for i, r in enumerate(rows, 1):
        inputs = TitleInputs(
            url=r[0], page_type=r[1] or "", current_title=r[2] or "",
            team_proposed=r[5] or "",
        )
        final, body = rewrite_title(inputs)
        flag = "" if len(body) <= THRESHOLD else " ⚠ OVER"
        short_url = inputs.url.replace("https://www.beehiveplumbing.com", "")
        print(f"{i:>3} {len(body):>4}{flag}  {final}")
        print(f"     URL: {short_url}")


if __name__ == "__main__":
    main()
