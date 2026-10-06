"""Query the leaked Content Warehouse index.

    python scripts/lookup.py attr siteAuthority          # exact attribute name (case-insensitive), all modules
    python scripts/lookup.py find trusted anchor         # substring search: attribute names, descriptions, summaries
    python scripts/lookup.py module PerDocData           # doc, summary, attributes, links in and out
    python scripts/lookup.py links CompressedQualitySignals
    python scripts/lookup.py seo high [--prefix Quality] # modules graded for SEO relevance
    python scripts/lookup.py versions PerDocData         # which package versions contain the module
    python scripts/lookup.py claims siteFocusScore       # third-party commentary about a name, with its grade and name check

All results come from package version 0.4.0 unless --version is given. Output is
documentation text only: a field's existence is not evidence it affects ranking.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "leak.sqlite"
PREFIX = "GoogleApi.ContentWarehouse.V1.Model."


def short(s: str) -> str:
    return s.replace(PREFIX, "")


def resolve(db, name: str, version: str) -> list[str]:
    rows = db.execute("SELECT module FROM modules WHERE version=? AND module LIKE ? ORDER BY module",
                      (version, f"%.{name}")).fetchall()
    return [r[0] for r in rows]


def cmd_attr(db, a):
    rows = db.execute(
        "SELECT module, attr, type, description FROM attributes WHERE version=? AND lower(attr)=lower(?) ORDER BY module",
        (a.version, a.name)).fetchall()
    if not rows:
        print(f"no attribute named {a.name!r} in {a.version}. Try: find {a.name}")
        return 1
    for module, attr, typ, desc in rows:
        print(f"{short(module)}.{attr}  [{short(typ)}]\n    {desc or '(no description in the docs)'}")
    return 0


def cmd_find(db, a):
    pat = f"%{' '.join(a.text).lower()}%"
    print("== attributes ==")
    for module, attr, desc in db.execute(
            "SELECT module, attr, description FROM attributes WHERE version=? AND (lower(attr) LIKE ? OR lower(description) LIKE ?) LIMIT ?",
            (a.version, pat, pat, a.limit)):
        print(f"{short(module)}.{attr}: {(desc or '')[:160]}")
    print("== module summaries ==")
    try:
        for module, summ, seo in db.execute(
                "SELECT module, summary, seo FROM summaries WHERE lower(summary) LIKE ? OR lower(module) LIKE ? LIMIT ?",
                (pat, pat, a.limit)):
            print(f"[{seo}] {module}: {summ[:160]}")
    except sqlite3.OperationalError:
        print("(summaries not loaded: run merge_summaries.py then build_index.py)")
    return 0


def cmd_module(db, a):
    mods = resolve(db, a.name, a.version)
    if not mods:
        print(f"no module named {a.name!r} in {a.version}")
        return 1
    for module in mods:
        print(f"## {short(module)}")
        doc = db.execute("SELECT moduledoc FROM modules WHERE version=? AND module=?", (a.version, module)).fetchone()[0]
        print("doc:", doc or "(none)")
        try:
            row = db.execute("SELECT summary, seo, why FROM summaries WHERE module=?", (short(module),)).fetchone()
            if row:
                print(f"summary [{row[1]}]: {row[0]}  ({row[2]})")
        except sqlite3.OperationalError:
            pass
        for attr, typ, desc in db.execute(
                "SELECT attr, type, description FROM attributes WHERE version=? AND module=? ORDER BY attr", (a.version, module)):
            print(f"  - {attr} [{short(typ)}]: {desc or '(no description)'}")
        cmd_links(db, argparse.Namespace(name=short(module), version=a.version))
    return 0


def cmd_links(db, a):
    for module in resolve(db, a.name, a.version):
        out = db.execute("SELECT attr, dst_module FROM edges WHERE version=? AND src_module=? ORDER BY attr", (a.version, module)).fetchall()
        inn = db.execute("SELECT src_module, attr FROM edges WHERE version=? AND dst_module=? ORDER BY src_module", (a.version, module)).fetchall()
        print(f"links from {short(module)}: " + (", ".join(f"{x}->{short(y)}" for x, y in out) or "none"))
        print("referenced by: " + (", ".join(f"{short(x)}.{y}" for x, y in inn[:30]) or "none") + (f" (+{len(inn) - 30} more)" if len(inn) > 30 else ""))
    return 0


def cmd_seo(db, a):
    order = ["none", "low", "medium", "high"]
    want = order[order.index(a.grade):]
    q = f"SELECT module, seo, summary FROM summaries WHERE seo IN ({','.join('?' * len(want))})"
    args = list(want)
    if a.prefix:
        q += " AND module LIKE ?"
        args.append(f"{a.prefix}%")
    q += " ORDER BY module LIMIT ?"
    args.append(a.limit)
    for module, seo, summ in db.execute(q, args):
        print(f"[{seo}] {module}: {summ[:140]}")
    return 0


def cmd_claims(db, a):
    pat = f"%{a.term.lower()}%"
    rows = db.execute(
        "SELECT id, call, name_check, class, source, claim, reason FROM claims "
        "WHERE lower(names) LIKE ? OR lower(claim) LIKE ? ORDER BY call, id LIMIT ?", (pat, pat, a.limit)).fetchall()
    if not rows:
        print(f"no commentary claims mention {a.term!r}")
        return 1
    for cid, call, check, cls, src, claim, reason in rows:
        print(f"[{call} | names:{check} | {cls}] {cid} {src}")
        print(f"    {claim}")
        print(f"    grader: {reason}")
    print("Grades are second-hand judgments of commentary. A name check proves a name exists, not that the claim is right.")
    return 0


def cmd_versions(db, a):
    for v, m in db.execute("SELECT version, module FROM modules WHERE module LIKE ? ORDER BY version", (f"%.{a.name}",)):
        n = db.execute("SELECT COUNT(*) FROM attributes WHERE version=? AND module=?", (v, m)).fetchone()[0]
        print(f"{v}: {short(m)} ({n} attributes)")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="0.4.0")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("attr", cmd_attr), ("module", cmd_module), ("links", cmd_links), ("versions", cmd_versions)):
        p = sub.add_parser(name)
        p.add_argument("name")
        p.set_defaults(fn=fn)
    p = sub.add_parser("find")
    p.add_argument("text", nargs="+")
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(fn=cmd_find)
    p = sub.add_parser("claims")
    p.add_argument("term")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_claims)
    p = sub.add_parser("seo")
    p.add_argument("grade", choices=["low", "medium", "high"])
    p.add_argument("--prefix")
    p.add_argument("--limit", type=int, default=60)
    p.set_defaults(fn=cmd_seo)
    a = ap.parse_args()
    if not DB_PATH.exists():
        print("index missing: run python scripts/build_index.py", file=sys.stderr)
        return 2
    return a.fn(sqlite3.connect(DB_PATH), a)


if __name__ == "__main__":
    sys.exit(main())
