"""URL Structure Auditor.

Audits URL-level hygiene issues that affect crawlability, duplicate
content risk, and signal consolidation. Goes beyond the basic checks
embedded in the technical auditor to surface the full spectrum of URL
quality problems.

The technical auditor already covers two URL-pattern checks (trailing
slash inconsistency and mixed-case URLs) because those overlap with
indexability concerns. This auditor handles the rest:

- URLs with consecutive slashes (`//`)
- URLs with underscores instead of hyphens
- URLs with stop words / overly long slugs
- URLs with parameters that should be canonical paths
- URLs with non-ASCII characters or unencoded special chars
- Hash fragments used as routing markers (covered in JS auditor too,
  but worth having a structural check)
- URL depth (deeply nested URLs > 4 levels deep)
- Trailing index.html / index.php
- Excessive parameter count
- Mixed www/non-www in canonical declarations
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional
from urllib.parse import urlparse, parse_qs

import pandas as pd

from .base_auditor import BaseAuditor, is_empty_or_missing
from models.audit_result import AuditCategory, AuditIssue, Severity


URL_DEPTH_THRESHOLD = 5
"""URLs nested more than this many levels deep are flagged. Mark and
many SEO sources note that pages buried 5+ clicks deep tend to
underperform regardless of content quality."""

LONG_SLUG_THRESHOLD = 80
"""Slugs longer than this many characters are flagged. Long slugs are
hard to read, hard to share, and often indicate keyword stuffing."""

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "must", "can",
    "to", "of", "in", "on", "at", "by", "for", "with", "from", "into",
    "this", "that", "these", "those", "it", "its",
}
"""Stop words that, when present in URL slugs, usually indicate poor
URL hygiene. Compare /how-to-make-a-cake/ (good) vs /how-to-make-a-cake-
that-is-the-best-cake-in-the-world/ (bad)."""


class URLStructureAuditor(BaseAuditor):
    """Auditor for URL structural hygiene issues."""

    def get_audit_type(self) -> str:
        return "technical"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        self._check_consecutive_slashes()
        self._check_underscores_in_slugs()
        self._check_excessively_long_slugs()
        self._check_index_file_in_url()
        self._check_excessive_parameters()
        self._check_unencoded_special_chars()
        self._check_excessive_url_depth()
        self._check_canonical_protocol_mismatch()

        return self.issues

    # =========================================================================
    # CHECKS
    # =========================================================================

    def _check_consecutive_slashes(self) -> None:
        """Flag URLs containing `//` in the path (after the protocol).

        Consecutive slashes are usually a bug — broken concatenation in
        a template, a missing trailing-slash trim, or a manual error.
        They create technically-different-but-visually-identical URLs
        that can become duplicate content if both resolve.
        """
        scope = self._get_scope()
        if scope.empty:
            return

        def has_double_slash(url: str) -> bool:
            if not isinstance(url, str):
                return False
            try:
                path = urlparse(url).path
                return "//" in path
            except Exception:
                return False

        condition = scope["url"].apply(has_double_slash)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.URL_STRUCTURE,
                issue_type="consecutive_slashes",
                title=f"{count} URLs contain consecutive slashes",
                description=(
                    f"Found {count} URLs containing `//` in the path. "
                    "This is almost always a template bug — a missing "
                    "trailing-slash trim, broken URL concatenation, or "
                    "a manual error. The resulting URLs are technically "
                    "valid but create duplicate-content risk if both "
                    "the clean and double-slash versions resolve."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Fix the source of the double-slash generation in "
                    "the template or CMS. 301-redirect any double-slash "
                    "URLs to their clean equivalents. Configure the "
                    "server (nginx, Apache, or framework) to "
                    "automatically collapse multiple slashes to single "
                    "slashes."
                ),
                impact=(
                    "Double-slash URLs split ranking signals from "
                    "their canonical equivalents and indicate poor "
                    "URL hygiene to crawlers. They're often linked "
                    "internally as a result of the same bug, so the "
                    "issue compounds across the site."
                ),
            )

    def _check_underscores_in_slugs(self) -> None:
        """Flag URLs using underscores instead of hyphens as word separators.

        Google has stated hyphens are the preferred word separator in
        URLs. Underscores are treated as part of the same word —
        `keyword_phrase` is read as one token, `keyword-phrase` as two.
        """
        scope = self._get_scope()
        if scope.empty:
            return

        def has_underscore_in_path(url: str) -> bool:
            if not isinstance(url, str):
                return False
            try:
                path = urlparse(url).path
                # Skip URLs where the underscore is in a known asset
                # path (less impactful than content URLs)
                if path.startswith(("/wp-content/", "/wp-includes/")):
                    return False
                return "_" in path
            except Exception:
                return False

        condition = scope["url"].apply(has_underscore_in_path)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.URL_STRUCTURE,
                issue_type="underscores_in_slugs",
                title=f"{count} URLs use underscores instead of hyphens",
                description=(
                    f"Found {count} indexable URLs using underscores "
                    "as word separators in the path. Google treats "
                    "hyphens as word separators and underscores as "
                    "part of the same word — `keyword_phrase` is read "
                    "as one token, `keyword-phrase` as two distinct "
                    "words. Hyphens are the preferred convention."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "For new URLs going forward, use hyphens. For "
                    "existing URLs with underscores: leave them in "
                    "place if they have established backlinks and "
                    "rankings — changing them creates a 301-redirect "
                    "burden with marginal SEO gain. Only migrate "
                    "underscore-to-hyphen URLs as part of a broader "
                    "URL restructure that's already happening."
                ),
                impact=(
                    "Underscored URLs are slightly harder for Google "
                    "to parse semantically. The impact is small "
                    "individually but adds up across many URLs. The "
                    "more important signal here is that underscored "
                    "URLs typically indicate older, less-maintained "
                    "URL structures that may benefit from a broader "
                    "audit."
                ),
            )

    def _check_excessively_long_slugs(self) -> None:
        """Flag URLs with very long final slugs.

        Long slugs usually indicate keyword stuffing or a CMS that
        auto-generates slugs from full titles without truncation.
        Both hurt URL readability and shareability.
        """
        scope = self._get_scope()
        if scope.empty:
            return

        def slug_too_long(url: str) -> bool:
            if not isinstance(url, str):
                return False
            try:
                path = urlparse(url).path
                segments = [s for s in path.split("/") if s]
                if not segments:
                    return False
                last = segments[-1]
                # Skip obvious file extensions
                if "." in last and not last.startswith("."):
                    last = last.rsplit(".", 1)[0]
                return len(last) > LONG_SLUG_THRESHOLD
            except Exception:
                return False

        condition = scope["url"].apply(slug_too_long)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.URL_STRUCTURE,
                issue_type="long_url_slugs",
                title=f"{count} URLs have excessively long slugs",
                description=(
                    f"Found {count} URLs with the final slug exceeding "
                    f"{LONG_SLUG_THRESHOLD} characters. Long slugs "
                    "usually indicate (a) keyword stuffing, (b) a CMS "
                    "auto-generating slugs from full titles without "
                    "truncation, or (c) URLs constructed mechanically "
                    "from page metadata. They hurt URL readability, "
                    "shareability, and CTR in SERPs where the URL is "
                    "displayed."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "For new URLs: keep slugs concise — ideally under "
                    "60 characters, focused on the primary keyword "
                    "phrase only. For existing long slugs: leave in "
                    "place if rankings are healthy. Only shorten "
                    "during a planned URL restructure with proper 301 "
                    "redirects in place."
                ),
                impact=(
                    "Long slugs make URLs harder to read, share, and "
                    "type. They also signal poor URL hygiene to "
                    "crawlers. The direct ranking impact is small but "
                    "they correlate with other URL-quality issues "
                    "worth investigating."
                ),
            )

    def _check_index_file_in_url(self) -> None:
        """Flag URLs containing /index.html, /index.php, /default.aspx etc.

        These should be canonicalized to the directory URL. When both
        `/about/` and `/about/index.html` resolve, they create
        duplicate content.
        """
        scope = self._get_scope()
        if scope.empty:
            return

        index_pattern = re.compile(
            r"/(index|default|home)\.(html?|php|aspx?|jsp)(\?|#|$)",
            re.IGNORECASE,
        )

        def has_index_file(url: str) -> bool:
            if not isinstance(url, str):
                return False
            return bool(index_pattern.search(url))

        condition = scope["url"].apply(has_index_file)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.URL_STRUCTURE,
                issue_type="index_file_in_url",
                title=f"{count} URLs include explicit index file names",
                description=(
                    f"Found {count} URLs containing explicit index file "
                    "names (index.html, index.php, default.aspx, etc.). "
                    "These should resolve to the parent directory URL "
                    "instead. When both `/about/` and `/about/index.html` "
                    "are accessible, duplicate content is created."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Configure the server to 301-redirect explicit "
                    "index file URLs to their parent directory. For "
                    "example, `/about/index.html` should redirect to "
                    "`/about/`. Update internal links to use the "
                    "directory URL form. Canonical tags should also "
                    "point to the directory URL, not the index file."
                ),
                impact=(
                    "Index-file URLs split signals between two "
                    "valid URLs for the same content. Fixing them "
                    "consolidates equity and produces cleaner URLs "
                    "for sharing and display."
                ),
            )

    def _check_excessive_parameters(self) -> None:
        """Flag URLs with many query parameters.

        URLs with 4+ parameters often indicate session IDs, tracking
        codes, or faceted-nav explosions that should be canonicalized
        or blocked from indexing.
        """
        scope = self._get_scope()
        if scope.empty:
            return

        def excessive_params(url: str) -> bool:
            if not isinstance(url, str):
                return False
            try:
                params = parse_qs(urlparse(url).query)
                return len(params) >= 4
            except Exception:
                return False

        condition = scope["url"].apply(excessive_params)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.URL_STRUCTURE,
                issue_type="excessive_url_parameters",
                title=f"{count} URLs have 4+ query parameters",
                description=(
                    f"Found {count} indexable URLs with four or more "
                    "query parameters. High parameter counts usually "
                    "indicate session IDs, tracking codes, faceted-nav "
                    "combinations, or analytics tags being indexed. "
                    "Each parameter combination is treated as a "
                    "separate URL, which can multiply the indexable "
                    "page count and waste crawl budget."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "1. Identify which parameters are functional "
                    "(needed for the page to work) vs. tracking-only "
                    "(can be stripped).\n"
                    "2. Configure URL parameter handling in GSC for "
                    "tracking-only parameters.\n"
                    "3. Use canonical tags pointing parameter URLs to "
                    "the clean version of the page.\n"
                    "4. For faceted nav: noindex parameter "
                    "combinations that don't have search demand. Only "
                    "expose facet URLs that target real queries.\n"
                    "5. For session IDs: switch to cookie-based "
                    "session tracking instead of URL parameters."
                ),
                impact=(
                    "URLs with many parameters explode the indexable "
                    "URL count, waste crawl budget on near-duplicate "
                    "pages, and dilute ranking signals across "
                    "parameter variations. On large sites this can "
                    "consume meaningful crawl resources without "
                    "ranking value."
                ),
            )

    def _check_unencoded_special_chars(self) -> None:
        """Flag URLs containing spaces or unencoded special characters."""
        scope = self._get_scope()
        if scope.empty:
            return

        # Look for spaces (encoded as %20 or literal) or other
        # problematic characters in the path
        def has_problematic_chars(url: str) -> bool:
            if not isinstance(url, str):
                return False
            try:
                path = urlparse(url).path
                if "%20" in path or " " in path:
                    return True
                # Common problematic characters: square brackets,
                # curly braces, pipes, backticks
                if any(c in path for c in "[]{}|`"):
                    return True
                return False
            except Exception:
                return False

        condition = scope["url"].apply(has_problematic_chars)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.URL_STRUCTURE,
                issue_type="unencoded_special_chars",
                title=f"{count} URLs contain spaces or special characters",
                description=(
                    f"Found {count} URLs containing spaces (literal or "
                    "%20-encoded) or other problematic characters "
                    "([], {}, |, etc.). These create encoding-related "
                    "issues — different systems may handle the "
                    "encoding inconsistently, leading to broken links "
                    "and duplicate content."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Replace spaces and special characters in URLs "
                    "with hyphens. For existing URLs with these "
                    "characters: 301-redirect to the clean form. "
                    "Configure the CMS to slugify titles properly "
                    "(replace spaces with hyphens, strip special "
                    "characters) so future content doesn't reproduce "
                    "the issue."
                ),
                impact=(
                    "URLs with unencoded special characters often "
                    "break when copy-pasted, shared in messaging "
                    "apps, or processed by analytics tools. They "
                    "also create duplicate-content risk when systems "
                    "encode them differently."
                ),
            )

    def _check_excessive_url_depth(self) -> None:
        """Flag URLs nested more than URL_DEPTH_THRESHOLD levels deep."""
        scope = self._get_scope()
        if scope.empty:
            return

        def too_deep(url: str) -> bool:
            if not isinstance(url, str):
                return False
            try:
                path = urlparse(url).path.strip("/")
                segments = [s for s in path.split("/") if s]
                return len(segments) > URL_DEPTH_THRESHOLD
            except Exception:
                return False

        condition = scope["url"].apply(too_deep)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.URL_STRUCTURE,
                issue_type="excessive_url_depth",
                title=f"{count} URLs are deeply nested ({URL_DEPTH_THRESHOLD}+ levels)",
                description=(
                    f"Found {count} URLs nested more than "
                    f"{URL_DEPTH_THRESHOLD} levels deep in the path. "
                    "Pages buried deep in the URL hierarchy tend to "
                    "rank worse because they accumulate less internal "
                    "link equity and signal lower importance to "
                    "Google. Click depth (how many clicks from the "
                    "homepage) is the more direct signal — but URL "
                    "depth correlates with click depth in most "
                    "templates."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Review the site architecture. Pages that should "
                    "rank well shouldn't require 5+ clicks from the "
                    "homepage to reach. Consider flattening category "
                    "hierarchies or adding contextual links from "
                    "higher-authority pages to bring deep pages "
                    "closer to the surface. The URL itself can stay "
                    "deeply nested — what matters is the click depth "
                    "in the internal link graph."
                ),
                impact=(
                    "Deep URLs receive less internal link equity. "
                    "When combined with weak internal linking, they "
                    "rank poorly regardless of content quality. "
                    "Architecture issues here are usually a much "
                    "bigger deal than the URL structure itself."
                ),
            )

    def _check_canonical_protocol_mismatch(self) -> None:
        """Flag pages where URL and canonical use different protocols/hosts.

        E.g., page is on `https://www.example.com/` but canonical
        points to `https://example.com/` (or http:// vs https://).
        These mismatches can prevent canonical consolidation from
        working correctly.
        """
        if not self.has_columns(["url", "canonical"]):
            return

        scope = self._get_scope()
        if scope.empty:
            return

        def host_mismatch(row: pd.Series) -> bool:
            url = row.get("url")
            canonical = row.get("canonical")
            if not isinstance(url, str) or not isinstance(canonical, str):
                return False
            if is_empty_or_missing(canonical):
                return False
            try:
                u = urlparse(url)
                c = urlparse(canonical)
                if u.scheme != c.scheme:
                    return True
                # Detect www-mismatch
                u_host = u.netloc.lower().lstrip("www.")
                c_host = c.netloc.lower().lstrip("www.")
                if u_host != c_host:
                    return True
                # Detect www in one but not the other
                if u.netloc.lower().startswith("www.") != \
                   c.netloc.lower().startswith("www."):
                    return True
                return False
            except Exception:
                return False

        condition = scope.apply(host_mismatch, axis=1)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.URL_STRUCTURE,
                issue_type="canonical_protocol_mismatch",
                title=f"{count} pages have canonical with mismatched protocol or host",
                description=(
                    f"Found {count} pages where the URL uses a "
                    "different protocol (http vs https) or hostname "
                    "(www vs non-www) than the canonical link element "
                    "specifies. This usually indicates an "
                    "incomplete migration — the canonical was updated "
                    "but pages are still being served on the old "
                    "protocol/host, or vice versa."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Decide on the single canonical protocol+host "
                    "combination for the site (typically https://www. "
                    "or https://). 301-redirect all variants to the "
                    "canonical form at the server level. Update "
                    "canonical tags to match. The page URL and the "
                    "canonical URL should always be identical (or "
                    "the canonical should be a different URL "
                    "entirely if the page is intentionally "
                    "consolidating to another resource)."
                ),
                impact=(
                    "Mismatched canonicals can prevent signal "
                    "consolidation. Google may treat the page and "
                    "its canonical as separate entities, defeating "
                    "the purpose of the canonical declaration. "
                    "During migrations this is a common cause of "
                    "ranking loss."
                ),
            )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_scope(self) -> pd.DataFrame:
        """Return the subset of indexable HTML pages for URL audits."""
        if not self.has_column("url"):
            return pd.DataFrame()
        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        return scope
