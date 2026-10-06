"""Pure-function checks for the October 2026 framework changes (1.5 / 1.8).

No network, no sheet access: sheets_io is mocked wherever a function would read.
"""

import datetime as dt
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import fill_1_5_section_a as sec_a  # noqa: E402
import fill_1_8 as f18  # noqa: E402
import prior_work as pw  # noqa: E402


# ---- prior_work -----------------------------------------------------------

@pytest.mark.parametrize("cell,want", [
    ("1. electrical services (534 impr, pos 10.3); electrical repair (185)",
     "electrical services"),
    ("TARGETS\n• furnace installation bountiful - 185 impr, pos 19.6\n• x - 3 impr",
     "furnace installation bountiful"),
    ("", ""),
    ("water heater repair (family); tankless AI prompts: how do i", "water heater repair"),
])
def test_first_target(cell, want):
    assert pw._first_target(cell) == want


def test_canon_ignores_trailing_slash():
    assert pw.canon("https://a.com/x/ ") == pw.canon("https://a.com/x")


def test_previous_workbook_picks_last_calendar_month():
    cfg = {"sheet_id": "oct", "sheet_id_2026_09": "sep", "sheet_id_2026_08": "aug"}
    assert pw.previous_workbook(cfg, dt.date(2026, 10, 5)) == ("sheet_id_2026_09", "sep")
    assert pw.previous_workbook(cfg, dt.date(2026, 9, 20)) == ("sheet_id_2026_08", "aug")


def test_previous_workbook_falls_back_to_newest_prior():
    cfg = {"sheet_id": "x", "sheet_id_2026_08": "aug"}
    assert pw.previous_workbook(cfg, dt.date(2026, 11, 3)) == ("sheet_id_2026_08", "aug")
    assert pw.previous_workbook({}, dt.date(2026, 11, 3)) == (None, None)


def test_prior_ids_newest_first_and_capped():
    cfg = {"sheet_id_2026_07": "a", "sheet_id_2026_09": "c", "sheet_id_2026_08": "b",
           "sheet_id_2026_06": "z"}
    assert pw.prior_ids(cfg, 3) == [("sheet_id_2026_09", "c"), ("sheet_id_2026_08", "b"),
                                    ("sheet_id_2026_07", "a")]


def test_new_layout_reads_pages_rows_only():
    rows = [["Refresh", "A", "https://x.com/a/", "TARGETS\n• q one - 5 impr", "", "kw"],
            ["Quick Win", "B", "https://x.com/b/", "MISSING\n• q two - 9 impr"],
            ["", "", ""]]
    with mock.patch.object(pw.S, "find_rows", return_value={"hdr": 5, "sec2": 18}), \
            mock.patch.object(pw.S, "read", return_value=rows):
        got = pw._new_layout("sid", "2.3 Page Optimizations")
    assert [(d["kind"], d["page"], d["query"]) for d in got] == [
        ("Refresh", "https://x.com/a/", "q one"),
        ("Quick Win", "https://x.com/b/", "q two")]


def test_layout_detection():
    assert pw.layout("s", ["1.1 Data Snapshot", "2.3 Page Optimizations"]) == "new"
    assert pw.layout("s", ["1.1 Data Snapshot", "2.3-3.1 Refresh Log"]) == "old"


# ---- 1.5 section A windows ------------------------------------------------

def test_windows_for_october_measure_september_against_august():
    sec_a.set_windows(dt.date(2026, 10, 1))
    w = sec_a.WIN
    assert w["before"] == (dt.date(2026, 8, 1), dt.date(2026, 8, 31))
    assert w["after"] == (dt.date(2026, 9, 1), dt.date(2026, 9, 30))
    assert w["resolve"] == (dt.date(2026, 6, 1), dt.date(2026, 9, 30))
    assert (w["before_name"], w["after_name"], w["year"]) == ("August", "September", 2026)


def test_windows_cross_a_year_boundary():
    sec_a.set_windows(dt.date(2027, 1, 1))
    w = sec_a.WIN
    assert w["before"] == (dt.date(2026, 11, 1), dt.date(2026, 11, 30))
    assert w["after"] == (dt.date(2026, 12, 1), dt.date(2026, 12, 31))
    assert w["year"] == 2026


# ---- 1.8 fill -------------------------------------------------------------

def test_page_label_from_slug():
    assert f18.page_label("https://x.com/service-areas/asphalt-paving-ann-arbor/") == \
        "Asphalt Paving Ann Arbor"
    assert f18.page_label("https://x.com/") == "Homepage"


def test_scan_row_cells_formats_missing_queries_and_selection():
    row = {"url": "https://x.com/a/", "gap_impr": 410, "excluded": "",
           "top": [{"q": "q one", "pos": 9.24, "impr": 300},
                   {"q": "q two", "pos": 14.8, "impr": 110}]}
    cells = f18.scan_row_cells(row, True)
    assert cells[0] == "https://x.com/a/"
    assert cells[1].startswith("MISSING QUERIES\n• q one - 300 impr, pos 9.2")
    assert cells[2] == "9.2-14.8"
    assert cells[3] == 410 and cells[5] == "Y"
    assert f18.scan_row_cells(row, False)[5] == "N"


def test_build_pages_orders_refresh_before_quick_win_and_checks_cell_limits():
    plan = {"targets": [{"url": "https://x.com/r/", "queries": "TARGETS\n• q - 5 impr",
                         "pos": "CURRENT STATE\n• pos 12", "ai": "• absent",
                         "angle": "Add a cost section."}],
            "quick_wins": [{"url": "https://x.com/q/"}]}
    scan = {"https://x.com/q": {"title": "T", "top": [{"q": "mq", "pos": 8.0, "impr": 70}]}}
    totals = {"/r": {"clicks": 3, "imp": 100}}
    rows = f18.build_pages(plan, scan, totals, "Jul-Sep")
    assert [r[0] for r in rows] == ["Refresh", "Quick Win"]
    assert "3 clicks / 100 impressions (GSC Jul-Sep)" in rows[0][4]
    assert "no GSC rows Jul-Sep" in rows[1][4]
    assert "CURRENT TITLE\n• T" in rows[1][4]


def test_build_pages_refuses_an_overlong_cell():
    plan = {"targets": [{"url": "https://x.com/r/", "queries": "x" * 1200, "pos": "p",
                         "ai": "a", "angle": "b"}]}
    with pytest.raises(Exception):
        f18.build_pages(plan, {}, {}, "Jul-Sep")


# ---- 1.8: landing URLs only -----------------------------------------------

class _Resp:
    def __init__(self, status, url):
        self.status_code, self.url = status, url

    def close(self):
        pass


def test_resolve_page_returns_the_landing_url_for_a_slash_redirect():
    with mock.patch.object(f18.requests, "get",
                           return_value=_Resp(200, "https://x.com/blog/a/")):
        final, note = f18.resolve_page("https://x.com/blog/a")
    assert final == "https://x.com/blog/a/" and note.startswith("resolved to")


def test_resolve_page_is_silent_when_nothing_moved():
    with mock.patch.object(f18.requests, "get",
                           return_value=_Resp(200, "https://x.com/blog/a/")):
        assert f18.resolve_page("https://x.com/blog/a/") == ("https://x.com/blog/a/", "")


def test_resolve_page_flags_dead_pages_and_never_calls_a_failure_clean():
    with mock.patch.object(f18.requests, "get", return_value=_Resp(404, "https://x.com/a")):
        assert f18.resolve_page("https://x.com/a")[1].startswith("DEAD")
    with mock.patch.object(f18.requests, "get", return_value=_Resp(403, "https://x.com/a")):
        assert "not verified" in f18.resolve_page("https://x.com/a")[1]
    with mock.patch.object(f18.requests, "get", side_effect=OSError("boom")):
        assert "not verified" in f18.resolve_page("https://x.com/a")[1]


# ---- 1.8: the lock-time cooldown guardrail --------------------------------

def test_guard_blocks_a_page_worked_inside_the_window():
    seen = {"x.com/a": ["2026_09 2.3-3.1 Refresh Log r5"]}
    with pytest.raises(SystemExit) as e:
        f18.guard_cooldown("c", ["https://x.com/a/", "https://x.com/b/"], set(), seen)
    assert "COOLDOWN VIOLATION" in str(e.value) and "https://x.com/a/" in str(e.value)


def test_guard_lets_a_clear_page_through_and_honours_an_explicit_override(capsys):
    seen = {"x.com/a": ["2026_09 2.3-3.1 Refresh Log r5"]}
    f18.guard_cooldown("c", ["https://x.com/b/"], set(), seen)
    f18.guard_cooldown("c", ["https://x.com/a/"], {"https://x.com/a"}, seen)
    assert "cooldown override" in capsys.readouterr().out


def test_guard_refuses_the_same_url_twice_in_one_plan():
    with pytest.raises(SystemExit) as e:
        f18.guard_cooldown("c", ["https://x.com/a/", "https://x.com/a"], set(), {})
    assert "twice" in str(e.value)


def test_every_gate_reads_one_window_constant():
    import gate_1_7_worked_pages as g17
    import run_1_5 as r15
    import url_cooldown as uc
    # 1.7, 1.8 and 2.3 read ONE window, so those gates cannot disagree.
    assert g17.COOLDOWN_MONTHS == uc.COOLDOWN_MONTHS
    # 1.5 has its own, longer lookback (owner instruction 2026-10-06). It may be stricter than the
    # shared window and must never be looser: a page the cooldown blocks may not reach 1.8 via 1.5.
    assert r15.LOOKBACK_WORKBOOKS == uc.CANDIDATE_LOOKBACK_MONTHS >= uc.COOLDOWN_MONTHS
