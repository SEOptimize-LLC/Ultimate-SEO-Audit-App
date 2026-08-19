"""Collect the FULL evidence base for expansion briefs: for each cluster's
primary query, the complete live top 10, the People Also Ask questions, and a
content parse (headings + word count) of the top 3 organic winners.

Exists because the first EW briefs were built on a two-page diff (our page vs
the one tracked competitor), which meant every "Google rewards X here" claim
generalised from a sample of one. Owner called it what it was. This script
makes the sample the actual winners.

    python scripts/serp_winners.py educationwalkthrough
"""

from __future__ import annotations

import base64
import json
import sys
import urllib.request
from pathlib import Path

import yaml


def creds():
    lo = pw = None
    for ln in open(".env", encoding="utf-8"):
        if ln.startswith("DATAFORSEO_LOGIN="):
            lo = ln.split("=", 1)[1].strip()
        if ln.startswith("DATAFORSEO_PASSWORD="):
            pw = ln.split("=", 1)[1].strip()
    return base64.b64encode(f"{lo}:{pw}".encode()).decode()


def post(tok, path, payload):
    req = urllib.request.Request(
        "https://api.dataforseo.com" + path, data=json.dumps(payload).encode(),
        headers={"Authorization": "Basic " + tok,
                 "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read().decode())


def serp(tok, q):
    d = post(tok, "/v3/serp/google/organic/live/advanced",
             [{"keyword": q, "location_code": 2840, "language_code": "en",
               "depth": 10, "people_also_ask_click_depth": 1}])
    res = (d["tasks"][0].get("result") or [{}])[0]
    organic, paa = [], []
    for it in (res.get("items") or []):
        if it.get("type") == "organic":
            organic.append({"pos": it["rank_absolute"],
                            "domain": str(it.get("domain", "")).replace("www.", ""),
                            "url": it.get("url"), "title": it.get("title")})
        elif it.get("type") == "people_also_ask":
            for x in (it.get("items") or []):
                t = x.get("title")
                if t:
                    paa.append(t)
    return organic, paa


def parse_page(tok, url):
    d = post(tok, "/v3/on_page/instant_pages",
             [{"url": url, "enable_javascript": False}])
    try:
        m = d["tasks"][0]["result"][0]["items"][0]["meta"]
        return {"h1": (m.get("htags") or {}).get("h1") or [],
                "h2": ((m.get("htags") or {}).get("h2") or [])[:30],
                "h3": ((m.get("htags") or {}).get("h3") or [])[:20],
                "words": (m.get("content") or {}).get("plain_text_word_count"),
                "title": m.get("title")}
    except Exception:
        return None


# cluster -> primary query (highest-volume verified gap query in the cluster)
PRIMARIES = {
    "Danielson rubric": "danielson rubrics",
    "T-TESS depth": "t-tess ratings",
    "Reinforcement vs refinement": "reinforcement vs refinement",
    "Classroom walkthroughs head term": "classroom walkthroughs",
    "Classroom observation": "observation of classroom",
    "Observation apps": "observation apps",
    "Marzano depth": "marzano domains",
    "Walkthrough forms": "walkthrough forms",
}


def main(slug):
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    out_dir = Path(reg[slug]["folder"]) / "gap_analysis"
    tok = creds()
    out = {}
    for cluster, q in PRIMARIES.items():
        organic, paa = serp(tok, q)
        winners = []
        for r in organic[:3]:
            page = None
            if r["domain"] != "educationwalkthrough.com":
                page = parse_page(tok, r["url"])
            winners.append({**r, "page": page})
        out[cluster] = {"query": q, "top10": organic, "paa": paa,
                        "winners": winners}
        print(f"{cluster:<34} top3: " +
              " | ".join(f"#{w['pos']} {w['domain']} "
                         f"({(w['page'] or {}).get('words', '?')}w)"
                         for w in winners), flush=True)
        if paa:
            print(f"    PAA: {'; '.join(paa[:6])[:150]}", flush=True)
    (out_dir / "2026-08-serp-winners.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved", out_dir / "2026-08-serp-winners.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "educationwalkthrough")
