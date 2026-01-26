"""Technical SEO Auditor.

Analyzes crawlability, indexability, redirects, Core Web Vitals,
and other technical SEO issues.

Based on Technical SEO Agent knowledge base.
"""

import pandas as pd
from typing import Optional

from .base_auditor import BaseAuditor, is_empty_or_missing
from models.audit_result import AuditIssue, Severity, AuditCategory


class TechnicalAuditor(BaseAuditor):
    """Auditor for technical SEO issues.

    Checks include:
    - Status codes (4xx, 5xx errors)
    - Indexability issues
    - Canonical problems
    - Robots directives
    - Redirect chains/loops
    - Core Web Vitals
    - HTTPS/Security
    """

    def get_audit_type(self) -> str:
        return "technical"

    def run_audit(self) -> list[AuditIssue]:
        """Run all technical SEO checks."""
        self.clear_issues()

        # Status code checks
        self._check_4xx_errors()
        self._check_5xx_errors()
        self._check_soft_404s()

        # Indexability checks
        self._check_noindex_pages()
        self._check_blocked_by_robots()
        self._check_orphan_pages()

        # Canonical checks
        self._check_missing_canonical()
        self._check_canonical_mismatch()
        self._check_canonical_chain()
        self._check_canonical_to_redirect()
        self._check_canonical_to_4xx_5xx()

        # Redirect checks
        self._check_redirect_chains()
        self._check_redirect_loops()
        self._check_http_to_https()

        # Core Web Vitals checks
        self._check_poor_lcp()
        self._check_poor_cls()
        self._check_poor_tbt()
        self._check_low_performance_score()

        # Security checks
        self._check_http_pages()
        self._check_mixed_content()

        # Response time
        self._check_slow_pages()

        return self.issues

    # =========================================================================
    # STATUS CODE CHECKS
    # =========================================================================

    def _check_4xx_errors(self) -> None:
        """Check for 4xx client errors."""
        if not self.has_column("status_code"):
            return

        condition = (self.df["status_code"] >= 400) & (self.df["status_code"] < 500)
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            # Breakdown by specific codes
            error_breakdown = self.df.loc[condition, "status_code"].value_counts().to_dict()

            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.CRAWLABILITY,
                issue_type="4xx_errors",
                title=f"{count} pages return 4XX errors",
                description=f"Found {count} URLs returning client error status codes (400-499). "
                           f"Breakdown: {error_breakdown}",
                affected_urls=urls,
                count=count,
                recommendation="Fix or remove broken internal links pointing to these pages. "
                              "Set up proper 301 redirects if content has moved.",
                impact="4XX errors waste crawl budget and create poor user experience. "
                      "Internal links to 4XX pages pass no value.",
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
        """Check for soft 404s (200 status but likely error pages)."""
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

        if count > 0:
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

        # Find noindex pages
        noindex_condition = self.df["meta_robots"].str.contains("noindex", case=False, na=False)

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
                severity=Severity.MEDIUM,
                category=AuditCategory.INDEXABILITY,
                issue_type="noindex_with_content",
                title=f"{count} noindex pages with significant content",
                description=f"Found {count} pages with noindex directive that have substantial content. "
                           f"Total noindex pages: {total_noindex}. Review if these should be indexed.",
                affected_urls=urls,
                count=count,
                recommendation="Review each noindex page. If it should be indexed, remove the noindex directive. "
                              "Common accidental noindex: staging settings left on, template issues.",
                impact="Noindex pages are excluded from search results, losing potential organic traffic.",
            )

    def _check_blocked_by_robots(self) -> None:
        """Check for pages blocked by robots.txt."""
        if not self.has_column("robots_txt_status"):
            return

        condition = self.df["robots_txt_status"].str.contains("blocked", case=False, na=False)
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
        """Check for orphan pages (no internal links pointing to them)."""
        if not self.has_column("internal_links_in"):
            return

        condition = self.df["internal_links_in"] == 0
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.INDEXABILITY,
                issue_type="orphan_pages",
                title=f"{count} orphan pages (no internal links)",
                description=f"Found {count} pages with zero internal links pointing to them. "
                           "These pages are isolated from the site structure.",
                affected_urls=urls,
                count=count,
                recommendation="Add contextual internal links from relevant pages. Consider adding to "
                              "navigation, related posts sections, or content hubs.",
                impact="Orphan pages receive no PageRank from internal links and may not be discovered by crawlers.",
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
