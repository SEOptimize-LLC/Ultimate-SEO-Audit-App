"""Base auditor abstract class.

Provides common functionality for all SEO auditors.
"""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

from models.audit_result import AuditIssue, Severity, AuditCategory


class BaseAuditor(ABC):
    """Abstract base class for SEO auditors.

    All specific auditors (Technical, OnPage, Backlink, Competitor)
    inherit from this class.
    """

    def __init__(self, df: pd.DataFrame):
        """Initialize the auditor with crawl data.

        Args:
            df: DataFrame from Screaming Frog export
        """
        self.df = df
        self.issues: list[AuditIssue] = []

    @abstractmethod
    def run_audit(self) -> list[AuditIssue]:
        """Run all audit checks and return issues.

        Returns:
            List of AuditIssue objects
        """
        pass

    @abstractmethod
    def get_audit_type(self) -> str:
        """Return the audit type identifier.

        Returns:
            String identifier (e.g., 'technical', 'onpage')
        """
        pass

    def create_issue(
        self,
        severity: Severity,
        category: AuditCategory,
        issue_type: str,
        title: str,
        description: str,
        affected_urls: Optional[list[str]] = None,
        count: Optional[int] = None,
        recommendation: Optional[str] = None,
        impact: Optional[str] = None,
        additional_data: Optional[dict] = None,
    ) -> AuditIssue:
        """Create an AuditIssue and add it to the issues list.

        Args:
            severity: Issue severity level
            category: Issue category
            issue_type: Specific issue identifier
            title: Short issue title
            description: Detailed description
            affected_urls: List of affected URLs
            count: Number of affected items (auto-calculated if urls provided)
            recommendation: How to fix the issue
            impact: Why this issue matters
            additional_data: Extra context data

        Returns:
            Created AuditIssue object
        """
        if affected_urls is None:
            affected_urls = []
        if additional_data is None:
            additional_data = {}

        issue = AuditIssue(
            severity=severity,
            category=category,
            issue_type=issue_type,
            title=title,
            description=description,
            affected_urls=affected_urls,
            count=count if count is not None else len(affected_urls),
            recommendation=recommendation,
            impact=impact,
            additional_data=additional_data,
        )

        self.issues.append(issue)
        return issue

    def has_column(self, column: str) -> bool:
        """Check if a column exists in the DataFrame.

        Args:
            column: Column name to check

        Returns:
            True if column exists
        """
        return column in self.df.columns

    def has_columns(self, columns: list[str]) -> bool:
        """Check if all specified columns exist.

        Args:
            columns: List of column names to check

        Returns:
            True if all columns exist
        """
        return all(self.has_column(col) for col in columns)

    def get_column_values(self, column: str, dropna: bool = True) -> pd.Series:
        """Get values from a column.

        Args:
            column: Column name
            dropna: Whether to drop NA values

        Returns:
            Series of values
        """
        if not self.has_column(column):
            return pd.Series(dtype=object)

        values = self.df[column]
        if dropna:
            values = values.dropna()
        return values

    def filter_by_condition(
        self,
        condition: pd.Series,
        url_column: str = "url",
        limit: int = 100
    ) -> list[str]:
        """Filter DataFrame and return affected URLs.

        Args:
            condition: Boolean Series for filtering
            url_column: Column containing URLs
            limit: Maximum number of URLs to return

        Returns:
            List of affected URLs
        """
        if not self.has_column(url_column):
            return []

        filtered = self.df.loc[condition, url_column]
        return filtered.head(limit).tolist()

    def count_by_condition(self, condition: pd.Series) -> int:
        """Count rows matching a condition.

        Args:
            condition: Boolean Series

        Returns:
            Count of matching rows
        """
        return condition.sum()

    def get_html_pages(self) -> pd.DataFrame:
        """Get only HTML pages from the DataFrame.

        Returns:
            Filtered DataFrame with HTML pages only
        """
        if self.has_column("content_type"):
            return self.df[self.df["content_type"].str.contains("text/html", na=False, case=False)]
        return self.df

    def get_indexable_pages(self) -> pd.DataFrame:
        """Get only indexable pages.

        Returns:
            Filtered DataFrame with indexable pages only
        """
        if self.has_column("indexability"):
            return self.df[self.df["indexability"].str.lower() == "indexable"]
        return self.df

    def get_2xx_pages(self) -> pd.DataFrame:
        """Get pages with 2xx status codes.

        Returns:
            Filtered DataFrame with 2xx pages
        """
        if self.has_column("status_code"):
            return self.df[(self.df["status_code"] >= 200) & (self.df["status_code"] < 300)]
        return self.df

    def clear_issues(self) -> None:
        """Clear all recorded issues."""
        self.issues = []

    def get_issue_summary(self) -> dict:
        """Get summary of issues by severity.

        Returns:
            Dictionary with counts by severity
        """
        summary = {s.value: 0 for s in Severity}
        for issue in self.issues:
            summary[issue.severity.value] += 1
        summary["total"] = len(self.issues)
        return summary


# Helper functions for common checks

def is_empty_or_missing(value) -> bool:
    """Check if a value is empty, missing, or NA.

    Args:
        value: Value to check

    Returns:
        True if empty/missing
    """
    if pd.isna(value):
        return True
    if isinstance(value, str):
        return value.strip() == "" or value.lower() == "nan"
    return False


def is_duplicate(series: pd.Series, value) -> bool:
    """Check if a value appears more than once in a series.

    Args:
        series: Series to check
        value: Value to look for

    Returns:
        True if value appears multiple times
    """
    if is_empty_or_missing(value):
        return False
    return (series == value).sum() > 1


def get_duplicates(series: pd.Series, min_count: int = 2) -> pd.Series:
    """Get values that appear multiple times.

    Args:
        series: Series to analyze
        min_count: Minimum occurrences to be considered duplicate

    Returns:
        Series of duplicate values with counts
    """
    # Remove empty values
    cleaned = series[~series.apply(is_empty_or_missing)]
    counts = cleaned.value_counts()
    return counts[counts >= min_count]


def check_length(value, min_len: int = 0, max_len: int = float("inf")) -> str:
    """Check if a value's length is within bounds.

    Args:
        value: Value to check
        min_len: Minimum length
        max_len: Maximum length

    Returns:
        'short', 'long', or 'ok'
    """
    if is_empty_or_missing(value):
        return "missing"

    length = len(str(value))
    if length < min_len:
        return "short"
    if length > max_len:
        return "long"
    return "ok"
