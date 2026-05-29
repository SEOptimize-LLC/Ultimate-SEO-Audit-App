"""Tests for cluster + _ngrams modules."""

from unittest.mock import patch

import numpy as np
import pandas as pd

from Skills.semantic_site_map._ngrams import top_ngrams_per_cluster
from Skills.semantic_site_map.cluster import (
    cluster_pages,
    compute_site_center,
    compute_site_radius,
    label_clusters,
    run_clustering,
)


def test_compute_site_center_is_mean():
    embeddings = np.array([
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0],
    ])
    center = compute_site_center(embeddings)
    np.testing.assert_allclose(center, [2 / 3, 2 / 3])


def test_compute_site_radius_is_cosine_distance():
    embeddings = np.array([
        [1.0, 0.0],
        [1.0, 0.0],   # same direction -> distance 0
        [-1.0, 0.0],  # opposite direction -> distance 2
        [0.0, 1.0],   # orthogonal -> distance 1
    ])
    center = np.array([1.0, 0.0])
    radii = compute_site_radius(embeddings, center)
    np.testing.assert_allclose(radii, [0.0, 0.0, 2.0, 1.0], atol=1e-6)


def test_run_clustering_groups_close_points():
    rng = np.random.default_rng(0)
    cluster_a = rng.normal(loc=[5, 5], scale=0.1, size=(30, 2))
    cluster_b = rng.normal(loc=[-5, -5], scale=0.1, size=(30, 2))
    # Outliers placed far from both cluster centers in all directions so
    # HDBSCAN cannot reach them with min_cluster_size=5.
    outliers = np.array([
        [0.0, 50.0],
        [50.0, 0.0],
        [-50.0, 0.0],
        [0.0, -50.0],
        [50.0, 50.0],
    ])
    embeddings = np.vstack([cluster_a, cluster_b, outliers])

    labels = run_clustering(embeddings, min_cluster_size=5)

    unique_clusters = set(labels) - {-1}
    assert len(unique_clusters) == 2
    # Every outlier is well-separated and should land in the noise bucket.
    assert (labels[-5:] == -1).all()


def test_run_clustering_falls_back_to_kmeans_on_degenerate():
    rng = np.random.default_rng(0)
    embeddings = rng.normal(loc=[0, 0], scale=0.01, size=(50, 2))
    labels = run_clustering(
        embeddings,
        min_cluster_size=5,
        kmeans_fallback_k=4,
    )
    assert len(set(labels) - {-1}) >= 2


def test_top_ngrams_per_cluster():
    texts = pd.Series([
        "hvac repair air conditioning",
        "air conditioning hvac repair",
        "plumbing leak repair pipe",
        "plumbing pipe leak",
    ])
    cluster_labels = np.array([0, 0, 1, 1])
    out = top_ngrams_per_cluster(texts, cluster_labels, top_n=3)
    assert 0 in out and 1 in out
    assert any(
        "hvac" in ng or "air" in ng or "conditioning" in ng for ng in out[0]
    )
    assert any(
        "plumb" in ng or "leak" in ng or "pipe" in ng for ng in out[1]
    )


def test_label_clusters_uses_llm():
    ngrams_by_cluster = {
        0: ["hvac repair", "furnace"],
        1: ["plumbing", "leak"],
    }
    samples_by_cluster = {
        0: ["https://x.com/hvac-1", "https://x.com/hvac-2"],
        1: ["https://x.com/plumb-1", "https://x.com/plumb-2"],
    }

    def fake_label(ngrams, samples, **_):
        if "hvac" in ngrams[0]:
            return "HVAC services"
        return "Plumbing services"

    target = "Skills.semantic_site_map.cluster._call_llm_for_label"
    with patch(target, side_effect=fake_label):
        labels = label_clusters(
            ngrams_by_cluster,
            samples_by_cluster,
            api_key="fake",
        )
    assert labels[0] == "HVAC services"
    assert labels[1] == "Plumbing services"


def test_label_clusters_falls_back_on_llm_failure():
    ngrams_by_cluster = {0: ["hvac repair", "furnace", "thermostat"]}
    samples_by_cluster = {0: ["https://x.com/a"]}

    def boom(*_, **__):
        raise RuntimeError("LLM down")

    target = "Skills.semantic_site_map.cluster._call_llm_for_label"
    with patch(target, side_effect=boom):
        labels = label_clusters(
            ngrams_by_cluster,
            samples_by_cluster,
            api_key="fake",
        )
    # Falls back to top-3 raw ngrams joined.
    assert "hvac repair" in labels[0]


def test_cluster_pages_end_to_end():
    rng = np.random.default_rng(0)
    cluster_a = rng.normal(loc=[5, 5], scale=0.1, size=(20, 2))
    cluster_b = rng.normal(loc=[-5, -5], scale=0.1, size=(20, 2))
    # Outliers placed far enough that HDBSCAN cannot absorb them.
    outliers = np.array([
        [0.0, 50.0],
        [50.0, 0.0],
        [-50.0, 0.0],
        [0.0, -50.0],
        [50.0, 50.0],
    ])
    embeddings = np.vstack([cluster_a, cluster_b, outliers]).astype(
        np.float32
    )

    n = len(embeddings)
    text_df = pd.DataFrame({
        "url": [f"https://x.com/{i}" for i in range(n)],
        "text": (
            ["hvac repair air conditioning"] * 20
            + ["plumbing leak pipe"] * 20
            + [
                "random off topic post a",
                "random off topic post b",
                "random off topic post c",
                "random off topic post d",
                "random off topic post e",
            ]
        ),
    })

    target = "Skills.semantic_site_map.cluster._call_llm_for_label"
    with patch(target) as m:
        m.side_effect = lambda ngrams, samples, **_: ngrams[0].title()
        result = cluster_pages(
            text_df,
            embeddings,
            min_cluster_size=5,
            api_key="fake",
        )

    assert "site_center" in result
    assert "site_radius" in result
    assert len(result["site_radius"]) == n
    assert "cluster_labels" in result
    assert "cluster_name_by_id" in result
    # The 5 far-away outliers should be marked unclustered.
    assert (result["cluster_labels"] == -1).sum() >= 5
