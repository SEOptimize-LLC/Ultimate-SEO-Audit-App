"""refresh_audit.py: pool arithmetic, buckets, gap matching and order. No network."""
from __future__ import annotations

import datetime as dt

import refresh_audit as R
from plan_1_8 import words


def pg(clicks, impr, pos):
    return {"clicks": clicks, "impressions": impr, "position": pos}


def test_year_ago_handles_month_ends():
    assert R.year_ago(dt.date(2026, 8, 1), dt.date(2026, 10, 31)) == (dt.date(2025, 8, 1), dt.date(2025, 10, 31))
    assert R.year_ago(dt.date(2024, 12, 1), dt.date(2025, 2, 28))[1] == dt.date(2024, 2, 29)


def test_months_back_counts_whole_months():
    assert R.months_back(dt.date(2026, 10, 31), 12) == dt.date(2025, 11, 1)
    assert R.months_back(dt.date(2026, 10, 31), 16) == dt.date(2025, 7, 1)


def test_comparison_prefers_year_ago():
    assert R.comparison(pg(1, 1, 1), pg(2, 2, 2), pg(3, 3, 3))[1].startswith("same 3 months")
    assert R.comparison(pg(1, 1, 1), pg(2, 2, 2), {})[1].startswith("previous 3 months")


def test_too_little_demand_is_out():
    assert R.diagnose(pg(0, 10, 9), pg(9, 50, 9), 99) == ("Out", "too little demand to judge (99 impressions in 12 months)")


def test_ranking_loss_is_recover_rank():
    assert R.diagnose(pg(40, 2000, 9.0), pg(100, 2100, 6.0), 9000)[0] == "Recover rank"


def test_demand_fall_is_out_not_a_rewrite():
    b, sig = R.diagnose(pg(40, 1000, 6.2), pg(100, 2500, 6.0), 9000)
    assert b == "Out" and sig.startswith("demand fall")


def test_held_position_and_impressions_is_win_the_answer():
    assert R.diagnose(pg(40, 2400, 6.1), pg(100, 2500, 6.0), 9000)[0] == "Win the answer"


def test_small_fall_is_holding():
    assert R.diagnose(pg(97, 2400, 6.1), pg(100, 2500, 6.0), 9000)[1].startswith("holding")
    assert R.diagnose(pg(1, 50, 6.1), pg(4, 50, 6.0), 900)[1].startswith("holding")   # under 5 clicks lost


def test_gap_prompts_need_absence_on_both_engines_and_shared_words():
    absent = {"text": "best water heater installer salt lake", "keyword": "water heater installation salt lake",
              "engines": {"chatgpt": {"answered": 5, "mentioned": 0}, "ai_mode": {"answered": 5, "mentioned": 0}}}
    present = {**absent, "text": "x", "keyword": "drain cleaning sandy", "engines": {"chatgpt": {"answered": 5, "mentioned": 2},
                                                  "ai_mode": {"answered": 5, "mentioned": 0}}}
    one_engine = {**absent, "text": "y", "keyword": "sewer repair ogden", "engines": {"chatgpt": {"answered": 5, "mentioned": 0}}}
    got = R.gap_prompts(["water heater installation cost"], [absent, present, one_engine], words)
    assert got == [absent["text"]]
    assert R.gap_prompts(["drain cleaning"], [absent], words) == []


def test_sort_puts_money_pages_and_leads_first_and_out_last():
    base = dict(leads_lost=0, clicks_lost=0, impr=0)
    rows = [
        {**base, "bucket": "Out", "value": "High (money page)", "clicks_lost": 999},
        {**base, "bucket": "Recover rank", "value": "Post: judge", "clicks_lost": 500},
        {**base, "bucket": "Win the answer", "value": "High (money page)", "leads_lost": 3},
        {**base, "bucket": "Earn citations", "value": "High (money page)", "impr": 50},
    ]
    order = [r["bucket"] for r in sorted(rows, key=R.sort_key)]
    assert order == ["Win the answer", "Earn citations", "Recover rank", "Out"]


def test_apply_review_marks_top_rows_and_the_rest():
    rows = [{"url": f"https://x.com/{i}", "bucket": "Recover rank", "value": "Post: judge"} for i in range(3)]
    rows.append({"url": "https://x.com/out", "bucket": "Out", "value": "Other: judge"})
    R.apply_review(rows, {"https://x.com/0": {"value": "Medium", "action": "content depth", "rationale": "A."}}, 2)
    assert [r["review"] for r in rows] == ["reviewed", "to review", "ranked, not reviewed", ""]
    assert rows[0]["value"] == "Medium"


def test_market_words_do_not_make_a_match():
    gaps = [{"text": t, "keyword": t, "engines": {"chatgpt": {"answered": 5, "mentioned": 0},
                                                  "ai_mode": {"answered": 5, "mentioned": 0}}}
            for t in ("best water softeners salt lake city", "commercial plumbing salt lake city weekends",
                      "drain cleaning salt lake city", "sewer line repair salt lake city")]
    assert R.gap_prompts(["tankless water heater salt lake city"], gaps, words) == []
    assert R.gap_prompts(["water softeners installation salt lake city"], gaps, words) == [gaps[0]["text"]]


def test_resolve_retries_429_then_reports_unconfirmed(monkeypatch):
    import urllib.error
    import urllib.request
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise urllib.error.HTTPError("u", 429, "Too Many", {}, None)
    monkeypatch.setattr(urllib.request, "urlopen", boom)
    st, why = R.resolve("https://x.com/a/", tries=3, sleep=lambda s: None)
    assert st is None and "429" in why and len(calls) == 3


def test_cause_comes_from_the_post_break_window_when_given():
    # year ago: impressions inflated by the old report; previous 3 months: comparable
    yoy, pri, cur = pg(100, 9000, 30.0), pg(60, 2400, 6.0), pg(40, 2400, 6.1)
    assert R.diagnose(cur, yoy, 9000)[1].startswith("demand fall")
    assert R.diagnose(cur, yoy, 9000, cause_base=pri)[0] == "Win the answer"


def test_plural_words_still_match():
    gaps = [{"text": "best water softeners salt lake city", "keyword": "best water softeners salt lake city",
             "engines": {"chatgpt": {"answered": 5, "mentioned": 0}, "ai_mode": {"answered": 5, "mentioned": 0}}}]
    assert R.gap_prompts(["water softener installation near me"], gaps, words) == [gaps[0]["text"]]


def test_only_confirmed_200_rows_reach_the_file():
    rows = [{"status": "200"}, {"status": "404"}, {"status": "not confirmed (HTTP 429 after 4 tries)"},
            {"status": "Search Console records https://x.com/a, which redirects here"}]
    keep, drop = R.deliverable_rows(rows)
    assert len(keep) == 2 and len(drop) == 2


def test_decline_before_the_clean_quarter_is_an_older_decline():
    yoy, clean, cur = pg(100, 9000, 30.0), pg(42, 2400, 12.0), pg(40, 2300, 12.2)
    b, sig = R.diagnose(cur, yoy, 9000, cause_base=clean)
    assert b == "Older decline" and "not readable" in sig
