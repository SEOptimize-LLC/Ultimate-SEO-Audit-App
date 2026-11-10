---
description: Library-wide content refresh audit for one client - every page that earns something, bucketed (recover rank / win the answer / earn citations / out) and ranked into one queue, as a branded xlsx.
---

# /refresh-audit <client>

On demand only. Never wired into the monthly workbook (owner, 2026-11-10). Use it for a whole-library
pass (a site with hundreds of posts and service or product pages); the monthly 1.5 > 1.8 chain stays the
way the five monthly refresh slots are chosen.

## Steps

1. `python scripts/refresh_audit.py <client>` (registry slug). Flags: `--serp-cap N` (default 100 live
   SERP checks, largest impressions first), `--no-serp`, `--no-ga4`, `--no-tracker`, `--review-top N`
   (default 30).
2. Optional input: a Search Console Generative AI report export saved as
   `Clients/<folder>/data/gsc_generative_ai_pages.csv`. The report has no API, so it is a manual export.
3. For each of the top 30 queue rows, read its evidence (`python scripts/evidence_1_5.py` style: live
   page, year over year, history, queries, the SERP line) and write a judgment into
   `Clients/<folder>/refresh_audit/review.yaml`:
   ```yaml
   https://www.example.com/page:
     value: High | Medium | Low        # posts: by intent and what the client sells
     action: content depth and internal links
     rationale: Two or three sentences citing this row's figures.
   ```
   REASONING.md applies: no judgment from a default. Then `python scripts/refresh_audit.py <client> --rewrite`
   writes the reviewed file from today's cached rows without fetching again.
4. Show the owner the file path, the bucket counts and the top 10 rows in chat.

## What the code decides, and what it does not

Mechanical (threshold arithmetic): the pool, the comparison window, the bucket, the SERP route, the
order. Judgment (review.yaml only): business value of posts, the action, the rationale. Rows below the
top 30 say "ranked, not reviewed" and must not be presented as recommendations.

Thresholds and their basis are on the workbook's "How to read" tab and in the script's docstring.

## Lessons from review

- 2026-11-10 · Live status checks ran 8 at a time and Beehive answered 114 pages with 429, which the first version read as dead pages. Check one page at a time with a pause, retry 429 and 5xx, and report a check that never clears as "not confirmed", never as Out. (caught by: failure pilot)
- 2026-11-10 · The AI-gap matcher attached the same two prompts to every page because they shared "salt lake city". Drop words that appear in a quarter of the client's prompts (and in at least two) before counting shared words, and compare singular and plural as one word. (caught by: failure pilot)
- 2026-11-10 · Year-ago impressions and positions from before October 2025 read as a "demand fall" on pages that lost their leads (water softeners 8 to 0). Read the cause against October-December 2025 while last year's window predates the Search Console reporting change; the previous three months hide older declines. (caught by: failure pilot)
- 2026-11-10 · Out rows reached the file without a status check, and non-200 addresses were listed. Resolve every row, write the address that serves 200, and leave out (count only) any row not confirmed 200. (caught by: reviewer D1)
- 2026-11-10 · Top-30 actions read "diagnose first" and "check last month's edit" when the deciding data could be pulled. Pull it (which page holds the query in Search Console, the page's monthly history, worked_urls in the prior workbooks) and write the call. (caught by: reviewer D3)
- 2026-11-10 · The SERP column carried DataForSEO readings as results-page claims, which K2 forbids even with a caveat. Write a feature claim only from a live Google check recorded as `serp:` in review.yaml; otherwise "SERP not checked live". (caught by: reviewer K2)
- 2026-11-10 · The workbook and reply stated a cause for the September 2025 impression shift that no source in the session documented. State the measured shift on the client's own totals, not a cause. (caught by: reviewer U2)
- 2026-11-10 · A per-client check ran over every registry entry, inactive clients included, and the report named Snow and Arsenal. Filter `all` to active clients in any script that loops over the registry. (caught by: reviewer U6)
- 2026-11-10 · A missing test month was cached as 'no shift'. Record a check that could not run as untested, separately from a negative result. (caught by: reviewer C4)
