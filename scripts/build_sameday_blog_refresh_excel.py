"""Build the SameDay Blog Refresh Implementation Plan Excel.

Output: Clients/SameDay/Full SEO Audit/sameday_blog_refresh_plan.xlsx

Tabs:
  1. Summary             - the two-population framing + tier counts
  2. Tier A - Protect    - top performers, careful refresh only
  3. Tier B - Lift       - page-2 posts, refresh for CTR + position
  4. Tier C - Diagnose   - impressions but no clicks, refresh + investigate
  5. Tier D - Triage     - low-visibility indexed, mostly noindex/merge
  6. Cluster Merges      - 5 cannibalization clusters with survivors
  7. Implementation Order- Phase-by-phase sequencing
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
CLIENT_DIR = ROOT / "Clients" / "SameDay" / "Full SEO Audit"
ENRICHED = CLIENT_DIR / "_survivors_49_enriched.csv"
LINKS_404 = CLIENT_DIR / "_survivors_links_to_404.csv"
LINKS_NOTIND = CLIENT_DIR / "_survivors_links_to_notindexed.csv"
CLUSTERS = CLIENT_DIR / "blog_cannibalization_clusters.xlsx"
OUTPUT = CLIENT_DIR / "sameday_blog_refresh_plan.xlsx"


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
TIER_FILLS = {
    "A": PatternFill("solid", fgColor="C6EFCE"),
    "B": PatternFill("solid", fgColor="FFEB9C"),
    "C": PatternFill("solid", fgColor="FFD9B3"),
    "D": PatternFill("solid", fgColor="F4CCCC"),
}


def style_header(ws, row: int = 1) -> None:
    for cell in ws[row]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 38


def autosize(ws, min_w: int = 10, max_w: int = 70) -> None:
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        longest = 0
        for cell in col:
            if cell.value is None:
                continue
            longest = max(longest, len(str(cell.value)))
        ws.column_dimensions[letter].width = min(max(min_w, longest + 2), max_w)


def wrap_data(ws, start_row: int = 2) -> None:
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def freeze(ws, row: str = "2") -> None:
    ws.freeze_panes = f"A{row}"


def url_slug(u: str) -> str:
    return u.rstrip("/").rsplit("/", 1)[-1]


def stale_band(days: float) -> str:
    if pd.isna(days):
        return "unknown"
    if days <= 90:
        return "fresh (≤90d)"
    if days <= 180:
        return "recent (91-180d)"
    if days <= 365:
        return "aging (181-365d)"
    if days <= 540:
        return "stale (12-18mo)"
    return "very stale (>18mo)"


def recommend_action(tier: str, days_since_mod: float, impressions: float) -> str:
    """Tier-driven recommendation."""
    if tier == "A":
        if days_since_mod <= 90:
            return "PROTECT - already fresh, leave alone"
        return "PROTECT-REFRESH - careful update, no URL/title change"
    if tier == "B":
        if days_since_mod <= 90:
            return "MONITOR - recently refreshed, watch position"
        return "LIFT-REFRESH - rewrite for page-1 (target +3 to +5 positions)"
    if tier == "C":
        if days_since_mod <= 90:
            return "DIAGNOSE - recently refreshed but 0 clicks; check title/intent"
        return "EXPAND-REFRESH - add depth + better title; re-evaluate intent"
    # Tier D
    if impressions < 50:
        return "PRUNE - noindex or merge into related survivor"
    return "TRIAGE - decide noindex vs merge vs minimal refresh"


def effort_hours(action: str) -> str:
    if action.startswith("PROTECT - already"):
        return "0"
    if action.startswith("PROTECT-REFRESH"):
        return "4-6"
    if action.startswith("MONITOR"):
        return "0"
    if action.startswith("LIFT-REFRESH"):
        return "3-4"
    if action.startswith("DIAGNOSE"):
        return "1-2"
    if action.startswith("EXPAND-REFRESH"):
        return "2-3"
    if action.startswith("PRUNE"):
        return "0.25"
    if action.startswith("TRIAGE"):
        return "0.5-1"
    return ""


def load_data() -> pd.DataFrame:
    df = pd.read_csv(ENRICHED)
    df["slug"] = df["url"].apply(url_slug)
    df["staleness"] = df["days_since_mod"].apply(stale_band)
    df["action"] = df.apply(
        lambda r: recommend_action(r["Tier"], r["days_since_mod"], r["Impressions"]),
        axis=1,
    )
    df["effort_hours"] = df["action"].apply(effort_hours)

    # Bad-link flags
    bad_404 = pd.read_csv(LINKS_404).groupby("source").size().rename("links_to_404")
    bad_ni = pd.read_csv(LINKS_NOTIND).groupby("source").size().rename("links_to_notindexed")
    df = df.merge(bad_404, left_on="url", right_index=True, how="left")
    df = df.merge(bad_ni, left_on="url", right_index=True, how="left")
    df["links_to_404"] = df["links_to_404"].fillna(0).astype(int)
    df["links_to_notindexed"] = df["links_to_notindexed"].fillna(0).astype(int)
    return df


def write_summary(wb: Workbook, df: pd.DataFrame) -> None:
    ws = wb.active
    ws.title = "Summary"

    ws.append(["SameDay Blog Refresh — Implementation Plan"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])

    ws.append(["Two distinct populations to address"])
    ws["A3"].font = Font(bold=True, size=12)
    ws.append([])

    headers = ["Population", "Posts", "Status", "Recommended action"]
    ws.append(headers)
    style_header(ws, ws.max_row)
    rows = [
        [
            "Not-indexed posts",
            119,
            "Median age 9.6 years, never updated",
            "Consolidate or noindex (separate workstream)",
        ],
        [
            "Indexed survivors",
            49,
            "Median publish 2020, 47 of 49 modified at least once, 34 of 49 stale (>12 mo)",
            "Refresh queue — this plan",
        ],
    ]
    for r in rows:
        ws.append(r)

    ws.append([])
    ws.append(["Survivor breakdown by tier"])
    ws[f"A{ws.max_row}"].font = Font(bold=True, size=12)
    ws.append([])
    headers = ["Tier", "Definition", "Posts", "Stale (>12 mo)", "Total effort"]
    ws.append(headers)
    style_header(ws, ws.max_row)

    tier_defs = {
        "A": ("≥10 clicks/90d - top performers", 2, "4-6 hrs"),
        "B": ("1-9 clicks/90d - page-2 ranking", 13, "3-4 hrs"),
        "C": ("0 clicks, ≥100 impressions", 9, "2-3 hrs"),
        "D": ("0 clicks, <100 impressions", 25, "0.25-1 hr"),
    }
    for t, (defn, count, eff) in tier_defs.items():
        stale_count = int(((df["Tier"] == t) & (df["days_since_mod"] > 365)).sum())
        ws.append([t, defn, count, stale_count, eff])

    ws.append([])
    ws.append(["One-time tracks (non-tier work)"])
    ws[f"A{ws.max_row}"].font = Font(bold=True, size=12)
    ws.append([])
    headers = ["Track", "Description", "Effort"]
    ws.append(headers)
    style_header(ws, ws.max_row)
    ws.append([
        "Template fix",
        "Add visible 'Last Updated:' block to single-blog-post Elementor template (currently dateModified is in JSON-LD only)",
        "2-4 hrs",
    ])
    ws.append([
        "Bad-link cleanup",
        "Fix 2 links to /priority-plus-maintenance-plan/ (404) and 21 links to to-be-noindexed posts. Concentrated in heating-furnace-guide (7) and plumbing-repair-guide (3).",
        "4-6 hrs",
    ])
    ws.append([
        "Cluster merges",
        "5 cannibalization clusters with indexed survivors — see Cluster Merges tab",
        "20-40 hrs",
    ])

    ws.append([])
    ws.append(["Total effort estimate"])
    ws[f"A{ws.max_row}"].font = Font(bold=True, size=12)
    ws.append(["Refresh queue + cluster merges + one-time tracks: 70-110 hours over 6-10 weeks"])

    autosize(ws, max_w=80)
    wrap_data(ws, start_row=2)


def write_tier_tab(wb: Workbook, df: pd.DataFrame, tier: str, title: str, guidance: str) -> None:
    sub = df[df["Tier"] == tier].sort_values(
        ["days_since_mod", "Impressions"], ascending=[False, False]
    ).copy()
    ws = wb.create_sheet(title)

    ws.append([f"Tier {tier} — {title.split('-',1)[1].strip()}"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([guidance])
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 50
    ws.append([])

    cols = [
        "URL slug",
        "Full URL",
        "Clicks/90d",
        "Impressions",
        "Position",
        "Published",
        "Last Modified",
        "Days stale",
        "Word count",
        "Outbound internal links",
        "Links to 404",
        "Links to soon-noindexed",
        "Recommended action",
        "Effort (hrs)",
    ]
    ws.append(cols)
    style_header(ws, ws.max_row)
    header_row = ws.max_row

    for _, r in sub.iterrows():
        ws.append([
            r["slug"],
            r["url"],
            int(r["Clicks"]) if pd.notna(r["Clicks"]) else 0,
            int(r["Impressions"]) if pd.notna(r["Impressions"]) else 0,
            round(float(r["Position"]), 1) if pd.notna(r["Position"]) else "",
            int(r["pub_year"]) if pd.notna(r["pub_year"]) else "",
            int(r["mod_year"]) if pd.notna(r["mod_year"]) else "",
            int(r["days_since_mod"]) if pd.notna(r["days_since_mod"]) else "",
            int(r["word_count_main"]) if pd.notna(r["word_count_main"]) else "",
            int(r["outbound_internal_links"]) if pd.notna(r["outbound_internal_links"]) else "",
            int(r["links_to_404"]),
            int(r["links_to_notindexed"]),
            r["action"],
            r["effort_hours"],
        ])

    # Color the URL slug column by tier
    fill = TIER_FILLS[tier]
    for row in ws.iter_rows(min_row=header_row + 1, max_col=1):
        for cell in row:
            cell.fill = fill

    autosize(ws, max_w=70)
    wrap_data(ws, start_row=header_row)
    freeze(ws, row=str(header_row + 1))


def write_clusters(wb: Workbook, df: pd.DataFrame) -> None:
    ws = wb.create_sheet("Cluster Merges")
    ws.append(["Cannibalization Cluster Merges"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([
        "Resolve cannibalization BEFORE refreshing survivors in these clusters. "
        "Pick canonical winner, 301-redirect cluster losers into the winner, "
        "then absorb merged content during the survivor refresh."
    ])
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 50
    ws.append([])

    canni = pd.read_excel(CLUSTERS)
    canni["URL"] = canni["URL"].astype(str)

    cols = ["Cluster", "URL", "Coverage", "Published", "Clicks", "Impressions", "Role"]
    ws.append(cols)
    style_header(ws, ws.max_row)
    header_row = ws.max_row

    survivor_urls = set(df["url"].str.replace("https://samedayutah.com", "", regex=False).str.rstrip("/"))

    for _, r in canni.sort_values(["Cluster", "Coverage"]).iterrows():
        url_path = r["URL"].rstrip("/")
        is_survivor = url_path in survivor_urls
        if is_survivor:
            role = "CANONICAL (keep + refresh)"
        elif r["Coverage"] == "Submitted and indexed":
            role = "CANONICAL CANDIDATE (no clear winner — manual choice)"
        else:
            role = "MERGE INTO CANONICAL (301 redirect)"
        pub = pd.to_datetime(r["Published"]).strftime("%Y-%m-%d") if pd.notna(r["Published"]) else ""
        ws.append([
            r["Cluster"],
            r["URL"],
            r["Coverage"],
            pub,
            int(r["Clicks"]) if pd.notna(r["Clicks"]) else 0,
            int(r["Impressions"]) if pd.notna(r["Impressions"]) else 0,
            role,
        ])

    autosize(ws, max_w=70)
    wrap_data(ws, start_row=header_row)
    freeze(ws, row=str(header_row + 1))


def write_implementation_order(wb: Workbook) -> None:
    ws = wb.create_sheet("Implementation Order")
    ws.append(["Implementation Sequence"])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([])

    cols = ["Phase", "Weeks", "Work", "Effort (hrs)", "Why this order"]
    ws.append(cols)
    style_header(ws, ws.max_row)

    phases = [
        [
            "1. Template fix",
            "Week 1",
            "Add visible 'Last Updated: Month YYYY' block to bc-sameday-heating single-post template. Without this, future dateModified updates are invisible to users.",
            "2-4",
            "One-time, high-leverage. Affects all current + future posts.",
        ],
        [
            "2. Bad-link cleanup",
            "Week 1",
            "Remove/redirect 2 links to /priority-plus-maintenance-plan/. Replace 21 links to to-be-noindexed posts (mostly in heating-furnace-guide and plumbing-repair-guide).",
            "4-6",
            "Quick wins. Stops bleeding link equity.",
        ],
        [
            "3. Cluster merges",
            "Weeks 2-4",
            "Resolve 5 cannibalization clusters with indexed survivors (Indoor Air Quality, Frozen Pipes, Energy Savings, Water Heater, Drain Cleaning). 301-redirect cluster losers into survivors.",
            "20-40",
            "Don't refresh survivors that are about to absorb sibling content. Merge first, refresh once.",
        ],
        [
            "4. Tier A refresh",
            "Week 4",
            "Protect-refresh the 2 Tier A posts. No URL or title change. Update body, internal links, FAQs, schema.",
            "8-12",
            "Highest-value asset (causes-of-low-voltage = 18k impressions, position 2.8). Touch carefully first.",
        ],
        [
            "5. Tier B refresh",
            "Weeks 5-8",
            "Lift-refresh the 13 Tier B posts (page-2 ranking, 1-9 clicks each). Add depth, refresh title/meta, internal links to service pages, visible Last Updated date.",
            "39-52",
            "Highest-ROI tier — small effort, large click uplift potential.",
        ],
        [
            "6. Tier C diagnose+expand",
            "Weeks 9-10",
            "Tier C has impressions but no clicks. Diagnose (intent mismatch? title/meta? thin?), then expand or rewrite as needed.",
            "18-27",
            "Lower priority than B because click-uplift is uncertain.",
        ],
        [
            "7. Tier D triage",
            "Weeks 9-10",
            "Most should be noindexed or merged into a related survivor. Don't burn budget rewriting low-impression posts.",
            "8-12",
            "Pruning and consolidation, not refresh. Cuts overhead from the queue.",
        ],
        [
            "8. Re-measure",
            "Weeks 13-22",
            "Compare GSC clicks/impressions/position 90 days after each refresh. Use to calibrate ROI for future content investment.",
            "ongoing",
            "Verify the refresh actually moved metrics. Not assumed — measured.",
        ],
    ]
    for p in phases:
        ws.append(p)

    autosize(ws, max_w=80)
    wrap_data(ws, start_row=3)
    freeze(ws, row="4")


def main() -> None:
    df = load_data()
    wb = Workbook()
    write_summary(wb, df)

    write_tier_tab(
        wb, df, "A", "Tier A - Protect",
        "Top performers (≥10 clicks/90d). Touch carefully. NO URL changes, NO title rewrites. "
        "Refresh body content, internal links, FAQs, and visible Last Updated date. "
        "Re-submit to GSC after publishing.",
    )
    write_tier_tab(
        wb, df, "B", "Tier B - Lift",
        "Page-2 posts earning 1-9 clicks. Highest-ROI refresh queue. "
        "Goal: lift +3 to +5 positions through depth, freshness, internal links, and "
        "title/meta optimization. Add visible Last Updated date when template ships.",
    )
    write_tier_tab(
        wb, df, "C", "Tier C - Diagnose",
        "Indexed and visible (≥100 impressions) but earning 0 clicks. "
        "Diagnose intent vs query mismatch BEFORE refreshing. Likely needs title/meta rewrite, "
        "topical expansion, or both. If intent is wrong, consider redirect to a better-fit page.",
    )
    write_tier_tab(
        wb, df, "D", "Tier D - Triage",
        "Indexed but low-visibility (<100 impressions). Most should be noindexed or merged "
        "into a related survivor. Do NOT spend refresh budget here unless a post is "
        "topically valuable enough to consolidate INTO.",
    )
    write_clusters(wb, df)
    write_implementation_order(wb)

    wb.save(OUTPUT)
    print(f"Wrote: {OUTPUT}")


if __name__ == "__main__":
    main()
