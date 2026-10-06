---
name: google-leak-reference
description: Leaked Google Content Warehouse docs, queryable. Use before citing a leaked attribute or module in any deliverable, when judging a claim from leak commentary, or when finding which leaked fields cover a topic.
---

# Google leak reference

Run from the project root. The scripts and data live in `Skills/google-leak-reference/`; `lookup.py` reads `data/leak.sqlite` there. If the index is missing, run `python Skills/google-leak-reference/scripts/build_index.py` first (rebuild notes: `Skills/google-leak-reference/README.md`).

## Cite an attribute or module

1. `python Skills/google-leak-reference/scripts/lookup.py attr <name>` for an attribute, `module <name>` for a module.
2. Quote the doc text. Summaries are a model's reading and are for orientation only.
3. Tag the claim: **documented** (the doc text says it), **inferred** (the description is empty or the claim goes past the text), or **DOJ-derived** (the source is testimony, not these docs).

Done when every name in the draft came back exact from `lookup` and every claim sentence carries one tag.

Pre-delivery QA CHECK 14 runs `python Skills/google-leak-reference/scripts/check_leak_citations.py <file>` on the finished deliverable. Exit 1 (a name absent from the docs) or exit 2 (could not run) blocks delivery. The script proves names exist; the tags above are still yours to settle.

## Judge a claim from commentary

`python Skills/google-leak-reference/scripts/lookup.py claims <name>` shows what 20 commentary pages said, each with a grade and a name check. Treat the claim as a hypothesis, then settle it with step 1 above. A `verified` name check means the name exists; the claim built on it still needs the doc text.

## Find what the leak covers on a topic

`find <words>` searches names, descriptions and summaries. `seo high --prefix Quality` lists modules graded for SEO relevance. `module <name>` shows links in and out. `versions <name>` shows which package versions carry it.

## What the docs are

Names, types and short descriptions of fields. They carry no weights, and a field's existence shows a field, not a ranking factor. Say "documented" for a field and reserve "ranking lever" for sources that show one.

Two facts that cannot come from these docs: the 13-month NavBoost click window and the 70-day RankEmbedBERT window are DOJ testimony. `goodClicks`, `badClicks` and `lastLongestClicks` have empty descriptions, so their meanings are inferred.

Only package versions 0.2.0 to 0.4.0 hold the SEO modules; 0.5.0 onward is stripped to about 190.
