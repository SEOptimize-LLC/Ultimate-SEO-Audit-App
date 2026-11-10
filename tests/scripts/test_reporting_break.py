"""reporting_break.py: Google's May 13, 2025 - April 27, 2026 impressions logging error. No network."""
from __future__ import annotations

import datetime as dt

import reporting_break as RB


def test_every_property_is_affected():
    assert RB.has_break(None, "https://any.example/")


def test_only_windows_starting_before_april_27_2026_are_affected():
    assert RB.affects(dt.date(2025, 8, 1))
    assert RB.affects(dt.date(2026, 4, 26))
    assert not RB.affects(dt.date(2026, 4, 27))
    assert not RB.affects(dt.date(2026, 5, 1))


def test_reference_quarter_is_clean():
    assert RB.POST[0] >= RB.CLEAN_FROM and RB.POST_LABEL == "May-Jul 2026"
