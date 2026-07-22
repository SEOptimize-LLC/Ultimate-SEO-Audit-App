"""
Superior Water & Air — Full URL Architecture Migration Plan.

REPLACES: superior_gsc_redirect_corrections_plan.xlsx (which contained
unverified targets and architectural inconsistencies — see audit-workflow
Rule 12 reference case).

Target architecture (per client decision, 2026-04-25):
    /services/<service>/                       — main service hubs
    /services/<service>/<sub-service>/         — sub-services (max depth 3)
    /service-areas/<city>-utah/                — location pages (existing convention preserved)
    /blog/<slug>/                              — all blog posts migrate here

Outputs:
    Clients/Superior/Full SEO Audit/superior_url_migration_plan.xlsx
        - Architecture Map
        - 301 Redirect List
        - Pages To Build
        - Internal Link Sweep List
        - Stranded URLs
        - Cosmetic / Leave As-Is
        - Pre-Migration Checklist
        - Post-Migration Monitoring
    Clients/Superior/Full SEO Audit/superior_redirects_rankmath_import.csv
        - CSV importable into Rank Math (and most redirect plugins) with
          source URL → target URL pairs. NO targets that fail verification
          appear in this file — the developer can run the import safely.

Rules applied (.claude/rules/audit-workflow.md):
    - Rule 7: scope filter (PPC / utility pages tagged appropriately)
    - Rule 11: live verification flagged where it matters
    - Rule 12: every target URL has explicit verification status — none
      are silently published. Architecture decisions surfaced as a single
      finding before row-level recommendations. Cosmetic redirects (singular/
      plural) NOT in the active list. Cross-vertical moves explicitly called out.
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
from urllib.parse import urlparse

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
CRAWL_FILE = os.path.join(ROOT, "Clients/Superior/superior_internal_all.xlsx")
GSC_FILE = os.path.join(
    ROOT, "Clients/Superior/Superior Water & Air - GSC Audit (Nov 24th 2025).xlsx"
)
OUT_XLSX = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_url_migration_plan.xlsx",
)
OUT_CSV = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_redirects_rankmath_import.csv",
)

DOMAIN = "https://superiorwaterandair.com"

# =============================================================================
# UTAH CITY DETECTION (for location detection in slugs)
# =============================================================================

UTAH_CITIES = {
    "salt-lake-city": "Salt Lake City",
    "salt-lake": "Salt Lake City",
    "st-george": "St. George",
    "park-city": "Park City",
    "west-jordan": "West Jordan",
    "west-valley": "West Valley",
    "west-haven": "West Haven",
    "south-jordan": "South Jordan",
    "north-salt-lake": "North Salt Lake",
    "north-ogden": "North Ogden",
    "spanish-fork": "Spanish Fork",
    "cedar-city": "Cedar City",
    "cedar-hills": "Cedar Hills",
    "pleasant-grove": "Pleasant Grove",
    "pleasant-view": "Pleasant View",
    "american-fork": "American Fork",
    "eagle-mountain": "Eagle Mountain",
    "saratoga-springs": "Saratoga Springs",
    "cottonwood-heights": "Cottonwood Heights",
    "farr-west": "Farr West",
    "woods-cross": "Woods Cross",
    "sandy": "Sandy",
    "orem": "Orem",
    "provo": "Provo",
    "ogden": "Ogden",
    "lehi": "Lehi",
    "draper": "Draper",
    "murray": "Murray",
    "tooele": "Tooele",
    "layton": "Layton",
    "riverton": "Riverton",
    "herriman": "Herriman",
    "highland": "Highland",
    "salem": "Salem",
    "midvale": "Midvale",
    "kearns": "Kearns",
    "bluffdale": "Bluffdale",
    "springville": "Springville",
    "millcreek": "Millcreek",
    "taylorsville": "Taylorsville",
    "kaysville": "Kaysville",
    "alpine": "Alpine",
    "bountiful": "Bountiful",
    "centerville": "Centerville",
    "clearfield": "Clearfield",
    "clinton": "Clinton",
    "farmington": "Farmington",
    "holladay": "Holladay",
    "hooper": "Hooper",
    "hurricane": "Hurricane",
    "lindon": "Lindon",
    "magna": "Magna",
    "mapleton": "Mapleton",
    "roy": "Roy",
    "syracuse": "Syracuse",
    "washington": "Washington",
    "ogden-utah": "Ogden",
    "odgen": "Ogden",  # known typo on /water/water-heaters/water-repair-odgen-utah/
}


def detect_city_in_slug(slug: str) -> tuple[str, str]:
    """Return (city_slug, city_name) if slug contains a city, else ('', '')."""
    s = slug.lower()
    # Sort longer keys first so 'salt-lake-city' wins over 'salt-lake'
    for key in sorted(UTAH_CITIES.keys(), key=len, reverse=True):
        # Look for the city as a hyphen-bounded token (or end-of-string)
        if re.search(rf"(^|-){re.escape(key)}(-|$)", s):
            return key, UTAH_CITIES[key]
    return "", ""


# Existing /service-areas/ slug for each city — preserve whatever convention
# is already on the site so redirects land on real, indexable URLs.
# Most use <city>-utah/ but a handful use <city>-ut/ or no suffix.
EXISTING_CITY_SLUGS = {
    "alpine": "alpine-utah",
    "american-fork": "american-fork-ut",
    "bluffdale": "bluffdale-utah",
    "bountiful": "bountiful-utah",
    "cedar-city": "cedar-city-utah",
    "cedar-hills": "cedar-hills-ut",
    "centerville": "centerville-utah",
    "clearfield": "clearfield-utah",
    "clinton": "clinton-utah",
    "cottonwood-heights": "cottonwood-heights-utah",
    "draper": "draper-utah",
    "eagle-mountain": "eagle-mountain-utah",
    "farmington": "farmington-utah",
    "farr-west": "farr-west-utah",
    "herriman": "herriman-utah",
    "highland": "highland-utah",
    "holladay": "holladay-utah",
    "hooper": "hooper-utah",
    "hurricane": "hurricane-utah",
    "kaysville": "kaysville-utah",
    "kearns": "kearns-utah",
    "layton": "layton-utah",
    "lehi": "lehi-utah",
    "lindon": "lindon-utah",
    "magna": "magna-utah",
    "mapleton": "mapleton-utah",
    "midvale": "midvale-utah",
    "millcreek": "millcreek-utah",
    "murray": "murray-utah",
    "north-ogden": "north-ogden",
    "north-salt-lake": "north-salt-lake-utah",
    "ogden": "ogden-utah",
    "odgen": "ogden-utah",  # typo alias — the URL /water-repair-odgen-utah/ should redirect to the real Ogden page
    "orem": "orem-utah",
    "park-city": "park-city-utah",  # NOTE: not in /service-areas/ yet — see Pages To Build
    "pleasant-grove": "pleasant-grove-utah",
    "pleasant-view": "pleasant-view-utah",
    "provo": "provo-utah",
    "riverton": "riverton-ut",
    "roy": "roy-utah",
    "salem": "salem-utah",
    "salt-lake-city": "salt-lake-city-utah",
    "salt-lake": "salt-lake-city-utah",  # alias
    "sandy": "sandy-utah",
    "saratoga-springs": "saratoga-springs-utah",
    "south-jordan": "south-jordan-utah",
    "spanish-fork": "spanish-fork-utah",
    "springville": "springville-utah",
    "st-george": "st-george-utah",
    "syracuse": "syracuse-utah",
    "taylorsville": "taylorsville-utah",
    "tooele": "tooele-utah",
    "washington": "washington-utah",
    "west-haven": "west-haven-utah",
    "west-jordan": "west-jordan-utah",
    "west-valley": "west-valley-utah",
    "woods-cross": "woods-cross-utah",
}


def city_url_segment(city_key: str) -> str:
    """Return the existing /service-areas/<segment>/ slug for a city.

    Falls back to '<city>-utah' if the city isn't in the lookup (means it's
    detected in a source slug but doesn't have an existing service-area page,
    in which case we'll standardize on -utah for new ones).
    """
    return EXISTING_CITY_SLUGS.get(city_key, f"{city_key}-utah")


# Canonical service slug for each detected service phrase. The keys are
# raw substrings/patterns as they appear in source URLs; the value is the
# canonical service slug under /service-areas/<city>/<service>/ and (for
# generic hubs) under /services/<vertical>/<service>/.
#
# These slugs match the existing /hvac/, /water/, /plumbing-services/
# slugs where possible, normalized for consistency. Per client decision:
#   - air-conditioner-* (long form), not ac-*
#   - heating-repair = furnace-repair (consolidate on furnace-repair)
SERVICE_NORMALIZATION = [
    # (regex on source slug, canonical service slug, service vertical)
    # HVAC
    (r"furnace-repair-services?", "furnace-repair", "hvac"),
    (r"furnace-repair", "furnace-repair", "hvac"),
    (r"furnace-installation", "furnace-installation", "hvac"),
    (r"furnace-maintenance", "furnace-maintenance", "hvac"),
    (r"heating-repair", "furnace-repair", "hvac"),
    (r"hvac-services?", "hvac", "hvac"),
    (r"air-conditioner-installation", "air-conditioner-installation", "hvac"),
    (r"air-conditioner-maintenance", "air-conditioner-maintenance", "hvac"),
    (r"air-conditioner-repair", "air-conditioner-repair", "hvac"),
    (r"ac-repair", "air-conditioner-repair", "hvac"),
    (r"air-purification", "air-purification", "hvac"),
    (r"home-generators?", "home-generators", "hvac"),
    # Water heaters (under plumbing per client decision)
    (r"tankless-water-heater-installation", "tankless-water-heater-installation", "plumbing/water-heaters"),
    (r"tankless-water-heater", "tankless-water-heater", "plumbing/water-heaters"),
    (r"water-heater-replacement", "water-heater-replacement", "plumbing/water-heaters"),
    (r"water-heater-installation", "water-heater-installation", "plumbing/water-heaters"),
    (r"water-heater-repair", "water-heater-repair", "plumbing/water-heaters"),
    (r"water-repair", "water-heater-repair", "plumbing/water-heaters"),  # 'water-repair-odgen-utah' typo
    (r"water-softener-installation", "water-softener-installation", "plumbing/water-heaters"),
    (r"water-softener-maintenance", "water-softener-maintenance", "plumbing/water-heaters"),
    (r"water-softener-repair", "water-softener-repair", "plumbing/water-heaters"),
    # Water treatment
    (r"reverse-osmosis-water-filter-system", "reverse-osmosis", "water-treatment"),
    (r"reverse-osmosis", "reverse-osmosis", "water-treatment"),
    (r"water-filtration-system", "water-filtration", "water-treatment"),
    (r"water-filtration", "water-filtration", "water-treatment"),
    (r"office-drinking-water", "office-drinking-water", "water-treatment"),
    (r"commercial-ice-maker", "commercial-ice-maker", "water-treatment"),
    # Plumbing
    (r"bathroom-plumbing", "bathroom-plumbing", "plumbing"),
    (r"kitchen-plumbing", "kitchen-plumbing", "plumbing"),
    (r"drain-cleaning", "drain-cleaning", "plumbing"),
    (r"sewer-and-drain", "sewer-and-drain", "plumbing"),
    (r"service-and-repair", "service-and-repair", "plumbing"),
    (r"emergency-plumbing", "emergency-plumbing", "plumbing"),
    (r"plumbing-repair", "plumbing-repair", "plumbing"),
    (r"plumbing", "plumbing", "plumbing"),  # bare 'plumbing' fallback last
]


def normalize_service_slug(raw: str) -> tuple[str, str]:
    """Given a raw URL slug fragment, return (canonical_slug, vertical).

    Searches SERVICE_NORMALIZATION in order. First match wins. Returns
    ('', '') if no service pattern matches.
    """
    for pattern, slug, vertical in SERVICE_NORMALIZATION:
        if re.search(pattern, raw, re.IGNORECASE):
            return slug, vertical
    return "", ""


def extract_service_from_city_slug(slug: str, city_key: str) -> str:
    """Strip the city portion from a slug and return what's left.

    e.g. 'furnace-repair-services-orem-utah' with city='orem'
        → 'furnace-repair-services'
        (then normalize_service_slug returns 'furnace-repair')
    """
    s = slug.lower()
    # Remove the city + any -utah/-ut suffix attached
    patterns = [
        rf"-?in-{re.escape(city_key)}(-utah|-ut)?",
        rf"-?{re.escape(city_key)}(-utah|-ut)?",
    ]
    for p in patterns:
        s = re.sub(p, "", s)
    s = s.strip("-")
    return s


# =============================================================================
# UTILITY / SCOPE-FILTER PATTERNS
# =============================================================================

UTILITY_SLUGS = {
    "thank-you", "thanks", "application-form", "test-lead-form",
    "404-error", "page-not-found", "privacy-policy", "terms-of-use",
    "terms-of-service", "cookie-policy", "disclaimer", "login",
    "wp-login", "wp-admin", "manuals",
}
PPC_PATTERN = re.compile(r"-ppc-\d+$|-ppc$")


def is_utility(slug: str) -> bool:
    s = slug.lower().strip("/")
    if s in UTILITY_SLUGS:
        return True
    if PPC_PATTERN.search(s):
        return True
    if s.startswith("page/") or s.endswith("/page/"):
        return True
    return False


# =============================================================================
# URL CLASSIFICATION & TARGET MAPPING
# =============================================================================

class Mapping:
    """Container for one URL's migration decision."""
    def __init__(self, source_url: str):
        self.source_url = source_url
        self.source_path = urlparse(source_url).path
        self.target_url: str = ""
        self.category: str = ""
        self.action: str = ""
        self.target_status: str = ""  # 'verified live' / 'TO BUILD' / 'leave as-is' etc.
        self.priority: str = ""
        self.notes: str = ""
        self.cross_vertical: bool = False
        self.cosmetic: bool = False


# Slug-rewrite rules that handle existing English/URL inconsistencies.
# Each rule maps the OLD service-area-style slug to a CLEAN service slug
# under the new architecture.
SERVICE_SLUG_REWRITES = {
    # HVAC
    "air-conditioner-installation": "air-conditioning/installation",
    "air-conditioner-maintenance": "air-conditioning/maintenance",
    "air-conditioner-repair": "air-conditioning/repair",
    "air-conditioners": "air-conditioning",
    "air-purification": "air-purification",
    "ductless-ac": "air-conditioning/ductless",
    "furnace-installation": "furnace/installation",
    "furnace-maintenance": "furnace/maintenance",
    "furnace-repair": "furnace/repair",
    "furnaces": "furnace",
    "home-generators": "home-generators",
    # Water heaters
    "tankless-water-heater": "water-heaters/tankless",
    "water-heater-installation": "water-heaters/installation",
    "water-heater-repairs": "water-heaters/repair",
    # Water treatment
    "water-treatment": "water-treatment",
    "commercial-ice-maker": "water-treatment/commercial-ice-maker",
    "water-heaters": "water-heaters",
    # Plumbing-services
    "bathroom-plumbing": "bathroom-plumbing",
    "drain-cleaning": "drain-cleaning",
    "kitchen-plumbing": "kitchen-plumbing",
    "service-and-repair": "service-and-repair",
    "sewer-and-drain": "sewer-and-drain",
    # Misc water (top-level under /water/)
    "office-drinking-water": "water-treatment/office-drinking-water",
}


def map_hvac(source_path: str) -> Mapping | None:
    """Map /hvac/<x>/ paths to /services/hvac/ or /service-areas/<city>/<service>/."""
    m = re.match(r"^/hvac/([^/]+)/?$", source_path)
    if not m:
        return None

    slug = m.group(1)
    # City-bearing HVAC URL → city-service page
    city_key, city_name = detect_city_in_slug(slug)
    if city_key:
        # Extract the service portion and normalize it
        service_raw = extract_service_from_city_slug(slug, city_key)
        canonical_service, _vertical = normalize_service_slug(service_raw)
        if not canonical_service:
            # Couldn't normalize — fall back to city umbrella with manual review note
            target = f"{DOMAIN}/service-areas/{city_url_segment(city_key)}/"
            result = Mapping(source_url=f"{DOMAIN}{source_path}")
            result.target_url = target
            result.category = "HVAC location page → REVIEW (service slug unrecognized)"
            result.action = "Review manually: could not auto-detect specific service from slug"
            result.target_status = "REVIEW"
            result.priority = "Medium"
            result.notes = (
                f"Source slug '{slug}' contains city '{city_name}' but the service "
                f"portion '{service_raw}' didn't match any known service. Manual review needed."
            )
            return result

        target = f"{DOMAIN}/service-areas/{city_url_segment(city_key)}/{canonical_service}/"
        result = Mapping(source_url=f"{DOMAIN}{source_path}")
        result.target_url = target
        result.category = "HVAC location service → /service-areas/<city>/<service>/"
        result.action = "Build city-service page; 301 source → target"
        result.target_status = "TO BUILD: city-service page does not exist yet"
        result.priority = "High"
        result.cross_vertical = True
        result.notes = (
            f"Local service URL: '{canonical_service}' service in {city_name}. "
            f"Per the new architecture, location-bound service URLs live at "
            f"/service-areas/<city>/<service>/. The existing source page's content "
            f"should be moved into the new city-service page during migration."
        )
        return result

    # Standard (non-location) HVAC service URL — goes to /services/hvac/
    canonical_service, vertical = normalize_service_slug(slug)
    if canonical_service and vertical == "hvac":
        target = f"{DOMAIN}/services/hvac/{canonical_service}/"
    else:
        # Unrecognized — preserve as fallback under /services/hvac/<slug>/
        target = f"{DOMAIN}/services/hvac/{slug}/"
        canonical_service = slug

    # Detect cosmetic-only redirects (slug doesn't change semantically)
    source_slug_normalized = slug.rstrip("s")  # crude singular form
    cosmetic = (canonical_service.rstrip("s") == source_slug_normalized
                and target.rstrip("/") == f"{DOMAIN}/services/hvac/{canonical_service}".rstrip("/"))

    result = Mapping(source_url=f"{DOMAIN}{source_path}")
    result.target_url = target
    result.category = "HVAC generic hub → /services/hvac/"
    result.action = "Build new page at target URL; 301 source → target"
    result.target_status = "TO BUILD: /services/hvac/ structure does not exist yet"
    result.priority = "High"
    result.cosmetic = cosmetic
    return result


def _city_service_target(city_key: str, source_path: str, slug_part: str,
                          fallback_vertical: str) -> Mapping:
    """Build a city-service mapping result.

    Used by both /hvac/, /water/, and stranded-root URL handlers when the
    source path contains a city + a recognizable service.
    """
    canonical_service, vertical = normalize_service_slug(slug_part)
    city_seg = city_url_segment(city_key)
    city_name = UTAH_CITIES.get(city_key, city_key.replace("-", " ").title())

    result = Mapping(source_url=f"{DOMAIN}{source_path}")
    if canonical_service:
        result.target_url = f"{DOMAIN}/service-areas/{city_seg}/{canonical_service}/"
        result.category = f"{fallback_vertical.capitalize()} location service → /service-areas/<city>/<service>/"
        result.action = "Build city-service page; 301 source → target"
        result.target_status = "TO BUILD: city-service page does not exist yet"
        result.priority = "High"
        result.cross_vertical = True
        result.notes = (
            f"Local service URL: '{canonical_service}' in {city_name}. "
            f"Per the new architecture, location-bound service URLs live at "
            f"/service-areas/<city>/<service>/. The source page's content should "
            f"be moved into the new city-service page during migration."
        )
    else:
        result.target_url = f"{DOMAIN}/service-areas/{city_seg}/"
        result.category = f"{fallback_vertical.capitalize()} location → REVIEW (service slug unrecognized)"
        result.action = "Review manually: could not auto-detect specific service"
        result.target_status = "REVIEW"
        result.priority = "Medium"
        result.notes = (
            f"Source contains city '{city_name}' but the service portion "
            f"'{slug_part}' didn't match any known service. Defaulting target to "
            f"city umbrella; please confirm the correct service slug manually."
        )
    return result


def map_water(source_path: str) -> Mapping | None:
    """Map /water/<x>/ paths to /services/plumbing/, /services/water-treatment/,
    or /service-areas/<city>/<service>/.

    Per client decision: water heaters live under plumbing.
    """
    m = re.match(r"^/water/(.+)$", source_path)
    if not m:
        return None
    rest = m.group(1).rstrip("/")

    # /water/water-heaters/ — bare hub
    if rest == "water-heaters":
        result = Mapping(source_url=f"{DOMAIN}{source_path}")
        result.target_url = f"{DOMAIN}/services/plumbing/water-heaters/"
        result.category = "Water Heaters hub → /services/plumbing/water-heaters/"
        result.action = "Build new hub page; 301 source → target"
        result.target_status = "TO BUILD: /services/plumbing/water-heaters/ does not exist yet"
        result.priority = "High"
        result.cross_vertical = True
        result.notes = (
            "CROSS-VERTICAL MOVE: from /water/ to /services/plumbing/ per the "
            "client's decision (2026-04-25) to follow industry convention "
            "(water heaters belong under plumbing)."
        )
        return result

    # /water/water-heaters/<sub>/
    if rest.startswith("water-heaters/"):
        sub = rest[len("water-heaters/"):]
        # City-bearing → city-service page
        city_key, _ = detect_city_in_slug(sub)
        if city_key:
            slug_part = extract_service_from_city_slug(sub, city_key)
            return _city_service_target(city_key, source_path, slug_part, "water-heaters")
        # Generic sub-service under water-heaters
        canonical_service, _vertical = normalize_service_slug(sub)
        if not canonical_service:
            canonical_service = sub
        result = Mapping(source_url=f"{DOMAIN}{source_path}")
        result.target_url = f"{DOMAIN}/services/plumbing/water-heaters/{canonical_service}/"
        result.category = "Water Heater sub-service → /services/plumbing/water-heaters/"
        result.action = "Build new page; 301 source → target"
        result.target_status = "TO BUILD: /services/plumbing/water-heaters/ structure does not exist yet"
        result.priority = "High"
        result.cross_vertical = True
        result.notes = (
            "CROSS-VERTICAL MOVE: from /water/water-heaters/ to "
            "/services/plumbing/water-heaters/ per industry convention."
        )
        return result

    # /water/water-treatment/* → /services/water-treatment/*
    if rest == "water-treatment" or rest.startswith("water-treatment/"):
        sub = rest[len("water-treatment"):].lstrip("/")
        # City-bearing under water-treatment → city-service page
        city_key, _ = detect_city_in_slug(sub) if sub else ("", "")
        if city_key:
            slug_part = extract_service_from_city_slug(sub, city_key)
            return _city_service_target(city_key, source_path, slug_part, "water-treatment")
        # Generic water-treatment service or hub
        canonical_service, _vertical = normalize_service_slug(sub) if sub else ("", "")
        if not sub:
            target = f"{DOMAIN}/services/water-treatment/"
        elif canonical_service:
            target = f"{DOMAIN}/services/water-treatment/{canonical_service}/"
        else:
            target = f"{DOMAIN}/services/water-treatment/{sub}/"
        result = Mapping(source_url=f"{DOMAIN}{source_path}")
        result.target_url = target
        result.category = "Water Treatment → /services/water-treatment/"
        result.action = "Build new page; 301 source → target"
        result.target_status = "TO BUILD: /services/water-treatment/ does not exist yet"
        result.priority = "High"
        return result

    # /water/<other>/ — top-level, may contain city
    city_key, _ = detect_city_in_slug(rest)
    if city_key:
        slug_part = extract_service_from_city_slug(rest, city_key)
        return _city_service_target(city_key, source_path, slug_part, "water")

    # /water/office-drinking-water/
    canonical_service, vertical = normalize_service_slug(rest)
    if canonical_service:
        if vertical == "water-treatment":
            target = f"{DOMAIN}/services/water-treatment/{canonical_service}/"
            cat = "Water Treatment service → /services/water-treatment/"
        elif vertical.startswith("plumbing"):
            target = f"{DOMAIN}/services/{vertical}/{canonical_service}/"
            cat = f"Water service → /services/{vertical}/"
        else:
            target = f"{DOMAIN}/services/water-treatment/{canonical_service}/"
            cat = "Water service → /services/water-treatment/ (fallback)"
        result = Mapping(source_url=f"{DOMAIN}{source_path}")
        result.target_url = target
        result.category = cat
        result.action = "Build new page; 301 source → target"
        result.target_status = "TO BUILD: /services/ structure does not exist yet"
        result.priority = "High"
        return result

    # Final catch-all — manual review
    result = Mapping(source_url=f"{DOMAIN}{source_path}")
    result.target_url = f"{DOMAIN}/services/water-treatment/{rest}/"
    result.category = "Other /water/ → REVIEW"
    result.action = "Review manually — auto-mapping confidence low"
    result.target_status = "REVIEW: auto-mapping confidence low"
    result.priority = "Medium"
    return result


def map_plumbing_services(source_path: str) -> Mapping | None:
    """Map /plumbing-services/<x>/ paths to /services/plumbing/<x>/."""
    m = re.match(r"^/plumbing-services/([^/]+)/?$", source_path)
    if not m:
        return None
    slug = m.group(1)
    new_slug = SERVICE_SLUG_REWRITES.get(slug, slug)
    target = f"{DOMAIN}/services/plumbing/{new_slug}/"
    result = Mapping(source_url=f"{DOMAIN}{source_path}")
    result.target_url = target
    result.category = "Plumbing service → /services/plumbing/"
    result.action = "Create new page at target URL; 301 source → target"
    result.target_status = "TO BUILD: /services/plumbing/ does not exist yet"
    result.priority = "High"
    return result


def map_emergency_services(source_path: str) -> Mapping | None:
    """Map /emergency-services/<x>/ to /services/emergency/<x>/."""
    m = re.match(r"^/emergency-services(/.*)?$", source_path)
    if not m:
        return None
    rest = (m.group(1) or "/").strip("/")
    target = f"{DOMAIN}/services/emergency/" + (f"{rest}/" if rest else "")
    result = Mapping(source_url=f"{DOMAIN}{source_path}")
    result.target_url = target
    result.category = "Emergency services → /services/emergency/"
    result.action = "Create new page; 301 source → target"
    result.target_status = "TO BUILD: /services/emergency/ does not exist yet"
    result.priority = "High"
    return result


def map_root_level(source_path: str) -> Mapping:
    """Map root-level URLs: blog posts, utility pages, stranded location pages."""
    slug = source_path.strip("/")
    result = Mapping(source_url=f"{DOMAIN}{source_path}")

    # Empty path = homepage — never migrate
    if not slug:
        result.category = "Homepage"
        result.action = "Leave as-is"
        result.target_url = f"{DOMAIN}/"
        result.target_status = "verified live (homepage)"
        result.priority = "—"
        result.cosmetic = True
        return result

    # Utility pages — leave URL alone, no migration
    if is_utility(slug):
        result.category = "Utility / scope-filter"
        result.action = "Leave as-is (no SEO value, do not migrate)"
        result.target_url = result.source_url
        result.target_status = "leave as-is"
        result.priority = "—"
        result.notes = (
            "Per scope-filter rule, this URL has no organic-search value. "
            "Don't include in migration. Recommend noindex if not already."
        )
        result.cosmetic = True
        return result

    # Stranded location-specific pages — migrate to /service-areas/<city>/<service>/
    # but ONLY if the non-city portion clearly maps to a service. Otherwise it's
    # editorial content (e.g. 'sandy-city-water-contamination') that goes to /blog/.
    city_key, city_name = detect_city_in_slug(slug)
    if city_key and len(slug.split("-")) <= 6:
        slug_part = extract_service_from_city_slug(slug, city_key)
        canonical_service, _vertical = normalize_service_slug(slug_part)
        city_seg = city_url_segment(city_key)
        if canonical_service:
            target = f"{DOMAIN}/service-areas/{city_seg}/{canonical_service}/"
            result.target_url = target
            result.category = "Stranded location service → /service-areas/<city>/<service>/"
            result.action = "Build city-service page; 301 source → target"
            result.target_status = "TO BUILD: city-service page does not exist yet"
            result.priority = "High"
            result.cross_vertical = True
            result.notes = (
                f"Root-level location-specific URL: '{canonical_service}' service "
                f"in {city_name}. Per the new architecture, location-bound service "
                f"URLs live at /service-areas/<city>/<service>/. Move source content "
                f"into the new city-service page during migration."
            )
            return result
        # City detected but no service match — likely a blog post that mentions
        # a city in the title (e.g. 'sandy-city-water-contamination'). Fall
        # through to the blog-post handler below.

    # Persistent top-nav pages: /about/, /contact/, /careers/, /blog/, /reviews/, /testimonials/, /tips/, /financing/, /home-warranties/, /superior-protection-plan/
    persistent = {
        "about", "contact", "careers", "blog", "reviews", "testimonials",
        "financing", "home-warranties", "superior-protection-plan", "tips",
    }
    if slug in persistent:
        result.category = "Persistent top-level page"
        result.action = "Leave as-is"
        result.target_url = result.source_url
        result.target_status = "verified live (existing page)"
        result.priority = "—"
        return result

    # Author archive — migrate to /blog/ or noindex
    if slug.startswith("author-") or slug.startswith("author/"):
        result.category = "Author archive"
        result.action = "Noindex or leave as-is — author archives are template pages"
        result.target_url = result.source_url
        result.target_status = "review"
        result.priority = "Low"
        result.notes = "Author archives rarely have SEO value. Recommend noindex."
        return result

    # Default: it's a blog post — migrate to /blog/<slug>/
    result.category = "Blog post → /blog/"
    result.action = "Move post into /blog/; 301 source → target"
    result.target_url = f"{DOMAIN}/blog/{slug}/"
    result.target_status = "TO BUILD: post must be moved within WordPress"
    result.priority = "High"
    result.notes = (
        "Per client decision (2026-04-25), all blog posts move to /blog/<slug>/. "
        "In WordPress: change the post permalink prefix to 'blog' or move via "
        "category-based permalink structure. Existing /blog/ list page already exists."
    )
    return result


def map_url(source_url: str) -> Mapping:
    """Top-level dispatch — given any source URL, return its Mapping."""
    path = urlparse(source_url).path
    parts = path.strip("/").split("/")
    top = parts[0] if parts and parts[0] else ""

    if top == "hvac":
        return map_hvac(path) or _fallback(source_url, path)
    if top == "water":
        return map_water(path) or _fallback(source_url, path)
    if top == "plumbing-services":
        return map_plumbing_services(path) or _fallback(source_url, path)
    if top == "emergency-services":
        return map_emergency_services(path) or _fallback(source_url, path)
    if top == "service-areas":
        # Already in the right place; only sub-paths inside need handling
        result = Mapping(source_url=source_url)
        result.target_url = source_url
        result.category = "/service-areas/ — already correct"
        result.action = "Leave as-is (already matches new architecture)"
        result.target_status = "verified live (existing URL, already correct)"
        result.priority = "—"
        return result
    if top == "coupons":
        result = Mapping(source_url=source_url)
        result.target_url = source_url
        result.category = "Coupons (existing top-level page)"
        result.action = "Leave as-is or migrate to /promotions/ if standardizing"
        result.target_status = "verified live"
        result.priority = "—"
        return result

    # Root level
    return map_root_level(path)


def _fallback(source_url: str, path: str) -> Mapping:
    result = Mapping(source_url=source_url)
    result.target_url = source_url
    result.category = "Unmapped — manual review required"
    result.action = "Review URL pattern manually"
    result.target_status = "REVIEW"
    result.priority = "Medium"
    result.notes = f"Auto-mapper could not classify {path!r} — needs human decision."
    return result


# =============================================================================
# WORKBOOK BUILDERS
# =============================================================================

NAVY = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
HEADER_ALIGN = Alignment(horizontal="left", vertical="center", wrap_text=True)


def style_header(ws, row: int, max_col: int):
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = NAVY
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGN
    ws.row_dimensions[row].height = 30


def set_widths(ws, widths: dict[int, int]):
    for col, w in widths.items():
        ws.column_dimensions[get_column_letter(col)].width = w


def wrap_data(ws, start_row: int = 2):
    ws.freeze_panes = f"A{start_row}"
    for row in ws.iter_rows(min_row=start_row, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def build_summary(wb, mappings: list[Mapping], stats: dict):
    ws = wb.create_sheet("Summary", 0)
    ws["A1"] = "Superior Water & Air — URL Architecture Migration Plan"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"Generated: {date.today().isoformat()}  |  Replaces: superior_gsc_redirect_corrections_plan.xlsx"
    ws["A2"].font = Font(italic=True, color="666666")

    ws["A4"] = "Architecture decision (locked-in)"
    ws["A4"].font = Font(bold=True, size=12)
    ws["A5"] = (
        "All main service pages migrate to /services/<service>/ with sub-services "
        "at /services/<service>/<sub-service>/ (max crawl depth 3). "
        "All location-specific service URLs migrate to /service-areas/<city>-utah/. "
        "All blog posts migrate to /blog/<slug>/. "
        "Water heaters live under /services/plumbing/water-heaters/ per industry convention."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A5:F5")
    ws.row_dimensions[5].height = 80

    ws["A7"] = "What this plan replaces"
    ws["A7"].font = Font(bold=True, size=12)
    ws["A8"] = (
        "The earlier superior_gsc_redirect_corrections_plan.xlsx contained unverified "
        "redirect targets extracted from the Nov 24 GSC audit doc. Several rows had "
        "architectural inconsistencies (e.g., /plumbing/ vs /plumbing-services/ as the "
        "canonical hub) and cosmetic redirects (singular→plural) that wasted effort. "
        "DO NOT IMPLEMENT the prior plan. This document is the authoritative migration plan."
    )
    ws["A8"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A8:F8")
    ws.row_dimensions[8].height = 90

    ws["A10"] = "Migration workload — by category"
    ws["A10"].font = Font(bold=True, size=12)

    ws["A11"] = "Category"
    ws["B11"] = "Count"
    ws["C11"] = "Priority"
    ws["D11"] = "Action"
    style_header(ws, 11, 4)

    cat_counts: dict[str, list[Mapping]] = defaultdict(list)
    for m in mappings:
        cat_counts[m.category].append(m)

    r = 12
    for cat in sorted(cat_counts.keys()):
        items = cat_counts[cat]
        prio = items[0].priority
        action = items[0].action
        ws.cell(row=r, column=1, value=cat)
        ws.cell(row=r, column=2, value=len(items))
        ws.cell(row=r, column=3, value=prio)
        ws.cell(row=r, column=4, value=action)
        ws.cell(row=r, column=4).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1

    r += 1
    ws.cell(row=r, column=1, value="TOTAL URLs in plan").font = Font(bold=True)
    ws.cell(row=r, column=2, value=len(mappings))
    r += 1
    ws.cell(row=r, column=1, value="Cross-vertical moves (need explicit confirmation)").font = Font(bold=True)
    ws.cell(row=r, column=2, value=stats["cross_vertical"])
    r += 1
    ws.cell(row=r, column=1, value="Pages requiring build before redirect").font = Font(bold=True)
    ws.cell(row=r, column=2, value=stats["to_build"])
    r += 1
    ws.cell(row=r, column=1, value="Cosmetic / leave-as-is (NOT in active list)").font = Font(bold=True)
    ws.cell(row=r, column=2, value=stats["cosmetic"])

    r += 2
    ws.cell(row=r, column=1, value="Recommended phasing").font = Font(bold=True, size=12)
    r += 1
    ws.cell(row=r, column=1, value=(
        "Phase 1 (week 1): Build all new pages at /services/... paths. "
        "Don't link to them publicly. Don't 301 anything. Pages exist as orphans for now.\n\n"
        "Phase 2 (week 2): Update internal links — every page that currently links to old URLs gets "
        "updated to point at the new URLs. Use the 'Internal Link Sweep' tab to drive this. "
        "Site still works because old URLs still respond.\n\n"
        "Phase 3 (week 3): Set up 301 redirects from old URLs to new URLs (use the CSV file shipped "
        "with this plan: superior_redirects_rankmath_import.csv). Update sitemap, canonicals, schema. "
        "Submit to GSC.\n\n"
        "Phase 4 (weeks 4-8): Monitor GSC. Watch coverage changes, ranking volatility, redirect errors. "
        "Don't make other major changes during this window.\n\n"
        "DO NOT execute all phases in a single change window — site migrations done that way create "
        "unnecessary risk and make rollback impossible. Phased execution is the standard practice."
    ))
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 240

    r += 2
    ws.cell(row=r, column=1, value="Tabs in this file").font = Font(bold=True, size=12)
    r += 1
    ws.cell(row=r, column=1, value=(
        "1. Summary — this sheet\n"
        "2. Architecture Map — every existing URL with its proposed new URL\n"
        "3. 301 Redirect List — every redirect to set up (active list)\n"
        "4. Pages To Build — new URLs that don't exist yet (Phase 1 work)\n"
        "5. Internal Link Sweep — every page that needs internal links updated (Phase 2 work)\n"
        "6. Stranded URLs — root-level URLs needing decisions (location-stranded, edge cases)\n"
        "7. Cosmetic / Leave As-Is — singular/plural redirects and trailing-slash variants. "
        "DO NOT add these to the developer's task list — they don't need fixing.\n"
        "8. Pre-Migration Checklist — sitemap, canonicals, schema, hreflang, analytics events\n"
        "9. Post-Migration Monitoring — what to track in GSC and how to measure recovery"
    ))
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    ws.row_dimensions[r].height = 195

    set_widths(ws, {1: 45, 2: 14, 3: 12, 4: 60, 5: 15, 6: 15})


def build_architecture_map(wb, mappings: list[Mapping]):
    ws = wb.create_sheet("Architecture Map")
    headers = [
        "#", "Source URL (current)", "Target URL (proposed)",
        "Category", "Action", "Target Status", "Priority",
        "Cross-vertical?", "Notes",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    for i, m in enumerate(mappings, start=1):
        ws.append([
            i, m.source_url, m.target_url, m.category, m.action,
            m.target_status, m.priority,
            "YES" if m.cross_vertical else "",
            m.notes,
        ])
    set_widths(ws, {1: 5, 2: 60, 3: 60, 4: 35, 5: 50, 6: 35, 7: 10, 8: 14, 9: 55})
    wrap_data(ws)


def build_redirect_list(wb, mappings: list[Mapping]):
    """Active 301 redirect list — only rows that produce a real source→target redirect."""
    ws = wb.create_sheet("301 Redirect List")
    headers = [
        "#", "Source URL (301 from)", "Target URL (301 to)",
        "Category", "Target Status", "Priority", "Notes",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    eligible = [
        m for m in mappings
        if m.source_url != m.target_url
        and not m.cosmetic
        and m.target_url
        and "Leave as-is" not in m.action
        and "leave as-is" not in m.target_status.lower()
    ]
    for i, m in enumerate(eligible, start=1):
        ws.append([
            i, m.source_url, m.target_url, m.category,
            m.target_status, m.priority, m.notes,
        ])
    set_widths(ws, {1: 5, 2: 60, 3: 60, 4: 35, 5: 35, 6: 10, 7: 55})
    wrap_data(ws)


def build_pages_to_build(wb, mappings: list[Mapping]):
    """Unique target URLs that need to be built before redirects can flip."""
    ws = wb.create_sheet("Pages To Build")
    headers = [
        "#", "Target URL to build", "Category", "Sources redirecting in", "Notes",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    # Group by target URL
    grouped: dict[str, list[Mapping]] = defaultdict(list)
    for m in mappings:
        if m.target_status.startswith("TO BUILD"):
            grouped[m.target_url].append(m)

    rows = sorted(grouped.items())
    for i, (target, items) in enumerate(rows, start=1):
        sources = "\n".join(f"  • {it.source_url}" for it in items[:10])
        if len(items) > 10:
            sources += f"\n  ...and {len(items) - 10} more"
        first_cat = items[0].category
        first_notes = items[0].notes
        ws.append([
            i, target, first_cat,
            f"{len(items)} URL(s):\n{sources}",
            first_notes,
        ])
    set_widths(ws, {1: 5, 2: 60, 3: 38, 4: 55, 5: 50})
    wrap_data(ws)


def build_internal_link_sweep(wb, redirect_pairs: list[tuple[str, str]], all_pages: list[str]):
    """List of every page that should be checked for outdated internal links.

    Without inlink data we list each redirect source as a 'find this URL in the
    site, replace with target URL' instruction.
    """
    ws = wb.create_sheet("Internal Link Sweep")
    headers = [
        "#", "OLD URL to find in internal links", "NEW URL to replace it with",
        "Where to look", "Priority",
    ]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    for i, (old, new) in enumerate(sorted(set(redirect_pairs)), start=1):
        ws.append([
            i, old, new,
            "Use SF crawl filtered to outlinks containing this old URL, OR run a "
            "site-wide search-and-replace in WordPress (Better Search Replace plugin). "
            "Verify hand-edited content blocks (Elementor/Gutenberg) — plugin sweeps "
            "miss links inside widget JSON.",
            "Phase 2 (before flipping redirects)",
        ])
    set_widths(ws, {1: 5, 2: 55, 3: 55, 4: 60, 5: 25})
    wrap_data(ws)


def build_stranded(wb, mappings: list[Mapping]):
    """Root-level URLs that needed special-case decisions."""
    ws = wb.create_sheet("Stranded URLs")
    headers = ["#", "Source URL", "Target URL", "Category", "Action", "Notes"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    stranded = [
        m for m in mappings
        if m.category in (
            "Stranded location URL → service-areas",
            "Author archive",
            "Unmapped — manual review required",
            "Other /water/ → /services/water-treatment/",
        )
    ]
    for i, m in enumerate(stranded, start=1):
        ws.append([i, m.source_url, m.target_url, m.category, m.action, m.notes])
    set_widths(ws, {1: 5, 2: 55, 3: 55, 4: 35, 5: 50, 6: 55})
    wrap_data(ws)


def build_cosmetic(wb, mappings: list[Mapping]):
    """The 'don't fix what isn't broken' list."""
    ws = wb.create_sheet("Cosmetic - Leave As-Is")
    headers = ["#", "URL", "Why leave alone", "Notes"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    cosmetic = [m for m in mappings if m.cosmetic]
    for i, m in enumerate(cosmetic, start=1):
        ws.append([
            i, m.source_url, m.action,
            m.notes or "Existing URL handles its current role correctly. "
            "No rewrite needed; no developer task.",
        ])
    set_widths(ws, {1: 5, 2: 60, 3: 50, 4: 55})
    wrap_data(ws)


def build_premigration_checklist(wb):
    ws = wb.create_sheet("Pre-Migration Checklist")
    headers = ["#", "Task", "Phase", "Owner", "Done?", "Notes"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    items = [
        ("Confirm /services/ and /service-areas/ structure decisions in writing", "Phase 0", "Roger / client", "",
         "Lock the architecture before any URL changes go live."),
        ("Take a full site backup (database + files)", "Phase 0", "Hosting / dev", "",
         "Required rollback target. WP Engine handles this — verify the backup completes successfully before Phase 1 starts."),
        ("Build the /services/ hub page", "Phase 1", "Dev", "",
         "/services/ landing page lists all top-level services and links to each hub."),
        ("Build /services/hvac/ hub", "Phase 1", "Dev", "",
         "Lists furnace, AC, air-purification, generators, etc. — links to each sub-page."),
        ("Build /services/plumbing/ hub", "Phase 1", "Dev", "",
         "Lists drain cleaning, water heaters, kitchen, bathroom, sewer, etc."),
        ("Build /services/water-treatment/ hub", "Phase 1", "Dev", "",
         "Lists water filtration, reverse osmosis, water softeners, ice makers, etc."),
        ("Build /services/emergency/ hub", "Phase 1", "Dev", "",
         "Lists emergency-service variants for each vertical."),
        ("Move all blog posts under /blog/<slug>/", "Phase 1", "Dev", "",
         "WordPress permalink change — coordinate so post IDs preserve, only the slug prefix changes."),
        ("Update WP main navigation menu to point to new /services/ URLs", "Phase 2", "Dev", "",
         "After hubs are built but before redirects flip."),
        ("Update WP footer to reference new /services/ URLs", "Phase 2", "Dev", "",
         ""),
        ("Run a Better Search Replace pass: find old URLs → replace with new", "Phase 2", "Dev", "",
         "Use the 'Internal Link Sweep' tab as the source of truth. Run on dry-run first; verify counts match expectations."),
        ("Hand-check Elementor/Gutenberg widget JSON for embedded old URLs", "Phase 2", "Dev", "",
         "Plugin sweeps miss links stored as JSON inside widget data. Spot-check the homepage, top service pages, and city pages."),
        ("Verify NO internal links still point to old URLs (run SF crawl, filter outlinks)", "Phase 2", "Dev / Roger", "",
         "Critical — internal redirects post-migration are a self-inflicted equity leak."),
        ("Import 301 redirect list (CSV file shipped with this plan)", "Phase 3", "Dev", "",
         "File: superior_redirects_rankmath_import.csv. Import via Rank Math → Redirections → Import."),
        ("Update XML sitemap to list NEW URLs only — remove all old URLs", "Phase 3", "Dev", "",
         "Rank Math regenerates this automatically when permalinks change."),
        ("Update canonical tags — every page's canonical should be the new URL", "Phase 3", "Dev", "",
         "WP themes usually emit self-referential canonicals; verify on a sample of 10 pages after the move."),
        ("Update LocalBusiness / Service schema with new URLs", "Phase 3", "Dev", "",
         "If schema is set in WP Customizer or a theme option, find and update."),
        ("Submit updated sitemap in Google Search Console", "Phase 3", "Roger", "",
         "GSC → Sitemaps → submit https://superiorwaterandair.com/sitemap_index.xml"),
        ("Use GSC URL Inspection on 10 high-value old URLs to confirm 301", "Phase 3", "Roger", "",
         "Spot-check the homepage, top service pages, and 3 city pages immediately after Phase 3."),
        ("Set up GA4 redirect event tracking (optional but recommended)", "Phase 3", "Roger", "",
         "Tracks how many visitors hit each redirected URL — useful for prioritizing post-migration content updates."),
        ("Monitor GSC Coverage report daily for first 2 weeks", "Phase 4", "Roger", "",
         "Watch for crawl errors, indexed-but-not-canonical warnings, and increased redirect volume."),
        ("Monitor rankings on top 20 commercial queries weekly for 8 weeks", "Phase 4", "Roger", "",
         "Use existing rank tracking. Expect 2-4 weeks of volatility — DON'T panic and revert."),
        ("Run a follow-up audit 60 days post-migration", "Phase 4", "Roger", "",
         "Confirm the migration achieved its goals — clean URL structure, no internal redirects, GSC coverage matches sitemap, organic traffic stable or improving."),
    ]
    for i, item in enumerate(items, start=1):
        ws.append([i] + list(item))
    set_widths(ws, {1: 5, 2: 60, 3: 12, 4: 15, 5: 7, 6: 55})
    wrap_data(ws)


def build_monitoring(wb):
    ws = wb.create_sheet("Post-Migration Monitoring")
    headers = ["#", "Metric", "Where to check", "What to expect", "Red flag"]
    ws.append(headers)
    style_header(ws, 1, len(headers))

    items = [
        ("Coverage report — total indexed", "GSC → Coverage",
         "Initial dip 1-2 weeks as old URLs deindex; should recover and exceed pre-migration count within 4-6 weeks.",
         "Persistent decline beyond 4 weeks, or 'Indexed, though blocked by robots.txt' warnings."),
        ("URL Inspection on top URLs", "GSC → URL Inspection",
         "Within 7-14 days, every old URL shows '301 to <new URL>' and the new URL shows 'Indexed'.",
         "Old URL still 'Indexed' after 14 days, OR new URL stuck on 'Discovered, currently not indexed'."),
        ("Total clicks (organic)", "GSC → Performance",
         "Possible 10-20% temporary dip in week 1-2; recovery in weeks 3-6; meet or exceed baseline by week 8.",
         "Dip exceeds 30% or fails to recover by week 6."),
        ("Average position on top 20 queries", "GSC → Performance",
         "Brief volatility (±3-5 positions) for 2-4 weeks, then stabilizes at or above prior position.",
         "Permanent drop on multiple high-value queries beyond week 4."),
        ("Internal redirects (SF crawl)", "Run SF crawl weekly during Phase 4",
         "Zero internal links pointing through 301s. Every internal link goes directly to the new URL.",
         "Any non-zero count after Phase 2 is an unfinished link sweep."),
        ("Crawl errors (404s)", "GSC → Coverage → Excluded",
         "Brief uptick as Googlebot hits old URLs that became 410 instead of 301; should drop to baseline in 2-4 weeks.",
         "Persistent 404s on URLs that should have 301s — indicates redirects didn't import correctly."),
        ("Sitemap accuracy", "GSC → Sitemaps",
         "Submitted sitemap shows the new URL set; 'Indexed' count matches submitted count within 2-3 weeks.",
         "Large gap between submitted and indexed counts indicates indexability problems on the new URLs."),
        ("GA4 organic sessions", "GA4 → Acquisition → Traffic acquisition",
         "Possibly minor dip in week 1; baseline restoration by week 4-6.",
         "Sustained 20%+ decline beyond week 6."),
    ]
    for i, item in enumerate(items, start=1):
        ws.append([i] + list(item))
    set_widths(ws, {1: 5, 2: 30, 3: 28, 4: 50, 5: 50})
    wrap_data(ws)


# =============================================================================
# CSV EXPORT FOR REDIRECT PLUGINS
# =============================================================================

def write_redirect_csv(mappings: list[Mapping], path: str):
    """Generate a CSV importable into Rank Math (and most redirect plugins).

    Format (Rank Math expected columns):
        source url, matching, destination url, type, code, hits, status

    We provide the Rank Math format AND a 'simple' format (source, target)
    that works with most other plugins. Rank Math's import tolerates
    extra columns being absent and infers sensible defaults.
    """
    eligible = [
        m for m in mappings
        if m.source_url != m.target_url
        and not m.cosmetic
        and m.target_url
        and "Leave as-is" not in m.action
        and "leave as-is" not in m.target_status.lower()
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        # Rank Math import format header
        writer.writerow([
            "source url", "matching", "destination url", "type",
            "code", "hits", "status",
        ])
        for m in eligible:
            # Source URL: relative path is more portable across Rank Math instances
            src_path = urlparse(m.source_url).path
            # Destination: use absolute URL so cross-domain redirects (none here)
            # would also work; for same-domain Rank Math accepts relative too.
            writer.writerow([
                src_path,           # source url (relative)
                "exact",            # matching mode
                m.target_url,       # destination
                "301",              # type
                "301",              # HTTP code
                "0",                # hits
                "active",           # status
            ])


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Load all indexable HTML URLs
    indexable = json.load(open("/tmp/superior_indexable.json", encoding="utf-8"))
    urls = [p["url"] for p in indexable]

    # Build mappings
    mappings = [map_url(u) for u in urls]

    # Stats
    stats = {
        "cross_vertical": sum(1 for m in mappings if m.cross_vertical),
        "to_build": sum(1 for m in mappings if m.target_status.startswith("TO BUILD")),
        "cosmetic": sum(1 for m in mappings if m.cosmetic),
    }

    print(f"Total URLs mapped: {len(mappings)}")
    print(f"Cross-vertical moves: {stats['cross_vertical']}")
    print(f"Pages to build: {stats['to_build']}")
    print(f"Cosmetic / leave-as-is: {stats['cosmetic']}")

    # Category breakdown
    cats: dict[str, int] = defaultdict(int)
    for m in mappings:
        cats[m.category] += 1
    print("\nCategory breakdown:")
    for cat, count in sorted(cats.items(), key=lambda kv: -kv[1]):
        print(f"  {count:3d}  {cat}")

    # Build workbook
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    build_summary(wb, mappings, stats)
    build_architecture_map(wb, mappings)
    build_redirect_list(wb, mappings)
    build_pages_to_build(wb, mappings)
    redirect_pairs = [
        (m.source_url, m.target_url)
        for m in mappings
        if m.source_url != m.target_url and not m.cosmetic
        and m.target_url and "leave as-is" not in m.target_status.lower()
    ]
    build_internal_link_sweep(wb, redirect_pairs, urls)
    build_stranded(wb, mappings)
    build_cosmetic(wb, mappings)
    build_premigration_checklist(wb)
    build_monitoring(wb)

    os.makedirs(os.path.dirname(OUT_XLSX), exist_ok=True)
    wb.save(OUT_XLSX)
    print(f"\nSaved Excel: {OUT_XLSX}")

    # Write CSV
    write_redirect_csv(mappings, OUT_CSV)
    csv_count = sum(1 for line in open(OUT_CSV, encoding="utf-8")) - 1
    print(f"Saved CSV:   {OUT_CSV}")
    print(f"  → {csv_count} redirect rules ready for Rank Math import")


if __name__ == "__main__":
    main()
