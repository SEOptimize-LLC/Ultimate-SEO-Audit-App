"""Click Signal Auditor — leak-grounded position-adjusted CTR analysis.

Grounded in the May 2024 Google API leak click attributes (NavBoost / Glue):

- goodClicks, badClicks, lastLongestClicks, unicornClicks, unsquashedClicks
- 13-month rolling memory window (DOJ testimony, not stated in the leak)
- ~70 days of search log data feed RankEmbedBERT/FastSearch (AI Overview source)

The auditor uses GSC Search Analytics data to classify pages by whether their
CTR is above/at/below the position-adjusted baseline, and routes recommendations
accordingly:

- Below baseline (snippet limiter)  → snippet rewrite is high-leverage
- At baseline (position limiter)    → ranking improvement is high-leverage; snippet rewrite has near-zero ceiling
- Above baseline (outperforming)    → page is earning clicks; protect/replicate the pattern

The baseline is the site's own CTR curve, built from the same GSC export in
two-position bands (1-2, 3-4, 5-6, 7-8, 9-10). A band is used only when it
holds at least MIN_CURVE_IMPRESSIONS impressions across MIN_CURVE_PAGES pages;
otherwise that band falls back to the generic tables below (Advanced Web
Ranking, SISTRIX, FirstPageSage averages, split by query-intent class).
Task 1.5 showed why: a generic curve made two average pages on one client look
like CTR failures, because that site earns about a third of typical CTR.
"""

from __future__ import annotations

import logging

import pandas as pd

from auditors.base_auditor import BaseAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity

logger = logging.getLogger(__name__)


CTR_BASELINES_INFORMATIONAL = {
    1: 0.29, 2: 0.165, 3: 0.11, 4: 0.075, 5: 0.055,
    6: 0.035, 7: 0.0275, 8: 0.0225, 9: 0.0175, 10: 0.0125,
}

CTR_BASELINES_COMMERCIAL = {
    1: 0.22, 2: 0.12, 3: 0.08, 4: 0.055, 5: 0.035,
    6: 0.025, 7: 0.0225, 8: 0.0175, 9: 0.0125, 10: 0.0085,
}

# A site-curve band is trusted only with this much data behind it. 400 matches
# task 1.5's band threshold; the page minimum stops one page from becoming its
# own baseline.
MIN_CURVE_IMPRESSIONS = 400
MIN_CURVE_PAGES = 3

# Minimum impressions a single (page, segment) slice must carry before it is
# classified. Lower than the page-level gate (100) because slicing by device or
# country necessarily splits a page's impressions across buckets; 50 keeps each
# slice above statistical noise while still allowing a real divergence to surface.
MIN_SEGMENT_IMPRESSIONS = 50

# GSC segmentation dimensions this auditor can split satisfaction by, expressed
# as (mapped_column_name, human_label). These are the mapped names produced by
# utils.file_parser.parse_gsc_performance (GSC_PERFORMANCE_COLUMNS): the GSC UI
# exposes Device and Country breakdowns but no language dimension — Country is the
# closest geo/language proxy GSC provides, so it stands in for "language" here.
SEGMENT_DIMENSIONS: list[tuple[str, str]] = [
    ("device", "device"),
    ("country", "country"),
]


class ClickSignalAuditor(BaseAuditor):
    """Audits click-signal performance vs. position-adjusted baselines."""

    def __init__(self, crawl_df: pd.DataFrame, gsc_df: pd.DataFrame):
        """Initialize the click signal auditor.

        Args:
            crawl_df: SF HTML Internal report DataFrame
            gsc_df: GSC Search Analytics export with query/page dimensions
        """
        super().__init__(crawl_df)
        self.gsc_df = gsc_df
        self._site_curve: dict[int, float] = {}

    def get_audit_type(self) -> str:
        return "click_signals"

    def run_audit(self) -> list[AuditIssue]:
        """Run click-signal analysis."""
        self.clear_issues()

        if self.gsc_df is None or len(self.gsc_df) == 0:
            return self.issues
        required = {"page", "clicks", "impressions", "position", "ctr"}
        if not required.issubset(set(self.gsc_df.columns)):
            return self.issues

        self._site_curve = self._build_site_curve()
        self._check_underperforming_snippets()
        self._check_at_baseline_pages()
        self._check_outperforming_pages()
        self._check_segment_divergence()

        return self.issues

    def _gsc_has_column(self, column: str) -> bool:
        """Check a column exists on the GSC dataframe.

        BaseAuditor.has_column inspects the crawl dataframe (self.df); the GSC
        Search Analytics export lives on self.gsc_df, so segmentation checks must
        guard against that frame's columns directly.
        """
        return self.gsc_df is not None and column in self.gsc_df.columns

    @staticmethod
    def _band(pos_int: int) -> int:
        """Two-position band index: 1-2 -> 0, 3-4 -> 1, ... 9-10 -> 4."""
        return (pos_int - 1) // 2

    def _build_site_curve(self) -> dict[int, float]:
        """The site's own CTR per two-position band, where the band has enough data."""
        df = self.gsc_df[["page", "clicks", "impressions", "position"]].dropna()
        df = df[(df["position"] >= 0.5) & (df["position"] < 10.5)]
        if df.empty:
            return {}
        bands = df["position"].round().astype(int).map(self._band)
        grouped = df.assign(band=bands).groupby("band").agg(
            clicks=("clicks", "sum"),
            impressions=("impressions", "sum"),
            pages=("page", "nunique"),
        )
        usable = grouped[
            (grouped["impressions"] >= MIN_CURVE_IMPRESSIONS)
            & (grouped["pages"] >= MIN_CURVE_PAGES)
        ]
        return {
            int(band): float(row["clicks"] / row["impressions"])
            for band, row in usable.iterrows()
        }

    def _classify_page(self, position: float, ctr: float, query: str = "") -> str:
        """Classify a page's CTR against the site curve, or the generic table as fallback."""
        pos_int = int(round(position))
        if pos_int < 1 or pos_int > 10:
            return "out_of_striking_distance"

        site_baseline = self._site_curve.get(self._band(pos_int))
        if site_baseline is not None:
            baseline = site_baseline
        else:
            intent_class = self._infer_intent(query)
            baseline = (
                CTR_BASELINES_COMMERCIAL[pos_int]
                if intent_class == "commercial"
                else CTR_BASELINES_INFORMATIONAL[pos_int]
            )

        if ctr < baseline * 0.7:
            return "underperforming"
        if ctr > baseline * 1.3:
            return "outperforming"
        return "at_baseline"

    @staticmethod
    def _infer_intent(query: str) -> str:
        """Quick heuristic intent classification."""
        q = (query or "").lower()
        commercial_signals = [
            "buy", "price", "cost", "near me", "service", "services",
            "company", "companies", "best", "top", "vs", "review", "reviews",
            "for sale", "deal", "deals", "discount",
        ]
        if any(s in q for s in commercial_signals):
            return "commercial"
        return "informational"

    def _check_underperforming_snippets(self) -> None:
        """Flag pages where CTR is well below position-adjusted baseline."""
        page_agg = (
            self.gsc_df.groupby("page")
            .agg(
                clicks=("clicks", "sum"),
                impressions=("impressions", "sum"),
                position=("position", "mean"),
                top_query=("query", "first") if "query" in self.gsc_df.columns else ("page", "first"),
            )
            .reset_index()
        )
        page_agg = page_agg[page_agg["impressions"] >= 100]
        page_agg["ctr"] = page_agg["clicks"] / page_agg["impressions"]

        underperforming = []
        for _, row in page_agg.iterrows():
            classification = self._classify_page(
                row["position"], row["ctr"], str(row.get("top_query", ""))
            )
            if classification == "underperforming":
                underperforming.append({
                    "url": row["page"],
                    "position": round(row["position"], 1),
                    "ctr": round(row["ctr"] * 100, 2),
                    "impressions": int(row["impressions"]),
                    "top_query": row.get("top_query", ""),
                })

        if not underperforming:
            return

        underperforming.sort(key=lambda x: x["impressions"], reverse=True)
        affected = [u["url"] for u in underperforming[:50]]
        examples = []
        for u in underperforming[:5]:
            examples.append(
                f"{u['url']} — pos {u['position']}, CTR {u['ctr']}%, "
                f"{u['impressions']:,} impressions (\"{u['top_query']}\")"
            )

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.CONTENT,
            issue_type="ctr_below_position_baseline",
            title=f"{len(underperforming)} pages with CTR below position-adjusted baseline",
            description=(
                f"{len(underperforming)} pages earn meaningfully less than the expected "
                "CTR for their average position. Per the May 2024 Google API leak and "
                "DOJ antitrust testimony, NavBoost weights pages on goodClicks / "
                "lastLongestClicks. When CTR is below baseline, the snippet (title + "
                "meta) is the limiter — the page would rank higher if Google saw "
                "stronger click engagement.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(underperforming),
            recommendation=(
                "For each flagged page: rewrite the title and meta description to "
                "match the user's actual query intent. The goal is intent matching, "
                "not power-word manipulation. Look at the top query the page ranks "
                "for and ensure the snippet promises exactly what that searcher wants. "
                "Per DOJ testimony, NavBoost has a ~13-month memory window — improvements take 4-8 "
                "weeks for initial signal accumulation, 8-16 weeks for full impact."
            ),
            impact=(
                "Below-baseline CTR signals to NavBoost that the result isn't "
                "satisfying the query. This becomes a self-reinforcing demotion: "
                "weak clicks → weaker rankings → fewer impressions → fewer clicks."
            ),
            additional_data={
                "underperforming_count": len(underperforming),
                "site_curve_bands": {
                    f"{b * 2 + 1}-{b * 2 + 2}": round(v * 100, 2)
                    for b, v in sorted(self._site_curve.items())
                },
            },
        )

    def _check_at_baseline_pages(self) -> None:
        """Insight: pages at-baseline where snippet rewrites have near-zero ceiling."""
        page_agg = (
            self.gsc_df.groupby("page")
            .agg(
                clicks=("clicks", "sum"),
                impressions=("impressions", "sum"),
                position=("position", "mean"),
                top_query=("query", "first") if "query" in self.gsc_df.columns else ("page", "first"),
            )
            .reset_index()
        )
        page_agg = page_agg[page_agg["impressions"] >= 100]
        page_agg["ctr"] = page_agg["clicks"] / page_agg["impressions"]

        at_baseline = []
        for _, row in page_agg.iterrows():
            classification = self._classify_page(
                row["position"], row["ctr"], str(row.get("top_query", ""))
            )
            if classification == "at_baseline" and row["position"] >= 5:
                at_baseline.append(row["page"])

        if len(at_baseline) < 5:
            return

        self.create_issue(
            severity=Severity.LOW,
            category=AuditCategory.CONTENT,
            issue_type="ctr_at_baseline_position_limited",
            title=f"{len(at_baseline)} pages: CTR at baseline → ranking is the limiter",
            description=(
                f"{len(at_baseline)} pages in striking distance (positions 5-10) earn "
                "approximately the expected CTR for their position. The snippet is "
                "doing its job — the limiter is the ranking position itself, not "
                "the title/meta. Per the click-signals framework, snippet rewrites "
                "on these pages have near-zero ceiling because there's no CTR gap "
                "to close."
            ),
            affected_urls=at_baseline[:50],
            count=len(at_baseline),
            recommendation=(
                "Don't recommend snippet rewrites for these pages. Focus on what "
                "actually moves them up: content depth, internal linking from "
                "topically-related pages, anchor text variation in inbound links, "
                "topical-cluster strengthening. Once ranking improves, CTR will "
                "follow the position curve naturally."
            ),
            impact=(
                "Spending VA editorial cycles on snippet rewrites for at-baseline "
                "pages produces no measurable lift. Prioritize the underperforming "
                "pages instead."
            ),
            additional_data={"at_baseline_count": len(at_baseline)},
        )

    def _check_outperforming_pages(self) -> None:
        """Insight: pages outperforming baseline → strong NavBoost signal, push them higher."""
        page_agg = (
            self.gsc_df.groupby("page")
            .agg(
                clicks=("clicks", "sum"),
                impressions=("impressions", "sum"),
                position=("position", "mean"),
                top_query=("query", "first") if "query" in self.gsc_df.columns else ("page", "first"),
            )
            .reset_index()
        )
        page_agg = page_agg[page_agg["impressions"] >= 100]
        page_agg["ctr"] = page_agg["clicks"] / page_agg["impressions"]

        outperforming = []
        for _, row in page_agg.iterrows():
            classification = self._classify_page(
                row["position"], row["ctr"], str(row.get("top_query", ""))
            )
            if classification == "outperforming":
                outperforming.append({
                    "url": row["page"],
                    "position": round(row["position"], 1),
                    "ctr": round(row["ctr"] * 100, 2),
                })

        if not outperforming:
            return

        affected = [o["url"] for o in outperforming[:50]]
        examples = [
            f"{o['url']} — pos {o['position']}, CTR {o['ctr']}%"
            for o in outperforming[:5]
        ]

        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.CONTENT,
            issue_type="ctr_above_baseline_navboost_strong",
            title=f"{len(outperforming)} pages outperforming CTR baseline",
            description=(
                f"{len(outperforming)} pages earn meaningfully more clicks than the "
                "baseline for their position. The snippet is doing its job — these "
                "pages are accumulating strong NavBoost goodClicks signal. The "
                "ranking position is the only limiter.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(outperforming),
            recommendation=(
                "These pages are click-magnets in their position. Push them higher "
                "with content depth and internal linking. Strong NavBoost signal + "
                "ranking lift = compounding gains. Also study what makes their "
                "snippets work and replicate the pattern for underperforming pages."
            ),
            impact=(
                "Outperforming pages are the site's click-signal anchors. They "
                "accumulate the goodClicks / lastLongestClicks that feed NavBoost "
                "AND the search-log training data that feeds AI Overview citation."
            ),
            additional_data={"outperforming_count": len(outperforming)},
        )

    # ------------------------------------------------------------------
    # Segmentation: device / country satisfaction divergence
    # ------------------------------------------------------------------

    def _check_segment_divergence(self) -> None:
        """Flag pages whose CTR satisfaction diverges across GSC segments.

        The page-level checks above collapse every device / country slice into a
        single per-page average, hiding cases where a page is at/above its
        position-adjusted baseline on one segment (e.g. desktop) but
        underperforming on another (e.g. mobile). Such splits point to a
        segment-specific problem — a mobile snippet/layout issue, a device-specific
        intent mismatch, or a geo where the SERP or offer is weaker — that a
        single blended snippet rewrite will not fix.

        No-ops gracefully when the GSC export carries no segment dimension (the
        common single-export case), so nothing is fabricated from data that can't
        support it.
        """
        for dim_col, dim_label in SEGMENT_DIMENSIONS:
            if not self._gsc_has_column(dim_col):
                continue
            # Need at least two distinct, non-empty segment values to compare.
            non_empty = self.gsc_df[dim_col].astype(str).str.strip()
            if non_empty[non_empty != ""].nunique() < 2:
                continue

            divergent = self._find_divergent_pages(dim_col)
            if not divergent:
                continue

            self._emit_divergence_issue(dim_col, dim_label, divergent)

    def _segment_page_agg(self, dim_col: str) -> pd.DataFrame:
        """Aggregate GSC rows to one row per (page, segment) slice."""
        df = self.gsc_df[self.gsc_df[dim_col].astype(str).str.strip() != ""]

        agg_kwargs: dict[str, tuple[str, str]] = {
            "clicks": ("clicks", "sum"),
            "impressions": ("impressions", "sum"),
            "position": ("position", "mean"),
        }
        if "query" in self.gsc_df.columns:
            agg_kwargs["top_query"] = ("query", "first")

        grouped = df.groupby(["page", dim_col]).agg(**agg_kwargs).reset_index()
        grouped = grouped[grouped["impressions"] >= MIN_SEGMENT_IMPRESSIONS].copy()
        if grouped.empty:
            return grouped
        grouped["ctr"] = grouped["clicks"] / grouped["impressions"]
        return grouped

    def _find_divergent_pages(self, dim_col: str) -> list[dict]:
        """Return pages with a healthy slice and an underperforming slice.

        A page is "divergent" when at least one segment slice classifies as
        underperforming while another classifies as at/above baseline — the case
        where per-segment diagnosis is warranted.
        """
        agg = self._segment_page_agg(dim_col)
        if agg.empty:
            return []

        divergent: list[dict] = []
        for page, group in agg.groupby("page"):
            if group[dim_col].nunique() < 2:
                continue

            slices: list[dict] = []
            for _, row in group.iterrows():
                if pd.isna(row["position"]):
                    continue
                classification = self._classify_page(
                    row["position"], row["ctr"], str(row.get("top_query", ""))
                )
                slices.append({
                    "segment": row[dim_col],
                    "classification": classification,
                    "position": round(float(row["position"]), 1),
                    "ctr": round(float(row["ctr"]) * 100, 2),
                    "impressions": int(row["impressions"]),
                })

            underperforming = [
                s for s in slices if s["classification"] == "underperforming"
            ]
            healthy = [
                s for s in slices
                if s["classification"] in ("at_baseline", "outperforming")
            ]
            if not underperforming or not healthy:
                continue

            worst = min(underperforming, key=lambda s: s["ctr"])
            best = max(healthy, key=lambda s: s["ctr"])
            divergent.append({
                "url": page,
                "worst": worst,
                "best": best,
                "total_impressions": sum(s["impressions"] for s in slices),
            })

        divergent.sort(key=lambda d: d["total_impressions"], reverse=True)
        return divergent

    def _emit_divergence_issue(
        self, dim_col: str, dim_label: str, divergent: list[dict]
    ) -> None:
        """Create the AuditIssue for a segment dimension's divergent pages."""
        affected = [d["url"] for d in divergent[:50]]
        examples = []
        for d in divergent[:5]:
            best, worst = d["best"], d["worst"]
            examples.append(
                f"{d['url']} — healthy on {best['segment']} "
                f"(pos {best['position']}, CTR {best['ctr']}%) but underperforming "
                f"on {worst['segment']} (pos {worst['position']}, CTR {worst['ctr']}%)"
            )

        logger.info(
            "click_signals: %d pages diverge by %s", len(divergent), dim_label
        )

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.CONTENT,
            issue_type=f"ctr_diverges_by_{dim_col}",
            title=(
                f"{len(divergent)} pages: CTR satisfaction diverges by {dim_label}"
            ),
            description=(
                f"{len(divergent)} pages sit at or above their position-adjusted "
                f"CTR baseline on one {dim_label} segment but underperform it on "
                f"another. The blended per-page averages used elsewhere in this "
                f"audit hide this split. Per the May 2024 leak, NavBoost weighs "
                f"goodClicks / lastLongestClicks, and those signals are collected "
                f"per {dim_label} — a page satisfying desktop searchers while losing "
                f"mobile searchers (or one geo while losing another) is accumulating "
                f"a mixed click signal that a single blended snippet rewrite cannot "
                f"resolve.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            recommendation=(
                f"Diagnose these pages per {dim_label} rather than in aggregate. "
                f"In GSC, filter each URL by {dim_label} and compare position and "
                f"CTR side by side. For a mobile-only shortfall, check the mobile "
                f"snippet truncation, above-the-fold layout, tap targets, and "
                f"interstitials — the desktop snippet is already proven, so the "
                f"limiter is the {dim_label}-specific experience or intent match, "
                f"not the title/meta as a whole. For a country/geo shortfall, check "
                f"whether the SERP composition, offer, or language expectation "
                f"differs in the weak segment."
            ),
            impact=(
                f"Optimizing on the blended average leaves the weak {dim_label} "
                "segment underperforming, and its bad-click signal keeps dragging "
                "the page's overall NavBoost standing even where the strong segment "
                "is doing everything right."
            ),
            additional_data={
                "dimension": dim_label,
                "divergent_count": len(divergent),
            },
        )
