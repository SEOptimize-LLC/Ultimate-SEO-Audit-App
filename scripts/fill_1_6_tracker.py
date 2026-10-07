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
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fill_1_6_all as F  # noqa: E402
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


def row_a(i: int, p: dict) -> list:
    m, n = prompt_totals(p)
    notes = []
    if n and m == 0:
        notes.append("Absent from every sampled answer."
                     + (f" Named instead: {top(p['competitors'], 3, lambda k, c: k)}." if p["competitors"] else ""))
    elif m:
        notes.append(f"Mentioned in {m} of {n} sampled answers.")
    if p["own_urls"]:
        notes.append(f"{len(p['own_urls'])} of our URLs cited here.")
    return [i, p["keyword"] or "n/a",
            f"{p['volume']:,} AI searches a month" if p["volume"] else "n/a",
            p["text"], T.intent_label(p["intent"]), engine_cell(p, "chatgpt"), prominence(p["best_rank"]),
            engine_cell(p, "ai_mode"), "", top(p["competitors"], 5), "\n".join(p["own_urls"][:3]) or "none",
            top(p["third"], 4), S.compose(("Notes", notes), where=f"1.6 prompt {i}")]


def rows_b(prompts: list[dict]) -> list[list]:
    money = []
    for p in prompts:
        m, n = prompt_totals(p)
        if T.intent_label(p["intent"]) in F.MONEY_INTENT and n and p["competitors"]:
            money.append((pct(m, n), -sum(p["competitors"].values()), -(p["volume"] or 0), p))
    money.sort(key=lambda x: x[:3])
    out = []
    for _, _, _, p in money[:7]:
        m, n = prompt_totals(p)
        pages = [u for u, _ in p["third_urls"].most_common(3)]
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
        out.append([p["text"], top(p["competitors"], 4), "\n".join(pages) or "none cited",
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


def sov_cells(snap: dict) -> list[list]:
    h, n, used = sov(snap["totals"])
    labels = ", ".join(ENGINE_LABEL[e] for e in used)
    gem = snap["totals"].get("gemini")
    ran = len(snap["prompts"])
    cover = [f"Engines queried: {labels}. Perplexity is not run, so its column is empty, not zero.",
             f"Tracker week of {snap['week']} ({snap['why']}), 5 samples per prompt."]
    if gem and gem["answered"]:
        cover.append(f"Gemini names the brand in {pct(gem['mentioned'], gem['answered']):.0f}% of its answers; "
                     "it is not part of the SOV figure.")
    return [
        [f"{pct(h, n):.0f}% ({h} of {n})",
         S.compose(("Basis", [f"{h} of {n} sampled answers across {labels}, {ran} non-branded prompts.",
                              "Branded prompts are not part of this scan."]), where="1.6 SOV basis")],
        ["baseline month",
         S.compose(("Change vs last month", [
             "Baseline month: last month's figure came from a different prompt set, so there is nothing to compare.",
             "From next month, treat a move under 12 points as noise, not movement."]), where="1.6 SOV change")],
        [f"{ran} of {ran}", S.compose(("Coverage", cover), where="1.6 coverage")]]


def fill(slug: str) -> None:
    cfg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))[slug]
    sid = cfg.get("sheet_id")
    if not sid:
        print(f"{slug}: no current-month workbook, skipped")
        return
    snap = T.snapshot(cfg["domain"])
    anchors = F.preflight(sid)
    prompts = snap["prompts"]
    body = [row_a(i, p) for i, p in enumerate(prompts[:ROWS_A], 1)]

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

    for key, vals in zip(("sov", "sov_prev", "run"), sov_cells(snap)):
        S.write(sid, f"'{TAB}'!B{anchors[key]}:C{anchors[key]}", [vals])

    col_a = S.read(sid, f"'{TAB}'!A1:A200")
    b_first = next(i for i, r in enumerate(col_a, 1) if r and str(r[0]).strip().startswith("Money Prompt")) + 1
    c_row = next(i for i, r in enumerate(col_a, 1) if r and str(r[0]).strip().startswith("C. Prompt-set"))
    S.clear(sid, f"'{TAB}'!A{b_first}:E{c_row - 1}")
    brows = rows_b(prompts)
    if brows:
        S.write(sid, f"'{TAB}'!A{b_first}:E{b_first + len(brows) - 1}", brows)
    c_first = c_row + 2
    d_row = next((i for i, r in enumerate(col_a, 1) if r and str(r[0]).startswith("D. Weekly LLM tracker")), None)
    S.clear(sid, f"'{TAB}'!A{c_first}:H{(d_row or c_first + 12) + 20}")   # also removes a retired section D
    crows = rows_c(prompts)
    if crows:
        S.write(sid, f"'{TAB}'!A{c_first}:C{c_first + len(crows) - 1}", crows)

    out = Path(cfg["folder"]) / "ai_visibility" / f"tracker_{snap['week']}.json"
    keep = {k: v for k, v in snap.items() if k != "prompts"}
    keep["prompts"] = [{**p, "competitors": dict(p["competitors"]), "third": dict(p["third"]),
                        "third_urls": dict(p["third_urls"])} for p in prompts]
    out.write_text(json.dumps(keep, indent=1, default=str), encoding="utf-8")
    h, n, used = sov(snap["totals"])
    print(f"{slug:<22} week {snap['week']}  SOV {pct(h, n):.1f}% ({h} of {n})  A:{len(body)}  B:{len(brows)}  "
          f"C:{len(crows)}  prompts {len(prompts)}  [{snap['why']}]")


if __name__ == "__main__":
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    names = F.active_slugs(reg) if sys.argv[1:] == ["all"] else sys.argv[1:]
    for s in names:
        fill(s)
