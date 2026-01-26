"""Data models for SEO audit results.

Defines severity levels, issue types, and audit result structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class Severity(Enum):
    """Issue severity levels based on SEO impact."""

    CRITICAL = "critical"  # Blocks crawling, indexing, or causes major ranking damage
    HIGH = "high"          # Significantly degrades ranking potential or UX
    MEDIUM = "medium"      # Reduces optimization but doesn't block functionality
    LOW = "low"            # Minor issues or informational
    INSIGHT = "insight"    # Informational only, no action needed

    @property
    def priority(self) -> int:
        """Return numeric priority (lower = more urgent)."""
        priorities = {
            Severity.CRITICAL: 1,
            Severity.HIGH: 2,
            Severity.MEDIUM: 3,
            Severity.LOW: 4,
            Severity.INSIGHT: 5,
        }
        return priorities[self]

    @property
    def color(self) -> str:
        """Return color for UI display."""
        colors = {
            Severity.CRITICAL: "#dc3545",  # Red
            Severity.HIGH: "#fd7e14",      # Orange
            Severity.MEDIUM: "#ffc107",    # Yellow
            Severity.LOW: "#17a2b8",       # Cyan
            Severity.INSIGHT: "#6c757d",   # Gray
        }
        return colors[self]

    @property
    def emoji(self) -> str:
        """Return emoji for display."""
        emojis = {
            Severity.CRITICAL: "🔴",
            Severity.HIGH: "🟠",
            Severity.MEDIUM: "🟡",
            Severity.LOW: "🔵",
            Severity.INSIGHT: "⚪",
        }
        return emojis[self]


class AuditCategory(Enum):
    """Categories of SEO audit checks."""

    # Technical SEO
    INDEXABILITY = "indexability"
    CRAWLABILITY = "crawlability"
    REDIRECTS = "redirects"
    PERFORMANCE = "performance"
    SECURITY = "security"

    # On-Page SEO
    TITLE_TAGS = "title_tags"
    META_DESCRIPTIONS = "meta_descriptions"
    HEADINGS = "headings"
    CONTENT = "content"
    INTERNAL_LINKS = "internal_links"
    IMAGES = "images"

    # Off-Page
    BACKLINKS = "backlinks"
    ANCHOR_TEXT = "anchor_text"
    REFERRING_DOMAINS = "referring_domains"

    # Competitive
    KEYWORD_GAPS = "keyword_gaps"
    CONTENT_GAPS = "content_gaps"
    COMPETITIVE_POSITION = "competitive_position"

    @property
    def display_name(self) -> str:
        """Return human-readable category name."""
        names = {
            AuditCategory.INDEXABILITY: "Indexability",
            AuditCategory.CRAWLABILITY: "Crawlability",
            AuditCategory.REDIRECTS: "Redirects",
            AuditCategory.PERFORMANCE: "Performance",
            AuditCategory.SECURITY: "Security",
            AuditCategory.TITLE_TAGS: "Title Tags",
            AuditCategory.META_DESCRIPTIONS: "Meta Descriptions",
            AuditCategory.HEADINGS: "Headings",
            AuditCategory.CONTENT: "Content",
            AuditCategory.INTERNAL_LINKS: "Internal Links",
            AuditCategory.IMAGES: "Images",
            AuditCategory.BACKLINKS: "Backlinks",
            AuditCategory.ANCHOR_TEXT: "Anchor Text",
            AuditCategory.REFERRING_DOMAINS: "Referring Domains",
            AuditCategory.KEYWORD_GAPS: "Keyword Gaps",
            AuditCategory.CONTENT_GAPS: "Content Gaps",
            AuditCategory.COMPETITIVE_POSITION: "Competitive Position",
        }
        return names[self]

    @property
    def audit_type(self) -> str:
        """Return the parent audit type."""
        technical = [
            AuditCategory.INDEXABILITY,
            AuditCategory.CRAWLABILITY,
            AuditCategory.REDIRECTS,
            AuditCategory.PERFORMANCE,
            AuditCategory.SECURITY,
        ]
        onpage = [
            AuditCategory.TITLE_TAGS,
            AuditCategory.META_DESCRIPTIONS,
            AuditCategory.HEADINGS,
            AuditCategory.CONTENT,
            AuditCategory.INTERNAL_LINKS,
            AuditCategory.IMAGES,
        ]
        backlink = [
            AuditCategory.BACKLINKS,
            AuditCategory.ANCHOR_TEXT,
            AuditCategory.REFERRING_DOMAINS,
        ]
        competitive = [
            AuditCategory.KEYWORD_GAPS,
            AuditCategory.CONTENT_GAPS,
            AuditCategory.COMPETITIVE_POSITION,
        ]

        if self in technical:
            return "technical"
        elif self in onpage:
            return "onpage"
        elif self in backlink:
            return "backlink"
        elif self in competitive:
            return "competitive"
        return "other"


@dataclass
class AuditIssue:
    """Represents a single SEO audit issue."""

    severity: Severity
    category: AuditCategory
    issue_type: str                           # e.g., "missing_title", "redirect_chain"
    title: str                                 # Short description
    description: str                           # Detailed explanation
    affected_urls: list[str] = field(default_factory=list)
    count: int = 0                             # Number of affected items
    recommendation: Optional[str] = None       # How to fix
    impact: Optional[str] = None               # Why it matters
    example_url: Optional[str] = None          # Sample affected URL
    additional_data: dict = field(default_factory=dict)  # Extra context

    def __post_init__(self):
        """Set count from affected_urls if not provided."""
        if self.count == 0 and self.affected_urls:
            self.count = len(self.affected_urls)
        if self.example_url is None and self.affected_urls:
            self.example_url = self.affected_urls[0]

    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "issue_type": self.issue_type,
            "title": self.title,
            "description": self.description,
            "count": self.count,
            "recommendation": self.recommendation,
            "impact": self.impact,
            "example_url": self.example_url,
            "affected_urls": self.affected_urls[:100],  # Limit for export
        }


@dataclass
class AuditSummary:
    """Summary statistics for an audit."""

    total_urls: int = 0
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    insight_count: int = 0

    # Data availability flags
    has_gsc_data: bool = False
    has_pagespeed_data: bool = False
    has_ga4_data: bool = False

    # Timestamps
    crawl_date: Optional[datetime] = None
    audit_date: datetime = field(default_factory=datetime.now)

    # Domain info
    domain: Optional[str] = None

    @property
    def health_score(self) -> int:
        """Calculate overall site health score (0-100)."""
        if self.total_urls == 0:
            return 100

        # Weight issues by severity
        penalty = (
            (self.critical_count * 10) +
            (self.high_count * 5) +
            (self.medium_count * 2) +
            (self.low_count * 0.5)
        )

        # Normalize to URLs
        normalized_penalty = (penalty / self.total_urls) * 10

        # Cap penalty at 100
        score = max(0, 100 - min(100, normalized_penalty))
        return int(score)

    @property
    def health_grade(self) -> str:
        """Return letter grade based on health score."""
        score = self.health_score
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        return "F"

    def update_from_issues(self, issues: list[AuditIssue]) -> None:
        """Update counts from a list of issues."""
        self.total_issues = len(issues)
        self.critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        self.high_count = sum(1 for i in issues if i.severity == Severity.HIGH)
        self.medium_count = sum(1 for i in issues if i.severity == Severity.MEDIUM)
        self.low_count = sum(1 for i in issues if i.severity == Severity.LOW)
        self.insight_count = sum(1 for i in issues if i.severity == Severity.INSIGHT)

    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        return {
            "domain": self.domain,
            "total_urls": self.total_urls,
            "total_issues": self.total_issues,
            "health_score": self.health_score,
            "health_grade": self.health_grade,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "insight_count": self.insight_count,
            "has_gsc_data": self.has_gsc_data,
            "has_pagespeed_data": self.has_pagespeed_data,
            "has_ga4_data": self.has_ga4_data,
            "audit_date": self.audit_date.isoformat() if self.audit_date else None,
        }


@dataclass
class AuditResult:
    """Complete audit result containing all findings."""

    summary: AuditSummary
    technical_issues: list[AuditIssue] = field(default_factory=list)
    onpage_issues: list[AuditIssue] = field(default_factory=list)
    backlink_issues: list[AuditIssue] = field(default_factory=list)
    competitor_issues: list[AuditIssue] = field(default_factory=list)

    # LLM-generated analysis
    technical_analysis: Optional[str] = None
    onpage_analysis: Optional[str] = None
    backlink_analysis: Optional[str] = None
    competitor_analysis: Optional[str] = None
    executive_summary: Optional[str] = None

    @property
    def all_issues(self) -> list[AuditIssue]:
        """Return all issues combined."""
        return (
            self.technical_issues +
            self.onpage_issues +
            self.backlink_issues +
            self.competitor_issues
        )

    @property
    def issues_by_severity(self) -> dict[Severity, list[AuditIssue]]:
        """Group all issues by severity."""
        grouped = {s: [] for s in Severity}
        for issue in self.all_issues:
            grouped[issue.severity].append(issue)
        return grouped

    @property
    def issues_by_category(self) -> dict[AuditCategory, list[AuditIssue]]:
        """Group all issues by category."""
        grouped = {c: [] for c in AuditCategory}
        for issue in self.all_issues:
            grouped[issue.category].append(issue)
        return grouped

    def get_top_issues(self, limit: int = 10) -> list[AuditIssue]:
        """Get top issues sorted by severity and count."""
        sorted_issues = sorted(
            self.all_issues,
            key=lambda x: (x.severity.priority, -x.count)
        )
        return sorted_issues[:limit]

    def get_quick_wins(self, limit: int = 5) -> list[AuditIssue]:
        """Get high-impact, easy-to-fix issues."""
        # Quick wins: HIGH severity with small affected count
        # or CRITICAL with single URL
        quick_wins = [
            issue for issue in self.all_issues
            if (issue.severity in [Severity.CRITICAL, Severity.HIGH] and issue.count <= 10)
        ]
        sorted_wins = sorted(quick_wins, key=lambda x: (x.severity.priority, x.count))
        return sorted_wins[:limit]
