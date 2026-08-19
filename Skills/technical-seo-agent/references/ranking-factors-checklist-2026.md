# Ranking Factors Checklist (2026) — Leak-Grounded Master Audit Surface

> Executable audit checklist consolidating Daniel Foley Carter's "SEO Ranking Factors for 2026" (~100 distinct checks, built on the May 2024 Google Content Warehouse leak) into the Ultimate SEO Auditor's cluster/auditor split. This is a **checklist**, not a mechanics reference — for the deep "why" on each leak attribute, see `seo-fundamentals-2026.md` and `click-signals-abc-framework.md`. This document tells the agent *what to check, what grounds it, what it needs, and who already owns it*.

## How to read each row

Every checklist item carries four tags plus a pointer:

- **Leak attribute** — the leaked signal the check grounds in (exact spelling from the Content Warehouse leak), or `—` if the check is durable-principle-only with no single leaked attribute.
- **Input file** — the file (from the Expanded Input Stack) or live source the check requires. `crawl_internal.csv` is the only always-present input; every other input is optional and its absence means the dependent checks are **skipped-and-flagged**, never guessed.
- **Severity** — Critical / High / Medium / Low. Weight for prioritisation, not a promise of ranking movement (tag the *outcome type* per `.claude/rules/audit-workflow.md` when the finding reaches a deliverable).
- **Mode** — how the check runs: **Deterministic (SF/GSC column)** = read a column, apply a threshold; **LLM-judgment** = requires a model to read content and judge; **External tool** = needs a live fetch, DFS, GSC API, Playwright, Lighthouse, or a third-party tool.
- **Where covered** — the auditor module or skill that already executes this, or `GAP — see <file>` when the framework does not yet cover it (flag it in the deliverable as a manual/external check).

Leak-attribute names are **grounding evidence for the auditor's reasoning**, never surfaced in client-facing reports (per `.claude/rules/report-formatting.md` — no internal references).

---

## Stage Index — read this before walking the checklist

**Every variable belongs to a pipeline stage, and stage position is the primary sort.**

```
CRAWLABILITY → RENDERING → INDEXABILITY → RANKING
```

A failure at any stage makes every stage downstream of it unreachable. Severity and
Impact × Effort only break ties **within** a stage. Stage mechanics live in
[stage-1-crawlability.md](stage-1-crawlability.md),
[stage-2-rendering.md](stage-2-rendering.md),
[stage-3-indexability.md](stage-3-indexability.md).

### Why this index exists

This checklist holds **143 variables across 20 clusters**, distributed like this:

| Coverage | Variables | Share |
|---|---|---|
| Clusters 1–4 (gating stages 1–3) | 27 | 18.9% |
| Clusters 5–20 (predominantly stage 4) | 116 | 81.1% |

Severity does not rescue you from that imbalance: only **4 of 143 rows are Critical** (all
four fall in clusters 1–3), against 43 High, 65 Medium and 31 Low. Walking the clusters in
numeric order therefore spends roughly four fifths of the audit effort on ranking variables
that cannot pay out until the three gating stages pass. **Sort by stage first, then walk
severity inside the stage.**

### Cluster → stage map

| Cluster | Primary stage | Notes |
|---|---|---|
| 1 Crawl Accessibility & Bot Access | **1** | 3 rows are dual with stage 2 (see exceptions) |
| 2 Rendering & JavaScript | **2** | 3 rows are actually stage 4 (see exceptions) |
| 3 Indexation & Canonicalization | **3** | Clean. Carries the mandatory directive verdict |
| 4 Non-Value Content & Crawl Budget | **SPLIT 1 / 3** | Genuinely two stages in one cluster |
| 5 On-Page (Titles / Meta / Headings) | 4 | |
| 6 Content Quality & Originality | 4 | **Also the stage-3 index gate.** "Crawled, not indexed" is a quality judgment |
| 7 Relevance & Query Matching | 4 | |
| 8 Internal Linking & Anchors | **DUAL 1 + 4** | Discovery mechanism at stage 1, PageRank and anchor signals at stage 4 |
| 9 Backlinks & Off-Page | 4 | External links are also a stage-1 discovery path |
| 10 Click Signals & User Behaviour | 4 | Post-ranking feedback. Cannot fire until indexed |
| 11 Domain-Level Quality & NSR | 4 | |
| 12 Demotions, Spam & Suppression | 4 | |
| 13 SERP Context & Twiddlers | 4 | Re-rankers, strictly post-index |
| 14 Schema & Structured Data | **3 + 4** | Index comprehension and SERP-feature eligibility |
| 15 Freshness & Dates | 4 | Interacts with stage-1 crawl frequency |
| 16 Page Experience & UX | 4 | |
| 17 Locale & International | **SPLIT 3 / 4**, evenly | hreflang and international duplication are index-selection (3); click-signal slicing and locality signals are ranking (4). Commonly misfiled wholesale as "international SEO" |
| 18 Entity, Author & Brand | 4 | |
| 19 AI Search / LLM Visibility | **SPANS 1 + 2 + 4** | Crawler access (1), no JS rendering (2), citation selection (4) |
| 20 Discover Visibility | 4 | `max-image-preview` is a robots directive, so a stage-3 dependency |

### Per-row exceptions (rows whose stage differs from their cluster)

**Cluster 1, dual with stage 2:**
- "Are CSS/JS resources crawlable so the page can render?" — stage-1 cause, stage-2 effect
- "Is primary nav present in raw DOM (no JS-only navigation)?" — detected at stage 2, but the damage is stage-1 discovery
- "Is content served to GPTBot / ClaudeBot / PerplexityBot?" — "not blocked" is stage 1, "not JS-gated" is stage 2

**Cluster 2, actually stage 4:**
- "Is above-the-fold dominated by content vs ad/clutter density?" (`clutterScore`) — page-experience quality
- "Does layout give visual weight to the primary terms?" (`avgTermWeight`) — relevance
- "Is the key answer above the LLM token-truncation threshold?" — AI citation selection, delivery-dependent on stage 2

**Cluster 4, split:**
- Stage 1: "Discovered — not indexed" crawl-budget/internal-link starvation; crawl budget wasted on parameter/faceted/paginated URLs
- Stage 3: aged/stagnant zero-traffic pages in lower index tiers; non-value pages to eliminate (also stage-4 site quality)

**Cluster 6 — Content Quality & Originality. The conditional rule, and the most important
item in this index.**

**The same quality variable changes stage depending on index status.**

- **Page NOT indexed** → the quality rows are **Stage 3**. They *are* the index gate.
  "Crawled, currently not indexed" is Google declining to store the document on quality
  grounds, so `OriginalContentScore`, `contentEffort` and information-gain findings are
  indexability findings on those URLs.
- **Page IS indexed but not ranking** → the same rows are **Stage 4**.

Check index status before assigning severity to any quality finding. And per
[stage-2-rendering.md](stage-2-rendering.md), check the raw HTML first: if the raw document is
hollow, the "quality" problem is a Stage 2 render failure and no content work will fix it.

One further row: "Does the page fit the site's own embedding" (`siteRadius`, `pageEmbedding`)
is Stage 4, but the semantic map that computes it is built from crawled body text, so it
inherits the Stage 2 verdict. A render gap produces wrong clusters.

**Cluster 8 — Internal Linking & Anchors. Genuinely three-way split.**

| Row | Stage |
|---|---|
| Internal anchors describe the destination (`anchorMismatchDemotion`) | **4** |
| Important internal links placed high, not just footer | **4** equity, **1** discovery |
| Internal links point directly to 200s, not through redirects | **1** |
| High-authority pages linking out to money pages | **4** |
| **Dropped anchors: links present in raw HTML but lost in render** | **2** |
| Click depth ≤3 for money pages | **1** |

The dropped-anchors row is worth noting because it is the **inverse** of the usual render
failure. Normally links exist after JS and not in raw. Here they exist in raw and are
destroyed by the render, which means the crawler may follow them but a rendering-dependent
consumer will not. It is a Stage 2 finding either way.

**Cluster 14 — Schema & Structured Data. One row is misfiled.**

| Row | Stage |
|---|---|
| Valid, non-misleading schema for the page type | **4** |
| Person/Organization schema `@id`-connected for the entity graph | **4** |
| Structured data machine-parseable for AI/LLM grounding | **4**, with a **Stage 2** dependency: it must be in raw HTML for non-rendering AI crawlers |
| **Self-referential canonicals on every indexable page** | **3 — misfiled.** This is a canonical check and belongs in Cluster 3. Also note it is **Low / non-binding** where no duplication exists |

**Cluster 17 — Locale & International. A clean 50/50 split, not "Stage 3 primary".**

| Row | Stage |
|---|---|
| hreflang in exactly one location, valid return tags, `x-default` | **3** — index selection per locale |
| International duplication controlled (subfolders over subdomains/TLDs) | **3** — duplication and canonicalisation |
| Click signals sliced correctly by country/language | **4** |
| Localness signals aligned for the target market (`localityScore`) | **4** |

**Cluster 19 — AI Search / LLM Visibility. One row gates the other five.**

| Row | Stage |
|---|---|
| **Can AI crawlers access content without JS (raw-HTML answerability)?** | **1 access + 2 rendering. Run this first.** |
| Brand cited in AI Overviews, and how often | **4** — outcome measurement |
| Content chunk-extractable for AI grounding | **4** |
| Brand present in LLM training/grounding data | **4** |
| Factual claims consistent across the web | **4** |
| Competitor share of voice in AI answers | **4** |

Most AI crawlers do not execute JavaScript. If the raw-HTML row fails, the five Stage 4 rows
cannot pay out no matter how well the content is optimised, because the crawler never sees it.

### Execution rule

1. **Gate on stages 1–3 first.** Run clusters 1, 2, 3, and the stage-1 rows of cluster 4.
   That is 27 variables and it contains all four Critical rows.
2. **Return an explicit verdict per stage, including "clean".** A missing stage verdict is
   an audit defect, on the same contract as the indexability-directive verdict.
3. **Do not begin cluster 5 onward until stages 1–3 are clean or the failures are
   documented as blockers.** Ranking work on a page that cannot be crawled, rendered or
   indexed produces no return, and recommending it inflates the deliverable with items that
   cannot move.
4. **Inside a stage, sort by Severity, then Impact × Effort.**
5. **Tag the outcome type** on every recommendation per `.claude/rules/audit-workflow.md`.
   Stage-1-to-3 fixes that unblock previously invisible content are **Ranking Levers**, not
   Infrastructure Hygiene.

### Coverage status of this index

**Row-level assignment is complete for every cluster that needed it.** Clusters 1–4 were
assigned row by row, and clusters 6, 8, 14, 17 and 19 (the dual and split ones) are assigned
row by row above. The remaining clusters — 5, 7, 9, 10, 11, 12, 13, 15, 16, 18, 20 — are
uniformly Stage 4 and need no row-level exceptions, because every row in them is a
post-index comparative signal.

**What the row-level pass changed, beyond adding tags:**

1. **Cluster 6 is conditional, not fixed.** Quality variables sit at Stage 3 when the page is
   not indexed and Stage 4 when it is. This is the only conditional assignment in the
   checklist and it is the one most likely to be got wrong.
2. **Cluster 8 splits three ways**, not two: Stage 1, 2 and 4 all appear inside six rows.
3. **One row is misfiled.** "Self-referential canonicals on every indexable page" sits in
   Cluster 14 (Schema) and belongs in Cluster 3 (Indexation). Left in place to avoid breaking
   the auditor-module mapping in the "Where covered" column, but tagged Stage 3.
4. **Cluster 17 is a 50/50 split**, not "Stage 3 primary" as the cluster-level map first
   recorded. That table has been corrected.
5. **Cluster 19 has an internal gate.** The raw-HTML answerability row must run before the
   five Stage 4 rows, or the audit optimises content that no AI crawler can read.

---

## Cluster 1 — Crawl Accessibility & Bot Access

Can Google and the AI crawlers reach, fetch, and follow the site at all? (Foley Carter cat. 1 ACCESSIBILITY.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Does `robots.txt` return 200 and not block critical paths? | — | Live fetch | Critical | External tool | `technical_auditor.py` |
| Are CSS/JS resources crawlable (not `Disallow`-ed) so the page can render? | — | Live fetch + `crawl_internal.csv` | High | External tool | `technical_auditor.py` / `javascript_rendering_auditor.py` |
| Does every important URL have sufficient internal inlinks (not orphaned)? | `scaledSelectionTierRank` | `crawl_internal.csv` | High | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Is primary nav present in raw DOM (no JS-only navigation)? | — | `crawl_internal.csv` (rendered vs raw) | High | Deterministic (SF/GSC column) | `javascript_rendering_auditor.py` |
| Are HTTP status codes consistent (no 200/redirect/404 conflicts for the same content)? | — | `crawl_internal.csv` | High | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Is redirect-chain depth ≤1 hop (no chains bleeding equity per hop)? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Does crawl frequency/demand match URL importance (money pages crawled often)? | `scaledSelectionTierRank` | GSC crawl stats / server logs | Medium | External tool | GAP — see `technical-seo-agent/SKILL.md` |
| Is the server reliable under load (no 5xx / timeouts / hostload throttling)? | — | Live fetch / server logs | High | External tool | GAP — see `technical-seo-agent/SKILL.md` |
| Is content served to GPTBot / ClaudeBot / PerplexityBot (not blocked or JS-gated)? | — | Live fetch (UA spoof) + `robots.txt` | High | External tool | `Skills/ai-search-optimization` |

## Cluster 2 — Rendering & JavaScript

What content actually survives to the rendered DOM and the LLM token window? (Foley Carter cat. 2 RENDERING.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Does critical content appear in raw-DOM (raw vs rendered-DOM diff)? | — | `crawl_internal.csv` (both views) | Critical | Deterministic (SF/GSC column) | `javascript_rendering_auditor.py` |
| Is the page SSR (not client-only), and does GSC URL Inspection confirm the rendered view? | — | GSC URL Inspection | High | External tool | `javascript_rendering_auditor.py` |
| What % of content is gated behind JS interaction (tabs/accordions not in DOM)? | — | Live fetch (Playwright) | High | External tool | `javascript_rendering_auditor.py` |
| Is the key answer above the LLM token-truncation threshold (early in the DOM)? | — | Live fetch | Medium | LLM-judgment | `Skills/ai-search-optimization` |
| Is above-the-fold dominated by content vs ad/clutter density? | `clutterScore` | Live fetch | High | External tool | `mobile_first_auditor.py` |
| Does layout give visual weight to the primary terms (not buried in boilerplate)? | `avgTermWeight` | Live fetch | Low | LLM-judgment | GAP — see `onpage-seo-agent/SKILL.md` |
| Is mobile render parity intact (mobile DOM == desktop DOM content)? | — | `crawl_internal.csv` + live fetch | Critical | External tool | `mobile_first_auditor.py` |

## Cluster 3 — Indexation & Canonicalization

Is Google indexing the URLs we want, on the canonicals we chose? (Foley Carter cat. 1/6.)

> **Per-state diagnostic playbook:** the rows below (and Cluster 4's) flag *which* indexation states to check; for *how* to diagnose and remediate each GSC Page-Indexing status — Discovered/Crawled-not-indexed, the duplicate/canonical states, Page-with-redirect, Soft 404, `noindex`/robots blocks — with a cause → remediation → validation for each, see **[gsc-indexation-states.md](gsc-indexation-states.md)**. It also carries the always-verify rule (GSC counts run ahead of live truth; slug/trailing-slash/stale-404 traps) validated across live client checks.
>
> **REQUIRED indexability-directive verdict (full-site AND single-URL).** The four directive checks in the last two rows of this cluster — meta robots `noindex` (head-level), `X-Robots-Tag` header `noindex`, body-placed (invalid/ignored) `noindex`, and declared-vs-Google-selected canonical divergence — are **non-negotiable on every audit**, whether a full-site crawl or a single-URL audit. A missing indexability verdict is an audit defect. On a single-URL audit the input is one live fetch: `curl -I <url>` for the response headers plus a `<head>` inspection for the robots/canonical directives. Full method in **[technical-seo-agent/SKILL.md](../SKILL.md)** → "REQUIRED — Indexability-Directive Verdict."

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Does the declared canonical match Google's selected canonical (report the gap, not just the declared value)? | — | GSC URL Inspection | High | External tool | `technical_auditor.py` |
| Are money pages actually indexed (not "Crawled — currently not indexed")? | — | `gsc_crawled_not_indexed.csv` | Critical | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Is the "Crawled — not indexed" set a content-quality signal (cross-ref word count)? | `OriginalContentScore` | `gsc_crawled_not_indexed.csv` + `crawl_internal.csv` | High | Deterministic (SF/GSC column) | `content_pruning_auditor.py` |
| Is canonical reliance excessive (fixing dup with canonicals instead of consolidating)? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Are URL parameters generating duplicate indexable variants? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `url_structure_auditor.py` |
| Is `noindex` correctly placed in `<head>` (a body-placed `noindex` is invalid — Google ignores it, so the page is actually indexable) and not stale in robots.txt? | — | Live fetch / `crawl_internal.csv` | High | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Is a `noindex` set via the `X-Robots-Tag` **HTTP response header** (invisible in view-source, cross-ref header vs meta)? | — | Live fetch (`curl -I`) / `crawl_internal.csv` | High | External tool | `technical_auditor.py` |

## Cluster 4 — Non-Value Content & Crawl Budget

Prune the dead weight that dilutes site quality and burns crawl budget. (Foley Carter cat. 6 NON-VALUE CONTENT.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Which "Discovered — not indexed" URLs signal crawl-budget/internal-link starvation? | — | `gsc_discovered_not_indexed.csv` + `crawl_internal.csv` | High | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Are there non-value pages to eliminate or consolidate (thin, near-dup, obsolete)? | `pandaDemotion` | `crawl_internal.csv` | High | LLM-judgment | `content_pruning_auditor.py` |
| Are aged/stagnant zero-traffic pages sitting in lower index tiers? | `scaledSelectionTierRank` | `crawl_internal.csv` + `gsc_performance.csv` | Medium | Deterministic (SF/GSC column) | `content_pruning_auditor.py` |
| Is crawl budget being wasted on parameter/faceted/paginated URLs? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `ecommerce_patterns_auditor.py` |

## Cluster 5 — On-Page (Titles / Meta / Headings)

The SERP-facing elements and heading structure. (Foley Carter cat. 4/8.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Does the title align with the page's target query (front-loaded, intent-matched)? | `titlematchScore` | `crawl_internal.csv` + `gsc_performance.csv` | High | LLM-judgment | `onpage_auditor.py` |
| Is there exactly one H1, with a logical H2/H3 hierarchy? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `onpage_auditor.py` |
| Does the meta description promise the specific deliverable (not boilerplate)? | — | `crawl_internal.csv` | Low | LLM-judgment | `onpage_auditor.py` |
| Are titles/metas duplicated across URLs (cannibalization signal)? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `onpage_auditor.py` |
| Is the title free of clickbait that mismatches page content (badClicks risk)? | `badClicks` | `crawl_internal.csv` + live fetch | Medium | LLM-judgment | `onpage_auditor.py` |

## Cluster 6 — Content Quality & Originality

Is the body genuinely useful, original, and effortful? (Foley Carter cat. 4 QUALITY.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Does the page open answer-first (info prioritisation, no throat-clearing)? | — | Live fetch | Medium | LLM-judgment | `onpage-seo-agent/SKILL.md` |
| Does short-content carry genuine originality (not templated/scraped boilerplate)? | `OriginalContentScore` | `crawl_internal.csv` + live fetch | High | LLM-judgment | `content_pruning_auditor.py` |
| Does the page show real effort (depth, media, tooling — not low-effort filler)? | `contentEffort` | Live fetch | High | LLM-judgment | GAP — see `onpage-seo-agent/SKILL.md` |
| Does it offer information gain vs what already ranks (not a rehash)? | `contentEffort` | Live fetch + DFS SERP | High | LLM-judgment | `competitor_auditor.py` |
| Is YMYL content routed through elevated E-E-A-T scrutiny? | `ymylHealthScore`, `ymylNewsScore` | Live fetch | High | LLM-judgment | `seo-audit-methodology/SKILL.md` |
| Are E-E-A-T sub-criteria present (named author, byline, citations, establishment)? | `unauthoritativeScore` | Live fetch | High | LLM-judgment | `seo-audit-methodology/SKILL.md` |
| Are YMYL sub-criteria present (regulatory/compliance/safety signals)? | `ymylHealthScore` | Live fetch | High | LLM-judgment | `seo-audit-methodology/SKILL.md` |
| Is the content free of keyword-stuffing / gibberish patterns? | — | `crawl_internal.csv` + live fetch | Medium | LLM-judgment | `onpage_auditor.py` |
| Does the page add unique value via original media/embeddings (not stock only)? | — | Live fetch | Low | LLM-judgment | GAP — see `onpage-seo-agent/SKILL.md` |
| Is the content structured/readable (headings, short paragraphs, skimmable)? | — | Live fetch | Low | LLM-judgment | `onpage_auditor.py` |
| Is tone/style/sentiment internally consistent (no spun/patchwork drift)? | — | Live fetch | Low | LLM-judgment | GAP — see `onpage-seo-agent/SKILL.md` |
| Do claims carry citations to primary sources? | — | Live fetch | Medium | LLM-judgment | `seo-audit-methodology/SKILL.md` |
| Does the page fit the site's own embedding (page-vs-site topic fit)? | `siteRadius`, `pageEmbedding` | `topical_map_koray.md` | Medium | External tool | `topical_authority_auditor.py` |
| If UGC/comments exist, is discussion quality high (not thin/spam)? | `ugcDiscussionEffortScore` | Live fetch | Low | LLM-judgment | GAP — see `onpage-seo-agent/SKILL.md` |

## Cluster 7 — Relevance & Query Matching

Does the page actually satisfy the query, semantically and at passage level? (Foley Carter cat. 8 RELEVANCE/QUERY.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Is the page's intent classification aligned with the target query's intent? | — | `gsc_performance.csv` + DFS intent | High | LLM-judgment | `onpage-seo-agent/SKILL.md` |
| Does the page cover topicality T* (term match, salience, synonyms)? | — | Live fetch + DFS SERP | Medium | LLM-judgment | `onpage-seo-agent/SKILL.md` |
| Is page-vs-query embedding similarity strong for the target term? | `pageEmbedding` | `topical_map_koray.md` | Medium | External tool | `topical_authority_auditor.py` |
| Is the answer extractable at passage/chunk level (retrievable snippets)? | — | Live fetch | Medium | LLM-judgment | `Skills/ai-search-optimization` |
| Is a clean snippet extractable for featured-snippet eligibility? | — | Live fetch | Low | LLM-judgment | `onpage-seo-agent/SKILL.md` |
| Does the query deserve freshness (QDF), and does the page satisfy it? | — | `gsc_performance.csv` | Low | LLM-judgment | `date_freshness_auditor.py` |
| Is there a strong historical query–URL association (established relevance)? | — | `gsc_performance.csv` | Medium | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Is NLP/topical coverage complete vs the SERP competitor set? | — | DFS SERP + live fetch | Medium | LLM-judgment | `competitor_auditor.py` |
| Are the page's entities mapped to the knowledge graph (entity coverage)? | — | Live fetch | Low | LLM-judgment | `Skills/ai-search-optimization` |
| Are sub-links (internal) topically relevant to the page? | `anchorMismatchDemotion` | `crawl_internal.csv` | Low | Deterministic (SF/GSC column) | `anchor_quality_auditor.py` |

## Cluster 8 — Internal Linking & Anchors

The site's own link graph — weighting, placement, anchor relevance. (Foley Carter cat. 9 LINKS.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Do internal anchors describe the destination topic (no anchor mismatch)? | `anchorMismatchDemotion` | `anchors_internal.csv` | High | Deterministic (SF/GSC column) | `anchor_quality_auditor.py` |
| Are important internal links placed high (body/nav) not just footer? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Are internal links pointing directly to 200s (not through redirects)? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Are high-authority pages (homepage) linking out to money pages? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Are there dropped anchors (links present in raw HTML but lost in render)? | — | `crawl_internal.csv` (raw vs rendered) | Medium | Deterministic (SF/GSC column) | `javascript_rendering_auditor.py` |
| Is click depth ≤3 for money pages? | — | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `crawl-depth-analysis` skill |

## Cluster 9 — Backlinks & Off-Page

The external link graph — tier, trust, velocity, relevance. (Foley Carter cat. 9 LINKS/PAGERANK.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| What tier are the referring source pages in (high vs low quality)? | `sourceType` (`TYPE_HIGH_QUALITY`…) | `backlinks_semrush.csv` | High | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Is referring-domain strength / PageRank distribution healthy? | — | `backlinks_semrush.csv` | High | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Is there an anchor-text spam spike (velocity, not just volume)? | `phraseAnchorSpamRate`, `phraseAnchorSpamDemoted`, `phraseAnchorSpamPenalty` | `backlinks_semrush.csv` | High | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Are inbound anchors seed-trusted (near trusted seed sites)? | `trustedAnchors` | `backlinks_semrush.csv` | Medium | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Is link value weighted by the linking site's homepage trust? | — | `backlinks_semrush.csv` | Medium | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Are source pages fresh vs disk-tier (velocity/spam-spike check)? | `TYPE_FRESHDOCS`, `sourceType` | `backlinks_semrush.csv` | Medium | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Do inbound anchors match this site's topic (external relevance)? | `anchorMismatchDemotion` | `backlinks_semrush.csv` | Medium | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Is link inflow consistent over time (no anchor-change spikes)? | `phraseAnchorSpamDays`, `phraseAnchorSpamStart`/`End` | `backlinks_semrush.csv` | Medium | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Do outbound links avoid known spammers? | `spamrank` | `crawl_internal.csv` + live fetch | Medium | External tool | GAP — see `technical-seo-agent/SKILL.md` |
| Is source-to-target relevance present (topically aligned linking sites)? | — | `backlinks_semrush.csv` | Low | LLM-judgment | `backlink_auditor.py` |

## Cluster 10 — Click Signals & User Behaviour (NavBoost)

In-SERP behaviour as a ranking input — earned, never manipulated. (Foley Carter cat. 3 DEMONSTRATED BEHAVIOUR. Full mechanics in `click-signals-abc-framework.md`.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Does the URL earn good clicks vs similar-position peers? | `goodClicks`, `badClicks` | `gsc_performance.csv` | High | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Is position-adjusted CTR below the expected baseline (NavBoost/CRAPS)? | `goodClicks` | `gsc_performance.csv` | High | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Is there return-to-SERP / pogo-sticking behaviour (coverage vs interaction)? | `badClicks` | `gsc_performance.csv` | Medium | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Does the page win the session-ending click? | `lastLongestClicks` | `gsc_performance.csv` | Medium | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Are branded search + repeat/direct visits present (demand signal)? | `chromeInTotal`, `directFrac` | `gsc_performance.csv` | Medium | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Is site-level Chrome/direct traffic feeding a sitewide signal? | `chromeInTotal` | GA4 / GSC | Low | External tool | GAP — see `click-signals-abc-framework.md` |
| Is the click data being read across the correct 13-month window? | — | `gsc_performance.csv` | Low | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Are click signals sliced correctly by country/device/language? | — | `gsc_performance.csv` | Low | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Is the analysis avoiding manipulation-prone raw signals (squashed/voter tokens/unicornClicks)? | `unicornClicks` | `gsc_performance.csv` | Low | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| At host/topic level, do impressions convert to clicks (or is coverage wasted)? | `impressions` | `gsc_performance.csv` | Medium | Deterministic (SF/GSC column) | `click_signal_auditor.py` |

## Cluster 11 — Domain-Level Quality & NSR

The sitewide tailwind or headwind applied to every page. (Foley Carter cat. 5 DOMAIN QUALITY.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| What is the aggregated site-quality / NSR direction (baseline vs trajectory)? | `nsr`, `predictedDefaultNsr`, `priorAdjustedNsr` | `crawl_internal.csv` (site-wide) | High | LLM-judgment | `topical_authority_auditor.py` |
| Is the site topically focused (focus score) with low page drift (radius)? | `siteFocusScore`, `siteRadius`, `site2vecEmbedding` | `topical_map_koray.md` | High | External tool | `topical_authority_auditor.py` |
| Is quality consistent across URLs (no high-variance thin-page tail)? | `siteQualityStddev` | `crawl_internal.csv` | Medium | Deterministic (SF/GSC column) | `content_pruning_auditor.py` |
| Does homepage trust propagate to new/deep pages? | — | `crawl_internal.csv` | Low | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Is the domain past sandbox (host age), or eligible for small-personal-site promotion? | `hostAge`, `smallPersonalSite` | Live fetch (WHOIS) | Medium | External tool | GAP — see `seo-fundamentals-2026.md` |
| Are trust indicators present (brand, links, reviews, searches, sentiment)? | `siteAuthority` | Live fetch + DFS | Medium | LLM-judgment | `backlink_auditor.py` |
| Is the site predominantly AI-generated (site-level AGC risk)? | `racterScores` | `crawl_internal.csv` + live fetch | High | LLM-judgment | GAP — see `seo-fundamentals-2026.md` |
| Do site media scores apply (video/image/shopping-focused classification)? | `videoScore`, `imageQualityClickSignals`, `shoppingScore` | `crawl_internal.csv` | Low | Deterministic (SF/GSC column) | GAP — see `technical-seo-agent/SKILL.md` |

## Cluster 12 — Demotions, Spam & Suppression

The named penalties — diagnostic when a site underperforms. (Foley Carter cat. 10 DEMOTIONS/SPAM + cat. 7 SITE BEHAVIOUR.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Is a Panda/thin-content demotion likely (long tail of thin/templated pages)? | `pandaDemotion`, `babyPandaDemotion`, `babyPandaV2Demotion` | `crawl_internal.csv` | High | LLM-judgment | `content_pruning_auditor.py` |
| Is nav demotion likely (confusing structure, dead-ends, missing breadcrumbs)? | `navDemotion` | `crawl_internal.csv` + live fetch | Medium | LLM-judgment | `technical_auditor.py` |
| Is SERP demotion likely (user-dissatisfaction click feedback)? | `serpDemotion` | `gsc_performance.csv` | High | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Is the domain an exact-match keyword domain (EMD headwind)? | `exactMatchDomainDemotion` | Live fetch | Low | Deterministic (SF/GSC column) | GAP — see `seo-fundamentals-2026.md` |
| Are scam/unauthoritative signals present (fake urgency, hidden costs, no credentials)? | `scamness`, `unauthoritativeScore` | Live fetch | High | LLM-judgment | `seo-audit-methodology/SKILL.md` |
| Is a low-quality / VLQ flag likely (NSR-derived)? | `lowQuality` | `crawl_internal.csv` | Medium | LLM-judgment | `content_pruning_auditor.py` |
| For review content, is a product-review demotion likely (templated "best of" pages)? | `productReviewPDemotePage`, `productReviewPDemoteSite` | Live fetch | Medium | LLM-judgment | GAP — see `onpage-seo-agent/SKILL.md` |
| Is a location/localness demotion at play? | `localityScore` | Live fetch + DFS local | Low | External tool | `local_seo_auditor.py` |
| Are inbound-link-spam patterns present (SpamBrain neutralisation candidates)? | `spambrainTotalDocSpamScore`, `spamrank` | `backlinks_semrush.csv` | Medium | Deterministic (SF/GSC column) | `backlink_auditor.py` |
| Are there scaled-content / site-reputation / expired-domain abuse patterns? | `racterScores` | `crawl_internal.csv` + live fetch | High | LLM-judgment | GAP — see `seo-fundamentals-2026.md` |
| Are there suspicious behaviour-over-time spikes (content production, sudden URL inflows, quality shifts, domain consolidations)? | — | `crawl_internal.csv` + GSC | Medium | Deterministic (SF/GSC column) | `Skills/traffic-loss-analysis` |

## Cluster 13 — SERP Context & Twiddlers

Post-scoring re-rankers and SERP-shape effects. (Foley Carter cat. 12 TWIDDLERS.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Are post-scoring re-rankers in play (freshness / click / official-page boost)? | — | DFS SERP | Low | External tool | GAP — see `technical-seo-agent/SKILL.md` |
| Is host-crowding / result-diversity capping the site's SERP footprint? | — | DFS SERP | Low | External tool | `cannibalization_auditor.py` |
| Is the page eligible for SERP features (snippets / PAA / AIO)? | — | DFS SERP + live fetch | Medium | External tool | `Skills/ai-search-optimization` |
| Is the query in a sensitive vertical with whitelist/quality gates (YMYL)? | `ymylHealthScore`, `ymylNewsScore` | Live fetch + DFS | Medium | LLM-judgment | `seo-audit-methodology/SKILL.md` |
| Are personalisation/locale re-ranking effects distorting the observed SERP? | — | DFS SERP (localised) | Low | External tool | `local_seo_auditor.py` |
| Is a gold-standard / golden-document flag applied to a competitor result? | — | DFS SERP | Low | External tool | GAP — see `technical-seo-agent/SKILL.md` |

## Cluster 14 — Schema & Structured Data

Machine-readable markup for rich results and entity building. (Foley Carter cat. 11/15.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Is valid, non-misleading schema present for the page type (Article/Product/Service/LocalBusiness)? | — | `crawl_internal.csv` + live fetch | Medium | External tool | `technical_auditor.py` |
| Are Person/Organization schema present and `@id`-connected for the entity graph? | — | Live fetch | Medium | External tool | `Skills/ai-search-optimization` |
| Is structured data machine-parseable for AI/LLM grounding? | — | Live fetch | Medium | External tool | `Skills/ai-search-optimization` |
| Do self-referential canonicals exist on every indexable page? | — | `crawl_internal.csv` | Low | Deterministic (SF/GSC column) | `technical_auditor.py` |

## Cluster 15 — Freshness & Dates

Freshness where the query demands it, with aligned date signals. (Foley Carter cat. 4 QUALITY / dates.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| For freshness-sensitive queries, is `lastSignificantUpdate` genuinely recent (not cosmetic)? | `lastSignificantUpdate` | `content_dates.csv` | Medium | Deterministic (SF/GSC column) | `date_freshness_auditor.py` |
| Do byline / syntactic / semantic dates agree (no date-unreliability flag)? | `semanticDate`, `bylineDate`, `syntacticDate`, `dateUnreliabilityInfo` | `content_dates.csv` | High | Deterministic (SF/GSC column) | `date_freshness_auditor.py` |
| Do sitemap `<lastmod>`, HTTP `Last-Modified`, and structured-data dates align with the visible byline? | `QualityTimebasedDateUnreliability` | `content_dates.csv` + live fetch | Medium | External tool | `date_freshness_auditor.py` |
| Is there a healthy update history (~20-version content history vs one-and-done)? | — | `content_dates.csv` | Low | Deterministic (SF/GSC column) | `date_freshness_auditor.py` |

## Cluster 16 — Page Experience & UX

Real-user experience signals. (Foley Carter cat. 13 PAGE EXPERIENCE.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Do field-data Core Web Vitals pass (LCP < 2.5s, INP < 200ms, CLS < 0.1)? | — | CrUX / Lighthouse | High | External tool | `core-web-vitals` skill |
| Is the page mobile-usable with content parity? | — | Live fetch + `crawl_internal.csv` | High | External tool | `mobile_first_auditor.py` |
| Is HTTPS enforced site-wide (HTTP → HTTPS 301, no mixed content)? | — | `crawl_internal.csv` + live fetch | High | Deterministic (SF/GSC column) | `technical_auditor.py` |
| Are intrusive interstitials / excessive ad density present (clutter demotion)? | `clutterScore` | Live fetch | Medium | External tool | `mobile_first_auditor.py` |
| Can the user complete the task easily (clear path, no hostile UX)? | `navDemotion` | Live fetch | Low | LLM-judgment | GAP — see `onpage-seo-agent/SKILL.md` |

## Cluster 17 — Locale & International

Language/region targeting and international duplication. (Foley Carter cat. 14 LOCALE.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Are click signals correctly sliced by country/language (no cross-locale bleed)? | — | `gsc_performance.csv` | Low | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Is hreflang implemented in exactly one location with valid return tags + `x-default`? | — | `crawl_internal.csv` + live fetch | Medium | External tool | `technical_auditor.py` |
| Is international duplication controlled (subfolders over subdomains/TLDs)? | — | `crawl_internal.csv` | Low | Deterministic (SF/GSC column) | `url_structure_auditor.py` |
| Are localness/locality signals aligned for the target market? | `localityScore` | Live fetch + DFS local | Low | External tool | `local_seo_auditor.py` |

## Cluster 18 — Entity, Author & Brand

Who is behind the content, and is the brand a recognised entity? (Foley Carter cat. 11 ENTITY/AUTHOR/BRAND.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Is the author a consistent cross-web entity with bio/credentials? | `authorObfuscatedGaiaStr` | Live fetch | Medium | LLM-judgment | `seo-audit-methodology/SKILL.md` |
| Are Person/Organization schema + Knowledge Panel signals in place? | — | Live fetch | Medium | External tool | `Skills/ai-search-optimization` |
| Is publisher establishment clear (about / contact / ownership pages)? | — | Live fetch | Medium | LLM-judgment | `seo-audit-methodology/SKILL.md` |
| Is there brand-search demand and entity-topic association? | `chromeInTotal` | `gsc_performance.csv` + DFS | Medium | Deterministic (SF/GSC column) | `click_signal_auditor.py` |
| Is off-site sentiment/reputation and NAP/entity consistency intact? | — | Live fetch + DFS listings | Medium | External tool | `local_seo_auditor.py` |

## Cluster 19 — AI Search / LLM Visibility (GEO/AEO)

Visibility inside AI Overviews and LLM answers. (Foley Carter cat. 15 AI/LLM VISIBILITY.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Is the brand included/cited in AI Overviews, and how frequently? | — | DFS LLM mentions | High | External tool | `Skills/ai-search-optimization` |
| Is content chunk-extractable for AI grounding (retrievable passages)? | — | Live fetch | Medium | LLM-judgment | `Skills/ai-search-optimization` |
| Is the brand present in LLM training/grounding data (share of voice)? | — | DFS LLM mentions | Medium | External tool | `Skills/ai-search-optimization` |
| Are factual claims consistent across the web (no contradictory entity data)? | — | Live fetch + DFS | Medium | LLM-judgment | `Skills/ai-search-optimization` |
| Can AI crawlers access content without JS (raw-HTML answerability)? | — | Live fetch (UA spoof) | High | External tool | `javascript_rendering_auditor.py` |
| What is the competitor share of voice in AI answers for target queries? | — | DFS LLM mentions | Medium | External tool | `competitor_auditor.py` |

## Cluster 20 — Discover Visibility

Is the site eligible for Google Discover — the personalised content feed that surfaces content **outside a query**? A separate traffic channel with its own GSC report, invisible to a standard SERP audit. **Inclusion is non-deterministic** — these are eligibility signals that raise/lower probability, never pass/fail rules; ship every finding as "raises Discover probability" with the guideline caveat. Full reference: `Skills/ai-search-optimization/references/google-discover.md`. (Mostly a blog/editorial opportunity; not applicable to purely transactional sites with no content library — say so rather than manufacturing a finding.)

| Audit question | Leak attribute | Input file | Severity | Mode | Where covered |
|---|---|---|---|---|---|
| Does the site earn any Discover impressions (is the Discover report populated)? | — | GSC Discover report | Medium | External tool | `discover_auditor.py` / `Skills/ai-search-optimization` |
| Is the Discover-eligible content informational/editorial, not commercial (product/category/service)? | — | `crawl_internal.csv` + live fetch | Medium | LLM-judgment | `discover_auditor.py` |
| Are article titles non-clickbait and matched to their content (misleading-title risk)? | `badClicks` | `crawl_internal.csv` + live fetch | Medium | LLM-judgment | `discover_auditor.py` / `onpage_auditor.py` |
| Do articles carry clear author E-E-A-T signals (named author, bio, topical expertise)? | `unauthoritativeScore` | Live fetch | Medium | LLM-judgment | `discover_auditor.py` / `seo-audit-methodology/SKILL.md` |
| Is a large, high-quality lead image present and not preview-restricted (`max-image-preview:large`)? | — | `crawl_internal.csv` + live fetch | Medium | External tool | `discover_auditor.py` |
| Are articles mobile-first and CWV-passing (Discover is a mobile feed)? | — | CrUX / Lighthouse + live fetch | High | External tool | `mobile_first_auditor.py` / `core-web-vitals` skill |
| Do target topics have current/trending demand (freshness + trend data, ideally a news angle)? | — | `gsc_performance.csv` + Google Trends | Low | LLM-judgment | `discover_auditor.py` / `date_freshness_auditor.py` |
| Are Web Stories present as an additional Discover appearance surface (optional booster)? | — | `crawl_internal.csv` | Low | Deterministic (SF/GSC column) | `discover_auditor.py` |

---

## How to use this checklist

This file is loaded by the **technical-seo-agent** and **onpage-seo-agent** during an audit. It is the master surface that ties Foley Carter's ~100 ranking-factor checks to the auditor/skill that executes each one and the leaked signal that grounds it.

Operating rules:

1. **Every cluster must return a verdict in the deliverable** — including "no issue found." A cluster silently omitted reads as "not checked," which is the failure mode this checklist exists to prevent. When a cluster is clean, say so explicitly.

2. **Graceful degradation on missing inputs.** Each row names the input file it needs. When that input is absent from `Clients/<name>/data/`, the dependent rows are **skipped-and-flagged**, not guessed — surface a line in the deliverable naming which analyses could not run and which input would unlock them (mirrors the Expanded Input Stack in `CLAUDE.md`). `crawl_internal.csv` is the only guaranteed input; every check that needs only it can always run.

3. **Mode drives how the finding is produced and how confident it is.** *Deterministic* rows are auditor-computed from a column and a threshold — high confidence, cite the column. *LLM-judgment* rows require reading content and applying judgment — state the reasoning. *External tool* rows require a live fetch, DFS, GSC, Playwright, or Lighthouse call — and per the no-unverified-claims rule and audit-workflow Rules 11–12, any high-severity or target-URL finding must be verified against the live site before it ships.

4. **`GAP —` rows are the framework's known blind spots.** They are real checks with no dedicated auditor yet. Run them manually (or via the pointed-to reference/external tool) and flag them as manual checks in the deliverable rather than dropping them.

5. **Leak attributes are grounding, not client copy.** Use them to reason about *why* a finding matters and to keep the diagnosis honest; never surface attribute names, module names, or "the leak says…" phrasing in a client-facing report (`.claude/rules/report-formatting.md`).

6. **Severity is triage weight, not outcome type.** Before a row's finding reaches a deliverable, tag its expected-outcome type (Ranking Lever / Infrastructure Hygiene / Risk Mitigation / UX-indirect) and add a Validation method per `.claude/rules/audit-workflow.md`. A Critical crawl-budget fix can still be Infrastructure Hygiene — say so.

## Source

Daniel Foley Carter, "SEO Ranking Factors for 2026" (15 source categories, ~100 checks), grounded on the May 2024 Google Content Warehouse leak. Cross-referenced against this project's `seo-fundamentals-2026.md` and `click-signals-abc-framework.md` for exact leak-attribute spellings and existing coverage. Mapped to the Ultimate SEO Auditor's auditor stack and domain skills. Cluster 20 (Discover Visibility) and the `gsc-indexation-states.md` diagnostic playbook were added from Foley Carter's "GSC Lessons" series and validated against live client indexation checks (Comfort Solutions, Superior Water & Air, Beehive). Last updated: 2026-07-21.
