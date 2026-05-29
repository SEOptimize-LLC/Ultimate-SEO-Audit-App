"""Tests for TopicalAuthorityAuditor.from_computed_map + new check."""

import json
from pathlib import Path

import pandas as pd
import pytest

from auditors.topical_authority_auditor import TopicalAuthorityAuditor
from models.audit_result import Severity


@pytest.fixture()
def crawl_df():
    return pd.DataFrame({
        "url": [
            "https://x.com/",
            "https://x.com/a",
            "https://x.com/b",
            "https://x.com/blog/off-topic-1",
        ],
        "title": [
            "Home - HVAC Services",
            "HVAC repair",
            "Furnace install",
            "Travel tips off topic",
        ],
    })


def _write_topical_map(tmp_path: Path) -> Path:
    out = {
        "central_entity": "HVAC Services",
        "rings": {
            "core": [
                {"url": "https://x.com/", "site_radius": 0.05}
            ],
            "focus": [
                {"url": "https://x.com/a", "site_radius": 0.20}
            ],
            "expansion": [
                {"url": "https://x.com/b", "site_radius": 0.40}
            ],
            "peripheral": [],
        },
        "outliers": ["https://x.com/blog/off-topic-1"],
    }
    p = tmp_path / "topical_map.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    return p


def _write_full_json(tmp_path: Path) -> Path:
    out = {
        "clicks_by_cluster": {
            "0": {"clicks": 5, "impressions": 100, "urls": 2},
            "1": {"clicks": 500, "impressions": 800, "urls": 1},
        },
        "site_radius_per_url": {
            "https://x.com/": 0.05,
            "https://x.com/a": 0.20,
            "https://x.com/b": 0.40,
            "https://x.com/blog/off-topic-1": 0.85,
        },
        "cluster_labels_per_url": {
            "https://x.com/": 0,
            "https://x.com/a": 0,
            "https://x.com/b": 0,
            "https://x.com/blog/off-topic-1": 1,
        },
        "cluster_name_by_id": {"0": "HVAC Services", "1": "Travel"},
        "high_click_off_topic_clusters": [
            {
                "cluster_id": 1,
                "cluster_name": "Travel",
                "clicks": 500,
                "median_site_radius": 0.85,
                "page_count": 1,
            },
        ],
    }
    p = tmp_path / "semantic_map_full.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    return p


def test_from_computed_map_loads_koray_compatible_shape(
    crawl_df, tmp_path
):
    topical_path = _write_topical_map(tmp_path)
    auditor = TopicalAuthorityAuditor.from_computed_map(
        crawl_df, topical_path
    )
    issues = auditor.run_audit()
    outlier_issues = [
        i for i in issues if i.issue_type == "topical_outlier_pages"
    ]
    assert len(outlier_issues) == 1
    assert (
        "https://x.com/blog/off-topic-1"
        in outlier_issues[0].affected_urls
    )


def test_from_computed_map_with_full_json_runs_new_check(
    crawl_df, tmp_path
):
    topical_path = _write_topical_map(tmp_path)
    full_path = _write_full_json(tmp_path)
    auditor = TopicalAuthorityAuditor.from_computed_map(
        crawl_df,
        topical_path,
        full_json_path=full_path,
    )
    issues = auditor.run_audit()
    high_click_issues = [
        i for i in issues
        if i.issue_type == "high_click_off_topic_cluster"
    ]
    assert len(high_click_issues) == 1
    assert high_click_issues[0].severity == Severity.HIGH
    assert "Travel" in high_click_issues[0].title


def test_outlier_recommendation_mentions_subdomain(crawl_df, tmp_path):
    topical_path = _write_topical_map(tmp_path)
    auditor = TopicalAuthorityAuditor.from_computed_map(
        crawl_df, topical_path
    )
    issues = auditor.run_audit()
    outlier = next(
        i for i in issues if i.issue_type == "topical_outlier_pages"
    )
    assert "subdomain" in outlier.recommendation.lower()
    assert "subfolder" in outlier.recommendation.lower()
