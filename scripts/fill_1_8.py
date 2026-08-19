"""Task 1.8 stage 3: populate the Monthly Plan tab from an authored plan file.

    python scripts/fill_1_8.py <client>

Reads Clients/<folder>/monthly_plan/plan.yaml:

    targets:            # 3-5, priority order; #1 -> 2.3, #2 -> 2.4, rest -> 3.1
      - url:            # page URL (or a labelled NEW BUILD line)
        clickup:        # "2.3" | "2.4" | "3.1" - must match the tab dropdown
        queries:        # target queries/prompts cell, with volumes
        pos:            # authored position evidence (live/GSC, with source)
        ai:             # authored AI-citation state for the baseline cell
        angle:          # one-sentence refresh angle
    deep_work:          # section C rows: {need, source, task}
    summary:            # exactly 3 bullets for section D

Section A baselines are COMPUTED, not authored: clicks and impressions come
from a fresh GSC May-Jul page-level pull at fill time, so every number in the
baseline cell traces to a query run today. Section B is pre-filled with the
target pages only - the Y/N verdict belongs to the content manager, and the
Decision dropdown is repaired here (the template shipped its sequencing option
split in two by the comma inside a ONE_OF_LIST value).

The 1.5 tab's "Selected in 1.8?" column is trued up to the actual lock, so
the two tabs never disagree about what was chosen.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io  # noqa: E402

MAY_JUL = (dt.date(2026, 5, 1), dt.date(2026, 7, 31))

DECISIONS = ["Proceed here", "Skip this month",
             "Sequence: content first - SEO next month",
             "Route to Content list (rewrite scope)"]


def norm_path(url: str) -> str:
    m = re.search(r"https?://[^/]+(/[^\s?#]*)", url or "")
    return (m.group(1) if m else (url or "")).rstrip("/") or "/"


def gsc_page_totals(cfg: dict) -> dict:
    """May-Jul clicks/impressions per page path, one query, matched loosely."""
    from task_1_5 import sc
    svc = sc()
    rows, at, out = [], 0, {}
    while True:
        r = svc.searchanalytics().query(siteUrl=cfg["gsc_property"], body={
            "startDate": str(MAY_JUL[0]), "endDate": str(MAY_JUL[1]),
            "dimensions": ["page"], "rowLimit": 25000, "startRow": at},
        ).execute().get("rows", [])
        rows += r
        if len(r) < 25000:
            break
        at += 25000
    for x in rows:
        p = norm_path(x["keys"][0])
        cur = out.setdefault(p, {"clicks": 0, "imp": 0})
        cur["clicks"] += x["clicks"]
        cur["imp"] += x["impressions"]
    return out


def fix_decision_dropdown(sheet_id: str, tab: str, r1: int, r2: int) -> None:
    svc = sheets_io.service()
    tid = sheets_io.tab_id(sheet_id, tab)
    sheets_io._call(svc.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"setDataValidation": {
            "range": {"sheetId": tid, "startRowIndex": r1 - 1, "endRowIndex": r2,
                      "startColumnIndex": 2, "endColumnIndex": 3},
            "rule": {"condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in DECISIONS]},
                "showCustomUi": True, "strict": False},
        }}]}))


def main(slug: str) -> None:
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    cfg = reg[slug]
    plan = yaml.safe_load(
        (Path(cfg["folder"]) / "monthly_plan/plan.yaml").read_text(encoding="utf-8"))
    targets = plan["targets"]
    assert 3 <= len(targets) <= 5, "1.8 selects 3-5 targets"
    assert len(plan["summary"]) == 3, "section D is exactly 3 bullets"

    sid = cfg["sheet_id"]
    tab = next(t for t in sheets_io.tab_names(sid) if t.strip().startswith("1.8"))
    rows = sheets_io.find_rows(sid, tab, {
        "a": "A. Selected targets", "b": "B. Content-calendar",
        "c": "C. Deep-work routing", "d": "D. Plan summary"})

    cap_a = rows["b"] - rows["a"] - 3
    cap_b = rows["c"] - rows["b"] - 3
    cap_c = rows["d"] - rows["c"] - 3
    if len(targets) > cap_a or len(targets) > cap_b:
        raise SystemExit(f"{slug}: plan needs more rows than the tab holds "
                         f"(A cap {cap_a}, B cap {cap_b})")

    gsc = gsc_page_totals(cfg)

    block_a = []
    for i, t in enumerate(targets, 1):
        p = gsc.get(norm_path(t["url"]))
        base = (f"{p['clicks']:,} clicks / {p['imp']:,} impressions (GSC May-Jul)"
                if p else "no GSC rows May-Jul (new/zero-traffic page)")
        block_a.append([i, t["url"], t["clickup"], t["queries"],
                        f"{base} / {t['pos']} / AI: {t['ai']}", t["angle"]])
    ra = sheets_io.write(sid, f"'{tab}'!A{rows['a'] + 2}:F{rows['a'] + 1 + len(block_a)}",
                         block_a)

    block_b = [[t["url"]] for t in targets]
    rb = sheets_io.write(sid, f"'{tab}'!A{rows['b'] + 2}:A{rows['b'] + 1 + len(block_b)}",
                         block_b)
    fix_decision_dropdown(sid, tab, rows["b"] + 2, rows["b"] + 1 + cap_b)

    deep = plan.get("deep_work") or []
    rc = None
    if deep:
        if len(deep) > cap_c:
            raise SystemExit(f"{slug}: {len(deep)} deep-work rows > cap {cap_c}")
        block_c = [[d["need"], d["source"], d.get("task", "")] for d in deep]
        rc = sheets_io.write(sid, f"'{tab}'!A{rows['c'] + 2}:C{rows['c'] + 1 + len(block_c)}",
                             block_c)

    block_d = [["• " + b] for b in plan["summary"]]
    rd = sheets_io.write(sid, f"'{tab}'!A{rows['d'] + 1}:A{rows['d'] + 3}", block_d)

    # True up 1.5's "Selected in 1.8?" column to the actual lock.
    tab15 = next(t for t in sheets_io.tab_names(sid) if t.strip().startswith("1.5"))
    b15 = sheets_io.find_rows(sid, tab15, {"b": "B. Ranked candidates"})["b"]
    grid = sheets_io.read(sid, f"'{tab15}'!A{b15 + 2}:I{b15 + 16}")
    chosen = {norm_path(t["url"]) for t in targets}
    flags, n_flip = [], 0
    for r in grid:
        r += [""] * (9 - len(r))
        if "http" not in str(r[1]):
            flags.append([r[8]])
            continue
        want = "Y" if norm_path(r[1]) in chosen else "N"
        if want != str(r[8]).strip():
            n_flip += 1
        flags.append([want])
    if flags:
        sheets_io.write(sid, f"'{tab15}'!I{b15 + 2}:I{b15 + 1 + len(flags)}", flags)

    print(f"{slug:<18} A: {len(block_a)} targets ({ra.cells} cells)  "
          f"B: {len(block_b)} candidates  C: {len(deep)} routed  D: 3 bullets  "
          f"1.5 sync: {n_flip} flag(s) flipped  dropdown repaired")


if __name__ == "__main__":
    main(sys.argv[1])
