---
description: Run the semantic-site-map skill against a client. Auto-discovers the SF crawl and GSC export from the client's folder; falls back to GSC MCP if no GSC CSV is present. Outputs 4 files to `Clients/<name>/Full SEO Audit/semantic_map/`. Use when you want a topical map without manually invoking the CLI.
---

# /semantic-map

You are running the semantic-site-map skill on behalf of the user. The user has typed `/semantic-map <client name>` and expects you to:

1. Discover the right input files inside their client folder
2. Fetch GSC data live (via MCP) if no GSC CSV is present
3. Run `python run_semantic_map.py` with the discovered paths
4. Surface the results

## Step 1 — Parse the client name from the user's invocation

The user invoked this command with a client name as the argument. The client name is whatever follows `/semantic-map` in their message (e.g. `/semantic-map Education Walkthrough` → client name is `Education Walkthrough`).

If the user provided NO client name:
- List the contents of `Clients/` (use Glob: `Clients/*`)
- Ask which client they want to run on
- Stop until they answer

If the user provided a client name that does NOT match any folder in `Clients/`:
- Use Glob to list all `Clients/*` and find the closest match (case-insensitive substring)
- If there's an obvious single match, confirm with the user before proceeding
- If multiple matches or none, list the options and ask

## Step 2 — Discover the SF crawl file

The skill needs a Screaming Frog "HTML Internal" CSV export. Search the client folder for it.

Run a Glob with this pattern under the client folder (in order — use the first match found):

1. `Clients/<name>/data/crawl_internal.csv` (the canonical path)
2. `Clients/<name>/data/*.csv` (any CSV in the data dir)
3. `Clients/<name>/Others/*crawl*.csv` (some clients put crawls in Others/)
4. `Clients/<name>/Others/*internal*.csv`
5. `Clients/<name>/**/*.csv` (last-resort wildcard)

For each candidate file, briefly verify it looks like an SF crawl:
- Read the first 2 lines (use `Read` with `limit=2`)
- Confirm it has a header row mentioning `url`, `address`, or `title` (case-insensitive)
- If it does, use it. If not, skip and try the next candidate.

If multiple candidates are valid, list them and ask the user to pick. If none are valid, stop and tell the user no SF crawl was found — they need to drop one into the client folder before this command can proceed.

## Step 3 — Discover the GSC data

The skill works WITHOUT GSC data (the click-overlay finding is skipped if absent), but a topical map with click overlay is dramatically more useful. So try hard to get it.

**3a. Look for a GSC CSV in the client folder.** Glob in order:

1. `Clients/<name>/data/gsc_performance.csv`
2. `Clients/<name>/data/gsc_*.csv`
3. `Clients/<name>/**/gsc*.csv`

For each candidate: read the first 2 lines. A valid GSC export has columns like `page`/`address`/`landing page` AND `clicks` AND `impressions`. If found, use it.

**3b. If no GSC CSV is found AND the GSC MCP is available, fetch the data live.**

Check whether the `mcp__gsc-mcp__*` tools are accessible. If yes:

1. Call `mcp__gsc-mcp__list_properties` to find the property matching this client. The property URL usually matches the client's domain — infer from the client name or ask if ambiguous.
2. If a matching property exists, call `mcp__gsc-mcp__get_search_analytics` (or `get_advanced_search_analytics`) with:
   - dimensions: `["page"]`
   - 90-day window (ending today)
   - row limit: 25,000 (or the API's max)
3. Save the result as a CSV to `Clients/<name>/data/gsc_performance_<YYYY-MM-DD>.csv` with columns `url, clicks, impressions`. Use the date stamp so future runs know which data window was used.
4. Tell the user: "No GSC CSV found in the folder — fetched 90 days of data via the GSC MCP and saved to `Clients/<name>/data/gsc_performance_<date>.csv`."

If neither a CSV nor MCP access works, proceed without GSC. The map will still cluster correctly; only the click-overlay finding is skipped. Tell the user explicitly that the run will produce no click overlay.

## Step 4 — Run the skill

Construct and execute the command via Bash:

```bash
python run_semantic_map.py \
    --client "<exact client folder name>" \
    --crawl "<resolved crawl path>" \
    --gsc "<resolved GSC path>" \
    -v
```

(Omit `--gsc` if no GSC source was resolved.)

**Foreground execution.** Run it in the foreground so the user sees live progress (Crawl4AI fetch progress lines if no body-text column is present, embedding batch logs, clustering, label calls, scatter render). Do NOT use `run_in_background`. The skill prints "Outputs written:" with 4 paths when it succeeds.

If the run takes more than ~5 minutes (typical on big sites without a cached `page_text.csv`), tell the user once that Crawl4AI is fetching N URLs at concurrency 8 and the run will take 15–40 minutes — do not interrupt the run.

**Important:** if the skill prints any error or non-zero exit, surface it directly. Don't try to fix it silently. Common ones:

- `OPENROUTER_API_KEY missing` → tell the user to add it to `.env`
- `Crawl4AI failed on >20% of URLs` → tell the user; suggest they configure an SF body-text custom extraction
- `Only N URLs survived eligibility filters` → tell the user the crawl is too small for clustering

## Step 5 — Surface the results

Once the run completes:

1. Read `Clients/<name>/Full SEO Audit/semantic_map/semantic_map_report.md` and show the full content inline.
2. Read `Clients/<name>/Full SEO Audit/semantic_map/topical_map.json` enough to extract: central entity, number of rings, outlier count, unclustered count, total clusters.
3. Show the scatter PNG (`Clients/<name>/Full SEO Audit/semantic_map/semantic_map.png`) inline by reading it.
4. End with a one-paragraph honest assessment:
   - What the central entity tells us about the site
   - Whether the cluster labels look topically coherent or generic-template-noise
   - Any clusters worth flagging to the user (high page count, surprising topic, noindex candidates)
   - If GSC clicks were overlaid, mention which clusters dominated traffic
   - If 0 outliers (which is the expected state for an on-topic site), explicitly say so

## What this command MUST NOT do

- Do not fabricate findings if the run fails. If the skill errored, surface the error and stop.
- Do not "interpret" the topical map without showing the user the raw cluster list first. They want to see what the skill found, not just your summary of it.
- Do not skip the GSC MCP fallback when no CSV is present and MCP access exists — click overlay is the whole reason this skill is more useful than a raw HDBSCAN run.
- Do not delete or overwrite the cache directory (`Clients/<name>/Full SEO Audit/_cache_semantic_map/`) — re-runs are supposed to be fast because of those caches.
- Do not run on `main` against client folders that have uncommitted changes elsewhere — the command writes JSON/PNG/MD outputs which are gitignored, but if the user is mid-PR on something else, they should know.

## Skill documentation

For background on what the skill does, see [Skills/semantic_site_map/SKILL.md](../../Skills/semantic_site_map/SKILL.md). The skill methodology, the May 2024 leak attributes it grounds in (`siteEmbedding`, `siteFocusScore`, `siteRadius`), and the v1 limitations are all there.
