"""Task 1.1 - Pull Monthly Data Snapshot.

Implements Skills/monthly-seo-workbook/tasks/1.1.md. Read that first; the rules
here exist because each was got wrong once.

Covers sections A, C and D. Section B (SEMrush Position Tracking) is filled
separately, because the SEMrush key lives in the MCP server rather than here.

    python scripts/task_1_1.py superior            # one client
    python scripts/task_1_1.py all --dry-run       # everyone, write nothing
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from collections import defaultdict
from pathlib import Path

import google.auth
import yaml
from googleapiclient.discovery import build

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheets_io as S  # noqa: E402

SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/webmasters.readonly",
          "https://www.googleapis.com/auth/analytics.readonly"]

# GSC impressions are inflated inside this window (confirmed Google logging bug).
# Any comparison touching it must suppress impressions and use clicks instead.
BUG_START, BUG_END = dt.date(2025, 5, 1), dt.date(2026, 4, 30)

_creds = None


def creds():
    global _creds
    if _creds is None:
        _creds, _ = google.auth.default(scopes=SCOPES)
    return _creds


def gsc():
    return build("searchconsole", "v1", credentials=creds(), cache_discovery=False)


def ga4():
    return build("analyticsdata", "v1beta", credentials=creds(), cache_discovery=False)


# --- periods ----------------------------------------------------------------

def month_bounds(year: int, month: int) -> tuple[str, str]:
    first = dt.date(year, month, 1)
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    return first.isoformat(), (nxt - dt.timedelta(days=1)).isoformat()


def periods(run_date: dt.date):
    """Last COMPLETE calendar month, the month before it, and the year-ago month.

    Calendar months, never rolling 30 days: the client's report is
    calendar-month and rolling windows will not reconcile with it.
    """
    y, m = (run_date.year, run_date.month - 1) if run_date.month > 1 else (run_date.year - 1, 12)
    prev_y, prev_m = (y, m - 1) if m > 1 else (y - 1, 12)
    return month_bounds(y, m), month_bounds(prev_y, prev_m), month_bounds(y - 1, m)


def touches_bug_window(start: str, end: str) -> bool:
    s, e = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    return not (e < BUG_START or s > BUG_END)


# --- GSC --------------------------------------------------------------------

def sc_totals(site: str, start: str, end: str, brand: str | None = None) -> dict:
    body = {"startDate": start, "endDate": end, "dimensions": []}
    if brand:
        body["dimensionFilterGroups"] = [{"filters": [
            {"dimension": "query", "operator": "contains", "expression": brand}]}]
    rows = gsc().searchanalytics().query(siteUrl=site, body=body).execute().get("rows", [])
    if not rows:
        return {"clicks": 0, "impressions": 0}
    return {"clicks": int(rows[0]["clicks"]), "impressions": int(rows[0]["impressions"])}


def sc_pages(site: str, start: str, end: str, limit: int = 200) -> dict[str, int]:
    """Clicks per page, consolidated.

    Two consolidations, both mandatory:
      1. Query-string variants collapse into the canonical path. GSC keys on the
         full URL, so GBP/UTM-tagged homepage links appear as separate pages and
         a raw top-10 is mostly one page repeated.
      2. Blog-migration pairs: where /x/ and /blog/x/ both have clicks, they are
         the same article mid-migration. Sum them under the /blog/ URL.
    """
    rows = gsc().searchanalytics().query(siteUrl=site, body={
        "startDate": start, "endDate": end,
        "dimensions": ["page"], "rowLimit": limit}).execute().get("rows", [])

    agg, variants = defaultdict(int), defaultdict(int)
    for r in rows:
        url = r["keys"][0].split("?")[0]
        agg[url] += int(r["clicks"])
        if "?" in r["keys"][0]:
            variants[url] += 1
    return dict(agg), dict(variants)


def resolve_finals(urls: list[str], timeout: int = 15) -> dict[str, str]:
    """Map each URL to the URL it actually resolves to, following redirects.

    A 301 means the old and new URLs are the same page. GSC keeps reporting the
    old one for a while after a migration, so their clicks must be summed under
    the destination or the page reads as two weaker pages.

    Resolved live rather than inferred from URL shape: a `/blog/` pattern match
    only catches one migration style and would miss every other redirect.
    """
    import urllib.request
    from concurrent.futures import ThreadPoolExecutor

    opener = urllib.request.build_opener()
    opener.addheaders = [("User-Agent", "Mozilla/5.0 (compatible; SEOAudit/1.0)")]

    def one(u: str) -> tuple[str, str]:
        try:
            with opener.open(u, timeout=timeout) as r:
                return u, r.geturl().split("?")[0]
        except Exception:
            return u, u         # unreachable: leave it standing on its own

    with ThreadPoolExecutor(max_workers=10) as pool:
        return dict(pool.map(one, urls))


def merge_by_final(cur: dict[str, int], prior: dict[str, int],
                   probe_top: int = 25) -> tuple[dict, dict, dict]:
    """Fold redirecting URLs into their destination, in both periods alike.

    Both periods get the same mapping, or the month-over-month comparison would
    be summing different things on each side.
    """
    cands = sorted(set(list(cur) + list(prior)),
                   key=lambda u: -(cur.get(u, 0) + prior.get(u, 0)))[:probe_top]
    final = resolve_finals(cands)
    moved = {u: f for u, f in final.items() if f != u}

    def fold(d: dict[str, int]) -> dict[str, int]:
        out: dict[str, int] = defaultdict(int)
        for u, c in d.items():
            out[moved.get(u, u)] += c
        return dict(out)

    return fold(cur), fold(prior), moved


# --- GA4 --------------------------------------------------------------------

def ga4_channels(prop: str, cur: tuple[str, str], prior: tuple[str, str]) -> dict:
    r = ga4().properties().runReport(property=f"properties/{prop}", body={
        "dateRanges": [{"startDate": cur[0], "endDate": cur[1]},
                       {"startDate": prior[0], "endDate": prior[1]}],
        "dimensions": [{"name": "sessionDefaultChannelGroup"}],
        "metrics": [{"name": "sessions"}, {"name": "conversions"}],
    }).execute()
    out = defaultdict(lambda: {"0": (0, 0), "1": (0, 0)})
    for row in r.get("rows", []):
        ch = row["dimensionValues"][0]["value"]
        rng = row["dimensionValues"][1]["value"].replace("date_range_", "")
        out[ch][rng] = (int(float(row["metricValues"][0]["value"])),
                        int(float(row["metricValues"][1]["value"])))
    return out


def pick(ch: dict, name: str, idx: str) -> tuple[int, int]:
    """Absent channel row means zero sessions, not missing configuration."""
    return ch.get(name, {}).get(idx, (0, 0))


# --- assemble + write -------------------------------------------------------

TAB_NAME = "1.1 Data Snapshot"
T = f"'{TAB_NAME}'"
HDR = ["Metric", "This Period", "Prior Period", "YoY (if clean)", "Notes"]


def run(slug: str, cfg: dict, run_date: dt.date, dry: bool) -> dict:
    site, prop = cfg["gsc_property"], cfg["ga4_property"]
    cur, prior, yoy = periods(run_date)

    c_cur, c_prior, c_yoy = (sc_totals(site, *p) for p in (cur, prior, yoy))
    b_cur, b_prior = (sc_totals(site, *p, brand=cfg["brand_token"]) for p in (cur, prior))
    raw_cur, variants = sc_pages(site, *cur)
    raw_prior, _ = sc_pages(site, *prior)
    pages_cur, pages_prior, moved = merge_by_final(raw_cur, raw_prior)
    ch = ga4_channels(prop, cur, prior)

    org_c, org_p = pick(ch, "Organic Search", "0"), pick(ch, "Organic Search", "1")
    ai_c, ai_p = pick(ch, "AI Assistant", "0"), pick(ch, "AI Assistant", "1")
    una_c, una_p = pick(ch, "Unassigned", "0"), pick(ch, "Unassigned", "1")

    bug = touches_bug_window(*yoy)
    bug_note = (f"YoY not usable: {yoy[0][:7]} sits in the May-2025 to Apr-2026 GSC "
                f"impressions logging bug window. Clicks YoY is valid.")
    rev = ["N/A", "N/A", "", "Not an e-commerce site (registry: ecommerce=false)"]
    if cfg["ecommerce"]:
        rev = ["", "", "", "E-commerce client: pull GA4 purchase revenue manually"]

    sec_a = [
        [c_cur["clicks"], c_prior["clicks"], c_yoy["clicks"],
         f"{cur[0][:7]} vs {prior[0][:7]}. YoY vs {yoy[0][:7]}: "
         f"{c_cur['clicks'] - c_yoy['clicks']:+,} "
         f"({(c_cur['clicks'] - c_yoy['clicks']) / max(c_yoy['clicks'], 1) * 100:+.1f}%)"],
        [c_cur["impressions"], c_prior["impressions"], "" if bug else c_yoy["impressions"],
         bug_note if bug else ""],
        [org_c[1], org_p[1], "", f"GA4 Organic Search key events. {org_c[1] - org_p[1]:+,} MoM"],
        rev,
        [ai_c[0], ai_p[0], "", "GA4 'AI Assistant' default channel group"],
        [ai_c[1], ai_p[1], "", ""],
        ["", "", "", "NOT AVAILABLE via API. Pull manually: GSC > Performance > Search Appearance"],
        [b_cur["impressions"], b_prior["impressions"], "",
         f"Queries containing '{cfg['brand_token']}'. "
         f"{b_cur['impressions'] / max(c_cur['impressions'], 1) * 100:.1f}% of all impressions"],
    ]

    top = sorted(pages_cur.items(), key=lambda kv: -kv[1])[:10]
    sec_c = []
    for url, clicks in top:
        pj = pages_prior.get(url)
        bits = []
        if variants.get(url):
            bits.append(f"GSC splits this across {variants[url]+1} URLs "
                        f"(bare + {variants[url]} tagged)")
        folded = [o for o, f in moved.items() if f == url]
        if folded:
            bits.append(f"Summed with {len(folded)} redirecting URL(s) that 301 here: "
                        + ", ".join(u.replace(site.rstrip('/'), '') for u in folded[:2]))
        note = ". ".join(bits)
        sec_c.append([url, clicks, pj if pj is not None else "",
                      clicks - pj if pj is not None else "", note])

    anoms = []
    if una_c[1] > max(una_c[0], 1) * 3:
        anoms.append([
            f"GA4 'Unassigned' reports {una_c[1]:,} conversions on only {una_c[0]:,} sessions "
            f"(prior: {una_p[1]:,} on {una_p[0]:,}). Conversions far exceeding sessions is a "
            f"tracking artifact, not real conversions.",
            f"GA4 {prop}, channel report",
            "Verify with tracking owner BEFORE any conversion total goes to the client"])
    for url, n in variants.items():
        if n >= 2 and url in dict(top):
            anoms.append([
                f"{url} appears under {n+1} URLs in GSC (bare + {n} tagged), so a raw per-URL "
                f"view understates it. Consolidated in section C.",
                "GSC page dimension",
                "Check the tagged URLs canonicalise to the bare one; if they do, no fix needed"])
    if bug:
        anoms.append([bug_note, "GSC YoY comparison",
                      "Impressions YoY left blank; clicks YoY used instead"])
    if not anoms:
        anoms.append(["None observed this period.", "-",
                      "Logged deliberately: an empty section is indistinguishable from a task nobody ran"])

    if dry:
        return {"slug": slug, "written": 0, "clicks": c_cur["clicks"], "pages": len(top),
                "anoms": len(anoms), "bug": bug}

    # Locate sections by heading text. Never hardcode rows: these workbooks are
    # shared, and one inserted row shifts every fixed range. Superior already
    # drifted by one and would have been written into the wrong cells.
    sid = cfg["sheet_id"]
    pos = S.find_rows(sid, TAB_NAME, {
        "snap": "Snapshot date", "a_hdr": "Metric",
        "c_hdr": "Page URL", "d_hdr": "Anomaly"})
    a0, c0, d0 = pos["a_hdr"] + 1, pos["c_hdr"] + 1, pos["d_hdr"] + 1

    chk = S.check_layout(sid, f"{T}!A{pos['a_hdr']}:E{pos['a_hdr']}", HDR)
    if not chk.ok:
        raise RuntimeError(f"{slug}: layout guard failed - {chk.found}")

    n = 0
    n += S.write(sid, f"{T}!B{pos['snap']}", [[run_date.isoformat()]]).cells
    n += S.write(sid, f"{T}!B{a0}:E{a0+7}", sec_a).cells
    n += S.write(sid, f"{T}!A{c0}:E{c0+len(sec_c)-1}", sec_c).cells
    n += S.write(sid, f"{T}!A{d0}:C{d0+len(anoms)-1}", anoms).cells
    for rng, fmt in ((f"{T}!B{a0}:D{a0+7}", S.FMT_INT),
                     (f"{T}!B{c0}:C{c0+9}", S.FMT_INT),
                     (f"{T}!D{c0}:D{c0+9}", S.FMT_DELTA)):
        S.set_number_format(sid, rng, fmt)
    # seed 4.2 with the top FIVE (4.2's own spec), not ten
    S.write(cfg["sheet_id"], "'4.2 Conversion Paths'!A5:A9",
            [[f"={T}!A{r}"] for r in range(24, 29)], verify=False)
    return {"slug": slug, "written": n, "clicks": c_cur["clicks"], "pages": len(top),
            "anoms": len(anoms), "bug": bug}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()

    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    todo = list(reg) if a.client == "all" else [a.client]
    run_date = dt.date.fromisoformat(a.date)
    cur, prior, yoy = periods(run_date)
    print(f"run date {run_date}   period {cur[0]}..{cur[1]}   prior {prior[0]}..{prior[1]}"
          f"   yoy {yoy[0]}..{yoy[1]}\n")
    print(f"{'client':<22}{'cells':>7}{'clicks':>9}{'pages':>7}{'anom':>6}  notes")
    print("-" * 74)
    fails = 0
    for slug in todo:
        try:
            r = run(slug, reg[slug], run_date, a.dry_run)
            print(f"{slug:<22}{r['written']:>7}{r['clicks']:>9,}{r['pages']:>7}{r['anoms']:>6}"
                  f"  {'impressions YoY suppressed' if r['bug'] else ''}")
        except Exception as e:
            fails += 1
            print(f"{slug:<22}{'FAIL':>7}  {e.__class__.__name__}: {str(e)[:44]}")
    print(f"\n{len(todo)-fails}/{len(todo)} ok" + (f", {fails} failed" if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
