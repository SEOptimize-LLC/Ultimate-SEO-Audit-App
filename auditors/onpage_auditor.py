"""On-Page SEO Auditor.

Analyzes title tags, meta descriptions, headings, content quality,
internal linking, and image optimization.

Based on On-Page SEO Agent knowledge base.
"""

import pandas as pd
from typing import Optional

from .base_auditor import BaseAuditor, is_empty_or_missing, get_duplicates
from models.audit_result import AuditIssue, Severity, AuditCategory


class OnPageAuditor(BaseAuditor):
    """Auditor for on-page SEO issues.

    Checks include:
    - Title tag optimization
    - Meta description optimization
    - H1 and heading structure
    - Content quality (word count, readability)
    - Internal linking
    - Image alt text
    """

    def get_audit_type(self) -> str:
        return "onpage"

    def run_audit(self) -> list[AuditIssue]:
        """Run all on-page SEO checks."""
        self.clear_issues()

        # Title tag checks
        self._check_missing_titles()
        self._check_duplicate_titles()
        self._check_title_length()
        self._check_multiple_titles()

        # Meta description checks
        self._check_missing_meta_descriptions()
        self._check_duplicate_meta_descriptions()
        self._check_meta_description_length()

        # Heading checks
        self._check_missing_h1()
        self._check_multiple_h1s()
        self._check_duplicate_h1s()
        self._check_h1_length()

        # Content checks
        self._check_thin_content()
        self._check_low_readability()

        # Internal linking checks
        self._check_pages_with_few_internal_links()
        self._check_pages_with_no_outlinks()

        # Image checks
        self._check_missing_alt_text()
        self._check_large_images()

        # GSC performance checks (if data available)
        self._check_low_ctr_high_impressions()
        self._check_high_position_pages()

        return self.issues

    # =========================================================================
    # TITLE TAG CHECKS
    # =========================================================================

    def _check_missing_titles(self) -> None:
        """Check for pages with missing title tags."""
        if not self.has_column("title"):
            return

        # Only check indexable HTML pages
        html_pages = self.get_html_pages()
        if self.has_column("indexability"):
            html_pages = html_pages[html_pages["indexability"].str.lower() == "indexable"]

        condition = html_pages["title"].apply(is_empty_or_missing)
        urls = html_pages.loc[condition, "url"].head(100).tolist() if "url" in html_pages.columns else []
        count = condition.sum()

        if count > 0:
            self.create_issue(
                severity=Severity.CRITICAL,
                category=AuditCategory.TITLE_TAGS,
                issue_type="missing_title",
                title=f"{count} pages missing title tags",
                description=f"Found {count} indexable pages without a title tag. "
                           "Title tags are crucial for SEO and click-through rates.",
                affected_urls=urls,
                count=count,
                recommendation="Add unique, descriptive title tags to all pages. "
                              "Format: Primary Keyword - Secondary Keyword | Brand",
                impact="Missing titles result in poor SERP display and significantly lower CTR. "
                      "Search engines may auto-generate titles from page content.",
            )

    def _check_duplicate_titles(self) -> None:
        """Check for duplicate title tags across pages."""
        if not self.has_columns(["title", "url"]):
            return

        # Only check indexable pages
        df = self.get_html_pages()
        if self.has_column("indexability"):
            df = df[df["indexability"].str.lower() == "indexable"]

        # Find duplicates
        duplicates = get_duplicates(df["title"], min_count=2)

        if len(duplicates) > 0:
            # Get URLs for each duplicate title
            total_affected = 0
            affected_urls = []
            duplicate_info = {}

            for title, count in duplicates.head(20).items():  # Top 20 duplicates
                if is_empty_or_missing(title):
                    continue
                urls = df.loc[df["title"] == title, "url"].tolist()
                total_affected += len(urls)
                affected_urls.extend(urls[:5])  # First 5 URLs per duplicate
                duplicate_info[title[:50]] = count

            if total_affected > 0:
                self.create_issue(
                    severity=Severity.HIGH,
                    category=AuditCategory.TITLE_TAGS,
                    issue_type="duplicate_titles",
                    title=f"{total_affected} pages with duplicate titles",
                    description=f"Found {total_affected} pages sharing duplicate title tags across "
                               f"{len(duplicates)} unique titles. Top duplicates shown in data.",
                    affected_urls=affected_urls[:100],
                    count=total_affected,
                    recommendation="Create unique titles for each page. Use page-specific keywords "
                                  "and content descriptors to differentiate.",
                    impact="Duplicate titles cause keyword cannibalization and make it harder for "
                          "search engines to determine which page to rank.",
                    additional_data={"duplicate_counts": duplicate_info},
                )

    def _check_title_length(self) -> None:
        """Check for titles that are too short or too long."""
        if not self.has_column("title_length"):
            return

        df = self.get_html_pages()

        # Too short (<30 chars)
        short_condition = (df["title_length"] > 0) & (df["title_length"] < 30)
        short_urls = df.loc[short_condition, "url"].head(100).tolist() if "url" in df.columns else []
        short_count = short_condition.sum()

        if short_count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.TITLE_TAGS,
                issue_type="title_too_short",
                title=f"{short_count} pages with short titles (<30 chars)",
                description=f"Found {short_count} pages with title tags under 30 characters. "
                           "Short titles miss opportunities to include keywords and compelling copy.",
                affected_urls=short_urls,
                count=short_count,
                recommendation="Expand titles to 50-60 characters. Include primary keyword, "
                              "secondary modifier, and brand name where space allows.",
                impact="Short titles may not fully communicate page content and miss ranking opportunities.",
            )

        # Too long (>60 chars)
        long_condition = df["title_length"] > 60
        long_urls = df.loc[long_condition, "url"].head(100).tolist() if "url" in df.columns else []
        long_count = long_condition.sum()

        if long_count > 0:
            avg_length = df.loc[long_condition, "title_length"].mean()

            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.TITLE_TAGS,
                issue_type="title_too_long",
                title=f"{long_count} pages with long titles (>60 chars)",
                description=f"Found {long_count} pages with title tags over 60 characters. "
                           f"Average length: {avg_length:.0f} chars. These will be truncated in SERPs.",
                affected_urls=long_urls,
                count=long_count,
                recommendation="Shorten titles to ~60 characters. Front-load important keywords "
                              "to ensure they're visible when truncated.",
                impact="Truncated titles may cut off important information, though this is a minor issue.",
                additional_data={"avg_length": round(avg_length, 0)},
            )

    def _check_multiple_titles(self) -> None:
        """Check for pages with multiple title tags."""
        if not self.has_column("title_2"):
            return

        condition = ~self.df["title_2"].apply(is_empty_or_missing)
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.TITLE_TAGS,
                issue_type="multiple_titles",
                title=f"{count} pages with multiple title tags",
                description=f"Found {count} pages with more than one title tag. "
                           "Browsers and search engines use only the first one.",
                affected_urls=urls,
                count=count,
                recommendation="Remove duplicate title tags. Ensure only one title tag exists in the <head>.",
                impact="Multiple titles indicate template or CMS issues and may confuse search engines.",
            )

    # =========================================================================
    # META DESCRIPTION CHECKS
    # =========================================================================

    def _check_missing_meta_descriptions(self) -> None:
        """Check for pages with missing meta descriptions."""
        if not self.has_column("meta_description"):
            return

        df = self.get_html_pages()
        if self.has_column("indexability"):
            df = df[df["indexability"].str.lower() == "indexable"]

        condition = df["meta_description"].apply(is_empty_or_missing)
        urls = df.loc[condition, "url"].head(100).tolist() if "url" in df.columns else []
        count = condition.sum()

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.META_DESCRIPTIONS,
                issue_type="missing_meta_description",
                title=f"{count} pages missing meta descriptions",
                description=f"Found {count} indexable pages without meta descriptions. "
                           "Search engines will auto-generate snippets from page content.",
                affected_urls=urls,
                count=count,
                recommendation="Write compelling meta descriptions for all important pages. "
                              "Include target keyword, value proposition, and call-to-action.",
                impact="Missing meta descriptions mean you lose control over SERP snippets, "
                      "potentially hurting click-through rates.",
            )

    def _check_duplicate_meta_descriptions(self) -> None:
        """Check for duplicate meta descriptions."""
        if not self.has_columns(["meta_description", "url"]):
            return

        df = self.get_html_pages()
        if self.has_column("indexability"):
            df = df[df["indexability"].str.lower() == "indexable"]

        duplicates = get_duplicates(df["meta_description"], min_count=2)

        if len(duplicates) > 0:
            total_affected = 0
            affected_urls = []

            for desc, count in duplicates.head(10).items():
                if is_empty_or_missing(desc):
                    continue
                urls = df.loc[df["meta_description"] == desc, "url"].tolist()
                total_affected += len(urls)
                affected_urls.extend(urls[:5])

            if total_affected > 0:
                self.create_issue(
                    severity=Severity.MEDIUM,
                    category=AuditCategory.META_DESCRIPTIONS,
                    issue_type="duplicate_meta_descriptions",
                    title=f"{total_affected} pages with duplicate meta descriptions",
                    description=f"Found {total_affected} pages sharing the same meta description "
                               f"across {len(duplicates)} unique descriptions.",
                    affected_urls=affected_urls[:100],
                    count=total_affected,
                    recommendation="Write unique meta descriptions for each page that accurately "
                                  "describe the specific content.",
                    impact="Duplicate meta descriptions miss the opportunity to differentiate pages in SERPs.",
                )

    def _check_meta_description_length(self) -> None:
        """Check for meta descriptions that are too short or too long."""
        if not self.has_column("meta_desc_length"):
            return

        df = self.get_html_pages()

        # Too short (<120 chars)
        short_condition = (df["meta_desc_length"] > 0) & (df["meta_desc_length"] < 120)
        short_count = short_condition.sum()

        if short_count > 0:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.META_DESCRIPTIONS,
                issue_type="meta_description_short",
                title=f"{short_count} pages with short meta descriptions (<120 chars)",
                description=f"Found {short_count} pages with meta descriptions under 120 characters.",
                affected_urls=self.filter_by_condition(short_condition),
                count=short_count,
                recommendation="Expand meta descriptions to 120-160 characters to maximize SERP real estate.",
                impact="Short meta descriptions may not fully communicate page value.",
            )

        # Too long (>160 chars)
        long_condition = df["meta_desc_length"] > 160
        long_count = long_condition.sum()

        if long_count > 0:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.META_DESCRIPTIONS,
                issue_type="meta_description_long",
                title=f"{long_count} pages with long meta descriptions (>160 chars)",
                description=f"Found {long_count} pages with meta descriptions over 160 characters. "
                           "These will be truncated in search results.",
                affected_urls=self.filter_by_condition(long_condition),
                count=long_count,
                recommendation="Shorten to ~155 characters. Front-load the value proposition.",
                impact="Truncation may cut off important information, but this is a minor issue.",
            )

    # =========================================================================
    # HEADING CHECKS
    # =========================================================================

    def _check_missing_h1(self) -> None:
        """Check for pages missing H1 tags."""
        if not self.has_column("h1"):
            return

        df = self.get_html_pages()
        if self.has_column("indexability"):
            df = df[df["indexability"].str.lower() == "indexable"]

        condition = df["h1"].apply(is_empty_or_missing)
        urls = df.loc[condition, "url"].head(100).tolist() if "url" in df.columns else []
        count = condition.sum()

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.HEADINGS,
                issue_type="missing_h1",
                title=f"{count} pages missing H1 tags",
                description=f"Found {count} indexable pages without an H1 heading. "
                           "H1 is an important signal for page topic.",
                affected_urls=urls,
                count=count,
                recommendation="Add a single, descriptive H1 to each page that clearly states the main topic. "
                              "Include the primary keyword naturally.",
                impact="Missing H1 weakens page structure signals and accessibility.",
            )

    def _check_multiple_h1s(self) -> None:
        """Check for pages with multiple H1 tags."""
        if not self.has_column("h1_2"):
            return

        condition = ~self.df["h1_2"].apply(is_empty_or_missing)
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.HEADINGS,
                issue_type="multiple_h1s",
                title=f"{count} pages with multiple H1 tags",
                description=f"Found {count} pages with more than one H1 tag. "
                           "Best practice is to have a single H1 per page.",
                affected_urls=urls,
                count=count,
                recommendation="Consolidate to a single H1 that represents the main page topic. "
                              "Use H2-H6 for subheadings.",
                impact="Multiple H1s dilute heading hierarchy signals, though modern search engines handle this better.",
            )

    def _check_duplicate_h1s(self) -> None:
        """Check for duplicate H1s across pages."""
        if not self.has_columns(["h1", "url"]):
            return

        df = self.get_html_pages()
        duplicates = get_duplicates(df["h1"], min_count=2)

        if len(duplicates) > 0:
            total_affected = 0
            affected_urls = []

            for h1, count in duplicates.head(10).items():
                if is_empty_or_missing(h1):
                    continue
                urls = df.loc[df["h1"] == h1, "url"].tolist()
                total_affected += len(urls)
                affected_urls.extend(urls[:5])

            if total_affected > 0:
                self.create_issue(
                    severity=Severity.MEDIUM,
                    category=AuditCategory.HEADINGS,
                    issue_type="duplicate_h1s",
                    title=f"{total_affected} pages with duplicate H1s",
                    description=f"Found {total_affected} pages sharing the same H1 tag.",
                    affected_urls=affected_urls[:100],
                    count=total_affected,
                    recommendation="Create unique H1s for each page that reflect specific page content.",
                    impact="Duplicate H1s may indicate template issues or thin/duplicate content.",
                )

    def _check_h1_length(self) -> None:
        """Check for H1s that are too short or too long."""
        if not self.has_column("h1_length"):
            return

        df = self.get_html_pages()

        # Too long (>70 chars)
        long_condition = df["h1_length"] > 70
        long_count = long_condition.sum()

        if long_count > 0:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.HEADINGS,
                issue_type="h1_too_long",
                title=f"{long_count} pages with long H1 tags (>70 chars)",
                description=f"Found {long_count} pages with H1 tags over 70 characters.",
                affected_urls=self.filter_by_condition(long_condition),
                count=long_count,
                recommendation="Keep H1s concise and focused on the main topic. Consider splitting into H1 + subtitle.",
                impact="Long H1s dilute focus and can be harder to scan.",
            )

    # =========================================================================
    # CONTENT CHECKS
    # =========================================================================

    def _check_thin_content(self) -> None:
        """Check for pages with thin content."""
        if not self.has_column("word_count"):
            return

        df = self.get_html_pages()
        if self.has_column("indexability"):
            df = df[df["indexability"].str.lower() == "indexable"]

        # Less than 300 words is thin
        condition = (df["word_count"] > 0) & (df["word_count"] < 300)
        urls = df.loc[condition, "url"].head(100).tolist() if "url" in df.columns else []
        count = condition.sum()

        if count > 0:
            avg_words = df.loc[condition, "word_count"].mean()

            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.CONTENT,
                issue_type="thin_content",
                title=f"{count} pages with thin content (<300 words)",
                description=f"Found {count} indexable pages with less than 300 words. "
                           f"Average word count: {avg_words:.0f}.",
                affected_urls=urls,
                count=count,
                recommendation="Expand thin pages with valuable, relevant content. Consider: "
                              "1) Adding more detail, 2) Combining with similar pages, "
                              "3) Noindexing if no unique value.",
                impact="Thin content pages provide little value to users and may be seen as low quality by search engines.",
                additional_data={"avg_word_count": round(avg_words, 0)},
            )

    def _check_low_readability(self) -> None:
        """Check for pages with poor readability scores."""
        if not self.has_column("flesch_score"):
            return

        df = self.get_html_pages()

        # Flesch score < 30 is very difficult to read
        condition = (df["flesch_score"] > 0) & (df["flesch_score"] < 30)
        urls = df.loc[condition, "url"].head(100).tolist() if "url" in df.columns else []
        count = condition.sum()

        if count > 0:
            avg_score = df.loc[condition, "flesch_score"].mean()

            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.CONTENT,
                issue_type="low_readability",
                title=f"{count} pages with low readability (Flesch <30)",
                description=f"Found {count} pages with Flesch reading ease score below 30 (very difficult). "
                           f"Average score: {avg_score:.1f}.",
                affected_urls=urls,
                count=count,
                recommendation="Simplify content: use shorter sentences, common words, and clear structure. "
                              "Target Flesch score of 60-70 for general audiences.",
                impact="Difficult content may increase bounce rates and reduce engagement.",
                additional_data={"avg_flesch_score": round(avg_score, 1)},
            )

    # =========================================================================
    # INTERNAL LINKING CHECKS
    # =========================================================================

    def _check_pages_with_few_internal_links(self) -> None:
        """Check for pages with very few internal links pointing to them."""
        if not self.has_column("internal_links_in"):
            return

        df = self.get_html_pages()
        if self.has_column("indexability"):
            df = df[df["indexability"].str.lower() == "indexable"]

        # Only 1 internal link (already caught orphans with 0)
        condition = df["internal_links_in"] == 1
        urls = df.loc[condition, "url"].head(100).tolist() if "url" in df.columns else []
        count = condition.sum()

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.INTERNAL_LINKS,
                issue_type="few_internal_links",
                title=f"{count} pages with only 1 internal link",
                description=f"Found {count} pages with only a single internal link pointing to them. "
                           "These pages receive minimal PageRank flow.",
                affected_urls=urls,
                count=count,
                recommendation="Add more contextual internal links from relevant pages. "
                              "Consider adding to navigation, related content sections, or content hubs.",
                impact="Pages with few internal links may not rank well and might not be crawled frequently.",
            )

    def _check_pages_with_no_outlinks(self) -> None:
        """Check for pages with no outgoing internal links (dead ends)."""
        if not self.has_column("internal_links_out"):
            return

        df = self.get_html_pages()

        condition = df["internal_links_out"] == 0
        urls = df.loc[condition, "url"].head(100).tolist() if "url" in df.columns else []
        count = condition.sum()

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.INTERNAL_LINKS,
                issue_type="no_outlinks",
                title=f"{count} pages with no outgoing internal links",
                description=f"Found {count} pages that don't link to any other internal pages. "
                           "These are 'dead ends' for crawlers and PageRank.",
                affected_urls=urls,
                count=count,
                recommendation="Add relevant internal links to guide users and crawlers to related content.",
                impact="Dead-end pages don't distribute PageRank and may reduce overall crawl efficiency.",
            )

    # =========================================================================
    # IMAGE CHECKS
    # =========================================================================

    def _check_missing_alt_text(self) -> None:
        """Check for images with missing alt text."""
        if not self.has_column("missing_alt"):
            return

        condition = self.df["missing_alt"] > 0
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            total_missing = int(self.df["missing_alt"].sum())

            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.IMAGES,
                issue_type="missing_alt_text",
                title=f"{total_missing} images missing alt text on {count} pages",
                description=f"Found {total_missing} images without alt text across {count} pages. "
                           "Alt text is important for accessibility and image SEO.",
                affected_urls=urls,
                count=count,
                recommendation="Add descriptive alt text to all meaningful images. "
                              "Include relevant keywords naturally. Use empty alt='' for decorative images.",
                impact="Missing alt text hurts accessibility (screen readers) and loses image ranking opportunities.",
                additional_data={"total_missing_images": total_missing},
            )

    def _check_large_images(self) -> None:
        """Check for oversized images."""
        if not self.has_column("large_images"):
            return

        condition = self.df["large_images"] > 0
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            total_large = int(self.df["large_images"].sum())

            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.IMAGES,
                issue_type="large_images",
                title=f"{total_large} oversized images on {count} pages",
                description=f"Found {total_large} images over 100KB across {count} pages. "
                           "Large images slow down page load.",
                affected_urls=urls,
                count=count,
                recommendation="Optimize images: 1) Resize to display dimensions, 2) Compress quality, "
                              "3) Use modern formats (WebP, AVIF), 4) Implement lazy loading.",
                impact="Large images significantly impact page load time and Core Web Vitals (LCP).",
                additional_data={"total_large_images": total_large},
            )

    # =========================================================================
    # GSC PERFORMANCE CHECKS (when data available)
    # =========================================================================

    def _check_low_ctr_high_impressions(self) -> None:
        """Check for pages with high impressions but low CTR (snippet optimization opportunities)."""
        if not self.has_columns(["gsc_impressions", "gsc_ctr"]):
            return

        # High impressions (>100) but low CTR (<2%)
        condition = (self.df["gsc_impressions"] > 100) & (self.df["gsc_ctr"] < 2)
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.TITLE_TAGS,
                issue_type="low_ctr_opportunity",
                title=f"{count} pages with high impressions but low CTR (<2%)",
                description=f"Found {count} pages getting significant impressions but below-average CTR. "
                           "These are prime opportunities for title/meta optimization.",
                affected_urls=urls,
                count=count,
                recommendation="Optimize titles and meta descriptions to be more compelling. "
                              "Add numbers, power words, and clear value propositions.",
                impact="Improving CTR on high-impression pages can significantly increase organic traffic.",
            )

    def _check_high_position_pages(self) -> None:
        """Check for pages ranking well that could be optimized further."""
        if not self.has_columns(["gsc_position", "gsc_impressions"]):
            return

        # Position 4-10 with good impressions - close to page 1 top
        condition = (
            (self.df["gsc_position"] >= 4) &
            (self.df["gsc_position"] <= 10) &
            (self.df["gsc_impressions"] > 50)
        )
        urls = self.filter_by_condition(condition)
        count = self.count_by_condition(condition)

        if count > 0:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.CONTENT,
                issue_type="ranking_opportunity",
                title=f"{count} pages ranking 4-10 with optimization potential",
                description=f"Found {count} pages ranking positions 4-10 with meaningful impressions. "
                           "Small improvements could push these to top 3 positions.",
                affected_urls=urls,
                count=count,
                recommendation="Review these pages for: content depth, freshness, internal links, "
                              "and featured snippet optimization opportunities.",
                impact="Moving from position 5-10 to top 3 typically doubles or triples click-through rate.",
            )
