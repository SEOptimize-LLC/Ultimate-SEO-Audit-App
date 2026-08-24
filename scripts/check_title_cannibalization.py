"""Sibling-page check: does a proposed title modifier belong to another page?

    python scripts/check_title_cannibalization.py <sitemap_url> "<proposed title>" <target_url>

Pulls every URL from the site's sitemap index, then reports any OTHER page
whose slug contains a service token from the proposed title. A hit means the
modifier is that page's job, and putting it in this page's title sets two
pages against each other.

Exists because five titles across two client sheets (2026-08-24) proposed
modifiers owned by sibling pages: "Heating Services" and "Maintenance" on a
furnace REPAIR page that has /hvac/furnace-maintenance/ and an /hvac/ parent;
"Repair" on a water-heater INSTALL page that has /water-heater-repair-utah/;
"Jetting" on a drain page that has /hydro-jetting-drain-cleaning-utah/.

Run this BEFORE proposing any title, H1, or section heading that adds a
service word the page does not already own.
"""

from __future__ import annotations

import re
import ssl
import sys
import urllib.request

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"

# Service words worth checking: a modifier that is one of these belongs to
# whichever page is named for it. NOTE "service(s)" is deliberately absent -
# the house title rule requires it on service pages, so it is a required
# suffix rather than a differentiating modifier, and flagging it is noise.
# City-page directories are skipped: a city page for a service does not
# compete with the main service page, it supports it.
SERVICE_TOKENS = [
    "repair", "install", "installation", "replacement", "replace",
    "maintenance", "tune-up", "tuneup", "cleaning",
    "jetting", "snaking", "inspection", "emergency", "heating", "cooling",
    "plumbing", "hvac", "softener", "filtration", "purification",
    "treatment", "tankless", "commercial", "residential", "drain", "sewer",
]

STOP = {"the", "and", "for", "in", "of", "your", "a", "an", "with", "to"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45, context=CTX) as r:
        return r.read().decode("utf-8", "replace")


def all_urls(sitemap_url: str) -> list[str]:
    idx = fetch(sitemap_url)
    locs = re.findall(r"<loc>([^<]+)</loc>", idx)
    if not any(l.endswith(".xml") for l in locs):
        return locs
    out: list[str] = []
    for m in locs:
        if not m.endswith(".xml"):
            continue
        try:
            out += re.findall(r"<loc>([^<]+)</loc>", fetch(m))
        except Exception as e:
            print(f"  (skipped {m}: {e.__class__.__name__})")
    return out


def main(sitemap_url: str, title: str, target: str) -> None:
    urls = [u for u in all_urls(sitemap_url) if "/blog/" not in u]
    tgt = target.rstrip("/").lower()
    words = [w for w in re.findall(r"[a-z0-9-]+", title.lower())
             if w not in STOP]
    mods = [w for w in words if w in SERVICE_TOKENS]
    print(f"sitemap URLs (non-blog): {len(urls)}")
    print(f"target: {target}")
    print(f"service tokens in the proposed title: {mods or '(none)'}")
    if not mods:
        print("nothing to check")
        print()
        print("VERDICT: no sibling conflicts found")
        return

    # A city or service-area page legitimately names several services: that
    # is what the page is for. Naming them does not compete with the service
    # pages, it points at them. Report findings as advisory only.
    city_page = any(s in tgt for s in ("/service-areas/", "/our-locations/",
                                       "/locations/", "/service-area/"))
    if city_page:
        print("  NOTE: target is a city / service-area page. Naming several "
              "services here is correct, not cannibalization.")
        print()
        print("VERDICT: no sibling conflicts found (city page)")
        return
    target_slug = tgt.split("//")[-1]
    tgt_section = tgt.split("//")[-1].split("/")[1] if tgt.count("/") > 3 else ""
    # The core service noun of the target page, taken from its own slug.
    # A conflict only exists when another page covers the SAME service with a
    # different modifier: /hvac/furnace-repair/ conflicts with
    # /hvac/furnace-maintenance/ (both furnace), but not with
    # /bidet-installation-repair-utah/ (a different service entirely).
    CORE = ["furnace", "boiler", "water-heater", "softener", "drain",
            "sewer", "plumbing", "hvac", "tankless", "treatment",
            "filtration", "toilet", "bidet", "faucet", "hydronic",
            "air-conditioner"]
    # Read the core noun from the PATH only. Reading it from the full URL
    # lets a domain like beehiveplumbing.com register "plumbing" as this
    # page's core service, which matches every page on the site.
    tgt_path = "/" + tgt.split("//")[-1].split("/", 1)[-1] if "/" in tgt.split("//")[-1] else ""
    # Prefer the core noun in the page's OWN slug over one in a parent
    # folder. On /plumbing/toilets/ the service is toilets; matching on
    # "plumbing" would make every page under /plumbing/ a competitor.
    tgt_slug = tgt_path.rstrip("/").rsplit("/", 1)[-1]
    core = [c for c in CORE if c in tgt_slug] or [c for c in CORE if c in tgt_path]
    problems = 0
    for tok in mods:
        owners = []
        for u in urls:
            ul = u.rstrip("/").lower()
            if (ul == tgt or "/service-areas/" in ul
                    or "/our-locations/" in ul or "/ppc-" in ul):
                continue
            slug = ul.rsplit("/", 1)[-1]
            if tok not in slug:
                continue
            # A SERVICE page is named for its service: short slug. Blog posts
            # and guides have long ones ("5-things-to-know-about-..."), and
            # flagging those is noise - they are not competing service pages.
            if len(slug.split("-")) > 6:
                continue
            # must cover the target's core service to be a competitor
            # (path only, for the same reason the target's core is)
            u_path = ("/" + ul.split("//")[-1].split("/", 1)[-1]
                      if "/" in ul.split("//")[-1] else "")
            if core and not any(c in u_path for c in core):
                continue
            # Cross-category pages are not competitors: an AIR filtration
            # page does not conflict with a WATER page's title.
            sec = ul.split("//")[-1].split("/")[1] if ul.count("/") > 3 else ""
            if tgt_section and sec and sec != tgt_section:
                owners.append((u, "different section, judge manually"))
                continue
            owners.append((u, ""))
        if tok in target_slug:
            print(f"  OK   '{tok}' is in the target's own slug")
            continue
        hard = [o for o in owners if not o[1]]
        soft = [o for o in owners if o[1]]
        if hard:
            problems += 1
            print(f"  !!   '{tok}' is owned by {len(hard)} sibling service page(s):")
            for o, _ in hard[:6]:
                print(f"         {o}")
        elif soft:
            print(f"  ?    '{tok}' appears in {len(soft)} page(s) in a different section:")
            for o, _ in soft[:4]:
                print(f"         {o}")
        else:
            print(f"  OK   '{tok}' has no dedicated service page")
    # Parent-category check. Broadening a specific service page into its
    # parent category is cannibalization the slug scan cannot see, because
    # the parent is often named differently: /hvac/ IS the heating category,
    # so "Heating Services" on /hvac/furnace-repair/ competes with the hub
    # even though no slug contains the word "heating".
    PARENT_WORDS = {
        "hvac": ["heating", "cooling", "air conditioning", "hvac"],
        "plumbing": ["plumbing", "plumber"],
        "water": ["water treatment", "water systems"],
        "emergency-services": ["emergency services"],
        "air-quality-services": ["air quality", "indoor air"],
    }
    tl = title.lower()
    if tgt_section in PARENT_WORDS and tgt_section not in target_slug.rsplit("/", 1)[-1]:
        for w in PARENT_WORDS[tgt_section]:
            if w in tl:
                problems += 1
                print(f"  !!   '{w}' is the parent category ({tgt_section}) of this "
                      f"page, not this page's service - it belongs to the hub")
                break

    print()
    print("VERDICT:", "REVISE THE TITLE" if problems else
          "no sibling conflicts found")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
