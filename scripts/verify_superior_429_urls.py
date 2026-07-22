"""
Live verification of the 135 Screaming Frog 429 (rate-limited) URLs from
Superior Water & Air's sitemap.

These URLs were marked "non-indexable" in the SF crawl only because SF got
rate-limited and couldn't fetch them — the actual indexability is unknown.
This script does live HTTP HEAD requests with a polite rate limit to figure
out which are 200 (truly indexable, sitemap is fine), 404 (broken, need to be
410'd), 301 (redirecting, shouldn't be in sitemap), or other.

Output:
    Clients/Superior/Full SEO Audit/superior_429_verification_results.json
        Raw per-URL verification data
    Clients/Superior/Full SEO Audit/superior_429_verification_summary.txt
        Human-readable summary by status code

Politeness:
    - HEAD requests only (no body downloaded)
    - 0.5s sleep between requests = ~120 req/min — well under rate-limit floors
    - Custom user-agent identifies us as a bot doing diagnostics
    - 10s timeout per request
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
import urllib.request
import urllib.error
from collections import Counter

import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
SITEMAP_FILE = os.path.join(ROOT, "Clients/Superior/superior_sitemaps_all.xlsx")
OUT_JSON = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_429_verification_results.json"
)
OUT_TXT = os.path.join(
    ROOT, "Clients/Superior/Full SEO Audit/superior_429_verification_summary.txt"
)

USER_AGENT = "Mozilla/5.0 (compatible; SEOptimizeAuditor/1.0; +https://seoptimizellc.com)"
DELAY_SECONDS = 0.5
TIMEOUT = 10


def load_429_urls() -> list[str]:
    """Pull every URL from the sitemap export that returned 429."""
    wb = openpyxl.load_workbook(SITEMAP_FILE, read_only=True, data_only=True)
    ws = wb["1 - All"]
    urls = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        if row[2] == 429:
            urls.append(row[0])
    wb.close()
    return urls


def head_check(url: str) -> dict:
    """Do a HEAD request and return what we learn.

    Returns dict with: status, final_url, error (if any).
    """
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", USER_AGENT)

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return {
                "status": resp.status,
                "final_url": resp.url,
                "error": None,
            }
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "final_url": e.url if hasattr(e, "url") else url,
            "error": None,
        }
    except urllib.error.URLError as e:
        return {
            "status": None,
            "final_url": url,
            "error": f"URLError: {e.reason}",
        }
    except Exception as e:
        return {
            "status": None,
            "final_url": url,
            "error": f"{type(e).__name__}: {e}",
        }


def main() -> None:
    urls = load_429_urls()
    print(f"Loaded {len(urls)} URLs that previously returned 429.")
    print(f"Estimated time: {len(urls) * DELAY_SECONDS / 60:.1f} minutes")
    print()

    results = []
    for i, url in enumerate(urls, start=1):
        info = head_check(url)
        results.append({"url": url, **info})
        # Status indicator every 10 URLs
        if i % 10 == 0 or i == len(urls):
            counts = Counter(r["status"] for r in results)
            print(f"  [{i:>3}/{len(urls)}] checked. Status so far: {dict(counts)}")
        time.sleep(DELAY_SECONDS)

    # Save raw results
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Generate summary
    counts = Counter(r["status"] for r in results)
    error_count = sum(1 for r in results if r["error"])
    image_count = sum(1 for r in results if "/wp-content/uploads/" in r["url"])

    lines = []
    lines.append("=" * 70)
    lines.append("SUPERIOR WATER & AIR — 429 URL Live Verification Results")
    lines.append("=" * 70)
    lines.append(f"URLs checked: {len(urls)}")
    lines.append(f"Image URLs (/wp-content/uploads/): {image_count}")
    lines.append(f"Other URLs: {len(urls) - image_count}")
    lines.append("")
    lines.append("Status code breakdown (live):")
    for status, n in sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0]))):
        lines.append(f"  {str(status):>6} : {n}")
    if error_count:
        lines.append(f"  Errors  : {error_count}")
    lines.append("")

    # Group by category
    truly_404 = [r for r in results if r["status"] == 404]
    truly_200 = [r for r in results if r["status"] == 200]
    truly_301 = [r for r in results if r["status"] in (301, 302, 307, 308)]
    rate_limited_again = [r for r in results if r["status"] == 429]
    other = [
        r for r in results
        if r["status"] not in (200, 301, 302, 307, 308, 404, 429)
    ]

    lines.append(f"Truly 404 (broken — should be 410'd): {len(truly_404)}")
    for r in truly_404[:30]:
        lines.append(f"  {r['url']}")
    if len(truly_404) > 30:
        lines.append(f"  ... and {len(truly_404) - 30} more")
    lines.append("")

    lines.append(f"Truly 200 (working — should stay in sitemap): {len(truly_200)}")
    for r in truly_200[:30]:
        lines.append(f"  {r['url']}")
    if len(truly_200) > 30:
        lines.append(f"  ... and {len(truly_200) - 30} more")
    lines.append("")

    lines.append(f"Redirecting (3xx — should NOT be in sitemap): {len(truly_301)}")
    for r in truly_301[:30]:
        lines.append(f"  {r['url']}  -> {r['final_url']}")
    if len(truly_301) > 30:
        lines.append(f"  ... and {len(truly_301) - 30} more")
    lines.append("")

    if rate_limited_again:
        lines.append(f"Still rate-limited (429): {len(rate_limited_again)}")
        for r in rate_limited_again[:10]:
            lines.append(f"  {r['url']}")
        lines.append("")

    if other:
        lines.append(f"Other status codes: {len(other)}")
        for r in other[:15]:
            lines.append(f"  [{r['status']}] {r['url']}")
        lines.append("")

    summary = "\n".join(lines)
    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(summary)

    print()
    print(summary)
    print()
    print(f"Saved JSON: {OUT_JSON}")
    print(f"Saved TXT:  {OUT_TXT}")


if __name__ == "__main__":
    main()
