"""Models module for Ultimate SEO Auditor.

Contains data classes and type definitions.
"""

from .audit_result import (
    Severity,
    AuditIssue,
    AuditSummary,
    AuditCategory,
)

__all__ = [
    "Severity",
    "AuditIssue",
    "AuditSummary",
    "AuditCategory",
]
