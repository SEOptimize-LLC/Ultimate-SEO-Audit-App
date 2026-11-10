"""Per-URL indexation audit via the Search Console URL Inspection API.

Answers what the Sitemaps API cannot. Its `indexed` field is deprecated and
returns nonsense (23 against 359 submitted on Superior), so the only honest
source for "is this URL actually in Google" is Google's own verdict per URL.

Feeds 1.2 check 3 (Page Indexing vs last month) and check 6 (indexed count).

Results are cached per client per month, so a re-run costs no quota and so that
next month can diff against this month: a URL that was "Submitted and indexed"
and is now "Crawled - currently not indexed" is the signal check 3 asks for, and
nothing else surfaces it. It reads as quality only after the 1.2 render check finds
the page renders clean (run_index_checks.render_gate, added 2026-11-10).

    python scripts/index_audit.py superior
    python scripts/index_audit.py superior --limit 50
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import threading
import time
import urllib.request
from collections import Counter
from pathlib import Path

import google.auth
import yaml
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; SEOAudit/1.0)"}

# Google's documented ceilings: 2,000 URLs/day and 600/minute per property.
# Neither binds here. A single inspect call costs ~7s of pure latency, so
# throughput is set by how many are in flight, and 8 workers lands near 68/min.
# Retries exist for transient SSL and timeout noise, which is frequent enough
# that an early no-retry run lost 9 of 12 URLs.
RETRIES = 3
WORKERS = int(os.environ.get("INDEX_WORKERS", "8"))


def creds():
    c, _ = google.auth.default(scopes=SCOPES)
    return c


_local = threading.local()


def client():
    """One Search Console client per thread.

    googleapiclient builds each service around a single httplib2.Http, and
    httplib2.Http is NOT thread-safe. Sharing one service across a thread pool
    interleaves writes on the same socket, which shows up as sporadic failures
    under light concurrency and as a permanent hang under heavier concurrency.
    An early 4-worker run lost 9 of 12 URLs this way and a later one stopped
    dead. Per-thread clients are the documented fix; credentials are shared
    safely because refresh is internally locked.
    """
    if not hasattr(_local, "sc"):
        _local.sc = build("searchconsole", "v1", credentials=creds(),
                          cache_discovery=False)
    return _local.sc


def sitemap_urls(sc, site, exclude=None):
    """Every URL across every sitemap registered in Search Console.

    Shape detection is delegated to task_1_2.sitemap_counts, which already knows
    that a `<sitemapindex>` lists child sitemaps while a `<urlset>` IS the URL
    list. The earlier version here assumed index-shape unconditionally and
    returned 0 URLs on Arsenal, whose sitemap is flat: it fetched each page as
    though it were a child sitemap and found no <loc> in the HTML. That is the
    same defect that wrote 337 false "empty sitemap" findings in task 1.2.

    All registered sitemaps are read, not only the first. Superior registers
    several and sm[0] is merely whichever Search Console happens to return first.
    """
    from task_1_2 import sitemap_counts

    ex = [x.lower() for x in (exclude or [])]
    out = []
    for entry in sc.sitemaps().list(siteUrl=site).execute().get("sitemap", []):
        try:
            _, _, urls = sitemap_counts(entry["path"])
        except Exception:
            continue                    # unreachable sitemap: 1.2 reports it
        out += urls
    seen = sorted(dict.fromkeys(u.strip() for u in out if u.strip()))
    return [u for u in seen if not any(x in u.lower() for x in ex)]


def resolve(url: str, timeout: float = 15.0) -> str:
    """Follow redirects and return the URL that actually serves the page.

    NEVER INSPECT A URL THAT DOES NOT RETURN 200. A sitemap that still lists
    a pre-restructure address, or lists the unslashed form of a path the site
    normalises, makes Search Console answer about the address we asked for
    rather than the page. That comes back "URL is unknown to Google" or "Page
    with redirect" and reads as a de-indexed page, while the destination is
    indexed perfectly well. The count is then wrong in the direction that
    causes work: somebody goes hunting for an indexation problem that does
    not exist.

    A site that refuses automated requests gets its original URL back
    unchanged. A page we could not reach is not evidence of a redirect, and
    guessing here would trade one wrong answer for another.
    """
    req = urllib.request.Request(url, method="HEAD", headers={
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status == 200 and r.url:
                return r.url
    except Exception:
        pass
    return url


def inspect_one(site: str, url: str) -> dict:
    """One URL, with backoff. Transient SSL/timeout noise is common and retryable."""
    for attempt in range(RETRIES):
        try:
            r = client().urlInspection().index().inspect(
                body={"inspectionUrl": url, "siteUrl": site}).execute()
            i = r["inspectionResult"]["indexStatusResult"]
            return {"url": url, "state": i.get("coverageState", "?"),
                    "verdict": i.get("verdict", ""),
                    "lastCrawl": (i.get("lastCrawlTime") or "")[:10],
                    "robots": i.get("robotsTxtState", ""),
                    "fetch": i.get("pageFetchState", ""),
                    "canonical": i.get("googleCanonical", "")}
        except Exception as e:
            if attempt == RETRIES - 1:
                return {"url": url, "state": f"ERROR {e.__class__.__name__}",
                        "verdict": "", "lastCrawl": "", "robots": "",
                        "fetch": "", "canonical": ""}
            time.sleep((2 ** attempt) + random.random())
    return {}


def audit(slug: str, cfg: dict, month: str, limit: int | None = None) -> dict:
    sc = client()
    site = cfg["gsc_property"]
    sm = sc.sitemaps().list(siteUrl=site).execute().get("sitemap", [])
    if not sm:
        raise RuntimeError(f"{slug}: no sitemap registered in Search Console")

    urls = sitemap_urls(sc, site, (cfg.get("crawl") or {}).get("exclude"))

    # Scope to what the owner defined as this site: money pages, posts and the
    # homepage. Cudio's /jobs/ and Snow's /pages/ sit in the sitemap but are
    # neither, and auditing them inflated every not-indexed count with URLs
    # outside the brief. The full sitemap total still reaches check 6 from
    # run_1_2, so nothing is hidden, it is just no longer counted as a problem.
    try:
        from crawl_targets import scope_urls
        keep = scope_urls(sm[0]["path"], site, cfg)
        scoped = [u for u in urls if u.rstrip("/") in keep]
        if scoped:
            urls = scoped
    except Exception:
        pass                       # unreachable sitemap: audit what we have

    if limit:
        urls = urls[:limit]

    # A single inspect call takes ~7s regardless of load, so this is latency-
    # bound, not throughput-bound: serial would put Snow's 1,058 URLs at two
    # hours. 8 concurrent calls is ~68/min against a documented ceiling of 600/
    # min per property, so Google is not the constraint. The earlier 4-worker
    # attempt that failed 9 of 12 URLs predates inspect_one's retry.
    from concurrent.futures import ThreadPoolExecutor

    # Resolve BEFORE inspecting. A HEAD request is cheap next to a ~7s
    # inspect call, and asking Google about an address that redirects
    # produces a not-indexed verdict about the redirect rather than about
    # the page.
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        landed = list(pool.map(resolve, urls))
    moved = [(u, v) for u, v in zip(urls, landed)
             if v.rstrip("/") != u.rstrip("/")]
    if moved:
        print(f"    {len(moved)} sitemap URL(s) redirect; inspecting where "
              f"they land", flush=True)
        for u, v in moved[:5]:
            print(f"      {u}", flush=True)
            print(f"        -> {v}", flush=True)
    was = dict(zip(landed, urls))
    urls = list(dict.fromkeys(landed))

    rows = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for n, rec in enumerate(pool.map(lambda u: inspect_one(site, u), urls), 1):
            src = was.get(rec.get("url"), "")
            if src and src.rstrip("/") != str(rec.get("url", "")).rstrip("/"):
                rec["sitemap_url"] = src
            rows.append(rec)
            if n % 100 == 0:
                print(f"    {n}/{len(urls)}", flush=True)

    out = {"client": slug, "month": month, "site": site,
           "sitemaps": [e["path"] for e in sm], "checked": len(rows),
           "counts": dict(Counter(r["state"] for r in rows)),
           "crawl": crawl_recency(rows), "rows": rows}

    dest = Path(cfg["folder"]) / "Monthly SEO Workbook" / month
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "index_audit.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def crawl_recency(rows, today=None):
    """Crawl-frequency proxy for check 4, derived from per-URL lastCrawlTime.

    Crawl Stats itself has NO API. It is a Search Console UI report, and nothing
    in the v1 surface exposes Googlebot request volume, the response-code mix or
    host status. What URL Inspection does return is the date Google last crawled
    each URL, so across the sampled set that yields a recency distribution plus a
    count of pages Google could not fetch.

    This measures how RECENTLY pages were crawled, not how MANY requests
    Googlebot made. The distinction is real and the sheet states it plainly: a
    month-over-month swell in the 90d+ bucket means coverage is going stale,
    which is the spike check 4 watches for, but it is not the UI's number and
    must never be labelled as though it were.
    """
    today = today or dt.date.today()
    buckets = {"0-7d": 0, "8-30d": 0, "31-90d": 0, "90d+": 0, "never": 0}
    ages = []
    for r in rows:
        d = r.get("lastCrawl") or ""
        try:
            age = (today - dt.date.fromisoformat(d)).days
        except ValueError:
            buckets["never"] += 1       # never crawled, or an unparseable date
            continue
        ages.append(age)
        key = ("0-7d" if age <= 7 else "8-30d" if age <= 30
               else "31-90d" if age <= 90 else "90d+")
        buckets[key] += 1
    ages.sort()
    # PAGE_FETCH_STATE_UNSPECIFIED is "not fetched yet", not "fetch failed".
    # It is what a URL Google has never discovered returns, so counting it as a
    # failure invents a server problem out of a discovery one and double-counts
    # the very same URLs already reported as unknown to Google.
    bad = Counter(r.get("fetch", "") for r in rows
                  if r.get("fetch") not in
                  ("", None, "SUCCESSFUL", "PAGE_FETCH_STATE_UNSPECIFIED"))
    return {"buckets": buckets,
            "median_age_days": ages[len(ages) // 2] if ages else None,
            "fetch_failures": dict(bad)}


def diff_previous(cfg: dict, month: str) -> list[tuple[str, str, str]]:
    """URLs whose state changed since the previous monthly audit."""
    base = Path(cfg["folder"]) / "Monthly SEO Workbook"
    months = sorted(p.name for p in base.glob("*") if (p / "index_audit.json").exists())
    if month not in months or months.index(month) == 0:
        return []
    prev = json.loads((base / months[months.index(month) - 1] / "index_audit.json")
                      .read_text(encoding="utf-8"))
    old = {r["url"]: r["state"] for r in prev["rows"]}
    cur = json.loads((base / month / "index_audit.json").read_text(encoding="utf-8"))
    return [(r["url"], old[r["url"]], r["state"]) for r in cur["rows"]
            if r["url"] in old and old[r["url"]] != r["state"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--month", default=dt.date.today().strftime("%Y-%m"))
    a = ap.parse_args()
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    res = audit(a.client, reg[a.client], a.month, a.limit)
    print(f"\n{res['checked']} URLs checked for {a.client}")
    for state, n in sorted(res["counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:>5}  {state}")
    c4 = res["crawl"]
    print("\n  crawl recency (median {}d): ".format(c4["median_age_days"])
          + "  ".join("{} {}".format(k, v) for k, v in c4["buckets"].items()))
    if c4["fetch_failures"]:
        print("  fetch failures: {}".format(c4["fetch_failures"]))

    changed = diff_previous(reg[a.client], a.month)
    if changed:
        print("\n  {} state changes vs previous month".format(len(changed)))
        for u, o, c in changed[:20]:
            print("  CHANGED  {} -> {}  {}".format(o, c, u))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
