"""Collect raw visible text for location-targeted pages, so an auditor can count their addresses and phones.

Separate from the semantic map's text loader on purpose: that loader strips lines repeated across pages
(global nav and footer) before embedding, which would hide a shared footer full of addresses, exactly what the
local check needs to count. This keeps the raw text.

Source order: a body-text column in the crawl when it has one, otherwise a fetch of just the location pages.
A failure returns an empty mapping, which the auditor reports as "not checked", never as clean.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Optional

import pandas as pd

logger = logging.getLogger(__name__)

Fetcher = Callable[[list[str]], dict[str, str]]


def _default_fetch(urls: list[str]) -> dict[str, str]:
    from Skills.semantic_site_map.text_loader import fetch_raw_page_text

    frame = asyncio.run(fetch_raw_page_text(urls))
    return {str(r.url): str(r.text) for r in frame.itertuples() if isinstance(r.text, str) and r.text.strip()}


def load_location_page_text(
    crawl_df: pd.DataFrame,
    is_location_url: Callable[[object], bool],
    fetch: Optional[Fetcher] = None,
) -> dict[str, str]:
    """Return {url: visible text} for indexable, 2xx, location-targeted HTML pages.

    Args:
        crawl_df: Screaming Frog crawl with at least a `url` column.
        is_location_url: predicate for single-place pages (the local auditor's own definition).
        fetch: replaces the network fetch, for tests.
    """
    if crawl_df is None or "url" not in crawl_df.columns:
        return {}
    pages = crawl_df
    if "status_code" in pages.columns:
        pages = pages[pages["status_code"].fillna(0).astype(int).between(200, 299)]
    if "content_type" in pages.columns:
        pages = pages[pages["content_type"].fillna("").str.contains("html", case=False, na=False)]
    if "indexability" in pages.columns:
        pages = pages[pages["indexability"].fillna("").str.lower() == "indexable"]
    pages = pages[pages["url"].apply(is_location_url)]
    urls = pages["url"].astype(str).tolist()
    if not urls:
        return {}

    from Skills.semantic_site_map.text_loader import detect_body_column

    body_col = detect_body_column(pages)
    if body_col is not None:
        return {
            str(r["url"]): str(r[body_col])
            for _, r in pages.iterrows()
            if pd.notna(r[body_col]) and str(r[body_col]).strip()
        }
    try:
        return (fetch or _default_fetch)(urls)
    except Exception as exc:  # noqa: BLE001 - an unavailable fetch must read as "unchecked", not crash the audit
        logger.warning("location page text unavailable for %d pages: %s", len(urls), exc)
        return {}
