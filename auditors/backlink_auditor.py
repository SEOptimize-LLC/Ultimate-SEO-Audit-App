"""Backlink Auditor.

Analyzes backlink profile, anchor text distribution, referring domains,
and identifies toxic or low-quality link patterns.

Based on Backlink Agent knowledge base.
"""

from typing import Optional
from collections import Counter

from models.audit_result import AuditIssue, Severity, AuditCategory
from services.dataforseo_client import BacklinkData


class BacklinkAuditor:
    """Auditor for backlink profile analysis.

    Checks include:
    - Anchor text distribution
    - Referring domain quality
    - Toxic link patterns
    - Link diversity
    - Dofollow/nofollow ratio
    """

    def __init__(self, backlink_data: BacklinkData, domain: str):
        """Initialize the auditor with backlink data.

        Args:
            backlink_data: BacklinkData from DataForSEO
            domain: Target domain being analyzed
        """
        self.data = backlink_data
        self.domain = domain
        self.issues: list[AuditIssue] = []

    def get_audit_type(self) -> str:
        return "backlink"

    def run_audit(self) -> list[AuditIssue]:
        """Run all backlink analysis checks."""
        self.issues = []

        # Anchor text analysis
        self._check_anchor_text_distribution()
        self._check_exact_match_anchors()
        self._check_generic_anchors()

        # Referring domain analysis
        self._check_domain_diversity()
        self._check_low_quality_domains()

        # Link pattern analysis
        self._check_dofollow_ratio()
        self._check_link_velocity_patterns()

        # Toxic signals
        self._check_potential_toxic_patterns()

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
    # ANCHOR TEXT ANALYSIS
    # =========================================================================

    def _check_anchor_text_distribution(self) -> None:
        """Analyze overall anchor text distribution."""
        if not self.data.anchors:
            return

        # Categorize anchors
        categories = self._categorize_anchors()
        total_links = sum(a.get("backlinks", 0) for a in self.data.anchors)

        if total_links == 0:
            return

        # Calculate percentages
        distribution = {}
        for cat, count in categories.items():
            distribution[cat] = round((count / total_links) * 100, 1)

        # Check for issues
        exact_match_pct = distribution.get("exact_match", 0)
        branded_pct = distribution.get("branded", 0)
        generic_pct = distribution.get("generic", 0)

        # Report distribution as insight
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.ANCHOR_TEXT,
            issue_type="anchor_distribution",
            title="Anchor text distribution analysis",
            description=f"Analyzed anchor text across {total_links} backlinks. "
                       f"Distribution: Branded: {branded_pct}%, "
                       f"Exact Match: {exact_match_pct}%, Generic: {generic_pct}%",
            count=len(self.data.anchors),
            additional_data={"distribution": distribution},
        )

    def _categorize_anchors(self) -> dict:
        """Categorize anchors by type.

        Returns:
            Dictionary with category counts
        """
        categories = {
            "branded": 0,
            "url": 0,
            "generic": 0,
            "partial_match": 0,
            "exact_match": 0,
            "other": 0,
        }

        generic_terms = {
            "click here", "here", "read more", "learn more", "website",
            "link", "this", "site", "page", "more", "visit", "go"
        }

        domain_parts = self.domain.lower().replace("www.", "").split(".")
        brand_terms = set(domain_parts[0].split("-"))  # Handle hyphenated domains

        for anchor_item in self.data.anchors:
            anchor = anchor_item.get("anchor", "").lower().strip()
            count = anchor_item.get("backlinks", 1)

            if not anchor:
                categories["other"] += count
                continue

            # Check category
            if any(term in anchor for term in brand_terms):
                categories["branded"] += count
            elif anchor.startswith("http") or anchor.startswith("www"):
                categories["url"] += count
            elif anchor in generic_terms or any(g in anchor for g in generic_terms):
                categories["generic"] += count
            else:
                # Could be exact or partial match - simplified check
                categories["partial_match"] += count

        return categories

    def _check_exact_match_anchors(self) -> None:
        """Check for over-optimized exact match anchors."""
        if not self.data.anchors:
            return

        total_links = sum(a.get("backlinks", 0) for a in self.data.anchors)
        if total_links == 0:
            return

        # Find potential exact match keyword anchors (non-branded, non-generic, non-url)
        generic_terms = {"click here", "here", "read more", "learn more", "website", "link"}
        suspicious_anchors = []

        for anchor_item in self.data.anchors:
            anchor = anchor_item.get("anchor", "").lower().strip()
            count = anchor_item.get("backlinks", 0)
            pct = (count / total_links) * 100

            # Skip if branded, url, or generic
            if (anchor.startswith("http") or
                anchor.startswith("www") or
                any(g in anchor for g in generic_terms)):
                continue

            # Flag if same anchor used many times (>5% of links)
            if pct > 5 and count > 10:
                suspicious_anchors.append({
                    "anchor": anchor,
                    "count": count,
                    "percentage": round(pct, 1)
                })

        if suspicious_anchors:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.ANCHOR_TEXT,
                issue_type="potential_over_optimization",
                title=f"{len(suspicious_anchors)} anchor texts may be over-optimized",
                description="Found anchor texts that appear frequently (>5% of links) and may "
                           "indicate over-optimization or unnatural link building.",
                count=len(suspicious_anchors),
                recommendation="Diversify anchor text. Natural profiles have varied anchors. "
                              "If these are from link building, vary the anchor text used.",
                impact="Over-optimized anchors can trigger algorithmic penalties for the target keywords.",
                additional_data={"suspicious_anchors": suspicious_anchors[:10]},
            )

    def _check_generic_anchors(self) -> None:
        """Check for excessive generic anchor text."""
        if not self.data.anchors:
            return

        generic_terms = {"click here", "here", "read more", "learn more", "website", "link", "this"}
        total_links = sum(a.get("backlinks", 0) for a in self.data.anchors)

        if total_links == 0:
            return

        generic_count = sum(
            a.get("backlinks", 0) for a in self.data.anchors
            if a.get("anchor", "").lower().strip() in generic_terms
        )

        generic_pct = (generic_count / total_links) * 100

        if generic_pct > 30:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.ANCHOR_TEXT,
                issue_type="high_generic_anchors",
                title=f"{generic_pct:.1f}% of anchors are generic",
                description=f"Found {generic_count} links ({generic_pct:.1f}%) using generic anchor text "
                           "like 'click here' or 'read more'.",
                count=generic_count,
                recommendation="While not harmful, descriptive anchors provide better context signals. "
                              "Focus future link building on more descriptive anchors.",
                impact="Generic anchors don't provide topical signals to search engines.",
            )

    # =========================================================================
    # REFERRING DOMAIN ANALYSIS
    # =========================================================================

    def _check_domain_diversity(self) -> None:
        """Check referring domain to backlink ratio."""
        total_links = self.data.total_backlinks
        total_domains = self.data.referring_domains

        if total_links == 0 or total_domains == 0:
            return

        ratio = total_links / total_domains

        if ratio > 20:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.REFERRING_DOMAINS,
                issue_type="low_domain_diversity",
                title=f"Low referring domain diversity (ratio: {ratio:.1f}:1)",
                description=f"Have {total_links} backlinks from only {total_domains} domains "
                           f"(average {ratio:.1f} links per domain). High ratios indicate "
                           "many links from few sources.",
                count=total_domains,
                recommendation="Focus on acquiring links from new, unique domains rather than "
                              "multiple links from existing sources.",
                impact="Diverse referring domains are a stronger signal than many links from few sites.",
            )
        else:
            # Healthy diversity - report as insight
            self.create_issue(
                severity=Severity.INSIGHT,
                category=AuditCategory.REFERRING_DOMAINS,
                issue_type="domain_diversity_good",
                title=f"Good referring domain diversity (ratio: {ratio:.1f}:1)",
                description=f"Have {total_links} backlinks from {total_domains} unique domains.",
                count=total_domains,
            )

    def _check_low_quality_domains(self) -> None:
        """Check for links from potentially low-quality domains."""
        if not self.data.referring_domain_list:
            return

        low_quality_count = 0
        low_quality_domains = []

        for domain_item in self.data.referring_domain_list:
            rank = domain_item.get("rank", 0)

            # Very low rank domains (rank is inverse - higher is worse in some APIs)
            # DataForSEO rank is 0-1000, lower is better
            if rank is not None and rank < 10:
                low_quality_count += 1
                low_quality_domains.append(domain_item.get("domain", "unknown"))

        if low_quality_count > 10:
            pct = (low_quality_count / len(self.data.referring_domain_list)) * 100
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.REFERRING_DOMAINS,
                issue_type="low_quality_referring_domains",
                title=f"{low_quality_count} potentially low-quality referring domains",
                description=f"Found {low_quality_count} referring domains ({pct:.1f}%) with very low "
                           "authority scores. These may provide minimal value.",
                count=low_quality_count,
                recommendation="Review these domains. If they appear spammy, consider disavowing. "
                              "Focus link building on higher-authority sites.",
                impact="Links from low-quality sites provide less value and could be risky in excess.",
                additional_data={"sample_domains": low_quality_domains[:20]},
            )

    # =========================================================================
    # LINK PATTERN ANALYSIS
    # =========================================================================

    def _check_dofollow_ratio(self) -> None:
        """Check the ratio of dofollow to nofollow links."""
        total = self.data.dofollow_backlinks + self.data.nofollow_backlinks
        if total == 0:
            return

        dofollow_pct = (self.data.dofollow_backlinks / total) * 100

        if dofollow_pct > 95:
            self.create_issue(
                severity=Severity.LOW,
                category=AuditCategory.BACKLINKS,
                issue_type="high_dofollow_ratio",
                title=f"{dofollow_pct:.1f}% of backlinks are dofollow",
                description="Unusually high percentage of dofollow links. Natural profiles typically "
                           "have 60-80% dofollow.",
                count=self.data.dofollow_backlinks,
                recommendation="This may be natural for some sites, but review if acquiring mostly dofollow "
                              "links through link building.",
                impact="Extremely high dofollow ratios can appear unnatural, though this is rarely an issue alone.",
            )
        elif dofollow_pct < 40:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.BACKLINKS,
                issue_type="low_dofollow_ratio",
                title=f"Only {dofollow_pct:.1f}% of backlinks are dofollow",
                description="Low percentage of dofollow links means most links aren't passing PageRank.",
                count=self.data.dofollow_backlinks,
                recommendation="Focus link building efforts on earning dofollow editorial links from "
                              "quality publications.",
                impact="Nofollow links don't directly pass PageRank, limiting their ranking impact.",
            )

    def _check_link_velocity_patterns(self) -> None:
        """Check for unusual link acquisition patterns.

        Note: This would require historical data not available in single API call.
        Placeholder for when time-series data is available.
        """
        # Would need historical data to properly analyze
        # For now, just report current state
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.BACKLINKS,
            issue_type="backlink_summary",
            title=f"Backlink profile: {self.data.total_backlinks} links from {self.data.referring_domains} domains",
            description=f"Current backlink profile summary. Domain rank: {self.data.domain_rank or 'N/A'}",
            count=self.data.total_backlinks,
        )

    # =========================================================================
    # TOXIC PATTERN DETECTION
    # =========================================================================

    def _check_potential_toxic_patterns(self) -> None:
        """Check for patterns that may indicate toxic links."""
        if not self.data.backlinks:
            return

        # Check for suspicious patterns
        suspicious_signals = {
            "foreign_language": 0,
            "low_rank": 0,
            "sitewide": 0,
        }

        for link in self.data.backlinks:
            # Check for sitewide links (same domain, many pages)
            # This is simplified - real detection would need more data
            page_from_rank = link.get("page_from_rank", 100)
            domain_from_rank = link.get("domain_from_rank", 100)

            if domain_from_rank < 5:
                suspicious_signals["low_rank"] += 1

        # Report if significant issues found
        total_suspicious = sum(suspicious_signals.values())
        if total_suspicious > len(self.data.backlinks) * 0.2:  # >20% suspicious
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.BACKLINKS,
                issue_type="potential_toxic_links",
                title=f"{total_suspicious} potentially toxic link signals detected",
                description="Found backlinks with patterns that may indicate low quality or toxic links. "
                           f"Breakdown: Low rank domains: {suspicious_signals['low_rank']}",
                count=total_suspicious,
                recommendation="Review flagged links manually. Consider disavowing confirmed toxic links. "
                              "Document patterns for future monitoring.",
                impact="Toxic links can trigger manual actions or algorithmic penalties.",
                additional_data={"signal_breakdown": suspicious_signals},
            )

    # =========================================================================
    # SUMMARY METHODS
    # =========================================================================

    def get_backlink_summary(self) -> dict:
        """Get summary statistics of backlink profile.

        Returns:
            Dictionary with key metrics
        """
        return {
            "total_backlinks": self.data.total_backlinks,
            "referring_domains": self.data.referring_domains,
            "dofollow_backlinks": self.data.dofollow_backlinks,
            "nofollow_backlinks": self.data.nofollow_backlinks,
            "domain_rank": self.data.domain_rank,
            "issues_found": len(self.issues),
            "critical_issues": sum(1 for i in self.issues if i.severity == Severity.CRITICAL),
            "high_issues": sum(1 for i in self.issues if i.severity == Severity.HIGH),
        }
