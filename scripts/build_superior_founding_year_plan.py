"""Superior Water & Air — Founding-year inconsistency action plan.

Audit finding (per superior_technical_onpage_audit.md, P2 priority #7
+ roadmap row #11): "Over 30 Years" / "past several years" — inconsistent
tenure claims across the site, no canonical founding year published.

Client confirmed (2026-04-27): founded January 1956 — 70 years of operation.

Live verification (2026-04-27) found three confirmed offender pages with
five distinct conflicting tenure claims. The /hvac/furnace-installation/
page alone has THREE conflicting claims on the same page ("Since 1956",
"68 Years", "over 65 years"). Site is currently rate-limiting bulk
requests, so the pattern strongly suggests a templated "Why Choose Us"
copy block propagates across other HVAC/water/plumbing service pages —
the dev team should sweep all service-detail pages during implementation.

Outputs:
  Clients/Superior/Full SEO Audit/superior_founding_year_plan.xlsx
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = (
    PROJECT_ROOT
    / "Clients"
    / "Superior"
    / "Full SEO Audit"
    / "superior_founding_year_plan.xlsx"
)

CANONICAL_FOUNDING_YEAR = 1956
CANONICAL_TENURE_YEARS = 70  # As of 2026
CANONICAL_CLAIM_LONG = (
    "Since 1956, Superior Water & Air has served Utah and Idaho homeowners "
    "with HVAC, plumbing, and water treatment services."
)
CANONICAL_CLAIM_SHORT = "Serving Utah & Idaho since 1956 — 70 years of trusted service"
CANONICAL_BADGE = "70 Years of Trusted Experience"


# ---------------------------------------------------------------------------
# Sheet 1 — Per-URL action plan (live-verified offenders)
# ---------------------------------------------------------------------------

VERIFIED_ROWS: list[dict] = [
    {
        "priority": 1,
        "url": "https://superiorwaterandair.com/",
        "page_type": "Homepage",
        "section": "About Us section, under heading 'Your Trusted Home Services Company in Utah'",
        "current_claim": "Proudly serving Utah for the past several years",
        "issue": "VAGUE — 'past several years' contradicts 70-year reality; weak trust signal",
        "proposed_replacement": (
            "Proudly serving Utah and Idaho since 1956 — over 70 years of trusted "
            "HVAC, plumbing, and water treatment service for local homeowners."
        ),
        "verified_status": "CONFIRMED LIVE (2026-04-27)",
    },
    {
        "priority": 2,
        "url": "https://superiorwaterandair.com/hvac/furnace-installation/",
        "page_type": "HVAC Service Page",
        "section": "Multiple sections (hero/intro + Why Choose Us + body)",
        "current_claim": (
            "(1) 'Since 1956, Superior Water & Air has been a reliable company...' "
            "(2) '68 Years of Trusted Experience' "
            "(3) 'over 65 years of trusted expertise'"
        ),
        "issue": (
            "THREE CONTRADICTING CLAIMS ON ONE PAGE — '1956' is correct (=70 years), "
            "'68 years' is stale, '65 years' is even more stale. Replace ALL with "
            "consistent canonical claim."
        ),
        "proposed_replacement": (
            "Replace ALL three with canonical claim: 'Since 1956 — 70 Years of Trusted "
            "Experience' as the badge/heading, and 'Since 1956, Superior Water & Air has "
            "served Utah and Idaho homeowners with HVAC, plumbing, and water treatment "
            "services' as the body copy."
        ),
        "verified_status": "CONFIRMED LIVE (2026-04-27)",
    },
    {
        "priority": 3,
        "url": "https://superiorwaterandair.com/hvac/furnace-repair/",
        "page_type": "HVAC Service Page",
        "section": "Why Choose Us section + body + footer CTA",
        "current_claim": (
            "(1) '60+ Years of Proven Excellence — We opened decades ago. Three "
            "generations of Utah families have trusted us.' "
            "(2) 'We've served the Salt Lake City area for decades.' (×2 instances — body + footer)"
        ),
        "issue": (
            "STALE — '60+ years' is a legacy claim; '70 years' is correct. 'Three generations' "
            "claim is preserved but tenure number must be updated. Vague 'decades' phrasing "
            "should be replaced with specific number."
        ),
        "proposed_replacement": (
            "(1) '70+ Years of Proven Excellence — We opened in 1956. Three generations of "
            "Utah families have trusted us.' "
            "(2) 'We've served the Salt Lake City area since 1956 — over 70 years.' "
            "(Apply to BOTH body and footer instances.)"
        ),
        "verified_status": "CONFIRMED LIVE (2026-04-27)",
    },
]


# ---------------------------------------------------------------------------
# Sheet 2 — Pages to sweep (dev team must verify during implementation)
# ---------------------------------------------------------------------------

SWEEP_PAGES: list[dict] = [
    # HVAC sub-services that returned NONE FOUND but share template family
    # with /furnace-installation/ and /furnace-repair/ — re-verify during edit.
    {
        "url": "https://superiorwaterandair.com/hvac/",
        "page_type": "HVAC Hub",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    {
        "url": "https://superiorwaterandair.com/hvac/furnace-maintenance/",
        "page_type": "HVAC Service",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    {
        "url": "https://superiorwaterandair.com/hvac/air-conditioner-installation/",
        "page_type": "HVAC Service",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    {
        "url": "https://superiorwaterandair.com/hvac/air-conditioner-repair/",
        "page_type": "HVAC Service",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    {
        "url": "https://superiorwaterandair.com/hvac/air-conditioner-maintenance/",
        "page_type": "HVAC Service",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    {
        "url": "https://superiorwaterandair.com/hvac/ductless-ac/",
        "page_type": "HVAC Service",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    {
        "url": "https://superiorwaterandair.com/hvac/air-purification/",
        "page_type": "HVAC Service",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    {
        "url": "https://superiorwaterandair.com/hvac/home-generators/",
        "page_type": "HVAC Service",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    # Water + plumbing pages — could not verify during audit (rate-limited).
    # Strongly likely to share the same template family. MUST sweep.
    {
        "url": "https://superiorwaterandair.com/water/",
        "page_type": "Water Hub",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim found. Confirm during edit pass.",
    },
    {
        "url": "https://superiorwaterandair.com/water/water-heaters/",
        "page_type": "Water Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": (
            "Could not live-verify. HVAC service pages share a templated 'Why "
            "Choose Us' tenure block; water pages likely do too. Sweep during edit."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/water/water-heaters/water-heater-installation/",
        "page_type": "Water Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/water/water-heaters/water-heater-repairs/",
        "page_type": "Water Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/water/water-heaters/tankless-water-heater/",
        "page_type": "Water Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/water/water-treatment/",
        "page_type": "Water Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/water/office-drinking-water/",
        "page_type": "Water Service",
        "verified": "NOT VERIFIED",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/plumbing-services/",
        "page_type": "Plumbing Hub",
        "verified": "Verified clean (2026-04-27)",
        "note": (
            "No tenure claim found in latest fetch. Note: April 8 semantic audit had "
            "flagged 'Over 30 Years' on this page — may have been edited since. "
            "Confirm during edit pass."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/plumbing-services/service-and-repair/",
        "page_type": "Plumbing Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/plumbing-services/drain-cleaning/",
        "page_type": "Plumbing Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/plumbing-services/sewer-and-drain/",
        "page_type": "Plumbing Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/plumbing-services/bathroom-plumbing/",
        "page_type": "Plumbing Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/plumbing-services/kitchen-plumbing/",
        "page_type": "Plumbing Service",
        "verified": "NOT VERIFIED — site rate-limit",
        "note": "Sweep during edit. Apply canonical claim if tenure block exists.",
    },
    {
        "url": "https://superiorwaterandair.com/about/",
        "page_type": "About",
        "verified": "Verified clean (2026-04-27)",
        "note": (
            "No tenure claim — and that's the underlying problem. Add the canonical "
            "claim here as the primary source of truth. Recommended: add 'Founded "
            "1956 in [Utah city]' as a clear factual line under the H1."
        ),
    },
    {
        "url": "https://superiorwaterandair.com/contact/",
        "page_type": "Contact",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim — leave as-is unless adding canonical badge to footer.",
    },
    {
        "url": "https://superiorwaterandair.com/reviews/",
        "page_type": "Reviews Hub",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim — leave as-is.",
    },
    {
        "url": "https://superiorwaterandair.com/service-areas/",
        "page_type": "Service Areas Hub",
        "verified": "Verified clean (2026-04-27)",
        "note": "No tenure claim — leave as-is.",
    },
    {
        "url": "https://superiorwaterandair.com/service-areas/<all city pages>",
        "page_type": "Service Area (City)",
        "verified": "PARTIAL — 4 sampled, all clean (Salt Lake City, Sandy, Draper, St. George)",
        "note": (
            "City-level service-area pages sampled and clean. Spot-check during edit. "
            "If they share a templated tenure block, the badge should be canonical."
        ),
    },
]


# ---------------------------------------------------------------------------
# Sheet 3 — Canonical claim & implementation guidance
# ---------------------------------------------------------------------------

GUIDANCE_ROWS: list[tuple[str, str]] = [
    ("Superior Water & Air — Founding-Year Inconsistency Implementation Guidance", ""),
    ("", ""),
    ("Source audit", "superior_technical_onpage_audit.md (April 8, 2026), Section 15 P2 #7 + roadmap row #11"),
    ("Client confirmation", "Founded January 1956 — 70 years of operation as of 2026 (confirmed by Roger Marquez, 2026-04-27)"),
    ("Verification method", "Live HTML fetch and parse on candidate pages (homepage, about, service hubs, top sub-services, sampled city pages) on 2026-04-27"),
    ("", ""),
    ("", ""),
    ("THE CORE PROBLEM", ""),
    ("", ""),
    ("Issue", "No canonical founding year published anywhere on the site. Three different stale tenure claims appear across service pages: 'Since 1956' (correct), '68 Years', '65 years', '60+ Years', 'past several years', 'for decades'. /hvac/furnace-installation/ alone contains three contradicting claims on the same page."),
    ("Why this matters", "Inconsistent founding-year claims across pages weaken E-E-A-T signals (one of the strongest AI-citation signals per the 2026 GEO research) and undermine the trust value of a 70-year tenure. Search engines and LLMs cross-reference tenure claims across a domain — contradictions reduce confidence in the entity. A 70-year track record is a genuine moat in a market dominated by 5-15 year competitors; underclaiming it is leaving authority on the table."),
    ("", ""),
    ("", ""),
    ("CANONICAL CLAIM (USE EVERYWHERE)", ""),
    ("", ""),
    ("Founding year", f"{CANONICAL_FOUNDING_YEAR}"),
    ("Years of service (as of 2026)", f"{CANONICAL_TENURE_YEARS}"),
    ("Long-form (body copy)", CANONICAL_CLAIM_LONG),
    ("Short-form (subheadings, taglines)", CANONICAL_CLAIM_SHORT),
    ("Badge / Why Choose Us heading", CANONICAL_BADGE),
    ("", ""),
    ("Schema.org recommendation", "Add 'foundingDate': '1956' to the Organization schema in the homepage JSON-LD. This gives Google and AI search a structured, machine-readable source of truth that supersedes the inconsistent body-copy claims while edits are propagating."),
    ("", ""),
    ("", ""),
    ("BANNED PHRASES — REPLACE EVERYWHERE", ""),
    ("", ""),
    ("'past several years'", "Vague and contradicts 70-year reality. NEVER use."),
    ("'Over 30 Years' / 'Over 40 Years' / 'Over 50 Years' / '60+ Years'", "Stale legacy claims. Replace with '70+ Years' or 'Since 1956'."),
    ("'68 Years of Trusted Experience'", "Stale by 2 years. Replace with '70 Years of Trusted Experience' (or '70+ Years' for evergreen copy)."),
    ("'over 65 years of trusted expertise'", "Stale by 5+ years. Replace with 'over 70 years' (or 'since 1956')."),
    ("'for decades' / 'for years'", "Vague. Replace with specific number when possible: 'since 1956' or 'over 70 years'."),
    ("'we opened decades ago'", "Vague. Replace with 'we opened in 1956'."),
    ("", ""),
    ("Evergreen vs. specific", "Prefer 'Since 1956' (never goes stale) over '70 Years' (stale every January). If using a year-count badge, use '70+' rather than '70' so the claim doesn't need annual updates."),
    ("", ""),
    ("", ""),
    ("RECOMMENDED IMPLEMENTATION ORDER", ""),
    ("", ""),
    ("Step 1 — Establish source of truth", "Add the canonical 1956 founding-year claim to (a) the About page (primary source), (b) the homepage hero or intro section, and (c) Organization schema JSON-LD (foundingDate: '1956')."),
    ("Step 2 — Fix confirmed offenders", "Update the 3 verified offender pages (homepage, /hvac/furnace-installation/, /hvac/furnace-repair/) using the per-URL action plan in Sheet 1."),
    ("Step 3 — Sweep templated pages", "If the 'Why Choose Us' / tenure block is template-driven, fixing the WordPress/builder template once will propagate the canonical claim to all child pages. Identify whether this is a global template, a section template, or page-by-page copy. If global, fix once. If page-by-page, sweep all pages in Sheet 2."),
    ("Step 4 — Verify post-edit", "Re-crawl the site after edits and confirm zero stale claims remain. The audit will be complete when every page either has the canonical claim or no tenure claim at all."),
    ("", ""),
    ("", ""),
    ("PAGES TO ADD CANONICAL CLAIM TO (HIGH-VALUE)", ""),
    ("", ""),
    ("/about/", "Currently has 'Since our founding' but no year. Add 'Founded in 1956' as a clear factual line. This is the entity's primary trust page."),
    ("/", "Homepage currently uses vague 'past several years'. Replace with canonical claim — high-impact location for both human and AI trust signals."),
    ("Footer (site-wide)", "Add 'Family-trusted since 1956' or 'Serving Utah & Idaho since 1956' to the site-wide footer. Single edit, propagates everywhere, never goes stale."),
    ("Organization schema (JSON-LD)", "Add 'foundingDate': '1956-01-01' to the Organization schema. Most reliable signal for Google/LLMs."),
]


# ---------------------------------------------------------------------------
# Workbook builder
# ---------------------------------------------------------------------------

THIN_BORDER = Border(
    left=Side(style="thin", color="D0D0D0"),
    right=Side(style="thin", color="D0D0D0"),
    top=Side(style="thin", color="D0D0D0"),
    bottom=Side(style="thin", color="D0D0D0"),
)


def build_workbook() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()

    _build_action_plan_sheet(wb)
    _build_sweep_sheet(wb)
    _build_guidance_sheet(wb)

    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    wb.save(OUTPUT_PATH)
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Size:  {OUTPUT_PATH.stat().st_size:,} bytes")


def _build_action_plan_sheet(wb: Workbook) -> None:
    ws = wb.create_sheet("Action Plan — Verified")

    title = (
        "Superior Water & Air — Founding-Year Inconsistency Action Plan "
        "(Verified Offenders)"
    )
    ws.merge_cells("A1:H1")
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 28

    headers = [
        "Priority",
        "URL",
        "Page Type",
        "Section",
        "Current Claim (Verbatim)",
        "Issue",
        "Proposed Replacement",
        "Verification",
    ]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = PatternFill("solid", fgColor="2E75B6")
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = THIN_BORDER
    ws.row_dimensions[2].height = 30

    for row_idx, row in enumerate(VERIFIED_ROWS, start=3):
        values = [
            row["priority"],
            row["url"],
            row["page_type"],
            row["section"],
            row["current_claim"],
            row["issue"],
            row["proposed_replacement"],
            row["verified_status"],
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = Font(size=10)
            cell.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )
            cell.border = THIN_BORDER
        ws.row_dimensions[row_idx].height = 110

    widths = {"A": 8, "B": 55, "C": 20, "D": 35, "E": 50, "F": 45, "G": 60, "H": 22}
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width

    ws.freeze_panes = "A3"


def _build_sweep_sheet(wb: Workbook) -> None:
    ws = wb.create_sheet("Pages to Sweep — Dev Team")

    title = (
        "Pages to Sweep During Implementation "
        "(Verify Tenure Block Exists, Apply Canonical Claim if Found)"
    )
    ws.merge_cells("A1:D1")
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 28

    headers = ["URL", "Page Type", "Verification Status", "Note"]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = PatternFill("solid", fgColor="2E75B6")
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = THIN_BORDER
    ws.row_dimensions[2].height = 30

    for row_idx, row in enumerate(SWEEP_PAGES, start=3):
        values = [
            row["url"],
            row["page_type"],
            row["verified"],
            row["note"],
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = Font(size=10)
            cell.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )
            cell.border = THIN_BORDER
            if col_idx == 3 and "NOT VERIFIED" in str(value):
                cell.fill = PatternFill("solid", fgColor="FFE699")
            elif col_idx == 3 and "Verified clean" in str(value):
                cell.fill = PatternFill("solid", fgColor="C6E0B4")
        ws.row_dimensions[row_idx].height = 50

    widths = {"A": 70, "B": 22, "C": 32, "D": 75}
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width

    ws.freeze_panes = "A3"


def _build_guidance_sheet(wb: Workbook) -> None:
    ws = wb.create_sheet("Canonical Claim & Guidance")

    title = "Canonical Tenure Claim & Implementation Guidance"
    ws.merge_cells("A1:B1")
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="1F4E78")
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 28

    section_headers = {
        "THE CORE PROBLEM",
        "CANONICAL CLAIM (USE EVERYWHERE)",
        "BANNED PHRASES — REPLACE EVERYWHERE",
        "RECOMMENDED IMPLEMENTATION ORDER",
        "PAGES TO ADD CANONICAL CLAIM TO (HIGH-VALUE)",
    }

    for row_idx, (label, value) in enumerate(GUIDANCE_ROWS, start=2):
        label_cell = ws.cell(row=row_idx, column=1, value=label)
        value_cell = ws.cell(row=row_idx, column=2, value=value)

        is_section = label in section_headers
        is_top_title = row_idx == 2

        if is_section:
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=2)
            label_cell.font = Font(bold=True, size=12, color="FFFFFF")
            label_cell.fill = PatternFill("solid", fgColor="305496")
            label_cell.alignment = Alignment(
                horizontal="left", vertical="center", wrap_text=True
            )
            ws.row_dimensions[row_idx].height = 24
        elif is_top_title:
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=2)
            label_cell.font = Font(bold=True, size=13)
            label_cell.alignment = Alignment(
                horizontal="left", vertical="center", wrap_text=True
            )
            ws.row_dimensions[row_idx].height = 24
        else:
            label_cell.font = Font(bold=True, size=10)
            value_cell.font = Font(size=10)
            label_cell.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )
            value_cell.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )
            if label or value:
                ws.row_dimensions[row_idx].height = 50

    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 95


def main() -> None:
    build_workbook()


if __name__ == "__main__":
    main()
