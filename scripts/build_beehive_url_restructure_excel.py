"""Build the Beehive URL Restructuring Excel deliverable for the dev team.

Output: Clients/Beehive/Full Site SEO Audit/beehive_url_restructuring.xlsx
Tabs:
  1. Summary             - Cluster KPIs + the 4 live findings
  2. Decisions Needed    - 5 open decisions blocking the migration
  3. Risk Tiering        - All 45 pages tier-sorted (HIGH/MEDIUM/LOW)
  4. Redirect Map        - Source URL -> Target URL (the dev's working list)
  5. Implementation Order- Phase-by-phase plan
  6. Internal Link Audit - Where to look for internal links to update
"""
from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DATA = Path("/tmp/beehive_url_restructure_data.json")
OUTPUT = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "beehive_url_restructuring.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
DECISION_FILL = PatternFill("solid", fgColor="C00000")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
DEFAULT_FONT = Font(name="Calibri", size=11, bold=False)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row=1, decision=False):
    fill = DECISION_FILL if decision else HEADER_FILL
    for cell in ws[row]:
        cell.fill = fill
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 32


def autosize(ws, min_w=10, max_w=80):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        longest = 0
        for cell in col:
            if cell.value is None:
                continue
            longest = max(longest, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max(min_w, longest + 2), max_w)


def normalize_data_rows(ws, start_row=2, wrap_cols: list[int] | None = None):
    """Apply explicit Calibri 11 not-bold to all data cells. Wrap only specified columns."""
    wrap_cols = wrap_cols or []
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.font = DEFAULT_FONT
            if cell.column in wrap_cols:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            else:
                cell.alignment = Alignment(wrap_text=False, vertical="center")


def main():
    with DATA.open() as f:
        results = json.load(f)

    wb = Workbook()

    # ---------- Summary ----------
    ws = wb.active
    ws.title = "Summary"
    total_imps = sum(r["imps"] for r in results)
    total_clicks = sum(r["clicks"] for r in results)
    total_bl = sum(r["bl"] for r in results)
    total_rd = sum(r["rd"] for r in results)
    hi = [r for r in results if r["risk"] == "HIGH"]
    md = [r for r in results if r["risk"] == "MEDIUM"]
    lo = [r for r in results if r["risk"] == "LOW"]

    summary = [
        ("Item", "Value", "Notes"),
        ("Task", "Execute URL restructuring (45 service pages -> /services/)", "Roadmap Item #15 (P3)"),
        ("Audience", "Web developer + SEO lead", "Pre-flight + execution + monitoring"),
        ("Pages in scope", 45, "Per Beehive URL Mapping spreadsheet (Parent Services New tab)"),
        ("Combined impressions (90d)", total_imps, "The visibility being moved"),
        ("Combined clicks (90d)", total_clicks, "Already low CTR - separate concern"),
        ("Combined backlinks", total_bl, "External equity at risk if redirects break"),
        ("Combined referring domains", total_rd, ""),
        ("HIGH risk pages", len(hi), ">=1k imps OR >=5 BL OR >=1 click"),
        ("MEDIUM risk pages", len(md), ">=100 imps OR >=1 BL"),
        ("LOW risk pages", len(lo), "Everything else"),
        ("", "", ""),
        ("Live finding 1", "Both URL versions render", "All 45 /services/<slug>/ already return 200 - migration flips canonical, not creates URLs"),
        ("Live finding 2", "/drain-cleaning-utah/ already redirects", "Goes to /drain-cleaning-salt-lake-city/ (not in URL Mapping plan) - reconcile before touching Drains"),
        ("Live finding 3", "Inventory's 'Non-Indexable' flag is stale", "41 of 45 pages flagged but live verification confirms indexed"),
        ("Live finding 4", "/sewer-line-repair-utah-old/ has 'old' suffix", "Don't migrate this one - delete + merge into canonical"),
        ("", "", ""),
        ("Top stakes page", "/water-heater-installation-services-utah/", f"686,498 imps - 78% of cluster traffic"),
        ("Top backlinks page", "/plumbing-repairs-utah/", "84 backlinks from 37 referring domains"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[3])

    # ---------- Decisions Needed ----------
    ws = wb.create_sheet("Decisions Needed")
    ws.append(["#", "Decision", "Why it matters", "Recommended", "Owner"])
    decisions = [
        (
            1,
            "What to do with /drain-cleaning-utah/ - keep redirect to /drain-cleaning-salt-lake-city/, or undo and migrate to /services/drain-cleaning-utah/",
            "Affects the highest-stakes Drains page (77k imps, 25 BL)",
            "Decide based on which URL has more backlink equity - likely keep current redirect target as canonical",
            "SEO + Dev",
        ),
        (
            2,
            "What to do with /sewer-line-repair-utah-old/",
            "'-old' suffix should not enter new hierarchy",
            "Delete + merge content into /services/sewer-line-repair-utah/",
            "SEO",
        ),
        (
            3,
            "What to do with /remodeling/",
            "Page is dead (4 imps), duplicates /remodeling-plumber-utah/ (1,621 imps)",
            "Per URL Mapping comment: repurpose for HVAC remodeling OR delete + 301 to canonical",
            "Content + SEO",
        ),
        (
            4,
            "Menu design: Commercial Services, Plumbing, Residential Services categories",
            "URL Mapping flags these as 'still need to decide' - affects internal link architecture",
            "Sketch new menu BEFORE migration, not after",
            "Design + SEO",
        ),
        (
            5,
            "Whether to include the topical cluster restructure (Drain & Sewer, Water Heaters, etc.) in this migration or as Phase 2",
            "Doing both at once is risky; doing them separately means two migration events",
            "Separate - execute flat /services/<slug>/ migration first, topical clusters as Phase 2",
            "SEO + Dev",
        ),
    ]
    for r in decisions:
        ws.append(r)
    style_header(ws, decision=True)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    normalize_data_rows(ws, wrap_cols=[2, 3, 4])

    # ---------- Risk Tiering ----------
    ws = wb.create_sheet("Risk Tiering")
    ws.append(
        [
            "Risk",
            "Category",
            "Source URL",
            "Target URL",
            "Impressions (90d)",
            "Clicks (90d)",
            "Backlinks",
            "RDs",
            "Word Count",
            "Internal Inlinks",
            "URL Mapping Comment",
        ]
    )
    sorted_results = sorted(results, key=lambda r: (
        {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[r["risk"]],
        -r["imps"],
    ))
    for r in sorted_results:
        ws.append([
            r["risk"],
            r["category"] or "",
            r["src"],
            r["tgt"],
            r["imps"],
            r["clicks"],
            r["bl"],
            r["rd"],
            r["wc"],
            r["inlinks"],
            (r["comment"] or "").strip(),
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[11])

    # ---------- Redirect Map ----------
    ws = wb.create_sheet("Redirect Map")
    ws.append(["#", "Source URL (CURRENT)", "Target URL (NEW)", "HTTP Method", "Phase Batch"])
    # Order by phase
    by_phase = []
    for r in sorted(results, key=lambda r: (
        {"HIGH": 2, "MEDIUM": 1, "LOW": 0}[r["risk"]],
        -r["imps"],
    )):
        if r["risk"] == "LOW":
            phase = "Phase 1 (LOW)"
        elif r["risk"] == "MEDIUM":
            phase = "Phase 2 (MEDIUM)"
        elif r["imps"] >= 10000:
            phase = "Phase 3c (HIGH - top 6 - migrate LAST)"
        else:
            phase = "Phase 3a/3b (HIGH - other)"
        by_phase.append((r, phase))
    for i, (r, phase) in enumerate(by_phase, 1):
        ws.append([i, r["src"], r["tgt"], "301", phase])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws)

    # ---------- Implementation Order ----------
    ws = wb.create_sheet("Implementation Order")
    ws.append(["Phase", "Week", "Action", "Pages", "Risk"])
    impl = [
        (
            "Phase 0",
            "Week 1",
            "Pre-flight: resolve 5 open decisions (Decisions Needed tab), run internal-link crawl, build update list",
            "All",
            "N/A",
        ),
        (
            "Phase 1",
            "Week 2",
            "Migrate LOW-risk batch first as confidence check. Validate migration playbook before touching higher-stakes pages.",
            "8 pages",
            "LOW",
        ),
        (
            "Phase 2",
            "Week 3",
            "Migrate MEDIUM-risk batch as single batch once Phase 1 monitored 7+ days with no issues.",
            "6 pages",
            "MEDIUM",
        ),
        (
            "Phase 3a",
            "Week 4",
            "HIGH-risk sub-batch 1 (excluding top 6 by impressions). Group by category for context.",
            "~10 pages",
            "HIGH",
        ),
        (
            "Phase 3b",
            "Week 5",
            "HIGH-risk sub-batch 2 (excluding top 6 by impressions).",
            "~10 pages",
            "HIGH",
        ),
        (
            "Phase 3c",
            "Week 6",
            "TOP 6 highest-stakes pages: water-heater-installation-services-utah, drain-cleaning-utah, emergency-plumber, sewer-line-repair-utah, commercial-plumber-utah, water-softeners-utah. Migrate LAST after playbook proven.",
            "6 pages",
            "HIGH",
        ),
        (
            "Phase 4",
            "Week 7",
            "Verification: full site crawl, confirm 100% of source URLs return 301, 100% of target URLs return 200, 0 internal links pointing to old URLs, sitemap matches new structure, top 6 pages show new canonical in GSC URL Inspection.",
            "All 45",
            "N/A",
        ),
        (
            "Phase 5",
            "Weeks 8-12",
            "Monitor: 301 chain length on each URL, GSC reprocessing on top 6 pages, impression/click delta vs 14 days pre-migration, any 404 errors referencing old URLs.",
            "All 45",
            "N/A",
        ),
    ]
    for r in impl:
        ws.append(r)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    normalize_data_rows(ws, wrap_cols=[2])

    # ---------- Internal Link Audit ----------
    ws = wb.create_sheet("Internal Link Audit")
    ws.append(["Location", "What to check", "Update mechanism", "Priority"])
    audit = [
        ("Main navigation menu", "Each <a href> targeting any of the 45 source URLs", "WordPress menu editor", "HIGH"),
        ("Footer", "Footer links to any of the 45 source URLs", "Theme footer.php or widget area", "HIGH"),
        ("Homepage hero/feature blocks", "Service-page CTAs on homepage", "Homepage editor or page-builder blocks", "HIGH"),
        ("In-content links (blog posts)", "515 blog posts may reference service pages by old URL", "Database SQL UPDATE on wp_posts.post_content + plugin like Better Search Replace", "HIGH"),
        ("In-content links (other service pages)", "Service pages may cross-link to other service pages by old URL", "Same as above", "HIGH"),
        ("Local service pages (under /our-locations/)", "Local pages link to parent service pages", "Same as above", "HIGH"),
        ("XML sitemap", "Old URLs should be removed and new URLs added", "Yoast/Rank Math/etc. - regenerate after URL changes", "HIGH"),
        ("Schema markup (LocalBusiness, Service, BreadcrumbList)", "Schema may reference old URLs in @id or url fields", "Inspect each schema block via Rich Results Test", "MEDIUM"),
        ("Image src/srcset", "Featured images may use absolute URLs containing old paths", "Database scan + replace", "LOW"),
        ("301 redirects (existing)", "Some redirects may point to one of the 45 source URLs - chain risk", "Audit existing redirect rules", "MEDIUM"),
        ("Robots.txt", "Confirm no Disallow rules block /services/", "Direct edit", "LOW"),
        ("Canonical tags", "After URL flip, canonicals on /services/<slug>/ must self-canonical (not point back to old URL)", "WordPress permalink config", "HIGH"),
    ]
    for r in audit:
        ws.append(r)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    normalize_data_rows(ws, wrap_cols=[1, 2])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
