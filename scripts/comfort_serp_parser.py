"""Parse cached DFS SERP responses for Comfort Solutions positions.

Loops through saved tool-result txt files and extracts positions for
comfortsolutionsutah.com and fireplacesutah.com (Comfort's fireplace
sub-brand) for each query. Saves a structured CSV.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

TOOL_RESULTS = Path(
    r"C:\Users\admin\.claude\projects"
    r"\c--Users-admin-Documents-Marketing-Roger-SEO-AI-Automations-Claude"
    r"-Claude-Code---VS-Code-SEO-Projects-Projects-Ultimate-SEO-Auditor"
    r"\9e9d695c-1264-41a1-b774-962076dcba36\tool-results"
)
OUT_DIR = Path(
    r"c:\Users\admin\Documents\Marketing\Roger SEO\AI Automations\Claude"
    r"\Claude Code + VS Code\SEO\Projects\Projects"
    r"\Ultimate SEO Auditor\Clients\Comfort\Full SEO Audit"
    r"\_keyword_data"
)


def parse_serp_file(path: Path) -> dict | None:
    """Extract Comfort's positions from a SERP tool-result file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list) and data:
            inner = json.loads(data[0]["text"])
        else:
            return None
    except (json.JSONDecodeError, KeyError, IndexError):
        return None
    items = inner.get("items", [])
    if not items:
        return None
    keyword = inner.get("keyword") or ""
    findings = []
    for it in items:
        blob = json.dumps(it).lower()
        is_main = "comfortsolutionsutah" in blob
        is_fp = "fireplacesutah.com" in blob
        if not (is_main or is_fp):
            continue
        domain = it.get("domain", "")
        # Detect domain in nested LSA / KG items
        if not domain and "comfortsolutionsutah" in blob:
            domain = "comfortsolutionsutah.com"
        elif not domain and "fireplacesutah.com" in blob:
            domain = "fireplacesutah.com"
        findings.append({
            "type": it.get("type", ""),
            "rank_absolute": it.get("rank_absolute"),
            "rank_group": it.get("rank_group"),
            "domain": domain,
            "url": (it.get("url", "") or "")[:200],
            "title": (it.get("title", "") or "")[:120],
            "is_paid": it.get("is_paid", False),
        })
    return {"keyword": keyword, "findings": findings}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    serp_files = sorted(TOOL_RESULTS.glob(
        "mcp-dfs-mcp-serp_organic_live_advanced-*.txt"
    ), reverse=True)
    rows = []
    seen_keywords = set()
    for f in serp_files:
        result = parse_serp_file(f)
        if not result:
            continue
        kw = result["keyword"].lower().strip()
        if not kw or kw in seen_keywords:
            continue
        seen_keywords.add(kw)
        # Only include results that have at least one Comfort domain
        # OR keyword matches our Comfort target set
        comfort_terms = [
            "comfort solutions", "fireplaces utah", "fireplace repair",
            "gas fireplace", "fireplace insert",
        ]
        if (
            not result["findings"]
            and not any(t in kw for t in comfort_terms)
        ):
            continue
        rows.append(result)
    # Build CSV — one row per query × finding
    out_csv = OUT_DIR / "_comfort_serp_findings_raw.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "keyword", "type", "rank_abs", "rank_grp", "domain",
            "is_paid", "url", "title",
        ])
        for r in rows:
            kw = r["keyword"]
            if not r["findings"]:
                w.writerow([kw, "NOT_VISIBLE", "", "", "", "", "", ""])
            else:
                for fnd in r["findings"]:
                    w.writerow([
                        kw, fnd["type"], fnd["rank_absolute"],
                        fnd["rank_group"], fnd["domain"],
                        "Y" if fnd["is_paid"] else "",
                        fnd["url"], fnd["title"],
                    ])
    print(f"Wrote {out_csv}")
    print(f"  Queries parsed: {len(rows)}")


if __name__ == "__main__":
    main()
