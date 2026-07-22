"""Google Discover Visibility Auditor.

Assesses eligibility for Google Discover — the personalised content feed
that surfaces content OUTSIDE a query (the Android swipe feed, the Google
app, the mobile homepage). Discover is a distinct traffic channel with its
own GSC report and its own eligibility model, and is invisible to a standard
SERP-focused technical/on-page audit.

IMPORTANT — Discover has no deterministic inclusion levers, only eligibility
signals that raise or lower probability. Every finding this auditor emits is
framed as "raises Discover probability," never as a pass/fail ranking rule.
Most output is therefore INSIGHT/LOW severity. The one exception is a strong,
verifiable eligibility blocker: robots directives that suppress image previews,
which effectively disqualify an image-led feed like Discover.

Verifiable checks (from the crawl):
- Identify the article/editorial URL set (Discover is a content, not a
  commercial-page, opportunity).
- Flag articles whose robots directives suppress image preview
  (``noimageindex`` / ``max-image-preview:none``), delivered via either the
  meta robots tag or the X-Robots-Tag HTTP header — a strong Discover blocker.

Reporting / guidance (needs GSC Discover export or LLM/manual judgment):
- When a GSC Discover Performance export is supplied, report current
  Discover-earning pages and high-impression/low-CTR opportunities.
- Surface the judgment-based eligibility checklist (informational-vs-commercial,
  non-clickbait titles, author E-E-A-T, mobile/CWV, timeliness, Web Stories)
  for the article set.

Internal reference for the eligibility mechanics:
Skills/ai-search-optimization/references/google-discover.md and Cluster 20 of
Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md
(kept here as a code comment only — never surfaced in client-facing text).
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd

from .base_auditor import BaseAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity


# URL path markers that identify editorial / article content (Discover-eligible).
ARTICLE_URL_MARKERS = (
    "/blog/",
    "/news/",
    "/article",
    "/guide",
    "/post/",
    "/posts/",
    "/resources/",
    "/insights/",
    "/learn/",
    "/stories/",
)

# URL path markers for commercial pages (rarely surface in Discover).
COMMERCIAL_URL_MARKERS = (
    "/product",
    "/products/",
    "/collections/",
    "/category/",
    "/categories/",
    "/shop/",
    "/service",
    "/services/",
    "/cart",
    "/checkout",
    "/pricing",
)

# Date-in-URL pattern (e.g. /2026/07/) — a strong editorial signal.
_DATE_IN_URL_RE = re.compile(r"/(19|20)\d{2}/\d{1,2}/")

# Robots directives that suppress image previews — a hard Discover blocker
# (Discover cards are image-led).
IMAGE_SUPPRESSING_DIRECTIVES = ("noimageindex", "max-image-preview:none")

# An article shorter than this is unlikely to be substantive enough for Discover.
MIN_ARTICLE_WORDS = 300

# Discover opportunity thresholds (used only when a Discover export is present).
HIGH_IMPRESSION_DISCOVER = 1000
LOW_CTR_DISCOVER = 0.02  # 2% — low for a served Discover card


class DiscoverAuditor(BaseAuditor):
    """Auditor for Google Discover eligibility and visibility."""

    def __init__(
        self,
        df: pd.DataFrame,
        discover_performance_df: Optional[pd.DataFrame] = None,
    ):
        """Initialize the Discover auditor.

        Args:
            df: DataFrame from Screaming Frog export.
            discover_performance_df: Optional GSC Discover Performance export
                (page-level clicks/impressions/ctr). When supplied, the auditor
                reports current Discover-earning pages and high-impression /
                low-CTR opportunities. When absent, the auditor runs the
                eligibility assessment from the crawl alone.
        """
        super().__init__(df)
        self.discover_performance_df = discover_performance_df

    def get_audit_type(self) -> str:
        return "onpage"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        articles = self._identify_articles()

        # Strong eligibility blocker — runs on the article set.
        self._check_image_preview_suppressed(articles)

        # Reporting from the GSC Discover export, if provided.
        self._check_discover_performance()

        # Guidance / judgment checklist for the article set.
        self._emit_eligibility_guidance(articles)

        return self.issues

    # =========================================================================
    # ARTICLE DETECTION
    # =========================================================================

    def _identify_articles(self) -> pd.DataFrame:
        """Return the subset of the crawl that looks like editorial content.

        Heuristic: indexable HTML pages whose URL carries an article marker or
        a date-in-URL pattern, excluding obvious commercial paths. Falls back
        to word-count substance when the column is available.
        """
        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[
                scope["indexability"].astype(str).str.lower() == "indexable"
            ]
        if "url" not in scope.columns or scope.empty:
            return scope.iloc[0:0] if hasattr(scope, "iloc") else scope

        def _is_article(url: object) -> bool:
            if not isinstance(url, str):
                return False
            u = url.lower()
            if any(m in u for m in COMMERCIAL_URL_MARKERS):
                return False
            if any(m in u for m in ARTICLE_URL_MARKERS):
                return True
            if _DATE_IN_URL_RE.search(u):
                return True
            return False

        articles = scope[scope["url"].apply(_is_article)]

        # If a word_count column exists, keep only substantive articles.
        if "word_count" in articles.columns:
            articles = articles[
                pd.to_numeric(articles["word_count"], errors="coerce").fillna(0)
                >= MIN_ARTICLE_WORDS
            ]
        return articles

    # =========================================================================
    # STRONG ELIGIBILITY BLOCKER
    # =========================================================================

    def _check_image_preview_suppressed(self, articles: pd.DataFrame) -> None:
        """Flag article pages whose robots directives suppress image previews.

        Discover cards are image-led; ``noimageindex`` or
        ``max-image-preview:none`` effectively disqualifies a page from
        Discover regardless of content quality. This is the strongest,
        highest-confidence, verifiable Discover eligibility blocker.

        The directive is commonly delivered via EITHER the meta robots tag or
        the ``X-Robots-Tag`` HTTP response header, so both sources are checked
        (whichever the crawl captured) over a single combined, lowercased mask.
        """
        if articles is None or articles.empty:
            return
        if "url" not in articles.columns:
            return

        # Combine every available robots-directive source into one lowercased
        # string per row: meta robots tag AND the X-Robots-Tag HTTP header.
        directive_cols = [
            col for col in ("meta_robots", "x_robots_tag")
            if col in articles.columns
        ]
        if not directive_cols:
            return

        combined = pd.Series("", index=articles.index, dtype=object)
        for col in directive_cols:
            combined = combined.str.cat(
                articles[col].astype(str).str.lower(), sep=" "
            )

        suppressed = combined.apply(
            lambda r: any(d in r for d in IMAGE_SUPPRESSING_DIRECTIVES)
        )
        count = int(suppressed.sum())
        if count == 0:
            return

        urls = articles.loc[suppressed, "url"].astype(str).tolist()
        sources = " and ".join(
            "the X-Robots-Tag HTTP header" if c == "x_robots_tag"
            else "the meta robots tag"
            for c in directive_cols
        )

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.DISCOVER,
            issue_type="discover_image_preview_suppressed",
            title=f"{count} article pages suppress image previews (Discover blocker)",
            description=f"Found {count} editorial pages whose robots directives "
                       "include noimageindex or max-image-preview:none "
                       f"(checked in {sources}). Google Discover is an image-led "
                       "feed — cards are built around a large thumbnail — so "
                       "suppressing the image preview effectively removes these "
                       "pages from Discover eligibility regardless of how strong "
                       "the content is. This is often an unintended side effect "
                       "of a blanket robots policy.",
            affected_urls=urls,
            recommendation="For editorial content that should be eligible for "
                          "Discover, set max-image-preview:large (and remove "
                          "noimageindex) in the robots meta or X-Robots-Tag "
                          "header. Confirm the site's default robots policy "
                          "isn't applying an image restriction to the blog/news "
                          "templates.",
            impact="These pages cannot earn Discover impressions while image "
                  "preview is suppressed — a self-inflicted block on a channel "
                  "that is often a large share of a content site's traffic.",
        )

    # =========================================================================
    # GSC DISCOVER PERFORMANCE (optional export)
    # =========================================================================

    def _check_discover_performance(self) -> None:
        """Report current Discover performance when a GSC export is supplied."""
        dp = self.discover_performance_df
        if dp is None or len(dp) == 0:
            return

        cols = {c.lower(): c for c in dp.columns}
        page_col = cols.get("page") or cols.get("url")
        impr_col = cols.get("impressions")
        click_col = cols.get("clicks")
        if page_col is None or impr_col is None:
            return

        earning = dp[pd.to_numeric(dp[impr_col], errors="coerce").fillna(0) > 0]
        earning_count = int(len(earning))

        # Only report the earning insight when pages are actually earning
        # (mirror the opp_count>0 guard below) — an all-zero export means the
        # site has no live Discover presence, which is not itself a finding.
        if earning_count > 0:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.DISCOVER,
                issue_type="discover_currently_earning",
                title=f"{earning_count} pages currently earn Google Discover impressions",
                description=f"The GSC Discover Performance export shows {earning_count} "
                           "pages appearing in Discover. Discover is query-independent, "
                           "so these are content pieces the feed's ranking systems "
                           "chose to surface — the topics and formats worth doubling "
                           "down on.",
                affected_urls=earning[page_col].astype(str).tolist(),
                recommendation="Identify the shared traits of the Discover-earning "
                              "pages (topic, freshness, format, imagery) and apply "
                              "them to comparable articles that aren't yet surfacing.",
                impact="Discover traffic is additive to Search and can be substantial "
                      "in editorial niches — understanding what already works is the "
                      "fastest way to grow the channel.",
            )

        # High-impression / low-CTR opportunities (thumbnail or title problem).
        if click_col is not None:
            impr = pd.to_numeric(earning[impr_col], errors="coerce").fillna(0)
            clicks = pd.to_numeric(earning[click_col], errors="coerce").fillna(0)
            ctr = clicks / impr.replace(0, pd.NA)
            opp = earning[(impr >= HIGH_IMPRESSION_DISCOVER) & (ctr < LOW_CTR_DISCOVER)]
            opp_count = int(len(opp))
            if opp_count > 0:
                self.create_issue(
                    severity=Severity.LOW,
                    category=AuditCategory.DISCOVER,
                    issue_type="discover_low_ctr_opportunity",
                    title=f"{opp_count} Discover pages with high impressions but low CTR",
                    description=f"Found {opp_count} pages served frequently in "
                               f"Discover (≥{HIGH_IMPRESSION_DISCOVER} impressions) "
                               f"but clicked under {LOW_CTR_DISCOVER:.0%}. In an "
                               "image-led feed, a low Discover CTR usually points "
                               "to a weak lead image or a title that doesn't earn "
                               "the tap — not a content-quality problem.",
                    affected_urls=opp[page_col].astype(str).tolist(),
                    recommendation="Test a stronger, higher-resolution lead image "
                                  "and a clearer, non-clickbait title that matches "
                                  "the content. Ensure max-image-preview:large is "
                                  "set. Re-check the Discover report after Google "
                                  "recrawls.",
                    impact="These pages already have Discover reach — recovering "
                          "the click on impressions they're already earning is a "
                          "low-effort traffic gain.",
                )

    # =========================================================================
    # ELIGIBILITY GUIDANCE (judgment checklist)
    # =========================================================================

    def _emit_eligibility_guidance(self, articles: pd.DataFrame) -> None:
        """Surface the judgment-based Discover eligibility checklist.

        Discover inclusion is non-deterministic, so the bulk of the assessment
        (informational-vs-commercial fit, non-clickbait titles, author E-E-A-T,
        mobile/CWV, timeliness) is LLM-judgment / manual. This emits the article
        set and the checklist as an INSIGHT so the reviewer runs it, rather than
        silently omitting the channel.
        """
        article_count = int(len(articles)) if articles is not None else 0

        if article_count == 0:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.DISCOVER,
                issue_type="discover_no_article_content",
                title="No editorial content detected — Google Discover not applicable",
                description="The crawl surfaced no article/editorial URL set "
                           "(blog, news, guides). Google Discover overwhelmingly "
                           "surfaces informational content, not commercial pages, "
                           "so a purely transactional site has little Discover "
                           "opportunity. This is a note, not a problem — don't "
                           "manufacture a Discover finding for a site with no "
                           "content library.",
                recommendation="If growing an editorial content library is a goal, "
                              "Discover becomes a channel worth targeting. "
                              "Eligibility hinges on substantive, timely, "
                              "informational articles with clear authorship, a "
                              "large indexable lead image (max-image-preview:large), "
                              "and strong mobile / Core Web Vitals — none of which a "
                              "purely transactional page set provides today.",
                impact="No Discover opportunity exists without editorial content; "
                      "effort is better spent on Search-side levers.",
            )
            return

        sample = (
            articles["url"].astype(str).tolist()
            if "url" in articles.columns else []
        )
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.DISCOVER,
            issue_type="discover_eligibility_review",
            title=f"{article_count} editorial pages — assess Google Discover eligibility",
            description=f"Identified {article_count} article/editorial pages that "
                       "are candidates for Google Discover, a query-independent "
                       "feed that can be a large traffic source in editorial "
                       "niches. Inclusion is non-deterministic — there are no "
                       "hard rules, only eligibility signals — so this is a "
                       "guided review, not a pass/fail check. For each page, "
                       "assess: (1) informational, not commercial, intent; (2) a "
                       "non-clickbait title that matches the content; (3) clear "
                       "author E-E-A-T (named author, bio, topical expertise); "
                       "(4) mobile-first and Core Web Vitals passing; (5) a large, "
                       "high-quality lead image with max-image-preview:large; "
                       "(6) current/trending topical demand. Web Stories are an "
                       "optional additional Discover surface.",
            affected_urls=sample,
            recommendation="Work the six-point eligibility checklist above against "
                          "these pages — informational intent, honest titles, "
                          "author E-E-A-T, mobile/CWV, a large indexable lead "
                          "image, and topical timeliness. Frame every "
                          "recommendation as 'raises Discover probability,' never "
                          "as a guarantee, and validate by monitoring the GSC "
                          "Discover Performance report over the following weeks.",
            impact="A content library with no Discover strategy leaves an entire "
                  "traffic channel unopened. Because inclusion is probabilistic, "
                  "the work is eligibility optimisation, not a deterministic fix.",
        )
