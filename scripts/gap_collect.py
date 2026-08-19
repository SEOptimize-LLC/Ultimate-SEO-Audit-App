"""Task 1.7 data collection engine. Three phases, judgment gates between them.

    python scripts/gap_collect.py serps <client>
    python scripts/gap_collect.py gaps <client> comp1.com,comp2.com,comp3.com
    python scripts/gap_collect.py winners <client> primaries.json
    python scripts/gap_collect.py links <client> comp1.com,comp2.com [page_urls...]

Phases and why they are separate: `serps` produces the domain-frequency table
from which the COMPARABLE competitor set is chosen - a judgment (same-type
business, not fixture/directory/publisher) that the EW pilot proved cannot be
keyword-matched. `gaps` needs that chosen set; it pulls competitor top-10
keywords (Labs, discovery only), junk-filters, cross-references our GSC
positions, dedupes variants and LIVE-VERIFIES every survivor, because the Labs
index killed 5 of the first 13 EW candidates (one competitor was #14 live where
Labs said #10). `winners` needs the human clustering of verified gaps; for each
cluster primary it keeps the full top 10, the People Also Ask, and parses the
top-3 pages - because briefs generalised from one competitor page prescribed
the strategy of the page ranking LAST.

Local clients get local SERPs: a national pull strips the market these
businesses actually compete in.
"""

from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

LOCATION = {  # SERP origin per client; text modifiers in queries still apply
    "beehive": "Salt Lake City,Utah,United States",
    "sameday": "Salt Lake City,Utah,United States",
    "superior": "Salt Lake City,Utah,United States",
    "comfort": "Salt Lake City,Utah,United States",
    "arsenal": "Denver,Colorado,United States",
}

JUNK = re.compile(r"login|log in|portal|\bmy\b.*account", re.I)


def creds():
    lo = pw = None
    for ln in open(".env", encoding="utf-8"):
        if ln.startswith("DATAFORSEO_LOGIN="):
            lo = ln.split("=", 1)[1].strip()
        if ln.startswith("DATAFORSEO_PASSWORD="):
            pw = ln.split("=", 1)[1].strip()
    return base64.b64encode(f"{lo}:{pw}".encode()).decode()


def post(tok, path, payload):
    import urllib.request
    req = urllib.request.Request(
        "https://api.dataforseo.com" + path, data=json.dumps(payload).encode(),
        headers={"Authorization": "Basic " + tok,
                 "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=150).read().decode())


def loc_payload(slug, extra):
    if slug in LOCATION:
        return {"location_name": LOCATION[slug], **extra}
    return {"location_code": 2840, **extra}


def live_serp(tok, slug, q, depth=10, paa=False):
    body = loc_payload(slug, {"keyword": q, "language_code": "en",
                              "depth": depth})
    if paa:
        body["people_also_ask_click_depth"] = 1
    d = post(tok, "/v3/serp/google/organic/live/advanced", [body])
    res = (d["tasks"][0].get("result") or [{}])[0]
    organic, paa_q = [], []
    for it in (res.get("items") or []):
        if it.get("type") == "organic":
            organic.append({"pos": it["rank_absolute"],
                            "domain": str(it.get("domain", "")).replace("www.", ""),
                            "url": it.get("url"), "title": it.get("title")})
        elif it.get("type") == "people_also_ask":
            for x in (it.get("items") or []):
                if x.get("title"):
                    paa_q.append(x["title"])
    return organic, paa_q


def parse_page(tok, url):
    d = post(tok, "/v3/on_page/instant_pages",
             [{"url": url, "enable_javascript": False}])
    try:
        m = d["tasks"][0]["result"][0]["items"][0]["meta"]
        return {"title": m.get("title"),
                "h1": (m.get("htags") or {}).get("h1") or [],
                "h2": ((m.get("htags") or {}).get("h2") or [])[:30],
                "words": (m.get("content") or {}).get("plain_text_word_count")}
    except Exception:
        return None


def cfg_of(slug):
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    return reg[slug]


def outdir(slug):
    d = Path(cfg_of(slug)["folder"]) / "gap_analysis"
    d.mkdir(parents=True, exist_ok=True)
    return d


def scope_queries(slug, cap=12):
    """The scoped query set: this client's GSC-derived prompt source queries,
    commercial intent first. These trace to the same 1.5-era analysis the tab's
    scope line names, and every one is a real query with real impressions."""
    doc = yaml.safe_load(Path(f"clients/prompts/{slug}.yaml").read_text(encoding="utf-8"))
    seen, out = set(), []
    for tier in (("Best-X", "Decision"), ("Comparison",), ("Discovery",)):
        for p in sorted((x for x in doc["prompts"] if x["kind"] == "category"
                         and x["intent"] in tier),
                        key=lambda x: -(x["impressions"] or 0)):
            q = p["source_query"]
            if q.startswith("(") or q in seen:
                continue
            seen.add(q)
            out.append(q)
            if len(out) >= cap:
                return out
    return out


def phase_serps(slug):
    tok = creds()
    from collections import defaultdict
    import statistics
    agg = defaultdict(lambda: {"hits": 0, "pos": [], "urls": [], "titles": []})
    snap = {}
    for q in scope_queries(slug):
        organic, _ = live_serp(tok, slug, q)
        snap[q] = organic
        for r in organic:
            a = agg[r["domain"]]
            a["hits"] += 1
            a["pos"].append(r["pos"])
            if len(a["urls"]) < 2:
                a["urls"].append(r["url"])
                a["titles"].append(r["title"])
        print(f"{q:<52} " + ", ".join(r["domain"] for r in organic[:5]), flush=True)
    d = outdir(slug)
    (d / "2026-08-serps.json").write_text(json.dumps(snap, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    print(f"\n=== {slug}: domain frequency (2+ of {len(snap)} scoped live SERPs) ===")
    for dom, a in sorted(agg.items(), key=lambda kv: (-kv[1]["hits"],
                                                      statistics.median(kv[1]["pos"]))):
        if a["hits"] < 2:
            continue
        print("  %2d q  med %4.1f  %-32s %s" % (
            a["hits"], statistics.median(a["pos"]), dom, str(a["titles"][0])[:58]))


def gsc_positions(slug):
    from task_1_5 import periods, sc
    import datetime as dt
    cfg = cfg_of(slug)
    (_, end), _ = periods()
    start = end - dt.timedelta(days=480)
    svc = sc()
    rows, at, out = [], 0, {}
    while True:
        r = svc.searchanalytics().query(siteUrl=cfg["gsc_property"], body={
            "startDate": str(start), "endDate": str(end),
            "dimensions": ["query"], "rowLimit": 25000, "startRow": at}
        ).execute().get("rows", [])
        rows += r
        if len(r) < 25000:
            break
        at += 25000
    for x in rows:
        out[x["keys"][0]] = {"pos": x["position"], "imp": x["impressions"]}
    return out


def phase_gaps(slug, comps, must_match=None):
    tok = creds()
    d = outdir(slug)
    brand = [t for t in str(cfg_of(slug).get("brand_token", "")).lower().split("|") if t]
    comp_junk = re.compile("|".join([re.escape(c.split(".")[0]) for c in comps]
                                    + [re.escape(b) for b in brand]), re.I)
    ours = gsc_positions(slug)
    print(f"{slug}: GSC queries loaded: {len(ours)}", flush=True)

    all_kw = {}
    for dom in comps:
        dd = post(tok, "/v3/dataforseo_labs/google/ranked_keywords/live",
                  [{"target": dom, "location_code": 2840, "language_code": "en",
                    "limit": 1000}])
        res = (dd["tasks"][0].get("result") or [{}])[0]
        rows = []
        for it in (res.get("items") or []):
            kd = it.get("keyword_data") or {}
            se = ((it.get("ranked_serp_element") or {}).get("serp_item")) or {}
            if (se.get("rank_group") or 99) <= 10:
                rows.append({"kw": kd.get("keyword"),
                             "vol": (kd.get("keyword_info") or {}).get("search_volume"),
                             "pos": se.get("rank_group"), "url": se.get("url")})
        all_kw[dom] = rows
        print(f"  {dom:<28} total {res.get('total_count')}  top-10 {len(rows)}", flush=True)
    (d / "2026-08-competitor-keywords.json").write_text(json.dumps(all_kw, indent=1),
                                                        encoding="utf-8")

    def norm(k):
        k = re.sub(r"[-']", " ", k.lower())
        ws = [re.sub(r"s\b", "", w) for w in k.split()
              if w not in ("vs", "and", "the", "of", "for", "a", "in")]
        return " ".join(sorted(ws))

    seen, cands = set(), []
    for dom, kws in all_kw.items():
        for r in kws:
            kw = str(r["kw"])
            if JUNK.search(kw) or comp_junk.search(kw) or not r["vol"] or r["vol"] < 40:
                continue
            # Topical relevance gate for broad-brand comparables: Crest ranks
            # for thousands of oral-care keywords Snow does not sell. Owner
            # rule: relevancy outranks volume - a keyword the buyer would
            # never search does not even enter discovery.
            if must_match and not re.search(must_match, kw, re.I):
                continue
            o = ours.get(kw)
            if o and o["pos"] <= 10 and o["pos"] - r["pos"] < 5:
                continue
            n = norm(kw)
            if n in seen:
                continue
            seen.add(n)
            cands.append({"kw": kw, "vol": r["vol"], "comp": dom, "cpos": r["pos"],
                          "curl": r["url"], "ours": (o or {}).get("pos")})
    cands.sort(key=lambda x: -(x["vol"] or 0))
    print(f"  gap candidates after dedupe: {len(cands)}; live-verifying...", flush=True)

    own = cfg_of(slug)["domain"].replace("www.", "")
    comp_bases = tuple(c.replace("www.", "") for c in comps)
    verified = []
    for i, r in enumerate(cands, 1):
        organic, _ = live_serp(tok, slug, r["kw"], depth=20)
        us = them = None
        them_dom = them_url = None
        for it in organic:
            base = it["domain"].replace("home.", "").replace("app.", "").replace("get.", "")
            if it["domain"] == own and us is None:
                us = (it["pos"], it["url"])
            if base in comp_bases and them is None:
                them, them_dom, them_url = it["pos"], base, it["url"]
        if them and them <= 10 and (not us or us[0] > 10 or us[0] - them >= 5):
            verified.append({**r, "live_them": them, "live_dom": them_dom,
                             "live_url": them_url,
                             "live_us": us[0] if us else None,
                             "live_us_url": us[1] if us else None})
        if i % 15 == 0:
            print(f"  ...{i}/{len(cands)} verified, {len(verified)} survive", flush=True)
    (d / "2026-08-verified-gaps.json").write_text(json.dumps(verified, indent=1),
                                                  encoding="utf-8")
    print(f"  LIVE-VERIFIED GAPS: {len(verified)}")
    for r in verified[:40]:
        print("   vol %5s  them #%-2s %-24s us %-5s %s" % (
            r["vol"], r["live_them"], (r["live_dom"] or "")[:24],
            ("#%d" % r["live_us"]) if r["live_us"] else "ABS", r["kw"]))


def phase_winners(slug, primaries_file):
    """primaries_file: JSON {cluster_name: primary_query} authored after the
    human clustering pass over verified-gaps."""
    tok = creds()
    primaries = json.loads(Path(primaries_file).read_text(encoding="utf-8"))
    own = cfg_of(slug)["domain"].replace("www.", "")
    out = {}
    for cluster, q in primaries.items():
        organic, paa = live_serp(tok, slug, q, depth=10, paa=True)
        winners = []
        for r in organic[:3]:
            page = parse_page(tok, r["url"]) if r["domain"] != own else None
            winners.append({**r, "page": page})
        out[cluster] = {"query": q, "top10": organic, "paa": paa, "winners": winners}
        print(f"{cluster:<34} top3: " + " | ".join(
            f"#{w['pos']} {w['domain']} ({(w['page'] or {}).get('words','?')}w)"
            for w in winners), flush=True)
        if paa:
            print("    PAA: " + "; ".join(paa[:6])[:160], flush=True)
    (outdir(slug) / "2026-08-serp-winners.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def phase_links(slug, comps, pages):
    tok = creds()

    def refdoms(target):
        d = post(tok, "/v3/backlinks/referring_domains/live",
                 [{"target": target, "limit": 1000,
                   "exclude_internal_backlinks": True,
                   "backlinks_status_type": "live"}])
        res = (d["tasks"][0].get("result") or [{}])[0]
        return {it["domain"]: {"rank": it.get("rank"), "bl": it.get("backlinks")}
                for it in (res.get("items") or [])}

    own = cfg_of(slug)["domain"].replace("www.", "")
    ew = refdoms(own)
    out = {"our_domain_refdoms": len(ew), "pages": {}, "domain_gaps": {}}
    for u in pages:
        out["pages"][u] = refdoms(u)
        print(f"  page {u[:60]}: {len(out['pages'][u])} ref domains", flush=True)
    for c in comps:
        doms = refdoms(c)
        gap = {k: v for k, v in doms.items() if k not in ew}
        out["domain_gaps"][c] = {"total": len(doms), "gap": gap}
        print(f"  {c}: {len(doms)} refdoms, {len(gap)} not linking to {own}", flush=True)
    (outdir(slug) / "2026-08-linkgaps.json").write_text(json.dumps(out, indent=1),
                                                        encoding="utf-8")


if __name__ == "__main__":
    phase, slug = sys.argv[1], sys.argv[2]
    if phase == "serps":
        phase_serps(slug)
    elif phase == "gaps":
        phase_gaps(slug, sys.argv[3].split(","),
                   sys.argv[4] if len(sys.argv) > 4 else None)
    elif phase == "winners":
        phase_winners(slug, sys.argv[3])
    elif phase == "links":
        phase_links(slug, sys.argv[3].split(","), sys.argv[4:])
    else:
        raise SystemExit(__doc__)
