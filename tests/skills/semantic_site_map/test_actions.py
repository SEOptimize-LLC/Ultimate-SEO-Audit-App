"""Tests for the Keep/Grow/Relocate/Prune classifier."""

from Skills.semantic_site_map.report import classify_pages_by_action


def test_high_clicks_high_value_is_keep():
    urls = ["https://x.com/a", "https://x.com/b", "https://x.com/c"]
    clicks = {"https://x.com/a": 100, "https://x.com/b": 10, "https://x.com/c": 5}
    value = {"https://x.com/a": 80, "https://x.com/b": 20, "https://x.com/c": 15}
    out = classify_pages_by_action(urls, clicks, value)
    assert out["https://x.com/a"] == "keep"


def test_low_clicks_high_value_is_grow():
    urls = ["https://x.com/a", "https://x.com/b", "https://x.com/c"]
    clicks = {"https://x.com/a": 1, "https://x.com/b": 50, "https://x.com/c": 100}
    value = {"https://x.com/a": 90, "https://x.com/b": 30, "https://x.com/c": 20}
    out = classify_pages_by_action(urls, clicks, value)
    assert out["https://x.com/a"] == "grow"


def test_high_clicks_low_value_is_relocate():
    urls = ["https://x.com/a", "https://x.com/b", "https://x.com/c"]
    clicks = {"https://x.com/a": 200, "https://x.com/b": 10, "https://x.com/c": 5}
    value = {"https://x.com/a": 5, "https://x.com/b": 60, "https://x.com/c": 70}
    out = classify_pages_by_action(urls, clicks, value)
    assert out["https://x.com/a"] == "relocate"


def test_low_clicks_low_value_is_prune():
    urls = ["https://x.com/a", "https://x.com/b", "https://x.com/c"]
    clicks = {"https://x.com/a": 1, "https://x.com/b": 50, "https://x.com/c": 100}
    value = {"https://x.com/a": 5, "https://x.com/b": 60, "https://x.com/c": 70}
    out = classify_pages_by_action(urls, clicks, value)
    assert out["https://x.com/a"] == "prune"


def test_url_missing_from_clicks_treated_as_zero():
    """A page with no GSC entry is treated as 0 clicks (low side)."""
    urls = ["https://x.com/a", "https://x.com/b", "https://x.com/c"]
    clicks = {"https://x.com/b": 50, "https://x.com/c": 100}  # a missing
    value = {"https://x.com/a": 90, "https://x.com/b": 30, "https://x.com/c": 20}
    out = classify_pages_by_action(urls, clicks, value)
    # a has 0 clicks (low) + high value -> grow
    assert out["https://x.com/a"] == "grow"


def test_url_missing_from_value_treated_as_zero():
    """A page with no derived value is treated as 0 (low side)."""
    urls = ["https://x.com/a", "https://x.com/b", "https://x.com/c"]
    clicks = {"https://x.com/a": 1, "https://x.com/b": 50, "https://x.com/c": 100}
    value = {"https://x.com/b": 60, "https://x.com/c": 70}  # a missing
    out = classify_pages_by_action(urls, clicks, value)
    # a has 1 click (low) + 0 value (low) -> prune
    assert out["https://x.com/a"] == "prune"


def test_every_url_gets_classified():
    """Output must include every input URL."""
    urls = [f"https://x.com/{i}" for i in range(10)]
    clicks = {u: i * 10 for i, u in enumerate(urls)}
    value = {u: 50 + i for i, u in enumerate(urls)}
    out = classify_pages_by_action(urls, clicks, value)
    assert set(out.keys()) == set(urls)
    for action in out.values():
        assert action in {"keep", "grow", "relocate", "prune"}


def test_zero_median_does_not_collapse_to_one_side():
    """When most clicks tie at 0, ties should split roughly 50/50.

    Regression: a previous version used strict `clicks > median`, which
    meant that with most URLs at 0 clicks (median=0), every zero-click
    URL fell to the 'low clicks' side and the 2x2 collapsed to grow/prune.
    """
    urls = [f"https://x.com/{i}" for i in range(10)]
    # 8 URLs have 0 clicks, 2 have some clicks. Median = 0.
    clicks = {urls[0]: 50, urls[1]: 10}
    # Values evenly split high/low.
    value = {u: (90 if i < 5 else 10) for i, u in enumerate(urls)}
    out = classify_pages_by_action(urls, clicks, value)
    n_keep_or_relocate = sum(
        1 for a in out.values() if a in ("keep", "relocate")
    )
    # Should be roughly half (5) on the high-clicks side, not zero.
    assert n_keep_or_relocate >= 3


def test_median_split_threshold_on_boundary():
    """Ties on the median boundary route deterministically."""
    # 4 URLs, sorted clicks: [10, 20, 30, 40], median = 25
    # sorted value: [10, 20, 30, 40], median = 25
    urls = [f"https://x.com/{i}" for i in range(4)]
    clicks = {urls[0]: 10, urls[1]: 20, urls[2]: 30, urls[3]: 40}
    value = {urls[0]: 40, urls[1]: 30, urls[2]: 20, urls[3]: 10}
    out = classify_pages_by_action(urls, clicks, value)
    # The function should produce deterministic, non-empty quadrants.
    assert len(set(out.values())) >= 2
