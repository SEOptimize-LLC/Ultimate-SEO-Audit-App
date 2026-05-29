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
        return cached[cached["url"].isin(filtered["url"])].reset_index(drop=True)

    logger.info("text_loader: falling back to Crawl4AI for %d URLs", len(filtered))
    fetched = await _fetch_via_crawl4ai(
        filtered["url"].tolist(),
        concurrency=crawl4ai_concurrency,
    )
    merged_df = filtered.merge(fetched, on="url", how="left").assign(
        _body=lambda d: d["text"]
    )
    # Drop the temporary `text` column from the merge so _build_text_from_sf can recompute.
    if "text" in merged_df.columns:
        merged_df = merged_df.drop(columns=["text"])
    merged = _build_text_from_sf(merged_df, "_body")
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(cache_path, index=False)
    return merged


def _filter_eligible(df: pd.DataFrame) -> pd.DataFrame:
    keep = df.copy()
    if "status_code" in keep.columns:
        keep = keep[
            keep["status_code"].fillna(0).astype(int).between(200, 299)
        ]
    if "content_type" in keep.columns:
        keep = keep[
            keep["content_type"].fillna("").str.contains("html", case=False, na=False)
        ]
    if "meta_robots" in keep.columns:
        keep = keep[
            ~keep["meta_robots"]
            .fillna("")
            .str.lower()
            .str.contains("noindex", na=False)
        ]
    return keep.reset_index(drop=True)


def _build_text_from_sf(df: pd.DataFrame, body_col: str) -> pd.DataFrame:
    parts_columns = ["title", "meta_desc", "h1", body_col]
    available = [c for c in parts_columns if c in df.columns]

    def row_text(row: pd.Series) -> str:
        return " \n".join(
            str(row[c])
            for c in available
            if pd.notna(row[c]) and str(row[c]).strip()
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
                    logger.warning(
                        "text_loader: Crawl4AI failed on %s: %s", url, exc
                    )
                    results.append({"url": url, "text": ""})

        await asyncio.gather(*(fetch_one(u) for u in urls))

    fetched_df = pd.DataFrame(results)
    failed_ratio = (
        (fetched_df["text"].str.len() == 0).mean() if len(fetched_df) else 1.0
    )
    if failed_ratio > 0.20:
        raise RuntimeError(
            f"text_loader: Crawl4AI failed on {failed_ratio:.1%} of URLs "
            "(threshold is 20%). Inspect logs and retry with a smaller URL set "
            "or supply an SF body-text column."
        )
    return fetched_df
