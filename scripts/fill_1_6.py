"""Fill tab 1.6 (AI Visibility SOV) from a completed AI visibility run.

SUPERSEDED 2026-08-18 by fill_1_6_all.py, which covers all eight clients in one
engine (this file was EW-only) and adds listings-based mention detection and
month-over-month. Kept because fill_1_6_bc.py imported from here during the
first build; do not run for new months.

    python scripts/fill_1_6.py educationwalkthrough 2026-08

Reads the raw platform JSON written by run_ai_visibility.py and the prompt set
that carries each prompt's GSC provenance. Every judgement cell is derived from
those records, never from a default.

The tab tracks ChatGPT, Google AI Mode and Perplexity. Gemini is run as well
because it is by far EW's strongest platform, but it has no column, so it is
reported in the Notes rather than silently folded into the SOV figure. Blending
it in would raise the headline number using a platform the tab does not claim to
measure.
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
# The three the tab has columns for, in column order F, H, I.
TRACKED = ("chatgpt", "google_ai_mode", "perplexity")

VENDORS = {
    "Education Walkthrough": "education walkthrough", "TeachBoost": "teachboost",
    "Frontline": "frontline", "iObservation": "iobservation",
    "Classroom Mosaic": "classroom mosaic", "Observation Copilot": "observation copilot",
    "KickUp": "kickup", "2gno.me": "2gno", "SchoolStatus": "schoolstatus",
    "PowerSchool": "powerschool", "Whetstone": "whetstone", "EvalScribe": "evalscribe",
    "Education Advanced": "education advanced", "Swivl": "swivl",
    # Absent from this dict on the first pass, which produced a false finding:
    # the run was reported as showing zero Observe4Success mentions when nothing
    # had ever looked for the string. It appears 9 times in 132 records. A name
    # missing from this map is invisible, not absent.
    "Observe4Success": "observe4success", "Observe 4 Success": "observe 4 success",
    "Standard for Success": "standard for success", "Teachscape": "teachscape",
}
BRAND_RE = re.compile(r"education\s*walk\s*through|educationwalkthrough", re.I)

# Superlative prompts get their own label on this tab, separate from Decision.
# A "best X" answer is a ranked list where being absent is a different failure
# from not being chosen once shortlisted.
INTENT = {
    "What is the best classroom walkthrough app for school districts?": "Best-X",
    "Best classroom observation software for K-12 administrators": "Best-X",
    "What software do schools use for teacher observations?": "Decision",
    "What tools do principals use to conduct learning walks?": "Decision",
    "What apps help school administrators track instruction?": "Decision",
    "What software supports OTES compliance for Ohio districts?": "Decision",
    "What are teacher evaluation systems and how do districts choose one?": "Comparison",
    "Danielson versus Marzano: which teacher evaluation framework should a district use?": "Comparison",
    "Is Education Walkthrough good for classroom observations?": "Decision",
    "How much does Education Walkthrough cost?": "Decision",
    "What do reviews say about Education Walkthrough?": "Decision",
    "Education Walkthrough versus Classroom Mosaic": "Comparison",
    "Classroom Mosaic alternatives": "Comparison",
    "Alternatives to Observe4Success": "Comparison",
    "Compare classroom walkthrough platforms for school districts": "Comparison",
}


def domain(u: str) -> str:
    m = re.match(r"https?://([^/]+)", str(u))
    return m.group(1).replace("www.", "") if m else ""


def prominence(answer: str) -> str:
    """Where the brand sits among the vendors named in one answer.

    Counts distinct competitors appearing before the brand's first mention.
    Being named last in a list of eight is not the same result as leading it,
    and a bare Y would report them identically.
    """
    a = answer.lower()
    i = a.find("education walkthrough")
    if i < 0:
        return "-"
    before = {n for n, tok in VENDORS.items()
              if n != "Education Walkthrough" and 0 <= a.find(tok) < i}
    return {0: "1st", 1: "2nd"}.get(len(before), "3rd+")


def load(client: str, stamp: str):
    doc = yaml.safe_load(
        Path(f"clients/prompts/{client}.yaml").read_text(encoding="utf-8"))
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    d = Path(reg[client]["folder"]) / "ai_visibility"
    data = {}
    for p in list(TRACKED) + ["gemini"]:
        f = d / f"{stamp}-{p}.json"
        if f.exists():
            recs = json.load(open(f, encoding="utf-8"))
            data[p] = {str(r.get("prompt")): r for r in recs if isinstance(r, dict)}
    return doc, reg[client], data


def build(doc, data):
    rows, sov_hits, sov_n = [], 0, 0
    brand_hits, brand_n = [0], [0]
    for i, p in enumerate(doc["prompts"], 1):
        q = p["prompt"]
        seen, comps, ours, third, prom = {}, Counter(), [], Counter(), "-"
        for plat in list(TRACKED) + ["gemini"]:
            r = (data.get(plat) or {}).get(q)
            if not r:
                seen[plat] = ""
                continue
            a = str(r.get("answer_text") or "")
            hit = bool(BRAND_RE.search(a))
            seen[plat] = "Y" if hit else "N"
            for name, tok in VENDORS.items():
                if name != "Education Walkthrough" and tok in a.lower():
                    comps[name] += 1
            for c in (r.get("citations") or []):
                u = str(c.get("url", ""))
                if BRAND_RE.search(u):
                    if u not in ours:
                        ours.append(u)
                elif domain(u):
                    third[domain(u)] += 1
            if plat in TRACKED and prom == "-":
                pr = prominence(a)
                if pr != "-":
                    prom = pr
        tracked_vals = [seen.get(k) for k in TRACKED if seen.get(k)]
        if p["kind"] == "category":
            sov_n += len(tracked_vals)
            sov_hits += sum(1 for v in tracked_vals if v == "Y")
        elif p["kind"] == "branded":
            brand_n[0] += len(tracked_vals)
            brand_hits[0] += sum(1 for v in tracked_vals if v == "Y")

        gem = seen.get("gemini", "")
        note = []
        if p["kind"] == "branded":
            note.append("Branded. Excluded from the SOV figure so it cannot "
                        "inflate the category number.")
        if gem:
            note.append(f"Gemini (untracked column): {gem}.")
        if p["kind"] == "category" and all(
                seen.get(k) == "N" for k in TRACKED if seen.get(k)):
            top = ", ".join(n for n, _ in comps.most_common(3))
            note.append(f"Absent on all three tracked platforms. Named instead: "
                        f"{top}." if top else "Absent on all three tracked platforms.")
        if ours:
            note.append(f"{len(ours)} of our URLs cited here.")
        rows.append([
            i, p["source_query"],
            (f"{p['impressions']:,} impr / pos {p['position']}"
             if p["impressions"] else "n/a (brand or competitor prompt)"),
            q, INTENT.get(q, "Discovery"),
            seen.get("chatgpt", ""), prom,
            seen.get("google_ai_mode", ""), seen.get("perplexity", ""),
            ", ".join(f"{n} ({c})" for n, c in comps.most_common(5)) or "none named",
            "\n".join(ours[:3]) or "none",
            ", ".join(f"{d} ({c})" for d, c in third.most_common(4)) or "none",
            " ".join(note),
        ])
    return rows, sov_hits, sov_n, brand_hits[0], brand_n[0]


def main(client: str, stamp: str):
    doc, cfg, data = load(client, stamp)
    sid = cfg["sheet_id"]
    rows, hits, n, bhits, bn = build(doc, data)

    # Anchor on column A. find_rows only scans column A and the section A header
    # label ("Sourced from") lives in column B, so it never matches there.
    colA = S.read(sid, f"'{TAB}'!A1:A120")
    hdr = next(i for i, r in enumerate(colA, 1)
               if r and str(r[0]).strip() == "#")
    first = hdr + 1
    have = 0
    for r in colA[first - 1:]:
        if r and str(r[0]).strip().startswith("B."):
            break
        have += 1
    need = len(rows) - have
    if need > 0:
        S.insert_rows(sid, TAB, first + have, need)
        print(f"inserted {need} rows for section A")

    cells = S.write(sid, f"'{TAB}'!A{first}:M{first+len(rows)-1}", rows).cells
    pct = 100.0 * hits / n if n else 0.0
    bpct = 100.0 * bhits / bn if bn else 0.0
    S.write(sid, f"'{TAB}'!D4:D6", [
        [f"{pct:.0f}% category SOV ({hits} of {n} checks across ChatGPT, AI Mode "
         f"and Perplexity, 25 non-branded prompts). Branded prompts run "
         f"separately at {bpct:.0f}% and are excluded here so they cannot "
         f"inflate the figure."],
        ["Baseline month, nothing to compare against yet. From next month, treat "
         "a move under 12 points as noise, not movement."],
        [f"{len(rows)} of {len(rows)}"]])
    print(f"section A: {len(rows)} rows, {cells} cells | SOV {pct:.1f}%")
    return sid, first, len(rows)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
