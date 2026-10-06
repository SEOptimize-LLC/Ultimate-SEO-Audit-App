"""Internal Prominence Auditor (leak attribute: onsiteProminence).

Checks whether the pages you want to move get internal links from pages that earn search clicks.

Documented (leaked PerDocData.onsiteProminence): "Onsite prominence measures the importance of the document
within its site. It is computed by propagating simulated traffic from the homepage and high craps click
pages." Inferred: a page that sits close to click-earning pages in the internal link graph receives more of
that propagation, so a priority page linked only from pages nobody finds in search misses it.

Method (the reading in seo-fundamentals-2026.md, "Source Internal Links From Pages That Earn Search Clicks"):

* Priority pages: indexable pages with Search Console impressions at an average position of 4 to 20, the
  quick-win window. Weighted by impressions.
* Click-earning sources: indexable pages with at least MIN_SOURCE_CLICKS Search Console clicks in the export.
* A priority page is flagged when none of its linking pages is a click-earning source. For each, the top
  click-earning pages that do not yet link to it are listed as candidates. Topic fit is a human call.

Inputs: the crawl, the Screaming Frog internal anchor-text export, and the Search Console performance export.
When one is missing the auditor says so; it never reports a clean pass it could not compute.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from .base_auditor import BaseAuditor
from .technical_auditor import TechnicalAuditor
from models.audit_result import AuditCategory, AuditIssue, Severity
from utils.url_keys import host_key, url_key

# A source page "earns real search clicks" at or above this many clicks in the export window.
MIN_SOURCE_CLICKS = 10
# Quick-win window for priority pages (average position, impressions-weighted).
PRIORITY_POSITION_MIN = 4.0
PRIORITY_POSITION_MAX = 20.0
MAX_CANDIDATES_PER_PAGE = 5
MAX_PAGES_DESCRIBED = 10
MAX_URLS_LISTED = 100
# Template links reach every page, so they say nothing about which pages lend prominence.
EXCLUDED_LINK_POSITIONS = {"navigation", "footer"}


class InternalProminenceAuditor(BaseAuditor):
    """Flags priority pages whose internal links come from no click-earning page."""

    def __init__(
        self,
        crawl_df: pd.DataFrame,
        anchors_df: Optional[pd.DataFrame],
        gsc_df: Optional[pd.DataFrame],
    ):
        """
        Args:
            crawl_df: SF HTML Internal report.
            anchors_df: parsed SF anchor-text export (source_url, target_url, optional link_position,
                link_type, follow).
            gsc_df: parsed Search Console performance export (page, clicks, impressions, position).
        """
        super().__init__(crawl_df)
        self.anchors_df = anchors_df
        self.gsc_df = gsc_df

    def get_audit_type(self) -> str:
        return "internal_prominence"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()
        reason = self._missing_input_reason()
        if reason:
            self._emit_not_run(reason)
            return self.issues

        eligible = self._eligible_pages()
        gsc = self._gsc_by_page()
        links, positions_used, exported_targets = self._internal_links(eligible)
        inbound = links.groupby("target")["source"].agg(set).to_dict() if not links.empty else {}

        clicks = gsc["clicks"].to_dict()
        click_sources = {k for k, c in clicks.items() if c >= MIN_SOURCE_CLICKS and k in eligible}
        priority = [
            k for k, row in gsc.iterrows()
            if k in eligible and row["impressions"] > 0
            and PRIORITY_POSITION_MIN <= row["position"] <= PRIORITY_POSITION_MAX
        ]

        flagged: list[dict] = []
        unverified: list[str] = []
        for key in priority:
            sources = inbound.get(key, set())
            if sources & click_sources:
                continue
            crawl_inlinks = eligible[key].get("internal_links_in")
            if key not in exported_targets and isinstance(crawl_inlinks, (int, float)) and crawl_inlinks > 0:
                # The crawl counts inlinks to this page but the anchor export lists none at all (before any
                # filtering): the export is incomplete for this page, so calling it unlinked would be a guess.
                unverified.append(eligible[key]["url"])
                continue
            candidates = sorted(
                (s for s in click_sources if s != key and s not in sources),
                key=lambda s: clicks[s], reverse=True,
            )[:MAX_CANDIDATES_PER_PAGE]
            flagged.append({
                "url": eligible[key]["url"],
                "impressions": int(gsc.loc[key, "impressions"]),
                "position": round(float(gsc.loc[key, "position"]), 1),
                "linking_pages": len(sources),
                "candidates": [{"url": eligible[c]["url"], "clicks": int(clicks[c])} for c in candidates],
            })
        flagged.sort(key=lambda r: r["impressions"], reverse=True)

        self._emit_summary(len(priority), len(click_sources), len(flagged), len(unverified), positions_used)
        if flagged:
            self._emit_flagged(flagged)
        if unverified:
            self._emit_unverified(unverified)
        return self.issues

    # -------------------------------------------------------------------------
    # Inputs
    # -------------------------------------------------------------------------

    def _missing_input_reason(self) -> Optional[str]:
        if not self.has_column("url"):
            return "the crawl has no URL column"
        a, g = self.anchors_df, self.gsc_df
        if a is None or len(a) == 0 or not {"source_url", "target_url"} <= set(a.columns):
            return "the internal anchor-text export (source and destination URLs) was not provided"
        needed = {"page", "clicks", "impressions", "position"}
        if g is None or len(g) == 0 or not needed <= set(g.columns):
            return "the Search Console performance export (page, clicks, impressions, position) was not provided"
        return None

    def _eligible_pages(self) -> dict[str, dict]:
        """Indexable, 2xx, HTML, non-utility pages keyed by url_key, holding the crawl's own URL."""
        pages = self.get_html_pages()
        if "status_code" in pages.columns:
            pages = pages[pages["status_code"].fillna(0).astype(int).between(200, 299)]
        if "indexability" in pages.columns:
            pages = pages[pages["indexability"].fillna("").str.lower() == "indexable"]
        out: dict[str, dict] = {}
        for _, row in pages.iterrows():
            url = str(row["url"])
            if TechnicalAuditor._is_non_seo_url(url):
                continue
            entry = {"url": url}
            if "internal_links_in" in pages.columns and pd.notna(row.get("internal_links_in")):
                entry["internal_links_in"] = float(row["internal_links_in"])
            out[url_key(url)] = entry
        return out

    def _gsc_by_page(self) -> pd.DataFrame:
        """Clicks, impressions and impressions-weighted position per page key."""
        g = self.gsc_df[["page", "clicks", "impressions", "position"]].copy()
        for col in ("clicks", "impressions", "position"):
            g[col] = pd.to_numeric(g[col], errors="coerce").fillna(0)
        g["key"] = g["page"].map(url_key)
        g = g[g["key"] != ""]
        g["weighted"] = g["position"] * g["impressions"]
        grouped = g.groupby("key").agg(
            clicks=("clicks", "sum"), impressions=("impressions", "sum"), weighted=("weighted", "sum")
        )
        grouped["position"] = (grouped["weighted"] / grouped["impressions"].where(grouped["impressions"] > 0)).fillna(0)
        return grouped[["clicks", "impressions", "position"]]

    def _internal_links(self, eligible: dict[str, dict]) -> tuple[pd.DataFrame, bool, set[str]]:
        """Distinct (source, target) pairs between pages of this site, template links excluded when possible.

        Also returns every target the export lists at all, before any filtering, so a page whose only
        links were filtered out is told apart from a page the export never mentions.
        """
        a = self.anchors_df.copy()
        exported_targets = set(a["target_url"].map(url_key)) - {""}
        if "link_type" in a.columns:
            kind = a["link_type"].fillna("").astype(str).str.lower()
            a = a[(kind == "") | kind.str.startswith("hyperlink")]
        if "follow" in a.columns:
            a = a[a["follow"].astype(bool)]
        positions_used = "link_position" in a.columns
        if positions_used:
            a = a[~a["link_position"].fillna("").astype(str).str.lower().isin(EXCLUDED_LINK_POSITIONS)]
        a = a.assign(source=a["source_url"].map(url_key), target=a["target_url"].map(url_key))
        site = pd.Series([host_key(e["url"]) for e in eligible.values()]).mode()
        site_host = site.iloc[0] if len(site) else ""
        a = a[(a["source"] != "") & (a["target"] != "") & (a["source"] != a["target"])]
        a = a[a["source"].str.split("/").str[0].eq(site_host) & a["target"].str.split("/").str[0].eq(site_host)]
        return a[["source", "target"]].drop_duplicates(), positions_used, exported_targets

    # -------------------------------------------------------------------------
    # Findings
    # -------------------------------------------------------------------------

    def _emit_not_run(self, reason: str) -> None:
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.INTERNAL_LINKS,
            issue_type="internal_prominence_not_run",
            title="Internal prominence check not run",
            description=(
                f"This check needs the crawl, the internal anchor-text export and the Search Console "
                f"performance export, but {reason}. No priority page is flagged or cleared."
            ),
            recommendation="Provide the missing export to run it.",
            impact="",
        )

    def _emit_summary(self, priority: int, sources: int, flagged: int, unverified: int, positions_used: bool) -> None:
        links_note = (
            "Navigation and footer links were excluded."
            if positions_used else
            "The anchor export has no link-position column, so template links are included and may make some "
            "pages look better linked than they are."
        )
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.INTERNAL_LINKS,
            issue_type="internal_prominence_checked",
            title="Internal prominence check ran",
            description=(
                f"Checked {priority} priority pages (average position {PRIORITY_POSITION_MIN:g} to "
                f"{PRIORITY_POSITION_MAX:g}, with impressions) against {sources} pages with at least "
                f"{MIN_SOURCE_CLICKS} search clicks. {flagged} flagged, {unverified} not verifiable. {links_note}"
            ),
            recommendation="No action.",
            impact="",
        )

    def _emit_flagged(self, flagged: list[dict]) -> None:
        lines = []
        for r in flagged[:MAX_PAGES_DESCRIBED]:
            cand = ", ".join(f"{c['url']} ({c['clicks']} clicks)" for c in r["candidates"]) or "none available"
            lines.append(
                f"{r['url']}: position {r['position']}, {r['impressions']} impressions, linked from "
                f"{r['linking_pages']} pages, none earning clicks. Candidate linking pages: {cand}"
            )
        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.INTERNAL_LINKS,
            issue_type="priority_pages_without_click_sourced_links",
            title=f"{len(flagged)} priority pages get no internal links from pages that earn search clicks",
            description=(
                f"{len(flagged)} pages rank at positions {PRIORITY_POSITION_MIN:g} to {PRIORITY_POSITION_MAX:g} "
                f"but none of their internal links comes from a page with at least {MIN_SOURCE_CLICKS} search "
                "clicks. Documented: per the May 2024 Google API leak, onsiteProminence measures a page's "
                "importance within its site and is computed by propagating simulated traffic from the homepage "
                "and high-click pages. Inferred: pages near click-earning pages in the link graph receive more "
                "of it. Largest first: " + " | ".join(lines)
            ),
            affected_urls=[r["url"] for r in flagged][:MAX_URLS_LISTED],
            recommendation=(
                "For each page, add contextual links from the listed candidate pages that are on a related "
                "topic, with anchor text that matches the target page's topic. Candidates are ranked by "
                "clicks only, so judge topic fit before adding a link, and skip any that would not read "
                "naturally. Record each source page's clicks next to the proposed link so the link map "
                "sorts by value."
            ),
            impact=(
                "These pages are close to page one but sit away from the pages that carry the site's search "
                "traffic. More links from click-earning pages is the documented lever that fits; the ranking "
                "effect is inferred, not measured."
            ),
            additional_data={
                "min_source_clicks": MIN_SOURCE_CLICKS,
                "position_window": [PRIORITY_POSITION_MIN, PRIORITY_POSITION_MAX],
                "pages": flagged,
            },
        )

    def _emit_unverified(self, urls: list[str]) -> None:
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.INTERNAL_LINKS,
            issue_type="internal_prominence_unverified",
            title=f"{len(urls)} priority pages could not be verified",
            description=(
                f"The crawl counts internal links to {len(urls)} priority pages, but the anchor-text export "
                "lists none for them, so the export looks incomplete for these pages. They are neither "
                "flagged nor cleared."
            ),
            affected_urls=urls[:MAX_URLS_LISTED],
            recommendation="Re-export the full internal anchor-text report and re-run the check.",
            impact="",
        )
