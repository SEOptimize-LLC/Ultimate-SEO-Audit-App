"""Tests for the content pruning auditor's topic-aware (siteRadius) elevation
sub-check: it fires for low-value pages that are also topical outliers when
siteRadius data is supplied (via constructor mapping or a df column), and
no-ops when no siteRadius data is present so the default wiring is unchanged.
"""

import pandas as pd
import pytest

from auditors.content_pruning_auditor import ContentPruningAuditor
from models.audit_result import Severity


def _issues_by_type(issues, issue_type):
    return [i for i in issues if i.issue_type == issue_type]


@pytest.fixture()
def prune_df():
    """Four indexable pages:
    - offtopic-dead:   no traffic + high siteRadius  -> should elevate
    - offtopic-live:   good traffic + high siteRadius -> NOT low-value, skip
    - ontopic-dead:    no traffic + low siteRadius    -> not an outlier, skip
    - ontopic-live:    good traffic + low siteRadius   -> healthy, skip
    """
    return pd.DataFrame(
        {
            "url": [
                "https://x.com/offtopic-dead",
                "https://x.com/offtopic-live",
                "https://x.com/ontopic-dead",
                "https://x.com/ontopic-live",
            ],
            "content_type": ["text/html"] * 4,
            "indexability": ["Indexable"] * 4,
            "word_count": [900, 900, 900, 900],
            "gsc_clicks": [0, 500, 0, 500],
            "internal_links_in": [3, 3, 3, 3],
        }
    )


def test_offtopic_elevation_fires_with_radius_dict(prune_df):
    # Arrange
    site_radius = {
        "https://x.com/offtopic-dead": 0.82,
        "https://x.com/offtopic-live": 0.75,
        "https://x.com/ontopic-dead": 0.20,
        "https://x.com/ontopic-live": 0.15,
    }
    auditor = ContentPruningAuditor(prune_df, site_radius=site_radius)

    # Act
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "content_prune_offtopic")

    # Assert — only the low-value AND off-topic page qualifies
    assert len(issues) == 1
    issue = issues[0]
    assert issue.severity == Severity.HIGH
    assert issue.affected_urls == ["https://x.com/offtopic-dead"]
    assert issue.additional_data["affected_count"] == 1


def test_offtopic_elevation_reads_site_radius_column(prune_df):
    # Arrange — same signal, delivered as a df column instead of a mapping
    df = prune_df.copy()
    df["site_radius"] = [0.82, 0.75, 0.20, 0.15]
    auditor = ContentPruningAuditor(df)

    # Act
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "content_prune_offtopic")

    # Assert
    assert len(issues) == 1
    assert issues[0].affected_urls == ["https://x.com/offtopic-dead"]


def test_offtopic_elevation_noops_without_radius(prune_df):
    # Arrange — no mapping, no column: sub-check must stay silent
    auditor = ContentPruningAuditor(prune_df)

    # Act
    auditor.run_audit()

    # Assert — topic-aware finding absent; standard prune buckets still run
    assert _issues_by_type(auditor.issues, "content_prune_offtopic") == []


def test_default_constructor_backward_compatible(prune_df):
    # Arrange / Act — the app.py call site passes only the DataFrame
    auditor = ContentPruningAuditor(prune_df)
    result = auditor.run_audit()

    # Assert — still runs and returns issues without raising
    assert isinstance(result, list)


# =============================================================================
# DFC CHECK 1 — VIABILITY 2x2 (viable x required)
# =============================================================================


@pytest.fixture()
def viability_df():
    """Three indexable pages spanning the viability x required quadrants:
    - service-a:       has demand              -> viable
    - privacy-policy:  no demand, required     -> noindex,follow (not delete)
    - random-dead:     no demand, not required -> prune candidate
    """
    return pd.DataFrame(
        {
            "url": [
                "https://x.com/service-a",
                "https://x.com/privacy-policy",
                "https://x.com/random-dead",
            ],
            "content_type": ["text/html"] * 3,
            "indexability": ["Indexable"] * 3,
            "word_count": [800, 300, 120],
            "gsc_clicks": [50, 0, 0],
            "gsc_impressions": [500, 0, 0],
        }
    )


def test_viability_matrix_fires_and_classifies(viability_df):
    # Arrange
    auditor = ContentPruningAuditor(viability_df)

    # Act
    auditor.run_audit()
    matrix = _issues_by_type(auditor.issues, "content_viability_matrix")
    noindex = _issues_by_type(auditor.issues, "content_required_noindex")

    # Assert — 2x2 summary present with correct quadrant counts
    assert len(matrix) == 1
    data = matrix[0].additional_data
    assert data["viable"] == 1
    assert data["nonviable_required"] == 1
    assert data["nonviable_prune"] == 1

    # Assert — required-but-dead page routed to noindex, not deletion
    assert len(noindex) == 1
    assert noindex[0].affected_urls == ["https://x.com/privacy-policy"]


def test_viability_matrix_noops_without_demand_columns(viability_df):
    # Arrange — strip both demand columns; viability is undeterminable
    df = viability_df.drop(columns=["gsc_clicks", "gsc_impressions"])
    auditor = ContentPruningAuditor(df)

    # Act
    auditor.run_audit()

    # Assert — the check degrades to silence rather than guessing
    assert _issues_by_type(auditor.issues, "content_viability_matrix") == []
    assert _issues_by_type(auditor.issues, "content_required_noindex") == []


# =============================================================================
# DFC CHECK 2 — CONSUMPTION-TIME vs DWELL GAP
# =============================================================================


@pytest.fixture()
def dwell_df():
    """Long/short-form pages with GA4 average session duration:
    - deadlong-numeric: 2000 words, 60s dwell (numeric secs) -> below floor, fires
    - deadlong-clock:   2000 words, '0:01:30' (90s)          -> below floor, fires
    - livelong:         2000 words, '0:10:00' (600s)         -> above floor, skip
    - shortpage:        400 words,  10s dwell                 -> not long-form, skip
    """
    return pd.DataFrame(
        {
            "url": [
                "https://x.com/deadlong-numeric",
                "https://x.com/deadlong-clock",
                "https://x.com/livelong",
                "https://x.com/shortpage",
            ],
            "content_type": ["text/html"] * 4,
            "indexability": ["Indexable"] * 4,
            "word_count": [2000, 2000, 2000, 400],
            "ga_avg_session_duration": [60, "0:01:30", "0:10:00", 10],
        }
    )


def test_dwell_gap_fires_for_low_engagement_longform(dwell_df):
    # Arrange
    auditor = ContentPruningAuditor(dwell_df)

    # Act
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "content_low_dwell_longform")

    # Assert — only the two low-dwell long-form pages are flagged (both
    # duration shapes parse); the healthy long-form and short pages are not
    assert len(issues) == 1
    assert issues[0].severity == Severity.LOW
    assert set(issues[0].affected_urls) == {
        "https://x.com/deadlong-numeric",
        "https://x.com/deadlong-clock",
    }


def test_dwell_gap_noops_without_duration_column(dwell_df):
    # Arrange — no dwell signal; it cannot be inferred from other columns
    df = dwell_df.drop(columns=["ga_avg_session_duration"])
    auditor = ContentPruningAuditor(df)

    # Act
    auditor.run_audit()

    # Assert — check stays silent rather than fabricating engagement
    assert _issues_by_type(auditor.issues, "content_low_dwell_longform") == []


def test_parse_duration_seconds_handles_shapes():
    # Arrange / Act / Assert — numeric, mm:ss, hh:mm:ss, and junk
    parse = ContentPruningAuditor._parse_duration_seconds
    assert parse(90) == 90.0
    assert parse("0:01:30") == 90.0
    assert parse("02:00") == 120.0
    assert parse("") is None
    assert parse(None) is None
    assert parse("not-a-time") is None


# =============================================================================
# DFC CHECK 3 — CATEGORY-PAGE INTENT GUARD
# =============================================================================


@pytest.fixture()
def category_df():
    """Category vs editorial pages by word count:
    - thin category:    /product-category/widgets, 60 words  -> guard fires
    - healthy category: /collections/tools, 800 words        -> not thin, skip
    - thin blog:        /blog/tips, 60 words                 -> not category, skip
    """
    return pd.DataFrame(
        {
            "url": [
                "https://x.com/product-category/widgets",
                "https://x.com/collections/tools",
                "https://x.com/blog/tips",
            ],
            "content_type": ["text/html"] * 3,
            "indexability": ["Indexable"] * 3,
            "word_count": [60, 800, 60],
        }
    )


def test_category_intent_guard_fires_for_thin_category(category_df):
    # Arrange
    auditor = ContentPruningAuditor(category_df)

    # Act
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "content_category_intent_guard")

    # Assert — only the thin commercial category page is flagged
    assert len(issues) == 1
    assert issues[0].affected_urls == [
        "https://x.com/product-category/widgets"
    ]


def test_category_intent_guard_noops_without_word_count(category_df):
    # Arrange — thinness (and thus the guard) can't be assessed
    df = category_df.drop(columns=["word_count"])
    auditor = ContentPruningAuditor(df)

    # Act
    auditor.run_audit()

    # Assert
    assert (
        _issues_by_type(auditor.issues, "content_category_intent_guard") == []
    )
