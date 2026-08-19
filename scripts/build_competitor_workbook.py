"""Build the competitor content analysis workbook.

Matches the house format used across all IHS competitor content analyses:

    Start Here | Content Gap Table | Benchmark | What Google Returns |
    Competitor Structure Matrix | How to Read the Matrix | Excluded |
    Decision Needed | Section Outlines

Reads competitor_matrix.csv and pages/*.json from the extraction step, plus a
hand-authored workbook_content.json holding the gap table, headline findings,
search results and decisions.

Usage:
    python scripts/build_competitor_workbook.py --dir <analysis_dir> [--open]
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

NAVY = "1F3864"
LIGHT = "D9E2F3"
BAND = "F2F5FB"
GREEN, GREEN_TX = "C6EFCE", "006100"
RED, RED_TX = "FFC7CE", "9C0006"
AMBER, AMBER_TX = "FFEB9C", "9C6500"
GREY_TX = "595959"

HDR_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

SISTER_DOMAINS = {
    "beehiveplumbing.com": "IHS property",
    "comfortsolutionsutah.com": "IHS property",
    "samedayutah.com": "IHS property",
    "superiorwaterandair.com": "IHS property",
}
DIRECTORIES = {
    "yelp.com": "Directory", "angi.com": "Directory",
    "thumbtack.com": "Directory", "homeadvisor.com": "Directory",
    "bbb.org": "Directory", "houzz.com": "Directory",
    "nextdoor.com": "Directory", "downtobid.com": "Directory",
}


def header(ws, row: int, labels: list[str], widths: list[int]) -> None:
    for i, label in enumerate(labels, start=1):
        c = ws.cell(row=row, column=i, value=label)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.font = HDR_FONT
        c.alignment = Alignment(horizontal="center", vertical="center",
                                wrap_text=True)
        c.border = BORDER
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[row].height = 32
    ws.freeze_panes = f"A{row+1}"
    ws.auto_filter.ref = f"A{row}:{get_column_letter(len(labels))}{row}"


def put(ws, r: int, c: int, v, *, wrap=True, align="left", bold=False,
        fill=None, color=None, size=10):
    cell = ws.cell(row=r, column=c, value=v)
    cell.alignment = Alignment(horizontal=align, vertical="top", wrap_text=wrap)
    cell.border = BORDER
    cell.font = Font(size=size, bold=bold, color=color or "000000")
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    return cell


def verdict_style(text: str):
    t = str(text).upper()
    if "MAIN PROBLEM" in t or t.startswith("GAP"):
        return RED, RED_TX
    if "STRENGTH" in t:
        return GREEN, GREEN_TX
    if "OPPORTUNITY" in t:
        return AMBER, AMBER_TX
    return None, None


PRIORITY_STYLE = {"P0": (RED, RED_TX), "P1": (AMBER, AMBER_TX),
                  "P2": (LIGHT, NAVY), "P3": ("EDEDED", GREY_TX)}


def sheet_start_here(wb, meta: dict, comp_n: int) -> None:
    ws = wb.create_sheet("Start Here")
    ws.column_dimensions["A"].width = 2
    ws.column_dimensions["B"].width = 132
    r = 1
    c = ws.cell(row=r, column=2,
                value=f"{meta['client']}: {meta['service']} Content Analysis")
    c.font = Font(bold=True, size=16, color=NAVY)
    r += 2
    for line in [f"The page reviewed: {meta['page_reviewed']}",
                 f"Market: {meta['city']}          "
                 f"Data collected: {meta['data_collected']}"]:
        ws.cell(row=r, column=2, value=line).font = Font(size=10, color=GREY_TX)
        r += 1
    r += 1

    def block(title: str, lines: list[str], numbered=False):
        nonlocal r
        ws.cell(row=r, column=2, value=title).font = Font(bold=True, size=12,
                                                          color=NAVY)
        r += 1
        for i, ln in enumerate(lines, start=1):
            txt = f"{i}. {ln}" if numbered else ln
            cell = ws.cell(row=r, column=2, value=txt)
            cell.font = Font(size=10)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[r].height = max(15, 13 * (len(txt) // 118 + 1))
            r += 1
        r += 1

    block("What this is, in one sentence", [
        f"We looked at the {comp_n} independent businesses winning the searches "
        f"{meta['short_client']} wants to win, recorded how their pages are "
        f"written and structured, and compared {meta['short_client']}'s page "
        f"against them.",
        "This workbook covers CONTENT only: what is written on the page, how it "
        "is structured, and how it is described to Google. Page design, layout "
        "and conversion behaviour are handled separately.",
        "This analysis never treats another IHS property as a competitor. All "
        "four are excluded from every figure. See the Excluded sheet.",
    ])
    block("What we found, in plain terms", meta["headline_findings"],
          numbered=True)
    block("How to use this workbook", [
        "Content Gap Table  -  every issue found. Each row says what the issue "
        "is, what it actually means, why it matters, what competitors do, what "
        "this page does today, and what to do about it.",
        "Benchmark  -  every measure we took, what the typical competitor "
        "scores, what this page scores, and whether that is a problem.",
        "What Google Returns  -  what Google actually shows for each search, "
        "and where this page sits in it.",
        "Competitor Structure Matrix  -  the raw record for every page examined.",
        "How to Read the Matrix  -  what each column in that raw record means.",
        "Excluded  -  every website deliberately left out, and why.",
        "Section Outlines  -  how every page divides its content, section by "
        "section, with the length of each.",
    ])
    block("What this analysis cannot tell you", meta["cannot_tell_you"])


def sheet_gap_table(wb, meta: dict) -> None:
    ws = wb.create_sheet("Content Gap Table")
    labels = ["#", "Issue", "What this actually means", "Why it matters",
              "What competitors do", "What the client's page does today",
              "What to do about it", "Priority", "Effort", "Expected outcome",
              "How to confirm it is fixed"]
    widths = [4, 40, 58, 52, 46, 52, 46, 9, 20, 20, 62]
    header(ws, 1, labels, widths)
    r = 2
    for i, g in enumerate(meta["gaps"], start=1):
        put(ws, r, 1, i, align="center", wrap=False, bold=True)
        put(ws, r, 2, g["issue"], bold=True)
        put(ws, r, 3, g["means"])
        put(ws, r, 4, g["why"])
        put(ws, r, 5, g["competitors"])
        put(ws, r, 6, g["client_today"])
        put(ws, r, 7, g["action"])
        fill, tx = PRIORITY_STYLE.get(g["priority"], (None, None))
        put(ws, r, 8, g["priority"], align="center", wrap=False, bold=True,
            fill=fill, color=tx, size=11)
        put(ws, r, 9, g["effort"])
        oc = g["outcome"]
        of = GREEN if "Ranking Lever" in oc else ("EDEDED" if
                                                  "Hygiene" in oc or
                                                  "Risk" in oc else None)
        ot = GREEN_TX if "Ranking Lever" in oc else (GREY_TX if of else None)
        put(ws, r, 10, oc, bold="Ranking Lever" in oc, fill=of, color=ot)
        put(ws, r, 11, g["confirm"])
        ws.row_dimensions[r].height = 118
        r += 1


def sheet_benchmark(wb, meta: dict, df: pd.DataFrame, comp: pd.DataFrame,
                    ours) -> None:
    ws = wb.create_sheet("Benchmark")
    name = meta["short_client"]
    labels = ["What we measured", "What it means", "Typical competitor", name,
              "Verdict"]
    header(ws, 1, labels, [34, 62, 22, 26, 40])

    def med(col):
        v = comp[col].median()
        return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"

    def cnt(col):
        return f"{int(comp[col].sum())} of {len(comp)}"

    rows = [
        ("Word count", "How much writing is on the page.",
         med("word_count"), f"{int(ours['word_count']):,}"),
        ("Major sections (H2)", "How many big sections the page is divided into.",
         med("h2_count"), int(ours["h2_count"])),
        ("Subsections (H3)", "Sections within sections.",
         med("h3_count"), int(ours["h3_count"])),
        ("Sub-subsections (H4)", "The level below that.",
         med("h4_count"), int(ours["h4_count"])),
        ("Tappable phone numbers", "How easy it is to call from the page.",
         med("tel_link_count"), int(ours["tel_link_count"])),
        ("Links to other pages on the site",
         "How well the page connects to the rest of the website.",
         med("internal_links"), int(ours["internal_links"])),
        ("Images", "Photographs or diagrams in the body of the page.",
         med("images"), int(ours["images"])),
        ("Title length",
         "Characters in the headline Google shows. Over roughly 60 gets cut off.",
         med("title_len"), int(ours["title_len"])),
        ("City named in the Google headline",
         "Whether the city appears in the headline Google displays.",
         cnt("city_in_title"), "Yes" if ours["city_in_title"] else "No"),
        ("City named in the page headline",
         "Whether the city appears in the page's own main headline.",
         cnt("city_in_h1"), "Yes" if ours["city_in_h1"] else "No"),
        ("Names local conditions or housing stock",
         "How often the page names something specific to this market: its "
         "water, geology, altitude or housing stock. Generic winter wording "
         "is deliberately not counted.",
         med("local_condition_mentions"),
         int(ours["local_condition_mentions"])),
        ("Shows a price", "Whether any actual price figure appears.",
         cnt("price_mentions") if False else
         f"{int((comp['price_mentions'] > 0).sum())} of {len(comp)}",
         "Yes" if ours["price_mentions"] > 0 else "No"),
        ("Has a questions section",
         "Whether the page carries a visible questions and answers block.",
         cnt("faq_present"), "Yes" if ours["faq_present"] else "No"),
        ("Questions marked up for Google",
         "Whether that block is declared in code Google reads directly.",
         cnt("schema_has_faqpage"),
         "Yes" if ours["schema_has_faqpage"] else "No"),
        ("Star rating marked up for Google",
         "Whether the review score is declared in code.",
         cnt("schema_has_aggregaterating"),
         "Yes" if ours["schema_has_aggregaterating"] else "No"),
        ("Service type marked up", "Whether the service offered is declared.",
         cnt("schema_has_service"), "Yes" if ours["schema_has_service"] else "No"),
        ("Business details marked up",
         "Whether name, address and phone are declared.",
         cnt("schema_has_localbusiness"),
         "Yes" if ours["schema_has_localbusiness"] else "No"),
        ("Total markup types on the page",
         "How many kinds of structured data the page declares in total.",
         med("schema_type_count"), int(ours["schema_type_count"])),
        ("Mentions 24/7 or emergency",
         "Whether the page states round-the-clock availability.",
         cnt("mentions_emergency_247"),
         "Yes" if ours["mentions_emergency_247"] else "No"),
        ("Offers a free estimate", "Whether a no-cost quote is offered.",
         cnt("mentions_free_estimate"),
         "Yes" if ours["mentions_free_estimate"] else "No"),
    ]

    r = 2
    for label, means, typical, mine in rows:
        verdict = _verdict(label, typical, mine)
        put(ws, r, 1, label, bold=True)
        put(ws, r, 2, means, color=GREY_TX)
        put(ws, r, 3, typical, align="center")
        put(ws, r, 4, mine, align="center", bold=True)
        f, t = verdict_style(verdict)
        put(ws, r, 5, verdict, bold=bool(f), fill=f, color=t)
        ws.row_dimensions[r].height = 30
        r += 1


def _verdict(label: str, typical, mine) -> str:
    """Plain-language verdict comparing our value against the field."""
    if isinstance(mine, str) and mine in ("Yes", "No"):
        have, total = (int(x) for x in str(typical).split(" of "))
        if mine == "Yes":
            if have == 0:
                return "STRENGTH, nobody else does this"
            if have < total / 2:
                return "STRENGTH, most competitors do not"
            return "Fine"
        # we do not do it
        if have == 0:
            return "Nobody does this, opportunity"
        if have < total / 2:
            return f"GAP, {have} of {total} competitors do"
        return "GAP"
    try:
        m = float(str(mine).replace(",", ""))
        t = float(str(typical).replace(",", ""))
    except ValueError:
        return ""
    if label == "Title length":
        return "Fine" if m <= 62 else "GAP, will be cut off"
    # Small-numbers guard. A ratio on tiny counts is noise, not a finding:
    # 1 against a median of 0.5 is not a strength, it means nobody is doing it.
    if m < 3 and t < 3:
        return "Whole field is weak here, opportunity"
    if t == 0:
        return "STRENGTH, above typical" if m > 0 else "Fine"
    ratio = m / t
    if ratio >= 1.5:
        return "STRENGTH, well above typical"
    if ratio >= 0.9:
        return "Fine"
    if ratio >= 0.6:
        return "Below typical"
    return "GAP, well below typical"


def sheet_serp(wb, meta: dict) -> None:
    ws = wb.create_sheet("What Google Returns")
    name = meta["short_client"]
    labels = ["The search", f"Where {name} appears in normal results",
              f"Where {name} appears in the map box",
              "Best-placed independent business",
              "What Google actually returns for this search"]
    header(ws, 1, labels, [34, 34, 26, 32, 70])
    r = 2
    for s in meta["serp"]:
        put(ws, r, 1, s["search"], bold=True)
        put(ws, r, 2, s["organic"])
        put(ws, r, 3, s["map"], align="center")
        put(ws, r, 4, s["best_independent"])
        put(ws, r, 5, s["returns"])
        ws.row_dimensions[r].height = 58
        r += 1


def sheet_matrix(wb, df: pd.DataFrame) -> None:
    ws = wb.create_sheet("Competitor Structure Matrix")
    labels = ["Competitor", "Cohort", "Counted in the averages", "URL",
              "Where it ranks", "Google headline (title)", "Headline length",
              "Page headline", "City in Google headline", "City in page headline",
              "Word count", "Word count source", "Local condition mentions",
              "Major sections", "Subsections", "Sub-subsections",
              "Tappable phone numbers", "Forms", "Images", "Internal links",
              "Shows price", "Price samples", "Questions marked up",
              "Service marked up", "Business details marked up",
              "Star rating marked up", "All markup found on the page"]
    widths = [30, 16, 13, 54, 40, 50, 9, 44, 11, 11, 10, 15, 12, 10, 10, 12,
              12, 8, 8, 11, 9, 22, 12, 11, 13, 12, 62]
    header(ws, 1, labels, widths)

    r = 2
    for _, x in df.iterrows():
        role = str(x.get("role", ""))
        usable = x["word_count"] > 100 and role == "competitor"
        cohort = ("CLIENT-TARGET" if role == "client-target" else
                  "CLIENT-OTHER" if role.startswith("client") else
                  "CLIENT-SECOND-SITE" if "sibling" in role else "ORGANIC")
        yn = lambda v: "Yes" if bool(v) else "No"  # noqa: E731
        vals = [
            x["brand"], cohort, "TRUE" if usable else "FALSE", x["url"],
            x.get("serp_note", ""), x.get("title", ""), x.get("title_len", ""),
            x.get("h1", ""), yn(x.get("city_in_title")), yn(x.get("city_in_h1")),
            x.get("word_count", ""), x.get("word_count_source", ""),
            x.get("local_condition_mentions", ""), x.get("h2_count", ""),
            x.get("h3_count", ""), x.get("h4_count", ""),
            x.get("tel_link_count", ""), x.get("form_count", ""),
            x.get("images", ""), x.get("internal_links", ""),
            yn(x.get("price_mentions", 0) > 0), x.get("prices_found", ""),
            yn(x.get("schema_has_faqpage")), yn(x.get("schema_has_service")),
            yn(x.get("schema_has_localbusiness")),
            yn(x.get("schema_has_aggregaterating")), x.get("schema_types", ""),
        ]
        is_client = role.startswith("client")
        is_second = "sibling" in role
        for i, v in enumerate(vals, start=1):
            if pd.isna(v):
                v = ""
            fill = LIGHT if is_client else ("FFF2CC" if is_second else None)
            put(ws, r, i, v,
                align="center" if i in (2, 3, 7, 9, 10, 11, 13, 14, 15, 16,
                                        17, 18, 19, 20, 21, 23, 24, 25, 26)
                else "left",
                bold=is_client, fill=fill,
                color=NAVY if is_client else None)
        # green/red the four markup columns
        for col in (23, 24, 25, 26):
            cell = ws.cell(row=r, column=col)
            if cell.value == "Yes":
                cell.fill = PatternFill("solid", fgColor=GREEN)
                cell.font = Font(size=10, bold=True, color=GREEN_TX)
            elif cell.value == "No":
                cell.fill = PatternFill("solid", fgColor=RED)
                cell.font = Font(size=10, color=RED_TX)
        ws.row_dimensions[r].height = 42
        r += 1


def sheet_matrix_guide(wb) -> None:
    ws = wb.create_sheet("How to Read the Matrix")
    header(ws, 1, ["Column in the matrix", "What it tells you"], [36, 108])
    guide = [
        ("Cohort", "CLIENT-TARGET is the page under review. CLIENT-OTHER is "
                   "another page on the client's own site. CLIENT-SECOND-SITE "
                   "is a different website the client also owns. ORGANIC is an "
                   "independent competitor."),
        ("Counted in the averages",
         "TRUE means this page counted toward the typical-competitor figures on "
         "the Benchmark sheet. FALSE means it did not, either because it is the "
         "client's own page or because the site blocked measurement."),
        ("Where it ranks", "Position in the Salt Lake City search results, and "
                           "whether the page appears in the map box or Google's "
                           "AI answer."),
        ("Google headline (title)",
         "The headline Google displays in the result. Over roughly 60 "
         "characters it gets cut off mid-sentence."),
        ("Page headline", "The main heading on the page itself, which is a "
                          "different thing from the Google headline."),
        ("Word count", "Words of body text, after removing navigation, footer, "
                       "and site-wide blocks such as review carousels and blog "
                       "feeds that appear on every page of the site."),
        ("Word count source", "Whether the count came from the page file or "
                              "from opening the page in a real browser. Some "
                              "sites build their content in a way that only "
                              "appears once a browser runs the page."),
        ("Local condition mentions",
         "How many times the page refers to conditions that cause the problem "
         "locally, such as hard water, inversion, altitude or housing age. This "
         "separates a page written about somewhere from a page that could be "
         "published for any city by changing the name."),
        ("Forms", "How many enquiry forms are on the page."),
        ("Shows price / Price samples",
         "Whether any actual price figure appears, and which figures were found."),
        ("Questions / Service / Business details / Star rating marked up",
         "Whether each type of structured data is present. Green means yes, red "
         "means no. Structured data is code stating a fact in a form Google "
         "reads directly rather than having to infer."),
        ("All markup found on the page",
         "The complete list of structured data types found, for reference."),
    ]
    r = 2
    for a, b in guide:
        put(ws, r, 1, a, bold=True)
        put(ws, r, 2, b, color=GREY_TX)
        ws.row_dimensions[r].height = 46
        r += 1


def sheet_excluded(wb, df: pd.DataFrame, extra: list) -> None:
    ws = wb.create_sheet("Excluded")
    ws.cell(row=1, column=1,
            value="Websites deliberately left out of the comparison"
            ).font = Font(bold=True, size=13, color=NAVY)
    header(ws, 3, ["Website", "Type", "Why we left it out"], [34, 20, 92])
    r = 4
    own = {u.split("/")[2].replace("www.", "").lower()
           for u in df["url"].tolist()}
    for dom, kind in SISTER_DOMAINS.items():
        if dom in own:
            continue  # this run's own client
        put(ws, r, 1, dom)
        put(ws, r, 2, kind, align="center")
        put(ws, r, 3, "Part of the same group. Measuring one group property "
                      "against another would compare our own work and inflate "
                      "the field we claim to be benchmarked against.")
        ws.row_dimensions[r].height = 32
        r += 1
    for dom, kind in DIRECTORIES.items():
        put(ws, r, 1, dom)
        put(ws, r, 2, kind, align="center")
        put(ws, r, 3, "A directory or aggregator rather than a local business. "
                      "Recorded when counting what occupies the results page, "
                      "but not compared against as a competitor.")
        ws.row_dimensions[r].height = 32
        r += 1
    for e in extra:
        put(ws, r, 1, e["site"])
        put(ws, r, 2, e["type"], align="center")
        put(ws, r, 3, e["why"])
        ws.row_dimensions[r].height = 32
        r += 1


def sheet_decisions(wb, meta: dict) -> None:
    if not meta.get("decisions"):
        return
    ws = wb.create_sheet("Decision Needed")
    ws.cell(row=1, column=1, value="Decisions this analysis raises"
            ).font = Font(bold=True, size=13, color=NAVY)
    header(ws, 3, ["What needs deciding", "The situation", "Who decides"],
           [40, 96, 24])
    r = 4
    for d in meta["decisions"]:
        put(ws, r, 1, d["what"], bold=True)
        put(ws, r, 2, d["situation"])
        put(ws, r, 3, d["who"], align="center")
        ws.row_dimensions[r].height = 76
        r += 1


def sheet_sections(wb, d: Path) -> None:
    ws = wb.create_sheet("Section Outlines")
    header(ws, 1, ["Page", "Cohort", "Section", "Words",
                   "Counts as page copy"], [40, 20, 64, 9, 18])
    r = 2
    for f in sorted(glob.glob(str(d / "pages" / "*.json"))):
        page = json.loads(Path(f).read_text(encoding="utf-8"))
        role = str(page.get("role", ""))
        is_client = role.startswith("client")
        for s in page.get("sections", []):
            fill = LIGHT if is_client else None
            put(ws, r, 1, page.get("brand", ""), bold=is_client, fill=fill,
                color=NAVY if is_client else None)
            put(ws, r, 2, role, align="center", fill=fill)
            put(ws, r, 3, s["h2"], fill=fill)
            put(ws, r, 4, s["words"], align="center", fill=fill)
            v = "Yes" if s["is_copy"] else "No"
            put(ws, r, 5, v, align="center",
                fill=None if s["is_copy"] else AMBER,
                color=None if s["is_copy"] else AMBER_TX, bold=not s["is_copy"])
            r += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--open", action="store_true")
    a = ap.parse_args()
    d = Path(a.dir)

    meta = json.loads((d / "workbook_content.json").read_text(encoding="utf-8"))
    df = pd.read_csv(d / "competitor_matrix.csv")
    comp = df[(df.role == "competitor") & (df.word_count > 100)]
    ours = df[df.role == "client-target"].iloc[0]

    blocked = df[(df.role == "competitor") & (df.word_count <= 100)]
    extra = [{"site": r["url"].split("/")[2].replace("www.", ""),
              "type": "Blocked measurement",
              "why": "The site serves an empty file to automated requests, so no "
                     "reliable measurement was possible. Named in the report "
                     "where relevant but excluded from every average."}
             for _, r in blocked.iterrows()]
    seen: set[str] = set()
    deduped = []
    for e in extra:
        if e["site"] not in seen:
            seen.add(e["site"])
            deduped.append(e)
    extra = deduped

    wb = Workbook()
    wb.remove(wb.active)
    sheet_start_here(wb, meta, len(comp))
    sheet_gap_table(wb, meta)
    sheet_benchmark(wb, meta, df, comp, ours)
    sheet_serp(wb, meta)
    sheet_matrix(wb, df)
    sheet_matrix_guide(wb)
    sheet_excluded(wb, df, extra)
    sheet_decisions(wb, meta)
    sheet_sections(wb, d)

    name = (f"{meta['short_client']} - {meta['service']} "
            f"Competitor Content Analysis.xlsx")
    out = d / name
    wb.save(out)
    print(f"[saved] {out}")
    print(f"[sheets] {' | '.join(wb.sheetnames)}")
    print(f"[competitors counted] {len(comp)}   "
          f"[excluded for blocking] {len(extra)}")
    if a.open:
        os.startfile(str(out))  # noqa: S606
    return 0


if __name__ == "__main__":
    sys.exit(main())
