"""Run cannibalization audit for Beehive Plumbing.

Inputs:
    - Clients/Beehive/beehive_internal_all.xlsx (Screaming Frog HTML internal)
    - _cannibalization_data/_step2b_query_page_clean.json (GSC query/page)
    - _cannibalization_data/_step4_intent_lookup.json (DFS intent lookup)

Outputs:
    - _cannibalization_data/_step5_audit_results.json (full auditor output)
    - _cannibalization_data/_step6_clusters_enriched.json (post-processed)
    - The .md report and Excel are built by separate scripts.

Beehive-specific intent override: DFS classifies several local-plumber
service queries as "navigational" because branded plumbing chains
dominate their SERPs. These are real money keywords for a Utah plumber,
so we override DFS labels on patterns matching local-service intent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from auditors.cannibalization_auditor import CannibalizationAuditor

CLIENT_DIR = ROOT / "Clients" / "Beehive"
DATA_DIR = CLIENT_DIR / "Full Site SEO Audit" / "_cannibalization_data"

# ----------------------------------------------------------------------
# Beehive intent override patterns
# ----------------------------------------------------------------------
LOCAL_SERVICE_TERMS = re.compile(
    r"\b(plumb|drain|sewer|water heater|hot water|tankless|"
    r"hydro jet|hydrojet|hydro-jet|emergency plumb|24 ?7 plumb|"
    r"toilet repair|leak|pipe|faucet|garbage disposal|flushometer|"
    r"reverse osmosis|water softener|water filtration|frozen pipe)\b",
    re.I,
)
LOCAL_GEO_TERMS = re.compile(
    r"\b(near me|nearby|salt lake|slc|utah|ut|sandy|provo|ogden|"
    r"west jordan|south jordan|draper|murray|orem|park city|lehi|"
    r"saratoga|riverton|herriman|tooele|bountiful|layton|kaysville|"
    r"farmington|clearfield)\b",
    re.I,
)


def beehive_intent_for_query(query: str, dfs_intent: str | None) -> str:
    """Apply Beehive-specific intent override.

    DFS labels many local-service queries as 'navigational' because
    branded plumbing chains dominate the SERP. For Beehive (a local
    Utah plumber), these are money keywords. Override to 'commercial'
    when query matches local-service + geo patterns.
    """
    q = (query or "").lower()
    has_service = bool(LOCAL_SERVICE_TERMS.search(q))
    has_geo = bool(LOCAL_GEO_TERMS.search(q))
    # Local-service + geo modifier = commercial money keyword
    if has_service and has_geo:
        return "commercial"
    # Pure local-service queries (no geo) where DFS said navigational
    # are also commercial — branded chain noise misclassified them
    if has_service and dfs_intent == "navigational":
        return "commercial"
    return (dfs_intent or "informational")


def main() -> None:
    # ----- Load Screaming Frog crawl -----
    sf_path = CLIENT_DIR / "beehive_internal_all.xlsx"
    print(f"Loading SF crawl from: {sf_path}")
    sf_df = pd.read_excel(sf_path)
    # Normalize column names to snake_case to match auditor expectations
    sf_df.columns = [c.strip().lower().replace(" ", "_") for c in sf_df.columns]
    print(f"  SF columns: {len(sf_df.columns)}, rows: {len(sf_df)}")

    # The auditor expects: url, title, h1_1, indexability, content_type,
    # status_code, gsc_position, gsc_impressions, gsc_clicks, etc.
    # Map common variants
    rename_map = {
        "address": "url",
        "title_1": "title",
        "h1-1": "h1_1",
        "status_code": "status_code",
        "indexability": "indexability",
        "content_type": "content_type",
        "gsc_clicks": "gsc_clicks",
        "gsc_impressions": "gsc_impressions",
        "gsc_position": "gsc_position",
    }
    for old, new in rename_map.items():
        if old in sf_df.columns and new not in sf_df.columns:
            sf_df = sf_df.rename(columns={old: new})

    # ----- Load GSC query+page -----
    # Prefer the prepared cache if it exists; otherwise regenerate it
    # from the raw step1 payload using the shared data-prep utils.
    cache_path = DATA_DIR / "_step2b_query_page_clean.json"
    if cache_path.exists():
        gsc_data = json.loads(cache_path.read_text(encoding="utf-8"))
        gsc_df = pd.DataFrame(gsc_data["rows"])
        print(f"  GSC query/page rows (from cache): {len(gsc_df)}")
    else:
        from utils.cannibalization_data_prep import prepare_for_auditor
        raw_path = DATA_DIR / "_step1_gsc_query_page_90d.json"
        if not raw_path.exists():
            raise FileNotFoundError(
                "Neither cleaned cache nor raw GSC payload exists. Pull "
                "GSC query/page data first (see step 1 in the cannibalization "
                "workflow)."
            )
        raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
        # Beehive brand exclusion lives here — the only client-specific
        # piece of the data-prep step
        beehive_brand = re.compile(r"\bbeehive|behive|bee\s?hive\b", re.I)
        prepared = prepare_for_auditor(
            raw_payload,
            host_hint="beehiveplumbing.com",
            brand_pattern=beehive_brand,
            output_dir=DATA_DIR,
        )
        gsc_df = pd.DataFrame(prepared["rows"])
        print(
            f"  GSC query/page rows (regenerated): {len(gsc_df)} | "
            f"queries={prepared['stats']['unique_queries']} | "
            f"pages={prepared['stats']['unique_pages']} | "
            f"candidate clusters={prepared['stats']['candidate_count']}"
        )

    # ----- Load DFS intent + apply Beehive override -----
    intent_data = json.loads((DATA_DIR / "_step4_intent_lookup.json").read_text(encoding="utf-8"))
    raw_intent = intent_data.get("intent_by_query", {})
    intent_lookup = {}
    overrides_applied = []
    for query, info in raw_intent.items():
        dfs_label = (info.get("intent") if isinstance(info, dict) else info) or None
        final = beehive_intent_for_query(query, dfs_label)
        intent_lookup[query.lower()] = final
        if dfs_label != final:
            overrides_applied.append({"query": query, "dfs": dfs_label, "applied": final})
    print(f"  Intent entries: {len(intent_lookup)}")
    print(f"  Beehive overrides applied: {len(overrides_applied)}")
    for o in overrides_applied[:10]:
        print(f"    {o['dfs']:<14} -> {o['applied']:<14} | {o['query']}")
    if len(overrides_applied) > 10:
        print(f"    ... and {len(overrides_applied) - 10} more")

    # ----- Run auditor (no live SERP fn — would burn API calls) -----
    auditor = CannibalizationAuditor(
        df=sf_df,
        gsc_query_page_data=gsc_df,
        keyword_intent_lookup=intent_lookup,
        # live_serp_overlap_fn left None for this run — we'll do live
        # verification on the top-priority clusters only, separately
    )
    issues = auditor.run_audit()
    print(f"\nIssues emitted: {len(issues)}")
    for issue in issues:
        print(f"  {issue.severity.value.upper():<10} {issue.title}")

    # ----- Save full results -----
    results = []
    for issue in issues:
        results.append({
            "severity": issue.severity.value,
            "category": issue.category.value,
            "issue_type": issue.issue_type,
            "title": issue.title,
            "description": issue.description,
            "count": issue.count,
            "affected_urls": issue.affected_urls,
            "recommendation": issue.recommendation,
            "impact": issue.impact,
            "additional_data": issue.additional_data,
        })
    out_path = DATA_DIR / "_step5_audit_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nWritten: {out_path}")

    # Save the override log for transparency
    override_log = DATA_DIR / "_step5_intent_overrides_applied.json"
    override_log.write_text(json.dumps({
        "total_overrides": len(overrides_applied),
        "logic": "DFS classifies local-service queries as 'navigational' when branded chains dominate the SERP. For Beehive (local Utah plumber), these are commercial money keywords.",
        "overrides": overrides_applied,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Override log: {override_log}")


if __name__ == "__main__":
    main()
