#!/usr/bin/env python
"""Per-candidate evidence for a client's 1.5 tab, so every judgment is made from that row's own data.

    python scripts/evidence_1_5.py <client> [--no-live]

Builds the candidate list exactly as run_1_5.py would, with every sheet write intercepted (nothing is
written), then prints for each candidate: the live page, same-window year-over-year, sequential change,
eleven months of history, the page's real queries, and where the slug appears in the client's plan files.

This is the data REASONING.md says to read before writing a judgment field. It decides nothing.
"""
from __future__ import annotations

import argparse
import os
import re
import ssl
import sys
import urllib.request
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("GATE_LOG", "60")
import run_1_5 as R  # noqa: E402
import task_1_5 as T  # noqa: E402

# Files that list URLs for reasons other than work: audits, QA output, caches.
NOT_WORK_RECORDS = ("index_audit", "qa\\", "qa/", "gap_analysis", "tab-backups", "ai_visibility", "Competitor")


def rx(url: str) -> str:
    return "^" + re.escape(url.rstrip("/")) + "/?(?:#.*)?$"


class Ev:
    def __init__(self, svc, site):
        self.svc, self.site = svc, site

    def rows(self, url, start, end, dims, extra=None):
        flt = [{"dimension": "page", "operator": "includingRegex", "expression": rx(url)}] + (extra or [])
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(), "dimensions": dims, "rowLimit": 5000,
                "dimensionFilterGroups": [{"filters": flt}]}
        return self.svc.searchanalytics().query(siteUrl=self.site, body=body).execute().get("rows", [])

    def page(self, url, start, end):
        rows = self.rows(url, start, end, ["page"])
        i = sum(r["impressions"] for r in rows)
        return {"clicks": int(sum(r["clicks"] for r in rows)), "impr": int(i),
                "pos": (sum(r["position"] * r["impressions"] for r in rows) / i) if i else 0.0}

    def queries(self, url, start, end, n=7):
        rows = sorted(self.rows(url, start, end, ["query"]), key=lambda r: -r["impressions"])[:n]
        return [(r["keys"][0][:55], int(r["clicks"]), int(r["impressions"]), round(r["position"], 1)) for r in rows]


def live(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SEOAudit/1.0)"})
        r = urllib.request.urlopen(req, timeout=30, context=ctx)
        html = r.read().decode("utf-8", "replace")
        strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()
        t = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        h = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
        words = len(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", html)).split())
        return f"{r.status} | title: {strip(t.group(1) if t else '')[:90]} | h1: {strip(h.group(1) if h else '')[:90]} | ~{words} words"
    except Exception as e:
        return f"LIVE FETCH FAILED: {type(e).__name__} {getattr(e, 'code', '')}"


def plan_mentions(folder: Path, url: str):
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    out = []
    plan = folder / "monthly_plan"
    for f in (plan.rglob("*") if plan.exists() else []):
        if not f.is_file() or f.suffix.lower() not in (".md", ".yaml", ".yml", ".txt"):
            continue
        if any(x in str(f) for x in NOT_WORK_RECORDS):
            continue
        try:
            if slug and slug in f.read_text(encoding="utf-8", errors="ignore"):
                out.append(f.name)
        except OSError:
            pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--no-live", action="store_true")
    a = ap.parse_args()
    cfg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))[a.client]
    captured = {}

    class _Res:
        cells = 0

    R.S.write = lambda sid, a1, values, **kw: (captured.setdefault(a1, values), _Res())[1]
    R.S.clear = lambda *x, **k: None
    svc = R.sc()
    R.build(a.client, cfg, svc, R.NOTES.get(a.client, {}))
    cand = next((v for k, v in captured.items() if v and isinstance(v[0][0], int)), [])
    print(f"\n===== CANDIDATES ({len(cand)}) =====")
    (c0, c1), (p0, p1) = T.periods()
    y0, y1 = c0.replace(year=c0.year - 1), c1.replace(year=c1.year - 1)
    m0, m1 = T.latest_month()
    ev, site = Ev(svc, cfg["gsc_property"]), cfg["gsc_property"]
    print("CLIENT CTR CURVE:", R.ctr_curve_text(R.analyse(svc, site, cfg)["sd"]))
    print(f"windows: current {c0}..{c1} | prior {p0}..{p1} | year ago {y0}..{y1} | latest month {m0}..{m1}")
    folder = Path(cfg["folder"])
    for row in cand:
        rank, url, src, q, pos, impr, why, bv, sel = row[:9]
        print("\n" + "=" * 112)
        print(f"#{rank} {bv}/{sel} {src} | {url}\n   target: {q!r} pos {pos} impr {impr}")
        print("   RUNNER RATIONALE:", why[:300])
        if not a.no_live:
            print("   LIVE:", live(url))
        cur, pri, yoy = ev.page(url, c0, c1), ev.page(url, p0, p1), ev.page(url, y0, y1)
        print(f"   SEQUENTIAL  clicks {pri['clicks']}->{cur['clicks']}  impr {pri['impr']}->{cur['impr']}  pos {pri['pos']:.1f}->{cur['pos']:.1f}")
        print(f"   YEAR-OVER-YEAR clicks {yoy['clicks']}->{cur['clicks']}  impr {yoy['impr']}->{cur['impr']}  pos {yoy['pos']:.1f}->{cur['pos']:.1f}"
              + ("   (no prior-year data)" if not yoy["impr"] else ""))
        try:
            h = T.history(svc, site, url, months=11)
            print("   HISTORY   " + " | ".join(f"{m[2:]}:{d['clicks']}/{d['impressions']}/{d['position']:.1f}" if d else f"{m[2:]}:-" for m, d in h))
        except Exception as e:
            print("   HISTORY FAILED", type(e).__name__)
        if not q.startswith("("):
            tq = ev.queries(url, m0, m1, 60)
            hit = [x for x in tq if x[0] == q[:55]]
            print(f"   TARGET in latest month: {hit[0][1:] if hit else 'not found'}  (clicks, impr, pos)")
        print("   TOP QUERIES current window (query, clicks, impr, pos):")
        for x in ev.queries(url, c0, c1):
            print("      ", x)
        if src == "Decay":
            pq = {x[0]: x for x in ev.queries(url, p0, p1, 40)}
            cq = {x[0]: x for x in ev.queries(url, c0, c1, 40)}
            print("   QUERY MOVEMENT prior -> current (clicks/impr/pos):")
            for k in sorted(set(pq) | set(cq), key=lambda k: -((pq.get(k) or (0, 0, 0, 0))[2] + (cq.get(k) or (0, 0, 0, 0))[2]))[:8]:
                f = lambda x: f"{x[1]}/{x[2]}/{x[3]}" if x else "none"
                print(f"      {k!r:58} {f(pq.get(k)):>16} -> {f(cq.get(k)):>16}")
        print("   PLAN-FILE MENTIONS (slug in monthly_plan, excluding audits/backups):", plan_mentions(folder, url) or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
