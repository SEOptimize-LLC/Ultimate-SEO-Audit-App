---
name: "Semantic Site Map"
description: "Computes a topical map from any SF crawl using embeddings (no Koray map required), overlays GSC clicks per cluster, and feeds the topical-authority auditor through a JSON adapter. Surfaces siteRadius outliers and the high-click-high-siteRadius dilution-driving clusters from the May 2024 Google leak attributes."
---

# Semantic Site Map

Stub — full version written in Task 9 after the skill is functional.

## Invocation

```bash
python run_semantic_map.py --client "<client-name>"
```

## Outputs

Written to `Clients/<name>/Full SEO Audit/semantic_map/`:
- `topical_map.json` — Koray-compatible, consumed by `TopicalAuthorityAuditor.from_computed_map`
- `semantic_map_full.json` — adds click overlay + per-URL siteRadius
- `semantic_map_report.md` — analyst-facing
- `semantic_map.png` — four-ring scatter plot
