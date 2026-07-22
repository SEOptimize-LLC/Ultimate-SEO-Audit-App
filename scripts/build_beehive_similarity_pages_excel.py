"""Build the Beehive Similarity Pages Differentiation Excel deliverable.

Output: Clients/Beehive/Full Site SEO Audit/beehive_similarity_pages_differentiation.xlsx
Tabs:
  1. Summary             - The 3 pages + the identity-crisis finding
  2. Page Diagnoses      - Per-page breakdown (live verification + GSC)
  3. Differentiation Framework - 5 dimensions every page must hit
  4. Per-Page Briefs     - Title, H1, sections, word count target, internal links
  5. Implementation Order- Phase-by-phase plan
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Clients" / "Beehive" / "Full Site SEO Audit" / "beehive_similarity_pages_differentiation.xlsx"


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row=1):
    for cell in ws[row]:
        cell.fill = HEADER_FILL
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


def wrap(ws, start_row=2):
    for row in ws.iter_rows(min_row=start_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def main():
    wb = Workbook()

    # ---------- Summary ----------
    ws = wb.active
    ws.title = "Summary"
    summary = [
        ("Item", "Value", "Notes"),
        ("Task", "Differentiate 85-88% similarity service pages", "Roadmap Item #19 (P3)"),
        ("Pages flagged", 3, "/low-flow-toilets-utah/, /reverse-osmosis-systems-utah/, /garbage-disposal-utah/"),
        ("Audit's similarity claim", "85-88%", "From near-duplicates report"),
        ("Live verification result", "Closer to 99% template-identical", "9,800-word HTML, ~37 words page-specific per URL"),
        ("Total impressions across all 3 (90d)", 159, ""),
        ("Total clicks across all 3 (90d)", 0, ""),
        ("CTR across all 3", "0.00%", ""),
        ("Identity crisis", "/low-flow-toilets-utah/", "URL says low-flow toilets but H1 says 'Flushometer Repair' - serves 2 different services badly"),
        ("Recommended action - low-flow page", "SPLIT into 2 pages", "Repurpose URL for low-flow toilets, create new /flushometer-repair-utah/"),
        ("Recommended action - RO page", "REWRITE", "1,500 words, 152 imps justify deeper content"),
        ("Recommended action - garbage disposal", "REWRITE", "1,200 words, currently invisible"),
        ("Total new content needed", "4,000-5,000 words", "Across 4 pages (3 rewrites + 1 new)"),
    ]
    for r in summary:
        ws.append(r)
    style_header(ws)
    autosize(ws, max_w=80)

    # ---------- Page Diagnoses ----------
    ws = wb.create_sheet("Page Diagnoses")
    ws.append(
        [
            "URL",
            "Live Status",
            "Title Tag",
            "H1",
            "Title-URL Match?",
            "Page-Specific WC",
            "Imps (90d)",
            "Clicks (90d)",
            "Top Query",
            "Diagnosis",
        ]
    )
    diagnoses = [
        (
            "https://www.beehiveplumbing.com/low-flow-toilets-utah/",
            "200 OK",
            "Flushometer Repair Low-Flow Toilets - Salt Lake City, Utah | Beehive Plumbing",
            "Flushometer Repair in Utah",
            "NO - URL says low-flow toilets, H1 says flushometer",
            37,
            0,
            0,
            "(no GSC data in 90d)",
            "Identity crisis - serves 2 unrelated services. SPLIT into two pages.",
        ),
        (
            "https://www.beehiveplumbing.com/reverse-osmosis-systems-utah/",
            "200 OK",
            "Reverse Osmosis Systems in Salt Lake City, Utah | Beehive Plumbing",
            "Reverse Osmosis Systems in Utah",
            "Yes",
            38,
            152,
            0,
            "reverse osmosis installation near me (76 imp pos 22)",
            "On-topic but content-thin. 152 imps already - rewrite captures real demand.",
        ),
        (
            "https://www.beehiveplumbing.com/garbage-disposal-utah/",
            "200 OK",
            "Garbage Disposal in Salt Lake City, Utah | Beehive Plumbing SLC",
            "Garbage Disposal in Utah",
            "Yes",
            37,
            7,
            0,
            "garbage disposals salt lake city ut (3 imp pos 51)",
            "On-topic but content-thin. Essentially invisible due to 37-word content.",
        ),
        (
            "https://www.beehiveplumbing.com/flushometer-repair-utah/ (PROPOSED)",
            "Does not exist yet",
            "(to be created)",
            "(to be created)",
            "—",
            "—",
            "—",
            "—",
            "—",
            "NEW page - takes flushometer content from /low-flow-toilets-utah/ and gives it a coherent home",
        ),
    ]
    for row in diagnoses:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Differentiation Framework ----------
    ws = wb.create_sheet("Differentiation Framework")
    ws.append(["#", "Dimension", "Why it matters", "Required for each page"])
    framework = [
        (
            1,
            "Topic coherence",
            "URL + title + H1 + content all answer the same query. Mismatch confuses Google and users.",
            "Verify the URL slug matches what the page actually serves. Fix /low-flow-toilets-utah/ first.",
        ),
        (
            2,
            "Service-specific content depth",
            "37 words of page-specific content cannot compete for any commercial query. Minimum threshold: 1,200-1,500 words of unique service content per page.",
            "Each page hits its own word count target with sections covering: what the service is, common failures (where applicable), brands, cost, process, FAQ.",
        ),
        (
            3,
            "Entity density",
            "Each service has 8-12 entity references Google associates with it (brands, technical terms, certifications). Without them, pages don't signal what they're about.",
            "Each page lists its required entities in its brief and hits all of them in the rewrite.",
        ),
        (
            4,
            "Internal linking",
            "Currently the 3 pages are silos. Linking to functional siblings + related blog posts builds topical clustering.",
            "Each page links to 2-3 sibling service pages + 1-2 supporting blog posts.",
        ),
        (
            5,
            "Schema markup",
            "None of the pages currently has Service schema. Schema is the cleanest signal to Google about what a page is.",
            "Service schema with priceRange + areaServed on each page. FAQPage schema if FAQ section exists.",
        ),
    ]
    for row in framework:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Per-Page Briefs ----------
    ws = wb.create_sheet("Per-Page Briefs")
    ws.append(
        [
            "Page",
            "Action",
            "Target Query Family",
            "Title Tag",
            "H1",
            "Word Count Target",
            "Required Sections",
            "Required Entities",
            "Internal Links",
        ]
    )
    briefs = [
        (
            "https://www.beehiveplumbing.com/low-flow-toilets-utah/",
            "REWRITE - keep URL, change content to residential low-flow toilets only",
            "low flow toilet installation, water efficient toilet, dual flush toilet, EPA WaterSense",
            "Low-Flow Toilet Installation in Utah: Save Water + Money | Beehive Plumbing",
            "Low-Flow Toilet Installation in Salt Lake City, Utah",
            1200,
            "Why install low-flow / EPA WaterSense / GPF rating / Dual-flush vs single-flush / Top brands / Cost / Utah water rebates / FAQ",
            "EPA WaterSense, GPF, 1.28 GPF, 1.6 GPF, Kohler, Toto, American Standard, dual-flush, Utah water rebate programs",
            "/plumbing-repairs-utah/, blog post on water-saving plumbing tips",
        ),
        (
            "https://www.beehiveplumbing.com/flushometer-repair-utah/ (NEW)",
            "CREATE - new URL, takes flushometer content from existing /low-flow-toilets-utah/",
            "flushometer repair, sloan flushometer, commercial toilet flush valve, urinal flush valve",
            "Commercial Flushometer Repair & Service in Utah | Beehive Plumbing",
            "Commercial Flushometer Repair in Salt Lake City, Utah",
            1200,
            "What flushometers are / Common failures / Diaphragm vs piston / Sloan + Zurn brands / Manual vs sensor / Commercial pricing / Same-day commercial response / FAQ",
            "Sloan Royal, Sloan Regal, Zurn, diaphragm assembly, piston, vacuum breaker, manual flush valve, sensor flush valve",
            "/commercial-plumber-utah/, blog posts on commercial restroom",
        ),
        (
            "https://www.beehiveplumbing.com/reverse-osmosis-systems-utah/",
            "REWRITE - keep URL, deepen content from 38 words to 1,500+",
            "reverse osmosis installation, reverse osmosis system Utah, RO water filter, whole house reverse osmosis",
            "Reverse Osmosis System Installation & Service in Utah | Beehive Plumbing",
            "Reverse Osmosis Systems in Salt Lake City, Utah",
            1500,
            "What RO does / Why Utah needs RO / Whole-house vs under-sink / Installation / Maintenance / Cost / Brands / RO vs water softener / FAQ",
            "TDS, Aquasana, APEC, Pentair, semipermeable membrane, sediment filter, carbon filter, mineralization, Salt Lake City water hardness",
            "/water-softeners-utah/, /water-treatment/ parent, blog posts on Utah hard water",
        ),
        (
            "https://www.beehiveplumbing.com/garbage-disposal-utah/",
            "REWRITE - keep URL, deepen content from 37 words to 1,200+",
            "garbage disposal installation, garbage disposal repair, garbage disposal replacement, insinkerator service",
            "Garbage Disposal Installation & Repair in Utah | Beehive Plumbing",
            "Garbage Disposal Installation & Repair in Salt Lake City, Utah",
            1200,
            "Common failures / Repair vs replace / Continuous vs batch feed / HP sizing / Brands / Septic-safe options / Cost / FAQ",
            "InSinkErator, Waste King, Kohler, GE Disposall, 1/3 HP, 1/2 HP, 3/4 HP, continuous feed, batch feed, dishwasher connection, septic-safe",
            "/drain-cleaning-utah/, /plumbing-repairs-utah/, blog post on grease + drain care",
        ),
    ]
    for row in briefs:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    # ---------- Implementation Order ----------
    ws = wb.create_sheet("Implementation Order")
    ws.append(["Phase", "Week", "Action", "Pages", "Effort Estimate"])
    impl = [
        (
            "Phase 0",
            "Week 1",
            "Confirm: split low-flow page or keep combined? Confirm Beehive installs RO + which brands. Confirm Beehive services flushometers (commercial). Verify backlinks for each URL before rewrite.",
            "All",
            "4-6 hours of stakeholder + research",
        ),
        (
            "Phase 1",
            "Weeks 2-3",
            "Rewrite /reverse-osmosis-systems-utah/ - 1,500 words with brand research and Utah water context",
            "1 page",
            "8-12 hours",
        ),
        (
            "Phase 2",
            "Week 4",
            "Rewrite /garbage-disposal-utah/ - 1,200 words with HP sizing and brand servicing",
            "1 page",
            "6-8 hours",
        ),
        (
            "Phase 3",
            "Weeks 5-6",
            "Low-flow toilet split: rewrite /low-flow-toilets-utah/ as residential low-flow service + create /flushometer-repair-utah/ new commercial page",
            "2 pages",
            "12-16 hours",
        ),
        (
            "Phase 4",
            "Week 7",
            "Internal linking pass - connect each rewritten page to 2-3 functional siblings + 1-2 blog posts",
            "All 4",
            "1-2 hours",
        ),
        (
            "Phase 5",
            "Week 7",
            "Schema deployment - Service + FAQPage schema on all 4 pages",
            "All 4",
            "2-3 hours",
        ),
        (
            "Phase 6",
            "Weeks 8-12",
            "Monitor: position movement on target query families, impression growth on /garbage-disposal-utah/ (currently 7 imp - target 50+), CTR on /reverse-osmosis-systems-utah/ (currently 0% on 152 imp), baseline impressions on new /flushometer-repair-utah/",
            "All 4",
            "30-day report",
        ),
    ]
    for row in impl:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=70)
    wrap(ws)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
