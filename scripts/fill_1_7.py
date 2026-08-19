"""Write a client's 1.7 Gap Analysis tab from its authored analysis file.

    python scripts/fill_1_7.py <client>

Reads Clients/<folder>/gap_analysis/analysis.yaml - the judgment layer authored
over the engine's evidence files (see tasks/1.7.md). The engine collects, the
analysis file decides, this script only writes. Layout is the owner's
restructured template: one row per keyword cluster, ten columns, one blank row
between sections.

analysis.yaml keys:
  competitor_set: str        -> B4
  baseline_note: str         -> B5
  clusters: [ {cluster, keywords, volume, clicks, intent, competitor,
               their_url, our_page, brief, comments} ]
  backlinks: [ {target, comp_page, our_page, quality_note, routed} ]
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io as S  # noqa: E402

TAB = "1.7 Gap Analysis"


def main(slug: str):
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    cfg = reg[slug]
    sid = cfg["sheet_id"]
    doc = yaml.safe_load((Path(cfg["folder"]) / "gap_analysis" / "analysis.yaml"
                          ).read_text(encoding="utf-8"))

    hdr = S.read(sid, f"'{TAB}'!A8:J8")
    want = ["Keyword Cluster", "Keywords", "Volume", "Clicks", "Intent",
            "Competitor", "Their Ranking URL", "Our Best Page",
            "Expansion Angle", "Additional Comments"]
    got = [str(c).strip() for c in (hdr[0] if hdr else [])]
    if got[:len(want)] != want:
        raise SystemExit(f"{slug}: section A header mismatch - copy the EW tab "
                         f"structure first. Got: {got}")

    S.write(sid, f"'{TAB}'!B4", [[doc["competitor_set"]]])
    S.write(sid, f"'{TAB}'!B5", [[doc["baseline_note"]]])

    colA = S.read(sid, f"'{TAB}'!A1:A160")
    a_first = next(i for i, r in enumerate(colA, 1)
                   if r and str(r[0]).strip() == "Keyword Cluster") + 1
    b_hdr = next(i for i, r in enumerate(colA, 1)
                 if r and str(r[0]).strip().startswith("B."))
    slots = b_hdr - 1 - a_first          # keep one blank separator row
    rows = doc["clusters"]
    if len(rows) > slots:
        S.insert_rows(sid, TAB, a_first + slots, len(rows) - slots)
    elif len(rows) < slots:
        S.delete_rows(sid, TAB, a_first + len(rows), slots - len(rows))
    body = [[c["cluster"], c["keywords"], c["volume"], c["clicks"], c["intent"],
             c["competitor"], c["their_url"], c["our_page"], c["brief"],
             c["comments"]] for c in rows]
    n = S.write(sid, f"'{TAB}'!A{a_first}:J{a_first+len(body)-1}", body).cells

    colA = S.read(sid, f"'{TAB}'!A1:A200")
    t_first = next(i for i, r in enumerate(colA, 1)
                   if r and str(r[0]).strip().startswith("Target Domain")) + 1
    brows = [[b["target"], b["comp_page"], b["our_page"], b["quality_note"],
              b["routed"]] for b in doc["backlinks"]]
    nb = S.write(sid, f"'{TAB}'!A{t_first}:E{t_first+len(brows)-1}", brows).cells
    print(f"{slug:<10} A: {len(body)} clusters ({n} cells)  B: {len(brows)} "
          f"targets ({nb} cells)")


if __name__ == "__main__":
    main(sys.argv[1])
