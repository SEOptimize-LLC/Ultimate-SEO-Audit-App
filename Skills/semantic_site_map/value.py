"""Business-value derivation for the Keep/Grow/Relocate/Prune classifier.

Three signals combined, each contributes when available:

1. URL-pattern score (always runs)     - base score from the URL shape
2. GSC commercial-intent boost         - +N when the page ranks for queries
                                          containing buy/pricing/near-me/etc.
3. GA4 conversion boost                - +N when the page has documented
                                          conversions in the GA4 export

Final score is capped at 100. The skill calls `derive_business_value(urls,
gsc_df, ga4_df)` and gets a {url: float} dict. From there the median-split
classifier in `report.classify_pages_by_action` produces the 2x2 buckets.

Design intent: don't rely on the client to manually provide a value file.
Every signal here is derivable from artifacts that already live in the
client folder (SF crawl gives URLs; GSC + GA4 fetchers populate the rest).
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL-pattern signal
# ---------------------------------------------------------------------------

# Patterns are matched against the full URL (case-insensitive). The first
# matching tier wins. Tiers ordered most-specific to most-general so a
# /services/contact/ URL scores as high (not as medium).
_HIGH_VALUE_PATTERNS = (
    r"/services?(/|$)",
    r"/products?(/|$)",
    r"/pricing(/|$)",
    r"/plans?(/|$)",
    r"/contact(-us|/|$)",
    r"/get-(a-)?quote(/|$)",
    r"/demo(/|$)",
    r"/book(-a-)?call(/|$)",
    r"/schedule(/|$)",
    r"/buy(/|$)",
    r"/checkout(/|$)",
    r"/cart(/|$)",
    r"/sign-?up(/|$)",
    r"/register(/|$)",
    r"/features?(/|$)",
    r"/solutions?(/|$)",
    r"/use-cases?(/|$)",
    r"/case-stud(y|ies)(/|$)",
    r"/locations?(/|$)",
    r"/areas?-served(/|$)",
    r"/whos-it-for(/|$)",
)
_MEDIUM_VALUE_PATTERNS = (
    r"/blog(/|$)",
    r"/guides?(/|$)",
    r"/resources?(/|$)",
    r"/learn(/|$)",
    r"/articles?(/|$)",
    r"/posts?(/|$)",
    r"/news(/|$)",
    r"/insights?(/|$)",
    r"/help(/|$)",
    r"/docs?(/|$)",
    r"/faq(s)?(/|$)",
    r"/glossary(/|$)",
    r"/how-to(/|$)",
)
_LOW_VALUE_PATTERNS = (
    r"/tags?(/|$)",
    r"/categor(y|ies)(/|$)",
    r"/authors?(/|$)",
    r"/page/\d+(/|$)",  # paginated archive
    r"/archive(s)?(/|$)",
    r"/privacy(-policy)?(/|$)",
    r"/terms(-of-service)?(/|$)",
    r"/cookie(-policy)?(/|$)",
    r"/legal(/|$)",
    r"/disclaimer(/|$)",
    r"/sitemap(/|$)",
    r"/login(/|$)",
    r"/admin(/|$)",
    r"/account(/|$)",
    r"/wp-",
    r"/feed(/|$)",
    r"/search(/|$)",
    r"/404(/|$)",
)

HIGH_SCORE = 60
MEDIUM_SCORE = 30
LOW_SCORE = 10
NEUTRAL_SCORE = 25  # uncategorized
HOMEPAGE_SCORE = 60  # treated as high


def score_url_pattern(url: str) -> int:
    """Return base value score from URL shape only."""
    url_lower = url.lower()
    # Homepage: path is "/" or empty after the host.
    path = re.sub(r"^https?://[^/]+", "", url_lower)
    if path in ("", "/"):
        return HOMEPAGE_SCORE

    for pattern in _LOW_VALUE_PATTERNS:
        if re.search(pattern, url_lower):
            return LOW_SCORE
    for pattern in _HIGH_VALUE_PATTERNS:
        if re.search(pattern, url_lower):
            return HIGH_SCORE
    for pattern in _MEDIUM_VALUE_PATTERNS:
        if re.search(pattern, url_lower):
            return MEDIUM_SCORE
    return NEUTRAL_SCORE


# ---------------------------------------------------------------------------
# GSC commercial-intent signal
# ---------------------------------------------------------------------------

COMMERCIAL_INTENT_TERMS = frozenset({
    "buy", "purchase", "order", "shop",
    "pricing", "price", "cost", "cheap", "affordable",
    "near me", "in [city]",  # placeholder - location modifiers handled below
    "best", "top", "review", "reviews", "vs",
    "service", "services", "hire", "book",
    "quote", "estimate", "consultation",
    "for sale", "deal", "deals", "discount",
    "demo", "trial", "free trial",
    "compare", "comparison",
})

# Generic location-suffix detector (covers "near me", "in <city>", etc.)
_LOCATION_RE = re.compile(
    r"\bnear me\b|\bin [a-z][a-z\s]{2,30}$", re.IGNORECASE
)

GSC_INTENT_BOOST_MAX = 20


def _commercial_intent_score(queries: pd.Series) -> int:
    """Return boost amount (0..GSC_INTENT_BOOST_MAX) for a query list."""
    if queries.empty:
        return 0
    total_queries = len(queries)
    commercial_hits = 0
    for q in queries.astype(str).str.lower():
        if _LOCATION_RE.search(q):
            commercial_hits += 1
            continue
        if any(term in q for term in COMMERCIAL_INTENT_TERMS):
            commercial_hits += 1
    ratio = commercial_hits / total_queries
    # Scale linearly: 100% commercial -> full boost; 0% -> no boost.
    return int(round(ratio * GSC_INTENT_BOOST_MAX))


# ---------------------------------------------------------------------------
# GA4 conversion signal
# ---------------------------------------------------------------------------

GA4_CONVERSION_BOOST = 30


def _ga4_conversion_boost(
    url: str, ga4_df: Optional[pd.DataFrame]
) -> int:
    if ga4_df is None or "url" not in ga4_df.columns:
        return 0
    if "conversions" not in ga4_df.columns:
        return 0
    matched = ga4_df.loc[ga4_df["url"] == url, "conversions"]
    if matched.empty:
        return 0
    if float(matched.sum()) > 0:
        return GA4_CONVERSION_BOOST
    return 0


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

def derive_business_value(
    urls: list[str],
    gsc_df: Optional[pd.DataFrame] = None,
    ga4_df: Optional[pd.DataFrame] = None,
) -> dict[str, float]:
    """Return per-URL composite business-value score (0..100).

    Args:
        urls: List of URLs to score.
        gsc_df: Optional DataFrame with columns ``url, query`` (clicks
            and impressions are accepted but not required for the
            commercial-intent boost - just the query mix per URL).
        ga4_df: Optional DataFrame with columns ``url, conversions``.

    Returns:
        Dict mapping every input URL to a float score in [0, 100].
    """
    # Pre-group GSC by URL once for O(N) lookup instead of repeated filters.
    gsc_by_url: dict[str, pd.Series] = {}
    if gsc_df is not None and "url" in gsc_df.columns and "query" in gsc_df.columns:
        for url, group in gsc_df.groupby("url"):
            gsc_by_url[str(url)] = group["query"]

    scores: dict[str, float] = {}
    for url in urls:
        base = score_url_pattern(url)
        gsc_boost = _commercial_intent_score(
            gsc_by_url.get(url, pd.Series([], dtype=str))
        )
        ga4_boost = _ga4_conversion_boost(url, ga4_df)
        total = min(100, base + gsc_boost + ga4_boost)
        scores[url] = float(total)
    logger.info(
        "value: scored %d URLs "
        "(URL-pattern always, GSC %s, GA4 %s)",
        len(urls),
        "ON" if gsc_df is not None else "OFF",
        "ON" if ga4_df is not None else "OFF",
    )
    return scores
