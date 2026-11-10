#!/usr/bin/env python
"""Fill a client's 1.6 tab from the LLM tracker's stored results. No vendor calls.

    python scripts/fill_1_6_tracker.py <client> [<client> ...]
    python scripts/fill_1_6_tracker.py all

Owner decision 2026-10-07: 1.6 reads the GEO-AEO-LLM-Tracker (DataForSEO, scanned weekly, 5 samples per
prompt) instead of running its own fixed prompt set through Bright Data.

  * SOV = share of answered ChatGPT and Google AI Mode samples, over the tracker's category prompts, in which
    the brand is mentioned. Gemini is a note, never in SOV. AI Overview is left out (a large share of its
    requests return no result). Perplexity is not run. Branded prompts are not part of the tracker's scan.
  * Section A lists the 30 highest-volume category prompts, each as "mentioned in m of n samples" per engine.
  * October 2026 is a baseline: the previous figure came from a different prompt set.
  * The week used is the latest one holding at least 70% of the prior week's samples (tracker_reader.pick_week).
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fill_1_6_all as F  # noqa: E402
import gap_collect as G  # noqa: E402  (DataForSEO credentials and POST helper)
import fill_1_8 as R  # noqa: E402  (resolve_all: redirects followed, slash-only canonical adopted)
import sheets_io as S  # noqa: E402
import tracker_reader as T  # noqa: E402

TAB = F.TAB
ROWS_A = 30
ENGINE_LABEL = {"chatgpt": "ChatGPT", "ai_mode": "Google AI Mode", "gemini": "Gemini"}


def pct(n: int, d: int) -> float:
    return 100.0 * n / d if d else 0.0


def prominence(rank: int | None) -> str:
    return "-" if rank is None else {1: "1st", 2: "2nd"}.get(rank, "3rd+")


def top(counter, n: int, fmt=lambda k, c: f"{k} ({c})") -> str:
    return ", ".join(fmt(k, c) for k, c in counter.most_common(n)) or "none"


def sov(totals: dict) -> tuple[int, int, list[str]]:
    used = [e for e in T.SOV_ENGINES if totals.get(e, {}).get("answered")]
    return (sum(totals[e]["mentioned"] for e in used), sum(totals[e]["answered"] for e in used), used)


def engine_cell(p: dict, eng: str) -> str:
    e = p["engines"].get(eng)
    return f"{e['mentioned']} of {e['answered']}" if e else ""


def prompt_totals(p: dict) -> tuple[int, int]:
    return (sum(e["mentioned"] for e in p["engines"].values()), sum(e["answered"] for e in p["engines"].values()))


def row_a(i: int, p: dict, resolved: dict | None = None) -> list:
    m, n = prompt_totals(p)
    notes = []
    if n and m == 0:
        notes.append("Absent from every sampled answer."
                     + (f" Named instead: {top(p['competitors'], 3, lambda k, c: k)}." if p["competitors"] else ""))
    elif m:
        notes.append(f"Mentioned in {m} of {n} sampled answers.")
    own_cell, n_own = url_cell(own_pages(p), resolved or {}, 3, f"1.6 own pages {i}", "none")
    if n_own:
        notes.append(f"{n_own} of our pages cited here." if n_own > 1 else "1 of our pages cited here.")
    return [i, p["keyword"] or "n/a",
            f"{p['volume']:,} AI searches a month" if p["volume"] else "n/a",
            p["text"], T.intent_label(p["intent"]), engine_cell(p, "chatgpt"), prominence(p["best_rank"]),
            engine_cell(p, "ai_mode"), "", top(p["competitors"], 5), own_cell,
            top(p["third"], 4), S.compose(("Notes", notes), where=f"1.6 prompt {i}")]


TRACKING = re.compile(r"^(utm_[a-z]+|srsltid|gclid|fbclid)$", re.I)
NOT_A_PAGE = re.compile(r"^(www\.)?google\.[a-z.]+$|vertexaisearch\.cloud\.google\.com$", re.I)


def clean(url: str) -> str | None:
    """The address a person can open: tracking parameters and fragments stripped. None for engine-internal
    links (google.com/searchviewer, grounding redirects), which are not pages anyone can be listed on."""
    parts = urlsplit(url.strip())
    if not parts.netloc or NOT_A_PAGE.search(parts.netloc):
        return None
    q = urlencode([(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not TRACKING.match(k)])
    return urlunsplit((parts.scheme, parts.netloc, parts.path, q, ""))


def candidate_pages(prompts: list[dict]) -> dict[str, Counter]:
    """Per prompt text: cited third-party pages, cleaned and merged, most cited first."""
    out = {}
    for p in prompts:
        c = Counter()
        for u, n in p["third_urls"].items():
            cu = clean(u)
            if cu:
                c[cu] += n
        out[p["text"]] = c
    return out


def resolve_pages(prompts: list[dict], per_prompt: int = 6) -> dict[str, tuple[str, str | None]]:
    """{cleaned url: (address, "ok" | None)}. "ok" serves 200, redirects followed; None is dropped and printed.
    House rule (follow-the-redirect-before-you-judge): no URL that has not been shown to return 200 goes in a
    deliverable, so bot-walled directories (Yelp, Thumbtack: 403/202 on both reads) are dropped, not labelled."""
    return resolve_urls({u for c in candidate_pages(prompts).values() for u, _ in c.most_common(per_prompt)})


def resolve_urls(want) -> dict[str, tuple[str, str | None]]:
    """Core of resolve_pages, for any set of cleaned URLs (section A's own pages use it too)."""
    res = R.resolve_all(sorted(want))
    blocked = [u for u, (_, note) in res.items() if note.startswith("not verified")]
    # Directories (Yelp, Angi, BBB) refuse our requests with 403, which says nothing about the page. Those get a
    # second read through the page-fetch service before anything is dropped.
    with ThreadPoolExecutor(max_workers=4) as pool:
        second = dict(zip(blocked, pool.map(remote_status, blocked)))
    out = {}
    for u, (final, note) in res.items():
        if note == "" or note.startswith("resolved to"):
            out[u] = (final, "ok")
            continue
        code, landed = second.get(u, (None, u))
        if code == 200:
            out[u] = (landed, "ok")
        else:
            out[u] = (u, None)
            print(f"  cited page dropped, 200 not shown: {u} ({note}; second read: {code if code else 'no answer'})")
    return out


def remote_status(url: str) -> tuple[int | None, str]:
    """(HTTP status, landing url) through DataForSEO instant_pages. (None, url) when the call fails; the
    caller drops the page and prints why, so a failed check never reads as a pass."""
    try:
        d = G.post(G.creds(), "/v3/on_page/instant_pages", [{"url": url, "enable_javascript": False}])
        it = d["tasks"][0]["result"][0]["items"][0]
        return it.get("status_code"), (it.get("url") or url).split("#")[0]
    except Exception as e:  # noqa: BLE001 - reported by the caller
        print(f"  section B: second read failed for {url} ({type(e).__name__})")
        return None, url


def url_cell(ranked: list[str], resolved: dict, cap: int, where: str, empty: str) -> tuple[str, int]:
    """(cell, pages listed). Only pages shown to serve 200 are listed, in citation order, up to `cap`."""
    ok = []
    for u in ranked:
        final, state = resolved.get(u, (u, None))
        if state == "ok" and final not in ok:
            ok.append(final)
        if len(ok) == cap:
            break
    return ("\n".join(ok) or empty), len(ok)


def own_pages(p: dict) -> list[str]:
    """The prompt's own-site citations, cleaned and de-duplicated, in citation order."""
    out = []
    for u in p["own_urls"]:
        cu = clean(u)
        if cu and cu not in out:
            out.append(cu)
    return out


def rows_b(prompts: list[dict], resolve=None) -> list[list]:
    """Section B: up to 7 money prompts. `resolve` maps the chosen prompts to {cleaned url: 200 address or None}
    (resolve_pages by default; tests pass a stub)."""
    money = []
    for p in prompts:
        m, n = prompt_totals(p)
        if T.intent_label(p["intent"]) in F.MONEY_INTENT and n and p["competitors"]:
            money.append((pct(m, n), -sum(p["competitors"].values()), -(p["volume"] or 0), p))
    money.sort(key=lambda x: x[:3])
    chosen = [x[3] for x in money[:7]]
    resolved = (resolve or resolve_pages)(chosen) if chosen else {}
    out = []
    for p in chosen:
        m, n = prompt_totals(p)
        pages_cell, _ = url_cell([u for u, _ in candidate_pages([p])[p["text"]].most_common()], resolved, 3,
                                 f"1.6 pages {p['text'][:30]}",
                                 "none that serves 200" if p["third_urls"] else "none cited")
        if m:
            step = [f"Mentioned in {m} of {n} sampled answers, competitors lead.",
                    "Narrow gap: reinforce the pages the engines already cite instead of writing net-new content."]
        elif p["own_urls"]:
            step = ["Absent from the answers while our own pages are cited as sources for it.",
                    "A positioning problem on a page already being read, not a coverage gap."]
        else:
            lead = p["competitors"].most_common(1)
            step = ["Absent everywhere and none of our pages cited.",
                    "The nearest route in is the third-party pages listed, which the engines already read for this question"
                    + (f"; displacing {lead[0][0]} head-on is the slow path." if lead else ".")]
        out.append([p["text"], top(p["competitors"], 4), pages_cell,
                    S.compose(("Next step", step), where=f"1.6 gap {p['text'][:30]}"), ""])
    return out


def rows_c(prompts: list[dict]) -> list[list]:
    out = []
    for p in prompts:
        m, n = prompt_totals(p)
        if n >= 5 and m == 0 and not p["competitors"]:
            out.append([p["text"], S.compose(("Why stale", [
                f"No brand or competitor was named in any of {n} sampled answers.",
                "Either the wording misses how buyers ask, or the competitor list lacks the names the engines use.",
                "Check before keeping."]), where="1.6 section C"), ""])
    return out[:5]


def noise_points(prompts: int, engines: int) -> int:
    """Month-over-month noise floor in points, from this client's own observation count (recipe 1.6).

    Half-width of a 95% interval on a share near 50%: 1.96 * sqrt(0.25 / n) * 100, n = prompts x engines.
    It gives the recipe's original 12 at 25 prompts on 3 platforms (75 observations); a client scanning
    fewer prompts, or 2 engines, gets a wider floor instead of reporting noise as movement.
    """
    obs = max(1, prompts * engines)
    return math.ceil(98 / math.sqrt(obs))
HEADLINE = re.compile(r"(\d+)% \((\d+) of (\d+)\)")
WEEK = re.compile(r"week of (\d{4}-\d{2}-\d{2})")


def prev_month_key(cfg: dict) -> str | None:
    """Newest sheet_id_YYYY_MM key: the registry keeps the current workbook in sheet_id, prior ones dated."""
    keys = sorted(k for k in cfg if re.fullmatch(r"sheet_id_\d{4}_\d{2}", k))
    return keys[-1][len("sheet_id_"):] if keys else None


def last_month(cfg: dict, snap: dict, month: str | None) -> dict | None:
    """Last month's published figure and week, read from last month's tab, plus that week recomputed over
    THIS month's prompts. None when there is no prior tab or it carries no tracker headline (a baseline)."""
    sid = cfg.get(f"sheet_id_{month}") if month else None
    if not sid:
        return None
    g = S.read(sid, f"'{TAB}'!A4:C6")
    head = HEADLINE.match(str(g[0][1]) if g and len(g[0]) > 1 else "")
    wk = WEEK.search(str(g[2][2]) if len(g) > 2 and len(g[2]) > 2 else "")
    if not (head and wk):
        print(f"  last month's tab ({month}) has no tracker headline; reporting as baseline")
        return None
    pids = [p["pid"] for p in snap["prompts"]]
    conn = T.connect()
    try:
        m, n = T.sov_over(conn.cursor(), snap["client_id"], wk[1], pids)
    finally:
        conn.close()
    ran = re.match(r"(\d+) of", str(g[2][1]) if len(g) > 2 and len(g[2]) > 1 else "")
    return dict(week=wk[1], published=head[0], published_prompts=int(ran[1]) if ran else None,
                mentioned=m, answered=n)


def sov_cells(snap: dict, prev: dict | None) -> list[list]:
    h, n, used = sov(snap["totals"])
    labels = ", ".join(ENGINE_LABEL[e] for e in used)
    gem = snap["totals"].get("gemini")
    ran = len(snap["prompts"])
    per = round(snap["totals"]["chatgpt"]["answered"] / ran) if ran and snap["totals"].get("chatgpt") else 0
    cover = [f"Engines queried: {labels}. Perplexity is not run, so its column is empty, not zero.",
             f"Tracker week of {snap['week']} ({snap['why']}), {per} samples per prompt."]
    if gem and gem["answered"]:
        cover.append(f"Gemini names the brand in {pct(gem['mentioned'], gem['answered']):.0f}% of its answers; "
                     "it is not part of the SOV figure.")
    floor = noise_points(ran, len(used))
    if prev and prev["answered"]:
        now_p, was_p = pct(h, n), pct(prev["mentioned"], prev["answered"])
        delta = now_p - was_p
        move = (f"No measurable change: {delta:+.0f} points, under the {floor}-point noise floor "
                f"for {ran} prompts on {len(used)} engines."
                if abs(delta) < floor else f"{'Up' if delta > 0 else 'Down'} {abs(delta):.0f} points.")
        why = [move, f"Last month is the tracker week of {prev['week']}, recomputed over the same {ran} prompts."]
        if prev["published_prompts"] and prev["published_prompts"] != ran:
            why.append(f"Last month's tab showed {prev['published']} over {prev['published_prompts']} prompts; "
                       f"the tracker now scans {ran} of them.")
        prev_cells = [f"{was_p:.0f}% ({prev['mentioned']} of {prev['answered']})",
                      S.compose(("Change vs last month", why), where="1.6 SOV change")]
    else:
        prev_cells = ["baseline month", S.compose(("Change vs last month", [
            "Baseline month: last month's figure came from a different prompt set, so there is nothing to compare.",
            f"From next month, treat a move under {floor} points as noise, not movement ({ran} prompts on {len(used)} engines)."]),
            where="1.6 SOV change")]
    return [
        [f"{pct(h, n):.0f}% ({h} of {n})",
         S.compose(("Basis", [f"{h} of {n} sampled answers across {labels}, {ran} non-branded prompts.",
                              "Branded prompts are not part of this scan."]), where="1.6 SOV basis")],
        prev_cells,
        [f"{ran} of {ran}", S.compose(("Coverage", cover), where="1.6 coverage")]]


def fill(slug: str, check: bool = False) -> None:
    cfg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))[slug]
    sid = cfg.get("sheet_id")
    if not sid:
        print(f"{slug}: no current-month workbook, skipped")
        return
    snap = T.snapshot(cfg["domain"])
    anchors = F.preflight(sid)
    prompts = snap["prompts"]
    own = resolve_urls({u for p in prompts[:ROWS_A] for u in own_pages(p)})
    body = [row_a(i, p, own) for i, p in enumerate(prompts[:ROWS_A], 1)]
    # Everything is computed before the first write, so a failure leaves the tab untouched.
    prev = last_month(cfg, snap, prev_month_key(cfg))
    cells = sov_cells(snap, prev)
    brows, crows = rows_b(prompts), rows_c(prompts)
    h, n, used = sov(snap["totals"])
    print(f"{slug:<22} week {snap['week']}  SOV {pct(h, n):.1f}% ({h} of {n})  A:{len(body)}  B:{len(brows)}  "
          f"C:{len(crows)}  prompts {len(prompts)}  [{snap['why']}]")
    print(f"{'':<22} last month: {cells[1][0]}  |  " + cells[1][1].replace(chr(10), " "))
    if check:
        return

    col_a = S.read(sid, f"'{TAB}'!A1:A200")
    hdr = next(i for i, r in enumerate(col_a, 1) if r and str(r[0]).strip() == "#")
    first, have = hdr + 1, 0
    for r in col_a[hdr:]:
        if r and str(r[0]).strip().startswith("B."):
            break
        have += 1
    if len(body) > have:
        S.insert_rows(sid, TAB, first + have, len(body) - have)
        have = len(body)
    S.clear(sid, f"'{TAB}'!A{first}:M{first + have - 1}")
    S.write(sid, f"'{TAB}'!A{first}:M{first + len(body) - 1}", body)

    for key, vals in zip(("sov", "sov_prev", "run"), cells):
        S.write(sid, f"'{TAB}'!B{anchors[key]}:C{anchors[key]}", [vals])

    col_a = S.read(sid, f"'{TAB}'!A1:A200")
    b_first = next(i for i, r in enumerate(col_a, 1) if r and str(r[0]).strip().startswith("Money Prompt")) + 1
    c_row = next(i for i, r in enumerate(col_a, 1) if r and str(r[0]).strip().startswith("C. Prompt-set"))
    S.clear(sid, f"'{TAB}'!A{b_first}:E{c_row - 1}")
    if brows:
        S.write(sid, f"'{TAB}'!A{b_first}:E{b_first + len(brows) - 1}", brows)
    c_first = c_row + 2
    d_row = next((i for i, r in enumerate(col_a, 1) if r and str(r[0]).startswith("D. Weekly LLM tracker")), None)
    S.clear(sid, f"'{TAB}'!A{c_first}:H{(d_row or c_first + 12) + 20}")   # also removes a retired section D
    if crows:
        S.write(sid, f"'{TAB}'!A{c_first}:C{c_first + len(crows) - 1}", crows)

    out = Path(cfg["folder"]) / "ai_visibility" / f"tracker_{snap['week']}.json"
    keep = {k: v for k, v in snap.items() if k != "prompts"}
    keep["prompts"] = [{**p, "competitors": dict(p["competitors"]), "third": dict(p["third"]),
                        "third_urls": dict(p["third_urls"])} for p in prompts]
    out.write_text(json.dumps(keep, indent=1, default=str), encoding="utf-8")
    print(f"{'':<22} written")


if __name__ == "__main__":
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    args = [a for a in sys.argv[1:] if a != "--check"]
    names = F.active_slugs(reg) if args == ["all"] else args
    for s in names:
        fill(s, check="--check" in sys.argv)
