"""Report Generator.

Generates audit reports in Markdown, HTML, and CSV formats.
"""

import csv
import io
from datetime import datetime
from typing import Optional

from models.audit_result import AuditResult, AuditIssue, Severity


class ReportGenerator:
    """Generates SEO audit reports in multiple formats."""

    def __init__(self, audit_result: AuditResult):
        """Initialize with audit results.

        Args:
            audit_result: Complete audit result object
        """
        self.result = audit_result

    def generate_markdown(self) -> str:
        """Generate a full audit report in Markdown format.

        Returns:
            Markdown string
        """
        md = []

        # Header
        md.append("# SEO Audit Report")
        md.append(f"\n**Domain:** {self.result.summary.domain or 'Unknown'}")
        md.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        md.append(f"**Total URLs Analyzed:** {self.result.summary.total_urls:,}")
        md.append("")

        # Health Score
        md.append("## Site Health Score")
        md.append("")
        md.append(f"**Score: {self.result.summary.health_score}/100 ({self.result.summary.health_grade})**")
        md.append("")
        md.append("| Severity | Count |")
        md.append("|----------|-------|")
        md.append(f"| Critical | {self.result.summary.critical_count} |")
        md.append(f"| High | {self.result.summary.high_count} |")
        md.append(f"| Medium | {self.result.summary.medium_count} |")
        md.append(f"| Low | {self.result.summary.low_count} |")
        md.append(f"| Insights | {self.result.summary.insight_count} |")
        md.append("")

        # Data sources
        md.append("### Data Sources")
        md.append(f"- Google Search Console: {'Yes' if self.result.summary.has_gsc_data else 'No'}")
        md.append(f"- PageSpeed Insights: {'Yes' if self.result.summary.has_pagespeed_data else 'No'}")
        md.append(f"- Google Analytics: {'Yes' if self.result.summary.has_ga4_data else 'No'}")
        md.append("")

        # Executive Summary (if available)
        if self.result.executive_summary:
            md.append("## Executive Summary")
            md.append("")
            md.append(self.result.executive_summary)
            md.append("")

        # Top Issues
        md.append("## Top Priority Issues")
        md.append("")
        top_issues = self.result.get_top_issues(10)
        for i, issue in enumerate(top_issues, 1):
            md.append(f"### {i}. {issue.severity.emoji} {issue.title}")
            md.append(f"**Severity:** {issue.severity.value.title()} | **Affected:** {issue.count} URLs")
            md.append("")
            md.append(issue.description)
            md.append("")
            if issue.recommendation:
                md.append(f"**Recommendation:** {issue.recommendation}")
                md.append("")
            if issue.example_url:
                md.append(f"**Example URL:** `{issue.example_url}`")
                md.append("")

        # Quick Wins
        quick_wins = self.result.get_quick_wins(5)
        if quick_wins:
            md.append("## Quick Wins")
            md.append("")
            md.append("High-impact issues that affect a small number of URLs (easy to fix):")
            md.append("")
            for issue in quick_wins:
                md.append(f"- **{issue.title}** ({issue.count} URLs) - {issue.category.display_name}")

            md.append("")

        # Technical SEO Issues
        if self.result.technical_issues:
            md.append("## Technical SEO Issues")
            md.append("")
            md.extend(self._format_issue_section(self.result.technical_issues))

            if self.result.technical_analysis:
                md.append("### AI Analysis")
                md.append("")
                md.append(self.result.technical_analysis)
                md.append("")

        # On-Page SEO Issues
        if self.result.onpage_issues:
            md.append("## On-Page SEO Issues")
            md.append("")
            md.extend(self._format_issue_section(self.result.onpage_issues))

            if self.result.onpage_analysis:
                md.append("### AI Analysis")
                md.append("")
                md.append(self.result.onpage_analysis)
                md.append("")

        # Backlink Analysis
        if self.result.backlink_issues:
            md.append("## Backlink Analysis")
            md.append("")
            md.extend(self._format_issue_section(self.result.backlink_issues))

            if self.result.backlink_analysis:
                md.append("### AI Analysis")
                md.append("")
                md.append(self.result.backlink_analysis)
                md.append("")

        # Competitor Analysis
        if self.result.competitor_issues:
            md.append("## Competitor Analysis")
            md.append("")
            md.extend(self._format_issue_section(self.result.competitor_issues))

            if self.result.competitor_analysis:
                md.append("### AI Analysis")
                md.append("")
                md.append(self.result.competitor_analysis)
                md.append("")

        # Footer
        md.append("---")
        md.append("")
        md.append("*Generated by Ultimate SEO Auditor*")

        return "\n".join(md)

    def _format_issue_section(self, issues: list[AuditIssue]) -> list[str]:
        """Format a list of issues for the report.

        Args:
            issues: List of issues to format

        Returns:
            List of markdown lines
        """
        lines = []

        # Group by severity
        severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INSIGHT]

        for severity in severity_order:
            severity_issues = [i for i in issues if i.severity == severity]
            if not severity_issues:
                continue

            lines.append(f"### {severity.emoji} {severity.value.title()} ({len(severity_issues)})")
            lines.append("")

            for issue in severity_issues:
                lines.append(f"**{issue.title}**")
                lines.append(f"- Category: {issue.category.display_name}")
                lines.append(f"- Affected: {issue.count} URLs")
                if issue.recommendation:
                    lines.append(f"- Fix: {issue.recommendation}")
                lines.append("")

        return lines

    def generate_html(self) -> str:
        """Generate an HTML report.

        Returns:
            HTML string
        """
        # Convert markdown to basic HTML
        md_content = self.generate_markdown()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Audit Report - {self.result.summary.domain or 'Unknown'}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ color: #1a1a2e; border-bottom: 2px solid #4a90d9; padding-bottom: 10px; }}
        h2 {{ color: #16213e; margin-top: 30px; }}
        h3 {{ color: #0f3460; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
        .critical {{ color: #dc3545; font-weight: bold; }}
        .high {{ color: #fd7e14; font-weight: bold; }}
        .medium {{ color: #ffc107; }}
        .low {{ color: #17a2b8; }}
        .score-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }}
        .score-box h2 {{ color: white; margin: 0; font-size: 3em; }}
        .issue-card {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            background: #fafafa;
        }}
        .issue-card h4 {{ margin-top: 0; }}
    </style>
</head>
<body>
    <h1>SEO Audit Report</h1>
    <p><strong>Domain:</strong> {self.result.summary.domain or 'Unknown'}</p>
    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <p><strong>URLs Analyzed:</strong> {self.result.summary.total_urls:,}</p>

    <div class="score-box">
        <h2>{self.result.summary.health_score}</h2>
        <p>Health Score (Grade: {self.result.summary.health_grade})</p>
    </div>

    <h2>Issue Summary</h2>
    <table>
        <tr><th>Severity</th><th>Count</th></tr>
        <tr><td class="critical">Critical</td><td>{self.result.summary.critical_count}</td></tr>
        <tr><td class="high">High</td><td>{self.result.summary.high_count}</td></tr>
        <tr><td class="medium">Medium</td><td>{self.result.summary.medium_count}</td></tr>
        <tr><td class="low">Low</td><td>{self.result.summary.low_count}</td></tr>
        <tr><td>Insights</td><td>{self.result.summary.insight_count}</td></tr>
    </table>

    <h2>Top Priority Issues</h2>
"""

        # Add top issues
        for i, issue in enumerate(self.result.get_top_issues(10), 1):
            severity_class = issue.severity.value
            html += f"""
    <div class="issue-card">
        <h4>{i}. <span class="{severity_class}">[{issue.severity.value.upper()}]</span> {issue.title}</h4>
        <p><strong>Category:</strong> {issue.category.display_name} | <strong>Affected:</strong> {issue.count} URLs</p>
        <p>{issue.description}</p>
        {f'<p><strong>Recommendation:</strong> {issue.recommendation}</p>' if issue.recommendation else ''}
    </div>
"""

        # Add AI analysis sections if available
        if self.result.executive_summary:
            html += f"""
    <h2>Executive Summary</h2>
    <div class="issue-card">
        <p>{self.result.executive_summary.replace(chr(10), '<br>')}</p>
    </div>
"""

        html += """
    <hr>
    <p><em>Generated by Ultimate SEO Auditor</em></p>
</body>
</html>"""

        return html

    def generate_csv(self) -> str:
        """Generate a CSV export of all issues.

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Severity",
            "Category",
            "Issue Type",
            "Title",
            "Description",
            "Count",
            "Recommendation",
            "Impact",
            "Example URL"
        ])

        # All issues
        for issue in self.result.all_issues:
            writer.writerow([
                issue.severity.value,
                issue.category.display_name,
                issue.issue_type,
                issue.title,
                issue.description,
                issue.count,
                issue.recommendation or "",
                issue.impact or "",
                issue.example_url or ""
            ])

        return output.getvalue()

    def generate_issues_csv(self, issues: list[AuditIssue]) -> str:
        """Generate a CSV export of specific issues with affected URLs.

        Args:
            issues: List of issues to export

        Returns:
            CSV string with one row per affected URL
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Severity",
            "Category",
            "Issue Type",
            "Title",
            "URL"
        ])

        # One row per URL
        for issue in issues:
            for url in issue.affected_urls:
                writer.writerow([
                    issue.severity.value,
                    issue.category.display_name,
                    issue.issue_type,
                    issue.title,
                    url
                ])

        return output.getvalue()

    def get_summary_dict(self) -> dict:
        """Get a dictionary summary for JSON export.

        Returns:
            Dictionary with all summary data
        """
        return {
            "domain": self.result.summary.domain,
            "audit_date": datetime.now().isoformat(),
            "total_urls": self.result.summary.total_urls,
            "health_score": self.result.summary.health_score,
            "health_grade": self.result.summary.health_grade,
            "issue_counts": {
                "critical": self.result.summary.critical_count,
                "high": self.result.summary.high_count,
                "medium": self.result.summary.medium_count,
                "low": self.result.summary.low_count,
                "insight": self.result.summary.insight_count,
                "total": self.result.summary.total_issues,
            },
            "data_sources": {
                "gsc": self.result.summary.has_gsc_data,
                "pagespeed": self.result.summary.has_pagespeed_data,
                "ga4": self.result.summary.has_ga4_data,
            },
            "top_issues": [
                {
                    "title": i.title,
                    "severity": i.severity.value,
                    "count": i.count,
                    "category": i.category.display_name,
                }
                for i in self.result.get_top_issues(10)
            ],
        }
