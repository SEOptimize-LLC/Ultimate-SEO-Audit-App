"""SameDay - Empty anchor text implementation plan (Elementor edition).

Audit finding (per sameday_technical_onpage_audit.md, Section 10 P2 #2,
roadmap row #8): "Add anchor text to 45 links currently without it."

Live verification (2026-04-28):
  - Audit's "45 links" is significantly under-counted
  - Screaming Frog crawl shows 779 truly-empty hyperlinks
    (no Anchor text AND no Alt Text on a child image)
  - 97% of those are template-driven repeat instances of the same
    underlying issues - not 779 unique fixes
  - The "Follow Us" social icons appear on 379 INNER pages only
    (blog + service-area + service-detail). Homepage has NO social
    icons in its footer.

Site stack: WordPress + Elementor. All fix instructions in this
deliverable are written as click-paths an Elementor admin can follow
in the WP dashboard - no code, no theme-template edits.

Output: Clients/SameDay/Full SEO Audit/sameday_empty_anchors_plan.xlsx
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INLINKS_PATH = PROJECT_ROOT / "Clients" / "SameDay" / "sameday_all_inlinks.xlsx"
OUTPUT_PATH = (
    PROJECT_ROOT
    / "Clients"
    / "SameDay"
    / "Full SEO Audit"
    / "sameday_empty_anchors_plan.xlsx"
)

THIN_BORDER = Border(
    left=Side(style="thin", color="D0D0D0"),
    right=Side(style="thin", color="D0D0D0"),
    top=Side(style="thin", color="D0D0D0"),
    bottom=Side(style="thin", color="D0D0D0"),
)


def load_truly_empty() -> pd.DataFrame:
    df = pd.read_excel(INLINKS_PATH, sheet_name=0)
    hyper = df[df["Type"] == "Hyperlink"].copy()
    empty_mask = hyper["Anchor"].isna() | (
        hyper["Anchor"].astype(str).str.strip() == ""
    )
    empties = hyper[empty_mask].copy()
    alt_present = empties["Alt Text"].notna() & (
        empties["Alt Text"].astype(str).str.strip() != ""
    )
    truly_empty = empties[~alt_present].copy()
    return truly_empty


def categorize(row: pd.Series) -> str:
    dest = str(row.get("Destination", "")).lower()
    pos = str(row.get("Link Position", ""))
    if "facebook.com" in dest:
        return "Inner-page footer - Facebook icon"
    if "twitter.com" in dest or "x.com" in dest:
        return "Inner-page footer - Twitter/X icon"
    if "fox13now.com" in dest:
        return "Broken external promo link"
    if "/testimonials/page/" in dest:
        return "Testimonials pagination"
    if dest.endswith("samedayutah.com/") or dest.endswith("samedayutah.com"):
        return "Logo link / homepage self-link"
    if pos == "Header":
        return "Header link"
    if "/electrical/" in dest or "/blog/ev-chargers" in dest:
        return "Electrical hub - heading-card link"
    if "/specials/" in dest:
        return "Heading-card / CTA"
    return "One-off content link"


# =====================================================================
# THE FIX TICKETS - one ticket per fix, written for Elementor admin
# =====================================================================

FIX_TICKETS = [
    # -------------------------------------------------------------
    # Ticket 1: Inner-page footer Follow Us section
    # -------------------------------------------------------------
    {
        "ticket": "FIX 1",
        "title": "Inner-page footer 'Follow Us' social icons",
        "instances_resolved": 758,
        "priority": "P1",
        "estimated_time": "20-30 min (after social-profile decision)",
        "what_users_see": (
            "On 379 inner pages (blog posts, service-area city pages, "
            "service-detail pages) there's a 'Follow Us' section in the "
            "footer with a Facebook and a Twitter/X icon. The icons are "
            "clickable but have no text label, so screen readers and "
            "search engines can't tell what they link to."
        ),
        "why_it_matters": (
            "(1) The Twitter icon links to https://twitter.com/i/flow/login - "
            "Twitter's generic login page, NOT a SameDay X profile. 379 pages "
            "are pointing users at a login screen.\n"
            "(2) Empty icon links count as 'empty anchor text' in SEO crawls "
            "and fail WCAG 2.1 SC 2.4.4 (Link Purpose). Both issues fixed by "
            "the same edit."
        ),
        "client_decision_required": (
            "BEFORE TOUCHING ELEMENTOR, confirm with the client:\n"
            "  Q1: Does SameDay actively maintain a Facebook page? "
            "(facebook.com/Samedayutah/)\n"
            "  Q2: Does SameDay have an active X (Twitter) profile? "
            "If yes, what's the URL?\n\n"
            "If BOTH are inactive/abandoned -> remove the entire 'Follow Us' "
            "section from the footer template (recommended).\n"
            "If FB only -> remove the X icon, fix the FB icon's accessibility.\n"
            "If both active -> update the X URL and fix accessibility on both."
        ),
        "elementor_steps": (
            "OPTION A - Remove the section entirely (recommended if profiles "
            "aren't maintained):\n"
            "  1. WP Admin -> Templates -> Theme Builder\n"
            "  2. Find the Footer template used on inner pages "
            "(it'll be the one with conditions covering posts/pages, "
            "NOT the homepage-only footer)\n"
            "  3. Click 'Edit with Elementor'\n"
            "  4. In the Elementor canvas, find the section/widget "
            "containing the Facebook and Twitter icons (usually labeled "
            "'Social Icons' or inside a column under 'Follow Us')\n"
            "  5. Right-click the Social Icons widget (or the column "
            "wrapping it) -> Delete\n"
            "  6. Click 'Update' (top right)\n\n"
            "OPTION B - Keep and fix:\n"
            "  1. WP Admin -> Templates -> Theme Builder -> open inner-page "
            "Footer -> Edit with Elementor\n"
            "  2. Click the Social Icons widget\n"
            "  3. In the left panel, under 'Content' tab, you'll see each "
            "icon listed (Facebook, Twitter)\n"
            "  4. For Twitter: click it, replace the URL with SameDay's "
            "real X profile URL (or remove this icon if no profile exists)\n"
            "  5. Elementor Social Icons widget auto-adds aria-labels based "
            "on the platform - no extra step needed for that\n"
            "  6. Click 'Update'\n\n"
            "VERIFY: Visit any blog post (e.g. /blog/when-to-call-an-"
            "electrician/) - the Follow Us section should be gone (Option A) "
            "or pointing at the right URLs (Option B)."
        ),
    },
    # -------------------------------------------------------------
    # Ticket 2: Logo missing alt text
    # -------------------------------------------------------------
    {
        "ticket": "FIX 2",
        "title": "Logo image in header has no alt text",
        "instances_resolved": 5,
        "priority": "P1",
        "estimated_time": "5 min",
        "what_users_see": (
            "The SameDay logo in the top-left of every page is a clickable "
            "image that takes you home. The image has no alt text, so a "
            "screen reader user hears 'link' or 'image link' with no idea "
            "what it goes to."
        ),
        "why_it_matters": (
            "Logo links are usually the most-clicked link on a website. "
            "Missing alt text on the logo is a top-10 finding in any "
            "accessibility audit and is also flagged as 'empty anchor text' "
            "in SEO crawls."
        ),
        "client_decision_required": "None - just do it.",
        "elementor_steps": (
            "1. WP Admin -> Templates -> Theme Builder -> open the Header "
            "template -> Edit with Elementor\n"
            "2. Click the logo image (the SameDay logo widget)\n"
            "3. In the left panel, under 'Content' tab, look for the image "
            "settings\n"
            "4. If the logo is set via the WordPress Site Identity (Customize "
            "-> Site Identity -> Logo), the alt text is set there: WP Admin "
            "-> Media Library -> click the logo file -> Alternative Text "
            "field -> enter: SameDay Heating, Air, Plumbing & Electrical\n"
            "5. If the logo is set directly in the Elementor widget, click "
            "the image in the widget settings, then in the Media popup edit "
            "the Alt Text field with the same text\n"
            "6. Click 'Update'\n\n"
            "VERIFY: Reload the homepage. Right-click the logo -> Inspect. "
            "The <img> tag should have alt='SameDay Heating, Air, Plumbing "
            "& Electrical'."
        ),
    },
    # -------------------------------------------------------------
    # Ticket 3: Electrical hub - heading-card empty anchors
    # -------------------------------------------------------------
    {
        "ticket": "FIX 3",
        "title": "Electrical hub page - service cards have no link text",
        "instances_resolved": 10,
        "priority": "P2",
        "estimated_time": "20-30 min",
        "what_users_see": (
            "On https://samedayutah.com/electrical/ there are service cards "
            "for Generators, Lighting, EV Chargers, Smoke Alarms, Rewiring, "
            "Surge Protection, Outlets/Switches, Ceiling Fans, Panel "
            "Upgrades, etc. Each card is clickable and shows a heading like "
            "'Whole-Home Surge Protection in the Greater Salt Lake City "
            "Area' - but the heading text is OUTSIDE the actual link, so "
            "search engines see the link as empty."
        ),
        "why_it_matters": (
            "Service-category cards are prime internal-linking real estate. "
            "Each card represents a service that competes for local search "
            "rankings. Empty link text on the card means Google can crawl "
            "to /electrical/generators/ but gets no contextual signal that "
            "the link is about generators."
        ),
        "client_decision_required": "None.",
        "elementor_steps": (
            "1. WP Admin -> Pages -> Electrical (the /electrical/ page) "
            "-> Edit with Elementor\n"
            "2. Scroll to the section with the service cards (Generators, "
            "Lighting, etc.)\n"
            "3. Click any one card to identify the widget type. Most likely "
            "options:\n"
            "   - 'Image Box' or 'Icon Box' widget\n"
            "   - Custom HTML widget\n"
            "   - A Section/Column with a Button widget\n\n"
            "IF Image Box / Icon Box:\n"
            "   a. Click the widget\n"
            "   b. Under Content tab, find 'Title' field - confirm it "
            "matches the heading shown on the page\n"
            "   c. Find 'Link' field below the title - the link should "
            "point to the service URL\n"
            "   d. Elementor automatically wraps the title text inside the "
            "link when both fields are populated - if the title is empty "
            "but the link is set, that's the bug\n"
            "   e. Fix: paste the heading text into the Title field\n"
            "   f. Repeat for all 9-10 service cards\n\n"
            "IF Custom HTML widget:\n"
            "   a. Click the widget -> the HTML opens in the left panel\n"
            "   b. Find the <a href='...'></a> tag with no text inside\n"
            "   c. Move the heading text from outside the <a> tag to "
            "inside it. Example:\n"
            "      Before: <a href='/electrical/generators/'></a><h3>Home "
            "Generators</h3>\n"
            "      After:  <a href='/electrical/generators/'><h3>Home "
            "Generators</h3></a>\n\n"
            "AFTER FIXING /electrical/, also check these sister hubs - "
            "they likely use the same card pattern:\n"
            "   - https://samedayutah.com/heating/\n"
            "   - https://samedayutah.com/cooling/\n"
            "   - https://samedayutah.com/plumbing/\n\n"
            "VERIFY: After saving, right-click any service card on "
            "/electrical/ -> Inspect. The <a> tag should now wrap the "
            "heading text, not be empty."
        ),
    },
    # -------------------------------------------------------------
    # Ticket 4: Fox13 broken contest promo
    # -------------------------------------------------------------
    {
        "ticket": "FIX 4",
        "title": "Broken Fox 13 'Heat for the Holidays' contest link on /about/",
        "instances_resolved": 1,
        "priority": "P2",
        "estimated_time": "5 min",
        "what_users_see": (
            "On the About page there's a SameDay Contest - FOX 13 section "
            "with a 'Nominate a deserving family or individual to receive "
            "a new furnace' promo. Clicking it leads to a 404 on Fox 13's "
            "site - the contest is over."
        ),
        "why_it_matters": (
            "Outbound link to a 404 hurts user experience and signals "
            "'untended site' to crawlers. The empty-anchor finding is "
            "the secondary issue here - the bigger problem is the dead "
            "destination."
        ),
        "client_decision_required": (
            "Confirm with client: should the entire 'SameDay Contest - "
            "FOX 13' section be removed, or replaced with a current "
            "promotion?"
        ),
        "elementor_steps": (
            "1. WP Admin -> Pages -> About Us -> Edit with Elementor\n"
            "2. Scroll to the 'SameDay Contest - FOX 13' section\n"
            "3. Right-click the entire section -> Delete\n"
            "4. (If client wants to replace with a current promotion, "
            "rebuild the section using Elementor's Image + Heading + "
            "Button widgets pointed at the new promotion URL.)\n"
            "5. Click 'Update'\n\n"
            "VERIFY: Reload /about/ - the Fox 13 contest section should "
            "be gone."
        ),
    },
    # -------------------------------------------------------------
    # Ticket 5: Testimonials pagination arrows
    # -------------------------------------------------------------
    {
        "ticket": "FIX 5",
        "title": "Testimonials pagination arrows have no labels",
        "instances_resolved": 2,
        "priority": "P3",
        "estimated_time": "5 min",
        "what_users_see": (
            "At the bottom of /testimonials/ there are pagination "
            "arrows (Next page / Previous page). The arrow icons are "
            "clickable but have no readable text - screen readers say "
            "'link' with no destination."
        ),
        "why_it_matters": (
            "Accessibility issue (WCAG 2.1 SC 2.4.4). Low SEO impact "
            "because pagination links are typically noindex/follow."
        ),
        "client_decision_required": "None.",
        "elementor_steps": (
            "1. Identify which Elementor widget renders the pagination. "
            "Open /testimonials/ in WP Admin -> Edit with Elementor.\n"
            "2. Most testimonial pagination uses 'Posts' or 'Loop Grid' "
            "widget pagination, or a custom 'Pagination' widget.\n"
            "3. If it's a Posts/Loop Grid widget:\n"
            "   - Click the widget -> Style tab -> Pagination section\n"
            "   - Look for 'Previous Label' and 'Next Label' fields\n"
            "   - Replace icon-only with text + icon, e.g. 'Previous' / "
            "'Next'\n"
            "   (Or keep the icon and add a text label that's "
            "screen-reader-only via Custom CSS - but Option A is "
            "simpler.)\n"
            "4. If it's a custom widget without label fields, replace it "
            "with the standard Elementor 'Posts' widget which has built-in "
            "labels.\n"
            "5. Click 'Update'\n\n"
            "VERIFY: Reload /testimonials/ - pagination should show "
            "visible 'Previous' / 'Next' text alongside or instead of "
            "the arrows."
        ),
    },
    # -------------------------------------------------------------
    # Ticket 6: Stray homepage links from blog posts
    # -------------------------------------------------------------
    {
        "ticket": "FIX 6",
        "title": "Stray empty links to homepage on 3 blog posts",
        "instances_resolved": 3,
        "priority": "P3",
        "estimated_time": "10-15 min total (3 posts x ~5 min each)",
        "what_users_see": (
            "Three blog posts contain an inline link to the homepage "
            "with no anchor text. Likely a leftover from a CMS import "
            "or a broken inline image that was deleted but its link "
            "wrapper stayed."
        ),
        "why_it_matters": (
            "Each empty link is a wasted internal-link slot. Low impact "
            "but trivial to fix."
        ),
        "client_decision_required": "None.",
        "elementor_steps": (
            "Affected posts:\n"
            "  - /blog/hire-a-licensed-electrician-to-update-light-fixtures/\n"
            "  - /blog/when-to-call-an-electrician/\n"
            "  - /blog/why-regular-air-conditioning-service/\n\n"
            "For EACH post:\n"
            "1. WP Admin -> Posts -> open the post -> Edit with Elementor "
            "(or click into the Text Editor widget if not Elementor-built)\n"
            "2. In the post body, find any link that has no visible text "
            "(it'll look like a thin underlined gap, or hover the cursor "
            "to reveal the cursor change)\n"
            "3. Click into the link, then either:\n"
            "   - DELETE the empty link entirely (recommended - they "
            "appear to be import artifacts)\n"
            "   - OR add anchor text describing what the link offers, e.g. "
            "'Schedule SameDay service' or 'Get a free estimate'\n"
            "4. Save / Update\n\n"
            "VERIFY: After save, visit the post and confirm no empty "
            "underlined gaps in the body text."
        ),
    },
    # -------------------------------------------------------------
    # Ticket 7: One-off CTA on /request-estimate/
    # -------------------------------------------------------------
    {
        "ticket": "FIX 7",
        "title": "One-off empty anchor on /request-estimate/ -> /specials/",
        "instances_resolved": 1,
        "priority": "P3",
        "estimated_time": "5 min",
        "what_users_see": (
            "A button or icon CTA on /request-estimate/ pointing to "
            "/specials/ has no readable text or label."
        ),
        "why_it_matters": (
            "Single instance. Same accessibility/SEO issue as the others "
            "but at smaller scale."
        ),
        "client_decision_required": "None.",
        "elementor_steps": (
            "1. WP Admin -> Pages -> Request Estimate -> Edit with "
            "Elementor\n"
            "2. Find the button/icon linking to /specials/ (look for the "
            "promotional callout that says something about specials or "
            "deals)\n"
            "3. Click the widget:\n"
            "   - If it's a Button widget: confirm the 'Text' field has "
            "visible copy like 'View Current Specials'. If empty, fill it.\n"
            "   - If it's an Icon Box / Image Box: confirm the Title field "
            "is populated.\n"
            "4. Click 'Update'\n\n"
            "VERIFY: Reload /request-estimate/ - the link should now "
            "show readable text."
        ),
    },
]


# =====================================================================
# Workbook builder
# =====================================================================


def build_workbook() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    truly_empty = load_truly_empty()
    truly_empty["Bucket"] = truly_empty.apply(categorize, axis=1)

    wb = Workbook()
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    _build_summary_sheet(wb, truly_empty)
    _build_fix_tickets_sheet(wb)
    _build_per_link_sheet(wb, truly_empty)

    wb.save(OUTPUT_PATH)
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Size:  {OUTPUT_PATH.stat().st_size:,} bytes")
    print(f"Total truly-empty rows: {len(truly_empty)}")
    print(truly_empty["Bucket"].value_counts().to_string())


def _title_cell(ws, ref: str, text: str) -> None:
    ws.merge_cells(ref)
    cell = ws[ref.split(":")[0]]
    cell.value = text
    cell.font = Font(bold=True, size=14, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E78")
    cell.alignment = Alignment(
        horizontal="left", vertical="center", wrap_text=True
    )
    ws.row_dimensions[1].height = 28


def _header_row(ws, row_idx: int, headers: list[str]) -> None:
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=row_idx, column=col_idx, value=header)
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = PatternFill("solid", fgColor="2E75B6")
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = THIN_BORDER
    ws.row_dimensions[row_idx].height = 30


def _build_summary_sheet(wb: Workbook, truly_empty: pd.DataFrame) -> None:
    ws = wb.create_sheet("Summary")

    _title_cell(
        ws, "A1:B1",
        "SameDay - Empty Anchor Text Fix Plan (Elementor + WordPress)",
    )

    rows = [
        (
            "Audit finding",
            "sameday_technical_onpage_audit.md, Section 10 P2 #2 + roadmap row #8: "
            "'Add anchor text to 45 links currently without it.'"
        ),
        ("", ""),
        ("Audit's reported count", "45 links"),
        (
            "Actual count (live SF crawl, 2026-04-28)",
            f"{len(truly_empty)} truly-empty hyperlinks "
            "(no anchor text AND no alt text on a wrapped image)"
        ),
        (
            "Why those numbers don't match",
            "The original audit likely deduplicated by destination URL "
            "or filtered out icon/social patterns. SF data on file is the "
            "source of truth and shows 779 instances - but those 779 "
            "boil down to just 7 fix tickets."
        ),
        ("", ""),
        ("Total fix tickets", "7 (see Fix Tickets sheet)"),
        (
            "Estimated total time",
            "~75 minutes total once social-profile decision is made"
        ),
        (
            "Site stack",
            "WordPress + Elementor. All instructions in this report are "
            "click-paths an Elementor admin can follow in the WP "
            "dashboard - no code, no theme files."
        ),
        ("", ""),
        ("Highest-leverage fix", "FIX 1 - Inner-page footer 'Follow Us' icons (758 of 779 instances)"),
        ("", ""),
        (
            "ACTION REQUIRED FROM CLIENT BEFORE FIX 1",
            "Confirm: Does SameDay actively maintain (a) a Facebook page, "
            "(b) an X/Twitter profile? The current X link points to "
            "Twitter's generic login page - a real profile URL is needed, "
            "or the X icon should be removed entirely."
        ),
        ("", ""),
        (
            "Recommended fix order",
            "FIX 1 (P1, requires client decision) -> FIX 2 (P1, no decision) "
            "-> FIX 3 (P2) -> FIX 4 (P2) -> FIX 5/6/7 (P3)"
        ),
        ("", ""),
        (
            "Verification method",
            "After all fixes, re-run a Screaming Frog crawl and re-check "
            "All Inlinks for Type=Hyperlink AND empty Anchor AND empty "
            "Alt Text. Target: <10 instances remaining."
        ),
    ]

    for row_idx, (label, value) in enumerate(rows, start=2):
        label_cell = ws.cell(row=row_idx, column=1, value=label)
        value_cell = ws.cell(row=row_idx, column=2, value=value)
        label_cell.font = Font(bold=True, size=10)
        value_cell.font = Font(size=10)
        label_cell.alignment = Alignment(
            horizontal="left", vertical="top", wrap_text=True
        )
        value_cell.alignment = Alignment(
            horizontal="left", vertical="top", wrap_text=True
        )
        if label or value:
            ws.row_dimensions[row_idx].height = 55

    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 95


def _build_fix_tickets_sheet(wb: Workbook) -> None:
    ws = wb.create_sheet("Fix Tickets")

    _title_cell(
        ws, "A1:B1",
        "Fix Tickets - Step-by-Step Elementor Click-Paths",
    )

    row_idx = 2

    for ticket in FIX_TICKETS:
        # Ticket header band
        header_text = (
            f"{ticket['ticket']} ({ticket['priority']}): {ticket['title']}"
        )
        ws.merge_cells(start_row=row_idx, start_column=1,
                       end_row=row_idx, end_column=2)
        cell = ws.cell(row=row_idx, column=1, value=header_text)
        cell.font = Font(bold=True, size=12, color="FFFFFF")
        prio_color = {"P1": "C00000", "P2": "ED7D31", "P3": "5B9BD5"}
        cell.fill = PatternFill(
            "solid", fgColor=prio_color.get(ticket["priority"], "305496")
        )
        cell.alignment = Alignment(
            horizontal="left", vertical="center", wrap_text=True
        )
        ws.row_dimensions[row_idx].height = 24
        row_idx += 1

        # Ticket body rows
        body_rows = [
            ("Instances resolved", str(ticket["instances_resolved"])),
            ("Estimated time", ticket["estimated_time"]),
            ("What users see", ticket["what_users_see"]),
            ("Why it matters", ticket["why_it_matters"]),
            ("Decision required from client", ticket["client_decision_required"]),
            ("Elementor steps", ticket["elementor_steps"]),
        ]
        for label, value in body_rows:
            label_cell = ws.cell(row=row_idx, column=1, value=label)
            value_cell = ws.cell(row=row_idx, column=2, value=value)
            label_cell.font = Font(bold=True, size=10)
            value_cell.font = Font(size=10)
            label_cell.fill = PatternFill("solid", fgColor="F2F2F2")
            label_cell.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )
            value_cell.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )
            label_cell.border = THIN_BORDER
            value_cell.border = THIN_BORDER

            # Auto-size based on number of newlines in value
            line_count = max(2, str(value).count("\n") + 2)
            ws.row_dimensions[row_idx].height = min(line_count * 16, 600)
            row_idx += 1

        # Spacer row between tickets
        row_idx += 1

    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 110


def _build_per_link_sheet(
    wb: Workbook, truly_empty: pd.DataFrame
) -> None:
    ws = wb.create_sheet("Per-Link Detail (Reference)")

    _title_cell(
        ws, "A1:F1",
        "Per-Link Detail - Source Data from SF Crawl (Reference Only)",
    )

    # Subtitle row explaining this sheet
    ws.merge_cells("A2:F2")
    sub = ws["A2"]
    sub.value = (
        "This sheet lists every individual empty-anchor link found in the SF "
        "crawl, mapped to the fix ticket that resolves it. The dev team does "
        "NOT need to click through these one by one - the Fix Tickets sheet "
        "is the actionable plan. This sheet exists to show traceability "
        "between the audit finding and the fix."
    )
    sub.font = Font(italic=True, size=10)
    sub.alignment = Alignment(
        horizontal="left", vertical="center", wrap_text=True
    )
    sub.fill = PatternFill("solid", fgColor="FFF2CC")
    ws.row_dimensions[2].height = 50

    headers = [
        "Source URL", "Destination URL", "Link Position",
        "Status Code", "Bucket", "Resolved By",
    ]
    _header_row(ws, 3, headers)

    bucket_to_ticket = {
        "Inner-page footer - Facebook icon": "FIX 1",
        "Inner-page footer - Twitter/X icon": "FIX 1",
        "Logo link / homepage self-link": "FIX 2",
        "Header link": "FIX 2",
        "Electrical hub - heading-card link": "FIX 3",
        "Heading-card / CTA": "FIX 7",
        "Broken external promo link": "FIX 4",
        "Testimonials pagination": "FIX 5",
        "One-off content link": "FIX 6 / FIX 7",
    }

    truly_empty_sorted = truly_empty.sort_values(
        by=["Bucket", "Source", "Destination"]
    ).reset_index(drop=True)

    for row_idx, (_, r) in enumerate(
        truly_empty_sorted.iterrows(), start=4
    ):
        ticket = bucket_to_ticket.get(r["Bucket"], "Review")
        values = [
            r["Source"],
            r["Destination"],
            r["Link Position"],
            int(r["Status Code"]) if pd.notna(r["Status Code"]) else "",
            r["Bucket"],
            ticket,
        ]
        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = Font(size=9)
            cell.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True
            )
            cell.border = THIN_BORDER

    widths = {"A": 60, "B": 60, "C": 14, "D": 12, "E": 36, "F": 16}
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width

    ws.freeze_panes = "A4"


def main() -> None:
    build_workbook()


if __name__ == "__main__":
    main()
