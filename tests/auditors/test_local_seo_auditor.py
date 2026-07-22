"""Tests for the LocalSEOAuditor location/localness demotion check.

Covers the ``location_demotion_risk`` finding: location-targeted pages
(city slug in the URL, or a service-area/locations sub-page) that carry
none of the on-page local reinforcement signals (city in title, city in
H1, LocalBusiness/areaServed schema). Verifies the check fires on a
positive fixture, respects reinforcement signals, and no-ops when the
crawl lacks the columns it needs.
"""

import pandas as pd
import pytest

from auditors.local_seo_auditor import LocalSEOAuditor
from models.audit_result import AuditCategory, Severity


def _issues_by_type(issues, issue_type):
    return [i for i in issues if i.issue_type == issue_type]


@pytest.fixture()
def location_df():
    """A local site with three under-reinforced pages and one reinforced."""
    return pd.DataFrame(
        {
            "url": [
                "https://x.com/service-areas/sandy/",  # flagged
                "https://x.com/service-areas/orem/",  # flagged
                "https://x.com/plumbing-provo/",  # flagged (city in URL)
                "https://x.com/service-areas/lehi/",  # reinforced -> not flagged
                "https://x.com/about/",  # not location-targeted
            ],
            "content_type": ["text/html"] * 5,
            "title": [
                "Plumbing Services",
                "Plumbing Services",
                "Plumber",
                "Plumbing Services in Lehi, UT | Brand",
                "About Us",
            ],
            "h1": [
                "Our Plumbing Services",
                "Our Services",
                "Plumber",
                "Lehi Plumbing",
                "About Our Company",
            ],
        }
    )


def test_location_demotion_risk_fires(location_df):
    # Arrange
    auditor = LocalSEOAuditor(location_df)

    # Act
    auditor.run_audit()
    issues = _issues_by_type(auditor.issues, "location_demotion_risk")

    # Assert
    assert len(issues) == 1
    issue = issues[0]
    assert issue.count == 3
    assert issue.severity == Severity.MEDIUM
    assert issue.category == AuditCategory.LOCAL_SEO
    assert "https://x.com/service-areas/sandy/" in issue.affected_urls
    assert "https://x.com/service-areas/orem/" in issue.affected_urls
    assert "https://x.com/plumbing-provo/" in issue.affected_urls
    # Reinforced and non-targeted pages must not appear
    assert "https://x.com/service-areas/lehi/" not in issue.affected_urls
    assert "https://x.com/about/" not in issue.affected_urls


def test_local_schema_reinforcement_prevents_flag():
    # Arrange: city-targeted URLs, no city in title/H1, but LocalBusiness
    # schema with areaServed is present -> reinforced, must not fire.
    df = pd.DataFrame(
        {
            "url": [
                "https://x.com/service-areas/sandy/",
                "https://x.com/service-areas/orem/",
                "https://x.com/service-areas/provo/",
            ],
            "content_type": ["text/html"] * 3,
            "title": ["Plumbing Services", "Plumbing Services", "Plumbing Services"],
            "h1": ["Our Services", "Our Services", "Our Services"],
            "structured_data": [
                '{"@type":"Plumber","areaServed":"Sandy"}',
                '{"@type":"LocalBusiness","areaServed":"Orem"}',
                '{"@type":"LocalBusiness","address":{"@type":"PostalAddress"}}',
            ],
        }
    )
    auditor = LocalSEOAuditor(df)

    # Act
    auditor.run_audit()

    # Assert
    assert _issues_by_type(auditor.issues, "location_demotion_risk") == []


def test_no_op_when_title_and_h1_missing():
    # Arrange: a clearly-local site but the crawl has neither title nor H1,
    # so reinforcement cannot be assessed -> the check must no-op.
    df = pd.DataFrame(
        {
            "url": [
                "https://x.com/service-areas/sandy/",
                "https://x.com/service-areas/orem/",
                "https://x.com/service-areas/provo/",
            ],
            "content_type": ["text/html"] * 3,
        }
    )
    auditor = LocalSEOAuditor(df)

    # Act: call the check directly to isolate it from other checks.
    auditor.clear_issues()
    auditor._check_location_demotion_risk()

    # Assert
    assert _issues_by_type(auditor.issues, "location_demotion_risk") == []


def test_no_op_when_url_column_missing():
    # Arrange
    df = pd.DataFrame({"title": ["Plumbing in Sandy"], "h1": ["Sandy Plumbing"]})
    auditor = LocalSEOAuditor(df)

    # Act
    auditor.clear_issues()
    auditor._check_location_demotion_risk()

    # Assert
    assert _issues_by_type(auditor.issues, "location_demotion_risk") == []


def test_no_op_when_no_location_targeted_pages():
    # Arrange: local site (LocalBusiness schema activates the auditor) but
    # no page URL targets a specific place -> check should not fire.
    df = pd.DataFrame(
        {
            "url": ["https://x.com/", "https://x.com/services/", "https://x.com/contact/"],
            "content_type": ["text/html"] * 3,
            "title": ["Home", "Services", "Contact"],
            "h1": ["Welcome", "Our Services", "Contact Us"],
            "structured_data": [
                '{"@type":"LocalBusiness"}',
                "",
                "",
            ],
        }
    )
    auditor = LocalSEOAuditor(df)

    # Act
    auditor.clear_issues()
    auditor._check_location_demotion_risk()

    # Assert
    assert _issues_by_type(auditor.issues, "location_demotion_risk") == []
