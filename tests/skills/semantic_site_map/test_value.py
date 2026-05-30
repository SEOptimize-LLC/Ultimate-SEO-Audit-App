"""Tests for the business-value derivation module."""

import pandas as pd
import pytest

from Skills.semantic_site_map.value import (
    COMMERCIAL_INTENT_TERMS,
    derive_business_value,
    score_url_pattern,
)


def test_score_url_pattern_high_value_paths():
    assert score_url_pattern("https://x.com/services/repair") >= 50
    assert score_url_pattern("https://x.com/pricing") >= 50
    assert score_url_pattern("https://x.com/contact") >= 50
    assert score_url_pattern("https://x.com/demo") >= 50
    assert score_url_pattern("https://x.com/product/widget") >= 50


def test_score_url_pattern_medium_value_paths():
    score = score_url_pattern("https://x.com/blog/post-1")
    assert 20 <= score < 50
    assert 20 <= score_url_pattern("https://x.com/guides/topic") < 50
    assert 20 <= score_url_pattern("https://x.com/resources/x") < 50
    assert 20 <= score_url_pattern("https://x.com/learn/y") < 50


def test_score_url_pattern_low_value_paths():
    assert score_url_pattern("https://x.com/tag/foo") < 20
    assert score_url_pattern("https://x.com/author/jane") < 20
    assert score_url_pattern("https://x.com/privacy-policy") < 20
    assert score_url_pattern("https://x.com/terms") < 20


def test_score_url_pattern_root_and_unclassified():
    """Homepage and uncategorized pages get a neutral default."""
    root = score_url_pattern("https://x.com/")
    assert root >= 50  # homepage is high-value
    unclassified = score_url_pattern("https://x.com/some-random-page")
    assert 20 <= unclassified < 50


def test_commercial_intent_terms_includes_expected():
    """The commercial-intent vocabulary covers obvious buy-signals."""
    assert "buy" in COMMERCIAL_INTENT_TERMS
    assert "pricing" in COMMERCIAL_INTENT_TERMS
    assert "near me" in COMMERCIAL_INTENT_TERMS
    assert "best" in COMMERCIAL_INTENT_TERMS


def test_derive_business_value_url_pattern_only():
    """No GSC, no GA4 - URL-pattern score only."""
    urls = [
        "https://x.com/services/repair",
        "https://x.com/blog/post-1",
        "https://x.com/tag/foo",
    ]
    scores = derive_business_value(urls, gsc_df=None, ga4_df=None)
    assert scores["https://x.com/services/repair"] >= 50
    assert 20 <= scores["https://x.com/blog/post-1"] < 50
    assert scores["https://x.com/tag/foo"] < 20


def test_derive_business_value_gsc_commercial_intent_boost():
    """Pages ranking for commercial queries get a boost."""
    urls = [
        "https://x.com/blog/buy-guide",
        "https://x.com/blog/educational-post",
    ]
    gsc_df = pd.DataFrame({
        "url": [
            "https://x.com/blog/buy-guide",
            "https://x.com/blog/buy-guide",
            "https://x.com/blog/educational-post",
        ],
        "query": [
            "buy widget online",
            "best widget pricing",
            "how does a widget work",
        ],
        "clicks": [10, 5, 20],
        "impressions": [100, 80, 200],
    })
    scores = derive_business_value(urls, gsc_df=gsc_df, ga4_df=None)
    # The commercial-intent page should score noticeably higher
    # than the educational one.
    assert (
        scores["https://x.com/blog/buy-guide"]
        > scores["https://x.com/blog/educational-post"]
    )


def test_derive_business_value_ga4_conversion_boost():
    """Pages with documented conversions get a boost."""
    urls = [
        "https://x.com/blog/post-with-conversions",
        "https://x.com/blog/post-no-conversions",
    ]
    ga4_df = pd.DataFrame({
        "url": [
            "https://x.com/blog/post-with-conversions",
            "https://x.com/blog/post-no-conversions",
        ],
        "conversions": [42, 0],
    })
    scores = derive_business_value(urls, gsc_df=None, ga4_df=ga4_df)
    assert (
        scores["https://x.com/blog/post-with-conversions"]
        > scores["https://x.com/blog/post-no-conversions"]
    )


def test_derive_business_value_scores_are_capped_at_100():
    """Even with every boost, scores must not exceed 100."""
    urls = ["https://x.com/services/repair"]
    gsc_df = pd.DataFrame({
        "url": ["https://x.com/services/repair"] * 3,
        "query": ["buy", "pricing", "best service near me"],
        "clicks": [50, 50, 50],
        "impressions": [500, 500, 500],
    })
    ga4_df = pd.DataFrame({
        "url": ["https://x.com/services/repair"],
        "conversions": [200],
    })
    scores = derive_business_value(urls, gsc_df=gsc_df, ga4_df=ga4_df)
    assert scores["https://x.com/services/repair"] <= 100


def test_derive_business_value_returns_value_per_input_url():
    """Every input URL gets a score, even if absent from GSC/GA4."""
    urls = [
        "https://x.com/services/a",
        "https://x.com/services/b",  # not in GSC/GA4
    ]
    gsc_df = pd.DataFrame({
        "url": ["https://x.com/services/a"],
        "query": ["buy"],
        "clicks": [10],
        "impressions": [100],
    })
    scores = derive_business_value(urls, gsc_df=gsc_df, ga4_df=None)
    assert set(scores.keys()) == set(urls)
