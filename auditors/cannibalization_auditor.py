"""Keyword Cannibalization Auditor.

Detects when multiple URLs from the same domain target the same query
intent, splitting ranking signals between them. This is one of the most
common and most underdiagnosed SEO problems — sites pour effort into
"improving both pages" when the right answer is to consolidate, 301, or
differentiate intent.

DETECTION TIERS
---------------
Tier 1 (full GSC + live SERP): catches the hardest cases — pages with
    different titles competing for the same query because Google sees
    them as semantic duplicates.
Tier 2 (URL-level GSC only): catches the common pattern — multiple
    pages ranking for the same query in GSC's per-URL data.
Tier 3 (no GSC, fallback): title + slug + H1 similarity clustering.
    Catches the most obvious cases (templated duplicates) but misses
    semantic overlap.

CANNIBALIZATION CAN HAPPEN AT ANY POSITION. The most damaging
cannibalization is in positions 1-3 because real captured visibility is
being diluted. Position 20+ cannibalization matters less because the
clusters aren't generating meaningful traffic in the first place.

WHY IT HAPPENS (Web Linker / Matt Cutts mechanism, episode 1,030 of the
Edward Show, 2026):
    Cannibalization is a duplicative-entry problem in Google's index.
    BERT-driven semantic indexing decides two pages are too similar to
    coexist in the top 10 for a query. The canonical-tag mechanism
    designed to handle technical duplicates does NOT catch semantic
    overlap. Google rotates between the pages, neither ranks
    consistently, traffic suffers. The fix is consolidation, not "make
    both pages stronger."

ROI-FIRST PRIORITIZATION
------------------------
Not every cannibalization cluster is worth fixing. Edward (Edward Show
ep. 1,030): "It's so easy to spend a ton of time fixing cannibalization
for keywords that are not going to bring you money." The auditor scores
each cluster on commercial intent + ranking proximity to revenue +
impression volume, then surfaces a Priority A/B/C tier. Priority A =
money keywords already close to ranking. Priority C = informational
clusters at deep positions = noise. Agencies should fix Priority A
first; Priority B second only if bandwidth allows; Priority C should
typically be skipped.

RESOLUTION PATHS (4 options, in order of preference)
----------------------------------------------------
1. CONSOLIDATE: pick the strongest URL, merge unique content from the
    losers into it, 301 the losers. Most common, most effective.
2. DIFFERENTIATE: when both pages should genuinely exist (informational
    vs transactional), rewrite each to target distinct intent.
3. CANONICALIZE: hub vs deep-dive coexistence — point a canonical from
    the deep-dive to the hub. Note: canonicals are hints, not commands.
4. REPUBLISH UNDER NEW SLUG: when consolidation hasn't moved rankings
    after 30+ days because Google's duplicate cluster is stuck on the
    old slugs, manual remove + no-index both, then republish content
    under fresh slug + new title + new H1. Last resort. Loses backlink
    equity and resets ranking history.

WINNER SELECTION RULE (multi-factor, in order)
----------------------------------------------
1. GSC current position (lower = better)
2. GSC clicks last 90 days (higher = better)
3. Backlinks pointing to the URL (higher = better)
4. Tie-breaker: fewer incoming internal links to update = lower
    consolidation effort = preferred winner

References:
- Reddit r/SEO post (legitimate_salary_108): https://reddit.com/r/SEO/...
- Edward Show episode 1,030 commentary
- Web Linker (r/SEO moderator) duplicative-entry mechanism explanation
- Matt Cutts "How does Google handle duplicate content?" video
"""

from __future__ import annotations

import re
import statistics
from collections import defaultdict
from typing import Any, Optional

import pandas as pd

from .base_auditor import BaseAuditor, is_empty_or_missing
from models.audit_result import AuditCategory, AuditIssue, Severity


# =============================================================================
# DETECTION THRESHOLDS — calibrated from /content-refresh client experience
# and the Reddit r/SEO cannibalization thread (2026)
# =============================================================================

MIN_IMPRESSIONS_PER_PAIR = 50
"""Filter out (query, URL) pairs with fewer impressions than this. Below
this threshold, the URL probably isn't actually competing for the query —
it's a long-tail accidental match."""

MIN_URLS_PER_QUERY = 2
"""A query needs at least this many URLs ranking to be flagged as
cannibalizing."""

TOP_RANK_THRESHOLD = 30
"""Only count URLs ranking in the top 30 — beyond that, they're not
really competing for visibility."""

CRITICAL_URLS_THRESHOLD = 4
"""Queries with this many or more cannibalizing URLs are flagged Critical
(usually a systemic problem like template duplication)."""

HIGH_IMPRESSIONS_THRESHOLD = 1000
"""Cannibalizing clusters with this much aggregate impressions volume
are HIGH severity. Below this, they're MEDIUM."""

TOP_3_POSITION_BAR = 3
"""URLs ranking at this position or better count as 'top-3' for severity
weighting. Top-3 cannibalization is the most damaging — real visibility
being diluted, not theoretical."""

SERP_OVERLAP_SAME_INTENT_THRESHOLD = 0.70
"""Reddit r/SEO post threshold (legitimate_salary_108): when the top-10
SERPs of two queries overlap by more than this fraction, Google sees
them as targeting the same intent. Used in Tier 1 detection to catch
cannibalization where titles differ but intent is identical."""

POSITION_VOLATILITY_SWING_THRESHOLD = 20
"""When a single URL's GSC position swings by this many places or more
across the analysis window, flag as 'rotation battle' candidate. Web
Linker's example: page introduced Feb 21, position rotation pulled both
pages out of the visible index within weeks."""

YEAR_URL_PATTERN = re.compile(r"\b(20\d{2})\b")
"""Detect year-versioned URLs like /best-tools-2024/, /best-tools-2025/.
These compete with each other AND with the evergreen version."""

CITY_TOKEN_PATTERN = re.compile(
    r"-(salt-lake-city|salt-lake|st-george|west-jordan|west-valley|"
    r"south-jordan|north-salt-lake|north-ogden|spanish-fork|cedar-city|"
    r"pleasant-grove|american-fork|park-city|"
    r"sandy|orem|provo|ogden|lehi|draper|murray|tooele|layton|"
    r"riverton|herriman|highland|salem|midvale|kearns|bluffdale|"
    r"springville|millcreek|"
    r"taylorsville)(-utah)?/?$"
)
"""Patterns identifying URLs that differ only by city slug. These are
intentional location pages, not cannibalization."""

COMMERCIAL_INTENT_VALUES = {"transactional", "commercial"}
"""DataForSEO search_intent values that mark a query as money-bearing.
Used in ROI-first prioritization."""


# =============================================================================
# SEED-TERM / MIXED-INTENT GUARD — false-positive prevention
# =============================================================================
#
# An ambiguous seed query (e.g., "flushometer", "manabloc", "urinal") can
# legitimately surface 2+ URLs from the same domain in the SERP without
# those URLs cannibalizing each other — they may be answering different
# intents (definition vs commercial vs adjacent topic) within the same
# mixed-intent SERP. Flagging these as cannibalization produces false
# positives that lead to incorrect consolidation recommendations.
#
# The guard:
#   1. Detect "seed query" = short query (≤2 words) lacking service /
#      geo / intent modifiers
#   2. Detect "different page topics" = cluster URLs whose normalized
#      title+H1 similarity falls below threshold
#   3. When BOTH apply, downgrade to "REVIEW" tier — flagged for manual
#      review rather than auto-consolidation

SEED_QUERY_MAX_WORDS = 2
"""Queries with this many words or fewer are seed-term candidates."""

SERVICE_VERB_PATTERN = re.compile(
    r"\b(repair|repairs|repairing|install|installs|installation|"
    r"installing|replace|replaces|replacement|replacing|fix|fixes|"
    r"fixing|clean|cleaning|service|services|maintenance|"
    r"unclog|unclogs|unclogging|inspection|emergency|24[-\s]?7|"
    r"24[-\s]?hour|recovery|consult|consultation|assessment|quote|"
    r"estimate|cost|price|near\s?me)\b",
    re.I,
)
"""Service verbs and intent qualifiers that indicate a specific
commercial query, not an ambiguous seed."""

GEO_MODIFIER_PATTERN = re.compile(
    r"\b(utah|ut|salt\s?lake|slc|sandy|provo|ogden|west\s?jordan|"
    r"south\s?jordan|draper|murray|orem|park\s?city|lehi|saratoga|"
    r"riverton|herriman|tooele|bountiful|layton|kaysville|farmington|"
    r"clearfield|hurricane|local|nearby|near\s?me)\b",
    re.I,
)
"""Geographic modifiers that anchor a query to commercial intent."""

INTENT_QUALIFIER_PATTERN = re.compile(
    r"\b(best|top|cheap|affordable|premium|professional|reliable|"
    r"trusted|certified|licensed|how\s?to|why|what|where|when|guide|"
    r"tutorial|tips|steps|vs|versus|compare|comparison|review|"
    r"reviews|recommended)\b",
    re.I,
)
"""Intent qualifiers — when present, the query has a clear (commercial
or informational) intent and isn't an ambiguous seed."""

PAGE_TOPIC_SIMILARITY_THRESHOLD = 0.30
"""When cluster URLs' normalized title+H1 similarity falls below this
fraction (Jaccard on tokens), the pages are targeting different topics.
Combined with seed-query detection, this signals a false positive."""


# =============================================================================
# QUERY-INTENT EXTRACTION — for winner-sanity + architectural-fit checks
# =============================================================================
#
# When the auditor picks a "winner candidate" from a cluster, we need
# to verify the winner page is actually aligned with the query intent.
# A query like "emergency plumber salt lake city" has two modifiers:
#   - geo: "salt lake city"
#   - service: "emergency plumber"
# A winner whose URL/title contains "sugar house" (different city) or
# is a generic homepage / About page (no service alignment) is a false
# winner — picked on metrics alone without query-intent alignment.
#
# These patterns extract the modifiers from a query so the auditor can
# verify the winner matches them.

GEO_TOKEN_PATTERN = re.compile(
    r"\b("
    r"salt\s?lake\s?city|salt\s?lake|slc|"
    r"west\s?valley\s?city|west\s?valley|"
    r"south\s?jordan|west\s?jordan|north\s?salt\s?lake|north\s?ogden|"
    r"sugar\s?house|park\s?city|cedar\s?city|spanish\s?fork|"
    r"american\s?fork|pleasant\s?grove|"
    r"sandy|provo|orem|ogden|draper|murray|tooele|layton|"
    r"riverton|herriman|highland|lehi|saratoga|kaysville|farmington|"
    r"clearfield|bountiful|midvale|kearns|bluffdale|springville|"
    r"millcreek|taylorsville|hurricane|st\s?george|cedar|"
    r"utah|ut|near\s?me"
    r")\b",
    re.I,
)
"""Geographic modifiers that anchor a query to a specific market.
When a query contains one of these, the winner page should reference
the same geography in its slug, title, or H1. If the query says SLC
and the winner says Sugar House, that's a geographic mismatch."""

SERVICE_VERB_KEYWORDS = re.compile(
    r"\b("
    r"emergency|24[-\s]?hour|24[-\s]?7|"
    r"repair|repairs|repairing|"
    r"install|installs|installation|installing|"
    r"replace|replaces|replacement|replacing|"
    r"fix|fixes|fixing|"
    r"clean|cleans|cleaning|"
    r"unclog|unclogs|unclogging|"
    r"inspection|inspect|inspecting|"
    r"service|services|servicing|"
    r"recovery|consult|consultation|assessment|quote|estimate"
    r")\b",
    re.I,
)
"""Service-intent keywords. When a query contains one of these AND
identifies a specific service (drain, sewer, water heater, etc.), the
winner page should be the dedicated service page for that service —
not the homepage, an About page, or a generic city landing page."""

PRIMARY_SERVICE_KEYWORDS = re.compile(
    r"\b("
    r"plumber|plumbing|plumb|"
    r"drain|sewer|"
    r"water\s?heater|hot\s?water|tankless|"
    r"hydro\s?jet|hydrojet|"
    r"toilet|faucet|sink|"
    r"leak|pipe|repipe|repiping|"
    r"garbage\s?disposal|"
    r"flushometer|"
    r"reverse\s?osmosis|water\s?softener|water\s?filtration|"
    r"frozen\s?pipe|main\s?water\s?line|water\s?main"
    r")\b",
    re.I,
)
"""Primary service nouns. Combined with SERVICE_VERB_KEYWORDS, these
tell us what service the query is asking about (e.g., 'emergency'
+ 'plumber' = emergency plumber service, 'water heater' + 'repair' =
water heater repair service)."""

GENERIC_PAGE_SLUGS = re.compile(
    r"^/(|home|about|about-us|contact|contact-us|get-in-touch|"
    r"get-a-quote|financing|financing-plumbing-utah|reviews|"
    r"testimonials|careers|blog|news|privacy|privacy-policy|terms|"
    r"sitemap|service-areas)/?$",
    re.I,
)
"""Generic non-service-page paths. When one of these is picked as a
winner for a service+geo query, that's a service-mismatch — the
winner should be a dedicated service page, not the homepage or About
page."""

CATEGORY_ARCHIVE_PATTERN = re.compile(r"^/category/", re.I)
"""WordPress / blog category archive paths. These are not canonical
service pages — they're auto-generated archive listings of blog posts.
Should not be picked as architecturally-correct service pages."""

SERVICE_TERM_EQUIVALENCE = {
    # Hot water and water heater are interchangeable terms for the
    # same service. The query "hot water heater repair" and a page
    # called "water heater repair" are about the same thing.
    "hotwater": {"hotwater", "waterheater"},
    "waterheater": {"hotwater", "waterheater"},
}
"""Service terms that are semantically equivalent for matching
purposes. Used by the architectural-fit detection so a query
mentioning 'hot water' matches pages about 'water heaters' and vice
versa. Add equivalence groups as new client patterns emerge."""


def _expand_service_terms(terms: set[str]) -> set[str]:
    """Expand a set of service tokens with their equivalents."""
    expanded = set(terms)
    for t in terms:
        expanded |= SERVICE_TERM_EQUIVALENCE.get(t, {t})
    return expanded


# =============================================================================
# CANNIBALIZATION AUDITOR
# =============================================================================


class CannibalizationAuditor(BaseAuditor):
    """Detect keyword cannibalization across URLs.

    Detection runs in tiers based on what data is available:
        Tier 1: full GSC + live SERP overlap (highest precision)
        Tier 2: URL-level GSC only (catches common patterns)
        Tier 3: title + slug + H1 fallback (no GSC required)

    Each detected cluster is scored on commercial intent + rank proximity
    + impression volume to produce a Priority A/B/C tier so agencies fix
    high-ROI clusters first.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        gsc_query_page_data: Optional[pd.DataFrame] = None,
        gsc_daily_position_data: Optional[pd.DataFrame] = None,
        live_serp_overlap_fn: Optional[Any] = None,
        keyword_intent_lookup: Optional[dict[str, str]] = None,
    ) -> None:
        """Initialize with crawl data and optional richer data sources.

        Args:
            df: Screaming Frog DataFrame (always required)
            gsc_query_page_data: GSC export with query + page + position
                + impressions + clicks (Tier 1 / Tier 2 detection)
            gsc_daily_position_data: GSC daily-granularity position data
                for rotation-battle detection (graceful degradation when
                absent)
            live_serp_overlap_fn: callable(query_a, query_b) -> float
                returning fraction of overlapping URLs in top-10 SERPs.
                When provided, enables Tier 1 SERP-overlap detection.
                Function should handle its own caching and rate limits.
            keyword_intent_lookup: dict[query -> intent] from DataForSEO
                Labs. Used for ROI-first prioritization.
        """
        super().__init__(df)
        self.gsc_query_page_data = gsc_query_page_data
        self.gsc_daily_position_data = gsc_daily_position_data
        self.live_serp_overlap_fn = live_serp_overlap_fn
        self.keyword_intent_lookup = keyword_intent_lookup or {}

    def get_audit_type(self) -> str:
        return "technical"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()
        self._check_data_availability()

        # Detection waterfall: highest-precision tier first
        clusters: list[dict] = []

        if self._has_gsc_query_page_data():
            clusters.extend(self._detect_via_gsc_query_page())
            if self.live_serp_overlap_fn is not None:
                clusters.extend(self._detect_via_serp_overlap(clusters))
        elif self._has_url_level_gsc_data():
            clusters.extend(self._detect_via_url_level_gsc())
        else:
            clusters.extend(self._detect_via_title_slug_h1())

        # Always run year-versioned URL detection (cheap, no GSC needed)
        clusters.extend(self._detect_year_versioned_urls())

        # Optional: rotation-battle detection if daily GSC data is present
        if self.gsc_daily_position_data is not None:
            clusters.extend(self._detect_rotation_battles())

        if not clusters:
            return self.issues

        # Deduplicate clusters by URL set (different detection methods
        # may have surfaced the same cluster)
        clusters = self._deduplicate_clusters(clusters)

        # Score and prioritize each cluster
        for cluster in clusters:
            self._enrich_cluster_with_priority(cluster)

        # False-positive guard: downgrade ambiguous-seed clusters with
        # divergent page topics to REVIEW tier
        for cluster in clusters:
            self._apply_false_positive_filter(cluster)

        # Winner selection + query-intent alignment sanity check.
        # Attach the winner to the cluster, then verify it actually
        # matches the query's geo/service modifiers — and search for
        # an architecturally correct non-cluster page when it doesn't.
        for cluster in clusters:
            cluster["winner_candidate"] = self._select_winner(cluster)
            self._apply_winner_sanity_check(cluster)

        # Emit aggregated issue grouped by priority tier
        self._emit_clusters(clusters)

        return self.issues

    # =========================================================================
    # AVAILABILITY DIAGNOSTIC
    # =========================================================================

    def _has_gsc_query_page_data(self) -> bool:
        """True when a separate GSC query+page export was provided."""
        if self.gsc_query_page_data is None:
            return False
        required_cols = {"query", "page", "position", "impressions"}
        return required_cols.issubset(set(self.gsc_query_page_data.columns))

    def _has_url_level_gsc_data(self) -> bool:
        """True when SF crawl has GSC integration columns at URL level."""
        return (
            self.has_column("gsc_position")
            and self.has_column("gsc_impressions")
            and self.has_column("title")
        )

    def _check_data_availability(self) -> None:
        """Emit an INSIGHT issue describing which detection tier is active."""
        if self._has_gsc_query_page_data() and self.live_serp_overlap_fn:
            tier = "Tier 1 (full): GSC query/page + live SERP overlap"
            recommendation = (
                "All detection methods active. SERP-overlap analysis will "
                "catch cannibalization where titles differ but Google "
                "treats two queries as the same intent."
            )
        elif self._has_gsc_query_page_data():
            tier = "Tier 1 (partial): GSC query/page (no live SERP)"
            recommendation = (
                "Per-query GSC data is available but no live SERP function "
                "was provided. To enable Tier 1 SERP-overlap detection, "
                "pass `live_serp_overlap_fn` (e.g., a wrapper around "
                "DataForSEO `serp_organic_live_advanced` with caching)."
            )
        elif self._has_url_level_gsc_data():
            tier = "Tier 2: URL-level GSC integration"
            recommendation = (
                "URL-level GSC data is present. For Tier 1 precision, "
                "supply a separate GSC query/page export — this catches "
                "cannibalization where titles differ but intent overlaps."
            )
        else:
            tier = "Tier 3 (fallback): title + slug + H1 similarity"
            recommendation = (
                "No GSC data detected. Re-run the Screaming Frog crawl "
                "with the GSC API integration enabled (Configuration > "
                "API Access > Google Search Console). For best results, "
                "also export GSC query/page data separately."
            )

        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.CANNIBALIZATION,
            issue_type="cannibalization_detection_tier",
            title=f"Cannibalization audit running: {tier}",
            description=(
                "Cannibalization detection runs in tiers based on data "
                "availability. Higher tiers catch more cases — "
                "particularly cases where titles differ but Google "
                "sees pages as semantic duplicates.\n\n"
                f"Active tier: {tier}"
            ),
            recommendation=recommendation,
            impact=(
                "Detection coverage scales with data quality. Tier 3 "
                "catches obvious template duplicates; Tier 1 catches "
                "the semantic-overlap cases that drive most measurable "
                "ranking damage."
            ),
        )

    # =========================================================================
    # TIER 1: GSC QUERY/PAGE DETECTION
    # =========================================================================

    def _detect_via_gsc_query_page(self) -> list[dict]:
        """Group GSC rows by query, flag queries with 2+ URLs ranking."""
        if not self._has_gsc_query_page_data():
            return []

        df = self.gsc_query_page_data.copy()
        df = df[df["impressions"].fillna(0) >= MIN_IMPRESSIONS_PER_PAIR]
        df = df[df["position"].fillna(999) <= TOP_RANK_THRESHOLD]
        df = df[~df["query"].apply(is_empty_or_missing)]
        df = df[~df["page"].apply(is_empty_or_missing)]

        clusters: list[dict] = []
        for query, group in df.groupby("query"):
            urls = group["page"].unique().tolist()
            if len(urls) < MIN_URLS_PER_QUERY:
                continue
            if self._is_geo_sibling_cluster(urls):
                continue
            cluster_urls = []
            for _, row in group.iterrows():
                cluster_urls.append({
                    "url": row["page"],
                    "position": float(row["position"]),
                    "impressions": int(row["impressions"]),
                    "clicks": int(row.get("clicks", 0) or 0),
                    "ctr": (
                        float(row["clicks"]) / float(row["impressions"])
                        if row.get("impressions", 0) and row.get("clicks") is not None
                        else 0.0
                    ),
                })
            clusters.append({
                "key": query,
                "detection_method": "gsc_query_page",
                "urls": cluster_urls,
                "total_impressions": sum(u["impressions"] for u in cluster_urls),
                "total_clicks": sum(u["clicks"] for u in cluster_urls),
                "best_position": min(u["position"] for u in cluster_urls),
            })
        return clusters

    # =========================================================================
    # TIER 1: SERP-OVERLAP DETECTION (cross-query intent matching)
    # =========================================================================

    def _detect_via_serp_overlap(
        self, existing_clusters: list[dict]
    ) -> list[dict]:
        """Use live SERP overlap to merge clusters across queries.

        When two queries have >70% top-10 SERP overlap, Google treats
        them as the same intent. Pages competing across both should be
        treated as a single cannibalization cluster.

        Cost-controlled: caps SERP comparisons at 20 per audit. Caller
        should provide a cached `live_serp_overlap_fn`.
        """
        if not existing_clusters or self.live_serp_overlap_fn is None:
            return []

        # Pair queries that share at least one URL — those are candidates
        # for being the "same intent"
        url_to_queries: dict[str, set[str]] = defaultdict(set)
        for cluster in existing_clusters:
            if cluster.get("detection_method") != "gsc_query_page":
                continue
            for u in cluster["urls"]:
                url_to_queries[u["url"]].add(cluster["key"])

        # Build candidate query pairs
        candidate_pairs: set[tuple[str, str]] = set()
        for queries in url_to_queries.values():
            if len(queries) < 2:
                continue
            queries_list = sorted(queries)
            for i, q1 in enumerate(queries_list):
                for q2 in queries_list[i + 1:]:
                    candidate_pairs.add((q1, q2))

        # Cap at 20 comparisons to control API cost
        MAX_SERP_COMPARISONS = 20
        if len(candidate_pairs) > MAX_SERP_COMPARISONS:
            # Prioritize pairs whose queries have the highest combined
            # impressions across existing clusters
            cluster_by_query = {c["key"]: c for c in existing_clusters
                                if c.get("detection_method") == "gsc_query_page"}
            sorted_pairs = sorted(
                candidate_pairs,
                key=lambda p: -(
                    cluster_by_query.get(p[0], {}).get("total_impressions", 0)
                    + cluster_by_query.get(p[1], {}).get("total_impressions", 0)
                ),
            )
            candidate_pairs = set(sorted_pairs[:MAX_SERP_COMPARISONS])

        # Run overlap checks
        same_intent_pairs: list[tuple[str, str, float]] = []
        for q1, q2 in candidate_pairs:
            try:
                overlap = self.live_serp_overlap_fn(q1, q2)
            except Exception:
                # Caller's responsibility to handle errors; we degrade
                # gracefully if a single comparison fails
                continue
            if overlap >= SERP_OVERLAP_SAME_INTENT_THRESHOLD:
                same_intent_pairs.append((q1, q2, overlap))

        if not same_intent_pairs:
            return []

        # Build merged-intent clusters
        cluster_by_query = {c["key"]: c for c in existing_clusters
                            if c.get("detection_method") == "gsc_query_page"}
        merged: list[dict] = []
        seen_query_sets: list[frozenset] = []
        for q1, q2, overlap in same_intent_pairs:
            c1 = cluster_by_query.get(q1)
            c2 = cluster_by_query.get(q2)
            if not c1 or not c2:
                continue
            merged_query_set = frozenset({q1, q2})
            if merged_query_set in seen_query_sets:
                continue
            seen_query_sets.append(merged_query_set)
            merged_urls = {u["url"]: u for u in c1["urls"]}
            for u in c2["urls"]:
                if u["url"] not in merged_urls:
                    merged_urls[u["url"]] = u
            urls_list = list(merged_urls.values())
            merged.append({
                "key": f"{q1} ↔ {q2}",
                "detection_method": "serp_overlap",
                "urls": urls_list,
                "total_impressions": sum(u["impressions"] for u in urls_list),
                "total_clicks": sum(u.get("clicks", 0) for u in urls_list),
                "best_position": min(u["position"] for u in urls_list),
                "serp_overlap": overlap,
                "merged_queries": [q1, q2],
            })
        return merged

    # =========================================================================
    # TIER 2: URL-LEVEL GSC DETECTION
    # =========================================================================

    def _detect_via_url_level_gsc(self) -> list[dict]:
        """Cluster URLs by normalized title using URL-level GSC data."""
        scope = self._get_indexable_html()
        if scope.empty:
            return []

        clusters_raw: dict[str, list[dict]] = defaultdict(list)
        for _, row in scope.iterrows():
            title = row.get("title", "")
            if is_empty_or_missing(title):
                continue
            url = row.get("url", "")
            position = row.get("gsc_position")
            impressions = row.get("gsc_impressions")
            clicks = row.get("gsc_clicks", 0)
            if pd.isna(position) or position > TOP_RANK_THRESHOLD:
                continue
            if pd.isna(impressions) or impressions < MIN_IMPRESSIONS_PER_PAIR:
                continue

            key = self._build_cluster_key(
                title=title,
                url=url,
                h1=row.get("h1_1") or row.get("h1") or "",
            )
            if not key:
                continue
            clusters_raw[key].append({
                "url": url,
                "title": title,
                "position": float(position),
                "impressions": int(impressions),
                "clicks": int(clicks or 0),
                "ctr": (
                    float(clicks or 0) / float(impressions)
                    if impressions else 0.0
                ),
            })

        clusters: list[dict] = []
        for key, urls in clusters_raw.items():
            if len(urls) < MIN_URLS_PER_QUERY:
                continue
            if self._is_geo_sibling_cluster([u["url"] for u in urls]):
                continue
            clusters.append({
                "key": key,
                "detection_method": "url_level_gsc",
                "urls": urls,
                "total_impressions": sum(u["impressions"] for u in urls),
                "total_clicks": sum(u["clicks"] for u in urls),
                "best_position": min(u["position"] for u in urls),
            })
        return clusters

    # =========================================================================
    # TIER 3: TITLE + SLUG + H1 FALLBACK
    # =========================================================================

    def _detect_via_title_slug_h1(self) -> list[dict]:
        """Fallback when no GSC data available — cluster by document name.

        Web Linker / Matt Cutts: Google's duplicate detection runs on
        document name (slug + page title + H1), not full content. We
        mirror that weighting here.
        """
        scope = self._get_indexable_html()
        if scope.empty or "title" not in scope.columns:
            return []

        clusters_raw: dict[str, list[dict]] = defaultdict(list)
        for _, row in scope.iterrows():
            title = row.get("title", "")
            if is_empty_or_missing(title):
                continue
            url = row.get("url", "")
            h1 = row.get("h1_1") or row.get("h1") or ""
            key = self._build_cluster_key(title=title, url=url, h1=h1)
            if not key:
                continue
            clusters_raw[key].append({"url": url, "title": title, "h1": h1})

        clusters: list[dict] = []
        for key, urls in clusters_raw.items():
            if len(urls) < MIN_URLS_PER_QUERY:
                continue
            url_strings = [u["url"] for u in urls]
            if self._is_geo_sibling_cluster(url_strings):
                continue
            clusters.append({
                "key": key,
                "detection_method": "title_slug_h1",
                "urls": urls,
                "total_impressions": 0,
                "total_clicks": 0,
                "best_position": None,
            })
        return clusters

    # =========================================================================
    # YEAR-VERSIONED URL DETECTION
    # =========================================================================

    def _detect_year_versioned_urls(self) -> list[dict]:
        """Detect URLs that differ only by a year token (best-tools-2024
        vs best-tools-2025 vs evergreen best-tools/).
        """
        scope = self._get_indexable_html()
        if scope.empty:
            return []

        # Group URLs by their de-yeared path
        path_groups: dict[str, list[dict]] = defaultdict(list)
        for _, row in scope.iterrows():
            url = row.get("url", "")
            if is_empty_or_missing(url):
                continue
            de_yeared = YEAR_URL_PATTERN.sub("YEAR", str(url))
            if de_yeared == url:
                # No year token in this URL
                continue
            path_groups[de_yeared].append({
                "url": url,
                "title": row.get("title", "") or "",
            })

        # Also include the evergreen version if it exists in the crawl
        all_urls = set(scope["url"].dropna().astype(str).tolist())

        clusters: list[dict] = []
        for de_yeared_pattern, year_urls in path_groups.items():
            if len(year_urls) < MIN_URLS_PER_QUERY:
                continue
            # Try to find an evergreen version (the same path with year
            # token removed entirely, not replaced)
            evergreen_candidate = re.sub(
                r"-?20\d{2}-?", "-", de_yeared_pattern.replace("YEAR", "")
            )
            evergreen_candidate = re.sub(r"-+", "-", evergreen_candidate)
            evergreen_candidate = evergreen_candidate.replace("-/", "/")
            evergreen_url = None
            for candidate_url in all_urls:
                if (
                    candidate_url.replace("--", "-").rstrip("-/") ==
                    evergreen_candidate.rstrip("-/")
                ):
                    evergreen_url = candidate_url
                    break

            cluster_urls = list(year_urls)
            if evergreen_url:
                cluster_urls.append({
                    "url": evergreen_url,
                    "title": "(evergreen)",
                    "is_evergreen": True,
                })

            if len(cluster_urls) < MIN_URLS_PER_QUERY:
                continue

            clusters.append({
                "key": f"year-versioned: {de_yeared_pattern}",
                "detection_method": "year_versioned_urls",
                "urls": cluster_urls,
                "total_impressions": 0,
                "total_clicks": 0,
                "best_position": None,
                "has_evergreen": evergreen_url is not None,
            })
        return clusters

    # =========================================================================
    # ROTATION-BATTLE DETECTION (graceful degradation)
    # =========================================================================

    def _detect_rotation_battles(self) -> list[dict]:
        """Detect URLs with high position-volatility on shared queries.

        Web Linker's example: page introduced Feb 21, watched the
        rotation battle pull both pages out of the visible index over
        the following weeks. Daily GSC position data needed.

        Graceful degradation: if `gsc_daily_position_data` isn't
        provided, this method is never called.
        """
        if self.gsc_daily_position_data is None:
            return []

        df = self.gsc_daily_position_data
        required = {"query", "page", "position", "date"}
        if not required.issubset(set(df.columns)):
            return []

        # For each (query, page), compute position swing
        swings: dict[str, dict[str, float]] = defaultdict(dict)
        for (query, page), group in df.groupby(["query", "page"]):
            positions = group["position"].dropna().tolist()
            if len(positions) < 3:
                continue
            swing = max(positions) - min(positions)
            swings[query][page] = swing

        clusters: list[dict] = []
        for query, page_swings in swings.items():
            volatile_pages = [
                page for page, swing in page_swings.items()
                if swing >= POSITION_VOLATILITY_SWING_THRESHOLD
            ]
            if len(volatile_pages) < MIN_URLS_PER_QUERY:
                continue
            if self._is_geo_sibling_cluster(volatile_pages):
                continue
            cluster_urls = [{
                "url": page,
                "position_swing": page_swings[page],
            } for page in volatile_pages]
            clusters.append({
                "key": f"rotation-battle: {query}",
                "detection_method": "rotation_battle",
                "urls": cluster_urls,
                "total_impressions": 0,
                "total_clicks": 0,
                "best_position": None,
                "max_swing": max(page_swings[p] for p in volatile_pages),
            })
        return clusters

    # =========================================================================
    # CLUSTER DEDUPLICATION + PRIORITY SCORING
    # =========================================================================

    def _deduplicate_clusters(self, clusters: list[dict]) -> list[dict]:
        """Merge clusters that share the same URL set, keeping the
        highest-precision detection method."""
        method_priority = {
            "serp_overlap": 1,
            "gsc_query_page": 2,
            "url_level_gsc": 3,
            "rotation_battle": 4,
            "year_versioned_urls": 5,
            "title_slug_h1": 6,
        }
        seen: dict[frozenset, dict] = {}
        for cluster in clusters:
            url_set = frozenset(u["url"] for u in cluster["urls"])
            if url_set not in seen:
                seen[url_set] = cluster
            else:
                # Keep the higher-precision (lower number) method
                existing = seen[url_set]
                existing_p = method_priority.get(
                    existing["detection_method"], 99
                )
                new_p = method_priority.get(
                    cluster["detection_method"], 99
                )
                if new_p < existing_p:
                    seen[url_set] = cluster
        return list(seen.values())

    def _enrich_cluster_with_priority(self, cluster: dict) -> None:
        """Score cluster on commercial intent + rank proximity + volume.

        Output: cluster["priority_tier"] in {"A", "B", "C"} and
        cluster["priority_reasoning"] explaining why.

        Scoring (Edward Show ep. 1,030 ROI-first principle):
            A — money keyword AND close to ranking (any URL in top 10)
            B — money keyword OR close to ranking, but not both
            C — informational AND deep position (informational fluff
                 cluster, not worth fixing first)
        """
        # Determine commercial intent
        cluster_query = cluster.get("key", "")
        # For SERP-overlap clusters with 2 merged queries, use the worse
        # case (least commercial of the two)
        intent_keys: list[str] = []
        if "merged_queries" in cluster:
            intent_keys = cluster["merged_queries"]
        else:
            intent_keys = [cluster_query]

        intents = [
            self.keyword_intent_lookup.get(k.lower(), "").lower()
            for k in intent_keys if isinstance(k, str)
        ]
        is_commercial = any(i in COMMERCIAL_INTENT_VALUES for i in intents)

        # Determine ranking proximity
        best_pos = cluster.get("best_position")
        in_top_10 = best_pos is not None and best_pos <= 10
        in_top_3 = best_pos is not None and best_pos <= TOP_3_POSITION_BAR

        # Score
        if is_commercial and in_top_10:
            tier = "A"
            reasoning = (
                f"Money keyword (intent: {next(i for i in intents if i in COMMERCIAL_INTENT_VALUES)}) "
                f"with at least one URL ranking in top 10 (best position: "
                f"{best_pos:.1f}). Real captured visibility being diluted."
            )
        elif is_commercial:
            tier = "B"
            commercial_intent = next(
                (i for i in intents if i in COMMERCIAL_INTENT_VALUES), "commercial"
            )
            best_pos_str = f"{best_pos:.1f}" if best_pos is not None else "N/A"
            reasoning = (
                f"Money keyword (intent: {commercial_intent}) but no URL "
                f"ranks in top 10 yet (best position: "
                f"{best_pos_str}). Worth fixing — "
                "consolidation may push the cluster into competitive range."
            )
        elif in_top_10:
            tier = "B"
            reasoning = (
                f"Informational query but already ranking in top 10 "
                f"(best position: {best_pos:.1f}). Real visibility being "
                "diluted, fix-worthy even though intent isn't commercial."
            )
        else:
            tier = "C"
            best_pos_str = f"{best_pos:.1f}" if best_pos is not None else "unknown"
            reasoning = (
                f"Informational query at deep position "
                f"(best position: {best_pos_str}). "
                "Low ROI to fix — consider skipping unless the cluster "
                "is core to broader content strategy."
            )

        # Top-3 escalation
        if in_top_3:
            reasoning += " [TOP-3: most damaging — high recovery upside]"

        cluster["priority_tier"] = tier
        cluster["priority_reasoning"] = reasoning
        cluster["is_commercial"] = is_commercial
        cluster["in_top_3"] = in_top_3
        cluster["in_top_10"] = in_top_10

    # =========================================================================
    # FALSE-POSITIVE GUARD: SEED-TERM / MIXED-INTENT
    # =========================================================================

    def _apply_false_positive_filter(self, cluster: dict) -> None:
        """Detect ambiguous-seed clusters and downgrade to REVIEW tier.

        An ambiguous seed query (e.g., "flushometer", "manabloc",
        "urinal") can legitimately surface multiple URLs from the same
        domain without those URLs cannibalizing each other — they may
        be answering different intents within the same mixed-intent
        SERP. This filter detects:

            1. Query is a seed term (≤2 words, no service/geo/intent
               modifiers)
            2. AND the cluster URLs target meaningfully different
               topics (low title+H1 similarity)

        When BOTH apply, the cluster is downgraded to "REVIEW" tier
        with explicit reasoning. This prevents auto-consolidation
        recommendations on false positives.

        Year-versioned and rotation-battle clusters are exempt —
        those have unambiguous detection signals.
        """
        # Skip clusters detected by methods with unambiguous signals
        if cluster.get("detection_method") in (
            "year_versioned_urls",
            "rotation_battle",
        ):
            cluster["false_positive_check"] = "skipped_by_detection_method"
            return

        query = (cluster.get("key") or "").strip()
        if not query:
            return

        is_seed = self._is_seed_query(query)
        page_topics_diverge = self._cluster_page_topics_diverge(cluster)

        cluster["is_seed_query"] = is_seed
        cluster["page_topics_diverge"] = page_topics_diverge

        if is_seed and page_topics_diverge:
            # Downgrade to REVIEW tier with explicit reasoning
            cluster["original_priority_tier"] = cluster.get("priority_tier")
            cluster["priority_tier"] = "REVIEW"
            cluster["false_positive_check"] = "flagged_seed_with_divergent_topics"
            cluster["review_reason"] = (
                "Ambiguous seed query with cluster URLs targeting "
                "meaningfully different topics. This is likely a "
                "false positive — the URLs may be answering different "
                "intents within a mixed-intent SERP rather than "
                "cannibalizing each other. Manual review required "
                "before any consolidation work."
            )
        elif is_seed:
            # Seed but topics align — keep as cannibalization but note
            cluster["false_positive_check"] = "seed_query_topics_align"
        elif page_topics_diverge:
            # Topics diverge but query is specific — note but keep tier
            cluster["false_positive_check"] = "specific_query_topics_diverge"
        else:
            cluster["false_positive_check"] = "passed"

    @staticmethod
    def _is_seed_query(query: str) -> bool:
        """Return True if the query is a seed term with mixed intent.

        Definition: ≤SEED_QUERY_MAX_WORDS words, AND lacks service
        verbs, geo modifiers, and intent qualifiers.
        """
        q = query.strip()
        if not q:
            return False
        word_count = len(re.findall(r"\b\w+\b", q))
        if word_count > SEED_QUERY_MAX_WORDS:
            return False
        # Has any disambiguating modifier? Then not a seed.
        if SERVICE_VERB_PATTERN.search(q):
            return False
        if GEO_MODIFIER_PATTERN.search(q):
            return False
        if INTENT_QUALIFIER_PATTERN.search(q):
            return False
        return True

    def _cluster_page_topics_diverge(self, cluster: dict) -> bool:
        """Return True if cluster URLs target meaningfully different topics.

        Compares each pair of URLs' normalized title+H1 token sets via
        Jaccard similarity using both SF crawl data AND the URL slug
        as a fallback when SF data is missing. Returns True when the
        average pairwise similarity is below
        PAGE_TOPIC_SIMILARITY_THRESHOLD.
        """
        urls_in_cluster = [u.get("url", "") for u in cluster.get("urls", [])]
        if len(urls_in_cluster) < 2:
            return False

        # Build token sets per URL: prefer SF title+H1, fall back to
        # URL slug when SF data is missing
        url_topics: dict[str, set[str]] = {}
        sf_data: dict[str, tuple[str, str]] = {}
        for _, row in self.df.iterrows():
            u = row.get("url")
            if not isinstance(u, str) or u not in urls_in_cluster:
                continue
            title = row.get("title", "") or ""
            h1 = row.get("h1_1") or row.get("h1") or ""
            sf_data[u] = (title, h1)

        for u in urls_in_cluster:
            if u in sf_data:
                title, h1 = sf_data[u]
                tokens = self._topic_tokens(f"{title} {h1}")
            else:
                tokens = set()
            # Fall back to URL slug tokens when SF data is missing or empty
            if not tokens:
                slug = self._extract_slug(u)
                # Convert slug like "what-is-a-flushometer" to readable
                slug_text = slug.replace("-", " ").replace("_", " ")
                tokens = self._topic_tokens(slug_text)
            if tokens:
                url_topics[u] = tokens

        if len(url_topics) < 2:
            # Truly can't compute — be conservative, assume topics align
            return False

        # Average pairwise Jaccard similarity
        urls_with_topics = list(url_topics.keys())
        similarities = []
        for i, u1 in enumerate(urls_with_topics):
            for u2 in urls_with_topics[i + 1:]:
                t1, t2 = url_topics[u1], url_topics[u2]
                if not t1 or not t2:
                    continue
                intersection = len(t1 & t2)
                union = len(t1 | t2)
                if union > 0:
                    similarities.append(intersection / union)
        if not similarities:
            return False
        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity < PAGE_TOPIC_SIMILARITY_THRESHOLD

    @staticmethod
    def _topic_tokens(text: str) -> set[str]:
        """Extract meaningful tokens from title+H1 for similarity check.

        Lowercases, removes brand suffix, strips stop words, returns
        token set for Jaccard comparison.
        """
        if not isinstance(text, str):
            return set()
        # Strip brand suffix
        for sep in [" | ", " - ", " — ", " – "]:
            if sep in text:
                segments = text.split(sep)
                if len(segments) > 1:
                    text = sep.join(segments[:-1])
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = re.findall(r"\b\w+\b", text)
        # Stop-word filter — focus on content words
        stop = {
            "a", "an", "the", "and", "or", "but", "of", "in", "on", "at",
            "to", "for", "with", "is", "are", "was", "were", "be", "been",
            "being", "do", "does", "did", "will", "should", "could", "would",
            "your", "you", "we", "our", "us", "i", "my", "what", "how",
            "why", "where", "when", "who", "which", "that", "this", "these",
            "those", "from", "by", "as", "have", "has", "had", "it", "its",
            "if", "so", "not", "no", "yes",
        }
        return {t for t in tokens if t not in stop and len(t) > 2}

    # =========================================================================
    # WINNER SELECTION
    # =========================================================================

    def _select_winner(self, cluster: dict) -> Optional[dict]:
        """Apply the multi-factor winner-selection rule.

        Order: position → 90d clicks → backlinks → fewer internal
        inlinks (tie-breaker on consolidation effort).
        """
        urls = cluster.get("urls", [])
        if not urls:
            return None

        sf_lookup: dict[str, dict] = {}
        for _, row in self.df.iterrows():
            u = row.get("url")
            if isinstance(u, str):
                sf_lookup[u] = {
                    "backlinks": (
                        row.get("backlinks") or row.get("# of backlinks") or 0
                    ),
                    "inlinks": (
                        row.get("inlinks") or row.get("unique_inlinks") or 0
                    ),
                }

        scored = []
        for u in urls:
            url = u.get("url")
            position = u.get("position", 999) or 999
            clicks = u.get("clicks", 0) or 0
            sf = sf_lookup.get(url, {})
            backlinks = float(sf.get("backlinks", 0) or 0)
            inlinks = float(sf.get("inlinks", 0) or 0)
            scored.append({
                "url": url,
                "position": position,
                "clicks": clicks,
                "backlinks": backlinks,
                "inlinks": inlinks,
            })

        scored.sort(key=lambda x: (
            x["position"],
            -x["clicks"],
            -x["backlinks"],
            x["inlinks"],
        ))
        return scored[0] if scored else None

    # =========================================================================
    # QUERY-INTENT EXTRACTION + WINNER SANITY CHECKS
    # =========================================================================

    @staticmethod
    def _extract_query_modifiers(query: str) -> dict:
        """Extract geo and service modifiers from a query string.

        Returns:
            {
              "geo_tokens": [list of geo phrases found],
              "service_verbs": [list of service-intent verbs found],
              "primary_services": [list of service nouns found],
              "has_geo": bool,
              "has_service": bool,
            }

        Used to verify the auditor's winner candidate aligns with the
        query intent. A query like "emergency plumber salt lake city"
        produces:
            geo_tokens: ["salt lake city"]
            service_verbs: ["emergency"]
            primary_services: ["plumber"]
        """
        if not isinstance(query, str):
            return {
                "geo_tokens": [],
                "service_verbs": [],
                "primary_services": [],
                "has_geo": False,
                "has_service": False,
            }
        q = query.lower()
        geo = [m.group(0).strip() for m in GEO_TOKEN_PATTERN.finditer(q)]
        verbs = [m.group(0).strip() for m in SERVICE_VERB_KEYWORDS.finditer(q)]
        services = [
            m.group(0).strip() for m in PRIMARY_SERVICE_KEYWORDS.finditer(q)
        ]
        # Deduplicate while preserving order
        geo = list(dict.fromkeys(geo))
        verbs = list(dict.fromkeys(verbs))
        services = list(dict.fromkeys(services))
        return {
            "geo_tokens": geo,
            "service_verbs": verbs,
            "primary_services": services,
            "has_geo": bool(geo),
            "has_service": bool(verbs or services),
        }

    def _winner_aligned_with_query(
        self,
        winner_url: str,
        modifiers: dict,
    ) -> dict:
        """Check whether a winner URL is aligned with the query's
        geo and service modifiers.

        Returns:
            {
              "geo_aligned": True/False/None,  (None if query has no geo)
              "service_aligned": True/False/None,
              "geo_mismatch_reason": str | None,
              "service_mismatch_reason": str | None,
            }
        """
        result = {
            "geo_aligned": None,
            "service_aligned": None,
            "geo_mismatch_reason": None,
            "service_mismatch_reason": None,
        }
        if not winner_url or not isinstance(winner_url, str):
            return result

        # Build text corpus for the winner page (slug + title + H1)
        slug = self._extract_slug(winner_url) or ""
        slug_text = slug.replace("-", " ").replace("_", " ")
        path = ""
        try:
            from urllib.parse import urlparse
            path = urlparse(winner_url).path or ""
        except Exception:
            path = ""

        title = ""
        h1 = ""
        for _, row in self.df.iterrows():
            if row.get("url") == winner_url:
                title = row.get("title", "") or ""
                h1 = row.get("h1_1") or row.get("h1") or ""
                break

        page_text = f"{path} {slug_text} {title} {h1}".lower()

        # Geographic alignment check
        if modifiers["has_geo"]:
            query_geos = modifiers["geo_tokens"]
            # Page must contain at least one of the query's geo tokens
            page_geos = [
                m.group(0).strip()
                for m in GEO_TOKEN_PATTERN.finditer(page_text)
            ]
            page_geos = list(dict.fromkeys(page_geos))

            # Normalize for comparison (collapse whitespace variations)
            def normalize_geo(g: str) -> str:
                return re.sub(r"\s+", "", g.lower())

            query_geos_norm = {normalize_geo(g) for g in query_geos}
            page_geos_norm = {normalize_geo(g) for g in page_geos}

            # Synonym groups
            slc_synonyms = {"saltlakecity", "saltlake", "slc"}
            # Parent geo (state-level) — acceptable for any Utah-city
            # query because the state contains all the cities
            parent_geo_synonyms = {"utah", "ut"}
            query_has_slc = bool(query_geos_norm & slc_synonyms)
            page_has_slc = bool(page_geos_norm & slc_synonyms)
            page_has_parent_geo = bool(page_geos_norm & parent_geo_synonyms)

            # Check for a different city geo on the page — if the
            # page is specifically about a different city, the parent
            # geo doesn't save it. "Sugar House" + "UT" in a slug
            # means the page is about Sugar House, not Utah generally.
            page_specific_cities = (
                page_geos_norm - parent_geo_synonyms - slc_synonyms
            )
            query_specific_cities = (
                query_geos_norm - parent_geo_synonyms - slc_synonyms
            )
            page_has_different_city = bool(
                page_specific_cities
                and not (page_specific_cities & query_specific_cities)
                and not (query_has_slc and page_has_slc)
            )

            direct_overlap = bool(query_geos_norm & page_geos_norm)
            slc_overlap = query_has_slc and page_has_slc

            if direct_overlap or slc_overlap:
                # Exact city match wins
                result["geo_aligned"] = True
            elif page_has_different_city:
                # Page is about a different specific city — mismatch
                # even if it also mentions the parent state
                result["geo_aligned"] = False
                result["geo_mismatch_reason"] = (
                    f"Query targets {query_geos!r} but winner page is "
                    f"about {sorted(page_specific_cities)!r}. Different "
                    f"specific city — parent state context doesn't make "
                    f"this aligned."
                )
            elif page_has_parent_geo:
                # Page has only the parent state geo (no different
                # specific city) — acceptable as canonical service answer
                result["geo_aligned"] = True
            else:
                result["geo_aligned"] = False
                if page_geos:
                    result["geo_mismatch_reason"] = (
                        f"Query targets {query_geos!r} but winner page is "
                        f"about {page_geos!r}. Different geography."
                    )
                else:
                    result["geo_mismatch_reason"] = (
                        f"Query targets {query_geos!r} but winner page has "
                        f"no geographic identifier in slug/title/H1."
                    )

        # Service alignment check
        if modifiers["has_service"]:
            # Generic page (homepage, about, contact, etc.) is NEVER
            # service-aligned for a service+intent query
            if GENERIC_PAGE_SLUGS.match(path):
                result["service_aligned"] = False
                result["service_mismatch_reason"] = (
                    f"Winner is a generic page (path={path!r}), not a "
                    f"dedicated service page. Service queries should "
                    f"resolve to dedicated service pages."
                )
            else:
                # Page must contain the query's service verbs OR primary
                # service nouns
                page_verbs = [
                    m.group(0).strip()
                    for m in SERVICE_VERB_KEYWORDS.finditer(page_text)
                ]
                page_services = [
                    m.group(0).strip()
                    for m in PRIMARY_SERVICE_KEYWORDS.finditer(page_text)
                ]
                query_verbs = set(
                    v.lower().replace("-", "").replace(" ", "")
                    for v in modifiers["service_verbs"]
                )
                query_services = set(
                    s.lower().replace("-", "").replace(" ", "")
                    for s in modifiers["primary_services"]
                )
                page_verbs_set = set(
                    v.lower().replace("-", "").replace(" ", "")
                    for v in page_verbs
                )
                page_services_set = set(
                    s.lower().replace("-", "").replace(" ", "")
                    for s in page_services
                )

                # Service alignment: at least one primary service must
                # match. Verb alignment is a bonus but not required.
                service_match = bool(
                    query_services & page_services_set
                )
                # If query has only a verb (e.g., "emergency"), check
                # that — though this is a weaker signal
                verb_match = bool(query_verbs & page_verbs_set)

                if query_services and not service_match:
                    result["service_aligned"] = False
                    result["service_mismatch_reason"] = (
                        f"Query targets service {modifiers['primary_services']!r} "
                        f"but winner page covers {page_services or 'no primary service'!r}. "
                        f"Different service intent."
                    )
                elif query_verbs and not verb_match and not service_match:
                    result["service_aligned"] = False
                    result["service_mismatch_reason"] = (
                        f"Query has service intent {modifiers['service_verbs']!r} "
                        f"but winner page lacks matching service verbs/nouns."
                    )
                else:
                    result["service_aligned"] = True

        return result

    def _find_architecturally_correct_page(
        self,
        modifiers: dict,
        cluster_urls: set[str],
    ) -> Optional[dict]:
        """Search the SF crawl for a page that better matches the
        query intent than any URL in the cluster.

        Looks for a non-cluster page whose slug + title + H1 contain
        all the query's primary service keywords AND, if the query
        has geo, a matching geo token. Returns None if no clear
        canonical match exists.

        Returns:
            {
              "url": str,
              "title": str,
              "match_strength": float,  (0..1)
              "matched_services": [...],
              "matched_geo": [...],
            }
        """
        if not modifiers["has_service"]:
            return None
        if not modifiers["primary_services"]:
            return None

        query_services_set = set(
            s.lower().replace("-", "").replace(" ", "")
            for s in modifiers["primary_services"]
        )
        # Expand with semantic equivalents so "hot water" matches
        # "water heater" and vice versa
        query_services_expanded = _expand_service_terms(query_services_set)
        query_verbs_set = set(
            v.lower().replace("-", "").replace(" ", "")
            for v in modifiers["service_verbs"]
        )
        query_geo_set = set()
        if modifiers["has_geo"]:
            for g in modifiers["geo_tokens"]:
                query_geo_set.add(re.sub(r"\s+", "", g.lower()))

        candidates = []
        scope = self._get_indexable_html()
        for _, row in scope.iterrows():
            url = row.get("url")
            if not isinstance(url, str) or url in cluster_urls:
                continue
            try:
                from urllib.parse import urlparse
                path = urlparse(url).path or ""
            except Exception:
                path = ""
            if GENERIC_PAGE_SLUGS.match(path):
                continue
            if CATEGORY_ARCHIVE_PATTERN.match(path):
                continue

            slug = self._extract_slug(url) or ""
            slug_text = slug.replace("-", " ").replace("_", " ")
            title = row.get("title", "") or ""
            h1 = row.get("h1_1") or row.get("h1") or ""
            page_text = f"{path} {slug_text} {title} {h1}".lower()

            page_services = set(
                m.group(0).lower().replace("-", "").replace(" ", "")
                for m in PRIMARY_SERVICE_KEYWORDS.finditer(page_text)
            )
            page_verbs = set(
                m.group(0).lower().replace("-", "").replace(" ", "")
                for m in SERVICE_VERB_KEYWORDS.finditer(page_text)
            )
            page_geos = set()
            for m in GEO_TOKEN_PATTERN.finditer(page_text):
                page_geos.add(re.sub(r"\s+", "", m.group(0).lower()))

            # Must match all primary services (or their equivalents)
            # from the query. We check whether each query-service
            # token has at least one of its equivalents present in
            # page_services.
            all_services_match = True
            for q_term in query_services_set:
                equivalents = SERVICE_TERM_EQUIVALENCE.get(
                    q_term, {q_term}
                )
                if not (equivalents & page_services):
                    all_services_match = False
                    break
            if not all_services_match:
                continue

            # Geo matching: handle parent-geo containment AND reject
            # pages about a different specific city
            geo_match = True
            matched_geo = []
            if query_geo_set:
                slc_synonyms = {"saltlakecity", "saltlake", "slc"}
                parent_geo_synonyms = {"utah", "ut"}
                query_has_slc = bool(query_geo_set & slc_synonyms)
                page_has_slc = bool(page_geos & slc_synonyms)
                page_has_parent_geo = bool(page_geos & parent_geo_synonyms)
                direct_overlap = query_geo_set & page_geos

                # Check if the page is about a DIFFERENT specific city
                page_specific = (
                    page_geos - parent_geo_synonyms - slc_synonyms
                )
                query_specific = (
                    query_geo_set - parent_geo_synonyms - slc_synonyms
                )
                page_has_different_city = bool(
                    page_specific
                    and not (page_specific & query_specific)
                    and not (query_has_slc and page_has_slc)
                )

                if direct_overlap:
                    matched_geo = list(direct_overlap)
                elif query_has_slc and page_has_slc:
                    matched_geo = ["slc"]
                elif page_has_different_city:
                    # Page is about a different city — reject
                    geo_match = False
                elif page_has_parent_geo:
                    matched_geo = list(page_geos & parent_geo_synonyms)
                elif not page_geos:
                    matched_geo = []
                else:
                    geo_match = False
            if not geo_match:
                continue

            # Score: how strong is the match (counting equivalents)
            service_score = len(
                query_services_expanded & page_services
            ) / max(1, len(query_services_expanded))
            verb_score = len(query_verbs_set & page_verbs) / max(
                1, len(query_verbs_set)
            ) if query_verbs_set else 0.5
            # Prefer pages whose slug contains the service term directly
            # (or one of its equivalents)
            slug_score = 1.0 if any(
                s in slug.lower().replace("-", "")
                for s in query_services_expanded
            ) else 0.5
            # Service-page bias: clean service-page slugs are short and
            # topic-focused. Blog-post slugs are long sentences. A
            # 4-word slug like "drain-cleaning-utah" is a better
            # canonical answer than a 9-word blog slug like
            # "warning-signs-that-you-have-a-drain-cleaning-emergency".
            slug_word_count = len(
                [w for w in slug.split("-") if w]
            )
            # Blog-style slugs typically have 6+ words and contain
            # sentence-like connectors. Service-page slugs typically
            # have 2-4 words.
            blog_pattern_words = {
                "the", "a", "an", "your", "you", "what", "why", "how",
                "where", "when", "who", "and", "or", "but", "of", "in",
                "on", "at", "to", "for", "with", "from", "by", "is",
                "are", "was", "were", "be", "been", "do", "does", "did",
                "will", "should", "can", "could", "would", "have", "has",
                "had", "that", "this", "these", "those", "if", "so",
                "vs", "versus",
            }
            slug_words = set(
                w.lower() for w in slug.split("-") if w
            )
            has_blog_connectors = bool(slug_words & blog_pattern_words)
            is_short_service_slug = slug_word_count <= 4
            if is_short_service_slug and not has_blog_connectors:
                page_type_score = 1.0
            elif slug_word_count <= 6 and not has_blog_connectors:
                page_type_score = 0.7
            elif has_blog_connectors:
                page_type_score = 0.2
            else:
                page_type_score = 0.5
            # Phrase-match bonus: prefer pages whose slug matches the
            # query's service+verb phrase verbatim. For "drain cleaning
            # salt lake city", a slug containing "drain-cleaning"
            # together is a stronger match than slugs with just "drain"
            # or just "cleaning" separately.
            slug_normalized = slug.lower().replace("-", " ")
            phrase_bonus = 0.0
            if modifiers["primary_services"] and modifiers["service_verbs"]:
                # Look for service+verb adjacency in slug
                for s in modifiers["primary_services"]:
                    for v in modifiers["service_verbs"]:
                        s_l = s.lower()
                        v_l = v.lower()
                        if (
                            f"{s_l} {v_l}" in slug_normalized
                            or f"{v_l} {s_l}" in slug_normalized
                        ):
                            phrase_bonus = 0.15
                            break
                    if phrase_bonus > 0:
                        break

            # Combined score: service match (25%) + verb (15%) +
            # slug-contains-service (15%) + page-type (30%) +
            # phrase-bonus (15%). Page-type prevents blog posts from
            # beating service pages; phrase-bonus picks the most
            # specific service page when multiple service pages match.
            score = (
                (service_score * 0.25)
                + (verb_score * 0.15)
                + (slug_score * 0.15)
                + (page_type_score * 0.30)
                + phrase_bonus
            )

            candidates.append({
                "url": url,
                "title": title,
                "match_strength": round(score, 3),
                "matched_services": list(
                    query_services_expanded & page_services
                ),
                "matched_verbs": list(
                    query_verbs_set & page_verbs
                ),
                "matched_geo": matched_geo,
            })

        if not candidates:
            return None
        candidates.sort(key=lambda c: -c["match_strength"])
        # Only return a result if the top match is strong enough
        if candidates[0]["match_strength"] < 0.5:
            return None
        return candidates[0]

    def _apply_winner_sanity_check(self, cluster: dict) -> None:
        """Run geo + service alignment checks on the winner candidate
        AND search for an architecturally correct non-cluster page.

        Adds these fields to the cluster:
            winner_query_alignment: dict (geo/service alignment result)
            architecturally_correct_page: dict | None (if a better
                non-cluster page exists)
            winner_sanity_flag: str
                "aligned" | "geo_mismatch" | "service_mismatch" |
                "both_mismatch" | "skipped" | "no_winner"
            architecture_fix_recommended: bool
        """
        # Skip for REVIEW tier — those clusters aren't getting
        # consolidation recommendations anyway
        if cluster.get("priority_tier") == "REVIEW":
            cluster["winner_sanity_flag"] = "skipped_review_tier"
            cluster["architecture_fix_recommended"] = False
            return

        # Skip detection methods where alignment doesn't apply
        if cluster.get("detection_method") in (
            "year_versioned_urls",
            "rotation_battle",
        ):
            cluster["winner_sanity_flag"] = "skipped_by_detection_method"
            cluster["architecture_fix_recommended"] = False
            return

        winner = cluster.get("winner_candidate")
        if not winner or not winner.get("url"):
            cluster["winner_sanity_flag"] = "no_winner"
            cluster["architecture_fix_recommended"] = False
            return

        # Extract query modifiers
        query = cluster.get("key", "")
        modifiers = self._extract_query_modifiers(query)
        cluster["query_modifiers"] = modifiers

        # Skip if query has no geo and no service — alignment check
        # doesn't apply to ambiguous queries
        if not modifiers["has_geo"] and not modifiers["has_service"]:
            cluster["winner_sanity_flag"] = "skipped_no_modifiers"
            cluster["architecture_fix_recommended"] = False
            return

        # Check winner alignment
        alignment = self._winner_aligned_with_query(
            winner["url"], modifiers
        )
        cluster["winner_query_alignment"] = alignment

        geo_bad = alignment["geo_aligned"] is False
        service_bad = alignment["service_aligned"] is False

        if geo_bad and service_bad:
            cluster["winner_sanity_flag"] = "both_mismatch"
        elif geo_bad:
            cluster["winner_sanity_flag"] = "geo_mismatch"
        elif service_bad:
            cluster["winner_sanity_flag"] = "service_mismatch"
        else:
            cluster["winner_sanity_flag"] = "aligned"

        # Search for architecturally correct non-cluster page
        cluster_urls = {
            u.get("url", "") for u in cluster.get("urls", [])
        }
        arch_page = self._find_architecturally_correct_page(
            modifiers, cluster_urls
        )
        cluster["architecturally_correct_page"] = arch_page

        # Recommend architecture fix when:
        # 1. Winner is misaligned, AND
        # 2. A canonical non-cluster page exists
        cluster["architecture_fix_recommended"] = bool(
            (geo_bad or service_bad) and arch_page is not None
        )

    # =========================================================================
    # CTR DISPARITY ANALYSIS
    # =========================================================================

    def _compute_ctr_disparity(self, cluster: dict) -> Optional[dict]:
        """Compute CTR disparity within a cluster.

        High variance + low average CTR = the "high impressions, low
        clicks across competing URLs" pattern from the Reddit post.
        """
        ctrs = [
            u.get("ctr", 0) for u in cluster.get("urls", [])
            if u.get("impressions") and u.get("ctr") is not None
        ]
        if len(ctrs) < 2:
            return None
        avg_ctr = sum(ctrs) / len(ctrs)
        try:
            stdev_ctr = statistics.stdev(ctrs)
        except statistics.StatisticsError:
            stdev_ctr = 0.0
        # Flag pattern: avg below 1% AND stdev > avg (high variance)
        is_diluted_ctr = avg_ctr < 0.01 and stdev_ctr > avg_ctr
        return {
            "avg_ctr": avg_ctr,
            "ctr_stdev": stdev_ctr,
            "diluted_ctr_pattern": is_diluted_ctr,
        }

    # =========================================================================
    # ISSUE EMISSION
    # =========================================================================

    def _emit_clusters(self, clusters: list[dict]) -> None:
        """Emit a single aggregated issue per priority tier."""
        clusters.sort(
            key=lambda c: (
                {"A": 0, "B": 1, "C": 2, "REVIEW": 3}.get(
                    c.get("priority_tier", "C"), 4
                ),
                -(c.get("total_impressions") or 0),
            )
        )

        # Priority tier counts
        tier_counts: dict[str, int] = defaultdict(int)
        for c in clusters:
            tier_counts[c.get("priority_tier", "C")] += 1

        # Severity: based on highest-priority tier present (REVIEW
        # doesn't drive severity — it's manual-review-pending, not
        # confirmed cannibalization)
        if tier_counts.get("A", 0) > 0:
            # Within Priority A: top-3 cannibalization escalates to Critical
            has_top_3 = any(
                c.get("priority_tier") == "A" and c.get("in_top_3")
                for c in clusters
            )
            severity = Severity.CRITICAL if has_top_3 else Severity.HIGH
        elif tier_counts.get("B", 0) > 0:
            severity = Severity.HIGH
        elif tier_counts.get("C", 0) > 0:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        total_clusters = len(clusters)
        affected_urls = []
        for cluster in clusters[:50]:
            for u in cluster["urls"]:
                affected_urls.append(u["url"])
        affected_urls = list(dict.fromkeys(affected_urls))[:200]
        total_affected_urls = len(set(
            u["url"] for c in clusters for u in c["urls"]
        ))
        total_impressions = sum(c.get("total_impressions") or 0 for c in clusters)

        # Build description with examples grouped by priority
        description_parts = [
            f"Found {total_clusters} cannibalization clusters across "
            f"{total_affected_urls} URLs.\n",
            "Cannibalization is a duplicative-entry problem in Google's "
            "index. When two pages on the same site are semantically too "
            "close, BERT-driven semantic indexing decides they shouldn't "
            "both appear in the top 10 for a query. The canonical-tag "
            "mechanism designed for technical duplicates does NOT catch "
            "semantic overlap. Google rotates between the pages, neither "
            "ranks consistently, and traffic suffers.\n",
            "Cannibalization can happen at any ranking position — but "
            "it's most damaging in positions 1-3, where real captured "
            "visibility is being diluted.\n",
            "Priority tier breakdown:\n"
            f"  A (money keywords, top-10 ranking): {tier_counts.get('A', 0)}\n"
            f"  B (money keyword OR top-10, not both): {tier_counts.get('B', 0)}\n"
            f"  C (informational at deep position, low ROI): {tier_counts.get('C', 0)}\n"
            f"  REVIEW (likely false positives, manual review): {tier_counts.get('REVIEW', 0)}\n",
            "REVIEW tier explanation: clusters where the query is an "
            "ambiguous seed term AND the cluster URLs target meaningfully "
            "different topics. These may be false positives — the URLs "
            "may be answering different intents within a mixed-intent "
            "SERP rather than cannibalizing each other. Manual review "
            "required before any consolidation work.\n",
        ]

        # Top examples per tier
        for tier_label in ["A", "B", "C", "REVIEW"]:
            tier_clusters = [
                c for c in clusters
                if c.get("priority_tier") == tier_label
            ][:3]
            if not tier_clusters:
                continue
            label_text = (
                "REVIEW (likely false positives)"
                if tier_label == "REVIEW"
                else f"Priority {tier_label}"
            )
            description_parts.append(f"\n{label_text} examples:\n")
            for cluster in tier_clusters:
                description_parts.append(
                    self._format_cluster_for_description(cluster)
                )

        # Build per-cluster recommendations
        recommendations = self._build_global_recommendation(clusters, tier_counts)

        # Top clusters with full enrichment for additional_data
        top_clusters_data = []
        for cluster in clusters[:20]:
            # winner already attached by run_audit's sanity-check step
            winner = cluster.get("winner_candidate") or self._select_winner(cluster)
            ctr_disparity = self._compute_ctr_disparity(cluster)
            top_clusters_data.append({
                "key": cluster.get("key"),
                "detection_method": cluster.get("detection_method"),
                "priority_tier": cluster.get("priority_tier"),
                "priority_reasoning": cluster.get("priority_reasoning"),
                "is_commercial": cluster.get("is_commercial"),
                "in_top_3": cluster.get("in_top_3"),
                "in_top_10": cluster.get("in_top_10"),
                "best_position": cluster.get("best_position"),
                "total_impressions": cluster.get("total_impressions"),
                "total_clicks": cluster.get("total_clicks"),
                "url_count": len(cluster["urls"]),
                "urls": [u["url"] for u in cluster["urls"]],
                "winner_candidate": winner,
                "ctr_disparity": ctr_disparity,
                "serp_overlap": cluster.get("serp_overlap"),
                "merged_queries": cluster.get("merged_queries"),
                "max_swing": cluster.get("max_swing"),
                "has_evergreen": cluster.get("has_evergreen"),
                "is_seed_query": cluster.get("is_seed_query"),
                "page_topics_diverge": cluster.get("page_topics_diverge"),
                "false_positive_check": cluster.get("false_positive_check"),
                "original_priority_tier": cluster.get("original_priority_tier"),
                "review_reason": cluster.get("review_reason"),
                # Winner sanity-check fields
                "query_modifiers": cluster.get("query_modifiers"),
                "winner_query_alignment": cluster.get("winner_query_alignment"),
                "winner_sanity_flag": cluster.get("winner_sanity_flag"),
                "architecturally_correct_page": cluster.get(
                    "architecturally_correct_page"
                ),
                "architecture_fix_recommended": cluster.get(
                    "architecture_fix_recommended"
                ),
            })

        impact = (
            "Cannibalization splits ranking signals between URLs, "
            "preventing any single page from ranking as well as a "
            "consolidated version would. Top-3 cannibalization is the "
            "most damaging — visibility you've already earned is being "
            "diluted across multiple pages, which Google then rotates, "
            "destabilizing rankings further. Resolving the highest-"
            "priority clusters typically lifts the winning URL by "
            "several positions and stabilizes traffic patterns."
        )

        self.create_issue(
            severity=severity,
            category=AuditCategory.CANNIBALIZATION,
            issue_type="keyword_cannibalization",
            title=(
                f"{total_clusters} cannibalization clusters "
                f"(A: {tier_counts.get('A', 0)}, B: {tier_counts.get('B', 0)}, "
                f"C: {tier_counts.get('C', 0)}, "
                f"REVIEW: {tier_counts.get('REVIEW', 0)})"
            ),
            description="\n".join(description_parts),
            affected_urls=affected_urls,
            count=total_affected_urls,
            recommendation=recommendations,
            impact=impact,
            additional_data={
                "total_clusters": total_clusters,
                "tier_counts": dict(tier_counts),
                "total_impressions": int(total_impressions),
                "top_clusters": top_clusters_data,
            },
        )

    def _format_cluster_for_description(self, cluster: dict) -> str:
        """Format a single cluster for the issue description."""
        lines = []
        method_label = {
            "serp_overlap": "SERP overlap (same intent across queries)",
            "gsc_query_page": "GSC query/page",
            "url_level_gsc": "URL-level GSC + title clustering",
            "title_slug_h1": "title + slug + H1 similarity",
            "rotation_battle": "rotation battle (position volatility)",
            "year_versioned_urls": "year-versioned URLs",
        }.get(cluster.get("detection_method", ""), cluster.get("detection_method", ""))

        header = f"   [{cluster.get('priority_tier', '?')}] {cluster.get('key', '')}"
        if cluster.get("serp_overlap"):
            header += f" (SERP overlap: {cluster['serp_overlap']:.0%})"
        lines.append(header)
        lines.append(f"      Detection: {method_label}")
        lines.append(f"      {cluster.get('priority_reasoning', '')}")

        for u in cluster["urls"][:4]:
            url = u.get("url", "?")
            pos = u.get("position")
            imp = u.get("impressions")
            clicks = u.get("clicks")
            extras = []
            if pos is not None:
                extras.append(f"pos {pos:.1f}")
            if imp:
                extras.append(f"{imp:,} imp")
            if clicks is not None:
                extras.append(f"{clicks:,} clicks")
            extras_str = f" ({', '.join(extras)})" if extras else ""
            lines.append(f"        - {url}{extras_str}")
        if len(cluster["urls"]) > 4:
            lines.append(f"        ...and {len(cluster['urls']) - 4} more")
        return "\n".join(lines)

    def _build_global_recommendation(
        self, clusters: list[dict], tier_counts: dict[str, int]
    ) -> str:
        """Build the recommendation block for the aggregated issue."""
        parts = [
            "FOUR resolution paths, in order of preference:\n",
            "1. CONSOLIDATE (most common): pick the strongest URL using "
            "the multi-factor winner-selection rule below, MERGE unique "
            "content from the losing pages into the winner BEFORE "
            "deleting them, then 301-redirect the loser URLs to the "
            "winner. Update internal links across the site that point "
            "to the loser URLs.\n",
            "2. DIFFERENTIATE: when both pages should genuinely exist "
            "(one informational, one transactional), rewrite each to "
            "target distinct intent — different titles, different H1s, "
            "different primary content focus.\n",
            "3. CANONICALIZE (least preferred): when a hub page and a "
            "deep-dive page must coexist with similar content, point a "
            "canonical from the deep-dive to the hub (or vice versa). "
            "Note: canonical tags are HINTS, not commands — Google may "
            "override them if content diverges enough.\n",
            "4. REPUBLISH UNDER NEW SLUG (last resort): when "
            "consolidation hasn't moved rankings within 30+ days "
            "because Google's duplicate cluster is stuck on the old "
            "slugs, manual remove + no-index BOTH pages, then republish "
            "content under a fresh slug + new title + new H1. Loses "
            "backlink equity and resets ranking history — only use when "
            "consolidation has demonstrably failed.\n",

            "WINNER SELECTION (multi-factor, in order):\n"
            "1. Lowest current GSC position (best existing rank)\n"
            "2. Highest 90-day GSC clicks\n"
            "3. Most backlinks pointing to the URL\n"
            "4. Tie-breaker: fewer incoming internal links to update "
            "(reduces consolidation effort)\n",

            "PRIORITY ORDER:\n"
            f"  Fix all {tier_counts.get('A', 0)} Priority A clusters first "
            "— money keywords already close to ranking. These are the "
            "highest-ROI fixes.\n"
            f"  Address {tier_counts.get('B', 0)} Priority B clusters next "
            "if bandwidth allows.\n"
            f"  {tier_counts.get('C', 0)} Priority C clusters can typically "
            "be skipped — they're informational queries at deep positions, "
            "low ROI to fix.\n",

            "DO NOT 'just improve both pages independently.' "
            "Cannibalization gets worse with more content effort, not "
            "better — adding new content just adds more competition.\n",

            "STRATEGIC SUGGESTION (not a hard rule): when planning new "
            "content for this site, finish resolving existing "
            "cannibalization first. Adding new pages targeting the "
            "same query family extends the rotation problem rather "
            "than solving it. This is a recommendation — final scope "
            "and sequencing are the editorial team's call.\n",

            "WHEN PLANNING NEW KEYWORD TARGETS: if two keywords have "
            ">70% top-10 SERP overlap, Google sees them as the same "
            "intent. Pick the higher-volume keyword and target ONE page "
            "for both, mentioning the lower-volume term as a secondary "
            "entity. Don't write separate pages for queries Google can't "
            "tell apart.",
        ]
        return "\n".join(parts)

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_indexable_html(self) -> pd.DataFrame:
        """Return the subset of the DataFrame that's indexable HTML."""
        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        return scope

    @staticmethod
    def _build_cluster_key(title: str, url: str, h1: str) -> str:
        """Build a clustering key from title + slug + H1.

        Web Linker / Matt Cutts: Google's duplicate detection runs on
        document name (slug + page title + H1). We mirror that
        weighting in our clustering — produces stronger clusters than
        title-only and catches cases the previous title-only logic
        missed.
        """
        title_norm = CannibalizationAuditor._normalize_text(title)
        slug = CannibalizationAuditor._extract_slug(url)
        slug_norm = CannibalizationAuditor._normalize_text(slug)
        h1_norm = CannibalizationAuditor._normalize_text(h1)

        # Combine title (60%) + slug (25%) + H1 (15%) into the key.
        # Use a stable composite that matches when any 2 of 3 align —
        # rare for non-cannibalizing pages.
        components = [c for c in [title_norm, slug_norm, h1_norm] if c]
        if not components:
            return ""
        # Title is the dominant signal — use it as the primary key
        return title_norm or slug_norm or h1_norm

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize a string for clustering comparison.

        Strips brand suffixes, lowercases, removes punctuation, collapses
        whitespace.
        """
        if not isinstance(text, str):
            return ""
        t = text.strip()
        for sep in [" | ", " - ", " — ", " – ", " :: ", " // "]:
            if sep in t:
                segments = t.split(sep)
                if len(segments) > 1:
                    t = sep.join(segments[:-1])
        t = t.lower()
        t = re.sub(r"[^\w\s-]", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    @staticmethod
    def _extract_slug(url: str) -> str:
        """Extract the last path segment from a URL as the slug."""
        if not isinstance(url, str):
            return ""
        # Strip protocol, host, query, fragment
        m = re.match(r"https?://[^/]+(/.*)?", url)
        if not m:
            return ""
        path = (m.group(1) or "").split("?")[0].split("#")[0]
        path = path.rstrip("/")
        if not path:
            return ""
        return path.split("/")[-1]

    @staticmethod
    def _is_geo_sibling_cluster(urls: list[str]) -> bool:
        """Return True if all URLs in the cluster differ only by city slug.

        Geo-siblings are intentional location pages, not cannibalization.
        """
        if len(urls) < 2:
            return False
        stripped = []
        for u in urls:
            if not isinstance(u, str):
                return False
            no_city = CITY_TOKEN_PATTERN.sub("/", u)
            stripped.append(no_city)
        return len(set(stripped)) == 1
