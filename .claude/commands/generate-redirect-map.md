---
description: Generate a candidate redirect map for a URL migration. Takes an old URL list (SF crawl or GSC export) and a new URL list (staging crawl, new-site crawl, or sitemap URL), runs scripts/generate_redirect_map.py through staged matching (same-path, slug, structural, semantic), and returns a confidence-scored candidate map plus a stranded-URLs review queue. Use at the start of any migration or restructure, BEFORE the redirect deliverable is drafted.
---

# /generate-redirect-map

You are generating a candidate redirect map on behalf of the user. The user typed `/generate-redirect-map <client name or file paths>` and expects you to locate the inputs, run the generator, and walk them through what needs review. The user never runs the Python script themselves.

**This command produces a CANDIDATE map, not a deliverable.** Its output enters the pipeline at the top: generate here, then Rule 12 verification of every proposed target, then implementation, then `/validate-redirects` post-implementation. Never hand its raw output to a developer.

## Step 1 — Resolve the inputs

Two inputs are needed: the OLD URL list and the NEW URL list.

**Old URLs** (what currently exists / existed):
- If the user gave a file path, use it.
- If the user gave a client name, look for a Screaming Frog crawl or GSC export: `Clients/<name>/data/crawl_internal.csv`, then `Clients/<name>/data/*.csv`, then `Clients/<name>/**/*crawl*.csv`. Verify the candidate has a URL column (read first 2 lines; look for Address/URL/Page). If GSC MCP access exists and no file is found, offer to pull the page list from GSC instead.

**New URLs** (the post-migration structure):
- A staging/new-site crawl CSV if the user has one, OR
- A sitemap URL (`--new-sitemap https://.../sitemap.xml`) when the new site or staging environment is live.
- If neither exists yet, stop and tell the user what's needed — do not attempt to infer the new architecture.

If either input is ambiguous, list the candidates and ask. Confirm both file choices in one line before running.

## Step 2 — Check the semantic stage

The embedding stage needs `OPENROUTER_API_KEY` in `.env`. Check whether it's configured (do not print the key). If missing, tell the user the run will use structural matching only and more URLs will land in the stranded queue — then proceed. Only pass `--no-semantic` if the user explicitly asks to skip embeddings.

## Step 3 — Run the generator

```bash
python scripts/generate_redirect_map.py \
    --old "<old list path>" \
    --new "<new list path>"            # or --new-sitemap <url>
    [--base-url <https://domain.com>]  # if either list has relative paths
    --output-dir "Clients/<name>/Full SEO Audit/redirect_map/"
```

Run in the foreground. Defaults (structural threshold 0.75 / margin 0.10, semantic threshold 0.80 / margin 0.02) are starting points; only tune them if a first pass strands an implausibly large share and the user wants a looser pass to review.

The embedding stage caches to `_cache_redirect_map/` under the output dir — do not delete it; re-runs are cheap because of it.

## Step 4 — Report the results

Read the JSON summary and the CSV, then present:

1. **Counts first:** N matched / N unchanged / N stranded, and the per-method breakdown (same-path, slug, structural, semantic).
2. **The review queue, by tier:**
   - `SPOT-CHECK` (slug matches): list them; the user skims for cross-section false positives (a /blog/ slug matching a /services/ page).
   - `YES` (structural + semantic): every row listed with full source URL, proposed target, and score. These need human confirmation before the map is drafted.
   - `STRANDED`: every row with its closest alternative and score. Each needs a decision: map it manually or 410 it. Never propose the homepage as a catch-all.
3. **Next step in the pipeline, stated explicitly:** once the user confirms the review rows, the accepted targets go through Rule 12 verification (dispatch the live-url-verifier subagent on the proposed targets — for a pre-launch staging site, verify against staging) before any redirect deliverable is drafted. After implementation, `/validate-redirects` closes the loop.

Full URLs always, no em dashes, tables max 6 columns (split the review listing into per-tier lists rather than one wide table).

## What this command MUST NOT do

- Do not ship or format the raw output as a client deliverable or a Rank Math import. Candidate map only.
- Do not fill stranded rows with the homepage or any default target. Google treats bulk redirects-to-homepage as soft 404s; stranded means a human decides.
- Do not auto-accept structural or semantic matches on the user's behalf. High-confidence tiers (same-path, unique slug) may be presented as accepted-unless-objected; medium and low tiers need explicit confirmation.
- Do not fabricate a new-site URL list from assumptions about the architecture. If no staging crawl or sitemap exists, the migration isn't ready for mapping.
- Do not skip the Rule 12 hand-off. Generated targets are upstream-document targets and are never trusted unverified.

## Background

Matching stages, thresholds, and the no-homepage-fallback rationale are documented in the docstring of [scripts/generate_redirect_map.py](../../scripts/generate_redirect_map.py). The downstream validation command is [/validate-redirects](validate-redirects.md); the governing rule is Rule 12 in [.claude/rules/audit-workflow.md](../rules/audit-workflow.md).
