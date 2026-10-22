#!/usr/bin/env python
"""Does a keyword need a page on the client's site, a placement on someone else's, or both?

    python scripts/serp_route.py --location "Salt Lake City,Utah,United States" --keywords-file kws.txt
    python scripts/serp_route.py --location "United States" "odoo implementation partner" --out route.csv

Feeds the Route column of the local-keyword-research skill. For each keyword it reads Google's organic top 10
(DataForSEO task queue, three checks by default), sorts every result into business site, directory or review
platform, listicle, forum, video, social, news or reference, and decides:

  * Our page   3 or more distinct business sites in the top 10.
  * Placement  2 or fewer: directories, listicles and review sites hold the query.
  * Both       3 or more, but positions 1 to 3 are all non-business.

The 3-of-10 line is a hypothesis taken from the Amadora buyer-search playbook, not a measured threshold.
Calibrate it on two clients before treating it as a rule. Known lean toward "Our page": big-box retailers
count as businesses, and a listicle whose title carries no count ("Best Plumbers in Sandy 2026") reads as a
business page.

Queue, not live, and three checks, not one: measured 2026-10-21, live calls stall under load and Google
serves different results pages for the same request (memory: dataforseo-live-rank-check-method). The route
comes from the median business count and the majority top-3 reading, and every row says what decided it.

Every posted task id and every collected result is written to a state file (--state, default
.cache/serp_route_state.json) as it happens. A crash, a network failure or a task still queued at the deadline
loses nothing already paid for: rerun the same command and it collects those tasks instead of posting again.
Results are reused for 7 days.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DFS_API = "https://api.dataforseo.com/v3"
QUEUE = "/serp/google/organic"
TOP_N = 10
MIN_BUSINESS = 3          # the hypothesis above
POST_CHUNK = 100          # tasks per task_post
MAX_REFILLS = 2           # re-post rounds for transient task failures
POLL_S = 15
TIMEOUT_S = 1200
MAX_RETRIES = 4
RETRY_CODES = {40101, 40106}   # transient task failures, ~12% of tasks (measured 2026-10-21): post again
QUEUED_CODES = {40601, 40602}  # task handed / in queue: not ready yet
STATE_MAX_AGE_S = 7 * 86400
COST_PER_CHECK = 0.0012        # priority queue, depth 10, approximate
MAX_UNCONFIRMED = 600          # checks posted without --yes
DEFAULT_STATE = ROOT / ".cache" / "serp_route_state.json"

# Registrable domains; a subdomain matches its parent (m.yelp.com is yelp.com).
DIRECTORY = {
    "yelp.com", "angi.com", "angieslist.com", "homeadvisor.com", "thumbtack.com", "bbb.org", "houzz.com",
    "porch.com", "nextdoor.com", "mapquest.com", "yellowpages.com", "superpages.com", "yellowbook.com",
    "manta.com", "chamberofcommerce.com", "expertise.com", "threebestrated.com", "buildzoom.com",
    "networx.com", "birdeye.com", "alignable.com", "bark.com", "homeguide.com", "fixr.com", "thervo.com",
    "nicelocal.com", "trustanalytica.com", "citysearch.com", "dexknows.com", "merchantcircle.com",
    "hotfrog.com", "brownbook.net", "local.com", "local.yahoo.com", "homeyou.com", "trustpilot.com",
    "tripadvisor.com",
    "g2.com", "capterra.com", "getapp.com", "softwareadvice.com", "trustradius.com", "clutch.co",
    "goodfirms.co", "upcity.com", "designrush.com", "sortlist.com", "avvo.com", "justia.com", "findlaw.com",
    "lawyers.com", "martindale.com", "healthgrades.com", "zocdoc.com", "vitals.com",
}
FORUM = {"reddit.com", "quora.com", "stackexchange.com", "justanswer.com", "city-data.com"}
VIDEO = {"youtube.com", "vimeo.com", "tiktok.com"}
SOCIAL = {"facebook.com", "instagram.com", "linkedin.com", "pinterest.com", "x.com", "twitter.com"}
NEWS = {
    "forbes.com", "nytimes.com", "usnews.com", "cnet.com", "businessinsider.com", "nerdwallet.com",
    "thespruce.com", "bobvila.com", "familyhandyman.com", "thisoldhouse.com", "hunker.com", "ksl.com",
    "sltrib.com", "deseret.com", "patch.com", "mlive.com", "freep.com", "lansingstatejournal.com",
}
REFERENCE = {"wikipedia.org", "energystar.gov"}

# A counted list OF PROVIDERS: "10 Best Plumbers", "Top 7 HVAC Companies", "Best 5 Odoo Partners". A count
# alone is not enough, because businesses put numbers in their own titles ("Best 24/7 Plumber", "Top 5
# Reasons to Choose Us"), and "Best X in City" with no count is how businesses title their pages.
PROVIDERS = (
    "companies|contractors|plumbers|electricians|roofers|pavers|builders|installers|cleaners|movers|"
    "painters|landscapers|technicians|services|providers|firms|agencies|partners|consultants|specialists|"
    "experts|pros|professionals|businesses|vendors|shops|stores|dentists|doctors|lawyers|attorneys|gyms|"
    "studios|restaurants|tools|software|platforms|apps|solutions|options|alternatives|picks|brands|places"
)
LISTICLE = re.compile(
    rf"\b(?:top|best)\s+\d{{1,2}}\s+(?:[\w&'-]+\s+){{0,3}}?(?:{PROVIDERS})\b"
    rf"|\b\d{{1,2}}\s+(?:best|top)(?:[- ]rated)?\s+(?:[\w&'-]+\s+){{0,3}}?(?:{PROVIDERS})\b",
    re.I,
)
KINDS = ("business", "directory", "listicle", "forum", "video", "social", "news", "reference")


def _in(domain: str, sites: set[str]) -> bool:
    return any(domain == s or domain.endswith("." + s) for s in sites)


def classify(domain: str, title: str | None) -> str:
    d = domain.lower().removeprefix("www.")
    if _in(d, DIRECTORY):
        return "directory"
    if _in(d, FORUM) or d.startswith("forum.") or d.startswith("forums."):
        return "forum"
    if _in(d, VIDEO):
        return "video"
    if _in(d, SOCIAL):
        return "social"
    if _in(d, NEWS):
        return "news"
    if _in(d, REFERENCE) or d.endswith(".gov") or d.endswith(".edu") or ".gov." in d:
        return "reference"
    if title and LISTICLE.search(title):
        return "listicle"
    return "business"


def composition(organic: list[dict]) -> dict:
    """Distinct domains by kind over the first TOP_N organic results, plus the top 3 by position.

    Distinct, because one company holding three slots is one business, not three.
    """
    top = [r for r in organic if r.get("domain")][:TOP_N]
    kinds = [classify(r["domain"], r.get("title")) for r in top]
    counts = Counter(kind for kind, _ in {(k, r["domain"]) for k, r in zip(kinds, top, strict=True)})
    return {**{k: counts.get(k, 0) for k in KINDS},
            "top3": [f"{r['domain']} ({k})" for r, k in zip(top[:3], kinds[:3], strict=True)],
            "top3_non_business": len(kinds) >= 3 and all(k != "business" for k in kinds[:3])}


def route(business: int, top3_non_business: bool) -> str:
    if business < MIN_BUSINESS:
        return "Placement"
    return "Both" if top3_non_business else "Our page"


def aggregate(checks: list[dict]) -> dict:
    """One route from several checks: median business count, majority top-3 reading."""
    if not checks:
        return {"route": "No reading", "business": None, "top3_non_business": None, "checks": 0}
    business = int(statistics.median_low([c["business"] for c in checks]))
    top3 = sum(c["top3_non_business"] for c in checks) * 2 > len(checks)
    return {"route": route(business, top3), "business": business, "top3_non_business": top3,
            "checks": len(checks)}


def parse_task(task: dict) -> list[dict]:
    items = ((task.get("result") or [{}])[0] or {}).get("items") or []
    return [{"pos": it.get("rank_absolute"), "domain": str(it.get("domain") or "").lower().removeprefix("www."),
             "title": it.get("title"), "url": it.get("url")}
            for it in items if it.get("type") == "organic" and it.get("domain")]


# ---------------------------------------------------------------- DataForSEO

def dfs_auth() -> tuple[str, str]:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    try:
        return os.environ["DATAFORSEO_LOGIN"], os.environ["DATAFORSEO_PASSWORD"]
    except KeyError as e:
        raise RuntimeError("DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD missing from .env") from e


def dfs_call(method: str, path: str, auth, payload=None) -> dict:
    """GETs retry on network errors and 429/5xx. A POST retries only on 429: a 5xx or a dropped connection
    after task_post can mean the batch was accepted and billed, and posting it again would pay twice."""
    get = method == "GET"
    retry_status = (429, 500, 502, 503) if get else (429,)
    for attempt in range(MAX_RETRIES + 1):
        last = attempt == MAX_RETRIES
        try:
            r = requests.request(method, DFS_API + path, auth=auth, json=payload, timeout=120)
        except requests.RequestException:
            if not get or last:
                raise
            time.sleep(10.0 * 2 ** attempt)
            continue
        if r.status_code not in retry_status or last:
            break
        time.sleep(10.0 * 2 ** attempt)
    r.raise_for_status()
    body = r.json()
    if body.get("status_code") != 20000:
        raise RuntimeError("DataForSEO " + path + ": " + str(body.get("status_message")))
    return body


def check_key(keyword: str, location: str, check: int) -> str:
    return f"{keyword}\t{location}\t{check}"


def run_checks(keywords: list[str], location: str, checks: int, auth, call=dfs_call, sleep=time.sleep,
               clock=time.monotonic, now=time.time, timeout_s: int = TIMEOUT_S, state: dict | None = None,
               save=lambda state: None) -> dict[str, list[list[dict]]]:
    """{keyword: [organic results per check that returned a reading]}.

    `state` holds {"pending": {task id: key}, "done": {key: {"at": epoch, "organic": list | None}}} and is
    passed to `save` after every change, so nothing paid for is lost to a crash or reposted on a rerun.
    """
    state = state if state is not None else {}
    pending: dict[str, str] = state.setdefault("pending", {})
    done: dict[str, dict] = state.setdefault("done", {})
    for key in [k for k, v in done.items() if now() - v["at"] > STATE_MAX_AGE_S]:
        del done[key]
    keys = [check_key(kw, location, c) for kw in keywords for c in range(checks)]

    def fetch(tid: str) -> None:
        task = (call("GET", f"{QUEUE}/task_get/advanced/{tid}", auth).get("tasks") or [{}])[0]
        code = task.get("status_code")
        if code in QUEUED_CODES:
            return
        key = pending.pop(tid)
        if code == 20000:
            # An empty results page is no reading; it was billed, so it is not posted again either.
            done[key] = {"at": now(), "organic": parse_task(task) or None}
        elif code not in RETRY_CODES:
            done[key] = {"at": now(), "organic": None}   # e.g. 40102 no results: billed and final
        # A RETRY_CODES failure leaves the key undone, so the next round posts it again.

    try:
        for tid in list(pending):            # tasks an earlier run posted: collect before posting anything
            fetch(tid)
        save(state)
        for _round in range(MAX_REFILLS + 1):
            queued = set(pending.values())
            to_post = [k for k in keys if k not in done and k not in queued]
            for start in range(0, len(to_post), POST_CHUNK):
                chunk = to_post[start:start + POST_CHUNK]
                payload = [{"keyword": k.split("\t")[0], "location_name": location, "language_code": "en",
                            "depth": TOP_N, "priority": 2, "tag": str(i)} for i, k in enumerate(chunk)]
                for task in call("POST", QUEUE + "/task_post", auth, payload).get("tasks") or []:
                    if task.get("status_code") == 20100:
                        pending[task["id"]] = chunk[int(task["data"]["tag"])]
                save(state)
            deadline = clock() + timeout_s
            while pending and clock() < deadline:
                ready = [r.get("id") for t in call("GET", QUEUE + "/tasks_ready", auth).get("tasks") or []
                         for r in (t.get("result") or [])]
                for tid in dict.fromkeys(ready):      # the vendor can list a task twice
                    if tid in pending:
                        fetch(tid)
                save(state)
                if pending:
                    sleep(POLL_S)
            if pending or all(k in done for k in keys):
                break                               # still-queued tasks stay in the state, never reposted
    except (requests.RequestException, RuntimeError) as e:
        print(f"!! DataForSEO call failed ({e}). Everything collected is in the state file; "
              f"rerun the same command to collect the {len(pending)} queued tasks. A failed task_post batch "
              "may still have been billed.", file=sys.stderr)
    finally:
        save(state)
    if pending:
        print(f"!! {len(pending)} checks still queued; rerun the same command later to collect them",
              file=sys.stderr)

    out: dict[str, list[list[dict]]] = {kw: [] for kw in keywords}
    for kw in keywords:
        for c in range(checks):
            reading = done.get(check_key(kw, location, c))
            if reading and reading["organic"]:
                out[kw].append(reading["organic"])
    return out


# ---------------------------------------------------------------- CLI

def read_keywords(args) -> list[str]:
    kws = list(args.keywords)
    if args.keywords_file:
        text = Path(args.keywords_file).read_text(encoding="utf-8-sig")
        if args.keywords_file.lower().endswith(".csv"):
            kws += [row[0].strip() for row in csv.reader(text.splitlines()) if row]
        else:
            kws += [line.strip() for line in text.splitlines()]
    seen: set[str] = set()
    out = []
    for kw in kws:
        if kw and kw.lower() != "keyword" and kw.lower() not in seen:
            seen.add(kw.lower())
            out.append(kw)
    return out


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    tmp.replace(path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    p.add_argument("keywords", nargs="*")
    p.add_argument("--keywords-file", help="a .txt with one keyword per line, or a .csv with keywords in column A")
    p.add_argument("--location", default="United States",
                   help='DataForSEO location_name, e.g. "Sandy,Utah,United States"')
    p.add_argument("--checks", type=int, default=3)
    p.add_argument("--out", help="CSV path for the results")
    p.add_argument("--state", default=str(DEFAULT_STATE), help="task and result log; reruns reuse it")
    p.add_argument("--yes", action="store_true", help=f"allow more than {MAX_UNCONFIRMED} checks in one run")
    args = p.parse_args(argv)

    keywords = read_keywords(args)
    if not keywords:
        p.error("no keywords given")
    if args.checks < 1:
        p.error("--checks must be 1 or more")
    total = len(keywords) * args.checks
    if total > MAX_UNCONFIRMED and not args.yes:
        p.error(f"{total} checks (about ${total * COST_PER_CHECK:.3f}); pass --yes to post them")
    print(f"{len(keywords)} keywords x {args.checks} checks, up to about ${total * COST_PER_CHECK:.3f} "
          "(results already in the state file are not paid for again)", file=sys.stderr)

    state_path = Path(args.state)
    state = load_state(state_path)
    results = run_checks(keywords, args.location, args.checks, dfs_auth(), state=state,
                         save=lambda s: save_state(state_path, s))

    header = ["keyword", "route", "business_sites", *KINDS[1:], "checks", "decided_by"]
    rows = []
    for kw in keywords:
        comps = [composition(org) for org in results[kw]]
        agg = aggregate(comps)
        if not comps:
            rows.append([kw, agg["route"], "", *[""] * (len(KINDS) - 1), 0, "no result returned"])
            continue
        median = [int(statistics.median_low([c[k] for c in comps])) for k in KINDS[1:]]
        # Show a top 3 from a check that agrees with the majority reading, so the text never contradicts it.
        shown = next(c for c in comps if c["top3_non_business"] == agg["top3_non_business"])
        decided = (f"median {agg['business']} business sites of {TOP_N} across {agg['checks']} checks; "
                   f"top 3 ({'all non-business' if agg['top3_non_business'] else 'mixed'}): "
                   f"{', '.join(shown['top3'])}")
        rows.append([kw, agg["route"], agg["business"], *median, agg["checks"], decided])

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows([header, *rows])
    for r in rows:
        print(f"{r[1]:<10} {r[0]}  ({r[-1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
