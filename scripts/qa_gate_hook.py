#!/usr/bin/env python
"""Claude Code hook: enforce the scripted pre-delivery QA checks on client deliverables.

Pre-delivery QA lists 14 checks, but only two have scripts (CHECK 12, the dash scrub, and CHECK 14, the
leak-citation name check) and nothing ran them. This hook runs both at the moment a deliverable is written.
The other twelve checks stay procedural.

    python scripts/qa_gate_hook.py pre     # PreToolUse on Write|Edit: blocks the write (exit 2)
    python scripts/qa_gate_hook.py post    # PostToolUse on Bash: feeds back on a fresh .xlsx (exit 2)

Scope: files under Clients/<name>/Full SEO Audit/ only (the QA skill's own trigger). Text files (.md, .txt,
.csv) are checked before they are written; .xlsx files are produced by scripts through Bash, so they are checked
right after, when a workbook there was modified in the last three minutes. Edits are checked on the text being
added, so old dashes in untouched parts of a file never block an unrelated edit.

Exit codes: 0 allow, 2 block or feed back (stderr reaches Claude), 1 the hook itself failed (non-blocking,
so a bug here cannot lock up work). Set QA_GATE_CLIENTS_DIR to point the post scan at another folder (tests).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRUB = ROOT / "scripts" / "scrub_ai_tells.py"
LEAK = ROOT / "Skills" / "google-leak-reference" / "scripts" / "check_leak_citations.py"
PROTECTED = re.compile(r"(?:^|/)Clients/[^/]+/Full SEO Audit/", re.I)
TEXT_SUFFIXES = {".md", ".txt", ".csv"}
FRESH_SECONDS = 180
LEAK_WORDS = re.compile(r"\bleak(?:ed|s)?\b|content[ -]?warehouse", re.I)
LEAK_TICKS = re.compile(r"`(?:[a-z]+[A-Z]\w*|[A-Z][a-z0-9]+[A-Z]\w*)`")


def run(script: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120,
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def check_text(name: str, text: str) -> list[str]:
    """Run CHECK 12 and, when the text cites the leak, CHECK 14. Returns failure messages."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(text, encoding="utf-8")
        code, out = run(SCRUB, str(path), "--dashes-only")
        if code != 0:
            failures.append(f"CHECK 12 (AI-tell scrub) failed:\n{out}")
        if LEAK_WORDS.search(text) or LEAK_TICKS.search(text):
            code, out = run(LEAK, str(path))
            if code != 0:
                failures.append(f"CHECK 14 (leak citations) failed:\n{out}")
    return failures


def check_file(path: Path) -> list[str]:
    failures: list[str] = []
    code, out = run(SCRUB, str(path), "--dashes-only")
    if code != 0:
        failures.append(f"CHECK 12 (AI-tell scrub) failed:\n{out}")
    code, out = run(LEAK, str(path))
    if code != 0:
        failures.append(f"CHECK 14 (leak citations) failed:\n{out}")
    return failures


def pre(event: dict) -> int:
    tool = event.get("tool_name", "")
    data = event.get("tool_input", {}) or {}
    file_path = str(data.get("file_path", "")).replace("\\", "/")
    if not PROTECTED.search(file_path) or Path(file_path).suffix.lower() not in TEXT_SUFFIXES:
        return 0
    text = data.get("content") if tool == "Write" else data.get("new_string")
    if not text:
        return 0
    failures = check_text(Path(file_path).name, text)
    if not failures:
        return 0
    print(f"Pre-delivery QA blocked this {tool} to {file_path}.\n\n" + "\n\n".join(failures) +
          "\n\nFix the text and write it again. These checks are defined in "
          "Skills/data-analysis/pre-delivery-qa/SKILL.md.", file=sys.stderr)
    return 2


def post(event: dict) -> int:
    clients = Path(os.environ.get("QA_GATE_CLIENTS_DIR", ROOT / "Clients"))
    if not clients.is_dir():
        return 0
    cutoff = time.time() - FRESH_SECONDS
    fresh = [p for p in clients.glob("*/Full SEO Audit/**/*.xlsx")
             if not p.name.startswith("~$") and p.stat().st_mtime >= cutoff]
    failures: list[str] = []
    for p in sorted(fresh):
        for msg in check_file(p):
            failures.append(f"{p.name}: {msg}")
    if not failures:
        return 0
    print("Pre-delivery QA found problems in a workbook just written under Full SEO Audit/.\n\n" +
          "\n\n".join(failures) + "\n\nFix the workbook before delivering it. Checks are defined in "
          "Skills/data-analysis/pre-delivery-qa/SKILL.md.", file=sys.stderr)
    return 2


def main() -> int:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # Windows defaults to cp1252; Claude reads UTF-8
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in {"pre", "post"}:
        print("usage: qa_gate_hook.py pre|post", file=sys.stderr)
        return 1
    try:
        event = json.loads(sys.stdin.read() or "{}")
        return pre(event) if mode == "pre" else post(event)
    except Exception as exc:  # a hook bug must never block work
        print(f"qa_gate_hook error (non-blocking): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
