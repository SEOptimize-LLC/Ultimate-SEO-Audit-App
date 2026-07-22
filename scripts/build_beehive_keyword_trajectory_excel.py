"""Build the Beehive Keyword Trajectory Tracker Excel deliverable.

Output: Clients/Beehive/Full Site SEO Audit/beehive_keyword_trajectory_tracker.xlsx

Tabs:
  1. Summary               - Headline numbers + workstream cross-reference
  2. Lost Top-10 Local     - Priority A: 18 commercial money keywords
  3. Pos 11-20 Local       - Striking-distance local recovery candidates
  4. Top Declining         - 100 declining keywords, all categories
  5. Improving Protect     - 100 improving keywords (protect list)
  6. URL-Level Decline     - Decline volume aggregated per ranking URL
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "_keyword_trajectory_data"
OUTPUT = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "beehive_keyword_trajectory_tracker.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
PRIORITY_FILL = PatternFill("solid", fgColor="C00000")
PRIORITY_FONT = Font(bold=True, color="FFFFFF", size=11)
PROTECT_FILL = PatternFill("solid", fgColor="2E7D32")
NEUTRAL_FILL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

BRAND_RX = re.compile(r"\bbeehive\b", re.I)
LOCAL_RX = re.compile(
    r"\b(utah|ut|salt lake|slc|sandy|provo|ogden|west jordan|south jordan|"
    r"draper|murray|orem|park city|lehi|saratoga|riverton|herriman|tooele|"
    r"bountiful|layton|kaysville|farmington|clearfield|hurricane)\b",
    re.I,
)


def url_path(u: str | None) -> str | None:
    if not u:
        return None
    m = re.match(r"https?://(?:www\.)?beehiveplumbing\.com(/[^?#]*)", u)
    return m.group(1) if m else u


def load_slice(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("items", [])
    rows: list[dict[str, Any]] = []
    for it in items:
        kd = it.get("keyword_data", {}) or {}
        ki = kd.get("keyword_info", {}) or {}
        si = (it.get("ranked_serp_element", {}) or {}).get("serp_item", {}) or {}
        rc = si.get("rank_changes") or {}
        kw = kd.get("keyword", "") or ""
        url = si.get("url", "") or ""
        rows.append(
            {
                "keyword": kw,
                "volume": ki.get("search_volume") or 0,
                "cpc": ki.get("cpc") or 0,
                "rank_group": si.get("rank_group"),
                "rank_absolute": si.get("rank_absolute"),
                "previous_rank_absolute": rc.get("previous_rank_absolute"),
                "is_up": bool(rc.get("is_up", False)),
                "is_down": bool(rc.get("is_down", False)),
                "etv": si.get("etv") or 0,
                "url": url,
                "path": url_path(url) or "",
                "branded": bool(BRAND_RX.search(kw)),
                "local": bool(LOCAL_RX.search(kw)),
            }
        )
    return rows


def style_header(ws, row: int = 1) -> None:
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 32


def autosize(ws, min_w: int = 10, max_w: int = 80) -> None:
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        longest = 0
        for cell in col:
            if cell.value is None:
                continue
            longest = max(longest, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(min_w, longest + 2), max_w)


def wrap(ws, start_row: int = 2) -> None:
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def fmt_pos(p: Any) -> str:
    if p is None or p == 0:
        return "—"
    return str(p)


def write_summary(wb: Workbook, all_data: dict[str, list[dict[str, Any]]]) -> None:
    ws = wb.active
    ws.title = "Summary"

    declining = all_data["declining"]
    improving = all_data["improving"]
    lost = all_data["lost_top10"]
    p11 = all_data["pos_11_20"]

    local_lost = [r for r in lost if r["local"] and not r["branded"]]
    local_p11 = [r for r in p11 if r["local"] and not r["branded"]]

    rows = [
        ["Beehive Plumbing — Keyword Trajectory Tracker", ""],
        ["Source", "DataForSEO Labs google_ranked_keywords API"],
        ["Pull Date", "April 30, 2026"],
        ["Domain", "beehiveplumbing.com"],
        ["", ""],
        ["Headline Numbers", ""],
        ["Keywords moving down (full domain)", "1,150"],
        ["Keywords moving up (full domain)", "414"],
        ["Total tracked keyword universe", "2,543"],
        ["", ""],
        ["This Analysis", ""],
        ["Top declining sample (this report)", f"{len(declining)} keywords"],
        ["Combined volume of declining sample", f"{sum(r['volume'] for r in declining):,}"],
        ["Top improving sample (this report)", f"{len(improving)} keywords"],
        ["Combined volume of improving sample", f"{sum(r['volume'] for r in improving):,}"],
        ["", ""],
        ["Priority A — Lost Top-10 Local (commercial money keywords)", ""],
        ["Total lost top-10 keywords (full universe)", f"{len(lost)} keywords"],
        ["Of those, LOCAL non-branded", f"{len(local_lost)} keywords"],
        ["Combined monthly volume — local lost top-10", f"{sum(r['volume'] for r in local_lost):,}"],
        ["Highest-value local query lost", "salt lake plumber — 2,900/mo, position 5 → 23"],
        ["", ""],
        ["Priority B — Pos 11-20 Local (recovery candidates)", ""],
        ["Local non-branded keywords in pos 11-20", f"{len(local_p11)} keywords"],
        ["Combined monthly volume", f"{sum(r['volume'] for r in local_p11):,}"],
        ["", ""],
        ["Cross-Reference With Existing Audit Roadmap", ""],
        ["Roadmap #4 — Top 4 service page rewrites (P0)", "Sewer-line page already showing positive trajectory; 3 others pending."],
        ["Roadmap #14 — Local service page rewrites (P2)", "PROMOTE TO P1 — 18 lost-top-10 local keywords confirm template-thinness collapse."],
        ["Roadmap #6 — Blog audit (P1)", "Defines refresh vs noindex set: 10 URLs absorb ~79% of declining-keyword volume."],
        ["Roadmap #16 — Internal linking (P2)", "Refresh pattern includes service-page internal links; do both at once."],
        ["NEW — Build /plumbing-salt-lake-city-utah/ page", "Not on existing roadmap. SLC queries (13,500+/mo) currently absorbed by homepage."],
        ["", ""],
        ["Success Metric", ""],
        ["Definition of recovery success", "≥12 of 18 lost-top-10 local keywords return to top-10 within local-pages rewrite cycle."],
        ["Re-pull cadence", "Monthly. Same DFS query, same filters."],
    ]
    for row in rows:
        ws.append(row)

    # Style title row
    ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
    # Style section headers
    for r in (6, 11, 17, 23, 28, 34):
        for cell in ws[r]:
            cell.fill = HEADER_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)
        ws.row_dimensions[r].height = 22

    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 70
    wrap(ws, start_row=1)


def write_lost_top10_local(wb: Workbook, lost: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Lost Top-10 Local")
    headers = [
        "Priority",
        "Keyword",
        "Search Volume",
        "Previous Position",
        "Current Position",
        "Position Drop",
        "CPC ($)",
        "Ranking URL",
        "Suggested Action",
        "Roadmap Item",
        "Recovery Position (next pull)",
    ]
    ws.append(headers)
    style_header(ws)

    rows = sorted(
        [r for r in lost if r["local"] and not r["branded"]],
        key=lambda x: -x["volume"],
    )
    for r in rows:
        prev_pos = r["previous_rank_absolute"] or 0
        cur_pos = r["rank_absolute"] or 0
        drop = (cur_pos - prev_pos) if (prev_pos and cur_pos) else None
        kw_lower = r["keyword"].lower()
        if "salt lake" in kw_lower:
            action = (
                "Fix /plumbing-salt-lake-city-ut/ redirect chain (currently HTTPS->HTTP->HTTPS). "
                "Audit page content quality. Migrate ranking signal off homepage onto city page."
            )
            roadmap = "NEW item"
        elif r["path"] in {
            "/tankless-water-heaters-utah/",
            "/water-heater-installation-services-utah/",
        }:
            action = "Service page rewrite — definition-first lead, internal links from blog cluster, refresh content."
            roadmap = "Aligns with #4"
        else:
            action = "Local page rewrite — replace 353-word template with city-specific content (entities, signals, history)."
            roadmap = "#14"

        ws.append(
            [
                "A",
                r["keyword"],
                r["volume"],
                fmt_pos(prev_pos),
                fmt_pos(cur_pos),
                drop if drop else "",
                round(r["cpc"], 2) if r["cpc"] else "",
                r["url"],
                action,
                roadmap,
                "",
            ]
        )

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):
        for cell in row:
            cell.fill = PRIORITY_FILL
            cell.font = PRIORITY_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")

    autosize(ws, min_w=12, max_w=70)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def write_pos_11_20_local(wb: Workbook, p11: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Pos 11-20 Local")
    headers = [
        "Keyword",
        "Search Volume",
        "Current Position",
        "Previous Position",
        "CPC ($)",
        "Ranking URL",
        "Recovery Notes",
    ]
    ws.append(headers)
    style_header(ws)

    rows = sorted(
        [r for r in p11 if r["local"] and not r["branded"]],
        key=lambda x: -x["volume"],
    )
    for r in rows:
        kw_lower = r["keyword"].lower()
        if "salt lake" in kw_lower and r["path"] == "/":
            note = "Homepage ranking. Move to dedicated SLC city page (build new)."
        elif r["path"].startswith("/plumbing-") or r["path"] in (
            "/park-city-utah/",
            "/plumbing-south-jordan-utah/",
        ):
            note = "Local page collapse — apply rewrite from Roadmap #14."
        else:
            note = "Verify ranking page is correct; consolidate signal if multiple URLs compete."

        ws.append(
            [
                r["keyword"],
                r["volume"],
                fmt_pos(r["rank_group"]),
                fmt_pos(r["previous_rank_absolute"]),
                round(r["cpc"], 2) if r["cpc"] else "",
                r["url"],
                note,
            ]
        )

    autosize(ws, min_w=12, max_w=60)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def write_declining(wb: Workbook, declining: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Top Declining")
    headers = [
        "Keyword",
        "Search Volume",
        "Previous Position",
        "Current Position",
        "Position Drop",
        "Est Traffic (etv)",
        "CPC ($)",
        "Branded?",
        "Local?",
        "Ranking URL",
    ]
    ws.append(headers)
    style_header(ws)

    rows = sorted(declining, key=lambda x: -x["volume"])
    for r in rows:
        prev_pos = r["previous_rank_absolute"] or 0
        cur_pos = r["rank_absolute"] or 0
        drop = (cur_pos - prev_pos) if (prev_pos and cur_pos) else ""
        ws.append(
            [
                r["keyword"],
                r["volume"],
                fmt_pos(prev_pos),
                fmt_pos(cur_pos),
                drop,
                round(r["etv"], 1) if r["etv"] else "",
                round(r["cpc"], 2) if r["cpc"] else "",
                "Yes" if r["branded"] else "",
                "Yes" if r["local"] else "",
                r["url"],
            ]
        )

    autosize(ws, min_w=10, max_w=70)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def write_improving(wb: Workbook, improving: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Improving Protect")
    headers = [
        "Keyword",
        "Search Volume",
        "Previous Position",
        "Current Position",
        "Position Gain",
        "Branded?",
        "Local?",
        "Ranking URL",
        "Protect Action",
    ]
    ws.append(headers)
    style_header(ws)

    rows = sorted(improving, key=lambda x: -x["volume"])
    for r in rows:
        prev_pos = r["previous_rank_absolute"] or 0
        cur_pos = r["rank_absolute"] or 0
        gain = (prev_pos - cur_pos) if (prev_pos and cur_pos) else ""
        # Most improvers are deep blog content with no real click value.
        if cur_pos and cur_pos <= 20:
            action = "Worth protecting — close to click-generating range. Refresh on next blog cycle."
        else:
            action = "Monitor only. Position gain not yet click-generating."
        ws.append(
            [
                r["keyword"],
                r["volume"],
                fmt_pos(prev_pos),
                fmt_pos(cur_pos),
                gain,
                "Yes" if r["branded"] else "",
                "Yes" if r["local"] else "",
                r["url"],
                action,
            ]
        )

    autosize(ws, min_w=10, max_w=70)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def write_url_decline(wb: Workbook, declining: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("URL-Level Decline")
    headers = [
        "Ranking URL",
        "Declining Keywords (count)",
        "Combined Volume",
        "Top 3 Keywords",
        "Recommended Treatment",
    ]
    ws.append(headers)
    style_header(ws)

    agg: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "volume": 0, "kws": []}
    )
    for r in declining:
        url = r["url"] or "(no url)"
        agg[url]["count"] += 1
        agg[url]["volume"] += r["volume"]
        agg[url]["kws"].append((r["keyword"], r["volume"]))

    sorted_urls = sorted(agg.items(), key=lambda x: -x[1]["volume"])
    for url, data in sorted_urls:
        top3 = sorted(data["kws"], key=lambda x: -x[1])[:3]
        top3_str = "; ".join(f"{kw} ({vol:,})" for kw, vol in top3)

        path = url_path(url) or ""
        if path.startswith("/plumbing-") or path in {
            "/park-city-utah/",
            "/plumbing-south-jordan-utah/",
        }:
            treatment = "Local page rewrite (Roadmap #14)."
        elif path in {
            "/sewer-line-repair-utah/",
            "/drain-cleaning-utah/",
            "/emergency-plumber/",
            "/water-heater-repair-utah/",
        }:
            treatment = "Service page rewrite (Roadmap #4 — P0)."
        elif path == "/":
            treatment = "Homepage rewrite (Roadmap #5) + build /plumbing-salt-lake-city-utah/ to take SLC queries."
        elif path.startswith("/heres-how-to-use-a-bidet"):
            treatment = "Off-topic for plumbing service intent. Consider noindex (Roadmap #6)."
        else:
            treatment = "Blog refresh — definition-first lead, internal link to matching service page, update modified date."
        ws.append(
            [
                url,
                data["count"],
                data["volume"],
                top3_str,
                treatment,
            ]
        )

    autosize(ws, min_w=12, max_w=80)
    wrap(ws, start_row=2)
    ws.freeze_panes = "A2"


def main() -> None:
    all_data = {
        "declining": load_slice("declining_top100_by_volume.json"),
        "improving": load_slice("improving_top100_by_volume.json"),
        "lost_top10": load_slice("striking_distance_lost_top10.json"),
        "pos_11_20": load_slice("striking_distance_pos_11_20.json"),
    }

    wb = Workbook()
    write_summary(wb, all_data)
    write_lost_top10_local(wb, all_data["lost_top10"])
    write_pos_11_20_local(wb, all_data["pos_11_20"])
    write_declining(wb, all_data["declining"])
    write_improving(wb, all_data["improving"])
    write_url_decline(wb, all_data["declining"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
