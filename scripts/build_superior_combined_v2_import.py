"""
Superior Water & Air — Combined v2 cleanup import for Rank Math.

Builds ONE CSV that:
  1. 301-redirects 23 newly-found page 404s to their best-fit targets
     (or 410s the ones with no good target)
  2. 410-marks 30 newly-found image 404s
  3. SKIPS anything we already imported in earlier batches

Already-imported sources are deduped against:
    - superior_410_gone_broken_images_import.csv (the original 83 broken images)
    - superior_rankmath_redirects_cleaned_full_import.csv (112 migration redirects)

Output:
    Clients/Superior/Full SEO Audit/superior_v2_cleanup_import.csv

Format follows Rank Math's CSV import spec:
    id, source, matching, destination, type, category, status, ignore
    - 301 rows: empty id, source = relative path, destination = full URL,
                type = 301, category = "Sitemap Cleanup v2"
    - 410 rows: empty id, source = relative path, destination = source URL
                (Rank Math requires the field but ignores it for 410),
                type = 410, category = "Sitemap Cleanup v2"
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys
from urllib.parse import urlparse

import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
PRIOR_410_CSV = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_410_gone_broken_images_import.csv",
)
MIGRATION_CSV = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_rankmath_redirects_cleaned_full_import.csv",
)
V2_PLAN_XLSX = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_sitemap_cleanup_plan_v2.xlsx",
)
OUT_CSV = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_v2_cleanup_import.csv",
)

DOMAIN = "https://superiorwaterandair.com"

UTAH_CITIES = {
    "salt-lake-city", "salt-lake", "st-george", "park-city", "west-jordan",
    "west-valley", "west-haven", "south-jordan", "north-salt-lake",
    "north-ogden", "spanish-fork", "cedar-city", "cedar-hills",
    "pleasant-grove", "pleasant-view", "american-fork", "eagle-mountain",
    "saratoga-springs", "cottonwood-heights", "farr-west", "woods-cross",
    "sandy", "orem", "provo", "ogden", "lehi", "draper", "murray", "tooele",
    "layton", "riverton", "herriman", "highland", "salem", "midvale",
    "kearns", "bluffdale", "springville", "millcreek", "taylorsville",
    "kaysville", "alpine", "bountiful", "centerville", "clearfield",
    "clinton", "farmington", "holladay", "hooper", "hurricane", "lindon",
    "magna", "mapleton", "roy", "syracuse", "washington",
}

EXISTING_CITY_SLUGS = {
    "alpine": "alpine-utah", "american-fork": "american-fork-ut",
    "bluffdale": "bluffdale-utah", "bountiful": "bountiful-utah",
    "cedar-city": "cedar-city-utah", "cedar-hills": "cedar-hills-ut",
    "centerville": "centerville-utah", "clearfield": "clearfield-utah",
    "clinton": "clinton-utah", "cottonwood-heights": "cottonwood-heights-utah",
    "draper": "draper-utah", "eagle-mountain": "eagle-mountain-utah",
    "farmington": "farmington-utah", "farr-west": "farr-west-utah",
    "herriman": "herriman-utah", "highland": "highland-utah",
    "holladay": "holladay-utah", "hooper": "hooper-utah",
    "hurricane": "hurricane-utah", "kaysville": "kaysville-utah",
    "kearns": "kearns-utah", "layton": "layton-utah", "lehi": "lehi-utah",
    "lindon": "lindon-utah", "magna": "magna-utah",
    "mapleton": "mapleton-utah", "midvale": "midvale-utah",
    "millcreek": "millcreek-utah", "murray": "murray-utah",
    "north-ogden": "north-ogden",
    "north-salt-lake": "north-salt-lake-utah", "ogden": "ogden-utah",
    "orem": "orem-utah", "park-city": "park-city-utah",
    "pleasant-grove": "pleasant-grove-utah",
    "pleasant-view": "pleasant-view-utah", "provo": "provo-utah",
    "riverton": "riverton-ut", "roy": "roy-utah", "salem": "salem-utah",
    "salt-lake-city": "salt-lake-city-utah",
    "salt-lake": "salt-lake-city-utah", "sandy": "sandy-utah",
    "saratoga-springs": "saratoga-springs-utah",
    "south-jordan": "south-jordan-utah",
    "spanish-fork": "spanish-fork-utah", "springville": "springville-utah",
    "st-george": "st-george-utah", "syracuse": "syracuse-utah",
    "taylorsville": "taylorsville-utah", "tooele": "tooele-utah",
    "washington": "washington-utah", "west-haven": "west-haven-utah",
    "west-jordan": "west-jordan-utah", "west-valley": "west-valley-utah",
    "woods-cross": "woods-cross-utah",
}


def detect_city(slug: str) -> str:
    s = slug.lower()
    for c in sorted(UTAH_CITIES, key=len, reverse=True):
        if re.search(rf"(^|-){re.escape(c)}(-|$)", s):
            return c
    return ""


def smart_target_for_page_404(url: str) -> tuple[str, str, str]:
    """Pick the best 301 target for a 404 page URL.

    Returns (target_url, redirect_type, reason).
    redirect_type is "301" or "410".
    """
    path = urlparse(url).path.rstrip("/")
    slug = path.lstrip("/")

    # Year-prefixed blog: /YYYY/MM/<slug>/ → /blog/<slug>/
    m = re.match(r"^(\d{4})/(\d{2})/(.+)$", slug)
    if m:
        post_slug = m.group(3)
        return (f"{DOMAIN}/blog/{post_slug}/", "301",
                "Old date-prefixed blog URL — redirect to new /blog/ structure")

    # /how-much-is-a-water-softener-2/ → strip -N suffix to reach canonical
    m = re.match(r"^(.+)-(\d+)$", slug)
    if m and slug.count("/") == 0:
        canonical_slug = m.group(1)
        # Verify the canonical version exists by checking known live URLs;
        # for this audit assume duplicate-slug pages should redirect to the
        # /blog/ version (since the migration moves blog posts there)
        return (f"{DOMAIN}/blog/{canonical_slug}/", "301",
                f"Duplicate-slug page — redirect to canonical /blog/{canonical_slug}/")

    # /plumbing-services/<service>/ → /services/plumbing/<service>/
    m = re.match(r"^plumbing-services/([^/]+)$", slug)
    if m:
        sub = m.group(1)
        # Special case: pipe-lining / bathro (truncated bathroom-plumbing)
        if sub == "pipe-lining":
            return (f"{DOMAIN}/services/plumbing/service-and-repair/", "301",
                    "Pipe lining is part of plumbing repair — redirect to service-and-repair")
        if sub.startswith("bathro"):
            return (f"{DOMAIN}/services/plumbing/bathroom-plumbing/", "301",
                    "Truncated slug — redirect to bathroom-plumbing")
        return (f"{DOMAIN}/services/plumbing/{sub}/", "301",
                "Migrate /plumbing-services/ to new /services/plumbing/ structure")

    # /water-heaters/tankless-water-heaters/ → /services/plumbing/water-heaters/tankless/
    if slug == "water-heaters/tankless-water-heaters":
        return (f"{DOMAIN}/services/plumbing/water-heaters/tankless/", "301",
                "Migrate to new tankless water heater service URL")

    # /sewer-drain-services-utah/ → /services/plumbing/sewer-and-drain/
    if slug == "sewer-drain-services-utah":
        return (f"{DOMAIN}/services/plumbing/sewer-and-drain/", "301",
                "Sewer drain services → /services/plumbing/sewer-and-drain/")

    # Service-specific city plumbing: /plumber-<city>-ut/ or /plumbing-<city>-ut/ or /<city>-plumbing/
    m = re.match(
        r"^(?:plumber|plumbing)-(.+)-(?:ut|utah)$|^(.+)-plumbing$|^(?:plumbing)-(.+)$",
        slug,
    )
    if m:
        city_part = m.group(1) or m.group(2) or m.group(3) or ""
        # Strip "-ut", "-utah", and "-county"
        city_part = re.sub(r"-(?:ut|utah|county)$", "", city_part)
        city = detect_city(city_part)
        if city:
            city_seg = EXISTING_CITY_SLUGS.get(city, f"{city}-utah")
            return (f"{DOMAIN}/service-areas/{city_seg}/plumbing/", "301",
                    f"City-plumbing URL → /service-areas/{city_seg}/plumbing/")
        # Multi-city or unknown: send to general plumbing service
        return (f"{DOMAIN}/services/plumbing/", "301",
                "Generic city/area plumbing URL — redirect to plumbing hub")

    # /plumbing-services-emergency-utah/ → /services/emergency/plumbing-repair/
    if slug == "plumbing-services-emergency-utah":
        return (f"{DOMAIN}/services/emergency/plumbing-repair/", "301",
                "Emergency plumbing variant → /services/emergency/plumbing-repair/")

    # /services/home-water-evaluation/ → /services/water-treatment/
    if slug == "services/home-water-evaluation":
        return (f"{DOMAIN}/services/water-treatment/", "301",
                "Home water evaluation → /services/water-treatment/")

    # /services/plumbingdrain-cleaning/ → /services/plumbing/drain-cleaning/
    if slug == "services/plumbingdrain-cleaning":
        return (f"{DOMAIN}/services/plumbing/drain-cleaning/", "301",
                "Typo'd service slug — redirect to /services/plumbing/drain-cleaning/")

    # /maintenance/ → 410 (no clear target)
    if slug == "maintenance":
        return ("", "410",
                "Generic /maintenance/ URL with no clear migration target")

    # /pipe-lining/ (root) → /services/plumbing/service-and-repair/
    if slug == "pipe-lining":
        return (f"{DOMAIN}/services/plumbing/service-and-repair/", "301",
                "Pipe lining → /services/plumbing/service-and-repair/")

    # /hard-water-tool/ → /services/water-treatment/
    if slug == "hard-water-tool":
        return (f"{DOMAIN}/services/water-treatment/", "301",
                "Hard water tool → /services/water-treatment/")

    # /portable_generator/ (note the underscore) → /services/hvac/home-generators/
    if slug == "portable_generator":
        return (f"{DOMAIN}/services/hvac/home-generators/", "301",
                "Portable generator → /services/hvac/home-generators/")

    # Bare slug that looks like a blog post → /blog/<slug>/
    if "/" not in slug and len(slug) > 5 and "-" in slug:
        # Skip if it starts with known service prefixes
        if not slug.startswith((
            "hvac", "water-", "plumbing-", "service-", "emergency-",
            "wp-", "page", "category", "author",
        )):
            return (f"{DOMAIN}/blog/{slug}/", "301",
                    "Bare blog-style slug — redirect to /blog/")

    # Fallback: 410
    return ("", "410", "No clear migration target — 410 Gone is safest")


def main() -> None:
    # Build the set of paths we've already imported (to dedupe)
    already_imported = set()
    with open(PRIOR_410_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            path = "/" + r["source"].lstrip("/").rstrip("/")
            already_imported.add(path)
    with open(MIGRATION_CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["destination"] == "DELETE":
                continue
            path = "/" + r["source"].lstrip("/").rstrip("/")
            already_imported.add(path)
    print(f"Already-imported source paths: {len(already_imported)}")

    # Pull URLs from the v2 plan
    wb = openpyxl.load_workbook(V2_PLAN_XLSX, read_only=True, data_only=True)

    image_404s_new = []
    ws = wb["Image 404s"]
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[1]:
            continue
        url = row[1]
        path = urlparse(url).path.rstrip("/")
        if path in already_imported:
            continue
        image_404s_new.append(url)

    page_404s_new = []
    ws = wb["Page 404s"]
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[1]:
            continue
        url = row[1]
        path = urlparse(url).path.rstrip("/")
        if path in already_imported:
            continue
        page_404s_new.append(url)
    wb.close()

    print(f"\nNEW image 404s to add: {len(image_404s_new)}")
    print(f"NEW page 404s to add: {len(page_404s_new)}")

    # Decide target for each page 404
    page_decisions = []
    for url in page_404s_new:
        target, rtype, reason = smart_target_for_page_404(url)
        page_decisions.append({
            "url": url,
            "target": target,
            "type": rtype,
            "reason": reason,
        })

    # Write the combined CSV
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "source", "matching", "destination",
            "type", "category", "status", "ignore",
        ])

        # Section 1: page 301s and 410s
        for d in page_decisions:
            src = urlparse(d["url"]).path.lstrip("/")
            if d["type"] == "301":
                writer.writerow([
                    "", src, "exact", d["target"], "301",
                    "Sitemap Cleanup v2", "active", "",
                ])
            else:  # 410
                writer.writerow([
                    "", src, "exact", d["url"], "410",
                    "Sitemap Cleanup v2", "active", "",
                ])

        # Section 2: image 410s
        for url in image_404s_new:
            src = urlparse(url).path.lstrip("/")
            writer.writerow([
                "", src, "exact", url, "410",
                "Sitemap Cleanup v2", "active", "",
            ])

    # Verification
    with open(OUT_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    type_counts = {"301": 0, "410": 0}
    for r in rows:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1

    print(f"\nSaved: {OUT_CSV}")
    print(f"\nVerification:")
    print(f"  Total rows: {len(rows)}")
    print(f"  301 redirects: {type_counts.get('301', 0)}")
    print(f"  410 Gone:      {type_counts.get('410', 0)}")

    # Print decisions
    print()
    print("301 decisions for page 404s:")
    for d in page_decisions:
        if d["type"] == "301":
            print(f"  {d['url']}")
            print(f"    -> {d['target']}")
            print(f"    {d['reason']}")
    print()
    print("410 decisions for page 404s:")
    for d in page_decisions:
        if d["type"] == "410":
            print(f"  {d['url']}")
            print(f"    {d['reason']}")


if __name__ == "__main__":
    main()
