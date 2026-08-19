#!/usr/bin/env python
"""Scrub the punctuation and vocabulary that make a deliverable read as AI-written.

Clients and senior stakeholders read em dashes as a machine tell. This script finds
them (plus the usual AI vocabulary) in any deliverable before it ships.

Usage
-----
    python scripts/scrub_ai_tells.py <file-or-folder> [...]        # check only
    python scripts/scrub_ai_tells.py <file-or-folder> --fix        # auto-fix safe cases
    python scripts/scrub_ai_tells.py <folder> --ext .md .xlsx      # limit file types

Supports .md, .txt, .csv and .xlsx (Excel cell text is checked too).

Exit codes: 0 = clean, 1 = tells found (so it can gate a build or a pre-commit hook).

What --fix will and won't touch
-------------------------------
It only rewrites cases where the correct replacement is unambiguous:

    ## Heading - Subtitle      ->  ## Heading: Subtitle
    | - |  (table cell)        ->  | n/a |
    word - word  (bare pair)   ->  word, word

Dashes inside a sentence are left alone and reported, because collapsing them to a
comma usually produces a worse sentence than rewriting it. Rewrite those by hand.

Note: real hyphens (K-12, top-of-page, walkthrough-first) are never touched. Only
em dash, en dash, horizontal bar and the Unicode minus sign are in scope.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Windows consoles default to cp1252 and raise UnicodeEncodeError on the very
# characters this script exists to report. Force UTF-8 on stdout and stderr.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

EM = "—"          # em dash
EN = "–"          # en dash
BAR = "―"         # horizontal bar
MINUS = "−"       # unicode minus

DASHES = {
    EM: "em dash",
    EN: "en dash",
    BAR: "horizontal bar",
    MINUS: "unicode minus",
}
DASH_CLASS = f"[{EM}{EN}{BAR}{MINUS}]"

TEXT_EXT = {".md", ".txt", ".csv"}
EXCEL_EXT = {".xlsx", ".xlsm"}

# Vocabulary that reads as machine-written in a client deliverable. Advisory only:
# these are never auto-fixed, because the right replacement depends on the sentence.
AI_WORDS = [
    "delve", "delves", "delving",
    "leverage", "leveraging", "leverages",
    "robust", "seamless", "seamlessly",
    "landscape", "realm", "tapestry", "testament",
    "crucial", "pivotal", "paramount",
    "underscore", "underscores", "underscoring",
    "myriad", "plethora",
    "harness", "harnessing",
    "unlock", "unlocking", "elevate", "elevating", "empower", "empowering",
    "game-changer", "game changer", "cutting-edge", "state-of-the-art",
    "furthermore", "moreover",
    "in today's", "it's worth noting", "it is worth noting",
    "navigate the", "navigating the",
    "when it comes to", "at the end of the day",
    "a testament to", "plays a vital role", "plays a crucial role",
]

AI_PHRASES = [
    (r"\bnot only\b[^.]{0,80}\bbut also\b", "'not only ... but also' construction"),
    (r"\bit'?s not (just )?\w+[^.]{0,40}, it'?s\b", "'it's not X, it's Y' construction"),
    (r"\bisn'?t (just )?about\b[^.]{0,40}\bit'?s about\b", "'isn't about X, it's about Y' construction"),
]

# Safe auto-fixes, applied in order.
SAFE_FIXES = [
    # Markdown heading:  "## Title - Subtitle"  ->  "## Title: Subtitle"
    (re.compile(rf"^(#{{1,6}} .+?) {DASH_CLASS} (.+)$", re.M), r"\1: \2"),
    # Bold label at line start: "**Label** - text" -> "**Label:** text"
    (re.compile(rf"^(\s*(?:[-*+]|\d+\.)?\s*)\*\*(.+?)\*\* {DASH_CLASS} ", re.M), r"\1**\2:** "),
    # Lone dash in a table cell -> n/a
    (re.compile(rf"\| {DASH_CLASS} \|"), "| n/a |"),
    (re.compile(rf"\|{DASH_CLASS}\|"), "|n/a|"),
]


class Finding:
    __slots__ = ("path", "loc", "kind", "detail", "text")

    def __init__(self, path, loc, kind, detail, text):
        self.path, self.loc, self.kind, self.detail, self.text = path, loc, kind, detail, text


def scan_text(text: str, path: Path, loc_prefix: str = "L") -> list[Finding]:
    found: list[Finding] = []
    for i, line in enumerate(text.split("\n"), 1):
        for ch, name in DASHES.items():
            if ch in line:
                found.append(Finding(path, f"{loc_prefix}{i}", "dash", name, line.strip()))
        low = line.lower()
        for w in AI_WORDS:
            if re.search(rf"\b{re.escape(w)}\b", low):
                found.append(Finding(path, f"{loc_prefix}{i}", "word", w, line.strip()))
        for pat, label in AI_PHRASES:
            if re.search(pat, low):
                found.append(Finding(path, f"{loc_prefix}{i}", "phrase", label, line.strip()))
    return found


def scan_excel(path: Path) -> list[Finding]:
    try:
        from openpyxl import load_workbook
    except ImportError:
        print(f"  (skipping {path.name}: openpyxl not installed)", file=sys.stderr)
        return []
    found: list[Finding] = []
    wb = load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if not isinstance(cell.value, str):
                    continue
                found.extend(scan_text(cell.value, path, loc_prefix=f"{ws.title}!{cell.coordinate} "))
    wb.close()
    return found


def apply_safe_fixes(text: str) -> tuple[str, int]:
    n = 0
    for pat, repl in SAFE_FIXES:
        text, k = pat.subn(repl, text)
        n += k
    return text, n


def gather(targets: list[str], exts: set[str]) -> list[Path]:
    files: list[Path] = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            files += [f for f in sorted(p.rglob("*")) if f.suffix.lower() in exts and f.is_file()]
        elif p.is_file():
            files.append(p)
        else:
            print(f"not found: {t}", file=sys.stderr)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", help="files or folders to scan")
    ap.add_argument("--fix", action="store_true", help="auto-fix the safe cases in text files")
    ap.add_argument("--ext", nargs="+", default=None, help="file extensions to include")
    ap.add_argument("--dashes-only", action="store_true", help="ignore vocabulary, report dashes only")
    args = ap.parse_args()

    exts = set(args.ext) if args.ext else (TEXT_EXT | EXCEL_EXT)
    files = gather(args.targets, exts)
    if not files:
        print("No matching files.")
        return 0

    all_found: list[Finding] = []
    fixed_total = 0

    for f in files:
        if f.suffix.lower() in EXCEL_EXT:
            all_found += scan_excel(f)
            continue

        text = f.read_text(encoding="utf-8", errors="replace")
        if args.fix:
            new, n = apply_safe_fixes(text)
            if n:
                f.write_text(new, encoding="utf-8", newline="\n")
                text = new
                fixed_total += n
                print(f"fixed {n} safe case(s) in {f.name}")
        all_found += scan_text(text, f)

    if args.dashes_only:
        all_found = [x for x in all_found if x.kind == "dash"]

    dashes = [x for x in all_found if x.kind == "dash"]
    words = [x for x in all_found if x.kind == "word"]
    phrases = [x for x in all_found if x.kind == "phrase"]

    print()
    print(f"Scanned {len(files)} file(s)")
    if args.fix:
        print(f"Auto-fixed: {fixed_total}")
    print(f"Dashes remaining : {len(dashes)}   (must be zero before shipping)")
    print(f"AI vocabulary    : {len(words)}   (advisory)")
    print(f"AI phrasing      : {len(phrases)}   (advisory)")

    if dashes:
        print("\nDASHES - rewrite these sentences by hand:")
        for x in dashes:
            print(f"  {x.path.name} {x.loc} [{x.detail}]")
            print(f"     {x.text[:150]}")

    if words:
        print("\nVOCABULARY - consider a plainer word:")
        seen: dict[str, int] = {}
        for x in words:
            seen[x.detail] = seen.get(x.detail, 0) + 1
        for w, c in sorted(seen.items(), key=lambda kv: -kv[1]):
            print(f"  {w} ({c})")

    if phrases:
        print("\nPHRASING:")
        for x in phrases:
            print(f"  {x.path.name} {x.loc} [{x.detail}]")
            print(f"     {x.text[:150]}")

    if not dashes and not words and not phrases:
        print("\nClean. Nothing that reads as AI-written.")

    return 1 if dashes else 0


if __name__ == "__main__":
    sys.exit(main())
