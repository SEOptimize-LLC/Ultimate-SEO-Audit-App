"""Live-verify EVERY URL in the audit-issues set - no sampling.

    python scripts/verify_issue_urls.py [YYYY-MM]

Owner rule, 2026-08-19: an August audit does not lean on Google's June crawl
memory. Every affected URL is fetched TODAY and the workbook carries the live
state (status, robots meta, canonical) next to Google's record, so the two
can never be confused again and every contradiction is surfaced.

Fetches are direct HTTP (concurrent, ordinary browser UA). Sites that refuse
our address (EW's WAF) are marked and retried through DataForSEO. Output:
Clients/<folder>/monthly_plan/<month>-live-verification.json per client.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

MONTH = sys.argv[1] if len(sys.argv) > 1 else "2026-08"
ROOT = Path(__file__).resolve().parent.parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

SLUGS = ["superior", "sameday", "beehive", "comfort", "arsenal", "cudio",
         "snow", "educationwalkthrough"]

ROBOTS_RE = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)', re.I)
ROBOTS_RE2 = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']robots["\']', re.I)
CANON_RE = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', re.I)
CANON_RE2 = re.compile(
    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', re.I)


def fetch(url: str) -> dict:
    """One live check: final status, redirect target, robots meta, canonical."""
    out = {"url": url, "status": None, "redirected_to": "", "robots": "",
           "canonical": "", "note": ""}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            out["status"] = r.status
            final = r.geturl()
            if final.rstrip("/") != url.rstrip("/"):
                out["redirected_to"] = final
            html = r.read(400_000).decode("utf-8", "replace")
        m = ROBOTS_RE.search(html) or ROBOTS_RE2.search(html)
        out["robots"] = m.group(1).strip() if m else "(no robots meta)"
        m = CANON_RE.search(html) or CANON_RE2.search(html)
        out["canonical"] = m.group(1).strip() if m else ""
    except urllib.error.HTTPError as e:
        out["status"] = e.code
    except Exception as e:
        out["status"] = e.__class__.__name__
        out["note"] = "fetch failed from our address"
    return out


def dfs_fetch(url: str) -> dict:
    """Fallback through DataForSEO for sites that refuse our address."""
    import base64
    lo = pw = None
    for ln in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if ln.startswith("DATAFORSEO_LOGIN="):
            lo = ln.split("=", 1)[1].strip()
        if ln.startswith("DATAFORSEO_PASSWORD="):
            pw = ln.split("=", 1)[1].strip()
    tok = base64.b64encode(f"{lo}:{pw}".encode()).decode()
    body = json.dumps([{"url": url, "enable_javascript": False}]).encode()
    req = urllib.request.Request(
        "https://api.dataforseo.com/v3/on_page/instant_pages", data=body,
        headers={"Authorization": "Basic " + tok,
                 "Content-Type": "application/json"})
    out = {"url": url, "status": None, "redirected_to": "", "robots": "",
           "canonical": "", "note": "via DataForSEO (our address refused)"}
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read().decode("utf-8", "replace"))
        it = d["tasks"][0]["result"][0]["items"][0]
        meta = it.get("meta") or {}
        out["status"] = it.get("status_code")
        out["canonical"] = meta.get("canonical") or ""
        # instant_pages exposes robots directives under checks/meta when set;
        # absence of a flag means no noindex was seen.
        noindex = bool((it.get("checks") or {}).get("is_noindex"))
        out["robots"] = "noindex (per DFS check)" if noindex else \
            "(no noindex per DFS check)"
    except Exception as e:
        out["status"] = e.__class__.__name__
        out["note"] = "DFS fetch also failed"
    return out


def issue_urls(slug: str, reg: dict) -> list[str]:
    """The same URL set the issues workbook lists (in-scope states + extras)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_issues_workbook as B
    urls = []
    ja = ROOT / reg[slug]["folder"] / "Monthly SEO Workbook" / MONTH / "index_audit.json"
    if ja.exists():
        data = json.loads(ja.read_text(encoding="utf-8"))
        for r in data.get("rows", []):
            if str(r.get("inScope")) != "True":
                continue
            if B.lane_for(str(r.get("state") or ""), slug):
                urls.append(r["url"])
    for url, _issue, _lane in B.EXTRA.get(slug, []):
        if url.startswith("http"):
            urls.append(url)
    return sorted(set(urls))


def main() -> None:
    reg = yaml.safe_load((ROOT / "clients/registry.yaml").read_text(encoding="utf-8"))
    grand = 0
    for slug in SLUGS:
        urls = issue_urls(slug, reg)
        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(fetch, urls))
        # Retry refused/failed fetches through DFS, serially (API etiquette).
        for i, r in enumerate(results):
            if r["status"] in (401, 403, 429) or not isinstance(r["status"], int):
                results[i] = dfs_fetch(r["url"])
        d = ROOT / reg[slug]["folder"] / "monthly_plan"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{MONTH}-live-verification.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
        ok200 = sum(1 for r in results if r["status"] == 200)
        noidx = [r for r in results if "noindex" in str(r["robots"]).lower()
                 and "no noindex" not in str(r["robots"]).lower()]
        gone = [r for r in results if r["status"] in (404, 410)]
        redir = [r for r in results if isinstance(r["status"], int)
                 and r["redirected_to"]]
        fail = [r for r in results if not isinstance(r["status"], int)]
        print(f"{slug:<20} {len(results):>3} checked | 200: {ok200} | "
              f"noindex live: {len(noidx)} | 404/410: {len(gone)} | "
              f"redirects: {len(redir)} | unreachable: {len(fail)}", flush=True)
        for r in noidx:
            print(f"    NOINDEX LIVE: {r['url']}  robots={r['robots']}", flush=True)
        for r in gone:
            print(f"    GONE {r['status']}: {r['url']}", flush=True)
        grand += len(results)
    print(f"\n{grand} URLs live-verified {MONTH}")


if __name__ == "__main__":
    main()
