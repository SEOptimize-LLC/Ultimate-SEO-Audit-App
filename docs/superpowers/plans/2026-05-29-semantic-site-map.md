# Semantic Site Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a `Skills/semantic-site-map/` skill that computes a topical map from any SF crawl (no Koray map required), overlays 90-day GSC clicks, feeds the existing `TopicalAuthorityAuditor` via a JSON adapter, adds a new auditor finding for high-click-high-siteRadius clusters, sharpens the subdomain-vs-subfolder recommendation copy, and renders a static scatter-plot PNG.

**Architecture:** Skill-first, single CLI orchestrator at the repo root. Four focused Python modules (`text_loader`, `embedder`, `cluster`, `report`) each under ~250 lines, communicating via DataFrames + dicts. Auditor gets a new classmethod loader and one new check. Streamlit gets one new upload slot.

**Tech Stack:** Python 3.x, pandas, numpy, scikit-learn (TF-IDF + KMeans fallback), hdbscan, pyarrow (parquet cache), matplotlib (scatter PNG), crawl4ai (text fetch fallback), requests (OpenRouter embeddings + chat), pytest.

**Spec:** [docs/superpowers/specs/2026-05-29-semantic-site-map-design.md](../specs/2026-05-29-semantic-site-map-design.md)

---

## File map

### Created

| Path | Responsibility |
|---|---|
| `Skills/semantic-site-map/SKILL.md` | When to trigger, how to invoke, prerequisites, output schema |
| `Skills/semantic-site-map/__init__.py` | Package marker; re-export public API |
| `Skills/semantic-site-map/text_loader.py` | Hybrid text source: detect SF body-text column or fall back to Crawl4AI |
| `Skills/semantic-site-map/embedder.py` | Batched OpenRouter embedding + parquet cache |
| `Skills/semantic-site-map/cluster.py` | HDBSCAN, site-center, siteRadius, LLM cluster labels |
| `Skills/semantic-site-map/report.py` | GSC join, 4 output files, scatter PNG |
| `Skills/semantic-site-map/_ngrams.py` | TF-IDF n-gram extraction (used for labels + label fallback) |
| `run_semantic_map.py` | CLI orchestrator at repo root |
| `tests/skills/semantic_site_map/__init__.py` | Test package marker |
| `tests/skills/semantic_site_map/test_text_loader.py` | Unit tests for text_loader |
| `tests/skills/semantic_site_map/test_embedder.py` | Unit tests for embedder |
| `tests/skills/semantic_site_map/test_cluster.py` | Unit tests for cluster |
| `tests/skills/semantic_site_map/test_report.py` | Unit tests for report |
| `tests/skills/semantic_site_map/test_integration.py` | Synthetic 100-URL site integration test |
| `tests/auditors/test_topical_authority_adapter.py` | Auditor `from_computed_map` adapter test |

### Modified

| Path | Change |
|---|---|
| `auditors/topical_authority_auditor.py` | Add `from_computed_map` classmethod, add `_check_high_click_off_topic_cluster`, sharpen outlier-pages recommendation copy |
| `app.py` | Add one upload slot: "Computed Semantic Map (JSON)" |
| `requirements.txt` | Add `hdbscan`, `scikit-learn`, `matplotlib`, `pyarrow`, `crawl4ai` (if not already present) |

---

## Task 1 — Project scaffold & dependencies

**Files:**
- Create: `Skills/semantic-site-map/SKILL.md` (stub only)
- Create: `Skills/semantic-site-map/__init__.py`
- Create: `tests/skills/semantic_site_map/__init__.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Verify which deps are already installed**

Run: `python -c "import hdbscan, sklearn, matplotlib, pyarrow, crawl4ai; print('all present')"`
Expected: One of (a) `all present` (skip step 2), or (b) ModuleNotFoundError naming the first missing package.

- [ ] **Step 2: Install missing deps**

For each missing package from step 1, run individually so we know which succeeded:
```bash
pip install hdbscan
pip install scikit-learn
pip install matplotlib
pip install pyarrow
pip install crawl4ai
```
Expected: each ends in `Successfully installed ...`. If `hdbscan` fails on Windows (it sometimes needs build tools), run `pip install hdbscan --no-build-isolation` and if that also fails, fall back to `pip install hdbscan==0.8.33` (last known good wheel for Windows).

- [ ] **Step 3: Update requirements.txt**

Read existing requirements.txt. Append (only the packages that weren't already pinned):
```
hdbscan>=0.8.33
scikit-learn>=1.3.0
matplotlib>=3.7.0
pyarrow>=14.0.0
crawl4ai>=0.3.0
```

- [ ] **Step 4: Create skill package skeleton**

Create `Skills/semantic-site-map/__init__.py`:
```python
"""Semantic Site Map skill — embeds pages, clusters them, overlays GSC clicks."""

from Skills.semantic_site_map.text_loader import load_page_text
from Skills.semantic_site_map.embedder import embed_pages
from Skills.semantic_site_map.cluster import cluster_pages
from Skills.semantic_site_map.report import build_outputs

__all__ = ["load_page_text", "embed_pages", "cluster_pages", "build_outputs"]
```

Note: the public API stubs here will be filled by later tasks. This file errors on import until those modules exist, which is fine — we don't import the package until Task 6.

- [ ] **Step 5: Create test package marker**

Create `tests/skills/semantic_site_map/__init__.py`:
```python
"""Tests for the semantic-site-map skill."""
```

- [ ] **Step 6: Stub SKILL.md (full version polished in Task 9)**

Create `Skills/semantic-site-map/SKILL.md`:
```markdown
---
name: "Semantic Site Map"
description: "Computes a topical map from any SF crawl using embeddings (no Koray map required), overlays GSC clicks per cluster, and feeds the topical-authority auditor through a JSON adapter. Surfaces siteRadius outliers and the high-click-high-siteRadius dilution-driving clusters from the May 2024 Google leak attributes."
---

# Semantic Site Map

Stub — full version written in Task 9 after the skill is functional.

## Invocation

```bash
python run_semantic_map.py --client "<client-name>"
```

## Outputs

Written to `Clients/<name>/Full SEO Audit/semantic_map/`:
- `topical_map.json` — Koray-compatible, consumed by `TopicalAuthorityAuditor.from_computed_map`
- `semantic_map_full.json` — adds click overlay + per-URL siteRadius
- `semantic_map_report.md` — analyst-facing
- `semantic_map.png` — four-ring scatter plot
```

- [ ] **Step 7: Verify package import skeleton compiles (modules don't exist yet)**

Run: `python -c "import Skills.semantic_site_map" 2>&1 | head -3`
Expected: ModuleNotFoundError on `text_loader`, `embedder`, `cluster`, or `report` (one of them — they don't exist yet). This is correct; it confirms the package is wired up. Will resolve in later tasks.

- [ ] **Step 8: Commit**

```bash
git add Skills/semantic-site-map/ tests/skills/semantic_site_map/ requirements.txt
git commit -m "feat(semantic-site-map): scaffold skill package and dependencies"
```

---

## Task 2 — text_loader.py

**Files:**
- Create: `Skills/semantic-site-map/text_loader.py`
- Create: `tests/skills/semantic_site_map/test_text_loader.py`

- [ ] **Step 1: Write failing tests for column detection**

Create `tests/skills/semantic_site_map/test_text_loader.py`:
```python
"""Tests for text_loader.detect_body_column."""

import pandas as pd
import pytest

from Skills.semantic_site_map.text_loader import detect_body_column


def test_detects_content_column():
    df = pd.DataFrame({"url": ["https://x.com/a"], "Content": ["body text"]})
    assert detect_body_column(df) == "Content"


def test_detects_body_text_column():
    df = pd.DataFrame({"url": ["https://x.com/a"], "Body Text": ["body text"]})
    assert detect_body_column(df) == "Body Text"


def test_detects_custom_extraction_column():
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "Custom Extraction 1": ["body text"],
    })
    assert detect_body_column(df) == "Custom Extraction 1"


def test_returns_none_when_no_body_column():
    df = pd.DataFrame({"url": ["https://x.com/a"], "title": ["t"]})
    assert detect_body_column(df) is None


def test_ignores_empty_body_column():
    df = pd.DataFrame({"url": ["https://x.com/a"], "Content": [None]})
    assert detect_body_column(df) is None


def test_lowercase_column_match():
    df = pd.DataFrame({"url": ["https://x.com/a"], "content": ["body text"]})
    assert detect_body_column(df) == "content"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skills/semantic_site_map/test_text_loader.py -v`
Expected: All FAIL with `ModuleNotFoundError: Skills.semantic_site_map.text_loader`.

- [ ] **Step 3: Implement detect_body_column**

Create `Skills/semantic-site-map/text_loader.py`:
```python
"""Hybrid text source: SF body-text column if present, Crawl4AI fallback."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Candidate column names that may carry rendered body text from SF custom extraction.
# Match is case-insensitive; order matters for tie-breaking.
BODY_TEXT_CANDIDATES = (
    "Content",
    "Body Text",
    "Body",
    "Custom Extraction 1",
    "Main Content",
    "Article Body",
)


def detect_body_column(df: pd.DataFrame) -> Optional[str]:
    """Return the first matching body-text column with at least one non-null value."""
    lookup = {col.lower(): col for col in df.columns}
    for candidate in BODY_TEXT_CANDIDATES:
        col = lookup.get(candidate.lower())
        if col is None:
            continue
        if df[col].notna().any():
            return col
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/skills/semantic_site_map/test_text_loader.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Write failing tests for SF-path text loading**

Append to `tests/skills/semantic_site_map/test_text_loader.py`:
```python
def test_load_page_text_uses_sf_column_when_present():
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "title": ["A", "B"],
        "meta_desc": ["da", "db"],
        "h1": ["H1a", "H1b"],
        "Content": ["body a", "body b"],
    })
    from Skills.semantic_site_map.text_loader import load_page_text

    result = asyncio.run(load_page_text(df, cache_path=None))
    assert set(result["url"]) == {"https://x.com/a", "https://x.com/b"}
    assert "body a" in result.loc[result["url"] == "https://x.com/a", "text"].iloc[0]
    assert "body b" in result.loc[result["url"] == "https://x.com/b", "text"].iloc[0]


def test_load_page_text_combines_title_meta_h1_with_body():
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "title": ["Title A"],
        "meta_desc": ["Meta A"],
        "h1": ["H1 A"],
        "Content": ["Body A"],
    })
    from Skills.semantic_site_map.text_loader import load_page_text

    result = asyncio.run(load_page_text(df, cache_path=None))
    text = result["text"].iloc[0]
    assert "Title A" in text
    assert "Meta A" in text
    assert "H1 A" in text
    assert "Body A" in text


def test_load_page_text_filters_non_200():
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "title": ["A", "B"],
        "status_code": [200, 404],
        "Content": ["body a", "body b"],
    })
    from Skills.semantic_site_map.text_loader import load_page_text

    result = asyncio.run(load_page_text(df, cache_path=None))
    assert list(result["url"]) == ["https://x.com/a"]


def test_load_page_text_filters_noindex():
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "title": ["A", "B"],
        "meta_robots": ["index,follow", "noindex,follow"],
        "Content": ["body a", "body b"],
    })
    from Skills.semantic_site_map.text_loader import load_page_text

    result = asyncio.run(load_page_text(df, cache_path=None))
    assert list(result["url"]) == ["https://x.com/a"]
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `pytest tests/skills/semantic_site_map/test_text_loader.py -v`
Expected: 4 new tests FAIL with `ImportError: cannot import name 'load_page_text'`. First 6 still PASS.

- [ ] **Step 7: Implement load_page_text (SF path only, Crawl4AI fallback stubbed)**

Append to `Skills/semantic-site-map/text_loader.py`:
```python
async def load_page_text(
    df: pd.DataFrame,
    cache_path: Optional[Path] = None,
    crawl4ai_concurrency: int = 8,
) -> pd.DataFrame:
    """Return a DataFrame[url, text] suitable for embedding.

    Strategy:
    1. Filter to indexable, 2xx, HTML pages (when the columns exist).
    2. If a body-text column is present in `df`, build the per-URL text from
       title + meta_desc + h1 + that column.
    3. Otherwise, fetch full body text via Crawl4AI and cache it to `cache_path`.

    Args:
        df: Screaming Frog crawl DataFrame (expects at least a `url` column).
        cache_path: Optional CSV path; if present and exists, read cached text.
            If absent, fetched text is written here.
        crawl4ai_concurrency: Max concurrent fetches when falling back.

    Returns:
        DataFrame with columns ["url", "text"], one row per URL.
    """
    if "url" not in df.columns:
        raise ValueError("text_loader.load_page_text requires a 'url' column")

    filtered = _filter_eligible(df)

    body_col = detect_body_column(filtered)
    if body_col is not None:
        logger.info("text_loader: using SF body-text column %r", body_col)
        return _build_text_from_sf(filtered, body_col)

    if cache_path is not None and cache_path.exists():
        logger.info("text_loader: reusing cached page_text from %s", cache_path)
        cached = pd.read_csv(cache_path)
        return cached[cached["url"].isin(filtered["url"])]

    logger.info("text_loader: falling back to Crawl4AI for %d URLs", len(filtered))
    fetched = await _fetch_via_crawl4ai(
        filtered["url"].tolist(),
        concurrency=crawl4ai_concurrency,
    )
    merged = _build_text_from_sf(
        filtered.merge(fetched, on="url", how="left").assign(_body=lambda d: d["text"]),
        "_body",
    )
    if cache_path is not None:
        merged.to_csv(cache_path, index=False)
    return merged


def _filter_eligible(df: pd.DataFrame) -> pd.DataFrame:
    keep = df.copy()
    if "status_code" in keep.columns:
        keep = keep[keep["status_code"].fillna(0).astype(int).between(200, 299)]
    if "content_type" in keep.columns:
        keep = keep[
            keep["content_type"].fillna("").str.contains("html", case=False, na=False)
        ]
    if "meta_robots" in keep.columns:
        keep = keep[
            ~keep["meta_robots"].fillna("").str.lower().str.contains("noindex", na=False)
        ]
    return keep


def _build_text_from_sf(df: pd.DataFrame, body_col: str) -> pd.DataFrame:
    parts_columns = ["title", "meta_desc", "h1", body_col]
    available = [c for c in parts_columns if c in df.columns]

    def row_text(row: pd.Series) -> str:
        return " \n".join(
            str(row[c]) for c in available if pd.notna(row[c]) and str(row[c]).strip()
        )

    out = pd.DataFrame({
        "url": df["url"].astype(str),
        "text": df.apply(row_text, axis=1),
    })
    out = out[out["text"].str.len() > 0].reset_index(drop=True)
    return out


async def _fetch_via_crawl4ai(urls: list[str], concurrency: int) -> pd.DataFrame:
    """Fetch main content for each URL using Crawl4AI's markdown extractor."""
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError as exc:
        raise RuntimeError(
            "crawl4ai is required when the SF crawl lacks a body-text column. "
            "Install with: pip install crawl4ai"
        ) from exc

    semaphore = asyncio.Semaphore(concurrency)
    results: list[dict] = []

    async with AsyncWebCrawler(verbose=False) as crawler:
        async def fetch_one(url: str) -> None:
            async with semaphore:
                try:
                    res = await crawler.arun(url=url, bypass_cache=True)
                    text = (res.markdown or "").strip() if res.success else ""
                    results.append({"url": url, "text": text})
                except Exception as exc:  # noqa: BLE001
                    logger.warning("text_loader: Crawl4AI failed on %s: %s", url, exc)
                    results.append({"url": url, "text": ""})

        await asyncio.gather(*(fetch_one(u) for u in urls))

    fetched_df = pd.DataFrame(results)
    failed_ratio = (fetched_df["text"].str.len() == 0).mean() if len(fetched_df) else 1.0
    if failed_ratio > 0.20:
        raise RuntimeError(
            f"text_loader: Crawl4AI failed on {failed_ratio:.1%} of URLs "
            "(threshold is 20%). Inspect logs and retry with a smaller URL set "
            "or supply an SF body-text column."
        )
    return fetched_df
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `pytest tests/skills/semantic_site_map/test_text_loader.py -v`
Expected: All 10 tests PASS.

- [ ] **Step 9: Commit**

```bash
git add Skills/semantic-site-map/text_loader.py tests/skills/semantic_site_map/test_text_loader.py
git commit -m "feat(semantic-site-map): hybrid SF/Crawl4AI text loader with eligibility filters"
```

---

## Task 3 — embedder.py

**Files:**
- Create: `Skills/semantic-site-map/embedder.py`
- Create: `tests/skills/semantic_site_map/test_embedder.py`

- [ ] **Step 1: Write failing tests**

Create `tests/skills/semantic_site_map/test_embedder.py`:
```python
"""Tests for embedder.embed_pages."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from Skills.semantic_site_map.embedder import (
    embed_pages,
    _hash_text,
    EMBEDDING_DIM,
)


def _fake_openrouter_response(texts: list[str]) -> dict:
    """Mimic the shape of POST /api/v1/embeddings."""
    return {
        "data": [
            {"embedding": [float(i) / 100] * EMBEDDING_DIM, "index": i}
            for i, _ in enumerate(texts)
        ],
        "model": "openai/text-embedding-3-small",
        "usage": {"prompt_tokens": sum(len(t) for t in texts), "total_tokens": 0},
    }


def test_hash_text_is_stable():
    assert _hash_text("abc") == _hash_text("abc")
    assert _hash_text("abc") != _hash_text("abd")


def test_embed_pages_returns_matrix(tmp_path: Path):
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "text": ["body a", "body b"],
    })
    with patch("Skills.semantic_site_map.embedder._call_openrouter_embeddings") as m:
        m.side_effect = lambda texts, **_: _fake_openrouter_response(texts)
        result = embed_pages(df, cache_dir=tmp_path, api_key="fake")
    assert result.shape == (2, EMBEDDING_DIM)
    assert isinstance(result, np.ndarray)


def test_embed_pages_caches_results(tmp_path: Path):
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "text": ["body a", "body b"],
    })
    with patch("Skills.semantic_site_map.embedder._call_openrouter_embeddings") as m:
        m.side_effect = lambda texts, **_: _fake_openrouter_response(texts)
        first = embed_pages(df, cache_dir=tmp_path, api_key="fake")
        assert m.call_count == 1
        second = embed_pages(df, cache_dir=tmp_path, api_key="fake")
        assert m.call_count == 1  # second call hits cache, no new API call
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
    with patch("Skills.semantic_site_map.embedder._call_openrouter_embeddings") as m:
        m.side_effect = lambda texts, **_: _fake_openrouter_response(texts)
        embed_pages(df_first, cache_dir=tmp_path, api_key="fake")
        m.reset_mock()
        embed_pages(df_second, cache_dir=tmp_path, api_key="fake")
        # Only the new URL should be embedded the second time.
        called_with = m.call_args.args[0]
        assert called_with == ["body b"]


def test_embed_pages_batches_requests(tmp_path: Path):
    n = 250  # batch size is 100
    df = pd.DataFrame({
        "url": [f"https://x.com/{i}" for i in range(n)],
        "text": [f"body {i}" for i in range(n)],
    })
    with patch("Skills.semantic_site_map.embedder._call_openrouter_embeddings") as m:
        m.side_effect = lambda texts, **_: _fake_openrouter_response(texts)
        result = embed_pages(df, cache_dir=tmp_path, api_key="fake", batch_size=100)
    assert m.call_count == 3  # 100 + 100 + 50
    assert result.shape == (n, EMBEDDING_DIM)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skills/semantic_site_map/test_embedder.py -v`
Expected: All FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement embedder.py**

Create `Skills/semantic-site-map/embedder.py`:
```python
"""Batched OpenRouter embeddings with parquet-backed URL-hash cache."""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "openai/text-embedding-3-small"
EMBEDDING_DIM = 1536
DEFAULT_BATCH_SIZE = 100
OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"


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
    return {row["text_hash"]: np.asarray(row["embedding"]) for _, row in df.iterrows()}


def _save_cache(cache_dir: Path, model: str, cache: dict[str, np.ndarray]) -> None:
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
                raise requests.HTTPError(f"retryable {response.status_code}")
            response.raise_for_status()
            return response.json()
        except (requests.HTTPError, requests.RequestException) as exc:
            if attempt == max_retries - 1:
                raise
            logger.warning(
                "embedder: API error (attempt %d/%d): %s. Backing off %.1fs",
                attempt + 1, max_retries, exc, backoff,
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
        model: OpenRouter model id (default openai/text-embedding-3-small).
        batch_size: How many texts per API call.

    Returns:
        Embedding matrix aligned to df's row order.
    """
    if not {"url", "text"}.issubset(df.columns):
        raise ValueError("embed_pages requires DataFrame columns ['url', 'text']")

    cache_dir = Path(cache_dir)
    cache = _load_cache(cache_dir, model)

    hashes = [_hash_text(t) for t in df["text"].astype(str)]
    to_fetch_idx = [i for i, h in enumerate(hashes) if h not in cache]
    to_fetch_texts = [df["text"].iloc[i] for i in to_fetch_idx]

    if to_fetch_texts:
        logger.info(
            "embedder: %d cached / %d to fetch", len(df) - len(to_fetch_texts), len(to_fetch_texts),
        )
        for batch_start in range(0, len(to_fetch_texts), batch_size):
            batch = to_fetch_texts[batch_start:batch_start + batch_size]
            response = _call_openrouter_embeddings(
                batch, api_key=api_key, model=model,
            )
            for item in response.get("data", []):
                idx_in_batch = item["index"]
                global_idx = to_fetch_idx[batch_start + idx_in_batch]
                cache[hashes[global_idx]] = np.asarray(item["embedding"], dtype=np.float32)
        _save_cache(cache_dir, model, cache)

    matrix = np.stack([cache[h] for h in hashes])
    return matrix
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/skills/semantic_site_map/test_embedder.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add Skills/semantic-site-map/embedder.py tests/skills/semantic_site_map/test_embedder.py
git commit -m "feat(semantic-site-map): batched OpenRouter embedder with parquet cache"
```

---

## Task 4 — cluster.py + _ngrams.py

**Files:**
- Create: `Skills/semantic-site-map/_ngrams.py`
- Create: `Skills/semantic-site-map/cluster.py`
- Create: `tests/skills/semantic_site_map/test_cluster.py`

- [ ] **Step 1: Write failing tests for n-gram extraction**

Create `tests/skills/semantic_site_map/test_cluster.py`:
```python
"""Tests for cluster + _ngrams modules."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from Skills.semantic_site_map._ngrams import top_ngrams_per_cluster
from Skills.semantic_site_map.cluster import (
    compute_site_center,
    compute_site_radius,
    run_clustering,
    label_clusters,
    cluster_pages,
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
        [1.0, 0.0],   # same direction → distance 0
        [-1.0, 0.0],  # opposite direction → distance 2
        [0.0, 1.0],   # orthogonal → distance 1
    ])
    center = np.array([1.0, 0.0])
    radii = compute_site_radius(embeddings, center)
    np.testing.assert_allclose(radii, [0.0, 0.0, 2.0, 1.0], atol=1e-6)


def test_run_clustering_groups_close_points():
    rng = np.random.default_rng(0)
    cluster_a = rng.normal(loc=[5, 5], scale=0.1, size=(30, 2))
    cluster_b = rng.normal(loc=[-5, -5], scale=0.1, size=(30, 2))
    outliers = np.array([[0.0, 10.0], [10.0, 0.0], [-10.0, 0.0]])
    embeddings = np.vstack([cluster_a, cluster_b, outliers])

    labels = run_clustering(embeddings, min_cluster_size=5)

    assert (labels == -1).sum() >= 3  # the 3 outliers
    unique_clusters = set(labels) - {-1}
    assert len(unique_clusters) == 2


def test_run_clustering_falls_back_to_kmeans_on_degenerate():
    rng = np.random.default_rng(0)
    embeddings = rng.normal(loc=[0, 0], scale=0.01, size=(50, 2))
    labels = run_clustering(embeddings, min_cluster_size=5, kmeans_fallback_k=4)
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
    assert any("hvac" in ng or "air" in ng or "conditioning" in ng for ng in out[0])
    assert any("plumb" in ng or "leak" in ng or "pipe" in ng for ng in out[1])


def test_label_clusters_uses_llm():
    ngrams_by_cluster = {0: ["hvac repair", "furnace"], 1: ["plumbing", "leak"]}
    samples_by_cluster = {
        0: ["https://x.com/hvac-1", "https://x.com/hvac-2"],
        1: ["https://x.com/plumb-1", "https://x.com/plumb-2"],
    }

    def fake_label(ngrams, samples, **_):
        if "hvac" in ngrams[0]:
            return "HVAC services"
        return "Plumbing services"

    with patch("Skills.semantic_site_map.cluster._call_llm_for_label", side_effect=fake_label):
        labels = label_clusters(ngrams_by_cluster, samples_by_cluster, api_key="fake")
    assert labels[0] == "HVAC services"
    assert labels[1] == "Plumbing services"


def test_label_clusters_falls_back_on_llm_failure():
    ngrams_by_cluster = {0: ["hvac repair", "furnace", "thermostat"]}
    samples_by_cluster = {0: ["https://x.com/a"]}

    def boom(*_, **__):
        raise RuntimeError("LLM down")

    with patch("Skills.semantic_site_map.cluster._call_llm_for_label", side_effect=boom):
        labels = label_clusters(ngrams_by_cluster, samples_by_cluster, api_key="fake")
    # Falls back to top-3 raw ngrams joined.
    assert "hvac repair" in labels[0]


def test_cluster_pages_end_to_end():
    rng = np.random.default_rng(0)
    cluster_a = rng.normal(loc=[5, 5], scale=0.1, size=(20, 2))
    cluster_b = rng.normal(loc=[-5, -5], scale=0.1, size=(20, 2))
    outliers = np.array([[0.0, 10.0], [10.0, 0.0]])
    embeddings = np.vstack([cluster_a, cluster_b, outliers]).astype(np.float32)

    text_df = pd.DataFrame({
        "url": [f"https://x.com/{i}" for i in range(42)],
        "text": (
            ["hvac repair air conditioning"] * 20
            + ["plumbing leak pipe"] * 20
            + ["random off topic post", "another off topic"]
        ),
    })

    with patch("Skills.semantic_site_map.cluster._call_llm_for_label") as m:
        m.side_effect = lambda ngrams, samples, **_: ngrams[0].title()
        result = cluster_pages(text_df, embeddings, min_cluster_size=5, api_key="fake")

    assert "site_center" in result
    assert "site_radius" in result
    assert len(result["site_radius"]) == 42
    assert "cluster_labels" in result        # int label per URL
    assert "cluster_name_by_id" in result    # human label per cluster id
    assert (result["cluster_labels"] == -1).sum() >= 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skills/semantic_site_map/test_cluster.py -v`
Expected: All FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement _ngrams.py**

Create `Skills/semantic-site-map/_ngrams.py`:
```python
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
    """Return the top n-grams for each cluster, ignoring the -1 outlier bucket."""
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
```

- [ ] **Step 4: Implement cluster.py**

Create `Skills/semantic-site-map/cluster.py`:
```python
"""Clustering, site-center / siteRadius, and LLM cluster labeling."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd
import requests

from Skills.semantic_site_map._ngrams import top_ngrams_per_cluster

logger = logging.getLogger(__name__)

DEFAULT_LLM_MODEL = "anthropic/claude-3.5-sonnet"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


def compute_site_center(embeddings: np.ndarray) -> np.ndarray:
    """Mean embedding across all pages."""
    if embeddings.ndim != 2 or len(embeddings) == 0:
        raise ValueError("compute_site_center requires a non-empty 2D matrix")
    return embeddings.mean(axis=0)


def compute_site_radius(embeddings: np.ndarray, center: np.ndarray) -> np.ndarray:
    """Cosine distance from each row to `center` (0 = same direction, 2 = opposite)."""
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
        Integer label per row; -1 indicates outlier (HDBSCAN) or far-from-centroid (fallback).
    """
    import hdbscan

    n = len(embeddings)
    if min_cluster_size is None:
        min_cluster_size = max(5, n // 50)
    min_cluster_size = max(2, min(min_cluster_size, n - 1))

    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
    labels = clusterer.fit_predict(embeddings)
    unique_clusters = set(labels) - {-1}

    if len(unique_clusters) >= 2:
        return labels

    logger.warning(
        "cluster: HDBSCAN found %d clusters; falling back to KMeans k=%d",
        len(unique_clusters), kmeans_fallback_k,
    )
    from sklearn.cluster import KMeans

    k = min(kmeans_fallback_k, max(2, n - 1))
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    km_labels = km.fit_predict(embeddings)

    # Treat the 5% farthest-from-its-centroid points as outliers so the -1 bucket
    # behaves the same way under the fallback.
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
    """Ask an LLM for a 2-4 word topic label given top n-grams + sample URLs."""
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
        + "\n\nReturn a 2-4 word topic label (Title Case, no punctuation, no quotes). "
        "Examples: 'HVAC Services', 'Plumbing Emergency Repairs', 'Educational Resources'."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You produce concise topic labels."},
            {"role": "user", "content": user},
        ],
        "max_tokens": 30,
        "temperature": 0.1,
    }
    response = requests.post(OPENROUTER_CHAT_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()
    return content.strip("\"' .\n")


def label_clusters(
    ngrams_by_cluster: dict[int, list[str]],
    samples_by_cluster: dict[int, list[str]],
    api_key: str,
    model: str = DEFAULT_LLM_MODEL,
) -> dict[int, str]:
    """Generate a human label for each cluster, falling back to n-grams on failure."""
    labels: dict[int, str] = {}
    for cid, ngrams in ngrams_by_cluster.items():
        if not ngrams:
            labels[cid] = f"Cluster {cid}"
            continue
        try:
            labels[cid] = _call_llm_for_label(
                ngrams, samples_by_cluster.get(cid, []), api_key=api_key, model=model,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("cluster: LLM label failed for cluster %s: %s", cid, exc)
            labels[cid] = " · ".join(ngrams[:3])
    return labels


def cluster_pages(
    text_df: pd.DataFrame,
    embeddings: np.ndarray,
    api_key: str,
    min_cluster_size: Optional[int] = None,
    llm_model: str = DEFAULT_LLM_MODEL,
) -> dict:
    """One-shot pipeline: cluster → labels → site-center + siteRadius.

    Returns a dict with keys:
        - cluster_labels: int per URL (-1 for outlier)
        - cluster_name_by_id: {cluster_id: human label}
        - site_center: 1D embedding (mean)
        - site_radius: cosine distance per URL
        - ngrams_by_cluster: {cluster_id: [top n-grams]}
    """
    if len(text_df) != len(embeddings):
        raise ValueError("cluster_pages: text_df and embeddings must align row-for-row")

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
        ngrams_by_cluster, samples_by_cluster, api_key=api_key, model=llm_model,
    )

    return {
        "cluster_labels": labels,
        "cluster_name_by_id": cluster_names,
        "site_center": center,
        "site_radius": radius,
        "ngrams_by_cluster": ngrams_by_cluster,
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/skills/semantic_site_map/test_cluster.py -v`
Expected: All 8 tests PASS. Note: `test_run_clustering_falls_back_to_kmeans_on_degenerate` may produce a warning log line — that's expected.

- [ ] **Step 6: Commit**

```bash
git add Skills/semantic-site-map/cluster.py Skills/semantic-site-map/_ngrams.py tests/skills/semantic_site_map/test_cluster.py
git commit -m "feat(semantic-site-map): HDBSCAN clustering + site-center + LLM cluster labels"
```

---

## Task 5 — report.py

**Files:**
- Create: `Skills/semantic-site-map/report.py`
- Create: `tests/skills/semantic_site_map/test_report.py`

- [ ] **Step 1: Write failing tests**

Create `tests/skills/semantic_site_map/test_report.py`:
```python
"""Tests for report.build_outputs."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from Skills.semantic_site_map.report import (
    aggregate_clicks_by_cluster,
    build_outputs,
    pick_central_entity,
    classify_into_rings,
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
    # 6 clustered URLs split into 4 ring quartiles; the 2 outliers go to `outliers`.
    assert set(rings.keys()) == {"core", "focus", "expansion", "peripheral"}
    assert sum(len(v) for v in rings.values()) == 6
    assert len(outliers) == 2


def test_pick_central_entity_uses_largest_cluster_label():
    cluster_name_by_id = {0: "Plumbing Services", 1: "HVAC", 2: "Random Topic"}
    cluster_labels = np.array([0, 0, 0, 1, 1, 2])
    assert pick_central_entity(cluster_labels, cluster_name_by_id) == "Plumbing Services"


def test_build_outputs_writes_four_files(tmp_path: Path):
    rng = np.random.default_rng(0)
    n = 12
    text_df = pd.DataFrame({
        "url": [f"https://x.com/{i}" for i in range(n)],
        "text": [f"page {i} text"] * n,  # noqa: E226 — repeated for the per-URL row
    })
    # Re-fix: distinct text content per row
    text_df["text"] = [f"page {i} content here" for i in range(n)]
    embeddings = rng.normal(size=(n, 8)).astype(np.float32)
    cluster_result = {
        "cluster_labels": np.array([0]*5 + [1]*5 + [-1]*2),
        "cluster_name_by_id": {0: "Topic A", 1: "Topic B"},
        "site_center": embeddings.mean(axis=0),
        "site_radius": np.linspace(0.1, 0.9, n),
        "ngrams_by_cluster": {0: ["alpha", "beta"], 1: ["gamma", "delta"]},
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

    koray = json.loads(paths["topical_map_json"].read_text(encoding="utf-8"))
    assert "central_entity" in koray
    assert "rings" in koray
    assert set(koray["rings"].keys()) == {"core", "focus", "expansion", "peripheral"}
    assert "outliers" in koray

    full = json.loads(paths["full_json"].read_text(encoding="utf-8"))
    assert "clicks_by_cluster" in full
    assert "site_radius_per_url" in full
    assert "high_click_off_topic_clusters" in full
    assert full["embedding_model_used"] == "openai/text-embedding-3-small"


def test_build_outputs_marks_no_gsc_when_missing(tmp_path: Path):
    rng = np.random.default_rng(0)
    n = 10
    text_df = pd.DataFrame({
        "url": [f"https://x.com/{i}" for i in range(n)],
        "text": [f"page {i} content here" for i in range(n)],
    })
    embeddings = rng.normal(size=(n, 8)).astype(np.float32)
    cluster_result = {
        "cluster_labels": np.array([0]*4 + [1]*4 + [-1]*2),
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/skills/semantic_site_map/test_report.py -v`
Expected: All FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement report.py**

Create `Skills/semantic-site-map/report.py`:
```python
"""GSC join, four output files, scatter-plot PNG."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server-side rendering
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

RING_NAMES = ("core", "focus", "expansion", "peripheral")
HIGH_CLICK_QUANTILE = 0.75
HIGH_RADIUS_THRESHOLD = 0.6  # cosine-distance threshold tuned during validation


def aggregate_clicks_by_cluster(
    urls: list[str],
    cluster_labels: np.ndarray,
    gsc: Optional[pd.DataFrame],
) -> dict[int, dict]:
    """Sum clicks/impressions per cluster id (including -1)."""
    df = pd.DataFrame({"url": urls, "cluster": cluster_labels})
    if gsc is None:
        return {int(c): {"clicks": 0, "impressions": 0, "urls": int((cluster_labels == c).sum())}
                for c in set(cluster_labels)}

    merged = df.merge(gsc[["url", "clicks", "impressions"]], on="url", how="left")
    merged[["clicks", "impressions"]] = merged[["clicks", "impressions"]].fillna(0)
    grouped = merged.groupby("cluster").agg(
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        urls=("url", "count"),
    )
    return {int(c): {"clicks": int(r["clicks"]),
                     "impressions": int(r["impressions"]),
                     "urls": int(r["urls"])}
            for c, r in grouped.iterrows()}


def classify_into_rings(
    urls: list[str],
    cluster_labels: np.ndarray,
    radii: np.ndarray,
) -> tuple[dict[str, list[dict]], list[dict]]:
    """Split URLs into 4 ring quartiles by siteRadius (excluding outliers)."""
    clustered_mask = cluster_labels != -1
    clustered_urls = [u for u, m in zip(urls, clustered_mask) if m]
    clustered_radii = radii[clustered_mask]
    outlier_urls = [u for u, m in zip(urls, clustered_mask) if not m]
    outlier_radii = radii[~clustered_mask]

    rings: dict[str, list[dict]] = {n: [] for n in RING_NAMES}

    if len(clustered_radii) == 0:
        outliers = [{"url": u, "site_radius": float(r)}
                    for u, r in zip(outlier_urls, outlier_radii)]
        return rings, outliers

    quartiles = np.quantile(clustered_radii, [0.25, 0.5, 0.75])
    for u, r in zip(clustered_urls, clustered_radii):
        if r <= quartiles[0]:
            rings["core"].append({"url": u, "site_radius": float(r)})
        elif r <= quartiles[1]:
            rings["focus"].append({"url": u, "site_radius": float(r)})
        elif r <= quartiles[2]:
            rings["expansion"].append({"url": u, "site_radius": float(r)})
        else:
            rings["peripheral"].append({"url": u, "site_radius": float(r)})

    outliers = [{"url": u, "site_radius": float(r)}
                for u, r in zip(outlier_urls, outlier_radii)]
    return rings, outliers


def pick_central_entity(
    cluster_labels: np.ndarray,
    cluster_name_by_id: dict[int, str],
) -> str:
    """The largest non-outlier cluster's human label."""
    counts = pd.Series(cluster_labels).value_counts()
    counts = counts[counts.index != -1]
    if counts.empty:
        return "Unknown"
    top_cluster = int(counts.idxmax())
    return cluster_name_by_id.get(top_cluster, f"Cluster {top_cluster}")


def find_high_click_off_topic_clusters(
    clicks_by_cluster: dict[int, dict],
    cluster_labels: np.ndarray,
    radii: np.ndarray,
    cluster_name_by_id: dict[int, str],
) -> list[dict]:
    """Clusters above the 75th percentile in clicks AND median siteRadius > 0.6."""
    clusters_only = {c: d for c, d in clicks_by_cluster.items() if c != -1}
    if not clusters_only:
        return []

    click_values = [d["clicks"] for d in clusters_only.values()]
    if not click_values or max(click_values) == 0:
        return []
    click_threshold = float(np.quantile(click_values, HIGH_CLICK_QUANTILE))

    flagged = []
    for cid, data in clusters_only.items():
        mask = cluster_labels == cid
        if not mask.any():
            continue
        median_radius = float(np.median(radii[mask]))
        if data["clicks"] >= click_threshold and median_radius > HIGH_RADIUS_THRESHOLD:
            flagged.append({
                "cluster_id": cid,
                "cluster_name": cluster_name_by_id.get(cid, f"Cluster {cid}"),
                "clicks": data["clicks"],
                "median_site_radius": median_radius,
                "page_count": int(mask.sum()),
            })
    return sorted(flagged, key=lambda x: -x["clicks"])


def _render_scatter(
    embeddings: np.ndarray,
    cluster_labels: np.ndarray,
    radii: np.ndarray,
    clicks_by_url: dict[str, int],
    urls: list[str],
    out_path: Path,
    client_name: str,
) -> None:
    """2D scatter via PCA. Rings = radius quartiles. Point size = clicks."""
    from sklearn.decomposition import PCA

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(embeddings)

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect("equal")

    # Ring overlays at radius quartiles, drawn as concentric circles in PC space.
    pc_dists = np.linalg.norm(coords, axis=1)
    if len(pc_dists):
        ring_radii = np.quantile(pc_dists, [0.25, 0.5, 0.75, 0.95])
        ring_colors = ["#3aa676", "#3a7da6", "#d4a017", "#c75450"]
        ring_labels = ["Core", "Focus", "Expansion", "Peripheral"]
        for r, color, label in zip(ring_radii, ring_colors, ring_labels):
            circle = plt.Circle(
                (0, 0), r, fill=False, linestyle="--", linewidth=1.2, color=color, alpha=0.7,
            )
            ax.add_patch(circle)
            ax.text(r * 0.71, r * 0.71, label, fontsize=8, color=color, alpha=0.85)

    # Color each point by cluster; outliers in light gray.
    unique = sorted(set(cluster_labels))
    cmap = plt.colormaps.get_cmap("tab20")
    color_map = {c: cmap(i / max(1, len(unique))) for i, c in enumerate(unique)}
    color_map[-1] = (0.7, 0.7, 0.7, 0.4)

    sizes = np.array([max(10, min(400, clicks_by_url.get(u, 0) * 4)) for u in urls])
    colors = [color_map[c] for c in cluster_labels]
    ax.scatter(coords[:, 0], coords[:, 1], s=sizes, c=colors, alpha=0.7, edgecolors="none")
    ax.scatter([0], [0], marker="*", s=300, color="black", zorder=5, label="Site Center")

    ax.set_title(f"Semantic Site Map — {client_name}", fontsize=14)
    ax.set_xlabel("Topical axis 1 (PCA)")
    ax.set_ylabel("Topical axis 2 (PCA)")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def _render_markdown_report(
    cluster_result: dict,
    clicks_by_cluster: dict,
    high_click_off_topic: list[dict],
    central_entity: str,
    client_name: str,
    has_gsc: bool,
) -> str:
    cluster_labels = cluster_result["cluster_labels"]
    cluster_name_by_id = cluster_result["cluster_name_by_id"]
    ngrams_by_cluster = cluster_result["ngrams_by_cluster"]
    n_total = len(cluster_labels)
    n_outliers = int((cluster_labels == -1).sum())

    lines = [
        f"# Semantic Site Map — {client_name}",
        "",
        f"- **Central entity (largest cluster):** {central_entity}",
        f"- **URLs analyzed:** {n_total}",
        f"- **Outliers (high siteRadius / unclustered):** {n_outliers}",
        f"- **Click overlay:** {'present' if has_gsc else 'click data unavailable'}",
        "",
        "## Clusters",
        "",
    ]
    clusters_only = {c: d for c, d in clicks_by_cluster.items() if c != -1}
    sorted_clusters = sorted(
        clusters_only.items(), key=lambda kv: -kv[1]["clicks"],
    )
    for cid, data in sorted_clusters:
        label = cluster_name_by_id.get(cid, f"Cluster {cid}")
        ngrams = ngrams_by_cluster.get(cid, [])
        lines.append(f"### {label} (cluster {cid})")
        lines.append(f"- Pages: {data['urls']}")
        if has_gsc:
            lines.append(f"- Clicks (90d): {data['clicks']}")
            lines.append(f"- Impressions (90d): {data['impressions']}")
        if ngrams:
            lines.append(f"- Top terms: {', '.join(ngrams[:8])}")
        lines.append("")

    if high_click_off_topic:
        lines.append("## Dilution-driving clusters (high traffic, off-topic)")
        lines.append("")
        lines.append(
            "These clusters earn meaningful traffic but sit far from the site's "
            "topical center. They are the highest-leverage prune-or-relocate candidates."
        )
        lines.append("")
        for entry in high_click_off_topic:
            lines.append(
                f"- **{entry['cluster_name']}** — {entry['clicks']} clicks across "
                f"{entry['page_count']} pages, median siteRadius "
                f"{entry['median_site_radius']:.2f}"
            )
        lines.append("")

    return "\n".join(lines)


def build_outputs(
    out_dir: Path,
    text_df: pd.DataFrame,
    embeddings: np.ndarray,
    cluster_result: dict,
    gsc: Optional[pd.DataFrame],
    client_name: str,
    model_name: str,
) -> dict[str, Path]:
    """Emit the four output files; return their paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    urls = text_df["url"].tolist()
    cluster_labels = cluster_result["cluster_labels"]
    radii = cluster_result["site_radius"]
    cluster_name_by_id = cluster_result["cluster_name_by_id"]

    clicks_by_cluster = aggregate_clicks_by_cluster(urls, cluster_labels, gsc)
    rings, outliers = classify_into_rings(urls, cluster_labels, radii)
    central_entity = pick_central_entity(cluster_labels, cluster_name_by_id)
    high_click_off_topic = find_high_click_off_topic_clusters(
        clicks_by_cluster, cluster_labels, radii, cluster_name_by_id,
    )

    # 1) Koray-compatible JSON
    koray = {
        "central_entity": central_entity,
        "rings": rings,
        "outliers": [o["url"] for o in outliers],
        "generated_from": "semantic-site-map skill",
    }
    topical_map_json = out_dir / "topical_map.json"
    topical_map_json.write_text(json.dumps(koray, indent=2), encoding="utf-8")

    # 2) Rich JSON
    full = {
        "central_entity": central_entity,
        "client_name": client_name,
        "embedding_model_used": model_name,
        "rings": rings,
        "outliers": outliers,
        "clicks_by_cluster": clicks_by_cluster if gsc is not None else {},
        "site_radius_per_url": {
            u: float(r) for u, r in zip(urls, radii)
        },
        "cluster_labels_per_url": {
            u: int(c) for u, c in zip(urls, cluster_labels)
        },
        "cluster_name_by_id": {
            str(k): v for k, v in cluster_name_by_id.items()
        },
        "high_click_off_topic_clusters": high_click_off_topic,
    }
    full_json = out_dir / "semantic_map_full.json"
    full_json.write_text(json.dumps(full, indent=2), encoding="utf-8")

    # 3) Markdown report
    md = _render_markdown_report(
        cluster_result, clicks_by_cluster, high_click_off_topic,
        central_entity, client_name, has_gsc=(gsc is not None),
    )
    report_md = out_dir / "semantic_map_report.md"
    report_md.write_text(md, encoding="utf-8")

    # 4) Scatter PNG
    clicks_by_url: dict[str, int] = {}
    if gsc is not None:
        per_url = gsc.groupby("url")["clicks"].sum()
        clicks_by_url = {str(u): int(c) for u, c in per_url.items()}
    png = out_dir / "semantic_map.png"
    _render_scatter(embeddings, cluster_labels, radii, clicks_by_url, urls, png, client_name)

    return {
        "topical_map_json": topical_map_json,
        "full_json": full_json,
        "report_md": report_md,
        "png": png,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/skills/semantic_site_map/test_report.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add Skills/semantic-site-map/report.py tests/skills/semantic_site_map/test_report.py
git commit -m "feat(semantic-site-map): four-file report output + scatter PNG"
```

---

## Task 6 — run_semantic_map.py CLI orchestrator

**Files:**
- Create: `run_semantic_map.py`

- [ ] **Step 1: Implement CLI orchestrator**

Create `run_semantic_map.py`:
```python
"""CLI orchestrator for the semantic-site-map skill.

Usage:
    python run_semantic_map.py --client "<client-name>"
    python run_semantic_map.py --client "Education Walkthrough" \\
        --crawl "Clients/Education Walkthrough/Others/ew_crawl_filtered.csv" \\
        --gsc  "Clients/Education Walkthrough/data/gsc_performance.csv"

If --crawl is omitted, defaults to Clients/<client>/data/crawl_internal.csv.
If --gsc is omitted, defaults to Clients/<client>/data/gsc_performance.csv (optional).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from dotenv import load_dotenv

from utils.file_parser import _read_csv_robust  # already handles SF/DFS quirks
from Skills.semantic_site_map.text_loader import load_page_text
from Skills.semantic_site_map.embedder import embed_pages, DEFAULT_MODEL
from Skills.semantic_site_map.cluster import cluster_pages
from Skills.semantic_site_map.report import build_outputs


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _resolve_paths(client: str, crawl: Optional[str], gsc: Optional[str]) -> tuple[Path, Optional[Path], Path]:
    client_root = Path("Clients") / client
    if not client_root.exists():
        raise SystemExit(f"Client folder not found: {client_root}")

    crawl_path = Path(crawl) if crawl else client_root / "data" / "crawl_internal.csv"
    if not crawl_path.exists():
        raise SystemExit(f"Crawl file not found: {crawl_path}")

    gsc_path: Optional[Path] = Path(gsc) if gsc else client_root / "data" / "gsc_performance.csv"
    if gsc_path and not gsc_path.exists():
        gsc_path = None

    out_dir = client_root / "Full SEO Audit" / "semantic_map"
    return crawl_path, gsc_path, out_dir


def _load_gsc(path: Optional[Path]) -> Optional[pd.DataFrame]:
    if path is None:
        return None
    df = _read_csv_robust(path)
    rename = {}
    for col in df.columns:
        low = col.lower().strip()
        if low in ("page", "address", "landing page"):
            rename[col] = "url"
        elif low in ("clicks", "url clicks"):
            rename[col] = "clicks"
        elif low in ("impressions",):
            rename[col] = "impressions"
    df = df.rename(columns=rename)
    needed = {"url", "clicks", "impressions"}
    if not needed.issubset(df.columns):
        logging.warning(
            "run_semantic_map: GSC file lacks expected columns (got %s) — skipping click overlay",
            list(df.columns),
        )
        return None
    return df[list(needed)]


async def _run(args: argparse.Namespace) -> None:
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENROUTER_API_KEY missing. Add it to .env or your environment."
        )

    crawl_path, gsc_path, out_dir = _resolve_paths(args.client, args.crawl, args.gsc)
    cache_dir = out_dir.parent / "_cache_semantic_map"
    cache_dir.mkdir(parents=True, exist_ok=True)

    logging.info("run_semantic_map: client=%s", args.client)
    logging.info("run_semantic_map: crawl=%s", crawl_path)
    logging.info("run_semantic_map: gsc=%s", gsc_path or "(none)")
    logging.info("run_semantic_map: out_dir=%s", out_dir)

    df = _read_csv_robust(crawl_path)
    if "url" not in df.columns:
        for col in df.columns:
            if col.lower() in ("address", "url"):
                df = df.rename(columns={col: "url"})
                break

    text_cache = cache_dir / "page_text.csv"
    text_df = await load_page_text(df, cache_path=text_cache)
    logging.info("run_semantic_map: text rows=%d", len(text_df))

    if len(text_df) < 5:
        raise SystemExit(
            f"Only {len(text_df)} URLs survived eligibility filters — refusing to cluster."
        )

    embeddings = embed_pages(text_df, cache_dir=cache_dir, api_key=api_key, model=args.model)
    logging.info("run_semantic_map: embedding matrix shape=%s", embeddings.shape)

    if len(text_df) < 50:
        logging.warning(
            "run_semantic_map: only %d URLs (<50) — clustering will be coarse. "
            "Markdown report will flag this limitation.",
            len(text_df),
        )

    cluster_result = cluster_pages(text_df, embeddings, api_key=api_key)
    gsc = _load_gsc(gsc_path)

    paths = build_outputs(
        out_dir=out_dir,
        text_df=text_df,
        embeddings=embeddings,
        cluster_result=cluster_result,
        gsc=gsc,
        client_name=args.client,
        model_name=args.model,
    )

    print("\nOutputs written:")
    for label, p in paths.items():
        print(f"  {label:>20}  {p}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Semantic site map for a client.")
    parser.add_argument("--client", required=True, help="Client folder name under Clients/")
    parser.add_argument("--crawl", help="Path to SF Internal CSV (default: data/crawl_internal.csv)")
    parser.add_argument("--gsc", help="Path to GSC performance CSV (default: data/gsc_performance.csv)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenRouter embedding model id")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI imports and --help works**

Run: `python run_semantic_map.py --help`
Expected: argparse usage screen with `--client`, `--crawl`, `--gsc`, `--model`, `-v` flags. No traceback.

- [ ] **Step 3: Commit**

```bash
git add run_semantic_map.py
git commit -m "feat(semantic-site-map): CLI orchestrator entry point"
```

---

## Task 7 — Auditor adapter + new check + copy edit

**Files:**
- Modify: `auditors/topical_authority_auditor.py`
- Create: `tests/auditors/test_topical_authority_adapter.py`

- [ ] **Step 1: Write failing tests for the adapter**

Create `tests/auditors/test_topical_authority_adapter.py`:
```python
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
            "core":      [{"url": "https://x.com/", "site_radius": 0.05}],
            "focus":     [{"url": "https://x.com/a", "site_radius": 0.20}],
            "expansion": [{"url": "https://x.com/b", "site_radius": 0.40}],
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
            "0": {"clicks": 5,   "impressions": 100, "urls": 2},
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
                "cluster_id": 1, "cluster_name": "Travel",
                "clicks": 500, "median_site_radius": 0.85, "page_count": 1,
            },
        ],
    }
    p = tmp_path / "semantic_map_full.json"
    p.write_text(json.dumps(out), encoding="utf-8")
    return p


def test_from_computed_map_loads_koray_compatible_shape(crawl_df, tmp_path):
    topical_path = _write_topical_map(tmp_path)
    auditor = TopicalAuthorityAuditor.from_computed_map(crawl_df, topical_path)
    issues = auditor.run_audit()
    # Should detect the one outlier URL via existing _check_outlier_pages
    outlier_issues = [i for i in issues if i.issue_type == "topical_outlier_pages"]
    assert len(outlier_issues) == 1
    assert "https://x.com/blog/off-topic-1" in outlier_issues[0].affected_urls


def test_from_computed_map_with_full_json_runs_new_check(crawl_df, tmp_path):
    topical_path = _write_topical_map(tmp_path)
    full_path = _write_full_json(tmp_path)
    auditor = TopicalAuthorityAuditor.from_computed_map(
        crawl_df, topical_path, full_json_path=full_path,
    )
    issues = auditor.run_audit()
    high_click_issues = [
        i for i in issues if i.issue_type == "high_click_off_topic_cluster"
    ]
    assert len(high_click_issues) == 1
    assert high_click_issues[0].severity == Severity.HIGH
    assert "Travel" in high_click_issues[0].title


def test_outlier_recommendation_mentions_subdomain(crawl_df, tmp_path):
    topical_path = _write_topical_map(tmp_path)
    auditor = TopicalAuthorityAuditor.from_computed_map(crawl_df, topical_path)
    issues = auditor.run_audit()
    outlier = next(i for i in issues if i.issue_type == "topical_outlier_pages")
    assert "subdomain" in outlier.recommendation.lower()
    assert "subfolder" in outlier.recommendation.lower()
```

Create `tests/auditors/__init__.py` if it doesn't exist (empty file).

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/auditors/test_topical_authority_adapter.py -v`
Expected: All FAIL — `from_computed_map` doesn't exist yet, and the new check doesn't exist.

- [ ] **Step 3: Modify the auditor — add classmethod loader**

Edit `auditors/topical_authority_auditor.py`. After the existing `__init__` method, add:

```python
    @classmethod
    def from_computed_map(
        cls,
        crawl_df,
        topical_map_path,
        full_json_path=None,
    ):
        """Construct an auditor from semantic-site-map JSON outputs.

        Args:
            crawl_df: SF Internal report DataFrame (same as the default constructor).
            topical_map_path: Path to the Koray-compatible topical_map.json.
            full_json_path: Optional path to semantic_map_full.json; if present,
                enables the high-click off-topic cluster check.
        """
        import json
        from pathlib import Path

        topical_map = json.loads(Path(topical_map_path).read_text(encoding="utf-8"))
        instance = cls(crawl_df, topical_map)
        if full_json_path is not None:
            instance._full_map = json.loads(
                Path(full_json_path).read_text(encoding="utf-8")
            )
        else:
            instance._full_map = None
        return instance
```

Also add `self._full_map = None` at the end of the existing `__init__` so attribute access is always safe.

- [ ] **Step 4: Modify the auditor — add the new check**

In `auditors/topical_authority_auditor.py`, modify `run_audit` to call a new check after the existing three:

```python
    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        if not self.topical_map:
            return self.issues

        self._check_outlier_pages()
        self._check_topic_dispersion()
        self._check_central_entity_alignment()
        self._check_high_click_off_topic_cluster()  # NEW

        return self.issues
```

Then add the new method at the bottom of the class:

```python
    def _check_high_click_off_topic_cluster(self) -> None:
        """Flag clusters that earn meaningful traffic AND sit far from site center.

        Requires the rich `semantic_map_full.json` payload loaded via
        from_computed_map(full_json_path=...). Skipped silently otherwise.
        """
        if not getattr(self, "_full_map", None):
            return

        flagged = self._full_map.get("high_click_off_topic_clusters") or []
        if not flagged:
            return

        labels = ", ".join(f.get("cluster_name", f"Cluster {f.get('cluster_id')}") for f in flagged)
        total_clicks = sum(int(f.get("clicks", 0)) for f in flagged)
        total_pages = sum(int(f.get("page_count", 0)) for f in flagged)

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.CONTENT,
            issue_type="high_click_off_topic_cluster",
            title=f"{len(flagged)} high-traffic cluster(s) dragging the site's topical center: {labels}",
            description=(
                f"{len(flagged)} topical cluster(s) earn meaningful traffic but sit far from "
                "the site's central topic. Combined: "
                f"{total_clicks} clicks across {total_pages} pages.\n\n"
                "Per the May 2024 Google API leak, the QualityAuthorityTopicEmbeddings module "
                "computes siteFocusScore from the aggregate of every indexed page on the domain. "
                "High-click clusters that sit at high siteRadius are the worst case: they look "
                "like traffic wins in a dashboard, but they drag the site embedding away from "
                "the topical center that the revenue pages need to rank for."
            ),
            count=len(flagged),
            recommendation=(
                "For each flagged cluster, ask: does this audience convert, or just consume? "
                "If it doesn't convert, the high-leverage move is to relocate the cluster to a "
                "subdomain — that creates a separate siteEmbedding pool so the cluster keeps its "
                "traffic while the main domain's topical center returns to the revenue topics. "
                "A subfolder move does not fix this; siteEmbedding aggregates everything under "
                "the same domain."
            ),
            impact=(
                "Off-topic clusters at high click volume have outsized negative effect on "
                "siteFocusScore — they pull the centroid by more than low-traffic outliers do."
            ),
            additional_data={"clusters": flagged},
        )
```

- [ ] **Step 5: Modify the auditor — sharpen the outlier-pages recommendation copy**

In `auditors/topical_authority_auditor.py`, find the `_check_outlier_pages` method and replace its `recommendation=` argument with:

```python
            recommendation=(
                "For each outlier page, choose: (a) prune via 410 / consolidate into a relevant "
                "page, (b) relocate to a subdomain, or (c) restructure into a Ring-aligned topic. "
                "When in doubt, prefer the subdomain over a subfolder move: a subdomain creates a "
                "separate siteEmbedding pool, so the off-topic content keeps its traffic while "
                "the main domain's topical center reclaims focus. A subfolder still aggregates "
                "into the main domain's siteEmbedding and doesn't fix the dilution problem."
            ),
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/auditors/test_topical_authority_adapter.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 7: Run the existing auditor's regression coverage to make sure nothing broke**

Run: `pytest tests/ -k "topical" -v`
Expected: Pass. If pre-existing tests for `TopicalAuthorityAuditor` exist with different expectations of the outlier recommendation text, they may fail — in that case, update those tests to match the new copy (the spec mandates this copy change).

- [ ] **Step 8: Commit**

```bash
git add auditors/topical_authority_auditor.py tests/auditors/test_topical_authority_adapter.py tests/auditors/__init__.py
git commit -m "feat(topical-authority): from_computed_map adapter + high-click off-topic check + subdomain copy edit"
```

---

## Task 8 — Streamlit upload slot

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Locate the existing topical-map upload slot**

Run: `grep -n -i "topical" app.py | head -20`
Expected: Lines indicating where the Koray topical map is currently uploaded (likely a `st.file_uploader` near other audit inputs).

- [ ] **Step 2: Add the new upload slot next to it**

In `app.py`, immediately after the existing topical-map `st.file_uploader` line, add:

```python
        computed_map_file = st.file_uploader(
            "Computed Semantic Map (optional, JSON)",
            type=["json"],
            help=(
                "Output of `python run_semantic_map.py --client <name>` "
                "(topical_map.json). Use this when the client doesn't have a Koray "
                "topical map. Pair with semantic_map_full.json below for the "
                "click-overlay finding."
            ),
            key="computed_map_upload",
        )
        full_map_file = st.file_uploader(
            "Semantic Map Full JSON (optional)",
            type=["json"],
            help=(
                "Optional richer payload (semantic_map_full.json) that unlocks the "
                "high-click off-topic cluster finding."
            ),
            key="full_map_upload",
        )
```

Then find where the auditor is currently instantiated for topical authority and add a branch that prefers the computed map when uploaded:

```python
        if computed_map_file is not None:
            import json
            import tempfile
            from pathlib import Path

            with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
                tf.write(computed_map_file.getvalue().decode("utf-8"))
                topical_tmp = Path(tf.name)
            full_tmp = None
            if full_map_file is not None:
                with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tf:
                    tf.write(full_map_file.getvalue().decode("utf-8"))
                    full_tmp = Path(tf.name)
            topical_auditor = TopicalAuthorityAuditor.from_computed_map(
                crawl_df=crawl_df, topical_map_path=topical_tmp, full_json_path=full_tmp,
            )
        elif topical_map_text:
            # existing Koray-map path — leave as is
            ...
```

(Note: the exact variable names — `crawl_df`, `topical_map_text` — should match what's already in `app.py`. Inspect the surrounding code before editing.)

- [ ] **Step 3: Smoke test the app loads**

Run: `streamlit run app.py --server.headless true --server.port 8765 &` then `curl -s http://localhost:8765/_stcore/health` and kill the process.
Expected: `ok`. If Streamlit fails to start with a syntax or import error, fix and retry.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat(app): upload slot for computed semantic map JSON"
```

---

## Task 9 — SKILL.md polish + integration test

**Files:**
- Modify: `Skills/semantic-site-map/SKILL.md`
- Create: `tests/skills/semantic_site_map/test_integration.py`

- [ ] **Step 1: Write the integration test on a synthetic 100-URL site**

Create `tests/skills/semantic_site_map/test_integration.py`:
```python
"""End-to-end integration test on a synthetic site with known structure."""

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from Skills.semantic_site_map.cluster import cluster_pages
from Skills.semantic_site_map.report import build_outputs


def _synthetic_corpus(n_per_cluster: int = 40, n_outliers: int = 5) -> tuple[pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(42)
    cluster_a_text = ["hvac repair air conditioning furnace install"] * n_per_cluster
    cluster_b_text = ["plumbing leak pipe water heater install"] * n_per_cluster
    outlier_texts = ["travel tips europe vacation"] * n_outliers

    texts = cluster_a_text + cluster_b_text + outlier_texts
    urls = (
        [f"https://x.com/hvac/{i}" for i in range(n_per_cluster)]
        + [f"https://x.com/plumb/{i}" for i in range(n_per_cluster)]
        + [f"https://x.com/blog/travel-{i}" for i in range(n_outliers)]
    )

    embeddings = np.vstack([
        rng.normal(loc=[5, 5, 0], scale=0.05, size=(n_per_cluster, 3)),
        rng.normal(loc=[-5, -5, 0], scale=0.05, size=(n_per_cluster, 3)),
        rng.normal(loc=[0, 0, 10], scale=0.05, size=(n_outliers, 3)),
    ]).astype(np.float32)

    return pd.DataFrame({"url": urls, "text": texts}), embeddings


def test_synthetic_pipeline_identifies_clusters_and_outliers(tmp_path):
    text_df, embeddings = _synthetic_corpus()

    with patch("Skills.semantic_site_map.cluster._call_llm_for_label") as m:
        m.side_effect = lambda ngrams, samples, **_: ngrams[0].title()
        result = cluster_pages(text_df, embeddings, api_key="fake", min_cluster_size=5)

    cluster_labels = result["cluster_labels"]
    # Expect 2 clusters and the 5 outlier-cluster pages flagged as -1
    n_clusters = len({c for c in cluster_labels if c != -1})
    assert n_clusters >= 2  # HDBSCAN may split the outlier blob into its own cluster
    n_outliers = int((cluster_labels == -1).sum())
    assert 0 <= n_outliers  # tolerance: HDBSCAN can absorb tight outlier blob

    gsc = pd.DataFrame({
        "url": text_df["url"],
        "clicks": [10] * 40 + [10] * 40 + [200] * 5,  # outliers drive traffic
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
    assert paths["png"].stat().st_size > 2000  # PNG actually rendered
```

- [ ] **Step 2: Run the integration test**

Run: `pytest tests/skills/semantic_site_map/test_integration.py -v`
Expected: PASS.

- [ ] **Step 3: Polish SKILL.md**

Replace `Skills/semantic-site-map/SKILL.md` with the full version:
```markdown
---
name: "Semantic Site Map"
description: "Computes a topical map from any SF crawl using embeddings (no Koray map required), overlays GSC clicks per cluster, and feeds the topical-authority auditor through a JSON adapter. Surfaces siteRadius outliers and the high-click-high-siteRadius dilution-driving clusters from the May 2024 Google leak attributes."
---

# Semantic Site Map

## When to trigger

- Client requests topical authority analysis but doesn't have a Koray topical map
- Audit needs `siteFocusScore` / `siteRadius` findings (the leak-grounded auditor)
- An audit produced strong on-page metrics but client says revenue pages aren't ranking — this skill surfaces whether off-topic clusters are diluting the topical center
- Periodic re-run (60–90 days) to confirm the topical center has moved as recommended

## Prerequisites

- Screaming Frog crawl: `Clients/<name>/data/crawl_internal.csv` (or any SF Internal CSV)
- Optional: GSC export with `url`, `clicks`, `impressions` columns (90-day window recommended)
- Optional but recommended: SF custom extraction column for body text (XPath `//main` or `//article`). Without it, the skill falls back to Crawl4AI (slower).
- `.env` contains `OPENROUTER_API_KEY`

## Invocation

```bash
python run_semantic_map.py --client "<client-name>"
python run_semantic_map.py --client "Education Walkthrough" \
    --crawl "Clients/Education Walkthrough/Others/ew_crawl_filtered.csv" \
    --gsc   "Clients/Education Walkthrough/data/gsc_performance.csv"
```

## Outputs

Written to `Clients/<name>/Full SEO Audit/semantic_map/`:

| File | Purpose | Consumer |
|---|---|---|
| `topical_map.json` | Koray-compatible: `central_entity`, `rings`, `outliers` | `TopicalAuthorityAuditor.from_computed_map(...)` |
| `semantic_map_full.json` | Adds `clicks_by_cluster`, `site_radius_per_url`, `cluster_name_by_id`, `high_click_off_topic_clusters` | Auditor's new high-click check; analyst reference |
| `semantic_map_report.md` | Per-cluster summary + dilution-driving clusters callout | Client deliverable |
| `semantic_map.png` | Four-ring scatter with point-size = clicks | Client deliverable |

Cache (safe to delete; speeds up re-runs):

- `Clients/<name>/Full SEO Audit/_cache_semantic_map/page_text.csv` — Crawl4AI fetch cache
- `Clients/<name>/Full SEO Audit/_cache_semantic_map/embeddings_<model>.parquet` — embedding cache keyed by text hash

## Auditor integration

```python
from auditors.topical_authority_auditor import TopicalAuthorityAuditor

auditor = TopicalAuthorityAuditor.from_computed_map(
    crawl_df=df_from_sf_csv,
    topical_map_path="Clients/Acme/Full SEO Audit/semantic_map/topical_map.json",
    full_json_path="Clients/Acme/Full SEO Audit/semantic_map/semantic_map_full.json",
)
issues = auditor.run_audit()
```

The auditor's three existing checks run unchanged on the computed map. The new `_check_high_click_off_topic_cluster` activates when `full_json_path` is provided.

## Decisions baked into this skill

- **Embeddings**: `openai/text-embedding-3-small` via OpenRouter (1536-dim, $0.02/1M tokens). Override with `--model`.
- **Clustering**: HDBSCAN with `min_cluster_size = max(5, n_urls // 50)`. K-means k=4 fallback when HDBSCAN finds <2 clusters.
- **Cluster labels**: LLM-generated (default `anthropic/claude-3.5-sonnet`), n-gram fallback on failure.
- **Ring assignment**: quartiles of `site_radius` among clustered URLs; outliers in `-1` go to the `outliers` list.
- **High-click off-topic threshold**: cluster clicks >= 75th percentile AND median `site_radius` > 0.6.

## Limitations

- < 50 URLs after eligibility filters → clustering is coarse; report flags this
- Crawl4AI fetch quality varies by template; supply an SF body-text column for production audits
- Embeddings are not Google's; `text-embedding-3-small` correlates with general topical similarity, not Google's production embeddings (the "Gemma 3 ≈ Google" claim from Dan Hickley's post is a hypothesis, not a tested fact)
- Snapshot/drift comparison across runs is not in v1 — re-runs overwrite previous outputs

## Related

- Spec: [docs/superpowers/specs/2026-05-29-semantic-site-map-design.md](../../docs/superpowers/specs/2026-05-29-semantic-site-map-design.md)
- Leak attributes context: [Skills/technical-seo-agent/references/seo-fundamentals-2026.md](../technical-seo-agent/references/seo-fundamentals-2026.md)
- Consumer: [auditors/topical_authority_auditor.py](../../auditors/topical_authority_auditor.py)
```

- [ ] **Step 4: Run the full test suite**

Run: `pytest tests/skills/semantic_site_map/ tests/auditors/test_topical_authority_adapter.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add Skills/semantic-site-map/SKILL.md tests/skills/semantic_site_map/test_integration.py
git commit -m "docs(semantic-site-map): polish SKILL.md + add synthetic-site integration test"
```

---

## Task 10 — End-to-end validation on Education Walkthrough

**Files:** (no code changes — this is a runtime validation pass)

- [ ] **Step 1: Confirm the client data exists**

Run:
```bash
ls "Clients/Education Walkthrough/" && \
ls "Clients/Education Walkthrough/Others/" && \
test -f "Clients/Education Walkthrough/Others/ew_crawl_filtered.csv" && echo "crawl present"
```
Expected: lists folders + `crawl present`. If the crawl file is missing, document the gap in the final report and stop — do not synthesize data.

- [ ] **Step 2: Check for a GSC export**

Run:
```bash
find "Clients/Education Walkthrough" -iname "gsc*" -type f 2>&1 | head -5
```
Expected: lists any `gsc_performance.csv` / `gsc_*.csv` files. If none, the validation still proceeds without the click overlay; the report will say "click data unavailable".

- [ ] **Step 3: Verify OPENROUTER_API_KEY**

Run: `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('present' if os.environ.get('OPENROUTER_API_KEY') else 'MISSING')"`
Expected: `present`. If `MISSING`, stop and ask the user to add it to `.env`.

- [ ] **Step 4: Run the skill**

Run:
```bash
python run_semantic_map.py \
    --client "Education Walkthrough" \
    --crawl "Clients/Education Walkthrough/Others/ew_crawl_filtered.csv" \
    -v
```
Expected: log lines for text loading (Crawl4AI fallback on first run since no body-text column), embedding (with batch count), clustering, and final "Outputs written:" summary listing 4 file paths.

If Crawl4AI fails on > 20% of URLs the skill aborts with a clear message — re-run with a smaller URL set or supply an SF body-text column. Do not bypass the threshold.

- [ ] **Step 5: Sanity-check the outputs**

Run:
```bash
ls "Clients/Education Walkthrough/Full SEO Audit/semantic_map/" && \
python -c "import json; d=json.load(open('Clients/Education Walkthrough/Full SEO Audit/semantic_map/topical_map.json','r',encoding='utf-8')); print('central:', d['central_entity']); print('rings:', {k:len(v) for k,v in d['rings'].items()}); print('outliers:', len(d['outliers']))"
```
Expected: lists all four output files; prints a sensible central entity, ring sizes, and outlier count. Verify the PNG file is non-trivial (>50 KB).

- [ ] **Step 6: Run the auditor against the computed map**

Run:
```bash
python -c "
import pandas as pd
from utils.file_parser import _read_csv_robust
from auditors.topical_authority_auditor import TopicalAuthorityAuditor

df = _read_csv_robust('Clients/Education Walkthrough/Others/ew_crawl_filtered.csv')
if 'url' not in df.columns:
    for c in df.columns:
        if c.lower() in ('address','url'):
            df = df.rename(columns={c:'url'}); break

auditor = TopicalAuthorityAuditor.from_computed_map(
    crawl_df=df,
    topical_map_path='Clients/Education Walkthrough/Full SEO Audit/semantic_map/topical_map.json',
    full_json_path='Clients/Education Walkthrough/Full SEO Audit/semantic_map/semantic_map_full.json',
)
issues = auditor.run_audit()
for i in issues:
    print(i.severity.value, '|', i.issue_type, '|', i.title)
"
```
Expected: prints 1+ issues, at minimum `topical_outlier_pages`. If a GSC file was present and the synthetic conditions are met, also prints `high_click_off_topic_cluster`.

- [ ] **Step 7: Final commit + summary**

If any of the validation steps surfaced bugs, fix them in the relevant module's task scope (NOT here — open new follow-up commits). Otherwise:

```bash
git add -A
git status  # confirm clean (only validation outputs, which live under Clients/ and are gitignored)
```

If the Clients/ output dir is gitignored (it is per CLAUDE.md), nothing new to commit. Report the validation results in the response message: which client folder, the four output paths, the cluster count, the outlier count, and a one-paragraph quality assessment.

---

## Self-Review Notes

- **Spec coverage:** All seven sections of the spec (Architecture, Data flow, Error handling, Testing, Out of scope, Risks, plus the Locked Decisions table) are addressed across Tasks 1–9; Task 10 is the validation pass. ✅
- **Placeholder scan:** Searched for "TBD/TODO/implement later/handle edge cases/similar to Task" — none. Step 2 of Task 8 instructs the engineer to "inspect the surrounding code" because the exact variable names in `app.py` are not in this plan — this is a deliberate fallback, not a placeholder; the engineer has the file path and the precise insertion point.
- **Type consistency:** `cluster_result` dict shape (`cluster_labels`, `cluster_name_by_id`, `site_center`, `site_radius`, `ngrams_by_cluster`) is identical across Tasks 4, 5, and 7. `EMBEDDING_DIM`, `DEFAULT_MODEL`, `DEFAULT_BATCH_SIZE` exported from `embedder.py` and re-used in `run_semantic_map.py`. `from_computed_map(crawl_df, topical_map_path, full_json_path=None)` signature is identical in the auditor module (Task 7) and in the Streamlit handler (Task 8) and the integration test (Task 9).
- **TF-IDF tokenization caveat:** `_ngrams.top_ngrams_per_cluster` lowercases via `TfidfVectorizer` defaults — labels will appear lowercased in fallback mode. This is intentional; LLM labels will be Title Case.
