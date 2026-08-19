---
name: "Semantic Site Map"
description: "Computes a topical map from any SF crawl using embeddings (no Koray map required), overlays GSC clicks per cluster, and feeds the topical-authority auditor through a JSON adapter. Surfaces siteRadius outliers and the high-click-high-siteRadius dilution-driving clusters from the May 2024 Google leak attributes."
---

# Semantic Site Map

## Pipeline stage assignment

> **Stage 4 — Ranking**, with a Stage 3 output.
> `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`

Topical authority, site focus and semantic relevance are Stage 4 signals, gated behind stages 1
to 3 per [stage-4-ranking.md](../technical-seo-agent/references/stage-4-ranking.md).

**The Stage 3 output is the noindex candidate list.** When the map surfaces a large cluster of
near-identical low-value pages (the 38-page privacy-policy cluster on Education Walkthrough is
the reference case), that is an index-bloat finding and it routes to
[stage-3-indexability.md](../technical-seo-agent/references/stage-3-indexability.md), where the
scale gate applies: index bloat only binds at a scale where it costs something.

**Input dependency worth noting:** the map is computed from crawled body text. If a site has a
render gap, the map is built on hollow documents and its clusters will be wrong. **Confirm the
Stage 2 verdict before trusting a semantic map**, particularly on JS-heavy builds.

## When to trigger

- Client requests topical authority analysis but doesn't have a Koray topical map
- Audit needs `siteFocusScore` / `siteRadius` findings (the leak-grounded auditor)
- An audit produced strong on-page metrics but client says revenue pages aren't ranking — this skill surfaces whether off-topic clusters are diluting the topical center
- Periodic re-run (60–90 days) to confirm the topical center has moved as recommended

## Prerequisites

- Screaming Frog crawl: `Clients/<name>/data/crawl_internal.csv` (or any SF Internal CSV)
- Optional: GSC export with `url`, `clicks`, `impressions` columns (90-day window recommended)
- Optional but recommended: SF custom extraction column for body text (XPath `//main` or `//article`). Without it, the skill falls back to Crawl4AI (slower).
- `.env` contains `OPENROUTER_API_KEY`

## Invocation

```bash
python run_semantic_map.py --client "<client-name>"
python run_semantic_map.py --client "Education Walkthrough" \
    --crawl "Clients/Education Walkthrough/Others/ew_crawl_filtered.csv" \
    --gsc   "Clients/Education Walkthrough/data/gsc_performance.csv"
```

Flags:

| Flag | Default | Purpose |
|---|---|---|
| `--client` (required) | — | Folder name under `Clients/` |
| `--crawl` | `Clients/<client>/data/crawl_internal.csv` | Path to SF Internal CSV |
| `--gsc` | `Clients/<client>/data/gsc_performance.csv` (optional) | Path to GSC performance export |
| `--model` | `openai/text-embedding-3-small` | OpenRouter embedding model id |
| `-v` / `--verbose` | off | Debug logging |

## Outputs

Written to `Clients/<name>/Full SEO Audit/semantic_map/`:

| File | Purpose | Consumer |
|---|---|---|
| `topical_map.json` | Koray-compatible: `central_entity`, `rings`, `outliers` | `TopicalAuthorityAuditor.from_computed_map(...)` |
| `semantic_map_full.json` | Adds `clicks_by_cluster`, `site_radius_per_url`, `cluster_name_by_id`, `high_click_off_topic_clusters` | Auditor's new high-click check; analyst reference |
| `semantic_map_report.md` | Per-cluster summary + dilution-driving clusters callout | Client deliverable |
| `semantic_map.png` | PCA scatter with four ring overlays; point size = clicks | Client deliverable |

Cache (safe to delete; speeds up re-runs):

- `Clients/<name>/Full SEO Audit/_cache_semantic_map/page_text.csv` — Crawl4AI fetch cache
- `Clients/<name>/Full SEO Audit/_cache_semantic_map/embeddings_<model>.parquet` — embedding cache keyed by text hash

## Auditor integration

```python
from auditors.topical_authority_auditor import TopicalAuthorityAuditor

auditor = TopicalAuthorityAuditor.from_computed_map(
    crawl_df=df_from_sf_csv,
    topical_map_path="Clients/Acme/Full SEO Audit/semantic_map/topical_map.json",
    full_json_path="Clients/Acme/Full SEO Audit/semantic_map/semantic_map_full.json",
)
issues = auditor.run_audit()
```

The auditor's three existing checks (`_check_outlier_pages`, `_check_topic_dispersion`, `_check_central_entity_alignment`) run unchanged on the computed map. The new `_check_high_click_off_topic_cluster` activates when `full_json_path` is provided.

## Streamlit integration

The Streamlit app exposes two new file-upload slots (slot 7: `topical_map.json`, slot 8: `semantic_map_full.json`). When both are uploaded, the topical authority audit branches to the computed-map path instead of the Koray markdown path. No changes to other auditors.

## Reading the map: two page-level lenses

The embedding map answers a **site-level** question — "how far does this page drift from the site's central topic?" (`siteRadius`). Two practitioner lenses from Daniel Foley Carter's own testing (DERIVED-FROM-TESTING — not confirmed Google ranking rules) complement it by asking **page-level** questions the embedding map alone can't answer.

### Page-level serve-rate dilution

`siteRadius` tells you a page is off-topic for the *site*. A different failure is a page that is perfectly on-topic for the site but for which Google has lost the *page's own* context. DFC's read: pull every query a URL is served for in GSC, weight each by impressions, and read the resulting keyword cloud. If a page's **lead served queries** — the highest-impression terms Google actually shows it for — are off-topic relative to the page's own title/H1/body, Google has lost the page's context. It's being served for the wrong things, which caps its average position on the queries it should win. This is page-level dilution, distinct from the site-level topical dilution the embedding map measures.

Cross-ref [auditors/query_count_auditor.py](../../auditors/query_count_auditor.py) — the serve-rate / lead-query dilution check runs on the GSC query-level frame, not the crawl df.

The two lenses read together:

| `siteRadius` | Serve-rate (lead queries) | Diagnosis | Fix |
|---|---|---|---|
| High | On-topic for the page | Coherent page, off-topic for the site | Site-level dilution — prune / relocate candidate |
| Low | Off-topic for the page | On-topic for the site, but Google lost the page's context | Page-level dilution — tighten title/H1/intro so the visually-prominent terms (`avgTermWeight`) match the intended query; not a content-strategy rewrite |

### Coverage / cluster substantiation

The cluster overlay matters beyond outlier detection. DFC's substantiation model (DERIVED-FROM-TESTING): a thin parent/hub page often ranks not on its own body content but because of the pages clustered beneath it — the cluster *substantiates* the parent. Google reads the depth of the surrounding cluster as evidence the parent covers the topic, so a hub with a strong cluster beneath it can outrank a better-written standalone page that has no supporting cluster.

The specialist-vs-generalist framing follows: a site whose clusters are few and deep (a specialist) reads as more authoritative on those topics than a generalist whose pages spread thinly across many shallow clusters. That is the same intuition the site-level `siteFocusScore` captures — but the cluster view shows *where* the depth is and *which parents are under-substantiated*.

Audit use: when a cluster shows a parent hub with few or thin supporting pages, the recommendation is not "rewrite the hub" — it's "build out the cluster beneath it" (the coverage that substantiates the parent). Conversely, a cluster of strong pages with no clear parent hub is a candidate for creating one to capture the head term the cluster already substantiates. See the topical-authority mechanics (`siteFocusScore` / `siteRadius`) in [Skills/technical-seo-agent/references/seo-fundamentals-2026.md](../technical-seo-agent/references/seo-fundamentals-2026.md).

## Decisions baked into this skill

- **Embeddings**: `openai/text-embedding-3-small` via OpenRouter (1536-dim, $0.02/1M tokens). Override with `--model`.
- **Text source**: Hybrid. If the SF crawl has a body-text column (`Content`, `Body Text`, `Custom Extraction 1`, etc.), use it. Otherwise fall back to Crawl4AI (concurrency 8 by default; aborts if >20% of fetches fail).
- **Clustering**: HDBSCAN with `min_cluster_size = max(5, n_urls // 50)`. K-means k=4 fallback when HDBSCAN finds <2 clusters; in that fallback the 5% farthest-from-centroid points are marked as outliers so the `-1` semantics carry through.
- **Cluster labels**: LLM-generated (default `anthropic/claude-sonnet-4.5`), 1 OpenRouter call per cluster, n-gram fallback on failure.
- **Ring assignment**: quartiles of `site_radius` among clustered URLs; outliers in `-1` go to the `outliers` list.
- **High-click off-topic threshold**: cluster clicks >= 75th percentile of cluster click totals AND median `site_radius` > 0.6 (cosine distance).

## Limitations

- < 50 URLs after eligibility filters → clustering is coarse; the report flags this
- Crawl4AI fetch quality varies by template; supply an SF body-text column for production audits
- Embeddings are not Google's; `text-embedding-3-small` correlates with general topical similarity, not Google's production embeddings (the "Gemma 3 ≈ Google" claim from Dan Hickley's post is a hypothesis, not a tested fact)
- Snapshot/drift comparison across runs is not in v1 — re-runs overwrite previous outputs

## Related

- Spec: [docs/superpowers/specs/2026-05-29-semantic-site-map-design.md](../../docs/superpowers/specs/2026-05-29-semantic-site-map-design.md)
- Implementation plan: [docs/superpowers/plans/2026-05-29-semantic-site-map.md](../../docs/superpowers/plans/2026-05-29-semantic-site-map.md)
- Leak attributes context: [Skills/technical-seo-agent/references/seo-fundamentals-2026.md](../technical-seo-agent/references/seo-fundamentals-2026.md)
- Consumer: [auditors/topical_authority_auditor.py](../../auditors/topical_authority_auditor.py)
