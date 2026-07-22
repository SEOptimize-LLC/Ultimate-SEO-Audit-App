"""Tests for the technical auditor's status-code, indexability, and
GSC Index Coverage checks (401/403/404/429 split, X-Robots-Tag mismatch,
soft-404 GSC cross-check, Crawled/Discovered - currently not indexed).
"""

import pandas as pd
import pytest

from auditors.technical_auditor import TechnicalAuditor
from models.audit_result import Severity


def _issues_by_type(issues, issue_type):
    return [i for i in issues if i.issue_type == issue_type]


@pytest.fixture()
def status_code_df():
    return pd.DataFrame({
        "url": [
            "https://x.com/ok",
            "https://x.com/unauthorized",
            "https://x.com/forbidden",
            "https://x.com/missing",
            "https://x.com/rate-limited-1",
            "https://x.com/rate-limited-2",
            "https://x.com/bad-request",
            "https://x.com/gone",
        ],
        "status_code": [200, 401, 403, 404, 429, 429, 400, 410],
    })


def test_401_errors_isolated(status_code_df):
    auditor = TechnicalAuditor(status_code_df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "401_unauthorized")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/unauthorized"]
    assert issues[0].severity == Severity.HIGH


def test_403_errors_isolated(status_code_df):
    auditor = TechnicalAuditor(status_code_df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "403_forbidden")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/forbidden"]


def test_404_errors_isolated(status_code_df):
    auditor = TechnicalAuditor(status_code_df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "404_errors")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].severity == Severity.CRITICAL


def test_429_responses_are_insight_not_error(status_code_df):
    auditor = TechnicalAuditor(status_code_df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "429_rate_limited")
    assert len(issues) == 1
    assert issues[0].count == 2
    assert issues[0].severity == Severity.INSIGHT

    # 429s must not leak into the other-4xx bucket
    other_4xx = _issues_by_type(auditor.issues, "other_4xx_errors")
    assert len(other_4xx) == 1
    assert "https://x.com/rate-limited-1" not in other_4xx[0].affected_urls
    assert "https://x.com/rate-limited-2" not in other_4xx[0].affected_urls


def test_other_4xx_excludes_401_403_404_429(status_code_df):
    auditor = TechnicalAuditor(status_code_df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "other_4xx_errors")
    assert len(issues) == 1
    # Only 400 and 410 should land here
    assert issues[0].count == 2
    assert set(issues[0].affected_urls) == {
        "https://x.com/bad-request",
        "https://x.com/gone",
    }


def test_no_4xx_issues_when_all_pages_ok():
    df = pd.DataFrame({
        "url": ["https://x.com/", "https://x.com/a"],
        "status_code": [200, 200],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    for issue_type in (
        "401_unauthorized", "403_forbidden", "404_errors",
        "429_rate_limited", "other_4xx_errors",
    ):
        assert _issues_by_type(auditor.issues, issue_type) == []


@pytest.fixture()
def x_robots_tag_df():
    return pd.DataFrame({
        "url": [
            "https://x.com/hidden-noindex",
            "https://x.com/visible-noindex",
            "https://x.com/clean",
        ],
        "status_code": [200, 200, 200],
        "meta_robots": ["index, follow", "noindex, follow", "index, follow"],
        "x_robots_tag": ["noindex", "noindex", ""],
    })


def test_x_robots_tag_flags_only_hidden_mismatch(x_robots_tag_df):
    auditor = TechnicalAuditor(x_robots_tag_df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "x_robots_tag_noindex_hidden")
    assert len(issues) == 1
    assert issues[0].affected_urls == ["https://x.com/hidden-noindex"]
    assert issues[0].severity == Severity.HIGH
    # The page with noindex in both header and meta tag is visible, not hidden
    assert "https://x.com/visible-noindex" not in issues[0].affected_urls


def test_x_robots_tag_check_noop_without_column():
    df = pd.DataFrame({
        "url": ["https://x.com/"],
        "status_code": [200],
        "meta_robots": ["index, follow"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "x_robots_tag_noindex_hidden") == []


@pytest.fixture()
def soft_404_crawl_df():
    return pd.DataFrame({
        "url": [
            "https://x.com/thin-zero-impressions",
            "https://x.com/thin-with-impressions",
            "https://x.com/healthy",
        ],
        "status_code": [200, 200, 200],
        "word_count": [10, 20, 800],
        "indexability": ["Indexable", "Indexable", "Indexable"],
    })


def test_soft_404_without_gsc_data_only_produces_base_issue(soft_404_crawl_df):
    auditor = TechnicalAuditor(soft_404_crawl_df)
    auditor.run_audit()
    base = _issues_by_type(auditor.issues, "soft_404s")
    confirmed = _issues_by_type(auditor.issues, "soft_404s_confirmed_zero_impressions")
    assert len(base) == 1
    assert base[0].count == 2
    assert confirmed == []


def test_soft_404_with_gsc_zero_impressions_elevates_severity(soft_404_crawl_df):
    gsc_df = pd.DataFrame({
        "page": [
            "https://x.com/thin-zero-impressions",
            "https://x.com/thin-with-impressions",
        ],
        "query": ["a", "b"],
        "clicks": [0, 1],
        "impressions": [0, 50],
        "ctr": [0.0, 0.02],
        "position": [40.0, 12.0],
    })
    auditor = TechnicalAuditor(soft_404_crawl_df, gsc_df=gsc_df)
    auditor.run_audit()
    confirmed = _issues_by_type(auditor.issues, "soft_404s_confirmed_zero_impressions")
    assert len(confirmed) == 1
    assert confirmed[0].affected_urls == ["https://x.com/thin-zero-impressions"]
    assert confirmed[0].severity == Severity.HIGH

    base = _issues_by_type(auditor.issues, "soft_404s")
    assert base[0].count == 2  # unaffected — still reports both thin pages


@pytest.fixture()
def crawl_with_inlinks_df():
    return pd.DataFrame({
        "url": [
            "https://x.com/",
            "https://x.com/thin-page",
            "https://x.com/undiscovered-a",
            "https://x.com/undiscovered-b",
        ],
        "status_code": [200, 200, 200, 200],
        "word_count": [500, 100, 500, 500],
        "internal_links_in": [50, 5, 1, 30],
    })


def test_crawled_not_indexed_check(crawl_with_inlinks_df):
    crawled_df = pd.DataFrame({
        "url": ["https://x.com/thin-page"],
        "index_status": ["Crawled - currently not indexed"],
    })
    auditor = TechnicalAuditor(
        crawl_with_inlinks_df, crawled_not_indexed_df=crawled_df
    )
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "gsc_crawled_not_indexed")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/thin-page"]
    assert "300 words" in issues[0].description


def test_discovered_not_indexed_check(crawl_with_inlinks_df):
    discovered_df = pd.DataFrame({
        "url": ["https://x.com/undiscovered-a", "https://x.com/undiscovered-b"],
        "index_status": ["Discovered - currently not indexed"] * 2,
    })
    auditor = TechnicalAuditor(
        crawl_with_inlinks_df, discovered_not_indexed_df=discovered_df
    )
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "gsc_discovered_not_indexed")
    assert len(issues) == 1
    assert issues[0].count == 2
    assert set(issues[0].affected_urls) == {
        "https://x.com/undiscovered-a",
        "https://x.com/undiscovered-b",
    }
    # Only undiscovered-a has <=2 internal links; the note should reference 1
    assert "1" in issues[0].description


def test_index_coverage_checks_noop_when_dfs_absent(crawl_with_inlinks_df):
    auditor = TechnicalAuditor(crawl_with_inlinks_df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "gsc_crawled_not_indexed") == []
    assert _issues_by_type(auditor.issues, "gsc_discovered_not_indexed") == []


# =============================================================================
# PAGE EXPERIENCE — third-party script density
# =============================================================================


def test_third_party_script_density_fires_above_threshold():
    df = pd.DataFrame({
        "url": [
            "https://x.com/clean",
            "https://x.com/ad-heavy",
        ],
        "status_code": [200, 200],
        "external_js_outlinks": [5, 45],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "third_party_script_density")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/ad-heavy"]
    assert issues[0].severity == Severity.MEDIUM
    assert issues[0].additional_data["max_external_scripts"] == 45


def test_third_party_script_density_noop_without_column():
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "status_code": [200],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "third_party_script_density") == []


# =============================================================================
# PAGE EXPERIENCE — response size vs content ratio
# =============================================================================


def test_response_size_ratio_fires_for_bloated_page():
    df = pd.DataFrame({
        "url": [
            "https://x.com/normal",
            "https://x.com/bloated",
        ],
        "status_code": [200, 200],
        "size_bytes": [60_000, 900_000],
        "word_count": [800, 40],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "response_size_to_content_ratio")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/bloated"]
    assert issues[0].severity == Severity.LOW


def test_response_size_ratio_noop_without_columns():
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "status_code": [200],
        "word_count": [500],  # size_bytes deliberately absent
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "response_size_to_content_ratio") == []


# =============================================================================
# INTERNATIONAL — hreflang return-tag reciprocity
# =============================================================================


def test_hreflang_missing_return_tag_fires():
    # A declares itself + B; B declares only itself (no return tag to A).
    df = pd.DataFrame({
        "url": [
            "https://x.com/en",
            "https://x.com/es",
            "https://x.com/no-hreflang",
        ],
        "hreflang_1_url": [
            "https://x.com/en",
            "https://x.com/es",
            "",
        ],
        "hreflang_2_url": [
            "https://x.com/es",
            "",
            "",
        ],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "hreflang_missing_return_tag")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/en"]
    assert issues[0].severity == Severity.HIGH


def test_hreflang_return_tag_noop_without_hreflang_columns():
    df = pd.DataFrame({
        "url": ["https://x.com/en", "https://x.com/es"],
        "status_code": [200, 200],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "hreflang_missing_return_tag") == []


# =============================================================================
# INTERNATIONAL — hreflang missing x-default
# =============================================================================


def test_hreflang_missing_x_default_fires_when_langs_present():
    # en: has an x-default annotation; es: does not.
    df = pd.DataFrame({
        "url": ["https://x.com/en", "https://x.com/es"],
        "hreflang_1_url": ["https://x.com/en", "https://x.com/en"],
        "hreflang_1_lang": ["en", "en"],
        "hreflang_2_url": ["https://x.com/default", "https://x.com/es"],
        "hreflang_2_lang": ["x-default", "es"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "hreflang_missing_x_default")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/es"]
    assert issues[0].severity == Severity.MEDIUM


def test_hreflang_x_default_noop_when_language_columns_absent():
    # URL-only hreflang export cannot support x-default detection.
    df = pd.DataFrame({
        "url": ["https://x.com/en", "https://x.com/es"],
        "hreflang_1_url": ["https://x.com/en", "https://x.com/en"],
        "hreflang_2_url": ["https://x.com/es", "https://x.com/es"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "hreflang_missing_x_default") == []


# =============================================================================
# INDEXABILITY — declared vs Google-selected canonical divergence
# =============================================================================


def test_declared_vs_selected_canonical_fires_on_divergence():
    df = pd.DataFrame({
        "url": [
            "https://x.com/agree",
            "https://x.com/diverge",
            "https://x.com/blank-declared",
        ],
        "user_canonical": [
            "https://x.com/agree",
            "https://x.com/diverge",
            "",
        ],
        "google_canonical": [
            "https://x.com/agree",
            "https://x.com/other",
            "https://x.com/blank-declared",
        ],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(
        auditor.issues, "declared_vs_selected_canonical_divergence"
    )
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/diverge"]
    assert issues[0].severity == Severity.HIGH


def test_declared_vs_selected_canonical_noop_without_gsc_column():
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "canonical": ["https://x.com/a"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(
        auditor.issues, "declared_vs_selected_canonical_divergence"
    ) == []


# =============================================================================
# INDEXABILITY — index-coverage reconciliation (crawl vs GSC indexed count)
# =============================================================================


def _clean_indexable_df(n: int) -> pd.DataFrame:
    """Build a crawl of `n` clean, indexable, HTTP-200 HTML pages.

    No content_type column (so get_html_pages returns all rows), no canonical
    column (so the self-canonical filter is skipped) — every row counts toward
    the crawl-side should-be-indexed total.
    """
    return pd.DataFrame({
        "url": [f"https://x.com/p{i}" for i in range(n)],
        "status_code": [200] * n,
        "indexability": ["Indexable"] * n,
    })


def test_index_coverage_baseline_when_gsc_count_absent():
    auditor = TechnicalAuditor(_clean_indexable_df(25))
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "index_coverage_baseline")
    assert len(issues) == 1
    assert issues[0].severity == Severity.INSIGHT
    assert issues[0].additional_data["should_be_indexed"] == 25
    # No reconciled verdict should appear when the count is absent
    assert _issues_by_type(auditor.issues, "index_coverage_under_indexation") == []
    assert _issues_by_type(auditor.issues, "index_coverage_bloat") == []
    assert _issues_by_type(auditor.issues, "index_coverage_healthy") == []


def test_index_coverage_under_indexation():
    auditor = TechnicalAuditor(_clean_indexable_df(100), gsc_indexed_count=50)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "index_coverage_under_indexation")
    assert len(issues) == 1
    assert issues[0].severity == Severity.HIGH
    assert issues[0].additional_data["gap"] == 50
    assert _issues_by_type(auditor.issues, "index_coverage_baseline") == []


def test_index_coverage_bloat():
    auditor = TechnicalAuditor(_clean_indexable_df(100), gsc_indexed_count=200)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "index_coverage_bloat")
    assert len(issues) == 1
    assert issues[0].severity == Severity.MEDIUM
    assert issues[0].additional_data["gsc_indexed"] == 200


def test_index_coverage_healthy():
    auditor = TechnicalAuditor(_clean_indexable_df(100), gsc_indexed_count=95)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "index_coverage_healthy")
    assert len(issues) == 1
    assert issues[0].severity == Severity.INSIGHT


def test_index_coverage_noop_below_min_pages():
    # Fewer than INDEX_COVERAGE_MIN_PAGES (20) clean pages — check must no-op
    # entirely, in both baseline and reconciled modes.
    auditor = TechnicalAuditor(_clean_indexable_df(10))
    auditor.run_audit()
    for t in (
        "index_coverage_baseline", "index_coverage_under_indexation",
        "index_coverage_bloat", "index_coverage_healthy",
    ):
        assert _issues_by_type(auditor.issues, t) == []

    auditor2 = TechnicalAuditor(_clean_indexable_df(10), gsc_indexed_count=5)
    auditor2.run_audit()
    for t in (
        "index_coverage_baseline", "index_coverage_under_indexation",
        "index_coverage_bloat", "index_coverage_healthy",
    ):
        assert _issues_by_type(auditor2.issues, t) == []


# =============================================================================
# INDEXABILITY — noindex placed in body (data-gated on a custom extraction)
# =============================================================================


def test_noindex_in_body_fires_with_position_column():
    df = pd.DataFrame({
        "url": ["https://x.com/body-noindex", "https://x.com/head-noindex"],
        "meta_robots": ["noindex, follow", "noindex, follow"],
        "meta_robots_position": ["body", "head"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "noindex_in_body")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/body-noindex"]
    assert issues[0].severity == Severity.HIGH


def test_noindex_in_body_noop_without_position_column():
    # meta_robots present, but no placement column from a custom extraction.
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "meta_robots": ["noindex, follow"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "noindex_in_body") == []


def test_noindex_in_body_noop_on_all_blank_meta_robots():
    # Locks FIX 1: an all-blank meta_robots column read as float64 must not
    # raise AttributeError on the .str accessor (which would otherwise abort
    # the whole audit). run_audit must complete and the check must no-op.
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "meta_robots": [float("nan"), float("nan")],  # all-blank -> float64
        "meta_robots_position": ["body", "head"],
    })
    assert df["meta_robots"].dtype == float
    auditor = TechnicalAuditor(df)
    issues = auditor.run_audit()
    assert isinstance(issues, list)
    assert _issues_by_type(auditor.issues, "noindex_in_body") == []


# =============================================================================
# INDEXABILITY — outbound links on noindex pages leak equity
# =============================================================================


def test_links_on_noindex_pages_fires():
    df = pd.DataFrame({
        "url": ["https://x.com/noindex-hub", "https://x.com/clean"],
        "meta_robots": ["noindex, follow", "index, follow"],
        "internal_links_out": [10, 5],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "links_on_noindex_pages")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/noindex-hub"]
    assert issues[0].additional_data["total_leaked_links"] == 10


def test_links_on_noindex_pages_noop_without_outlinks_column():
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "meta_robots": ["noindex, follow"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "links_on_noindex_pages") == []


def test_links_on_noindex_pages_noop_on_all_blank_meta_robots():
    # Locks FIX 1 for the sibling method.
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "meta_robots": [float("nan"), float("nan")],  # all-blank -> float64
        "internal_links_out": [10, 5],
    })
    auditor = TechnicalAuditor(df)
    issues = auditor.run_audit()
    assert isinstance(issues, list)
    assert _issues_by_type(auditor.issues, "links_on_noindex_pages") == []


# =============================================================================
# REDIRECTS — internal links pointing at redirecting URLs (FIX 3 guard)
# =============================================================================


def test_internal_links_to_redirects_fires_without_redirect_url_column():
    # No redirect_url column present — FIX 3 dropped it from the guard, so the
    # check derives redirects from status_code + internal_links_in and fires.
    df = pd.DataFrame({
        "url": ["https://x.com/old-redirect", "https://x.com/live"],
        "status_code": [301, 200],
        "internal_links_in": [7, 20],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "internal_links_to_redirects")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/old-redirect"]
    assert issues[0].additional_data["total_inlinks_through_redirects"] == 7


def test_internal_links_to_redirects_noop_without_inlinks_column():
    df = pd.DataFrame({
        "url": ["https://x.com/old-redirect"],
        "status_code": [301],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "internal_links_to_redirects") == []


# =============================================================================
# URL HYGIENE — trailing-slash inconsistency
# =============================================================================


def test_trailing_slash_inconsistency_fires():
    # 15 trailing-slash URLs (majority) + 5 no-slash URLs (minority, 25%).
    urls = (
        [f"https://x.com/page-{i}/" for i in range(15)]
        + [f"https://x.com/post-{i}" for i in range(5)]
    )
    df = pd.DataFrame({
        "url": urls,
        "indexability": ["Indexable"] * len(urls),
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "trailing_slash_inconsistency")
    assert len(issues) == 1
    assert issues[0].count == 5
    assert issues[0].severity == Severity.MEDIUM
    assert issues[0].additional_data["majority_convention"] == "trailing slash"


def test_trailing_slash_inconsistency_noop_on_uniform_convention():
    # All URLs share one convention -> no minority -> graceful no-op.
    urls = [f"https://x.com/page-{i}/" for i in range(15)]
    df = pd.DataFrame({
        "url": urls,
        "indexability": ["Indexable"] * len(urls),
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "trailing_slash_inconsistency") == []


def test_trailing_slash_inconsistency_noop_on_tiny_sample():
    df = pd.DataFrame({
        "url": ["https://x.com/a/", "https://x.com/b", "https://x.com/c/"],
        "indexability": ["Indexable"] * 3,
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "trailing_slash_inconsistency") == []


# =============================================================================
# URL HYGIENE — mixed-case URLs
# =============================================================================


def test_mixed_case_urls_fires():
    df = pd.DataFrame({
        "url": ["https://x.com/About-Us", "https://x.com/contact"],
        "indexability": ["Indexable", "Indexable"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "mixed_case_urls")
    assert len(issues) == 1
    assert issues[0].count == 1
    assert issues[0].affected_urls == ["https://x.com/About-Us"]
    assert issues[0].severity == Severity.MEDIUM


def test_mixed_case_urls_noop_when_all_lowercase():
    df = pd.DataFrame({
        "url": ["https://x.com/about-us", "https://x.com/contact"],
        "indexability": ["Indexable", "Indexable"],
    })
    auditor = TechnicalAuditor(df)
    auditor.run_audit()
    assert _issues_by_type(auditor.issues, "mixed_case_urls") == []
