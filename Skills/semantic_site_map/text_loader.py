"""Hybrid text source: SF body-text column if present, Crawl4AI fallback."""

from __future__ import annotations

import asyncio
import logging
import re
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
        logger.info(
            "text_loader: reusing cached page_text from %s", cache_path
        )
        cached = pd.read_csv(cache_path)
        cached = cached[
            cached["url"].isin(filtered["url"])
        ].reset_index(drop=True)
        # Re-apply boilerplate detection on cached text. Cheap (~1s
        # for 1,500 rows) and guards against caches written before
        # the boilerplate pass existed.
        boilerplate = _detect_boilerplate_lines(cached["text"].tolist())
        if boilerplate:
            logger.info(
                "text_loader: cached corpus - stripping %d "
                "boilerplate line(s)",
                len(boilerplate),
            )
            cached["text"] = cached["text"].apply(
                lambda t: _strip_boilerplate(t, boilerplate)
            )
            cached = cached[
                cached["text"].str.len() > 0
            ].reset_index(drop=True)
        return cached

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


_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
_MD_LINK_PATTERN = re.compile(r"\[([^\]]*)\]\([^)]*\)")

# Lines appearing on >= this fraction of pages are treated as
# site-wide template chrome (global nav, footer, sidebar) and removed
# before embedding. 0.80 = appears on 80% of pages. Empirically this
# catches mega-menus and global footers without removing legitimate
# repeating content (e.g. category-page boilerplate that should still
# inform clustering).
BOILERPLATE_THRESHOLD = 0.80


def _clean_noise(text: str) -> str:
    """Strip URLs and markdown link targets that pollute embeddings.

    Crawl4AI's markdown output preserves every internal link as
    ``[anchor](https://full-url)``. With ~50-200 internal links per
    page, the domain itself dominates TF-IDF and embedding signal,
    making distinct topical clusters look identical. Strip both the
    URL targets (keeping the anchor text) and any bare URLs.
    """
    # Markdown link first: keep anchor, drop URL target.
    text = _MD_LINK_PATTERN.sub(r"\1", text)
    # Any remaining bare URLs.
    text = _URL_PATTERN.sub("", text)
    return text


def _detect_boilerplate_lines(
    texts: list[str], threshold: float = BOILERPLATE_THRESHOLD
) -> set[str]:
    """Find lines that appear on >= threshold fraction of pages.

    These are global nav / footer / sidebar elements that pollute
    embeddings on short pages where chrome dominates the body.

    Below 10 pages, boilerplate detection is a no-op: the statistical
    signal isn't strong enough to distinguish chrome from genuine
    repeating content, and tiny corpora (unit tests, debug runs)
    would otherwise have every line marked as boilerplate.
    """
    import math

    if not texts or len(texts) < 10:
        return set()
    n_pages = len(texts)
    line_pages: dict[str, int] = {}
    for text in texts:
        # Unique non-trivial lines per page (don't double-count
        # repeated nav within one page).
        seen_in_page: set[str] = set()
        for line in text.splitlines():
            stripped = line.strip()
            if len(stripped) < 3:
                continue
            seen_in_page.add(stripped)
        for line in seen_in_page:
            line_pages[line] = line_pages.get(line, 0) + 1
    # ceil so 75% at threshold 0.80 does NOT qualify (4 pages -> need 4,
    # not 3). int truncation would let 75% through.
    cutoff = max(1, math.ceil(n_pages * threshold))
    return {line for line, count in line_pages.items() if count >= cutoff}


def _strip_boilerplate(text: str, boilerplate: set[str]) -> str:
    """Drop lines that match the detected boilerplate set."""
    if not boilerplate:
        return text
    kept_lines = []
    for line in text.splitlines():
        if line.strip() not in boilerplate:
            kept_lines.append(line)
    return "\n".join(kept_lines)


def _build_text_from_sf(df: pd.DataFrame, body_col: str) -> pd.DataFrame:
    parts_columns = ["title", "meta_desc", "h1", body_col]
    available = [c for c in parts_columns if c in df.columns]

    def row_text(row: pd.Series) -> str:
        joined = " \n".join(
            str(row[c])
            for c in available
            if pd.notna(row[c]) and str(row[c]).strip()
        )
        return _clean_noise(joined)

    out = pd.DataFrame({
        "url": df["url"].astype(str),
        "text": df.apply(row_text, axis=1),
    })
    out = out[out["text"].str.len() > 0].reset_index(drop=True)

    # Two-pass site-wide boilerplate strip: detect lines that appear
    # on >= BOILERPLATE_THRESHOLD of pages (global nav/footer chrome),
    # then drop them from every page. This must run AFTER url cleanup
    # so the lines being compared aren't differentiated by URL targets.
    boilerplate = _detect_boilerplate_lines(out["text"].tolist())
    if boilerplate:
        logger.info(
            "text_loader: stripping %d boilerplate line(s) "
            "(present on >= %.0f%% of pages)",
            len(boilerplate),
            BOILERPLATE_THRESHOLD * 100,
        )
        out["text"] = out["text"].apply(
            lambda t: _strip_boilerplate(t, boilerplate)
        )
        # Drop pages whose entire content was boilerplate.
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


async def fetch_raw_page_text(urls: list[str], concurrency: int = 8) -> pd.DataFrame:
    """Fetch each URL's markdown with no boilerplate stripping; returns DataFrame[url, text].

    For callers that must see the whole document, footer and header included, such as counting the
    addresses and phone numbers a page lists. Raises when more than 20% of the fetches fail.
    """
    return await _fetch_via_crawl4ai(list(urls), concurrency=concurrency)
