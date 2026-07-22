"""Tests for QueryCountAuditor — Daniel Foley Carter query-counting checks.

Covers the four single-snapshot checks (dead-page breadth, position-band
distribution, content-to-query ratio, lead-query dilution), the query-gate
INSIGHT emitted when only page-level GSC is supplied, and graceful no-ops when
gsc_df is empty/None.
"""

import pandas as pd
import pytest

from auditors.query_count_auditor import QueryCountAuditor


def _types(issues) -> list[str]:
    return [i.issue_type for i in issues]


def _get(issues, issue_type):
    return next(i for i in issues if i.issue_type == issue_type)


@pytest.fixture()
def crawl_df() -> pd.DataFrame:
    """Crawl frame with the columns the checks join against."""
    return pd.DataFrame({
        "url": [
            "https://x.com/dead-page",
            "https://x.com/healthy-page",
            "https://x.com/heavy-page",
            "https://x.com/mismatch-page",
        ],
        "indexability": ["indexable", "indexable", "indexable", "indexable"],
        "word_count": [300, 1200, 2000, 900],
        "title": [
            "Dead Page",
            "Healthy Page About Leak Repair",
            "Comprehensive Guide",
            "Blue Widgets Overview",
        ],
        "h1": [
            "Dead Page",
            "Leak Repair Guide",
            "Comprehensive Guide",
            "Blue Widgets",
        ],
    })


def _query_rows(page, queries, position=5.0, impressions=200):
    """Build GSC rows: one row per query for a page."""
    return pd.DataFrame({
        "page": [page] * len(queries),
        "query": queries,
        "position": [position] * len(queries),
        "impressions": [impressions] * len(queries),
        "clicks": [1] * len(queries),
    })


# ---------------------------------------------------------------------------
# Query gate + empty/None no-ops
# ---------------------------------------------------------------------------

def test_emits_insight_when_query_column_absent(crawl_df):
    # Arrange: page-level GSC only (no 'query' dimension).
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/dead-page"],
        "position": [5.0],
        "impressions": [200],
        "clicks": [1],
    })
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert: exactly the query-gate insight, nothing else.
    assert _types(issues) == ["query_count_needs_query_level_gsc"]


def test_noops_when_gsc_empty(crawl_df):
    # Arrange
    auditor = QueryCountAuditor(crawl_df, pd.DataFrame())

    # Act / Assert
    assert auditor.run_audit() == []


def test_noops_when_gsc_none(crawl_df):
    # Arrange
    auditor = QueryCountAuditor(crawl_df, None)

    # Act / Assert
    assert auditor.run_audit() == []


# ---------------------------------------------------------------------------
# CHECK 1 — dead page by query breadth
# ---------------------------------------------------------------------------

def test_fires_dead_page_query_breadth(crawl_df):
    # Arrange: dead-page served for 2 distinct queries (near-zero band).
    gsc_df = _query_rows("https://x.com/dead-page", ["leak repair", "fix leak"])
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "query_breadth_dead_pages" in _types(issues)
    issue = _get(issues, "query_breadth_dead_pages")
    assert "https://x.com/dead-page" in issue.affected_urls
    assert issue.additional_data["dead_count"] == 1


def test_healthy_page_not_flagged_as_dead(crawl_df):
    # Arrange: 60 distinct queries clears the little-value band (< 50).
    queries = [f"leak repair variant {n}" for n in range(60)]
    gsc_df = _query_rows("https://x.com/healthy-page", queries)
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "query_breadth_dead_pages" not in _types(issues)


# ---------------------------------------------------------------------------
# CHECK 2 — position-band distribution
# ---------------------------------------------------------------------------

def test_fires_position_band_low_visibility(crawl_df):
    # Arrange: 6 distinct queries all deep in positions 21-100.
    queries = [f"blue widget q{n}" for n in range(6)]
    gsc_df = _query_rows(
        "https://x.com/mismatch-page", queries, position=35.0, impressions=150,
    )
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "queries_stuck_low_visibility" in _types(issues)
    issue = _get(issues, "queries_stuck_low_visibility")
    assert "https://x.com/mismatch-page" in issue.affected_urls


def test_position_band_noops_when_queries_rank_well(crawl_df):
    # Arrange: 6 queries all on page one (position 5) — visible, not stuck.
    queries = [f"leak repair q{n}" for n in range(6)]
    gsc_df = _query_rows("https://x.com/healthy-page", queries, position=5.0)
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "queries_stuck_low_visibility" not in _types(issues)


# ---------------------------------------------------------------------------
# CHECK 3 — content-to-query ratio
# ---------------------------------------------------------------------------

def test_fires_high_word_low_query_ratio(crawl_df):
    # Arrange: heavy-page has 2000 words (crawl) but only 3 distinct queries.
    gsc_df = _query_rows(
        "https://x.com/heavy-page", ["guide a", "guide b", "guide c"],
    )
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "high_word_low_query_ratio" in _types(issues)
    issue = _get(issues, "high_word_low_query_ratio")
    assert "https://x.com/heavy-page" in issue.affected_urls


def test_content_ratio_excludes_category_urls():
    # Arrange: heavy category page with few queries is exempt.
    crawl_df = pd.DataFrame({
        "url": ["https://x.com/category/widgets"],
        "indexability": ["indexable"],
        "word_count": [2500],
        "title": ["Widgets Category"],
        "h1": ["Widgets"],
    })
    gsc_df = _query_rows("https://x.com/category/widgets", ["widgets", "buy widgets"])
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "high_word_low_query_ratio" not in _types(issues)


# ---------------------------------------------------------------------------
# CHECK 4 — serve-rate / lead-query dilution
# ---------------------------------------------------------------------------

def test_fires_lead_query_title_mismatch(crawl_df):
    # Arrange: mismatch-page's top query ("waterproof membrane") shares no tokens
    # with its title/H1 ("Blue Widgets ..."). High impressions on the lead query.
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/mismatch-page", "https://x.com/mismatch-page"],
        "query": ["waterproof membrane installation", "sealant coating"],
        "position": [8.0, 9.0],
        "impressions": [500, 40],
        "clicks": [3, 0],
    })
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "lead_query_title_mismatch" in _types(issues)
    issue = _get(issues, "lead_query_title_mismatch")
    assert "https://x.com/mismatch-page" in issue.affected_urls


def test_lead_query_aligned_not_flagged(crawl_df):
    # Arrange: healthy-page's lead query ("leak repair guide") overlaps its
    # title ("Healthy Page About Leak Repair") and H1 ("Leak Repair Guide").
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/healthy-page"],
        "query": ["leak repair guide"],
        "position": [4.0],
        "impressions": [500],
        "clicks": [30],
    })
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "lead_query_title_mismatch" not in _types(issues)


# ---------------------------------------------------------------------------
# Graceful degradation — missing crawl columns
# ---------------------------------------------------------------------------

def test_content_ratio_noops_without_word_count():
    # Arrange: crawl df has no word_count column → check 3 cannot run.
    crawl_df = pd.DataFrame({
        "url": ["https://x.com/heavy-page"],
        "indexability": ["indexable"],
        "title": ["Guide"],
        "h1": ["Guide"],
    })
    gsc_df = _query_rows("https://x.com/heavy-page", ["a", "b", "c"])
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert: no crash, and the content-ratio check simply doesn't emit.
    assert "high_word_low_query_ratio" not in _types(issues)


def test_lead_query_noops_without_impressions():
    # Arrange: GSC lacks impressions → check 4 (and its idxmax) cannot run.
    crawl_df = pd.DataFrame({
        "url": ["https://x.com/mismatch-page"],
        "indexability": ["indexable"],
        "word_count": [900],
        "title": ["Blue Widgets"],
        "h1": ["Blue Widgets"],
    })
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/mismatch-page"],
        "query": ["waterproof membrane"],
        "position": [8.0],
    })
    auditor = QueryCountAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "lead_query_title_mismatch" not in _types(issues)
