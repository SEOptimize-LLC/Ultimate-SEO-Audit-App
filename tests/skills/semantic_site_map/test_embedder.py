"""Tests for embedder.embed_pages."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from Skills.semantic_site_map.embedder import (
    EMBEDDING_DIM,
    _hash_text,
    embed_pages,
)


def _fake_openrouter_response(texts: list[str]) -> dict:
    """Mimic the shape of POST /api/v1/embeddings."""
    return {
        "data": [
            {
                "embedding": [float(i) / 100] * EMBEDDING_DIM,
                "index": i,
            }
            for i, _ in enumerate(texts)
        ],
        "model": "openai/text-embedding-3-small",
        "usage": {
            "prompt_tokens": sum(len(t) for t in texts),
            "total_tokens": 0,
        },
    }


def test_hash_text_is_stable():
    assert _hash_text("abc") == _hash_text("abc")
    assert _hash_text("abc") != _hash_text("abd")


def test_embed_pages_returns_matrix(tmp_path: Path):
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "text": ["body a", "body b"],
    })
    target = "Skills.semantic_site_map.embedder._call_openrouter_embeddings"
    with patch(target) as m:
        m.side_effect = lambda texts, **_: _fake_openrouter_response(texts)
        result = embed_pages(df, cache_dir=tmp_path, api_key="fake")
    assert result.shape == (2, EMBEDDING_DIM)
    assert isinstance(result, np.ndarray)


def test_embed_pages_caches_results(tmp_path: Path):
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "text": ["body a", "body b"],
    })
    target = "Skills.semantic_site_map.embedder._call_openrouter_embeddings"
    with patch(target) as m:
        m.side_effect = lambda texts, **_: _fake_openrouter_response(texts)
        first = embed_pages(df, cache_dir=tmp_path, api_key="fake")
        assert m.call_count == 1
        second = embed_pages(df, cache_dir=tmp_path, api_key="fake")
        # Second call should hit the cache and skip the API.
        assert m.call_count == 1
    np.testing.assert_array_equal(first, second)


def test_embed_pages_only_fetches_uncached(tmp_path: Path):
    df_first = pd.DataFrame({
        "url": ["https://x.com/a"],
        "text": ["body a"],
    })
    df_second = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "text": ["body a", "body b"],
    })
    target = "Skills.semantic_site_map.embedder._call_openrouter_embeddings"
    with patch(target) as m:
        m.side_effect = lambda texts, **_: _fake_openrouter_response(texts)
        embed_pages(df_first, cache_dir=tmp_path, api_key="fake")
        m.reset_mock()
        embed_pages(df_second, cache_dir=tmp_path, api_key="fake")
        # Only the new URL's text should be sent on the second call.
        called_with = m.call_args.args[0]
        assert called_with == ["body b"]


def test_embed_pages_truncates_oversized_text(tmp_path: Path):
    """A text longer than MAX_INPUT_CHARS is truncated before send."""
    from Skills.semantic_site_map.embedder import MAX_INPUT_CHARS

    long_text = "x" * (MAX_INPUT_CHARS + 5000)
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "text": [long_text],
    })
    sent_batches: list[list[str]] = []
    target = "Skills.semantic_site_map.embedder._call_openrouter_embeddings"

    def capture(texts, **_):
        sent_batches.append(list(texts))
        return _fake_openrouter_response(texts)

    with patch(target, side_effect=capture):
        embed_pages(df, cache_dir=tmp_path, api_key="fake")

    assert len(sent_batches) == 1
    sent_text = sent_batches[0][0]
    # Must be exactly the safety cap, not the original length.
    assert len(sent_text) == MAX_INPUT_CHARS


def test_embed_pages_raises_on_provider_error_with_200(
    tmp_path: Path,
):
    """OpenRouter returns 200 with provider error -> we must raise."""
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "text": ["body a"],
    })
    target = "Skills.semantic_site_map.embedder.requests.post"

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "error": {
                    "message": (
                        "HTTP 400: maximum input length is "
                        "8192 tokens."
                    ),
                    "code": 400,
                },
            }

    with patch(target, return_value=FakeResponse()):
        with pytest.raises(RuntimeError, match="provider error"):
            embed_pages(df, cache_dir=tmp_path, api_key="fake")


def test_embed_pages_batches_requests(tmp_path: Path):
    n = 250  # batch size 100 -> 100 + 100 + 50
    df = pd.DataFrame({
        "url": [f"https://x.com/{i}" for i in range(n)],
        "text": [f"body {i}" for i in range(n)],
    })
    target = "Skills.semantic_site_map.embedder._call_openrouter_embeddings"
    with patch(target) as m:
        m.side_effect = lambda texts, **_: _fake_openrouter_response(texts)
        result = embed_pages(
            df,
            cache_dir=tmp_path,
            api_key="fake",
            batch_size=100,
        )
    assert m.call_count == 3
    assert result.shape == (n, EMBEDDING_DIM)
