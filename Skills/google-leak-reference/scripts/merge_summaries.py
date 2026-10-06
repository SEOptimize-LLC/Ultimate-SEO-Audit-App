"""Validate agent-written module summaries and merge them into one committed file.

    python scripts/merge_summaries.py

Reads data/summaries/batch_*.jsonl, checks that every 0.4.0 Model module has
exactly one summary with a valid grade, then writes summaries/module_summaries.jsonl
(committed, unlike data/). build_index.py loads that file into the `summaries` table.
Exits non-zero on any gap so a partial merge never passes silently.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "leak.sqlite"
IN_DIR = ROOT / "data" / "summaries"
OUT = ROOT / "summaries" / "module_summaries.jsonl"
OVERRIDES = ROOT / "summaries" / "overrides.jsonl"
PREFIX = "GoogleApi.ContentWarehouse.V1.Model."
GRADES = {"none", "low", "medium", "high"}
BANNED = ("confirmed ranking", "confirms that", "boosts rankings", "ranking factor")


def main() -> int:
    db = sqlite3.connect(DB_PATH)
    expected = {r[0].replace(PREFIX, "") for r in db.execute(
        "SELECT module FROM modules WHERE version='0.4.0' AND module LIKE '%.Model.%'")}

    rows: dict[str, dict] = {}
    problems: list[str] = []
    for path in sorted(IN_DIR.glob("batch_*.jsonl")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"{path.name}:{n} bad JSON ({exc})")
                continue
            name = obj.get("module", "")
            if name not in expected:
                problems.append(f"{path.name}:{n} unknown module {name!r}")
                continue
            if name in rows:
                problems.append(f"{path.name}:{n} duplicate {name}")
                continue
            if obj.get("seo") not in GRADES:
                problems.append(f"{path.name}:{n} bad seo grade {obj.get('seo')!r} for {name}")
                continue
            if not str(obj.get("summary", "")).strip():
                problems.append(f"{path.name}:{n} empty summary for {name}")
                continue
            low = obj["summary"].lower()
            if any(b in low for b in BANNED):
                problems.append(f"{path.name}:{n} overclaiming phrase in {name}")
            rows[name] = {"module": name, "summary": obj["summary"].strip(), "seo": obj["seo"],
                          "why": str(obj.get("why", "")).strip()}

    # Hand corrections survive re-merges: summaries/overrides.jsonl, one {"module", "summary"[, "seo", "why"]} per line.
    if OVERRIDES.exists():
        for n, line in enumerate(OVERRIDES.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            o = json.loads(line)
            if o.get("module") not in rows:
                problems.append(f"overrides.jsonl:{n} unknown module {o.get('module')!r}")
                continue
            rows[o["module"]].update({k: o[k] for k in ("summary", "seo", "why") if k in o})

    missing = sorted(expected - set(rows))
    print(f"expected {len(expected)} | merged {len(rows)} | missing {len(missing)} | problems {len(problems)}")
    print("grades:", dict(Counter(r["seo"] for r in rows.values())))
    for p in problems[:40]:
        print("  PROBLEM", p)
    for m in missing[:40]:
        print("  MISSING", m)
    if problems or missing:
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for name in sorted(rows):
            fh.write(json.dumps(rows[name], ensure_ascii=False) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
