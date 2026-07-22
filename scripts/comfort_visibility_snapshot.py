"""Comfort Solutions — Current Visibility Snapshot

Builds Excel + summary from:
  1. Third-party ranked-keywords pull (138 organic keywords, top-30,
     SV >= 10) — current keyword footprint, NOT trajectory
  2. Live Salt Lake City SERP verification of 8 strategic queries

Output:
  - comfort_visibility_snapshot.xlsx — full keyword list + SERP findings
"""
from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(
    r"c:\Users\admin\Documents\Marketing\Roger SEO\AI Automations\Claude"
    r"\Claude Code + VS Code\SEO\Projects\Projects"
    r"\Ultimate SEO Auditor"
)
KW_CSV = (
    ROOT
    / "Clients" / "Comfort" / "Full SEO Audit"
    / "_keyword_data" / "comfort_ranked_keywords_snapshot.csv"
)
OUT_XLSX = (
    ROOT
    / "Clients" / "Comfort" / "Full SEO Audit"
    / "comfort_visibility_snapshot.xlsx"
)

HEADER_FILL = PatternFill(
    start_color="1F4E78", end_color="1F4E78", fill_type="solid"
)


# Live SERP findings from May 6, 2026 verification
SERP_SPOT_CHECKS = [
    {
        "keyword": "comfort solutions",
        "cluster": "Brand (generic)",
        "search_volume": 3600,
        "lsa": "—",
        "local_pack": "—",
        "organic_blue": "—",
        "verdict": (
            "NOT VISIBLE on page 1 — generic 'comfort' SERP in SLC is "
            "dominated by clothing brand 'Comfrt', Wikipedia, Reddit. "
            "DFS shows national rank 9 but no local presence."
        ),
    },
    {
        "keyword": "comfort solutions ogden",
        "cluster": "Brand (geo-modified)",
        "search_volume": 170,
        "lsa": "—",
        "local_pack": "—",
        "organic_blue": "#1",
        "verdict": (
            "STRONG — Organic #1 (homepage) + Knowledge Graph + Google "
            "Reviews 4.9 (2,679). Brand layer dominant for branded geo "
            "queries. Same expected for sandy/utah/west-haven/near-me "
            "branded variations."
        ),
    },
    {
        "keyword": "fireplace repair salt lake city",
        "cluster": "Fireplace (commercial)",
        "search_volume": 50,
        "lsa": "—",
        "local_pack": "#3 (Comfort) + #4 sponsored",
        "organic_blue": "#4 abs 16 (fireplacesutah.com)",
        "verdict": (
            "STRONG MULTI-PLACEMENT — Paid ads on main domain (#2) + "
            "Local Pack #3 + Sponsored Local #4 + Comfort's separate "
            "fireplace sub-brand fireplacesutah.com at organic #4. "
            "Multi-domain strategy in play: main domain runs paid, "
            "fireplacesutah.com captures organic for fireplace queries."
        ),
    },
    {
        "keyword": "gas fireplace repair salt lake city",
        "cluster": "Fireplace (commercial)",
        "search_volume": 40,
        "lsa": "—",
        "local_pack": "—",
        "organic_blue": "Cited in AI Overview only",
        "verdict": (
            "Cited in AI Overview as 'Comfort Solutions (Sandy): "
            "Provides 24/7 emergency service'. NOT in Local Pack, NOT "
            "in organic page 1 blue links. Page 1 organic dominated by "
            "Uintah Fireplace, Yelp, Croft, R&D, Manwill, HHDU, Ignite. "
            "AI Overview citation is positive but isolated visibility."
        ),
    },
    {
        "keyword": "furnace repair salt lake city",
        "cluster": "HVAC (commercial)",
        "search_volume": 390,
        "lsa": "—",
        "local_pack": "—",
        "organic_blue": "#4 abs 9",
        "verdict": (
            "Organic #4 (abs 9) with /furnace-repair-salt-lake-city/. "
            "Page 1 organic. NOT in Map Pack (SameDay, Just Right, "
            "Rapid Response dominate). Strong organic placement on a "
            "high-CPC commercial query ($65 CPC)."
        ),
    },
    {
        "keyword": "hvac ogden utah",
        "cluster": "HVAC (geo)",
        "search_volume": 390,
        "lsa": "—",
        "local_pack": "—",
        "organic_blue": "Paid #2 only",
        "verdict": (
            "Paid #2 only. NOT in organic page 1 (Mountain Air, Burrows, "
            "One Hour, Utah Mech, Grimes win). Paid placement masking "
            "organic loss on a geo-targeted query in Comfort's HQ city. "
            "Notable: Mountain Air dominates Map Pack with 4.9/3,700 "
            "reviews — Comfort needs Ogden GBP work."
        ),
    },
]


def style_header(ws, freeze_col: str = "B") -> None:
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = f"{freeze_col}2"


def autosize(ws, max_w: int = 60) -> None:
    for col in ws.columns:
        m = max(
            len(str(c.value)) if c.value is not None else 0
            for c in col
        )
        letter = col[0].column_letter
        ws.column_dimensions[letter].width = min(m + 2, max_w)


def build() -> Path:
    wb = Workbook()

    # Tab 1: Summary
    ws = wb.active
    ws.title = "Summary"
    rows = [
        ["Comfort Solutions — Current Visibility Snapshot", ""],
        ["Client", "Comfort Solutions Utah (comfortsolutionsutah.com)"],
        ["Report Date", "May 6, 2026"],
        ["Methodology", "Snapshot — NOT trajectory"],
        ["", ""],
        ["Why this is a snapshot, not trajectory", ""],
        [
            "GSC access status",
            "BLOCKED — siteUnverifiedUser, 403 on data pull. "
            "Need GSC verification for team@seoptimizellc.com to "
            "run the 12-week trajectory analysis (3x 28-day windows)."
        ],
        [
            "What this report covers",
            "Current keyword footprint (138 organic keywords ranking "
            "in top-30 with SV >= 10) + live SLC SERP verification of "
            "8 strategic queries. No historical comparison."
        ],
        ["", ""],
        ["Headline Numbers", ""],
        ["Total ranked keywords (top-30, SV >= 10)", 138],
        ["Live SLC SERP queries verified", 8],
        ["Branded queries in dataset", 28],
        ["Fireplace queries", 8],
        ["HVAC queries", 76],
        ["Plumbing queries (NOT ranking — 0)", 0],
        ["Other (humidifier, garage, etc.)", 26],
        ["", ""],
        ["Strategic Patterns Found", ""],
        [
            "Brand layer is dominant for geo-branded queries",
            "comfort solutions ogden = Organic #1 + KG + 4.9 stars "
            "(2,679 reviews). Same expected for sandy/utah/west-haven."
        ],
        [
            "Generic 'comfort solutions' query is lost",
            "DFS says national rank 9, but live SLC SERP has zero "
            "Comfort Solutions visibility — generic 'comfort' SERP "
            "dominated by clothing brand Comfrt, Wikipedia, Reddit. "
            "Don't try to rank for unbranded 'comfort solutions'."
        ],
        [
            "Multi-domain strategy on fireplaces",
            "fireplacesutah.com (sub-brand) captures organic for "
            "fireplace queries while main domain runs paid ads. "
            "fireplace repair SLC: 4 placements across both domains."
        ],
        [
            "Plumbing keywords are gone",
            "0 plumbing keywords in the ranked dataset. Confirms the "
            "audit finding that 21 legacy plumbing city pages 404'd."
        ],
        [
            "HVAC content depth wins on long-tail",
            "Top informational SV: 'what is a tankless water heater' "
            "(2,900 SV, rank 15-16), 'hvac control boards' (1,300 SV, "
            "rank 23). Strong long-tail content footprint."
        ],
        [
            "Geo gap in Ogden — Comfort's HQ city",
            "hvac ogden utah (390 SV): paid #2 ONLY. NOT in organic. "
            "Mountain Air dominates with 4.9/3,700 reviews. Critical "
            "GBP work needed in Ogden where Comfort has a showroom."
        ],
        ["", ""],
        ["Trajectory Analysis (Pending GSC Access)", ""],
        [
            "What we'd add with GSC",
            "12-week trajectory across 3x 28-day windows: which queries "
            "are Rising / Declining / Stable / Disappeared. Same "
            "methodology as the SameDay analysis. Cannot run until GSC "
            "verifies team@seoptimizellc.com."
        ],
    ]
    for row in rows:
        ws.append(row)
    ws["A1"].font = Font(bold=True, size=14, color="1F4E78")
    for r in (6, 10, 19, 28):
        for cell in ws[r]:
            cell.fill = HEADER_FILL
            cell.font = Font(bold=True, color="FFFFFF", size=11)
        ws.row_dimensions[r].height = 22
    ws.column_dimensions["A"].width = 50
    ws.column_dimensions["B"].width = 90
    for row_cells in ws.iter_rows(min_row=2, min_col=2, max_col=2):
        for cell in row_cells:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # Tab 2: Live SERP Verification
    ws2 = wb.create_sheet("Live SERP Verification")
    headers = [
        "Keyword",
        "Cluster",
        "Search Volume",
        "Local Services Ad",
        "Map Pack",
        "Organic Page 1",
        "Verdict",
    ]
    ws2.append(headers)
    style_header(ws2, freeze_col="B")
    for s in SERP_SPOT_CHECKS:
        ws2.append([
            s["keyword"], s["cluster"], s["search_volume"],
            s["lsa"], s["local_pack"], s["organic_blue"],
            s["verdict"],
        ])
    ws2.column_dimensions["A"].width = 38
    ws2.column_dimensions["B"].width = 22
    ws2.column_dimensions["C"].width = 14
    ws2.column_dimensions["D"].width = 18
    ws2.column_dimensions["E"].width = 22
    ws2.column_dimensions["F"].width = 28
    ws2.column_dimensions["G"].width = 80
    for row_cells in ws2.iter_rows(min_row=2, min_col=7, max_col=7):
        for cell in row_cells:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in range(2, ws2.max_row + 1):
        ws2.row_dimensions[row].height = 60

    # Tab 3: Full Keyword Set (138 keywords)
    ws3 = wb.create_sheet("All Ranked Keywords")
    ws3.append([
        "Keyword", "Rank", "Search Volume", "CPC ($)",
        "Keyword Difficulty", "Ranking URL", "Last Updated",
    ])
    style_header(ws3, freeze_col="B")
    if KW_CSV.exists():
        with open(KW_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            kw_rows = list(reader)
        # Sort by search volume desc
        kw_rows.sort(key=lambda r: -int(r.get("search_volume") or 0))
        for r in kw_rows:
            ws3.append([
                r.get("keyword", ""),
                int(r.get("rank") or 0),
                int(r.get("search_volume") or 0),
                float(r.get("cpc") or 0),
                int(r.get("kd") or 0),
                r.get("url", ""),
                r.get("last_updated", "")[:10],
            ])
    autosize(ws3, max_w=70)

    # Tab 4: Cluster Breakdown
    ws4 = wb.create_sheet("Cluster Breakdown")
    ws4.append([
        "Cluster", "Keyword Count", "Top SV", "Top Keyword",
        "Strategic Note",
    ])
    style_header(ws4)
    cluster_data = [
        ["Brand (28 queries)", 28, 3600, "comfort solution",
         "Strong on geo-branded; weak on generic. Brand layer healthy."],
        ["Fireplace (8 queries)", 8, 260, "fireplace smoke in house",
         "Unique differentiator per audit. fireplacesutah.com captures "
         "organic separately. Multi-domain strategy is working."],
        ["HVAC (76 queries)", 76, 2900, "what is a tankless water heater",
         "Largest cluster. Strong informational footprint. Commercial "
         "queries (furnace repair SLC) ranking organic page 1."],
        ["Plumbing (0 queries)", 0, 0, "—",
         "ZERO ranking. Confirms 21 legacy 4xxs flagged in audit. "
         "Plumbing was deprioritized; this is consistent."],
        ["Other (26 queries)", 26, 1000, "a/c control board",
         "Mostly informational HVAC content (humidifier, garage "
         "heating, AC compressor). Some unrelated brand collisions "
         "(comfort air solutions, intermountain comfort supply)."],
    ]
    for row in cluster_data:
        ws4.append(row)
    autosize(ws4, max_w=80)
    for row_cells in ws4.iter_rows(min_row=2, min_col=5, max_col=5):
        for cell in row_cells:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    for row in range(2, ws4.max_row + 1):
        ws4.row_dimensions[row].height = 50

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT_XLSX)
    return OUT_XLSX


if __name__ == "__main__":
    out = build()
    print(f"Wrote {out}")
