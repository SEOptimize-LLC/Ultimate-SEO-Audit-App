"""Batched OpenRouter embeddings with parquet-backed URL-hash cache."""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "openai/text-embedding-3-small"
EMBEDDING_DIM = 1536
DEFAULT_BATCH_SIZE = 100
OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"

# text-embedding-3-small accepts up to 8192 tokens per input.
# At ~4 chars/token that's ~32k chars; we truncate to 24k to leave a
# safety margin for tokens that compress poorly (emoji, multi-byte
# scripts like Arabic, code samples, URLs).
MAX_INPUT_CHARS = 24_000


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _cache_file(cache_dir: Path, model: str) -> Path:
    safe = model.replace("/", "_")
    return cache_dir / f"embeddings_{safe}.parquet"


def _load_cache(cache_dir: Path, model: str) -> dict[str, np.ndarray]:
    path = _cache_file(cache_dir, model)
    if not path.exists():
        return {}
    df = pd.read_parquet(path)
    return {
        row["text_hash"]: np.asarray(row["embedding"])
        for _, row in df.iterrows()
    }


def _save_cache(
    cache_dir: Path, model: str, cache: dict[str, np.ndarray]
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([
        {"text_hash": h, "embedding": list(v)} for h, v in cache.items()
    ])
    df.to_parquet(_cache_file(cache_dir, model), index=False)


def _call_openrouter_embeddings(
    texts: list[str],
    api_key: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = 3,
) -> dict:
    """Call OpenRouter's embeddings endpoint with exponential backoff."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://seo-auditor.local",
        "X-Title": "Ultimate SEO Auditor",
    }
    payload = {"model": model, "input": texts}

    backoff = 2.0
    for attempt in range(max_retries):
        try:
            response = requests.post(
                OPENROUTER_EMBEDDINGS_URL,
                headers=headers,
                json=payload,
                timeout=120,
            )
            if response.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(
                    f"retryable {response.status_code}"
                )
            response.raise_for_status()
            payload = response.json()
            # OpenRouter returns HTTP 200 even when the underlying
            # provider rejected the call. Detect by checking for an
            # `error` key and surface it loudly so we don't silently
            # cache zero embeddings.
            if "error" in payload and payload["error"]:
                err = payload["error"]
                if isinstance(err, dict):
                    msg = err.get("message", str(err))
                else:
                    msg = str(err)
                raise RuntimeError(
                    f"OpenRouter returned 200 with provider error: "
                    f"{msg}"
                )
            return payload
        except (requests.HTTPError, requests.RequestException) as exc:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                "embedder: API error (attempt %d/%d): %s. "
                "Backing off %.1fs",
                attempt + 1,
                max_retries,
                exc,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2
    raise RuntimeError("unreachable")


def embed_pages(
    df: pd.DataFrame,
    cache_dir: Path,
    api_key: str,
    model: str = DEFAULT_MODEL,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> np.ndarray:
    """Embed each row's `text` into a (n_urls, embedding_dim) matrix.

    Args:
        df: DataFrame with columns ["url", "text"], one row per URL.
        cache_dir: Where to read/write the parquet cache.
        api_key: OpenRouter API key.
        model: OpenRouter model id (default text-embedding-3-small).
        batch_size: How many texts per API call.

    Returns:
        Embedding matrix aligned to df's row order.
    """
    if not {"url", "text"}.issubset(df.columns):
        raise ValueError(
            "embed_pages requires DataFrame columns ['url', 'text']"
        )

    cache_dir = Path(cache_dir)
    cache = _load_cache(cache_dir, model)

    # Truncate each text to MAX_INPUT_CHARS BEFORE hashing so the
    # cache key matches the bytes actually sent to the API. Otherwise
    # a long page hashes to one key but is sent truncated, and the
    # reverse lookup at matrix-assembly time misses.
    raw_texts = df["text"].astype(str)
    truncated = [t[:MAX_INPUT_CHARS] for t in raw_texts]
    over_limit = sum(
        1 for t in raw_texts if len(t) > MAX_INPUT_CHARS
    )
    if over_limit:
        logger.info(
            "embedder: %d/%d texts truncated to %d chars "
            "(model token limit)",
            over_limit,
            len(raw_texts),
            MAX_INPUT_CHARS,
        )

    hashes = [_hash_text(t) for t in truncated]
    to_fetch_idx = [i for i, h in enumerate(hashes) if h not in cache]
    to_fetch_texts = [truncated[i] for i in to_fetch_idx]

    if to_fetch_texts:
        logger.info(
            "embedder: %d cached / %d to fetch",
            len(df) - len(to_fetch_texts),
            len(to_fetch_texts),
        )
        for batch_start in range(0, len(to_fetch_texts), batch_size):
            batch = to_fetch_texts[batch_start : batch_start + batch_size]
            response = _call_openrouter_embeddings(
                batch,
                api_key=api_key,
                model=model,
            )
            for item in response.get("data", []):
                idx_in_batch = item["index"]
                global_idx = to_fetch_idx[batch_start + idx_in_batch]
                cache[hashes[global_idx]] = np.asarray(
                    item["embedding"], dtype=np.float32
                )
        _save_cache(cache_dir, model, cache)

    matrix = np.stack([cache[h] for h in hashes])
    return matrix
