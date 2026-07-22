"""Cannibalization data prep — reusable across clients.

Three pure-function utilities that any client's cannibalization audit
can use:

    parse_gsc_pipe_payload(raw_text)  ->  list[dict]
        Parses the pipe-delimited text format the GSC MCP tool returns
        into normalized row dicts.

    normalize_gsc_rows(rows)  ->  list[dict]
        Strips URL query strings (UTM tracking parameters), normalizes
        case + host, deduplicates (query, normalized_page) pairs by
        impression-weighted average position. This step prevents
        inflated cluster counts caused by GBP/UTM URL variants being
        treated as separate pages.

    detect_candidate_clusters(rows, brand_pattern, ...)  ->  list[dict]
        Groups rows by query, applies brand exclusion + impression /
        position thresholds, returns candidate clusters sorted by
        impressions volume. Output is the input the cannibalization
        auditor's `gsc_query_page_data` expects.

Client-specific concerns (intent overrides, brand-name patterns,
geo-modifier patterns) stay in the per-client driver script. This
module only handles the generic data-prep that's identical across
clients.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional, Pattern
from urllib.parse import urlparse, urlunparse


# =============================================================================
# THRESHOLDS — match the cannibalization auditor's defaults
# =============================================================================

DEFAULT_MIN_IMPRESSIONS = 50
"""Filter out (query, URL) pairs with fewer impressions than this.
Below this threshold, the URL probably isn't actually competing for
the query — it's a long-tail accidental match."""

DEFAULT_MAX_POSITION = 30
"""Only count URLs ranking in the top 30 — beyond that, they're not
really competing for visibility."""

DEFAULT_MIN_PAGES_PER_QUERY = 2
"""A query needs at least this many distinct URLs ranking to be a
cannibalization candidate."""


# =============================================================================
# PARSE: GSC pipe-delimited payload  ->  normalized rows
# =============================================================================


def parse_gsc_pipe_payload(raw_text: str) -> list[dict]:
    """Parse the pipe-delimited text format the GSC MCP tool returns.

    Expected format:
        Query | Page | Clicks | Impressions | CTR | Position
        ---
        keyword text | https://... | 12 | 1500 | 0.80% | 5.4
        ...

    Returns one dict per data row with keys: query, page, clicks,
    impressions, ctr (as float 0..1), position.

    Skips malformed rows defensively. Returns empty list if no header
    found. Handles queries that contain ' | ' as part of the query
    text by re-joining the leading fields.
    """
    if not raw_text:
        return []

    lines = raw_text.split("\n")
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Query | Page |"):
            header_idx = i
            break
    if header_idx is None:
        return []

    rows: list[dict] = []
    for line in lines[header_idx + 1:]:
        line = line.strip()
        if not line or line.startswith("---") or " | " not in line:
            continue
        parts = line.split(" | ")
        if len(parts) < 6:
            continue
        # Last 4 fields are clicks, impressions, ctr, position. Earlier
        # fields can include " | " inside the query text — re-join
        # them.
        position = parts[-1]
        ctr = parts[-2]
        impressions = parts[-3]
        clicks = parts[-4]
        page = parts[-5]
        query = " | ".join(parts[:-5])
        try:
            ctr_val = float(ctr.replace("%", "").strip()) / 100.0
            rows.append({
                "query": query.strip(),
                "page": page.strip(),
                "position": round(float(position), 2),
                "impressions": int(impressions),
                "clicks": int(clicks),
                "ctr": round(ctr_val, 4),
            })
        except (ValueError, AttributeError):
            continue
    return rows


# =============================================================================
# NORMALIZE: dedupe URLs, strip UTM, weighted avg position
# =============================================================================


def normalize_url(url: str, host_hint: Optional[str] = None) -> str:
    """Strip query string and fragment, normalize host case + scheme.

    `host_hint` is an optional bare domain (e.g., "beehiveplumbing.com")
    used to canonicalize host variants — bare-domain pages are rewritten
    to www. when host_hint matches.
    """
    if not isinstance(url, str) or not url:
        return ""
    p = urlparse(url)
    netloc = p.netloc.lower()
    if host_hint:
        bare = host_hint.lower().lstrip("www.")
        if netloc == bare:
            netloc = "www." + bare
    path = p.path or "/"
    return urlunparse((p.scheme, netloc, path, "", "", ""))


def normalize_gsc_rows(
    rows: Iterable[dict],
    host_hint: Optional[str] = None,
) -> list[dict]:
    """Aggregate rows by (query, normalized_page) using impression-
    weighted average position.

    Dedupes UTM/GBP-tracked URL variants. Returns one row per unique
    (query, page) with combined impressions, combined clicks,
    impression-weighted position, and recomputed CTR.
    """
    agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"impressions": 0, "clicks": 0, "weighted_pos_sum": 0.0}
    )
    for r in rows:
        query = (r.get("query") or "").strip()
        page = normalize_url(r.get("page") or "", host_hint=host_hint)
        if not query or not page:
            continue
        impr = int(r.get("impressions") or 0)
        clicks = int(r.get("clicks") or 0)
        position = r.get("position")
        if impr <= 0 or position is None:
            continue
        try:
            position_f = float(position)
        except (TypeError, ValueError):
            continue
        key = (query, page)
        agg[key]["impressions"] += impr
        agg[key]["clicks"] += clicks
        # Weight position by impressions
        agg[key]["weighted_pos_sum"] += position_f * impr

    out: list[dict] = []
    for (query, page), v in agg.items():
        impr = v["impressions"]
        if impr <= 0:
            continue
        avg_pos = v["weighted_pos_sum"] / impr
        out.append({
            "query": query,
            "page": page,
            "position": round(avg_pos, 2),
            "impressions": impr,
            "clicks": v["clicks"],
            "ctr": round(v["clicks"] / impr, 4) if impr else 0.0,
        })
    return out


# =============================================================================
# DETECT: candidate clusters with brand exclusion + thresholds
# =============================================================================


def detect_candidate_clusters(
    rows: Iterable[dict],
    brand_pattern: Optional[Pattern[str]] = None,
    min_impressions: int = DEFAULT_MIN_IMPRESSIONS,
    max_position: float = DEFAULT_MAX_POSITION,
    min_pages_per_query: int = DEFAULT_MIN_PAGES_PER_QUERY,
) -> list[dict]:
    """Group rows by query, apply filters, return candidate clusters.

    A query becomes a cluster when:
      - it doesn't match `brand_pattern` (None disables brand exclusion)
      - at least `min_pages_per_query` distinct URLs rank for it AND
        each clears `min_impressions` and `max_position` thresholds

    Returns clusters sorted by total_impressions descending.
    """
    by_query: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_query[r["query"]].append(r)

    clusters: list[dict] = []
    for query, group in by_query.items():
        if brand_pattern and brand_pattern.search(query):
            continue
        # Each row must clear thresholds independently
        qualifying = [
            r for r in group
            if r["impressions"] >= min_impressions
            and r["position"] <= max_position
        ]
        distinct_pages = {r["page"] for r in qualifying}
        if len(distinct_pages) < min_pages_per_query:
            continue
        clusters.append({
            "query": query,
            "page_count": len(distinct_pages),
            "total_impressions": sum(r["impressions"] for r in qualifying),
            "total_clicks": sum(r["clicks"] for r in qualifying),
            "best_position": min(r["position"] for r in qualifying),
            "pages": qualifying,
        })

    clusters.sort(key=lambda c: -c["total_impressions"])
    return clusters


# =============================================================================
# CONVENIENCE: end-to-end pipeline
# =============================================================================


def prepare_for_auditor(
    raw_payload: str | dict,
    *,
    host_hint: Optional[str] = None,
    brand_pattern: Optional[Pattern[str]] = None,
    min_impressions: int = DEFAULT_MIN_IMPRESSIONS,
    max_position: float = DEFAULT_MAX_POSITION,
    min_pages_per_query: int = DEFAULT_MIN_PAGES_PER_QUERY,
    output_dir: Optional[Path] = None,
) -> dict:
    """End-to-end: parse + normalize + detect candidate clusters.

    Args:
        raw_payload: either the pipe-delimited text from the GSC MCP
            tool, OR a dict with a "raw_text" / "result" field, OR a
            dict with a "rows" array (already-parsed input).
        host_hint: optional domain for URL normalization (e.g.,
            "beehiveplumbing.com")
        brand_pattern: optional regex to exclude branded queries
        min_impressions / max_position / min_pages_per_query: thresholds
            (defaults match the auditor's defaults)
        output_dir: when set, writes _step1, _step2, _step3 JSON files
            for traceability — same naming pattern the project uses

    Returns a dict with:
        - rows: normalized (query, page) rows ready for the auditor's
            `gsc_query_page_data` parameter
        - clusters: candidate clusters (informational; the auditor
            re-detects clusters from `rows` itself)
        - stats: {total_rows, unique_queries, unique_pages,
            candidate_count}
    """
    # Resolve the input shape
    if isinstance(raw_payload, dict):
        if "rows" in raw_payload:
            # Pre-parsed
            parsed_rows = list(raw_payload["rows"])
        elif "raw_text" in raw_payload:
            parsed_rows = parse_gsc_pipe_payload(raw_payload["raw_text"])
        elif "result" in raw_payload and isinstance(raw_payload["result"], str):
            parsed_rows = parse_gsc_pipe_payload(raw_payload["result"])
        else:
            parsed_rows = []
    elif isinstance(raw_payload, str):
        # Treat as the pipe-delimited text
        parsed_rows = parse_gsc_pipe_payload(raw_payload)
    else:
        parsed_rows = []

    normalized = normalize_gsc_rows(parsed_rows, host_hint=host_hint)
    clusters = detect_candidate_clusters(
        normalized,
        brand_pattern=brand_pattern,
        min_impressions=min_impressions,
        max_position=max_position,
        min_pages_per_query=min_pages_per_query,
    )

    stats = {
        "total_rows": len(normalized),
        "unique_queries": len({r["query"] for r in normalized}),
        "unique_pages": len({r["page"] for r in normalized}),
        "candidate_count": len(clusters),
    }

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "_step2_query_page_normalized.json").write_text(
            json.dumps({
                "total_rows": stats["total_rows"],
                "unique_queries": stats["unique_queries"],
                "unique_pages": stats["unique_pages"],
                "rows": normalized,
            }, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (output_dir / "_step3_candidate_clusters.json").write_text(
            json.dumps({
                "candidate_count": stats["candidate_count"],
                "clusters": clusters,
            }, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    return {
        "rows": normalized,
        "clusters": clusters,
        "stats": stats,
    }
