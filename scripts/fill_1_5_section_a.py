"""1.5 Section A: last month's optimizations, before/after.

    python scripts/fill_1_5_section_a.py <client|all> [--month YYYY-MM] [--dry-run]

--month is the month this workbook is for (default: the current month). The
work being measured is LAST month's: before = the month before that, after =
last month. The windows are derived from it; nothing here names a month.

Section A is empty on a client's first run because there is no record of work.
From the second run it fills from whatever 1.8 SELECTED - never from ranking
history, because a position change with no record of a change made is not a
before/after.

The "after" month is last month. How much of it is post-change depends on
the ship date, so each note states that share when the sitemap can confirm the
date and says the date is unconfirmed when it cannot. The first COMPLETE
post-change month is the one after, which a later run reads.

Pages come from the prior workbook through prior_work.worked_pages(), which
reads both layouts: 1.8 section A + Refresh Log + 2.5 up to September 2026, the
2.3 Pages section from October 2026.
"""
from __future__ import annotations

import datetime as dt
import re
import statistics
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import prior_work as PW         # noqa: E402
import sheets_io as S           # noqa: E402
import task_1_5 as T            # noqa: E402
import run_1_5 as R             # noqa: E402

TAB = "1.5 Candidate List"
# Single complete months on both sides: comparing three months of clicks
# against one is not a comparison, and the point of this section is that the two
# numbers sit side by side.
#
# Choosing the target and measuring it are different jobs. One month is a thin
# basis for deciding what a page is FOR - a good target that happened not to
# surface in the before month drops out and something worse wins - so the pick
# is made on the full span (four months ending with the work month) and only
# the measurement is held to single months.
WIN: dict = {}


def month_start(y: int, m: int) -> dt.date:
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return dt.date(y, m, 1)


def month_end(d: dt.date) -> dt.date:
    return month_start(d.year, d.month + 1) - dt.timedelta(days=1)


def set_windows(run_month: dt.date) -> None:
    """Derive every window from the month the workbook is for."""
    work = month_start(run_month.year, run_month.month - 1)       # last month
    before = month_start(work.year, work.month - 1)               # the month before
    first = month_start(work.year, work.month - 3)
    WIN.update(work=work, before=(before, month_end(before)),
               after=(work, month_end(work)), resolve=(first, month_end(work)),
               before_name=before.strftime("%B"), after_name=work.strftime("%B"),
               year=work.year)


_LABEL_NOISE = {"family", "cluster", "queries", "query", "prompts", "prompt"}


def primary_query(cell: str) -> str:
    """First target query, without its volume parenthetical or AI-prompt tail."""
    txt = str(cell or "").split("AI prompt")[0].split("AI prompts")[0]
    first = txt.split(";")[0]
    first = re.sub(r"\([^)]*\)", "", first)
    return first.strip(" ,;:-")


def target_label(cell: str) -> str:
    """The one target query a 1.8 plan cell names, or "" when it names none.

    A 1.8 target cell is a numbered list ("1. commercial paving ann arbor / 2. ..."),
    sometimes followed by sections of reasoning, and sometimes it opens with an
    upper-case heading saying no target qualified. Quoting the whole cell into this
    month's notes pasted last month's reasoning onto the sheet and pushed the cell
    past the length cap. Only the first target is wanted, and a heading is not one.
    """
    first = str(cell or "").strip().split("\n")[0].strip()
    if not first or not any(ch.islower() for ch in first):
        return ""
    first = re.sub(r"^\d+[.)]\s*", "", first)
    return primary_query(first)


def brand_keys(cfg: dict) -> set:
    """Brand spellings reduced to letters and digits, so "barts asphalt" matches "bart's asphalt"."""
    raw = cfg.get("brand_token") or []
    raw = [raw] if isinstance(raw, str) else list(raw)
    return {k for k in (re.sub(r"[^a-z0-9]", "", str(b).lower()) for b in raw) if k}


def without_brand(rows: dict, brands: set) -> dict:
    """Drop branded queries. A brand query is not a target: its position says nothing about whether
    optimizing the page worked, and a plan that found no non-branded target means there is none."""
    if not brands:
        return rows
    return {q: r for q, r in rows.items()
            if not any(b in re.sub(r"[^a-z0-9]", "", q.lower()) for b in brands)}


def _toks(s):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).split()
            if len(w) > 2 and w not in _LABEL_NOISE}


def slug_tokens(url: str) -> set:
    """What the page itself says it is about, from its own path."""
    path = re.sub(r"https?://[^/]+", "", str(url))
    return _toks(re.sub(r"[-_/]", " ", path))


def usable_target(q: str, client_terms: set) -> bool:
    """Whether a query can be TRACKED as a page's target.

    A query with no resolvable search intent is not a target, however many
    impressions it carries. "look fors" and "classroom walkthrough" name a
    subject and stop there - nobody, Google included, can say what the searcher
    wants - so a position against them measures cluster visibility, not whether
    this page is doing its job. Owner callout 2026-09-04.

    Two or fewer meaningful terms is the presumption of ambiguity. It is only a
    presumption: "odoo migration" and "furnace repair" are two words that name a
    job somebody wants done, so a commercial marker or one of the client's own
    service/location terms clears it.
    """
    toks = _toks(q)
    if len(toks) >= 3:
        return True
    low = q.lower()
    if any(k in low for k in R.BUY):
        return True
    return bool(toks & client_terms)


def resolve_query(label: str, rows: dict, page: str, client_terms: set,
                  measurable: set | None = None, both: set | None = None):
    """The real GSC query a 1.8 target label refers to.

    1.8 records targets as families - "tankless water heater family" - which are
    not strings anyone searched, so an exact lookup finds nothing. Rank the
    page's real queries by how much they share with BOTH the recorded label and
    the page's own subject, after dropping any that carry no resolvable intent.
    Impressions only break ties: picking on volume alone is what put "look fors"
    on a page about what to look for during a walkthrough.

    Returns (row, exact, rejected) - rejected is what the intent gate removed.
    """
    if not rows:
        return None, False, []
    usable = {q: r for q, r in rows.items() if usable_target(q, client_terms)}
    rejected = sorted(set(rows) - set(usable))
    # A target nobody can measure is not a target. Scoring across the whole span
    # picked queries that surfaced in May and vanished before July, leaving both
    # columns blank, so restrict to queries that appear in a measurement window.
    if measurable:
        narrowed = {q: r for q, r in usable.items() if q in measurable}
        if narrowed:
            usable = narrowed
    if label in usable:
        return usable[label], True, rejected
    if not usable:
        return None, False, rejected
    want, subject = _toks(label), slug_tokens(page)
    scored = []
    for q, r in usable.items():
        qt = _toks(q)
        score = len(want & qt) * 2 + len(subject & qt)
        if both and q in both:
            score += 1          # measurable on both sides beats a one-sided read
        if score:
            scored.append((score, r["impressions"], q, r))
    if not scored:
        return None, False, rejected
    scored.sort(reverse=True)
    return scored[0][3], False, rejected


def page_queries(svc, site, page, start, end, also=()):
    """query -> row, for one page. Filtered server-side so the pull stays small.

    `also` lists other addresses that are the same page (the URL it moved from or to); their rows
    are summed in with the page's own.

    Matches the page's slashed AND unslashed spellings. An exact `equals` filter on the URL as the
    prior workbook recorded it only sees that one spelling, so a page recorded without its trailing
    slash lost the traffic Search Console files under the slashed URL. Because the only dimension is
    the query, Search Console sums the matching spellings into one row per query.
    """
    urls = list(dict.fromkeys(u.rstrip("/") for u in (page, *also)))
    alt = "|".join(re.escape(u) for u in urls)
    body = {"startDate": start.isoformat(), "endDate": end.isoformat(),
            "dimensions": ["query"], "rowLimit": 25000,
            "dimensionFilterGroups": [{"filters": [
                {"dimension": "page", "operator": "includingRegex",
                 # `(?:#.*)?` takes the page's #anchor rows (a table-of-contents jump link is the same
                 # page and carries real impressions: 1,241 of one Cudio post's 3,549).
                 "expression": "^" + (alt if len(urls) == 1 else f"(?:{alt})") + "/?(?:#.*)?$"}]}]}
    r = svc.searchanalytics().query(siteUrl=site, body=body).execute()
    return {row["keys"][0]: row for row in r.get("rows", [])}


def all_pages(svc, site, start, end) -> dict:
    """url -> row, page dimension. NOT summed from query rows.

    GSC withholds anonymized queries from the query breakdown, so query rows do
    not add up to the page total - on EW's Danielson page they gave 1 click
    against the page dimension's 21. Page totals only ever come from here.
    """
    rows, start_row = [], 0
    while True:
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(),
                "dimensions": ["page"], "rowLimit": 25000, "startRow": start_row}
        r = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        got = r.get("rows", [])
        rows.extend(got)
        if len(got) < 25000:
            break
        start_row += len(got)
    # SUM rows that normalize to the same URL; never let one overwrite another.
    # GSC reports a page's slashed and unslashed spellings (and its #anchor
    # variants) as separate rows. Assigning by key let a 3-impression stub
    # replace Bart's 10,985-impression sealcoating page and report it as having
    # collapsed to nothing. task_1_5.merge() already sums them correctly.
    return T.merge(rows)


def landing(url: str) -> str:
    """Where a recorded URL lands now. A workbook records the address as it stood that month, and a
    site that moves its tree leaves every recorded address redirecting. The page is judged, and
    printed, at the address that serves it. A URL that cannot be read raises rather than passing."""
    page = R._resolve(url)
    status = (page or {}).get("status")
    if page is None or (status and status not in (200, 404, 410)):
        raise RuntimeError(f"could not resolve {url} ({'no response' if page is None else 'HTTP ' + str(status)})")
    return (page.get("final") or url).split("?")[0] if status == 200 else url


def combine(*rows):
    """One page row from several addresses of the same page: clicks and impressions add, position is
    impression-weighted. None when no address had a row."""
    rows = [r for r in rows if r]
    if not rows:
        return None
    impr = sum(r["impressions"] for r in rows)
    return {"clicks": sum(r["clicks"] for r in rows), "impressions": impr,
            "position": (sum(r["position"] * r["impressions"] for r in rows) / impr) if impr else 0.0}


def _pct(before, after):
    if not before:
        return None
    return 100.0 * (after - before) / before


def control_for(page, worked, bpages, apages):
    """How pages we did NOT touch moved over the same window.

    Without this the section reports seasonality as a result. EW's Danielson
    page gained 129% clicks in August; an untouched sibling in the same cluster
    gained 157% over the same days, so the lift was the school year starting,
    not the rewrite. Siblings share at least two slug terms; a site-wide median
    stands in when a page has too few of them to mean anything.
    """
    subject = slug_tokens(page)
    # Short slugs need a looser rule. "danielson-rubric" carries two terms, so
    # demanding two shared ones means an exact match and the whole Danielson
    # cluster failed to qualify - the page fell back to a site-wide median that
    # mixed in unrelated topics and hid a category-wide surge.
    need = 1 if len(subject) <= 2 else 2
    sibs, wide = [], []
    for url, brow in bpages.items():
        if url in worked or brow["impressions"] < 50:
            continue
        arow = apages.get(url)
        pair = (brow, arow["clicks"] if arow else 0,
                arow["impressions"] if arow else 0)
        wide.append(pair)
        if len(subject & slug_tokens(url)) >= need:
            sibs.append(pair)
    pool, scope = (sibs, "siblings") if len(sibs) >= 3 else (wide, "site-wide")
    if not pool:
        return ""
    ci = [_pct(b["clicks"], c) for b, c, _ in pool if b["clicks"] >= 5]
    ii = [_pct(b["impressions"], i) for b, _, i in pool if b["impressions"]]
    ci = [x for x in ci if x is not None]
    ii = [x for x in ii if x is not None]
    bits = []
    if ci:
        bits.append(f"clicks {statistics.median(ci):+.0f}%")
    if ii:
        bits.append(f"impressions {statistics.median(ii):+.0f}%")
    return f"Untouched {scope}: {', '.join(bits)} (n={len(pool)})" if bits else ""


def ship_dates(cfg):
    """url -> the date its content changed, where the sitemap can show that.

    Returns (dates, reliable). On a site whose whole sitemap is restamped by
    every release, lastmod says when the site deployed, not when a page was
    edited, so the ship date is reported as unconfirmed rather than guessed.
    """
    try:
        lm = R._lastmod(cfg)
    except Exception:
        return {}, False
    if not lm:
        return {}, False
    deploys = set(R._deploy_dates(lm))
    inwin = [d for d in lm.values() if WIN["after"][0] <= d <= WIN["after"][1]]
    on_deploy = sum(1 for d in inwin if d in deploys)
    reliable = not (inwin and on_deploy / len(inwin) > 0.8)
    return {u.rstrip("/"): d for u, d in lm.items()}, reliable


# Columns A-I are shared with section B further down the same tab, where G is
# the wide "Rationale" column and I is a narrow Y/N. Section A must not retune
# them or it breaks the candidate table. J-N belong to section A alone.
SECTION_A_WIDTHS = {9: 110, 10: 100, 11: 100, 12: 260, 13: 380}


NUMBER_FORMATS = ((("C", "D"), "0.0"),
                  (("E", "F", "G", "H", "I", "J"), "#,##0"),
                  (("K", "L"), "0.00"))


def apply_number_formats(sheet_id: str, tab: str, r0: int, r1: int) -> None:
    """Per-column display formats for section A.

    Called TWICE, and both are needed. Before the write, because write()
    verifies by reading the cell back and a stale format renders 0.09 as "0.1",
    failing a correct write. After format_section_a, because copying A-G's
    formatting onto H-N carries its number formats with it - that is what put
    one decimal on Page Impr After and printed 19002.0.
    """
    for cols, pattern in NUMBER_FORMATS:
        for col in cols:
            try:
                S.set_number_format(sheet_id, f"'{tab}'!{col}{r0}:{col}{r1}", pattern)
            except Exception:
                pass


def format_section_a(sheet_id: str, tab: str, header_row: int, n_rows: int) -> None:
    """Extend the tab's own styling across the new columns.

    The workbook was built seven columns wide, so H-N land unstyled - no header
    fill, no borders - and the section reads as two different tables. Rather
    than hardcode a palette, copy the format the client's own sheet already
    uses for A-G onto H-N, so each workbook keeps its own look.
    """
    sid = S.tab_id(sheet_id, tab)
    hdr0 = header_row - 1
    reqs = [
        {"copyPaste": {
            "source": {"sheetId": sid, "startRowIndex": hdr0, "endRowIndex": hdr0 + 1,
                       "startColumnIndex": 0, "endColumnIndex": 7},
            "destination": {"sheetId": sid, "startRowIndex": hdr0, "endRowIndex": hdr0 + 1,
                            "startColumnIndex": 7, "endColumnIndex": 14},
            "pasteType": "PASTE_FORMAT"}},
        {"copyPaste": {
            "source": {"sheetId": sid, "startRowIndex": hdr0 + 1,
                       "endRowIndex": hdr0 + 1 + n_rows,
                       "startColumnIndex": 0, "endColumnIndex": 7},
            "destination": {"sheetId": sid, "startRowIndex": hdr0 + 1,
                            "endRowIndex": hdr0 + 1 + n_rows,
                            "startColumnIndex": 7, "endColumnIndex": 14},
            "pasteType": "PASTE_FORMAT"}},
    ]
    for idx, px in SECTION_A_WIDTHS.items():
        reqs.append({"updateDimensionProperties": {
            "range": {"sheetId": sid, "dimension": "COLUMNS",
                      "startIndex": idx, "endIndex": idx + 1},
            "properties": {"pixelSize": px}, "fields": "pixelSize"}})
    S._call(S.service().spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": reqs}))

    # Freezing the Keyword column would help on a 14-column tab, but the section
    # banners are merged across the row and Sheets refuses to freeze part of a
    # merge. Attempted separately so a refusal cannot roll back the formatting
    # above, which is the part that matters.
    try:
        S._call(S.service().spreadsheets().batchUpdate(
            spreadsheetId=sheet_id, body={"requests": [{"updateSheetProperties": {
                "properties": {"sheetId": sid,
                               "gridProperties": {"frozenColumnCount": 1}},
                "fields": "gridProperties.frozenColumnCount"}}]}))
    except Exception:
        pass


def build(slug: str, cfg: dict, svc) -> int:
    _key, prior = PW.previous_workbook(cfg, WIN["run"])
    if not prior:
        print(f"{slug:<22} no prior workbook, section A stays baseline")
        return 0

    sel = []
    for d in PW.worked_pages(prior):
        # Every page worked last month is a 2.3 page now. Prior workbooks numbered the same work 2.3, 2.4,
        # 2.5 and 3.1; those numbers no longer exist and must not reach a sheet.
        sel.append({"page": d["page"], "q": target_label(d["query"])})
    if not sel:
        print(f"{slug:<22} last month's workbook worked no pages")
        return 0

    lm, reliable = ship_dates(cfg)
    site = cfg["gsc_property"]
    money, _posts, _scope = T.scope(cfg)
    client_terms = R._service_terms(cfg, money)
    bpages = all_pages(svc, site, *WIN["before"])
    apages = all_pages(svc, site, *WIN["after"])
    for s in sel:
        s["recorded"], s["page"] = s["page"], landing(s["page"])
    worked = {u.rstrip("/") for x in sel for u in (x["recorded"], x["page"])}
    body = []
    for s in sel:
        brands = brand_keys(cfg)
        same = (s["recorded"],)
        brows = without_brand(page_queries(svc, site, s["page"], *WIN["before"], also=same), brands)
        arows = without_brand(page_queries(svc, site, s["page"], *WIN["after"], also=same), brands)
        pick, exact, rejected = resolve_query(
            s["q"], without_brand(page_queries(svc, site, s["page"], *WIN["resolve"], also=same), brands),
            s["page"], client_terms,
            measurable=set(brows) | set(arows),
            both=set(brows) & set(arows))
        shown = s["q"] or "(page-level)"
        if pick and not exact:
            shown = pick["keys"][0]

        # Blank rather than zero when the query did not surface in a window:
        # 0 clicks at position 4 and no rows at all are different facts.
        pos = pos_a = clicks = clicks_a = ""
        if pick:
            q = pick["keys"][0]
            brow, arow = brows.get(q), arows.get(q)
            # Real numbers, never pre-formatted strings. A string cell is left
            # aligned, cannot be sorted or charted and is invisible to a formula;
            # sheets_io applies the thousands separator as a cell FORMAT so the
            # cell keeps holding a number. Standing rule in _autoformat().
            if brow:
                pos, clicks = round(brow["position"], 1), int(brow["clicks"])
            if arow:
                pos_a, clicks_a = round(arow["position"], 1), int(arow["clicks"])

        d = lm.get(s["page"].rstrip("/")) or lm.get(s["recorded"].rstrip("/"))
        bn, an, yr = WIN["before_name"], WIN["after_name"], WIN["year"]
        w0, w1 = WIN["after"]
        if not reliable or d is None:
            when = "Edit date not confirmed from this site's sitemap"
            share = ""
        elif w0 <= d <= w1:
            post = (w1 - d).days + 1
            when = f"Change went live {d}"
            share = f" {an} is {100 * post / ((w1 - w0).days + 1):.0f}% post-change."
        else:
            when = f"Page last changed {d}, outside the {an} work window"
            share = ""

        key = s["page"].rstrip("/")
        rkey = s["recorded"].rstrip("/")
        pb, pa = (combine(bpages.get(key), bpages.get(rkey) if rkey != key else None),
                  combine(apages.get(key), apages.get(rkey) if rkey != key else None))
        measured = ["Recorded in 2.3 Page Optimizations."]
        if rkey != key:
            measured.append(f"This page moved from {s['recorded'].replace(site.rstrip('/'), '')}; "
                            "traffic at both addresses is counted.")
        if pick and not exact and s["q"]:
            measured.append(f"Best intent match in the \"{s['q']}\" target family.")
        elif pick and not exact:
            measured.append("Page-level target; this is the page's strongest query on its own subject.")
        if pick and not pos_a:
            measured.append(f"This query returned no Search Console rows for this page in {an}.")
        if not pick:
            if (pb and pb["impressions"]) or (pa and pa["impressions"]):
                # Page-level data exists. "No query to pick" is not "no impressions".
                measured.append("No single query is recorded as this page's target, so this row "
                                "compares the page as a whole.")
            else:
                measured.append(f"This page returned no Search Console impressions at all in {bn} or "
                                f"{an} {yr}, so there is nothing to compare.")
        note = S.compose(
            ("Target", measured),
            ("Timing", [f"{when}.", f"Before {bn} {yr}, after {an} {yr}.", share.strip()]),
            ("Reading", "Treat it as an early reading; Google normally needs three to four weeks to "
                        "re-read a page."),
            where=s["page"])
        # Page level, from the page dimension. Average position is deliberately
        # NOT carried: it is impression-weighted across every query the page
        # surfaces for, so a page that starts winning MORE terms reads as if it
        # got worse. EW's Danielson page went 7.4 -> 14.8 while clicks went
        # 21 -> 48. Reporting that column would call a win a loss.
        pc_b = int(pb["clicks"]) if pb else ""
        pc_a = int(pa["clicks"]) if pa else ""
        pi_b = int(pb["impressions"]) if pb else ""
        pi_a = int(pa["impressions"]) if pa else ""
        # Percentage POINTS, not a ratio with a % cell format. read() returns a
        # percent-formatted cell as "1.55%", which no longer equals the 0.0155
        # that was sent, and write()'s read-back verification would reject a
        # correct write. The unit lives in the header instead.
        ct_b = round(100 * pb["clicks"] / pb["impressions"], 2) if pb and pb["impressions"] else ""
        ct_a = round(100 * pa["clicks"] / pa["impressions"], 2) if pa and pa["impressions"] else ""
        control = control_for(s["page"], worked, bpages, apages)

        body.append([shown, s["page"], pos, pos_a, clicks, clicks_a,
                     pc_b, pc_a, pi_b, pi_a, ct_b, ct_a, control, note])

    # The client's own CTR by position band is part of Section A (1.5 recipe), so
    # next month judges a CTR claim against it rather than a generic curve. The
    # first-month baseline row carried it. From the second month this section
    # replaces that row, so the curve is carried here as the section's last row.
    res = T.analyse(svc, site, cfg)
    body.append(["CLIENT CTR CURVE", "", "", "", "", "", "", "", "", "", "", "", "",
                 S.compose(("Client CTR curve",
                            [f"By position band, {res['month'][0]:%B %Y}: {T.ctr_curve_text(res['sd'])}.",
                             "Judge any CTR claim against this, not a generic curve."]),
                           where="CTR curve")])

    header = ["Keyword", "Page", "Query Pos Before", "Query Pos After",
              "Query Clicks Before", "Query Clicks After",
              "Page Clicks Before", "Page Clicks After",
              "Page Impr Before", "Page Impr After",
              "Page CTR Before (%)", "Page CTR After (%)",
              "Control (untouched pages, same window)", "Notes"]
    if DRY:
        n = 0
    else:
        p = S.find_rows(cfg["sheet_id"], TAB, {"a": "Keyword", "b": "Rank"})
        # Section B's title row sits at p['b'] - 1. Rows between the header and
        # that title are this section's; grow it rather than overwrite section B.
        room = (p["b"] - 2) - p["a"]
        if len(body) > room:
            S.insert_rows(cfg["sheet_id"], TAB, p["b"] - 1, len(body) - room)
            p = S.find_rows(cfg["sheet_id"], TAB, {"a": "Keyword", "b": "Rank"})
        S.clear(cfg["sheet_id"], f"'{TAB}'!A{p['a']}:N{p['b'] - 2}")
        # The baseline banner is a merged row. When Section A grows, that merge ends up under a data row
        # and Google refuses the format copy ("partially intersects a merge"): EW failed on it. Section A's
        # data rows are never merged, so any merge left there is removed.
        sid_ = S.tab_id(cfg["sheet_id"], TAB)
        S._call(S.service().spreadsheets().batchUpdate(spreadsheetId=cfg["sheet_id"], body={"requests": [
            {"unmergeCells": {"range": {"sheetId": sid_, "startRowIndex": p["a"], "endRowIndex": p["b"] - 2,
                                        "startColumnIndex": 0, "endColumnIndex": 14}}}]}))
        n = S.write(cfg["sheet_id"], f"'{TAB}'!A{p['a']}:N{p['a']}", [header]).cells
        # autoformat off: its float rule stamps 0.0 on the CTR column, so a
        # written 0.09 reads back as "0.1" and write()'s own verification
        # rejects a correct write. Formats are applied per column below, after
        # the read-back has compared raw values.
        r0, r1 = p["a"] + 1, p["a"] + len(body)
        # Formats FIRST. write() verifies by reading the cell back, and a cell
        # carries whatever format it already had - a 0.0 left over from an
        # earlier run renders a written 0.09 as "0.1" and the write is rejected
        # as unverified. Setting the format before the value makes the read-back
        # agree with what was sent.
        apply_number_formats(cfg["sheet_id"], TAB, r0, r1)
        n += S.write(cfg["sheet_id"], f"'{TAB}'!A{r0}:N{r1}", body,
                     autoformat=False).cells
        format_section_a(cfg["sheet_id"], TAB, p["a"], len(body))
        apply_number_formats(cfg["sheet_id"], TAB, r0, r1)
        try:
            S.set_font_size(cfg["sheet_id"], f"'{TAB}'!A{r0}:N{r1}")
        except Exception:
            pass
    withpos = sum(1 for b in body if b[2])
    witha = sum(1 for b in body if b[3])
    print(f"{slug:<22} section A rows {len(body)}  before-pos {withpos}  after-pos "
          f"{witha}  cells {n}  ship-date {'sitemap' if reliable else 'unconfirmed'}")
    for b in body:
        c = [f"{v:,}" if isinstance(v, int) else (f"{v}" if v != "" else "") for v in b]
        print(f"     {b[0][:34]:34} qpos {c[2]:>5}->{c[3]:<5} qclk {c[4]:>4}->{c[5]:<4} "
              f"| page clk {c[6]:>5}->{c[7]:<5} impr {c[8]:>6}->{c[9]:<6} "
              f"ctr {c[10]:>5}->{c[11]:<5}")
        print(f"       control: {b[12] or '(none)'}   {b[1][-52:]}")
    return len(body)


DRY = False


def main() -> int:
    global DRY
    if "--dry-run" in sys.argv:
        DRY = True
        sys.argv.remove("--dry-run")
    run = dt.date.today().replace(day=1)
    if "--month" in sys.argv:
        i = sys.argv.index("--month")
        y, m = sys.argv[i + 1].split("-")
        run = dt.date(int(y), int(m), 1)
        del sys.argv[i:i + 2]
    set_windows(run)
    WIN["run"] = run
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    want = sys.argv[1] if len(sys.argv) > 1 else "all"
    todo = ([k for k, v in reg.items() if isinstance(v, dict) and v.get("sheet_id")]
            if want == "all" else [want])
    svc = T.sc()
    for slug in todo:
        try:
            build(slug, reg[slug], svc)
        except Exception as e:
            print(f"{slug:<22} FAILED {e.__class__.__name__}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
