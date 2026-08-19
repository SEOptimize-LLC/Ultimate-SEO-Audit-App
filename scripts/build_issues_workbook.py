"""Build the per-URL audit-issues workbook: 8 tabs, every affected URL and
its issue, mapped to the fix lane (2.1 queue / 1.8 quality review) covering it.

    python scripts/build_issues_workbook.py [YYYY-MM]

Exists because the 1.2 tabs deliberately carry findings with sample URLs
(readability), which means no Google Sheet tab holds the full implementation
lists - the owner needs them to work the fixes. Source: each client's
Monthly SEO Workbook/<month>/index_audit.json (per-URL Inspection states)
plus the handful of 1.4/week-1 items that are not GSC states.

Output: Documents/Audit Issues by URL - all clients - <month>.xlsx
Red Hat Display via the shared font table (brand rule), frozen header,
full URLs, no example rows.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import openpyxl
import yaml
from openpyxl.styles import Font

MONTH = sys.argv[1] if len(sys.argv) > 1 else "2026-08"
ROOT = Path(__file__).resolve().parent.parent

NAMES = {
    "superior": "Superior Water & Air", "sameday": "SameDay Utah",
    "beehive": "Beehive Plumbing", "comfort": "Comfort Solutions",
    "arsenal": "Arsenal Health", "cudio": "Cudio",
    "snow": "Snow Teeth Whitening", "educationwalkthrough": "Education Walkthrough",
}

# GSC coverage states that ARE audit issues, with the lane that owns them.
# Normal states (Submitted and indexed, Page with redirect, Alternative page
# with proper canonical tag) are deliberately excluded - this workbook lists
# problems, not inventory (the Indexation by URL workbook holds everything).
STATE_LANE = [
    ("noindex", "2.1 - stale-noindex recrawl (SameDay fix #1)", ("sameday",)),
    ("noindex", "Review - noindex found; confirm intentional before touching", None),
    ("Crawled - currently not indexed", "1.8 - quality review (improve or prune)", None),
    ("Discovered - currently not indexed", "2.1 - crawl path / internal links (old-tail rows wait for the 1.8 quality review)", None),
    ("unknown to Google", "2.1 - sitemap + internal links", None),
    ("Not found (404)", "2.1 - restore or 301 (see the fix row for the exact target)", None),
    ("Soft 404", "2.1 - populate the page (reads as empty to Google)", None),
    ("Redirect error", "2.1 - fix the redirect chain/loop", None),
    ("Duplicate", "2.1 - canonical fix", None),
    ("Server error", "2.1 - server fix", None),
    ("Blocked by robots.txt", "Review - confirm the block is intentional", None),
]

# 1.4 / week-1 items that are not GSC coverage states. Every URL verified in
# session (render shells, dead coupons, live duplicate pairs).
EXTRA = {
    "arsenal": [
        ("SITEWIDE - every route serves ~8 words of raw HTML (sampled URLs below)",
         "Raw HTML empty (client-rendered SPA)", "2.1 fix #1 - server-render/pre-render"),
    ] + [(u, "Raw HTML empty (client-rendered SPA)", "2.1 fix #1 - server-render/pre-render")
         for u in [
            "https://www.arsenalhealth.com/",
            "https://www.arsenalhealth.com/gym/one-on-one-personal-training-denver",
            "https://www.arsenalhealth.com/gym/personal-training-for-back-pain-denver",
            "https://www.arsenalhealth.com/gym/personal-training-for-shoulder-pain",
            "https://www.arsenalhealth.com/locations/arvada",
            "https://www.arsenalhealth.com/locations/dtc",
            "https://www.arsenalhealth.com/locations/dtc/personal-trainer",
            "https://www.arsenalhealth.com/locations/louisville",
            "https://www.arsenalhealth.com/chiropractic-therapy",
            "https://www.arsenalhealth.com/female-personal-trainer-in-denver",
            "https://www.arsenalhealth.com/hyrox",
            "https://www.arsenalhealth.com/memberships",
            "https://www.arsenalhealth.com/personal-training-in-arvada",
            "https://www.arsenalhealth.com/personal-training/injury-recovery",
            "https://www.arsenalhealth.com/personal-training/strength-training",
            "https://www.arsenalhealth.com/personal-training/weight-loss",
            "https://www.arsenalhealth.com/blog/8-week-hyrox-training-plan-beginners",
            "https://www.arsenalhealth.com/blog/do-peptides-actually-work-the-science-behind-the-claims",
            "https://www.arsenalhealth.com/blog/how-soon-can-i-walk-after-prp-injection",
            "https://www.arsenalhealth.com/nad",
            "https://www.arsenalhealth.com/sports-massage-therapy"]] + [
        ("https://www.arsenalhealth.com/hyrox-gym-denver",
         "Live duplicate of /blog/hyrox-gym-denver (migration leftover)",
         "2.1 fix #2 - 301 root form to the /blog/ form"),
    ],
    "comfort": [
        (u, "404 but still earning impressions (deleted coupon)",
         "2.1 fix #2 - 301 to /coupons/")
        for u in [
            "https://www.comfortsolutionsutah.com/coupons/5600-in-rebates/",
            "https://www.comfortsolutionsutah.com/coupons/59-off-any-fireplace-repair-or-upgrade/",
            "https://www.comfortsolutionsutah.com/coupons/free-plasma-pure-air-on-any-hvac-installation/"]
    ] + [
        ("https://www.comfortsolutionsutah.com/sitemap_index.xml",
         "Registered sitemap returns 404", "2.1 fix #1 - fix or resubmit"),
    ],
    "educationwalkthrough": [
        ("https://educationwalkthrough.com/what-to-look-for-during-classroom-walkthroughs/",
         "Live duplicate of the main what-to-look-for post (splits look-fors rankings)",
         "2.1 fix #3 - 301 to the main post"),
    ],
    "superior": [
        ("https://superiorwaterandair.com/video-sitemap.xml",
         "Listed in the sitemap index but does not resolve",
         "2.1 fix #1 - fix or remove from the index"),
    ],
    "sameday": [
        ("https://samedayutah.com/service-area/sandy-ut/plumbing/",
         "Duplicate URL pattern (mirror of /service-area/plumbing/sandy-ut/)",
         "2.1 fix #2 - standardize + 301; enumerate all pairs per the fix row"),
    ],
}

BRAND_FONT = "Red Hat Display"


def lane_for(state: str, slug: str) -> str | None:
    for needle, lane, only in STATE_LANE:
        if needle.lower() in state.lower():
            if only and slug not in only:
                continue
            return lane
    return None


def main() -> None:
    reg = yaml.safe_load((ROOT / "clients/registry.yaml").read_text(encoding="utf-8"))
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    total = 0
    for slug, name in NAMES.items():
        ws = wb.create_sheet(name[:31])
        ja = ROOT / reg[slug]["folder"] / "Monthly SEO Workbook" / MONTH / "index_audit.json"
        # Live verification (owner rule 2026-08-19: every URL fetched TODAY,
        # never Google's crawl memory alone). Produced by verify_issue_urls.py.
        live = {}
        lv = ROOT / reg[slug]["folder"] / "monthly_plan" / f"{MONTH}-live-verification.json"
        if lv.exists():
            for r in json.loads(lv.read_text(encoding="utf-8")):
                live[r["url"].rstrip("/")] = r
        rows_out = []
        if ja.exists():
            data = json.loads(ja.read_text(encoding="utf-8"))
            for r in data.get("rows", []):
                # In-scope only: the audit's findings counted in-scope URLs
                # (audit-workflow rule 7 - no fr_CA locales, jobs pages or
                # similar non-SEO URLs padding a working list). The full
                # population lives in the Indexation by URL workbook.
                if str(r.get("inScope")) != "True":
                    continue
                state = str(r.get("state") or "")
                lane = lane_for(state, slug)
                if not lane:
                    continue
                # The raw GSC state misled a manual check (owner, 2026-08-19:
                # five random "noindex" URLs all carried index,follow live).
                # The Issue cell must state the DIAGNOSIS, not Google's label:
                # these are stale index records, not live tags.
                if slug == "sameday" and "noindex" in state.lower():
                    state = ("Google's index record says noindex (last crawl "
                             "June) - the LIVE page has index,follow; stale "
                             "verdict, needs recrawl, no page edit")
                rows_out.append([r.get("url"), state, lane,
                                 r.get("lastCrawl") or "never"])
        for url, issue, lane in EXTRA.get(slug, []):
            rows_out.append([url, issue, lane, "-"])
        rows_out.sort(key=lambda x: (x[2], x[1], x[0]))

        def live_cell(url: str) -> str:
            r = live.get(str(url).rstrip("/"))
            if not r:
                return "(not fetchable - see row text)" if not str(url).startswith("http") else "(not checked)"
            bits = [f"HTTP {r['status']}"]
            if r.get("redirected_to"):
                bits.append(f"redirects to {r['redirected_to']}")
            if r.get("robots"):
                bits.append(f"robots: {r['robots']}")
            if r.get("note"):
                bits.append(r["note"])
            return " | ".join(bits)

        rows_out = [[u, s, live_cell(u), lane, lc]
                    for u, s, lane, lc in rows_out]

        ws.append([f"{name} - audit issues by URL, {MONTH}"])
        ws.append([f"{len(rows_out)} affected URL(s). Every URL fetched live on "
                   f"the date in the header - the live column is today's "
                   f"reality; Google's record is what Search Console remembers. "
                   f"Fix details on the 2.1 tab; quality-review items in 1.8 "
                   f"section C."])
        ws.append([])
        ws.append(["URL", "Google's record (issue)", "LIVE check 2026-08-19",
                   "Fix lane", "Google last crawled"])
        for row in rows_out:
            ws.append(row)
        ws.freeze_panes = "A5"
        ws.column_dimensions["A"].width = 78
        ws.column_dimensions["B"].width = 40
        ws.column_dimensions["C"].width = 48
        ws.column_dimensions["D"].width = 46
        ws.column_dimensions["E"].width = 15
        for c in ws[4]:
            c.font = Font(bold=True)
        ws["A1"].font = Font(bold=True, size=13)
        total += len(rows_out)
        print(f"{name:<24} {len(rows_out):>4} affected URLs")

    out = ROOT / "Documents" / f"Audit Issues by URL - all clients - {MONTH}.xlsx"
    wb.save(out)

    # Brand font via the shared font table (spreadsheet-standards): one pass,
    # index 0 included, sizes/weights untouched.
    wb2 = openpyxl.load_workbook(out)
    for f in wb2._fonts:
        f.name = BRAND_FONT
    for st in getattr(wb2, "_named_styles", []):
        if getattr(st, "font", None) is not None:
            st.font.name = BRAND_FONT
    wb2.save(out)
    import zipfile
    x = zipfile.ZipFile(out).read("xl/styles.xml").decode("utf-8", "replace")
    assert x.count("Calibri") == 0 and x.count("Arial") == 0, "brand font not applied"
    print(f"\nwrote {out} ({total} rows, font verified)")


if __name__ == "__main__":
    main()
