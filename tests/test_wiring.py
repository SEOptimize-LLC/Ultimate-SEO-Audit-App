"""Wiring contracts: the cross-file promises that used to break silently.

Found by the October 2026 workflow review: seven registered skills had drifted from the library by 100 to
400 lines, the QA check count in CLAUDE.md was stale twice, two workflows were reachable from nowhere, and
the QA gate had no enforcer. Each test below turns one of those into a check.
"""

import glob
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
QA_SKILL = ROOT / "Skills" / "data-analysis" / "pre-delivery-qa" / "SKILL.md"
PATH_RE = re.compile(r"(?<![\w/.-])((?:scripts|auditors|services|utils|prompts|fetchers|Skills|templates|\.claude)"
                     r"/[\w./-]+\.(?:py|md|json|yaml|yml|csv))")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def test_registered_skills_are_pointers_in_sync_with_the_library():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "sync_registered_skills.py"), "--check"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout + r.stderr


def test_documented_paths_exist():
    sources = (glob.glob(str(ROOT / ".claude" / "commands" / "*.md")) + glob.glob(str(ROOT / ".claude" / "agents" / "*.md"))
               + [str(CLAUDE_MD), str(QA_SKILL)])
    missing = {}
    for src in sources:
        for ref in set(PATH_RE.findall(read(Path(src)))):
            ref = ref.rstrip(".,;:)")
            if any(c in ref for c in "<{*"):
                continue
            if not (ROOT / ref).exists():
                missing.setdefault(ref, []).append(Path(src).name)
    assert not missing, missing


def test_claude_md_check_count_matches_the_qa_skill():
    headings = len(re.findall(r"(?m)^### CHECK \d+", read(QA_SKILL)))
    claimed = {int(n) for n in re.findall(r"(\d+)-check", read(CLAUDE_MD))}
    assert claimed == {headings}, f"CLAUDE.md says {claimed}, the QA skill has {headings} checks"


def test_every_skills_folder_is_reachable():
    """A folder under Skills/ must be a registered skill, or be named by path in CLAUDE.md or a command."""
    registered = {p.parent.name for p in (ROOT / ".claude" / "skills").glob("*/SKILL.md")}
    routes = read(CLAUDE_MD) + "".join(read(Path(p)) for p in glob.glob(str(ROOT / ".claude" / "commands" / "*.md")))
    orphans = [d.name for d in (ROOT / "Skills").iterdir()
               if d.is_dir() and not d.name.startswith(("_", ".")) and d.name not in registered
               and f"Skills/{d.name}" not in routes]
    assert not orphans, f"not registered and not named in CLAUDE.md or a command: {orphans}"


def test_qa_gate_hooks_are_registered_and_the_script_exists():
    settings = json.loads(read(ROOT / ".claude" / "settings.json"))
    pre = settings["hooks"]["PreToolUse"][0]
    post = settings["hooks"]["PostToolUse"][0]
    assert pre["matcher"] == "Write|Edit" and "qa_gate_hook.py" in pre["hooks"][0]["command"]
    assert post["matcher"] == "Bash" and "qa_gate_hook.py" in post["hooks"][0]["command"]
    assert (ROOT / "scripts" / "qa_gate_hook.py").exists()


def test_workflow_suppression_files_are_identical():
    """The engine reads known-intentional.yaml from whichever root it scans, so both copies must match."""
    a = read(ROOT / ".workflow-review" / "known-intentional.yaml")
    b = read(ROOT / ".claude" / ".workflow-review" / "known-intentional.yaml")
    assert a == b
