"""
Build the corrected Comfort Solutions authority-signals deliverable for the web dev.

Source of truth: fact-cheats/Comfort Solutions Utah - Fact Cheat.md (March/April 2026 updates).
- Trane removed (Comfort is a Lennox dealer now).
- NATE removed (use "certified technicians").
- "Rocky Mountain Region" removed (use "Utah" / "Wasatch Front").
- Lennox tier "Premier" removed (unverified).
- "Factory-trained" softened to "trained on the equipment".

Output: Clients/Comfort/Full SEO Audit/comfort_authority_signals_implementation_v2.xlsx
"""

from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

OUT = Path(
    "Clients/Comfort/Full SEO Audit/comfort_authority_signals_implementation_v2.xlsx"
)


# ---------------------------------------------------------------------------
# Per-URL implementation rows
# ---------------------------------------------------------------------------

# Hub pages with strong-claim Template A
A_HVAC_HUB = "https://www.comfortsolutionsutah.com/services/hvac-systems/"
A_FIREPLACE_HUB = "https://www.comfortsolutionsutah.com/services/fireplace/"

# Multi-cert hubs (BOTH soft mentions)
MULTICERT_HUBS = [
    (
        "https://www.comfortsolutionsutah.com/services/emergency-services/",
        7314,
        0,
    ),
    ("https://www.comfortsolutionsutah.com/services/", 70, 0),
]

# B-HVAC only (HVAC service pages with Trane badge currently — needs Lennox swap)
B_HVAC_PAGES = [
    (
        "https://www.comfortsolutionsutah.com/services/hvac-systems/heating/",
        8202,
        0,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/emergency-services/air-conditioner-repair/",
        6347,
        0,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/hvac-systems/ac-repair-service/",
        5409,
        0,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/hvac-systems/furnace-repair-service/",
        4746,
        3,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/hvac-systems/air-conditioning/",
        3893,
        0,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/emergency-services/furnace-repair/",
        2884,
        0,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/hvac-systems/furnace-replacement-upgrade/",
        1077,
        0,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/hvac-systems/residential-ac/",
        781,
        0,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/hvac-systems/ac-upgrade-replacement/",
        325,
        1,
    ),
    (
        "https://www.comfortsolutionsutah.com/services/hvac-systems/residential-heating/",
        311,
        0,
    ),
]

# B-Fireplace only
B_FIREPLACE_PAGES = [
    ("https://www.comfortsolutionsutah.com/fireplaces/", 1477, 2),
    (
        "https://www.comfortsolutionsutah.com/fireplace-repair-salt-lake-city/",
        109,
        2,
    ),
]

# Template C — city pages, currently NO badge, need Lennox badge added
C_CITY_PAGES = [
    (
        "https://www.comfortsolutionsutah.com/emergency-furnace-repair-salt-lake-city/",
        1066,
        1,
        "Salt Lake City",
    ),
    (
        "https://www.comfortsolutionsutah.com/expert-ac-repair-davis-county/",
        529,
        1,
        "Davis County",
    ),
    (
        "https://www.comfortsolutionsutah.com/furnace-tune-up-salt-lake-city/",
        473,
        0,
        "Salt Lake City",
    ),
    (
        "https://www.comfortsolutionsutah.com/furnace-tune-up-services-salt-lake-city/",
        218,
        0,
        "Salt Lake City",
    ),
    (
        "https://www.comfortsolutionsutah.com/furnace-replacement-salt-lake-city/",
        203,
        0,
        "Salt Lake City",
    ),
]


# ---------------------------------------------------------------------------
# Copy templates (rewritten against fact cheat)
# ---------------------------------------------------------------------------

A_HVAC_BODY = (
    "Why Choose Comfort Solutions for Your HVAC Service\n\n"
    "Comfort Solutions has served Utah's Wasatch Front since 2000 as an authorized "
    "Lennox dealer, with two physical showrooms in West Haven and Sandy and a BBB A+ "
    "rating from local homeowners. Our certified technicians install and service "
    "Lennox furnaces, air conditioners, and heat pumps — along with Rinnai, Daikin, "
    "Goodman, and Carrier equipment — across every city we serve, from Ogden to Park "
    "City to Salt Lake City."
)

A_FIREPLACE_BODY = (
    "Why Choose Comfort Solutions for Your Fireplace\n\n"
    "Comfort Solutions is among the nation's largest Napoleon fireplace suppliers, "
    "with two showrooms in West Haven and Sandy — the largest fireplace showrooms in "
    "Utah — where customers can see Napoleon's full gas, electric, wood-burning, and "
    "outdoor lineup in person before purchase. Twenty-five-plus years of fireplace "
    "installation expertise across Utah's Wasatch Front, with one of the deepest "
    "Napoleon inventories in the state."
)

B_HVAC_BODY = (
    "As an authorized Lennox dealer, Comfort Solutions installs and services the full "
    "Lennox residential HVAC product line, with certified technicians trained on the "
    "equipment and BBB A+ accreditation backing every job."
)

B_FIREPLACE_BODY = (
    "Comfort Solutions is an authorized Napoleon fireplace dealer — among the largest "
    "in the country — with two physical showrooms in West Haven and Sandy and "
    "certified installers trained on Napoleon's full gas, electric, and outdoor "
    "fireplace lineup."
)


def c_hvac_body(city: str) -> str:
    return (
        f"Comfort Solutions has served {city}, Utah homeowners since 2000 as an "
        "authorized Lennox dealer. Our certified technicians dispatch from showrooms "
        "in West Haven and Sandy — which means parts, equipment, and service stay "
        "local rather than coming from a distant warehouse."
    )


D_HVAC_FAQ = (
    "Q: Are you an authorized Lennox dealer?\n"
    "A: Yes. Comfort Solutions is an authorized Lennox dealer, with full access to "
    "the Lennox residential HVAC product line and certified technicians trained to "
    "install and service the equipment correctly.\n\n"
    "Q: Are your technicians certified?\n"
    "A: Yes. All Comfort Solutions HVAC technicians are certified, and our company "
    "holds BBB A+ accreditation along with our authorized Lennox dealer designation."
)

D_FIREPLACE_FAQ = (
    "Q: Do you sell and install Napoleon fireplaces?\n"
    "A: Yes. Comfort Solutions is among the nation's largest Napoleon fireplace "
    "suppliers, with two showrooms in West Haven and Sandy where customers can see "
    "Napoleon gas, electric, and outdoor fireplaces in person before they buy.\n\n"
    "Q: What fireplace brands do you carry?\n"
    "A: Comfort Solutions is an authorized Napoleon dealer — one of the largest in "
    "the country. We carry Napoleon's full residential line — gas, electric, "
    "wood-burning, and outdoor — with showroom and installation services across "
    "Utah's Wasatch Front."
)

ALT_LENNOX = "Comfort Solutions — Authorized Lennox Dealer in Utah"
ALT_NAPOLEON = (
    "Comfort Solutions — Authorized Napoleon Fireplace Dealer "
    "(one of the nation's largest)"
)
ALT_BBB = "Comfort Solutions — BBB A+ Accredited Business in Utah"


SCHEMA_BLOCK = """{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Comfort Solutions",
  "url": "https://www.comfortsolutionsutah.com/",
  "award": [
    "Among the nation's largest Napoleon fireplace suppliers",
    "BBB A+ Accredited"
  ],
  "hasCredential": [
    {
      "@type": "EducationalOccupationalCredential",
      "name": "Authorized Lennox Dealer"
    },
    {
      "@type": "EducationalOccupationalCredential",
      "name": "Authorized Napoleon Fireplace Dealer"
    }
  ]
}"""


# ---------------------------------------------------------------------------
# Build implementation rows (one row per URL — single checklist for the dev)
# ---------------------------------------------------------------------------


def build_implementation_rows() -> list[dict]:
    rows: list[dict] = []

    # Template A — HVAC hub
    rows.append(
        {
            "Priority": 1,
            "URL": A_HVAC_HUB,
            "Page Type": "HVAC Hub",
            "Imps (90d)": 656,
            "Clicks (90d)": 0,
            "Body Block — Add (where: near bottom of body, before footer)": A_HVAC_BODY,
            "Badge Action": (
                "REPLACE existing Trane badge with Lennox badge image. "
                "Add BBB badge if not present."
            ),
            "New Alt Text": (
                f"Lennox badge alt: {ALT_LENNOX}\n"
                f"BBB badge alt: {ALT_BBB}"
            ),
            "FAQ Block — Add (where: bottom of body, above footer)": D_HVAC_FAQ,
            "Schema": "Sitewide change — see 'Schema Block' tab",
            "Notes": (
                "Highest-authority HVAC hub. Use the FULL strong-claim block. "
                "Trane references must be stripped from this page entirely."
            ),
        }
    )

    # Template A — Fireplace hub
    rows.append(
        {
            "Priority": 2,
            "URL": A_FIREPLACE_HUB,
            "Page Type": "Fireplace Hub",
            "Imps (90d)": 985,
            "Clicks (90d)": 5,
            "Body Block — Add (where: near bottom of body, before footer)": A_FIREPLACE_BODY,
            "Badge Action": (
                "Add Napoleon badge image if not present. "
                "Add BBB badge if not present."
            ),
            "New Alt Text": (
                f"Napoleon badge alt: {ALT_NAPOLEON}\n"
                f"BBB badge alt: {ALT_BBB}"
            ),
            "FAQ Block — Add (where: bottom of body, above footer)": D_FIREPLACE_FAQ,
            "Schema": "Sitewide change — see 'Schema Block' tab",
            "Notes": "Strong-claim Napoleon page. Lennox not surfaced here.",
        }
    )

    # Multi-cert hubs (B-HVAC + B-Fireplace + both FAQs)
    for url, imps, clicks in MULTICERT_HUBS:
        rows.append(
            {
                "Priority": 3,
                "URL": url,
                "Page Type": "Multi-cert Hub (HVAC + Fireplace)",
                "Imps (90d)": imps,
                "Clicks (90d)": clicks,
                "Body Block — Add (where: near bottom of body, before footer)": (
                    f"PARAGRAPH 1 (HVAC):\n{B_HVAC_BODY}\n\n"
                    f"PARAGRAPH 2 (Fireplace):\n{B_FIREPLACE_BODY}"
                ),
                "Badge Action": (
                    "REPLACE existing Trane badge with Lennox badge. "
                    "Add Napoleon badge. Add BBB badge if not present."
                ),
                "New Alt Text": (
                    f"Lennox badge alt: {ALT_LENNOX}\n"
                    f"Napoleon badge alt: {ALT_NAPOLEON}\n"
                    f"BBB badge alt: {ALT_BBB}"
                ),
                "FAQ Block — Add (where: bottom of body, above footer)": (
                    f"HVAC QUESTIONS:\n{D_HVAC_FAQ}\n\n"
                    f"FIREPLACE QUESTIONS:\n{D_FIREPLACE_FAQ}"
                ),
                "Schema": "Sitewide change — see 'Schema Block' tab",
                "Notes": (
                    "Page covers both HVAC and Fireplace — both certifications "
                    "carry equal weight. Use BOTH soft mentions, not the strong "
                    "claim."
                ),
            }
        )

    # Template B — HVAC only
    for url, imps, clicks in B_HVAC_PAGES:
        rows.append(
            {
                "Priority": 4,
                "URL": url,
                "Page Type": "HVAC Service Page",
                "Imps (90d)": imps,
                "Clicks (90d)": clicks,
                "Body Block — Add (where: near bottom of body, before footer)": B_HVAC_BODY,
                "Badge Action": (
                    "REPLACE existing Trane badge with Lennox badge. "
                    "Add BBB badge if not present."
                ),
                "New Alt Text": (
                    f"Lennox badge alt: {ALT_LENNOX}\n"
                    f"BBB badge alt: {ALT_BBB}"
                ),
                "FAQ Block — Add (where: bottom of body, above footer)": D_HVAC_FAQ,
                "Schema": "Sitewide change — see 'Schema Block' tab",
                "Notes": (
                    "Currently has Trane badge — must be swapped to Lennox. "
                    "Body block adds the dealer language Google can read."
                ),
            }
        )

    # Template B — Fireplace only
    for url, imps, clicks in B_FIREPLACE_PAGES:
        rows.append(
            {
                "Priority": 5,
                "URL": url,
                "Page Type": "Fireplace Service Page",
                "Imps (90d)": imps,
                "Clicks (90d)": clicks,
                "Body Block — Add (where: near bottom of body, before footer)": B_FIREPLACE_BODY,
                "Badge Action": (
                    "Add Napoleon badge to nearest fireplace image area. "
                    "Add BBB badge if not present."
                ),
                "New Alt Text": (
                    f"Napoleon badge alt: {ALT_NAPOLEON}\n"
                    f"BBB badge alt: {ALT_BBB}"
                ),
                "FAQ Block — Add (where: bottom of body, above footer)": D_FIREPLACE_FAQ,
                "Schema": "Sitewide change — see 'Schema Block' tab",
                "Notes": "Body already has fireplace content — add Napoleon dealer language.",
            }
        )

    # Template C — city pages (no current badge, need Lennox badge added)
    for url, imps, clicks, city in C_CITY_PAGES:
        rows.append(
            {
                "Priority": 6,
                "URL": url,
                "Page Type": f"HVAC City Page ({city})",
                "Imps (90d)": imps,
                "Clicks (90d)": clicks,
                "Body Block — Add (where: near bottom of body, before footer)": c_hvac_body(
                    city
                ),
                "Badge Action": (
                    "ADD Lennox badge — page currently has no certification badge. "
                    "Add BBB badge if not present."
                ),
                "New Alt Text": (
                    f"Lennox badge alt: {ALT_LENNOX}\n"
                    f"BBB badge alt: {ALT_BBB}"
                ),
                "FAQ Block — Add (where: bottom of body, above footer)": D_HVAC_FAQ,
                "Schema": "Sitewide change — see 'Schema Block' tab",
                "Notes": (
                    f"City-context variant. Substitute [City] = {city}. "
                    "Lennox badge ADDED (not replaced — page has none)."
                ),
            }
        )

    return rows


# ---------------------------------------------------------------------------
# Excel writer
# ---------------------------------------------------------------------------


def write_excel() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    impl_rows = build_implementation_rows()
    impl_df = pd.DataFrame(impl_rows)

    summary_rows = [
        {
            "Section": "Total URLs requiring implementation",
            "Value": len(impl_rows),
        },
        {
            "Section": "Template A (Strong Claim) — count",
            "Value": 2,
        },
        {
            "Section": "Template B (Soft Mention) — count",
            "Value": 14,
        },
        {
            "Section": "Template C (City Context) — count",
            "Value": 5,
        },
        {
            "Section": "Total impressions across these 21 pages (90d)",
            "Value": sum(r["Imps (90d)"] for r in impl_rows),
        },
        {
            "Section": "Pages where Trane badge must be REPLACED with Lennox",
            "Value": 13,
        },
        {
            "Section": "Pages where Lennox badge must be ADDED (no existing badge)",
            "Value": 5,
        },
        {
            "Section": "Pages where Napoleon badge must be ADDED",
            "Value": 4,
        },
        {
            "Section": "Sitewide schema change required",
            "Value": "Yes — see Schema Block tab",
        },
    ]
    summary_df = pd.DataFrame(summary_rows)

    rules_df = pd.DataFrame(
        [
            {
                "Rule": "NEVER use 'Trane' anywhere",
                "Why": "Comfort is no longer a Trane Comfort Specialist (changed March 2026). Comfort is now a Lennox dealer.",
            },
            {
                "Rule": "NEVER use 'NATE' or 'NATE-Certified'",
                "Why": "Per client direction (April 2026). Use 'certified technicians' instead.",
            },
            {
                "Rule": "NEVER use 'Rocky Mountain Region'",
                "Why": "Per client direction. Use 'Utah' or 'Utah's Wasatch Front'.",
            },
            {
                "Rule": "NEVER use 'Lennox Premier Dealer' or any specific tier",
                "Why": "Specific tier not yet confirmed by client. Use 'authorized Lennox dealer' only.",
            },
            {
                "Rule": "NEVER claim '100+ employees' or specific headcount",
                "Why": "Per client direction (March 2026). They do not currently have that team size.",
            },
            {
                "Rule": "NEVER use 'factory-trained' for technicians",
                "Why": "Not supported in fact cheat. Use 'certified technicians' or 'trained on the equipment' instead.",
            },
            {
                "Rule": "OK to use 'BBB A+ Accredited'",
                "Why": "Confirmed in fact cheat — 4.96 stars from 27 verified customers.",
            },
            {
                "Rule": "OK to use 'Among the nation's largest Napoleon fireplace suppliers'",
                "Why": "Confirmed in fact cheat.",
            },
            {
                "Rule": "OK to use 'two showrooms in West Haven and Sandy'",
                "Why": "Confirmed in fact cheat — 1723 S 1900 W, West Haven + 8451 Sandy Parkway, Sandy.",
            },
            {
                "Rule": "OK to use 'since 2000' or '25+ years'",
                "Why": "Founded July 1, 2000. Math: 2026 - 2000 = 26 years.",
            },
            {
                "Rule": "OK to use 'authorized Lennox dealer'",
                "Why": "Confirmed in fact cheat (March 2026).",
            },
        ]
    )

    schema_rows = [
        {
            "Item": "Where to add",
            "Value": (
                "Site footer schema, theme schema template, or whatever plugin "
                "generates LocalBusiness JSON-LD on the site (Yoast / Rank Math / "
                "Schema Pro / etc.). One file edit, applies to every page "
                "automatically. MERGE the award[] and hasCredential[] arrays into "
                "the existing LocalBusiness block — don't replace the whole block."
            ),
        },
        {
            "Item": "JSON-LD to merge",
            "Value": SCHEMA_BLOCK,
        },
        {
            "Item": "Critical — what to STRIP from existing schema",
            "Value": (
                "If the current LocalBusiness schema contains 'Trane Comfort "
                "Specialist', 'Largest Trane Comfort Specialist in the Rocky "
                "Mountain Region', 'NATE-Certified', or 'NATE-Certified "
                "Technicians' — REMOVE those lines. They are no longer accurate "
                "claims and must not appear in structured data."
            ),
        },
    ]
    schema_df = pd.DataFrame(schema_rows)

    templates_df = pd.DataFrame(
        [
            {
                "Template ID": "A-HVAC",
                "Use on (URL)": A_HVAC_HUB,
                "Body copy": A_HVAC_BODY,
            },
            {
                "Template ID": "A-Fireplace",
                "Use on (URL)": A_FIREPLACE_HUB,
                "Body copy": A_FIREPLACE_BODY,
            },
            {
                "Template ID": "B-HVAC",
                "Use on (URL)": "10 HVAC service pages + 2 multi-cert hubs (paragraph 1)",
                "Body copy": B_HVAC_BODY,
            },
            {
                "Template ID": "B-Fireplace",
                "Use on (URL)": "2 fireplace service pages + 2 multi-cert hubs (paragraph 2)",
                "Body copy": B_FIREPLACE_BODY,
            },
            {
                "Template ID": "C-HVAC (city, [City] = Salt Lake City)",
                "Use on (URL)": (
                    "/emergency-furnace-repair-salt-lake-city/, "
                    "/furnace-tune-up-salt-lake-city/, "
                    "/furnace-tune-up-services-salt-lake-city/, "
                    "/furnace-replacement-salt-lake-city/"
                ),
                "Body copy": c_hvac_body("Salt Lake City"),
            },
            {
                "Template ID": "C-HVAC (city, [City] = Davis County)",
                "Use on (URL)": "/expert-ac-repair-davis-county/",
                "Body copy": c_hvac_body("Davis County"),
            },
            {
                "Template ID": "D-HVAC (FAQ)",
                "Use on (URL)": "All HVAC + multi-cert hubs (17 pages)",
                "Body copy": D_HVAC_FAQ,
            },
            {
                "Template ID": "D-Fireplace (FAQ)",
                "Use on (URL)": "All Fireplace + multi-cert hubs (5 pages)",
                "Body copy": D_FIREPLACE_FAQ,
            },
        ]
    )

    phasing_df = pd.DataFrame(
        [
            {
                "Phase": "Phase 1 (~2 hours)",
                "Action": (
                    "Sitewide schema update + sitewide badge swap. Replace the "
                    "Trane badge image with the Lennox badge in the theme/media "
                    "library. Update LocalBusiness JSON-LD per Schema Block tab. "
                    "Strip every Trane and NATE reference from the existing schema."
                ),
            },
            {
                "Phase": "Phase 2 (~4 hours)",
                "Action": (
                    "Hub pages first. Add Template A body block to /services/"
                    "hvac-systems/ and /services/fireplace/. Add Template B "
                    "BOTH-paragraph blocks to /services/emergency-services/ "
                    "and /services/. Add D-HVAC + D-Fireplace FAQ where "
                    "applicable. Update badge alt text on these 4 pages."
                ),
            },
            {
                "Phase": "Phase 3 (~6 hours)",
                "Action": (
                    "Top-7 high-impression HVAC pages (1,000+ impressions each). "
                    "Add Template B-HVAC body block. Add D-HVAC FAQ. Confirm "
                    "Lennox badge replaced existing Trane badge."
                ),
            },
            {
                "Phase": "Phase 4 (~4 hours)",
                "Action": (
                    "Remaining HVAC pages, both fireplace pages, and 5 city "
                    "pages. Template B or C as listed. Add Lennox badge to the "
                    "5 city pages (currently no badge). Add Napoleon badge to "
                    "fireplace pages."
                ),
            },
            {
                "Phase": "Phase 5 (~2 hours)",
                "Action": (
                    "QA: spot-check that no Trane and no NATE language survives "
                    "anywhere on the site — body copy, alt text, schema, "
                    "footer trust blocks, FAQ. Use site search and view-source "
                    "to confirm."
                ),
            },
        ]
    )

    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        rules_df.to_excel(writer, sheet_name="Copy Rules (READ FIRST)", index=False)
        impl_df.to_excel(
            writer, sheet_name="Per-URL Implementation", index=False
        )
        templates_df.to_excel(writer, sheet_name="Copy Templates", index=False)
        schema_df.to_excel(writer, sheet_name="Schema Block", index=False)
        phasing_df.to_excel(writer, sheet_name="Phasing", index=False)

    # Formatting
    wb = load_workbook(OUT)
    header_fill = PatternFill(
        start_color="1F4E79", end_color="1F4E79", fill_type="solid"
    )
    header_font = Font(bold=True, color="FFFFFF", size=11)
    rule_fill = PatternFill(
        start_color="FFF2CC", end_color="FFF2CC", fill_type="solid"
    )

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        # Header row formatting
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )

        # Wrap text + top-align all cells
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(
                    horizontal="left", vertical="top", wrap_text=True
                )

        # Highlight rules sheet
        if sheet_name == "Copy Rules (READ FIRST)":
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
                for cell in row:
                    if cell.column == 1:  # Rule column
                        cell.fill = rule_fill
                        cell.font = Font(bold=True)

        # Column widths
        widths = {
            "Summary": [55, 30],
            "Copy Rules (READ FIRST)": [55, 90],
            "Per-URL Implementation": [
                10,
                70,
                30,
                12,
                12,
                90,
                55,
                55,
                90,
                40,
                60,
            ],
            "Copy Templates": [40, 70, 100],
            "Schema Block": [40, 110],
            "Phasing": [22, 100],
        }
        for i, w in enumerate(widths.get(sheet_name, []), start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

        # Freeze header
        ws.freeze_panes = "A2"

    wb.save(OUT)
    print(f"Wrote: {OUT}")
    print(f"Total URL rows: {len(impl_rows)}")


if __name__ == "__main__":
    write_excel()
