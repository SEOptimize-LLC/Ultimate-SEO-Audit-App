"""Re-run Beehive audit with winner-sanity + architectural-fit checks."""
from __future__ import annotations
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditors.cannibalization_auditor import CannibalizationAuditor

DATA_DIR = ROOT / "Clients/Beehive/Full Site SEO Audit/_cannibalization_data"

LOCAL_SERVICE = re.compile(
    r"\b(plumb|drain|sewer|water heater|hot water|tankless|hydro jet|"
    r"hydrojet|hydro-jet|emergency plumb|24 ?7 plumb|toilet repair|leak|"
    r"pipe|faucet|garbage disposal|flushometer|reverse osmosis|"
    r"water softener|water filtration|frozen pipe)\b",
    re.I,
)
LOCAL_GEO = re.compile(
    r"\b(near me|nearby|salt lake|slc|utah|ut|sandy|provo|ogden|"
    r"west jordan|south jordan|draper|murray|orem|park city|lehi|"
    r"saratoga|riverton|herriman|tooele|bountiful|layton|kaysville|"
    r"farmington|clearfield)\b",
    re.I,
)


def beehive_intent(query, dfs):
    q = (query or "").lower()
    has_s = bool(LOCAL_SERVICE.search(q))
    has_g = bool(LOCAL_GEO.search(q))
    if has_s and has_g:
        return "commercial"
    if has_s and dfs == "navigational":
        return "commercial"
    return dfs or "informational"


def main():
    sf_df = pd.read_excel(ROOT / "Clients/Beehive/beehive_internal_all.xlsx")
    sf_df.columns = [c.strip().lower().replace(" ", "_") for c in sf_df.columns]
    for old, new in [("address", "url"), ("title_1", "title"), ("h1-1", "h1_1")]:
        if old in sf_df.columns and new not in sf_df.columns:
            sf_df = sf_df.rename(columns={old: new})

    gsc_data = json.loads(
        (DATA_DIR / "_step2b_query_page_clean.json").read_text(encoding="utf-8")
    )
    gsc_df = pd.DataFrame(gsc_data["rows"])
    intent_data = json.loads(
        (DATA_DIR / "_step4_intent_lookup.json").read_text(encoding="utf-8")
    )
    raw_intent = intent_data.get("intent_by_query", {})
    intent_lookup = {
        q.lower(): beehive_intent(
            q, info.get("intent") if isinstance(info, dict) else info
        )
        for q, info in raw_intent.items()
    }

    auditor = CannibalizationAuditor(
        df=sf_df,
        gsc_query_page_data=gsc_df,
        keyword_intent_lookup=intent_lookup,
    )
    auditor.clear_issues()
    auditor._check_data_availability()
    clusters = []
    if auditor._has_gsc_query_page_data():
        clusters.extend(auditor._detect_via_gsc_query_page())
    clusters.extend(auditor._detect_year_versioned_urls())
    clusters = auditor._deduplicate_clusters(clusters)
    for c in clusters:
        auditor._enrich_cluster_with_priority(c)
    for c in clusters:
        auditor._apply_false_positive_filter(c)
    for c in clusters:
        c["winner_candidate"] = auditor._select_winner(c)
        auditor._apply_winner_sanity_check(c)

    counts = Counter(c["priority_tier"] for c in clusters)
    top3 = sum(1 for c in clusters if c["priority_tier"] == "A" and c["in_top_3"])
    arch_fix = sum(1 for c in clusters if c.get("architecture_fix_recommended"))
    geo_m = sum(1 for c in clusters if c.get("winner_sanity_flag") == "geo_mismatch")
    svc_m = sum(
        1 for c in clusters if c.get("winner_sanity_flag") == "service_mismatch"
    )
    both_m = sum(
        1 for c in clusters if c.get("winner_sanity_flag") == "both_mismatch"
    )
    aligned = sum(
        1 for c in clusters if c.get("winner_sanity_flag") == "aligned"
    )

    print(f"Total clusters: {len(clusters)}")
    print(
        f"Tiers: A={counts.get('A',0)}, B={counts.get('B',0)}, "
        f"C={counts.get('C',0)}, REVIEW={counts.get('REVIEW',0)}"
    )
    print(f"Top-3 in A: {top3}")
    print(f"\nWinner sanity check:")
    print(f"  Aligned:           {aligned}")
    print(f"  Geo mismatch:      {geo_m}")
    print(f"  Service mismatch:  {svc_m}")
    print(f"  Both mismatched:   {both_m}")
    print(f"  Architecture fix:  {arch_fix}")

    target_key = "emergency plumber salt lake city"
    target = next((c for c in clusters if c["key"] == target_key), None)
    if target:
        print(f"\n=== CASE: '{target_key}' ===")
        print(f"  Tier: {target['priority_tier']}")
        print(f"  Modifiers: {target.get('query_modifiers')}")
        w = target.get("winner_candidate") or {}
        print(f"  Auditor's winner: {w.get('url')}")
        a = target.get("winner_query_alignment") or {}
        print(f"  Geo aligned: {a.get('geo_aligned')}")
        print(f"  Service aligned: {a.get('service_aligned')}")
        if a.get("geo_mismatch_reason"):
            print(f"  GEO MISMATCH: {a['geo_mismatch_reason']}")
        if a.get("service_mismatch_reason"):
            print(f"  SVC MISMATCH: {a['service_mismatch_reason']}")
        print(f"  Sanity flag: {target.get('winner_sanity_flag')}")
        arch = target.get("architecturally_correct_page")
        if arch:
            print(f"  *** ARCH-CORRECT PAGE: {arch['url']}")
            print(f"      strength={arch['match_strength']}, "
                  f"services={arch['matched_services']}, "
                  f"geo={arch['matched_geo']}")
        print(f"  Architecture fix recommended: "
              f"{target.get('architecture_fix_recommended')}")

    print("\n=== TOP CLUSTERS WITH ARCHITECTURE FIX RECOMMENDED ===")
    arch_list = [c for c in clusters if c.get("architecture_fix_recommended")]
    arch_list.sort(key=lambda x: -(x.get("total_impressions") or 0))
    for c in arch_list[:15]:
        arch = c.get("architecturally_correct_page") or {}
        w = c.get("winner_candidate") or {}
        print(f"  [{c['priority_tier']}] '{c['key']}' "
              f"({c.get('total_impressions',0):,} impr)")
        print(f"      auditor's winner: {w.get('url')}")
        print(f"      should be:        {arch.get('url')}")

    # Save export
    enriched_full = []
    for c in clusters:
        ctr = auditor._compute_ctr_disparity(c)
        enriched_full.append({
            "key": c.get("key"),
            "detection_method": c.get("detection_method"),
            "priority_tier": c.get("priority_tier"),
            "original_priority_tier": c.get("original_priority_tier"),
            "priority_reasoning": c.get("priority_reasoning"),
            "is_commercial": c.get("is_commercial"),
            "is_seed_query": c.get("is_seed_query"),
            "page_topics_diverge": c.get("page_topics_diverge"),
            "false_positive_check": c.get("false_positive_check"),
            "review_reason": c.get("review_reason"),
            "in_top_3": c.get("in_top_3"),
            "in_top_10": c.get("in_top_10"),
            "best_position": c.get("best_position"),
            "total_impressions": c.get("total_impressions"),
            "total_clicks": c.get("total_clicks"),
            "urls": c.get("urls", []),
            "winner_candidate": c.get("winner_candidate"),
            "ctr_disparity": ctr,
            "query_modifiers": c.get("query_modifiers"),
            "winner_query_alignment": c.get("winner_query_alignment"),
            "winner_sanity_flag": c.get("winner_sanity_flag"),
            "architecturally_correct_page": c.get("architecturally_correct_page"),
            "architecture_fix_recommended": c.get("architecture_fix_recommended"),
        })
    enriched_full.sort(
        key=lambda c: (
            {"A": 0, "B": 1, "C": 2, "REVIEW": 3}.get(
                c.get("priority_tier", "C"), 4
            ),
            -(c.get("total_impressions") or 0),
        )
    )
    out_path = DATA_DIR / "_step6_clusters_full_export.json"
    out_path.write_text(
        json.dumps(
            {
                "total_clusters": len(enriched_full),
                "tier_counts": dict(counts),
                "top_3_priority_a_count": top3,
                "review_count": counts.get("REVIEW", 0),
                "architecture_fix_count": arch_fix,
                "winner_aligned_count": aligned,
                "geo_mismatch_count": geo_m,
                "service_mismatch_count": svc_m,
                "both_mismatch_count": both_m,
                "clusters": enriched_full,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
