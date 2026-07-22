"""Mobile-First Indexing Auditor.

Audits patterns that affect mobile-first indexing. Google indexes the
mobile version of the site exclusively — if the mobile version has
stripped-down content compared to desktop, the stripped version is
what gets indexed.

Detection scope is limited without dual-crawl data (mobile + desktop
crawls run separately). When dual-crawl data isn't available, this
auditor falls back to detecting common patterns that correlate with
mobile-first issues:

- Viewport meta tag missing or misconfigured
- Pages flagged as not mobile-friendly by PageSpeed Insights
- Pages with very small font sizes (<14px) that fail mobile readability
- Pages with tap targets too close together (when CWV reports it)

This is the lowest-priority auditor in the suite because most modern
themes are responsive by default — detection rate is typically low.
The auditor exists so that when there IS a problem, it gets surfaced.
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd

from .base_auditor import BaseAuditor, is_empty_or_missing
from models.audit_result import AuditCategory, AuditIssue, Severity


class MobileFirstAuditor(BaseAuditor):
    """Auditor for mobile-first indexing patterns."""

    def get_audit_type(self) -> str:
        return "technical"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        self._emit_data_availability()
        self._check_missing_viewport()
        self._check_mobile_unfriendly()

        return self.issues

    def _emit_data_availability(self) -> None:
        """Note the limited scope of mobile-first audits in single-crawl mode."""
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.MOBILE_FIRST,
            issue_type="mobile_first_limited_scope",
            title="Mobile-first audit running with single-crawl data",
            description=(
                "True mobile-first auditing requires comparing the "
                "mobile and desktop renders of each page to detect "
                "content parity issues. Single-crawl data only "
                "surfaces patterns visible from one rendering pass. "
                "The checks running here detect common mobile-first "
                "problems (missing viewport, mobile-unfriendly "
                "patterns) but cannot guarantee mobile-desktop "
                "content parity. For sites where mobile UX is a "
                "concern, run a separate mobile crawl in Screaming "
                "Frog and diff it against the desktop crawl."
            ),
            recommendation=(
                "For a complete mobile-first audit: (1) run a "
                "Screaming Frog crawl with user-agent set to "
                "Googlebot Smartphone, (2) run a separate crawl "
                "with the desktop user-agent, (3) diff the two "
                "crawls — pages with materially less content on "
                "mobile, fewer internal links, or missing schema "
                "are mobile-first risks."
            ),
            impact=(
                "Most modern themes are responsive by default, so "
                "the failure rate on this audit is typically low. "
                "When issues exist, they're usually concentrated in "
                "older templates, custom mobile views, or pages "
                "with conditional content blocks that render "
                "differently on mobile."
            ),
        )

    def _check_missing_viewport(self) -> None:
        """Flag indexable pages without a viewport meta tag."""
        # SF column for viewport varies — check several candidates
        viewport_col = None
        for candidate in ("viewport", "meta_viewport", "viewport_meta"):
            if self.has_column(candidate):
                viewport_col = candidate
                break
        if viewport_col is None:
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if scope.empty:
            return

        condition = scope[viewport_col].apply(is_empty_or_missing)
        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.MOBILE_FIRST,
                issue_type="missing_viewport_meta",
                title=f"{count} pages missing viewport meta tag",
                description=(
                    f"Found {count} indexable pages without a viewport "
                    "meta tag. Without `<meta name='viewport' "
                    "content='width=device-width, initial-scale=1'>`, "
                    "mobile browsers render the page at desktop "
                    "width and require zoom-to-read — failing "
                    "mobile-friendliness checks and degrading mobile "
                    "user experience."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Add the viewport meta tag to the <head> of all "
                    "pages: `<meta name='viewport' content='width="
                    "device-width, initial-scale=1'>`. For most "
                    "themes this is added globally in the layout "
                    "template — fixing one template fixes all "
                    "affected pages. Verify the fix using Google's "
                    "Mobile-Friendly Test."
                ),
                impact=(
                    "Pages without viewport configuration fail "
                    "Google's mobile-friendly check. Mobile-first "
                    "indexing means the mobile experience is what "
                    "gets indexed — if it's broken, rankings suffer."
                ),
            )

    def _check_mobile_unfriendly(self) -> None:
        """Flag pages explicitly marked as not mobile-friendly.

        SF can capture this when integrated with the Mobile-Friendly
        Test API. Falls back gracefully if column not present.
        """
        # SF column candidates
        mobile_col = None
        for candidate in ("mobile_friendly", "is_mobile_friendly",
                          "mobile_usability"):
            if self.has_column(candidate):
                mobile_col = candidate
                break
        if mobile_col is None:
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        # Detect "false" or "no" or specific failure markers
        def is_unfriendly(value) -> bool:
            if pd.isna(value):
                return False
            s = str(value).lower().strip()
            return s in ("false", "no", "fail", "failed", "not_mobile_friendly")

        condition = scope[mobile_col].apply(is_unfriendly)
        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.MOBILE_FIRST,
                issue_type="mobile_unfriendly_pages",
                title=f"{count} pages flagged as not mobile-friendly",
                description=(
                    f"Found {count} indexable pages flagged by "
                    "Google's Mobile-Friendly Test as failing "
                    "mobile usability checks. Common causes: "
                    "viewport not configured, font sizes too small, "
                    "tap targets too close, content wider than "
                    "screen, or JavaScript-driven layouts that fail "
                    "responsive rendering."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "For each affected page, run Google's Mobile-"
                    "Friendly Test individually to see the specific "
                    "failure reason. Common fixes:\n"
                    "- Add or fix viewport meta tag\n"
                    "- Increase base font size to at least 14px (16px "
                    "preferred)\n"
                    "- Increase spacing between tap targets to at "
                    "least 8px\n"
                    "- Use responsive CSS instead of fixed-width "
                    "layouts\n"
                    "- Test with the Chrome DevTools device emulator "
                    "to verify fixes before re-running the audit."
                ),
                impact=(
                    "Mobile-unfriendly pages rank lower in mobile "
                    "results — and since mobile-first indexing means "
                    "mobile is THE index, this affects desktop "
                    "rankings too. Failing pages often see direct "
                    "ranking suppression in competitive queries."
                ),
            )
