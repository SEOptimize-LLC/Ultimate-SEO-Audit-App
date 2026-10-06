"""Tests for Skills/google-leak-reference (the folder name has a hyphen, so modules load by path)."""

import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent / "Skills" / "google-leak-reference"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SAMPLE = '''defmodule GoogleApi.ContentWarehouse.V1.Model.DemoSignals do
  @moduledoc """
  A demo message.

  ## Attributes

  *   `goodThing` (*type:* `integer()`, *default:* `nil`) - First line
      continued on a second line.
  *   `child` (*type:* `GoogleApi.ContentWarehouse.V1.Model.OtherThing.t`, *default:* `nil`) -
  """
end
'''


def test_parse_module_reads_attributes_and_continuations():
    build_index = _load("build_index")
    module, doc, attrs = build_index.parse_module(SAMPLE)
    assert module == "GoogleApi.ContentWarehouse.V1.Model.DemoSignals"
    assert doc == "A demo message."
    assert attrs[0] == ("goodThing", "integer()", "nil", "First line continued on a second line.")
    assert attrs[1][0] == "child" and attrs[1][3] == ""


def test_parse_module_without_attributes_section():
    build_index = _load("build_index")
    text = 'defmodule GoogleApi.ContentWarehouse.V1.Model.Empty do\n  @moduledoc """\n  Nothing here.\n  """\nend\n'
    module, doc, attrs = build_index.parse_module(text)
    assert module.endswith("Empty") and doc == "Nothing here." and attrs == []


def test_name_level_distinguishes_exact_substring_mention_absent():
    bc = _load("build_commentary")
    exact = {"siteradius", "ugcdiscussioneffortscore"}
    joined = " ".join(sorted(exact))
    text = "used in the freshnesstwiddler to rank things"
    assert bc.name_level("siteRadius", exact, joined, text) == "exact"
    assert bc.name_level("effortScore", exact, joined, text) == "substring"
    assert bc.name_level("FreshnessTwiddler", exact, joined, text) == "mention"
    assert bc.name_level("pageQualityScore", exact, joined, text) == "absent"


@pytest.mark.skipif(not (ROOT / "data" / "leak.sqlite").exists(), reason="index not built")
def test_every_model_module_has_one_summary_and_valid_grade():
    db = sqlite3.connect(ROOT / "data" / "leak.sqlite")
    prefix = "GoogleApi.ContentWarehouse.V1.Model."
    modules = {r[0].replace(prefix, "") for r in db.execute(
        "SELECT module FROM modules WHERE version='0.4.0' AND module LIKE '%.Model.%'")}
    rows = db.execute("SELECT module, seo FROM summaries").fetchall()
    assert {r[0] for r in rows} == modules
    assert len(rows) == len(modules)
    assert {r[1] for r in rows} <= {"none", "low", "medium", "high"}


@pytest.mark.skipif(not (ROOT / "data" / "leak.sqlite").exists(), reason="index not built")
def test_framework_citations_match_the_primary_source():
    """The corrected identifiers exist; the ones the audit removed must not come back."""
    db = sqlite3.connect(ROOT / "data" / "leak.sqlite")
    names = {r[0] for r in db.execute("SELECT module FROM modules WHERE version='0.4.0'")}
    short = {n.replace("GoogleApi.ContentWarehouse.V1.Model.", "") for n in names}
    assert "QualityAuthorityTopicEmbeddingsVersionedItem" in short
    assert "QualityNavboostCrapsCrapsClickSignals" in short
    assert "QualityAuthorityTopicEmbeddings" not in short
    assert "QualityNavboostCrapsCrapsUrlSignals" not in short
    attrs = {r[0] for r in db.execute("SELECT DISTINCT attr FROM attributes WHERE version='0.4.0'")}
    assert "trustedAnchors" not in attrs


def test_claims_file_rows_are_well_formed():
    path = ROOT / "commentary" / "claims.jsonl"
    if not path.exists():
        pytest.skip("claims not built")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    for r in rows:
        assert r["call"] in {"KEEP", "KEEP-WITH-CAVEAT", "DISCARD"}
        assert r["name_check"] in {"verified", "related", "partial", "not_found", "none_cited"}


# ---- check_leak_citations.py -------------------------------------------------

BAD_DRAFT = (
    "Per the Content Warehouse leak, the `QualityAuthorityTopicEmbeddings` module computes `siteFocusScore`.\n"
    "The leak documents a `trustedAnchors` concept, and `siteEmbeddings` stores the site vector.\n"
)
GOOD_DRAFT = (
    "Per the leak, `QualityAuthorityTopicEmbeddingsVersionedItem` documents `siteFocusScore` "
    "(documented: \"how much a site is focused on one topic\").\n"
)


def _run_check(monkeypatch, capsys, tmp_path, text, db_path=None):
    check = _load("check_leak_citations")
    if db_path is not None:
        monkeypatch.setattr(check, "DB_PATH", db_path)
    draft = tmp_path / "draft.md"
    draft.write_text(text, encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["check_leak_citations.py", str(draft)])
    code = check.main()
    return code, capsys.readouterr()


needs_index = pytest.mark.skipif(not (ROOT / "data" / "leak.sqlite").exists(), reason="index not built")


@needs_index
def test_check_blocks_wrong_module_and_invented_attribute(monkeypatch, capsys, tmp_path):
    code, out = _run_check(monkeypatch, capsys, tmp_path, BAD_DRAFT)
    assert code == 1
    for name in ("QualityAuthorityTopicEmbeddings", "trustedAnchors", "siteEmbeddings"):
        assert f"FAIL  {name}" in out.out


@needs_index
def test_check_passes_correct_citations(monkeypatch, capsys, tmp_path):
    code, out = _run_check(monkeypatch, capsys, tmp_path, GOOD_DRAFT)
    assert code == 0 and "FAIL" not in out.out


@needs_index
def test_check_is_a_noop_when_no_leak_identifiers(monkeypatch, capsys, tmp_path):
    code, out = _run_check(monkeypatch, capsys, tmp_path, "A short note about title tags and meta descriptions.\n")
    assert code == 0 and "nothing to check" in out.out


@needs_index
def test_check_warns_on_unsourced_window(monkeypatch, capsys, tmp_path):
    code, out = _run_check(monkeypatch, capsys, tmp_path, "The leak shows a 13-month window for clicks.\n")
    assert code == 0 and "13-month" in out.out


def test_check_exits_2_when_index_missing(monkeypatch, capsys, tmp_path):
    code, out = _run_check(monkeypatch, capsys, tmp_path, BAD_DRAFT, db_path=tmp_path / "nope.sqlite")
    assert code == 2 and "index missing" in out.err
