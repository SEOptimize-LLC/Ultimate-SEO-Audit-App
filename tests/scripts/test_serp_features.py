"""serp_features.py: which answer features a SERP carries, and the route they give. No network."""
from __future__ import annotations

import serp_features as F

AIO_US = {"type": "ai_overview", "references": [{"domain": "www.beehiveplumbing.com"}, {"domain": "angi.com"}]}
AIO_THEM = {"type": "ai_overview", "references": [{"domain": "angi.com"}, {"url": "https://homedepot.com/x"}]}
SNIPPET_US = {"type": "featured_snippet", "domain": "beehiveplumbing.com"}
PAA = {"type": "people_also_ask", "items": [{"type": "people_also_ask_element", "domain": "reddit.com"}]}
ORGANIC = {"type": "organic", "domain": "beehiveplumbing.com"}


def test_no_feature_is_a_ctr_gap():
    assert F.route(F.features([ORGANIC], "beehiveplumbing.com"))[0] == "CTR GAP"


def test_feature_without_us_is_win_the_answer():
    feats = F.features([AIO_THEM, PAA, ORGANIC], "beehiveplumbing.com")
    assert set(feats) == {"ai_overview", "people_also_ask"}
    assert F.route(feats)[0] == "WIN THE ANSWER"


def test_cited_in_any_feature_is_already_answered():
    assert F.route(F.features([AIO_US, PAA], "beehiveplumbing.com"))[0] == "ALREADY ANSWERED"
    assert F.route(F.features([SNIPPET_US], "www.beehiveplumbing.com"))[0] == "ALREADY ANSWERED"


def test_subdomain_counts_lookalike_does_not():
    assert F.features([{"type": "featured_snippet", "domain": "blog.beehiveplumbing.com"}],
                      "beehiveplumbing.com")["featured_snippet"]["cited"]
    assert not F.features([{"type": "featured_snippet", "domain": "notbeehiveplumbing.com"}],
                          "beehiveplumbing.com")["featured_snippet"]["cited"]


def test_reference_url_without_domain_is_read():
    assert F.features([AIO_THEM], "homedepot.com")["ai_overview"]["cited"]


def test_paa_source_inside_expanded_element_is_read():
    paa = {"type": "people_also_ask", "items": [{"type": "people_also_ask_element", "title": "How often?",
                                                 "expanded_element": [{"domain": "www.beehiveplumbing.com"}]}]}
    assert F.features([paa], "beehiveplumbing.com")["people_also_ask"]["cited"]
