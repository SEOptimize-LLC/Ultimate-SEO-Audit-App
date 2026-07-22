"""Build the Comfort Authority Signals Surfacing Excel deliverable.

Output: Clients/Comfort/Full SEO Audit/comfort_authority_signals_surfacing.xlsx
Tabs:
  1. Client Summary       - brief shareable narrative
  2. Summary              - internal KPIs
  3. The Four Surfaces    - body / alt / schema / FAQ explanation
  4. Tier 1 - Hubs        - 4 hub pages (need both Trane + Napoleon)
  5. Tier 2 - HVAC pages  - 15 HVAC pages needing Trane body
  6. Tier 3 - Fireplace   - 2 pages needing Napoleon body
  7. Already Compliant    - 24 pages where body already mentions brand
  8. Copy Templates       - A/B/C body copy + FAQ blocks
  9. Schema Block         - LocalBusiness JSON-LD to append
  10. Implementation Order
"""
from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
DATA = Path("/tmp/comfort_authority_results.json")
OUTPUT = ROOT / "Clients" / "Comfort" / "Full SEO Audit" / "comfort_authority_signals_surfacing.xlsx"

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
DEFAULT_FONT = Font(name="Calibri", size=11, bold=False)
SECTION_FONT = Font(name="Calibri", size=11, bold=True, color="1F4E78")
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


def normalize_data_rows(ws, start_row=2, wrap_cols=None):
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

    # Bucket pages
    hubs = []  # Tier 1
    needs_trane = []  # Tier 2 - HVAC missing Trane
    needs_napoleon = []  # Tier 3 - fireplace missing Napoleon
    already = []  # already compliant

    for r in results:
        if r.get("status") != 200:
            continue
        cat = r["category"]
        has_trane = r.get("trane_specialist_in_body", False)
        has_napoleon = r.get("napoleon_in_body", False)
        if cat == "Hub":
            hubs.append(r)
        elif cat == "HVAC":
            if not has_trane:
                needs_trane.append(r)
            else:
                already.append(r)
        elif cat == "Fireplace":
            if not has_napoleon:
                needs_napoleon.append(r)
            else:
                already.append(r)

    # Sort each by impressions descending
    for lst in (hubs, needs_trane, needs_napoleon, already):
        lst.sort(key=lambda x: -(x.get("impressions") or 0))

    wb = Workbook()

    # ---------- Client Summary ----------
    ws = wb.active
    ws.title = "Client Summary"
    msg = [
        ("Authority Signals — Quick Summary", "", ""),
        ("", "", ""),
        ("Why this matters", "", ""),
        (
            "On-page issue",
            "Comfort Solutions is the largest Trane Comfort Specialist in the Rocky Mountain Region and among the nation's largest Napoleon fireplace suppliers. These are real competitive moats — but they're buried in badge images only. Search engines and AI search engines (AI Overview, Gemini, ChatGPT) cannot read badge images as authority signals.",
            "",
        ),
        (
            "Why it costs traffic",
            "Pages that don't carry the certification phrase in body text cannot rank for high-intent commercial queries like 'Trane Comfort Specialist near me' or 'Napoleon fireplace dealer Utah'. AI search engines can't cite the certifications in their answers either.",
            "",
        ),
        ("", "", ""),
        ("What we did", "", ""),
        (
            "Scoped to HVAC + fireplace clusters only",
            "45 service pages where Trane and Napoleon are directly relevant. Plumbing pages were excluded from scope.",
            "",
        ),
        (
            "Live-verified all 45 pages on May 6, 2026",
            "Captured current state of body mentions, alt text, and FAQ presence on every page.",
            "",
        ),
        (
            "Mapped the gap to four surfaces",
            "Body content, image alt text, structured data (LocalBusiness schema), and FAQ blocks. Each surface signals different things to Google and AI engines.",
            "",
        ),
        (
            "Drafted page-by-page action plan",
            "21 pages need a content addition. 24 already mention the certification and just need FAQ + schema audit.",
            "",
        ),
        ("", "", ""),
        ("Findings at a glance", "", ""),
        ("Total pages reviewed", 45, "All HVAC + fireplace + service hub pages"),
        ("Pages already mentioning Trane in body", 14, "Of 33 HVAC + hub pages — about 42%"),
        ("Pages already mentioning Napoleon in body", 10, "Of 16 fireplace + hub pages — about 63%"),
        ("Hub pages needing both certifications added", 4, "9,025 impressions at stake"),
        ("HVAC pages needing Trane body mention added", 15, "36,464 impressions at stake"),
        ("Fireplace pages needing Napoleon body added", 2, "1,586 impressions"),
        ("Total impressions on pages currently missing the signal", "47,075", ""),
        ("Highest-impression page missing the signal", "/services/hvac-systems/heating/", "8,202 impressions, 0 clicks"),
        ("", "", ""),
        ("Next steps", "", ""),
        (
            "Phase 1 — One-shot wins (Week 1)",
            "Update LocalBusiness schema with award + hasCredential arrays. Update existing badge alt text. ~2 hours dev work, applies sitewide.",
            "",
        ),
        (
            "Phase 2 — Hub pages (Week 1-2)",
            "Add strong-claim body block + FAQ to the 4 service hub pages. Highest-leverage edits.",
            "",
        ),
        (
            "Phase 3 — High-impression HVAC pages (Week 2)",
            "Add soft-supporting body block + FAQ to the 7 HVAC pages with 1,000+ impressions.",
            "",
        ),
        (
            "Phase 4 — Remaining pages (Week 3)",
            "Lower-impression HVAC + fireplace pages. Same template, lower priority.",
            "",
        ),
        (
            "Phase 5 — Audit already-compliant pages (Week 3)",
            "24 pages already mention the brand. Spot-check that the mention is meaningful and add FAQ + schema completeness.",
            "",
        ),
        (
            "Phase 6 — Monitor (Weeks 4-8)",
            "Track GSC impressions on 'Trane Comfort Specialist near me', 'Napoleon fireplace dealer Utah', and CTR delta on modified pages vs 90-day baseline.",
            "",
        ),
        ("", "", ""),
        (
            "How to read the rest of this workbook",
            "Tier 1 - Hubs: 4 hub pages with both certifications. Tier 2 - HVAC: 15 HVAC pages needing Trane body. Tier 3 - Fireplace: 2 pages needing Napoleon. Already Compliant: 24 pages just needing FAQ + schema audit. Copy Templates: A/B/C/D body and FAQ templates. Schema Block: LocalBusiness JSON-LD to append. Implementation Order: phase-by-phase plan.",
            "",
        ),
    ]
    for row in msg:
        ws.append(row)
    style_header(ws, row=1)
    ws.row_dimensions[1].height = 36
    autosize(ws, max_w=90)
    normalize_data_rows(ws, wrap_cols=[1, 2])
    # Make section headings bold
    section_rows = [3, 7, 14, 24]
    for row_idx in section_rows:
        cell = ws.cell(row=row_idx, column=1)
        cell.font = SECTION_FONT

    # ---------- Internal Summary ----------
    ws = wb.create_sheet("Summary")
    summary = [
        ("Item", "Value", "Notes"),
        ("Task", "Surface Trane Comfort Specialist + Napoleon dealer authority signals", "Roadmap Item #17 (P2)"),
        ("Scope", "HVAC + fireplace clusters only", "Plumbing excluded per task definition"),
        ("Pages reviewed", 45, "Live-verified May 6, 2026"),
        ("All return 200", "Yes", "0 broken URLs in scope"),
        ("Hub pages (Tier 1)", 4, "9,025 imps — need BOTH certifications"),
        ("HVAC pages needing Trane body (Tier 2)", 15, "36,464 imps"),
        ("Fireplace pages needing Napoleon body (Tier 3)", 2, "1,586 imps"),
        ("Already mention brand in body", 24, "FAQ + schema audit only"),
        ("Total impressions in cluster", 53790, "From content audit"),
        ("Total clicks in cluster (90 days)", 23, "0.04% CTR"),
        ("Pages where Trane is in alt only (not body)", 13, "The audit's exact flagged scenario"),
        ("Pages where Napoleon is in alt only", 0, "Napoleon isn't even in alt — body or nothing"),
    ]
    for row in summary:
        ws.append(row)
    style_header(ws)
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[2])

    # ---------- The Four Surfaces ----------
    ws = wb.create_sheet("The Four Surfaces")
    ws.append(["Surface", "What it is", "Why it matters", "Effort", "Per-page or sitewide"])
    surfaces = [
        (
            "1. Body content",
            "1-2 sentence 'Why Choose Us' or 'Our Certifications' block stating the certification in body text",
            "Strongest ranking signal. Body content is what Google's main crawler indexes and matches against query intent.",
            "Per-page",
            "Per-page (~30 min/page including FAQ)",
        ),
        (
            "2. Image alt text",
            "Rewrite badge alts to carry Comfort's relationship with the brand, not just the brand identity",
            "Currently 'Trane – heating and air conditioning brand logo' — doesn't even say 'Comfort Specialist'. Wasted real estate.",
            "Sitewide (1 fix)",
            "Sitewide if alts live in theme/media library",
        ),
        (
            "3. Structured data (LocalBusiness schema)",
            "Add award[] and hasCredential[] arrays to LocalBusiness JSON-LD",
            "Cleanest, most explicit signal. Feeds Google knowledge panel + AI Overview / Gemini citations.",
            "Sitewide (1 fix)",
            "Sitewide — one schema template edit",
        ),
        (
            "4. FAQ blocks",
            "1-3 question FAQ block per page with FAQPage schema",
            "AI search engines (ChatGPT, Gemini, Perplexity) heavily weight FAQ-formatted content in their citation pool. Highest-impact addition for AI search visibility.",
            "Per-page",
            "Per-page (~10 min/page using template)",
        ),
    ]
    for row in surfaces:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[1, 2, 3, 4])

    # ---------- Tier 1 - Hubs ----------
    ws = wb.create_sheet("Tier 1 - Hubs (Both)")
    ws.append([
        "URL", "Imps (90d)", "Clicks (90d)", "Action — Body Block Voice", "Action — Alt Text", "Action — FAQ", "Notes",
    ])
    voice_for_hub = {
        "/services/hvac-systems/": ("Strong claim (HVAC) + soft supporting (Napoleon)", "Add Trane Comfort Specialist alt + Napoleon Authorized Dealer alt", "Add HVAC FAQ block (Trane question)"),
        "/services/fireplace/": ("Strong claim (Napoleon) + soft supporting (HVAC)", "Add Napoleon Authorized Dealer alt + Trane Comfort Specialist alt", "Add fireplace FAQ block (Napoleon question)"),
        "/services/emergency-services/": ("Both certifications, equal weight", "Add both alts", "Add 2-question FAQ — both certs"),
        "/services/": ("Both certifications, equal weight", "Add both alts", "Add 2-question FAQ — both certs"),
    }
    for r in hubs:
        url = r["url"]
        path = url.replace("https://www.comfortsolutionsutah.com", "").rstrip("/") + "/"
        v = voice_for_hub.get(path, ("Both certifications", "Add both alts", "Add 2-question FAQ"))
        ws.append([
            url,
            r.get("impressions") or 0,
            r.get("clicks") or 0,
            v[0],
            v[1],
            v[2],
            "Most-linked pages in cluster — highest leverage",
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[3, 4, 5, 6])

    # ---------- Tier 2 - HVAC pages needing Trane ----------
    ws = wb.create_sheet("Tier 2 - HVAC needs Trane")
    ws.append([
        "URL", "Imps (90d)", "Clicks (90d)", "Trane in alt currently?", "Action — Body Block", "Action — Alt", "Action — FAQ",
    ])
    for r in needs_trane:
        url = r["url"]
        # Determine voice based on whether URL has a city
        u = url.lower()
        has_city = any(c in u for c in [
            "salt-lake-city", "park-city", "sandy", "ogden", "orem", "layton",
            "davis-county", "south-salt-lake", "draper", "bountiful", "murray",
        ])
        if has_city:
            voice = "Template C — Local-context variant (pair certification with city + showrooms)"
        else:
            voice = "Template B — Soft supporting mention (~25-30 words)"
        alt_action = "Update existing Trane alt to 'Comfort Solutions — Trane Comfort Specialist (Largest in the Rocky Mountain Region)'" if r.get("trane_in_alt") else "ADD Trane badge with full alt text — page currently has no badge"
        ws.append([
            url,
            r.get("impressions") or 0,
            r.get("clicks") or 0,
            "Yes" if r.get("trane_in_alt") else "No — no badge",
            voice,
            alt_action,
            "Add 1-question Trane FAQ block",
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[4, 5, 6])

    # ---------- Tier 3 - Fireplace pages needing Napoleon ----------
    ws = wb.create_sheet("Tier 3 - Fireplace Napoleon")
    ws.append([
        "URL", "Imps (90d)", "Clicks (90d)", "Action — Body Block", "Action — Alt", "Action — FAQ",
    ])
    for r in needs_napoleon:
        ws.append([
            r["url"],
            r.get("impressions") or 0,
            r.get("clicks") or 0,
            "Template B — Soft supporting Napoleon mention",
            "Add Napoleon Authorized Dealer alt to nearest fireplace image",
            "Add 1-question Napoleon FAQ block",
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[3, 4, 5])

    # ---------- Already Compliant ----------
    ws = wb.create_sheet("Already Compliant")
    ws.append([
        "URL", "Category", "Imps (90d)", "Has Trane in body?", "Has Napoleon in body?", "Action",
    ])
    for r in already:
        ws.append([
            r["url"],
            r["category"],
            r.get("impressions") or 0,
            "Yes" if r.get("trane_specialist_in_body") else "No",
            "Yes" if r.get("napoleon_in_body") else "No",
            "Audit only — verify mention is meaningful (not in global footer template) + add FAQ + schema",
        ])
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[5])

    # ---------- Copy Templates ----------
    ws = wb.create_sheet("Copy Templates")
    ws.append(["Template", "Use case", "Body copy"])
    templates = [
        (
            "A — Strong claim (HVAC)",
            "Use ONCE per HVAC cluster, on the highest-impression hub page (/services/hvac-systems/)",
            "Why Choose Comfort Solutions for Your HVAC Service\n\nComfort Solutions is the largest Trane Comfort Specialist in the Rocky Mountain Region — a designation Trane awards to dealers meeting their highest standards for installation quality, customer satisfaction, and ongoing technician training. Combined with our NATE-Certified technicians, BBB A+ accreditation, and Authorized Lennox Premier Dealer status, we bring manufacturer-level expertise to every furnace, AC, and heat pump installation across Utah's Wasatch Front.",
        ),
        (
            "A — Strong claim (Fireplace)",
            "Use ONCE per fireplace cluster, on the hub page (/services/fireplace/)",
            "Why Choose Comfort Solutions for Your Fireplace\n\nComfort Solutions is among the nation's largest Napoleon fireplace suppliers, with two showrooms in West Haven and Sandy where customers can see Napoleon's full gas, electric, wood-burning, and outdoor lineup in person before purchase. Our designation reflects 25+ years of fireplace installation expertise and one of the deepest Napoleon inventories on the Wasatch Front.",
        ),
        (
            "B — Soft supporting (HVAC)",
            "Every other HVAC service page in the cluster (~15 pages)",
            "As a Trane Comfort Specialist, Comfort Solutions has direct access to Trane's premium residential HVAC product line and the manufacturer training to install and service it correctly. This certification — combined with our NATE-Certified technicians — means your furnace repair is handled by a team factory-trained on the equipment.",
        ),
        (
            "B — Soft supporting (Fireplace)",
            "Every other fireplace page in the cluster",
            "Comfort Solutions is an authorized Napoleon fireplace dealer with two physical showrooms in West Haven and Sandy. Our installers are factory-trained on Napoleon's gas, electric, and outdoor fireplace lines, with full access to the brand's residential and commercial product range.",
        ),
        (
            "C — Local context (HVAC city pages)",
            "City-specific HVAC service pages (Park City, Sandy, Ogden, etc.)",
            "Comfort Solutions has served [City], Utah homeowners as a Trane Comfort Specialist since 2000. Our [City]-area technicians are NATE-Certified and operate from showrooms in West Haven and Sandy — which means parts, equipment, and dispatch happen locally, not from a distant warehouse.",
        ),
        (
            "C — Local context (Fireplace city pages)",
            "City-specific fireplace pages",
            "Comfort Solutions has served [City], Utah homeowners as an authorized Napoleon fireplace dealer with two physical showrooms in West Haven and Sandy. Our [City]-area installers are factory-trained on Napoleon's full lineup.",
        ),
        (
            "D — FAQ block (HVAC)",
            "Add to every HVAC page",
            "Q: Are you a certified Trane dealer?\nA: Yes. Comfort Solutions is the largest Trane Comfort Specialist in the Rocky Mountain Region, with full access to Trane's premium residential and commercial HVAC product line and the factory training to install it.\n\nQ: Are your technicians certified?\nA: Yes. All Comfort Solutions HVAC technicians are NATE-Certified, and our company holds Trane Comfort Specialist designation, Authorized Lennox Premier Dealer status, and BBB A+ accreditation.",
        ),
        (
            "D — FAQ block (Fireplace)",
            "Add to every fireplace page",
            "Q: Do you sell and install Napoleon fireplaces?\nA: Yes. Comfort Solutions is among the nation's largest Napoleon fireplace suppliers, with two showrooms in West Haven and Sandy where customers can see Napoleon gas, electric, and outdoor fireplaces in person before they buy.\n\nQ: What fireplace brands do you carry?\nA: Comfort Solutions is an authorized Napoleon dealer and one of the largest in the country. We carry Napoleon's full residential line — gas, electric, wood-burning, and outdoor — with both showroom and installation services across Utah's Wasatch Front.",
        ),
    ]
    for row in templates:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=90)
    normalize_data_rows(ws, wrap_cols=[1, 2])

    # ---------- Schema Block ----------
    ws = wb.create_sheet("Schema Block")
    schema_json = '''{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Comfort Solutions",
  "url": "https://www.comfortsolutionsutah.com/",
  "award": [
    "Largest Trane Comfort Specialist in the Rocky Mountain Region",
    "Among the nation's largest Napoleon fireplace suppliers",
    "BBB A+ Accredited",
    "NATE-Certified"
  ],
  "hasCredential": [
    {
      "@type": "EducationalOccupationalCredential",
      "name": "Trane Comfort Specialist"
    },
    {
      "@type": "EducationalOccupationalCredential",
      "name": "Authorized Lennox Premier Dealer"
    },
    {
      "@type": "EducationalOccupationalCredential",
      "name": "Authorized Napoleon Fireplace Dealer"
    },
    {
      "@type": "EducationalOccupationalCredential",
      "name": "NATE-Certified Technicians"
    }
  ]
}'''
    ws.append(["Schema block to add to LocalBusiness JSON-LD"])
    ws.append([""])
    ws.append(["Where to add it"])
    ws.append([
        "Site footer schema, theme schema template, or whatever plugin generates LocalBusiness JSON-LD on the site (Yoast/Rank Math/Schema Pro/etc.). One file edit, applies to every page automatically. Merge the award[] and hasCredential[] arrays into the existing LocalBusiness block — don't replace the whole block.",
    ])
    ws.append([""])
    ws.append(["JSON-LD"])
    ws.append([schema_json])
    style_header(ws, row=1)
    autosize(ws, max_w=120)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.font = DEFAULT_FONT
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    # ---------- Implementation Order ----------
    ws = wb.create_sheet("Implementation Order")
    ws.append(["Phase", "Week", "Action", "Pages", "Effort"])
    impl = [
        ("Phase 1", "Week 1", "Update LocalBusiness schema with award[] + hasCredential[]. Update existing badge alt text to carry Comfort's relationship.", "Sitewide (1 schema edit + alt edits in theme/media)", "~2 hours"),
        ("Phase 2", "Week 1-2", "Add strong-claim body block + FAQ to 4 hub pages. Order: emergency-services > fireplace > hvac-systems > services.", "4 hub pages", "~4 hours"),
        ("Phase 3", "Week 2", "Add soft-supporting body block + FAQ to high-impression HVAC pages (1,000+ imps).", "7 HVAC pages", "~6 hours"),
        ("Phase 4", "Week 3", "Add body block + FAQ to remaining HVAC + fireplace pages.", "8 HVAC + 2 fireplace pages", "~4 hours"),
        ("Phase 5", "Week 3", "Audit Tier 4 (already-compliant) pages — verify mention is meaningful, add FAQ + schema completeness.", "24 pages", "~2 hours"),
        ("Phase 6", "Weeks 4-8", "Monitor: GSC impressions on 'Trane Comfort Specialist near me', 'Napoleon fireplace dealer Utah', CTR delta on top 21 modified pages, AI Overview citations.", "All 45", "30-day report"),
    ]
    for row in impl:
        ws.append(row)
    style_header(ws)
    ws.freeze_panes = "A2"
    autosize(ws, max_w=80)
    normalize_data_rows(ws, wrap_cols=[2])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Wrote {OUTPUT}")
    print(f"  Hubs: {len(hubs)}")
    print(f"  HVAC needs Trane: {len(needs_trane)}")
    print(f"  Fireplace needs Napoleon: {len(needs_napoleon)}")
    print(f"  Already compliant: {len(already)}")
    print(f"  Total: {len(hubs)+len(needs_trane)+len(needs_napoleon)+len(already)}")


if __name__ == "__main__":
    main()
