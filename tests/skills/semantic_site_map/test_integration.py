"""End-to-end integration test on a synthetic site with known structure."""

from unittest.mock import patch

import numpy as np
import pandas as pd

from Skills.semantic_site_map.cluster import cluster_pages
from Skills.semantic_site_map.report import build_outputs


def _synthetic_corpus(
    n_per_cluster: int = 40, n_outliers: int = 5
) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(42)
    cluster_a_text = [
        "hvac repair air conditioning furnace install"
    ] * n_per_cluster
    cluster_b_text = [
        "plumbing leak pipe water heater install"
    ] * n_per_cluster
    outlier_texts = ["travel tips europe vacation"] * n_outliers

    texts = cluster_a_text + cluster_b_text + outlier_texts
    urls = (
        [f"https://x.com/hvac/{i}" for i in range(n_per_cluster)]
        + [f"https://x.com/plumb/{i}" for i in range(n_per_cluster)]
        + [f"https://x.com/blog/travel-{i}" for i in range(n_outliers)]
    )

    embeddings = np.vstack([
        rng.normal(loc=[5, 5, 0], scale=0.05, size=(n_per_cluster, 3)),
        rng.normal(
            loc=[-5, -5, 0], scale=0.05, size=(n_per_cluster, 3)
        ),
        rng.normal(loc=[0, 0, 10], scale=0.05, size=(n_outliers, 3)),
    ]).astype(np.float32)

    return pd.DataFrame({"url": urls, "text": texts}), embeddings


def test_synthetic_pipeline_identifies_clusters_and_outputs(tmp_path):
    text_df, embeddings = _synthetic_corpus()

    target = "Skills.semantic_site_map.cluster._call_llm_for_label"
    with patch(target) as m:
        m.side_effect = (
            lambda ngrams, samples, **_: ngrams[0].title()
        )
        result = cluster_pages(
            text_df,
            embeddings,
            api_key="fake",
            min_cluster_size=5,
        )

    cluster_labels = result["cluster_labels"]
    # Expect at least the two main clusters; the small outlier blob
    # may itself form a third cluster under HDBSCAN.
    n_clusters = len({c for c in cluster_labels if c != -1})
    assert n_clusters >= 2

    gsc = pd.DataFrame({
        "url": text_df["url"],
        "clicks": [10] * 40 + [10] * 40 + [200] * 5,
        "impressions": [200] * 85,
    })

    paths = build_outputs(
        out_dir=tmp_path,
        text_df=text_df,
        embeddings=embeddings,
        cluster_result=result,
        gsc=gsc,
        client_name="Synthetic",
        model_name="openai/text-embedding-3-small",
    )
    assert paths["topical_map_json"].exists()
    assert paths["full_json"].exists()
    assert paths["report_md"].exists()
    assert paths["png"].exists()
    # PNG should be non-trivial (real render, not a 0-byte stub).
    assert paths["png"].stat().st_size > 2000
