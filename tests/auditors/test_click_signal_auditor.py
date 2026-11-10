"""Tests for ClickSignalAuditor segment-divergence check.

Covers the device/country segmentation check that surfaces pages whose CTR
satisfaction diverges across GSC slices (e.g. healthy on desktop, pogosticking
on mobile), and its graceful no-op when no segment dimension is present.
"""

import pandas as pd
import pytest

from auditors.click_signal_auditor import ClickSignalAuditor


@pytest.fixture()
def crawl_df() -> pd.DataFrame:
    """Minimal crawl frame — the segmentation check only reads gsc_df."""
    return pd.DataFrame({"url": ["https://x.com/leak-repair"]})


def _divergence_issue_types(issues) -> list[str]:
    return [i.issue_type for i in issues if i.issue_type.startswith("ctr_diverges_by_")]


def test_fires_on_device_divergent_page(crawl_df: pd.DataFrame) -> None:
    # Arrange: one page, informational query, healthy on desktop (CTR ~11% at
    # position 3, baseline 0.11 = at_baseline) but underperforming on mobile
    # (CTR ~3% is below 0.7 * baseline).
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/leak-repair", "https://x.com/leak-repair"],
        "query": ["how to fix a leak", "how to fix a leak"],
        "device": ["DESKTOP", "MOBILE"],
        "clicks": [11, 3],
        "impressions": [100, 100],
        "position": [3.0, 3.0],
        "ctr": [0.11, 0.03],
    })
    auditor = ClickSignalAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    types = _divergence_issue_types(issues)
    assert "ctr_diverges_by_device" in types
    issue = next(i for i in issues if i.issue_type == "ctr_diverges_by_device")
    assert issue.affected_urls == ["https://x.com/leak-repair"]
    assert issue.count == 1
    assert issue.additional_data["dimension"] == "device"


def test_noops_when_segment_columns_absent(crawl_df: pd.DataFrame) -> None:
    # Arrange: valid GSC data but no device/country dimension at all.
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/leak-repair"] * 2,
        "query": ["how to fix a leak"] * 2,
        "clicks": [11, 3],
        "impressions": [100, 100],
        "position": [3.0, 3.0],
        "ctr": [0.11, 0.03],
    })
    auditor = ClickSignalAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _divergence_issue_types(issues) == []


def test_noops_when_single_segment_value(crawl_df: pd.DataFrame) -> None:
    # Arrange: device column present but only one distinct value → cannot compare.
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/leak-repair"] * 2,
        "query": ["how to fix a leak"] * 2,
        "device": ["DESKTOP", "DESKTOP"],
        "clicks": [11, 3],
        "impressions": [100, 100],
        "position": [3.0, 3.0],
        "ctr": [0.11, 0.03],
    })
    auditor = ClickSignalAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _divergence_issue_types(issues) == []


def test_noops_when_slices_below_impression_floor(crawl_df: pd.DataFrame) -> None:
    # Arrange: device-split page but each slice is under MIN_SEGMENT_IMPRESSIONS.
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/leak-repair"] * 2,
        "query": ["how to fix a leak"] * 2,
        "device": ["DESKTOP", "MOBILE"],
        "clicks": [3, 1],
        "impressions": [30, 30],
        "position": [3.0, 3.0],
        "ctr": [0.10, 0.03],
    })
    auditor = ClickSignalAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert _divergence_issue_types(issues) == []


def test_country_divergence_also_detected(crawl_df: pd.DataFrame) -> None:
    # Arrange: healthy in usa, underperforming in gbr for the same page.
    gsc_df = pd.DataFrame({
        "page": ["https://x.com/leak-repair"] * 2,
        "query": ["how to fix a leak"] * 2,
        "country": ["usa", "gbr"],
        "clicks": [11, 3],
        "impressions": [100, 100],
        "position": [3.0, 3.0],
        "ctr": [0.11, 0.03],
    })
    auditor = ClickSignalAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert
    assert "ctr_diverges_by_country" in _divergence_issue_types(issues)


def _low_ctr_site(impressions_per_page: int) -> pd.DataFrame:
    """Four pages at position 3, each with a 3% CTR on an informational query.

    The generic informational baseline at position 3 is 11%, so 3% is below
    0.7 x baseline. Against the site's own curve (also 3%) it is average.
    """
    pages = [f"https://x.com/p{i}" for i in range(4)]
    clicks = round(impressions_per_page * 0.03)
    return pd.DataFrame({
        "page": pages,
        "query": ["how to fix a leak"] * 4,
        "clicks": [clicks] * 4,
        "impressions": [impressions_per_page] * 4,
        "position": [3.0] * 4,
        "ctr": [0.03] * 4,
    })


def _below_baseline_issue(issues):
    return next((i for i in issues if i.issue_type == "ctr_below_position_baseline"), None)


def test_site_curve_replaces_generic_baseline_when_band_has_data(crawl_df: pd.DataFrame) -> None:
    # Arrange: 4 pages x 200 impressions = 800 in band 3-4, above the 400 minimum.
    auditor = ClickSignalAuditor(crawl_df, _low_ctr_site(200))

    # Act
    issues = auditor.run_audit()

    # Assert: average for this site, so no page is flagged as a snippet failure.
    assert _below_baseline_issue(issues) is None
    assert auditor._site_curve == {1: pytest.approx(0.03, abs=0.001)}


def test_generic_baseline_used_when_band_is_thin(crawl_df: pd.DataFrame) -> None:
    # Arrange: 3 pages x 100 impressions = 300 in band 3-4, under the 400 minimum.
    gsc_df = _low_ctr_site(100).iloc[:3]

    auditor = ClickSignalAuditor(crawl_df, gsc_df)

    # Act
    issues = auditor.run_audit()

    # Assert: no site curve for the band, so the generic 11% baseline flags all three.
    assert auditor._site_curve == {}
    issue = _below_baseline_issue(issues)
    assert issue is not None and issue.count == 3
