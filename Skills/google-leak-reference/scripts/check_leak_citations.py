"""Pre-delivery check: every leaked attribute or module named in a deliverable must exist in the docs.

    python Skills/google-leak-reference/scripts/check_leak_citations.py <file> [<file> ...] [--allow name,name]

Reads .md, .txt, .csv and .xlsx (cell text). Exit codes:
    0  clean, or the deliverable cites no leak identifiers (nothing to check)
    1  at least one identifier is absent from the leaked docs: delivery blocked
    2  cannot run (index missing, file unreadable): delivery blocked, never read as a pass

What counts as a leak identifier
    * camelCase or PascalCase tokens found inside backticks or on a line within two lines of a
      leak keyword (leak, leaked, Content Warehouse).
    * Tokens on other lines are ignored unless they match a real name exactly, so code terms such
      as `robotsTxt` or schema.org's `areaServed` elsewhere in a report are not flagged.

Result per identifier
    exact      attribute or module name exists exactly                 -> pass
    substring  only part of a longer real name (e.g. siteEmbeddings)   -> WARN, nearest real names shown
    mention    appears verbatim in doc text but is not a field name    -> WARN
    absent     appears nowhere in the docs                             -> FAIL
    non-leak   a known term from testimony, public sources or web vocabulary -> INFO, tag claims DOJ-derived or public

This proves names exist. It does not prove the claim made about them: tag each claim documented,
inferred or DOJ-derived per the google-leak-reference skill.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = ROOT / "data" / "leak.sqlite"

LEAK_WORDS = re.compile(r"\bleak(?:ed|s)?\b|content[ -]?warehouse", re.I)
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{3,}")
CAMEL_RE = re.compile(r"[a-z][A-Z]|^[A-Z][a-z0-9]+[A-Z]")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
TAG_WORDS = re.compile(r"documented|inferred|doj|testimony|leak-derived|court", re.I)
WINDOW_CLAIM = re.compile(r"13[- ]month|70[- ]days?", re.I)
TESTIMONY = re.compile(r"doj|testimony|court|trial", re.I)

# System names that come from testimony, public statements or common SEO vocabulary rather than
# from these docs. Absent from the index by design, so they are information, not failures.
NON_LEAK_TERMS = {
    "rankembedbert", "rankbrain", "deeprank", "bert", "mum", "spambrain", "navboost", "glue",
    "mustang", "qstar", "twiddler", "twiddlers", "panda", "penguin", "hummingbird", "pagerank",
    "trustrank", "lighthouse", "robotstxt", "areaserved", "datemodified", "datepublished",
    "unsolicitedseotips",
}


def _load_name_level():
    spec = importlib.util.spec_from_file_location("build_commentary", HERE / "build_commentary.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_lines(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        import openpyxl

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        lines = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                for cell in row:
                    if isinstance(cell, str):
                        lines.extend(cell.splitlines())
        return lines
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def leak_context(lines: list[str]) -> set[int]:
    """Zero-based line indexes within two lines of a leak keyword."""
    return {j for i, ln in enumerate(lines) if LEAK_WORDS.search(ln) for j in range(i - 2, i + 3)}


def candidates(lines: list[str]) -> dict[str, list[int]]:
    """Map identifier -> line numbers where it is a possible leak citation (backticked, or in leak context)."""
    near = leak_context(lines)
    found: dict[str, list[int]] = {}
    for i, ln in enumerate(lines):
        in_ticks = {t for chunk in BACKTICK_RE.findall(ln) for t in TOKEN_RE.findall(chunk)}
        for tok in TOKEN_RE.findall(ln):
            if CAMEL_RE.search(tok) and (tok in in_ticks or i in near):
                found.setdefault(tok, []).append(i + 1)
    return found


def suggest(db: sqlite3.Connection, name: str, limit: int = 4) -> list[str]:
    """Real attribute or module names close to a wrong one (plural or truncated forms)."""
    stem = name.lower().rstrip("s")
    pat = f"{stem[: max(6, len(stem) - 3)]}%"
    rows = db.execute("SELECT DISTINCT attr FROM attributes WHERE version='0.4.0' AND lower(attr) LIKE ? LIMIT ?",
                      (pat, limit)).fetchall()
    rows += db.execute("SELECT DISTINCT replace(module, 'GoogleApi.ContentWarehouse.V1.Model.', '') FROM modules "
                       "WHERE version='0.4.0' AND lower(module) LIKE ? LIMIT ?", (f"%.model.{pat}", limit)).fetchall()
    return [r[0] for r in rows][:limit]


def nearest(db: sqlite3.Connection, name: str, limit: int = 4) -> list[str]:
    rows = db.execute(
        "SELECT DISTINCT attr FROM attributes WHERE version='0.4.0' AND lower(attr) LIKE ? LIMIT ?",
        (f"%{name.lower()}%", limit)).fetchall()
    return [r[0] for r in rows]


def check_file(path: Path, db: sqlite3.Connection, allow: set[str]) -> int:
    bc = _load_name_level()
    exact, joined, text = bc.load_index(db)
    exact_cs = {r[0] for r in db.execute("SELECT DISTINCT attr FROM attributes WHERE version='0.4.0'")}
    exact_cs |= {r[0].replace(bc.PREFIX, "") for r in db.execute(
        "SELECT module FROM modules WHERE version='0.4.0' AND module LIKE '%.Model.%'")}
    text_cs = " ".join((r[0] or "") for r in db.execute(
        "SELECT description FROM attributes WHERE version='0.4.0' UNION ALL SELECT moduledoc FROM modules WHERE version='0.4.0'"))
    lines = read_lines(path)
    found = candidates(lines)
    near = leak_context(lines)

    rows: dict[str, list[tuple[str, int]]] = {"exact": [], "substring": [], "mention": [], "absent": [], "non-leak": []}
    for tok, nums in sorted(found.items()):
        if tok in exact_cs:
            level = "exact"
        elif tok in text_cs:
            level = "mention"  # appears verbatim in doc text (proto or system name), not as a field name
        elif tok.lower() in joined:
            level = "substring"  # part of a longer real name, or the same letters in different casing
        else:
            level = "absent"  # includes names that match only as a loose phrase, e.g. trustedAnchors
        if level != "exact" and tok.lower() in NON_LEAK_TERMS | allow:
            level = "non-leak"
        if level != "exact" and not any(n - 1 in near for n in nums):
            continue  # a backticked code term far from any leak keyword is not a leak citation
        if level == "substring" and tok[0].isupper():
            level = "absent"  # a module-style name that is only the start of a longer module name is wrong as written
        rows[level].append((tok, nums[0]))

    cited = sum(len(v) for v in rows.values())
    print(f"== {path.name}")
    window_warnings = [
        f"   WARN  line {i + 1}: a 13-month or 70-day window sits beside a leak claim with no testimony source. "
        "These windows are not in the leaked docs."
        for i, ln in enumerate(lines)
        if WINDOW_CLAIM.search(ln) and LEAK_WORDS.search(ln) and not TESTIMONY.search(ln)
    ]
    if cited == 0:
        if window_warnings:
            print("   no leak identifiers found")
            print(*window_warnings, sep="\n")
        else:
            print("   no leak identifiers found: nothing to check")
        return 0
    print(f"   {cited} identifiers: {len(rows['exact'])} exact, {len(rows['substring']) + len(rows['mention'])} related, "
          f"{len(rows['absent'])} absent, {len(rows['non-leak'])} non-leak")
    for tok, n in rows["absent"]:
        hint = ", ".join(suggest(db, tok))
        print(f"   FAIL  {tok} (line {n}): not a field or module name in the leaked docs."
              + (f" Closest real names: {hint}." if hint else "") + " Correct the name or remove the claim.")
    for tok, n in rows["substring"]:
        near = ", ".join(nearest(db, tok)) or "none"
        print(f"   WARN  {tok} (line {n}): only part of a longer name. Nearest real names: {near}")
    for tok, n in rows["mention"]:
        print(f"   WARN  {tok} (line {n}): appears in doc text but is not a field name.")
    for tok, n in rows["non-leak"]:
        print(f"   INFO  {tok} (line {n}): known non-leak term (testimony, public sources or web vocabulary); tag any claim about it DOJ-derived or public.")

    if window_warnings:
        print(*window_warnings, sep="\n")
    untagged = [n for tok, n in rows["exact"] if not TAG_WORDS.search(lines[n - 1])]
    if untagged:
        print(f"   NOTE  {len(untagged)} cited identifiers have no documented/inferred/DOJ tag on their line "
              f"(first at line {untagged[0]}). Tag each claim per the google-leak-reference skill.")
    return 1 if rows["absent"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--allow", default="", help="comma-separated names to treat as known non-leak terms")
    args = ap.parse_args()
    if not DB_PATH.exists():
        print("ERROR: index missing. Run python Skills/google-leak-reference/scripts/build_index.py, "
              "then re-run this check. Delivery stays blocked until it runs.", file=sys.stderr)
        return 2
    allow = {a.strip().lower() for a in args.allow.split(",") if a.strip()}
    db = sqlite3.connect(DB_PATH)
    worst = 0
    for f in args.files:
        p = Path(f)
        try:
            code = check_file(p, db, allow)
        except Exception as exc:  # unreadable file must not read as a pass
            print(f"ERROR: could not check {p}: {exc}", file=sys.stderr)
            return 2
        worst = max(worst, code)
    return worst


if __name__ == "__main__":
    sys.exit(main())
