"""Fill task 1.2 checks 3 and 4 from the URL Inspection API, and close out 6.

Runs separately from run_1_2.py because it is separately triggerable and far
slower: it asks Google about every URL in the sitemap, one call each.

  3  Page Indexing vs last month   coverageState per URL, diffed against the
                                   previous cached month
  4  Crawl Stats - error spikes    lastCrawlTime recency + pageFetchState
  6  Sitemap URL count vs indexed  supplies the indexed half, which the
                                   Sitemaps API cannot (its `indexed` field is
                                   deprecated and returned 23 against 359 on
                                   Superior)

WHAT THIS IS NOT. The URL Inspection API has no history: it reports the state of
a URL right now and offers no way to ask what that state was in July. "vs last
month" therefore comes from OUR cache, not from Google, and the first run on a
client can only establish the baseline. Check 4 is likewise a proxy: Crawl Stats
proper is a UI-only report and no API exposes Googlebot request volume, the
response-code mix or host status. Crawl RECENCY is what we can measure, and the
sheet says so rather than implying we have the real thing.

    python scripts/run_index_checks.py arsenal
    python scripts/run_index_checks.py all --force
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import index_audit as IX   # noqa: E402
import sheets_io as S      # noqa: E402

TAB = "1.2 Health Sweep"
UA = "Mozilla/5.0 (compatible; SEOAudit/1.0)"

MARKS = {"c3": "3. Page Indexing", "c4": "4. Crawl Stats",
         "c6": "6. Sitemap URL count", "bsec": "B. Findings log"}

INDEXED = "Submitted and indexed"
CNI = "Crawled - currently not indexed"
DNI = "Discovered - currently not indexed"
UNKNOWN = "URL is unknown to Google"
DUP = "Duplicate without user-selected canonical"
DUP_OVERRIDE = "Duplicate, Google chose different canonical than user"

# States that mean the page is fine. "Alternate page with proper canonical tag"
# is a correctly canonicalised duplicate, which is the system working, not a
# fault. Everything NOT listed here and not handled by name below still gets a
# finding, so a state we have never seen can never be dropped in silence.
BENIGN = {INDEXED, "Alternate page with proper canonical tag"}

# Thresholds are fixed here rather than judged per client, so that the same
# input produces the same severity next month and for whoever runs it.
CNI_SHARE_WATCH = 0.10      # crawled-not-indexed as a share of the sitemap
DNI_SHARE_FLAG = 0.10       # discovered-not-indexed: crawl budget / linking
STALE_SHARE_WATCH = 0.30    # share not crawled in 90+ days
MAX_LISTED = 8              # URLs named per finding; the rest are counted
INDEXED_SHARE_OK = 0.80     # below this, check 6 is an issue, not a pass


def pct(n: int, d: int) -> str:
    return f"{(100.0 * n / d):.0f}%" if d else "n/a"


def urls_for(res: dict, state: str) -> list[str]:
    return [r["url"] for r in res["rows"] if r.get("state") == state]


def listing(urls: list[str]) -> str:
    """The URL cell for a finding: real URLs, never a pointer to a data file.

    Whoever works this row needs somewhere to click. "see index_audit.json"
    sends them to a file they cannot open from the sheet, and the project's
    report rules ban pointing a reader at another document besides.
    """
    shown = "; ".join(urls[:MAX_LISTED])
    rest = len(urls) - MAX_LISTED
    return shown + (f"; (+{rest} more of the same type)" if rest > 0 else "")


def live_noindex(urls: list[str], sample: int = 12) -> dict:
    """How many of these URLs actually carry noindex right now.

    URL Inspection reports what Google saw when it last crawled, which can be
    months old. SameDay's 98 "excluded by noindex" URLs were all crawled on
    2026-06-30, the day after its relaunch; every one of a 12-URL live sample
    now returns 200 with `follow, index` and 1,400 to 2,200 words. Reporting
    that record as "these pages carry a noindex tag" states a live fact from a
    stale source, and the two situations need opposite fixes: one is "remove the
    tag", the other is "the tag is already gone, get Google to re-crawl".
    """
    import random
    import re as _re
    import urllib.request
    from concurrent.futures import ThreadPoolExecutor

    rnd = random.Random(0)                      # fixed seed: same sample monthly
    pick = urls if len(urls) <= sample else rnd.sample(sorted(urls), sample)

    def one(u: str) -> bool | None:
        try:
            h = urllib.request.urlopen(
                urllib.request.Request(u, headers={"User-Agent": UA}),
                timeout=20).read().decode("utf-8", "replace")
        except Exception:
            return None
        m = _re.search(r"<meta[^>]*name=[\"']robots[\"'][^>]*content=[\"']([^\"']+)",
                       h, _re.I)
        return bool(m and "noindex" in m.group(1).lower())

    with ThreadPoolExecutor(max_workers=3) as pool:
        got = [x for x in pool.map(one, pick) if x is not None]
    return {"checked": len(got), "noindex": sum(got)}


def build_findings(res: dict, changed: list[tuple[str, str, str]],
                   prev: dict | None) -> list[list]:
    """Findings for section B. Severity is table-driven, never judged ad hoc."""
    F: list[list] = []
    counts = res["counts"]
    total = res["checked"]
    crawl = res["crawl"]

    # A page Google had indexed and no longer does is the loudest signal here:
    # it is lost coverage on a URL we already know is worth having. Nothing else
    # in the monthly sweep surfaces it.
    lost = [(u, o, c) for u, o, c in changed if o == INDEXED and c != INDEXED]
    if lost:
        F.append([f"{len(lost)} URL(s) dropped out of the index since last month",
                  listing([u for u, _, _ in lost]),
                  "Blocker", "1.8",
                  "These were 'Submitted and indexed' last month and are not now. "
                  "Google re-evaluated pages it had already accepted, which points at "
                  "content quality rather than a technical block. Confirm each in URL "
                  "Inspection, then route to the content-quality task."])

    gained = [(u, o, c) for u, o, c in changed if c == INDEXED and o != INDEXED]
    if gained:
        F.append([f"{len(gained)} URL(s) newly indexed since last month",
                  listing([u for u, _, _ in gained]),
                  "Watch", "-",
                  "Recorded as movement, not as a problem. Confirms Google is "
                  "still picking up new or re-submitted pages on this site."])

    cni = counts.get(CNI, 0)
    if cni:
        prev_cni = (prev or {}).get("counts", {}).get(CNI)
        delta = f" (was {prev_cni} last month)" if prev_cni is not None else " (baseline month)"
        sev = "Fix This Month" if cni / max(total, 1) >= CNI_SHARE_WATCH else "Watch"
        F.append([f"{cni} URL(s) Crawled - currently not indexed "
                  f"({pct(cni, total)} of sitemap){delta}",
                  listing(urls_for(res, CNI)), sev, "1.8",
                  "Google fetched these and chose not to index them. That is a quality "
                  "judgment, not a crawl failure, so resubmitting will not fix it. "
                  "Compare word count and uniqueness against pages that ARE indexed."])

    dni = counts.get(DNI, 0)
    if dni:
        sev = "Fix This Month" if dni / max(total, 1) >= DNI_SHARE_FLAG else "Watch"
        F.append([f"{dni} URL(s) Discovered - currently not indexed ({pct(dni, total)})",
                  listing(urls_for(res, DNI)), sev, "2.1",
                  "Google knows these URLs exist but has not crawled them. That is a "
                  "crawl-budget and internal-linking problem, not a content one: check "
                  "how many internal links point at each."])

    unknown = counts.get(UNKNOWN, 0)
    if unknown:
        F.append([f"{unknown} URL(s) unknown to Google despite being in the sitemap",
                  listing(urls_for(res, UNKNOWN)), "Fix This Month", "2.1",
                  "In the sitemap but never discovered. Usually means no internal link "
                  "path reaches them. Verify the sitemap is submitted and each URL is "
                  "linked from somewhere crawlable."])

    dup = counts.get(DUP, 0)
    if dup:
        F.append([f"{dup} URL(s) duplicate without a user-selected canonical",
                  listing(urls_for(res, DUP)), "Fix This Month", "2.1",
                  "Google found near-identical pages and picked the canonical itself, "
                  "which means the page kept may not be the one wanted. Set an explicit "
                  "rel=canonical on each so the choice is ours rather than inferred."])

    over = counts.get(DUP_OVERRIDE, 0)
    if over:
        F.append([f"{over} URL(s) where Google overrode our canonical",
                  listing(urls_for(res, DUP_OVERRIDE)), "Fix This Month", "2.1",
                  "A canonical IS set on these and Google ignored it, indexing a "
                  "different URL instead. That is a stronger signal than a missing "
                  "canonical: Google judged the pages near-identical and disagreed with "
                  "our choice. Either differentiate the content or consolidate to the "
                  "URL Google already picked."])

    # Only report a fetch failure when the coverage state does not already
    # explain it. Every non-benign state above produces its own finding, so a
    # URL whose state is "Redirect error" AND whose fetch state is
    # REDIRECT_ERROR is one problem, not two. Beehive shipped both rows for a
    # single URL before this filter existed.
    state_of = {r["url"]: r.get("state", "") for r in res["rows"]}
    for state, n in crawl["fetch_failures"].items():
        urls = [r["url"] for r in res["rows"]
                if r.get("fetch") == state and state_of.get(r["url"]) in BENIGN]
        if not urls:
            continue
        F.append([f"{len(urls)} URL(s) Google could not fetch ({state})",
                  listing(urls), "Fix This Month", "2.1",
                  "Google reports this page as otherwise fine yet could not fetch it, "
                  "so this is a server or robots problem rather than a content one. "
                  "It is the closest signal available to a Crawl Stats error spike."])

    stale = crawl["buckets"]["90d+"] + crawl["buckets"]["never"]
    if total and stale / total >= STALE_SHARE_WATCH:
        F.append([f"{stale} URL(s) ({pct(stale, total)}) not crawled in 90+ days",
                  listing([r["url"] for r in res["rows"] if not r.get("lastCrawl")]
                          or ["multiple - see the 90d+ bucket"]), "Watch", "2.1",
                  f"Median last-crawl age across the site is {crawl['median_age_days']} days. "
                  "Crawl recency is a proxy for crawl frequency, not Googlebot request "
                  "volume, which has no API. Watch this share month over month: a rising "
                  "figure means coverage is going stale."])

    # A URL in the sitemap that carries noindex is the site contradicting
    # itself: the sitemap asks Google to index it, the page forbids it. Matched
    # on substring because Google returns the state with curly quotes around
    # noindex, which an equality check misses. Found on 98 SameDay URLs, 32% of
    # its sitemap, and invisible to check 5 because that crawls only money pages
    # and recent posts.
    nox = [(st, n) for st, n in counts.items() if "noindex" in st.lower()]
    for st, n in nox:
        urls = urls_for(res, st)
        live = live_noindex(urls)
        crawled = sorted({r["lastCrawl"][:7] for r in res["rows"]
                          if r.get("state") == st and r.get("lastCrawl")})
        when = f"last crawled {', '.join(crawled)}" if crawled else "crawl date unknown"
        if live["checked"] and not live["noindex"]:
            F.append([f"{n} URL(s) held out of the index on a STALE noindex verdict "
                      f"({pct(n, total)})",
                      listing(urls), "Blocker", "2.1",
                      f"Google records these as excluded by noindex, {when}, but a live "
                      f"check of {live['checked']} of them found the tag on NONE: all "
                      f"return 200 with an index directive and real content. The tag was "
                      f"removed and Google has not re-crawled to notice. These pages are "
                      f"sitting out of the index for no current reason. Request indexing "
                      f"on the highest-value ones and resubmit the sitemap."])
        elif live["checked"]:
            F.append([f"{n} URL(s) recorded as excluded by noindex ({pct(n, total)}), "
                      f"{live['noindex']} of {live['checked']} confirmed live",
                      listing(urls), "Fix This Month", "2.1",
                      f"Google's record says noindex, {when}, and a live sample confirms "
                      f"the tag is still present on {live['noindex']} of "
                      f"{live['checked']} checked. The sitemap submits these for indexing "
                      f"while the page forbids it. Decide per URL which signal is wrong."])
        else:
            F.append([f"{n} URL(s) recorded as excluded by noindex ({pct(n, total)}), "
                      f"live state UNVERIFIED",
                      listing(urls), "Fix This Month", "2.1",
                      f"Google's record says noindex, {when}. The live check could not "
                      f"run, so whether the tag is still present is unconfirmed. Verify "
                      f"before acting: a removed tag Google has not re-crawled and a tag "
                      f"still in place need opposite fixes."])

    # Anything left over. Google adds and renames coverage states, and a state
    # nobody coded for is exactly the one worth seeing: "Duplicate, Google chose
    # different canonical than user" appeared on two clients and was reported by
    # nothing until this catch-all existed.
    named = {INDEXED, CNI, DNI, UNKNOWN, DUP, DUP_OVERRIDE} | {st for st, _ in nox}
    for st, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        if st in named or st in BENIGN or st.startswith("ERROR"):
            continue
        F.append([f"{n} URL(s) in state '{st}'",
                  listing(urls_for(res, st)), "Watch", "2.1",
                  "Google returned a coverage state this check has no specific rule "
                  "for, so it is surfaced rather than dropped. Read the state name, "
                  "confirm one URL in Search Console, and add a rule if it recurs."])

    errs = sum(n for st, n in counts.items() if st.startswith("ERROR"))
    if errs:
        F.append([f"{errs} URL(s) could not be inspected (API error after retries)",
                  listing([r["url"] for r in res["rows"]
                           if r.get("state", "").startswith("ERROR")]), "Watch", "-",
                  "OUR limitation, not a site fault. These URLs are unmeasured this "
                  "month and are excluded from the counts above. Re-run to resolve."])
    return F


# Every finding this script writes must match this, or a re-run appends a
# second copy instead of replacing it. The sample-fallback row did exactly that
# on Comfort because only the "<n> URL(s)" shape was listed. Add any new finding
# title here at the same time as you add the finding.
MINE = re.compile(r"^(\d+ URL\(s\) |Indexation measured on a sample)")


def append_findings(sid: str, b0: int, new: list[list]) -> int:
    """Replace this script's own findings, leaving run_1_2's in place.

    Clearing the whole block would delete 1.2's findings, which are still valid
    and were produced by a separate trigger. Appending without clearing is worse:
    a second run duplicated every row, which is how Arsenal ended up reporting
    both "3 URL(s) could not be fetched" and its corrected replacement at once.

    Ownership is read off the issue text. Every finding written here starts
    "<n> URL(s) ", and none of 1.2's do, so the split needs no marker column and
    survives rows shifting when 1.2 is re-run.
    """
    existing = S.read(sid, f"'{TAB}'!A{b0}:F{b0 + 200}")
    keep = [(r + [""] * 6)[:6] for r in existing
            if len(r) > 1 and r[1].strip() and not MINE.match(r[1].strip())]
    body = [[i + 1] + r[1:] for i, r in enumerate(keep)]
    body += [[len(keep) + i + 1] + f for i, f in enumerate(new)]
    if not body:
        return 0
    S.clear(sid, f"'{TAB}'!A{b0}:F{b0 + 200}")
    return S.write(sid, f"'{TAB}'!A{b0}:F{b0 + len(body) - 1}", body).cells


def run(slug: str, cfg: dict, month: str, force: bool = False) -> dict:
    cache = Path(cfg["folder"]) / "Monthly SEO Workbook" / month / "index_audit.json"
    res = None
    if cache.exists() and not force:
        import json
        res = json.loads(cache.read_text(encoding="utf-8"))
        # A cache written by an older version of the script is not a cache, it
        # is a crash waiting to happen: Superior's August file predated the
        # `crawl` key and took the whole run down with a KeyError. Treat any
        # file missing a key we now depend on as absent and re-fetch.
        if not all(k in res for k in ("crawl", "rows", "counts", "checked")):
            res = None
    if res is None:
        res = IX.audit(slug, cfg, month)

    # A sitemap that does not resolve yields zero URLs, and zero URLs is not a
    # measurement. Comfort's first run wrote "Pass" on both checks off an empty
    # set, reported "Median age Noned", and told check 6 that 0 of 0 URLs were
    # indexed. Fall back to the pages 1.1 already proved earn clicks, the same
    # fallback run_1_2 uses, so the client gets real data instead of a hollow
    # pass. The sample is labelled everywhere it appears: it is a handful of
    # landing pages, not the site.
    # Read the flag back off the cache, not just off this run. A sampled result
    # is persisted with its rows, so a later run loading that cache sees 10 real
    # URLs and would otherwise forget they were a sample and quietly report them
    # as the whole site.
    # Only the owner-defined URL set counts. Rows outside it stay in the cache
    # so the sitemap total is never lost, but they are not findings: Cudio's
    # /jobs/ and Snow's /pages/ are in the sitemap and are not part of the site
    # under audit.
    if any("inScope" in r for r in res.get("rows", [])):
        res = {**res, "rows": [r for r in res["rows"] if r.get("inScope")]}

    sampled = bool(res.get("sampled"))
    if not res["checked"]:
        p11 = S.find_rows(cfg["sheet_id"], "1.1 Data Snapshot", {"c": "Page URL"})
        top = [r[0] for r in S.read(
            cfg["sheet_id"], f"'1.1 Data Snapshot'!A{p11['c']+1}:A{p11['c']+10}")
            if r and str(r[0]).startswith("http")]
        if not top:
            raise RuntimeError(
                f"{slug}: sitemap yields no URLs and 1.1 has no landing pages "
                "to fall back on. Nothing to inspect.")
        rows = [IX.inspect_one(cfg["gsc_property"], u) for u in top]
        from collections import Counter
        res = {**res, "checked": len(rows), "rows": rows,
               "counts": dict(Counter(r["state"] for r in rows)),
               "crawl": IX.crawl_recency(rows), "sampled": True}
        sampled = True
        # Persist it, or next month diffs against the empty file IX.audit wrote
        # and every sampled URL looks brand new. A sample is still a baseline.
        cache.parent.mkdir(parents=True, exist_ok=True)
        import json as _j
        cache.write_text(_j.dumps(res, indent=1), encoding="utf-8")

    changed = IX.diff_previous(cfg, month)
    prev = None
    base = Path(cfg["folder"]) / "Monthly SEO Workbook"
    months = sorted(p.name for p in base.glob("*") if (p / "index_audit.json").exists())
    if month in months and months.index(month) > 0:
        import json
        prev = json.loads((base / months[months.index(month) - 1] / "index_audit.json")
                          .read_text(encoding="utf-8"))

    sid = cfg["sheet_id"]
    p = S.find_rows(sid, TAB, MARKS)
    counts, total, crawl = res["counts"], res["checked"], res["crawl"]
    idx = counts.get(INDEXED, 0)
    cni, dni = counts.get(CNI, 0), counts.get(DNI, 0)

    mix = ", ".join(f"{st} {n}" for st, n in
                    sorted(counts.items(), key=lambda kv: -kv[1]))
    if prev:
        pc = prev["counts"]
        moved = (f"vs last month: indexed {pc.get(INDEXED,0)}->{idx}, "
                 f"crawled-not-indexed {pc.get(CNI,0)}->{cni}, "
                 f"discovered-not-indexed {pc.get(DNI,0)}->{dni}. "
                 f"{len(changed)} URL(s) changed state.")
        c3_status = "Issue Found" if any(
            o == INDEXED and c != INDEXED for _, o, c in changed) else "Pass"
    else:
        moved = ("BASELINE MONTH - no comparison possible. The URL Inspection API "
                 "returns current state only and holds no history, so month-over-month "
                 "starts from next month's run against this stored result.")
        c3_status = "Issue Found" if (cni / max(total, 1) >= CNI_SHARE_WATCH
                                      or dni / max(total, 1) >= DNI_SHARE_FLAG) else "Pass"

    b = crawl["buckets"]
    stale = b["90d+"] + b["never"]
    fetchbad = sum(crawl["fetch_failures"].values())
    c4_txt = (f"CRAWL RECENCY PROXY, not Crawl Stats: that report is UI-only and no API "
              f"exposes Googlebot request volume or the response-code mix. Measured from "
              f"last-crawl date on {total} URLs. Median age {crawl['median_age_days']}d. "
              f"0-7d {b['0-7d']}, 8-30d {b['8-30d']}, 31-90d {b['31-90d']}, "
              f"90d+ {b['90d+']}, never {b['never']}. "
              + (f"Fetch failures: {crawl['fetch_failures']}." if fetchbad
                 else "No fetch failures."))
    if prev:
        pb = prev["crawl"]["buckets"]
        c4_txt += (f" vs last month: 90d+ {pb['90d+']}->{b['90d+']}, "
                   f"never {pb['never']}->{b['never']}.")

    scope = (f"SAMPLE ONLY: the registered sitemap does not resolve, so this "
             f"covers the {total} top landing pages from 1.1, NOT the whole site. "
             f"Percentages are of the sample. "
             if sampled else f"URL Inspection API, all {total} sitemap URLs. ")
    rows = {
        p["c3"]: [c3_status, f"{scope}{mix}. {moved}"],
        p["c4"]: ["Issue Found" if (fetchbad or stale / max(total, 1) >= STALE_SHARE_WATCH)
                  else "Pass", c4_txt],
    }
    n = sum(S.write(sid, f"'{TAB}'!B{r}:C{r}", [[a, bb]]).cells
            for r, (a, bb) in rows.items())

    # Check 6 asked for "URL count vs indexed count" and could only ever answer
    # half of it. Now it can answer both, so the old caveat is replaced rather
    # than left standing next to a number that contradicts it.
    #
    # Unless we sampled: with no resolving sitemap there is no sitemap count to
    # compare against, and an indexed figure drawn from ten landing pages would
    # read as a site-wide one. Comfort's first run appended "Indexed: 0 of 0
    # (n/a)" directly under a row that already said SITEMAP UNREACHABLE.
    if not sampled:
        old6 = S.read(sid, f"'{TAB}'!C{p['c6']}:C{p['c6']}")
        # Strip anything this script appended before, not just run_1_2's
        # caveat. Splitting on the caveat alone stacked a new sentence onto the
        # stale one every run: Cudio's cell ended up asserting 145 of 234 twice
        # and then 68 of 80, three contradictory figures in one cell.
        txt6 = (old6[0][0] if old6 and old6[0] else "")
        for marker in ("Real indexed count", " Indexed: ", "Indexed count NOT"):
            txt6 = txt6.split(marker)[0]
        txt6 = txt6.strip()
        smtot = res.get("sitemapTotal")
        scope_note = (f" ({smtot} URLs in the sitemap; the rest are outside the "
                      f"defined scope of money pages and posts)"
                      if smtot and smtot != total else "")
        txt6 += (f" Indexed: {idx} of {total} in-scope URLs ({pct(idx, total)})"
                 f"{scope_note}, measured per URL via URL Inspection, not the "
                 f"deprecated Sitemaps API field.")
        n += S.write(sid, f"'{TAB}'!C{p['c6']}", [[txt6]]).cells

        # Check 6 is "sitemap URL count vs indexed count", and until this run it
        # had no indexed count, so its status came from sitemap errors alone.
        # Now that the cell carries the comparison, the status has to reflect it:
        # SameDay read "Pass" directly beside "Indexed: 88 of 305 (29%)". Only
        # downgrade, never upgrade, so a real sitemap error already flagged by
        # run_1_2 is never overwritten with a pass.
        if idx / max(total, 1) < INDEXED_SHARE_OK:
            n += S.write(sid, f"'{TAB}'!B{p['c6']}", [["Issue Found"]]).cells

    F = build_findings(res, changed, prev)
    if sampled:
        F.insert(0, ["Indexation measured on a sample, not the site",
                     cfg["gsc_property"],
                     "Fix This Month", "2.1",
                     f"The registered sitemap does not resolve, so checks 3 and 4 cover "
                     f"only the {total} top landing pages from 1.1. Everything else on "
                     f"the site is unmeasured. Fix the sitemap and re-run to get real "
                     f"coverage; until then, treat these two rows as indicative only."])
    n += append_findings(sid, p["bsec"] + 2, F)
    return {"cells": n, "urls": total, "indexed": idx, "cni": cni, "dni": dni,
            "changed": len(changed), "findings": len(F), "baseline": prev is None,
            "sampled": sampled}


def main() -> int:
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    force = "--force" in sys.argv
    month = dt.date.today().strftime("%Y-%m")
    todo = list(reg) if arg == "all" else [arg]

    print(f"{'client':<12}{'urls':>6}{'indexed':>9}{'CNI':>6}{'DNI':>6}"
          f"{'chg':>5}{'find':>6}{'cells':>7}  note")
    print("-" * 78)
    for slug in todo:
        try:
            r = run(slug, reg[slug], month, force)
            print(f"{slug:<12}{r['urls']:>6}{r['indexed']:>9}{r['cni']:>6}"
                  f"{r['dni']:>6}{r['changed']:>5}{r['findings']:>6}{r['cells']:>7}  "
                  + ("baseline" if r["baseline"] else "vs prior month"))
        except Exception as e:
            print(f"{slug:<12}{'':>39}  FAILED {e.__class__.__name__}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
