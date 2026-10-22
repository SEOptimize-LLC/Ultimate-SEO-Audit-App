"""tracker_reader.topic_lock: is AI share of voice on a topic open, or held by one brand?

Run from the project root:

    pytest tests/scripts/test_topic_lock.py -q

Pure function; no database.
"""

from __future__ import annotations

import tracker_reader as T


def test_one_brand_over_half_the_mentions_locks_the_topic():
    out = T.topic_lock(answered=30, mentions={"Acme": 3, "Rival": 12, "Third": 5}, client="Acme")
    assert out["label"] == "Locked"
    assert out["leader"] == "Rival"
    assert out["leader_share"] == 0.6
    assert out["client_share"] == 0.15


def test_exactly_half_is_still_open():
    assert T.topic_lock(answered=30, mentions={"Acme": 5, "Rival": 5}, client="Acme")["label"] == "Open"


def test_the_client_can_hold_the_lock():
    out = T.topic_lock(answered=30, mentions={"Acme": 9, "Rival": 3}, client="Acme")
    assert out["label"] == "Locked"
    assert out["leader"] == "Acme"


def test_too_few_answers_withholds_the_call():
    out = T.topic_lock(answered=T.TOPIC_MIN_SAMPLES - 1, mentions={"Rival": 10, "Acme": 4}, client="Acme")
    assert out["label"] == "Too few answers"
    assert out["client_share"] is None  # no share is quoted below the bar either


def test_a_handful_of_mentions_cannot_lock_a_topic():
    # 25 answers, two of which name the same rival: 100% share on almost nothing (python-reviewer, 2026-10-22).
    out = T.topic_lock(answered=25, mentions={"Rival": 2}, client="Acme")
    assert out["label"] == "Too few mentions"
    assert out["leader"] is None


def test_no_brand_named_is_its_own_finding():
    out = T.topic_lock(answered=40, mentions={}, client="Acme")
    assert out["label"] == "No brands named"
    assert out["leader"] is None


def test_the_bars():
    assert T.TOPIC_MIN_SAMPLES == 20
    assert T.TOPIC_MIN_MENTIONS == 10
    assert T.LOCK_SHARE == 0.5
