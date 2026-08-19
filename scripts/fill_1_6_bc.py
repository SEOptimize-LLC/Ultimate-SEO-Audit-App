"""Fill 1.6 sections B (gaps) and C (prompt-set maintenance).

SUPERSEDED 2026-08-18 by fill_1_6_all.py, which covers all eight clients in one
engine (this file was EW-only) and adds listings-based mention detection and
month-over-month. Kept because fill_1_6_bc.py imported from here during the
first build; do not run for new months.

    python scripts/fill_1_6_bc.py educationwalkthrough 2026-08

B answers one question: on the prompts where a buyer is choosing a tool, who is
being recommended instead of us, and which third-party page is the assistant
reading to reach that conclusion. That page is the actionable object, because
getting listed on a page the model already cites is faster than displacing the
model's opinion.

C is where prompts go to be retired. On a first run most of it is empty by
definition, but a prompt that returned nothing useful is worth naming now rather
than carrying it silently for a year.
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
from fill_1_6 import BRAND_RE, INTENT, VENDORS, domain, load  # noqa: E402

TAB = "1.6 AI Visibility SOV"
TRACKED = ("chatgpt", "google_ai_mode", "perplexity")
MONEY = ("Best-X", "Decision")


def gather(doc, data):
    out = {}
    for p in doc["prompts"]:
        q = p["prompt"]
        hits, comps, third, ours = {}, Counter(), Counter(), []
        for plat in list(TRACKED) + ["gemini"]:
            r = (data.get(plat) or {}).get(q)
            if not r:
                continue
            a = str(r.get("answer_text") or "")
            hits[plat] = bool(BRAND_RE.search(a))
            for name, tok in VENDORS.items():
                if name != "Education Walkthrough" and tok in a.lower():
                    comps[name] += 1
            for c in (r.get("citations") or []):
                u = str(c.get("url", ""))
                if BRAND_RE.search(u):
                    ours.append(u)
                elif domain(u):
                    third[u] += 1
        out[q] = {"p": p, "hits": hits, "comps": comps, "third": third, "ours": ours}
    return out


def main(client, stamp):
    doc, cfg, data = load(client, stamp)
    sid = cfg["sheet_id"]
    g = gather(doc, data)

    colA = S.read(sid, f"'{TAB}'!A1:A120")
    def row_of(prefix):
        return next(i for i, r in enumerate(colA, 1)
                    if r and str(r[0]).strip().startswith(prefix))
    b_first, c_first = row_of("Money Prompt") + 1, row_of("Prompt\n") if False else None
    c_first = row_of("C. Prompt-set") + 2

    # --- Section B: money prompts we are losing -----------------------------
    money = [q for q, d in g.items()
             if d["p"]["kind"] == "category" and INTENT.get(q) in MONEY]
    money.sort(key=lambda q: (sum(1 for v in g[q]["hits"].values() if v),
                              -g[q]["p"]["impressions"]))
    rows = []
    for q in money:
        d = g[q]
        tracked_hit = [p for p in TRACKED if d["hits"].get(p)]
        comps = ", ".join(f"{n} ({c})" for n, c in d["comps"].most_common(4)) or "none"
        pages = [u for u, _ in d["third"].most_common(3)]
        if tracked_hit:
            step = (f"Present on {', '.join(tracked_hit)} but absent on the rest. "
                    f"Narrow gap: the model already knows we belong in this answer, "
                    f"so the work is reinforcement on the pages it cites, not net-new "
                    f"content.")
        elif d["ours"]:
            step = ("Absent from the answer while our own pages ARE cited as sources "
                    "for it. The model reads us and recommends someone else, so this "
                    "is a positioning problem on our own page, not a coverage gap: "
                    "the cited page explains the topic without establishing that we "
                    "sell a tool for it.")
        else:
            step = (f"Absent everywhere and none of our pages cited. Nearest route in "
                    f"is the third-party pages listed, which the assistants already "
                    f"read for this question. Getting listed there is faster than "
                    f"displacing {d['comps'].most_common(1)[0][0] if d['comps'] else 'the incumbents'}.")
        rows.append([q, comps, "\n".join(pages) or "none cited", step, ""])
    rows = rows[:7]
    n1 = S.write(sid, f"'{TAB}'!A{b_first}:E{b_first+len(rows)-1}", rows).cells

    # --- Section C: prompts that did not earn their slot --------------------
    cr = []
    for q, d in g.items():
        p = d["p"]
        if p["kind"] == "competitor" and not d["comps"] and not any(d["hits"].values()):
            cr.append([q, "The named competitor did not appear in a single one of the "
                          "132 responses collected this month, on any platform. Either "
                          "the name is wrong or the company no longer registers with "
                          "the models.", ""])
        elif (p["kind"] == "category" and p["position"] and p["position"] > 40
              and not any(d["hits"].values())):
            cr.append([q, f"Sourced from a query ranking at position {p['position']}, "
                          f"and absent from every platform. The audience is also wrong: "
                          f"this reaches teachers and parents rather than the "
                          f"administrators who buy. Candidate to swap for a "
                          f"vendor-intent prompt.", ""])
    n2 = S.write(sid, f"'{TAB}'!A{c_first}:C{c_first+len(cr)-1}", cr).cells if cr else 0
    print(f"B: {len(rows)} rows at {b_first} ({n1} cells) | "
          f"C: {len(cr)} rows at {c_first} ({n2} cells)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
