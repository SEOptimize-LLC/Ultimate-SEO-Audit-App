"""Tests for BacklinkProfileAuditor.

Covers the four deterministic checks the SEMrush per-link export can support —
DR-proxy band distribution, dofollow share, sitewide/footer concentration, and
new/lost velocity — plus graceful no-ops on an empty frame and on each check's
missing columns.
"""

import pandas as pd
import pytest

from auditors.backlink_profile_auditor import BacklinkProfileAuditor
from models.audit_result import AuditCategory, Severity


def _by_type(issues, issue_type):
    return next((i for i in issues if i.issue_type == issue_type), None)


# ---------------------------------------------------------------------------
# Whole-auditor no-op
# ---------------------------------------------------------------------------

def test_noops_on_empty_dataframe():
    # Arrange
    auditor = BacklinkProfileAuditor(pd.DataFrame())

    # Act
    issues = auditor.run_audit()

    # Assert
    assert issues == []


def test_noops_on_none_dataframe():
    # Arrange
    auditor = BacklinkProfileAuditor(None)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert issues == []


# ---------------------------------------------------------------------------
# Check 1 — DR-proxy band distribution
# ---------------------------------------------------------------------------

def test_dr_distribution_flags_weak_profile():
    # Arrange: 6 distinct referring domains, 5 of 6 in the two lowest DR bands.
    df = pd.DataFrame({
        "source_domain": [f"d{i}.com" for i in range(6)],
        "source_authority": [5, 8, 12, 20, 15, 60],
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "referring_domain_authority_distribution")
    assert issue is not None
    assert issue.severity == Severity.LOW
    assert issue.category == AuditCategory.REFERRING_DOMAINS
    assert issue.additional_data["total_referring_domains"] == 6
    assert issue.additional_data["low_band_share"] == pytest.approx(5 / 6, abs=0.01)


def test_dr_distribution_reports_insight_when_authority_healthy():
    # Arrange: majority of domains in the strong bands → not a weak profile.
    df = pd.DataFrame({
        "source_domain": [f"d{i}.com" for i in range(6)],
        "source_authority": [80, 70, 60, 55, 50, 5],
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "referring_domain_authority_distribution")
    assert issue is not None
    assert issue.severity == Severity.INSIGHT


def test_dr_distribution_dedupes_by_domain():
    # Arrange: many links but only 5 distinct domains; low authority throughout.
    df = pd.DataFrame({
        "source_domain": (["a.com"] * 3 + ["b.com"] * 3 + ["c.com", "d.com", "e.com"]),
        "source_authority": [5, 5, 5, 8, 8, 8, 12, 20, 15],
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "referring_domain_authority_distribution")
    assert issue is not None
    assert issue.additional_data["total_referring_domains"] == 5


def test_dr_distribution_noops_when_authority_missing():
    # Arrange: no source_authority column.
    df = pd.DataFrame({"source_domain": [f"d{i}.com" for i in range(6)]})
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _by_type(issues, "referring_domain_authority_distribution") is None


def test_dr_distribution_noops_below_min_domains():
    # Arrange: only 3 distinct domains (< MIN_REFERRING_DOMAINS).
    df = pd.DataFrame({
        "source_domain": ["a.com", "b.com", "c.com"],
        "source_authority": [5, 8, 12],
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _by_type(issues, "referring_domain_authority_distribution") is None


# ---------------------------------------------------------------------------
# Check 2 — dofollow / nofollow ratio
# ---------------------------------------------------------------------------

def test_dofollow_ratio_flags_low_share():
    # Arrange: 20 links, 18 nofollow → 10% dofollow share.
    df = pd.DataFrame({
        "source_domain": [f"d{i}.com" for i in range(20)],
        "nofollow": [True] * 18 + [False] * 2,
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "low_dofollow_share")
    assert issue is not None
    assert issue.severity == Severity.LOW
    assert issue.category == AuditCategory.BACKLINKS
    assert issue.additional_data["dofollow_share"] == pytest.approx(0.10)


def test_dofollow_ratio_coerces_string_flags():
    # Arrange: nofollow arrives as strings (parser hard-casts, but be defensive).
    df = pd.DataFrame({
        "source_domain": [f"d{i}.com" for i in range(20)],
        "nofollow": ["true"] * 13 + ["false"] * 7,  # 35% dofollow → INSIGHT band
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "low_dofollow_share")
    assert issue is not None
    assert issue.severity == Severity.INSIGHT


def test_dofollow_ratio_noops_when_healthy():
    # Arrange: all dofollow → 100% share.
    df = pd.DataFrame({
        "source_domain": [f"d{i}.com" for i in range(20)],
        "nofollow": [False] * 20,
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _by_type(issues, "low_dofollow_share") is None


def test_dofollow_ratio_noops_below_min_links():
    # Arrange: only 5 links (< MIN_LINKS_FOR_RATIO) even though all nofollow.
    df = pd.DataFrame({
        "source_domain": [f"d{i}.com" for i in range(5)],
        "nofollow": [True] * 5,
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _by_type(issues, "low_dofollow_share") is None


def test_dofollow_ratio_noops_when_column_missing():
    # Arrange: no nofollow column.
    df = pd.DataFrame({"source_domain": [f"d{i}.com" for i in range(20)]})
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _by_type(issues, "low_dofollow_share") is None


# ---------------------------------------------------------------------------
# Check 3 — sitewide / footer link concentration
# ---------------------------------------------------------------------------

def test_sitewide_flags_footer_domain():
    # Arrange: footer.com contributes 60 links; other domains a handful each.
    df = pd.DataFrame({
        "source_domain": (["footer.com"] * 60 + ["a.com", "a.com", "b.com", "c.com"]),
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "sitewide_footer_link_concentration")
    assert issue is not None
    assert issue.severity == Severity.MEDIUM
    assert "footer.com" in issue.affected_urls
    assert issue.additional_data["flagged_domain_count"] == 1


def test_sitewide_noops_when_balanced():
    # Arrange: 3 domains, 5 links each — none clears the threshold.
    df = pd.DataFrame({
        "source_domain": (["a.com"] * 5 + ["b.com"] * 5 + ["c.com"] * 5),
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _by_type(issues, "sitewide_footer_link_concentration") is None


def test_sitewide_noops_when_column_missing():
    # Arrange: no source_domain column.
    df = pd.DataFrame({"anchor_text": ["a", "b", "c"]})
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _by_type(issues, "sitewide_footer_link_concentration") is None


# ---------------------------------------------------------------------------
# Check 4 — new / lost velocity
# ---------------------------------------------------------------------------

def test_velocity_flags_heavy_loss_skew():
    # Arrange: 8 lost vs 2 new → heavy loss skew.
    df = pd.DataFrame({
        "source_url": [f"https://d{i}.com/p" for i in range(10)],
        "is_new": [True, True] + [False] * 8,
        "is_lost": [False, False] + [True] * 8,
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "backlink_new_lost_velocity")
    assert issue is not None
    assert issue.severity == Severity.LOW
    assert issue.additional_data["heavy_loss_skew"] is True
    assert issue.additional_data["lost_count"] == 8
    assert len(issue.affected_urls) == 8


def test_velocity_reports_insight_when_balanced():
    # Arrange: 6 new vs 2 lost → not heavily loss-skewed.
    df = pd.DataFrame({
        "source_url": [f"https://d{i}.com/p" for i in range(8)],
        "is_new": [True] * 6 + [False] * 2,
        "is_lost": [False] * 6 + [True] * 2,
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "backlink_new_lost_velocity")
    assert issue is not None
    assert issue.severity == Severity.INSIGHT
    assert issue.additional_data["heavy_loss_skew"] is False


def test_velocity_coerces_string_flags():
    # Arrange: SEMrush Newlink/Lostlink arriving as strings.
    df = pd.DataFrame({
        "source_url": [f"https://d{i}.com/p" for i in range(10)],
        "is_new": ["false"] * 10,
        "is_lost": ["true"] * 8 + ["false"] * 2,
    })
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    issue = _by_type(issues, "backlink_new_lost_velocity")
    assert issue is not None
    assert issue.severity == Severity.LOW
    assert issue.additional_data["lost_count"] == 8


def test_velocity_noops_when_columns_missing():
    # Arrange: no is_new / is_lost columns.
    df = pd.DataFrame({"source_domain": ["a.com", "b.com"]})
    auditor = BacklinkProfileAuditor(df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _by_type(issues, "backlink_new_lost_velocity") is None
