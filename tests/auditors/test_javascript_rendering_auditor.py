"""Tests for the JavaScript rendering auditor's interaction-gated content
check (accordion/tab/load-more widget signature) and its graceful no-op when
the required raw-vs-rendered comparison columns are absent.
"""

import pandas as pd
import pytest

from auditors.javascript_rendering_auditor import JavaScriptRenderingAuditor
from models.audit_result import Severity


def _issues_by_type(issues, issue_type):
    return [i for i in issues if i.issue_type == issue_type]


@pytest.fixture()
def gated_content_df():
    """Two pages with the widget signature (big word AND link gap), one clean
    SSR page, and one empty SPA shell (excluded — handled elsewhere)."""
    return pd.DataFrame(
        {
            "url": [
                "https://x.com/gated-one",
                "https://x.com/gated-two",
                "https://x.com/clean-ssr",
                "https://x.com/spa-shell",
            ],
            "content_type": ["text/html"] * 4,
            "indexability": ["Indexable"] * 4,
            # gated: raw has real content but rendered is much larger
            "raw_word_count": [400, 500, 800, 20],
            "rendered_word_count": [1200, 1400, 850, 1000],
            # gated: rendered exposes many more outlinks than raw
            "raw_outlinks": [10, 8, 40, 2],
            "rendered_outlinks": [60, 50, 45, 30],
        }
    )


def test_interaction_gated_content_fires(gated_content_df):
    # Arrange
    auditor = JavaScriptRenderingAuditor(gated_content_df)

    # Act
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "interaction_gated_content")

    # Assert
    assert len(issues) == 1
    issue = issues[0]
    assert issue.severity == Severity.HIGH
    assert issue.count == 2
    assert set(issue.affected_urls) == {
        "https://x.com/gated-one",
        "https://x.com/gated-two",
    }
    # SSR page (small gaps) and SPA shell (empty raw) must be excluded
    assert "https://x.com/clean-ssr" not in issue.affected_urls
    assert "https://x.com/spa-shell" not in issue.affected_urls


def test_interaction_gated_content_noops_without_link_columns():
    # Arrange — word-count columns present but NO outlink columns
    df = pd.DataFrame(
        {
            "url": ["https://x.com/a", "https://x.com/b"],
            "content_type": ["text/html", "text/html"],
            "indexability": ["Indexable", "Indexable"],
            "raw_word_count": [400, 500],
            "rendered_word_count": [1200, 1400],
        }
    )
    auditor = JavaScriptRenderingAuditor(df)

    # Act
    auditor.run_audit()

    # Assert — the gated-content check cannot run and must emit nothing
    assert _issues_by_type(auditor.issues, "interaction_gated_content") == []
