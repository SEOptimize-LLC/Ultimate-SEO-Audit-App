# Semantic Site Map — Design Spec

**Date:** 2026-05-29
**Project:** Ultimate SEO Auditor
**Status:** Approved, ready for implementation
**Source:** [/analyze-resource on Dan Hickley's LinkedIn post](../../../temp-files/1779981586603.jpg)
**Related:** [topical_authority_auditor.py](../../../auditors/topical_authority_auditor.py), [Skills/technical-seo-agent/references/seo-fundamentals-2026.md](../../../Skills/technical-seo-agent/references/seo-fundamentals-2026.md)

## Problem

The project's topical authority auditor models the May 2024 Google leak attributes (`siteEmbedding`, `siteFocusScore`, `siteRadius`) but depends on a user-supplied Koray topical map as the input. Most clients don't have one, so the most leak-grounded auditor in the stack rarely runs. The auditor also has no view of GSC click density per topical cluster — it can find off-topic outliers but can't find the higher-leverage problem of high-traffic-but-off-topic clusters that drag the site's topical center away from revenue pages.

## Goal

Ship a `Skills/semantic-site-map/` skill that (a) computes a topical map from any SF crawl without needing a Koray map, (b) overlays GSC clicks on the map, (c) feeds the existing auditor through a JSON adapter so existing checks run unchanged, and (d) adds a new auditor finding for the high-click-high-siteRadius case. Includes a static scatter-plot PNG matching the screenshot's four-ring structure.

## Locked decisions

| Decision | Choice | Reasoning |
|---|---|---|
| Text source | Hybrid: SF body-text column if present, Crawl4AI fallback | Fastest + cheapest in steady state; zero blocker on first run |
| Embedding model | OpenAI `text-embedding-3-small` via OpenRouter | Cheapest at scale, no new API keys, strong clustering quality |
| Clustering | HDBSCAN with auto-tuned `min_cluster_size` | Native outlier concept matches `siteRadius` semantics |
| Cluster labels | LLM-generated (1 OpenRouter call per cluster) | Human-readable labels in client-facing report |
| Outputs | All three: Koray-compatible JSON, rich JSON, Markdown report + scatter PNG | Decoupled consumers; auditor reads JSON, client reads Markdown |
| v1 scope | Recs #1 + #2 + #3 + #4 + #7 | Full conceptual unlock in one ship |
| Structure | Skill-first, single CLI entry point, Streamlit gets one new upload slot | Matches existing project patterns |

## Architecture

`Skills/semantic-site-map/` contains:

- `SKILL.md` — when to trigger, how to invoke, prerequisites, output schema
- `text_loader.py` — hybrid text source (SF column detection → Crawl4AI fallback). Writes `Clients/<name>/data/page_text.csv` on first fetch for re-use
- `embedder.py` — batched OpenRouter embedding with retries + parquet cache keyed by URL hash
- `cluster.py` — HDBSCAN, site-center computation, per-URL siteRadius, LLM labels with n-gram fallback
- `report.py` — GSC click join, four output files, scatter-plot PNG

Repo root entry point: `run_semantic_map.py --client <name>` (mirrors existing `run_fetch.py`).

Auditor changes in [auditors/topical_authority_auditor.py](../../../auditors/topical_authority_auditor.py):

1. New classmethod `from_computed_map(json_path) -> TopicalAuthorityAuditor` that loads `topical_map.json` and normalizes to the same dict shape the existing constructor accepts. Existing three checks run unchanged.
2. New check method `_check_high_click_off_topic_cluster()` that reads the rich JSON (passed alongside the basic map) and emits a finding when any cluster has clicks > P75 AND median siteRadius > 0.6 (cosine distance threshold; tuned during validation).
3. Copy edit in `_check_outlier_pages` recommendation field — sharpen subdomain-vs-subfolder argument using siteEmbedding mechanism.

Streamlit change in [app.py](../../../app.py): one new file-upload slot labeled "Computed Semantic Map (JSON)" that mirrors the existing topical-map slot. No new pages, no new tabs.

## Data flow

1. **Input** — `run_semantic_map.py --client <name>` reads `Clients/<name>/data/crawl_internal.csv`
2. **Text** — `text_loader.py` detects a body-text column (candidates: `Content`, `Body Text`, `Custom Extraction 1`). Present → use it. Absent → Crawl4AI on the URL list → cache to `page_text.csv`. Filter non-200, non-HTML, noindex.
3. **Embeddings** — `embedder.py` batches 100 URLs per OpenRouter request, retries 3× with backoff, caches to `embeddings_text-embedding-3-small_<date>.parquet`. Re-runs skip cached URL hashes.
4. **Clusters** — `cluster.py` computes site-center as mean embedding, per-URL siteRadius as cosine distance to center, runs HDBSCAN with `min_cluster_size = max(5, len(urls)//50)`. Unclustered points = outliers. For each cluster: top TF-IDF n-grams against the rest of the site, then OpenRouter call with (n-grams + 3 sample URLs) → 2–4 word label.
5. **Outputs** — `report.py` reads `Clients/<name>/data/gsc_performance.csv` (90-day default), aggregates clicks/impressions per cluster, computes high-click-high-siteRadius pages, emits four files to `Clients/<name>/Full SEO Audit/semantic_map/`:
   - `topical_map.json` — Koray-compatible shape: `{central_entity, rings: {core, focus, expansion, peripheral}, outliers}`
   - `semantic_map_full.json` — adds `clicks_by_cluster`, `site_radius_per_url`, `cluster_centroids`, `embedding_model_used`, `high_click_off_topic_clusters`
   - `semantic_map_report.md` — analyst-facing, with per-cluster click density and the top dilution-driving pages
   - `semantic_map.png` — matplotlib scatter, four concentric rings, point size = clicks, color = cluster, site-center marker
6. **Auditor** — `TopicalAuthorityAuditor.from_computed_map("Clients/<name>/Full SEO Audit/semantic_map/topical_map.json")` returns an instance; existing checks run unchanged + new `_check_high_click_off_topic_cluster` reads the rich JSON.

## Error handling

| Failure | Behavior |
|---|---|
| No SF body-text column AND Crawl4AI fails on >20% of URLs | Abort with explicit error listing failed URLs; no silent truncation |
| OpenRouter rate-limit / outage during embedding | Retry 3× with exponential backoff, then fail with cache intact so re-run resumes |
| Fewer than 50 URLs after filtering | Emit embeddings + single-cluster output, skip HDBSCAN, warn in Markdown that the site is too small for meaningful clustering |
| HDBSCAN produces < 2 clusters | Fall back to K-means with k=4 so the four-ring structure still renders; flag fallback in report |
| GSC data missing | Run without click overlay; outputs note "click data unavailable"; skip Rec #3 finding |
| LLM cluster-label call fails | Fall back to top-3 raw n-grams as the label; flag in report |

Every error path leaves the embedding cache intact so re-runs are cheap.

## Testing

- Unit tests for `text_loader.detect_body_column`, `embedder.batch_embed` (mocked), `cluster.compute_site_center`, `cluster.compute_site_radius`, `report.aggregate_clicks_by_cluster`
- Integration test: synthetic 100-URL site with 2 known on-topic clusters + 5 known outliers → assert HDBSCAN finds 2 clusters and flags the 5 outliers
- Auditor adapter test: load sample computed `topical_map.json` → verify three existing checks fire identically to a Koray .md input
- Cross-check on one existing client with a Koray map → log cluster label / outlier set discrepancies for review (sanity log, not pass/fail)

## Out of scope (deferred to v1.1+)

- SERP-entity overlay / "third map" (Rec #5) — pilot after v1 validates
- Snapshot mechanism + topical-drift-over-time view (Rec #6)
- Interactive scatter plot in Streamlit (current v1 is static PNG only)
- Embedding-model swap (`gemini-embedding-001`, Voyage) — config hook deferred until a benchmark justifies it

## Risks

- **Cluster labels feel arbitrary on sparse sites** — mitigated by the n-gram fallback + the `< 50 URLs` warning
- **Crawl4AI extraction quality varies by template** — mitigated by hybrid text source (SF column path is the preferred steady state)
- **Embedding model drift if OpenAI deprecates `text-embedding-3-small`** — mitigated by parameterizing the model name in `embedder.py`; cache files include model name in filename so regeneration is detectable
- **HDBSCAN can be unstable on small sites** — mitigated by K-means fallback when cluster count < 2
