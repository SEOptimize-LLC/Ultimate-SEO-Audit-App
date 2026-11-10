#!/usr/bin/env python
"""Did a search feature take the clicks? The "win the answer" check for 1.5 (and the library refresh audit).

    python scripts/serp_features.py <client> "<query>" [--domain example.com]

A page whose position and impressions held while its clicks fell has two possible causes. Either its
title and snippet lose the click, or an AI Overview, featured snippet or People Also Ask box answers the
query on the results page. The second has a different fix, so read the live SERP before routing the page.

Routing (research run 2026-11-10, report "SEO lens" and "AEO lens"; Google's traffic-drop guide):
  * no feature on the page        -> CTR GAP: title and meta, judged against the site's own CTR curve
  * feature present, we are cited -> ALREADY ANSWERED: title and snippet work, no restructuring
  * feature present, not cited    -> WIN THE ANSWER: answer-first passage for this query, then snippet work

One live DataForSEO call per query. It decides nothing on a sheet: it prints evidence for the judgment.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ANSWER_TYPES = ("ai_overview", "featured_snippet", "people_also_ask")


def _host(url_or_domain: str | None) -> str:
    s = str(url_or_domain or "").lower().split("//")[-1].split("/")[0]
    return s[4:] if s.startswith("www.") else s


def _ours(host: str, domain: str) -> bool:
    d = _host(domain)
    return bool(host) and (host == d or host.endswith("." + d))


def features(items: list[dict], domain: str) -> dict:
    """Which answer features the SERP carries, and whether `domain` is a source in each."""
    out: dict[str, dict] = {}
    for it in items or []:
        t = it.get("type")
        if t not in ANSWER_TYPES or t in out:
            continue
        if t == "ai_overview":
            refs = [_host(r.get("domain") or r.get("url")) for r in (it.get("references") or [])]
            out[t] = {"cited": any(_ours(h, domain) for h in refs), "sources": [h for h in refs if h][:8]}
        elif t == "featured_snippet":
            h = _host(it.get("domain") or it.get("url"))
            out[t] = {"cited": _ours(h, domain), "sources": [h] if h else []}
        else:
            hs = []
            for x in (it.get("items") or []):
                if not isinstance(x, dict):
                    continue
                # DataForSEO puts a PAA answer's source inside expanded_element, not on the question.
                for e in [x, *(x.get("expanded_element") or [])]:
                    if isinstance(e, dict) and (e.get("domain") or e.get("url")):
                        hs.append(_host(e.get("domain") or e.get("url")))
            out[t] = {"cited": any(_ours(h, domain) for h in hs), "sources": [h for h in hs if h][:8]}
    return out


def route(feats: dict) -> tuple[str, str]:
    """(route, reason) for a page whose position and impressions held while clicks fell."""
    if not feats:
        return ("CTR GAP", "no AI Overview, featured snippet or People Also Ask on the results page")
    names = ", ".join(k.replace("_", " ") for k in feats)
    cited = [k.replace("_", " ") for k, v in feats.items() if v["cited"]]
    if cited:
        return ("ALREADY ANSWERED", f"{names} on the page; the site is a source in {', '.join(cited)}")
    return ("WIN THE ANSWER", f"{names} on the page; the site is a source in none of them")


def fetch(slug: str, query: str) -> list[dict]:
    """Live SERP items for `query` in the client's market (gap_collect's location rules)."""
    import gap_collect as G
    body = G.loc_payload(slug, {"keyword": query, "language_code": "en", "depth": 10,
                                "load_async_ai_overview": True, "people_also_ask_click_depth": 1})
    d = G.post(G.creds(), "/v3/serp/google/organic/live/advanced", [body])
    task = (d.get("tasks") or [{}])[0]
    if task.get("status_code") != 20000:
        raise RuntimeError(f"SERP check failed for {query!r}: {task.get('status_message')}")
    return ((task.get("result") or [{}])[0] or {}).get("items") or []


def check(slug: str, query: str, domain: str) -> tuple[str, str, dict]:
    feats = features(fetch(slug, query), domain)
    r, why = route(feats)
    return r, why, feats


def main() -> int:
    import yaml
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("query")
    ap.add_argument("--domain")
    a = ap.parse_args()
    cfg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))[a.client]
    r, why, feats = check(a.client, a.query, a.domain or cfg["domain"])
    print(f"{r}: {why}")
    for k, v in feats.items():
        print(f"  {k}: cited={v['cited']} sources={', '.join(v['sources'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
