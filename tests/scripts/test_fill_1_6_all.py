"""fill_1_6_all.py against the October 2026 template: preflight, B4:C6, slug list.

Run from the project root:

    pytest tests/scripts/test_fill_1_6_all.py -q

Mocked sheets_io throughout. Nothing is read from or written to Google Sheets.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import fill_1_6_all as F  # noqa: E402


class FakeSheets:
    def __init__(self, headers=None, anchors=None):
        self.headers = headers or {}
        self.anchors = anchors or {"sov": 4, "sov_prev": 5, "run": 6,
                                   "a_hdr": 9, "b": 36, "b_hdr": 37, "c": 45}
        self.writes = []

    def find_rows(self, sid, tab, prefixes, scan_to=80):
        self.last_prefixes = dict(prefixes)
        return dict(self.anchors)

    def check_layout(self, sid, a1, expected):
        row = int(a1.split("!A")[1].split(":")[0])
        found = self.headers.get(row, expected)

        class R:
            pass
        r = R()
        r.ok = list(found) == list(expected)
        r.expected, r.found = expected, found
        return r

    def write(self, *a, **k):          # pragma: no cover - must never run
        self.writes.append(a)
        raise AssertionError("preflight must not write")


def test_preflight_returns_anchors_and_checks_all_three_headers(monkeypatch):
    fake = FakeSheets()
    monkeypatch.setattr(F, "S", fake)
    a = F.preflight("sid")
    assert a["a_hdr"] == 9 and a["b_hdr"] == 37
    # Section C header is the row UNDER its banner.
    assert a["c_hdr"] == 46
    assert fake.last_prefixes["sov"] == "SOV this month"
    assert fake.writes == []


def test_preflight_refuses_the_september_three_column_b_header(monkeypatch):
    fake = FakeSheets(headers={
        37: ["Money Prompt", "Competitor Present", "Third-Party Page AI Cites"]})
    monkeypatch.setattr(F, "S", fake)
    with pytest.raises(RuntimeError, match="Nothing was written"):
        F.preflight("sid")


def test_preflight_refuses_a_stale_routed_header(monkeypatch):
    stale = list(F.HEADER_B[:4]) + ["Routed to 3.4 (Y)"]
    fake = FakeSheets(headers={37: stale})
    monkeypatch.setattr(F, "S", fake)
    with pytest.raises(RuntimeError, match=r"Routed to 3\.4"):
        F.preflight("sid")


def test_preflight_refuses_sections_out_of_order(monkeypatch):
    fake = FakeSheets(anchors={"sov": 4, "sov_prev": 5, "run": 6, "a_hdr": 9,
                               "b": 50, "b_hdr": 37, "c": 45})
    monkeypatch.setattr(F, "S", fake)
    with pytest.raises(RuntimeError, match="out of order"):
        F.preflight("sid")


def test_routed_header_names_task_3_3():
    assert F.HEADER_B[-1] == "Routed to 3.3 (Y)"
    assert F.HEADER_B[3] == "Opportunity / Next Step"


# ---------------------------------------------------------------- sov cells

def rows(prior=None, miss=""):
    return F.sov_summary(9, 46, ["chatgpt", "perplexity"], 23, 25.0, prior,
                         "mom text", 27, miss)


def test_value_cells_are_text_that_cannot_parse_as_numbers():
    this, last, run = rows(prior=("2026-09", 30.0, 60))
    assert this[0] == "20% (9 of 46)"
    assert last[0] == "30% (18 of 60)"
    assert run[0] == "27 of 27"
    for v in (this[0], last[0], run[0]):
        with pytest.raises(ValueError):
            float(v.replace(",", "").rstrip("%"))


def test_baseline_month_still_fills_b5_so_4_5_does_not_say_not_recorded():
    _, last, _ = rows(prior=None)
    assert last[0] == "baseline month"


def test_detail_goes_in_column_c_and_miss_note_is_stripped():
    this, last, run = rows(prior=("2026-09", 30.0, 60),
                           miss=" NOT RUN: gemini. That column is empty, not zero.")
    assert this[1].startswith("BASIS\n") and "9 of 46 checks" in this[1]   # label, then bullets
    assert last[1] == "CHANGE VS LAST MONTH\n• mom text"
    assert run[1] == "COVERAGE\n• NOT RUN: gemini.\n• That column is empty, not zero."
    assert "—" not in (this[1] + run[1])      # no em dash on a sheet


# -------------------------------------------------------------- slug list

def test_active_slugs_skips_inactive_and_clients_without_prompts(monkeypatch):
    monkeypatch.chdir(ROOT)
    reg = {"ihs_group": {"note": "not a client"},
           "beehive": {"sheet_id": "x"},
           "barts": {"sheet_id": "y"},
           "arsenal": {"active": False},              # no sheet_id
           "ghost": {"sheet_id": "z"},                # no prompt file
           "snow": {"active": False, "sheet_id_2026_09": "old"}}
    assert F.active_slugs(reg) == ["beehive", "barts"]


def test_barts_brand_matches_the_typographic_apostrophe():
    import fill_1_6_all as F
    assert F.brand_hit("barts", "Bart\u2019s Asphalt \u2014 Located at 915 E South St, Jackson, MI")
    assert F.brand_hit("barts", "Bart's Asphalt") and F.brand_hit("barts", "bartsasphalt.com")
    assert not F.brand_hit("barts", "Bartley Paving")
