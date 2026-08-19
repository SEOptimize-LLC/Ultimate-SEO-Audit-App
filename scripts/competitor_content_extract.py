"""Competitor content extraction for the content-level competitor analysis workflow.

Fetches a set of competitor + client URLs, extracts the structural, copy, and schema
signals the analysis compares on, and writes:

  <outdir>/raw/<slug>.txt      full extracted main-content text (audit trail)
  <outdir>/pages/<slug>.json   structured per-page extraction
  <outdir>/competitor_matrix.csv  one row per page

Usage:
    python scripts/competitor_content_extract.py --config <config.json> --outdir <dir>

Config is a JSON list of {"url", "brand", "role", "serp_note"} objects.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Sister properties in the same group. These must never be analysed as competitors
# of one another: they are all ours, so benchmarking one against another measures
# our own work and silently inflates the "field" we claim to be compared against.
# The script hard-blocks them; a config listing one aborts the run.
SISTER_DOMAINS = {
    "beehiveplumbing.com",
    "comfortsolutionsutah.com",
    "samedayutah.com",
    "superiorwaterandair.com",
}
HEADERS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
TIMEOUT = 45

# Chrome/blocks that are template furniture, not page copy.
STRIP_TAGS = ["script", "style", "noscript", "svg", "iframe", "form"]
STRIP_ROLES = ["navigation", "banner", "contentinfo"]

# Site-wide widget blocks. Present on every page of the site, so they are template
# furniture rather than page copy (audit-workflow Rule 8). Stripped for the "core"
# word count; the raw count is reported alongside it so the delta stays visible.
WIDGET_CLASS_PATTERNS = [
    "coupon", "special", "promo", "savings-club", "recent-post", "related-post",
    "latest-post", "blog-roll", "testimonial", "review-slider", "review-carousel",
    "reviews-widget", "financing-banner", "popup", "modal", "newsletter",
    "social-share", "sidebar", "widget-area", "service-area-list", "city-list",
]
WIDGET_HEADING_PATTERNS = [
    r"^recent posts", r"^latest (posts|news|articles)", r"^from (our|the) blog",
    r"^save big", r"^join .* (savings|club)", r"^our coupons", r"^current specials",
    r"^related (posts|articles|services)",
]

CITY = "salt lake city"
EQUIPMENT_BRANDS = [
    "lennox", "carrier", "trane", "goodman", "rheem", "bryant", "amana",
    "york", "american standard", "daikin", "payne", "ruud", "heil", "coleman",
]
SYMPTOM_TERMS = [
    "not blowing hot", "blowing cold", "won't turn on", "wont turn on",
    "short cycling", "short cycle", "pilot light", "strange noise", "loud noise",
    "blower motor", "heat exchanger", "flame sensor", "ignitor", "igniter",
    "thermostat", "gas valve", "limit switch", "carbon monoxide", "no heat",
]
TRUST_TERMS = [
    "licensed", "insured", "bonded", "nate", "epa certified", "background",
    "bbb", "warranty", "guarantee", "satisfaction",
]
# Local conditions that cause the problem in this market. Counts how far a page
# goes beyond naming the city, which is the signal that separates a page written
# about somewhere from a page that could be published for any city.
# Deliberately excludes generic cold-climate words (winter, snow, freeze,
# basement). Those appear on every page in every market and counting them makes
# an interchangeable page look locally specific. Only terms that tie to this
# market's geology, water, altitude or housing stock count here.
LOCAL_CONDITION_TERMS = [
    "inversion", "hard water", "altitude", "elevation", "wasatch",
    "salt lake valley", "canyon", "mineral", "calcium", "sediment",
    "lime scale", "limescale", "well water", "water hardness", "grains per",
    "historic district", "bungalow", "victorian", "craftsman", "pre-war",
    "post-war", "high-rise", "high rise", "avenues", "sugar house",
    "marmalade", "millcreek", "cottonwood", "housing stock", "built in the",
]


def slugify(url: str) -> str:
    p = urlparse(url)
    base = (p.netloc + p.path).replace("www.", "")
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:80]


def fetch(url: str) -> tuple[str | None, dict]:
    meta = {"fetch_status": None, "fetch_error": "", "x_robots_tag": ""}
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        meta["fetch_status"] = r.status_code
        meta["x_robots_tag"] = r.headers.get("X-Robots-Tag", "")
        meta["final_url"] = r.url
        if r.status_code != 200:
            meta["fetch_error"] = f"HTTP {r.status_code}"
            return None, meta
        return r.text, meta
    except Exception as exc:  # noqa: BLE001 - report, never swallow
        meta["fetch_error"] = f"{type(exc).__name__}: {exc}"
        return None, meta


def fetch_rendered(url: str) -> tuple[str | None, dict]:
    """Render with a headless browser. Needed for JS-only sites (React/Next shells)."""
    meta = {"fetch_status": None, "fetch_error": "", "x_robots_tag": "", "rendered": True}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        meta["fetch_error"] = f"playwright unavailable: {exc}"
        return None, meta
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(user_agent=UA, viewport={"width": 1440, "height": 900})
            resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
            meta["fetch_status"] = resp.status if resp else None
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass  # trackers/chat widgets can keep the network busy indefinitely
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()
        return html, meta
    except Exception as exc:  # noqa: BLE001 - report, never swallow
        meta["fetch_error"] = f"{type(exc).__name__}: {exc}"
        return None, meta


def main_content_soup(soup: BeautifulSoup) -> BeautifulSoup:
    """Return a copy of the soup with template furniture removed."""
    body = BeautifulSoup(str(soup), "html.parser")
    for tag in body(STRIP_TAGS):
        tag.decompose()
    for name in ["nav", "header", "footer", "aside"]:
        for tag in body.find_all(name):
            tag.decompose()
    for role in STRIP_ROLES:
        for tag in body.find_all(attrs={"role": role}):
            tag.decompose()
    # Common template-furniture class hooks across WP / builder themes.
    for pat in ["site-header", "site-footer", "main-nav", "menu-", "breadcrumb",
                "cookie", "skip-link", "off-canvas", "mobile-menu"]:
        for tag in body.find_all(class_=re.compile(pat, re.I)):
            tag.decompose()
    main = body.find("main") or body.find("article") or body
    return main


def strip_widgets(main: BeautifulSoup) -> BeautifulSoup:
    """Remove site-wide widget blocks so the core copy count reflects page content.

    Guarded by size: a matching element is only removed when it holds a minority of
    the page's words. Without that guard a page wrapper whose class happens to match
    (a builder's "...-modal-wrap", "...-widget-area") takes the whole page with it.
    """
    core = BeautifulSoup(str(main), "html.parser")
    total = len(core.get_text(" ", strip=True).split()) or 1
    max_share = 0.35

    for pat in WIDGET_CLASS_PATTERNS:
        for attr in ("class", "id"):
            for tag in core.find_all(attrs={attr: re.compile(pat, re.I)}):
                if not tag.parent:  # already detached by an earlier pass
                    continue
                share = len(tag.get_text(" ", strip=True).split()) / total
                if share <= max_share:
                    tag.decompose()
    # Drop a heading that opens a widget block plus everything up to the next heading.
    for h in core.find_all(["h2", "h3"]):
        label = h.get_text(" ", strip=True).lower()
        if any(re.search(p, label) for p in WIDGET_HEADING_PATTERNS):
            for sib in list(h.find_next_siblings()):
                if sib.name in ("h2", "h3"):
                    break
                sib.decompose()
            h.decompose()
    return core


NON_COPY_SECTION_PATTERNS = [
    r"review", r"testimonial", r"what (our|their) (customers|clients)",
    r"recent post", r"latest (post|news|article)", r"from (our|the) blog",
    r"related (post|article)", r"coupon", r"special offer", r"current special",
    r"savings club", r"save big",
]


def section_breakdown(core: BeautifulSoup) -> list[dict]:
    """Split main content into H2 sections with per-section word counts.

    Gives 'section depth' directly, and lets non-copy blocks (reviews carousels,
    blog feeds) be excluded from the copy-length figure by name rather than by a
    blunt class-name match.
    """
    h2s = core.find_all("h2")
    sections: list[dict] = []
    if not h2s:
        return sections
    for i, h in enumerate(h2s):
        label = text_of(h)
        stop = h2s[i + 1] if i + 1 < len(h2s) else None
        words = 0
        for node in h.next_elements:
            if stop is not None and node is stop:
                break
            if getattr(node, "name", None) is None and str(node).strip():
                words += len(str(node).split())
        is_copy = not any(re.search(p, label, re.I)
                          for p in NON_COPY_SECTION_PATTERNS)
        sections.append({"h2": label, "words": words, "is_copy": is_copy})
    return sections


def text_of(node) -> str:
    txt = node.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", txt)


def extract_schema(soup: BeautifulSoup) -> tuple[list[str], dict]:
    types: list[str] = []
    props: dict = {}

    def walk(obj):
        if isinstance(obj, dict):
            t = obj.get("@type")
            if isinstance(t, str):
                types.append(t)
            elif isinstance(t, list):
                types.extend([str(x) for x in t])
            for key in ("areaServed", "serviceType", "priceRange", "aggregateRating",
                        "review", "address", "telephone", "openingHours",
                        "openingHoursSpecification", "hasOfferCatalog", "provider",
                        "mainEntity", "offers"):
                if key in obj and key not in props:
                    props[key] = True
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for tag in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
        raw = tag.string or tag.get_text() or ""
        try:
            walk(json.loads(raw))
        except Exception:
            # Some sites emit multiple concatenated objects or trailing commas.
            for chunk in re.findall(r"\{.*?\}(?=\s*[,\]]|\s*$)", raw, re.S):
                try:
                    walk(json.loads(chunk))
                except Exception:
                    continue
    return sorted(set(types)), props


def count_terms(text_lower: str, terms: list[str]) -> list[str]:
    return [t for t in terms if t in text_lower]


RENDER_THRESHOLD = 150  # below this, assume a JS-only shell and re-fetch rendered


def extract(url: str, brand: str, role: str, serp_note: str, outdir: Path,
            force_render: bool = False) -> dict:
    if force_render:
        html, meta = fetch_rendered(url)
    else:
        html, meta = fetch(url)
    row: dict = {
        "brand": brand,
        "url": url,
        "role": role,
        "serp_note": serp_note,
        "rendered": bool(meta.get("rendered")),
        **{k: v for k, v in meta.items() if k in ("fetch_status", "fetch_error", "x_robots_tag")},
    }
    if not html:
        return row

    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else ""
    md = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    meta_desc = md.get("content", "").strip() if md else ""
    robots = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    robots_val = robots.get("content", "") if robots else ""
    canon = soup.find("link", attrs={"rel": re.compile("canonical", re.I)})
    canonical = canon.get("href", "") if canon else ""

    schema_types, schema_props = extract_schema(soup)

    main = main_content_soup(soup)
    core = strip_widgets(main)
    h1s = [text_of(h) for h in main.find_all("h1")] or [text_of(h) for h in soup.find_all("h1")]
    h2s = [text_of(h) for h in core.find_all("h2")]
    h3s = [text_of(h) for h in core.find_all("h3")]
    h2s_raw = [text_of(h) for h in main.find_all("h2")]
    h4s = [text_of(h) for h in core.find_all("h4")]
    # forms are stripped from the copy soup, so count them on the original document
    form_count = len(soup.find_all("form"))
    body_text = text_of(main)
    core_text = text_of(core)
    low = body_text.lower()
    words = len(body_text.split())
    core_words = len(core_text.split())

    # A near-empty extraction means the HTML was a JS shell. Retry with a real browser.
    if core_words < RENDER_THRESHOLD and not force_render:
        print("         (thin HTML, re-fetching rendered)")
        return extract(url, brand, role, serp_note, outdir, force_render=True)

    sections = section_breakdown(core)
    copy_sections = [s for s in sections if s["is_copy"]]
    noncopy_words = sum(s["words"] for s in sections if not s["is_copy"])
    copy_words = max(core_words - noncopy_words, 0)

    h1 = h1s[0] if h1s else ""
    # FAQ detection: schema FAQPage, or heading block that reads as Q&A.
    q_headings = [h for h in (h2s + h3s) if h.strip().endswith("?")]
    faq_heading = any(re.search(r"\bfaq|frequently asked", h, re.I) for h in (h2s + h3s))
    faq_present = bool("FAQPage" in schema_types or faq_heading or len(q_headings) >= 3)

    tel_links = soup.select('a[href^="tel:"]')
    phones = sorted({re.sub(r"[^0-9]", "", a.get("href", "").replace("tel:", ""))[-10:]
                     for a in tel_links if a.get("href")})
    internal, external = 0, 0
    host = urlparse(url).netloc.replace("www.", "")
    for a in main.find_all("a", href=True):
        h = a["href"]
        if h.startswith("#") or h.startswith("tel:") or h.startswith("mailto:"):
            continue
        nh = urlparse(h).netloc.replace("www.", "")
        if not nh or nh == host:
            internal += 1
        else:
            external += 1

    prices = sorted(set(re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?", body_text)))
    row.update({
        "title": title,
        "title_len": len(title),
        "city_in_title": CITY in title.lower(),
        "meta_desc": meta_desc,
        "meta_desc_len": len(meta_desc),
        "city_in_meta": CITY in meta_desc.lower(),
        "meta_robots": robots_val,
        "canonical": canonical,
        "h1": h1,
        "city_in_h1": CITY in h1.lower(),
        "h1_count": len(h1s),
        "h2_count": len(h2s),
        "h2_count_copy": len(copy_sections),
        "h2_count_raw": len(h2s_raw),
        "h3_count": len(h3s),
        "h4_count": len(h4s),
        "form_count": form_count,
        "local_condition_mentions": sum(low.count(t)
                                        for t in LOCAL_CONDITION_TERMS),
        "local_condition_terms": "|".join(count_terms(low,
                                                      LOCAL_CONDITION_TERMS)),
        "word_count_source": "rendered browser" if force_render else "page source",
        "word_count": copy_words,
        "word_count_incl_widgets": core_words,
        "word_count_raw": words,
        "noncopy_section_words": noncopy_words,
        "city_mentions": low.count(CITY),
        "faq_present": faq_present,
        "faq_question_count": len(q_headings),
        "schema_types": "|".join(schema_types),
        "schema_type_count": len(schema_types),
        "schema_has_service": any(t in schema_types for t in ("Service", "HomeAndConstructionBusiness", "HVACBusiness")),
        "schema_has_localbusiness": any("LocalBusiness" in t or t in ("HVACBusiness", "Plumber", "Electrician") for t in schema_types),
        "schema_has_faqpage": "FAQPage" in schema_types,
        "schema_has_aggregaterating": "aggregateRating" in schema_props,
        "schema_has_areaserved": "areaServed" in schema_props,
        "schema_has_offers": "offers" in schema_props or "hasOfferCatalog" in schema_props,
        "internal_links": internal,
        "external_links": external,
        "images": len(main.find_all("img")),
        "tel_link_count": len(tel_links),
        "unique_phones": "|".join(p for p in phones if len(p) == 10),
        "price_mentions": len(prices),
        "prices_found": "|".join(prices[:12]),
        "mentions_financing": bool(re.search(r"financ|payment plan|monthly payment", low)),
        "mentions_membership": bool(re.search(r"membership|club|maintenance plan|service plan", low)),
        "mentions_emergency_247": bool(re.search(r"24/7|24-7|24 hour|emergency", low)),
        "mentions_sameday": bool(re.search(r"same[- ]day", low)),
        "mentions_warranty": bool(re.search(r"warrant|guarantee", low)),
        "mentions_upfront_pricing": bool(re.search(r"upfront pric|up-front pric|flat rate|no hidden|transparent pric", low)),
        "mentions_free_estimate": bool(re.search(r"free estimate|free quote|no cost estimate", low)),
        "equipment_brands": "|".join(count_terms(low, EQUIPMENT_BRANDS)),
        "equipment_brand_count": len(count_terms(low, EQUIPMENT_BRANDS)),
        "symptom_terms": "|".join(count_terms(low, SYMPTOM_TERMS)),
        "symptom_term_count": len(count_terms(low, SYMPTOM_TERMS)),
        "trust_terms": "|".join(count_terms(low, TRUST_TERMS)),
        "trust_term_count": len(count_terms(low, TRUST_TERMS)),
        "h2_outline": " || ".join(h2s[:40]),
        "h3_outline": " || ".join(h3s[:40]),
    })

    slug = slugify(url)
    (outdir / "raw").mkdir(parents=True, exist_ok=True)
    (outdir / "pages").mkdir(parents=True, exist_ok=True)
    (outdir / "raw" / f"{slug}.txt").write_text(core_text, encoding="utf-8")
    (outdir / "raw" / f"{slug}.full.txt").write_text(body_text, encoding="utf-8")
    (outdir / "pages" / f"{slug}.json").write_text(
        json.dumps({**row, "h2s": h2s, "h3s": h3s, "sections": sections},
                   indent=2),
        encoding="utf-8",
    )
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    targets = json.loads(Path(args.config).read_text(encoding="utf-8"))

    # A sister property may appear as the client's own page (role starts "client"),
    # never as a competitor or benchmark. Anything else is a config error.
    for t in targets:
        host = urlparse(t["url"]).netloc.replace("www.", "").lower()
        if host in SISTER_DOMAINS and not t.get("role", "").startswith("client"):
            raise SystemExit(
                f"ABORT: {host} is a sister property and cannot be analysed as a "
                f"competitor (entry: {t['brand']}, role: {t.get('role')}). "
                f"Remove it from the config or set role to 'client-*'."
            )

    rows = []
    for t in targets:
        print(f"[fetch] {t['brand']:<28} {t['url']}")
        row = extract(t["url"], t["brand"], t.get("role", "competitor"),
                      t.get("serp_note", ""), outdir)
        if row.get("fetch_error"):
            print(f"         !! {row['fetch_error']}")
        else:
            print(f"         words={row.get('word_count')} h2={row.get('h2_count')} "
                  f"schema={row.get('schema_type_count')}")
        rows.append(row)

    df = pd.DataFrame(rows)
    csv_path = outdir / "competitor_matrix.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n[done] {len(df)} pages -> {csv_path}")
    failed = df[df["fetch_error"].astype(str).str.len() > 0] if "fetch_error" in df else df.iloc[0:0]
    if len(failed):
        print(f"[warn] {len(failed)} page(s) failed to fetch:")
        for _, r in failed.iterrows():
            print(f"   - {r['brand']}: {r['fetch_error']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
