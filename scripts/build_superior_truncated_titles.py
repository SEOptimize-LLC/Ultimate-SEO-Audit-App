"""Build Superior Water & Air truncated titles shortening plan.

181 pages with titles >60 chars. Root cause: every title has the bloated suffix
" - Salt Lake City, Utah | Superior Water & Air" (~50 chars). Removing this suffix
alone fixes most pages. Apply same framework rules as Comfort Solutions:
- Scope filter: skip PPC/archives/utility
- No modality ("Top", "Best", "Reliable", "Expert", "Premier", etc.)
- Brand suffix only where room + benefit
- City+service format for city pages
- Under 60 chars
"""
import pandas as pd
import re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = (r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/"
        r"Claude/Claude Code + VS Code/SEO/Projects/Projects/"
        r"Ultimate SEO Auditor/Clients/Superior/Full SEO Audit/")
out = base + "superior_truncated_titles_plan.xlsx"

df = pd.read_excel(base + "truncated_titles.xlsx")


UTAH_CITIES = {
    "salt-lake-city", "sandy", "ogden", "orem", "lehi", "provo", "park-city",
    "draper", "sugarhouse", "west-jordan", "south-jordan", "layton",
    "davis-county", "tooele", "magna", "riverton", "murray", "bountiful",
    "farmington", "alpine", "centerville", "clearfield", "west-valley",
    "saratoga-springs", "american-fork", "cottonwood-heights", "holladay",
    "midvale", "south-salt-lake", "north-salt-lake", "herriman", "roy",
}

SERVICE_HUBS = {
    "home-cooling", "air-conditioning", "heating", "plumbing",
    "plumbing-services", "water-heaters", "water-softeners",
    "water-treatment", "emergency-services", "furnace", "hvac",
    "duct-cleaning", "drain-cleaning", "generators",
}


def classify(url: str) -> str:
    u = url.lower()
    path = re.sub(r"^https?://[^/]+", "", u)
    segments = [s for s in path.split("/") if s]
    slug = segments[-1] if segments else ""

    if any(x in u for x in ["/coupons/", "/specials/"]):
        return "Coupon/Specials"
    if any(x in u for x in ["/testimonials/", "/reviews/"]):
        return "Testimonials/Reviews"
    if any(x in u for x in ["/services-type/", "/category/", "/tag/"]):
        return "Archive"
    if "/page/" in u:
        return "Pagination"
    if "-ppc-" in u or "/ppc-" in u:
        return "PPC Landing"
    if any(x in u for x in ["/thank-you", "/privacy", "/terms", "/sitemap"]):
        return "Utility/Legal"
    if slug in ("faq", "faqs"):
        return "FAQ"

    for city in UTAH_CITIES:
        if city in slug:
            return "City Service Page"

    if slug in ("about", "about-us"):
        return "About"
    if slug == "contact":
        return "Contact"

    if len(segments) == 2 and segments[0] == "services":
        return "Services Hub"

    if len(segments) == 1 and segments[0] in SERVICE_HUBS:
        return "Top-Level Service Hub"

    if len(segments) >= 2 and segments[0] in (
        "water", "heating", "cooling", "plumbing", "hvac", "services"
    ):
        return "Nested Service Page"

    return "Blog Post"


df["Classification"] = df["Address"].apply(classify)

# Extract city from URL where present
def extract_city(url: str) -> str:
    u = url.lower()
    path = re.sub(r"^https?://[^/]+", "", u)
    segments = [s for s in path.split("/") if s]
    slug = segments[-1] if segments else ""
    for city in UTAH_CITIES:
        if city in slug:
            # Return title-cased city name
            return " ".join(w.capitalize() for w in city.split("-"))
    return ""


# Extract the "topic" from a blog-post slug (strip common filler words)
def blog_topic_from_slug(url: str, max_len: int = 55) -> str:
    u = url.lower()
    slug = u.rstrip("/").rsplit("/", 1)[-1]
    # Convert slug to title case
    words = slug.replace("_", "-").split("-")
    # Expand common abbreviations
    expansions = {"ac": "AC", "hvac": "HVAC"}
    out_words = []
    for w in words:
        out_words.append(expansions.get(w.lower(), w.capitalize()))
    title = " ".join(out_words)
    # Ensure it ends with a question mark if question words present
    question_starters = {"how", "what", "why", "when", "where", "who", "which", "does", "do", "is", "are", "can", "should"}
    first_word = out_words[0].lower() if out_words else ""
    if first_word in question_starters and not title.endswith("?"):
        title += "?"
    # Trim to max_len
    if len(title) > max_len:
        title = title[:max_len - 3].rstrip() + "..."
    return title


def clean_title_remove_junk(title: str) -> str:
    """Remove modality + redundant brand/city suffixes from current title."""
    MODALITY = (
        "top ", "best ", "reliable ", "expert ", "premier ", "trusted ",
        "leading ", "ultimate ", "amazing ", "professional ", "affordable ",
    )
    t = title
    # Strip trailing brand/city suffix patterns
    t = re.sub(r"\s*[-–|:]\s*Salt Lake City,?\s*Utah\s*[-–|:]*\s*Superior Water\s*&\s*Air.*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*[-–|:]\s*Superior Water\s*&\s*Air.*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*[-–|:]\s*Salt Lake City,?\s*Utah\s*$", "", t, flags=re.IGNORECASE)
    # Strip modality
    for m in MODALITY:
        t = re.sub(rf"^{re.escape(m)}", "", t, flags=re.IGNORECASE)
        t = re.sub(rf"\s+{re.escape(m)}", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def draft_title(row) -> tuple[str, str]:
    """Return (new_title, notes)."""
    classification = row["Classification"]
    current = row["Title 1"]
    url = row["Address"]

    if classification in ("PPC Landing",):
        return ("", "PPC page — do not rewrite. Add noindex via robots meta.")

    if classification in ("Archive", "Pagination", "Coupon/Specials",
                            "Testimonials/Reviews", "Utility/Legal"):
        return ("", f"{classification} — per scope filter, apply noindex instead of rewrite.")

    # Strip junk first
    cleaned = clean_title_remove_junk(current)

    BRAND_SUFFIX = " | Superior Water & Air"

    if classification == "Top-Level Service Hub":
        # Keep brand, city, tight format: "Service Name | Superior Water & Air"
        # Example: Heating Services in Salt Lake City | Superior Water & Air
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        service = " ".join(w.capitalize() for w in slug.split("-"))
        # Some service hubs already have well-named titles
        candidate = f"{service} in Salt Lake City{BRAND_SUFFIX}"
        if len(candidate) <= 60:
            return (candidate, "Hub: service + SLC + brand, all fit")
        candidate2 = f"{service} Services in SLC{BRAND_SUFFIX}"
        if len(candidate2) <= 60:
            return (candidate2, "Hub abbreviated SLC")
        return (f"{service} Services | Salt Lake City, UT", "Hub: dropped brand for fit")

    if classification == "City Service Page":
        city = extract_city(url)
        # Try to infer service from slug
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        # Remove city from slug
        city_slug = city.lower().replace(" ", "-")
        service_part = re.sub(rf"-?{re.escape(city_slug)}-?", "", slug).strip("-")
        service_part = re.sub(r"-?(utah|ut)-?", "", service_part).strip("-")
        # Fallback: use what remains
        if not service_part:
            # Use whatever topic we can extract from current title
            service_part = clean_title_remove_junk(current).split("|")[0].strip()
        else:
            service_part = " ".join(w.capitalize() for w in service_part.split("-"))
        # Try variants
        candidate = f"{service_part} in {city}, UT"
        if len(candidate) <= 60:
            return (candidate, "City page: service + city + UT")
        # Shortcut
        candidate2 = f"{service_part} {city}, UT"
        if len(candidate2) <= 60:
            return (candidate2, "City page: terser")
        # Fallback
        return (candidate[:57] + "...", "Trimmed to fit 60 chars")

    if classification == "Nested Service Page":
        # Strip current title's brand/city suffix; use cleaned
        if len(cleaned) <= 60:
            return (cleaned, "Used cleaned current title (suffix stripped)")
        # Trim
        return (cleaned[:57] + "...", "Trimmed nested service title")

    if classification == "About":
        return ("About Superior Water & Air", "About page: brand-first")

    if classification == "Contact":
        return ("Contact Superior Water & Air | Salt Lake City", "Contact page")

    # Blog Post — most common case. Two approaches:
    # (a) use cleaned current if it fits
    # (b) otherwise derive from slug
    if len(cleaned) <= 60 and cleaned:
        return (cleaned, "Blog: cleaned current title fits")
    slug_based = blog_topic_from_slug(url, max_len=57)
    if slug_based:
        return (slug_based, "Blog: derived from slug")
    return (cleaned[:57] + "..." if cleaned else "(manual review)",
            "Blog: trimmed cleaned title or manual")


# Run draft
drafts = df.apply(lambda r: pd.Series(draft_title(r), index=["new_title", "notes"]), axis=1)
df = pd.concat([df, drafts], axis=1)
df["new_length"] = df["new_title"].str.len()


# Determine action per row
def get_action(row):
    cls = row["Classification"]
    if cls == "PPC Landing":
        return "NOINDEX (not rewrite)"
    if cls in ("Archive", "Pagination", "Coupon/Specials",
                "Testimonials/Reviews", "Utility/Legal"):
        return "NOINDEX (not rewrite)"
    if not row["new_title"]:
        return "REVIEW"
    if row["new_length"] > 60:
        return "REWRITE (over 60 — manual polish needed)"
    return "REWRITE"


df["action"] = df.apply(get_action, axis=1)

# Sort: Service hub > Nested service > City page > Blog post > About > Contact > PPC
sort_order = {
    "Top-Level Service Hub":   0,
    "Services Hub":            1,
    "Nested Service Page":     2,
    "City Service Page":       3,
    "About":                   4,
    "Contact":                 5,
    "FAQ":                     6,
    "Blog Post":               7,
    "PPC Landing":             8,
}
df["_sort"] = df["Classification"].map(sort_order).fillna(9)
df["_title_len_sort"] = -df["Title 1 Length"]
df = df.sort_values(by=["_sort", "_title_len_sort", "Address"]).reset_index(drop=True)


# =========================================================================
# BUILD WORKBOOK
# =========================================================================
wb = Workbook()
ws = wb.active
ws.title = "Title Shortening Plan"

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
subtitle_font = Font(name="Calibri", size=10, italic=True, color="595959")
cell_font = Font(name="Calibri", size=10)
cell_font_small = Font(name="Calibri", size=9)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)
thin = Side(border_style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
red_fill = PatternFill("solid", fgColor="F8CBAD")
yellow_fill = PatternFill("solid", fgColor="FFF2CC")
green_fill = PatternFill("solid", fgColor="C6E0B4")
gray_fill = PatternFill("solid", fgColor="E7E6E6")
blue_fill = PatternFill("solid", fgColor="D9E1F2")

classification_colors = {
    "Top-Level Service Hub":   red_fill,
    "Services Hub":            red_fill,
    "Nested Service Page":     PatternFill("solid", fgColor="FFD9B3"),
    "City Service Page":       yellow_fill,
    "About":                   blue_fill,
    "Contact":                 blue_fill,
    "FAQ":                     blue_fill,
    "Blog Post":               green_fill,
    "PPC Landing":             gray_fill,
    "Archive":                 gray_fill,
    "Pagination":              gray_fill,
    "Coupon/Specials":         gray_fill,
    "Testimonials/Reviews":    gray_fill,
    "Utility/Legal":           gray_fill,
}

ws["A1"] = "Superior Water & Air — Truncated Titles Shortening Plan"
ws["A1"].font = title_font
ws.merge_cells("A1:I1")

rewrite_count = (df["action"].str.startswith("REWRITE")).sum()
noindex_count = (df["action"].str.startswith("NOINDEX")).sum()
ws["A2"] = (
    f"{len(df)} pages with titles >60 chars | "
    f"{rewrite_count} REWRITES + {noindex_count} NOINDEX (per scope filter) | "
    "All drafts strip redundant ' - Salt Lake City, Utah | Superior Water & Air' suffix + modality words"
)
ws["A2"].font = subtitle_font
ws.merge_cells("A2:I2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 28

headers = [
    "#", "URL", "Classification", "Current Title", "Curr Len",
    "Recommended Title", "New Len", "Action/Notes", "Status",
]
for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 36

for i, row in df.iterrows():
    r = i + 5
    values = [
        i + 1,
        row["Address"],
        row["Classification"],
        row["Title 1"],
        int(row["Title 1 Length"]),
        row["new_title"] if row["new_title"] else "",
        int(row["new_length"]) if row["new_length"] and row["new_length"] > 0 else "",
        (row["action"] + ": " + (row["notes"] or "")) if row["notes"] else row["action"],
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col in (4, 6, 8) else cell_font
        c.border = border
        if col in (1, 5, 7, 9):
            c.alignment = center
        else:
            c.alignment = left
        if col == 3:
            c.fill = classification_colors.get(row["Classification"], gray_fill)
            c.font = Font(name="Calibri", size=10, bold=True)
        if col == 5 and isinstance(v, int) and v > 70:
            c.fill = red_fill
        elif col == 5 and isinstance(v, int) and v > 60:
            c.fill = yellow_fill
        if col == 7 and isinstance(v, int):
            if v <= 60 and v > 0:
                c.fill = green_fill
            elif v > 60:
                c.fill = red_fill
        if col == 6 and v and row["new_length"] <= 60:
            c.fill = green_fill

widths = {
    "A": 4, "B": 55, "C": 22, "D": 60, "E": 9,
    "F": 52, "G": 9, "H": 55, "I": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w
for r in range(5, 5 + len(df)):
    ws.row_dimensions[r].height = 44
ws.freeze_panes = "C5"

# =========================================================================
# Sheet 2 — Summary + Standards
# =========================================================================
ws2 = wb.create_sheet("Summary & Standards")
ws2["A1"] = "Summary & Writing Standards"
ws2["A1"].font = title_font
ws2.merge_cells("A1:B1")

ctx = [
    ("", ""),
    ("=== THE PATTERN ===", ""),
    ("Total titles >60 chars", str(len(df))),
    ("Average current length", f"{int(df['Title 1 Length'].mean())} chars"),
    ("Longest current title", f"{int(df['Title 1 Length'].max())} chars"),
    ("Root cause",
     "Every title on the site appends ' - Salt Lake City, Utah | Superior Water & Air' "
     "(~50 chars). Remove this redundant suffix from blog posts + city pages; keep brand "
     "only on main service hubs where it fits."),
    ("", ""),
    ("=== ACTION BREAKDOWN ===", ""),
    ("REWRITE", f"{rewrite_count} titles"),
    ("NOINDEX (scope filter excludes)",
     f"{noindex_count} titles (PPC / archive / utility — no SEO value)"),
    ("", ""),
    ("=== CLASSIFICATION BREAKDOWN ===", ""),
    *[(cls, f"{count} titles")
      for cls, count in df["Classification"].value_counts().items()],
    ("", ""),
    ("=== WRITING STANDARDS APPLIED ===", ""),
    ("Max length", "60 characters (SERP desktop truncation point)"),
    ("No modality",
     "Removed: 'Top', 'Best', 'Reliable', 'Expert', 'Premier', 'Trusted', "
     "'Leading', 'Ultimate', 'Professional', 'Affordable'. Per semantic framework."),
    ("Brand treatment",
     "Keep '| Superior Water & Air' only on top-level service hubs (if room). "
     "Drop from blog posts + city pages + nested service pages."),
    ("City format",
     "City service pages use '<Service> in <City>, UT' format. Short, concrete, "
     "no modality."),
    ("Blog post format",
     "Use existing blog post topic, cleaned of city/brand suffix. If still too long, "
     "trim from the slug."),
    ("", ""),
    ("=== EXECUTION ORDER ===", ""),
    ("1. Top-level service hubs first (highest SEO leverage)",
     "Few pages, each drives a lot of traffic. Rewrite carefully."),
    ("2. City service pages",
     "Apply '<Service> in <City>, UT' template. ~51 pages."),
    ("3. Nested service pages", "~17 pages. Strip suffix, done."),
    ("4. Blog posts",
     "~107 pages. Bulk edit: strip suffix, check lengths. Use Rank Math bulk editor "
     "if available, otherwise per-page edit."),
    ("5. NOINDEX the scope-excluded URLs",
     "5 PPC pages — apply noindex via Rank Math post-type rule. Do NOT rewrite."),
    ("", ""),
    ("=== HOW TO IMPLEMENT IN WORDPRESS ===", ""),
    ("Per-page", "Rank Math meta box → SEO Title field → paste new title → Update."),
    ("Bulk (if Rank Math PRO)",
     "Rank Math → Dashboard → Bulk Actions → export to CSV → edit → reimport."),
    ("Verification",
     "After changes, inspect 5 sample URLs via 'View Source' — confirm <title> matches "
     "the new title. Re-crawl with Screaming Frog 2 weeks later to confirm 0 pages >60 chars."),
    ("", ""),
    ("=== EXPECTED OUTCOME ===", ""),
    ("SERP CTR", "~5-15% lift on impressions for 181 pages. Titles stop truncating."),
    ("Ranking",
     "Modality removal + keyword clarity may yield 1-3 position improvements over 4-8 "
     "weeks on head terms."),
]

for r, (k, v) in enumerate(ctx, 2):
    c1 = ws2.cell(row=r, column=1, value=k)
    c2 = ws2.cell(row=r, column=2, value=v)
    if k.startswith("==="):
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    elif k and not v:
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    else:
        c1.font = Font(name="Calibri", size=10, bold=True)
        c2.font = cell_font
        c2.alignment = Alignment(wrap_text=True, vertical="top")

ws2.column_dimensions["A"].width = 45
ws2.column_dimensions["B"].width = 110
for r in range(2, 2 + len(ctx)):
    ws2.row_dimensions[r].height = 34

wb.save(out)
print(f"Saved: {out}")
print(f"REWRITE: {rewrite_count} | NOINDEX: {noindex_count}")
print()
print("Classification:")
for cls, count in df["Classification"].value_counts().items():
    print(f"  {cls}: {count}")
