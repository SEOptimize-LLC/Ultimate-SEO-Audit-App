"""Audit context — unified container for the expanded leak-grounded input stack.

Aggregates the eight inputs that ground audit recommendations in evidence:

    1. SF HTML Internal report      (crawl_df)
    2. SEMrush backlink report      (backlinks_df)
    3. SF Anchor Text report        (anchors_df)
    4. SF custom extraction (dates) (dates_df)
    5. GSC Search Analytics export  (gsc_df)
    6. Koray topical map            (topical_map dict)
    7. GSC "Crawled - currently not indexed" export    (crawled_not_indexed_df)
    8. GSC "Discovered - currently not indexed" export (discovered_not_indexed_df)

Each input is optional. The auditor degrades gracefully when an input is absent,
flagging which leak-grounded analyses cannot be performed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from utils.file_parser import (
    parse_screaming_frog_export,
    parse_semrush_backlinks,
    parse_sf_anchor_report,
    parse_content_dates,
    parse_gsc_performance,
    parse_gsc_index_coverage,
    parse_topical_map,
    detect_integrations,
    get_domain_from_urls,
)


FilePath = Union[BytesIO, str, Path]


@dataclass
class AuditContext:
    """Unified container for all audit inputs.

    All fields are optional — the auditor checks `available_inputs` to decide
    which leak-grounded analyses to run.
    """

    crawl_df: Optional[pd.DataFrame] = None
    backlinks_df: Optional[pd.DataFrame] = None
    anchors_df: Optional[pd.DataFrame] = None
    dates_df: Optional[pd.DataFrame] = None
    gsc_df: Optional[pd.DataFrame] = None
    topical_map: Optional[dict] = None
    crawled_not_indexed_df: Optional[pd.DataFrame] = None
    discovered_not_indexed_df: Optional[pd.DataFrame] = None

    domain: Optional[str] = None
    integrations: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.crawl_df is not None and self.domain is None:
            self.domain = get_domain_from_urls(self.crawl_df)
        if self.crawl_df is not None and not self.integrations:
            self.integrations = detect_integrations(self.crawl_df)

    @property
    def available_inputs(self) -> dict:
        """Map of input name -> bool (whether the input was provided and has data)."""
        return {
            "crawl": self.crawl_df is not None and len(self.crawl_df) > 0,
            "backlinks": self.backlinks_df is not None and len(self.backlinks_df) > 0,
            "anchors": self.anchors_df is not None and len(self.anchors_df) > 0,
            "dates": self.dates_df is not None and len(self.dates_df) > 0,
            "gsc": self.gsc_df is not None and len(self.gsc_df) > 0,
            "topical_map": self.topical_map is not None
            and bool(self.topical_map.get("central_entity") or self.topical_map.get("rings")),
            "crawled_not_indexed": self.crawled_not_indexed_df is not None
            and len(self.crawled_not_indexed_df) > 0,
            "discovered_not_indexed": self.discovered_not_indexed_df is not None
            and len(self.discovered_not_indexed_df) > 0,
        }

    @property
    def available_analyses(self) -> dict:
        """Map of leak-grounded analysis name -> whether its required inputs are present.

        Each analysis ties to specific Google API leak attributes documented in
        Skills/technical-seo-agent/references/seo-fundamentals-2026.md.
        """
        a = self.available_inputs
        return {
            # Standard audits — require crawl only
            "technical_audit": a["crawl"],
            "onpage_audit": a["crawl"],

            # Leak-grounded analyses
            "anchor_mismatch_demotion": a["crawl"] and a["anchors"],
            "anchor_spam_velocity": a["anchors"],
            "external_backlink_quality": a["backlinks"],
            "site_authority_signal": a["backlinks"],
            "date_triangulation": a["crawl"] and a["dates"],
            "freshness_unreliability": a["dates"],
            "position_adjusted_ctr": a["crawl"] and a["gsc"],
            "click_signal_grounding": a["gsc"],
            "topical_authority_outliers": a["crawl"] and a["topical_map"],
            "site_radius_analysis": a["topical_map"],
            "crawled_not_indexed_diagnosis": a["crawl"] and a["crawled_not_indexed"],
            "discovered_not_indexed_diagnosis": a["crawl"] and a["discovered_not_indexed"],
        }

    def missing_for_full_audit(self) -> list[str]:
        """Return list of inputs missing from the full leak-grounded audit stack."""
        missing = []
        for name, present in self.available_inputs.items():
            if not present:
                missing.append(name)
        return missing

    def summary(self) -> dict:
        """Return a summary dict describing what's loaded."""
        return {
            "domain": self.domain,
            "available_inputs": self.available_inputs,
            "available_analyses": self.available_analyses,
            "missing_for_full_audit": self.missing_for_full_audit(),
            "row_counts": {
                "crawl": len(self.crawl_df) if self.crawl_df is not None else 0,
                "backlinks": len(self.backlinks_df) if self.backlinks_df is not None else 0,
                "anchors": len(self.anchors_df) if self.anchors_df is not None else 0,
                "dates": len(self.dates_df) if self.dates_df is not None else 0,
                "gsc": len(self.gsc_df) if self.gsc_df is not None else 0,
                "crawled_not_indexed": len(self.crawled_not_indexed_df)
                if self.crawled_not_indexed_df is not None else 0,
                "discovered_not_indexed": len(self.discovered_not_indexed_df)
                if self.discovered_not_indexed_df is not None else 0,
            },
        }


def load_audit_context(
    crawl_file: Optional[FilePath] = None,
    backlinks_file: Optional[FilePath] = None,
    anchors_file: Optional[FilePath] = None,
    dates_file: Optional[FilePath] = None,
    gsc_file: Optional[FilePath] = None,
    topical_map_file: Optional[FilePath] = None,
    crawled_not_indexed_file: Optional[FilePath] = None,
    discovered_not_indexed_file: Optional[FilePath] = None,
) -> AuditContext:
    """Load all available inputs into a unified AuditContext.

    Each parser is wrapped in a try/except so a single bad file doesn't block
    the rest of the audit.

    Args:
        crawl_file: SF HTML Internal report (CSV/Excel)
        backlinks_file: SEMrush backlink export (CSV/Excel)
        anchors_file: SF Anchor Text report (CSV/Excel)
        dates_file: SF custom extraction with date fields (CSV/Excel)
        gsc_file: GSC Search Analytics export (CSV/Excel)
        topical_map_file: Koray topical map (markdown)
        crawled_not_indexed_file: GSC Page Indexing export for the
            "Crawled - currently not indexed" status (CSV/Excel)
        discovered_not_indexed_file: GSC Page Indexing export for the
            "Discovered - currently not indexed" status (CSV/Excel)

    Returns:
        AuditContext with whichever inputs successfully parsed.
    """
    ctx = AuditContext()
    errors = []

    if crawl_file is not None:
        try:
            ctx.crawl_df = parse_screaming_frog_export(crawl_file)
            ctx.domain = get_domain_from_urls(ctx.crawl_df)
            ctx.integrations = detect_integrations(ctx.crawl_df)
        except Exception as e:
            errors.append(f"crawl: {e}")
            print(f"[ERROR] Failed to parse crawl file: {e}")

    if backlinks_file is not None:
        try:
            ctx.backlinks_df = parse_semrush_backlinks(backlinks_file)
        except Exception as e:
            errors.append(f"backlinks: {e}")
            print(f"[ERROR] Failed to parse backlinks file: {e}")

    if anchors_file is not None:
        try:
            ctx.anchors_df = parse_sf_anchor_report(anchors_file)
        except Exception as e:
            errors.append(f"anchors: {e}")
            print(f"[ERROR] Failed to parse anchors file: {e}")

    if dates_file is not None:
        try:
            ctx.dates_df = parse_content_dates(dates_file)
        except Exception as e:
            errors.append(f"dates: {e}")
            print(f"[ERROR] Failed to parse dates file: {e}")

    if gsc_file is not None:
        try:
            ctx.gsc_df = parse_gsc_performance(gsc_file)
        except Exception as e:
            errors.append(f"gsc: {e}")
            print(f"[ERROR] Failed to parse GSC file: {e}")

    if topical_map_file is not None:
        try:
            ctx.topical_map = parse_topical_map(topical_map_file)
        except Exception as e:
            errors.append(f"topical_map: {e}")
            print(f"[ERROR] Failed to parse topical map: {e}")

    if crawled_not_indexed_file is not None:
        try:
            ctx.crawled_not_indexed_df = parse_gsc_index_coverage(
                crawled_not_indexed_file,
                status_label="Crawled - currently not indexed",
            )
        except Exception as e:
            errors.append(f"crawled_not_indexed: {e}")
            print(f"[ERROR] Failed to parse crawled-not-indexed file: {e}")

    if discovered_not_indexed_file is not None:
        try:
            ctx.discovered_not_indexed_df = parse_gsc_index_coverage(
                discovered_not_indexed_file,
                status_label="Discovered - currently not indexed",
            )
        except Exception as e:
            errors.append(f"discovered_not_indexed: {e}")
            print(f"[ERROR] Failed to parse discovered-not-indexed file: {e}")

    if errors:
        print(f"[WARN] {len(errors)} input(s) failed to load: {errors}")

    return ctx
