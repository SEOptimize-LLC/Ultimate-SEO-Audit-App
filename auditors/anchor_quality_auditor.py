"""Anchor Quality Auditor — leak-grounded analysis of anchor text patterns.

Grounded in two Google API leak modules:

- AnchorsAnchor (sourceType tiers: TYPE_HIGH_QUALITY / MEDIUM / LOW / FRESHDOCS)
- IndexingDocjoinerAnchorPhraseSpamInfo (phraseAnchorSpamCount, Rate, Penalty,
  Demoted) — flags pages where inbound anchor patterns look like spam velocity

Demotion factor: anchorMismatchDemotion (CompressedQualitySignals) — pages where
inbound anchor topics drift from the page's actual content are demoted.

Detects four issue classes:

1. Anchor mismatch — inbound anchors don't topically match the page's H1/title
2. Anchor spam velocity — heavy concentration of one keyword anchor across
   many internal linking pages
3. Non-descriptive anchor abuse — "click here", "read more", bare URLs as the
   dominant pattern (passes no topical context)
4. Shared-anchor crisscrossing — the inverse of (2): one anchor phrase reused
   across many DIFFERENT internal targets, so it no longer describes any single
   page's topic (anchor dilution)
"""

from __future__ import annotations

import pandas as pd

from auditors.base_auditor import BaseAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity


GENERIC_ANCHORS = {
    "click here", "read more", "learn more", "here", "more",
    "this", "this page", "this article", "this link", "link",
    "read", "see more", "find out more", "view", "more info",
}

# One anchor phrase pointing at this many DISTINCT internal targets is anchor
# "crisscrossing" / dilution — the inverse of per-target concentration. A single
# generic anchor across a few targets is fine; the same anchor spread across ~10+
# different destinations means it no longer describes any one page's topic.
SHARED_ANCHOR_TARGETS = 10
SHARED_ANCHOR_TARGETS_HIGH = 20


class AnchorQualityAuditor(BaseAuditor):
    """Audits internal linking anchor patterns against leak-grounded signals."""

    def __init__(self, crawl_df: pd.DataFrame, anchors_df: pd.DataFrame):
        """Initialize the anchor quality auditor.

        Args:
            crawl_df: SF HTML Internal report DataFrame (for page-level H1/title)
            anchors_df: SF Anchor Text report DataFrame (source/target/anchor)
        """
        super().__init__(crawl_df)
        self.anchors_df = anchors_df

    def get_audit_type(self) -> str:
        return "anchor_quality"

    def run_audit(self) -> list[AuditIssue]:
        """Run all anchor-quality checks."""
        self.clear_issues()

        if self.anchors_df is None or len(self.anchors_df) == 0:
            return self.issues

        self._check_generic_anchor_dominance()
        self._check_anchor_concentration_per_target()
        self._check_shared_anchor_across_targets()
        self._check_anchor_mismatch_against_h1()

        return self.issues

    def _check_generic_anchor_dominance(self) -> None:
        """Flag sites where >40% of internal anchors are non-descriptive."""
        if "anchor_text" not in self.anchors_df.columns:
            return

        anchors = self.anchors_df["anchor_text"].astype(str).str.lower().str.strip()
        total = len(anchors)
        if total == 0:
            return

        generic_count = anchors.isin(GENERIC_ANCHORS).sum()
        generic_pct = (generic_count / total) * 100

        if generic_pct >= 40:
            severity = Severity.HIGH
        elif generic_pct >= 20:
            severity = Severity.MEDIUM
        else:
            return

        sample_targets = []
        if "target_url" in self.anchors_df.columns:
            mask = self.anchors_df["anchor_text"].astype(str).str.lower().str.strip().isin(GENERIC_ANCHORS)
            sample_targets = self.anchors_df.loc[mask, "target_url"].dropna().unique().tolist()[:20]

        self.create_issue(
            severity=severity,
            category=AuditCategory.ANCHOR_TEXT,
            issue_type="generic_anchor_dominance",
            title=f"{generic_pct:.0f}% of internal anchors are non-descriptive",
            description=(
                f"{generic_count:,} of {total:,} internal links use generic anchors "
                f"(\"click here\", \"read more\", etc.). Generic anchors pass no topical "
                "context to the destination. Per the May 2024 Google API leak, "
                "internal anchor text is a tiered signal — descriptive anchors carry "
                "topical relevance, generic ones do not."
            ),
            affected_urls=sample_targets,
            count=int(generic_count),
            recommendation=(
                "Rewrite generic internal anchors to describe the destination's topic. "
                "\"Read more\" → \"see our HVAC repair pricing guide\". Vary phrasing "
                "across pages — don't replace one generic anchor with the same "
                "keyword-stuffed anchor everywhere (that triggers anchor spam velocity)."
            ),
            impact=(
                "Internal links with descriptive anchors strengthen topical relevance "
                "for the destination page. Generic anchors waste internal PageRank flow."
            ),
            additional_data={
                "generic_count": int(generic_count),
                "total_anchors": int(total),
                "generic_percent": round(generic_pct, 1),
            },
        )

    def _check_anchor_concentration_per_target(self) -> None:
        """Flag pages with heavy concentration of one anchor phrase (spam velocity)."""
        if "target_url" not in self.anchors_df.columns or "anchor_text" not in self.anchors_df.columns:
            return

        df = self.anchors_df[["target_url", "anchor_text"]].copy()
        df["anchor_text"] = df["anchor_text"].astype(str).str.lower().str.strip()
        df = df[df["anchor_text"].astype(bool)]
        df = df[~df["anchor_text"].isin(GENERIC_ANCHORS)]

        target_anchor_counts = (
            df.groupby(["target_url", "anchor_text"]).size().reset_index(name="count")
        )
        target_totals = df.groupby("target_url").size().reset_index(name="total")

        merged = target_anchor_counts.merge(target_totals, on="target_url")
        merged["concentration"] = merged["count"] / merged["total"]

        suspicious = merged[(merged["total"] >= 10) & (merged["concentration"] >= 0.6)]

        if len(suspicious) == 0:
            return

        affected_urls = suspicious["target_url"].unique().tolist()[:50]

        examples = []
        for _, row in suspicious.head(5).iterrows():
            examples.append(
                f"{row['target_url']} — \"{row['anchor_text']}\" "
                f"({row['count']}/{row['total']} = {row['concentration']*100:.0f}%)"
            )

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.ANCHOR_TEXT,
            issue_type="anchor_phrase_spam_velocity",
            title=f"{len(suspicious)} pages have anchor phrase concentration ≥60%",
            description=(
                f"{len(suspicious)} target pages receive 60%+ of their inbound internal "
                "anchors using a single phrase. The May 2024 Google API leak documents "
                "phraseAnchorSpamCount/Rate/Penalty/Demoted attributes — heavy phrase "
                "concentration looks like internal-link manipulation at the algorithm "
                "level, even if the intent was benign.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected_urls,
            recommendation=(
                "Vary anchor phrasing across the linking pages. If 50 pages all link to "
                "/service-x/ with the anchor \"service x near me\", rewrite ~half to use "
                "natural variations (\"our service x team\", \"how service x works\", "
                "\"[brand]'s service x process\")."
            ),
            impact=(
                "phraseAnchorSpamPenalty / phraseAnchorSpamDemoted are algorithmic "
                "responses. Even if the page was the right destination, this pattern can "
                "trigger demotion."
            ),
            additional_data={"suspicious_target_count": len(suspicious)},
        )

    def _check_shared_anchor_across_targets(self) -> None:
        """Flag anchor phrases reused across many DISTINCT internal targets.

        This is the inverse of ``_check_anchor_concentration_per_target``: instead
        of one target attracting one dominant anchor, one anchor phrase is spread
        across a large number of different destinations. When the same anchor text
        points at ~10+ different pages, it stops describing any single page's topic
        and dilutes the internal-linking topical signal.
        """
        if (
            "anchor_text" not in self.anchors_df.columns
            or "target_url" not in self.anchors_df.columns
        ):
            return

        df = self.anchors_df[["anchor_text", "target_url"]].copy()
        df["anchor_text"] = df["anchor_text"].astype(str).str.lower().str.strip()
        df["target_url"] = df["target_url"].astype(str).str.strip()

        # Exclude blank / image anchors (image links carry alt_text, not anchor
        # text) and rows with no resolvable target.
        df = df[df["anchor_text"].astype(bool)]
        df = df[~df["anchor_text"].isin({"", "nan"})]
        df = df[df["target_url"].astype(bool)]
        df = df[~df["target_url"].isin({"", "nan"})]

        if len(df) == 0:
            return

        distinct_targets = (
            df.drop_duplicates(subset=["anchor_text", "target_url"])
            .groupby("anchor_text")["target_url"]
            .nunique()
            .reset_index(name="distinct_targets")
        )

        shared = distinct_targets[
            distinct_targets["distinct_targets"] >= SHARED_ANCHOR_TARGETS
        ].sort_values("distinct_targets", ascending=False)

        if len(shared) == 0:
            return

        max_spread = int(shared["distinct_targets"].max())
        severity = (
            Severity.HIGH
            if max_spread >= SHARED_ANCHOR_TARGETS_HIGH
            else Severity.MEDIUM
        )

        # Sample the target URLs of the worst-spread anchor for affected_urls.
        worst_anchor = shared.iloc[0]["anchor_text"]
        affected_urls = (
            df.loc[df["anchor_text"] == worst_anchor, "target_url"]
            .drop_duplicates()
            .tolist()[:50]
        )

        examples = [
            f"\"{row['anchor_text']}\" → {int(row['distinct_targets'])} distinct targets"
            for _, row in shared.head(5).iterrows()
        ]

        self.create_issue(
            severity=severity,
            category=AuditCategory.ANCHOR_TEXT,
            issue_type="shared_anchor_across_targets",
            title=(
                f"{len(shared)} anchor phrase(s) reused across "
                f"{SHARED_ANCHOR_TARGETS}+ different internal targets"
            ),
            description=(
                f"{len(shared)} internal anchor phrase(s) point at "
                f"{SHARED_ANCHOR_TARGETS} or more distinct target URLs (worst: "
                f"{max_spread} targets). This is the inverse of anchor "
                "over-concentration — the same anchor text is spread across so many "
                "different destinations that it no longer describes any one page's "
                "topic. Internal anchors are meant to pass topical context to the "
                "specific page they link to; a phrase used on 10-20 different targets "
                "dilutes that signal.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected_urls,
            recommendation=(
                "Diversify the shared anchors so each closely matches its own target "
                "page. If \"our services\" links to 15 different service pages, rewrite "
                "each link to name the specific service (\"AC repair\", \"furnace "
                "installation\", etc.) so every anchor describes its destination."
            ),
            impact=(
                "Descriptive, target-specific anchors reinforce each page's topical "
                "relevance. One anchor phrase smeared across many targets passes an "
                "ambiguous signal and weakens internal topical routing."
            ),
            additional_data={
                "shared_anchor_count": int(len(shared)),
                "max_distinct_targets": max_spread,
                "threshold": SHARED_ANCHOR_TARGETS,
                "worst_anchor": str(worst_anchor),
            },
        )

    def _check_anchor_mismatch_against_h1(self) -> None:
        """Flag anchor mismatch — inbound anchors don't topically match the H1/title."""
        if "target_url" not in self.anchors_df.columns or "anchor_text" not in self.anchors_df.columns:
            return
        if not self.has_columns(["url", "h1"]) and not self.has_columns(["url", "title"]):
            return

        page_topics = {}
        topic_col = "h1" if self.has_column("h1") else "title"
        for _, row in self.df[["url", topic_col]].dropna().iterrows():
            page_topics[str(row["url"]).strip()] = str(row[topic_col]).lower()

        if not page_topics:
            return

        mismatches = []
        anchor_groups = self.anchors_df.groupby("target_url")
        for target, group in anchor_groups:
            target_str = str(target).strip()
            if target_str not in page_topics:
                continue
            page_topic = page_topics[target_str]
            page_words = set(self._tokenize(page_topic))
            if len(page_words) == 0:
                continue

            anchors = (
                group["anchor_text"].astype(str).str.lower().str.strip().tolist()
            )
            anchors = [a for a in anchors if a and a not in GENERIC_ANCHORS]
            if len(anchors) < 5:
                continue

            overlap_scores = []
            for anchor in anchors:
                anchor_words = set(self._tokenize(anchor))
                if not anchor_words:
                    continue
                overlap = len(anchor_words & page_words) / len(anchor_words)
                overlap_scores.append(overlap)

            if not overlap_scores:
                continue
            avg_overlap = sum(overlap_scores) / len(overlap_scores)

            if avg_overlap < 0.15:
                mismatches.append({
                    "url": target_str,
                    "page_topic": page_topic[:80],
                    "anchor_count": len(anchors),
                    "avg_overlap": round(avg_overlap, 2),
                })

        if not mismatches:
            return

        affected = [m["url"] for m in mismatches[:50]]
        examples = []
        for m in mismatches[:5]:
            examples.append(
                f"{m['url']} — H1: \"{m['page_topic']}\" "
                f"({m['anchor_count']} anchors, {m['avg_overlap']*100:.0f}% topical overlap)"
            )

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.ANCHOR_TEXT,
            issue_type="anchor_mismatch_demotion_risk",
            title=f"{len(mismatches)} pages show inbound-anchor / on-page topic mismatch",
            description=(
                f"{len(mismatches)} pages receive internal anchors that don't topically "
                "match the page's H1/title. The May 2024 Google API leak documents "
                "anchorMismatchDemotion as a named demotion factor — when inbound "
                "anchor text drifts from the page's actual content, the page is "
                "demoted. This often signals content drift (page evolved away from "
                "its anchor profile) or stale internal linking.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(mismatches),
            recommendation=(
                "For each flagged page, decide: (a) rewrite the page to align with how "
                "it's being linked (if anchors reflect intent better than the H1), or "
                "(b) update the inbound internal links to use anchors that match the "
                "page's actual topic. Don't leave the mismatch — it triggers algorithmic "
                "demotion."
            ),
            impact=(
                "anchorMismatchDemotion is applied at scoring time. Pages affected by "
                "this signal underperform regardless of standalone content quality."
            ),
            additional_data={"mismatch_count": len(mismatches)},
        )

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Lightweight tokenizer for topical-overlap comparison."""
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will", "would",
            "should", "could", "may", "might", "must", "can", "this", "that",
            "these", "those", "your", "our", "their", "its",
        }
        import re as _re

        tokens = _re.findall(r"\b[a-z]+\b", text.lower())
        return [t for t in tokens if len(t) > 2 and t not in stop_words]
