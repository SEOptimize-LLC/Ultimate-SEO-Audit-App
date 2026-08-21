"""Positive structured-data detection for one or more URLs.

    python scripts/check_rich_results.py <url> [<url> ...] [--dfs]

Fetches the page and reports every JSON-LD @type found, plus required-field
checks for the rich-result types Google actually shows (Article, Breadcrumb,
Product, FAQ*, HowTo*, LocalBusiness, Organization, VideoObject, Review).

Fetch legs, in order:
  1. local Playwright (RENDERED - catches JS-injected schema)  [default]
  2. DataForSEO instant_pages + raw_html retrieval             [--dfs, for
     sites that block our IP, e.g. educationwalkthrough.com]

Exists because of the 2026-08-21 incident: "no rich results" was written from
a tool output that lacked the field, while Google's Rich Results Test showed
Article + Breadcrumbs valid. The URL Inspection API omits richResultsResult
even when rich results exist - NEVER use its absence as evidence. This script
reports what is actually in the page. The Rich Results Test UI remains the
authoritative eligibility verdict; this is the scriptable 95%.

* FAQPage/HowTo earn no rich results for most sites since 2023 - reported
  here as present/absent but never to be recommended as a rich-result play.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REQUIRED = {  # minimal required-property checks per Google's docs
    "Article": ["headline"],
    "NewsArticle": ["headline"],
    "BlogPosting": ["headline"],
    "BreadcrumbList": ["itemListElement"],
    "Product": ["name"],
    "FAQPage": ["mainEntity"],
    "HowTo": ["name", "step"],
    "LocalBusiness": ["name", "address"],
    "Organization": ["name"],
    "VideoObject": ["name", "thumbnailUrl", "uploadDate"],
    "Review": ["itemReviewed", "reviewRating"],
}


def fetch_playwright(url: str) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        html = page.content()
        b.close()
    return html


def fetch_dfs(url: str) -> str:
    sys.path.insert(0, str(Path(__file__).parent))
    import gap_collect
    tok = gap_collect.creds()

    def call(path, payload):
        req = urllib.request.Request(
            "https://api.dataforseo.com/v3/" + path,
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Basic " + tok,
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())

    d = call("on_page/instant_pages",
             [{"url": url, "enable_javascript": True, "store_raw_html": True}])
    tid = d["tasks"][0]["id"]
    for wait in (5, 10, 20, 30):
        time.sleep(wait)
        d2 = call("on_page/raw_html", [{"id": tid, "url": url}])
        t = d2["tasks"][0]
        res = t.get("result") or []
        # NOTE: "items" here is a DICT {"html": ...}, not a list - assuming a
        # list is the bug that made retrieval look broken on 2026-08-20/21.
        items = res[0].get("items") if res and isinstance(res[0], dict) else None
        if isinstance(items, list):
            items = items[0] if items else None
        if isinstance(items, dict) and items.get("html"):
            return items["html"]
        print(f"  (raw_html not ready: {t.get('status_message')}; waited {wait}s)")
    raise RuntimeError("DFS raw_html retrieval failed - run the Rich Results "
                       "Test manually for this URL")


def walk_types(node, out):
    if isinstance(node, dict):
        t = node.get("@type")
        if t:
            for tt in (t if isinstance(t, list) else [t]):
                out.append((tt, node))
        for v in node.values():
            walk_types(v, out)
    elif isinstance(node, list):
        for v in node:
            walk_types(v, out)


def check(url: str, use_dfs: bool) -> None:
    print("=" * 72)
    print(url)
    html = fetch_dfs(url) if use_dfs else fetch_playwright(url)
    print(f"  fetched {len(html):,} bytes ({'DFS rendered' if use_dfs else 'Playwright rendered'})")
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.S | re.I)
    if not blocks:
        print("  NO JSON-LD blocks found in rendered HTML "
             "(microdata/RDFa not covered by this script - confirm with the "
             "Rich Results Test before claiming absence)")
        return
    found = []
    for b in blocks:
        try:
            walk_types(json.loads(b.strip()), found)
        except Exception:
            print("  !! unparseable JSON-LD block (syntax error - would fail "
                  "validation)")
    by_type = {}
    for t, node in found:
        by_type.setdefault(t, node)
    print(f"  {len(blocks)} JSON-LD block(s), types: {sorted(by_type)}")
    for t, node in sorted(by_type.items()):
        req = REQUIRED.get(t)
        if not req:
            continue
        missing = [p for p in req if not node.get(p)]
        verdict = "OK" if not missing else f"MISSING required: {missing}"
        print(f"  [{t}] {verdict}")


if __name__ == "__main__":
    urls = [a for a in sys.argv[1:] if not a.startswith("--")]
    for u in urls:
        check(u, "--dfs" in sys.argv)
