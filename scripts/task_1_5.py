"""Task 1.5 - Decay and striking-distance candidate list, from Search Console.

Windows are anchored on COMPLETE months, never rolling from today. Run in
August, the data is May-July against February-April: two ~90 day windows that
contain no partial month. A rolling 90 days would end mid-August and drag half a
month of incomplete data into the comparison.

Three sources, per the tab:

  decay              pages whose clicks fell more than 20% between the windows
  striking distance  queries at position 4-15 in the latest complete month, with
                     real impressions, mapped to the page that ranks for them
  CTR anomaly        impressions flat or rising while CTR falls: the page is
                     still being served and is being clicked less, which points
                     at the title and meta description rather than the content
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import google.auth
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

DECAY_DROP = 0.20        # clicks down more than this counts as decay
SD_MIN, SD_MAX = 4.0, 20.0
# Widened 2026-09-03. A 100/month floor is written for national search volume and
# silently excludes local commercial queries, which are the money on this client
# base: "furnace repair sandy utah" can carry 40 impressions a month and still be
# worth winning. Measured effect on the August window, unique candidate pages:
# Comfort 2 -> 12, Arsenal 9 -> 21, Bart's 5 -> 16. Position 20 is the floor the
# owner already works to, so page 2 -> page 1 is in scope and deeper is not.
SD_MIN_IMPR = 50         # per month, so a query has real demand behind it
CTR_DROP = 0.20          # relative CTR fall
CTR_MIN_IMPR = 200


def periods(today: dt.date | None = None):
    """(current, prior) as (start, end) pairs of complete months.

    The current window ends on the last day of the month BEFORE this one, so
    running on any day of August yields May 1 - July 31 and February 1 -
    April 30. Three whole months each, ~92 and ~89 days.
    """
    today = today or dt.date.today()
    first_this = today.replace(day=1)
    cur_end = first_this - dt.timedelta(days=1)
    cur_start = (cur_end.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
    cur_start = (cur_start - dt.timedelta(days=1)).replace(day=1)
    pri_end = cur_start - dt.timedelta(days=1)
    pri_start = (pri_end.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
    pri_start = (pri_start - dt.timedelta(days=1)).replace(day=1)
    return (cur_start, cur_end), (pri_start, pri_end)


def latest_month(today: dt.date | None = None):
    today = today or dt.date.today()
    end = today.replace(day=1) - dt.timedelta(days=1)
    return end.replace(day=1), end


def sc():
    c, _ = google.auth.default(scopes=SCOPES)
    return build("searchconsole", "v1", credentials=c, cache_discovery=False)


# GSC returns rows ordered by CLICKS descending, so a cap does not sample - it
# keeps the top and discards the long tail. That tail is exactly where striking
# distance lives: high impressions, few clicks. The old default of 25000 was
# also the page size, so the loop broke after ONE page and SameDay's query data
# stopped dead at 25000 rows. Raised 2026-09-03.
MAX_ROWS = 500000


def query(svc, site, start, end, dims, rows=MAX_ROWS):
    out, start_row = [], 0
    while True:
        body = {"startDate": start.isoformat(), "endDate": end.isoformat(),
                "dimensions": dims, "rowLimit": min(rows, 25000),
                "startRow": start_row}
        r = svc.searchanalytics().query(siteUrl=site, body=body).execute()
        got = r.get("rows", [])
        out += got
        if len(got) < 25000 or len(out) >= rows:
            break
        start_row += len(got)
    return out


def norm(url: str) -> str:
    """Canonical form of a GSC page URL: no fragment, no trailing slash.

    Search Console reports anchor links as SEPARATE pages. Education Walkthrough
    returns 154 of them out of 1,227 rows, all Elementor table-of-contents
    anchors like #elementor-toc__heading-anchor-0, carrying 8,812 impressions
    and one click between them. The Alabama guide appears seven times: once as
    itself and six times as anchors.

    Left unmerged they split a page's impressions across phantom rows so no row
    shows its true volume, and every anchor row is a guaranteed false CTR
    anomaly by construction: thousands of impressions, zero clicks.
    """
    return url.split("#")[0].rstrip("/")


def merge(rows: list[dict]) -> dict[str, dict]:
    """Sum GSC rows onto their canonical URL, re-deriving the weighted position."""
    out: dict[str, dict] = {}
    for r in rows:
        u = norm(r["keys"][0])
        a = out.setdefault(u, {"clicks": 0, "impressions": 0, "_pw": 0.0})
        a["clicks"] += r["clicks"]
        a["impressions"] += r["impressions"]
        a["_pw"] += r["position"] * r["impressions"]
    for a in out.values():
        a["position"] = a["_pw"] / a["impressions"] if a["impressions"] else 0.0
        a["ctr"] = a["clicks"] / a["impressions"] if a["impressions"] else 0.0
    return out


def history(svc, site, url, months=11):
    """Monthly clicks / impressions / position for one page, newest last.

    This is what separates a ranking loss from a demand fall, and the two need
    opposite fixes. Without it a rationale can only describe the symptom.
    """
    import datetime as _dt
    end = _dt.date.today().replace(day=1) - _dt.timedelta(days=1)
    out = []
    for i in range(months - 1, -1, -1):
        m1 = end
        for _ in range(i):
            m1 = m1.replace(day=1) - _dt.timedelta(days=1)
        m0 = m1.replace(day=1)
        rows = svc.searchanalytics().query(siteUrl=site, body={
            "startDate": m0.isoformat(), "endDate": m1.isoformat(),
            "dimensions": ["page"], "rowLimit": 25,
            "dimensionFilterGroups": [{"filters": [{
                "dimension": "page", "operator": "contains",
                "expression": url.split("://")[-1].split("/", 1)[-1]}]}],
        }).execute().get("rows", [])
        agg = merge(rows).get(norm(url))
        out.append((m0.strftime("%Y-%m"), agg))
    return out


def scope(cfg):
    """(money set, post set) for this client, from the cached index audit.

    Business value comes from the owner's own money-page definition, never from
    impression volume. EW has 8 money pages against ~300 posts, so ranking by
    volume alone would fill the list with blog and bury everything that sells.
    """
    import json
    import yaml  # noqa: F401
    base = Path(cfg["folder"]) / "Monthly SEO Workbook"
    months = sorted(p.name for p in base.glob("*")
                    if (p / "index_audit.json").exists()) if base.exists() else []
    crawl = cfg.get("crawl") or {}
    money = {u.rstrip("/") for u in (crawl.get("money_pages") or [])}
    posts, in_scope = set(), set()
    if months:
        d = json.loads((base / months[-1] / "index_audit.json").read_text(encoding="utf-8"))
        for r in d.get("rows", []):
            if not r.get("inScope", True):
                continue
            in_scope.add(r["url"].rstrip("/"))
    # Anything in scope that is not a declared money page is a post. Matching
    # the `posts` rule against the URL only works when that rule is a path;
    # EW's is the sitemap name `post-sitemap`, so path matching classified all
    # 355 of its URLs as "Other" and the business-value weighting collapsed.
    # Fourth appearance of this bug: sitemap-name rules are not URL substrings.
    home = cfg["gsc_property"].rstrip("/")
    if money:
        posts = {u for u in in_scope if u not in money and u != home}
    else:
        # Classify posts from the SITEMAP GROUP, not the URL path. Superior,
        # SameDay and Beehive all use the sitemap NAME `post-sitemap` as their
        # posts rule, and path matching finds nothing, so every blog URL was
        # falling through to "money" and would have been graded High business
        # value. Fifth appearance of this bug in the project.
        posts = set()
        try:
            import crawl_targets as CT
            sm = cfg.get("sitemap")
            if not sm:
                import datetime as _dt
                import json as _j
                cache = (Path(cfg["folder"]) / "Monthly SEO Workbook" /
                         _dt.date.today().strftime("%Y-%m") / "index_audit.json")
                if cache.exists():
                    sms = _j.loads(cache.read_text(encoding="utf-8")).get("sitemaps") or []
                    sm = sms[0] if sms else None
            if sm:
                for name, entries in CT.collect(sm).items():
                    if any(x.lower() in name.lower() for x in (crawl.get("posts") or [])):
                        posts |= {loc.rstrip("/") for loc, _ in entries}
        except Exception:
            pass
        pats = [x for x in (crawl.get("posts") or []) if x.startswith("/")]
        posts |= {u for u in in_scope if any(x.lower() in u.lower() for x in pats)}
        posts &= in_scope
        money = {u for u in in_scope if u not in posts and u != home}
    return money, posts, in_scope


def analyse(svc, site, cfg):
    (c0, c1), (p0, p1) = periods()
    m0, m1 = latest_month()
    money, posts, in_scope = scope(cfg)

    home = site.rstrip("/")

    def val(url):
        u = norm(url)
        # The homepage is always a money page. norm() strips the trailing slash,
        # so it stopped matching the money set and Beehive's homepage was filed
        # as "Other" and dropped from candidacy while carrying 100,856
        # impressions and a fall from position 20.8 to 24.2.
        if u == home:
            return "Money page"
        return "Money page" if u in money else ("Post" if u in posts else "Other")

    cur = merge(query(svc, site, c0, c1, ["page"]))
    pri = merge(query(svc, site, p0, p1, ["page"]))

    decay = []
    for u, r in cur.items():
        if in_scope and u not in in_scope:
            continue
        before = pri.get(u, {}).get("clicks", 0)
        pos_before = pri.get(u, {}).get("position", 0.0)
        if before < 10:                     # too small to call a trend
            continue
        drop = (before - r["clicks"]) / before
        if drop > DECAY_DROP:
            decay.append({"url": u, "before": before, "after": r["clicks"],
                          "drop": drop, "impr": r["impressions"],
                          "impr_before": pri.get(u, {}).get("impressions", 0),
                          "pos": r["position"], "pos_before": pos_before,
                          "value": val(u)})

    sd = []
    for r in query(svc, site, m0, m1, ["query", "page"]):
        q, u = r["keys"][0], norm(r["keys"][1])
        if in_scope and u not in in_scope:
            continue
        if SD_MIN <= r["position"] <= SD_MAX and r["impressions"] >= SD_MIN_IMPR:
            sd.append({"query": q, "url": u, "pos": r["position"],
                       "impr": r["impressions"], "clicks": r["clicks"],
                       "ctr": r["ctr"], "value": val(u)})

    curq = {(r["keys"][0], norm(r["keys"][1])): r
            for r in query(svc, site, c0, c1, ["query", "page"])}
    priq = {(r["keys"][0], norm(r["keys"][1])): r
            for r in query(svc, site, p0, p1, ["query", "page"])}
    # A query often ranks more than one page. The secondary page always shows a
    # poor CTR because the clicks correctly go to the primary one, and that is
    # not a title problem. EW's brand term looked like a 95% CTR collapse until
    # this filter: "education walkthrough" earns 67% CTR to the homepage at
    # position 3.7, while the same query pointing at /pricing/ shows 1.37%.
    # Only the page that actually wins the query can have a CTR problem.
    best: dict[str, tuple[float, str]] = {}
    for (q, u), r in curq.items():
        if r["clicks"] >= best.get(q, (-1, ""))[0]:
            best[q] = (r["clicks"], u)

    ctr = []
    for k, r in curq.items():
        q, u = k
        if in_scope and u not in in_scope:
            continue
        b = priq.get(k)
        if not b or r["impressions"] < CTR_MIN_IMPR:
            continue
        if best.get(q, (0, ""))[1] != u:
            continue                    # not the page that wins this query
        # Impressions holding or growing while CTR falls: still being served,
        # being clicked less. That is a title and snippet problem, not content.
        if r["impressions"] >= b["impressions"] * 0.9 and b["ctr"] > 0:
            fall = (b["ctr"] - r["ctr"]) / b["ctr"]
            if fall > CTR_DROP:
                ctr.append({"query": q, "url": u, "impr": r["impressions"],
                            "ctr_before": b["ctr"], "ctr_after": r["ctr"],
                            "fall": fall, "pos": r["position"], "value": val(u)})

    return {"decay": sorted(decay, key=lambda d: -d["before"]),
            "sd": sorted(sd, key=lambda d: -d["impr"]),
            "ctr": sorted(ctr, key=lambda d: -d["impr"]),
            "periods": ((c0, c1), (p0, p1)), "month": (m0, m1),
            "counts": {"money": len(money), "posts": len(posts)}}


# Business value is a multiplier, not a tiebreak. The owner's instruction is to
# weight money pages heavily over blog without discarding blog, so a money page
# is worth 3x a post at equal opportunity size.
VALUE = {"Money page": 3.0, "Post": 1.0, "Other": 0.0}

# Effort is assigned by FIX TYPE, not guessed per page. A title and meta rewrite
# is genuinely cheaper than a content rebuild, and that is knowable from which
# detector found the candidate.
EFFORT = {"CTR anomaly": ("Low", 1.5), "Striking distance": ("Medium", 1.0),
          "Decay": ("Medium", 1.0)}


def rank(res: dict, limit: int = 10) -> list[dict]:
    """One scored row per candidate, best first.

    Opportunity is expressed in monthly impressions so the three sources are
    comparable: a decayed page and a striking-distance query both get scored on
    the traffic actually in reach, then weighted by business value and by how
    cheap the fix is.
    """
    out = []
    for d in res["decay"]:
        out.append({"source": "Decay", "url": d["url"], "query": "(page level)",
                    "pos": d["pos"], "impr": d["impr"], "value": d["value"],
                    "opp": d["before"] - d["after"],
                    "why": f"clicks fell {d['before']} to {d['after']}, "
                           f"down {d['drop']*100:.0f}%"})
    for d in res["sd"]:
        out.append({"source": "Striking distance", "url": d["url"],
                    "query": d["query"], "pos": d["pos"], "impr": d["impr"],
                    "value": d["value"], "opp": d["impr"] * 0.06,
                    "why": f"position {d['pos']:.1f} on {d['impr']:,} impressions/mo, "
                           f"{d['clicks']} clicks"})
    for d in res["ctr"]:
        out.append({"source": "CTR anomaly", "url": d["url"], "query": d["query"],
                    "pos": d["pos"], "impr": d["impr"], "value": d["value"],
                    "opp": d["impr"] * (d["ctr_before"] - d["ctr_after"]),
                    "why": f"impressions held at {d['impr']:,} while CTR fell "
                           f"{d['ctr_before']*100:.2f}% to {d['ctr_after']*100:.2f}%"})

    for r in out:
        eff_label, eff_mult = EFFORT[r["source"]]
        r["effort"] = eff_label
        r["score"] = r["opp"] * VALUE[r["value"]] * eff_mult

    out = [r for r in out if r["value"] != "Other"]
    out.sort(key=lambda r: -r["score"])

    # One row per URL: the same page decaying AND sitting in striking distance
    # is one piece of work, not two.
    seen, final = set(), []
    for r in out:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        final.append(r)
        if len(final) >= limit:
            break
    return final


def ctr_curve_text(sd_rows: list[dict]) -> str:
    """The client's own CTR by position band, from the striking-distance rows of the latest month.

    Bands of two positions (4-5, 6-7, ...), kept only where the band holds more than 400
    impressions, so a thin band cannot pass for a curve. "n/a" when no band qualifies.
    """
    curve: dict[int, list[float]] = {}
    for d in sd_rows:
        band = int(d["pos"] // 2) * 2
        acc = curve.setdefault(band, [0, 0])
        acc[0] += d["clicks"]
        acc[1] += d["impr"]
    return ", ".join(f"pos {b}-{b + 1} {100 * c / i:.2f}%"
                     for b, (c, i) in sorted(curve.items()) if i > 400) or "n/a"
