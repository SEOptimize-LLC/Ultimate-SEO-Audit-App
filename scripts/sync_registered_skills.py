#!/usr/bin/env python
"""Keep the registered skills in .claude/skills/ as thin pointers to the maintained library in Skills/.

Claude Code auto-loads project skills only from .claude/skills/. The maintained knowledge base lives
in Skills/. Two full copies drift (seven did, by 100 to 400 lines each), so each registered entry is a
pointer: the frontmatter the model matches on, plus an instruction to read the library file.

    python scripts/sync_registered_skills.py            # create or refresh pointers
    python scripts/sync_registered_skills.py --check    # exit 1 if any pointer is missing or drifted

What it owns
    * name and description in each pointer's frontmatter, copied from the library SKILL.md so the
      trigger text cannot diverge.
    * a new pointer body, written only when the registered file is missing or is not yet a pointer.
      An existing pointer body (for example the hand-written ai-search-optimization one) is kept.
    * removal of everything else in a pointer's registered folder (stale copies of references/).

What it leaves alone
    google-leak-reference is registered-only: its SKILL.md lives in .claude/skills/ and its data and
    scripts live in Skills/google-leak-reference/.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "Skills"
REGISTERED = ROOT / ".claude" / "skills"
MARKER = "This entry point is a pointer."
POINTER_SKILLS = [
    "ai-search-optimization",
    "backlink-agent",
    "competitor-agent",
    "onpage-seo-agent",
    "seo-audit-methodology",
    "technical-seo-agent",
    "traffic-loss-analysis",
]
FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def frontmatter(text: str) -> dict[str, str]:
    m = FRONT_RE.match(text.replace("\r\n", "\n"))
    out: dict[str, str] = {}
    if m:
        for line in m.group(1).splitlines():
            k, sep, v = line.partition(":")
            if sep and k.strip() in {"name", "description"}:
                out[k.strip()] = v.strip()
    return out


def reference_lines(skill: str) -> list[str]:
    refs = sorted((LIBRARY / skill / "references").glob("*.md")) if (LIBRARY / skill / "references").is_dir() else []
    lines = []
    for p in refs:
        h1 = next((ln[2:].strip() for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()
                   if ln.startswith("# ")), p.stem)
        lines.append(f"- `Skills/{skill}/references/{p.name}`: {h1}")
    return lines


def new_pointer(skill: str, fm: dict[str, str]) -> str:
    title = fm["name"].strip('"')
    body = [
        "---",
        f"name: {fm['name']}",
        f"description: {fm['description']}",
        "---",
        "",
        f"# {title}",
        "",
        f"**{MARKER}** The canonical, maintained knowledge base for this skill lives at "
        f"`Skills/{skill}/SKILL.md` in the project root.",
        "",
        f"**Action: Read `Skills/{skill}/SKILL.md` in full and follow it.** Do not rely on any content "
        "formerly in this file; it was an older snapshot and was consolidated to a pointer on 2026-10-05 "
        "to stop the two copies from drifting.",
    ]
    refs = reference_lines(skill)
    if refs:
        body += ["", "Reference files in the library:"] + refs
    return "\n".join(body) + "\n"


def refresh_frontmatter(text: str, fm: dict[str, str]) -> str:
    nl = "\r\n" if "\r\n" in text else "\n"
    t = text.replace("\r\n", "\n")
    m = FRONT_RE.match(t)
    head = f"---\nname: {fm['name']}\ndescription: {fm['description']}\n---\n"
    out = head + (t[m.end():] if m else t)
    return out.replace("\n", nl)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report drift, change nothing")
    args = ap.parse_args()
    problems: list[str] = []
    for skill in POINTER_SKILLS:
        lib = LIBRARY / skill / "SKILL.md"
        reg = REGISTERED / skill / "SKILL.md"
        if not lib.exists():
            problems.append(f"{skill}: library SKILL.md missing")
            continue
        fm = frontmatter(lib.read_text(encoding="utf-8"))
        if "name" not in fm or "description" not in fm:
            problems.append(f"{skill}: library frontmatter lacks name or description")
            continue
        text = reg.read_text(encoding="utf-8") if reg.exists() else ""
        is_pointer = MARKER in text
        reg_fm = frontmatter(text) if text else {}
        extras = [p for p in (REGISTERED / skill).glob("*") if p.name != "SKILL.md"] if reg.exists() else []
        drift = []
        if not is_pointer:
            drift.append("not a pointer")
        if reg_fm.get("description") != fm["description"] or reg_fm.get("name") != fm["name"]:
            drift.append("frontmatter differs from the library")
        if extras:
            drift.append("stale files: " + ", ".join(p.name for p in extras))
        if args.check:
            if drift:
                problems.append(f"{skill}: " + "; ".join(drift))
            continue
        if not drift:
            continue
        reg.parent.mkdir(parents=True, exist_ok=True)
        reg.write_text(new_pointer(skill, fm) if not is_pointer else refresh_frontmatter(text, fm),
                       encoding="utf-8", newline="")
        for p in extras:
            shutil.rmtree(p) if p.is_dir() else p.unlink()
        print(f"synced {skill}: {'; '.join(drift)}")
    for p in problems:
        print("DRIFT" if args.check else "ERROR", p)
    if args.check and not problems:
        print(f"{len(POINTER_SKILLS)} registered skills are pointers in sync with the library")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
