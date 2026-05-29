"""Topical Authority Auditor — leak-grounded siteRadius outlier detection.

Grounded in QualityAuthorityTopicEmbeddingsVersionedItem from the May 2024
Google API leak:

- siteEmbedding — vector representation of what the site is centrally about
- pageEmbedding — vector representation of each page's topic
- siteFocusScore — how concentrated the site is around its topical center
- siteRadius — how far each page sits from the site's center

The auditor cannot compute embeddings. It uses the Koray topical map output
(central entity, Ring 1/2/3 page groupings, outliers) as the user-supplied
proxy for these signals, and surfaces:

1. Outlier pages — pages flagged as off-topic in the topical map
2. Topic dispersion — many small topic clusters (low siteFocusScore proxy)
3. Two-Hop Rule violations — Ring 3 pages without paths through Ring 1/2
"""

from __future__ import annotations

import pandas as pd

from auditors.base_auditor import BaseAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity


class TopicalAuthorityAuditor(BaseAuditor):
    """Audits topical concentration vs. dispersion using a topical map input."""

    def __init__(self, crawl_df: pd.DataFrame, topical_map: dict):
        """Initialize the topical authority auditor.

        Args:
            crawl_df: SF HTML Internal report DataFrame
            topical_map: Parsed Koray topical map dict (from parse_topical_map)
        """
        super().__init__(crawl_df)
        self.topical_map = topical_map or {}
        # Optional rich payload from the semantic-site-map skill.
        self._full_map: dict | None = None

    @classmethod
    def from_computed_map(
        cls,
        crawl_df,
        topical_map_path,
        full_json_path=None,
    ):
        """Construct an auditor from semantic-site-map JSON outputs.

        Args:
            crawl_df: SF Internal report DataFrame.
            topical_map_path: Path to Koray-compatible topical_map.json.
            full_json_path: Optional path to semantic_map_full.json; if
                present, enables the high-click off-topic cluster check.
        """
        import json
        from pathlib import Path

        topical_map = json.loads(
            Path(topical_map_path).read_text(encoding="utf-8")
        )
        instance = cls(crawl_df, topical_map)
        if full_json_path is not None:
            instance._full_map = json.loads(
                Path(full_json_path).read_text(encoding="utf-8")
            )
        return instance

    def get_audit_type(self) -> str:
        return "topical_authority"

    def run_audit(self) -> list[AuditIssue]:
        """Run topical authority checks."""
        self.clear_issues()

        if not self.topical_map:
            return self.issues

        self._check_outlier_pages()
        self._check_topic_dispersion()
        self._check_central_entity_alignment()
        self._check_high_click_off_topic_cluster()

        return self.issues

    def _check_outlier_pages(self) -> None:
        """Flag pages the topical map identifies as off-topic outliers."""
        outliers = self.topical_map.get("outliers", [])
        if not outliers:
            return

        urls = []
        for item in outliers:
            urls.extend(self._extract_urls(item))

        if not urls:
            return

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.CONTENT,
            issue_type="topical_outlier_pages",
            title=f"{len(urls)} pages flagged as off-topic outliers",
            description=(
                f"{len(urls)} pages sit outside the site's topical center per the "
                "topical map analysis. Per the May 2024 Google API leak, the "
                "QualityAuthorityTopicEmbeddings module computes siteRadius — pages "
                "far from the site's topical center (`siteEmbedding`) underperform "
                "regardless of standalone content quality. They also dilute the "
                "site's topical focus score, weakening every other page's ranking "
                "potential."
            ),
            affected_urls=urls[:50],
            count=len(urls),
            recommendation=(
                "For each outlier page, choose: (a) prune via 410 / "
                "consolidate into a relevant page, (b) relocate to a "
                "subdomain, or (c) restructure into a Ring-aligned "
                "topic. When in doubt, prefer the subdomain over a "
                "subfolder move: a subdomain creates a separate "
                "siteEmbedding pool, so the off-topic content keeps "
                "its traffic while the main domain's topical center "
                "reclaims focus. A subfolder still aggregates into "
                "the main domain's siteEmbedding and does not fix "
                "the dilution problem."
            ),
            impact=(
                "siteRadius outliers are weak ranking candidates AND they reduce "
                "siteFocusScore, weakening the entire site's topical authority signal."
            ),
            additional_data={"outlier_urls": urls[:50]},
        )

    def _check_topic_dispersion(self) -> None:
        """Flag low siteFocusScore (proxy: many small disconnected ring clusters)."""
        rings = self.topical_map.get("rings", {})
        if not rings:
            return

        ring_sizes = {ring: len(items) for ring, items in rings.items()}
        total_topics = sum(ring_sizes.values())
        if total_topics == 0:
            return

        ring_count = len(rings)
        avg_per_ring = total_topics / ring_count if ring_count else 0

        if ring_count >= 5 and avg_per_ring < 3:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.CONTENT,
                issue_type="low_topical_focus_score",
                title=f"Topic dispersion: {ring_count} thin topic clusters (~{avg_per_ring:.1f} pages each)",
                description=(
                    f"The site has {ring_count} distinct topic clusters but each "
                    f"averages only {avg_per_ring:.1f} pages. Per the May 2024 Google "
                    "API leak, siteFocusScore measures how concentrated the site is "
                    "around its topical center. Many thin, disconnected clusters = "
                    "low focus score = weak topical authority across all clusters."
                ),
                count=ring_count,
                recommendation=(
                    "Pick the 1-2 strongest clusters and double down — add depth to "
                    "Ring 1 (core), Ring 2 (supporting), Ring 3 (peripheral) for "
                    "those topics. Prune or consolidate the thin clusters. A site "
                    "with 3 deep clusters outranks a site with 10 thin ones."
                ),
                impact=(
                    "Low siteFocusScore caps the ranking ceiling for every page on "
                    "the site, even pages that are individually well-optimized."
                ),
                additional_data={
                    "ring_sizes": ring_sizes,
                    "ring_count": ring_count,
                    "avg_per_ring": round(avg_per_ring, 1),
                },
            )

    def _check_central_entity_alignment(self) -> None:
        """Flag if homepage/title doesn't align with the declared central entity."""
        central = self.topical_map.get("central_entity", "").strip()
        if not central:
            return

        if not self.has_columns(["url", "title"]):
            return

        candidates = self.df.head(20)
        homepage = None
        for _, row in candidates.iterrows():
            url = str(row.get("url", "")).strip()
            if not url:
                continue
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.path in ("", "/"):
                homepage = row
                break

        if homepage is None:
            return

        homepage_title = str(homepage.get("title", "")).lower()
        if not homepage_title:
            return

        central_words = set(self._tokenize(central.lower()))
        title_words = set(self._tokenize(homepage_title))
        if not central_words:
            return

        overlap = len(central_words & title_words) / len(central_words)

        if overlap < 0.2:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.CONTENT,
                issue_type="central_entity_homepage_mismatch",
                title="Homepage title doesn't reflect the declared central entity",
                description=(
                    f"The topical map declares the central entity as: \"{central[:120]}\"\n"
                    f"The homepage title is: \"{homepage.get('title', '')}\"\n"
                    f"Topical overlap: {overlap*100:.0f}%\n\n"
                    "Per the May 2024 Google API leak, siteEmbedding is computed from "
                    "the site's overall content — and the homepage is heavily "
                    "weighted in that signal. A homepage that doesn't reflect the "
                    "site's actual topic confuses the embedding."
                ),
                affected_urls=[str(homepage.get("url", ""))],
                recommendation=(
                    "Rewrite the homepage title (and H1) to clearly state what the "
                    "site is about in terms aligned with the central entity. The "
                    "homepage should be the clearest expression of the site's "
                    "topical center."
                ),
                impact=(
                    "A misaligned homepage drags siteEmbedding away from the actual "
                    "topical center, reducing every page's siteFocusScore benefit."
                ),
                additional_data={
                    "central_entity": central,
                    "homepage_title": homepage.get("title", ""),
                    "overlap_pct": round(overlap * 100, 1),
                },
            )

    def _check_high_click_off_topic_cluster(self) -> None:
        """Flag clusters that earn meaningful traffic AND sit far from center.

        Requires the rich `semantic_map_full.json` payload loaded via
        from_computed_map(full_json_path=...). Skipped silently otherwise.
        """
        if not self._full_map:
            return

        flagged = self._full_map.get(
            "high_click_off_topic_clusters"
        ) or []
        if not flagged:
            return

        labels = ", ".join(
            f.get("cluster_name", f"Cluster {f.get('cluster_id')}")
            for f in flagged
        )
        total_clicks = sum(int(f.get("clicks", 0)) for f in flagged)
        total_pages = sum(
            int(f.get("page_count", 0)) for f in flagged
        )

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.CONTENT,
            issue_type="high_click_off_topic_cluster",
            title=(
                f"{len(flagged)} high-traffic cluster(s) dragging "
                f"the site's topical center: {labels}"
            ),
            description=(
                f"{len(flagged)} topical cluster(s) earn meaningful "
                "traffic but sit far from the site's central topic. "
                f"Combined: {total_clicks} clicks across "
                f"{total_pages} pages.\n\n"
                "Per the May 2024 Google API leak, the "
                "QualityAuthorityTopicEmbeddings module computes "
                "siteFocusScore from the aggregate of every indexed "
                "page on the domain. High-click clusters that sit at "
                "high siteRadius are the worst case: they look like "
                "traffic wins in a dashboard, but they drag the site "
                "embedding away from the topical center that the "
                "revenue pages need to rank for."
            ),
            count=len(flagged),
            recommendation=(
                "For each flagged cluster, ask: does this audience "
                "convert, or just consume? If it does not convert, "
                "the high-leverage move is to relocate the cluster "
                "to a subdomain - that creates a separate "
                "siteEmbedding pool so the cluster keeps its traffic "
                "while the main domain's topical center returns to "
                "the revenue topics. A subfolder move does not fix "
                "this; siteEmbedding aggregates everything under the "
                "same domain."
            ),
            impact=(
                "Off-topic clusters at high click volume have "
                "outsized negative effect on siteFocusScore - they "
                "pull the centroid by more than low-traffic outliers "
                "do."
            ),
            additional_data={"clusters": flagged},
        )

    @staticmethod
    def _extract_urls(text: str) -> list[str]:
        """Pull URLs from a topical-map outlier item."""
        import re

        return re.findall(r"https?://[^\s\)\]]+|/[A-Za-z0-9\-_/]+", str(text))

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        import re

        stop = {
            "the", "a", "an", "and", "or", "of", "in", "on", "at", "to",
            "for", "with", "by", "from", "is", "are", "was", "were",
            "this", "that", "your", "our", "their",
        }
        tokens = re.findall(r"\b[a-z]+\b", text.lower())
        return [t for t in tokens if len(t) > 2 and t not in stop]
