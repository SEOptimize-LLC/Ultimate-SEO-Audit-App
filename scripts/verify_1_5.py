#!/usr/bin/env python
"""Independent check of a client's 1.5 tab: re-derive every figure through a different request shape.

    python scripts/verify_1_5.py <client> [--month YYYY-MM]

fill_1_5_section_a.py and run_1_5.py pull page and query data in bulk. This reads what is actually IN
the sheet and re-derives each figure from a separate, page-filtered request, so a defect in the bulk path
(it once let a 3-impression URL variant overwrite a 10,985-impression page) cannot pass its own check.

Windows come from the sheet, not from the scripts: Section A's notes say "Before August 2026, after
September 2026", and Section B's windows are the three complete months ending last month.

Exit 0 when every figure matches, 1 on any mismatch, 2 when it could not run.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io as S          # noqa: E402
import task_1_5 as T           # noqa: E402

TAB = "1.5 Candidate List"
MONTHS = {m: i for i, m in enumerate(calendar.month_name) if m}
FAILS: list[str] = []
CHECKED = 0


def month_window(name: str, year: int):
    n = MONTHS[name]
    return dt.date(year, n, 1), dt.date(year, n, calendar.monthrange(year, n)[1])


def shift(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    return dt.date(d.year + y, m + 1, 1)


def check(label: str, sheet, derived, tol: float = 0.0501):
    """Compare one figure. Blank in the sheet must also be blank (None) here."""
    global CHECKED
    CHECKED += 1
    if sheet in ("", None) and derived in ("", None):
        return
    try:
        num = lambda v: float(str(v).replace(",", ""))   # the sheet hands numbers back as "6,073"
        ok = sheet not in ("", None) and derived not in ("", None) and abs(num(sheet) - num(derived)) <= tol
    except (TypeError, ValueError):
        ok = str(sheet) == str(derived)
    if not ok:
        FAILS.append(f"{label}: sheet {sheet!r} vs re-derived {derived!r}")


class Pull:
    """Page-filtered requests, one page at a time, summed over URL spellings."""

    def __init__(self, svc, site: str):
        self.svc, self.site = svc, site
        host = re.escape(site.rstrip("/"))
        path = lambda u: re.escape(u.replace(site.rstrip("/"), "").rstrip("/"))
        # `also` are other addresses of the same page (the URL it moved from), summed in.
        self.rx = lambda url, also=(): "^" + host + (
            path(url) if not also else "(?:" + "|".join(dict.fromkeys(path(u) for u in (url, *also))) + ")") + "/?(?:#.*)?$"

    def _rows(self, url, start, end, dims, extra=None, also=()):
        flt = [{"dimension": "page", "operator": "includingRegex", "expression": self.rx(url, also)}] + (extra or [])
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "dimensions": dims, "rowLimit": 5000,
                "dimensionFilterGroups": [{"filters": flt}]}
        return self.svc.searchanalytics().query(siteUrl=self.site, body=body).execute().get("rows", [])

    def page(self, url, start, end, also=()):
        rows = self._rows(url, start, end, ["page"], also=also)
        c = sum(r["clicks"] for r in rows)
        i = sum(r["impressions"] for r in rows)
        pos = sum(r["position"] * r["impressions"] for r in rows) / i if i else 0.0
        return {"clicks": int(c), "impressions": int(i), "position": pos}

    def query(self, url, q, start, end, also=()):
        rows = self._rows(url, start, end, ["query"], [{"dimension": "query", "operator": "equals", "expression": q}], also)
        i = sum(r["impressions"] for r in rows)
        if not i:
            return None
        return {"clicks": int(sum(r["clicks"] for r in rows)), "impressions": int(i),
                "position": sum(r["position"] * r["impressions"] for r in rows) / i}


def moved_from(cfg) -> dict:
    """dest url -> the addresses last month's workbook recorded for it, for pages that have since moved.

    Section A prints a page at the address that serves it, while its 'before' traffic sits under the
    address it was worked at. Read from the prior workbook and a live redirect check, not from the sheet
    under test."""
    import prior_work as PW
    import run_1_5 as R
    _key, prior = PW.previous_workbook(cfg)
    out: dict = {}
    for d in (PW.worked_pages(prior) if prior else []):
        page = R._onpage(d["page"])
        if page and page.get("status") == 200:
            dest = (page.get("final") or d["page"]).split("?")[0].rstrip("/")
            if dest != d["page"].rstrip("/"):
                out.setdefault(dest, []).append(d["page"])
    return out


def verify_section_a(sid, pull, rows, first, aliases=None):
    wins = None
    for off, row in enumerate(rows):
        r = first + off
        if not row or not row[0] or row[0] == "CLIENT CTR CURVE" or len(row) < 12 or not str(row[1]).startswith("http"):
            continue
        note = row[13] if len(row) > 13 else ""
        m = re.search(r"Before (\w+) (\d{4}), after (\w+) (\d{4})", note)
        if not m:
            FAILS.append(f"row {r}: notes carry no 'Before <month>, after <month>' to take the windows from")
            continue
        before, after = month_window(m[1], int(m[2])), month_window(m[3], int(m[4]))
        wins = (before, after)
        url = row[1]
        also = (aliases or {}).get(url.rstrip("/"), ())
        pb, pa = pull.page(url, *before, also=also), pull.page(url, *after, also=also)

        def cell(i):
            return row[i] if len(row) > i else ""

        check(f"A r{r} page clicks before", cell(6), pb["clicks"] if pb["impressions"] else "")
        check(f"A r{r} page clicks after", cell(7), pa["clicks"] if pa["impressions"] else "")
        check(f"A r{r} page impr before", cell(8), pb["impressions"] if pb["impressions"] else "")
        check(f"A r{r} page impr after", cell(9), pa["impressions"] if pa["impressions"] else "")
        check(f"A r{r} CTR before", cell(10), round(100 * pb["clicks"] / pb["impressions"], 2) if pb["impressions"] else "", 0.0101)
        check(f"A r{r} CTR after", cell(11), round(100 * pa["clicks"] / pa["impressions"], 2) if pa["impressions"] else "", 0.0101)
        q = row[0]
        if q != "(page-level)":
            qb, qa = pull.query(url, q, *before, also=also), pull.query(url, q, *after, also=also)
            check(f"A r{r} query pos before", cell(2), round(qb["position"], 1) if qb else "")
            check(f"A r{r} query pos after", cell(3), round(qa["position"], 1) if qa else "")
            check(f"A r{r} query clicks before", cell(4), qb["clicks"] if qb else "")
            check(f"A r{r} query clicks after", cell(5), qa["clicks"] if qa else "")
    return wins


def verify_section_b(pull, rows, first, after_window):
    last_month_start, last_month_end = after_window
    cur_end = last_month_end
    cur_start = shift(last_month_start, -2)
    pri_end = cur_start - dt.timedelta(days=1)
    pri_start = shift(cur_start, -3)
    for off, row in enumerate(rows):
        r = first + off
        if not row or len(row) < 9 or not str(row[1]).startswith("http"):
            continue
        url, src, q, pos, impr, why = row[1], row[2], row[3], row[4], row[5], row[6]
        if src == "Striking Distance":
            d = pull.query(url, q, last_month_start, last_month_end)
            check(f"B r{r} {q!r} impressions", impr, d["impressions"] if d else "")
            check(f"B r{r} {q!r} position", pos, round(d["position"], 1) if d else "")
        else:
            cur, pri = pull.page(url, cur_start, cur_end), pull.page(url, pri_start, pri_end)
            check(f"B r{r} decay impressions", impr, cur["impressions"])
            check(f"B r{r} decay position", pos, round(cur["position"], 1))
            # The three rationale shapes: "position 8.6 to 15.2, clicks 76 to 17", "position held at 15.4 to
            # 14.9 while impressions fell 2,168 to 1,307, clicks 41 to 15", and "position 15.6 to 14.9,
            # impressions 7,061 to 6,731, clicks 38 to 25".
            pm = re.search(r"position (?:held at )?([\d.]+) to ([\d.]+)", why)
            cm = re.search(r"clicks (\d+) to (\d+)", why)
            im = re.search(r"impressions (?:fell |rose )?([\d,]+) to ([\d,]+)", why)
            if pm and cm:
                check(f"B r{r} decay position before", pm[1], round(pri["position"], 1))
                check(f"B r{r} decay clicks before", cm[1], pri["clicks"])
                check(f"B r{r} decay clicks after", cm[2], cur["clicks"])
                if im:
                    check(f"B r{r} decay impressions before", im[1], pri["impressions"])
                    check(f"B r{r} decay impressions after", im[2], cur["impressions"])
            else:
                FAILS.append(f"B r{r}: decay rationale has no position and clicks movement to verify")
        if not str(why).startswith("ACTION:"):
            FAILS.append(f"B r{r}: rationale does not open with ACTION")
        if row[8] not in ("Y", "N"):
            FAILS.append(f"B r{r}: Selected in 1.8? is {row[8]!r}, not Y or N")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("client")
    a = ap.parse_args()
    cfg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))[a.client]
    sid = cfg["sheet_id"]
    try:
        pull = Pull(T.sc(), cfg["gsc_property"])
        grid = S.read(sid, f"'{TAB}'!A1:N60")
    except Exception as exc:
        print(f"CANNOT RUN: {exc.__class__.__name__}: {str(exc)[:200]}")
        return 2
    hdr_a = next(i for i, r in enumerate(grid) if r and r[0] == "Keyword")
    hdr_b = next(i for i, r in enumerate(grid) if r and r[0] == "Rank")
    rows_a = grid[hdr_a + 1: hdr_b - 1]
    rows_b = grid[hdr_b + 1:]
    wins = verify_section_a(sid, pull, rows_a, hdr_a + 2, moved_from(cfg))
    if wins:
        verify_section_b(pull, rows_b, hdr_b + 2, wins[1])
    print(f"{a.client}: {CHECKED} figures re-derived, {len(FAILS)} mismatches")
    for f in FAILS:
        print("  MISMATCH", f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
