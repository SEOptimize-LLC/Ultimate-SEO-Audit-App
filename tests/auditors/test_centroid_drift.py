"""Tests for the click-weighted centroid drift finding."""

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
            "https://x.com/c",
        ],
        "title": ["Home", "A", "B", "Off-topic C"],
    })


def _write_topical_map(tmp_path: Path) -> Path:
    out = {
        "central_entity": "HVAC Services",
        "rings": {
            "core": [{"url": "https://x.com/", "site_radius": 0.05}],
            "focus": [{"url": "https://x.com/a", "site_radius": 0.15}],
            "expansion": [{"url": "https://x.com/b", "site_radius": 0.30}],
            "peripheral": [{"url": "https://x.com/c", "site_radius": 0.45}],
        },
        "outliers": [],
    }
    p = tmp_path / "topical_map.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    return p


def _write_full_json(
    tmp_path: Path,
    centroid_cosine_similarity: float,
    name: str = "semantic_map_full.json",
) -> Path:
    """Write a minimal full JSON with a pre-computed drift signal."""
    out = {
        "clicks_by_cluster": {},
        "site_radius_per_url": {
            "https://x.com/": 0.05,
            "https://x.com/a": 0.15,
            "https://x.com/b": 0.30,
            "https://x.com/c": 0.45,
        },
        "cluster_labels_per_url": {
            "https://x.com/": 0,
            "https://x.com/a": 0,
            "https://x.com/b": 0,
            "https://x.com/c": 1,
        },
        "cluster_name_by_id": {"0": "HVAC", "1": "Off-topic"},
        "high_click_off_topic_clusters": [],
        # The new field this finding reads:
        "click_weighted_centroid_drift": {
            "cosine_similarity": centroid_cosine_similarity,
            "top_drift_clusters": (
                [{"cluster_id": 1, "cluster_name": "Off-topic",
                  "clicks": 500, "median_site_radius": 0.45}]
                if centroid_cosine_similarity < 0.9
                else []
            ),
        },
    }
    p = tmp_path / name
    p.write_text(json.dumps(out), encoding="utf-8")
    return p


def test_no_drift_finding_when_centroids_align(crawl_df, tmp_path):
    """Cosine sim >= 0.9 means traffic matches content - no finding."""
    topical_path = _write_topical_map(tmp_path)
    full_path = _write_full_json(tmp_path, centroid_cosine_similarity=0.95)
    auditor = TopicalAuthorityAuditor.from_computed_map(
        crawl_df, topical_path, full_json_path=full_path,
    )
    issues = auditor.run_audit()
    drift_issues = [
        i for i in issues
        if i.issue_type == "click_weighted_centroid_drift"
    ]
    assert drift_issues == []


def test_drift_finding_when_centroids_diverge(crawl_df, tmp_path):
    """Cosine sim < 0.9 means traffic is off-center - emit HIGH finding."""
    topical_path = _write_topical_map(tmp_path)
    full_path = _write_full_json(tmp_path, centroid_cosine_similarity=0.65)
    auditor = TopicalAuthorityAuditor.from_computed_map(
        crawl_df, topical_path, full_json_path=full_path,
    )
    issues = auditor.run_audit()
    drift_issues = [
        i for i in issues
        if i.issue_type == "click_weighted_centroid_drift"
    ]
    assert len(drift_issues) == 1
    assert drift_issues[0].severity == Severity.HIGH


def test_drift_finding_skipped_when_no_full_map(crawl_df, tmp_path):
    """Without the full JSON, the drift check is a silent no-op."""
    topical_path = _write_topical_map(tmp_path)
    auditor = TopicalAuthorityAuditor.from_computed_map(
        crawl_df, topical_path, full_json_path=None,
    )
    issues = auditor.run_audit()
    drift_issues = [
        i for i in issues
        if i.issue_type == "click_weighted_centroid_drift"
    ]
    assert drift_issues == []


def test_drift_finding_skipped_when_no_drift_field(crawl_df, tmp_path):
    """Backward compat: old full JSONs without the field don't crash."""
    topical_path = _write_topical_map(tmp_path)
    out = {
        "clicks_by_cluster": {},
        "site_radius_per_url": {},
        "cluster_labels_per_url": {},
        "cluster_name_by_id": {},
        "high_click_off_topic_clusters": [],
        # No click_weighted_centroid_drift field at all.
    }
    full_path = tmp_path / "semantic_map_full_legacy.json"
    full_path.write_text(json.dumps(out), encoding="utf-8")
    auditor = TopicalAuthorityAuditor.from_computed_map(
        crawl_df, topical_path, full_json_path=full_path,
    )
    issues = auditor.run_audit()  # must not raise
    drift_issues = [
        i for i in issues
        if i.issue_type == "click_weighted_centroid_drift"
    ]
    assert drift_issues == []
