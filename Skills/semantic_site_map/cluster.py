"""Clustering, site-center / siteRadius, and LLM cluster labeling."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import requests

from Skills.semantic_site_map._ngrams import top_ngrams_per_cluster

logger = logging.getLogger(__name__)

DEFAULT_LLM_MODEL = "anthropic/claude-sonnet-4.5"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


def compute_site_center(embeddings: np.ndarray) -> np.ndarray:
    """Mean embedding across all pages."""
    if embeddings.ndim != 2 or len(embeddings) == 0:
        raise ValueError(
            "compute_site_center requires a non-empty 2D matrix"
        )
    return embeddings.mean(axis=0)


def compute_site_radius(
    embeddings: np.ndarray, center: np.ndarray
) -> np.ndarray:
    """Cosine distance from each row to `center`.

    0 = same direction; 2 = opposite.
    """
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(center)
    norms = np.where(norms == 0, 1e-9, norms)
    cosine_sim = (embeddings @ center) / norms
    return 1.0 - cosine_sim


def run_clustering(
    embeddings: np.ndarray,
    min_cluster_size: Optional[int] = None,
    kmeans_fallback_k: int = 4,
) -> np.ndarray:
    """Cluster embeddings with HDBSCAN; fall back to KMeans when degenerate.

    Returns:
        Integer label per row; -1 indicates outlier (HDBSCAN) or
        far-from-centroid (KMeans fallback).
    """
    import hdbscan

    n = len(embeddings)
    if min_cluster_size is None:
        min_cluster_size = max(5, n // 50)
    min_cluster_size = max(2, min(min_cluster_size, n - 1))

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size, metric="euclidean"
    )
    labels = clusterer.fit_predict(embeddings)
    unique_clusters = set(labels) - {-1}

    if len(unique_clusters) >= 2:
        return labels

    logger.warning(
        "cluster: HDBSCAN found %d clusters; falling back to KMeans k=%d",
        len(unique_clusters),
        kmeans_fallback_k,
    )
    from sklearn.cluster import KMeans

    k = min(kmeans_fallback_k, max(2, n - 1))
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km_labels = km.fit_predict(embeddings)

    # Treat the 5% farthest-from-its-centroid points as outliers so the -1
    # bucket behaves the same way under the fallback.
    centers = km.cluster_centers_
    dists = np.linalg.norm(embeddings - centers[km_labels], axis=1)
    cutoff = np.quantile(dists, 0.95)
    km_labels = np.where(dists >= cutoff, -1, km_labels)
    return km_labels


def _call_llm_for_label(
    ngrams: list[str],
    samples: list[str],
    api_key: str,
    model: str = DEFAULT_LLM_MODEL,
) -> str:
    """Ask an LLM for a 2-4 word topic label.

    Args:
        ngrams: Top distinctive n-grams from the cluster.
        samples: A handful of sample URLs from the cluster.
        api_key: OpenRouter key.
        model: Chat model id.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://seo-auditor.local",
        "X-Title": "Ultimate SEO Auditor",
    }
    user = (
        "Top distinctive phrases for this group of web pages:\n- "
        + "\n- ".join(ngrams[:10])
        + "\n\nSample URLs:\n- "
        + "\n- ".join(samples[:3])
        + "\n\nReturn a 2-4 word topic label "
        "(Title Case, no punctuation, no quotes). "
        "Examples: 'HVAC Services', 'Plumbing Emergency Repairs', "
        "'Educational Resources'."
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You produce concise topic labels.",
            },
            {"role": "user", "content": user},
        ],
        "max_tokens": 30,
        "temperature": 0.1,
    }
    response = requests.post(
        OPENROUTER_CHAT_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()
    return content.strip("\"' .\n")


def label_clusters(
    ngrams_by_cluster: dict[int, list[str]],
    samples_by_cluster: dict[int, list[str]],
    api_key: str,
    model: str = DEFAULT_LLM_MODEL,
) -> dict[int, str]:
    """Generate a human label for each cluster.

    Falls back to top n-grams when the LLM call fails.
    """
    labels: dict[int, str] = {}
    for cid, ngrams in ngrams_by_cluster.items():
        if not ngrams:
            labels[cid] = f"Cluster {cid}"
            continue
        try:
            labels[cid] = _call_llm_for_label(
                ngrams,
                samples_by_cluster.get(cid, []),
                api_key=api_key,
                model=model,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "cluster: LLM label failed for cluster %s: %s", cid, exc
            )
            labels[cid] = " | ".join(ngrams[:3])
    return labels


def cluster_pages(
    text_df: pd.DataFrame,
    embeddings: np.ndarray,
    api_key: str,
    min_cluster_size: Optional[int] = None,
    llm_model: str = DEFAULT_LLM_MODEL,
) -> dict:
    """One-shot pipeline: cluster -> labels -> site-center + siteRadius.

    Returns a dict with keys:
        cluster_labels      int per URL (-1 for outlier)
        cluster_name_by_id  {cluster_id: human label}
        site_center         1D embedding (mean)
        site_radius         cosine distance per URL
        ngrams_by_cluster   {cluster_id: [top n-grams]}
    """
    if len(text_df) != len(embeddings):
        raise ValueError(
            "cluster_pages: text_df and embeddings must align row-for-row"
        )

    center = compute_site_center(embeddings)
    radius = compute_site_radius(embeddings, center)
    labels = run_clustering(embeddings, min_cluster_size=min_cluster_size)

    ngrams_by_cluster = top_ngrams_per_cluster(text_df["text"], labels)

    samples_by_cluster: dict[int, list[str]] = {}
    for cid in ngrams_by_cluster:
        mask = labels == cid
        sample_urls = text_df.loc[mask, "url"].head(3).tolist()
        samples_by_cluster[cid] = sample_urls

    cluster_names = label_clusters(
        ngrams_by_cluster,
        samples_by_cluster,
        api_key=api_key,
        model=llm_model,
    )

    return {
        "cluster_labels": labels,
        "cluster_name_by_id": cluster_names,
        "site_center": center,
        "site_radius": radius,
        "ngrams_by_cluster": ngrams_by_cluster,
    }
