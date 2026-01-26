"""Competitor Auditor.

Analyzes competitive landscape, keyword gaps, content opportunities,
and market positioning.

Based on Competitor Agent knowledge base.
"""

from typing import Optional
from collections import defaultdict

from models.audit_result import AuditIssue, Severity, AuditCategory
from services.dataforseo_client import CompetitorData


class CompetitorAuditor:
    """Auditor for competitive SEO analysis.

    Checks include:
    - Keyword gap analysis
    - Competitor identification
    - Content opportunities
    - Quick wins identification
    """

    def __init__(self, competitor_data: CompetitorData, domain: str):
        """Initialize the auditor with competitor data.

        Args:
            competitor_data: CompetitorData from DataForSEO
            domain: Target domain being analyzed
        """
        self.data = competitor_data
        self.domain = domain
        self.issues: list[AuditIssue] = []

    def get_audit_type(self) -> str:
        return "competitor"

    def run_audit(self) -> list[AuditIssue]:
        """Run all competitive analysis checks."""
        self.issues = []

        # Competitor analysis
        self._analyze_top_competitors()

        # Keyword analysis
        self._analyze_keyword_portfolio()
        self._identify_quick_wins()
        self._identify_keyword_gaps()

        # Position analysis
        self._analyze_ranking_distribution()

        return self.issues

    def create_issue(
        self,
        severity: Severity,
        category: AuditCategory,
        issue_type: str,
        title: str,
        description: str,
        count: int = 0,
        recommendation: Optional[str] = None,
        impact: Optional[str] = None,
        additional_data: Optional[dict] = None,
    ) -> AuditIssue:
        """Create an AuditIssue and add it to the issues list."""
        issue = AuditIssue(
            severity=severity,
            category=category,
            issue_type=issue_type,
            title=title,
            description=description,
            affected_urls=[],
            count=count,
            recommendation=recommendation,
            impact=impact,
            additional_data=additional_data or {},
        )
        self.issues.append(issue)
        return issue

    # =========================================================================
    # COMPETITOR ANALYSIS
    # =========================================================================

    def _analyze_top_competitors(self) -> None:
        """Analyze and report on top competitors."""
        if not self.data.competitors:
            return

        # Get top 5 competitors by keyword overlap
        top_competitors = []
        for comp in self.data.competitors[:10]:
            domain = comp.get("domain", "unknown")
            intersections = comp.get("intersections", 0)
            metrics = comp.get("metrics", {})

            top_competitors.append({
                "domain": domain,
                "keyword_overlap": intersections,
                "organic_keywords": metrics.get("organic", {}).get("count", 0),
                "organic_traffic": metrics.get("organic", {}).get("etv", 0),
            })

        if top_competitors:
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.COMPETITIVE_POSITION,
                issue_type="top_competitors",
                title=f"Identified {len(top_competitors)} organic competitors",
                description=f"Top competitor: {top_competitors[0]['domain']} with "
                           f"{top_competitors[0]['keyword_overlap']} overlapping keywords.",
                count=len(top_competitors),
                recommendation="Monitor these competitors for content strategies, new keywords, "
                              "and link building opportunities.",
                additional_data={"competitors": top_competitors[:5]},
            )

    # =========================================================================
    # KEYWORD PORTFOLIO ANALYSIS
    # =========================================================================

    def _analyze_keyword_portfolio(self) -> None:
        """Analyze the current keyword portfolio."""
        if not self.data.ranked_keywords:
            return

        # Categorize by position
        position_buckets = {
            "top_3": 0,
            "4_10": 0,
            "11_20": 0,
            "21_50": 0,
            "51_100": 0,
        }

        total_volume = 0
        total_traffic = 0

        for kw in self.data.ranked_keywords:
            position = kw.get("ranked_serp_element", {}).get("serp_item", {}).get("rank_group", 100)
            kw_data = kw.get("keyword_data", {}).get("keyword_info", {})
            volume = kw_data.get("search_volume", 0) or 0
            traffic = kw.get("ranked_serp_element", {}).get("serp_item", {}).get("etv", 0) or 0

            total_volume += volume
            total_traffic += traffic

            if position <= 3:
                position_buckets["top_3"] += 1
            elif position <= 10:
                position_buckets["4_10"] += 1
            elif position <= 20:
                position_buckets["11_20"] += 1
            elif position <= 50:
                position_buckets["21_50"] += 1
            else:
                position_buckets["51_100"] += 1

        total_keywords = len(self.data.ranked_keywords)

        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.KEYWORD_GAPS,
            issue_type="keyword_portfolio",
            title=f"Ranking for {total_keywords} keywords",
            description=f"Position distribution: Top 3: {position_buckets['top_3']}, "
                       f"4-10: {position_buckets['4_10']}, 11-20: {position_buckets['11_20']}, "
                       f"21-50: {position_buckets['21_50']}, 51-100: {position_buckets['51_100']}",
            count=total_keywords,
            additional_data={
                "position_distribution": position_buckets,
                "total_search_volume": total_volume,
                "estimated_traffic": int(total_traffic),
            },
        )

    def _identify_quick_wins(self) -> None:
        """Identify quick win opportunities (positions 4-20 with good volume)."""
        if not self.data.ranked_keywords:
            return

        quick_wins = []

        for kw in self.data.ranked_keywords:
            position = kw.get("ranked_serp_element", {}).get("serp_item", {}).get("rank_group", 100)
            kw_data = kw.get("keyword_data", {}).get("keyword_info", {})
            keyword = kw_data.get("keyword", "")
            volume = kw_data.get("search_volume", 0) or 0
            url = kw.get("ranked_serp_element", {}).get("serp_item", {}).get("url", "")

            # Quick wins: Position 4-20, decent volume (>100)
            if 4 <= position <= 20 and volume >= 100:
                quick_wins.append({
                    "keyword": keyword,
                    "position": position,
                    "volume": volume,
                    "url": url,
                    "potential_gain": self._estimate_traffic_gain(position, volume),
                })

        if quick_wins:
            # Sort by potential gain
            quick_wins.sort(key=lambda x: x["potential_gain"], reverse=True)
            top_wins = quick_wins[:10]

            total_potential = sum(w["potential_gain"] for w in quick_wins)

            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.KEYWORD_GAPS,
                issue_type="quick_wins",
                title=f"{len(quick_wins)} quick win keyword opportunities",
                description=f"Found {len(quick_wins)} keywords ranking 4-20 with search volume >100. "
                           f"Improving these to top 3 could gain ~{int(total_potential)} monthly visits.",
                count=len(quick_wins),
                recommendation="Prioritize these pages for optimization: improve content depth, "
                              "add internal links, optimize title/meta for CTR, build targeted backlinks.",
                impact="Moving from position 5-10 to top 3 typically doubles or triples click-through rate.",
                additional_data={"quick_wins": top_wins},
            )

    def _estimate_traffic_gain(self, current_position: int, volume: int) -> int:
        """Estimate additional traffic from improving to top 3.

        Args:
            current_position: Current ranking position
            volume: Monthly search volume

        Returns:
            Estimated additional monthly traffic
        """
        # CTR estimates by position
        ctr_by_position = {
            1: 0.28, 2: 0.15, 3: 0.11,
            4: 0.08, 5: 0.07, 6: 0.05,
            7: 0.04, 8: 0.03, 9: 0.03, 10: 0.02,
        }

        current_ctr = ctr_by_position.get(current_position, 0.01)
        target_ctr = ctr_by_position.get(3, 0.11)  # Assume moving to position 3

        current_traffic = volume * current_ctr
        potential_traffic = volume * target_ctr

        return int(potential_traffic - current_traffic)

    def _identify_keyword_gaps(self) -> None:
        """Identify keyword gaps vs competitors.

        Note: Full gap analysis would require competitor keyword data.
        This is a simplified version based on available data.
        """
        if not self.data.ranked_keywords:
            return

        # Identify weak positions (21-100) with decent volume
        weak_positions = []

        for kw in self.data.ranked_keywords:
            position = kw.get("ranked_serp_element", {}).get("serp_item", {}).get("rank_group", 100)
            kw_data = kw.get("keyword_data", {}).get("keyword_info", {})
            keyword = kw_data.get("keyword", "")
            volume = kw_data.get("search_volume", 0) or 0
            competition = kw_data.get("competition", 0) or 0

            # Weak positions with opportunity
            if position > 20 and volume >= 100:
                weak_positions.append({
                    "keyword": keyword,
                    "position": position,
                    "volume": volume,
                    "competition": competition,
                })

        if weak_positions:
            # Sort by volume
            weak_positions.sort(key=lambda x: x["volume"], reverse=True)
            top_gaps = weak_positions[:15]

            total_volume = sum(w["volume"] for w in weak_positions)

            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.KEYWORD_GAPS,
                issue_type="weak_rankings",
                title=f"{len(weak_positions)} keywords with weak rankings (21+)",
                description=f"Found {len(weak_positions)} keywords ranking below position 20 with "
                           f"search volume >100. Combined monthly volume: {total_volume:,}",
                count=len(weak_positions),
                recommendation="Create or improve content targeting these keywords. Consider "
                              "content consolidation or new dedicated pages for high-volume terms.",
                impact="These represent potential traffic you're not capturing effectively.",
                additional_data={"weak_keywords": top_gaps},
            )

    # =========================================================================
    # POSITION ANALYSIS
    # =========================================================================

    def _analyze_ranking_distribution(self) -> None:
        """Analyze the distribution of rankings and identify patterns."""
        if not self.data.ranked_keywords:
            return

        # Group keywords by URL to find pages with multiple rankings
        url_keywords = defaultdict(list)

        for kw in self.data.ranked_keywords:
            url = kw.get("ranked_serp_element", {}).get("serp_item", {}).get("url", "")
            kw_data = kw.get("keyword_data", {}).get("keyword_info", {})
            keyword = kw_data.get("keyword", "")
            position = kw.get("ranked_serp_element", {}).get("serp_item", {}).get("rank_group", 100)

            if url:
                url_keywords[url].append({
                    "keyword": keyword,
                    "position": position,
                })

        # Find pages with many keyword rankings (content hubs)
        content_hubs = [
            {"url": url, "keyword_count": len(kws)}
            for url, kws in url_keywords.items()
            if len(kws) >= 5
        ]

        if content_hubs:
            content_hubs.sort(key=lambda x: x["keyword_count"], reverse=True)

            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.CONTENT_GAPS,
                issue_type="content_hubs",
                title=f"{len(content_hubs)} pages ranking for 5+ keywords",
                description="These pages are ranking for multiple keywords and may be content hubs "
                           "or comprehensive guides that are performing well.",
                count=len(content_hubs),
                recommendation="Study these successful pages. Consider expanding them further and "
                              "using similar strategies for other topics.",
                additional_data={"content_hubs": content_hubs[:10]},
            )

        # Check for potential cannibalization (multiple URLs for same keyword intent)
        # This would require more sophisticated analysis
        # Placeholder for future enhancement

    # =========================================================================
    # SUMMARY METHODS
    # =========================================================================

    def get_competitor_summary(self) -> dict:
        """Get summary statistics of competitive analysis.

        Returns:
            Dictionary with key metrics
        """
        top_3_count = sum(
            1 for kw in self.data.ranked_keywords
            if kw.get("ranked_serp_element", {}).get("serp_item", {}).get("rank_group", 100) <= 3
        )

        return {
            "target_domain": self.data.target_domain,
            "total_keywords": self.data.total_keywords,
            "top_3_keywords": top_3_count,
            "competitor_count": len(self.data.competitors),
            "top_competitor": self.data.competitors[0].get("domain") if self.data.competitors else None,
            "issues_found": len(self.issues),
        }
