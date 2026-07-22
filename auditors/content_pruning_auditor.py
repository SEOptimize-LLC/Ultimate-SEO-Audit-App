"""Content Pruning Auditor.

Identifies content prune candidates following the consolidate / rewrite /
reformat / redirect / delete hierarchy. Deletion is the last option, not
the first — pages with backlink history or template similarity to
better content are usually worth more as 301 sources or rewrite targets
than as 410s.

Detection logic:
- Pages with 0 GSC clicks in last 12 months (if GSC data available)
- Pages with 0 backlinks (if backlink data available — not in scope
  for v1, falls back to internal-link-count heuristic)
- Old pages with no traffic (using last-modified date if available)
- Pages with high template-similarity to other pages (already covered
  by near-duplicates data when available)
- Pages with thin content AND no traffic AND no inlinks

For each candidate, recommends a decision tree action: Keep / Rewrite /
Consolidate / Redirect / Delete.

This auditor is on-page focused (it's about content quality and
strategy, not technical health). It's wired into onpage_issues in app.py
when the parent runner ties it in.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd

from .base_auditor import BaseAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity

logger = logging.getLogger(__name__)


# Thresholds
ZERO_TRAFFIC_THRESHOLD = 0
"""GSC clicks at or below this in the last reported period = 'no traffic'."""

LOW_TRAFFIC_THRESHOLD = 5
"""Below this many clicks = candidate for review (not necessarily prune)."""

THIN_CONTENT_WORDS = 200
"""Pages under this word count are considered thin."""

OLD_CONTENT_DAYS = 365 * 2
"""Pages last modified more than this many days ago, with no traffic,
are stale-content candidates."""

HIGH_SITE_RADIUS = 0.6
"""siteRadius at or above this marks a page as a topical outlier — its
embedding sits far from the site's central-entity centroid. Matches the
outlier threshold used by the semantic-site-map pipeline. Off-topic pages
that also carry no traffic are the highest-confidence prune candidates
(seo-fundamentals: prioritise pages that are BOTH low-value AND off-topic)."""

READING_WPM = 250
"""Average adult reading speed (words per minute) used to derive the
theoretical full-read time of a page from its word count."""

LONG_FORM_WORDS = 1500
"""Pages at or above this word count are treated as long-form for the
consumption-time vs dwell comparison. Below it, a short dwell is expected
and carries no engagement signal."""

DWELL_SEC_PER_1000_WORDS = 120
"""Moderated engagement floor: readers don't consume every word, so we
expect at least ~2 minutes of dwell per 1,000 words on a long-form page.
A page whose measured average session duration falls below this floor is a
low-engagement / Helpful-Content red flag, not proof the content is bad —
but worth reviewing."""


class ContentPruningAuditor(BaseAuditor):
    """Auditor for content pruning candidates."""

    def __init__(
        self,
        df: pd.DataFrame,
        site_radius: Optional[dict[str, float]] = None,
    ):
        """Initialize the pruning auditor.

        Args:
            df: DataFrame from Screaming Frog export.
            site_radius: Optional per-URL topical outlier scores, as a mapping
                of URL -> siteRadius (0..1, higher = more off-topic). When
                supplied — or when the DataFrame carries a ``site_radius``
                column — the auditor runs an extra topic-aware sub-check that
                elevates prune priority for low-value pages that are also
                topical outliers. Defaults to None for backward compatibility
                so the existing ``ContentPruningAuditor(df)`` wiring in app.py
                keeps working unchanged.
        """
        super().__init__(df)
        self.site_radius = site_radius

    def get_audit_type(self) -> str:
        return "onpage"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        # Diagnostic
        self._emit_data_availability()

        # The core check — assigns an action to each candidate
        self._check_prune_candidates()

        # Topic-aware elevation — no-ops when no siteRadius data is present
        self._check_offtopic_prune_candidates()

        # DFC (Delete-First-Cautiously) sub-checks. Each guards its own
        # required columns and no-ops when the data isn't available, so
        # they never crash and never fabricate a signal.
        self._check_viability_matrix()
        self._check_consumption_dwell_gap()
        self._check_category_intent_guard()

        return self.issues

    # =========================================================================
    # AVAILABILITY DIAGNOSTIC
    # =========================================================================

    def _emit_data_availability(self) -> None:
        """Note which data sources are available for the prune analysis."""
        has_gsc = self.has_column("gsc_clicks")
        has_inlinks = self.has_column("internal_links_in")
        has_word_count = self.has_column("word_count")

        if not (has_gsc and has_word_count):
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.CONTENT_PRUNING,
                issue_type="content_pruning_data_limited",
                title="Content pruning analysis running with limited data",
                description=(
                    "Full content pruning requires GSC traffic data "
                    "AND content metrics (word count, last-modified). "
                    "One or more of these is missing from the crawl. "
                    "The pruning analysis will use whatever signals "
                    "are available, but the recommendations will be "
                    "less precise."
                ),
                recommendation=(
                    "Re-run the crawl with GSC API integration enabled "
                    "(Configuration > API Access > Google Search "
                    "Console) and ensure word count is being captured. "
                    "These two signals together produce the most "
                    "reliable prune recommendations."
                ),
                impact=(
                    "Without GSC data, pages with no organic traffic "
                    "can't be distinguished from pages with healthy "
                    "traffic. Pruning decisions made without traffic "
                    "data risk removing pages that are actually "
                    "performing."
                ),
            )

    # =========================================================================
    # MAIN CHECK
    # =========================================================================

    def _check_prune_candidates(self) -> None:
        """Identify and categorize content prune candidates."""
        if not self.has_column("url"):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if scope.empty:
            return

        # Apply scope filter — exclude utility pages that have no SEO value
        # to begin with (covered by other auditors / not pruning concerns)
        scope = scope[~scope["url"].astype(str).apply(self._is_utility_url)]
        if scope.empty:
            return

        candidates = self._build_candidates(scope)
        if not candidates:
            return

        # Group by recommended action
        by_action: dict[str, list[dict]] = {}
        for c in candidates:
            by_action.setdefault(c["action"], []).append(c)

        # Emit one issue per action category
        for action, items in by_action.items():
            self._emit_action_issue(action, items)

    def _build_candidates(self, scope: pd.DataFrame) -> list[dict]:
        """Return list of prune candidates with assigned actions."""
        has_gsc = "gsc_clicks" in scope.columns
        has_word_count = "word_count" in scope.columns
        has_inlinks = "internal_links_in" in scope.columns

        candidates: list[dict] = []
        for _, row in scope.iterrows():
            url = row.get("url", "")
            if not isinstance(url, str):
                continue

            clicks = (
                row.get("gsc_clicks")
                if has_gsc and not pd.isna(row.get("gsc_clicks"))
                else None
            )
            words = (
                row.get("word_count")
                if has_word_count and not pd.isna(row.get("word_count"))
                else None
            )
            inlinks = (
                row.get("internal_links_in")
                if has_inlinks and not pd.isna(row.get("internal_links_in"))
                else None
            )

            # Skip pages that aren't candidates
            if not self._is_candidate(clicks, words, inlinks):
                continue

            action = self._decide_action(clicks, words, inlinks, row)
            if action == "Keep":
                continue

            candidates.append({
                "url": url,
                "clicks": clicks,
                "words": words,
                "inlinks": inlinks,
                "action": action,
            })
        return candidates

    @staticmethod
    def _is_candidate(clicks, words, inlinks) -> bool:
        """Return True if the page is worth considering for pruning."""
        # If we have GSC data, no clicks is a candidate signal
        if clicks is not None and clicks <= ZERO_TRAFFIC_THRESHOLD:
            return True
        # If we have word count, very thin pages are candidates regardless
        if words is not None and words < THIN_CONTENT_WORDS:
            return True
        # If page has no inlinks, it's already an orphan — also a candidate
        if inlinks is not None and inlinks == 0:
            return True
        return False

    @staticmethod
    def _decide_action(clicks, words, inlinks, row) -> str:
        """Decide the recommended action for a candidate page.

        Returns one of: Keep, Rewrite, Consolidate, Redirect, Delete.

        Decision tree:
        - No traffic + no inlinks + thin content → Delete or Redirect
        - No traffic + has inlinks → Rewrite (the page is referenced
          internally, so removing it would create broken links)
        - No traffic + thick content → Consolidate (page has effort
          invested but isn't performing — merge into a stronger page)
        - Some traffic but thin → Rewrite
        - Otherwise → Keep
        """
        no_traffic = clicks is not None and clicks <= ZERO_TRAFFIC_THRESHOLD
        thin = words is not None and words < THIN_CONTENT_WORDS
        no_inlinks = inlinks is not None and inlinks == 0

        if no_traffic and thin and no_inlinks:
            # Page has nothing going for it — but still don't auto-
            # recommend deletion if it might have backlinks (we don't
            # have backlink data here, so default to Redirect to be safe)
            return "Redirect"

        if no_traffic and thin:
            # Has internal links but no traffic — rewrite or consolidate.
            # Since we don't know if a target page exists, default to
            # Rewrite (the safer of the two)
            return "Rewrite"

        if no_traffic and not thin:
            # Substantial content but no traffic — consolidate into a
            # stronger page covering similar intent
            return "Consolidate"

        if not no_traffic and thin:
            # Page is getting traffic despite being thin — expand it
            return "Rewrite"

        return "Keep"

    @staticmethod
    def _is_utility_url(url) -> bool:
        """Return True if the URL is a utility page (already filtered elsewhere)."""
        if not isinstance(url, str):
            return False
        u = url.lower()
        markers = (
            "/thank-you",
            "/thanks/",
            "/application-form",
            "/terms-of-use",
            "/terms-of-service",
            "/terms-and-conditions",
            "/privacy-policy",
            "/privacy/",
            "/cookie-policy",
            "/disclaimer",
            "/404-error",
            "/page-not-found",
            "/login",
            "/wp-login",
            "/wp-admin",
            "/cart",
            "/checkout",
            "/my-account",
            "/account/",
            "/wishlist",
        )
        if any(m in u for m in markers):
            return True
        if "-ppc-" in u or u.rstrip("/").endswith("-ppc"):
            return True
        return False

    # =========================================================================
    # TOPIC-AWARE ELEVATION (siteRadius)
    # =========================================================================

    def _has_site_radius_data(self) -> bool:
        """True if per-URL siteRadius is available via param or a df column."""
        if isinstance(self.site_radius, dict) and len(self.site_radius) > 0:
            return True
        return self.has_column("site_radius")

    def _radius_for(self, url: str, row: pd.Series) -> Optional[float]:
        """Resolve the siteRadius for a single page.

        Priority: the explicit ``site_radius`` mapping passed to the
        constructor, then a ``site_radius`` column on the row. Returns None
        when neither source has a usable numeric value.
        """
        if isinstance(self.site_radius, dict):
            value = self.site_radius.get(url)
            if value is not None and not pd.isna(value):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None
        if "site_radius" in row.index:
            value = row.get("site_radius")
            if value is not None and not pd.isna(value):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None
        return None

    def _check_offtopic_prune_candidates(self) -> None:
        """Elevate low-value pages that are ALSO topical outliers.

        A page carrying little/no traffic is a prune candidate; a page that is
        additionally off-topic (high siteRadius — its content sits far from the
        site's central entity) is the highest-confidence prune target, because
        keeping it both wastes crawl budget and dilutes the site's topical
        focus. This sub-check surfaces that intersection as a prioritised
        finding on top of the standard prune buckets.

        No-ops entirely when no siteRadius data is available (neither the
        constructor mapping nor a ``site_radius`` column), so the default
        ``ContentPruningAuditor(df)`` wiring is unaffected.
        """
        if not self.has_column("url"):
            return
        if not self._has_site_radius_data():
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if scope.empty:
            return

        scope = scope[~scope["url"].astype(str).apply(self._is_utility_url)]
        if scope.empty:
            return

        has_gsc = "gsc_clicks" in scope.columns
        has_word_count = "word_count" in scope.columns
        has_inlinks = "internal_links_in" in scope.columns

        flagged: list[dict] = []
        for _, row in scope.iterrows():
            url = row.get("url", "")
            if not isinstance(url, str):
                continue

            radius = self._radius_for(url, row)
            if radius is None or radius < HIGH_SITE_RADIUS:
                continue

            clicks = (
                row.get("gsc_clicks")
                if has_gsc and not pd.isna(row.get("gsc_clicks"))
                else None
            )
            words = (
                row.get("word_count")
                if has_word_count and not pd.isna(row.get("word_count"))
                else None
            )
            inlinks = (
                row.get("internal_links_in")
                if has_inlinks and not pd.isna(row.get("internal_links_in"))
                else None
            )

            if not self._is_low_value(clicks, words, inlinks):
                continue

            flagged.append({"url": url, "radius": radius, "clicks": clicks})

        if not flagged:
            return

        flagged.sort(key=lambda c: c["radius"], reverse=True)
        urls = [c["url"] for c in flagged]
        count = len(flagged)
        avg_radius = sum(c["radius"] for c in flagged) / count

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.CONTENT_PRUNING,
            issue_type="content_prune_offtopic",
            title=f"{count} off-topic low-value pages — prune first",
            description=(
                f"Found {count} indexable pages that are both low-value (no or "
                "minimal traffic) and topical outliers — their content sits "
                "far from the site's central entity (siteRadius at or above "
                f"{HIGH_SITE_RADIUS}, avg {avg_radius:.2f}). These are the "
                "highest-confidence prune targets: they contribute no traffic "
                "while actively diluting the site's topical focus and "
                "consuming crawl budget. Prioritise them ahead of the standard "
                "prune candidates."
            ),
            affected_urls=urls,
            recommendation=(
                "Work this list first. For each page, decide between "
                "consolidation into an on-topic page, 301-redirect to the "
                "most relevant live page, or removal (410) if no backlinks "
                "exist — same decision tree as the standard prune buckets, but "
                "applied with higher priority because the off-topic signal "
                "reinforces the low-value signal. Check for backlinks before "
                "deleting."
            ),
            impact=(
                "Off-topic, zero-traffic pages weaken the site's overall "
                "topical authority (a wider siteRadius reads as a less "
                "focused site) and spend crawl budget that should go to "
                "on-topic pages. Removing them tightens topical focus and "
                "concentrates ranking signals."
            ),
            additional_data={
                "affected_count": count,
                "avg_site_radius": round(avg_radius, 2),
                "site_radius_threshold": HIGH_SITE_RADIUS,
            },
        )

    @staticmethod
    def _is_low_value(clicks, words, inlinks) -> bool:
        """Return True if any available signal marks the page as low-value.

        Mirrors ``_is_candidate`` but uses the low-traffic threshold (not just
        zero) since the off-topic signal already adds confidence.
        """
        if clicks is not None and clicks <= LOW_TRAFFIC_THRESHOLD:
            return True
        if words is not None and words < THIN_CONTENT_WORDS:
            return True
        if inlinks is not None and inlinks == 0:
            return True
        return False

    # =========================================================================
    # DFC CHECK 1 — VIABILITY 2x2 (viable x required)
    # =========================================================================

    def _has_demand_signal(self) -> bool:
        """True if the crawl carries a GSC demand column we can read."""
        return self.has_column("gsc_clicks") or self.has_column("gsc_impressions")

    @staticmethod
    def _is_viable(clicks, impressions) -> bool:
        """A page is 'viable' if it shows any search demand at all.

        Demand = at least one GSC click OR at least one impression. Both are
        allowed to be None (missing) independently; the caller only invokes
        this when at least one demand column exists.
        """
        if clicks is not None and not pd.isna(clicks) and clicks > 0:
            return True
        if impressions is not None and not pd.isna(impressions) and impressions > 0:
            return True
        return False

    @classmethod
    def _is_required_page(cls, url) -> bool:
        """True if the URL is a legally/operationally required page.

        These pages (privacy, terms, contact, about, shipping/returns,
        accessibility, and the utility pages already recognised by
        ``_is_utility_url``) must stay live even with no search demand — they
        are prune-exempt. The correct treatment for a non-viable required page
        is ``noindex, follow``, never deletion.
        """
        if cls._is_utility_url(url):
            return True
        if not isinstance(url, str):
            return False
        u = url.lower()
        required_markers = (
            "/contact",
            "/about",
            "/refund",
            "/returns",
            "/return-policy",
            "/shipping",
            "/warranty",
            "/accessibility",
            "/legal",
            "/gdpr",
            "/ccpa",
            "/dmca",
            "/sitemap",
        )
        return any(m in u for m in required_markers)

    def _check_viability_matrix(self) -> None:
        """Classify indexable pages on the viable x required 2x2.

        Quadrants:
        - viable + required / viable + non-required  -> keep (healthy)
        - NON-viable + REQUIRED                       -> keep but noindex,follow
        - NON-viable + non-required                   -> prune candidate

        Emits a summary INSIGHT of the 2x2 plus a dedicated finding for the
        non-viable + required bucket (the genuinely new guidance: these pages
        should be de-indexed, not deleted). No-ops when no GSC demand column is
        present, since viability cannot be determined without it.
        """
        if not self.has_column("url"):
            return
        if not self._has_demand_signal():
            logger.debug(
                "Viability matrix skipped: no gsc_clicks/gsc_impressions column."
            )
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if scope.empty:
            return

        has_clicks = "gsc_clicks" in scope.columns
        has_impr = "gsc_impressions" in scope.columns

        counts = {
            "viable": 0,
            "nonviable_required": 0,
            "nonviable_prune": 0,
        }
        noindex_urls: list[str] = []
        for _, row in scope.iterrows():
            url = row.get("url", "")
            if not isinstance(url, str):
                continue
            clicks = row.get("gsc_clicks") if has_clicks else None
            impressions = row.get("gsc_impressions") if has_impr else None

            if self._is_viable(clicks, impressions):
                counts["viable"] += 1
                continue

            if self._is_required_page(url):
                counts["nonviable_required"] += 1
                noindex_urls.append(url)
            else:
                counts["nonviable_prune"] += 1

        total = sum(counts.values())
        if total == 0:
            return

        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.CONTENT_PRUNING,
            issue_type="content_viability_matrix",
            title="Viability x required classification of indexable pages",
            description=(
                f"Classified {total} indexable pages on two axes — whether "
                "they have search demand (viable: at least one GSC click or "
                "impression) and whether they are legally/operationally "
                f"required. {counts['viable']} are viable (keep as-is), "
                f"{counts['nonviable_required']} are required but have no "
                "search demand (keep the page but set it to noindex,follow — "
                "do NOT delete a required page), and "
                f"{counts['nonviable_prune']} have neither demand nor a "
                "required-page reason to exist (prune candidates — see the "
                "action-specific findings for the recommended treatment)."
            ),
            recommendation=(
                "Handle each quadrant differently. Viable pages: leave alone. "
                "Non-viable but required pages: set noindex,follow so they stay "
                "reachable for users and compliance without spending index "
                "slots on zero-demand pages. Non-viable, non-required pages: "
                "run them through the prune decision tree (consolidate / "
                "redirect / remove). The single most common mistake is "
                "deleting a required page because it has no traffic — noindex "
                "it instead."
            ),
            impact=(
                "Separating 'no demand' from 'no reason to exist' prevents two "
                "opposite errors: deleting a compliance page that must stay "
                "live, and keeping a zero-value page that only dilutes the "
                "index. The 2x2 makes the correct treatment unambiguous."
            ),
            additional_data={
                "viable": counts["viable"],
                "nonviable_required": counts["nonviable_required"],
                "nonviable_prune": counts["nonviable_prune"],
                "total_classified": total,
            },
        )

        if noindex_urls:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.CONTENT_PRUNING,
                issue_type="content_required_noindex",
                title=(
                    f"{len(noindex_urls)} required pages have no search "
                    "demand — noindex, don't delete"
                ),
                description=(
                    f"Found {len(noindex_urls)} indexable pages that are "
                    "legally or operationally required (privacy, terms, "
                    "contact, returns, and similar) but show no GSC search "
                    "demand. These must stay live for users and compliance, "
                    "yet they don't need to occupy index slots or compete for "
                    "crawl budget."
                ),
                affected_urls=noindex_urls[:100],
                recommendation=(
                    "Set these pages to noindex,follow. They remain fully "
                    "reachable by users and keep passing internal link equity "
                    "onward (follow), but Google stops indexing them. Do NOT "
                    "delete or redirect a required page just because it has no "
                    "organic traffic — that removes content the site must "
                    "provide."
                ),
                impact=(
                    "Keeps compliance and utility content available while "
                    "tightening the indexable footprint to pages that actually "
                    "serve search demand."
                ),
                additional_data={"affected_count": len(noindex_urls)},
            )

    # =========================================================================
    # DFC CHECK 2 — CONSUMPTION-TIME vs DWELL GAP
    # =========================================================================

    @staticmethod
    def _parse_duration_seconds(value) -> Optional[float]:
        """Parse an average-session-duration value into seconds.

        Handles the two shapes Screaming Frog's GA4 integration emits:
        - a plain numeric count of seconds (int/float, or a numeric string)
        - a clock string 'hh:mm:ss' or 'mm:ss'

        Returns None for missing/blank/unparseable values so the caller can
        degrade gracefully rather than fabricate an engagement number.
        """
        if value is None or pd.isna(value):
            return None

        # Numeric seconds (covers int, float, numpy numerics)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value) if value >= 0 else None

        text = str(value).strip()
        if text == "" or text.lower() == "nan":
            return None

        # Clock form: hh:mm:ss or mm:ss
        if ":" in text:
            parts = text.split(":")
            try:
                nums = [float(p) for p in parts]
            except (TypeError, ValueError):
                return None
            if any(n < 0 for n in nums):
                return None
            if len(parts) == 3:
                hours, minutes, seconds = nums
                return hours * 3600 + minutes * 60 + seconds
            if len(parts) == 2:
                minutes, seconds = nums
                return minutes * 60 + seconds
            return None

        # Plain numeric string of seconds
        try:
            seconds = float(text)
        except (TypeError, ValueError):
            return None
        return seconds if seconds >= 0 else None

    def _check_consumption_dwell_gap(self) -> None:
        """Flag long-form pages whose measured dwell is far below expectation.

        reading_time_sec = word_count / READING_WPM * 60 (theoretical full
        read). Readers rarely consume every word, so the engagement floor is a
        moderated ~2 min per 1,000 words. A long-form page (>= LONG_FORM_WORDS)
        whose average session duration falls below that floor is a
        low-engagement / Helpful-Content red flag worth reviewing.

        Requires BOTH word_count and a parseable ga_avg_session_duration
        (Screaming Frog's GA4 integration). No-ops entirely when the dwell
        column is absent — dwell cannot be inferred from any other crawl
        signal, so the check degrades rather than guessing.
        """
        if not self.has_column("url"):
            return
        if not (self.has_column("word_count") and
                self.has_column("ga_avg_session_duration")):
            logger.debug(
                "Dwell-gap check skipped: word_count and/or "
                "ga_avg_session_duration column absent."
            )
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if scope.empty:
            return
        scope = scope[~scope["url"].astype(str).apply(self._is_utility_url)]
        if scope.empty:
            return

        flagged: list[dict] = []
        for _, row in scope.iterrows():
            url = row.get("url", "")
            if not isinstance(url, str):
                continue

            words = row.get("word_count")
            if words is None or pd.isna(words):
                continue
            try:
                words = float(words)
            except (TypeError, ValueError):
                continue
            if words < LONG_FORM_WORDS:
                continue

            dwell_sec = self._parse_duration_seconds(
                row.get("ga_avg_session_duration")
            )
            if dwell_sec is None:
                # Unparseable / missing for THIS row — degrade, don't guess.
                continue

            expected_floor = (words / 1000.0) * DWELL_SEC_PER_1000_WORDS
            if dwell_sec < expected_floor:
                reading_time_sec = words / READING_WPM * 60
                flagged.append({
                    "url": url,
                    "words": int(words),
                    "dwell_sec": round(dwell_sec, 1),
                    "expected_floor_sec": round(expected_floor, 1),
                    "reading_time_sec": round(reading_time_sec, 1),
                })

        if not flagged:
            return

        flagged.sort(key=lambda c: c["dwell_sec"])
        urls = [c["url"] for c in flagged]
        count = len(flagged)
        avg_dwell = sum(c["dwell_sec"] for c in flagged) / count

        self.create_issue(
            severity=Severity.LOW,
            category=AuditCategory.CONTENT,
            issue_type="content_low_dwell_longform",
            title=(
                f"{count} long-form pages have dwell far below their "
                "reading time"
            ),
            description=(
                f"Found {count} long-form pages (>= {LONG_FORM_WORDS} words) "
                "whose measured average session duration sits below the "
                f"moderated engagement floor of {DWELL_SEC_PER_1000_WORDS} "
                "seconds per 1,000 words (avg measured dwell "
                f"{avg_dwell:.0f}s). When a page carries article-length "
                "content but visitors leave well before they could have read "
                "it, that gap is a low-engagement signal — the content may be "
                "hard to consume, mismatched to intent, or padded to length "
                "without substance. This is a review flag, not proof of a "
                "quality problem."
            ),
            affected_urls=urls,
            recommendation=(
                "Review these pages for consumption friction: front-load the "
                "answer, break up walls of text, add scannable structure "
                "(headings, lists, tables), and cut padding added only to hit "
                "a word count. Cross-check the target query intent — a "
                "long-form page ranking for a quick-answer query will always "
                "show short dwell and may be the wrong format entirely."
            ),
            impact=(
                "Sustained low engagement on long-form content is one of the "
                "behavioural signals associated with Helpful-Content "
                "assessments. Improving consumption tends to lift both dwell "
                "and the page's ability to satisfy the query."
            ),
            additional_data={
                "affected_count": count,
                "avg_dwell_sec": round(avg_dwell, 1),
                "engagement_floor_sec_per_1000_words": DWELL_SEC_PER_1000_WORDS,
                "requires": "Screaming Frog GA4 integration "
                            "(ga_avg_session_duration)",
            },
        )

    # =========================================================================
    # DFC CHECK 3 — CATEGORY-PAGE INTENT GUARD
    # =========================================================================

    # Compiled once — matches commercial category / collection / shop URLs.
    _CATEGORY_URL_RE = re.compile(
        r"/(?:category|categories|product-category|collections?|shop|store|"
        r"catalog(?:ue)?|department|brands?)(?:/|$|\?)",
        re.IGNORECASE,
    )

    @classmethod
    def _is_category_url(cls, url) -> bool:
        """True if the URL looks like a commercial category/collection page."""
        if not isinstance(url, str):
            return False
        return bool(cls._CATEGORY_URL_RE.search(url))

    def _check_category_intent_guard(self) -> None:
        """Caution against over-contenting thin commercial category pages.

        Category / collection / shop pages serve a commercial-navigational
        intent: get the shopper to the right products fast. When such a page
        shows up as thin, the reflexive fix ('add 1,500 words of content') is
        wrong — piling article-length prose onto a category page shifts its
        intent signal from commercial toward informational and can hurt it in
        the SERP. This guard surfaces the affected category pages so the thin
        finding isn't mis-actioned.

        Requires word_count to identify thin category pages. No-ops when
        word_count is absent.
        """
        if not self.has_column("url"):
            return
        if not self.has_column("word_count"):
            logger.debug(
                "Category intent guard skipped: no word_count column."
            )
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if scope.empty:
            return

        flagged: list[str] = []
        for _, row in scope.iterrows():
            url = row.get("url", "")
            if not isinstance(url, str):
                continue
            if not self._is_category_url(url):
                continue
            words = row.get("word_count")
            if words is None or pd.isna(words):
                continue
            try:
                words = float(words)
            except (TypeError, ValueError):
                continue
            if words < THIN_CONTENT_WORDS:
                flagged.append(url)

        if not flagged:
            return

        urls = flagged[:100]
        count = len(flagged)
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.CONTENT_PRUNING,
            issue_type="content_category_intent_guard",
            title=(
                f"{count} thin category pages — do NOT fix with "
                "article-length content"
            ),
            description=(
                f"Found {count} commercial category/collection pages that read "
                "as thin by word count. These pages serve a "
                "commercial-navigational intent — route shoppers to products "
                "quickly — so a low word count is often correct, not a defect. "
                "Treating them like thin blog posts and adding long-form prose "
                "shifts the page's intent signal from commercial toward "
                "informational and can degrade its commercial ranking."
            ),
            affected_urls=urls,
            recommendation=(
                "Do NOT add article-length content to these pages. If a "
                "category page genuinely needs more signal, add a concise "
                "intro (2-3 sentences), ensure product/subcategory links and "
                "facets are crawlable, and place any long-form supporting "
                "content on a linked guide rather than on the category page "
                "itself. Only apply the thin-content rewrite guidance to "
                "editorial/informational pages, never to commercial category "
                "pages."
            ),
            impact=(
                "Preserves the commercial intent of category pages. "
                "Over-contenting them is a common self-inflicted ranking loss "
                "that this guard prevents by flagging them before the thin "
                "finding is acted on."
            ),
            additional_data={"affected_count": count},
        )

    # =========================================================================
    # ISSUE EMITTERS
    # =========================================================================

    def _emit_action_issue(self, action: str, items: list[dict]) -> None:
        """Create an audit issue for a group of candidates with the same action."""
        urls = [c["url"] for c in items][:100]
        count = len(items)

        if action == "Rewrite":
            severity = Severity.MEDIUM
            title = f"{count} pages need rewriting (low traffic or thin content)"
            description = (
                f"Found {count} indexable pages that are candidates "
                "for rewriting — either thin content (<200 words) "
                "with some traffic, or pages with no traffic that "
                "have internal links pointing to them (so they can't "
                "be deleted without breaking those links). Rewriting "
                "expands content depth and improves intent matching."
            )
            recommendation = (
                "For each page: identify the query intent it should "
                "satisfy, then expand the content to actually answer "
                "that intent. Add sections, examples, comparisons, "
                "evidence — anything that makes the page genuinely "
                "useful to someone searching for the topic. Don't pad "
                "with filler to hit a word count. If the page can't "
                "be made genuinely useful, switch to Consolidate "
                "(merge into a better page) instead."
            )
            impact = (
                "Thin content pages drag down site-wide quality "
                "signals. Rewriting them improves both the individual "
                "page's ranking potential and the overall perceived "
                "quality of the site."
            )

        elif action == "Consolidate":
            severity = Severity.MEDIUM
            title = f"{count} pages should be consolidated"
            description = (
                f"Found {count} indexable pages with substantial "
                "content but no traffic. Substantial-but-zero-traffic "
                "is a signal that the content is misaligned with "
                "search demand — either targeting the wrong query, "
                "competing with a stronger sibling page, or covering "
                "an intent that doesn't exist. Consolidating these "
                "pages into stronger sibling pages preserves the "
                "content effort while concentrating ranking signals."
            )
            recommendation = (
                "For each page, identify a stronger page on the site "
                "covering similar intent. Merge the unique content "
                "from the consolidate candidate into the stronger "
                "page. 301-redirect the consolidate URL to the "
                "stronger page. The result: one consolidated page "
                "with combined content depth, ranking signal, and "
                "any historical backlinks pointing to the redirected "
                "URL."
            )
            impact = (
                "Consolidation typically lifts the merged-into page "
                "by several positions because (a) ranking signals "
                "are no longer split, (b) the page is now more "
                "comprehensive, and (c) any backlinks to the "
                "redirected URL flow into the stronger destination."
            )

        elif action == "Redirect":
            severity = Severity.MEDIUM
            title = f"{count} pages are candidates for 301 + remove"
            description = (
                f"Found {count} pages with no traffic, thin content, "
                "and no internal links pointing to them. These pages "
                "have no current value to the site. The right action "
                "is to 301-redirect them to the most relevant live "
                "page (preserving any backlinks that may exist) and "
                "remove them from the sitemap. Outright deletion "
                "(returning 410) is also acceptable but loses any "
                "backlink equity."
            )
            recommendation = (
                "Work the ordered protocol per page: (a) Strip the "
                "internal links pointing to the page first, then check "
                "GA/GA4 and referral data to confirm it isn't acquiring "
                "users through non-organic channels. (b) Check if any "
                "external sites link to it via a backlink tool — if "
                "yes, 301-redirect to the most relevant live page on "
                "the site to preserve the link equity (only redirect to "
                "a genuinely relevant target, never a catch-all "
                "homepage redirect, which Google treats as a soft 404). "
                "(c) If no backlinks exist, the redirect is still safer "
                "than deletion (handles bookmarked or shared URLs); "
                "removing the page with a 410 is the alternative once "
                "internal links are stripped. (d) Remove from sitemap "
                "either way. (e) Update any remaining internal "
                "references to point to the new destination directly "
                "rather than relying on the redirect."
            )
            impact = (
                "Pages that exist but contribute nothing to the site "
                "consume crawl budget and dilute the perceived "
                "quality of the index. Removing them via 301 cleans "
                "up the index while preserving any backlink history."
            )

        elif action == "Delete":
            severity = Severity.LOW
            title = f"{count} pages can be deleted"
            description = (
                f"Found {count} pages that meet all deletion "
                "criteria: no traffic, thin content, no internal "
                "links, and no obvious topical relevance to other "
                "site content."
            )
            recommendation = (
                "Follow the ordered removal protocol — do NOT skip a "
                "step: (1) Strip ALL internal links pointing to the "
                "page first, so removing it never leaves a broken "
                "internal link. (2) Check GA/GA4 and referral data — "
                "confirm the page isn't quietly acquiring users through "
                "direct, referral, or email channels that organic "
                "search doesn't show. (3) Check external backlinks with "
                "a backlink tool — if any exist, do NOT delete; switch "
                "to the Redirect action to preserve that equity. (4) "
                "Only if steps 1-3 are clean, serve HTTP 410 (Gone) so "
                "the page is removed decisively. Never 301-redirect a "
                "genuinely removed URL to an unrelated page — a soft-404 "
                "redirect to the homepage or a mismatched target is "
                "treated as a soft 404 and wastes crawl budget. Remove "
                "from the sitemap regardless."
            )
            impact = (
                "Deletion is the last-resort prune action. Use it "
                "only when redirect targets aren't appropriate and "
                "no backlinks would be lost."
            )

        else:
            return

        self.create_issue(
            severity=severity,
            category=AuditCategory.CONTENT_PRUNING,
            issue_type=f"content_prune_{action.lower()}",
            title=title,
            description=description,
            affected_urls=urls,
            count=count,
            recommendation=recommendation,
            impact=impact,
            additional_data={"action": action},
        )
