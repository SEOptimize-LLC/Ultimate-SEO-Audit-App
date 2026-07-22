"""
Live verification pass for SameDay's 49 indexed blog survivors.

Per-URL extracts:
  - HTTP status
  - Schema datePublished, dateModified (from JSON-LD blocks)
  - On-page "Last Updated" / "Updated" text (visible to users)
  - Author byline (text + URL if present)
  - Word count of main article body
  - Outbound internal links FROM the post body (target URLs only,
    same-domain), so we can flag links pointing to known 404s or
    to-be-noindexed posts later.

Output: Clients/SameDay/Full SEO Audit/_survivors_49_verification.csv
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
URL_FILE = ROOT / "Clients" / "SameDay" / "Full SEO Audit" / "_survivors_49_urls.txt"
OUT_FILE = ROOT / "Clients" / "SameDay" / "Full SEO Audit" / "_survivors_49_verification.csv"
LINK_FILE = ROOT / "Clients" / "SameDay" / "Full SEO Audit" / "_survivors_49_outbound_links.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SEOAuditBot/1.0; "
        "+contact: team@seoptimizellc.com)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

DOMAIN = "samedayutah.com"

UPDATED_TEXT_PATTERNS = [
    re.compile(r"last\s*updated[:\s]*([A-Za-z0-9, ]+)", re.I),
    re.compile(r"updated[:\s]*on\s+([A-Za-z0-9, ]+)", re.I),
    re.compile(r"updated[:\s]+([A-Za-z]+ \d{1,2}[, ]+\d{4})", re.I),
]


def extract_jsonld(soup: BeautifulSoup) -> list[dict]:
    blocks: list[dict] = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                # Some plugins emit a JSON array or comma-separated objects
                data = json.loads("[" + raw.strip().rstrip(",") + "]")
            except Exception:
                continue
        if isinstance(data, list):
            blocks.extend([d for d in data if isinstance(d, dict)])
        elif isinstance(data, dict):
            graph = data.get("@graph")
            if isinstance(graph, list):
                blocks.extend([d for d in graph if isinstance(d, dict)])
            else:
                blocks.append(data)
    return blocks


def find_article_dates(blocks: list[dict]) -> tuple[str | None, str | None, str | None]:
    """Return (datePublished, dateModified, schema_type)."""
    candidates = []
    for b in blocks:
        t = b.get("@type")
        if isinstance(t, list):
            t_norm = ",".join(t)
        else:
            t_norm = str(t or "")
        if not t_norm:
            continue
        if any(
            x in t_norm
            for x in ("Article", "BlogPosting", "NewsArticle", "WebPage")
        ):
            candidates.append((t_norm, b))
    # Prefer Article/BlogPosting over WebPage
    for t_norm, b in candidates:
        if "Article" in t_norm or "BlogPosting" in t_norm:
            return b.get("datePublished"), b.get("dateModified"), t_norm
    if candidates:
        t_norm, b = candidates[0]
        return b.get("datePublished"), b.get("dateModified"), t_norm
    return None, None, None


def find_author(blocks: list[dict], soup: BeautifulSoup) -> str:
    for b in blocks:
        author = b.get("author")
        if isinstance(author, dict):
            n = author.get("name")
            if n:
                return str(n)
        if isinstance(author, list) and author:
            first = author[0]
            if isinstance(first, dict) and first.get("name"):
                return str(first["name"])
    # Fallback to common WP byline classes
    for sel in [".entry-author", ".author-name", ".byline a", "[rel=author]"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return ""


def find_visible_updated(soup: BeautifulSoup) -> str:
    text = soup.get_text(" ", strip=True)
    for p in UPDATED_TEXT_PATTERNS:
        m = p.search(text)
        if m:
            # Trim to a reasonable substring
            return m.group(0).strip()[:80]
    return ""


def find_main_body(soup: BeautifulSoup):
    # WordPress + Elementor common containers
    for sel in [
        "article .entry-content",
        ".elementor-widget-theme-post-content",
        "article",
        "main",
    ]:
        el = soup.select_one(sel)
        if el:
            return el
    return soup.body or soup


def word_count(el) -> int:
    txt = el.get_text(" ", strip=True)
    return len([w for w in re.split(r"\s+", txt) if w])


def outbound_internal_links(body_el, base_url: str) -> list[str]:
    out = []
    for a in body_el.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        if href.startswith("/"):
            full = f"https://{DOMAIN}{href}"
        elif href.startswith("http"):
            try:
                p = urlparse(href)
            except Exception:
                continue
            if DOMAIN not in (p.netloc or ""):
                continue
            full = href
        else:
            continue
        out.append(full)
    return out


def fetch(url: str) -> dict:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
    except Exception as exc:
        return {"url": url, "status": -1, "error": str(exc)}
    if r.status_code != 200:
        return {"url": url, "status": r.status_code, "final_url": r.url, "error": ""}

    soup = BeautifulSoup(r.text, "html.parser")
    blocks = extract_jsonld(soup)
    pub, mod, schema_type = find_article_dates(blocks)
    author = find_author(blocks, soup)
    visible_updated = find_visible_updated(soup)
    body = find_main_body(soup)
    wc = word_count(body)
    out_links = outbound_internal_links(body, url)
    return {
        "url": url,
        "status": r.status_code,
        "final_url": r.url,
        "schema_type": schema_type or "",
        "datePublished": pub or "",
        "dateModified": mod or "",
        "dates_match": "YES" if (pub and mod and pub == mod) else "NO" if (pub and mod) else "",
        "author": author,
        "visible_updated_text": visible_updated,
        "word_count_main": wc,
        "outbound_internal_links": len(out_links),
        "_links": out_links,  # not written to main CSV, used for link CSV
        "error": "",
    }


def main():
    urls = [u.strip() for u in URL_FILE.read_text().splitlines() if u.strip()]
    print(f"Verifying {len(urls)} URLs ...", flush=True)

    rows = []
    link_rows = []
    for i, u in enumerate(urls, 1):
        print(f"[{i:02d}/{len(urls)}] {u}", flush=True)
        rec = fetch(u)
        for tgt in rec.pop("_links", []):
            link_rows.append({"source": u, "target": tgt})
        rows.append(rec)
        time.sleep(0.6)  # polite

    # Main verification CSV
    main_cols = [
        "url", "status", "final_url", "schema_type",
        "datePublished", "dateModified", "dates_match",
        "author", "visible_updated_text",
        "word_count_main", "outbound_internal_links",
        "error",
    ]
    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=main_cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in main_cols})

    # Outbound internal links CSV
    with LINK_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source", "target"])
        w.writeheader()
        for r in link_rows:
            w.writerow(r)

    print(f"\nWrote: {OUT_FILE}")
    print(f"Wrote: {LINK_FILE}")
    print(f"Verified rows: {len(rows)}, internal link edges: {len(link_rows)}")


if __name__ == "__main__":
    sys.exit(main())
