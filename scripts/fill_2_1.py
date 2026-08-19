"""Task 2.1 - populate the Technical Fixes tab from an authored fix file.

    python scripts/fill_2_1.py <client>

Reads Clients/<folder>/monthly_plan/fixes.yaml:

    fixes:      # priority-ordered: indexation > redirects/links > performance
      - source: # "1.2" | "1.4" | "1.8 verification (week 1)" etc.
        where:  # URL or scope
        fix:    # the detailed instruction INCLUDING its verify steps
    overflow:   # not completable this month -> next month's 1.8
      - {item: ..., scope: ...}
    score_note: # true -> writes the trend rule onto the 1.3 + 2.2 sheet

Only #, Source, Fix and Where/URL are written. Implemented By, Verified How,
Indexing Requested and Date stay blank - assignment is the owner's, completion
evidence is the implementer's. Template example rows are cleared first (the
workbook shipped with a fake fix row on every 2.1 tab).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io  # noqa: E402


def _tab_text(sid: str, tab: str, rng: str) -> str:
    return " ".join(str(c) for row in sheets_io.read(sid, f"'{tab}'!{rng}")
                    for c in row).lower()


def reconcile(sid: str) -> int:
    """Verify every routed Week-1 finding actually landed where it was routed.

    Reads the 1.2 findings log (# | Issue | URLs | Severity | Routed To) and
    the 1.4 section D fix items, then checks each item's presence on its
    target tab (2.1 or 1.8) by URL path, falling back to a distinctive issue
    token. Exists because the owner caught two routed findings missing from
    their target tabs on the EW pilot (2026-08-19) - the human must never be
    the reconciliation mechanism.
    """
    tabs = sheets_io.tab_names(sid)
    t12 = next(t for t in tabs if t.strip().startswith("1.2"))
    t14 = next(t for t in tabs if t.strip().startswith("1.4"))
    text = {
        "2.1": _tab_text(sid, next(t for t in tabs if t.strip().startswith("2.1")),
                         "A1:H40"),
        "1.8": _tab_text(sid, next(t for t in tabs if t.strip().startswith("1.8")),
                         "A1:F35"),
    }

    items = []      # (label, routed_to, keys)
    b = sheets_io.find_rows(sid, t12, {"log": "B. Findings log"})["log"]
    for row in sheets_io.read(sid, f"'{t12}'!A{b + 2}:F{b + 15}"):
        row += [""] * (6 - len(row))
        issue, urls, routed = str(row[1]), str(row[2]), str(row[4]).strip()
        if not issue.strip() or routed not in text:
            continue
        keys = [re.sub(r"https?://[^/]+", "", u).strip().strip("/").lower()
                for u in re.split(r"[;\s]+", urls) if u.startswith("http")]
        keys = [k for k in keys if k] or \
               [w.lower() for w in re.findall(r"[A-Za-z]{5,}", issue)[:2]]
        items.append((f"1.2 '{issue[:48]}'", routed, keys))
    try:
        d = sheets_io.find_rows(sid, t14, {"fix": "D. Fix"})["fix"]
        for row in sheets_io.read(sid, f"'{t14}'!A{d + 2}:B{d + 20}"):
            fix = str(row[0]) if row else ""
            if not fix.strip() or fix.lower().startswith("no fixes required"):
                continue
            keys = [re.sub(r"https?://[^/]+", "", u).strip().strip("/").lower()
                    for u in re.findall(r"https?://\S+", fix)] or \
                   [w.lower() for w in re.findall(r"[A-Za-z]{5,}", fix)[:2]]
            items.append((f"1.4 '{fix[:48]}'", "2.1", keys))
    except KeyError:
        pass

    missing = 0
    for label, routed, keys in items:
        ok = any(k in text[routed] for k in keys)
        if not ok:
            missing += 1
            print(f"  !! MISSING on {routed}: {label} (looked for {keys})")
    print(f"  reconcile: {len(items)} routed finding(s) checked, "
          f"{missing} missing" + ("" if missing else " - all landed"))
    return missing


def main(slug: str) -> None:
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    cfg = reg[slug]
    plan = yaml.safe_load(
        (Path(cfg["folder"]) / "monthly_plan/fixes.yaml").read_text(encoding="utf-8"))
    fixes = plan["fixes"]
    sid = cfg["sheet_id"]
    tab = next(t for t in sheets_io.tab_names(sid) if t.strip().startswith("2.1"))
    sheets_io.snapshot_tab(sid, tab, Path(cfg["folder"]) / "monthly_plan")

    p = sheets_io.find_rows(sid, tab, {"hdr": "#", "over": "Not completable"})
    top = p["hdr"] + 1
    cap = p["over"] - 1 - top
    if len(fixes) > cap:
        need = len(fixes) - cap
        sheets_io.insert_rows(sid, tab, p["over"] - 1, need)
        p = sheets_io.find_rows(sid, tab, {"hdr": "#", "over": "Not completable"})
        top = p["hdr"] + 1

    # Clear the whole queue area (template example rows included), then write.
    sheets_io.clear(sid, f"'{tab}'!A{top}:H{p['over'] - 2}")
    body = [[i, f["source"], f["fix"], f["where"]] for i, f in enumerate(fixes, 1)]
    r = sheets_io.write(sid, f"'{tab}'!A{top}:D{top + len(body) - 1}", body)

    over = plan.get("overflow") or []
    n_over = 0
    if over:
        o0 = p["over"] + 2
        sheets_io.write(sid, f"'{tab}'!A{o0}:B{o0 + len(over) - 1}",
                        [[o["item"], o.get("scope", "")] for o in over])
        n_over = len(over)

    note = ""
    if plan.get("score_note"):
        t13 = next((t for t in sheets_io.tab_names(sid) if "2.2" in t), None)
        if t13:
            q = sheets_io.find_rows(sid, t13, {"after": "Site Health score — after fixes"})
            sheets_io.write(sid, f"'{t13}'!C{q['after']}", [[
                "Trend rule: next month's 1.3 baseline is compared against THIS post-fix "
                "score (did the work hold?); the <92% fix-sheet trigger always reads next "
                "month's own fresh baseline."]])
            note = "  score-note added"

    print(f"{slug:<18} 2.1: {len(body)} fixes ({r.cells} cells, verified) "
          f"overflow: {n_over}{note}")
    reconcile(sid)


if __name__ == "__main__":
    main(sys.argv[1])
