---
name: "Single-Page Content Expansion (GSC-Driven)"
description: "Single-URL content optimization workflow that pulls a page's GSC query mix, classifies query intent, scores expansion opportunities against an expansion-vs-cannibalization gate, and produces a ranked deliverable (intra-page additions, new-page candidates, internal-link suggestions). Use when a client asks 'what should I add to this page?' or when an audit surfaces a single URL with strong impression volume and weak CTR/rankings. Invoked by the /page-content-expansion slash command, but also reusable inside larger audits."
---

# Single-Page Content Expansion (GSC-Driven)

You are the content-expansion analyst. Your job: take ONE URL the client cares about, pull its GSC query mix, and produce a ranked, source-attributed plan for how to expand its topical coverage — without creating cannibalization or thin content.

This skill is the methodology layer. The `/page-content-expansion` slash command is the user-facing trigger. Audits may also call this skill ad-hoc when a single URL warrants deep treatment (Cudio's `/services/odoo-migration` at position 2.7 with 0.49% CTR is the canonical example).

## Pipeline stage assignment

> **Stage 4 — Ranking.** `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`

Gated behind stages 1 to 3 per
[stage-4-ranking.md](../technical-seo-agent/references/stage-4-ranking.md). This skill already
requires a live 200, indexability and a canonical check in its pre-flight, which is the stage
gate in practice — keep those checks, they are not optional formality.

**The Stage 3 interaction is this skill's core risk.** The expansion-vs-cannibalisation gate
exists because adding content targeting a query another URL already holds creates an
index-selection conflict, which is a Stage 3 failure introduced by Stage 4 work. Never skip
the gate. See [cannibalization/SKILL.md](../cannibalization/SKILL.md), which is itself a
Stage 3 skill.

**Prerequisite worth stating explicitly:** a page with impressions but poor CTR is a valid
target. A page with **no impressions** is not, and the reason it has none is the real finding,
sitting somewhere in stages 1 to 3.

## When this skill applies

- User asks "what should I add to this page?" / "how can I improve this article?" / "this page has impressions but no clicks — why?"
- An audit surfaces a single URL with strong impression volume and weak CTR (CTR < position-average expected CTR)
- A client wants a quick win on a specific high-impression page before committing to a full audit
- A page is "Crawled — currently not indexed" or "Submitted, indexed" but ranking 8-20 — needs topical reinforcement

## When this skill does NOT apply

- Site-wide audits — use `Skills/seo-audit-methodology` instead
- Traffic decline diagnosis — use `Skills/traffic-loss-analysis` instead
- Multiple pages competing for the same query — use `Skills/cannibalization` instead (this skill calls cannibalization as a guard, but doesn't resolve it)
- Pages with zero GSC impressions in the last 90 days — there's nothing to expand from. Use a different workflow (competitive content analysis or topic research).

## The 6-Step Workflow

### Step 1 — Validate the target URL

Before pulling any data, verify the URL is real and worth analyzing.

| Check | Tool | Pass condition |
|---|---|---|
| URL returns 200 | `curl -I` or `mcp__fetch__fetch` | Status 200 |
| URL is indexable | parse meta robots from raw HTML | No `noindex` directive |
| URL is canonical to itself OR canonical target is the same | parse `<link rel="canonical">` from raw HTML | Self-canonical, or canonical points to the same URL post-normalization |
| URL has GSC impressions in last 90 days | `mcp__gsc-mcp__get_search_by_page_query` | At least 50 impressions over 90 days (rough floor — below this the query mix is too sparse to expand from) |

If any check fails, stop and tell the user what's wrong. Do NOT proceed to query analysis on a noindex'd or unindexable URL — the recommendations will be wasted.

### Step 2 — Pull the page's GSC query data

```python
# Pseudocode — actual call uses the MCP tool
result = mcp__gsc_mcp__get_search_by_page_query(
    site_url="<GSC property>",
    page_url="<target URL>",
    days=90
)
```

For each query the page ranks for, capture: query text, clicks, impressions, CTR, average position.

Sanity check the result:
- **<10 queries returned:** the page is too low-volume for this workflow. Tell the user; suggest a competitive content gap analysis instead.
- **>500 queries returned:** the page is a high-traffic hub. Filter to queries with ≥5 impressions to keep the analysis manageable.
- **The page has clicks but no impressions:** GSC is reporting strangely. Re-run with a longer window (180 days) before trusting the data.

### Step 3 — Classify each query by intent, research stage, and position

For every query in the page's mix, assign three dimensions. The shared definition for the first
two — including the vertical overlays, the secondary-label tie-break, and the confidence rule —
lives in `Skills/seo-audit-methodology/references/search-intent-classification.md`. This step is
the applied version; when the two disagree, the shared reference wins.

**Intent classification (4 categories):**

| Intent | Pattern | Example |
|---|---|---|
| **Informational** | "what is", "how to", "guide to", "explained" | "what is odoo software" |
| **Commercial** | comparison / evaluation / "best" / "vs" / "alternatives" | "odoo vs netsuite", "best erp for small business" |
| **Transactional** | "buy", "pricing", "cost", "hire", "services" | "odoo implementation cost", "odoo migration services" |
| **Navigational** | brand name / product name / specific entity | "cudio", "odoo enterprise pricing page" |

When in doubt, look at the top 3 SERP results for the query — if they're guides and how-tos, it's informational; if they're product pages and pricing pages, it's transactional; if they're listicles and comparisons, it's commercial.

**Read the SERP furniture and the title-word lexicon BEFORE you brief.**

The query-text patterns in the table above are a first pass. Confirm intent by reading two harder signals off the *live* SERP before writing any brief — practitioner method (Daniel Foley Carter). The words in the query and the shape of the SERP together classify intent more reliably than the query text alone.

*SERP furniture — what Google chooses to render tells you what it thinks the intent is:*

| SERP element present | Signals intent |
|---|---|
| Shopping / product-listing ads, price-driven results | Transactional |
| Local pack / maps, booking-engine widgets | Transactional (local / book-now) |
| Ads dominating above the fold | Commercial-to-transactional (money query) |
| Organic results are articles, guides, "how to" | Informational |
| "Best" / "top" listicles, comparison articles | Commercial-investigation |
| Featured snippet, PAA, definition box | Informational |

*Title-word lexicon — the words in the query pre-classify it:*

| Word in query | Leans |
|---|---|
| best, top, luxury, review, vs, compare, guide | **Informational / commercial-investigation** — the searcher is still choosing |
| cheap, buy, discount, for sale, price, cost, order, near me, book | **Transactional** — the searcher is ready to act. Sub-classify by which word: "price/cost" = comparison-transactional (still weighing); "buy/order/book" = ready-to-buy |

The trap this avoids: "best luxury watches" *looks* transactional (luxury, watches) but the "best" lexicon word plus an article-and-listicle SERP make it **informational** — briefing it as a product page targets the wrong intent. Classify from furniture and lexicon together, then brief.

**Apply the client's vertical overlay before you trust the lexicon.**

The lexicon above is generic, and generic is where misclassification originates. The same word flips meaning between verticals: "emergency" is a decided-stage money query for a plumber and an informational one for a SaaS blog; "how to fix" is a low-value DIY query in home services and a legitimate lead-magnet in B2B. Pull the overlay for this client's vertical from `Skills/seo-audit-methodology/references/search-intent-classification.md` (home services, B2B SaaS, ecommerce, health/YMYL) and apply it on top of the base lexicon. Check the client's memory file too — a standing content constraint overrides any intent classification.

**A query may carry a primary and a secondary label.** The primary determines the page type; the secondary determines section content. "plumber near me" is transactional (primary) plus local (secondary), so it wants a service page (primary) carrying service-area content and NAP (secondary). Local is always a secondary modifier, never a primary label. The tie-break for genuinely contested queries is in the shared reference.

**Research stage (3 stages) — read off the modifier, not the head term:**

| Stage | The searcher is | Modifiers |
|---|---|---|
| **Early** | Still defining the problem; doesn't know the solution category | "what is", "why", "how does", "types of", "symptoms of" |
| **Evaluating** | Knows the category; choosing between options or providers | "best", "vs", "alternatives", "review", "cost", "how much", "for [use case]" |
| **Decided** | Has chosen; executing | "buy", "order", "book", "hire", "near me", "emergency", "[brand] + [service]" |

Stage is the dimension that separates queries the intent label alone collapses together. "odoo migration cost" and "odoo migration vs netsuite pricing" both classify commercial-to-transactional, but the first wants a pricing block on the page you already have and the second wants a comparison page you don't. Without the stage, Step 5 routes both to the same recommendation and one of them is wrong.

If you've labelled a query **informational + decided**, re-read the SERP. That combination is almost always a misclassification of a transactional query wearing an instructional modifier ("how to book a plumber").

**Position bucket (4 buckets):**

| Bucket | Position range | What it means for expansion |
|---|---|---|
| **Strongly held** | 1-5 | The page already wins this query. Do NOT split off; reinforce in place. |
| **Striking distance** | 6-15 | Real expansion opportunity. Adding a focused section often moves these into top 5. |
| **Latent** | 16+, OR has impressions but <0.1% CTR | The page is being shown but is not satisfying intent. Investigate intent mismatch before recommending expansion. |
| **Wrong intent** | Position varies; query intent ≠ page intent | Do NOT expand on this page — these queries belong on a different page (or should be deferred entirely). |

### Step 4 — Run the expansion-vs-cannibalization gate (mandatory)

Before recommending ANY new content (whether intra-page section or new page), check whether the query is already held by another URL on the same site. This is the rule that distinguishes a real opportunity from a self-inflicted wound.

For each query in your "expansion candidate" list:

```python
# Pseudocode
result = mcp__gsc_mcp__get_advanced_search_analytics(
    site_url="<GSC property>",
    dimensions="page",
    filter_dimension="query",
    filter_operator="equals",
    filter_expression="<query>",
    days=90
)
```

Three outcomes:

| Outcome | Decision |
|---|---|
| Target URL is the only page ranking for this query (or the strongest by a 3x+ click margin) | **Proceed** — recommend expansion |
| Another URL on the same site ranks stronger for this query | **Block** — recommending content for this query on the target URL creates cannibalization. Either send the user to the stronger URL's expansion workflow, or document the split decision and stop. |
| Multiple URLs already rank in a tight cluster | **Escalate to `Skills/cannibalization`** — this is a cannibalization problem, not an expansion problem. Resolve cannibalization first; revisit expansion after. |

This gate is non-negotiable. Without it, the workflow generates cannibalization at scale.

### Step 4.5 — Run the information-gain gate (mandatory before any expansion)

The cannibalization gate (Step 4) checks whether *another URL on the same site* already holds the query. The information-gain gate checks the complementary question: does *the wider SERP* already answer what you're about to add? Expansion earns rankings when it adds information the ranking pages don't already have — not when it adds words that restate the consensus. A section that says the same five things the top 10 results already say is thin content with a longer word count, and it will not move position.

For each surviving expansion candidate (each cluster you're about to recommend as an intra-page section), before writing the recommendation:

1. Pull the top 5-10 ranking URLs for the cluster's primary query (`mcp__dfs-mcp__serp_organic_live_advanced`, or manual SERP inspection).
2. List what those pages collectively already cover — the "table stakes" set for the query.
3. Ask what the client's new section would contribute *beyond* that set: proprietary data, first-hand testing, a named/proven process, a local specific, an updated figure, an original example, a defensible contrarian take, an original visual.

Three outcomes:

| Outcome | Decision |
|---|---|
| The addition contributes something the ranking set does not already cover | **Proceed** — recommend the section, and name the specific information-gain element in the deliverable ("adds explicit per-business-size timelines, which none of the top 10 provide") |
| The addition only restates what the ranking set already covers | **Block** — more words won't help. Either give the section a differentiated angle, or drop it. Do NOT ship an "add a section on X" recommendation whose only justification is impression volume. |
| The query has impressions but the page's intent is wrong for what ranks | This is the "wrong intent" bucket from Step 3, not an information-gain case — defer per Step 3; don't force expansion. |

This gate distinguishes **information gain** (unique value vs. what already *ranks* — a SERP-relative test) from **originality in isolation** (the May 2024 leak's `OriginalContentScore`, a leak-derived attribute that scores a short page's own originality without reference to competitors — directional, not a confirmed weighting). A page can be original in isolation and still add zero information gain. Both gates — cannibalization and information gain — must pass before an expansion recommendation ships. For the on-page framing of the same concept, see `Skills/onpage-seo-agent/SKILL.md`.

**Set target length from the SERP, not from a word-count ambition.**

When the deliverable states how much to add, benchmark against the SERP — but benchmark **only intent-matched, non-doorway, page-one results**. Practitioner method (Daniel Foley Carter): take the pages actually ranking on page one for the cluster's primary query, discard any doorway/thin/off-intent outliers, and read the *typical* body length of what remains. That length is the target — enough to be competitive, not a number pulled from a "long content ranks" belief.

- **Never over-write to "beat" the SERP.** If the intent-matched page-one results sit around 2,000 words, do not recommend a 10,000-word page to "win on depth." Length past the SERP's demonstrated norm adds dilution, not relevance — and on the wrong page type it shifts intent (see the category-page intent guard in `Skills/onpage-seo-agent/SKILL.md`).
- **Length is an output of information gain, not a substitute for it.** Hit the SERP-typical length *and* add something the ranking set doesn't have. A page that is the right length and adds nothing new still fails the gate above.
- **Exclude doorway pages from the benchmark.** A thin doorway ranking on brand strength is not evidence of what the query rewards; including it skews the target length in either direction.

### Step 5 — Group queries into topical clusters

Now group the surviving queries (those that passed steps 3, 4, and 4.5) into topical clusters. The goal: identify which clusters belong on the existing page vs. which clusters justify a new page.

**Clustering rules:**

- Cluster by **shared head term** plus **shared intent** plus **shared research stage**. "odoo migration cost" and "odoo migration services pricing" belong in the same cluster — same head, same transactional intent, both evaluating-stage. "odoo migration" (informational) and "odoo migration services" (transactional) belong in DIFFERENT clusters, even though they share a head term.
- **A stage split is a cluster split, even when the intent label matches.** "odoo migration cost" (evaluating) and "book an odoo migration" (decided) share a head term and both read transactional, but they are separate clusters. A page serves two stages only when its page type genuinely serves both, which is rare; a service page that also tries to absorb evaluating-stage comparison queries becomes a hybrid that ranks for neither, because the SERP for each stage rewards a different content type.
- Cluster size matters: a cluster with 1-2 queries is usually a section addition. A cluster with 5+ queries and shared intent is usually a new page.
- The page's existing title/H1/primary topic is the "home cluster." Queries that fit the home cluster are expansion candidates for the page itself. Queries that fit a clearly different cluster are new-page candidates.

**Decision logic — expansion vs. new page:**

| Signal | Existing-page expansion | New-page candidate |
|---|---|---|
| Cluster size | 1-4 queries | 5+ queries |
| Shared intent with target page | Yes | No |
| **Shared research stage with target page** | **Yes** | **No** |
| Total cluster impression volume | < 500/month | ≥ 500/month |
| Top SERP results for the cluster | Same content type as target page | Different content type (e.g., target is comparison, cluster wants a how-to) |
| Would a section/H2 satisfy the cluster? | Yes | No — needs dedicated treatment |

**The stage row overrides the size and volume rows.** A cluster that shares the target page's intent but sits at a different research stage is a new-page candidate even at 2 queries and low volume, because no amount of section-writing makes one page type serve two stages. This is the one row that can promote a small cluster to a new page on its own.

When the answer is mixed on every other row (cluster has 4 queries with shared intent and shared stage but high volume), default to **section expansion first**. Only recommend a new page when the case is clear. The Sehgal "20 new pages from 1 export" headline is a thin-content trap — your default is fewer, better pages.

**A low-confidence intent classification cannot promote a cluster to a new page on its own.** Per the confidence rule in `Skills/seo-audit-methodology/references/search-intent-classification.md`, when the lexicon and the SERP disagree, or the top 5 results split with no majority, default to the reversible option (section expansion) and state the low confidence in the deliverable. A section that underperforms is recoverable; a new page built on a misread SERP becomes a cannibalization source that has to be redirected later.

**Coverage / cluster audit — rank the cluster, not the page.**

Before deciding a cluster justifies a new page, quantify how deeply competitors already cover that cluster — and how deeply the client's site does. Practitioner method (Daniel Foley Carter): rankings for a competitive topic are won by the **cluster** (a topical hub plus its supporting offshoots), not by a single page. A lone new page dropped into a topic a competitor covers with fifteen interlinked pages will not out-rank that cluster on its own.

How to quantify cluster depth:

- **`site:competitor.com <topic>`** — a rough count of how many pages the competitor has aimed at the topic.
- **Ahrefs / Semrush top-pages** filtered to the topic's URL pattern — which of the competitor's pages actually earn traffic in the cluster, and which offshoot angles they cover.
- **Screaming Frog Include/Exclude on the topic's directory** — crawl `competitor.com/topic/` in isolation to see the real directory tree: the hub page, its children, and the internal-link structure that binds them. This surfaces offshoot gaps — sub-topics they cover that the client doesn't.

The **coverage-substantiation** model: to rank the client's hub page, you often have to *substantiate* it with the surrounding offshoot pages the SERP leaders have — the cluster is the unit of authority, not the page. This reframes the Step 5 expansion-vs-new-page decision: a new page is justified not only by its own cluster's volume, but by whether it fills a **structural gap in the client's cluster** relative to the leaders'. Feed the offshoot gaps you find here into the new-page candidates list, and prefer building out a shallow-but-present cluster over launching an isolated page into a topic the client has never covered.

### Step 6 — Identify semantic entities and internal links

Two final outputs alongside the cluster decisions:

**Semantic entities to surface on the page:**

For each cluster of queries (especially those staying as intra-page expansions), extract the entities and concepts that appear in the queries but are missing from the current page body. Use the page's raw HTML to confirm absence — don't trust assumptions.

| Cluster | Queries (sample) | Entities missing from current page | Action |
|---|---|---|---|
| odoo migration timing | "how long odoo migration takes", "odoo migration timeline" | "timeline", "weeks", "phases", "downtime window" | Add a section: "How Long Does an Odoo Migration Take?" with explicit time ranges per business size |
| odoo migration risks | "odoo migration risks", "odoo migration failures" | "risk", "failure", "rollback", "data loss", "downtime" | Add a section: "What Can Go Wrong During an Odoo Migration (And How We Prevent It)" |

This is where the framework leans on `Skills/ai-search-optimization` — entities and definitive answers improve both Google ranking AND AI citation eligibility.

**Internal links to add:**

Two directions:

1. **TO the target page from existing pages** — for every cluster you recommend the target page win, identify 2-3 existing pages on the site that should link to it with anchor text matching the cluster. Use `mcp__gsc_mcp__get_advanced_search_analytics` filtered to the cluster's queries to find which other URLs already get impressions for related queries — those are natural link sources.
2. **FROM the target page to other pages** — for every cluster you defer to a new or existing different page, add an outbound internal link from the target page with descriptive anchor text.

Internal links carry the topical authority that justifies the expansion to Google.

**Building the section/page brief — competitor body content + PAA, safely.**

When you turn a surviving cluster into an actual content brief (the H2/H3 outline in the deliverable), use competitor content and People-Also-Ask as raw material — but through a specific, hallucination-safe recipe (Daniel Foley Carter method, adapted):

1. **Paste competitor BODY CONTENT into the model as documents — never feed the model a URL.** A URL invites the model to hallucinate what's on the page, or to reason over a cached/wrong version. Extract the actual rendered body text (Crawl4AI, `mcp__dfs-mcp__on_page_content_parsing`, or a live fetch), strip nav/footer/boilerplate, and paste the *text* as reference documents. The model then reasons over what you gave it, not over what it imagines is at the link. This is the single biggest source of brief-stage fabrication — close it.
2. **Pull PAA / related questions** (AlsoAsked, or the PAA block from `mcp__dfs-mcp__serp_organic_live_advanced`) for the cluster's primary query, and **structure them by priority** — questions closest to the page's core intent and highest impression clusters first, tangential ones last or dropped.
3. **Output the brief's headings in priority order** — most important sub-topic first, so the writer leads with what matters and the page front-loads the answer (which also helps snippet/AIO eligibility; see `Skills/ai-search-optimization`).
4. **Run the InLinks (or equivalent NLP) coverage gate** — check the drafted outline against the entity/term set an NLP tool extracts from the ranking set. Terms the outline misses are coverage gaps; terms it over-uses relative to the SERP are over-optimization. This is a mechanical backstop to the information-gain gate (Step 4.5), not a replacement: NLP coverage tells you *whether you cover the table-stakes terms*; information gain tells you *whether you add anything past them*. A brief must pass both — cover the consensus **and** contribute something the ranking set does not already have. Competitor body content shows you the table-stakes set to match; the information-gain requirement forces you past it.

## Required Output Structure

The deliverable (whether written to a `.md` file under `Clients/<name>/` or returned inline by the slash command) must have these sections in this order:

### 1. Page Snapshot

- URL, current title, H1, word count
- 90-day GSC totals: clicks, impressions, blended CTR, top 5 queries by impressions
- Position distribution: how many queries are in each of the 4 position buckets
- Intent distribution: how many queries are in each of the 4 intent buckets
- Research-stage distribution: how many queries are early / evaluating / decided, and whether that matches what the page is actually built to serve
- Any queries classified at low confidence, and what made them low confidence
- Cannibalization status (passed gate / blocked / escalated)

### 2. Intra-Page Content Additions

For each recommended section addition:

```
[Section title — usually the cluster head term as a question]
Target queries: [list of 1-5 queries the section will satisfy]
Cluster impressions (28d / 90d): [number]
Current page position for primary query: [position]
Priority: P0/P1/P2/P3
Effort: [estimate, in hours]
Expected outcome: [Ranking Lever | Infrastructure Hygiene | UX]
Likely effect: [one sentence — e.g., "Move 'odoo migration timeline' from position 8 → top 3-5 by adding explicit time ranges and a comparison table"]
Information gain: [what this section adds beyond what the top 5-10 ranking URLs already cover — the specific new data point, angle, or asset. If you can't name one, the section fails the Step 4.5 gate and should not be here.]
Validation method: [one sentence — e.g., "Re-run GSC `get_search_by_page_query` 30 days after publishing; confirm position for 'odoo migration timeline' has improved by at least 3 positions."]
Semantic entities to include: [list]
Suggested H2/H3 outline: [3-7 line outline]
```

### 3. New-Page Candidates

Only include items that survived the expansion-vs-new-page decision logic in Step 5. For each:

```
[Proposed page title]
URL slug: [recommended slug]
Target query cluster: [list of queries the new page would target]
Cluster impressions (28d / 90d): [number]
Why a new page (not a section): [one sentence justification per Step 5 decision table]
Priority: P0/P1/P2/P3
Effort: [estimate, in hours — typically 4-12 hours per new page]
Expected outcome: [Ranking Lever]
Likely effect: [one sentence]
Validation method: [one sentence]
Suggested content outline: [5-10 line outline]
Internal link sources (existing pages that should link to it): [3-5 URLs]
```

### 4. Internal Links to Add

For each recommended link:

```
From: [source URL]
To: [target URL]
Anchor text: [proposed anchor]
Reason: [one sentence — what topical signal this strengthens]
```

### 5. Cannibalization Risks Flagged

Anything blocked by Step 4's gate. Document them — even if no action is recommended now, the user needs to know these queries were excluded and why.

```
Query: [query]
Excluded because: [stronger URL on site, position X, Y clicks/30d]
Recommended path: [either "send to stronger URL" or "escalate to cannibalization workflow"]
```

### 6. Methodology Footer

A 3-line block at the bottom confirming:
- GSC data range (start date — end date)
- Page validation results (200, indexable, self-canonical)
- Cannibalization gate ran (yes/no, queries checked) and information-gain gate ran (yes/no, clusters SERP-checked)

## Quality Rules

1. **Default to fewer, better recommendations.** A clean deliverable with 3-5 intra-page sections and 1-2 new pages beats a sprawling deliverable with 15 weak suggestions. Sehgal's "20 new pages" headline is the anti-pattern.
2. **Every recommendation must cite specific queries from GSC data.** No "consider adding a section on X" without naming the queries that would justify the section.
3. **Every recommendation carries the full required-fields format** (Priority / Effort / Expected outcome / Likely effect / Validation method) per `.claude/rules/audit-workflow.md`.
4. **No recommendation may skip the cannibalization gate.** If the gate wasn't run, the deliverable is not ready to ship.
4b. **No expansion recommendation may skip the information-gain gate (Step 4.5).** Every intra-page section addition must name what it adds beyond what already ranks in the SERP. "More words on a query we get impressions for" is not an information-gain justification. If the Information-gain field is empty, the section doesn't ship.
5. **No new-page recommendation without explicit decision-table justification.** Step 5's decision table must be applied; the "why a new page (not a section)" field must be filled out.
6. **No semantic-entity recommendation without verification.** Confirm the entity is actually absent from the current page body. Re-curl the page and grep — don't rely on assumptions.
7. **The expansion plan should be reviewable in 5 minutes.** If the deliverable is longer than that, it's too long. Compress.

## Anti-Patterns

- **Recommending "add a FAQ section" without specifying which questions.** The FAQ must be derived from actual GSC queries, not generic.
- **Recommending a section that only restates what already ranks.** If the top 10 results already cover it, more words on your page won't move it — that's the Step 4.5 information-gain gate failing. Add a differentiated angle or drop the section.
- **Recommending a new page for a query the existing page already ranks 4th for.** That's a striking-distance opportunity, not a new-page opportunity.
- **Skipping the cannibalization gate because "the page seems strongest."** The gate is data, not vibes. Run it.
- **Treating long-tail variants as distinct opportunities.** "odoo migration timeline" and "how long does odoo migration take" are the same query for content purposes. Cluster them.
- **Recommending entity additions that are already in the page body.** Verify with a re-fetch and grep.
- **Producing a deliverable longer than the page being analyzed.** Compress.

## Source & Adoption Notes

This workflow was scaffolded from the GSC page-query expansion pattern raised in Akash Sehgal's LinkedIn post (Jan 2026). The Sehgal prompt provides the SHAPE — single URL → GSC export → expansion ideas. This skill adds:

- The expansion-vs-cannibalization gate (Sehgal's prompt does not include this)
- The information-gain gate (Sehgal's prompt does not test additions against the SERP — it treats impression volume alone as justification)
- Query intent classification (Sehgal does not classify intent)
- Position-bucket scoring (Sehgal treats all queries as equal candidates)
- Required-fields output format per `.claude/rules/audit-workflow.md` (Sehgal returns free-form text)
- The 6-output deliverable structure (Sehgal's prompt asks for 5 generic outputs)
- Validation method per recommendation (Sehgal does not include validation)

The underlying pattern (page-level query analysis) is well-established in SEO practice — Ahrefs and Semrush both expose it as features. This skill is the codified version for this framework.
