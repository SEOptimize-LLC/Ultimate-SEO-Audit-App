"""Task 1.2 - Technical Health Sweep.

Fills the four checklist rows that have a data source, plus the findings log.

  2  Algorithm-update watch      status.search.google.com/incidents.json
  5  Crawl of money pages        status / redirect chain / noindex / canonical
  6  Sitemap URL count           sitemap index + children
  7  Core Web Vitals field data  PageSpeed Insights (CrUX)

Rows 1 (Manual Actions), 3 (Page Indexing) and 4 (Crawl Stats) are left for the
owner: Search Console exposes none of them through any API. Confirmed against
the API surface, which offers only searchanalytics, sitemaps, sites,
urlInspection and urlTestingTools.

    python scripts/task_1_2.py superior
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import urllib.parse
import urllib.error
import urllib.request
import random
import time
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (compatible; SEOAudit/1.0)"}
INCIDENTS = "https://status.search.google.com/incidents.json"
PSI = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# CrUX "good" thresholds. Anything worse is a real failure, not a lab warning:
# the task says field data only, so lab scores are deliberately ignored.
CWV_GOOD = {"LARGEST_CONTENTFUL_PAINT_MS": 2500,
            "INTERACTION_TO_NEXT_PAINT": 200,
            "CUMULATIVE_LAYOUT_SHIFT_SCORE": 10}


def _get(url: str, timeout: int = 30, tries: int = 4) -> str:
    """Fetch, retrying transient throttling.

    Client sites rate-limit. Snow returned 429 on 20 of 54 page requests and
    then on the sitemap itself, and both were written up as client findings.
    A 429 is our problem, so it is retried here rather than surfaced upward.
    """
    import random
    import time
    for attempt in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout
            ).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == tries - 1:
                raise
            time.sleep(2 ** attempt + random.random())
    raise RuntimeError("unreachable")


# --- check 2 ----------------------------------------------------------------

def algorithm_updates(since: dt.date) -> list[dict]:
    """Confirmed Google updates that began on or after `since`.

    Google's own status feed, not a third-party roundup, so the dates are
    authoritative and there is nothing to second-guess.
    """
    out = []
    for e in json.loads(_get(INCIDENTS)):
        begin = str(e.get("begin", ""))[:10]
        if not begin or dt.date.fromisoformat(begin) < since:
            continue
        out.append({"name": e.get("external_desc", "").strip(),
                    "begin": begin, "end": str(e.get("end", ""))[:10],
                    "status": e.get("most_recent_update", {}).get("status", "")})
    return sorted(out, key=lambda d: d["begin"], reverse=True)


# --- check 5 ----------------------------------------------------------------

def crawl(urls: list[str], timeout: int = 20, workers: int = 3) -> list[dict]:
    """Status, redirect chain, noindex and canonical for each URL.

    This is the Screaming Frog list-mode crawl expressed as the checks the task
    actually asks for. Redirect chains are counted by following manually, since
    a chain of two or more is itself the finding.
    """
    def one(u: str) -> dict:
        rec = {"url": u, "status": None, "chain": 0, "final": u,
               "noindex": False, "canonical": None, "error": None,
               "throttled": False, "textlen": None, "texthash": None}
        try:
            cur, seen, tries = u, [], 0
            while len(seen) < 6:
                req = urllib.request.Request(cur, headers=UA)
                op = urllib.request.build_opener(NoRedirect)
                try:
                    r = op.open(req, timeout=timeout)
                    rec["status"] = r.status
                    body = r.read().decode("utf-8", "replace")
                    rec["final"] = cur
                    m = re.search(r'rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', body, re.I)
                    rec["canonical"] = m.group(1) if m else None
                    rb = re.search(r'name=["\']robots["\'][^>]*content=["\']([^"\']+)', body, re.I)
                    rec["noindex"] = bool(rb and "noindex" in rb.group(1).lower())
                    # Visible text length in the RAW response. On a JS-rendered
                    # site this is near zero for every route, which is how a
                    # client-side app is detected without guessing at framework
                    # names. Arsenal returns a 52-character shell on all 40
                    # money pages, so every canonical and noindex check below
                    # is reading an empty document.
                    body_txt = re.sub(r"<[^>]+>", " ",
                                      re.sub(r"(?is)<(script|style).*?</>", " ", body))
                    flat = " ".join(body_txt.split())
                    rec["textlen"] = len(flat)
                    rec["texthash"] = hashlib.md5(flat.encode()).hexdigest()[:12]
                    break
                except urllib.error.HTTPError as he:
                    if he.code in (301, 302, 307, 308) and he.headers.get("Location"):
                        seen.append(cur)
                        cur = urllib.parse.urljoin(cur, he.headers["Location"])
                        rec["chain"] = len(seen)
                        rec["status"] = he.code
                        continue
                    if he.code in (429, 503) and tries < 3:
                        tries += 1
                        time.sleep(2 ** tries + random.random())
                        continue            # our rate limit, not their bug
                    if he.code in (429, 503):
                        rec["throttled"] = True
                    rec["status"] = he.code
                    break
        except Exception as e:
            rec["error"] = e.__class__.__name__
        return rec

    # 3 workers, not 8. Every URL in a run hits ONE domain, and Shopify
    # rate-limited at 8: Snow returned 429 on 20 of 54 URLs, all of which were
    # written up as client findings. Politeness here is correctness, not manners.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, urls))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


# --- check 6 ----------------------------------------------------------------

def sitemap_counts(sitemap_url: str) -> tuple[int, list[tuple[str, int]], list[str]]:
    """URL counts from a sitemap, whether it is an index or a flat urlset.

    Both shapes are common and they are not interchangeable. A `<sitemapindex>`
    lists child sitemaps to fetch; a `<urlset>` IS the URL list. Treating a flat
    urlset as an index makes every page look like an empty child sitemap, which
    on Cudio produced 234 false "empty sitemap" findings.
    """
    body = _get(sitemap_url)
    locs = re.findall(r"<loc>(.*?)</loc>", body)

    if "<sitemapindex" not in body[:2000]:
        return len(locs), [(sitemap_url, len(locs))], locs

    def one(u: str) -> tuple[str, list[str] | None]:
        try:
            return u, re.findall(r"<loc>(.*?)</loc>", _get(u))
        except Exception:
            return u, None          # None = unreachable, distinct from empty

    with ThreadPoolExecutor(max_workers=3) as pool:
        got = list(pool.map(one, locs))
    per = [(u, len(v) if v is not None else -1) for u, v in got]
    allurls = [x for _, v in got if v for x in v]
    return sum(n for _, n in per if n > 0), sorted(per, key=lambda t: -t[1]), allurls


# --- check 7 ----------------------------------------------------------------

def cwv(url: str, key: str, strategy: str = "mobile") -> dict | None:
    q = urllib.parse.urlencode({"url": url, "strategy": strategy, "key": key})
    try:
        d = json.loads(_get(f"{PSI}?{q}", timeout=90))
    except Exception:
        return None
    le = d.get("loadingExperience", {})
    if not le.get("metrics"):
        return None                      # no field data: too little CrUX traffic
    # origin_fallback means CrUX had too little traffic for THIS URL and
    # returned site-wide numbers instead. Reporting that as a per-template
    # measurement invents three readings out of one.
    out = {"overall": le.get("overall_category"),
           "origin_fallback": bool(le.get("origin_fallback"))}
    for k, v in le["metrics"].items():
        out[k] = {"p75": v["percentile"], "cat": v["category"]}
    return out
