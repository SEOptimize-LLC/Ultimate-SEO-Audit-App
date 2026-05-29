"""Tests for report.build_outputs."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from Skills.semantic_site_map.report import (
    aggregate_clicks_by_cluster,
    build_outputs,
    classify_into_rings,
    pick_central_entity,
)


def test_aggregate_clicks_by_cluster():
    cluster_labels = np.array([0, 0, 1, 1, -1])
    urls = [f"https://x.com/{i}" for i in range(5)]
    gsc = pd.DataFrame({
        "url": urls,
        "clicks": [50, 30, 5, 0, 2],
        "impressions": [500, 200, 100, 20, 30],
    })
    out = aggregate_clicks_by_cluster(urls, cluster_labels, gsc)
    assert out[0]["clicks"] == 80
    assert out[0]["impressions"] == 700
    assert out[1]["clicks"] == 5
    assert out[-1]["clicks"] == 2


def test_aggregate_clicks_handles_missing_gsc():
    cluster_labels = np.array([0, 1])
    urls = ["https://x.com/a", "https://x.com/b"]
    out = aggregate_clicks_by_cluster(urls, cluster_labels, gsc=None)
    assert out[0]["clicks"] == 0
    assert out[1]["clicks"] == 0


def test_classify_into_rings_splits_by_quartiles():
    radii = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    cluster_labels = np.array([0, 0, 1, 1, 2, 2, -1, -1])
    urls = [f"https://x.com/{i}" for i in range(8)]

    rings, outliers = classify_into_rings(urls, cluster_labels, radii)
    assert set(rings.keys()) == {
        "core",
        "focus",
        "expansion",
        "peripheral",
    }
    assert sum(len(v) for v in rings.values()) == 6
    assert len(outliers) == 2


def test_pick_central_entity_uses_largest_cluster_label():
    cluster_name_by_id = {
        0: "Plumbing Services",
        1: "HVAC",
        2: "Random Topic",
    }
    cluster_labels = np.array([0, 0, 0, 1, 1, 2])
    assert pick_central_entity(
        cluster_labels, cluster_name_by_id
    ) == "Plumbing Services"


def test_build_outputs_writes_four_files(tmp_path: Path):
    rng = np.random.default_rng(0)
    n = 12
    text_df = pd.DataFrame({
        "url": [f"https://x.com/{i}" for i in range(n)],
        "text": [f"page {i} content here" for i in range(n)],
    })
    embeddings = rng.normal(size=(n, 8)).astype(np.float32)
    cluster_result = {
        "cluster_labels": np.array([0] * 5 + [1] * 5 + [-1] * 2),
        "cluster_name_by_id": {0: "Topic A", 1: "Topic B"},
        "site_center": embeddings.mean(axis=0),
        "site_radius": np.linspace(0.1, 0.9, n),
        "ngrams_by_cluster": {
            0: ["alpha", "beta"],
            1: ["gamma", "delta"],
        },
    }
    gsc = pd.DataFrame({
        "url": text_df["url"],
        "clicks": [10, 20, 5, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        "impressions": [100] * n,
    })

    paths = build_outputs(
        out_dir=tmp_path,
        text_df=text_df,
        embeddings=embeddings,
        cluster_result=cluster_result,
        gsc=gsc,
        client_name="Test Client",
        model_name="openai/text-embedding-3-small",
    )

    assert paths["topical_map_json"].exists()
    assert paths["full_json"].exists()
    assert paths["report_md"].exists()
    assert paths["png"].exists()

    koray = json.loads(
        paths["topical_map_json"].read_text(encoding="utf-8")
    )
    assert "central_entity" in koray
    assert "rings" in koray
    assert set(koray["rings"].keys()) == {
        "core",
        "focus",
        "expansion",
        "peripheral",
    }
    assert "outliers" in koray

    full = json.loads(paths["full_json"].read_text(encoding="utf-8"))
    assert "clicks_by_cluster" in full
    assert "site_radius_per_url" in full
    assert "high_click_off_topic_clusters" in full
    assert full["embedding_model_used"] == (
        "openai/text-embedding-3-small"
    )


def test_build_outputs_marks_no_gsc_when_missing(tmp_path: Path):
    rng = np.random.default_rng(0)
    n = 10
    text_df = pd.DataFrame({
        "url": [f"https://x.com/{i}" for i in range(n)],
        "text": [f"page {i} content here" for i in range(n)],
    })
    embeddings = rng.normal(size=(n, 8)).astype(np.float32)
    cluster_result = {
        "cluster_labels": np.array([0] * 4 + [1] * 4 + [-1] * 2),
        "cluster_name_by_id": {0: "Topic A", 1: "Topic B"},
        "site_center": embeddings.mean(axis=0),
        "site_radius": np.linspace(0.1, 0.9, n),
        "ngrams_by_cluster": {0: ["alpha"], 1: ["beta"]},
    }
    paths = build_outputs(
        out_dir=tmp_path,
        text_df=text_df,
        embeddings=embeddings,
        cluster_result=cluster_result,
        gsc=None,
        client_name="Test",
        model_name="openai/text-embedding-3-small",
    )
    full = json.loads(paths["full_json"].read_text(encoding="utf-8"))
    assert full["clicks_by_cluster"] == {}
    md = paths["report_md"].read_text(encoding="utf-8")
    assert "click data unavailable" in md.lower()
