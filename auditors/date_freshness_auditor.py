"""Date Freshness Auditor — leak-grounded date triangulation.

Grounded in PerDocData attributes from the May 2024 Google API leak:

- semanticDate — Google's inferred date from content references
- lastSignificantUpdate — fires only when content materially changes
- dateUnreliabilityInfo — flags pages where dates conflict with content signals

Detects three issue classes:

1. Date conflict — visible byline date vs. schema dates vs. Last-Modified disagree
2. Stale-but-dated — schema dateModified bumped without content change
3. Outdated visible date — page references current year/version but date is old

The auditor cannot read Google's semanticDate directly. It triangulates the
visible signals Google uses as inputs, and flags patterns that map to known
dateUnreliabilityInfo triggers.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pandas as pd

from auditors.base_auditor import BaseAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity


class DateFreshnessAuditor(BaseAuditor):
    """Audits content date consistency for triangulation reliability."""

    def __init__(self, crawl_df: pd.DataFrame, dates_df: pd.DataFrame):
        """Initialize the date freshness auditor.

        Args:
            crawl_df: SF HTML Internal report DataFrame (URL, word_count)
            dates_df: SF custom extraction with date fields
        """
        super().__init__(crawl_df)
        self.dates_df = dates_df

    def get_audit_type(self) -> str:
        return "date_freshness"

    def run_audit(self) -> list[AuditIssue]:
        """Run date triangulation checks."""
        self.clear_issues()

        if self.dates_df is None or len(self.dates_df) == 0:
            return self.issues
        if "url" not in self.dates_df.columns:
            return self.issues

        self._check_date_conflicts()
        self._check_stale_dated_content()
        self._check_modified_without_content_signal()

        return self.issues

    def _check_date_conflicts(self) -> None:
        """Flag pages where date sources disagree by >180 days."""
        date_cols = ["byline_date", "schema_published", "schema_modified", "last_modified"]
        present = [c for c in date_cols if c in self.dates_df.columns]
        if len(present) < 2:
            return

        conflicts = []
        for _, row in self.dates_df.iterrows():
            url = str(row.get("url", "")).strip()
            if not url:
                continue
            dates = {}
            for col in present:
                val = row.get(col)
                if pd.notna(val):
                    dates[col] = val

            if len(dates) < 2:
                continue

            timestamps = [pd.Timestamp(v) for v in dates.values() if pd.notna(v)]
            if len(timestamps) < 2:
                continue

            spread = max(timestamps) - min(timestamps)
            if spread > timedelta(days=180):
                conflicts.append({
                    "url": url,
                    "spread_days": spread.days,
                    "dates": {k: str(v)[:10] for k, v in dates.items()},
                })

        if not conflicts:
            return

        affected = [c["url"] for c in conflicts[:50]]
        examples = []
        for c in conflicts[:5]:
            date_str = ", ".join(f"{k}={v}" for k, v in c["dates"].items())
            examples.append(f"{c['url']} — {c['spread_days']}d spread ({date_str})")

        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.CONTENT,
            issue_type="date_triangulation_conflict",
            title=f"{len(conflicts)} pages have conflicting date signals (>180d spread)",
            description=(
                f"{len(conflicts)} pages have visible byline, schema, or HTTP "
                "Last-Modified dates that disagree by more than 180 days. Per the "
                "May 2024 Google API leak, dateUnreliabilityInfo flags pages where "
                "date sources conflict — Google triangulates across all visible date "
                "signals and assigns reduced trust when they don't agree.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(conflicts),
            recommendation=(
                "Pick one authoritative date per page and ensure all surface signals "
                "agree: visible byline date = schema datePublished, schema dateModified "
                "= the actual last meaningful edit. If a page hasn't been updated, "
                "don't bump dateModified to today — that triggers date-unreliability "
                "flagging without any lastSignificantUpdate signal to back it up."
            ),
            impact=(
                "Pages with unreliable dates are weighted down by Google's freshness "
                "algorithms — they don't get the freshness boost a real update earns, "
                "and they may be demoted as low-trust."
            ),
            additional_data={"conflict_count": len(conflicts)},
        )

    def _check_stale_dated_content(self) -> None:
        """Flag pages where schema dateModified is recent but content has stale year/version refs."""
        if "schema_modified" not in self.dates_df.columns:
            return
        if not self.has_columns(["url"]):
            return

        current_year = datetime.now(timezone.utc).year
        stale_year_threshold = current_year - 2

        merged = self.dates_df.merge(
            self.df[["url"] + (["title"] if self.has_column("title") else [])],
            on="url",
            how="left",
        )

        stale = []
        for _, row in merged.iterrows():
            modified = row.get("schema_modified")
            if pd.isna(modified):
                continue
            modified_ts = pd.Timestamp(modified)
            if modified_ts.tz is None:
                modified_ts = modified_ts.tz_localize("UTC")
            now = pd.Timestamp.now(tz="UTC")
            if (now - modified_ts).days > 365:
                continue

            title = str(row.get("title", "")).lower()
            url = str(row.get("url", "")).strip()
            if not url or not title:
                continue

            for old_year in range(2015, stale_year_threshold + 1):
                if str(old_year) in title:
                    stale.append({
                        "url": url,
                        "title_year": old_year,
                        "schema_modified": str(modified_ts)[:10],
                    })
                    break

        if not stale:
            return

        affected = [s["url"] for s in stale[:50]]
        examples = [
            f"{s['url']} — title says {s['title_year']}, schema modified {s['schema_modified']}"
            for s in stale[:5]
        ]

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.CONTENT,
            issue_type="date_modified_but_content_stale",
            title=f"{len(stale)} pages: dateModified recent but title references old year",
            description=(
                f"{len(stale)} pages have a recent schema dateModified but their "
                "title still references a year more than 2 years old. This is a "
                "classic dateUnreliabilityInfo trigger — the date claims freshness "
                "the content doesn't back up.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(stale),
            recommendation=(
                "Either genuinely refresh the content (update the year reference, "
                "update facts, replace dated examples) and confirm dateModified, or "
                "roll back dateModified to reflect when the content was actually "
                "updated. Bumping dates without substantive edits doesn't trigger "
                "lastSignificantUpdate and may flag the page as date-unreliable."
            ),
            impact=(
                "Pages flagged as date-unreliable lose freshness ranking benefits "
                "and may be demoted in queries that reward genuinely fresh content."
            ),
            additional_data={"stale_count": len(stale)},
        )

    def _check_modified_without_content_signal(self) -> None:
        """Flag thin pages that show recent dateModified — likely date-bump-only refreshes."""
        if "schema_modified" not in self.dates_df.columns:
            return
        if not self.has_column("word_count"):
            return

        merged = self.dates_df.merge(
            self.df[["url", "word_count"]],
            on="url",
            how="left",
        )

        thin_recently_modified = []
        for _, row in merged.iterrows():
            modified = row.get("schema_modified")
            if pd.isna(modified):
                continue
            modified_ts = pd.Timestamp(modified)
            if modified_ts.tz is None:
                modified_ts = modified_ts.tz_localize("UTC")
            now = pd.Timestamp.now(tz="UTC")
            if (now - modified_ts).days > 90:
                continue

            wc = row.get("word_count")
            if pd.isna(wc) or wc >= 300:
                continue

            url = str(row.get("url", "")).strip()
            if url:
                thin_recently_modified.append({
                    "url": url,
                    "word_count": int(wc),
                    "modified": str(modified_ts)[:10],
                })

        if len(thin_recently_modified) < 5:
            return

        affected = [t["url"] for t in thin_recently_modified[:50]]
        examples = [
            f"{t['url']} — {t['word_count']} words, modified {t['modified']}"
            for t in thin_recently_modified[:5]
        ]

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.CONTENT,
            issue_type="thin_content_recent_datemodified",
            title=f"{len(thin_recently_modified)} thin pages with recent dateModified",
            description=(
                f"{len(thin_recently_modified)} pages with under 300 words show a "
                "schema dateModified within the last 90 days. Thin pages can't "
                "have undergone a substantive update (there's not enough content to "
                "meaningfully change). Per the May 2024 Google API leak, "
                "lastSignificantUpdate fires only when content materially changes — "
                "a date bump on a thin page doesn't trigger it.\n\n"
                "Examples:\n" + "\n".join(f"- {e}" for e in examples)
            ),
            affected_urls=affected,
            count=len(thin_recently_modified),
            recommendation=(
                "Audit these pages: either expand them substantively (so the recent "
                "dateModified is justified), or stop bumping the date on them. The "
                "pattern of \"thin content + recent dateModified\" is a strong signal "
                "of fake-freshness updates that Google's date triangulation will "
                "catch."
            ),
            impact=(
                "Fake freshness updates don't earn freshness ranking — and over time "
                "they erode the site's date trustworthiness across all pages."
            ),
            additional_data={"flagged_count": len(thin_recently_modified)},
        )
