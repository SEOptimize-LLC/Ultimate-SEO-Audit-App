"""TREND and BUSINESS CASE blocks for every 1.8 refresh target.

    python scripts/business_case_1_8.py <client|all> [--month YYYY-MM]

Owner rules, 2026-10-08:
- A refresh target is justified by its trend across windows, not one comparison: last 90 days vs the
  90 before and vs the same 90 last year, last 6 months vs the 6 before, and the last quarter vs the
  same quarter last year (decline_windows.py computes them).
- Organic performance only matters as business: each page shows its organic visits and leads (GA4,
  the client's approved lead events in clients/registry.yaml `ga4_lead_events`), and what getting back
  to its own level last year is worth in leads. Measured from the page's history, never modelled.
- No dollar figures until the client supplies job values and close rates.

Inputs, in `<client folder>/monthly_plan/`:
  plan.yaml                  the month's refresh targets
  trend-<month>.json         written here if missing (decline_windows.analyse)
  ga4-pages-<month>.json     organic sessions and lead events per landing page for q3_2025, q3_2026
                             and last12. The GA4 API needs gcloud ADC; when that has expired, pull the
                             same report through the analytics connector and save it in this shape.
Output: business-case-<month>.yaml, {url: block}. fill_1_8.py merges each block into the 2.3 Pages
context cell, after the baseline.

Percentages are shown only when the earlier window had at least 10 clicks; below that a percentage is
noise (one page read +7,433% on 4 clicks).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import decline_windows as DW                          # noqa: E402
import sheets_io                                      # noqa: E402

MIN_BASE = 10          # clicks: below this an earlier window is too small for a percentage or a verdict
FALL, RISE = -20, 20   # percent change that counts as down / up
CLIENTS = ("barts", "superior", "sameday", "beehive", "comfort", "cudio", "educationwalkthrough")


def _pct(now: int, then: int) -> str:
    if then < MIN_BASE:
        return ""
    p = round(100 * (now - then) / then)
    return f" ({'+' if p > 0 else ''}{p}%)"


def trend_block(a: dict) -> str:
    w = a["windows"]
    k = list(w)
    d90, prev90, yoy90 = w[k[0]]["now"], w[k[0]]["then"], w[k[1]]["then"]
    m6, m6p = w[k[2]]["now"], w[k[2]]["then"]
    seen = any(x[s]["impressions"] for x in w.values() for s in ("now", "then"))
    if not seen:
        return ("TREND (NO SEARCH HISTORY YET)\n"
                "• No clicks or impressions at this address in the last 16 months; any history sits on an older URL.")
    comparable = [x for x in w.values() if x["then"]["clicks"] >= MIN_BASE]
    down = [x for x in comparable if (x["clicks_pct"] or 0) <= FALL]
    up = [x for x in comparable if (x["clicks_pct"] or 0) >= RISE]
    names = dict(zip(k, ("PRIOR 90 DAYS", "LAST YEAR", "PRIOR 6 MONTHS", "LAST YEAR'S QUARTER")))
    if not comparable:
        label = "TREND (LOW VOLUME)"
    elif len(comparable) == 1:      # one comparison is a signal, not a verdict: name it
        name = names[next(n for n, x in w.items() if x is comparable[0])]
        label = f"TREND (DOWN ON {name})" if down else f"TREND (UP ON {name})" if up else "TREND (FLAT)"
    elif len(down) == len(comparable) == len(w):
        label = "TREND (DOWN IN EVERY WINDOW)"
    elif len(down) == len(comparable):
        label = "TREND (DOWN WHERE COMPARABLE)"
    elif down:
        label = f"TREND (DOWN IN {len(down)} OF {len(comparable)} WINDOWS)"
    elif len(up) == len(comparable):
        label = "TREND (GROWING)"
    else:
        label = "TREND (FLAT)"
    lines = [f"• Clicks, last 90 days: {d90['clicks']}, against {prev90['clicks']} the 90 days before"
             f"{_pct(d90['clicks'], prev90['clicks'])} and {yoy90['clicks']} a year ago"
             f"{_pct(d90['clicks'], yoy90['clicks'])}."]
    six = f"• Last 6 months: {m6['clicks']} against {m6p['clicks']}{_pct(m6['clicks'], m6p['clicks'])}."
    p_now, p_then = w[k[1]]["now"]["position"], yoy90["position"]
    post = a.get("post_shift")
    if not w[k[1]].get("impr_comparable", True):
        # Year-ago positions fall in Google's May 2025-Apr 2026 logging error (reporting_break.py).
        if p_now and post and post.get("position"):
            six += (f" Position #{post['position']:.1f} in May-July 2026, #{p_now:.1f} now "
                    "(Search Console misreported position from May 2025 to April 2026).")
    elif p_now and p_then:
        six += f" Position #{p_then:.1f} a year ago, #{p_now:.1f} now."
    lines.append(six)
    return label + "\n" + "\n".join(lines)


def _count(page: dict, events: list[str], rng: str) -> int:
    return sum(int((page.get(e) or {}).get(rng, 0)) for e in events)


def business_block(cfg: dict, url: str, ga4: dict, note: str = "") -> str:
    path = urlparse(url).path.rstrip("/") or "/"
    page = ga4.get(path) or ga4.get(path + "/") or {}
    leads_ev = cfg.get("ga4_lead_events") or []
    dl_ev = cfg.get("ga4_download_events") or []
    v12, vthen, vnow = (_count(page, ["session_start"], r) for r in ("last12", "q3_2025", "q3_2026"))
    l12, lthen, lnow = (_count(page, leads_ev, r) for r in ("last12", "q3_2025", "q3_2026"))
    dl = _count(page, dl_ev, "last12")
    noun = lambda n: "lead" if n == 1 else "leads"  # noqa: E731
    out = []
    if not v12 and not vthen:
        out.append("• No organic visits recorded on this page in 12 months (GA4).")
    else:
        line = f"• 12 months: {v12:,} organic {'visit' if v12 == 1 else 'visits'}, {l12} {noun(l12)} (GA4)."
        if dl:
            line += f" Plus {dl} PDF or template downloads."
        out.append(line)
    if max(vthen, vnow) >= 20:
        line = f"• Jul-Sep organic visits: {vthen:,} last year, {vnow:,} now; {noun(2)} {lthen} to {lnow}."
        if vthen > vnow:
            if lthen > lnow:
                line += f" Back at last year's level is {lthen - lnow} more {noun(lthen - lnow)} a quarter."
            elif l12 >= 3 and v12:
                est = round((vthen - vnow) * l12 / v12)
                line += (f" Back at last year's visits, about {est} more {noun(est)} a quarter at this page's rate."
                         if est >= 1 else " At this page's rate, that is under one lead a quarter.")
            else:
                line += " Too few leads here to project a recovery."
        out.append(line)
    if note:                        # a verified, page-specific reading of the numbers (plan target `bc_note`)
        out.append(f"• {note}")
    # The client-wide tracking gap qualifies lead counts, so it rides only on pages with real lead
    # counts: repeated on every row it is boilerplate (sheet-cells rule).
    if cfg.get("ga4_tracking_gap") and l12 + lthen >= 3:
        out.append(f"• {cfg['ga4_tracking_gap']}")
    return "BUSINESS CASE\n" + "\n".join(out)


def build(slug: str, month: str, reg: dict) -> dict[str, str]:
    cfg = reg[slug]
    d = Path(cfg["folder"]) / "monthly_plan"
    plan = yaml.safe_load(open(d / "plan.yaml", encoding="utf-8"))
    targets = plan.get("targets") or []
    ga4_f = d / f"ga4-pages-{month}.json"
    if not ga4_f.exists():
        raise SystemExit(f"{slug}: {ga4_f} is missing. Pull organic sessions and the approved lead events per "
                         "landing page (q3_2025, q3_2026, last12) and save them there first.")
    ga4 = json.loads(ga4_f.read_text(encoding="utf-8"))["pages"]
    trend_f = d / f"trend-{month}.json"
    trends = {a["url"]: a for a in json.loads(trend_f.read_text(encoding="utf-8"))} if trend_f.exists() else {}
    missing = [t["url"] for t in targets if t["url"] not in trends]
    if missing:
        import gsc_api
        svc = gsc_api.service()
        for u in missing:
            trends[u] = DW.analyse(svc, cfg["gsc_property"], u)
        trend_f.write_text(json.dumps(list(trends.values()), indent=1), encoding="utf-8")
    cases = {}
    for t in targets:
        block = trend_block(trends[t["url"]]) + "\n\n" + business_block(cfg, t["url"], ga4, t.get("bc_note", ""))
        cases[t["url"]] = sheets_io.check_cell(block, f"{slug} business case {t['url']}")
    (d / f"business-case-{month}.yaml").write_text(
        yaml.safe_dump(cases, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    return cases


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--month", default=date.today().strftime("%Y-%m"))
    args = ap.parse_args()
    reg = yaml.safe_load(open(Path(__file__).parent.parent / "clients" / "registry.yaml", encoding="utf-8"))
    for slug in (CLIENTS if args.client == "all" else (args.client,)):
        cases = build(slug, args.month, reg)
        print(f"\n##### {slug}: {len(cases)} refresh target(s)")
        for u, b in cases.items():
            print(f"--- {u}  ({len(b)} chars)\n{b}")


if __name__ == "__main__":
    main()
