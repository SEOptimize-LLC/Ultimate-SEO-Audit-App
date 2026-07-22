"""Comfort Solutions keyword trajectory analysis.

Same methodology as SameDay. 3x 28-day GSC windows, classifies each
target query as Rising / Stable / Declining / Volatile / Disappeared
/ Emerging. Live SLC SERP verification layered on top.

Windows:
  W1 = latest 28 days (2026-04-08 to 2026-05-06)
  W2 = prior 28 days (2026-03-11 to 2026-04-07)
  W3 = baseline 28 days (2026-02-11 to 2026-03-10)
"""
from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook, load_workbook
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
    r"\mcp-gsc-mcp-get_advanced_search_analytics-1778082992696.txt"
)
W2_FILE = (
    r"C:\Users\admin\.claude\projects"
    r"\c--Users-admin-Documents-Marketing-Roger-SEO-AI-Automations-Claude"
    r"-Claude-Code---VS-Code-SEO-Projects-Projects-Ultimate-SEO-Auditor"
    r"\9e9d695c-1264-41a1-b774-962076dcba36\tool-results"
    r"\mcp-gsc-mcp-get_advanced_search_analytics-1778082999609.txt"
)
W3_FILE = (
    r"C:\Users\admin\.claude\projects"
    r"\c--Users-admin-Documents-Marketing-Roger-SEO-AI-Automations-Claude"
    r"-Claude-Code---VS-Code-SEO-Projects-Projects-Ultimate-SEO-Auditor"
    r"\9e9d695c-1264-41a1-b774-962076dcba36\tool-results"
    r"\mcp-gsc-mcp-get_advanced_search_analytics-1778083007771.txt"
)

OUT_DIR = ROOT / "Clients" / "Comfort" / "Full SEO Audit"

HEADER_FILL = PatternFill(
    start_color="1F4E78", end_color="1F4E78", fill_type="solid"
)


def parse_window(path: str) -> dict[str, dict]:
    """Load a GSC tool-result JSON file and return {query: metrics}."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    text = data["result"]
    out = {}
    for line in text.split("\n"):
        if " | " not in line:
            continue
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


def classify(w1, w2, w3) -> str:
    has_w1 = bool(w1)
    has_w3 = bool(w3)
    if has_w1 and not has_w3 and not w2:
        return "Emerging"
    if not has_w1 and (w2 or has_w3):
        return "Disappeared"
    if not (has_w1 and has_w3):
        return "Insufficient data"
    p1, p3 = w1["position"], w3["position"]
    p2 = w2["position"] if w2 else (p1 + p3) / 2
    delta = p3 - p1
    swing = max(p1, p2, p3) - min(p1, p2, p3)
    if delta >= 2:
        return "Rising"
    if delta <= -2:
        return "Declining"
    if swing >= 5:
        return "Volatile"
    return "Stable"


# Live SERP findings from May 6 verification (8 queries already done)
SERP_SPOT_CHECKS = {
    "comfort solutions": {
        "lsa": None, "local_pack": None, "organic": None,
        "summary": "NOT VISIBLE on page 1 — generic 'comfort' SERP dominated by clothing brand Comfrt, Wikipedia, Reddit.",
    },
    "comfort solutions ogden": {
        "lsa": None, "local_pack": None, "organic": 1,
        "summary": "STRONG — Organic #1 (homepage) + Knowledge Graph + Google Reviews 4.9 (2,679).",
    },
    "fireplace repair salt lake city": {
        "lsa": None, "local_pack": 3, "organic": 16,
        "summary": "Multi-placement: Paid #2 + Local Pack #3 + Sponsored Local #4 + organic #4 abs 16 (fireplacesutah.com sub-brand).",
    },
    "gas fireplace repair salt lake city": {
        "lsa": None, "local_pack": None, "organic": None,
        "summary": "Cited in AI Overview as 'Comfort Solutions (Sandy): 24/7 emergency'. NOT in organic page 1.",
    },
    "furnace repair salt lake city": {
        "lsa": None, "local_pack": None, "organic": 9,
        "summary": "Organic #4 (abs 9) with /furnace-repair-salt-lake-city/. Page 1 organic. NOT in Map Pack.",
    },
    "hvac ogden utah": {
        "lsa": None, "local_pack": None, "organic": None,
        "summary": "Paid #2 only. NOT in organic page 1. Mountain Air dominates Map Pack with 4.9/3,700 reviews.",
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
    for cell in ws[1]:
        cell.fill = HEADER_FILL
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
    }
    traj_font = {"Rising": "006100", "Declining": "9C0006"}

    for r in rows:
        spot = SERP_SPOT_CHECKS.get(r["query"])
        if spot:
            parts = []
            if spot["lsa"] is not None:
                parts.append(f"LSA #{spot['lsa']}")
            if spot["local_pack"] is not None:
                parts.append(f"Map Pack #{spot['local_pack']}")
            if spot["organic"] is not None:
                parts.append(f"Organic #{spot['organic']}")
            if not parts:
                parts.append("Page 2+ only")
            serp = "; ".join(parts) + " — " + spot["summary"]
        else:
            serp = ""
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
            serp,
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
    for row_cells in ws.iter_rows(min_row=2, min_col=12, max_col=13):
        for cell in row_cells:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # SERP-context tab
    ws2 = wb.create_sheet("Live SERP Verification")
    ws2.append([
        "Query", "Trajectory (GSC)", "LSA", "Map Pack",
        "Organic Page 1", "Live SLC Verdict",
    ])
    for cell in ws2[1]:
        cell.fill = HEADER_FILL
        cell.font = Font(bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 24
    by_query = {r["query"]: r for r in rows}
    for q, spot in SERP_SPOT_CHECKS.items():
        traj = by_query.get(q, {}).get("trajectory", "(not in target)")
        ws2.append([
            q, traj,
            f"#{spot['lsa']}" if spot["lsa"] else "—",
            f"#{spot['local_pack']}" if spot["local_pack"] else "—",
            f"#{spot['organic']}" if spot["organic"] else "Page 2+",
            spot["summary"],
        ])
    widths2 = [42, 16, 12, 12, 18, 90]
    for i, w in enumerate(widths2, start=1):
        ws2.column_dimensions[chr(64 + i)].width = w
    ws2.freeze_panes = "B2"
    for row_cells in ws2.iter_rows(min_row=2, min_col=6, max_col=6):
        for cell in row_cells:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    out_path = OUT_DIR / "comfort_keyword_trajectory.xlsx"
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

    # Build target keyword set from the 138-keyword snapshot
    snapshot_csv = (
        OUT_DIR / "_keyword_data" / "comfort_ranked_keywords_snapshot.csv"
    )
    target_queries = set()
    if snapshot_csv.exists():
        import csv
        with open(snapshot_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                target_queries.add(row["keyword"].lower().strip())

    # Add strategic queries from the audit
    strategic = {
        # Brand
        "comfort solutions", "comfort solutions ogden",
        "comfort solutions sandy", "comfort solutions utah",
        "comfort solutions hvac", "comfort solutions heating and cooling",
        "comfort solutions near me", "comfort solutions heating and air",
        "comfort solutions west haven", "comfort solutions inc",
        # Fireplace
        "fireplace repair salt lake city",
        "gas fireplace repair salt lake city",
        "gas fireplaces salt lake city", "fireplace insert efficiency",
        "fireplace smoke in house", "what is a decorative fireplace",
        "fireplace insert furnace",
        # HVAC commercial
        "furnace repair salt lake city", "salt lake city furnace repair",
        "hvac ogden", "hvac ogden utah", "hvac companies utah",
        "hvac sandy utah", "hvac park city utah", "sandy hvac",
        "utah furnace repair", "furnace repair utah",
        "ac repair sandy utah", "air conditioner repair sandy utah",
        "air conditioning repair sandy utah",
        # HVAC informational
        "what is a tankless water heater",
        "tankless water heaters utah", "hvac control boards",
        "hvac system residential",
    }
    target_queries.update(strategic)
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
        r["impr_w1"] or 0, r["impr_w2"] or 0, r["impr_w3"] or 0
    ))

    out_path = build_excel(rows)
    print(f"Wrote {out_path}")

    # Summary
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
    summary_path = OUT_DIR / "_keyword_trajectory_summary.json"
    summary_path.write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {summary_path}")
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    main()
