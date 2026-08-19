"""Run task 1.2 for one client or all, and write the sheet.

task_1_2.py holds the checks; this holds the assembly, the severity rules and
the writing.

    python scripts/run_1_2.py all
    python scripts/run_1_2.py beehive
"""

from __future__ import annotations

import datetime as dt
import os
from collections import Counter
import re
import sys
from pathlib import Path

import google.auth
import yaml
from dotenv import load_dotenv
from googleapiclient.discovery import build

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheets_io as S      # noqa: E402
import task_1_2 as K       # noqa: E402
import crawl_targets as CT # noqa: E402

TAB = "1.2 Health Sweep"
MARKS = {"c2": "2. Algorithm-update", "c5": "5. Screaming Frog",
         "c6": "6. Sitemap URL count", "c7": "7. CWV field data",
         "bsec": "B. Findings log"}
# The three that are actually Core Web Vitals. TTFB is not one, and calling it
# a CWV failure sends someone optimising the wrong thing.
CORE = ("LARGEST_CONTENTFUL_PAINT_MS", "INTERACTION_TO_NEXT_PAINT",
        "CUMULATIVE_LAYOUT_SHIFT_SCORE")


def sc_client():
    c, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    return build("searchconsole", "v1", credentials=c, cache_discovery=False)


def templates(money: list[str], posts: list[str], site: str) -> list[tuple[str, str]]:
    """One representative URL per template: home, a money page, a post.

    Taken from the resolved lists rather than matched against hardcoded path
    patterns, which named no template on any SaaS or e-commerce client.
    """
    out = [("Home", site)]
    svc = next((u for u in money if u.rstrip("/") != site.rstrip("/")), None)
    if svc:
        out.append(("Money page", svc))
    if posts:
        out.append(("Post", posts[0]))
    return out


def build_findings(per, errs, warns, sitemap_path, crawled, cw, top5) -> list[list]:
    F: list[list] = []
    for u, n in per:
        if n == 0:
            F.append([f"{u.split('/')[-1]} is submitted in the sitemap index but contains 0 URLs",
                      u, "Watch", "2.1",
                      "Empty sitemap wastes a crawl request. Remove it or populate it."])
        elif n < 0:
            F.append([f"{u.split('/')[-1]} is listed in the sitemap index but could not be fetched",
                      u, "Fix This Month", "2.1",
                      "Googlebot will hit the same failure. Check it resolves."])
    if errs:
        F.append([f"Search Console reports {errs} sitemap error(s)", sitemap_path,
                  "Fix This Month", "2.1", "Detail is UI-only: GSC > Sitemaps."])
    # The API's `warnings` field is stale and must NOT become a finding. On EW
    # it reports 12 while the UI shows Success on every sitemap, and the same
    # object claims indexed=0 against 357 submitted. Same deprecated data as the
    # `indexed` field. Reported in the notes, never as an issue.
    for r in crawled:
        sev = "Blocker" if r["url"] in top5 else "Fix This Month"
        if r.get("throttled"):
            F.append(["Could not verify: the site rate-limited our crawler (HTTP 429)",
                      r["url"], "Watch", "-",
                      "OUR limitation, not a site fault. Re-run with lower concurrency "
                      "before treating this URL as unchecked."])
        elif r["error"]:
            F.append([f"Could not fetch ({r['error']})", r["url"], "Watch", "2.1",
                      "Transient or blocked. Re-check before acting."])
        elif r["status"] and r["status"] != 200 and not r.get("throttled"):
            F.append([f"Returns HTTP {r['status']}", r["url"], sev, "2.1",
                      "A top-5 money page not returning 200." if r["url"] in top5 else ""])
        if r["noindex"]:
            F.append(["Page carries a noindex directive", r["url"], "Blocker", "2.1",
                      "Removes the page from Google entirely."])
        if r["chain"] >= 2:
            F.append([f"{r['chain']}-hop redirect chain", r["url"], "Fix This Month", "2.1",
                      f"Resolves to {r['final']}. Collapse to a single hop."])
        if r["canonical"] and r["canonical"].rstrip("/") != r["final"].rstrip("/"):
            F.append(["Canonical points to a different URL", r["url"], "Fix This Month", "2.1",
                      f"Canonical: {r['canonical']}"])
    # When every template fell back to origin, there is ONE measurement, not
    # three. Report it once or the findings log repeats itself per template.
    origin_only = bool(cw) and all(d and d.get("origin_fallback") for _, d in cw.values())
    seen_ttfb = False
    for name, (u, d) in cw.items():
        if not d:
            continue
        if origin_only and seen_ttfb:
            break
        if origin_only:
            name, seen_ttfb = "Site-wide (origin)", True
        for m in CORE:
            if d.get(m, {}).get("cat") == "POOR":
                F.append([f"{name} template: {m} failing in field data ({d[m]['p75']})", u,
                          "Fix This Month", "2.1", "Real CrUX failure, not a lab score."])
        t = d.get("EXPERIMENTAL_TIME_TO_FIRST_BYTE")
        if t and t["cat"] != "FAST":
            F.append([f"{name} template: TTFB {t['p75']}ms ({t['cat']})", u, "Watch", "2.1",
                      "Not a Core Web Vital. Server response work, not a CWV fix."])
    if not F:
        F.append(["No issues found this sweep", "-", "Watch", "-",
                  "Logged deliberately: a clean sweep is a valid outcome, a blank tab is not."])
    return F


def run(slug: str, cfg: dict, since: dt.date, key: str) -> dict:
    site, sid = cfg["gsc_property"], cfg["sheet_id"]

    ups = K.algorithm_updates(since)
    sm = sc_client().sitemaps().list(siteUrl=site).execute().get("sitemap", [])
    if not sm:
        raise RuntimeError("no sitemap registered in Search Console")
    # A registered sitemap that does not resolve is itself the finding, and a
    # loud one: Search Console is submitting a URL Googlebot cannot fetch.
    sitemap_error = None
    try:
        total, per, allurls = K.sitemap_counts(sm[0]["path"])
    except Exception as e:
        code = getattr(e, "code", e.__class__.__name__)
        sitemap_error = f"HTTP {code}" if str(code).isdigit() else str(code)
        total, per, allurls = 0, [], []
    subm = (sm[0].get("contents") or [{}])[0].get("submitted", "?")
    errs, warns = int(sm[0].get("errors", 0)), int(sm[0].get("warnings", 0))

    # Targets come from the sitemap, not from 1.1's click-ranked list. Money
    # pages are an owner-supplied allowlist where one exists, otherwise derived
    # from the page sitemap. Posts are the most recent by <lastmod>.
    if sitemap_error:
        # No sitemap means no target list. Fall back to the pages we know earn
        # clicks, from 1.1 section C, so the crawl still runs and the client is
        # not silently skipped.
        p11 = S.find_rows(sid, "1.1 Data Snapshot", {"c": "Page URL"})
        top = [r[0] for r in S.read(sid, f"'1.1 Data Snapshot'!A{p11['c']+1}:A{p11['c']+10}")
               if r and str(r[0]).startswith("http")]
        posts, sel = [], {"money_source": "1.1 top landing pages (no sitemap)",
                          "post_source": "none - no sitemap", "newest": "", "oldest_taken": ""}
    else:
        top, posts, sel = CT.select(sm[0]["path"], site, cfg)
    targets = list(dict.fromkeys(top + posts))
    crawled = K.crawl(targets)
    cw = {n: (u, K.cwv(u, key)) for n, u in templates(top, posts, site)}

    F = build_findings(per, errs, warns, sm[0]["path"], crawled, cw, set(top[:5]))
    if sitemap_error:
        # 429 is us being throttled; 404 is the client's sitemap genuinely
        # missing. Reporting the first as the second sends a developer chasing
        # a fault that does not exist.
        if "429" in sitemap_error or "503" in sitemap_error:
            F.insert(0, ["Could not verify the sitemap: the site rate-limited our crawler "
                         f"({sitemap_error})", sm[0]["path"], "Watch", "-",
                         "OUR limitation, not a site fault. Re-run after a cooldown."])
        else:
            F.insert(0, [f"Registered sitemap does not resolve ({sitemap_error})",
                         sm[0]["path"], "Fix This Month", "2.1",
                         "Search Console is submitting a sitemap Googlebot cannot fetch. "
                         "Either fix the URL or resubmit the correct one."])

    p = S.find_rows(sid, TAB, MARKS)
    up_txt = ("; ".join(f"{u['name']} ({u['begin']} to {u['end'] or 'ongoing'})" for u in ups)
              if ups else "No confirmed Google update began in the period.")
    fallback = bool(cw) and all(d and d.get("origin_fallback") for _, d in cw.values())
    if fallback:
        d = next(d for _, d in cw.values() if d)
        cw_txt = ("ORIGIN-LEVEL ONLY: CrUX has too little traffic for per-URL data on this site, "
                  "so these are site-wide figures, not per-template. "
                  + ", ".join(f"{m.split('_')[0][:4]} {d[m]['p75']} {d[m]['cat']}"
                              for m in CORE if m in d))
    else:
        cw_txt = " | ".join(
            f"{n}: " + (", ".join(f"{m.split('_')[0][:4]} {d[m]['p75']} {d[m]['cat']}"
                                  for m in CORE if m in d)
                        + (" [origin fallback]" if d.get("origin_fallback") else "")
                        if d else "no field data")
            for n, (u, d) in cw.items())
    # A site whose raw responses carry no text is rendered client-side, and the
    # canonical and noindex checks below are then reading an empty shell. Saying
    # "0 flagged" without saying that turns a blind spot into a clean bill of
    # health. Threshold is deliberately low: a real page has hundreds of words.
    # Identical raw content across genuinely different URLs means the response
    # is an application shell and the real page is assembled by JavaScript. That
    # is a far better tell than any length threshold: Arsenal's shell is 1,458
    # characters, comfortably above "suspiciously short", yet byte-identical on
    # all 40 money pages. The canonical and noindex checks below are then
    # reading a document that contains neither, so reporting them as passed
    # would turn a blind spot into a clean bill of health.
    ok200 = [r for r in crawled if r["status"] == 200 and r.get("texthash")]
    common = Counter(r["texthash"] for r in ok200).most_common(1)
    spa = bool(common) and len(ok200) >= 3 and common[0][1] >= 0.8 * len(ok200)

    bad = [r for r in crawled
           if r["error"] or r.get("throttled")
           or (r["status"] or 200) != 200 or r["noindex"] or r["chain"] >= 2]
    cwv_fail = any(d and any(d.get(m, {}).get("cat") == "POOR" for m in CORE)
                   for _, d in cw.values())

    rows = {
        p["c2"]: ["Pass", f"Google Search Status feed. {up_txt}"],
        p["c5"]: ["Pass" if not bad else "Issue Found",
                  f"{len(crawled)} URLs crawled: {len(top)} money pages "
                  f"({sel.get('money_source','?')}) + {len(posts)} newest posts "
                  f"[{sel.get('post_source','?')}, {sel.get('oldest_taken','?')} to "
                  f"{sel.get('newest','?')}]. "
                  f"{len(crawled)-len(bad)} clean, {len(bad)} flagged."
                  + (f" JS-RENDERED SITE: {common[0][1]} of {len(ok200)} URLs returned "
                     "byte-identical raw HTML, so the real page is assembled by "
                     "JavaScript. Canonical and noindex could NOT be read and are "
                     "UNVERIFIED for this client, not passed. Confirm in a rendered "
                     "browser or via URL Inspection." if spa else "")],
        p["c6"]: ["Issue Found" if (sitemap_error or errs
                                    or any(n <= 0 for _, n in per)) else "Pass",
                  (f"SITEMAP UNREACHABLE ({sitemap_error}). " if sitemap_error else "")
                  + f"{total} URLs across {len(per)} sitemap(s) ("
                  + ", ".join(f"{u.split('/')[-1].replace('-sitemap.xml','')} {n}"
                              for u, n in per[:6])
                  + f"). GSC: submitted {subm}, errors {errs}. API also reports {warns} warnings "
                    f"and a stale indexed count, both unreliable - the GSC UI is authoritative. "
                    f"Real indexed count "
                    f"NOT available - the API's 'indexed' field is deprecated and unreliable."],
        p["c7"]: ["Issue Found" if cwv_fail else "Pass", f"Field data (CrUX), mobile. {cw_txt}"],
    }
    n = sum(S.write(sid, f"'{TAB}'!B{r}:C{r}", [[a, b]]).cells for r, (a, b) in rows.items())
    b0 = p["bsec"] + 2
    S.clear(sid, f"'{TAB}'!A{b0}:F{b0 + 80}")   # stale rows from a prior run
    body = [[i + 1] + f for i, f in enumerate(F)]
    n += S.write(sid, f"'{TAB}'!A{b0}:F{b0+len(body)-1}", body).cells
    return {"cells": n, "findings": len(F), "urls": total, "bad": len(bad),
            "money": len(top), "posts": len(posts),
            "src": sel.get("money_source", "?")}


def main() -> int:
    load_dotenv(".env")
    key = os.environ["PAGESPEED_API_KEY"]
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    # Superior was excluded here while its tab layout was drifting and breaking
    # hardcoded row numbers. find_rows anchors on heading text now, so it runs
    # like everything else. An "all" that silently skips a client is worse than
    # one that fails on it.
    todo = list(reg) if arg == "all" else [arg]
    since = dt.date(2026, 6, 1)
    print(f"{'client':<22}{'cells':>7}{'find':>6}{'money':>7}{'posts':>7}{'bad':>5}  source")
    print("-" * 66)
    for slug in todo:
        try:
            r = run(slug, reg[slug], since, key)
            print(f"{slug:<22}{r['cells']:>7}{r['findings']:>6}{r['money']:>7}"
                  f"{r['posts']:>7}{r['bad']:>5}  {r['src']}", flush=True)
        except Exception as e:
            print(f"{slug:<22}   FAIL  {e.__class__.__name__}: {str(e)[:44]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
