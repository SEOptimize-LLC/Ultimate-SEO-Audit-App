"""Normalize third-party commentary digests and check their cited names against the primary source.

    python scripts/build_commentary.py     # needs data/leak.sqlite; writes commentary/claims.jsonl

Input: commentary/raw/commentary_{A,B,C}.json (graded digests of 20 commentary pages).
Each claim keeps the author's grade (KEEP / KEEP-WITH-CAVEAT / DISCARD) and gains
`names` (identifiers parsed from the cited text) and `name_check`:
    verified   every cited name is an exact attribute or module name in the 0.4.0 docs
    related    every name is found, but some only as part of a longer name or in doc text
    partial    some names are found, some are absent
    not_found  no cited name appears anywhere in the docs
    none_cited the author named no attribute or module
`name_check` tests that a name exists. It does not test the claim made about it.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "leak.sqlite"
RAW = ROOT / "commentary" / "raw"
OUT = ROOT / "commentary" / "claims.jsonl"
PREFIX = "GoogleApi.ContentWarehouse.V1.Model."
NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,}")
CAMEL_RE = re.compile(r"[a-z][A-Z]|^[A-Z][a-z0-9]+[A-Z]")
SKIP_CLASSES = {"SOURCE_NOTE"}
SKIP_CALLS = {"FAILED"}


def load_index(db: sqlite3.Connection) -> tuple[set[str], str, str]:
    """Return (exact names, joined names for substring tests, joined doc text), all lowercase."""
    names = {r[0].lower() for r in db.execute("SELECT DISTINCT attr FROM attributes WHERE version='0.4.0'")}
    names |= {r[0].replace(PREFIX, "").lower() for r in db.execute(
        "SELECT module FROM modules WHERE version='0.4.0' AND module LIKE '%.Model.%'")}
    text = " ".join((r[0] or "") for r in db.execute(
        "SELECT description FROM attributes WHERE version='0.4.0' UNION ALL "
        "SELECT moduledoc FROM modules WHERE version='0.4.0'")).lower()
    return names, " ".join(sorted(names)), text


def name_level(name: str, exact: set[str], joined: str, text: str) -> str:
    n = name.lower()
    if n in exact:
        return "exact"
    if n in joined:
        return "substring"
    if n in text or re.sub(r"[^a-z0-9]", "", n) in re.sub(r"[^a-z0-9]", "", text):
        return "mention"
    return "absent"


def main() -> int:
    if not DB_PATH.exists():
        print("index missing: run scripts/build_index.py first", file=sys.stderr)
        return 2
    exact, joined, text = load_index(sqlite3.connect(DB_PATH))
    out, skipped = [], 0
    for path in sorted(RAW.glob("commentary_*.json")):
        batch = path.stem.split("_")[-1]
        for e in json.loads(path.read_text(encoding="utf-8")):
            cls = e.get("cls") or e.get("class") or e.get("entry_type") or ""
            call = e.get("call") or ""
            if "claim" not in e or cls in SKIP_CLASSES or call in SKIP_CALLS:
                skipped += 1  # per-source verdict rows and failed-fetch notes carry no claim
                continue
            cited = str(e.get("attributes") or e.get("modules") or "none cited")
            names = sorted({n for n in NAME_RE.findall(cited) if CAMEL_RE.search(n)})
            levels = {n: name_level(n, exact, joined, text) for n in names}
            if not names:
                check = "none_cited"
            elif all(v == "exact" for v in levels.values()):
                check = "verified"
            elif all(v != "absent" for v in levels.values()):
                check = "related"
            elif any(v != "absent" for v in levels.values()):
                check = "partial"
            else:
                check = "not_found"
            out.append({
                "id": f"{batch}-{e.get('id')}", "source": e.get("source", ""), "cited": cited,
                "names": names, "name_levels": levels, "name_check": check, "claim": e["claim"], "class": cls,
                "call": call, "reason": e.get("reason", ""),
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for row in out:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tally: dict[tuple[str, str], int] = {}
    for r in out:
        tally[(r["call"], r["name_check"])] = tally.get((r["call"], r["name_check"]), 0) + 1
    print(f"claims {len(out)} | skipped non-claim rows {skipped} | wrote {OUT}")
    for k in sorted(tally):
        print(f"  {k[0]:<18} {k[1]:<11} {tally[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
