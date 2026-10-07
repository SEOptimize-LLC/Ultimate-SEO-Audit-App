"""Fill tab 1.6 (sections A, B, C and the SOV header) for any client.

    python scripts/fill_1_6_all.py beehive 2026-10
    python scripts/fill_1_6_all.py all 2026-10

October 2026 template (task numbers moved when 2.3/2.4/3.1/2.5 merged into 2.3):
old 3.4 Mentions is now 3.3, so section B's last column reads "Routed to 3.3 (Y)"
(it read "Routed to 3.4 (Y)" through September). This engine leaves that column
BLANK on purpose: Y means a person read the row and decided it is a mention
target, and a Y from a rule would be a judgment field filled by lookup
(REASONING.md). Section B's header has five columns in the October template
(Money Prompt | Competitor Present | Third-Party Page AI Cites | Opportunity /
Next Step | Routed to 3.3 (Y)); September workbooks had only the first three.
This engine writes the CURRENT month only, so it targets the October layout only
and refuses to write anything if a header does not match (see preflight).

The SOV summary lives in B4:B6 (the template's yellow input cells; the 4.5 report
reads B4 and B5 and concatenates them as text, so B holds a short text value such
as "20% (9 of 46)", never a bare percentage, which would concatenate as 0.2).
Detail sits beside it in C4:C6. September workbooks held a long sentence in D4:D6.

Generalisation of the EW-specific fill_1_6.py / fill_1_6_bc.py pair. EW's tab is
already filled by those; this engine covers every active client in the registry
(`all` is read from clients/registry.yaml, so an `active: false` client with no
sheet_id is skipped). Everything the EW build learned is carried here:

- SOV counts CATEGORY prompts only. Branded prompts return the brand nearly
  every time by construction; folding them in turned 9% into 25% on EW.
- Report per platform, never blended (EW: ChatGPT 4% vs Gemini 24%).
- A vendor name missing from the map is INVISIBLE, not absent (Observe4Success
  appeared 9 times while being reported as zero). Maps below are curated from
  scans of the actual answers, and generous: an absent token costs nothing.
- Vendor tokens match on WORD BOUNDARIES ("app" matched inside "appreciation").

New in this engine, and why: on the local home-services clients ChatGPT answers
"who does X in Salt Lake City" with a MAP of business listings, not prose. The
competitors are in the record's `business_locations`, and brand presence in that
listing block is real visibility even when the prose never says the name. So
mention = answer text OR listing, and the Notes say which. Beehive appears in
SameDay's listings as a competitor, which only this path can see.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io as S  # noqa: E402

TAB = "1.6 AI Visibility SOV"
TRACKED = ("chatgpt", "google_ai_mode", "perplexity")   # tab columns F, H, I
VALID_INTENT = {"Discovery", "Comparison", "Best-X", "Decision"}
MONEY_INTENT = {"Best-X", "Decision"}

# October 2026 template headers. check_layout compares them case- and
# whitespace-insensitively, so line breaks inside a header cell do not matter.
HEADER_A = ["#", "Sourced From (Top Ranking Query)", "Impressions & Avg Position",
            "Prompt", "Intent", "ChatGPT", "Prominence", "AIO / AI Mode",
            "Perplexity", "Competitors Named", "Our URLs Cited",
            "Third-Party URLs Cited", "Notes"]
HEADER_B = ["Money Prompt", "Competitor Present", "Third-Party Page AI Cites",
            "Opportunity / Next Step", "Routed to 3.3 (Y)"]
HEADER_C = ["Prompt", "Why stale", "Roger decision"]
# Row labels of the three SOV summary cells; the value cell is column B.
SOV_LABELS = {"sov": "SOV this month", "sov_prev": "SOV last month",
              "run": "Prompts run"}


def preflight(sid: str) -> dict[str, int]:
    """Locate every anchor and verify every header BEFORE the first write.

    The old flow found its anchors after section A was already written, so a
    missing heading died with StopIteration halfway through a tab (the
    2026-09 repair_1_6_sections.py incident). Everything is checked up front
    here, and any mismatch raises with the tab name, the row and what was
    found. Nothing is guessed.
    """
    a = S.find_rows(sid, TAB, {**SOV_LABELS, "a_hdr": "#", "b": "B.",
                               "b_hdr": "Money Prompt", "c": "C. Prompt-set"},
                    scan_to=160)
    if not a["a_hdr"] < a["b"] < a["b_hdr"] < a["c"]:
        raise RuntimeError(f"{TAB}: sections out of order {a}")
    for key, expected, last_col, row in (
            ("a_hdr", HEADER_A, "M", a["a_hdr"]),
            ("b_hdr", HEADER_B, "E", a["b_hdr"]),
            ("c_hdr", HEADER_C, "C", a["c"] + 1)):
        chk = S.check_layout(sid, f"'{TAB}'!A{row}:{last_col}{row}", expected)
        if not chk.ok:
            raise RuntimeError(
                f"{TAB} header at row {row} does not match the October "
                f"template. expected {chk.expected} found {chk.found}. "
                f"Nothing was written.")
        a[key] = row
    return a


def rx(*parts):
    return [re.compile(p) for p in parts]


# Per-client brand detection. Bare tokens collide with ordinary words, so each
# regex is written against the collision seen or feared: "snow" is weather,
# "superior" is an adjective, "same day" is the generic service phrase,
# "arsenal" is a football club, "comfort solutions" can be generic HVAC prose.
BRAND = {
    "beehive": rx(r"(?i)beehive\s+plumbing|beehiveplumbing"),
    "sameday": rx(r"SameDay\b", r"(?i)sameday\s*(utah|heating)|samedayutah"),
    "superior": rx(r"(?i)superior\s+water"),
    "comfort": rx(r"Comfort\s+Solutions", r"(?i)comfortsolutionsutah"),
    "cudio": rx(r"(?i)\bcudio\b"),
    "snow": rx(r"\bSNOW\b", r"(?i)snow\s+teeth\s+whitening|trysnow",
               r"(?i)snow\s+(whitening|magic|wand|advanced|diamond)\b"),
    "arsenal": rx(r"(?i)arsenal\s+health"),
    "educationwalkthrough": rx(r"(?i)education\s*walk\s*through|educationwalkthrough"),
    # "bart" alone is a given name and collides with Bartley, a nearby paving
    # contractor that already appears in this client's own GSC queries.
    # The apostrophe class includes the typographic one: Google AI Mode wrote "Bart’s Asphalt" with U+2019
    # and the plain-quote pattern missed a real mention, so September's SOV was one prompt short.
    "barts": rx(r"(?i)bart['’‘ʼ]?s\s+asphalt|bartsasphalt"),
}

# Competitor vendor maps: display name -> word-boundary token. Curated from
# capitalized-phrase scans and business_locations of THIS month's answers, plus
# the large local franchises worth watching even at zero. Generous on purpose.
VENDORS = {
 "beehive": {
  "Roto-Rooter": "roto-?rooter", "Mr. Rooter": "mr\\.?\\s*rooter",
  "Tom-Plumber": "tom-?plumber", "Monkey Wrench Plumbing": "monkey\\s*wrench",
  "Salt Lake Plumbing": "salt\\s*lake\\s*plumbing",
  "Valley Plumbing": "valley\\s*plumbing", "PlumbWorks": "plumbworks",
  "Whipple": "whipple", "Any Hour Services": "any\\s*hour",
  "Neerings": "neerings", "Manwill": "manwill",
  "Black Diamond": "black\\s*diamond", "Just Right Plumbing": "just\\s*right\\s*plumbing",
  "Towers Plumbing": "towers\\s*plumbing", "Action Plumbing": "action\\s*plumbing",
 },
 "sameday": {
  "Beehive Plumbing": "beehive\\s*plumbing", "Roto-Rooter": "roto-?rooter",
  "Whipple": "whipple", "Any Hour Services": "any\\s*hour",
  "Utah Heating and Cooling": "utah\\s*heating\\s*and\\s*cooling",
  "GeltenPro": "geltenpro", "Huish": "huish",
  "Elevation Plumbing": "elevation\\s*plumbing",
  "Just Right Plumbing": "just\\s*right\\s*plumbing",
  "S.O.S. Heating": "s\\.?o\\.?s\\.?\\s*heating", "True Pros": "true\\s*pros",
  "Western Heating": "western\\s*heating", "Absolute Air": "absolute\\s*air",
  "Black Diamond": "black\\s*diamond", "Manwill": "manwill",
  "Triple-T": "triple-?t",
 },
 "superior": {
  "Culligan": "culligan", "Kinetico": "kinetico", "Fleck": "fleck",
  "RainSoft": "rainsoft", "EcoWater": "ecowater", "Aquasana": "aquasana",
  "SpringWell": "springwell", "Nuvia Water": "nuvia",
  "Guardian Soft Water": "guardian\\s*soft\\s*water",
  "Whipple": "whipple", "Any Hour Services": "any\\s*hour",
  "Beehive Plumbing": "beehive\\s*plumbing", "Roto-Rooter": "roto-?rooter",
  "Manwill": "manwill", "Black Diamond": "black\\s*diamond",
 },
 "comfort": {
  "Whipple": "whipple", "Any Hour Services": "any\\s*hour",
  "Absolute Air": "absolute\\s*air", "Manwill": "manwill",
  "Black Diamond": "black\\s*diamond", "Triple-T": "triple-?t",
  "One Hour Heating": "one\\s*hour\\s*heating", "Lee's Heating": "lee'?s\\s*heating",
  "ESCO": "\\besco\\b", "Utah Heating and Cooling": "utah\\s*heating\\s*and\\s*cooling",
  "S.O.S. Heating": "s\\.?o\\.?s\\.?\\s*heating", "Huish": "huish",
  "Western Heating": "western\\s*heating", "Beehive Plumbing": "beehive\\s*plumbing",
 },
 "cudio": {
  "NetSuite": "netsuite", "Microsoft Dynamics": "microsoft\\s*dynamics|dynamics\\s*365",
  "ERPNext": "erpnext", "QuickBooks": "quickbooks", "Acumatica": "acumatica",
  "Zoho": "\\bzoho\\b", "SAP": "\\bsap\\b",
  # "sage" is an English word ("sage advice" appears in ERP prose), so the
  # token requires a product context rather than the bare name.
  "Sage": "sage\\s*(intacct|50|100|300|x3|erp|accounting|business\\s*cloud)",
  "Epicor": "epicor", "Infor": "\\binfor\\b", "Novobi": "novobi",
  "Captivea": "captivea", "Bista Solutions": "bista", "Brainvire": "brainvire",
  "Ksolves": "ksolves",
 },
 "snow": {
  "Crest": "\\bcrest\\b", "Colgate": "colgate", "Opalescence": "opalescence",
  "Oral-B": "oral-?b", "Philips Sonicare": "sonicare", "Philips Zoom": "philips\\s*zoom",
  "Auraglow": "auraglow", "Lumineux": "lumineux", "Hismile": "hismile",
  "Zimba": "zimba", "GLO Science": "glo\\s*science", "Burst": "\\bburst\\b",
 },
 "educationwalkthrough": {
  "TeachBoost": "teachboost", "Frontline": "frontline",
  "iObservation": "iobservation", "Classroom Mosaic": r"classroom\s*mosaic",
  "Observation Copilot": r"observation\s*copilot", "KickUp": "kickup",
  "2gno.me": "2gno", "SchoolStatus": "schoolstatus", "PowerSchool": "powerschool",
  "Whetstone": "whetstone", "EvalScribe": "evalscribe",
  "Education Advanced": r"education\s*advanced", "Swivl": "swivl",
  "Observe4Success": r"observe\s*4\s*success|observe4success",
  "Standard for Success": r"standard\s*for\s*success", "Teachscape": "teachscape",
 },
 "arsenal": {
  "F45": "\\bf45\\b", "Orangetheory": "orange\\s*theory|orangetheory",
  "CrossFit": "crossfit", "Life Time": "life\\s*time\\s*fitness|lifetime\\s*fitness",
  "Barry's": "barry'?s", "Restore Hyper Wellness": "restore\\s*hyper",
  "VASA Fitness": "\\bvasa\\b", "Chuze Fitness": "chuze",
  "Anytime Fitness": "anytime\\s*fitness", "Planet Fitness": "planet\\s*fitness",
  "EoS Fitness": "\\beos\\s*fitness", "24 Hour Fitness": "24\\s*hour\\s*fitness",
  "CorePower": "corepower", "TruFusion": "trufusion",
 },
 "barts": {
  "McKearney Asphalt": r"mckearney",
  "American Asphalt": r"american\s*asphalt",
  "Michigan Paving": r"michigan\s*paving",
  "Allied Asphalt": r"allied\s*asphalt",
  "T Burke's Paving": r"t\.?\s*burke'?s?|burke'?s?\s*paving",
  "Asphalt Solutions Plus": r"asphalt\s*solutions\s*plus",
  "CK Paving": r"\bck\s*paving",
  "Mullins Asphalt": r"mullins",
  "Belson Asphalt Paving": r"belson",
  "Cornstubbles Asphalt": r"cornstubble",
  "Mike & Son Asphalt": r"mike\s*(and|&)\s*son",
 },
}


def brand_hit(slug: str, text: str) -> bool:
    return any(r.search(text) for r in BRAND[slug])


def domain(u: str) -> str:
    m = re.match(r"https?://([^/]+)", str(u))
    return m.group(1).replace("www.", "") if m else ""


def vendor_hits(slug: str, text: str) -> list[str]:
    out = []
    for name, tok in VENDORS[slug].items():
        if re.search(r"(?<![a-z0-9])(?:" + tok + r")(?![a-z0-9])", text, re.I):
            out.append(name)
    return out


def listing_names(rec: dict) -> list[str]:
    out = []
    for v in (rec.get("business_locations") or []):
        if isinstance(v, dict):
            n = v.get("name") or v.get("title")
            if n:
                out.append(str(n))
    return out


def prominence(slug: str, answer: str) -> str:
    """Distinct competitors named before the brand's first mention."""
    first = None
    for r in BRAND[slug]:
        m = r.search(answer)
        if m and (first is None or m.start() < first):
            first = m.start()
    if first is None:
        return "-"
    before = 0
    for name, tok in VENDORS[slug].items():
        m = re.search(r"(?<![a-z0-9])(?:" + tok + r")(?![a-z0-9])", answer, re.I)
        if m and m.start() < first:
            before += 1
    return {0: "1st", 1: "2nd"}.get(before, "3rd+")


def load(slug: str, stamp: str):
    doc = yaml.safe_load(Path(f"clients/prompts/{slug}.yaml").read_text(encoding="utf-8"))
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    d = Path(reg[slug]["folder"]) / "ai_visibility"
    data = {}
    for p in TRACKED:
        f = d / f"{stamp}-{p}.json"
        if f.exists():
            recs = json.load(open(f, encoding="utf-8"))
            data[p] = {str(r.get("prompt")): r for r in recs if isinstance(r, dict)}
    return doc, reg[slug], data


def analyse(slug: str, doc, data):
    """Per-prompt rollup across the tracked platforms."""
    out = []
    for p in doc["prompts"]:
        q = p["prompt"]
        seen, via_map, comps, ours, third = {}, [], Counter(), [], Counter()
        prom = "-"
        for plat in TRACKED:
            r = (data.get(plat) or {}).get(q)
            if not r:
                seen[plat] = ""
                continue
            a = str(r.get("answer_text") or "")
            names = listing_names(r)
            in_text = brand_hit(slug, a)
            in_listing = any(brand_hit(slug, n) for n in names)
            seen[plat] = "Y" if (in_text or in_listing) else "N"
            if in_listing and not in_text:
                via_map.append(plat)
            for name in vendor_hits(slug, a):
                comps[name] += 1
            for n in names:
                if not brand_hit(slug, n):
                    comps[n] += 1
            for c in (r.get("citations") or []):
                u = str(c.get("url", ""))
                if brand_hit(slug, u) or domain(u) == doc.get("own_domain", "\x00"):
                    if u not in ours:
                        ours.append(u)
                elif domain(u):
                    third[domain(u)] += 1
            if prom == "-":
                pr = prominence(slug, a)
                if pr != "-":
                    prom = pr
        intent = p.get("intent") if p.get("intent") in VALID_INTENT else "Decision"
        out.append({"p": p, "q": q, "intent": intent, "seen": seen, "prom": prom,
                    "via_map": via_map, "comps": comps, "ours": ours, "third": third})
    return out


def prior_sov(slug: str, doc, cfg, stamp: str, plats=TRACKED):
    """Category SOV recomputed from LAST month's stored records, or None.

    The raw platform JSONs are the durable record; the sheet is a monthly copy.
    So last month's figure is recomputed from disk rather than read from a cell
    that may live in a different workbook copy. Computed over the platforms THIS month
    actually ran (`plats`), so a month that skipped a platform is not compared against a
    month that had it. Computed over the CURRENT prompt
    set, so if a prompt was swapped between months the comparison covers only
    the prompts both months actually ran; the count in the note says how many.
    """
    d = Path(cfg["folder"]) / "ai_visibility"
    stamps = sorted({f.name.rsplit("-", 1)[0] for f in d.glob("*-*.json")
                     if f.name.rsplit("-", 1)[0] < stamp})
    if not stamps:
        return None
    prev = stamps[-1]
    cat = {p["prompt"] for p in doc["prompts"] if p["kind"] == "category"}
    hits = n = 0
    for plat in plats:
        f = d / f"{prev}-{plat}.json"
        if not f.exists():
            continue
        for r in json.load(open(f, encoding="utf-8")):
            if not isinstance(r, dict) or str(r.get("prompt")) not in cat:
                continue
            n += 1
            a = str(r.get("answer_text") or "")
            if brand_hit(slug, a) or any(brand_hit(slug, x) for x in listing_names(r)):
                hits += 1
    return (prev, 100.0 * hits / n, n) if n else None


def sov_summary(sov_h: int, sov_n: int, plats: list[str], ncat: int,
                bpct: float, prior, mom_text: str, n_prompts: int,
                miss_txt: str) -> list[list[str]]:
    """The three [value, detail] rows for B4:C6 (this month, last month, run).

    Column B is the value, and the 4.5 report reads B4 and B5 and joins them
    as text. It is deliberately text: "20%" typed into a USER_ENTERED cell
    becomes the number 0.2, and 4.5 would print "0.3 -> 0.2". "20% (9 of 46)"
    cannot parse as a number. Column C holds the supporting detail.
    """
    pct = 100.0 * sov_h / sov_n if sov_n else 0.0
    if prior is None:
        prev_value = "baseline month"
    else:
        prev_hits = round(prior[1] * prior[2] / 100.0)
        prev_value = f"{prior[1]:.0f}% ({prev_hits} of {prior[2]})"
    return [
        [f"{pct:.0f}% ({sov_h} of {sov_n})",
         S.compose(("Basis", [f"{sov_h} of {sov_n} checks across {', '.join(plats)}, {ncat} non-branded prompts.",
                              f"Branded prompts run separately at {bpct:.0f}% and are excluded here."]),
                   where="1.6 SOV basis")],
        [prev_value, S.compose(("Change vs last month", mom_text), where="1.6 SOV change")],
        [f"{n_prompts} of {n_prompts}", S.compose(("Coverage", miss_txt.strip()), where="1.6 coverage")]]


def fill(slug: str, stamp: str):
    doc, cfg, data = load(slug, stamp)
    sid = cfg.get("sheet_id")
    if not sid:
        print(f"{slug:<10} no current-month workbook (active: false in the "
              f"registry), skipped")
        return
    # own citations detected by domain as well as brand text
    doc["own_domain"] = cfg["domain"].replace("www.", "")
    anchors = preflight(sid)          # raises before any write if the layout moved
    rows = analyse(slug, doc, data)

    plats_present = [p for p in TRACKED if data.get(p)]
    missing = [p for p in TRACKED if not data.get(p)]

    # ---------------- section A ----------------
    body, sov_h, sov_n, br_h, br_n = [], 0, 0, 0, 0
    for i, r in enumerate(rows, 1):
        p = r["p"]
        vals = [r["seen"].get(k) for k in TRACKED if r["seen"].get(k)]
        if p["kind"] == "category":
            sov_n += len(vals)
            sov_h += sum(1 for v in vals if v == "Y")
        elif p["kind"] == "branded":
            br_n += len(vals)
            br_h += sum(1 for v in vals if v == "Y")
        note = []
        if p["kind"] == "branded":
            note.append("Branded. Excluded from the SOV figure so it cannot "
                        "inflate the category number.")
        if r["via_map"]:
            note.append("Present via ChatGPT's local business listing, not the "
                        "prose, on: " + ", ".join(r["via_map"]) + ". A map slot "
                        "is real visibility; the answer text never says the name.")
        if p["kind"] == "category" and vals and all(v == "N" for v in vals):
            top = ", ".join(n for n, _ in r["comps"].most_common(3))
            note.append(f"Absent on all {len(vals)} platforms queried." +
                        (f" Named instead: {top}." if top else ""))
        if r["ours"]:
            note.append(f"{len(r['ours'])} of our URLs cited here.")
        body.append([
            i, p["source_query"],
            (f"{p['impressions']:,} impr / pos {p['position']}"
             if p["impressions"] else "n/a (brand or competitor prompt)"),
            r["q"], r["intent"],
            r["seen"].get("chatgpt", ""), r["prom"],
            r["seen"].get("google_ai_mode", ""), r["seen"].get("perplexity", ""),
            ", ".join(f"{n} ({c})" for n, c in r["comps"].most_common(5)) or "none named",
            "\n".join(r["ours"][:3]) or "none",
            ", ".join(f"{d} ({c})" for d, c in r["third"].most_common(4)) or "none",
            S.compose(("Notes", note), where=f"1.6 prompt {i}"),
        ])

    colA = S.read(sid, f"'{TAB}'!A1:A140")
    hdr = next(i for i, rr in enumerate(colA, 1) if rr and str(rr[0]).strip() == "#")
    first, have = hdr + 1, 0
    for rr in colA[hdr:]:
        if rr and str(rr[0]).strip().startswith("B."):
            break
        have += 1
    if len(body) > have:
        S.insert_rows(sid, TAB, first + have, len(body) - have)
    cells = S.write(sid, f"'{TAB}'!A{first}:M{first+len(body)-1}", body).cells

    pct = 100.0 * sov_h / sov_n if sov_n else 0.0
    bpct = 100.0 * br_h / br_n if br_n else 0.0
    ncat = sum(1 for r in rows if r["p"]["kind"] == "category")
    prior = prior_sov(slug, doc, cfg, stamp, plats_present)
    if prior is None:
        mom_text = ("Baseline month, nothing to compare against yet. From next "
                    "month, treat a move under 12 points as noise, not movement.")
    else:
        prev, ppct, pn = prior
        delta = pct - ppct
        # The noise floor is a HARD reporting rule, not advisory: at ~75
        # observations a swing under 12 points is indistinguishable from the
        # models' own run-to-run variation, and reporting it as movement is the
        # statistical version of the fabricated-claim failure.
        verdict = ("no measurable change (under the 12-point noise floor)"
                   if abs(delta) < 12 else
                   ("REAL movement, above the noise floor" ))
        mom_text = (f"{prev}: {ppct:.0f}% ({pn} checks, recomputed from the "
                    f"stored records over the current prompt set). Delta "
                    f"{delta:+.0f} points: {verdict}.")
    miss_txt = ("" if not missing else
                f" NOT RUN: {', '.join(missing)}. That column is empty, not zero.")
    # A platform can return FEWER records than prompts sent, which the file-level
    # check above cannot see: the file exists, it is simply thin. The SOV maths
    # already ignores a prompt a platform never answered, so the figure is not
    # wrong - but a reader told "across chatgpt, google_ai_mode, perplexity"
    # reasonably assumes all three answered everything. State the denominator.
    partial = {pl: sum(1 for r in rows if r["seen"].get(pl))
               for pl in plats_present}
    partial = {pl: c for pl, c in partial.items() if c < len(rows)}
    if partial:
        miss_txt += (" PARTIAL COVERAGE: "
                     + "; ".join(f"{pl} answered {c} of {len(rows)} prompts"
                                 for pl, c in sorted(partial.items()))
                     + ". Those prompts count for no platform they were not "
                       "answered on, so that column rests on a smaller sample "
                       "than the others.")
    # AI Mode answers collected through a different vendor than last month's are not like for like.
    ai_mode_src = {str(r.get("source", "")) for r in (data.get("google_ai_mode") or {}).values()}
    if "dataforseo" in ai_mode_src:
        miss_txt += (" METHOD CHANGE: Google AI Mode answers were collected with a different method this "
                     "month, so its change against last month is indicative, not like for like.")
    summary = sov_summary(sov_h, sov_n, plats_present, ncat, bpct, prior,
                          mom_text, len(body), miss_txt)
    for key, vals in zip(("sov", "sov_prev", "run"), summary):
        S.write(sid, f"'{TAB}'!B{anchors[key]}:C{anchors[key]}", [vals])

    # ---------------- section B ----------------
    money = [r for r in rows
             if r["p"]["kind"] == "category" and r["intent"] in MONEY_INTENT]
    money.sort(key=lambda r: (sum(1 for v in r["seen"].values() if v == "Y"),
                              -r["p"]["impressions"]))
    brows = []
    for r in money[:7]:
        hit_on = [p for p in TRACKED if r["seen"].get(p) == "Y"]
        comps = ", ".join(f"{n} ({c})" for n, c in r["comps"].most_common(4)) or "none"
        pages = [u for u, _ in r["third"].most_common(3)]
        if hit_on:
            step = (f"Present on {', '.join(hit_on)} but absent on the rest. "
                    f"Narrow gap: reinforce the pages the models already cite "
                    f"rather than writing net-new content.")
        elif r["ours"]:
            step = ("Absent from the answer while our own pages ARE cited as "
                    "sources for it. Positioning problem on a page already being "
                    "read, not a coverage gap.")
        else:
            lead = r["comps"].most_common(1)
            step = ("Absent everywhere and none of our pages cited. Nearest "
                    "route in is the third-party pages listed, which the "
                    "assistants already read for this question"
                    + (f"; displacing {lead[0][0]} head-on is the slow path."
                       if lead else "."))
        # Last cell is "Routed to 3.3 (Y)": blank by design. A person decides
        # which cited pages become mention targets, never a rule.
        brows.append([r["q"], comps, "\n".join(pages) or "none cited",
                      S.compose(("Next step", step), where=f"1.6 gap {r['q'][:30]}"), ""])
    colA = S.read(sid, f"'{TAB}'!A1:A160")
    b_first = next(i for i, rr in enumerate(colA, 1)
                   if rr and str(rr[0]).strip().startswith("Money Prompt")) + 1
    n_b = S.write(sid, f"'{TAB}'!A{b_first}:E{b_first+len(brows)-1}", brows).cells if brows else 0

    # ---------------- section C ----------------
    crows = []
    for r in rows:
        p = r["p"]
        if (p["kind"] == "competitor" and not r["comps"]
                and not any(v == "Y" for v in r["seen"].values())):
            crows.append([r["q"], S.compose(("Why stale", [
                "No competitor from this client's map appeared in any response to it this month.",
                "Either the framing misses how buyers ask, or the map lacks the names the models actually use.",
                "Check before keeping."]), where="1.6 section C"), ""])
        elif (p["kind"] == "category" and p.get("position") and p["position"] > 40
                and not any(v == "Y" for v in r["seen"].values())):
            crows.append([r["q"], S.compose(("Why stale", [
                f"Sourced from a query ranking at position {p['position']} and absent from every platform.",
                "Candidate to swap for a stronger vendor-intent prompt."]), where="1.6 section C"), ""])
    c_first = next(i for i, rr in enumerate(colA, 1)
                   if rr and str(rr[0]).strip().startswith("C. Prompt-set")) + 2
    n_c = S.write(sid, f"'{TAB}'!A{c_first}:C{c_first+len(crows)-1}", crows).cells if crows else 0

    print(f"{slug:<10} A:{len(body)} rows ({cells} cells)  SOV {pct:.1f}%  "
          f"brand {bpct:.0f}%  B:{len(brows)}  C:{len(crows)}"
          f"{'  MISSING: ' + ','.join(missing) if missing else ''}")


def active_slugs(reg: dict) -> list[str]:
    """Registry clients with a current-month workbook and a prompt set.

    Reading the registry is what keeps `all` honest: a hardcoded list went stale
    twice (Bart's was missing from it, and Arsenal and Snow stay on it after
    going inactive). An `active: false` client has no sheet_id by design.
    """
    return [k for k, v in reg.items()
            if isinstance(v, dict) and v.get("sheet_id")
            and Path(f"clients/prompts/{k}.yaml").exists()]


if __name__ == "__main__":
    if len(sys.argv) != 3 or not re.fullmatch(r"\d{4}-\d{2}", sys.argv[2]):
        raise SystemExit("usage: fill_1_6_all.py <client|all> <YYYY-MM>")
    registry = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    slugs = active_slugs(registry) if sys.argv[1] == "all" else [sys.argv[1]]
    for s in slugs:
        try:
            fill(s, sys.argv[2])
        except Exception as e:
            print(f"{s:<10} FAILED {e.__class__.__name__}: {e}")
