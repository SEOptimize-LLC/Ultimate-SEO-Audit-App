"""Task 2.3/2.4/3.1 - populate the Refresh Log tab from the locked 1.8 plan.

    python scripts/fill_2_3.py <client> [--dry-run] [--force]

Reads Clients/<folder>/monthly_plan/plan.yaml (targets: url, clickup, queries,
ai, angle) and the client's 1.8 tab section A (baseline cells, copied VERBATIM
so the two tabs always reconcile). Writes one row per target into the
"2.3-3.1 Refresh Log" tab, columns A:G ONLY:

    A ClickUp Task | B Page URL | C Target Queries (+ the full refresh angle,
    which carries any step-0 revision gates) | D Baseline Clicks |
    E Baseline Impr | F Baseline Pos (narrative) | G AI Cited (1.6)

Columns H onward (Outdated Cut ... Date Done) are SOP completion records and
are NEVER written by this script - they mean "verified done" and get filled
per-row as work ships (see Skills/monthly-seo-workbook/tasks/2.3.md).

Safety: snapshots the tab first; refuses to overwrite a tab that already
holds real (non-example) rows unless --force. EW pilot rows (2026-08-20)
count as real rows.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io  # noqa: E402

EXAMPLE_TOKENS = ("/services/water-heater-repair",)  # template sample row

BASELINE_RE = re.compile(
    r"([\d,]+) clicks / ([\d,]+) impressions \(GSC ([^)]+)\) / (.*)", re.S)


def split_baseline(text: str) -> tuple[str, str, str]:
    m = BASELINE_RE.match(text.strip())
    if not m:
        return "", "", text.strip()
    return m.group(1), m.group(2), f"({m.group(3)}) {m.group(4)}"


def ai_cell(ai_text: str) -> str:
    t = (ai_text or "").strip()
    if not t:
        return ""
    low = t.lower()
    if low.startswith(("no tracked", "absent")):
        return f"N - {t}"
    return t


def main(slug: str, dry: bool = False, force: bool = False) -> None:
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    cfg = reg[slug]
    plan = yaml.safe_load(
        (Path(cfg["folder"]) / "monthly_plan/plan.yaml").read_text(encoding="utf-8"))
    targets = plan["targets"]
    sid = cfg["sheet_id"]
    tab = next(t for t in sheets_io.tab_names(sid) if t.strip().startswith("2.3"))

    # 1.8 section A baselines, verbatim, keyed by URL (slash-insensitive)
    t18 = next(t for t in sheets_io.tab_names(sid) if t.strip().startswith("1.8"))
    p18 = sheets_io.find_rows(sid, t18, {"a": "A. Selected targets"})
    b18 = {}
    for row in sheets_io.read(sid, f"'{t18}'!A{p18['a'] + 2}:E{p18['a'] + 2 + 6}"):
        if len(row) >= 5 and str(row[1]).startswith("http"):
            b18[str(row[1]).strip().rstrip("/")] = str(row[4]).strip()

    rows = []
    for t in targets:
        clicks, impr, pos = split_baseline(b18.get(t["url"].rstrip("/"), ""))
        if not clicks:
            print(f"  !! no 1.8 baseline matched for {t['url']} - baseline cells left blank")
        queries = re.sub(r"\s+", " ", t.get("queries", "").strip())
        angle = re.sub(r"[ \t]+", " ", t.get("angle", "").strip())
        rows.append([t.get("clickup", ""), t["url"],
                     f"{queries}\nANGLE: {angle}",
                     clicks, impr, pos, ai_cell(t.get("ai", ""))])

    if dry:
        for r in rows:
            print("-" * 70)
            print(f"{r[0]} | {r[1]}")
            print(f"  C: {r[2][:180]}...")
            print(f"  D/E/F: {r[3]} / {r[4]} / {r[5][:80]}")
            print(f"  G: {r[6][:80]}")
        print(f"(dry run - nothing written; {len(rows)} rows built)")
        return

    p = sheets_io.find_rows(sid, tab, {"hdr": "ClickUp Task", "unv": "Unviable mid-work"})
    top = p["hdr"] + 1
    existing = sheets_io.read(sid, f"'{tab}'!A{top}:C{p['unv'] - 2}")
    real = [r for r in existing
            if len(r) > 1 and str(r[1]).strip()
            and not any(tok in str(r[1]) for tok in EXAMPLE_TOKENS)]
    if real and not force:
        print(f"{slug}: tab already holds {len(real)} real row(s) - refusing to "
              f"overwrite. Re-run with --force to replace, or edit by hand.")
        return

    sheets_io.snapshot_tab(sid, tab, Path(cfg["folder"]) / "monthly_plan")
    cap = p["unv"] - 1 - top
    if len(rows) > cap:
        sheets_io.insert_rows(sid, tab, p["unv"] - 1, len(rows) - cap)
        p = sheets_io.find_rows(sid, tab, {"hdr": "ClickUp Task", "unv": "Unviable mid-work"})
        top = p["hdr"] + 1
    # replace the queue area's A:G only - checkpoint columns are never touched
    sheets_io.clear(sid, f"'{tab}'!A{top}:G{p['unv'] - 2}")
    r = sheets_io.write(sid, f"'{tab}'!A{top}:G{top + len(rows) - 1}", rows)
    print(f"{slug:<18} 2.3 refresh log: {len(rows)} targets ({r.cells} cells, verified)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], dry="--dry-run" in sys.argv, force="--force" in sys.argv)
