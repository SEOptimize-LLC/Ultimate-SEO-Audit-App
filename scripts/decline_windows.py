"""Is this page in decline? Clicks, impressions and position across the windows the owner reads.

    python scripts/decline_windows.py <client> <url> [<url> ...] [--json out.json]

Owner rule (2026-10-08): a refresh target is justified by its trend, not one comparison.
Every page gets three windows against their baselines, plus the monthly series:

  last 90 days     vs the 90 days before, and vs the same 90 days last year
  last 6 months    vs the 6 months before (Search Console keeps 16 months, so the
                   same 6 months last year is out of reach until it ages in)
  same quarter     the last full calendar quarter vs the same quarter last year

Search Console data runs about three days behind, so windows end three days ago.
The trailing-slash and unslashed forms of a URL are summed: Search Console splits them.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import gsc_api                                        # noqa: E402
import reporting_break as RB                          # noqa: E402

LAG_DAYS = 3


def _q(svc, prop: str, url: str, start: date, end: date, dims=None) -> list[dict]:
    """Rows for both slash forms of `url`, summed per key."""
    forms = {url.rstrip("/"), url.rstrip("/") + "/"}
    out: dict[tuple, dict] = {}
    for form in forms:
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "dimensions": dims or [],
                "dimensionFilterGroups": [{"filters": [{"dimension": "page", "operator": "equals",
                                                        "expression": form}]}], "rowLimit": 1000}
        for r in svc.searchanalytics().query(siteUrl=prop, body=body).execute().get("rows", []):
            k = tuple(r.get("keys", []))
            cur = out.setdefault(k, {"clicks": 0, "impressions": 0, "pos_w": 0.0})
            cur["clicks"] += r["clicks"]
            cur["impressions"] += r["impressions"]
            cur["pos_w"] += r["position"] * r["impressions"]
    return [{"keys": list(k), "clicks": v["clicks"], "impressions": v["impressions"],
             "position": v["pos_w"] / v["impressions"] if v["impressions"] else None}
            for k, v in sorted(out.items())]


def window(svc, prop, url, start, end) -> dict:
    rows = _q(svc, prop, url, start, end)
    r = rows[0] if rows else {"clicks": 0, "impressions": 0, "position": None}
    return {"start": start.isoformat(), "end": end.isoformat(), "clicks": r["clicks"],
            "impressions": r["impressions"], "position": r["position"]}


def _pct(new, old):
    return None if not old else round(100 * (new - old) / old)


def analyse(svc, prop: str, url: str, today: date | None = None) -> dict:
    end = (today or date.today()) - timedelta(days=LAG_DAYS)
    d90 = window(svc, prop, url, end - timedelta(days=89), end)
    d90_prev = window(svc, prop, url, end - timedelta(days=179), end - timedelta(days=90))
    d90_yoy = window(svc, prop, url, end - timedelta(days=89 + 365), end - timedelta(days=365))
    m6 = window(svc, prop, url, end - timedelta(days=182), end)
    m6_prev = window(svc, prop, url, end - timedelta(days=365), end - timedelta(days=183))
    q_end = date(end.year, ((end.month - 1) // 3) * 3 + 1, 1) - timedelta(days=1)
    q_start = date(q_end.year, q_end.month - 2, 1)
    qtr = window(svc, prop, url, q_start, q_end)
    qtr_yoy = window(svc, prop, url, q_start.replace(year=q_start.year - 1), q_end.replace(year=q_end.year - 1))
    monthly = _q(svc, prop, url, end - timedelta(days=480), end, ["date"])
    months: dict[str, dict] = {}
    for r in monthly:
        m = months.setdefault(r["keys"][0][:7], {"clicks": 0, "impressions": 0, "pos_w": 0.0})
        m["clicks"] += r["clicks"]
        m["impressions"] += r["impressions"]
        m["pos_w"] += (r["position"] or 0) * r["impressions"]
    series = [{"month": k, "clicks": v["clicks"], "impressions": v["impressions"],
               "position": round(v["pos_w"] / v["impressions"], 1) if v["impressions"] else None}
              for k, v in sorted(months.items())]
    starts = {"last 90 days vs prior 90": end - timedelta(days=179),
              "last 90 days vs same 90 last year": end - timedelta(days=89 + 365),
              "last 6 months vs prior 6": end - timedelta(days=365),
              "quarter": q_start.replace(year=q_start.year - 1)}
    broken = RB.has_break(svc, prop)
    comps = {
        "last 90 days vs prior 90": (d90, d90_prev),
        "last 90 days vs same 90 last year": (d90, d90_yoy),
        "last 6 months vs prior 6": (m6, m6_prev),
        f"{q_start:%b}-{q_end:%b %Y} vs same quarter last year": (qtr, qtr_yoy),
    }
    out = {"url": url, "windows": {}, "monthly": series, "shifted": broken}
    for name, (a, b) in comps.items():
        start = starts.get(name, starts["quarter"])
        # Google's logging error (reporting_break.py: May 13, 2025 to April 27, 2026): impressions and
        # position from before October 2025 are not comparable; clicks are.
        ok = not RB.affects(start, broken)
        out["windows"][name] = {"now": a, "then": b, "clicks_pct": _pct(a["clicks"], b["clicks"]),
                                "impr_pct": _pct(a["impressions"], b["impressions"]) if ok else None,
                                "impr_comparable": ok}
    if any(not w["impr_comparable"] for w in out["windows"].values()):
        out["post_shift"] = window(svc, prop, url, *RB.POST)
    falling = [n for n, w in out["windows"].items() if (w["clicks_pct"] or 0) <= -20]
    out["verdict"] = ("declining in every window" if len(falling) == len(comps)
                      else f"declining in {len(falling)} of {len(comps)} windows" if falling
                      else "not declining")
    return out


def show(a: dict) -> None:
    print(f"\n## {a['url']}\n   VERDICT: {a['verdict']}")
    for name, w in a["windows"].items():
        n, t = w["now"], w["then"]
        pos = lambda p: f"#{p:.1f}" if p else "  -  "  # noqa: E731
        print(f"   {name:40} clicks {t['clicks']:>5} -> {n['clicks']:>5} ({w['clicks_pct'] if w['clicks_pct'] is not None else '-':>4}%)"
              + (f"  impr {t['impressions']:>8,} -> {n['impressions']:>8,}  pos {pos(t['position'])} -> {pos(n['position'])}"
                 if w.get("impr_comparable", True) else "  impr/pos: not comparable (Google logging error, May 2025-Apr 2026)"))
    if a.get("post_shift"):
        p = a["post_shift"]
        print(f"   {RB.POST_LABEL} (first clean quarter): clicks {p['clicks']}  impr {p['impressions']:,}"
              f"  pos {('#%.1f' % p['position']) if p['position'] else '-'}")
    print("   monthly: " + "  ".join(f"{m['month'][2:]}:{m['clicks']}" for m in a["monthly"]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--json")
    args = ap.parse_args()
    reg = yaml.safe_load(open(Path(__file__).parent.parent / "clients" / "registry.yaml", encoding="utf-8"))
    prop = reg[args.client]["gsc_property"]
    svc = gsc_api.service()
    res = [analyse(svc, prop, u) for u in args.urls]
    for a in res:
        show(a)
    if args.json:
        Path(args.json).write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
