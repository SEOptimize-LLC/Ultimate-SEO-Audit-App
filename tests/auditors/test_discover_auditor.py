"""Tests for the DiscoverAuditor (Google Discover eligibility).

Covers:
- Article-set detection: /blog/ + dated URLs produce the eligibility INSIGHT
  with the right count.
- The strong image-preview blocker fires on ``noimageindex`` /
  ``max-image-preview:none`` delivered via the meta robots tag AND, separately,
  via the X-Robots-Tag HTTP header (the new fix).
- A commercial-only crawl produces the "no editorial content" INSIGHT.
- An empty crawl missing meta_robots/x_robots_tag/url/word_count runs without
  raising.
- A GSC Discover Performance export produces the earning insight + a low-CTR
  opportunity, and a zero-earning export does NOT emit the earning insight.
"""

import pandas as pd

from auditors.discover_auditor import DiscoverAuditor
from models.audit_result import AuditCategory, Severity


def _issues_by_type(issues, issue_type):
    return [i for i in issues if i.issue_type == issue_type]


# ---------------------------------------------------------------------------
# 1. Editorial-set detection -> eligibility INSIGHT with the right count
# ---------------------------------------------------------------------------

def test_blog_and_dated_urls_produce_eligibility_insight():
    # Arrange
    df = pd.DataFrame(
        {
            "url": [
                "https://x.com/blog/how-to-observe-classrooms/",
                "https://x.com/2026/07/summer-learning-trends/",
                "https://x.com/news/spring-release/",
                "https://x.com/products/pricing/",  # commercial -> excluded
            ],
            "content_type": ["text/html"] * 4,
            "indexability": ["indexable"] * 4,
            "word_count": [800, 950, 700, 500],
            "meta_robots": ["index, follow"] * 4,
        }
    )
    auditor = DiscoverAuditor(df)

    # Act
    issues = auditor.run_audit()
    review = _issues_by_type(issues, "discover_eligibility_review")

    # Assert
    assert len(review) == 1
    issue = review[0]
    assert issue.severity == Severity.INSIGHT
    assert issue.category == AuditCategory.DISCOVER
    assert issue.count == 3  # 3 editorial pages, commercial excluded
    urls = issue.affected_urls
    assert "https://x.com/blog/how-to-observe-classrooms/" in urls
    assert "https://x.com/2026/07/summer-learning-trends/" in urls
    assert "https://x.com/products/pricing/" not in urls


# ---------------------------------------------------------------------------
# 2. Image-preview blocker via meta_robots
# ---------------------------------------------------------------------------

def test_image_preview_blocker_via_meta_robots():
    # Arrange
    df = pd.DataFrame(
        {
            "url": [
                "https://x.com/blog/a/",
                "https://x.com/blog/b/",
            ],
            "content_type": ["text/html"] * 2,
            "indexability": ["indexable"] * 2,
            "word_count": [800, 900],
            "meta_robots": [
                "index, follow, noimageindex",
                "index, follow, max-image-preview:none",
            ],
        }
    )
    auditor = DiscoverAuditor(df)

    # Act
    issues = auditor.run_audit()
    blocked = _issues_by_type(issues, "discover_image_preview_suppressed")

    # Assert
    assert len(blocked) == 1
    issue = blocked[0]
    assert issue.severity == Severity.MEDIUM
    assert issue.category == AuditCategory.DISCOVER
    assert issue.count == 2
    assert set(issue.affected_urls) == {
        "https://x.com/blog/a/",
        "https://x.com/blog/b/",
    }


# ---------------------------------------------------------------------------
# 3. Image-preview blocker via x_robots_tag (the new fix)
# ---------------------------------------------------------------------------

def test_image_preview_blocker_via_x_robots_tag():
    # Arrange — directive delivered ONLY via the HTTP header, not meta robots
    df = pd.DataFrame(
        {
            "url": [
                "https://x.com/blog/a/",
                "https://x.com/blog/b/",
            ],
            "content_type": ["text/html"] * 2,
            "indexability": ["indexable"] * 2,
            "word_count": [800, 900],
            "meta_robots": ["index, follow", "index, follow"],
            "x_robots_tag": ["noimageindex", ""],
        }
    )
    auditor = DiscoverAuditor(df)

    # Act
    issues = auditor.run_audit()
    blocked = _issues_by_type(issues, "discover_image_preview_suppressed")

    # Assert
    assert len(blocked) == 1
    issue = blocked[0]
    assert issue.severity == Severity.MEDIUM
    assert issue.count == 1
    assert issue.affected_urls == ["https://x.com/blog/a/"]


# ---------------------------------------------------------------------------
# 4. Commercial-only crawl -> "no editorial content" INSIGHT
# ---------------------------------------------------------------------------

def test_commercial_only_crawl_emits_no_article_content():
    # Arrange
    df = pd.DataFrame(
        {
            "url": [
                "https://x.com/products/widget/",
                "https://x.com/collections/all/",
                "https://x.com/checkout/",
            ],
            "content_type": ["text/html"] * 3,
            "indexability": ["indexable"] * 3,
            "word_count": [400, 300, 200],
            "meta_robots": ["index, follow"] * 3,
        }
    )
    auditor = DiscoverAuditor(df)

    # Act
    issues = auditor.run_audit()
    none_found = _issues_by_type(issues, "discover_no_article_content")
    review = _issues_by_type(issues, "discover_eligibility_review")

    # Assert
    assert len(none_found) == 1
    assert none_found[0].severity == Severity.INSIGHT
    assert none_found[0].category == AuditCategory.DISCOVER
    assert review == []


# ---------------------------------------------------------------------------
# 5. Empty df missing key columns -> no exception
# ---------------------------------------------------------------------------

def test_empty_df_missing_columns_does_not_raise():
    # Arrange — no meta_robots, x_robots_tag, url, or word_count columns
    df = pd.DataFrame()
    auditor = DiscoverAuditor(df)

    # Act / Assert — must not raise
    issues = auditor.run_audit()
    assert isinstance(issues, list)
    # With no editorial content it should still degrade to the no-content note.
    assert _issues_by_type(issues, "discover_no_article_content")


# ---------------------------------------------------------------------------
# 6a. Discover export -> earning insight + low-CTR opportunity
# ---------------------------------------------------------------------------

def test_discover_performance_earning_and_low_ctr_opportunity():
    # Arrange
    crawl = pd.DataFrame(
        {
            "url": ["https://x.com/blog/a/"],
            "content_type": ["text/html"],
            "indexability": ["indexable"],
            "word_count": [900],
            "meta_robots": ["index, follow"],
        }
    )
    # One high-impression low-CTR page (opportunity) + one healthy page.
    perf = pd.DataFrame(
        {
            "Page": [
                "https://x.com/blog/a/",
                "https://x.com/blog/b/",
            ],
            "Impressions": [5000, 200],
            # page a: 0.8% CTR (<2%, >=1000 impr) -> low-CTR opportunity
            "Clicks": [40, 30],
        }
    )
    auditor = DiscoverAuditor(crawl, discover_performance_df=perf)

    # Act
    issues = auditor.run_audit()
    earning = _issues_by_type(issues, "discover_currently_earning")
    opp = _issues_by_type(issues, "discover_low_ctr_opportunity")

    # Assert
    assert len(earning) == 1
    assert earning[0].severity == Severity.INSIGHT
    assert earning[0].count == 2  # both pages have impressions > 0
    assert len(opp) == 1
    assert opp[0].severity == Severity.LOW
    assert opp[0].count == 1
    assert opp[0].affected_urls == ["https://x.com/blog/a/"]


# ---------------------------------------------------------------------------
# 6b. Zero-earning export -> earning insight NOT emitted
# ---------------------------------------------------------------------------

def test_zero_earning_export_does_not_emit_earning_insight():
    # Arrange
    crawl = pd.DataFrame(
        {
            "url": ["https://x.com/blog/a/"],
            "content_type": ["text/html"],
            "indexability": ["indexable"],
            "word_count": [900],
            "meta_robots": ["index, follow"],
        }
    )
    perf = pd.DataFrame(
        {
            "Page": ["https://x.com/blog/a/", "https://x.com/blog/b/"],
            "Impressions": [0, 0],
            "Clicks": [0, 0],
        }
    )
    auditor = DiscoverAuditor(crawl, discover_performance_df=perf)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _issues_by_type(issues, "discover_currently_earning") == []
    assert _issues_by_type(issues, "discover_low_ctr_opportunity") == []
