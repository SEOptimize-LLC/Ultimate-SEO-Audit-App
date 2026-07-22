"""Build Beehive Plumbing — Keyword Cannibalization Tracker (Excel).

Source: _cannibalization_data/_step6_clusters_full_export.json
Output: Clients/Beehive/Full Site SEO Audit/beehive_keyword_cannibalization_tracker.xlsx

Tabs:
  1. Summary             - Headline counts, methodology, how to read
  2. REVIEW              - Likely false-positive clusters (manual review)
  3. Priority A Top-3    - Highest-damage clusters (top-3 ranking)
  4. Priority A          - All money keyword + top-10 clusters
  5. Priority B          - Partial-criteria clusters
  6. Priority C          - Low-ROI clusters
  7. All Clusters        - Full cluster list with all data columns
  8. URL Frequency       - Which URLs appear in the most clusters
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT / "Clients" / "Beehive" / "Full Site SEO Audit"
    / "_cannibalization_data" / "_step6_clusters_full_export.json"
)
OUTPUT = (
    ROOT / "Clients" / "Beehive" / "Full Site SEO Audit"
    / "beehive_keyword_cannibalization_tracker.xlsx"
)


def _resolve_output_path(base: Path) -> Path:
    """If the target file is locked (open in Excel), fall back to a
    suffixed filename so the build still completes."""
    try:
        # Try to open the file for writing — if locked, this fails
        with base.open("a"):
            pass
        return base
    except (PermissionError, OSError):
        suffix = base.stem + "_updated" + base.suffix
        return base.with_name(suffix)

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
PRIORITY_A_FILL = PatternFill("solid", fgColor="C00000")
PRIORITY_B_FILL = PatternFill("solid", fgColor="ED7D31")
PRIORITY_C_FILL = PatternFill("solid", fgColor="A6A6A6")
REVIEW_FILL = PatternFill("solid", fgColor="6F42C1")
TOP_3_FILL = PatternFill("solid", fgColor="8B0000")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row: int = 1) -> None:
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )
        cell.border = BORDER
    ws.row_dimensions[row].height = 38


def autosize(ws, min_w: int = 10, max_w: int = 70) -> None:
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        longest = 0
        for cell in col:
            if cell.value is None:
                continue
            longest = max(longest, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(
            max(min_w, longest + 2), max_w
        )


def wrap(ws, start_row: int = 2) -> None:
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def fmt_pos(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.1f}"
    except (TypeError, ValueError):
        return str(v)


def fmt_int(v: Any) -> Any:
    return v if v else ""


def write_summary(wb: Workbook, payload: dict) -> None:
    ws = wb.active
    ws.title = "Summary"

    counts = payload.get("tier_counts", {})
    top3 = payload.get("top_3_priority_a_count", 0)
    total = payload.get("total_clusters", 0)
    arch_fix = payload.get("architecture_fix_count", 0)
    aligned = payload.get("winner_aligned_count", 0)
    geo_m = payload.get("geo_mismatch_count", 0)
    svc_m = payload.get("service_mismatch_count", 0)
    both_m = payload.get("both_mismatch_count", 0)

    rows = [
        ["Beehive Plumbing — Keyword Cannibalization Tracker", ""],
        ["Client", "Beehive Plumbing (beehiveplumbing.com)"],
        ["Report Date", "April 30, 2026"],
        ["Total Cannibalization Clusters Detected", total],
        ["", ""],
        ["Priority Breakdown", ""],
        ["Priority A — money keyword + top-10 ranking", counts.get("A", 0)],
        ["    of which top-3 ranking (most damaging)", top3],
        ["Priority B — money keyword OR top-10, not both", counts.get("B", 0)],
        ["Priority C — informational at deep position", counts.get("C", 0)],
        ["REVIEW — likely false positives (manual review required)", counts.get("REVIEW", 0)],
        ["", ""],
        ["Winner Alignment Check", ""],
        ["Auditor's winner is correctly aligned with query", aligned],
        ["Geographic mismatch (winner targets wrong city/area)", geo_m],
        ["Service mismatch (winner is generic / non-service page)", svc_m],
        ["Both geographic AND service mismatched", both_m],
        ["Architecture fix recommended (canonical page exists, not winning)", arch_fix],
        ["", ""],
        ["What This Means", ""],
        [
            "Cannibalization",
            "Multiple URLs from beehiveplumbing.com competing for the same query, splitting ranking signals.",
        ],
        [
            "Why it matters",
            "Google rotates between competing pages. Neither ranks consistently. Top-3 cannibalization directly costs clicks because real visibility is being diluted.",
        ],
        [
            "The fix",
            "Pick one winner per cluster. Merge unique content from losers into the winner. 301-redirect losers. Update internal links. Do NOT 'just improve both pages' — that makes it worse.",
        ],
        ["", ""],
        ["How to Read This File", ""],
        [
            "REVIEW tab",
            "Look at this FIRST. These clusters are likely false positives — ambiguous seed queries (single-word terms with mixed-intent SERPs) where cluster URLs target meaningfully different topics. Manually review each before any consolidation work. The recommendation for most of these is 'skip'.",
        ],
        [
            "Architecture Fix tab",
            "Look at this SECOND. These are clusters where the auditor's automatic winner is misaligned with the query — wrong city, generic page (homepage/About), or non-service page. A more architecturally correct page exists elsewhere on the site. The fix is content + internal linking, NOT redirecting to the auditor's winner.",
        ],
        [
            "Priority A Top-3 tab",
            "Highest-damage real cannibalization. Fix these first — at least one URL is in positions 1-3, where rotation directly costs clicks.",
        ],
        [
            "Priority A tab",
            "All money keyword clusters with at least one URL in top-10. Includes the top-3 set. Fix in the order shown.",
        ],
        [
            "Priority B tab",
            "Clusters with either money intent OR top-10 ranking, but not both. Address as bandwidth allows.",
        ],
        [
            "Priority C tab",
            "Informational queries at deep positions. Usually skip — low ROI to fix.",
        ],
        [
            "All Clusters tab",
            "Full cluster list with all data columns including REVIEW tier.",
        ],
        [
            "URL Frequency tab",
            "Which URLs appear in the most clusters. Identifies systemic issues (e.g., homepage competing across many service queries).",
        ],
        ["", ""],
        ["Key Architectural Findings", ""],
        [
            "Homepage cannibalization",
            "The homepage (/) appears in 14 of 23 Priority A clusters. It's competing with service pages on service-specific commercial queries. Fix: tighten homepage content + improve internal links to service pages.",
        ],
        [
            "Salt Lake City redirect chain",
            "A SLC city page exists at /plumbing-salt-lake-city-ut/ but is buried behind a multi-hop HTTPS-HTTP redirect chain. Fix this before resolving SLC-related clusters.",
        ],
        [
            "Service vs blog overlap",
            "Several clusters mix service pages with blog posts. Decide per cluster: differentiate (informational vs commercial) or consolidate to service page.",
        ],
        ["", ""],
        ["Winner Selection Rule", ""],
        [
            "Multi-factor (in order)",
            "1. Best current GSC position. 2. Most 90-day clicks. 3. Most backlinks. 4. Tiebreaker: fewer internal links to update.",
        ],
        [
            "Manual review note",
            "The auditor's automated winner-selection should be reviewed manually for content fit. Some winners need overriding (e.g., the flushometer cluster — see report).",
        ],
        ["", ""],
        ["Resolution Paths (in order of preference)", ""],
        [
            "1. Consolidate",
            "Pick winner. Merge unique content from losers. 301-redirect losers. Update internal links. Most common, most effective.",
        ],
        [
            "2. Differentiate",
            "When both pages should genuinely exist (informational + commercial). Rewrite each to target distinct intent.",
        ],
        [
            "3. Canonicalize",
            "Hub + deep-dive coexistence. Canonicals are hints, not commands. Less reliable than 301.",
        ],
        [
            "4. Republish under new slug",
            "Last resort. When consolidation hasn't moved rankings within 30 days because Google's duplicate cluster is stuck on old slugs.",
        ],
    ]
    for row in rows:
        ws.append(row)

    ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
    # Section header rows: Priority Breakdown, Winner Alignment Check,
    # What This Means, How to Read This File, Key Architectural Findings,
    # Winner Selection Rule, Resolution Paths
    for r in (6, 13, 20, 25, 35, 40, 44):
        for cell in ws[r]:
            cell.fill = HEADER_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)
        ws.row_dimensions[r].height = 22

    ws.column_dimensions["A"].width = 56
    ws.column_dimensions["B"].width = 95
    wrap(ws, start_row=1)


def cluster_row_simple(cluster: dict) -> list:
    """Single-row summary per cluster.

    Override logic: when the auditor's metric-based pick fails the
    alignment check AND a more architecturally correct page exists,
    the canonical recommendation becomes the architecturally correct
    page. The metric-based pick is preserved in a separate column for
    transparency. When no override applies, the metric-based pick IS
    the canonical recommendation and the override column is blank.
    """
    metric_pick = cluster.get("winner_candidate") or {}
    metric_pick_url = metric_pick.get("url", "")

    arch_page = cluster.get("architecturally_correct_page") or {}
    arch_url = arch_page.get("url", "") if arch_page else ""
    arch_strength = arch_page.get("match_strength") if arch_page else None
    arch_fix = bool(cluster.get("architecture_fix_recommended"))

    sanity_flag = cluster.get("winner_sanity_flag", "")
    tier = cluster.get("priority_tier", "—")

    # Determine the recommended canonical and the alignment note.
    # REVIEW tier: skip the recommendation entirely.
    if tier == "REVIEW":
        recommended_canonical = ""
        alignment_note = "n/a — manual review required (REVIEW tier)"
        metric_pick_display = metric_pick_url
    elif arch_fix and arch_url:
        # Override applies — canonical is the architecturally correct page
        recommended_canonical = arch_url
        if sanity_flag == "geo_mismatch":
            reason = "wrong city"
        elif sanity_flag == "service_mismatch":
            reason = "not a service page"
        elif sanity_flag == "both_mismatch":
            reason = "wrong city AND not a service page"
        else:
            reason = "alignment failed"
        strength_str = (
            f", canonical strength {arch_strength:.2f}"
            if arch_strength is not None else ""
        )
        alignment_note = (
            f"OVERRIDE — metric pick was {reason}{strength_str}"
        )
        metric_pick_display = metric_pick_url
    else:
        # No override — metric pick IS the canonical recommendation
        recommended_canonical = metric_pick_url
        alignment_label_map = {
            "aligned": "OK — metric pick matches query",
            "skipped_no_modifiers": "n/a (no geo/service modifiers)",
            "skipped_by_detection_method": "n/a",
            "no_winner": "n/a (no metric-based pick)",
            # When there's a mismatch but NO arch-correct page found
            "geo_mismatch": "FLAG — geo mismatch but no canonical page found on site",
            "service_mismatch": "FLAG — service mismatch but no canonical page found on site",
            "both_mismatch": "FLAG — both mismatch but no canonical page found on site",
            "": "",
        }
        alignment_note = alignment_label_map.get(sanity_flag, sanity_flag)
        metric_pick_display = ""  # Same as canonical — no need to repeat

    other_urls = [
        u.get("url", "") for u in cluster.get("urls", [])
        if u.get("url") and u.get("url") != metric_pick_url
    ]
    other_urls_str = "\n".join(other_urls[:6])
    if len(other_urls) > 6:
        other_urls_str += f"\n...and {len(other_urls) - 6} more"

    return [
        tier,
        "Yes" if cluster.get("in_top_3") else "",
        cluster.get("key", ""),
        cluster.get("total_impressions") or 0,
        cluster.get("total_clicks") or 0,
        fmt_pos(cluster.get("best_position")),
        len(cluster.get("urls", [])),
        "Yes" if cluster.get("is_commercial") else "",
        recommended_canonical,
        alignment_note,
        metric_pick_display,
        fmt_pos(metric_pick.get("position")),
        metric_pick.get("clicks") if metric_pick else "",
        f"{int(metric_pick.get('backlinks', 0)):,}" if metric_pick else "",
        other_urls_str,
        cluster.get("detection_method", ""),
    ]


def write_cluster_tab(
    wb: Workbook,
    name: str,
    clusters: list[dict],
    fill: PatternFill | None = None,
) -> None:
    ws = wb.create_sheet(name)
    headers = [
        "Tier",
        "Top-3?",
        "Query (Cluster Key)",
        "Impressions 90d",
        "Clicks 90d",
        "Best Position",
        "URL Count",
        "Commercial?",
        "Recommended Canonical",
        "Alignment Note",
        "Metric-Based Pick (Pre-Override)",
        "Metric-Pick Pos",
        "Metric-Pick Clicks",
        "Metric-Pick Backlinks",
        "Other Competing URLs",
        "Detection Method",
    ]
    ws.append(headers)
    style_header(ws)

    for cluster in clusters:
        row = cluster_row_simple(cluster)
        ws.append(row)

    if fill is not None:
        for row_cells in ws.iter_rows(min_row=2, min_col=1, max_col=1):
            for cell in row_cells:
                cell.fill = fill
                cell.font = Font(bold=True, color="FFFFFF", size=11)
                cell.alignment = Alignment(horizontal="center", vertical="center")

    # Top-3 column highlight
    for row_cells in ws.iter_rows(min_row=2, min_col=2, max_col=2):
        for cell in row_cells:
            if cell.value == "Yes":
                cell.fill = TOP_3_FILL
                cell.font = Font(bold=True, color="FFFFFF", size=11)
                cell.alignment = Alignment(horizontal="center", vertical="center")

    autosize(ws, min_w=10, max_w=70)
    wrap(ws, start_row=2)
    ws.freeze_panes = "C2"


def write_review_tab(wb: Workbook, clusters: list[dict]) -> None:
    """REVIEW tier — clusters flagged as likely false positives.

    Different column structure than the priority tabs because the
    actionable info is the review reason, the original tier, and the
    cluster URLs (not the auditor's automated winner candidate, which
    isn't meaningful for false positives).
    """
    ws = wb.create_sheet("REVIEW")
    headers = [
        "Query (Seed Term)",
        "Original Tier (Pre-Filter)",
        "Impressions 90d",
        "Clicks 90d",
        "Best Position",
        "URL Count",
        "Why Flagged",
        "URLs in Cluster",
        "Recommended Action",
    ]
    ws.append(headers)
    style_header(ws)

    review_clusters = [
        c for c in clusters if c.get("priority_tier") == "REVIEW"
    ]
    review_clusters.sort(key=lambda c: -(c.get("total_impressions") or 0))

    for c in review_clusters:
        urls_str = "\n".join(
            u.get("url", "") for u in c.get("urls", [])[:6]
        )
        if len(c.get("urls", [])) > 6:
            urls_str += f"\n...and {len(c['urls']) - 6} more"

        why = (
            "Ambiguous seed query (≤2 words, no service/geo/intent "
            "modifiers) AND cluster URLs target meaningfully different "
            "topics. Likely a false positive — URLs may be answering "
            "different intents within a mixed-intent SERP."
        )

        # Per-cluster recommended action based on the query shape
        key = (c.get("key") or "").lower()
        if "beehive" in key:
            action = (
                "SKIP. Branded query — multiple URLs from beehiveplumbing.com "
                "legitimately rank for the brand name (homepage, contact, city pages). "
                "Expected pattern, not cannibalization."
            )
        elif key == "plumber":
            action = (
                "SKIP. The two ranking URLs are city service pages "
                "(West Valley City and Orem) targeting different geo-intents. "
                "Geo-sibling pattern — not cannibalization."
            )
        elif key == "flushometer":
            action = (
                "SKIP. The dedicated flushometer page answers the definitional "
                "query; the pressure-assisted-toilets page answers the adjacent "
                "topic. Both are also cited inside Google's AI Overview for related "
                "queries — DO NOT redirect either page."
            )
        elif key == "manabloc":
            action = (
                "REVIEW + DIFFERENTIATE if needed. One page is informational, "
                "one is commercial-Utah. Likely keep both with cross-page internal "
                "links, not consolidate."
            )
        elif key == "bidet toilet":
            action = (
                "SKIP. Two informational blog posts on different bidet angles "
                "(misconceptions vs how-to). Different intents within an "
                "informational SERP."
            )
        elif key == "flush":
            action = (
                "SKIP. Extremely ambiguous single-word seed. Two pages on "
                "different topics (pressure-assisted toilets vs toilet "
                "flushing problems). Not cannibalization."
            )
        elif key == "home repiping":
            action = (
                "REVIEW. Borderline case — 'repiping' is technically a service term. "
                "Manual look at homepage vs /repiping-a-house/ to verify whether "
                "the homepage is legitimately answering a different intent or "
                "should be tightened to push the query to the service page."
            )
        else:
            action = (
                "Manual review required. Check whether the URLs are competing "
                "for the same intent (true cannibalization) or answering "
                "different intents within a mixed-intent SERP (skip)."
            )

        ws.append([
            c.get("key", ""),
            c.get("original_priority_tier") or "—",
            c.get("total_impressions") or 0,
            c.get("total_clicks") or 0,
            fmt_pos(c.get("best_position")),
            len(c.get("urls", [])),
            why,
            urls_str,
            action,
        ])

    # REVIEW fill on the query column
    for row_cells in ws.iter_rows(min_row=2, min_col=1, max_col=1):
        for cell in row_cells:
            cell.fill = REVIEW_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)

    autosize(ws, min_w=12, max_w=70)
    wrap(ws, start_row=2)
    ws.freeze_panes = "B2"


def write_architecture_fix_tab(
    wb: Workbook, clusters: list[dict]
) -> None:
    """Architecture-fix tab: clusters where the auditor's automatic
    winner is misaligned with the query AND a more architecturally
    correct page exists elsewhere on the site.

    The actionable column is 'Recommended Canonical Page' — the page
    that should actually own this query. The recommendation is NOT to
    consolidate to the auditor's winner. It's to strengthen the
    canonical page and pull the cluster URLs off the query.
    """
    ws = wb.create_sheet("Architecture Fix")
    headers = [
        "Tier",
        "Query",
        "Impressions 90d",
        "Best Position",
        "Recommended Canonical",
        "Match Strength",
        "Metric-Based Pick (Wrong)",
        "Why the Metric Pick Is Wrong",
        "Other Cluster URLs",
        "Recommended Action",
    ]
    ws.append(headers)
    style_header(ws)

    arch_clusters = [
        c for c in clusters
        if c.get("architecture_fix_recommended")
    ]
    arch_clusters.sort(key=lambda c: -(c.get("total_impressions") or 0))

    for c in arch_clusters:
        winner = c.get("winner_candidate") or {}
        arch = c.get("architecturally_correct_page") or {}
        alignment = c.get("winner_query_alignment") or {}

        why_wrong_parts = []
        if alignment.get("geo_mismatch_reason"):
            why_wrong_parts.append(
                f"Geography: {alignment['geo_mismatch_reason']}"
            )
        if alignment.get("service_mismatch_reason"):
            why_wrong_parts.append(
                f"Service: {alignment['service_mismatch_reason']}"
            )
        why_wrong = "\n\n".join(why_wrong_parts)

        other_urls = [
            u.get("url", "") for u in c.get("urls", [])
            if u.get("url") and u.get("url") != winner.get("url")
        ]
        other_urls_str = "\n".join(other_urls[:6])
        if len(other_urls) > 6:
            other_urls_str += f"\n...and {len(other_urls) - 6} more"

        action = (
            "1. Strengthen the canonical page (improve content depth, "
            "add geo signals if needed). 2. Tighten the cluster URLs "
            "so they no longer compete on this query — remove copy "
            "that targets the query intent, update internal links to "
            "point to the canonical page. 3. Do NOT 301-redirect the "
            "auditor's winner to the canonical page — these aren't "
            "duplicate content, they're misaligned ranking signals. "
            "The fix is content + linking, not redirects."
        )

        ws.append([
            c.get("priority_tier", "—"),
            c.get("key", ""),
            c.get("total_impressions") or 0,
            fmt_pos(c.get("best_position")),
            arch.get("url", ""),
            f"{arch.get('match_strength', 0):.2f}" if arch else "",
            winner.get("url", ""),
            why_wrong,
            other_urls_str,
            action,
        ])

    # Color code by tier
    tier_colors = {
        "A": PRIORITY_A_FILL,
        "B": PRIORITY_B_FILL,
        "C": PRIORITY_C_FILL,
    }
    for row_idx, c in enumerate(arch_clusters, start=2):
        tier = c.get("priority_tier", "")
        fill = tier_colors.get(tier)
        if fill:
            cell = ws.cell(row=row_idx, column=1)
            cell.fill = fill
            cell.font = Font(bold=True, color="FFFFFF", size=11)
            cell.alignment = Alignment(
                horizontal="center", vertical="center"
            )

    autosize(ws, min_w=12, max_w=70)
    wrap(ws, start_row=2)
    ws.freeze_panes = "C2"


def write_url_frequency(wb: Workbook, clusters: list[dict]) -> None:
    """Which URLs appear in the most clusters — surfaces systemic issues."""
    ws = wb.create_sheet("URL Frequency")
    headers = [
        "URL",
        "Total Cluster Appearances",
        "In Priority A",
        "In Priority A Top-3",
        "Total Combined Impressions",
        "Notes",
    ]
    ws.append(headers)
    style_header(ws)

    counter: Counter = Counter()
    a_counter: Counter = Counter()
    top3_counter: Counter = Counter()
    impressions: dict[str, int] = {}

    for c in clusters:
        for u in c.get("urls", []):
            url = u.get("url")
            if not url:
                continue
            counter[url] += 1
            impressions[url] = impressions.get(url, 0) + (c.get("total_impressions") or 0)
            if c.get("priority_tier") == "A":
                a_counter[url] += 1
                if c.get("in_top_3"):
                    top3_counter[url] += 1

    sorted_urls = sorted(
        counter.items(),
        key=lambda x: (-a_counter.get(x[0], 0), -x[1]),
    )
    for url, total in sorted_urls:
        notes = ""
        if url == "https://www.beehiveplumbing.com/":
            notes = "Homepage. Tighten content + internal linking to push service queries to dedicated service pages."
        elif "/plumbing-" in url and url.endswith("-ut/") or url.endswith("-utah/"):
            notes = "City service page. Verify content depth matches service-page quality."
        elif "/water-heater" in url:
            notes = "Water heater service or content page. Aligns with Roadmap #7 consolidation work."

        ws.append([
            url,
            total,
            a_counter.get(url, 0),
            top3_counter.get(url, 0),
            f"{impressions.get(url, 0):,}",
            notes,
        ])

    autosize(ws, min_w=12, max_w=70)
    wrap(ws, start_row=2)
    ws.freeze_panes = "B2"


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    clusters = payload.get("clusters", [])

    a_clusters = [c for c in clusters if c.get("priority_tier") == "A"]
    top3_a = [c for c in a_clusters if c.get("in_top_3")]
    b_clusters = [c for c in clusters if c.get("priority_tier") == "B"]
    c_clusters = [c for c in clusters if c.get("priority_tier") == "C"]

    wb = Workbook()
    write_summary(wb, payload)
    # REVIEW tab first — it's the "look here first before consolidating"
    # set, ensures the user sees false-positive flags before action tabs
    write_review_tab(wb, clusters)
    # Architecture Fix tab next — clusters where the auditor's winner
    # is misaligned and a more architecturally correct page exists
    write_architecture_fix_tab(wb, clusters)
    write_cluster_tab(wb, "Priority A Top-3", top3_a, TOP_3_FILL)
    write_cluster_tab(wb, "Priority A", a_clusters, PRIORITY_A_FILL)
    write_cluster_tab(wb, "Priority B", b_clusters, PRIORITY_B_FILL)
    write_cluster_tab(wb, "Priority C", c_clusters, PRIORITY_C_FILL)
    write_cluster_tab(wb, "All Clusters", clusters)
    write_url_frequency(wb, clusters)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    target = _resolve_output_path(OUTPUT)
    wb.save(target)
    print(f"Wrote {target}")
    if target != OUTPUT:
        print(
            f"NOTE: original target was locked (likely open in Excel). "
            f"Saved as fallback filename. Close the original file to "
            f"replace it, then re-run."
        )


if __name__ == "__main__":
    main()
