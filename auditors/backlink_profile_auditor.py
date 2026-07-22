"""Backlink Profile Auditor — deterministic link-profile segmentation.

Runs on the SEMrush per-link export (``ctx.backlinks_df``), which the pipeline
parses today but no auditor consumes. Computes the honest deterministic subset
of Daniel Foley Carter's link-audit segmentation table given the columns SEMrush
actually provides:

1. DR-proxy (Authority Score) band distribution, deduped per referring domain
2. Dofollow / nofollow split
3. Backlinks-per-referring-domain ratio (a sitewide / footer-link detector —
   DFC's "backlinks : referring-domains gap" heuristic)
4. New / lost link velocity

The full DR x traffic x in-content x topical-relevance table requires
referring-domain traffic + link placement (in-content vs footer) + trust flow.
The SEMrush per-link export carries NONE of those, so:

- The artificial-DR-inflation check (high DR + near-zero referring-domain
  traffic) is NOT attempted here — there is no traffic column to support it.
- In-content vs template placement is only *approximated* by the backlinks-per-
  domain ratio; true placement detection is an analyst/skill method.

Those remain documented analyst methods in the backlink-agent skill rather than
fabricated from data that cannot support them.

The class name and the ``(backlinks_df)`` constructor signature are kept stable
so the wiring in ``app.py`` / ``auditors.__init__`` stays valid.
"""
from __future__ import annotations

import logging

import pandas as pd

from auditors.base_auditor import BaseAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity

logger = logging.getLogger(__name__)


# DR-proxy (SEMrush Authority Score, 0-100) bands. Boundaries chosen to mirror
# the coarse tiers link auditors reason in: throwaway (0-9), weak (10-25),
# mid (26-49), strong (50-74), authority (75-100).
DR_BANDS: list[tuple[str, int, int]] = [
    ("0-9", 0, 9),
    ("10-25", 10, 25),
    ("26-49", 26, 49),
    ("50-74", 50, 74),
    ("75-100", 75, 100),
]
LOW_BANDS = {"0-9", "10-25"}

# A referring-domain profile is "weak" when this share of its referring domains
# sit in the two lowest DR bands.
WEAK_PROFILE_LOW_SHARE = 0.70
# Minimum distinct referring domains before the distribution is worth flagging.
MIN_REFERRING_DOMAINS = 5

# Dofollow-share thresholds.
DOFOLLOW_SHARE_LOW = 0.20     # below this → LOW (very few equity-passing links)
DOFOLLOW_SHARE_NOTE = 0.50    # below this → INSIGHT
# Minimum total links before the ratio is statistically meaningful.
MIN_LINKS_FOR_RATIO = 20

# Sitewide / footer detector: a single referring domain contributing this many
# backlinks (absolute) OR this multiple of the median per-domain count is
# treated as a likely template / sitewide / footer link source.
SITEWIDE_ABS_MIN = 50
SITEWIDE_MEDIAN_MULT = 10
MIN_DOMAINS_FOR_SITEWIDE = 3

# New/lost velocity: flag a heavy loss skew when losses exceed gains by this
# multiple and clear this absolute floor.
LOSS_SKEW_MULT = 1.5
LOSS_SKEW_MIN = 5

# Truthy tokens SEMrush uses for boolean-ish flag columns (Newlink / Lostlink).
_TRUTHY = {"true", "yes", "1", "t", "y"}

_SAMPLE_LIMIT = 50


class BacklinkProfileAuditor(BaseAuditor):
    """Segments a SEMrush backlink export by the quality proxies it exposes."""

    def __init__(self, backlinks_df: pd.DataFrame):
        super().__init__(backlinks_df)
        self.backlinks_df = backlinks_df

    def get_audit_type(self) -> str:
        return "backlink_profile"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        if self.backlinks_df is None or len(self.backlinks_df) == 0:
            return self.issues

        self._check_dr_band_distribution()
        self._check_dofollow_ratio()
        self._check_sitewide_footer_links()
        self._check_new_lost_velocity()

        return self.issues

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _bl_has_column(self, column: str) -> bool:
        """Guard against the backlinks frame's own columns.

        ``self.df`` *is* the backlinks frame here (it is passed to
        ``super().__init__``), so ``has_column`` already inspects the right
        frame — this alias exists purely to make the intent explicit at the
        call sites.
        """
        return self.backlinks_df is not None and column in self.backlinks_df.columns

    @staticmethod
    def _coerce_bool(series: pd.Series) -> pd.Series:
        """Coerce a SEMrush flag column (which may arrive as strings) to bool.

        The parser only hard-casts ``nofollow``; ``is_new`` / ``is_lost`` may
        still be strings like ``"true"`` / ``"false"`` / ``""``.
        """
        if series.dtype == bool:
            return series
        return series.astype(str).str.strip().str.lower().isin(_TRUTHY)

    @staticmethod
    def _band_of(score: float) -> str:
        """Return the DR band label for a 0-100 authority score."""
        for label, low, high in DR_BANDS:
            if low <= score <= high:
                return label
        # Scores above 100 (shouldn't happen) fall into the top band.
        return DR_BANDS[-1][0] if score > 100 else DR_BANDS[0][0]

    # ------------------------------------------------------------------
    # Check 1 — DR-proxy band distribution (per referring domain)
    # ------------------------------------------------------------------

    def _check_dr_band_distribution(self) -> None:
        """Band referring domains by Authority Score; flag weak-authority profiles."""
        if not self._bl_has_column("source_authority") or not self._bl_has_column("source_domain"):
            return

        df = self.backlinks_df[["source_domain", "source_authority"]].copy()
        df["source_authority"] = pd.to_numeric(df["source_authority"], errors="coerce")
        df = df.dropna(subset=["source_authority"])
        df = df[df["source_domain"].astype(str).str.strip() != ""]
        if df.empty:
            return

        # One authority value per referring domain (dedupe multiple links from
        # the same domain). Authority is a domain-level metric, so max collapses
        # any per-link noise to the domain's score.
        per_domain = df.groupby("source_domain")["source_authority"].max()
        total_domains = int(len(per_domain))
        if total_domains < MIN_REFERRING_DOMAINS:
            return

        bands = per_domain.apply(self._band_of)
        distribution = {label: int((bands == label).sum()) for label, _, _ in DR_BANDS}

        low_count = sum(distribution[b] for b in LOW_BANDS)
        low_share = low_count / total_domains

        band_summary = ", ".join(
            f"{label}: {distribution[label]}" for label, _, _ in DR_BANDS
        )

        if low_share >= WEAK_PROFILE_LOW_SHARE:
            severity = Severity.LOW
            title = (
                f"Weak referring-domain authority: {low_share * 100:.0f}% of "
                f"{total_domains} domains in the two lowest DR bands"
            )
            description = (
                f"{low_count} of {total_domains} referring domains have a SEMrush "
                f"Authority Score under 26 (bands 0-9 and 10-25). Distribution — "
                f"{band_summary}. A profile concentrated in the low bands passes "
                "little authority; ranking gains from link equity will be limited "
                "until higher-authority domains are earned."
            )
            recommendation = (
                "Prioritise earning links from domains with Authority Score 50+ "
                "(digital PR, industry publications, partnerships) over volume from "
                "low-authority directories and syndication. Audit the 0-9 band for "
                "spam/PBN patterns worth disavowing."
            )
            impact = (
                "Link equity scales with referring-domain authority. A low-band-heavy "
                "profile caps the ceiling of what backlinks can contribute to rankings."
            )
        else:
            severity = Severity.INSIGHT
            title = f"Referring-domain authority distribution ({total_domains} domains)"
            description = (
                f"Authority Score distribution across {total_domains} referring "
                f"domains — {band_summary}. "
                f"{low_share * 100:.0f}% sit in the two lowest DR bands (under 26)."
            )
            recommendation = (
                "Use this as the authority baseline for the profile. Focus new "
                "link-building on the 50+ bands to raise the profile's overall "
                "authority weight."
            )
            impact = (
                "The authority band mix is a proxy for how much ranking weight the "
                "existing backlink profile can pass."
            )

        logger.info(
            "backlink_profile: DR band distribution over %d domains (low_share=%.2f)",
            total_domains,
            low_share,
        )

        self.create_issue(
            severity=severity,
            category=AuditCategory.REFERRING_DOMAINS,
            issue_type="referring_domain_authority_distribution",
            title=title,
            description=description,
            recommendation=recommendation,
            impact=impact,
            additional_data={
                "total_referring_domains": total_domains,
                "band_distribution": distribution,
                "low_band_share": round(low_share, 3),
            },
        )

    # ------------------------------------------------------------------
    # Check 2 — dofollow / nofollow ratio
    # ------------------------------------------------------------------

    def _check_dofollow_ratio(self) -> None:
        """Flag profiles where the dofollow share of links is very low."""
        if not self._bl_has_column("nofollow"):
            return

        nofollow = self._coerce_bool(self.backlinks_df["nofollow"])
        total = int(len(nofollow))
        if total < MIN_LINKS_FOR_RATIO:
            return

        nofollow_count = int(nofollow.sum())
        dofollow_count = total - nofollow_count
        dofollow_share = dofollow_count / total

        if dofollow_share < DOFOLLOW_SHARE_LOW:
            severity = Severity.LOW
        elif dofollow_share < DOFOLLOW_SHARE_NOTE:
            severity = Severity.INSIGHT
        else:
            return

        logger.info(
            "backlink_profile: dofollow share %.2f (%d/%d)",
            dofollow_share,
            dofollow_count,
            total,
        )

        self.create_issue(
            severity=severity,
            category=AuditCategory.BACKLINKS,
            issue_type="low_dofollow_share",
            title=f"Dofollow links are {dofollow_share * 100:.0f}% of the profile",
            description=(
                f"{dofollow_count:,} of {total:,} backlinks are dofollow "
                f"({dofollow_share * 100:.0f}%); the remaining {nofollow_count:,} are "
                "nofollow. Nofollow links can still drive referral traffic and a "
                "natural profile mixes both, but only dofollow links pass ranking "
                "equity, so a very low dofollow share limits the profile's ranking "
                "contribution."
            ),
            recommendation=(
                "Confirm this reflects the real placement mix rather than an export "
                "filter. If genuine, weight future link-building toward editorial "
                "dofollow placements. Do not chase a specific ratio — a natural "
                "profile includes nofollow from social, forums and UGC."
            ),
            impact=(
                "Only dofollow links pass PageRank-equivalent equity. A low dofollow "
                "share caps how much the backlink profile can move rankings."
            ),
            additional_data={
                "total_links": total,
                "dofollow_count": dofollow_count,
                "nofollow_count": nofollow_count,
                "dofollow_share": round(dofollow_share, 3),
            },
        )

    # ------------------------------------------------------------------
    # Check 3 — backlinks per referring domain (sitewide / footer detector)
    # ------------------------------------------------------------------

    def _check_sitewide_footer_links(self) -> None:
        """Flag domains contributing an outsized number of backlinks (sitewide/footer)."""
        if not self._bl_has_column("source_domain"):
            return

        domains = self.backlinks_df["source_domain"].astype(str).str.strip()
        domains = domains[domains != ""]
        if domains.empty:
            return

        counts = domains.value_counts()
        if len(counts) < MIN_DOMAINS_FOR_SITEWIDE:
            return

        median = float(counts.median())
        threshold = max(SITEWIDE_ABS_MIN, median * SITEWIDE_MEDIAN_MULT)

        flagged = counts[counts >= threshold]
        if flagged.empty:
            return

        affected = flagged.index.tolist()[:_SAMPLE_LIMIT]
        examples = [
            f"{domain} — {int(count):,} backlinks"
            for domain, count in flagged.head(5).items()
        ]

        logger.info(
            "backlink_profile: %d sitewide/footer-suspect domains (threshold=%.0f, median=%.1f)",
            len(flagged),
            threshold,
            median,
        )

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.BACKLINKS,
            issue_type="sitewide_footer_link_concentration",
            title=f"{len(flagged)} referring domains contribute sitewide/footer-style link volume",
            description=(
                f"{len(flagged)} referring domains each contribute at least "
                f"{int(threshold):,} backlinks (median per domain is {median:.0f}). "
                "When one domain links thousands of times it is almost always a "
                "sitewide element — a footer credit, blogroll, template widget or "
                "author byline repeated on every page — not many independent "
                "editorial links. Search engines largely consolidate these to a "
                "single domain-level signal, so the raw backlink count overstates "
                "the profile's real strength (the DFC backlinks:referring-domains "
                "gap).\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=int(len(flagged)),
            recommendation=(
                "Judge these domains by referring-DOMAIN count, not link count. "
                "Confirm each is a legitimate sitewide placement (partner footer, "
                "network site). Investigate any low-authority domain contributing "
                "thousands of links for PBN / spam patterns worth disavowing. Do not "
                "count these toward link-acquisition targets."
            ),
            impact=(
                "Sitewide links inflate the reported backlink total without a "
                "proportional ranking benefit; reading the raw count as unique links "
                "overstates authority and hides how narrow the real referring-domain "
                "base is."
            ),
            additional_data={
                "flagged_domain_count": int(len(flagged)),
                "median_links_per_domain": round(median, 1),
                "threshold": int(threshold),
                "top_domains": {str(d): int(c) for d, c in flagged.head(20).items()},
            },
        )

    # ------------------------------------------------------------------
    # Check 4 — new / lost velocity
    # ------------------------------------------------------------------

    def _check_new_lost_velocity(self) -> None:
        """Summarise gained vs lost links; flag a heavy loss skew."""
        has_new = self._bl_has_column("is_new")
        has_lost = self._bl_has_column("is_lost")
        if not has_new and not has_lost:
            # first_seen / last_seen give no reliable gained/lost split without a
            # known export cutoff date, so velocity is left to the analyst method.
            return

        new_count = int(self._coerce_bool(self.backlinks_df["is_new"]).sum()) if has_new else 0
        lost_count = int(self._coerce_bool(self.backlinks_df["is_lost"]).sum()) if has_lost else 0
        if new_count == 0 and lost_count == 0:
            return

        heavy_loss = lost_count >= LOSS_SKEW_MIN and lost_count > new_count * LOSS_SKEW_MULT

        affected: list[str] = []
        if heavy_loss and has_lost and self._bl_has_column("source_url"):
            lost_mask = self._coerce_bool(self.backlinks_df["is_lost"])
            affected = (
                self.backlinks_df.loc[lost_mask, "source_url"]
                .astype(str)
                .replace("", pd.NA)
                .dropna()
                .unique()
                .tolist()[:_SAMPLE_LIMIT]
            )

        if heavy_loss:
            severity = Severity.LOW
            title = f"Link loss outpacing gains: {lost_count:,} lost vs {new_count:,} new"
            description = (
                f"The export flags {lost_count:,} lost backlinks against {new_count:,} "
                "newly gained — a net-negative velocity. Sustained loss skew erodes "
                "the profile faster than it is replenished and can signal decaying "
                "placements (expired posts, redesigned partner sites, pruned pages)."
            )
            recommendation = (
                "Pull the lost-link list and triage: recover high-value placements "
                "(outreach, reclaim broken/removed links, fix 404'd target pages) and "
                "ignore low-authority churn. Then confirm new-link acquisition is "
                "outpacing loss going forward."
            )
            impact = (
                "A profile losing links faster than it gains them trends toward weaker "
                "authority over time, all else equal."
            )
        else:
            severity = Severity.INSIGHT
            title = f"Backlink velocity: {new_count:,} new / {lost_count:,} lost"
            description = (
                f"The export flags {new_count:,} newly gained and {lost_count:,} lost "
                "backlinks. Velocity is not heavily loss-skewed. Use this as the "
                "gained-vs-lost baseline for the profile."
            )
            recommendation = (
                "Track new vs lost over time to confirm acquisition keeps pace with "
                "natural link decay; investigate if the lost count starts to dominate."
            )
            impact = (
                "Gained-vs-lost velocity is a leading indicator of whether the profile "
                "is growing or eroding."
            )

        logger.info(
            "backlink_profile: velocity new=%d lost=%d (heavy_loss=%s)",
            new_count,
            lost_count,
            heavy_loss,
        )

        self.create_issue(
            severity=severity,
            category=AuditCategory.BACKLINKS,
            issue_type="backlink_new_lost_velocity",
            title=title,
            description=description,
            affected_urls=affected,
            count=lost_count if heavy_loss else 0,
            recommendation=recommendation,
            impact=impact,
            additional_data={
                "new_count": new_count,
                "lost_count": lost_count,
                "heavy_loss_skew": heavy_loss,
            },
        )
