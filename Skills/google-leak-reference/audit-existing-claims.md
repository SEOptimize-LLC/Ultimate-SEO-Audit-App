# Audit of existing leak claims against the primary source

Checked against `google_api_content_warehouse` 0.4.0 (2,596 modules, 14,031 attributes), parsed from the Hex package by `scripts/build_index.py`.

## Name-level check (every leak identifier cited in Skills/, auditors/, prompts/, utils/, CLAUDE.md, app.py)

- 51 attribute names and 7 module names exist exactly as cited.
- 4 identifiers do not match (see below; `areaServed` is a schema.org term, not a leak attribute).

## Wrong, fix needed

| Where | Claim | Primary source says |
|---|---|---|
| seo-fundamentals-2026.md:664 | module `QualityAuthorityTopicEmbeddings` | Real module is `QualityAuthorityTopicEmbeddingsVersionedItem`. `siteFocusScore` ("how much a site is focused on one topic") and `siteRadius` ("how far page_embeddings deviate from the site_embedding") are confirmed. |
| click-signals-abc-framework.md:27 | module `QualityNavboostCrapsCrapsUrlSignals` | Does not exist. Real module is `QualityNavboostCrapsCrapsClickSignals`. |
| seo-fundamentals-2026.md:712, prompts/backlink_prompt.py:87, technical-seo-agent SKILL.md | `trustedAnchors` = seed-trust set, TrustRank-style | Not an attribute. Nearest are `IndexingDocjoinerAnchorSpamInfo.trusted*` (counts of trusted anchors used to compute anchor SPAM probability) and `IndexingDocjoinerAnchorTrustedInfo.trustedScore` ("fraction of pages with newsy anchors on the site, >0 for trusted sites"). Neither supports the seed-trust reading. |
| seo-fundamentals-2026.md:534 | `PerDocData` keeps ~20 prior page versions | The 20 is real but sits in `CompositeDocIndexingInfo.urlHistory`: "URL change history... we only keep the last 20 changes". Module is wrong; "prior page versions" is an inference. |

## Not in the attribute docs (may still be true, but not leak-derived)

- **13-month click window.** No attribute doc mentions it. It comes from DOJ testimony.
- **`goodClicks`, `badClicks`, `lastLongestClicks`** have empty descriptions. Their meanings are inferred. `unicornClicks` is documented ("clicks associated with an event from a Unicorn user").
- **Twiddler catalog.** The docs name only `SiteBoostTwiddler`, `FreshnessTwiddler` and `WebImageBoostTwiddler`. The table rows for NavBoost, host-crowding (QDD), official-page and local pack as twiddlers are not in the docs text.

## Confirmed by doc text

- `hostAge`: "used in twiddler to sandbox fresh spam in serving time."
- `siteAuthority`: "converted from quality_nsr.SiteAuthority, applied in Qstar."
- `bylineDate`, `syntacticDate`, `semanticDate`, `lastSignificantUpdate` all exist and are described as the framework states.
- `smallPersonalSite`: "Score of small personal site promotion."

## Version finding

Versions 0.2.0 to 0.4.0 carry about 2,590 modules. 0.5.0 onward carry 177 to 191, and only 174 of the 2,593 Model modules survive. Every SEO-relevant module cited in the project (`CompressedQualitySignals`, `QualityNsrNsrData`, `QualityNavboostCrapsCrapsData`, `PerDocData`, `AnchorsAnchor`) is absent from 0.5.0+.

## Scope of this audit

Name-level: complete. Meaning-level: 8 high-impact claims checked. The sentence-level pass over the remaining leak sections is not done.
