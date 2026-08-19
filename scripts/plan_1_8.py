"""Task 1.8 stage 1: the candidate matrix.

    python scripts/plan_1_8.py matrix <client|all> [stamp]

Joins the three Week-1 signal sources into one evidence table per client:

  1.5  ranked candidates      - read from the client's 1.5 tab, section B
  1.7  gap clusters           - analysis.yaml (or the tab itself where no yaml
                                exists - EW predates the generic filler)
  1.6  AI-visibility gaps     - category prompts where the brand is absent on
                                more platforms than it is present, via the 1.6
                                engine's own load()/analyse()

The template's selection rule does the ranking: a page holding a ranking
signal AND an AI-visibility gap AND a competitor keyword gap outranks any
single-purpose target. This script only assembles that evidence; choosing the
3-5 targets is the judgment gate, and the owner confirms the picks against the
content calendar before anything is written to Weeks 2-4 (one team touches a
page per month).

Output: Clients/<folder>/monthly_plan/<stamp>-matrix.json + a console table.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io  # noqa: E402
import fill_1_6_all as six  # noqa: E402

STOP = {"the", "a", "of", "for", "in", "and", "vs", "to", "what", "how",
        "best", "near", "me", "is", "services", "service"}


def words(s: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (s or "").lower())
            if w not in STOP and len(w) > 2}


def path_of(url: str) -> str:
    m = re.search(r"https?://[^/]+(/[^\s)]*)", url or "")
    p = (m.group(1) if m else (url or "")).rstrip("/")
    return p or "/"


def read_15(sheet_id: str) -> list[dict]:
    tab = next(t for t in sheets_io.tab_names(sheet_id) if t.strip().startswith("1.5"))
    anchor = sheets_io.find_rows(sheet_id, tab, {"b": "B. Ranked candidates"})["b"]
    rows = sheets_io.read(sheet_id, f"'{tab}'!A{anchor + 1}:I{anchor + 16}")
    out = []
    for r in rows[1:]:  # first row is the header
        r += [""] * (9 - len(r))
        if "http" not in str(r[1]):
            continue
        out.append({"rank": r[0], "page": r[1].strip(), "source": r[2],
                    "query": r[3], "pos": r[4], "imp": r[5],
                    "rationale": r[6], "value": r[7], "selected": r[8]})
    return out


def read_17(slug: str, cfg: dict) -> list[dict]:
    ya = Path(cfg["folder"]) / "gap_analysis/analysis.yaml"
    if ya.exists():
        doc = yaml.safe_load(ya.read_text(encoding="utf-8"))
        return [{"cluster": c["cluster"], "our_page": c["our_page"],
                 "volume": c["volume"], "clicks": c["clicks"],
                 "intent": c["intent"],
                 "parked": "PARKED" in str(c["cluster"]).upper()}
                for c in doc["clusters"]]
    # EW: the pilot tab predates analysis.yaml - read section A off the sheet.
    sid = cfg["sheet_id"]
    tab = next(t for t in sheets_io.tab_names(sid) if t.strip().startswith("1.7"))
    anchor = sheets_io.find_rows(sid, tab, {"a": "A. Keyword Gaps"})["a"]
    rows = sheets_io.read(sid, f"'{tab}'!A{anchor + 1}:J{anchor + 20}")
    out = []
    for r in rows[1:]:
        r += [""] * (10 - len(r))
        if not str(r[0]).strip() or str(r[0]).startswith("B."):
            break
        out.append({"cluster": r[0], "our_page": r[7], "volume": r[2],
                    "clicks": r[3], "intent": r[4],
                    "parked": "PARKED" in str(r[0]).upper()})
    return out


def read_16_gaps(slug: str, stamp: str) -> list[dict]:
    doc, _cfg, data = six.load(slug, stamp)
    gaps = []
    for rec in six.analyse(slug, doc, data):
        if rec["p"].get("kind") != "category":
            continue
        marks = [v for v in rec["seen"].values() if v in ("Y", "N")]
        if len(marks) < 2:
            continue
        n, y = marks.count("N"), marks.count("Y")
        if n >= y and n >= 2:
            gaps.append({"prompt": rec["q"],
                         "source_query": rec["p"].get("source_query"),
                         "absent_on": n, "present_on": y,
                         "top_comps": [c for c, _ in rec["comps"].most_common(3)]})
    return gaps


def build(slug: str, stamp: str) -> dict:
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    cfg = reg[slug]
    c15 = read_15(cfg["sheet_id"])
    c17 = read_17(slug, cfg)
    c16 = read_16_gaps(slug, stamp)

    cands: dict[str, dict] = {}

    def slot(page: str) -> dict:
        key = path_of(page)
        return cands.setdefault(key, {"page": page, "signals": {}, "score": 0})

    for r in c15:
        slot(r["page"])["signals"]["1.5"] = r
    for c in c17:
        if c["parked"]:
            continue
        page = c["our_page"]
        key = "NEW BUILD: " + c["cluster"] if "http" not in str(page) else page
        s = slot(key)
        s["signals"].setdefault("1.7", []).append(c)
    # 1.6 prompt gaps attach by query-word overlap with the candidate's
    # query/cluster/slug - approximate on purpose; the judgment pass reviews it.
    for g in c16:
        gw = words(g["source_query"] or g["prompt"])
        if not gw:
            continue
        best, best_ov = None, 0.0
        for key, s in cands.items():
            cw = set()
            f15 = s["signals"].get("1.5")
            if f15:
                cw |= words(f15["query"]) | words(path_of(f15["page"]).replace("-", " "))
            for c in s["signals"].get("1.7", []):
                cw |= words(c["cluster"])
            cw |= words(key.replace("-", " ").replace("/", " "))
            ov = len(gw & cw) / len(gw)
            if ov > best_ov:
                best, best_ov = key, ov
        if best and best_ov >= 0.5:
            cands[best]["signals"].setdefault("1.6", []).append(g)

    for s in cands.values():
        sig = s["signals"]
        s["score"] = sum(k in sig for k in ("1.5", "1.7", "1.6"))
        f15 = sig.get("1.5")
        s["selected_15"] = (f15 or {}).get("selected", "")
        imp = str((f15 or {}).get("imp", "0")).replace(",", "")
        s["imp"] = int(imp) if imp.isdigit() else 0

    ranked = sorted(cands.values(), key=lambda s: (-s["score"], -s["imp"]))
    out = {"client": slug, "stamp": stamp, "candidates": ranked,
           "unmatched_16_gaps": [g for g in c16 if not any(
               g in s["signals"].get("1.6", []) for s in cands.values())]}
    d = Path(cfg["folder"]) / "monthly_plan"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{stamp}-matrix.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def show(m: dict) -> None:
    print(f"\n=== {m['client']} - candidate matrix ({m['stamp']}) ===")
    for s in m["candidates"]:
        sig = s["signals"]
        tags = []
        if "1.5" in sig:
            f = sig["1.5"]
            tags.append(f"1.5[{f['value']}/pos {f['pos']}/imp {f['imp']}/sel {f['selected']}]")
        for c in sig.get("1.7", []):
            tags.append(f"1.7[{c['cluster']} vol {c['volume']} clk {c['clicks']}]")
        for g in sig.get("1.6", []):
            tags.append(f"1.6[absent {g['absent_on']}p: {g['prompt'][:40]}]")
        print(f"  score {s['score']}  {path_of(s['page'])[:60]:<60}")
        for t in tags:
            print(f"        {t[:110]}")
    if m["unmatched_16_gaps"]:
        print("  -- 1.6 gaps with no page match (need a judgment look):")
        for g in m["unmatched_16_gaps"]:
            print(f"        absent {g['absent_on']}p  {g['prompt'][:80]}")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "matrix":
        raise SystemExit(__doc__)
    slug, stamp = sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "2026-08")
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    slugs = list(reg) if slug == "all" else [slug]
    for s in slugs:
        try:
            show(build(s, stamp))
        except Exception as e:
            print(f"\n=== {s}: FAILED - {type(e).__name__}: {e}")
