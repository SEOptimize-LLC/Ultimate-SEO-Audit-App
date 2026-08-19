"""Fill 1.5 for the remaining seven clients.

Candidates are pooled from decay AND striking distance, because on the
home-services clients the decayed pages are DIY blog posts while the money sits
in striking distance on service pages against local commercial queries. Ranking
on click loss alone would fill four tabs with garbage-disposal how-tos and miss
"furnace repair salt lake city" at position 7.
"""
import sys
import yaml

sys.path.insert(0, "scripts")
import sheets_io as S
from task_1_5 import sc, analyse

TAB = "1.5 Candidate List"

# Commercial intent of the QUERY, judged per client business model. This is the
# judgement the whole tab exists for, so it is written out rather than derived.
BUY = ("repair", "replace", "install", "near me", "service", "cost", "price",
       "quote", "emergency", "company", "companies", "contractor", "plumber",
       "buy", "best", "vs", "review", "migration", "consultant", "partner")
DIY = ("how to", "how-to", "diy", "why do", "what is", "can i", "can you",
       "signs", "tips", "ideas", "examples", "thank", "guide to")


def commercial(text):
    t = text.lower()
    if any(k in t for k in DIY):
        return False
    return any(k in t for k in BUY)


def cause(d):
    move = d["pos"] - d["pos_before"]
    ib, ia = d.get("impr_before", 0), d["impr"]
    if move >= 1.5:
        return ("RANKING LOSS", f"position {d['pos_before']:.1f} to {d['pos']:.1f}, "
                f"clicks {d['before']} to {d['after']} on {ia:,} impressions")
    if ib and ia < ib * 0.85:
        return ("DEMAND FALL", f"position held at {d['pos_before']:.1f} to "
                f"{d['pos']:.1f} while impressions fell {ib:,} to {ia:,}, clicks "
                f"{d['before']} to {d['after']}")
    return ("CTR GAP", f"position {d['pos_before']:.1f} to {d['pos']:.1f}, "
            f"impressions {ib:,} to {ia:,}, clicks {d['before']} to {d['after']}")


ACTION = {
    "RANKING LOSS": "content depth and internal links",
    "DEMAND FALL": "validate seasonality year over year BEFORE any rewrite",
    "CTR GAP": "title and meta, judged against this site's own CTR curve",
}


def build(slug, cfg, svc, notes):
    site = cfg["gsc_property"]
    B = site.rstrip("/")
    res = analyse(svc, site, cfg)

    curve = {}
    for d in res["sd"]:
        b = int(d["pos"] // 2) * 2
        a = curve.setdefault(b, [0, 0])
        a[0] += d["clicks"]; a[1] += d["impr"]
    curve_txt = ", ".join(f"pos {b}-{b+1} {100*c/i:.2f}%"
                          for b, (c, i) in sorted(curve.items()) if i > 400) or "n/a"

    pool = []
    for d in res["decay"]:
        if d["value"] == "Other":
            continue
        kind, ev = cause(d)
        pool.append({"url": d["url"], "src": "Decay", "q": "(page-level decay)",
                     "pos": d["pos"], "impr": d["impr"], "value": d["value"],
                     "opp": d["before"] - d["after"], "kind": kind, "ev": ev,
                     "buy": commercial(d["url"])})
    best = {}
    for d in res["sd"]:
        if d["value"] == "Other":
            continue
        k = d["url"]
        if k not in best or d["impr"] > best[k]["impr"]:
            best[k] = d
    for d in best.values():
        pool.append({"url": d["url"], "src": "Striking Distance", "q": d["query"],
                     "pos": d["pos"], "impr": d["impr"], "value": d["value"],
                     "opp": d["impr"] * 0.04, "kind": "STRIKING DISTANCE",
                     "ev": f"position {d['pos']:.1f} on {d['impr']:,} impressions "
                           f"for \"{d['query']}\", {d['clicks']} clicks",
                     "buy": commercial(d["query"])})

    # Business value: who the page reaches and whether the query is someone
    # ready to buy. A money page on a commercial query is the top of this scale
    # on every one of these clients.
    # A MONEY PAGE IS HIGH, full stop. The client designated it as a page that
    # sells; that settles its business value and no keyword test improves on it.
    # A keyword heuristic graded Snow's product pages Medium because "purple
    # teeth whitening strips" contains no word from a buy-intent list, when
    # someone searching a product by name is as close to buying as it gets.
    # Only POSTS need an intent judgement, because a post can serve a buyer
    # (cost, comparison, "near me") or a DIY reader who will never convert.
    for r in pool:
        if r["value"] == "Money page":
            r["bv"] = "High"
        else:
            r["bv"] = "Medium" if r["buy"] else "Low"
        r["score"] = r["opp"] * {"High": 4.0, "Medium": 1.5, "Low": 0.4}[r["bv"]]

    # Rank by value band first, so a Low/N row can never head the list. Beehive
    # and Cudio both put a Low informational post at rank 1 on raw impressions.
    order = {"High": 0, "Medium": 1, "Low": 2}
    pool.sort(key=lambda r: (order[r["bv"]], -r["score"]))
    seen, rows = set(), []
    for r in pool:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        rows.append(r)
        if len(rows) >= 10:
            break

    body = []
    for i, r in enumerate(rows, 1):
        act = ("close the gap to top 5" if r["kind"] == "STRIKING DISTANCE"
               else ACTION[r["kind"]])
        why = (f"ACTION: {act}. {r['kind']}: {r['ev']}. "
               + notes.get(r["url"].replace(B, ""), "")
               + (" Commercial-intent query, so the searcher is close to buying."
                  if r["buy"] else
                  " Informational intent: useful for reach, further from revenue."))
        body.append([i, r["url"], r["src"], r["q"], round(r["pos"], 1),
                     int(r["impr"]), why.strip(), r["bv"],
                     "Y" if r["bv"] in ("High", "Medium") else "N"])

    p = S.find_rows(cfg["sheet_id"], TAB, {"a": "Keyword", "b": "Rank"})
    n = S.write(cfg["sheet_id"], f"'{TAB}'!A{p['a']+1}:G{p['a']+1}", [[
        "BASELINE MONTH - nothing to measure yet", "", "", "", "", "",
        "First run of the workbook, so there is no recorded set of July "
        "optimizations to compare against. Fills from next month using whatever "
        "1.8 selects. Do not back-fill from ranking history: a position change "
        "with no record of a change made is not a before/after. This client's own "
        f"CTR curve, May-Jul: {curve_txt}. Judge any CTR claim against THAT, not "
        "a generic curve."]]).cells
    n += S.write(cfg["sheet_id"], f"'{TAB}'!A{p['b']+1}:I{p['b']+len(body)}", body).cells
    ys = sum(1 for b in body if b[8] == "Y")
    print(f"{slug:<22} rows {len(body):>2}  Y {ys}  N {len(body)-ys}  cells {n}")
    for b in body[:4]:
        print(f"     {b[0]} {b[7]:<7}{b[8]} {b[2]:<18}{b[1].replace(B,'')[:40]:<40} "
              f"pos {b[4]:<5} {b[5]:>8,}")
    return len(body)


NOTES = {
 "superior": {"/hvac/furnace-repair": "Core revenue service in the primary market.",
              "/water/water-treatment": "Water treatment is this client's flagship line.",
              "/water/water-heaters/tankless-water-heater": "High-ticket install."},
 "sameday": {"/plumbing": "Top-level plumbing hub on the highest-intent queries in "
                          "home services, sitting on page 2-3."},
 "beehive": {"/emergency-plumber": "Emergency work is the highest-margin call.",
             "/water-heater-installation-services-utah": "High-ticket install at page 3+."},
 "comfort": {"/service-areas/sandy-utah": "City page on direct service queries."},
 "arsenal": {"/locations/dtc": "Physical location page, drives foot traffic.",
             "/peptide-therapy-2": "Duplicate of /peptide-therapy: resolve "
                                   "cannibalization before optimising either."},
 "cudio": {"/services/odoo-migration": "Primary commercial service page.",
           "/blog/odoo-implementation-costs": "Cost queries are late-stage B2B intent."},
 "snow": {"/products/teeth-whitening-strips": "Core product.",
          "/products/purple-teeth-whitening-strips": "Purple range is the growth line."},
}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("client", nargs="?", default="all")
    a = ap.parse_args()
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    svc = sc()
    todo = list(reg) if a.client == "all" else [a.client]
    for slug in todo:
        try:
            build(slug, reg[slug], svc, NOTES.get(slug, {}))
        except Exception as e:
            print(f"{slug:<22} FAILED {e.__class__.__name__}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


_UNUSED = ["superior", "sameday", "beehive", "comfort", "arsenal", "cudio", "snow"]
for slug in []:
    pass
