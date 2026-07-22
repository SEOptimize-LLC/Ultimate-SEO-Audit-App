"""Build the Beehive Keyword Trajectory Tracker Excel deliverable.

Source: _trajectory_data_v2/_step8_master_watchlist_local.json (GSC + live SERP +
Salt Lake City / Utah keyword metrics merged).

Output: Clients/Beehive/Full Site SEO Audit/beehive_keyword_trajectory_tracker.xlsx

Tabs:
  1. Summary               - Headline counts and how to read the file
  2. Watchlist             - All 40 keywords, ranking-first column order
  3. Lost Tankless Cluster - Priority A: 8 keywords absent from live SLC SERP
  4. Map Pack-Only         - Priority A: 6 keywords with attribution gap
  5. Active Trajectory     - Priority B: 6 keywords with movement
  6. AI Overview Wins      - Priority B: 6 keywords cited in AI Overview

Design rules:
- Rankings first, metrics support. Ranking columns lead.
- Plain-English status labels. No flag-style raw values.
- No internal-process language anywhere.
- All metrics use Salt Lake City first, Utah state-level fallback per keyword.
  Each keyword's geography is shown explicitly so the reader knows what level of
  data they're looking at.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT
    / "Clients"
    / "Beehive"
    / "Full Site SEO Audit"
    / "_trajectory_data_v2"
    / "_step8_master_watchlist_local.json"
)
OUTPUT = (
    ROOT
    / "Clients"
    / "Beehive"
    / "Full Site SEO Audit"
    / "beehive_keyword_trajectory_tracker.xlsx"
)

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
PRIORITY_A_FILL = PatternFill("solid", fgColor="C00000")
PRIORITY_B_FILL = PatternFill("solid", fgColor="ED7D31")
PROTECT_FILL = PatternFill("solid", fgColor="2E7D32")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

TANKLESS_KEYWORDS = {
    "tankless water heater",
    "tankless gas water heater",
    "tankless water heaters",
    "instant hot water heater",
    "hot water tank",
    "gas tankless water heater",
    "tankless water heater gas",
    "tankless hot water heater",
}

STATUS_MAP = {
    "agree": "Stable",
    "disagree_minor": "Active trajectory",
    "not_in_top_50_organic": "Not in top 50",
    "map_pack_only": "Map Pack only",
    "unknown": "Mixed placement",
}


def style_header(ws, row: int = 1) -> None:
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )
        cell.border = BORDER
    ws.row_dimensions[row].height = 38


def autosize(ws, min_w: int = 10, max_w: int = 65) -> None:
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
    if v is None or v == 0:
        return "—"
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)


def fmt_int(v: Any) -> Any:
    return v if v else ""


def fmt_pct(v: Any) -> str:
    if v is None or v == 0:
        return ""
    return f"{v * 100:.2f}%"


def fmt_money(v: Any) -> str:
    if v is None or v == 0:
        return ""
    return f"${v:.2f}"


def fmt_status(flag: str) -> str:
    return STATUS_MAP.get(flag, flag)


def fmt_geo(geo: str) -> str:
    if geo == "no_local_data":
        return "(no local data)"
    return geo or "—"


def movement_summary(k: dict[str, Any]) -> str:
    """Plain-English summary of position movement Feb -> Apr."""
    g28o = k.get("gsc_28d_older") or {}
    g28r = k.get("gsc_28d_recent") or {}
    s = k.get("live_serp_slc") or {}
    old_pos = g28o.get("avg_position") if g28o else None
    recent_pos = g28r.get("avg_position") if g28r else None
    live_org = s.get("organic_rank_group")
    live_mp = s.get("map_pack_rank_absolute")

    if old_pos and recent_pos:
        delta = old_pos - recent_pos
        if abs(delta) < 1:
            return "Stable (Feb to Apr)"
        if delta > 0:
            return f"Improved {delta:.1f} places (Feb to Apr)"
        return f"Lost {abs(delta):.1f} places (Feb to Apr)"
    if old_pos and not recent_pos:
        if not live_org and not live_mp:
            return "Disappeared from top 50 (had Feb data, no Apr data)"
        return "Reduced impressions (had Feb data, low Apr volume)"
    if not old_pos and recent_pos:
        return "New in Apr"
    if not live_org and not live_mp:
        return "Not currently ranking"
    if live_mp and not live_org:
        return f"Map Pack #{live_mp} (no organic)"
    return "Insufficient data to compare"


def write_summary(wb: Workbook, kws: list[dict[str, Any]]) -> None:
    ws = wb.active
    ws.title = "Summary"

    flag_counts: dict[str, int] = {}
    for k in kws:
        flag = k["reconciliation"]["flag"]
        flag_counts[flag] = flag_counts.get(flag, 0) + 1

    tankless = [k for k in kws if k["keyword"] in TANKLESS_KEYWORDS]
    map_pack_only = [
        k for k in kws if k["reconciliation"]["flag"] == "map_pack_only"
    ]
    striking = [
        k for k in kws if k["reconciliation"]["flag"] == "disagree_minor"
    ]
    ai_overview = [
        k for k in kws if k.get("live_serp_slc", {}).get("in_ai_overview")
    ]

    geo_counts: dict[str, int] = {}
    for k in kws:
        geo = k.get("geography", "unknown")
        geo_counts[geo] = geo_counts.get(geo, 0) + 1

    rows: list[list[Any]] = [
        ["Beehive Plumbing — Keyword Trajectory Tracker", ""],
        ["Client", "Beehive Plumbing (beehiveplumbing.com)"],
        ["Report Date", "April 30, 2026"],
        ["Total Keywords Tracked", len(kws)],
        ["", ""],
        ["Trajectory Groups", ""],
        ["Lost tankless cluster (Priority A)", f"{len(tankless)} keywords"],
        ["Map Pack-only with attribution gap (Priority A)", f"{len(map_pack_only)} keywords"],
        ["Active trajectory (Priority B)", f"{len(striking)} keywords"],
        ["AI Overview citations (Priority B)", f"{len(ai_overview)} keywords"],
        ["", ""],
        ["Status Breakdown", ""],
        ["Stable (averages and live position agree)", flag_counts.get("agree", 0)],
        ["Active trajectory (positions moving)", flag_counts.get("disagree_minor", 0)],
        ["Not in top 50 (no organic ranking)", flag_counts.get("not_in_top_50_organic", 0)],
        ["Map Pack only (Map Pack rank, no organic)", flag_counts.get("map_pack_only", 0)],
        ["Mixed placement (both Map Pack and organic)", flag_counts.get("unknown", 0)],
        ["", ""],
        ["Volume / CPC / Competition Geography", ""],
        ["Salt Lake City (city-level data)", geo_counts.get("SLC", 0)],
        ["Utah (state-level fallback when city had no data)", geo_counts.get("UT", 0)],
        ["No local data available", geo_counts.get("no_local_data", 0)],
        ["", ""],
        ["How to Read This File", ""],
        [
            "Position columns",
            "Pos Feb / Pos Apr / Pos 90d Avg are average positions from Search Console — Google's own data, what position fired when an impression happened.",
        ],
        [
            "Live position columns",
            "Live Organic and Live Map Pack are current rankings from a Salt Lake City search performed today. Live position differs from averages when impressions came from non-SLC searches.",
        ],
        [
            "Movement column",
            "Plain-English summary of how the position changed from February to April.",
        ],
        [
            "Volume / CPC / KD geography",
            "Volume and CPC use Salt Lake City data when available. When a keyword had no city-level data, the row falls back to Utah state-level (shown in the Geography column). Keyword Difficulty and Intent are country-level (US) — these don't materially shift below country level.",
        ],
        [
            "Re-pull cadence",
            "Monthly. Replace live position and recent month of Search Console; keep the 90-day baseline fixed.",
        ],
    ]
    for row in rows:
        ws.append(row)

    ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
    for r in (6, 12, 19, 24):
        for cell in ws[r]:
            cell.fill = HEADER_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)
        ws.row_dimensions[r].height = 22

    ws.column_dimensions["A"].width = 56
    ws.column_dimensions["B"].width = 95
    wrap(ws, start_row=1)


def watchlist_headers() -> list[str]:
    return [
        "Keyword",
        "Status",
        "Pos Feb",
        "Pos Apr",
        "Pos 90d Avg",
        "Live Organic (SLC)",
        "Live Map Pack (SLC)",
        "Movement (Feb → Apr)",
        "Ranking URL",
        "Geography",
        "Search Volume",
        "CPC",
        "Keyword Difficulty",
        "Intent",
        "Impressions 90d",
        "Clicks 90d",
        "CTR 90d",
        "AI Overview",
    ]


def watchlist_row(k: dict[str, Any]) -> list[Any]:
    g90 = k.get("gsc_90d") or {}
    g28r = k.get("gsc_28d_recent") or {}
    g28o = k.get("gsc_28d_older") or {}
    s = k.get("live_serp_slc") or {}
    return [
        k["keyword"],
        fmt_status(k["reconciliation"]["flag"]),
        fmt_pos(g28o.get("avg_position")),
        fmt_pos(g28r.get("avg_position")),
        fmt_pos(g90.get("avg_position")),
        fmt_pos(s.get("organic_rank_group")),
        fmt_pos(s.get("map_pack_rank_absolute")),
        movement_summary(k),
        s.get("ranking_url") or "",
        fmt_geo(k.get("geography", "")),
        fmt_int(k.get("search_volume_local")),
        fmt_money(k.get("cpc_local")),
        fmt_int(k.get("keyword_difficulty_us")),
        k.get("search_intent_us") or "",
        fmt_int(g90.get("impressions")),
        fmt_int(g90.get("clicks")),
        fmt_pct(g90.get("ctr")),
        "Yes" if s.get("in_ai_overview") else "",
    ]


def write_watchlist(wb: Workbook, kws: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Watchlist")
    ws.append(watchlist_headers())
    style_header(ws)

    sorted_kws = sorted(
        kws, key=lambda x: -((x.get("gsc_90d") or {}).get("impressions", 0))
    )
    for k in sorted_kws:
        ws.append(watchlist_row(k))

    autosize(ws, min_w=10, max_w=55)
    wrap(ws, start_row=2)
    ws.freeze_panes = "C2"


def write_tankless(wb: Workbook, kws: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Lost Tankless Cluster")
    headers = [
        "Priority",
        "Keyword",
        "Pos Feb",
        "Pos Apr",
        "Pos 90d Avg",
        "Live Organic (SLC)",
        "Movement",
        "Geography",
        "Search Volume",
        "Impressions 90d",
        "Recommended Action",
    ]
    ws.append(headers)
    style_header(ws)

    rows = sorted(
        [k for k in kws if k["keyword"] in TANKLESS_KEYWORDS],
        key=lambda x: -((x.get("gsc_90d") or {}).get("impressions", 0)),
    )
    for k in rows:
        g90 = k.get("gsc_90d") or {}
        g28r = k.get("gsc_28d_recent") or {}
        g28o = k.get("gsc_28d_older") or {}
        s = k.get("live_serp_slc") or {}
        kw = k["keyword"]
        if "gas" in kw or "instant" in kw:
            action = (
                "Pivot target. Modifier variant still ranks in recent month "
                "(position 1.8-7.9 depending on variant). Consolidate "
                "/tankless-water-heaters-utah/ brief around installation/repair/"
                "gas-tankless variants where Google still surfaces local service."
            )
        elif "hot water tank" in kw or kw == "tankless hot water heater":
            action = (
                "Lower priority within cluster. Longer-tail informational "
                "variant. Refresh with installation/replacement angle if "
                "pivoting the cluster."
            )
        else:
            action = (
                "Head term lost to product-research SERP (Home Depot, Lowes, "
                "Reddit, manufacturer sites). Google no longer surfaces local "
                "plumber service pages on this query. Pivot investment to "
                "modifier variants (gas, installation, repair) where Beehive "
                "still ranks."
            )
        live_org_str = (
            "not in top 50"
            if not s.get("organic_rank_group")
            else fmt_pos(s.get("organic_rank_group"))
        )
        ws.append(
            [
                "A",
                kw,
                fmt_pos(g28o.get("avg_position")),
                fmt_pos(g28r.get("avg_position")),
                fmt_pos(g90.get("avg_position")),
                live_org_str,
                movement_summary(k),
                fmt_geo(k.get("geography", "")),
                fmt_int(k.get("search_volume_local")),
                fmt_int(g90.get("impressions")),
                action,
            ]
        )

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):
        for cell in row:
            cell.fill = PRIORITY_A_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)
            cell.alignment = Alignment(horizontal="center", vertical="center")

    autosize(ws, min_w=10, max_w=65)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def write_map_pack(wb: Workbook, kws: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Map Pack-Only")
    headers = [
        "Priority",
        "Keyword",
        "Pos Feb",
        "Pos Apr",
        "Pos 90d Avg",
        "Map Pack Rank",
        "Movement",
        "Geography",
        "Search Volume",
        "Impressions 90d",
        "Clicks 90d",
        "CTR 90d",
        "Investigation",
    ]
    ws.append(headers)
    style_header(ws)

    rows = sorted(
        [k for k in kws if k["reconciliation"]["flag"] == "map_pack_only"],
        key=lambda x: -((x.get("gsc_90d") or {}).get("impressions", 0)),
    )
    for k in rows:
        g90 = k.get("gsc_90d") or {}
        g28r = k.get("gsc_28d_recent") or {}
        g28o = k.get("gsc_28d_older") or {}
        s = k.get("live_serp_slc") or {}
        ws.append(
            [
                "A",
                k["keyword"],
                fmt_pos(g28o.get("avg_position")),
                fmt_pos(g28r.get("avg_position")),
                fmt_pos(g90.get("avg_position")),
                fmt_pos(s.get("map_pack_rank_absolute")),
                movement_summary(k),
                fmt_geo(k.get("geography", "")),
                fmt_int(k.get("search_volume_local")),
                fmt_int(g90.get("impressions")),
                fmt_int(g90.get("clicks")),
                fmt_pct(g90.get("ctr")),
                (
                    "Pull GA4 Maps referrals + GBP phone-call data for the same "
                    "90-day window. If GA4 + phone data accounts for the click "
                    "gap, attribution-only issue (no ranking action). If not, "
                    "GBP optimization needed (photos, reviews, posts, attributes)."
                ),
            ]
        )

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):
        for cell in row:
            cell.fill = PRIORITY_A_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)
            cell.alignment = Alignment(horizontal="center", vertical="center")

    autosize(ws, min_w=10, max_w=65)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def write_active_trajectory(wb: Workbook, kws: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Active Trajectory")
    headers = [
        "Priority",
        "Keyword",
        "Pos Feb",
        "Pos Apr",
        "Pos 90d Avg",
        "Live Organic (SLC)",
        "Live Map Pack (SLC)",
        "Movement",
        "Geography",
        "Search Volume",
        "AI Overview",
        "Trajectory Read",
    ]
    ws.append(headers)
    style_header(ws)

    rows = sorted(
        [k for k in kws if k["reconciliation"]["flag"] == "disagree_minor"],
        key=lambda x: -((x.get("gsc_90d") or {}).get("impressions", 0)),
    )
    for k in rows:
        g90 = k.get("gsc_90d") or {}
        g28r = k.get("gsc_28d_recent") or {}
        g28o = k.get("gsc_28d_older") or {}
        s = k.get("live_serp_slc") or {}

        old_pos = g28o.get("avg_position") if g28o else None
        recent_pos = g28r.get("avg_position") if g28r else None
        if old_pos and recent_pos:
            if recent_pos < old_pos - 1:
                read = (
                    f"Improving. Position improved from {old_pos:.1f} to "
                    f"{recent_pos:.1f} over the 60-day comparison window."
                )
            elif recent_pos > old_pos + 1:
                read = (
                    f"Slipping. Position degraded from {old_pos:.1f} to "
                    f"{recent_pos:.1f}."
                )
            else:
                read = (
                    "Stable in averages. Live SERP shows minor disagreement "
                    "worth watching."
                )
        else:
            read = (
                "Trajectory unclear (gaps in recent data). Track over next pull."
            )

        ws.append(
            [
                "B",
                k["keyword"],
                fmt_pos(g28o.get("avg_position")),
                fmt_pos(g28r.get("avg_position")),
                fmt_pos(g90.get("avg_position")),
                fmt_pos(s.get("organic_rank_group")),
                fmt_pos(s.get("map_pack_rank_absolute")),
                movement_summary(k),
                fmt_geo(k.get("geography", "")),
                fmt_int(k.get("search_volume_local")),
                "Yes" if s.get("in_ai_overview") else "",
                read,
            ]
        )

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):
        for cell in row:
            cell.fill = PRIORITY_B_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)
            cell.alignment = Alignment(horizontal="center", vertical="center")

    autosize(ws, min_w=10, max_w=65)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def write_ai_overview(wb: Workbook, kws: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("AI Overview Wins")
    headers = [
        "Keyword",
        "Pos 90d Avg",
        "Live Organic (SLC)",
        "Geography",
        "Search Volume",
        "Impressions 90d",
        "Beehive Cited URL",
        "Protection Action",
    ]
    ws.append(headers)
    style_header(ws)

    rows = sorted(
        [k for k in kws if (k.get("live_serp_slc") or {}).get("in_ai_overview")],
        key=lambda x: -((x.get("gsc_90d") or {}).get("impressions", 0)),
    )
    for k in rows:
        g90 = k.get("gsc_90d") or {}
        s = k.get("live_serp_slc") or {}
        cited_url = s.get("ai_overview_cited_url") or s.get("ranking_url") or ""
        ws.append(
            [
                k["keyword"],
                fmt_pos(g90.get("avg_position")),
                fmt_pos(s.get("organic_rank_group")),
                fmt_geo(k.get("geography", "")),
                fmt_int(k.get("search_volume_local")),
                fmt_int(g90.get("impressions")),
                cited_url,
                (
                    "Tag URL 'do not edit without QA' before any blog audit "
                    "(Roadmap #6) edits. Verify AI Overview citation persists "
                    "post-edit. Citation can drop if the structured-answer "
                    "paragraph Google extracted is changed."
                ),
            ]
        )

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):
        for cell in row:
            cell.fill = PROTECT_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)

    autosize(ws, min_w=10, max_w=65)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    kws: list[dict[str, Any]] = payload["keywords"]

    wb = Workbook()
    write_summary(wb, kws)
    write_watchlist(wb, kws)
    write_tankless(wb, kws)
    write_map_pack(wb, kws)
    write_active_trajectory(wb, kws)
    write_ai_overview(wb, kws)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
