"""Site tech-stack fingerprint generator.

Given a domain, fetch the homepage HTML and detect:
  - CMS (WordPress, Shopify, Webflow, Squarespace, custom)
  - Page builder (Elementor, Divi, WP Bakery, Gutenberg, Beaver Builder, hand-coded)
  - Theme name (wp-content/themes/<theme-name>/)
  - Schema.org types present
  - Analytics (GA4, GTM, Meta Pixel, etc.)
  - Review widgets (Google reviews, Trustpilot, Yelp embed, etc.)
  - Hosting hints (WP Engine, Cloudflare, Kinsta, etc.)

Writes Clients/<client-name>/site_fingerprint.json.

Usage:
    python scripts/fingerprint_site.py --client Superior --url https://superiorwaterandair.com/
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


def fetch(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20, allow_redirects=True)
    r.raise_for_status()
    return r.text


def detect_cms(html: str, headers: dict) -> str:
    h = html.lower()
    if "/wp-content/" in h or "/wp-includes/" in h:
        return "WordPress"
    if "cdn.shopify.com" in h or "shopify-section" in h:
        return "Shopify"
    if "webflow.com" in h or "data-wf-page" in h:
        return "Webflow"
    if "squarespace.com" in h or "squarespace-cdn.com" in h:
        return "Squarespace"
    if "wix.com" in h or "wixstatic.com" in h:
        return "Wix"
    if "duda.co" in h or "dudamobile.com" in h:
        return "Duda"
    if "_next/static" in h:
        return "Next.js (likely headless)"
    return "Unknown / Custom"


def detect_page_builder(html: str) -> dict:
    """Returns {builder, evidence, body_uses_builder}."""
    h = html.lower()
    builders = []

    elementor_count = h.count("elementor-")
    if elementor_count > 0:
        builders.append({
            "name": "Elementor",
            "evidence_count": elementor_count,
            "body_use": elementor_count > 50,
        })
    if "et_pb_" in h or "divi" in h:
        builders.append({
            "name": "Divi",
            "evidence_count": h.count("et_pb_"),
            "body_use": h.count("et_pb_") > 20,
        })
    if "vc_row" in h or "wpb_" in h or "js_composer" in h:
        builders.append({
            "name": "WP Bakery (Visual Composer)",
            "evidence_count": h.count("vc_row") + h.count("wpb_"),
            "body_use": True,
        })
    if "fl-builder" in h or "fl-row" in h:
        builders.append({
            "name": "Beaver Builder",
            "evidence_count": h.count("fl-row"),
            "body_use": True,
        })
    if "wp-block-" in h:
        builders.append({
            "name": "Gutenberg (WordPress block editor)",
            "evidence_count": h.count("wp-block-"),
            "body_use": h.count("wp-block-") > 5,
        })
    if "oxygen-" in h and "wp-content" in h:
        builders.append({
            "name": "Oxygen Builder",
            "evidence_count": h.count("oxygen-"),
            "body_use": True,
        })

    if not builders:
        return {"builders": [], "primary": "Hand-coded theme / no detected page builder"}

    builders.sort(key=lambda b: b["evidence_count"], reverse=True)
    return {
        "builders": builders,
        "primary": builders[0]["name"] if builders[0]["body_use"] else f"{builders[0]['name']} (limited use)",
    }


def detect_theme(html: str) -> dict:
    """Find wp-content/themes/<name>/ patterns. Returns parent + child if both."""
    matches = re.findall(r"/wp-content/themes/([a-z0-9_-]+)/", html, re.IGNORECASE)
    if not matches:
        return {"theme_name": None, "child_theme": None}

    counts: dict[str, int] = {}
    for m in matches:
        counts[m] = counts.get(m, 0) + 1
    sorted_themes = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "all_detected_themes": [{"name": n, "asset_references": c} for n, c in sorted_themes],
        "primary_theme": sorted_themes[0][0],
        "child_theme": sorted_themes[1][0] if len(sorted_themes) > 1 else None,
    }


def detect_analytics(html: str) -> list[str]:
    found = []
    if re.search(r"G-[A-Z0-9]{8,}", html) or "googletagmanager.com/gtag/js" in html:
        found.append("Google Analytics 4")
    if "googletagmanager.com/gtm.js" in html or re.search(r"GTM-[A-Z0-9]{6,}", html):
        found.append("Google Tag Manager")
    if "connect.facebook.net" in html or "fbq(" in html:
        found.append("Meta (Facebook) Pixel")
    if "static.hotjar.com" in html or "hjid" in html.lower():
        found.append("Hotjar")
    if "clarity.ms" in html:
        found.append("Microsoft Clarity")
    if "linkedin.com/insights" in html or "_linkedin_data_partner" in html:
        found.append("LinkedIn Insight Tag")
    return found


def detect_schema_types(html: str) -> list[str]:
    """Extract @type values from JSON-LD scripts."""
    types: set[str] = set()
    json_ld_blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    for block in json_ld_blocks:
        for match in re.findall(r'"@type"\s*:\s*"([^"]+)"', block):
            types.add(match)
        for match in re.findall(r'"@type"\s*:\s*\[([^\]]+)\]', block):
            for t in re.findall(r'"([^"]+)"', match):
                types.add(t)
    return sorted(types)


def detect_review_widgets(html: str) -> list[str]:
    h = html.lower()
    found = []
    if "googleusercontent.com" in h and ("review" in h or "rating" in h):
        found.append("Google Reviews (likely)")
    if "trustpilot.com" in h:
        found.append("Trustpilot")
    if "birdeye" in h:
        found.append("BirdEye")
    if "podium.com" in h:
        found.append("Podium")
    if "nicejob" in h:
        found.append("NiceJob")
    if "shopperapproved" in h:
        found.append("Shopper Approved")
    return found


def detect_hosting_hints(html: str, headers: dict) -> list[str]:
    found = []
    server = headers.get("server", "").lower()
    powered_by = headers.get("x-powered-by", "").lower()
    cf_ray = headers.get("cf-ray")
    if cf_ray or "cloudflare" in server:
        found.append("Cloudflare (CDN/proxy)")
    if "wpengine" in headers.get("x-powered-by", "").lower() or "wpengine" in html.lower():
        found.append("WP Engine")
    if "kinsta" in server or "kinsta" in headers.get("x-kinsta-cache", "").lower():
        found.append("Kinsta")
    if "siteground" in server:
        found.append("SiteGround")
    if "fly.io" in server:
        found.append("Fly.io")
    if powered_by:
        found.append(f"X-Powered-By: {powered_by}")
    return found


def detect_spa(html: str) -> dict:
    """Detect single-page-app shells where the homepage is a thin JS bootstrap."""
    h = html.lower()
    is_thin = len(html) < 30000
    has_root_div = bool(re.search(r'<div\s+id=["\'](root|app|__next|___gatsby|svelte)["\']\s*>', h))
    has_react = "react" in h or "reactdom" in h or 'data-reactroot' in h
    has_vite = "/@vite/" in h or '"vite"' in h or "src=\"/src/main." in h
    has_next = "_next/static" in h or "__next_data__" in h
    has_nuxt = "__nuxt" in h or "nuxt" in h
    has_gatsby = "___gatsby" in h or "gatsby" in h
    has_astro = "astro-island" in h or "astro:" in h
    has_svelte = "svelte-" in h
    has_vue = "v-cloak" in h or "vue.global" in h or "vue.runtime" in h
    has_angular = "ng-version" in h or "ng-app" in h

    framework = None
    if has_next:
        framework = "Next.js"
    elif has_nuxt:
        framework = "Nuxt"
    elif has_gatsby:
        framework = "Gatsby"
    elif has_astro:
        framework = "Astro"
    elif has_vite:
        framework = "Vite (React/Vue/Svelte)"
    elif has_svelte:
        framework = "Svelte / SvelteKit"
    elif has_vue:
        framework = "Vue"
    elif has_angular:
        framework = "Angular"
    elif has_react:
        framework = "React (build tool unknown)"

    is_spa = is_thin and has_root_div
    return {
        "is_spa_shell": is_spa,
        "framework": framework,
        "thin_html": is_thin,
        "has_root_div": has_root_div,
        "warning": (
            "Homepage HTML is a thin SPA shell — page builder/theme detection "
            "from this URL alone is unreliable. Inner pages may have different "
            "rendering. Recommend re-fingerprinting with a rendered HTML "
            "snapshot (Playwright/Puppeteer) for accurate detection."
        ) if is_spa else None,
    }


def detect_other_signals(html: str) -> dict:
    h = html.lower()
    return {
        "has_yoast_seo": "yoast" in h,
        "has_rankmath": "rankmath" in h or "rank-math" in h,
        "has_aioseo": "aioseo" in h or "all-in-one-seo" in h,
        "uses_amp": "<html amp" in h or 'rel="amphtml"' in h,
        "has_woocommerce": "woocommerce" in h,
        "has_elementor_pro": "elementor-pro" in h,
        "uses_jquery": "jquery" in h,
        "has_recaptcha": "recaptcha" in h,
        "has_cookie_banner": any(x in h for x in ["cookieconsent", "cookielaw", "onetrust", "cookiebot"]),
    }


def build_fingerprint(client: str, url: str, save: bool = True) -> dict:
    print(f"[1/2] Fetching {url} ...")
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20, allow_redirects=True)
    r.raise_for_status()
    html = r.text
    headers = {k.lower(): v for k, v in r.headers.items()}

    print(f"[2/2] Detecting tech stack ...")
    fp = {
        "client": client,
        "url": url,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "http_status": r.status_code,
        "final_url": r.url,
        "cms": detect_cms(html, headers),
        "spa": detect_spa(html),
        "page_builder": detect_page_builder(html),
        "theme": detect_theme(html),
        "analytics": detect_analytics(html),
        "schema_types": detect_schema_types(html),
        "review_widgets": detect_review_widgets(html),
        "hosting": detect_hosting_hints(html, headers),
        "other": detect_other_signals(html),
        "html_size_bytes": len(html),
    }

    if save:
        out_dir = PROJECT_ROOT / "Clients" / client
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "site_fingerprint.json"
        out_path.write_text(json.dumps(fp, indent=2), encoding="utf-8")
        print(f"Saved: {out_path}")

    return fp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True, help="Client folder name")
    parser.add_argument("--url", required=True, help="Homepage URL")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    fp = build_fingerprint(args.client, args.url, save=not args.no_save)
    print(json.dumps(fp, indent=2))


if __name__ == "__main__":
    main()
