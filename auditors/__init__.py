"""Auditors module for Ultimate SEO Auditor.

Contains specialized SEO audit engines.
"""

from .base_auditor import BaseAuditor
from .technical_auditor import TechnicalAuditor
from .javascript_rendering_auditor import JavaScriptRenderingAuditor
from .cannibalization_auditor import CannibalizationAuditor
from .url_structure_auditor import URLStructureAuditor
from .ecommerce_patterns_auditor import EcommercePatternsAuditor
from .local_seo_auditor import LocalSEOAuditor
from .mobile_first_auditor import MobileFirstAuditor
from .content_pruning_auditor import ContentPruningAuditor
from .discover_auditor import DiscoverAuditor
from .onpage_auditor import OnPageAuditor
from .backlink_auditor import BacklinkAuditor
from .competitor_auditor import CompetitorAuditor

# Leak-grounded auditors (require expanded input stack)
from .anchor_quality_auditor import AnchorQualityAuditor
from .date_freshness_auditor import DateFreshnessAuditor
from .topical_authority_auditor import TopicalAuthorityAuditor
from .click_signal_auditor import ClickSignalAuditor
from .query_count_auditor import QueryCountAuditor
from .backlink_profile_auditor import BacklinkProfileAuditor

__all__ = [
    "BaseAuditor",
    "TechnicalAuditor",
    "JavaScriptRenderingAuditor",
    "CannibalizationAuditor",
    "URLStructureAuditor",
    "EcommercePatternsAuditor",
    "LocalSEOAuditor",
    "MobileFirstAuditor",
    "ContentPruningAuditor",
    "DiscoverAuditor",
    "OnPageAuditor",
    "BacklinkAuditor",
    "CompetitorAuditor",
    # Leak-grounded
    "AnchorQualityAuditor",
    "DateFreshnessAuditor",
    "TopicalAuthorityAuditor",
    "ClickSignalAuditor",
    "QueryCountAuditor",
    "BacklinkProfileAuditor",
]
