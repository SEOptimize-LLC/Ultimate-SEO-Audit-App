#!/usr/bin/env python
"""Library-wide content refresh audit: every page that earns something, one bucket each, one ranked queue.

    python scripts/refresh_audit.py <client> [--serp-cap 100] [--no-serp] [--no-ga4] [--no-tracker]
                                             [--review-top 30] [--out PATH]

On demand only, never part of the monthly workbook (owner, 2026-11-10). Built on the 1.5 rules and the
2026-11-10 refresh-prioritization research run. The code does the mechanical part (pool, signals,
bucket, sort). Business value for posts, the action and the rationale are judgments: the top
`--review-top` rows take them from Clients/<folder>/refresh_audit/review.yaml, written after reading
each row's evidence; every other row says "ranked, not reviewed".

Buckets
  Recover rank     clicks fell and position worsened 1.5+ places            -> content depth and links
  Win the answer   clicks fell, position and impressions held                -> SERP route decides the fix
  Earn citations   no decline, but the page's topic has a tracker prompt where the client is absent on
                   both engines                                              -> sources, quotes, statistics
  Out              too little demand, demand fall (no rewrite), or holding

Every comparison is against the same three months a year earlier when the page has a year of data, and
against the previous three months only when it does not (1.5: year-over-year control is mandatory).
"""
from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import re
import ssl
import sys
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit

import yaml

sys.path.insert(0, str(Path(__file__).parent))

MIN_IMPR_12M = 100        # owner, 2026-11-10: under this in 12 months there is too little demand to judge
DROP_SHARE = 0.20         # a click fall smaller than 20% is holding (research: Animalz threshold, untested)
DROP_MIN_CLICKS = 5       # and fewer than 5 clicks lost is noise on a small page
POS_LOSS = 1.5            # 1.5: a move of 1.5+ places worse is a ranking loss
IMPR_HELD = 0.85          # 1.5: impressions at 85%+ of the comparison count as held
GAP_MIN_SHARED = 2        # content words a page's queries must share with a tracker prompt
# Google's May 2025-Apr 2026 impressions logging error is handled in reporting_break.py.
BUCKET_ORDER = {"Recover rank": 0, "Win the answer": 1, "Older decline": 2, "Earn citations": 3, "Out": 4}


# ---------------------------------------------------------------- pure logic (tested)

def year_ago(d0: dt.date, d1: dt.date) -> tuple[dt.date, dt.date]:
    s = d0.replace(year=d0.year - 1)
    e = dt.date(d1.year - 1, d1.month, calendar.monthrange(d1.year - 1, d1.month)[1])
    return s, e


def months_back(end: dt.date, n: int) -> dt.date:
    """First day of the month n-1 months before `end`'s month (n whole months ending at `end`)."""
    y, m = end.year, end.month - (n - 1)
    while m <= 0:
        y, m = y - 1, m + 12
    return dt.date(y, m, 1)


def comparison(cur: dict, pri: dict, yoy: dict) -> tuple[dict, str]:
    if yoy.get("impressions"):
        return yoy, "same 3 months last year"
    return pri, "previous 3 months (no year-ago data)"


def diagnose(cur: dict, base: dict, impr_12m: int, cause_base: dict | None = None) -> tuple[str, str]:
    """(bucket, signature) from threshold arithmetic only. Earn citations is decided by the caller.

    `base` decides whether clicks fell. `cause_base` (default `base`) decides why: ranking, demand or
    neither. They differ when the year-ago window falls in Google's May 2025-Apr 2026 logging error, whose impressions and positions
    are not comparable with today's."""
    if impr_12m < MIN_IMPR_12M:
        return "Out", f"too little demand to judge ({impr_12m} impressions in 12 months)"
    lost = base.get("clicks", 0) - cur.get("clicks", 0)
    fell = lost >= DROP_MIN_CLICKS and lost >= DROP_SHARE * max(base.get("clicks", 0), 1)
    if not fell:
        return "Out", "holding: no click fall of 20% or more"
    cb = cause_base if cause_base is not None else base
    if cause_base is not None and cb.get("clicks", 0) and cur.get("clicks", 0) >= (1 - DROP_SHARE) * cb["clicks"]:
        return "Older decline", ("decline shown in clicks; cause not readable in Search Console (it misreported "
                                 "impressions and position from May 2025 to April 2026)")
    move = (cur.get("position") or 0) - (cb.get("position") or 0)
    if cb.get("position") and move >= POS_LOSS:
        return "Recover rank", f"ranking loss: position {cb['position']:.1f} to {cur['position']:.1f}"
    if cb.get("impressions") and cur.get("impressions", 0) < IMPR_HELD * cb["impressions"]:
        return "Out", (f"demand fall: position held, impressions {cb['impressions']:,} to "
                       f"{cur['impressions']:,}; no rewrite, monitor")
    return "Win the answer", "clicks fell while position and impressions held"


COMMON_SHARE = 0.25       # a word in a quarter of the client's prompts (its city, its trade) proves no match


def _stem(ws: set) -> set:
    return {w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w for w in ws}


def common_words(prompts: list[dict], words) -> set:
    n = len(prompts)
    if not n:
        return set()
    seen = Counter(w for p in prompts for w in _stem(words(p.get("keyword") or p.get("text") or "")))
    return {w for w, k in seen.items() if k >= max(2, COMMON_SHARE * n)}


def gap_prompts(page_queries: list[str], prompts: list[dict], words, common: set | None = None) -> list[str]:
    """Tracker prompts absent on both SOV engines whose keyword shares GAP_MIN_SHARED topic words with the
    page. Words common to the client's whole prompt set (Salt Lake City, plumbing) do not count: on the
    Beehive pilot they attached the same two prompts to every page."""
    common = common if common is not None else common_words(prompts, words)
    pw = (_stem(set().union(*(words(q) for q in page_queries))) - common) if page_queries else set()
    out = []
    for p in prompts:
        eng = p.get("engines") or {}
        sov = [eng.get(e) for e in ("chatgpt", "ai_mode") if eng.get(e)]
        if len(sov) < 2 or any(e["mentioned"] for e in sov):
            continue
        if len(pw & (_stem(words(p.get("keyword") or p.get("text") or "")) - common)) >= GAP_MIN_SHARED:
            out.append(p["text"])
    return out


def sort_key(row: dict) -> tuple:
    band = 0 if row["value"].startswith("High") else 1
    return (row["bucket"] == "Out", band, -row["leads_lost"], -row["clicks_lost"], -row["impr"])


# ---------------------------------------------------------------- data

def gsc_pages(T, svc, site, start, end) -> dict[str, dict]:
    return T.merge(T.query(svc, site, start, end, ["page"]))


def page_queries(T, svc, site, start, end, brand: str) -> tuple[dict, dict]:
    """({page: [non-branded queries by impressions]}, {page: True when every query is branded})."""
    rows = T.query(svc, site, start, end, ["page", "query"])
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(T.norm(r["keys"][0]), []).append((r["keys"][1], r["impressions"]))
    nb, branded_only = {}, {}
    for u, qs in by.items():
        keep = [q for q, _ in sorted(qs, key=lambda x: -x[1]) if not (brand and brand in q.lower())]
        nb[u] = keep[:10]
        branded_only[u] = not keep
    return nb, branded_only


def ga4_leads(cfg, cur: tuple[dt.date, dt.date], base: tuple[dt.date, dt.date]) -> dict[str, tuple[int, int]]:
    """{landing path: (leads now, leads in the comparison window)} from organic sessions, approved events."""
    import task_1_1 as G
    ev = cfg.get("ga4_lead_events") or []
    if not (cfg.get("ga4_property") and ev):
        raise RuntimeError("no GA4 property or approved lead events in the registry")
    r = G.ga4().properties().runReport(property=f"properties/{cfg['ga4_property']}", body={
        "dateRanges": [{"startDate": cur[0].isoformat(), "endDate": cur[1].isoformat()},
                       {"startDate": base[0].isoformat(), "endDate": base[1].isoformat()}],
        "dimensions": [{"name": "landingPage"}],
        "metrics": [{"name": "eventCount"}],
        "dimensionFilter": {"andGroup": {"expressions": [
            {"filter": {"fieldName": "sessionDefaultChannelGroup", "stringFilter": {"value": "Organic Search"}}},
            {"filter": {"fieldName": "eventName", "inListFilter": {"values": ev}}}]}},
        "limit": 10000,
    }).execute()
    out: dict[str, list[int]] = {}
    for row in r.get("rows", []):
        path = (row["dimensionValues"][0]["value"].split("?")[0].rstrip("/")) or "/"
        rng = int(row["dimensionValues"][1]["value"].replace("date_range_", ""))
        out.setdefault(path, [0, 0])[rng] += int(float(row["metricValues"][0]["value"]))
    return {k: (v[0], v[1]) for k, v in out.items()}


def manual_ai_impressions(folder: Path) -> dict[str, int]:
    f = folder / "data" / "gsc_generative_ai_pages.csv"
    if not f.exists():
        return {}
    out = {}
    with f.open(encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            url = r.get("Top pages") or r.get("Page") or r.get("URL") or ""
            imp = re.sub(r"[^\d]", "", str(r.get("Impressions") or ""))
            if url and imp:
                out[url.split("#")[0].rstrip("/")] = int(imp)
    return out


RETRY = {429, 500, 502, 503, 504}


def resolve(url: str, tries: int = 4, sleep=None) -> tuple[int | None, str]:
    """(status, final URL) following redirects. 429 and 5xx are retried with a growing pause; one that
    never clears comes back as (None, reason), which the caller reports as unconfirmed, never as dead."""
    import time
    sleep = sleep or time.sleep
    ctx = ssl.create_default_context()
    last = "fetch failed"
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SEOAudit/1.0)"})
            r = urllib.request.urlopen(req, timeout=25, context=ctx)
            return r.status, r.geturl().split("#")[0].rstrip("/")
        except urllib.error.HTTPError as e:
            if e.code not in RETRY:
                return e.code, url
            last = f"HTTP {e.code} after {i + 1} tries"
        except Exception as e:                   # noqa: BLE001 - reported on the row
            last = f"fetch failed: {type(e).__name__}"
        sleep(3 * (i + 1))
    return None, last


# ---------------------------------------------------------------- build

def build(slug: str, cfg: dict, args) -> tuple[list[dict], dict]:
    import task_1_5 as T
    from plan_1_8 import words
    import prior_work
    svc, site = T.sc(), cfg["gsc_property"]
    (c0, c1), (p0, p1) = T.periods()
    y0, y1 = year_ago(c0, c1)
    _, last = T.latest_month()
    money, posts, in_scope = T.scope(cfg)
    home = site.rstrip("/")
    notes = {"windows": f"current {c0}..{c1}, previous {p0}..{p1}, year ago {y0}..{y1}"}

    cur, pri, yoy = gsc_pages(T, svc, site, c0, c1), gsc_pages(T, svc, site, p0, p1), gsc_pages(T, svc, site, y0, y1)
    m12 = gsc_pages(T, svc, site, months_back(last, 12), last)
    import reporting_break as RB
    shifted = RB.affects(y0, RB.has_break(svc, site))
    post = gsc_pages(T, svc, site, *RB.POST) if shifted else {}
    m16 = gsc_pages(T, svc, site, months_back(last, 16), last)
    queries, branded_only = page_queries(T, svc, site, c0, c1, (cfg.get("brand_token") or "").lower())

    leads, leads_note = {}, ""
    if getattr(args, "ga4_json", None):
        import json
        raw = json.loads(Path(args.ga4_json).read_text(encoding="utf-8"))
        leads = {(k.rstrip("/") or "/"): tuple(v) for k, v in raw.items()}
    elif not args.no_ga4:
        try:
            leads = ga4_leads(cfg, (c0, c1), (y0, y1))
        except Exception as e:                   # noqa: BLE001 - stated on the tab, never silently zero
            leads_note = f"GA4 leads not confirmed ({type(e).__name__})"
            print("!!", leads_note, e)
    prompts, cited, tracker_note = [], Counter(), ""
    if not args.no_tracker:
        try:
            import tracker_reader as TR
            snap = TR.snapshot(cfg["domain"])
            prompts = snap["prompts"]
            for p in prompts:
                for u in p.get("own_urls") or []:
                    cited[T.norm(u.split("?")[0])] += 1
            notes["tracker"] = f"tracker week of {snap['week']}, {len(prompts)} category prompts"
        except Exception as e:                   # noqa: BLE001
            tracker_note = f"AI citations not confirmed ({type(e).__name__})"
            print("!!", tracker_note, e)
    try:
        worked = {}
        for key, sid in prior_work.prior_ids(cfg, 6):   # newest first, so the first hit is the latest month
            for u in prior_work.worked_urls(sid):
                worked.setdefault(prior_work.canon(u).rstrip("/"), key.replace("sheet_id_", "").replace("_", "-"))
    except Exception as e:                       # noqa: BLE001
        worked = {}
        print("!! recently-worked list not read:", e)
    ai_impr = manual_ai_impressions(Path(cfg["folder"]))

    common = common_words(prompts, words)
    pool = (set(m16) | set(cited)) - {u for u, b in branded_only.items() if b}
    if in_scope:
        pool &= in_scope | {home}
    rows = []
    for u in sorted(pool):
        c = cur.get(u) or {}
        b, label = comparison(c, pri.get(u) or {}, yoy.get(u) or {})
        cause = b
        if label.startswith("same 3 months") and shifted and post.get(u):
            cause = post[u]
            label = ("clicks: same 3 months last year; ranking and demand: May-Jul 2026, the first clean quarter "
                     "after Search Console misreported impressions and position (May 2025 to April 2026)")
        bucket, sig = diagnose(c, b, int((m12.get(u) or {}).get("impressions", 0)), cause)
        qs = queries.get(u, [])
        gaps = gap_prompts(qs, prompts, words, common) if prompts else []
        if bucket == "Out" and sig.startswith(("holding", "demand fall")) and gaps:
            bucket, sig = "Earn citations", f"{sig.split(':')[0]} in search; the client is absent from AI answers on this topic"
        path = urlsplit(u).path.rstrip("/") or "/"
        ln, lb = leads.get(path, (0, 0)) if leads else (None, None)
        value = ("High (homepage)" if u == home else "High (money page)" if u in money
                 else "Post: judge" if u in posts else "Other: judge")
        rows.append(dict(
            url=u, value=value, bucket=bucket, signature=sig, compare=label,
            clicks=int(c.get("clicks", 0)), clicks_base=int(b.get("clicks", 0)),
            impr=int(c.get("impressions", 0)), impr_base=int(cause.get("impressions", 0)),
            pos=c.get("position") or 0, pos_base=cause.get("position") or 0,
            clicks_lost=max(0, int(b.get("clicks", 0)) - int(c.get("clicks", 0))),
            leads=ln, leads_base=lb, leads_lost=max(0, lb - ln) if leads else 0,
            top_query=qs[0] if qs else "", gaps=gaps, cited=cited.get(u, 0),
            ai_impr=ai_impr.get(u), worked=worked.get(u, ""), serp="", status=""))

    # SERP check on Win-the-answer rows, largest impressions first, capped.
    wins = sorted((r for r in rows if r["bucket"] == "Win the answer"), key=lambda r: -r["impr"])
    if not args.no_serp:
        import serp_features as SF

        def one(r):
            try:
                route, why, _ = SF.check(slug, r["top_query"], cfg["domain"])
                return f"{route}: {why} (one DataForSEO reading; not confirmed on a live Google results page)"
            except Exception as e:               # noqa: BLE001 - stated on the row
                return f"SERP check failed ({type(e).__name__})"
        todo = [r for r in wins if r["top_query"]][:args.serp_cap]
        for r in wins:
            r["serp"] = "no non-branded query" if not r["top_query"] else "SERP not checked (over the cap)"
        with ThreadPoolExecutor(6) as ex:
            for r, res in zip(todo, ex.map(one, todo)):
                r["serp"] = res
    rows.sort(key=sort_key)

    # Status check on every row in the queue (not Out): an address that does not serve 200 is never analysed.
    # Every address written to the file is resolved first, Out rows included (follow-the-redirect rule).
    import time
    for r in rows:                               # one at a time: the Beehive pilot drew 114 429s at 8 threads
        st, final = resolve(r["url"] + "/")
        time.sleep(0.5)
        if st is None:
            r["status"] = f"not confirmed ({final})"
        elif st == 200 and final.rstrip("/") == r["url"].rstrip("/"):
            r["status"] = "200"
        elif st == 200:
            # The deliverable carries the address that serves the page; the recorded one goes in Status.
            r["status"] = f"Search Console records {r['url']}, which redirects here"
            r["url"] = final
            r["bucket"], r["signature"] = "Out", "redirecting address: judge the page under its own row"
        else:
            r["status"] = str(st)
            r["bucket"], r["signature"] = "Out", f"does not serve 200 ({r['status']}); not analysed"
    rows.sort(key=sort_key)
    notes["leads"] = leads_note or "organic leads from the client's approved GA4 events"
    notes["tracker_note"] = tracker_note
    return rows, notes


# ---------------------------------------------------------------- review overlay and output

def apply_review(rows: list[dict], review: dict, top: int) -> None:
    n = 0
    for r in rows:
        if r["bucket"] == "Out":
            r["review"] = ""
            continue
        n += 1
        rv = review.get(r["url"]) or review.get(r["url"] + "/") or {}
        if n <= top and rv:
            r["value"] = rv.get("value", r["value"])
            r["serp_live"] = rv.get("serp", "")
            r["action"], r["rationale"], r["review"] = rv.get("action", ""), rv.get("rationale", ""), "reviewed"
        else:
            r["action"], r["rationale"] = "", ""
            r["review"] = "to review" if n <= top else "ranked, not reviewed"


HEADERS = ["#", "URL", "Bucket", "Business value", "Diagnosis", "Compared with", "Clicks now / then",
           "Impressions now / then", "Position now / then", "Organic leads now / then", "Top query",
           "SERP features", "AI citations (prompts citing it)", "AI prompts where absent",
           "AI-surface impressions (manual export)", "Last worked (workbook month)", "Status",
           "Action", "Rationale", "Review"]


def serp_cell(r: dict) -> str:
    """K2: what a results page shows is written only from a live Google check recorded in review.yaml.
    The DataForSEO screen routes the row for review; it never reaches the file as a claim."""
    import sheets_io as S
    if r.get("serp_live"):
        return S.compose(("CHECKED ON GOOGLE", [x.strip() for x in re.split(r"(?<=\.)\s+", r["serp_live"]) if x.strip()]),
                         where=f"refresh audit serp {r['url']}")
    return "SERP not checked live" if r.get("serp") else ""


def gaps_cell(r: dict) -> str:
    import sheets_io as S
    return S.compose(("ABSENT FROM", r["gaps"][:3]), where=f"refresh audit gaps {r['url']}") if r.get("gaps") else ""


def to_cells(i: int, r: dict) -> list:
    import sheets_io as S
    rationale = r.get("rationale") or ""
    if rationale:
        rationale = S.compose(("Why", [s.strip() for s in re.split(r"(?<=\.)\s+", rationale) if s.strip()]),
                              where=f"refresh audit {r['url']}")
    return [i, r["url"], r["bucket"], r["value"], r["signature"], r["compare"],
            f"{r['clicks']:,} / {r['clicks_base']:,}", f"{r['impr']:,} / {r['impr_base']:,}",
            f"{r['pos']:.1f} / {r['pos_base']:.1f}",
            "not confirmed" if r["leads"] is None else f"{r['leads']} / {r['leads_base']}",
            r["top_query"], serp_cell(r), r["cited"] or "", gaps_cell(r),
            r["ai_impr"] if r["ai_impr"] is not None else "", r["worked"] or "",
            r["status"], r.get("action", ""), rationale, r.get("review", "")]


def deliverable_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """(rows that may be written, rows left out). Only an address confirmed to serve 200 is written; a
    non-200 or unconfirmed check is printed in the run output and counted, never listed."""
    keep, drop = [], []
    for r in rows:
        (keep if r.get("status") == "200" or str(r.get("status", "")).startswith("Search Console records") else drop).append(r)
    return keep, drop


def write_xlsx(rows: list[dict], notes: dict, path: Path, client: str) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    head_fill, head_font = PatternFill("solid", fgColor="0DE24C"), Font(bold=True, color="000000")
    align = Alignment(wrap_text=True, vertical="center")
    wb = Workbook()
    queue = wb.active
    queue.title = "Refresh queue"
    out = wb.create_sheet("Out")
    for ws, subset in ((queue, [r for r in rows if r["bucket"] != "Out"]), (out, [r for r in rows if r["bucket"] == "Out"])):
        ws.append(HEADERS)
        for i, r in enumerate(subset, 1):
            ws.append(to_cells(i, r))
        widths = [5, 60, 16, 18, 42, 22, 14, 18, 14, 14, 30, 40, 14, 40, 16, 12, 18, 40, 60, 16]
        for col, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(1, col).column_letter].width = w
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = align
        for cell in ws[1]:
            cell.fill, cell.font = head_fill, head_font
        ws.freeze_panes = "C2"
        dv = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"D2:D{max(ws.max_row, 2)}")
    how = wb.create_sheet("How to read")
    lines = [
        ["Client", client], ["Windows", notes.get("windows", "")],
        ["Comparison", "Clicks are compared with the same 3 months last year (previous 3 months for pages without a year of data). Ranking and demand are read against May-July 2026: Google's Data Anomalies page says Search Console misreported impressions, CTR and average position from May 13, 2025 to April 27, 2026, and that clicks were not affected."],
        ["Older decline", "Clicks fell against last year but not against May-July 2026, so the decline happened during the misreported period and Search Console cannot say whether it was ranking or demand. Read the page and its history before choosing the work."],
        ["Recover rank", "Clicks fell 20%+ (at least 5) and position worsened 1.5+ places. Work: content depth and internal links."],
        ["Win the answer", "Clicks fell while position and impressions held. The SERP column routes it: title and meta, snippet work, or an answer-first passage."],
        ["Earn citations", "No decline, but the client is absent from AI answers on a tracked prompt about this page's topic. Work: sources, named-expert quotes, statistics."],
        ["Out", "Under 100 impressions in 12 months, a demand fall (no rewrite), holding, or not serving 200."],
        ["Order", "Money pages first, then organic leads lost, then clicks lost, then impressions."],
        ["Leads", notes.get("leads", "")], ["AI citations", notes.get("tracker", notes.get("tracker_note", ""))],
        ["SERP features", "Filled only where the results page was checked on a live Google search. Other Win-the-answer rows say 'SERP not checked live'."],
        ["Left out", notes.get("left_out", "")],
    ]
    for ln in lines:
        how.append(ln)
    how.column_dimensions["A"].width, how.column_dimensions["B"].width = 18, 110
    for row in how.iter_rows():
        for cell in row:
            cell.alignment = align
    for f in wb._fonts:
        f.name = "Red Hat Display"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--serp-cap", type=int, default=100)
    ap.add_argument("--no-serp", action="store_true")
    ap.add_argument("--no-ga4", action="store_true")
    ap.add_argument("--no-tracker", action="store_true")
    ap.add_argument("--review-top", type=int, default=30)
    ap.add_argument("--ga4-json", help="{landing path: [leads now, leads a year ago]} pulled another way")
    ap.add_argument("--rewrite", action="store_true", help="re-apply review.yaml to today's cached rows, no fetching")
    ap.add_argument("--out")
    a = ap.parse_args()
    cfg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))[a.client]
    folder = Path(cfg["folder"]) / "refresh_audit"
    import json
    cache = folder / f"{a.client}-rows-{dt.date.today().isoformat()}.json"
    if a.rewrite:
        rows, notes = json.loads(cache.read_text(encoding="utf-8"))
    else:
        rows, notes = build(a.client, cfg, a)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps([rows, notes]), encoding="utf-8")
    rows, dropped = deliverable_rows(rows)
    notes["left_out"] = (f"{len(dropped)} recorded addresses did not serve 200 or could not be confirmed, so they are not listed."
                         if dropped else "None.")
    for r in dropped:
        print(f"  left out: {r['url']} ({r.get('status')})")
    rv_file = folder / "review.yaml"
    review = yaml.safe_load(rv_file.read_text(encoding="utf-8")) if rv_file.exists() else {}
    apply_review(rows, review or {}, a.review_top)
    out = Path(a.out) if a.out else folder / f"{a.client}-refresh-audit-{dt.date.today().isoformat()}.xlsx"
    write_xlsx(rows, notes, out, cfg.get("name", a.client))
    counts = Counter(r["bucket"] for r in rows)
    print(f"\n{out}\n{len(rows)} pages: " + ", ".join(f"{k} {counts[k]}" for k in BUCKET_ORDER))
    for i, r in enumerate([r for r in rows if r["bucket"] != "Out"][:a.review_top], 1):
        print(f"{i:>3} {r['bucket']:<15} {r['value']:<18} clicks {r['clicks_base']}->{r['clicks']} "
              f"leads {r['leads_base']}->{r['leads']} | {r['url']} | {r['serp'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
