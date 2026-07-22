"""JavaScript Rendering Auditor.

Detects JS-rendering issues that affect both Google's indexing pipeline and
non-rendering AI crawlers (ChatGPT, Claude, Perplexity, Bing AI Overviews).

Core principle (post March 2026 Google docs update):
    Google CAN render JavaScript. But:
      1. Rendering is queued, delayed, and budgeted (~5s window)
      2. Indexability decisions happen on the RAW HTML, before rendering
      3. AI crawlers do NOT render JavaScript at all
      4. Googlebot does NOT trigger user interactions (click, scroll, hover)

The audit therefore focuses on the gap between RAW HTML (what every crawler
sees instantly) and RENDERED HTML (what only Googlebot eventually sees), plus
patterns indicating critical content is gated behind user interaction.

Requires Screaming Frog crawls run with JavaScript Rendering enabled (the
"Response vs Render" report). Gracefully degrades when those columns are
absent — the auditor only flags issues it can verify from the data.
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd

from .base_auditor import BaseAuditor, is_empty_or_missing
from models.audit_result import AuditCategory, AuditIssue, Severity


# Thresholds calibrated from sources reviewed (Sitebulb, Conductor,
# Search Engine Journal, deltavdigital, Zumeirah, December 2025 Google docs).
RAW_CONTENT_MIN_WORDS = 100
"""Pages with raw word count below this are treated as content-empty
(classic SPA shell — `<div id='root'></div>`)."""

RENDER_GAP_RATIO = 1.5
"""Rendered word count must be at most this multiple of raw word count.
Above 1.5x means more than 33% of content is JS-injected — significant
exposure if rendering fails or for AI crawlers that don't render."""

CRITICAL_RENDER_GAP_RATIO = 3.0
"""Rendered word count more than 3x raw means the page is effectively
hollow without JS — critical for AI search visibility."""

LINK_GAP_THRESHOLD = 5
"""Absolute difference in outlinks between raw and rendered. Below this
the gap is just template-level chrome differences. Above means navigation
or content links are JS-injected."""

LINK_GAP_RATIO = 2.0
"""Rendered outlinks > 2x raw outlinks signals JS-dependent navigation."""

GATED_CONTENT_MIN_RAW_WORDS = RAW_CONTENT_MIN_WORDS
"""Interaction-gated detection only applies to already-hydrated pages (raw
HTML has real content). Empty SPA shells are handled by the empty-raw check;
excluding them here keeps this signal a distinct population."""


class JavaScriptRenderingAuditor(BaseAuditor):
    """Auditor for JavaScript-rendering SEO issues.

    Checks include:
    - Empty raw HTML / SPA shell detection
    - Content visibility gap (raw vs rendered word count)
    - Critical SEO elements only present in rendered HTML
      (title, canonical, meta description, H1, meta robots)
    - Link discovery gap (rendered link count >> raw)
    - Soft-404 indicators in raw HTML (December 2025 Google clarification)
    - Click/hover-gated content patterns (accordion/tab/load-more heuristics)
    - Hash-based routing for indexable pages
    - Render budget exposure (TBT/INP correlated with JS heaviness)
    """

    def get_audit_type(self) -> str:
        return "technical"

    def run_audit(self) -> list[AuditIssue]:
        """Run all JavaScript-rendering SEO checks."""
        self.clear_issues()

        # Whole-site availability check first — emit an INSIGHT so the user
        # knows whether deeper checks ran or were skipped due to missing data.
        self._check_rendering_data_availability()

        # Content visibility checks (require rendered + raw word counts)
        self._check_empty_raw_html()
        self._check_content_visibility_gap()
        self._check_critical_render_gap()

        # Critical SEO element checks (require source-vs-rendered field columns)
        self._check_render_only_title()
        self._check_render_only_canonical()
        self._check_render_only_meta_description()
        self._check_render_only_h1()
        self._check_render_only_meta_robots()

        # Link discovery
        self._check_link_discovery_gap()

        # Click/hover-gated content (composite word+link injection signature)
        self._check_interaction_gated_content()

        # URL-pattern checks (work without rendering data)
        self._check_hash_based_routing()

        # Render-budget exposure (uses existing TBT/JS columns)
        self._check_render_budget_exposure()

        return self.issues

    # =========================================================================
    # AVAILABILITY DIAGNOSTIC
    # =========================================================================

    def _check_rendering_data_availability(self) -> None:
        """Tell the user whether their crawl supports JS-rendering audits."""
        has_word_diff = self.has_columns(
            ["raw_word_count", "rendered_word_count"]
        )
        has_field_diff = any(
            self.has_column(col)
            for col in [
                "raw_title", "raw_canonical", "raw_meta_description",
                "raw_h1", "raw_meta_robots",
            ]
        )

        if has_word_diff or has_field_diff:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.JS_RENDERING,
                issue_type="js_rendering_data_present",
                title="JS rendering comparison data detected",
                description=(
                    "The crawl includes Screaming Frog's Response vs Render "
                    "report data. JS-rendering audits will run against this "
                    "data."
                ),
                recommendation=(
                    "No action — informational. Findings below are based on "
                    "actual raw vs rendered comparison."
                ),
                impact=(
                    "Layer 1 audit coverage active: content gap, critical "
                    "element visibility, link discovery."
                ),
            )
        else:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.JS_RENDERING,
                issue_type="js_rendering_data_missing",
                title="JS rendering data not in crawl — limited audit",
                description=(
                    "This crawl does not include Screaming Frog's Response "
                    "vs Render comparison data (raw word count, raw title, "
                    "raw canonical, etc.). Only URL-pattern and JS-budget "
                    "checks will run. To unlock the full JS-rendering audit, "
                    "re-crawl with Configuration -> Spider -> Rendering -> "
                    "JavaScript enabled, then export the Response vs Render "
                    "report."
                ),
                recommendation=(
                    "Re-run the Screaming Frog crawl with JavaScript "
                    "Rendering enabled to detect content visibility gaps, "
                    "render-only SEO elements, and link discovery gaps."
                ),
                impact=(
                    "Without this data we can't tell whether critical content "
                    "is in the raw HTML (visible to AI crawlers and Google "
                    "pre-rendering) or only after JS execution."
                ),
            )

    # =========================================================================
    # CONTENT VISIBILITY CHECKS
    # =========================================================================

    def _check_empty_raw_html(self) -> None:
        """Pages with effectively no content in raw HTML — SPA shells."""
        if not self.has_columns(["raw_word_count", "rendered_word_count"]):
            return

        # Restrict to indexable HTML pages where this matters
        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        condition = (
            (scope["raw_word_count"].fillna(0) < RAW_CONTENT_MIN_WORDS)
            & (scope["rendered_word_count"].fillna(0) >= 300)
        )
        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            avg_raw = float(scope.loc[condition, "raw_word_count"].mean())
            avg_rendered = float(
                scope.loc[condition, "rendered_word_count"].mean()
            )
            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.JS_RENDERING,
                issue_type="empty_raw_html",
                title=f"{count} pages have empty raw HTML (SPA shell)",
                description=(
                    f"Found {count} indexable pages where the raw HTML "
                    f"contains less than {RAW_CONTENT_MIN_WORDS} words "
                    f"(avg {avg_raw:.0f}) but the rendered HTML has "
                    f"substantial content (avg {avg_rendered:.0f} words). "
                    "These pages are effectively SPA shells — invisible to "
                    "AI crawlers (ChatGPT, Claude, Perplexity) and at risk "
                    "in Google's render queue."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Move to Server-Side Rendering (SSR) or Static Site "
                    "Generation (SSG). Frameworks: Next.js, Nuxt.js, "
                    "Angular Universal, Remix, Astro. Goal: the raw HTML "
                    "should pass the View Source test — the page's main "
                    "content must appear there before any JS executes."
                ),
                impact=(
                    "AI search engines that don't render JS cannot cite or "
                    "surface this content. Google's render queue is "
                    "delayed and budgeted, so even Googlebot may index a "
                    "stale/empty version."
                ),
                additional_data={
                    "avg_raw_words": round(avg_raw, 0),
                    "avg_rendered_words": round(avg_rendered, 0),
                },
            )

    def _check_content_visibility_gap(self) -> None:
        """Pages where significant content is JS-injected (raw < 0.67 * rendered)."""
        if not self.has_columns(["raw_word_count", "rendered_word_count"]):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        # Avoid double-counting pages already flagged as "empty raw"
        raw = scope["raw_word_count"].fillna(0)
        rendered = scope["rendered_word_count"].fillna(0)
        ratio = rendered / raw.replace(0, pd.NA)

        condition = (
            (raw >= RAW_CONTENT_MIN_WORDS)  # exclude empty-shell case
            & (rendered >= 300)
            & (ratio >= RENDER_GAP_RATIO)
            & (ratio < CRITICAL_RENDER_GAP_RATIO)
        )
        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.JS_RENDERING,
                issue_type="content_visibility_gap",
                title=f"{count} pages with significant JS-injected content",
                description=(
                    f"Found {count} pages where the rendered HTML contains "
                    f"at least {int((RENDER_GAP_RATIO - 1) * 100)}% more "
                    f"words than the raw HTML. A meaningful share of the "
                    "content only appears after JS executes."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Identify which content blocks are JS-injected (compare "
                    "View Source vs DevTools Elements panel). Move primary "
                    "body content, FAQ sections, product descriptions, and "
                    "schema markup into the raw HTML response."
                ),
                impact=(
                    "Content gap weakens AI crawler visibility and depends "
                    "on Google's renderer succeeding within ~5 seconds. "
                    "Long JS tasks can push content past that window."
                ),
            )

    def _check_critical_render_gap(self) -> None:
        """Pages where rendered content is >3x raw — page is effectively hollow."""
        if not self.has_columns(["raw_word_count", "rendered_word_count"]):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        raw = scope["raw_word_count"].fillna(0)
        rendered = scope["rendered_word_count"].fillna(0)
        ratio = rendered / raw.replace(0, pd.NA)

        condition = (
            (raw >= RAW_CONTENT_MIN_WORDS)
            & (rendered >= 300)
            & (ratio >= CRITICAL_RENDER_GAP_RATIO)
        )
        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.JS_RENDERING,
                issue_type="critical_render_gap",
                title=f"{count} pages with critical render gap (>3x)",
                description=(
                    f"Found {count} pages where the rendered HTML has more "
                    f"than {int(CRITICAL_RENDER_GAP_RATIO)}x the words of "
                    "the raw HTML. The page is effectively hollow without "
                    "JavaScript execution."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Treat as urgent. SSR or SSG migration is the right fix. "
                    "If a full migration isn't feasible, prerender these "
                    "specific page types as a stopgap (Prerender.io, "
                    "Rendertron, or framework-native static generation for "
                    "the affected routes)."
                ),
                impact=(
                    "Pages this hollow are nearly invisible to AI crawlers "
                    "and at high risk of partial indexing in Google when "
                    "the renderer fails or is delayed by render budget."
                ),
            )

    # =========================================================================
    # CRITICAL SEO ELEMENT CHECKS
    # =========================================================================

    def _check_render_only_title(self) -> None:
        """Title tag missing in raw HTML but present after rendering."""
        self._check_render_only_field(
            raw_col="raw_title",
            rendered_col="title",
            field_name="title tag",
            severity=Severity.CRITICAL,
            issue_type="render_only_title",
            recommendation=(
                "Move the <title> tag into the raw HTML response. Setting "
                "document.title via JavaScript means the title may not "
                "appear in SERPs for crawlers that don't render."
            ),
        )

    def _check_render_only_canonical(self) -> None:
        """Canonical tag missing in raw HTML but present after rendering."""
        self._check_render_only_field(
            raw_col="raw_canonical",
            rendered_col="canonical",
            field_name="canonical tag",
            severity=Severity.CRITICAL,
            issue_type="render_only_canonical",
            recommendation=(
                "Emit the <link rel='canonical'> in the raw HTML <head>. "
                "Conductor warns that JS-injected canonicals are a known "
                "cause of unintended URL parameter explosion in indexes."
            ),
        )

    def _check_render_only_meta_description(self) -> None:
        """Meta description missing in raw HTML but present after rendering."""
        self._check_render_only_field(
            raw_col="raw_meta_description",
            rendered_col="meta_description",
            field_name="meta description",
            severity=Severity.HIGH,
            issue_type="render_only_meta_description",
            recommendation=(
                "Render the <meta name='description'> in the raw HTML. "
                "AI crawlers and pre-render indexability checks need this "
                "available without JS execution."
            ),
        )

    def _check_render_only_h1(self) -> None:
        """H1 missing in raw HTML but present after rendering."""
        self._check_render_only_field(
            raw_col="raw_h1",
            rendered_col="h1",
            field_name="primary H1",
            severity=Severity.HIGH,
            issue_type="render_only_h1",
            recommendation=(
                "Output the <h1> in the raw HTML body. JS-injected H1s "
                "miss the initial indexability assessment and are absent "
                "for non-rendering crawlers."
            ),
        )

    def _check_render_only_meta_robots(self) -> None:
        """Meta robots missing in raw HTML but present after rendering.

        This is especially dangerous given the December 2025 Google docs
        update: indexability is decided on raw HTML, so a JS-injected
        noindex may be ignored entirely while a JS-injected index/follow
        directive is similarly skipped.
        """
        self._check_render_only_field(
            raw_col="raw_meta_robots",
            rendered_col="meta_robots",
            field_name="meta robots directive",
            severity=Severity.CRITICAL,
            issue_type="render_only_meta_robots",
            recommendation=(
                "Output meta robots in the raw HTML or rely on the "
                "X-Robots-Tag HTTP header. Per Google's December 2025 "
                "clarification, indexability decisions happen before the "
                "renderer runs — JS-injected robots directives can be "
                "skipped entirely."
            ),
        )

    def _check_render_only_field(
        self,
        raw_col: str,
        rendered_col: str,
        field_name: str,
        severity: Severity,
        issue_type: str,
        recommendation: str,
    ) -> None:
        """Generic raw-vs-rendered field comparison.

        Flags pages where the rendered column has a value but the raw
        column is empty/missing.
        """
        if not self.has_columns([raw_col, rendered_col]):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        raw_missing = scope[raw_col].apply(is_empty_or_missing)
        rendered_present = ~scope[rendered_col].apply(is_empty_or_missing)
        condition = raw_missing & rendered_present

        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=severity,
                category=AuditCategory.JS_RENDERING,
                issue_type=issue_type,
                title=f"{count} pages with {field_name} only in rendered HTML",
                description=(
                    f"Found {count} pages where the {field_name} is "
                    "missing from the raw HTML response but appears after "
                    "JavaScript renders. Crawlers that don't render JS "
                    "won't see this element at all, and Google decides "
                    "indexability before its renderer runs."
                ),
                affected_urls=urls,
                count=count,
                recommendation=recommendation,
                impact=(
                    f"Render-only {field_name} weakens both Google's "
                    "indexing pipeline (decisions happen pre-render) and "
                    "AI crawler visibility (no rendering at all)."
                ),
            )

    # =========================================================================
    # LINK DISCOVERY CHECKS
    # =========================================================================

    def _check_link_discovery_gap(self) -> None:
        """Rendered outlinks significantly higher than raw — JS-dependent nav."""
        if not self.has_columns(["raw_outlinks", "rendered_outlinks"]):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        raw = scope["raw_outlinks"].fillna(0)
        rendered = scope["rendered_outlinks"].fillna(0)

        absolute_gap = rendered - raw
        ratio = rendered / raw.replace(0, pd.NA)

        condition = (
            (absolute_gap >= LINK_GAP_THRESHOLD)
            & (ratio >= LINK_GAP_RATIO)
        )
        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            avg_gap = float(absolute_gap[condition].mean())
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.JS_RENDERING,
                issue_type="link_discovery_gap",
                title=f"{count} pages with JS-dependent navigation",
                description=(
                    f"Found {count} pages where the rendered HTML exposes "
                    f"significantly more outlinks than the raw HTML "
                    f"(avg gap of {avg_gap:.0f} links per page). Critical "
                    "navigation, related-page links, or content links are "
                    "JS-injected."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Render primary navigation and any pagination links "
                    "in raw HTML. Reserve JS injection for purely "
                    "interactive elements (filters, modals, accordions). "
                    "Links that crawlers should follow must be present in "
                    "the initial response."
                ),
                impact=(
                    "JS-injected links are discovered slowly by Google "
                    "(if at all) and not at all by AI crawlers. This "
                    "weakens internal link equity flow and crawl coverage."
                ),
                additional_data={"avg_link_gap": round(avg_gap, 0)},
            )

    # =========================================================================
    # INTERACTION-GATED CONTENT
    # =========================================================================

    def _check_interaction_gated_content(self) -> None:
        """Flag pages whose content AND links are both JS-injected together.

        Googlebot renders JavaScript but never triggers user interactions
        (click, hover, scroll). Content hidden behind accordions, tabs,
        "read more" expanders, and "load more" widgets is therefore at risk,
        and AI crawlers (which don't render at all) miss it entirely.

        Pure raw-vs-rendered word/link counts cannot prove that a specific
        block is interaction-gated rather than merely injected on page load —
        Screaming Frog renders without clicking, so this is a heuristic, not a
        certainty. What it CAN detect reliably is the co-occurrence signature
        of interactive widgets: a page where BOTH a meaningful share of the
        text AND a meaningful share of the outlinks only appear after JS runs.
        That combination is the fingerprint of tabbed/accordion/load-more
        components (each panel carries its own copy and its own links), and it
        fires on a narrower, distinct population than either the word-gap or
        link-gap check alone. Every flagged page is worth a manual check for
        click-to-reveal content that Googlebot won't expand.

        Requires raw + rendered word counts AND raw + rendered outlink counts.
        No-ops if any of those columns are absent.
        """
        if not self.has_columns(
            [
                "raw_word_count",
                "rendered_word_count",
                "raw_outlinks",
                "rendered_outlinks",
            ]
        ):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if scope.empty:
            return

        raw_words = scope["raw_word_count"].fillna(0)
        rendered_words = scope["rendered_word_count"].fillna(0)
        raw_links = scope["raw_outlinks"].fillna(0)
        rendered_links = scope["rendered_outlinks"].fillna(0)

        word_ratio = rendered_words / raw_words.replace(0, pd.NA)
        link_gap = rendered_links - raw_links
        link_ratio = rendered_links / raw_links.replace(0, pd.NA)

        condition = (
            (raw_words >= GATED_CONTENT_MIN_RAW_WORDS)  # already-hydrated page
            & (rendered_words >= 300)
            & (word_ratio >= RENDER_GAP_RATIO)          # text injected by JS
            & (link_gap >= LINK_GAP_THRESHOLD)          # links injected too
            & (link_ratio >= LINK_GAP_RATIO)
        )

        urls = (
            scope.loc[condition, "url"].tolist()
            if "url" in scope.columns
            else []
        )
        count = int(condition.sum())
        if count == 0:
            return

        avg_word_ratio = float(word_ratio[condition].mean())
        avg_link_gap = float(link_gap[condition].mean())

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.JS_RENDERING,
            issue_type="interaction_gated_content",
            title=f"{count} pages show interactive-widget content gating",
            description=(
                f"Found {count} indexable pages where both a large share of "
                "the text and a large share of the outlinks only appear after "
                "JavaScript renders (avg rendered-to-raw word ratio "
                f"{avg_word_ratio:.1f}x, avg {avg_link_gap:.0f} extra links "
                "per page). This co-occurrence is the signature of interactive "
                "widgets — accordions, tabs, 'read more' expanders, and 'load "
                "more' lists — where each panel carries its own copy and "
                "links. Googlebot renders JavaScript but never clicks, hovers, "
                "or scrolls to expand these, and AI crawlers don't render at "
                "all, so gated panels can be missed entirely."
            ),
            affected_urls=urls,
            recommendation=(
                "Manually inspect a sample of these pages for click-to-reveal "
                "content. For anything that must rank or be cited, render the "
                "panel content in the initial HTML (open by default, or "
                "present in the DOM with CSS-only show/hide rather than "
                "JS-injected on click). Reserve interaction-gated loading for "
                "genuinely secondary content. Load-more / infinite-scroll "
                "lists should also expose a crawlable paginated URL set."
            ),
            impact=(
                "Content and links that require a user interaction to appear "
                "are invisible to non-rendering AI crawlers and are not "
                "expanded by Googlebot, so their text is not indexed and the "
                "links pass no internal equity or crawl discovery."
            ),
            additional_data={
                "affected_count": count,
                "avg_word_ratio": round(avg_word_ratio, 1),
                "avg_link_gap": round(avg_link_gap, 0),
            },
        )

    # =========================================================================
    # URL PATTERN CHECKS
    # =========================================================================

    def _check_hash_based_routing(self) -> None:
        """Indexable URLs using hash-based routing (#/, #!, etc.)."""
        if not self.has_column("url"):
            return

        url_pattern = re.compile(r"#[!/]")
        condition = self.df["url"].astype(str).apply(
            lambda u: bool(url_pattern.search(u))
        )

        urls = self.filter_by_condition(condition)
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.JS_RENDERING,
                issue_type="hash_based_routing",
                title=f"{count} URLs use hash-based routing",
                description=(
                    f"Found {count} URLs containing hash fragments "
                    "(#/ or #!) used as routing markers. Hash fragments "
                    "are not crawlable as separate pages — Google treats "
                    "everything before the # as the canonical URL."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Migrate to History API URLs (push state). Replace "
                    "/#/category/shoes with /category/shoes/. Any hash-"
                    "routed page intended to rank must be exposed at a "
                    "real URL."
                ),
                impact=(
                    "Hash-routed pages cannot be indexed independently. "
                    "All rank signals collapse onto the parent URL, and "
                    "deep pages become invisible to search."
                ),
            )

    # =========================================================================
    # RENDER BUDGET EXPOSURE
    # =========================================================================

    def _check_render_budget_exposure(self) -> None:
        """High TBT pages risk exceeding Google's ~5s render window."""
        if not self.has_column("tbt"):
            return

        # TBT > 1.5s is severe — main thread blocked long enough that
        # critical content may not paint within Google's render budget.
        condition = self.df["tbt"] > 1500
        urls = self.filter_by_condition(condition)
        count = int(condition.sum())

        if count > 0:
            avg_tbt = float(self.df.loc[condition, "tbt"].mean())
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.JS_RENDERING,
                issue_type="render_budget_exposure",
                title=f"{count} pages risk exceeding Google's render budget",
                description=(
                    f"Found {count} pages with Total Blocking Time over "
                    f"1.5 seconds (avg {avg_tbt:.0f}ms). Google's renderer "
                    "operates within an approximate 5-second snapshot "
                    "window. High TBT means long JS tasks may push "
                    "critical content past that window."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Break up long JavaScript tasks (>50ms). Audit the "
                    "Coverage panel in DevTools to find unused JS. Code-"
                    "split heavy bundles. Defer non-critical scripts. "
                    "Reduce third-party tag count above the fold."
                ),
                impact=(
                    "Pages that don't finish rendering within Google's "
                    "budget are indexed as a partial snapshot — content, "
                    "links, and schema added late may be missed."
                ),
                additional_data={"avg_tbt_ms": round(avg_tbt, 0)},
            )
