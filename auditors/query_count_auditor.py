"""Query Count Auditor — leak-grounded query-breadth diagnostics.

Consumes a GSC performance dataframe (query-level when a ``query`` column is
present) alongside the Screaming Frog crawl df. Implements Daniel Foley Carter's
"query counting" method: the number of DISTINCT queries a URL is served for is a
proxy for the value Google assigns the page. Single-snapshot checks only — the
two-period devaluation-vs-slippage gate is a documented method in the
traffic-loss-analysis skill (no historical GSC in the audit context).

Every check gates on a query-level GSC export (``query`` column present). When
only page-level GSC is supplied, distinct-query breadth cannot be computed, so
the auditor emits a single INSIGHT explaining the gap and no-ops the rest.

Checks (each single-snapshot):
1. Dead-page by query breadth  — pages served for very few distinct queries.
2. Position-band distribution   — queries stuck in positions 21-100 (no visibility).
3. Content-to-query ratio       — high word count serving few queries.
4. Serve-rate / lead-query      — top served query not reflected in title/H1.

Keep the class name and the ``(df, gsc_df)`` constructor signature stable so the
app.py / auditors.__init__ wiring stays valid.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd

from auditors.base_auditor import BaseAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Daniel Foley Carter query-breadth bands. On an established site the distinct
# query count a URL is served for is a proxy for the weight Google assigns it:
# a money page ranks for hundreds of queries, a dead page for a handful.
# ---------------------------------------------------------------------------
LITTLE_VALUE_QUERY_BAND = 50
"""Fewer than this many distinct queries = 'little value' band (DFC)."""

MEDIUM_QUERY_BAND = 250
"""50-250 distinct queries = 'medium' band; above 250 = 'healthy' (DFC)."""

DEAD_QUERY_THRESHOLD = 3
"""At or below this many distinct queries = near-zero weight (prune/repurpose)."""

# Position-band distribution (check 2)
LOW_VISIBILITY_MIN_POSITION = 20
"""Positions strictly above this (21+) carry impressions but almost no clicks."""

LOW_VISIBILITY_MAX_POSITION = 100
"""GSC caps average position around 100; ignore anything beyond as noise."""

STUCK_QUERY_FRACTION = 0.8
"""Flag a page when at least this share of its distinct queries sit in 21-100."""

MIN_QUERIES_FOR_BAND = 5
"""A page needs at least this many distinct queries before the band split is
statistically meaningful (avoids flagging pages with one or two stray queries)."""

# Content-to-query ratio (check 3)
HIGH_WORD_COUNT = 1500
"""Pages at or above this word count are 'heavy' — expected to earn breadth."""

LOW_QUERY_FOR_CONTENT = 50
"""Heavy pages serving fewer distinct queries than this are valueless or out
of scope for search demand (DFC): the effort isn't converting to coverage."""

# Serve-rate / lead-query dilution (check 4)
MIN_PAGE_IMPRESSIONS = 100
"""Impression floor for the lead-query check — below this a single top query is
too noisy to trust as the page's real lead query."""

LEAD_QUERY_OVERLAP_FLOOR = 0.34
"""If fewer than this share of the lead query's content tokens appear in the
page's title/H1, Google's understanding of the page focus is diluted."""

MAX_AFFECTED_URLS = 100
"""Cap on affected_urls carried in any single issue."""

# Lightweight English stopword set for token-overlap scoring. Intentionally
# small — it only needs to strip the function words that would otherwise inflate
# title/query overlap (e.g. "the", "for", "in").
_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "that", "the", "to", "vs",
    "was", "what", "when", "where", "which", "who", "why", "with", "your",
    "you", "my", "me", "i", "we", "our", "near",
})

# URL markers for nav/listing pages that legitimately carry heavy body text but
# few of their own queries (they aggregate, they don't rank as an answer). These
# are exempt from the content-to-query ratio check.
_CATEGORY_URL_MARKERS = (
    "/category/",
    "/categories/",
    "/product-category/",
    "/collection/",
    "/collections/",
    "/shop/",
    "/tag/",
    "/tags/",
    "/topic/",
    "/topics/",
    "/archive/",
    "/page/",
)


def _tokenize(text: str) -> set[str]:
    """Lowercase, split on non-alphanumerics, drop stopwords and 1-char tokens."""
    if not isinstance(text, str) or not text.strip():
        return set()
    raw = re.split(r"[^a-z0-9]+", text.lower())
    return {t for t in raw if len(t) > 1 and t not in _STOPWORDS}


class QueryCountAuditor(BaseAuditor):
    """Counts distinct queries served per URL and diagnoses query-breadth health."""

    def __init__(self, df: pd.DataFrame, gsc_df: pd.DataFrame):
        super().__init__(df)
        self.gsc_df = gsc_df
        # Populated in run_audit once the query gate passes.
        self._pq: Optional[pd.DataFrame] = None

    def get_audit_type(self) -> str:
        return "query_count"

    def _gsc_has_column(self, column: str) -> bool:
        """Guard against the GSC frame's own columns (BaseAuditor.has_column
        inspects the crawl df, not gsc_df)."""
        return self.gsc_df is not None and column in self.gsc_df.columns

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        if self.gsc_df is None or len(self.gsc_df) == 0:
            return self.issues
        if not self._gsc_has_column("page"):
            return self.issues

        # Every check below counts DISTINCT queries per page. Without a query
        # column the export is page-level only and the method cannot run.
        if not self._gsc_has_column("query"):
            self._emit_query_level_missing()
            return self.issues

        self._pq = self._build_page_query_frame()
        if self._pq is None or self._pq.empty:
            return self.issues

        self._check_dead_page_query_breadth()
        self._check_position_band_distribution()
        self._check_content_to_query_ratio()
        self._check_lead_query_dilution()

        return self.issues

    def _emit_query_level_missing(self) -> None:
        """Explain that only page-level GSC was supplied so breadth can't run."""
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.CONTENT,
            issue_type="query_count_needs_query_level_gsc",
            title="Query-breadth analysis skipped — page-level GSC only",
            description=(
                "The query-counting method measures how many DISTINCT queries "
                "each URL is served for, which is a proxy for the weight Google "
                "assigns the page. The GSC export provided is page-level only "
                "(no 'query' dimension), so distinct-query breadth cannot be "
                "computed and all four query-count checks are skipped."
            ),
            recommendation=(
                "Re-export GSC Search Analytics with BOTH the Query and Page "
                "dimensions included (or export the per-page query breakdown). "
                "With query-level rows the auditor can flag dead pages by query "
                "breadth, low-visibility position clustering, content-to-query "
                "mismatch, and lead-query dilution."
            ),
            impact=(
                "Distinct-query breadth is one of the clearest single-snapshot "
                "signals of a page's value to Google. Without it, prune and "
                "repurpose candidates that a query-level export would surface "
                "stay invisible."
            ),
        )

    # ------------------------------------------------------------------
    # Shared aggregation
    # ------------------------------------------------------------------

    def _indexable_urls(self) -> Optional[set[str]]:
        """Return the set of indexable crawl URLs, or None if undeterminable.

        Used to restrict query-breadth findings to pages that can actually rank.
        Returns None (meaning "don't filter") when the crawl df lacks the url or
        indexability columns, so the auditor degrades gracefully.
        """
        if not (self.has_column("url") and self.has_column("indexability")):
            return None
        mask = self.df["indexability"].astype(str).str.lower() == "indexable"
        return set(self.df.loc[mask, "url"].astype(str))

    def _build_page_query_frame(self) -> Optional[pd.DataFrame]:
        """Collapse GSC rows to one row per (page, query) slice.

        Aggregates position (mean), impressions (sum) and clicks (sum) where
        those columns exist. Restricts to indexable pages when the crawl df can
        tell us which URLs are indexable.
        """
        gsc = self.gsc_df.copy()
        gsc["page"] = gsc["page"].astype(str)
        gsc["query"] = gsc["query"].astype(str).str.strip()
        gsc = gsc[gsc["query"] != ""]
        if gsc.empty:
            return None

        indexable = self._indexable_urls()
        if indexable is not None:
            gsc = gsc[gsc["page"].isin(indexable)]
            if gsc.empty:
                return None

        agg_kwargs: dict[str, tuple[str, str]] = {}
        if "position" in gsc.columns:
            agg_kwargs["position"] = ("position", "mean")
        if "impressions" in gsc.columns:
            agg_kwargs["impressions"] = ("impressions", "sum")
        if "clicks" in gsc.columns:
            agg_kwargs["clicks"] = ("clicks", "sum")

        if agg_kwargs:
            pq = gsc.groupby(["page", "query"]).agg(**agg_kwargs).reset_index()
        else:
            # No metric columns — still have distinct (page, query) pairs.
            pq = gsc[["page", "query"]].drop_duplicates().reset_index(drop=True)
        return pq

    def _distinct_queries_by_page(self) -> pd.Series:
        """Distinct query count per page (one entry per (page, query) already)."""
        return self._pq.groupby("page").size()

    def _band(self, distinct: int) -> str:
        """DFC breadth band label for a distinct-query count."""
        if distinct < LITTLE_VALUE_QUERY_BAND:
            return "little_value"
        if distinct < MEDIUM_QUERY_BAND:
            return "medium"
        return "healthy"

    # ------------------------------------------------------------------
    # CHECK 1 — dead page by query breadth
    # ------------------------------------------------------------------

    def _check_dead_page_query_breadth(self) -> None:
        """Flag indexable pages served for very few distinct queries.

        Near-zero-breadth pages carry no weight in Google's eyes — the clearest
        prune/repurpose candidates. Reports the full band distribution for
        context so the count is read against the site's scale.
        """
        counts = self._distinct_queries_by_page()
        if counts.empty:
            return

        impr = None
        if "impressions" in self._pq.columns:
            impr = self._pq.groupby("page")["impressions"].sum()

        band_counts = {"little_value": 0, "medium": 0, "healthy": 0}
        little_value: list[dict] = []
        for page, distinct in counts.items():
            band = self._band(int(distinct))
            band_counts[band] += 1
            if band == "little_value":
                little_value.append({
                    "url": page,
                    "distinct_queries": int(distinct),
                    "impressions": int(impr.get(page, 0)) if impr is not None else None,
                    "is_dead": int(distinct) <= DEAD_QUERY_THRESHOLD,
                })

        if not little_value:
            return

        little_value.sort(key=lambda c: c["distinct_queries"])
        dead_count = sum(1 for c in little_value if c["is_dead"])
        affected = [c["url"] for c in little_value][:MAX_AFFECTED_URLS]
        examples = []
        for c in little_value[:5]:
            impr_txt = (
                f", {c['impressions']:,} impressions" if c["impressions"] is not None else ""
            )
            tag = " [near-zero]" if c["is_dead"] else ""
            examples.append(f"{c['url']} — {c['distinct_queries']} distinct queries{impr_txt}{tag}")

        logger.info(
            "query_count: %d little-value pages (%d near-zero)",
            len(little_value), dead_count,
        )

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.CONTENT_PRUNING,
            issue_type="query_breadth_dead_pages",
            title=f"{len(little_value)} pages serve very few distinct queries",
            description=(
                f"{len(little_value)} indexable pages are served for fewer than "
                f"{LITTLE_VALUE_QUERY_BAND} distinct queries — the 'little value' "
                "band in the query-counting method. The distinct-query count a "
                "URL earns is a proxy for the weight Google assigns it: money "
                f"pages rank for hundreds of queries (healthy = {MEDIUM_QUERY_BAND}+), "
                f"while a page served for {DEAD_QUERY_THRESHOLD} or fewer carries "
                f"near-zero weight. {dead_count} of the flagged pages are in that "
                "near-zero range and are the sharpest prune/repurpose candidates.\n\n"
                f"Band distribution across pages in GSC: "
                f"{band_counts['little_value']} little-value, "
                f"{band_counts['medium']} medium, {band_counts['healthy']} healthy.\n\n"
                "Examples (fewest queries first):\n"
                + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(little_value),
            recommendation=(
                "Work the near-zero pages first. For each: decide between "
                "consolidating its unique content into a stronger on-topic page "
                "(then 301 the URL), rewriting it to target a real query cluster "
                "with demonstrated demand, or removing it if it serves no intent. "
                "Pages that already rank for a broad query set should be left "
                "alone — this list is specifically the low-breadth tail. Bands are "
                "calibrated for established sites; on a small or new site, a low "
                "count may just reflect the site's age rather than a dead page."
            ),
            impact=(
                "Pages that earn almost no query breadth contribute little "
                "organic value while still consuming crawl budget and diluting "
                "the site's average page quality. Consolidating or repurposing "
                "them concentrates ranking signal on pages that can actually earn "
                "breadth."
            ),
            additional_data={
                "little_value_count": len(little_value),
                "dead_count": dead_count,
                "band_counts": band_counts,
                "little_value_band": LITTLE_VALUE_QUERY_BAND,
                "dead_threshold": DEAD_QUERY_THRESHOLD,
            },
        )

    # ------------------------------------------------------------------
    # CHECK 2 — position-band distribution
    # ------------------------------------------------------------------

    def _check_position_band_distribution(self) -> None:
        """Surface pages whose queries sit almost entirely in positions 21-100.

        Such pages carry impressions but essentially no click visibility (page 3
        and beyond). They're improvement candidates: the demand exists, but the
        page never surfaces high enough to earn the click. Informational.
        """
        if "position" not in self._pq.columns:
            return

        stuck: list[dict] = []
        for page, group in self._pq.groupby("page"):
            positions = group["position"].dropna()
            positions = positions[
                (positions >= 1) & (positions <= LOW_VISIBILITY_MAX_POSITION)
            ]
            distinct = len(positions)
            if distinct < MIN_QUERIES_FOR_BAND:
                continue

            low_vis = positions[positions > LOW_VISIBILITY_MIN_POSITION]
            fraction = len(low_vis) / distinct
            if fraction < STUCK_QUERY_FRACTION:
                continue

            impressions = (
                int(group["impressions"].sum())
                if "impressions" in group.columns
                else None
            )
            stuck.append({
                "url": page,
                "distinct_queries": distinct,
                "low_vis_fraction": round(fraction, 2),
                "impressions": impressions,
            })

        if not stuck:
            return

        # Rank by impressions (demand at stake) then breadth.
        stuck.sort(
            key=lambda c: (c["impressions"] or 0, c["distinct_queries"]),
            reverse=True,
        )
        affected = [c["url"] for c in stuck][:MAX_AFFECTED_URLS]
        examples = []
        for c in stuck[:5]:
            impr_txt = f", {c['impressions']:,} impressions" if c["impressions"] is not None else ""
            examples.append(
                f"{c['url']} — {int(c['low_vis_fraction'] * 100)}% of "
                f"{c['distinct_queries']} queries in positions 21-100{impr_txt}"
            )

        self.create_issue(
            severity=Severity.LOW,
            category=AuditCategory.CONTENT,
            issue_type="queries_stuck_low_visibility",
            title=f"{len(stuck)} pages: queries stuck in positions 21-100",
            description=(
                f"{len(stuck)} pages have at least {int(STUCK_QUERY_FRACTION * 100)}% "
                "of their distinct queries ranking in positions 21-100 — deep on "
                "page three or beyond, where impressions accrue but clicks do not. "
                "The demand exists (Google serves the page for these queries) but "
                "the page never surfaces high enough to earn a visit. These are "
                "improvement candidates, not prune candidates: they already have "
                "topical relevance to the query set.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(stuck),
            recommendation=(
                "Treat these as ranking-lift targets. For each page, pull its "
                "position-21-100 query cluster from GSC, confirm the queries share "
                "a single intent, then strengthen the page against that cluster: "
                "add depth that directly answers the queries, improve internal "
                "links from topically-related pages, and check the title/H1 match "
                "the cluster. If several stuck pages target the same cluster, "
                "consolidate them into one authority page rather than lifting each "
                "separately."
            ),
            impact=(
                "Queries stuck beyond position 20 represent captured demand with "
                "zero realised clicks. A page pushed from position 25 to the first "
                "page converts existing impressions into traffic without needing "
                "new demand."
            ),
            additional_data={
                "stuck_count": len(stuck),
                "position_floor": LOW_VISIBILITY_MIN_POSITION,
                "stuck_fraction": STUCK_QUERY_FRACTION,
            },
        )

    # ------------------------------------------------------------------
    # CHECK 3 — content-to-query ratio
    # ------------------------------------------------------------------

    def _check_content_to_query_ratio(self) -> None:
        """Flag heavy pages (>=1500 words) serving few distinct queries.

        Joins crawl word_count with the distinct-query count. A page carrying
        substantial content that earns almost no query breadth is either
        valueless or out of scope for search demand — the effort isn't
        converting to coverage. Excludes category/collection nav pages, which
        legitimately carry heavy body text without ranking as an answer.
        """
        if not (self.has_column("url") and self.has_column("word_count")):
            return

        words = pd.to_numeric(self.df["word_count"], errors="coerce")
        word_by_url = dict(zip(self.df["url"].astype(str), words))

        counts = self._distinct_queries_by_page()
        if counts.empty:
            return

        flagged: list[dict] = []
        for page, distinct in counts.items():
            if self._is_category_url(page):
                continue
            wc = word_by_url.get(page)
            if wc is None or pd.isna(wc):
                continue
            if wc < HIGH_WORD_COUNT:
                continue
            if int(distinct) >= LOW_QUERY_FOR_CONTENT:
                continue
            flagged.append({
                "url": page,
                "word_count": int(wc),
                "distinct_queries": int(distinct),
            })

        if not flagged:
            return

        # Worst ratio first (most words per query).
        flagged.sort(
            key=lambda c: c["word_count"] / max(c["distinct_queries"], 1),
            reverse=True,
        )
        affected = [c["url"] for c in flagged][:MAX_AFFECTED_URLS]
        examples = [
            f"{c['url']} — {c['word_count']:,} words but only "
            f"{c['distinct_queries']} distinct queries"
            for c in flagged[:5]
        ]

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.CONTENT,
            issue_type="high_word_low_query_ratio",
            title=f"{len(flagged)} heavy pages earn little query breadth",
            description=(
                f"{len(flagged)} pages carry {HIGH_WORD_COUNT:,}+ words yet are "
                f"served for fewer than {LOW_QUERY_FOR_CONTENT} distinct queries. "
                "Substantial content that earns almost no query breadth is a "
                "query-counting red flag: the page is either valueless (the "
                "content doesn't match how people search) or out of scope (it "
                "targets an intent with little demand). The writing effort isn't "
                "converting into coverage. Category and collection nav pages are "
                "excluded from this check.\n\n"
                "Examples (most words per query first):\n"
                + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(flagged),
            recommendation=(
                "For each page, pull the queries it does earn and check whether "
                "they point to a coherent intent. If they do, the page is "
                "mistargeted — re-angle the title, H1 and opening to match how the "
                "audience actually searches, then confirm the body answers that "
                "intent. If the queries are incoherent or near-zero, the topic may "
                "have no real demand: consolidate the usable content into a "
                "stronger page or repurpose it off-search (email, sales enablement). "
                "Do not simply add more words — breadth comes from intent match, "
                "not length."
            ),
            impact=(
                "Long pages that earn no breadth tie up production effort and "
                "crawl budget while returning little organic value. Re-angling or "
                "consolidating them converts sunk content into either ranking "
                "coverage or a leaner, more focused site."
            ),
            additional_data={
                "flagged_count": len(flagged),
                "word_threshold": HIGH_WORD_COUNT,
                "query_threshold": LOW_QUERY_FOR_CONTENT,
            },
        )

    @staticmethod
    def _is_category_url(url: str) -> bool:
        """True for nav/listing URLs exempt from the content-to-query check."""
        if not isinstance(url, str):
            return False
        u = url.lower()
        return any(marker in u for marker in _CATEGORY_URL_MARKERS)

    # ------------------------------------------------------------------
    # CHECK 4 — serve-rate / lead-query dilution
    # ------------------------------------------------------------------

    def _check_lead_query_dilution(self) -> None:
        """Flag pages whose top served query is absent from their title/H1.

        For each page the lead query is the distinct query with the most
        impressions. Comparing its content tokens against the page's title + H1
        tokens measures whether Google's strongest demand signal for the page is
        reflected in the page's own focus signals. Low overlap means Google is
        unsure what the page is about — topical dilution that caps average
        position across the whole query set.
        """
        if "impressions" not in self._pq.columns:
            return
        if not (self.has_column("url")
                and (self.has_column("title") or self.has_column("h1"))):
            return

        page_tokens = self._build_page_focus_tokens()
        if not page_tokens:
            return

        # Lead query per page = highest-impression (page, query) row.
        idx = self._pq.groupby("page")["impressions"].idxmax()
        lead = self._pq.loc[idx]

        diluted: list[dict] = []
        for _, row in lead.iterrows():
            page = row["page"]
            impressions = row.get("impressions")
            if impressions is None or pd.isna(impressions) or impressions < MIN_PAGE_IMPRESSIONS:
                continue

            focus = page_tokens.get(page)
            if not focus:
                continue
            q_tokens = _tokenize(str(row["query"]))
            if not q_tokens:
                continue

            overlap = len(q_tokens & focus) / len(q_tokens)
            if overlap >= LEAD_QUERY_OVERLAP_FLOOR:
                continue

            diluted.append({
                "url": page,
                "lead_query": str(row["query"]),
                "impressions": int(impressions),
                "overlap": round(overlap, 2),
            })

        if not diluted:
            return

        diluted.sort(key=lambda c: c["impressions"], reverse=True)
        affected = [c["url"] for c in diluted][:MAX_AFFECTED_URLS]
        examples = [
            f"{c['url']} — lead query \"{c['lead_query']}\" "
            f"({c['impressions']:,} impressions), {int(c['overlap'] * 100)}% "
            "of query terms in title/H1"
            for c in diluted[:5]
        ]

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.CONTENT,
            issue_type="lead_query_title_mismatch",
            title=f"{len(diluted)} pages: top query missing from title/H1",
            description=(
                f"{len(diluted)} pages earn most of their impressions from a lead "
                "query whose terms barely appear in the page's own title and H1 "
                f"(under {int(LEAD_QUERY_OVERLAP_FLOOR * 100)}% overlap). The lead "
                "query is the strongest demand signal Google has for the page, so "
                "when the page's focus signals don't reflect it, Google is unsure "
                "what the page is about. That uncertainty caps the average "
                "position across the whole query set — the page ranks for the "
                "query but never confidently.\n\n"
                "Examples (highest impressions first):\n"
                + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(diluted),
            recommendation=(
                "For each page, confirm the lead query reflects the intent the "
                "page should own. If it does, rework the title and H1 to lead with "
                "the query's core terms (intent match, not keyword stuffing) and "
                "make sure the opening paragraph answers that query directly. If "
                "the lead query points to a different intent than the page targets, "
                "the mismatch is strategic — either the page is cannibalising a "
                "better-fit URL or it needs to be split. Cross-check against the "
                "cannibalization findings before rewriting."
            ),
            impact=(
                "When the page's focus signals contradict the query Google serves "
                "it for, the page ranks tentatively and leaves position on the "
                "table across its entire query set. Aligning title/H1 with the "
                "lead query is a low-effort, high-leverage focus fix."
            ),
            additional_data={
                "diluted_count": len(diluted),
                "overlap_floor": LEAD_QUERY_OVERLAP_FLOOR,
                "min_impressions": MIN_PAGE_IMPRESSIONS,
            },
        )

    def _build_page_focus_tokens(self) -> dict[str, set[str]]:
        """Map each crawl URL to the token set of its title + H1."""
        has_title = self.has_column("title")
        has_h1 = self.has_column("h1")
        tokens: dict[str, set[str]] = {}
        for _, row in self.df.iterrows():
            url = row.get("url")
            if not isinstance(url, str):
                continue
            combined = set()
            if has_title:
                combined |= _tokenize(str(row.get("title", "")))
            if has_h1:
                combined |= _tokenize(str(row.get("h1", "")))
            if combined:
                tokens[url] = combined
        return tokens
