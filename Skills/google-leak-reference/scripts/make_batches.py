"""Split the 0.4.0 Model modules into text batches for summarization agents.

    python scripts/make_batches.py [--max-chars 150000]

Writes data/batches/batch_NN.txt (human-readable, short lines, so an agent can
page through it with Read) and data/batches/manifest.json. Modules are packed in
name order so each batch holds neighbouring namespaces.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "leak.sqlite"
OUT = ROOT / "data" / "batches"
VERSION = "0.4.0"
PREFIX = "GoogleApi.ContentWarehouse.V1.Model."
DOC_MAX = 700
ATTR_MAX = 260
LINKS_MAX = 12


def short(t: str) -> str:
    return t.replace(PREFIX, "")


def render(db: sqlite3.Connection, module: str, moduledoc: str) -> str:
    name = module.replace(PREFIX, "")
    lines = [f"### {name}", f"doc: {(moduledoc or '(none)')[:DOC_MAX].strip()}"]
    attrs = db.execute(
        "SELECT attr, type, description FROM attributes WHERE version=? AND module=? ORDER BY attr",
        (VERSION, module),
    ).fetchall()
    lines.append(f"attributes ({len(attrs)}):")
    for attr, typ, desc in attrs:
        d = (desc or "").strip()[:ATTR_MAX] or "(no description)"
        lines.append(f"- {attr} [{short(typ)[:70]}]: {d}")
    out_links = sorted({short(r[0]) for r in db.execute(
        "SELECT dst_module FROM edges WHERE version=? AND src_module=?", (VERSION, module))})
    n_in = db.execute("SELECT COUNT(DISTINCT src_module) FROM edges WHERE version=? AND dst_module=?",
                      (VERSION, module)).fetchone()[0]
    if out_links:
        extra = f" (+{len(out_links) - LINKS_MAX} more)" if len(out_links) > LINKS_MAX else ""
        lines.append("links to: " + ", ".join(out_links[:LINKS_MAX]) + extra)
    lines.append(f"referenced by {n_in} modules")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-chars", type=int, default=150_000)
    args = ap.parse_args()

    db = sqlite3.connect(DB_PATH)
    mods = db.execute(
        "SELECT module, moduledoc FROM modules WHERE version=? AND module LIKE '%.Model.%' ORDER BY module",
        (VERSION,),
    ).fetchall()

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("batch_*.txt"):
        old.unlink()

    batches: list[list[str]] = [[]]
    size = 0
    names: list[list[str]] = [[]]
    for module, doc in mods:
        block = render(db, module, doc)
        if size + len(block) > args.max_chars and batches[-1]:
            batches.append([])
            names.append([])
            size = 0
        batches[-1].append(block)
        names[-1].append(module.replace(PREFIX, ""))
        size += len(block)

    manifest = []
    for i, (blocks, ns) in enumerate(zip(batches, names, strict=True), start=1):
        path = OUT / f"batch_{i:02d}.txt"
        path.write_text("\n".join(blocks), encoding="utf-8")
        manifest.append({"batch": i, "file": path.name, "modules": len(ns), "first": ns[0], "last": ns[-1],
                         "chars": sum(len(b) for b in blocks)})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{len(mods)} modules -> {len(batches)} batches")
    for m in manifest:
        print(m)


if __name__ == "__main__":
    main()
