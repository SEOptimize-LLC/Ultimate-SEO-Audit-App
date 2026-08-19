"""Task 1.3 - Site Health Audit. Filters SEMrush findings to the owner's scope.

The agent fetches from the SEMrush MCP tools (there is no SEMrush key in .env,
and MCP is not callable from Python) and hands the result here as JSON. This
module owns the part that must never be improvised: scope filtering, dropping
issues that touch nothing in scope, and writing the tab.

    python scripts/run_1_3.py educationwalkthrough --data payload.json

Payload shape:
    {"score": 90, "prev_weekly": 89, "crawl_date": "2026-08-15",
     "pages_crawled": 494, "errors": 33, "warnings": 31,
     "issues": [{"title": "...", "severity": "Error", "semrush_count": 30,
                 "urls": ["https://..."], "fix": "..."}]}
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheets_io as S              # noqa: E402
from crawl_targets import scope_urls   # noqa: E402

TAB = "1.3 + 2.2 Fix Sheet"
MARKS = {"this": "Site Health score — this month",
         "last": "Site Health score — last month",
         "after": "Site Health score — after fixes",
         "need": "Fix sheet required?"}
THRESHOLD = 92

# What earns a row, set by the owner 2026-08-17 after SameDay shipped with one
# row when it had four errors and three structural notices.
#
#   Errors   ALL of them, always, no threshold. An error is an error.
#   Warnings at 10% of sitemap URLs, or always when it is link integrity:
#            two dead outbound links on an editorial post is worth a row even
#            though two is a small number.
#   Notices  at 20% of sitemap URLs. Below that they are background noise; above
#            it they are structural. 178 permanent redirects on a 305-URL site
#            is not a notice in any useful sense, it is a template defect.
WARN_SHARE = 0.10
NOTICE_SHARE = 0.20
ALWAYS_WARN = {12, 13, 14, 103, 106}   # broken links/images, missing H1, missing meta


def select_issues(counts: dict, sitemap_total: int) -> tuple[list, list]:
    """Which issue ids earn a row, and which fell just short.

    `counts` is {issue_id: (severity, count)}. Returns (included, near_miss) so
    that anything dropped near the line is named on the tab rather than
    vanishing silently.
    """
    inc, near = [], []
    for iid, (sev, cnt) in counts.items():
        if not cnt:
            continue
        share = cnt / max(sitemap_total, 1)
        if sev == "Error":
            inc.append(iid)
        elif sev == "Warning":
            (inc if (share >= WARN_SHARE or iid in ALWAYS_WARN) else near).append(iid)
        elif share >= NOTICE_SHARE:
            inc.append(iid)
        elif share >= NOTICE_SHARE * 0.75:
            near.append(iid)
    return inc, near


def filter_to_scope(issues: list[dict], keep: set[str],
                    patterns: list[str] | None = None) -> tuple[list[dict], list[dict]]:
    """Keep only in-scope URLs. An issue left with none is dropped outright.

    Dropped, not downgraded: SEMrush raising an issue on a privacy policy is not
    a finding about this client's site, and a row that names no actionable URL
    is worse than no row because someone has to read it to discard it.

    ERRORS get a second chance on path patterns. The scope set is built from the
    sitemap, and a broken page is often missing from the sitemap precisely
    BECAUSE it is broken. SameDay's redirect loop on
    /emergency-services/air-conditioner-repair/ was filtered out on exactly that
    circularity, and it was the most severe finding on the client. So for an
    Error, a URL sitting under one of the owner's money or post paths counts as
    in scope even when the sitemap has forgotten it.
    """
    pats = [p.lower() for p in (patterns or [])]
    kept, dropped = [], []
    for iss in issues:
        urls = [u for u in iss["urls"] if u.rstrip("/") in keep]
        if not urls and iss.get("severity") == "Error" and pats:
            urls = [u for u in iss["urls"] if any(p in u.lower() for p in pats)]
        if urls:
            kept.append({**iss, "urls": urls})
        else:
            dropped.append(iss)
    return kept, dropped


def _scope_from_cache(cfg: dict) -> set[str] | None:
    """In-scope URLs from this month's cached index audit, if one exists."""
    import datetime as _dt
    import json as _json
    base = Path(cfg["folder"]) / "Monthly SEO Workbook"
    months = sorted(p.name for p in base.glob("*")
                    if (p / "index_audit.json").exists()) if base.exists() else []
    if not months:
        return None
    d = _json.loads((base / months[-1] / "index_audit.json").read_text(encoding="utf-8"))
    rows = [r for r in d.get("rows", []) if r.get("inScope", True)]
    return {r["url"].rstrip("/") for r in rows} or None


def build(slug: str, cfg: dict, payload: dict, sitemap: str) -> dict:
    sid = cfg["sheet_id"]
    # A client whose sitemap does not resolve has no derivable scope. Comfort's
    # sitemap 404s, which SEMrush independently reports as NOT_FOUND. Rather
    # than crash or silently filter against an empty set (which would drop every
    # row), fall back to the owner allowlist if there is one, and otherwise pass
    # the issues through with the limitation stated on the tab.
    try:
        keep = scope_urls(sitemap, cfg["gsc_property"], cfg)
        scoped = True
    except Exception:
        # The sitemap is unreachable. Before falling back to the money allowlist,
        # which knows nothing about posts, try the cached index audit: it already
        # holds every sitemap URL with its inScope flag from when the site WAS
        # reachable. EW is 403-blocking us this month and the allowlist fallback
        # silently dropped three of its four findings because every one sat on a
        # post rather than one of the 8 listed money pages.
        keep = _scope_from_cache(cfg)
        if keep is None:
            allow = (cfg.get("crawl") or {}).get("money_pages")
            keep = {u.rstrip("/") for u in allow} if allow else None
        scoped = keep is not None
    if keep is None:
        kept, dropped = list(payload["issues"]), []
    else:
        c = cfg.get("crawl") or {}
        kept, dropped = filter_to_scope(
            payload["issues"], keep, (c.get("money") or []) + (c.get("posts") or []))

    p = S.find_rows(sid, TAB, MARKS)
    first = p["need"] + 3

    score = payload["score"]
    # Trigger on the score OR on any issue that grew, which is the tab's own
    # rule. A site can sit above 92 and still have picked up a new error.
    new_errs = any(i.get("delta", 0) > 0 for i in kept)
    need = "Yes" if (score < THRESHOLD or new_errs) else "No"
    why = (f"Score is {score}%, below the {THRESHOLD}% threshold. "
           if score < THRESHOLD else f"Score is {score}%, at or above {THRESHOLD}%. ")
    if new_errs:
        why += "At least one in-scope issue grew since the last crawl. "
    if not kept:
        why += ("Nothing SEMrush flagged falls on a money page or post in this "
                "client's defined scope, so there is nothing to action here.")
        need = "No"
    elif dropped:
        why += (f"{len(kept)} in-scope issue type(s) below. {len(dropped)} further "
                f"type(s) were dropped because every URL they touch is outside "
                f"the defined scope.")
    else:
        why += f"{len(kept)} in-scope issue type(s) below."
    if payload.get("near_miss"):
        why += (" Just below the reporting thresholds and deliberately not listed: "
                + "; ".join(payload["near_miss"]) + ".")

    n = 0
    n += S.write(sid, f"'{TAB}'!B{p['this']}", [[f"{score}%"]]).cells
    n += S.write(sid, f"'{TAB}'!C{p['this']}", [[
        f"SEMrush Site Audit, crawl finished {payload['crawl_date']}, "
        f"{payload['pages_crawled']} pages crawled. SEMrush reports "
        f"{payload['errors']} errors and {payload['warnings']} warnings across the "
        f"whole site; the rows below cover only this client's defined money pages "
        f"and posts."
        + ("" if scoped else " SCOPE NOT FILTERED: this client's sitemap does not "
           "resolve, so there is no URL list to filter against. Check each row "
           "below is on a page that matters before actioning it.")]]).cells

    # The month-ago figure needs the 10,000-unit history report. Record the
    # reason and the weekly trend instead; next month this fills from the value
    # written above, at no cost.
    n += S.write(sid, f"'{TAB}'!B{p['last']}", [["Not retrieved"]]).cells
    n += S.write(sid, f"'{TAB}'!C{p['last']}", [[
        "The month-ago score needs SEMrush's History report, which costs 10,000 "
        "API units and the balance is currently below that. The previous weekly "
        f"crawl scored {payload['prev_weekly']}. From next month this fills "
        f"automatically from the {score}% recorded above."]]).cells

    n += S.write(sid, f"'{TAB}'!B{p['need']}", [[need]]).cells
    n += S.write(sid, f"'{TAB}'!C{p['need']}", [[why]]).cells

    audit = f"https://www.semrush.com/projects/{cfg['semrush_project']}/siteaudit/"
    # ONE URL PER ROW. The number and issue type repeat down the group so the
    # sheet still filters, and the URL column can be selected and pasted
    # straight into a browser. Owner's requirement, 2026-08-17: a semicolon-
    # joined list in one cell cannot be used that way.
    body = []
    for i, iss in enumerate(kept, 1):
        note = iss["fix"]
        if iss.get("semrush_count") and iss["semrush_count"] > len(iss["urls"]):
            note += (f" SEMrush counts {iss['semrush_count']} URLs for this issue; "
                     f"the other {iss['semrush_count'] - len(iss['urls'])} are "
                     f"outside this client's defined scope or not listed here.")
        label = f"{iss['title']} ({iss['severity']})"
        for j, url in enumerate(iss["urls"]):
            # The instruction sits on the first row of each group only: it is one
            # instruction, and repeating 900 characters down eight rows makes the
            # sheet unreadable without making it more useful.
            body.append([i, label, url, note if j == 0 else "",
                         "Rahman" if j == 0 else "", "", "", "", "", audit])
    S.clear(sid, f"'{TAB}'!A{first}:J{first + 60}")
    if body:
        n += S.write(sid, f"'{TAB}'!A{first}:J{first + len(body) - 1}", body).cells
    return {"cells": n, "kept": len(kept), "dropped": len(dropped),
            "urls": sum(len(i["urls"]) for i in kept), "need": need,
            "in_scope": len(keep) if keep else 0, "scoped": scoped}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--data", required=True)
    ap.add_argument("--sitemap", required=True)
    a = ap.parse_args()
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    payload = json.loads(Path(a.data).read_text(encoding="utf-8"))
    r = build(a.client, reg[a.client], payload, a.sitemap)
    print(f"{a.client:<22} kept {r['kept']} dropped {r['dropped']} "
          f"urls {r['urls']} need={r['need']} cells {r['cells']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
