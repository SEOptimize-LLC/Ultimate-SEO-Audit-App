"""Surface prompt candidates for task 1.6 from 16 months of GSC.

    python scripts/prompt_candidates.py beehive

Prints the buckets a prompt set is built from. It does NOT write the prompt set:
turning a query into a prompt is a judgement about who the client sells to, and
the whole value of the tab rests on that judgement being made rather than
generated. See tasks/1.6.md.

Word boundaries throughout. Substring matching filed EW's entire
teacher-appreciation corpus as software intent because "app" sits inside
"appreciation", and those searchers are parents writing thank-you cards.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from task_1_5 import periods, sc  # noqa: E402

LATIN = re.compile(r"^[\x00-\x7F\s]+$")
QUESTION = re.compile(r"^(what|how|why|which|when|who|can|could|do|does|is|are|"
                      r"should|will|where)\b")
# Someone choosing a provider or product, not someone learning a topic.
VENDOR = re.compile(r"\b(software|tool|tools|app|apps|platform|system|systems|"
                    r"company|companies|contractor|service|services|vendor|near me|"
                    r"best|top|cheapest|alternative|alternatives|vs|versus|review|"
                    r"reviews|pricing|price|prices|cost|quote|hire|buy)\b")
# Free-information intent. Real volume, no purchase in it.
DIY = re.compile(r"\b(diy|yourself|how to fix|how to make|free template|meaning|"
                 r"definition|salary|jobs|resume|thank|thanks|appreciation|gift|"
                 r"gifts|quote(s)? for|poem|birthday|retirement)\b")


def pull(site, months=16):
    svc = sc()
    (cs, ce), _ = periods()
    start = (yaml.safe_load(str(cs)) if False else cs)
    import datetime as dt
    start = ce - dt.timedelta(days=30 * months)
    rows, at = [], 0
    while True:
        r = svc.searchanalytics().query(siteUrl=site, body={
            "startDate": str(start), "endDate": str(ce),
            "dimensions": ["query"], "rowLimit": 25000, "startRow": at}
        ).execute().get("rows", [])
        rows += r
        if len(r) < 25000:
            break
        at += 25000
    return start, ce, rows


def main(slug):
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    cfg = reg[slug]
    brand = [t.strip().lower() for t in str(cfg.get("brand_token", "")).split("|") if t.strip()]
    start, end, rows = pull(cfg["gsc_property"])
    qs = []
    for x in rows:
        q = x["keys"][0]
        if not LATIN.match(q):
            continue
        qs.append({"q": q, "i": x["impressions"], "c": x["clicks"],
                   "p": x["position"],
                   "brand": any(b and b in q.lower() for b in brand),
                   "quest": bool(QUESTION.match(q)),
                   "vend": bool(VENDOR.search(q)),
                   "diy": bool(DIY.search(q))})
    nb = [r for r in qs if not r["brand"]]
    print(f"{slug}: {start} to {end} | {len(rows)} queries | "
          f"branded {len(qs)-len(nb)} | non-branded latin {len(nb)}")

    def show(title, sel, n=22):
        sel = sorted(sel, key=lambda r: -r["i"])[:n]
        print(f"\n=== {title} ({len(sel)} shown) ===")
        for r in sel:
            print("  %9s imp %4s clk pos %5.1f | %s"
                  % (format(r["i"], ","), r["c"], r["p"], r["q"]))

    show("VENDOR INTENT, no DIY (bottom of funnel, the money seam)",
         [r for r in nb if r["vend"] and not r["diy"]])
    show("QUESTION FORM, no DIY (Lovett's primary source)",
         [r for r in nb if r["quest"] and not r["diy"]])
    show("TOP VOLUME, no DIY, non-question (topic anchors)",
         [r for r in nb if not r["quest"] and not r["vend"] and not r["diy"]], 18)
    diy = [r for r in nb if r["diy"]]
    print(f"\nDIY/gift/thank-you noise excluded: {len(diy)} queries, "
          f"{sum(r['i'] for r in diy):,} impressions")


if __name__ == "__main__":
    main(sys.argv[1])
