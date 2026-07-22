"""Tests for the pure aggregation functions in fetch_ai_visibility:
compute_share_of_voice (client-vs-competitor citation SoV) and
aggregate_llm_probes (sampled multi-model mention-rate rollup).

These cover the network-free logic with mocked citation / probe data, so they
run without DataForSEO credentials.
"""

import pytest

from fetchers.fetch_ai_visibility import (
    aggregate_llm_probes,
    compute_share_of_voice,
)

CLIENT = "educationwalkthrough.com"
COMPETITORS = ["classroommosaic.com", "observe4success.com", "home.2gno.me"]


def _ai_row(keyword, present, citations):
    return {
        "keyword": keyword,
        "ai_overview_present": present,
        "ai_overview_citations": citations,
    }


@pytest.fixture()
def ai_results():
    return [
        _ai_row("classroom walkthrough", True, [
            "https://www.educationwalkthrough.com/features",
            "https://classroommosaic.com/blog/post",
            "https://en.wikipedia.org/wiki/Walkthrough",
        ]),
        _ai_row("teacher observation", True, [
            "https://classroommosaic.com/observation",
            "https://home.2gno.me/product",
            "https://edutopia.org/article",
        ]),
        # No AI overview -> ignored entirely
        _ai_row("instructional coaching", False, []),
        # Present but empty citations -> not counted toward keywords_with_ai_overview
        _ai_row("teacher feedback", True, []),
    ]


def test_sov_total_citations_counts_all_urls(ai_results):
    sov = compute_share_of_voice(ai_results, CLIENT, COMPETITORS)
    assert sov["total_citations"] == 6
    assert sov["keywords_analyzed"] == 4
    assert sov["keywords_with_ai_overview"] == 2


def test_sov_client_share(ai_results):
    sov = compute_share_of_voice(ai_results, CLIENT, COMPETITORS)
    assert sov["client_citations"] == 1
    assert sov["client_share_of_voice_pct"] == pytest.approx(16.67, abs=0.01)


def test_sov_competitor_rollup_and_subdomain_match(ai_results):
    sov = compute_share_of_voice(ai_results, CLIENT, COMPETITORS)
    by_domain = {e["domain"]: e for e in sov["tracked_entities"]}
    # classroommosaic cited twice across two keywords
    assert by_domain["classroommosaic.com"]["citations"] == 2
    assert by_domain["classroommosaic.com"]["keywords_cited"] == 2
    assert by_domain["classroommosaic.com"]["role"] == "competitor"
    # home.2gno.me listed as a subdomain competitor must match exactly
    assert by_domain["home.2gno.me"]["citations"] == 1
    # A competitor that was never cited still appears at zero (explicit absence)
    assert by_domain["observe4success.com"]["citations"] == 0


def test_sov_other_bucket(ai_results):
    sov = compute_share_of_voice(ai_results, CLIENT, COMPETITORS)
    # wikipedia + edutopia are untracked -> "other"
    assert sov["other_citations_total"] == 2
    other_domains = {d["domain"] for d in sov["top_other_domains"]}
    assert other_domains == {"en.wikipedia.org", "edutopia.org"}


def test_sov_www_normalization_matches_client():
    rows = [_ai_row("kw", True, [
        "https://www.educationwalkthrough.com/a",
        "https://educationwalkthrough.com/b",
    ])]
    sov = compute_share_of_voice(rows, CLIENT, COMPETITORS)
    # both URLs collapse to the same client host
    assert sov["client_citations"] == 2
    assert sov["client_share_of_voice_pct"] == 100.0


def test_sov_empty_results_no_divide_by_zero():
    sov = compute_share_of_voice([], CLIENT, COMPETITORS)
    assert sov["total_citations"] == 0
    assert sov["client_share_of_voice_pct"] == 0.0
    # client + all competitors still enumerated at zero
    labels = {e["domain"] for e in sov["tracked_entities"]}
    assert CLIENT in labels
    assert "home.2gno.me" in labels


def test_aggregate_llm_probes_groups_by_model_and_browse():
    probes = [
        {"model": "chatgpt", "keyword": "k1", "browse": True, "brand_mentioned": True, "error": None},
        {"model": "chatgpt", "keyword": "k1", "browse": True, "brand_mentioned": False, "error": None},
        {"model": "chatgpt", "keyword": "k1", "browse": False, "brand_mentioned": False, "error": None},
        {"model": "gemini", "keyword": "k1", "browse": True, "brand_mentioned": None, "error": "HTTP 500"},
    ]
    agg = aggregate_llm_probes(probes)
    rows = {(r["model"], r["browse"]): r for r in agg["models"]}

    # browse-on chatgpt: 2 valid samples, 1 mention -> 0.5 rate
    assert rows[("chatgpt", True)]["mention_rate"] == 0.5
    assert rows[("chatgpt", True)]["valid_samples"] == 2
    # browse-off chatgpt: 1 valid, 0 mentions -> 0.0 (browse dependence visible)
    assert rows[("chatgpt", False)]["mention_rate"] == 0.0
    # gemini: only an errored sample -> no valid samples, rate None
    assert rows[("gemini", True)]["valid_samples"] == 0
    assert rows[("gemini", True)]["mention_rate"] is None
    assert rows[("gemini", True)]["errors"] == 1


def test_aggregate_llm_probes_overall_rate_and_disclosure():
    probes = [
        {"model": "chatgpt", "keyword": "k", "browse": True, "brand_mentioned": True, "error": None},
        {"model": "chatgpt", "keyword": "k", "browse": True, "brand_mentioned": True, "error": None},
    ]
    agg = aggregate_llm_probes(probes)
    assert agg["overall_mention_rate"] == 1.0
    assert agg["total_valid_samples"] == 2
    # Disclosure fields must always be present so a rate is never shown bare
    assert "over-report" in agg["caveat"]
    assert "real logged-in session" in agg["validation_method"]


def test_aggregate_llm_probes_empty():
    agg = aggregate_llm_probes([])
    assert agg["overall_mention_rate"] is None
    assert agg["total_samples"] == 0
    assert agg["models"] == []
