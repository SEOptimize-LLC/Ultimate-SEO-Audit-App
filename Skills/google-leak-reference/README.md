# Google Content Warehouse Leak Reference

A queryable copy of the leaked Google Content Warehouse API documentation (Elixir package `google_api_content_warehouse`), plus graded third-party commentary. Standalone and on-demand: nothing in the audit pipeline or the monthly workbook calls it.

## What is in it

| Piece | Where | Notes |
|---|---|---|
| Primary index | `data/leak.sqlite` (rebuilt, gitignored) | 6 package versions. 0.4.0 has 2,596 modules, 14,031 attributes, 4,407 cross-module links. |
| Module summaries | `summaries/module_summaries.jsonl` | One grounded summary and SEO grade (none, low, medium, high) for each of the 2,593 Model modules. Hand fixes in `overrides.jsonl`. |
| Commentary | `commentary/claims.jsonl` | 313 claims from 20 pages, each with the grader's call and a name check against the docs. Raw digests in `commentary/raw/`. |
| Audit of our own claims | `audit-existing-claims.md` | What the framework said about the leak vs what the docs say. |

## Use it

Commands and the rules for citing the docs live in [the registered skill](../../.claude/skills/google-leak-reference/SKILL.md), the single source for both.

Rebuild from scratch: `python scripts/build_index.py` (downloads the tarballs from repo.hex.pm, about 1.4 MB each, cached in `data/raw/`). After changing summaries or commentary: `merge_summaries.py` or `build_commentary.py`, then `build_index.py --offline`.

## Commentary sources, by what they were worth

Most useful (quote doc text, flag their own speculation): Mojo Dojo, Seirdy, MarketMuse, and the three hobo-web posts (leak overview, link building, product reviews). Mixed: Marketing Aid, Marie Haynes (intro post only), Endurtech, bmg360. Derivative of Mike King's original post: HulkApps, Trapilot, Endurtech. Discard: Dealers League (cites attributes that do not exist), Okoone, getfound, brainz, BlackCat (illustrative numbers shown as weights). Mojeek thread is nearly empty. The Digital Marketing Institute page could not be fetched.

## Working files

`data/batches/` and `data/summaries/` are scratch space from the one-time summarization run. They are safe to delete once `merge_summaries.py` has written `summaries/module_summaries.jsonl`, which is the committed result. `data/leak.sqlite` and `data/raw/` rebuild from `build_index.py`.

## Known limits

- Summaries were checked by script (every number and technical term must appear in the module's own source text) and by sampling. One hallucination was found and fixed. The check does not catch every plain-English slip.
- Commentary grades come from agents that read small-model digests of each page, not the raw pages.
- The sentence-level review of every leak claim in the framework reference files is not complete.
