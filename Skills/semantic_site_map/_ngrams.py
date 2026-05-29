"""TF-IDF n-gram extraction for cluster labels."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


def top_ngrams_per_cluster(
    texts: pd.Series,
    cluster_labels: np.ndarray,
    top_n: int = 10,
    ngram_range: tuple[int, int] = (1, 3),
) -> dict[int, list[str]]:
    """Return the top n-grams for each cluster.

    The -1 (outlier) bucket is ignored.
    """
    unique = sorted({int(c) for c in cluster_labels if c != -1})
    if not unique:
        return {}

    vectorizer = TfidfVectorizer(
        ngram_range=ngram_range,
        stop_words="english",
        max_features=5000,
        min_df=1,
    )
    matrix = vectorizer.fit_transform(texts.astype(str))
    vocab = np.array(vectorizer.get_feature_names_out())

    out: dict[int, list[str]] = {}
    for cid in unique:
        mask = cluster_labels == cid
        if not mask.any():
            continue
        mean_tfidf = matrix[mask].mean(axis=0)
        scores = np.asarray(mean_tfidf).flatten()
        top_idx = np.argsort(scores)[::-1][:top_n]
        out[cid] = [vocab[i] for i in top_idx if scores[i] > 0]
    return out
