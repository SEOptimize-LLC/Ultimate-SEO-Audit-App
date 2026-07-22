"""Tests for AnchorQualityAuditor shared-anchor / crisscrossing check.

Covers the ``_check_shared_anchor_across_targets`` check that surfaces a single
anchor phrase reused across many DISTINCT internal targets (anchor dilution —
the inverse of per-target over-concentration), and its graceful no-ops when the
required columns are absent, when anchors are unique, and when anchors are blank
or image (empty anchor text).
"""

import pandas as pd
import pytest

from auditors.anchor_quality_auditor import (
    AnchorQualityAuditor,
    SHARED_ANCHOR_TARGETS,
    SHARED_ANCHOR_TARGETS_HIGH,
)
from models.audit_result import Severity


@pytest.fixture()
def crawl_df() -> pd.DataFrame:
    """Minimal crawl frame — the shared-anchor check only reads anchors_df."""
    return pd.DataFrame({"url": ["https://x.com/"]})


def _shared_issue(issues):
    return next(
        (i for i in issues if i.issue_type == "shared_anchor_across_targets"),
        None,
    )


def test_fires_when_one_anchor_spans_many_targets(crawl_df: pd.DataFrame) -> None:
    # Arrange: the anchor "our services" points at SHARED_ANCHOR_TARGETS distinct
    # targets; every other anchor is unique.
    targets = [f"https://x.com/service-{i}" for i in range(SHARED_ANCHOR_TARGETS)]
    anchors_df = pd.DataFrame(
        {
            "source_url": [f"https://x.com/page-{i}" for i in range(SHARED_ANCHOR_TARGETS)],
            "target_url": targets,
            "anchor_text": ["our services"] * SHARED_ANCHOR_TARGETS,
        }
    )
    auditor = AnchorQualityAuditor(crawl_df, anchors_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _shared_issue(issues)
    assert issue is not None
    assert issue.severity == Severity.MEDIUM
    assert issue.additional_data["max_distinct_targets"] == SHARED_ANCHOR_TARGETS
    assert issue.additional_data["worst_anchor"] == "our services"
    assert set(issue.affected_urls) == set(targets)


def test_escalates_to_high_at_very_high_spread(crawl_df: pd.DataFrame) -> None:
    # Arrange: one anchor across SHARED_ANCHOR_TARGETS_HIGH distinct targets.
    n = SHARED_ANCHOR_TARGETS_HIGH
    anchors_df = pd.DataFrame(
        {
            "target_url": [f"https://x.com/t-{i}" for i in range(n)],
            "anchor_text": ["click"] * n,
        }
    )
    auditor = AnchorQualityAuditor(crawl_df, anchors_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _shared_issue(issues)
    assert issue is not None
    assert issue.severity == Severity.HIGH


def test_noops_when_anchors_are_unique(crawl_df: pd.DataFrame) -> None:
    # Arrange: many links but each anchor->target pair is unique (1 target each).
    n = SHARED_ANCHOR_TARGETS + 5
    anchors_df = pd.DataFrame(
        {
            "target_url": [f"https://x.com/t-{i}" for i in range(n)],
            "anchor_text": [f"unique anchor {i}" for i in range(n)],
        }
    )
    auditor = AnchorQualityAuditor(crawl_df, anchors_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _shared_issue(issues) is None


def test_ignores_blank_and_image_anchors(crawl_df: pd.DataFrame) -> None:
    # Arrange: blank/image anchors (empty anchor_text) span many targets but must
    # be excluded — an image link carries alt_text, not anchor text.
    n = SHARED_ANCHOR_TARGETS + 3
    anchors_df = pd.DataFrame(
        {
            "target_url": [f"https://x.com/img-{i}" for i in range(n)],
            "anchor_text": [""] * n,
        }
    )
    auditor = AnchorQualityAuditor(crawl_df, anchors_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _shared_issue(issues) is None


def test_counts_distinct_targets_not_link_rows(crawl_df: pd.DataFrame) -> None:
    # Arrange: same anchor->target pair repeated many times = 1 distinct target,
    # so it must NOT fire even though there are many rows.
    anchors_df = pd.DataFrame(
        {
            "source_url": [f"https://x.com/src-{i}" for i in range(SHARED_ANCHOR_TARGETS + 5)],
            "target_url": ["https://x.com/one-target"] * (SHARED_ANCHOR_TARGETS + 5),
            "anchor_text": ["our services"] * (SHARED_ANCHOR_TARGETS + 5),
        }
    )
    auditor = AnchorQualityAuditor(crawl_df, anchors_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _shared_issue(issues) is None


def test_noops_when_target_url_column_absent(crawl_df: pd.DataFrame) -> None:
    # Arrange: anchor_text present but no target_url column at all.
    anchors_df = pd.DataFrame({"anchor_text": ["our services"] * SHARED_ANCHOR_TARGETS})
    auditor = AnchorQualityAuditor(crawl_df, anchors_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _shared_issue(issues) is None


def test_noops_on_empty_anchors_df(crawl_df: pd.DataFrame) -> None:
    # Arrange
    anchors_df = pd.DataFrame(columns=["target_url", "anchor_text"])
    auditor = AnchorQualityAuditor(crawl_df, anchors_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _shared_issue(issues) is None
