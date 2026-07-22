"""Superior Water & Air — Internal Redirect URLs action plan.

Audit finding: "Fix 66 internal redirect URLs — 209 pages link to /water/ and
/hvac/ but both redirect instead of serving content; old blog/location
redirects should point to relevant service pages, not homepage"

Live verification (2026-04-21) confirms:
- /water/ and /hvac/ 301 → / (homepage) — 209 + 209 = 418 internal links wasted
- 17 city-plumbing pages 301 → / (homepage) — massive local SEO equity loss
- /contact → /contact/ (trailing slash) — 208 links, trivial fix
- 45+ other legacy URL → / redirects from old blog posts, location pages, 2014-2018 archives

Total internal links pointing to redirects: 1,322 across 66 redirect URLs.
"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = (r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/"
        r"Claude/Claude Code + VS Code/SEO/Projects/Projects/"
        r"Ultimate SEO Auditor/Clients/Superior/Full SEO Audit/")
out = base + "superior_internal_redirects_plan.xlsx"

df = pd.read_excel(base + "internal_redirect_urls.xlsx")
df = df.sort_values("Pages Linking To It", ascending=False).reset_index(drop=True)


# =========================================================================
# Classify each redirect + suggest a better destination
# =========================================================================
def classify(row):
    url = row["Redirecting URL"]
    dest = str(row["Final Destination"])
    path = url.replace("https://superiorwaterandair.com", "")
    dest_path = dest.replace("https://superiorwaterandair.com", "")
    home = dest_path.rstrip("/") == ""

    # Hub category pages 301ing to homepage — biggest issue
    if path in ("/water/", "/water"):
        return {
            "tier": 1,
            "tier_label": "Tier 1 — Category Hub",
            "issue": "Water category hub 301s to homepage. 209 internal links lose their signal.",
            "suggested_dest": "Restore /water/ as an indexable category hub listing water services (water treatment, water softeners, water heaters). OR if restoring isn't possible, 301 to /plumbing-services/ — not homepage.",
        }
    if path in ("/hvac/", "/hvac"):
        return {
            "tier": 1,
            "tier_label": "Tier 1 — Category Hub",
            "issue": "HVAC category hub 301s to homepage. 209 internal links lose their signal.",
            "suggested_dest": "Restore /hvac/ as an indexable category hub listing HVAC services (heating, cooling, duct cleaning). OR 301 to /home-cooling/ or /furnace-heating-guide-repair-installation/ — not homepage.",
        }

    # Contact trailing slash
    if path.rstrip("/") == "/contact":
        return {
            "tier": 2,
            "tier_label": "Tier 2 — Trailing Slash",
            "issue": "208 pages link to /contact (no trailing slash). 301s to /contact/.",
            "suggested_dest": "Update all 208 internal links to use /contact/ with trailing slash. OR accept the 301 as a one-hop redirect (low-impact but adds latency).",
        }
    if path.rstrip("/") == "/contact/estimate":
        return {
            "tier": 2,
            "tier_label": "Tier 2 — Trailing Slash",
            "issue": "/contact/estimate/ redirects back to /contact/ — looks like an orphan URL being bounced.",
            "suggested_dest": "If /contact/estimate/ was an old CTA URL, update any internal references to point directly to /contact/ OR create a proper estimate form page.",
        }

    # City/location pages 301ing to homepage (critical local SEO loss)
    city_patterns = [
        "plumbing-salt-lake-city", "plumbing-sandy", "plumbing-lehi",
        "plumbing-orem", "plumbing-draper", "plumbing-bountiful",
        "plumbing-west-jordan", "plumbing-south-jordan",
        "plumbing-west-valley-city", "plumbing-kaysville",
        "plumbing-midvale", "plumbing-centerville", "plumbing-davis-county",
        "plumbing-bluffdale", "plumbing-murray", "plumbing-utah-county",
        "plumber-sugar-house", "park-city-utah",
    ]
    if home and any(c in path.lower() for c in city_patterns):
        # Extract city name
        city = ""
        for c in city_patterns:
            if c in path.lower():
                # Clean up
                city = c.replace("plumbing-", "").replace("plumber-", "")
                city = city.replace("-utah", "").replace("-ut", "").replace("-", " ").title()
                break
        return {
            "tier": 3,
            "tier_label": "Tier 3 — City/Location Redirect",
            "issue": f"Old {city} plumbing city page 301s to homepage. 30 internal links losing local equity.",
            "suggested_dest": (
                f"Redirect to a dedicated {city} plumbing service page if one exists, "
                "OR the main /plumbing-services/ hub. Homepage is the weakest choice "
                "because it doesn't match the 'plumbing in {city}' intent."
            ),
        }

    # Service/sub-service redirects with specific mapping
    specific_maps = {
        "/plumbing-services/pipe-lining/": "/plumbing-services/service-and-repair/ (current dest is correct — keep as-is, but verify 48 linking pages still reference the old URL in anchors/content — consider updating internal links to save the 301 hop)",
        "/plumbing-services/emergency-plumber/": "/emergency-services/plumbing-repair/ (current dest is correct)",
        "/pipe-lining/": "Either /plumbing-services/service-and-repair/ or keep homepage if no relevant page exists",
        "/plumbing-services/bathro": "Looks truncated — likely /plumbing-services/bathroom-plumbing/ → check WP for the real URL",
        "/plumbing-services": "/plumbing-services/ (trailing slash fix)",
        "/plumbing-repair": "/plumbing-repair/ (trailing slash fix)",
        "/water-heaters/tankless-water-heaters/": "Should go to /water/water-heaters/tankless-water-heater/ or similar, not homepage",
        "/water-purification/water-softeners/": "Should go to /water/water-treatment/ or /water/water-softeners/, not homepage",
        "/services/air-conditioning-repair/": "Should go to /home-cooling/ or /air-conditioning/, not homepage",
        "/services/plumbingdrain-cleaning/": "Should go to /plumbing-services/drain-cleaning/ or similar",
        "/services/home-water-evaluation/": "/water/water-treatment/ (current dest is correct)",
        "/hard-water-tool/": "/water/water-treatment/ (current dest is correct)",
    }

    if path in specific_maps:
        return {
            "tier": 4 if "correct" in specific_maps[path] else 3,
            "tier_label": "Tier 4 — Verified Correct" if "correct" in specific_maps[path] else "Tier 3 — Remap Destination",
            "issue": f"Legacy URL pattern.",
            "suggested_dest": specific_maps[path],
        }

    # Old blog posts (2011-2018 date paths or old slugs) 301ing to homepage
    if home and (path.startswith("/2011/") or path.startswith("/2014/") or
                   path.startswith("/2015/") or path.startswith("/2016/") or
                   path.startswith("/2017/") or path.startswith("/2018/")):
        return {
            "tier": 5,
            "tier_label": "Tier 5 — Old Blog Archive",
            "issue": "Old date-prefix blog URL 301s to homepage. Low traffic impact.",
            "suggested_dest": (
                "Check if the non-dated version of the slug exists (/post-slug/ "
                "without the /YYYY/MM/ prefix). Redirect to that if it does. "
                "If post is gone entirely, 301 to the closest related service "
                "page or keep homepage if no good match."
            ),
        }

    # Old blog 301ing to a specific relevant page (already decent)
    if not home:
        return {
            "tier": 4,
            "tier_label": "Tier 4 — Already Reasonable",
            "issue": "Redirects to a relevant specific page, not homepage. Low priority.",
            "suggested_dest": (
                f"Current dest {dest_path} is topically aligned. "
                "Optional: update internal links to point directly to the "
                "destination to remove the 301 hop. Not urgent."
            ),
        }

    # Old blog post slugs 301ing to homepage — topic lost
    return {
        "tier": 5,
        "tier_label": "Tier 5 — Old Blog → Homepage",
        "issue": "Old blog post URL 301s to homepage — topic relevance lost.",
        "suggested_dest": (
            "Evaluate the post topic. If a current post or service page exists "
            "on the same topic, 301 there instead of homepage. Otherwise, "
            "homepage is an acceptable fallback."
        ),
    }


classifications = df.apply(classify, axis=1, result_type="expand")
df = pd.concat([df, classifications], axis=1)


# Sort by tier then by pages linking
df = df.sort_values(by=["tier", "Pages Linking To It"],
                     ascending=[True, False]).reset_index(drop=True)


# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()
ws = wb.active
ws.title = "Redirect Action Plan"

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1F4E78")
SUBTITLE_FONT = Font(name="Calibri", size=10, italic=True, color="595959")
CELL_FONT = Font(name="Calibri", size=10)
CELL_FONT_SM = Font(name="Calibri", size=9)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
SECTION_FILL = PatternFill("solid", fgColor="DDEBF7")
RED_FILL = PatternFill("solid", fgColor="F8CBAD")
ORANGE_FILL = PatternFill("solid", fgColor="FCE4D6")
YELLOW_FILL = PatternFill("solid", fgColor="FFF2CC")
GREEN_FILL = PatternFill("solid", fgColor="C6E0B4")
GRAY_FILL = PatternFill("solid", fgColor="E7E6E6")
thin = Side(border_style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)

tier_colors = {
    1: RED_FILL,
    2: ORANGE_FILL,
    3: YELLOW_FILL,
    4: GREEN_FILL,
    5: GRAY_FILL,
}

ws["A1"] = "Superior Water & Air — Internal Redirects Action Plan"
ws["A1"].font = TITLE_FONT
ws.merge_cells("A1:G1")

tier_counts = df["tier"].value_counts().sort_index()
total_pages_linking = df["Pages Linking To It"].sum()

ws["A2"] = (
    f"66 redirects | 1,322 internal links pointing to redirects | "
    f"Tiered by impact: 2 critical hubs (418 links), 17 city pages (510 links), "
    f"47 lower-priority legacy URLs"
)
ws["A2"].font = SUBTITLE_FONT
ws.merge_cells("A2:G2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 28

# ==========================================================================
# Executive summary
# ==========================================================================
ws.cell(row=4, column=1, value="WHAT TO DO — PLAIN ENGLISH").fill = SECTION_FILL
ws.cell(row=4, column=1).font = Font(
    name="Calibri", size=11, bold=True, color="1F4E78"
)
ws.merge_cells("A4:G4")
ws.row_dimensions[4].height = 22

summary_lines = [
    ("The real problem",
     "Your site has 1,322 internal links pointing to URLs that redirect. Most of those "
     "redirects dump visitors on the homepage instead of a relevant page. Google treats "
     "these as weak signals — it diverts link equity away from pages that should rank, "
     "and confuses crawlers about your site structure."),
    ("The 3 fixes that matter",
     "1) Fix /water/ and /hvac/ — these are supposed to be service category hubs but "
     "they redirect to the homepage. 418 links on your site are wasted because of this."
     "\n2) Fix the 17 city plumbing URLs — old city landing pages like /plumbing-salt-"
     "lake-city-ut/ all redirect to the homepage. 510 internal links lose their local "
     "signal."
     "\n3) Update internal anchors to point to /contact/ instead of /contact — 208 "
     "links have the wrong trailing slash."),
    ("Everything else (47 URLs)",
     "Lower-priority legacy blog/service URLs. Some already redirect to good "
     "destinations (keep as-is). Others redirect to homepage from old blog posts — "
     "update those to point to topically-relevant pages. Can batch in a second sweep."),
    ("Priority by impact",
     f"Tier 1 ({int(tier_counts.get(1, 0))} URLs, 418 links affected) → do first. "
     f"Tier 2 ({int(tier_counts.get(2, 0))} URLs, 210 links) → quick wins. "
     f"Tier 3 ({int(tier_counts.get(3, 0))} URLs, ~590 links) → batch. "
     f"Tier 4 ({int(tier_counts.get(4, 0))} URLs) → already OK. "
     f"Tier 5 ({int(tier_counts.get(5, 0))} URLs, low impact) → batch last."),
]

for r_off, (k, v) in enumerate(summary_lines):
    r = 5 + r_off
    c1 = ws.cell(row=r, column=1, value=k)
    c1.font = BOLD_FONT
    c1.alignment = LEFT
    c1.border = BORDER
    c2 = ws.cell(row=r, column=2, value=v)
    c2.font = CELL_FONT
    c2.alignment = LEFT
    c2.border = BORDER
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=7)
    ws.row_dimensions[r].height = 85

# ==========================================================================
# Tier 1 — Category Hubs
# ==========================================================================
t1_start = 5 + len(summary_lines) + 2
ws.cell(row=t1_start, column=1,
         value="TIER 1 — CATEGORY HUBS (critical, fix first)").fill = RED_FILL
ws.cell(row=t1_start, column=1).font = Font(
    name="Calibri", size=12, bold=True, color="9C0006"
)
ws.merge_cells(start_row=t1_start, start_column=1, end_row=t1_start, end_column=7)
ws.row_dimensions[t1_start].height = 22

t1_intro = t1_start + 1
ws.cell(row=t1_intro, column=1,
         value=("These 2 URLs should BE service category hub pages, but they "
                "301-redirect to the homepage. Result: 418 internal links across "
                "your site point to what Google sees as 'just the homepage' instead "
                "of a rich service category. This is the single biggest internal "
                "linking / site architecture issue.")).font = CELL_FONT
ws.cell(row=t1_intro, column=1).alignment = LEFT
ws.merge_cells(start_row=t1_intro, start_column=1,
                end_row=t1_intro, end_column=7)
ws.row_dimensions[t1_intro].height = 50

t1_header_row = t1_intro + 2
headers_main = ["#", "Redirecting URL", "Current Destination",
                "Pages Linking", "Issue", "Recommended Fix", "Status"]
for col, h in enumerate(headers_main, 1):
    c = ws.cell(row=t1_header_row, column=col, value=h)
    c.fill = HEADER_FILL
    c.font = HEADER_FONT
    c.alignment = CENTER
    c.border = BORDER
ws.row_dimensions[t1_header_row].height = 34

t1_df = df[df["tier"] == 1].reset_index(drop=True)
for i, row in t1_df.iterrows():
    r = t1_header_row + 1 + i
    values = [
        i + 1,
        row["Redirecting URL"],
        row["Final Destination"],
        int(row["Pages Linking To It"]),
        row["issue"],
        row["suggested_dest"],
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = CELL_FONT_SM if col in (2, 3, 5, 6) else CELL_FONT
        c.border = BORDER
        c.alignment = CENTER if col in (1, 4, 7) else LEFT
        if col == 4 and isinstance(v, int) and v >= 100:
            c.fill = RED_FILL
    ws.row_dimensions[r].height = 100


# ==========================================================================
# Tier 2 — Trailing slash
# ==========================================================================
def write_tier_section(ws, start_row, tier_num, title, intro_text, tier_df,
                        headers_list, header_fill=HEADER_FILL):
    """Helper to write a tier section. Returns end_row."""
    tier_color = tier_colors.get(tier_num, GRAY_FILL)
    ws.cell(row=start_row, column=1, value=title).fill = tier_color
    ws.cell(row=start_row, column=1).font = Font(
        name="Calibri", size=12, bold=True
    )
    ws.merge_cells(start_row=start_row, start_column=1,
                    end_row=start_row, end_column=7)
    ws.row_dimensions[start_row].height = 22

    intro_row = start_row + 1
    ws.cell(row=intro_row, column=1, value=intro_text).font = CELL_FONT
    ws.cell(row=intro_row, column=1).alignment = LEFT
    ws.merge_cells(start_row=intro_row, start_column=1,
                    end_row=intro_row, end_column=7)
    ws.row_dimensions[intro_row].height = 42

    header_row = intro_row + 2
    for col, h in enumerate(headers_list, 1):
        c = ws.cell(row=header_row, column=col, value=h)
        c.fill = header_fill
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER
    ws.row_dimensions[header_row].height = 34

    for i, row in tier_df.iterrows():
        r = header_row + 1 + i
        values = [
            i + 1,
            row["Redirecting URL"],
            row["Final Destination"],
            int(row["Pages Linking To It"]),
            row["issue"],
            row["suggested_dest"],
            "Not Started",
        ]
        for col, v in enumerate(values, 1):
            c = ws.cell(row=r, column=col, value=v)
            c.font = CELL_FONT_SM if col in (2, 3, 5, 6) else CELL_FONT
            c.border = BORDER
            c.alignment = CENTER if col in (1, 4, 7) else LEFT
            if col == 4 and isinstance(v, int) and v >= 100:
                c.fill = RED_FILL
            elif col == 4 and isinstance(v, int) and v >= 20:
                c.fill = YELLOW_FILL
        ws.row_dimensions[r].height = 72

    return header_row + len(tier_df)


t2_start = t1_header_row + len(t1_df) + 3
t2_df = df[df["tier"] == 2].reset_index(drop=True)
t2_end = write_tier_section(
    ws, t2_start, 2,
    "TIER 2 — TRAILING SLASH FIXES (easy wins)",
    ("208 internal links point to /contact without trailing slash. Trivial "
     "fix: bulk-update anchors OR accept the 301 (low-impact, adds ~50ms to "
     "each click but doesn't hurt rankings meaningfully)."),
    t2_df, headers_main,
)

t3_start = t2_end + 3
t3_df = df[df["tier"] == 3].reset_index(drop=True)
t3_end = write_tier_section(
    ws, t3_start, 3,
    f"TIER 3 — CITY PAGES + REMAPS ({len(t3_df)} URLs, ~590 links affected)",
    ("Old city plumbing URLs (/plumbing-salt-lake-city-ut/ etc.) 301 to "
     "homepage. Each has 30 internal links. Net effect: ~510 links pass "
     "through homepage instead of signaling local relevance. Fix by "
     "remapping 301s to topically-relevant service or city pages."),
    t3_df, headers_main,
)

t4_start = t3_end + 3
t4_df = df[df["tier"] == 4].reset_index(drop=True)
t4_end = write_tier_section(
    ws, t4_start, 4,
    f"TIER 4 — ALREADY REASONABLE ({len(t4_df)} URLs)",
    ("These already redirect to topically-aligned pages, not homepage. "
     "Optional cleanup: update internal anchors to point to the destination "
     "directly (removes the 301 hop). Not urgent."),
    t4_df, headers_main,
)

t5_start = t4_end + 3
t5_df = df[df["tier"] == 5].reset_index(drop=True)
t5_end = write_tier_section(
    ws, t5_start, 5,
    f"TIER 5 — OLD BLOG → HOMEPAGE ({len(t5_df)} URLs, low impact)",
    ("Old blog post URLs that 301 to homepage. Each has 1-3 internal "
     "links. Fix in a batch after higher tiers. For each: check if a "
     "current topically-relevant page exists and remap, otherwise "
     "leave homepage as fallback."),
    t5_df, headers_main,
)


# Column widths
widths = {
    "A": 4, "B": 50, "C": 50, "D": 12, "E": 55, "F": 60, "G": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

ws.freeze_panes = "C5"


# ==========================================================================
# Sheet 2 — How to Execute
# ==========================================================================
ws2 = wb.create_sheet("How to Execute")
ws2["A1"] = "Implementation Steps"
ws2["A1"].font = TITLE_FONT
ws2.merge_cells("A1:B1")

steps = [
    ("", ""),
    ("=== TIER 1 — CATEGORY HUBS ===", ""),
    ("Decision 1: Restore /water/ and /hvac/ as real pages",
     "Best long-term fix. Create actual category hub pages listing water "
     "services (water treatment, water softeners, water heaters) and HVAC "
     "services (heating, cooling, duct cleaning). This captures the 418 "
     "internal links AS value instead of leaking them."),
    ("Decision 2 (if decision 1 isn't possible): Remap the 301",
     "Option A: 301 /water/ → /plumbing-services/ (closest topical hub). "
     "Option B: 301 /water/ → the strongest existing water-related page. "
     "Same for /hvac/ → /home-cooling/ or /furnace-heating-guide-repair-"
     "installation/."),
    ("Decision 3 (do this regardless): Audit internal anchors",
     "Even if you fix the destination, go through top-linking pages and "
     "update anchor text. If a page links to /water/ with 'Water Services' "
     "as anchor, check that the actual destination still matches that "
     "anchor text."),
    ("", ""),
    ("=== TIER 2 — TRAILING SLASH ===", ""),
    ("Bulk anchor update",
     "In WP admin: search database for '/contact' without trailing slash. "
     "Tools: WP search-replace plugins (Better Search Replace), or run a "
     "wp-cli command against the database. Replace with '/contact/'. "
     "Test on staging first."),
    ("Alternative: accept the 301",
     "208 pages with a single 301 hop is not a ranking killer. If "
     "database search-replace feels risky, leave it and move on."),
    ("", ""),
    ("=== TIER 3 — CITY PAGES ===", ""),
    ("17 city plumbing URLs",
     "For each /plumbing-[city]-ut/ URL: decide whether to restore the "
     "city page (best for local SEO — see separate City Landing Pages "
     "work if applicable) OR 301 to /plumbing-services/ (adequate) instead "
     "of homepage (poor fit). Hosting provider / Rank Math / Redirection "
     "plugin can update the 301 destinations in bulk."),
    ("Service remaps (e.g., /pipe-lining/, /water-heaters/tankless-...)",
     "Per-URL review. Each old legacy URL should 301 to the most "
     "topically-aligned current page. Refer to the 'Recommended Fix' "
     "column in the main plan for each URL."),
    ("", ""),
    ("=== TIER 4 — LEAVE OR POLISH ===", ""),
    ("Update linking pages",
     "For these URLs, destination is already correct. Optional: find the "
     "pages that still link to the old URL and update those anchors to "
     "point to the destination directly. Saves the 301 hop and improves "
     "crawl efficiency."),
    ("", ""),
    ("=== TIER 5 — OLD BLOG POSTS ===", ""),
    ("Batch review",
     "Export list. For each: look at the slug to infer the topic. If a "
     "current page (blog post or service page) exists on the same topic, "
     "remap the 301. Otherwise, leave as-is."),
    ("", ""),
    ("=== WHERE TO MAKE CHANGES ===", ""),
    ("WordPress redirects",
     "Most likely managed via Rank Math → Dashboard → Redirections, OR "
     "Redirection plugin → Redirects, OR .htaccess rules. Check all three."),
    ("Verification after changes",
     "1) Re-crawl with Screaming Frog — redirect count should drop. "
     "2) GSC → Coverage → verify none of the fixed URLs show crawl errors. "
     "3) Spot-check 5-10 random fixed URLs in the browser."),
    ("", ""),
    ("=== EXPECTED IMPACT ===", ""),
    ("After Tier 1",
     "418 previously-homepage-bound internal links now pass relevance to "
     "proper service hubs. Expect positive signal for /water-treatment/, "
     "/water-softeners/, /heating/, /cooling/ type pages over 4-8 weeks."),
    ("After Tier 3",
     "17 city pages stop being 'ghost URLs that redirect to homepage.' "
     "510 internal links get local-intent signal back. Modest but real "
     "improvement on city-specific plumbing queries."),
    ("Overall",
     "1,322 internal links currently pointing to redirects → target is "
     "under 50 after cleanup. Crawl efficiency improves, and internal "
     "PageRank flows to the right destinations."),
]

for r, (k, v) in enumerate(steps, 2):
    c1 = ws2.cell(row=r, column=1, value=k)
    c2 = ws2.cell(row=r, column=2, value=v)
    if k.startswith("==="):
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    elif k and not v:
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    else:
        c1.font = BOLD_FONT
        c2.font = CELL_FONT
        c2.alignment = Alignment(wrap_text=True, vertical="top")

ws2.column_dimensions["A"].width = 45
ws2.column_dimensions["B"].width = 105
for r in range(2, 2 + len(steps)):
    ws2.row_dimensions[r].height = 42


wb.save(out)
print(f"Saved: {out}")
print()
print(f"Tier breakdown ({len(df)} total redirects, "
      f"{int(df['Pages Linking To It'].sum())} affected internal links):")
for t in sorted(df["tier"].unique()):
    sub = df[df["tier"] == t]
    print(f"  Tier {t}: {len(sub)} URLs, "
          f"{int(sub['Pages Linking To It'].sum())} internal links")
