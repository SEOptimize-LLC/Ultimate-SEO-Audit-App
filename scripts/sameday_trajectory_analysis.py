"""SameDay keyword trajectory analysis.

Processes 3 GSC analytics windows and the existing Striking Distance
list to classify keyword trajectory (Rising / Stable / Declining /
Volatile / Disappeared / Emerging). Outputs Excel + summary JSON.

Windows:
  W1 = latest 28 days (2026-04-08 to 2026-05-06)
  W2 = prior 28 days (2026-03-11 to 2026-04-07)
  W3 = baseline 28 days (2026-02-11 to 2026-03-10)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(
    r"c:\Users\admin\Documents\Marketing\Roger SEO\AI Automations\Claude"
    r"\Claude Code + VS Code\SEO\Projects\Projects"
    r"\Ultimate SEO Auditor"
)
W1_FILE = (
    r"C:\Users\admin\.claude\projects"
    r"\c--Users-admin-Documents-Marketing-Roger-SEO-AI-Automations-Claude"
    r"-Claude-Code---VS-Code-SEO-Projects-Projects-Ultimate-SEO-Auditor"
    r"\9e9d695c-1264-41a1-b774-962076dcba36\tool-results"
    r"\mcp-gsc-mcp-get_advanced_search_analytics-1778070340930.txt"
)
W2_FILE = (
    r"C:\Users\admin\.claude\projects"
    r"\c--Users-admin-Documents-Marketing-Roger-SEO-AI-Automations-Claude"
    r"-Claude-Code---VS-Code-SEO-Projects-Projects-Ultimate-SEO-Auditor"
    r"\9e9d695c-1264-41a1-b774-962076dcba36\tool-results"
    r"\mcp-gsc-mcp-get_advanced_search_analytics-1778070347288.txt"
)
W3_FILE = (
    r"C:\Users\admin\.claude\projects"
    r"\c--Users-admin-Documents-Marketing-Roger-SEO-AI-Automations-Claude"
    r"-Claude-Code---VS-Code-SEO-Projects-Projects-Ultimate-SEO-Auditor"
    r"\9e9d695c-1264-41a1-b774-962076dcba36\tool-results"
    r"\mcp-gsc-mcp-get_advanced_search_analytics-1778070351932.txt"
)

OUT_DIR = ROOT / "Clients" / "SameDay" / "Full SEO Audit"


def parse_window(path: str) -> dict[str, dict]:
    """Load a GSC tool-result JSON file and return {query: metrics}.

    Format is pipe-delimited table rows after the header divider:
        Query | Clicks | Impressions | CTR | Position
        -----------------
        same day heating and air | 40 | 870 | 4.60% | 5.9
    """
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    text = data["result"]
    out = {}
    for line in text.split("\n"):
        if " | " not in line:
            continue
        # Skip header
        if line.lower().startswith("query | "):
            continue
        parts = [p.strip() for p in line.split(" | ")]
        if len(parts) != 5:
            continue
        try:
            clicks = int(parts[1].replace(",", ""))
            impr = int(parts[2].replace(",", ""))
            ctr = float(parts[3].rstrip("%"))
            pos = float(parts[4])
        except (ValueError, IndexError):
            continue
        q = parts[0].lower().strip()
        out[q] = {
            "clicks": clicks,
            "impressions": impr,
            "ctr": ctr,
            "position": pos,
        }
    return out


def classify(w1: dict | None, w2: dict | None, w3: dict | None) -> str:
    """Classify a query's trajectory from 3 windows of metrics.

    Position rules (lower = better):
      - Rising: pos improves by >= 2 from W3->W1, monotonic-ish
      - Declining: pos worsens by >= 2 from W3->W1
      - Stable: |W1 pos - W3 pos| < 2 AND consistent across windows
      - Volatile: large swings between windows but no net trend
      - Emerging: only present in W1 (newly appearing)
      - Disappeared: present in W3 but missing from W1
    """
    has_w1, has_w2, has_w3 = bool(w1), bool(w2), bool(w3)

    if has_w1 and not has_w2 and not has_w3:
        return "Emerging"
    if not has_w1 and (has_w2 or has_w3):
        return "Disappeared"
    if not (has_w1 and has_w3):
        return "Insufficient data"

    p1, p3 = w1["position"], w3["position"]
    p2 = w2["position"] if has_w2 else (p1 + p3) / 2

    delta = p3 - p1  # positive = ranking improved
    swing_max = max(p1, p2, p3)
    swing_min = min(p1, p2, p3)
    swing = swing_max - swing_min

    if delta >= 2:
        return "Rising"
    if delta <= -2:
        return "Declining"
    if swing >= 5:
        return "Volatile"
    return "Stable"


SERP_SPOT_CHECKS = {
    # Live-verified Salt Lake City SERPs, May 6 2026 — all 24 Disappeared
    # Format: lsa = position in Local Services Ads (paid),
    #         local_pack = position in Map Pack (organic GBP),
    #         organic_page1 = absolute organic position (or None if page 2+)
    "furnace repair": {
        "organic_page1": None, "local_pack": 3, "lsa": None,
        "summary": "Map Pack #3 only. NOT in organic page 1.",
    },
    "electrician salt lake city": {
        "organic_page1": None, "local_pack": None, "lsa": 2,
        "summary": "Local Services Ad #2 only. NOT in Map Pack. NOT in organic page 1.",
    },
    "water heater repair salt lake city": {
        "organic_page1": None, "local_pack": 3, "lsa": None,
        "summary": "Map Pack #3 only. NOT in organic page 1.",
    },
    "plumbers near me": {
        "organic_page1": 7, "local_pack": None, "lsa": None,
        "summary": "FALSE ALARM — organic position 7 with /plumbing/. NOT in Map Pack. Query intermittent in GSC sample.",
    },
    "air conditioner repair": {
        "organic_page1": None, "local_pack": 3, "lsa": 1,
        "summary": "Local Services Ad #1 + Map Pack #3 (organic GBP). NOT in organic page 1.",
    },
    "drain cleaning salt lake city": {
        "organic_page1": 8, "local_pack": None, "lsa": None,
        "summary": "Organic position 8 (page 1 bottom). NOT in Map Pack. Map Pack opportunity exists.",
    },
    "furnace replacement salt lake city": {
        "organic_page1": 5, "local_pack": 1, "lsa": None,
        "summary": "STRONG — Map Pack #1 + organic position 5 with homepage. Dual placement.",
    },
    "plumber near me": {
        "organic_page1": 6, "local_pack": None, "lsa": None,
        "summary": "FALSE ALARM — organic position 6 with /plumbing/. NOT in Map Pack (Just Right, Beehive, Salt City instead).",
    },
    "ac replacement near me": {
        "organic_page1": 3, "local_pack": 2, "lsa": None,
        "summary": "STRONG — Map Pack #2 + organic position 3 with /air-conditioning/installation/. Dual placement.",
    },
    "plumbing services salt lake city": {
        "organic_page1": None, "local_pack": None, "lsa": 1,
        "summary": "Local Services Ad #1 (sponsored) only. NOT in Map Pack. NOT in organic page 1.",
    },
    "plumbers salt lake city": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "TRUE LOSS — invisible across LSAs, Map Pack, and organic page 1.",
    },
    "emergency electrician near me": {
        "organic_page1": 3, "local_pack": None, "lsa": 1,
        "summary": "Local Services Ad #1 + organic position 3 with /service-area/electrical/salt-lake-city-ut/. Strong combined placement.",
    },
    "local plumbers": {
        "organic_page1": 7, "local_pack": None, "lsa": None,
        "summary": "Organic position 7 with /plumbing/. NOT in Map Pack, NOT in LSAs.",
    },
    "plumbers in salt lake city": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "TRUE LOSS — invisible across LSAs, Map Pack, and organic page 1.",
    },
    "air conditioning installation salt lake city": {
        "organic_page1": 8, "local_pack": 1, "lsa": None,
        "summary": "STRONG — Map Pack #1 + organic position 8 (homepage). Dual placement.",
    },
    "salt lake city electrician": {
        "organic_page1": None, "local_pack": None, "lsa": 2,
        "summary": "Local Services Ad #2 only. NOT in Map Pack. NOT in organic page 1.",
    },
    "salt lake plumbing": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "Brand-name query — Salt Lake Plumbing (the company) dominates. Not a relevant SameDay target.",
    },
    "licensed electrician near me": {
        "organic_page1": 8, "local_pack": None, "lsa": None,
        "summary": "Organic position 8 with /service-area/electrical/salt-lake-city-ut/. NOT in Map Pack, NOT in LSAs.",
    },
    "pipe inspection": {
        "organic_page1": 7, "local_pack": None, "lsa": None,
        "summary": "Organic position 7 (top of page 1 informational) with /plumbing/video-inspection/. NOT in Map Pack.",
    },
    "cheap ac repair near me": {
        "organic_page1": None, "local_pack": 2, "lsa": None,
        "summary": "Map Pack #2 only. NOT in organic page 1.",
    },
    "24-hour plumbing": {
        "organic_page1": 11, "local_pack": None, "lsa": None,
        "summary": "Organic position 11 (top of page 2 — borderline) with /plumbing/. NOT in Map Pack.",
    },
    "plumbing inspections": {
        "organic_page1": 3, "local_pack": None, "lsa": None,
        "summary": "STRONG — organic position 3 with /plumbing/video-inspection/. Above the Map Pack.",
    },
    "24 hour electric": {
        "organic_page1": 6, "local_pack": None, "lsa": None,
        "summary": "Two organic placements — position 6 (/service-area/electrical/salt-lake-city-ut/) AND position 13 (/service-area/electrical/south-salt-lake-ut/).",
    },
    "24/7 water heater repair": {
        "organic_page1": 12, "local_pack": None, "lsa": None,
        "summary": "Organic position 12 (top of page 2 — borderline) with /plumbing/. NOT in Map Pack.",
    },
    "water leak detection plumber": {
        "organic_page1": None, "local_pack": None, "lsa": 1,
        "summary": "Local Services Ad #1 (sponsored) only. NOT in Map Pack, NOT in organic page 1.",
    },
    # ===== Rising / Stable / Declining / Emerging trajectory queries =====
    "water heater repair": {
        "organic_page1": None, "local_pack": None, "lsa": 1,
        "summary": "Local Services Ad #1 (sponsored) only. NOT in Map Pack. NOT in organic page 1. Despite Rising classification, live position is page 2+.",
    },
    "ac repair near me": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "TRUE INVISIBILITY — not visible in any SERP feature on page 1. Despite GSC Stable classification at 11.5 with 3,078 impressions.",
    },
    "same day plumbing": {
        "organic_page1": 1, "local_pack": None, "lsa": None,
        "summary": "STRONG — Organic #1 (homepage) + Knowledge Graph + Facebook + Yelp profile + Angi profile. Branded query, top placement.",
    },
    "electrician near me": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "TRUE INVISIBILITY — not visible in any SERP feature on page 1. Despite GSC Stable classification at 8.9 with 1,205 impressions.",
    },
    "24 7 plumber near me": {
        "organic_page1": 7, "local_pack": None, "lsa": None,
        "summary": "Organic position 3 (abs 7) with /plumbing/. Strong organic, no Map Pack.",
    },
    "24 hour plumber": {
        "organic_page1": 10, "local_pack": None, "lsa": None,
        "summary": "Organic position 5 (abs 10) with /plumbing/. NOT in Map Pack. Page 1 organic.",
    },
    "plumbing": {
        "organic_page1": 14, "local_pack": None, "lsa": None,
        "summary": "Organic abs #14 with /plumbing/. Page 2 — NOT on page 1. GSC Emerging at 9.8 may reflect averaging effect.",
    },
    "24 hour plumber salt lake city": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "TRUE PAGE-1 LOSS — not visible on page 1. Confirms GSC Declining 8.4 → 15.3.",
    },
    "24 hour water heater repair near me": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "TRUE PAGE-1 LOSS — not visible on page 1. Confirms GSC Declining 9.5 → 26.6.",
    },
    "24 hour electrician salt lake city": {
        "organic_page1": 5, "local_pack": None, "lsa": 2,
        "summary": "STRONG — LSA #2 + Organic #1 (abs 5) with /service-area/electrical/salt-lake-city-ut/. Multi-placement.",
    },
    "garbage disposal replacement": {
        "organic_page1": 10, "local_pack": None, "lsa": None,
        "summary": "Organic position 5 (abs 10) with /plumbing/garbage-disposals/. Page 1 bottom — borderline. NOT in Map Pack.",
    },
    "ac repair provo ut": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "Page 2+ — not visible on page 1. SERP is Provo-focused; SameDay's HQ is SLC. GSC Emerging classification overstates visibility.",
    },
    "sameday plumbing": {
        "organic_page1": 1, "local_pack": None, "lsa": None,
        "summary": "STRONG — Organic #1 + Knowledge Graph + Facebook #2 + Yelp #3 + Angi #4. Branded query, dominant placement.",
    },
    "sameday utah": {
        "organic_page1": 2, "local_pack": None, "lsa": 1,
        "summary": "STRONG — Paid #1 + Organic #1 (abs 2) + Knowledge Graph + Facebook + Yelp. Branded query, dominant placement.",
    },
    "24 hour furnace repair near me": {
        "organic_page1": 11, "local_pack": None, "lsa": 1,
        "summary": "LSA #1 + Organic #4 (abs 11) with /heating/furnaces/repair/. Strong combined placement.",
    },
    "24/7 plumber salt lake city": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "TRUE PAGE-1 LOSS — not visible on page 1. Confirms GSC Declining 9.4 → 27.5 (steepest decline in trajectory).",
    },
    "24 hour heater repair near me": {
        "organic_page1": 8, "local_pack": 2, "lsa": None,
        "summary": "STRONG — Map Pack #2 + Organic #3 (abs 8) with /heating/. Multi-placement.",
    },
    "ac repair orem utah": {
        "organic_page1": None, "local_pack": None, "lsa": None,
        "summary": "TRUE PAGE-2+ — not visible on page 1. SERP is Orem-focused; SameDay's HQ is SLC. Confirms GSC Declining 13 → 22.5.",
    },
    "24 7 heating and air conditioning": {
        "organic_page1": 9, "local_pack": 1, "lsa": None,
        "summary": "STRONG — Paid #2 + Paid #4 + Map Pack #1 + Organic #3 (abs 9). Multi-placement (heavy paid + organic).",
    },
}


def build_excel(rows: list[dict]) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Trajectory"
    headers = [
        "Query",
        "Trajectory",
        "Pos W3 (Baseline)",
        "Pos W2 (Prior)",
        "Pos W1 (Latest)",
        "Pos Delta (W3->W1)",
        "Impr W3",
        "Impr W2",
        "Impr W1",
        "Impr Delta (W3->W1)",
        "Clicks W1",
        "Live SLC SERP Check",
        "Notes",
    ]
    ws.append(headers)
    header_fill = PatternFill(
        start_color="1F4E78", end_color="1F4E78", fill_type="solid"
    )
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 24

    traj_colors = {
        "Rising": "C6EFCE",
        "Declining": "FFC7CE",
        "Stable": "E7E6E6",
        "Volatile": "FFEB9C",
        "Emerging": "BDD7EE",
        "Disappeared": "F4B084",
        "Insufficient data": "FFFFFF",
    }
    traj_font = {
        "Rising": "006100",
        "Declining": "9C0006",
    }

    for r in rows:
        spot = SERP_SPOT_CHECKS.get(r["query"])
        if spot:
            parts = []
            if spot["lsa"] is not None:
                parts.append(f"LSA #{spot['lsa']}")
            if spot["local_pack"] is not None:
                parts.append(f"Map Pack #{spot['local_pack']}")
            if spot["organic_page1"] is not None:
                parts.append(f"Organic #{spot['organic_page1']}")
            if not parts:
                parts.append("Page 2+ only")
            serp_summary = (
                "; ".join(parts) + " — " + spot["summary"]
            )
        else:
            serp_summary = ""
        ws.append([
            r["query"],
            r["trajectory"],
            r["pos_w3"],
            r["pos_w2"],
            r["pos_w1"],
            r["pos_delta"],
            r["impr_w3"],
            r["impr_w2"],
            r["impr_w1"],
            r["impr_delta"],
            r["clicks_w1"],
            serp_summary,
            r["notes"],
        ])

    for row_idx, r in enumerate(rows, start=2):
        traj = r["trajectory"]
        cell = ws.cell(row=row_idx, column=2)
        cell.fill = PatternFill(
            start_color=traj_colors.get(traj, "FFFFFF"),
            end_color=traj_colors.get(traj, "FFFFFF"),
            fill_type="solid",
        )
        if traj in traj_font:
            cell.font = Font(bold=True, color=traj_font[traj])
        else:
            cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    widths = [42, 16, 12, 12, 12, 14, 11, 11, 11, 14, 11, 70, 50]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + i)].width = w
    ws.freeze_panes = "C2"
    # Wrap text on the wide narrative columns
    from openpyxl.styles import Alignment as _A
    for row_cells in ws.iter_rows(min_row=2, min_col=12, max_col=13):
        for cell in row_cells:
            cell.alignment = _A(wrap_text=True, vertical="top")

    # SERP-context tab — live verification of every classified query
    ws2 = wb.create_sheet("Live SERP Verification")
    ws2.append([
        "Query",
        "Trajectory (GSC)",
        "Local Services Ad",
        "Map Pack",
        "Organic Page 1",
        "Live SLC Verdict",
    ])
    header_fill = PatternFill(
        start_color="1F4E78", end_color="1F4E78", fill_type="solid"
    )
    for cell in ws2[1]:
        cell.fill = header_fill
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 24
    by_query = {r["query"]: r for r in rows}
    for q, spot in SERP_SPOT_CHECKS.items():
        row_data = by_query.get(q, {})
        traj = row_data.get("trajectory", "(not in target set)")
        ws2.append([
            q,
            traj,
            f"#{spot['lsa']}" if spot["lsa"] is not None else "—",
            f"#{spot['local_pack']}" if spot["local_pack"] is not None else "—",
            f"#{spot['organic_page1']}" if spot["organic_page1"] is not None else "Page 2+",
            spot["summary"],
        ])
    widths2 = [40, 16, 16, 12, 16, 90]
    for i, w in enumerate(widths2, start=1):
        ws2.column_dimensions[chr(64 + i)].width = w
    ws2.freeze_panes = "B2"
    for row_cells in ws2.iter_rows(min_row=2, min_col=6, max_col=6):
        for cell in row_cells:
            cell.alignment = _A(wrap_text=True, vertical="top")

    out_path = OUT_DIR / "sameday_keyword_trajectory.xlsx"
    wb.save(out_path)
    return out_path


def main() -> None:
    print("Loading 3 GSC windows...")
    w1 = parse_window(W1_FILE)
    w2 = parse_window(W2_FILE)
    w3 = parse_window(W3_FILE)
    print(f"  W1: {len(w1)} queries")
    print(f"  W2: {len(w2)} queries")
    print(f"  W3: {len(w3)} queries")

    # Build target set from striking-distance + cluster reports
    from openpyxl import load_workbook
    sd_wb = load_workbook(
        ROOT
        / "Clients"
        / "SameDay"
        / "SameDay - Striking Distance Analysis.xlsx"
    )
    sd_ws = sd_wb["Main Tab"]
    target_queries = set()
    for row in sd_ws.iter_rows(min_row=2, values_only=True):
        if row[1]:
            target_queries.add(row[1].lower().strip())

    cluster_money = {
        # Water heater cluster
        "water heater repair",
        "water heater repair near me",
        "water heater repair salt lake city",
        "water heater replacement",
        "water heater replacement near me",
        "tankless water heater installation",
        "tankless water heater repair",
        "hot water heater repair",
        "hot water heater repair near me",
        "salt lake city water heater repair",
        "emergency water heater repair",
        "emergency hot water heater repair",
        "water heater installation near me",
        # Electrician cluster
        "electrician salt lake city",
        "electrician near me",
        "salt lake city electrician",
        "salt lake city electrical repair",
        "emergency electrician near me",
        "ev charger installation",
        # Emergency cluster
        "emergency plumber salt lake city",
        "24 hour plumber salt lake city",
        "emergency plumber near me",
        "24/7 plumber salt lake city",
        # Branded / general
        "sameday utah",
        "sameday plumbing",
        "same day plumbing",
        "plumbers near me",
        "plumbing services salt lake city",
        "plumbers salt lake city",
        "plumbers in salt lake city",
        "plumbers bountiful",
        "plumber south jordan",
        "drain cleaning salt lake city",
        "ac repair provo ut",
        "heat pump installation salt lake city",
        "garbage disposal repair",
        "toilet installation near me",
        "electrician orem",
    }
    target_queries.update(cluster_money)
    print(f"Target keyword set: {len(target_queries)} queries")

    rows = []
    for q in sorted(target_queries):
        d1 = w1.get(q)
        d2 = w2.get(q)
        d3 = w3.get(q)
        if not (d1 or d2 or d3):
            continue
        traj = classify(d1, d2, d3)
        p1 = d1["position"] if d1 else None
        p2 = d2["position"] if d2 else None
        p3 = d3["position"] if d3 else None
        i1 = d1["impressions"] if d1 else 0
        i2 = d2["impressions"] if d2 else 0
        i3 = d3["impressions"] if d3 else 0
        c1 = d1["clicks"] if d1 else 0

        if p1 is not None and p3 is not None:
            pos_delta = round(p3 - p1, 1)
        else:
            pos_delta = None
        impr_delta = i1 - i3

        notes = []
        if traj == "Rising":
            if p1 is not None and p1 <= 10 and p3 is not None and p3 > 10:
                notes.append("Crossed into top-10")
            if p1 is not None and p1 <= 3:
                notes.append("Currently top-3")
        elif traj == "Declining":
            if p3 is not None and p3 <= 10 and p1 is not None and p1 > 10:
                notes.append("DROPPED out of top-10")
            if p1 is not None and p1 > 30:
                notes.append("Now beyond page 3")
        elif traj == "Stable":
            if p1 is not None and p1 <= 3:
                notes.append("Stable top-3")
            elif p1 is not None and p1 <= 10:
                notes.append("Stable page 1")
        elif traj == "Volatile":
            notes.append("Position swinging — needs spot-check")
        elif traj == "Emerging":
            notes.append("First-time appearance in W1")
        elif traj == "Disappeared":
            notes.append("Was ranking, now gone")

        rows.append({
            "query": q,
            "trajectory": traj,
            "pos_w1": p1,
            "pos_w2": p2,
            "pos_w3": p3,
            "pos_delta": pos_delta,
            "impr_w1": i1,
            "impr_w2": i2,
            "impr_w3": i3,
            "impr_delta": impr_delta,
            "clicks_w1": c1,
            "notes": "; ".join(notes),
        })

    rows.sort(key=lambda r: -max(
        r["impr_w1"] or 0, r["impr_w2"] or 0, r["impr_w3"] or 0,
    ))

    out_path = build_excel(rows)
    print(f"Wrote {out_path}")

    # Summary stats
    summary = {
        "total_target_queries": len(target_queries),
        "queries_with_data": len(rows),
        "trajectory_counts": {},
    }
    for r in rows:
        t = r["trajectory"]
        summary["trajectory_counts"][t] = (
            summary["trajectory_counts"].get(t, 0) + 1
        )
    summary_path = (
        OUT_DIR / "_keyword_trajectory_summary.json"
    )
    summary_path.write_text(
        json.dumps({
            "summary": summary,
            "rows": rows,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {summary_path}")
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    main()
