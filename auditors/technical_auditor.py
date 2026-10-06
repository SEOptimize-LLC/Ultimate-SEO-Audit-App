"""Technical SEO Auditor.

Analyzes crawlability, indexability, redirects, Core Web Vitals,
and other technical SEO issues.

Based on Technical SEO Agent knowledge base.
"""

import logging
import re
from typing import Optional

import pandas as pd

from .base_auditor import BaseAuditor, is_empty_or_missing
from models.audit_result import AuditIssue, Severity, AuditCategory

logger = logging.getLogger(__name__)

# --- Page Experience thresholds (clutter / third-party proxies) --------------
# Number of unique external JavaScript resources above which a page is treated
# as third-party-script heavy (ad networks, trackers, chat widgets, tag
# managers all load as external JS). A proxy for clutter, not a direct measure.
THIRD_PARTY_SCRIPT_THRESHOLD = 30
# HTML document size (bytes) above which a page is considered a large payload.
LARGE_HTML_BYTES = 500_000
# Bytes-of-HTML per word above which a large page is markup-heavy relative to
# its readable content — a proxy for template/ad-container bloat.
HIGH_BYTES_PER_WORD = 2_000

# --- Index-coverage reconciliation -------------------------------------------
# Below this many crawl-side "should-be-indexed" pages, skip the reconciliation
# check — the ratio is noisy on very small sites.
INDEX_COVERAGE_MIN_PAGES = 20
# Fractional divergence between the crawl's clean indexable-200 count and GSC's
# reported indexed count above which the gap is flagged as a real signal
# (under-indexation) rather than expected slack.
INDEX_COVERAGE_GAP_PCT = 0.20

# --- Hreflang / international -------------------------------------------------
# Regexes matching the internal column names produced by file_parser for each
# numbered hreflang annotation (see _build_hreflang_column_variants there).
_HREFLANG_URL_COL_RE = re.compile(r"^hreflang_\d+_url$")
_HREFLANG_LANG_COL_RE = re.compile(r"^hreflang_\d+_lang$")
X_DEFAULT_LANG = "x-default"

# URL Inspection coverage states that mean the page IS in Google's index.
# Kept as an explicit set, never a substring test: both "not indexed" states
# contain the word "indexed".
_GSC_INDEXED_STATES = {
    "Submitted and indexed",
    "Indexed, not submitted in sitemap",
}


class TechnicalAuditor(BaseAuditor):
    """Auditor for technical SEO issues.

    Checks include:
    - Status codes (401/403/404/429/other 4xx, 5xx errors)
    - Indexability issues (noindex, X-Robots-Tag mismatches, robots.txt)
    - GSC Index Coverage (Crawled / Discovered — currently not indexed)
    - Canonical problems
    - Robots directives
    - Redirect chains/loops
    - Core Web Vitals
    - HTTPS/Security
    """

    def __init__(
        self,
        df: pd.DataFrame,
        gsc_df: Optional[pd.DataFrame] = None,
        crawled_not_indexed_df: Optional[pd.DataFrame] = None,
        discovered_not_indexed_df: Optional[pd.DataFrame] = None,
        gsc_indexed_count: Optional[int] = None,
        gsc_export_verification: Optional[dict] = None,
    ):
        """Initialize the technical auditor.

        Args:
            df: DataFrame from Screaming Frog export
            gsc_df: Optional GSC Search Analytics export (query/page/clicks/
                impressions/position). Enables the zero-impression soft-404
                cross-check.
            crawled_not_indexed_df: Optional GSC Page Indexing export for the
                "Crawled - currently not indexed" status
                (see `utils.file_parser.parse_gsc_index_coverage`).
            discovered_not_indexed_df: Optional GSC Page Indexing export for
                the "Discovered - currently not indexed" status.
            gsc_indexed_count: Optional total number of indexed URLs reported
                by GSC's Page Indexing report ("Indexed" tab), used for the
                index-coverage reconciliation check. When omitted, that check
                still runs in baseline mode — it reports the crawl-side
                should-be-indexed count and the manual reconciliation step.
            gsc_export_verification: Optional mapping of URL -> fresh URL
                Inspection coverageState, produced by
                `scripts/verify_gsc_exports.py`. GSC's Page indexing report
                lags its own URL Inspection verdicts, so export rows can list
                pages that are in fact indexed. When provided, the
                Crawled/Discovered-not-indexed checks drop rows whose fresh
                verdict is indexed instead of diagnosing them; when absent,
                those findings carry an explicit unverified-snapshot caveat.
        """
        super().__init__(df)
        self.gsc_df = gsc_df
        self.crawled_not_indexed_df = crawled_not_indexed_df
        self.discovered_not_indexed_df = discovered_not_indexed_df
        self.gsc_indexed_count = gsc_indexed_count
        # Normalized on trailing slash so an export row and a verification key
        # that differ only in the slash still match.
        self._export_verification = {
            str(u).rstrip("/"): s
            for u, s in (gsc_export_verification or {}).items()
        }

    def get_audit_type(self) -> str:
        return "technical"

    def run_audit(self) -> list[AuditIssue]:
        """Run all technical SEO checks.

        Every check runs in isolation via ``_run_check``: if one check
        raises (e.g. an unexpected column dtype or a malformed export), the
        failure is logged and the remaining checks still run. A single bad
        column can never abort the entire technical audit.
        """
        self.clear_issues()

        checks = (
            # Status code checks
            self._check_401_errors,
            self._check_403_errors,
            self._check_404_errors,
            self._check_429_responses,
            self._check_other_4xx_errors,
            self._check_5xx_errors,
            self._check_soft_404s,
            # Indexability checks
            self._check_noindex_pages,
            self._check_noindex_in_body,
            self._check_x_robots_tag_noindex,
            self._check_blocked_by_robots,
            self._check_orphan_pages,
            self._check_links_on_noindex_pages,
            # GSC Index Coverage checks (require manual GSC Page Indexing export)
            self._check_crawled_not_indexed,
            self._check_discovered_not_indexed,
            self._check_index_coverage_reconciliation,
            # Canonical checks
            self._check_missing_canonical,
            self._check_canonical_mismatch,
            self._check_canonical_chain,
            self._check_canonical_to_redirect,
            self._check_canonical_to_4xx_5xx,
            self._check_declared_vs_selected_canonical,
            # Redirect checks
            self._check_redirect_chains,
            self._check_redirect_loops,
            self._check_http_to_https,
            self._check_internal_links_to_redirects,
            # URL hygiene checks
            self._check_trailing_slash_inconsistency,
            self._check_mixed_case_urls,
            # Core Web Vitals checks
            self._check_poor_lcp,
            self._check_poor_cls,
            self._check_poor_tbt,
            self._check_low_performance_score,
            # Security checks
            self._check_http_pages,
            self._check_mixed_content,
            # Response time
            self._check_slow_pages,
            # Page experience checks (clutter / third-party proxies)
            self._check_third_party_script_density,
            self._check_response_size_to_content_ratio,
            # International / hreflang checks
            self._check_hreflang_return_tags,
            self._check_hreflang_missing_x_default,
        )

        for check in checks:
            self._run_check(check)

        return self.issues

    def _run_check(self, check) -> None:
        """Run a single check method, isolating and logging any failure.

        Checks are expected to no-op gracefully when their required columns
        are absent. This wrapper is the second line of defense: any
        unexpected exception (bad dtype, malformed data) is logged and
        swallowed so it cannot abort the remaining checks.
        """
        try:
            check()
        except Exception:
            logger.exception(
                "Technical check %s failed and was skipped", check.__name__
            )

    # =========================================================================
    # STATUS CODE CHECKS
    # =========================================================================

    def _check_401_errors(self) -> None:
        """Check for pages blocked by authentication (401 Unauthorized)."""
        if not self.has_column("status_code"):
            return

        condition = self.df["status_code"] == 401
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.CRAWLABILITY,
                issue_type="401_unauthorized",
                title=f"{count} pages return 401 Unauthorized",
                description=f"Found {count} URLs returning HTTP 401, meaning they sit behind "
                           "authentication Googlebot cannot pass. Common causes: HTTP Basic "
                           "Auth left on a staging/dev environment, member-only or paywalled "
                           "content, or auth accidentally enabled on a public section after "
                           "launch.",
                affected_urls=urls,
                count=count,
                recommendation="If the content is intentionally private, no action is needed "
                              "beyond keeping these URLs out of the sitemap. If the content "
                              "should be public, remove the auth requirement or scope it to "
                              "allow Googlebot through. For paywalled content that should still "
                              "be indexed, implement paywalled-content structured data "
                              "(isAccessibleForFree) instead of a hard 401.",
                impact="401 pages cannot be crawled or indexed at all — Google gives up "
                      "immediately on an auth challenge rather than treating it as a "
                      "temporary error.",
            )

    def _check_403_errors(self) -> None:
        """Check for pages blocked with 403 Forbidden — flags disambiguation need."""
        if not self.has_column("status_code"):
            return

        condition = self.df["status_code"] == 403
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.CRAWLABILITY,
                issue_type="403_forbidden",
                title=f"{count} pages return 403 Forbidden",
                description=f"Found {count} URLs returning HTTP 403 to this crawl. This status "
                           "is ambiguous without further verification: it may mean a WAF, "
                           "bot-protection rule, or IP/geo block is also blocking Googlebot (a "
                           "real indexability problem) — or it may mean the crawler used for "
                           "this audit specifically triggered bot-protection while Googlebot "
                           "passes through fine (a false positive specific to this crawl, not "
                           "a real issue).",
                affected_urls=urls,
                count=count,
                recommendation="Before recommending a fix, disambiguate: check GSC URL "
                              "Inspection's live test for each affected URL (it uses Google's "
                              "own fetch, not this crawler), or re-check with a "
                              "Googlebot-verified user agent. Only escalate to a WAF/firewall "
                              "fix if Google's own fetch also returns 403 or a coverage error. "
                              "Never recommend loosening bot-protection based on this crawl's "
                              "403 alone.",
                impact="If Googlebot is genuinely blocked, these pages cannot be crawled or "
                      "indexed. If it's a crawler-specific false positive, no real "
                      "indexability impact exists and no fix is needed.",
            )

    def _check_404_errors(self) -> None:
        """Check for Not Found (404) pages."""
        if not self.has_column("status_code"):
            return

        condition = self.df["status_code"] == 404
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.CRAWLABILITY,
                issue_type="404_errors",
                title=f"{count} pages return 404 Not Found",
                description=f"Found {count} URLs returning HTTP 404. Google's index retains "
                           "legacy URLs after deletion for a period, so 404s discovered via "
                           "old sitemaps, backlinks, or stale internal links are expected — "
                           "the question for each is whether the content should still exist.",
                affected_urls=urls,
                count=count,
                recommendation="For each 404: if the content moved, add a 301 redirect to the "
                              "closest equivalent page. If it's permanently gone, leave it as "
                              "404 (or return 410 to signal permanence) rather than redirecting "
                              "to the homepage. Remove 404 URLs from the sitemap and fix any "
                              "internal links still pointing to them. Check for external "
                              "backlinks before deciding between 404 and 410 — a 410 signals "
                              "Google to drop the URL faster.",
                impact="404 errors waste crawl budget and break the user/link-equity path for "
                      "any page still receiving internal or external links.",
            )

    def _check_429_responses(self) -> None:
        """Check for 429 Too Many Requests — a crawl-rate artifact, not a confirmed issue."""
        if not self.has_column("status_code"):
            return

        condition = self.df["status_code"] == 429
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.CRAWLABILITY,
                issue_type="429_rate_limited",
                title=f"{count} URLs returned 429 during this crawl (re-crawl to confirm)",
                description=f"Found {count} URLs returning HTTP 429 (Too Many Requests) during "
                           "this crawl. This status code almost always reflects the crawler "
                           "exceeding a rate limit on the server or WAF, not a real "
                           "indexability problem with these URLs — their true status is "
                           "unknown until re-verified.",
                affected_urls=urls,
                count=count,
                recommendation="Re-run the crawl at a slower rate (increase the crawl delay / "
                              "reduce concurrent threads) to get each URL's real status code. "
                              "Do not include these URLs in a correction or cleanup list until "
                              "re-verified — treating a rate-limit artifact as a confirmed "
                              "problem produces false work items.",
                impact="No confirmed SEO impact from this crawl alone. If the site also "
                      "rate-limits Googlebot in production, that IS a real crawlability "
                      "problem — check Search Console crawl stats for a spike in server "
                      "errors to confirm before acting.",
            )

    def _check_other_4xx_errors(self) -> None:
        """Check for remaining 4xx codes not covered by dedicated checks (400, 405, 410, etc.)."""
        if not self.has_column("status_code"):
            return

        handled_codes = {401, 403, 404, 429}
        condition = (
            (self.df["status_code"] >= 400)
            & (self.df["status_code"] < 500)
            & (~self.df["status_code"].isin(handled_codes))
        )
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            error_breakdown = self.df.loc[condition, "status_code"].value_counts().to_dict()

            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.CRAWLABILITY,
                issue_type="other_4xx_errors",
                title=f"{count} pages return other 4XX errors",
                description=f"Found {count} URLs returning client error codes other than "
                           f"401/403/404/429. Breakdown: {error_breakdown}. Common causes: 400 "
                           "from malformed URLs or bad parameters, 405 from method "
                           "restrictions, 410 from intentional permanent removal.",
                affected_urls=urls,
                count=count,
                recommendation="Identify the exact code per URL via server logs or live "
                              "inspection. For 400: fix the malformed-URL source (often a "
                              "broken internal link generator). For 410: if intentional, no "
                              "action needed. For anything else, investigate the specific "
                              "server rule producing it.",
                impact="These codes waste crawl budget and, apart from intentional 410s, "
                      "usually indicate a bug in URL generation or a server misconfiguration.",
                additional_data={"breakdown": error_breakdown},
            )

    def _check_5xx_errors(self) -> None:
        """Check for 5xx server errors."""
        if not self.has_column("status_code"):
            return

        condition = (self.df["status_code"] >= 500) & (self.df["status_code"] < 600)
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.CRAWLABILITY,
                issue_type="5xx_errors",
                title=f"{count} pages return 5XX errors",
                description=f"Found {count} URLs returning server error status codes (500-599). "
                           "These indicate server-side problems.",
                affected_urls=urls,
                count=count,
                recommendation="Investigate server logs to identify and fix the underlying issues. "
                              "Common causes: broken scripts, database errors, resource exhaustion.",
                impact="5XX errors prevent pages from being indexed and create very poor user experience. "
                      "Persistent 5XX errors can lead to pages being dropped from the index.",
            )

    def _check_soft_404s(self) -> None:
        """Check for soft 404s (200 status but likely error pages).

        When a GSC Search Analytics export is available, thin-content
        candidates are cross-referenced against GSC impressions — zero
        impressions over the export window is a stronger soft-404 signal
        (the page has never been shown for any query) and is surfaced as a
        separate, higher-severity issue.
        """
        if not self.has_columns(["status_code", "word_count"]):
            return

        # Pages with 200 status but very thin content might be soft 404s
        condition = (
            (self.df["status_code"] == 200) &
            (self.df["word_count"] < 50) &
            (self.df.get("indexability", pd.Series([""])) == "Indexable")
        )
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count == 0:
            return

        # Cross-reference GSC impressions when available: 0 impressions
        # strengthens the soft-404 signal.
        zero_impression_urls = []
        if (
            self.gsc_df is not None
            and len(self.gsc_df) > 0
            and self.has_column("url")
            and {"page", "impressions"}.issubset(set(self.gsc_df.columns))
        ):
            impressions_by_page = (
                self.gsc_df.groupby("page")["impressions"].sum().to_dict()
            )
            for u in urls:
                if impressions_by_page.get(u, 0) == 0:
                    zero_impression_urls.append(u)

        if zero_impression_urls:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="soft_404s_confirmed_zero_impressions",
                title=f"{len(zero_impression_urls)} likely soft 404 pages with zero GSC impressions",
                description=f"Of the {count} thin-content pages flagged below, "
                           f"{len(zero_impression_urls)} have zero impressions in the GSC "
                           "Search Analytics export — meaning they've never been shown for any "
                           "query over that period. Combined with under 50 words of content on "
                           "a 200-status page, this is a strong soft-404 signal rather than a "
                           "borderline case.",
                affected_urls=zero_impression_urls,
                count=len(zero_impression_urls),
                recommendation="Prioritize these over the wider thin-content list below. "
                              "Configure the server to return a genuine 404/410 status, or add "
                              "substantive unique content if the page should exist and rank.",
                impact="These pages are Google-confirmed non-performers with near-empty "
                      "content — removing or fixing them is close to zero-risk since they're "
                      "not currently earning any visibility to lose.",
            )

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.INDEXABILITY,
            issue_type="soft_404s",
            title=f"{count} potential soft 404 pages",
            description=f"Found {count} pages with 200 status but very little content (<50 words). "
                       "These may be soft 404s that should return proper 404 status.",
            affected_urls=urls,
            count=count,
            recommendation="Review these pages. If they are error pages, configure server to return "
                          "proper 404 status. If legitimate, add more content.",
            impact="Soft 404s waste crawl budget and can dilute site quality signals.",
        )

    # =========================================================================
    # INDEXABILITY CHECKS
    # =========================================================================

    def _check_noindex_pages(self) -> None:
        """Check for noindex pages that may be unintentional."""
        if not self.has_column("meta_robots"):
            return

        # Find noindex pages. Cast to string first: an Excel crawl where this
        # column exists but every row is blank is read by pandas as float64
        # (all NaN), and .str accessors raise AttributeError on non-string
        # dtypes — which, unguarded, would abort the whole audit.
        noindex_condition = self.df["meta_robots"].astype(str).str.contains(
            "noindex", case=False, na=False
        )

        # Filter to potentially problematic ones (pages with content or traffic)
        if self.has_column("word_count"):
            # Noindex pages with significant content
            problem_condition = noindex_condition & (self.df["word_count"] > 300)
        else:
            problem_condition = noindex_condition

        urls = self.filter_by_condition(problem_condition)
        count = self.count_by_condition(problem_condition)
        total_noindex = self.count_by_condition(noindex_condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="noindex_with_content",
                title=f"{count} noindex pages with significant content",
                description=f"Found {count} pages with noindex directive that have substantial content (>300 words). "
                           f"Total noindex pages: {total_noindex}. Noindex on content-heavy pages is almost always "
                           "accidental — staging settings left on, template misconfiguration, or a bulk-edit mistake.",
                affected_urls=urls,
                count=count,
                recommendation="Review each noindex page. If it should be indexed, remove the noindex directive. "
                              "Common accidental noindex: staging settings left on, template issues, plugin conflicts. "
                              "Also note: links from noindex pages eventually get treated as nofollow, so any internal "
                              "linking from these pages is leaking equity.",
                impact="Noindex pages are excluded from search results entirely. For pages with substantial content, "
                      "this is usually unintended and represents a direct loss of organic traffic on those URLs.",
            )

    def _check_x_robots_tag_noindex(self) -> None:
        """Check for noindex set only via X-Robots-Tag header (invisible in page source).

        Google honors X-Robots-Tag noindex identically to a meta robots
        noindex tag, but the header is applied server/CDN/middleware-side
        and never appears when viewing page source — making it the most
        commonly missed source of accidental noindex. Flags any page where
        the header carries noindex but the HTML meta robots tag does not,
        since that combination means the exclusion is invisible to anyone
        auditing the rendered HTML alone.
        """
        if not self.has_column("x_robots_tag"):
            return

        # Cast to string before .str.contains(): an Excel-sourced crawl where
        # this column exists but every row is blank (the common case — most
        # sites never set X-Robots-Tag) gets read by pandas as float64 (all
        # NaN), and .str accessors raise AttributeError on non-string dtypes.
        header_noindex = self.df["x_robots_tag"].astype(str).str.contains(
            "noindex", case=False, na=False
        )
        if not header_noindex.any():
            return

        if self.has_column("meta_robots"):
            meta_noindex = self.df["meta_robots"].astype(str).str.contains(
                "noindex", case=False, na=False
            )
        else:
            meta_noindex = pd.Series(False, index=self.df.index)

        # The dangerous case: header says noindex, but the HTML meta tag
        # doesn't — invisible via view-source, easy to miss in a manual audit.
        condition = header_noindex & ~meta_noindex

        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)
        total_header_noindex = self.count_by_condition(header_noindex)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="x_robots_tag_noindex_hidden",
                title=f"{count} pages noindexed via X-Robots-Tag header only",
                description=f"Found {count} pages where the X-Robots-Tag HTTP response header "
                           "carries a noindex directive that is NOT also present in the HTML "
                           f"meta robots tag (total pages with X-Robots-Tag noindex: "
                           f"{total_header_noindex}). Header-level noindex is applied "
                           "server-side or at the CDN/middleware layer and is invisible when "
                           "viewing page source — this is the most commonly missed source of "
                           "accidental noindex because a normal 'view source' check shows "
                           "nothing wrong.",
                affected_urls=urls,
                count=count,
                recommendation="Inspect response headers directly (`curl -I <url>` or the "
                              "DevTools Network panel) rather than relying on view-source. "
                              "Trace which layer is setting the header — CDN rule, reverse "
                              "proxy config, WAF, or an app-level middleware rule applied to a "
                              "URL pattern. If the page should be indexed, remove the header "
                              "rule at its source layer.",
                impact="These pages are fully excluded from search results exactly as if a "
                      "meta noindex tag were present, but the exclusion cannot be found by "
                      "inspecting the page's HTML — only by checking response headers.",
            )

    def _check_blocked_by_robots(self) -> None:
        """Check for pages blocked by robots.txt."""
        if not self.has_column("robots_txt_status"):
            return

        # Cast to string first — a column read as all-NaN float would raise
        # AttributeError on the .str accessor and abort the audit.
        condition = self.df["robots_txt_status"].astype(str).str.contains(
            "blocked", case=False, na=False
        )
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.CRAWLABILITY,
                issue_type="blocked_by_robots",
                title=f"{count} pages blocked by robots.txt",
                description=f"Found {count} pages that are blocked from crawling by robots.txt rules.",
                affected_urls=urls,
                count=count,
                recommendation="Review robots.txt rules. Ensure you're not accidentally blocking important content. "
                              "Note: pages can still be indexed if linked from external sites.",
                impact="Blocked pages cannot be crawled, preventing content updates from being discovered.",
            )

    def _check_orphan_pages(self) -> None:
        """Check for orphan pages (no internal links pointing to them).

        Applies a scope filter to exclude pages that have no SEO value to
        begin with — orphan status is correct for these and shouldn't be
        flagged. Excluded patterns: PPC landing pages, thank-you pages,
        application forms, terms/privacy/legal pages, 404/error pages,
        login/admin pages, draft/test pages.
        """
        if not self.has_column("internal_links_in"):
            return

        # Restrict to indexable HTML pages — non-indexable orphan status
        # is usually intentional (utility pages, blocked resources).
        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        # Apply scope filter: exclude utility/non-SEO URL patterns.
        if "url" in scope.columns:
            scope = scope[~scope["url"].apply(self._is_non_seo_url)]

        condition = scope["internal_links_in"] == 0
        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="orphan_pages",
                title=f"{count} orphan pages (no internal links)",
                description=f"Found {count} indexable pages with zero internal "
                           "links pointing to them. These pages are isolated "
                           "from the site structure. Utility pages (PPC, "
                           "thank-you, forms, legal, error pages) have been "
                           "excluded from this count — orphan status on those "
                           "is correct and not actionable.",
                affected_urls=urls,
                count=count,
                recommendation="For each page: either (a) add contextual "
                              "internal links from relevant parent hubs and "
                              "service-area pages, or (b) remove the page "
                              "from the sitemap if it shouldn't be indexed. "
                              "Don't create generic 'related links' widgets "
                              "as the only fix — link from contextually "
                              "relevant pages with descriptive anchor text.",
                impact="Orphan pages receive no internal link equity and signal low importance to Google. "
                      "They typically rank poorly regardless of content quality.",
            )

    @staticmethod
    def _is_non_seo_url(url: str) -> bool:
        """Return True if the URL pattern indicates a non-SEO utility page.

        Used to apply scope filters consistently across orphan, sitemap,
        and content-quality checks. Patterns derived from real client
        audits across the IHS portfolio.
        """
        if not isinstance(url, str):
            return False
        u = url.lower()

        # Path-based markers
        markers = (
            "/thank-you",
            "/thanks/",
            "/thankyou",
            "/application-form",
            "/terms-of-use",
            "/terms-of-service",
            "/terms-and-conditions",
            "/privacy-policy",
            "/privacy/",
            "/cookie-policy",
            "/disclaimer",
            "/404-error",
            "/404/",
            "/page-not-found",
            "/error/",
            "/login",
            "/wp-login",
            "/wp-admin",
            "/admin/",
            "/test-page",
            "/test-lead",
            "/scheduling-pro-test",
            "/draft-",
            "/-draft/",
            "/staging/",
            "/dev/",
            "/cart",
            "/checkout",
            "/my-account",
            "/account/",
            "/wishlist",
        )
        if any(m in u for m in markers):
            return True

        # PPC slug suffix patterns (e.g., /furnace-ppc-001/, /landing-ppc/)
        if "-ppc-" in u or u.rstrip("/").endswith("-ppc"):
            return True

        # Pagination URLs (page=N or /page/N/)
        # Note: these are usually noindex by default; flagging here would
        # add noise. Exclude them from orphan analysis.
        if "/page/" in u and any(c.isdigit() for c in u.split("/page/")[-1]):
            return True

        return False

    # =========================================================================
    # GSC INDEX COVERAGE CHECKS
    # =========================================================================

    _EXPORT_LAG_CAVEAT = (
        " These counts come directly from the GSC export snapshot and have "
        "not been re-verified per URL. GSC's Page indexing report can lag "
        "its own URL Inspection verdicts, so a share of these pages may "
        "already be indexed; re-check a sample in URL Inspection before "
        "acting on individual URLs."
    )

    def _partition_export_urls(
        self, flagged_urls: list[str]
    ) -> Optional[tuple[list[str], list[str], int]]:
        """Split GSC export rows by their fresh URL Inspection verdict.

        Returns (now_indexed, remaining, unverified_count), or None when no
        verification data was supplied. `remaining` keeps both confirmed
        not-indexed URLs and URLs the verification run did not cover — a
        missing verdict is not evidence the page is indexed.
        """
        if not self._export_verification:
            return None
        now_indexed: list[str] = []
        remaining: list[str] = []
        unverified = 0
        for u in flagged_urls:
            state = self._export_verification.get(u.rstrip("/"))
            if state in _GSC_INDEXED_STATES:
                now_indexed.append(u)
            else:
                remaining.append(u)
                if state is None:
                    unverified += 1
        return now_indexed, remaining, unverified

    def _verification_note(
        self, reported: int, now_indexed: int, remaining: int, unverified: int
    ) -> str:
        """One-sentence audit trail for a verified export finding."""
        confirmed = remaining - unverified
        note = (
            f" The export listed {reported} URLs. A fresh URL Inspection "
            f"re-check verified {confirmed} still not indexed and found "
            f"{now_indexed} already indexed; the stale rows are excluded "
            "from this finding."
        )
        if unverified:
            plural = "URLs were" if unverified != 1 else "URL was"
            note += (
                f" {unverified} {plural} not covered by the re-check and "
                "are included unverified."
            )
        return note

    def _create_stale_export_insight(
        self, status_label: str, issue_type: str, flagged_urls: list[str]
    ) -> None:
        """Record that every row of a GSC export is now indexed — no action."""
        count = len(flagged_urls)
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.INDEXABILITY,
            issue_type=issue_type,
            title=f"GSC's '{status_label}' export is stale: all {count} "
                  "listed pages are now indexed",
            description=f"The export listed {count} URLs, but a fresh URL "
                       "Inspection re-check found every one already indexed. "
                       "GSC's Page indexing report lags its own URL Inspection "
                       "verdicts, so export rows can describe a state Google "
                       "has since revised. No content or linking work is "
                       "needed on these pages.",
            affected_urls=flagged_urls,
            count=count,
            recommendation="No action needed on these pages. Re-export the "
                          "Page indexing report before the next audit cycle "
                          "so findings start from current data.",
            impact="None. Recorded so the audit trail shows these pages were "
                  "checked and found indexed.",
        )

    def _check_crawled_not_indexed(self) -> None:
        """Surface pages GSC reports as 'Crawled - currently not indexed'.

        This status is Google's own content-quality judgment, not a
        technical block — pure Screaming Frog crawl data can never reveal
        it. Requires a manual export of this status from GSC's Page
        indexing report (see `crawled_not_indexed_df`). Cross-references
        word_count from the crawl data where the URL is present, since
        thin/low-value content is the most common driver of this status.
        """
        if self.crawled_not_indexed_df is None or len(self.crawled_not_indexed_df) == 0:
            return
        if "url" not in self.crawled_not_indexed_df.columns:
            return

        # Deduplicate before counting so the count is unique URLs, not raw
        # rows (project Rule 10 — GSC exports can repeat a URL across rows).
        flagged_urls = list(
            dict.fromkeys(self.crawled_not_indexed_df["url"].dropna().astype(str))
        )
        count = len(flagged_urls)
        if count == 0:
            return

        # Fresh URL Inspection verdicts (when supplied) beat the export
        # snapshot: rows Google has since indexed are stale report lag, not
        # findings, and diagnosing them as thin content would be wrong twice.
        split = self._partition_export_urls(flagged_urls)
        if split is not None:
            now_indexed, remaining, unverified = split
            if not remaining:
                self._create_stale_export_insight(
                    "Crawled - currently not indexed",
                    "gsc_crawled_not_indexed_stale",
                    flagged_urls,
                )
                return
            verification_note = self._verification_note(
                count, len(now_indexed), len(remaining), unverified
            )
            flagged_urls = remaining
            count = len(remaining)
        else:
            verification_note = self._EXPORT_LAG_CAVEAT

        thin_count = 0
        if self.has_columns(["url", "word_count"]):
            word_counts = self.df.set_index("url")["word_count"].to_dict()
            thin_count = sum(
                1 for u in flagged_urls
                if word_counts.get(u, 0) and word_counts.get(u, 0) < 300
            )

        thin_note = (
            f" Of these, {thin_count} have under 300 words in the current crawl, "
            "consistent with a thin-content driven exclusion."
            if thin_count else ""
        )

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.INDEXABILITY,
            issue_type="gsc_crawled_not_indexed",
            title=f"{count} pages reported as 'Crawled - currently not indexed' in GSC",
            description=f"Google crawled {count} URLs but chose not to index them — this is "
                       f"a quality/value judgment, not a technical block.{thin_note} Common "
                       "drivers: thin or low-value content lacking a clear reason to index, "
                       "near-duplication that doesn't fit a formal duplicate category, weak "
                       "internal linking combined with weak external signals, or rendering "
                       f"issues that leave the page looking empty to Google.{verification_note}",
            affected_urls=flagged_urls,
            count=count,
            recommendation="For each page, ask 'what reason does Google have to index this?' "
                          "and provide one: improve depth, originality, and genuine end-user "
                          "value; merge or prune pages that don't clear that bar; strengthen "
                          "internal links from authoritative pages; verify the rendered HTML "
                          "actually contains the content (GSC URL Inspection → View Crawled "
                          "Page). Re-submitting for indexing without an on-page change will "
                          "not help — Google already crawled it once and passed.",
            impact="These pages are permanently invisible in search until the underlying "
                  "quality or rendering issue is fixed. No technical fix (redirects, "
                  "canonicals, robots.txt) resolves this status — only content and linking "
                  "changes do.",
        )

    def _check_discovered_not_indexed(self) -> None:
        """Surface pages GSC reports as 'Discovered - currently not indexed'.

        Google knows the URL exists but hasn't crawled it yet — usually a
        crawl-budget or perceived-low-value signal, distinct from the
        quality-judgment 'Crawled - currently not indexed' status.
        Cross-references internal_links_in from the crawl data, since weak
        internal linking is the most actionable, most common driver.
        """
        if self.discovered_not_indexed_df is None or len(self.discovered_not_indexed_df) == 0:
            return
        if "url" not in self.discovered_not_indexed_df.columns:
            return

        # Deduplicate before counting so the count is unique URLs, not raw
        # rows (project Rule 10 — GSC exports can repeat a URL across rows).
        flagged_urls = list(
            dict.fromkeys(self.discovered_not_indexed_df["url"].dropna().astype(str))
        )
        count = len(flagged_urls)
        if count == 0:
            return

        # Same stale-row filter as the crawled-not-indexed check: a fresh
        # URL Inspection verdict of indexed removes the row from the finding.
        split = self._partition_export_urls(flagged_urls)
        if split is not None:
            now_indexed, remaining, unverified = split
            if not remaining:
                self._create_stale_export_insight(
                    "Discovered - currently not indexed",
                    "gsc_discovered_not_indexed_stale",
                    flagged_urls,
                )
                return
            verification_note = self._verification_note(
                count, len(now_indexed), len(remaining), unverified
            )
            flagged_urls = remaining
            count = len(remaining)
        else:
            verification_note = self._EXPORT_LAG_CAVEAT

        weakly_linked_count = 0
        if self.has_columns(["url", "internal_links_in"]):
            inlinks = self.df.set_index("url")["internal_links_in"].to_dict()
            weakly_linked_count = sum(
                1 for u in flagged_urls if inlinks.get(u, 0) <= 2
            )

        linking_note = (
            f" Of these, {weakly_linked_count} have 2 or fewer internal links pointing to "
            "them in the current crawl, consistent with a weak-internal-linking driver."
            if weakly_linked_count else ""
        )

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.INDEXABILITY,
            issue_type="gsc_discovered_not_indexed",
            title=f"{count} pages reported as 'Discovered - currently not indexed' in GSC",
            description=f"Google knows {count} URLs exist but has not crawled them yet — no "
                       f"last-crawl date is recorded for this status.{linking_note} Common "
                       "drivers: crawl budget rationing on large sites, weak internal linking "
                       "burying the page many clicks from the homepage, mass URL generation "
                       "(faceted navigation, parameter explosion) diluting crawl budget, or "
                       "perceived low value based on similar pages Google has already "
                       f"seen.{verification_note}",
            affected_urls=flagged_urls,
            count=count,
            recommendation="Strengthen internal linking from high-authority, "
                          "frequently-crawled parent pages (homepage, hub pages, related "
                          "content). Audit for mass low-value URL generation competing for the "
                          "same crawl budget and prune or consolidate it. Ensure the URL is in "
                          "an accurate, well-maintained XML sitemap. For genuinely important "
                          "pages, request indexing in GSC as a hint — it doesn't force "
                          "indexing, only patience and stronger signals do.",
            impact="Undiscovered-by-crawl pages earn zero organic visibility. Unlike "
                  "'Crawled - currently not indexed', this status often resolves purely by "
                  "improving internal linking and reducing competing low-value URLs, without "
                  "any content rewrite.",
        )

    def _count_should_be_indexed(self) -> int:
        """Count crawl pages that should be indexed.

        The clean "should-be-indexed" set: HTML pages returning 200, marked
        indexable, with a self-referencing or absent canonical. This is the
        crawl-side number to reconcile against GSC's indexed total.
        """
        scope = self.get_html_pages()
        if "status_code" in scope.columns:
            scope = scope[
                (scope["status_code"] >= 200) & (scope["status_code"] < 300)
            ]
        if "indexability" in scope.columns:
            scope = scope[
                scope["indexability"].astype(str).str.lower() == "indexable"
            ]
        if "canonical" in scope.columns and "url" in scope.columns:
            canon = scope["canonical"]
            self_or_blank = canon.apply(is_empty_or_missing) | (canon == scope["url"])
            scope = scope[self_or_blank]
        return int(len(scope))

    def _check_index_coverage_reconciliation(self) -> None:
        """Reconcile the crawl's indexable-page count against GSC's indexed total.

        Foley Carter's index-health gauge (GSC Lesson 4): the count of clean,
        indexable HTTP-200 HTML pages found in the crawl should be close to the
        number of URLs GSC reports as indexed. A large divergence points to a
        real problem in one of two directions:
          - crawl >> GSC indexed  → under-indexation (orphaning, thin/low-value
            content, crawl-budget starvation) — pages that should rank aren't
            in the index.
          - GSC indexed >> crawl  → index bloat (parameter/faceted/variant or
            stale URLs) inflating the index beyond the real page set.

        Two modes:
          - Baseline (no ``gsc_indexed_count``): report the crawl-side
            should-be-indexed count plus the manual reconciliation step, so the
            gap can be checked by hand against GSC's Page Indexing report.
          - Reconciled (``gsc_indexed_count`` supplied): compute the gap and
            flag it when it exceeds ``INDEX_COVERAGE_GAP_PCT`` in either
            direction.
        """
        should_index = self._count_should_be_indexed()
        if should_index < INDEX_COVERAGE_MIN_PAGES:
            return

        if self.gsc_indexed_count is None:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.INDEXABILITY,
                issue_type="index_coverage_baseline",
                title=f"Crawl finds {should_index} clean indexable pages — "
                      "reconcile against GSC indexed count",
                description=f"The crawl contains {should_index} pages that should "
                           "be indexed (HTTP 200, indexable, self-referencing or "
                           "no canonical). This number should be close to the "
                           "total GSC reports under Indexing → Pages → 'Indexed'. "
                           "A large gap in either direction is a site-wide "
                           "index-health signal that per-page checks miss: many "
                           "more crawlable-indexable pages than GSC indexes points "
                           "to under-indexation (orphaning, thin content, crawl "
                           "budget); far more indexed URLs than the crawl's clean "
                           "set points to index bloat (parameter/variant/stale "
                           "URLs).",
                recommendation="Open GSC → Indexing → Pages, read the 'Indexed' "
                              f"total, and compare it to {should_index}. If GSC "
                              "indexes far fewer, investigate the not-indexed "
                              "reasons (Discovered/Crawled – currently not "
                              "indexed) and internal linking. If GSC indexes far "
                              "more, audit for parameter/faceted URL bloat. Supply "
                              "the indexed count to the auditor to compute the gap "
                              "automatically.",
                impact="Reconciling crawl vs indexed counts catches whole classes "
                      "of problem (mass orphaning, parameter bloat) that no "
                      "single-URL check surfaces, because each individual page "
                      "can look fine while the aggregate is badly off.",
                additional_data={"should_be_indexed": should_index},
            )
            return

        indexed = int(self.gsc_indexed_count)
        gap = should_index - indexed
        denom = should_index if should_index else 1
        under_pct = gap / denom
        over_pct = (indexed - should_index) / denom

        if under_pct >= INDEX_COVERAGE_GAP_PCT:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="index_coverage_under_indexation",
                title=f"Under-indexation: {should_index} indexable pages crawled, "
                      f"only {indexed} indexed by Google",
                description=f"The crawl found {should_index} clean indexable pages "
                           f"(200, indexable, self-canonical) but GSC reports only "
                           f"{indexed} indexed — a gap of {gap} pages "
                           f"({under_pct:.0%}). A gap this large means a "
                           "meaningful share of pages that should rank are not in "
                           "the index. Common drivers: mass orphaning (pages with "
                           "no internal links), thin/low-value content Google "
                           "declines to index, or crawl-budget starvation from "
                           "competing low-value URLs.",
                recommendation="Cross-reference the Discovered/Crawled – currently "
                              "not indexed reports (see gsc-indexation-states.md) "
                              "to split the gap into orphaning (fix internal "
                              "linking) vs quality (improve/prune content). "
                              "Strengthen internal links to important unindexed "
                              "pages and prune low-value URLs competing for crawl "
                              "budget, then request indexing on the priority set.",
                impact="Every page in the gap earns zero organic visibility. This "
                      "is usually the single largest recoverable-traffic finding "
                      "on a site, because the content already exists — it just "
                      "isn't in the index.",
                additional_data={
                    "should_be_indexed": should_index,
                    "gsc_indexed": indexed,
                    "gap": gap,
                },
            )
        elif over_pct >= INDEX_COVERAGE_GAP_PCT:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.INDEXABILITY,
                issue_type="index_coverage_bloat",
                title=f"Index bloat: Google indexes {indexed} URLs vs "
                      f"{should_index} clean indexable pages in the crawl",
                description=f"GSC reports {indexed} indexed URLs but the crawl "
                           f"found only {should_index} clean indexable pages — "
                           f"Google is indexing {indexed - should_index} more URLs "
                           f"({over_pct:.0%}) than the site's real page set. This "
                           "is the classic parameter/faceted/variant bloat "
                           "pattern: filter combinations, session/tracking "
                           "parameters, and stale URLs inflating the index.",
                recommendation="Audit for parameter and faceted-navigation URL "
                              "generation and apply the canonical-child "
                              "segmentation → value-gate → robots.txt workflow "
                              "(robots-txt-ecommerce-framework.md). Confirm "
                              "canonicals are self-referencing on real pages and "
                              "consolidate/prune stale URLs. Keep the XML sitemap "
                              "limited to the clean indexable set.",
                impact="Index bloat wastes crawl budget on worthless URLs and can "
                      "dilute site-wide quality signals, slowing how often the "
                      "pages that matter get recrawled.",
                additional_data={
                    "should_be_indexed": should_index,
                    "gsc_indexed": indexed,
                    "gap": gap,
                },
            )
        else:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.INDEXABILITY,
                issue_type="index_coverage_healthy",
                title=f"Index coverage healthy: {indexed} indexed vs "
                      f"{should_index} crawlable-indexable pages",
                description=f"GSC's indexed count ({indexed}) is within "
                           f"{INDEX_COVERAGE_GAP_PCT:.0%} of the crawl's clean "
                           f"indexable set ({should_index}). No site-wide "
                           "index-coverage gap is evident — the pages that should "
                           "be indexed largely are, without significant bloat.",
                recommendation="No action needed on index coverage. Continue to "
                              "monitor the Discovered/Crawled – currently not "
                              "indexed reports for individual pages.",
                impact="A tight crawl-vs-indexed match indicates healthy "
                      "crawlability and index hygiene at the site level.",
                additional_data={
                    "should_be_indexed": should_index,
                    "gsc_indexed": indexed,
                },
            )

    # =========================================================================
    # CANONICAL CHECKS
    # =========================================================================

    def _check_missing_canonical(self) -> None:
        """Check for missing canonical tags on indexable pages."""
        if not self.has_column("canonical"):
            return

        # Only check indexable HTML pages
        html_pages = self.get_html_pages()
        if self.has_column("indexability"):
            html_pages = html_pages[html_pages["indexability"].str.lower() == "indexable"]

        condition = html_pages["canonical"].apply(is_empty_or_missing)
        urls = html_pages.loc[condition, "url"].head(100).tolist() if "url" in html_pages.columns else []
        count = condition.sum()

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="missing_canonical",
                title=f"{count} indexable pages missing canonical tag",
                description=f"Found {count} indexable pages without a canonical link element. "
                           "This can lead to duplicate content issues.",
                affected_urls=urls,
                count=count,
                recommendation="Add self-referencing canonical tags to all indexable pages. "
                              "Use absolute URLs in canonical tags.",
                impact="Without canonicals, search engines may index duplicate or parameter URLs, "
                      "diluting ranking signals.",
            )

    def _check_canonical_mismatch(self) -> None:
        """Check for pages where canonical doesn't point to self."""
        if not self.has_columns(["url", "canonical"]):
            return

        # Pages where canonical != url (and canonical is not empty)
        has_canonical = ~self.df["canonical"].apply(is_empty_or_missing)
        canonical_mismatch = has_canonical & (self.df["canonical"] != self.df["url"])

        urls = self.filter_by_condition(canonical_mismatch)
        count = self.count_by_condition(canonical_mismatch)

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.INDEXABILITY,
                issue_type="canonical_mismatch",
                title=f"{count} pages with non-self-referencing canonical",
                description=f"Found {count} pages where the canonical URL differs from the page URL. "
                           "This may be intentional (duplicate handling) or an error.",
                affected_urls=urls,
                count=count,
                recommendation="Review each case. Intentional uses: pagination, parameter variations, "
                              "duplicate content consolidation. Fix if canonicals are pointing incorrectly.",
                impact="Non-self-referencing canonicals tell search engines to consolidate signals to another URL.",
            )

    def _check_canonical_chain(self) -> None:
        """Check for canonical chains (canonical points to another page with different canonical)."""
        if not self.has_columns(["url", "canonical"]):
            return

        # Build canonical target lookup
        canonical_targets = self.df.set_index("url")["canonical"].to_dict()

        chain_urls = []
        for _, row in self.df.iterrows():
            url = row.get("url", "")
            canonical = row.get("canonical", "")

            if is_empty_or_missing(canonical) or canonical == url:
                continue

            # Check if the canonical target has a different canonical
            if canonical in canonical_targets:
                target_canonical = canonical_targets[canonical]
                if not is_empty_or_missing(target_canonical) and target_canonical != canonical:
                    chain_urls.append(url)

        if chain_urls:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="canonical_chain",
                title=f"{len(chain_urls)} pages with canonical chains",
                description=f"Found {len(chain_urls)} pages where the canonical target has a different canonical. "
                           "This creates a chain that may confuse search engines.",
                affected_urls=chain_urls[:100],
                count=len(chain_urls),
                recommendation="Update canonicals to point directly to the final target URL. "
                              "Avoid intermediate hops in canonical chains.",
                impact="Canonical chains may not be followed completely, leading to incorrect canonicalization.",
            )

    def _check_canonical_to_redirect(self) -> None:
        """Check for canonicals pointing to redirect URLs."""
        if not self.has_columns(["canonical", "status_code"]):
            return

        # Build status code lookup
        url_status = self.df.set_index("url")["status_code"].to_dict() if "url" in self.df.columns else {}

        problem_urls = []
        for _, row in self.df.iterrows():
            canonical = row.get("canonical", "")
            if is_empty_or_missing(canonical):
                continue

            # Check if canonical target is a redirect
            target_status = url_status.get(canonical, 200)
            if 300 <= target_status < 400:
                problem_urls.append(row.get("url", ""))

        if problem_urls:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.INDEXABILITY,
                issue_type="canonical_to_redirect",
                title=f"{len(problem_urls)} pages with canonical pointing to redirect",
                description=f"Found {len(problem_urls)} pages where the canonical URL is a redirect (3XX). "
                           "Canonicals should point to the final destination.",
                affected_urls=problem_urls[:100],
                count=len(problem_urls),
                recommendation="Update canonicals to point to the final redirect destination URL.",
                impact="Canonical to redirect adds unnecessary hop and may not be processed correctly.",
            )

    def _check_canonical_to_4xx_5xx(self) -> None:
        """Check for canonicals pointing to error pages."""
        if not self.has_columns(["canonical", "status_code"]):
            return

        url_status = self.df.set_index("url")["status_code"].to_dict() if "url" in self.df.columns else {}

        problem_urls = []
        for _, row in self.df.iterrows():
            canonical = row.get("canonical", "")
            if is_empty_or_missing(canonical):
                continue

            target_status = url_status.get(canonical, 200)
            if target_status >= 400:
                problem_urls.append(row.get("url", ""))

        if problem_urls:
            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.INDEXABILITY,
                issue_type="canonical_to_error",
                title=f"{len(problem_urls)} pages with canonical pointing to error page",
                description=f"Found {len(problem_urls)} pages where the canonical URL returns 4XX/5XX error. "
                           "This is a serious canonicalization issue.",
                affected_urls=problem_urls[:100],
                count=len(problem_urls),
                recommendation="Update canonicals to point to valid, working URLs. "
                              "If the original content is gone, consider removing these pages or redirecting.",
                impact="Canonical to error page creates a dead end for link equity and indexation signals.",
            )

    def _check_declared_vs_selected_canonical(self) -> None:
        """Flag pages where Google chose a canonical different from the declared one.

        Requires GSC URL Inspection data in the crawl: the
        `Google-Selected Canonical` column (mapped to ``google_canonical``).
        The declared canonical is read from `User-Declared Canonical`
        (``user_canonical``) when present, otherwise from the on-page
        `Canonical Link Element 1` (``canonical``). When Google selects a
        different URL than the one declared, it is ignoring the site's
        canonical hint — usually a duplication/consolidation signal worth
        investigating. No-ops entirely when URL Inspection data is absent.
        """
        if not self.has_column("google_canonical"):
            return

        declared_col = (
            "user_canonical" if self.has_column("user_canonical")
            else "canonical" if self.has_column("canonical")
            else None
        )
        if declared_col is None:
            return

        google = self.df["google_canonical"].astype(str).str.strip()
        declared = self.df[declared_col].astype(str).str.strip()

        def _blank(series: pd.Series) -> pd.Series:
            return series.apply(is_empty_or_missing)

        # Both sides present and non-blank, and they disagree.
        condition = (
            ~_blank(google)
            & ~_blank(declared)
            & (google != declared)
        )
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="declared_vs_selected_canonical_divergence",
                title=f"{count} pages where Google ignores the declared canonical",
                description=f"Found {count} pages where the Google-Selected Canonical "
                           "(from GSC URL Inspection) differs from the canonical the "
                           "page declares. Google treats the declared canonical as a "
                           "hint, not a directive — when it picks a different URL, it "
                           "has judged another page to be the better representative "
                           "(often due to duplicate/near-duplicate content, an "
                           "internal-linking imbalance, or conflicting signals such as "
                           "sitemaps or redirects pointing elsewhere).",
                affected_urls=urls,
                count=count,
                recommendation="For each page, compare the declared vs Google-selected "
                              "URL in GSC URL Inspection. If the declared canonical is "
                              "correct, strengthen the signals that support it: ensure "
                              "internal links, the sitemap, and any redirects all point "
                              "to the declared URL, and differentiate the content from "
                              "the page Google prefers. If Google's choice is actually "
                              "the better URL, update the declared canonical to match it.",
                impact="When Google overrides the declared canonical, ranking signals "
                      "consolidate to a page the site owner did not choose, and the "
                      "declared page may be dropped from the index — a silent loss of "
                      "control over which URL represents the content.",
            )

    # =========================================================================
    # REDIRECT CHECKS
    # =========================================================================

    def _check_redirect_chains(self) -> None:
        """Check for redirect chains (3+ hops)."""
        if not self.has_column("redirect_count"):
            return

        # 3+ redirects is a chain
        condition = self.df["redirect_count"] >= 3
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            # Get max chain length
            max_chain = int(self.df["redirect_count"].max())

            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.REDIRECTS,
                issue_type="redirect_chains",
                title=f"{count} redirect chains (3+ hops)",
                description=f"Found {count} URLs with 3 or more redirects. Maximum chain length: {max_chain}. "
                           "Long chains waste crawl budget and lose link equity.",
                affected_urls=urls,
                count=count,
                recommendation="Update redirects to point directly to the final destination. "
                              "Each redirect hop can lose ~10-15% of link equity.",
                impact="Redirect chains slow down users and crawlers, waste crawl budget, "
                      "and progressively lose PageRank with each hop.",
                additional_data={"max_chain_length": max_chain},
            )

    def _check_redirect_loops(self) -> None:
        """Check for redirect loops."""
        if not self.has_columns(["url", "redirect_url"]):
            return

        # Simple loop detection: URL redirects to itself
        self_redirects = self.df["url"] == self.df["redirect_url"]
        urls = self.filter_by_condition(self_redirects)
        count = self.count_by_condition(self_redirects)

        if count > 0:
            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.REDIRECTS,
                issue_type="redirect_loops",
                title=f"{count} redirect loops detected",
                description=f"Found {count} URLs that redirect to themselves, creating infinite loops.",
                affected_urls=urls,
                count=count,
                recommendation="Fix the redirect rules to point to the correct destination. "
                              "Check server configuration and .htaccess rules.",
                impact="Redirect loops make pages completely inaccessible to users and search engines.",
            )

    def _check_http_to_https(self) -> None:
        """Check for HTTP to HTTPS redirect issues."""
        if not self.has_columns(["url", "redirect_url"]):
            return

        # HTTP pages that redirect to HTTPS
        http_pages = self.df["url"].str.startswith("http://", na=False)
        has_redirect = ~self.df["redirect_url"].apply(is_empty_or_missing)
        https_redirect = self.df["redirect_url"].str.startswith("https://", na=False)

        # HTTP pages not redirecting to HTTPS
        http_no_redirect = http_pages & ~has_redirect
        urls = self.filter_by_condition(http_no_redirect)
        count = self.count_by_condition(http_no_redirect)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.SECURITY,
                issue_type="http_no_redirect",
                title=f"{count} HTTP pages not redirecting to HTTPS",
                description=f"Found {count} HTTP URLs that are accessible without redirecting to HTTPS.",
                affected_urls=urls,
                count=count,
                recommendation="Implement 301 redirects from all HTTP URLs to their HTTPS equivalents. "
                              "Configure server to force HTTPS.",
                impact="HTTP pages are marked as 'Not Secure' by browsers and may rank lower. "
                      "Also causes duplicate content issues if both versions are accessible.",
            )

    # =========================================================================
    # CORE WEB VITALS CHECKS
    # =========================================================================

    def _check_poor_lcp(self) -> None:
        """Check for poor LCP (Largest Contentful Paint)."""
        if not self.has_column("lcp"):
            return

        # LCP > 4.0s is poor
        condition = self.df["lcp"] > 4.0
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            avg_lcp = self.df.loc[condition, "lcp"].mean()

            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.PERFORMANCE,
                issue_type="poor_lcp",
                title=f"{count} pages with poor LCP (>4.0s)",
                description=f"Found {count} pages with LCP greater than 4 seconds (poor). "
                           f"Average LCP of affected pages: {avg_lcp:.2f}s. "
                           "Good LCP is ≤2.5s, needs improvement is 2.5-4.0s.",
                affected_urls=urls,
                count=count,
                recommendation="Optimize LCP by: 1) Reducing server response time (TTFB), "
                              "2) Eliminating render-blocking resources, 3) Preloading LCP images, "
                              "4) Using efficient image formats (WebP, AVIF).",
                impact="Poor LCP degrades user experience and is a Google ranking factor. "
                      "Users may abandon pages that load slowly.",
                additional_data={"avg_lcp": round(avg_lcp, 2)},
            )

        # Also check needs improvement (2.5-4.0s)
        needs_improvement = (self.df["lcp"] > 2.5) & (self.df["lcp"] <= 4.0)
        ni_count = self.count_by_condition(needs_improvement)

        if ni_count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.PERFORMANCE,
                issue_type="lcp_needs_improvement",
                title=f"{ni_count} pages with LCP needing improvement (2.5-4.0s)",
                description=f"Found {ni_count} pages with LCP between 2.5 and 4.0 seconds. "
                           "These pages would benefit from optimization.",
                affected_urls=self.filter_by_condition(needs_improvement),
                count=ni_count,
                recommendation="Target LCP under 2.5 seconds for good user experience.",
                impact="LCP in this range may impact rankings and user engagement.",
            )

    def _check_poor_cls(self) -> None:
        """Check for poor CLS (Cumulative Layout Shift)."""
        if not self.has_column("cls"):
            return

        # CLS > 0.25 is poor
        condition = self.df["cls"] > 0.25
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            avg_cls = self.df.loc[condition, "cls"].mean()

            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.PERFORMANCE,
                issue_type="poor_cls",
                title=f"{count} pages with poor CLS (>0.25)",
                description=f"Found {count} pages with CLS greater than 0.25 (poor). "
                           f"Average CLS: {avg_cls:.3f}. Good CLS is ≤0.1.",
                affected_urls=urls,
                count=count,
                recommendation="Fix CLS by: 1) Setting explicit width/height on images and videos, "
                              "2) Reserving space for ads and embeds, 3) Using font-display: swap "
                              "with similar fallback fonts, 4) Avoiding inserting content above existing content.",
                impact="Poor CLS creates frustrating visual instability where elements shift as the page loads.",
                additional_data={"avg_cls": round(avg_cls, 3)},
            )

    def _check_poor_tbt(self) -> None:
        """Check for poor TBT (Total Blocking Time)."""
        if not self.has_column("tbt"):
            return

        # TBT > 600ms is poor (correlates with INP)
        condition = self.df["tbt"] > 600
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            avg_tbt = self.df.loc[condition, "tbt"].mean()

            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.PERFORMANCE,
                issue_type="poor_tbt",
                title=f"{count} pages with poor TBT (>600ms)",
                description=f"Found {count} pages with Total Blocking Time greater than 600ms. "
                           f"Average TBT: {avg_tbt:.0f}ms. High TBT correlates with poor interactivity.",
                affected_urls=urls,
                count=count,
                recommendation="Reduce TBT by: 1) Breaking up long JavaScript tasks, "
                              "2) Removing unused JavaScript, 3) Deferring non-critical JS, "
                              "4) Reducing DOM size and complexity.",
                impact="High TBT means the main thread is blocked, making pages feel unresponsive to user input.",
                additional_data={"avg_tbt_ms": round(avg_tbt, 0)},
            )

    def _check_low_performance_score(self) -> None:
        """Check for low overall performance scores."""
        if not self.has_column("performance_score"):
            return

        # Score < 50 is poor
        condition = self.df["performance_score"] < 50
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            avg_score = self.df.loc[condition, "performance_score"].mean()

            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.PERFORMANCE,
                issue_type="low_performance_score",
                title=f"{count} pages with low performance score (<50)",
                description=f"Found {count} pages with Lighthouse performance score below 50. "
                           f"Average score: {avg_score:.0f}. Target score is 90+.",
                affected_urls=urls,
                count=count,
                recommendation="Review individual Lighthouse reports to identify specific optimizations. "
                              "Focus on the largest opportunities first.",
                impact="Low performance scores indicate significant loading and interactivity issues.",
                additional_data={"avg_score": round(avg_score, 0)},
            )

    # =========================================================================
    # SECURITY CHECKS
    # =========================================================================

    def _check_http_pages(self) -> None:
        """Check for non-HTTPS pages."""
        if not self.has_column("url"):
            return

        condition = self.df["url"].str.startswith("http://", na=False)
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.SECURITY,
                issue_type="http_pages",
                title=f"{count} pages served over HTTP",
                description=f"Found {count} pages using HTTP instead of HTTPS. "
                           "Browsers mark these as 'Not Secure'.",
                affected_urls=urls,
                count=count,
                recommendation="Migrate all pages to HTTPS. Obtain SSL certificate, "
                              "update internal links, and implement 301 redirects from HTTP to HTTPS.",
                impact="HTTP pages are insecure, marked by browsers, and may rank lower in search results.",
            )

    def _check_mixed_content(self) -> None:
        """Check for mixed content issues (HTTPS pages with HTTP resources).

        Note: This check requires external resource data which may not be in standard SF exports.
        """
        # This would require additional data about page resources
        # Placeholder for when resource data is available
        pass

    # =========================================================================
    # RESPONSE TIME CHECKS
    # =========================================================================

    def _check_slow_pages(self) -> None:
        """Check for slow response times (TTFB)."""
        if not self.has_column("response_time"):
            return

        # Response time > 1000ms is slow
        condition = self.df["response_time"] > 1000
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            avg_time = self.df.loc[condition, "response_time"].mean()

            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.PERFORMANCE,
                issue_type="slow_response_time",
                title=f"{count} pages with slow response time (>1s)",
                description=f"Found {count} pages with server response time over 1 second. "
                           f"Average response time: {avg_time:.0f}ms. Target is <500ms.",
                affected_urls=urls,
                count=count,
                recommendation="Improve server response time by: 1) Implementing caching, "
                              "2) Optimizing database queries, 3) Using a CDN, "
                              "4) Upgrading server resources.",
                impact="Slow TTFB directly impacts LCP and overall page load speed.",
                additional_data={"avg_response_time_ms": round(avg_time, 0)},
            )

    # =========================================================================
    # NOINDEX PLACEMENT CHECK
    # =========================================================================

    def _check_noindex_in_body(self) -> None:
        """Check for noindex declarations placed in body instead of head.

        Google ignores noindex meta tags placed outside the <head>. Pages
        intending to be noindexed but with the directive in the body will
        still be indexed.

        DATA-GATED: meta-robots placement (head vs body) is NOT a native
        Screaming Frog column. It only exists when the crawl includes a
        custom extraction that captures where the meta robots tag sits in
        the document (an XPath/regex extractor the auditor names e.g. "Meta
        Robots Position"). ``utils.file_parser`` maps those custom-extraction
        headers to ``meta_robots_position`` / ``meta_robots_location`` /
        ``robots_position``. When that extraction wasn't part of the crawl,
        this check intentionally no-ops — it is data-gated, not broken.
        """
        # SF column variants for the placement marker (see docstring — these
        # come from a named custom extraction, mapped in file_parser).
        position_col = None
        for candidate in ("meta_robots_position", "robots_position",
                          "meta_robots_location"):
            if self.has_column(candidate):
                position_col = candidate
                break
        if position_col is None or not self.has_column("meta_robots"):
            return

        # Cast to string before .str accessors — an all-blank column read as
        # float would raise AttributeError and abort the audit.
        has_noindex = self.df["meta_robots"].astype(str).str.contains(
            "noindex", case=False, na=False
        )
        in_body = self.df[position_col].astype(str).str.lower().str.contains(
            "body", na=False
        )
        condition = has_noindex & in_body

        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="noindex_in_body",
                title=f"{count} pages with noindex in body (will be ignored)",
                description=f"Found {count} pages where the noindex meta tag "
                           "is placed in the page body rather than the "
                           "<head>. Google only honors noindex directives "
                           "in the <head>; body placement is silently "
                           "ignored. The intent to deindex these pages "
                           "is therefore not being respected.",
                affected_urls=urls,
                count=count,
                recommendation="Move the noindex meta tag into the <head> "
                              "section of the page template. If the "
                              "directive is being injected by a plugin or "
                              "JavaScript, switch to an X-Robots-Tag HTTP "
                              "header instead — header-based directives "
                              "are evaluated server-side and don't depend "
                              "on placement in HTML.",
                impact="The noindex intent is ignored. If these pages "
                      "should be deindexed, they remain in Google's index. "
                      "If they shouldn't be deindexed, remove the noindex "
                      "tag entirely instead of leaving it in the body.",
            )

    # =========================================================================
    # LINK HEALTH CHECKS
    # =========================================================================

    def _check_internal_links_to_redirects(self) -> None:
        """Flag internal links pointing to URLs that 301-redirect.

        Each redirect hop loses link equity. The fix is to update the
        source link to point directly to the final destination — not to
        rely on the redirect to carry the user there.

        Redirects are derived from ``status_code`` (3xx) and the inlink count
        from ``internal_links_in`` — the ``redirect_url`` column is not
        needed, so it is deliberately absent from the guard below (requiring
        it would make this check needlessly no-op on exports that carry
        status + inlinks but not the redirect-target column).
        """
        if not self.has_columns(["url", "status_code", "internal_links_in"]):
            return

        # Build set of URLs that are redirect sources
        redirect_sources = set(
            self.df.loc[
                (self.df["status_code"] >= 300)
                & (self.df["status_code"] < 400),
                "url",
            ].dropna().tolist()
        )
        if not redirect_sources:
            return

        condition = (
            self.df["url"].isin(redirect_sources)
            & (self.df["internal_links_in"] > 0)
        )
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            total_inlinks = int(
                self.df.loc[condition, "internal_links_in"].sum()
            )
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.REDIRECTS,
                issue_type="internal_links_to_redirects",
                title=f"{count} redirecting URLs receive internal links",
                description=f"Found {count} URLs that 301-redirect but "
                           f"are still being linked to internally "
                           f"(total of {total_inlinks} internal links "
                           "pointing through redirects). Each redirect "
                           "hop loses link equity. The links should point "
                           "directly to the final destination.",
                affected_urls=urls,
                count=count,
                recommendation="Update internal links to point directly "
                              "to the redirect destination URLs. Don't "
                              "rely on the redirect to carry users — "
                              "fix the source links. The redirect itself "
                              "can stay in place to handle external "
                              "traffic, but internal navigation should "
                              "always use current URLs.",
                impact="Internal redirects waste crawl budget and slowly "
                      "leak PageRank with each hop. Sites with hundreds "
                      "of internal-to-redirect links lose meaningful "
                      "equity flow to important pages.",
                additional_data={"total_inlinks_through_redirects": total_inlinks},
            )

    def _check_links_on_noindex_pages(self) -> None:
        """Flag noindex pages that link out to indexable pages.

        Links from noindex pages eventually get treated as nofollow by
        Google. This means any internal link equity flowing from these
        pages to other pages is leaked — the destination pages don't
        receive the signal they would from a regular indexable page.
        """
        if not self.has_column("meta_robots"):
            return
        if not self.has_column("internal_links_out"):
            return

        # Cast to string first — an all-blank meta_robots column read as
        # float would raise AttributeError on the .str accessor.
        has_noindex = self.df["meta_robots"].astype(str).str.contains(
            "noindex", case=False, na=False
        )
        has_outlinks = self.df["internal_links_out"] > 0
        condition = has_noindex & has_outlinks

        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            total_leaked = int(
                self.df.loc[condition, "internal_links_out"].sum()
            )
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.INDEXABILITY,
                issue_type="links_on_noindex_pages",
                title=f"{count} noindex pages still linking to other pages",
                description=f"Found {count} noindex pages that contain "
                           f"internal links to other pages on the site "
                           f"({total_leaked} total outbound internal "
                           "links). Google eventually treats links from "
                           "noindex pages as nofollow, so any link equity "
                           "intended to flow through these pages is "
                           "leaked rather than passed.",
                affected_urls=urls,
                count=count,
                recommendation="Either (a) remove the noindex from these "
                              "pages if they should be indexed and pass "
                              "equity, or (b) accept the equity loss and "
                              "make sure the destinations they link to "
                              "are also reached from indexable pages "
                              "elsewhere on the site. Don't rely on "
                              "noindex pages as the only source of "
                              "internal links to important content.",
                impact="Internal link equity that should be flowing to "
                      "destination pages is being lost. If important "
                      "pages are only linked from noindex pages, they "
                      "are effectively orphaned for ranking purposes.",
                additional_data={"total_leaked_links": total_leaked},
            )

    # =========================================================================
    # URL HYGIENE CHECKS
    # =========================================================================

    def _check_trailing_slash_inconsistency(self) -> None:
        """Detect mixed trailing-slash conventions across the site.

        When the same site uses both `/page` and `/page/` for different
        URLs, search engines may treat them as duplicates. The fix is
        to pick one convention and 301-redirect the other.
        """
        if not self.has_column("url"):
            return

        # Restrict to indexable HTML pages — assets and redirects don't
        # count toward this issue
        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if "url" not in scope.columns:
            return

        urls = scope["url"].dropna().astype(str).tolist()
        if len(urls) < 10:
            # Need a meaningful sample to detect a pattern
            return

        # Strip query strings and fragments before counting
        def _path(u: str) -> str:
            return u.split("?")[0].split("#")[0]

        paths = [_path(u) for u in urls]
        # Exclude root (always trailing slash) and asset-like URLs
        paths = [p for p in paths if p and p != "/" and "." not in p.split("/")[-1]]

        with_slash = sum(1 for p in paths if p.endswith("/"))
        without_slash = sum(1 for p in paths if not p.endswith("/"))
        total = with_slash + without_slash
        if total == 0:
            return

        minority = min(with_slash, without_slash)
        majority = max(with_slash, without_slash)
        minority_pct = minority / total * 100

        # Only flag if the minority is meaningful (>5% of URLs and >5 URLs)
        # — otherwise it's likely a small handful of intentional exceptions
        if minority < 5 or minority_pct < 5:
            return

        majority_convention = (
            "trailing slash" if with_slash > without_slash else "no trailing slash"
        )
        minority_convention = (
            "trailing slash" if with_slash < without_slash else "no trailing slash"
        )

        # Sample minority URLs as affected
        sample = []
        for u in urls:
            p = _path(u)
            if p == "/" or "." in p.split("/")[-1]:
                continue
            ends_with = p.endswith("/")
            if (with_slash > without_slash and not ends_with) or \
               (with_slash < without_slash and ends_with):
                sample.append(u)
                if len(sample) >= 100:
                    break

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.INDEXABILITY,
            issue_type="trailing_slash_inconsistency",
            title=f"Trailing slash inconsistency across {total} URLs",
            description=f"The site uses both trailing-slash and "
                       f"no-trailing-slash conventions across "
                       f"indexable pages. Majority convention: "
                       f"{majority_convention} ({majority} URLs, "
                       f"{majority/total*100:.0f}%). Minority "
                       f"convention: {minority_convention} ({minority} "
                       f"URLs, {minority_pct:.0f}%). When both "
                       "conventions resolve as 200, search engines may "
                       "treat them as separate URLs and split ranking "
                       "signals.",
            affected_urls=sample,
            count=minority,
            recommendation=f"Pick one convention ({majority_convention} "
                          "is already dominant) and 301-redirect the "
                          "minority URLs to their canonical form. Update "
                          "internal links and the sitemap to use the "
                          "chosen convention consistently. Configure the "
                          "server (or framework) to enforce the chosen "
                          "convention for all future URLs.",
            impact="Mixed trailing-slash conventions create duplicate "
                  "content risk and split ranking signals between "
                  "variants. Fixing this consolidates equity and removes "
                  "an avoidable source of crawl waste.",
            additional_data={
                "majority_convention": majority_convention,
                "majority_count": majority,
                "minority_count": minority,
            },
        )

    def _check_mixed_case_urls(self) -> None:
        """Detect URLs containing uppercase characters in the path.

        URLs are case-sensitive on the server. Mixed-case URLs create
        risk of duplicate-content variants if both `/Page` and `/page`
        resolve to 200, and they're inconsistent for users typing URLs
        directly.
        """
        if not self.has_column("url"):
            return

        # Restrict to indexable HTML pages — assets in /wp-content/ etc.
        # often have legitimate mixed-case names that aren't a problem
        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if "url" not in scope.columns:
            return

        def _has_upper_in_path(u: str) -> bool:
            if not isinstance(u, str):
                return False
            try:
                # Strip protocol + domain, look only at path
                from urllib.parse import urlparse
                path = urlparse(u).path
                return any(c.isupper() for c in path)
            except Exception:
                return False

        condition = scope["url"].apply(_has_upper_in_path)
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.INDEXABILITY,
                issue_type="mixed_case_urls",
                title=f"{count} URLs contain uppercase characters",
                description=f"Found {count} indexable URLs with uppercase "
                           "characters in the path. URLs are case-"
                           "sensitive — `/Page` and `/page` are different "
                           "URLs to the server. If both variants resolve, "
                           "they create duplicate content. Even when only "
                           "one variant resolves, the inconsistency is a "
                           "minor signal of poor URL hygiene and makes "
                           "manual URL entry less reliable for users.",
                affected_urls=urls,
                count=count,
                recommendation="Standardize on lowercase URLs. Implement "
                              "a server-level rewrite that 301-redirects "
                              "any uppercase URL request to its lowercase "
                              "equivalent. Update internal links to use "
                              "the lowercase form. For pages that already "
                              "have backlinks under mixed-case URLs, "
                              "preserve the redirect indefinitely.",
                impact="Mixed-case URLs create duplicate content risk and "
                      "represent inconsistent URL conventions across the "
                      "site. Fixing them is low-effort and removes a "
                      "small but real source of confusion for crawlers "
                      "and users.",
            )

    # =========================================================================
    # PAGE EXPERIENCE CHECKS (clutter / third-party proxies)
    # =========================================================================
    #
    # Honesty note: Screaming Frog crawl data cannot detect true intrusive
    # interstitials, cookie-wall overlays, or on-screen ad density / layout —
    # those require rendered-viewport inspection (a real browser) or a
    # human/LLM judgment call and remain a checklist item outside this auditor.
    # The two checks below implement only genuinely-detectable *proxies* for
    # page-experience clutter from the columns SF actually exports.

    def _check_third_party_script_density(self) -> None:
        """Flag pages loading an unusually high number of external JS resources.

        Uses `Unique External JS Outlinks` (mapped to ``external_js_outlinks``).
        Ad networks, trackers, chat widgets, tag managers and consent platforms
        all load as external JavaScript, so a page referencing many unique
        external scripts is a reasonable *proxy* for third-party clutter — not a
        direct measurement of ad density. No-ops when the column is absent.
        """
        if not self.has_column("external_js_outlinks"):
            return

        scope = self.get_html_pages()
        if "external_js_outlinks" not in scope.columns:
            return

        js_counts = pd.to_numeric(
            scope["external_js_outlinks"], errors="coerce"
        )
        condition = js_counts > THIRD_PARTY_SCRIPT_THRESHOLD
        # filter_by_condition operates on self.df, so reindex the condition to
        # the full frame (rows outside `scope` are simply False/NaN -> False).
        full_condition = condition.reindex(self.df.index, fill_value=False)
        urls = self.filter_by_condition(full_condition)
        count = int(full_condition.sum())

        if count > 0:
            max_scripts = int(js_counts[condition].max())
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.PAGE_EXPERIENCE,
                issue_type="third_party_script_density",
                title=f"{count} pages load {THIRD_PARTY_SCRIPT_THRESHOLD}+ "
                      "external JavaScript resources",
                description=f"Found {count} pages referencing more than "
                           f"{THIRD_PARTY_SCRIPT_THRESHOLD} unique external "
                           f"JavaScript resources (max on a single page: "
                           f"{max_scripts}). Ad networks, tag managers, "
                           "trackers, chat widgets and consent platforms all "
                           "load as external scripts, so a high count is a "
                           "proxy for third-party clutter that can degrade "
                           "interactivity (INP/TBT) and add cookie/consent "
                           "overhead. This is a signal to review, not a "
                           "confirmed problem — some external scripts are "
                           "legitimate and necessary.",
                affected_urls=urls,
                count=count,
                recommendation="Audit the external scripts on these pages "
                              "(DevTools → Network → JS, or a tag-governance "
                              "review of Google Tag Manager). Remove or "
                              "consolidate redundant tags, defer non-critical "
                              "third-party scripts, and confirm each script "
                              "still serves a purpose. Prioritize pages where "
                              "the count is far above the site norm.",
                impact="Excessive third-party JavaScript is a leading cause of "
                      "poor interactivity (high TBT/INP) and slower loads, "
                      "both of which feed Google's page-experience signals and "
                      "hurt real-user experience.",
                additional_data={"max_external_scripts": max_scripts},
            )

    def _check_response_size_to_content_ratio(self) -> None:
        """Flag large HTML documents that carry little readable content.

        Uses `Size (Bytes)` (``size_bytes``) and `Word Count` (``word_count``).
        A large HTML payload with few words means the document is dominated by
        markup rather than content — a *proxy* for template/ad-container bloat,
        heavy inline data, or a JS-shell page. No-ops when either column is
        absent. Restricted to 200-status HTML pages to avoid flagging assets
        and error pages.
        """
        if not self.has_columns(["size_bytes", "word_count"]):
            return

        scope = self.get_html_pages()
        if not {"size_bytes", "word_count"}.issubset(scope.columns):
            return

        size = pd.to_numeric(scope["size_bytes"], errors="coerce")
        words = pd.to_numeric(scope["word_count"], errors="coerce")

        if "status_code" in scope.columns:
            status_ok = scope["status_code"] == 200
        else:
            status_ok = pd.Series(True, index=scope.index)

        # bytes-per-word, guarding division by zero (0 words -> treat as 1).
        bytes_per_word = size / words.clip(lower=1)
        condition = (
            status_ok
            & size.notna()
            & words.notna()
            & (size > LARGE_HTML_BYTES)
            & (bytes_per_word > HIGH_BYTES_PER_WORD)
        )
        full_condition = condition.reindex(self.df.index, fill_value=False)
        urls = self.filter_by_condition(full_condition)
        count = int(full_condition.sum())

        if count > 0:
            worst_ratio = int(bytes_per_word[condition].max())
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.PAGE_EXPERIENCE,
                issue_type="response_size_to_content_ratio",
                title=f"{count} large HTML pages are markup-heavy for their content",
                description=f"Found {count} pages whose HTML document exceeds "
                           f"{LARGE_HTML_BYTES:,} bytes while carrying little "
                           "readable text (over "
                           f"{HIGH_BYTES_PER_WORD:,} bytes of HTML per word; "
                           f"worst case: {worst_ratio:,} bytes/word). A heavy "
                           "document with sparse content usually indicates "
                           "bloated markup — nested ad/containers, large inline "
                           "JSON/data blobs, or a JavaScript shell that renders "
                           "content client-side. This is a *proxy* for clutter "
                           "and warrants a look, not an automatic defect.",
                affected_urls=urls,
                count=count,
                recommendation="Inspect the raw HTML of these pages. If the "
                              "bulk is inline data or duplicated template "
                              "markup, trim or externalize it. If content is "
                              "rendered client-side, confirm Google can render "
                              "it (GSC URL Inspection → View Crawled Page). "
                              "Reducing document weight improves load time and "
                              "lowers parse/style cost on the main thread.",
                impact="Oversized HTML slows first paint and inflates "
                      "parse/render work, weakening page-experience signals. "
                      "When the weight hides client-rendered content, it can "
                      "also risk under-indexing if rendering fails.",
                additional_data={"worst_bytes_per_word": worst_ratio},
            )

    # =========================================================================
    # INTERNATIONAL / HREFLANG CHECKS
    # =========================================================================

    def _hreflang_url_columns(self) -> list[str]:
        """Return present internal hreflang alternate-URL columns, in order."""
        cols = [c for c in self.df.columns if _HREFLANG_URL_COL_RE.match(c)]
        return sorted(cols, key=lambda c: int(c.split("_")[1]))

    def _hreflang_lang_columns(self) -> list[str]:
        """Return present internal hreflang language-code columns, in order."""
        cols = [c for c in self.df.columns if _HREFLANG_LANG_COL_RE.match(c)]
        return sorted(cols, key=lambda c: int(c.split("_")[1]))

    def _hreflang_targets_by_url(self, url_cols: list[str]) -> dict[str, set[str]]:
        """Build {page_url: set(declared alternate URLs)} from the crawl.

        Only rows with a usable ``url`` value are included. Blank/NaN
        annotation cells are ignored. A page with no annotations maps to an
        empty set (so it still counts as "crawled" for reciprocity lookups).
        """
        targets: dict[str, set[str]] = {}
        for _, row in self.df.iterrows():
            page = row.get("url", "")
            if is_empty_or_missing(page):
                continue
            page = str(page).strip()
            alts: set[str] = set()
            for col in url_cols:
                value = row.get(col, "")
                if not is_empty_or_missing(value):
                    alts.add(str(value).strip())
            targets[page] = alts
        return targets

    def _check_hreflang_return_tags(self) -> None:
        """Flag hreflang annotations missing a reciprocal return tag.

        hreflang is bidirectional: if page A declares B as an alternate, B must
        declare A in return, or Google ignores the entire cluster. Reciprocity
        can only be verified for pages that are BOTH in this crawl — annotations
        pointing to URLs outside the crawl (other domains, uncrawled pages) are
        skipped rather than guessed. No-ops when no hreflang columns exist.
        """
        if not self.has_column("url"):
            return
        url_cols = self._hreflang_url_columns()
        if not url_cols:
            return

        targets_by_url = self._hreflang_targets_by_url(url_cols)
        if not targets_by_url:
            return

        broken_sources: list[str] = []
        for source, alts in targets_by_url.items():
            if not alts:
                continue  # page declares no hreflang — not a source cluster
            for target in alts:
                if target == source:
                    continue  # self-reference is fine, not a return tag
                if target not in targets_by_url:
                    continue  # target not in crawl — cannot verify, skip
                if source not in targets_by_url[target]:
                    broken_sources.append(source)
                    break  # one broken return tag is enough to flag the page

        count = len(broken_sources)
        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INTERNATIONAL,
                issue_type="hreflang_missing_return_tag",
                title=f"{count} pages have hreflang annotations without a return tag",
                description=f"Found {count} pages that declare an hreflang "
                           "alternate which does not point back at them. "
                           "hreflang must be reciprocal: if page A lists page B "
                           "as an alternate, B must list A in return. When the "
                           "return tag is missing, Google discards the whole "
                           "annotation and may serve the wrong language/region "
                           "version. Only alternates that are also in this crawl "
                           "were checked — annotations to URLs outside the crawl "
                           "were not verified.",
                affected_urls=broken_sources[:100],
                count=count,
                recommendation="For each flagged page, open the alternate URLs "
                              "it declares and confirm each one includes a "
                              "matching hreflang annotation pointing back (same "
                              "URL, correct language/region code). Fix the "
                              "template or plugin generating the annotations so "
                              "every locale in the cluster lists every other "
                              "locale, including a self-reference.",
                impact="Non-reciprocal hreflang is ignored by Google, so the "
                      "intended language/region targeting silently fails and "
                      "users can be served the wrong regional page — eroding "
                      "the value of maintaining localized content at all.",
            )

    def _check_hreflang_missing_x_default(self) -> None:
        """Flag hreflang clusters that declare no x-default annotation.

        Requires language-code columns to be present in the export (SF does not
        always store them). x-default tells Google which page to serve users
        whose language/region matches none of the declared locales; omitting it
        is a common, genuinely-detectable gap. No-ops when language columns are
        absent (URL-only exports cannot support this check).
        """
        if not self.has_column("url"):
            return
        lang_cols = self._hreflang_lang_columns()
        url_cols = self._hreflang_url_columns()
        # Language codes are required to detect x-default; a page must also
        # actually participate in an hreflang cluster (declare alternates).
        if not lang_cols or not url_cols:
            return

        missing_x_default: list[str] = []
        for _, row in self.df.iterrows():
            page = row.get("url", "")
            if is_empty_or_missing(page):
                continue

            has_annotation = any(
                not is_empty_or_missing(row.get(c, "")) for c in url_cols
            )
            if not has_annotation:
                continue

            langs = {
                str(row.get(c, "")).strip().lower()
                for c in lang_cols
                if not is_empty_or_missing(row.get(c, ""))
            }
            if X_DEFAULT_LANG not in langs:
                missing_x_default.append(str(page).strip())

        count = len(missing_x_default)
        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.INTERNATIONAL,
                issue_type="hreflang_missing_x_default",
                title=f"{count} pages with hreflang but no x-default",
                description=f"Found {count} pages that declare hreflang "
                           "alternates but include no x-default annotation. The "
                           "x-default value tells Google which page to serve "
                           "users whose language or region does not match any "
                           "declared locale. Without it, Google guesses, and "
                           "users outside the targeted locales may land on an "
                           "unintended version.",
                affected_urls=missing_x_default[:100],
                count=count,
                recommendation="Add an x-default hreflang annotation to each "
                              "locale cluster, pointing at the best fallback "
                              "page (commonly the primary-language or "
                              "language-selector page). Ensure the x-default "
                              "entry appears in the annotation set on every "
                              "page in the cluster, alongside the "
                              "locale-specific alternates.",
                impact="A missing x-default leaves fallback routing to Google's "
                      "discretion, so unmatched users can be shown the wrong "
                      "regional or language version — a poorer experience and "
                      "weaker relevance for international visitors.",
            )
