"""The QA gate hook blocks dashes and invented leak names in client deliverables, and nothing else."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "scripts" / "qa_gate_hook.py"
PROTECTED = "C:\\work\\Clients\\Acme\\Full SEO Audit\\report.md"
OUTSIDE = "C:\\work\\Clients\\Acme\\data\\export.csv"
EM = "\u2014"
needs_index = pytest.mark.skipif(not (ROOT / "Skills" / "google-leak-reference" / "data" / "leak.sqlite").exists(),
                                 reason="leak index not built")


def call(mode: str, event: dict | str, env: dict | None = None):
    payload = event if isinstance(event, str) else json.dumps(event)
    return subprocess.run([sys.executable, str(HOOK), mode], input=payload, capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, **(env or {})})


def write(path: str, content: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": path, "content": content}}


def test_blocks_em_dash_in_a_deliverable():
    r = call("pre", write(PROTECTED, f"Fix the title {EM} it is too long.\n"))
    assert r.returncode == 2 and "CHECK 12" in r.stderr


def test_allows_clean_text_in_a_deliverable():
    assert call("pre", write(PROTECTED, "Fix the title, it is too long.\n")).returncode == 0


def test_ignores_files_outside_full_seo_audit():
    assert call("pre", write(OUTSIDE, f"raw {EM} export\n")).returncode == 0


def test_ignores_non_text_suffix():
    assert call("pre", write(PROTECTED.replace(".md", ".json"), f"{EM}")).returncode == 0


def test_edit_checks_only_the_new_text():
    old_dash = {"tool_name": "Edit", "tool_input": {"file_path": PROTECTED, "old_string": f"a {EM} b",
                                                    "new_string": "a, b"}}
    assert call("pre", old_dash).returncode == 0
    new_dash = {"tool_name": "Edit", "tool_input": {"file_path": PROTECTED, "old_string": "a, b",
                                                    "new_string": f"a {EM} b"}}
    assert call("pre", new_dash).returncode == 2


@needs_index
def test_blocks_invented_leak_attribute():
    r = call("pre", write(PROTECTED, "Per the leak, `trustedAnchors` weights links by seed distance.\n"))
    assert r.returncode == 2 and "CHECK 14" in r.stderr and "trustedAnchors" in r.stderr


@needs_index
def test_allows_real_leak_attribute():
    r = call("pre", write(PROTECTED, "Per the leak, `siteFocusScore` is documented as topical focus.\n"))
    assert r.returncode == 0, r.stderr


def test_malformed_input_is_non_blocking():
    assert call("pre", "not json").returncode == 1


def test_post_flags_a_fresh_workbook_with_a_dash(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    folder = tmp_path / "Acme" / "Full SEO Audit"
    folder.mkdir(parents=True)
    wb = openpyxl.Workbook()
    wb.active["A1"] = f"Slow page {EM} fix it"
    wb.save(folder / "audit.xlsx")
    r = call("post", {"tool_name": "Bash"}, env={"QA_GATE_CLIENTS_DIR": str(tmp_path)})
    assert r.returncode == 2 and "audit.xlsx" in r.stderr


def test_post_passes_a_clean_workbook(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    folder = tmp_path / "Acme" / "Full SEO Audit"
    folder.mkdir(parents=True)
    wb = openpyxl.Workbook()
    wb.active["A1"] = "Slow page, fix it"
    wb.save(folder / "audit.xlsx")
    assert call("post", {"tool_name": "Bash"}, env={"QA_GATE_CLIENTS_DIR": str(tmp_path)}).returncode == 0
