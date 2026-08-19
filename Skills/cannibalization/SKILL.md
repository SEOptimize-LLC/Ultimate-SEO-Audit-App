---
name: "Keyword Cannibalization"
description: "Detection methodology, technical mechanism, prioritization rules, and resolution paths for keyword cannibalization. Use when auditing a site for self-competing pages, prioritizing cannibalization fixes by ROI, or explaining cannibalization to a client."
---

# Keyword Cannibalization

You are a keyword cannibalization expert. Cannibalization is one of the most underdiagnosed SEO problems and one of the easiest to over-fix — the discipline is knowing which clusters actually deserve attention.

## Pipeline stage assignment

> **Stage 3 — Indexability.** Not a content problem, and not a Stage 4 ranking problem.
> `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`

Two URLs competing for one query is **Google selecting a representative document**, which is
the same mechanism as canonicalisation. It sits at the index-selection sub-phase described in
[stage-3-indexability.md](../technical-seo-agent/references/stage-3-indexability.md), alongside
declared-vs-Google-selected canonical divergence and duplicate clustering.

**Why the stage assignment changes the fix.** Filed as a content problem, the instinct is
"rewrite one page to differentiate it." Filed correctly as index selection, the options are
consolidate (301 the weaker into the stronger), canonicalise (keep both reachable, declare one
authoritative), or genuinely re-target (different query, different intent). Rewriting to
differentiate is the *slowest* of those and often does not resolve the selection conflict at
all, because Google's choice was driven by signals the rewrite does not touch.

**Priority consequence:** cannibalisation outranks every Stage 4 finding on the same URLs. A
page whose query is being split cannot have its ranking meaningfully assessed until the split
is resolved, so do not stack title, content-depth or link recommendations on top of an
unresolved cannibalisation cluster.

## What Cannibalization Actually Is (the mechanism)

Cannibalization is a duplicative-entry problem in Google's index. When two pages on the same site are semantically too close, BERT-driven semantic indexing decides they shouldn't both appear in the top 10 for a query. The canonical-tag mechanism designed to handle technical duplicates does NOT catch semantic overlap. Google rotates between the pages, neither ranks consistently, and traffic suffers.

This matters because most clients understand cannibalization as a "duplicate content" problem, which leads them to either rewrite both pages slightly (doesn't fix the underlying duplicate-entry signal) or apply canonical tags (canonicals are hints, not commands, and they don't override BERT's semantic clustering). The actual fix is consolidation — one page wins, the others 301 to it.

Reference: Matt Cutts (former Google head of web spam), "How does Google handle duplicate content?" — Google clusters semantically similar pages, picks one, suppresses the others. Web Linker (r/SEO moderator) extends this: the duplicate-detection algorithm runs on document name (slug + page title + H1), not full body content, which is why two pages with different bodies but similar slugs/titles still get clustered as duplicates.

## When to Recommend Cannibalization Fixes

**Cannibalization is real, but most cannibalization fixes are noise.** Edward (Edward Show ep. 1,030): "It's so easy to spend a ton of time fixing cannibalization for keywords that are not going to bring you money." Apply the ROI-first filter:

| Cluster characteristic | Action |
|---|---|
| Money keyword (transactional/commercial intent) AND at least one URL in top 10 | Priority A — fix immediately |
| Money keyword OR top-10, but not both | Priority B — fix if bandwidth allows |
| Informational query at deep position (11+) | Priority C — usually skip |

"Money keyword" here means the DataForSEO label is `transactional` or `commercial`, matching `COMMERCIAL_INTENT_VALUES` in `auditors/cannibalization_auditor.py`. The shared definition of all four labels is in `Skills/seo-audit-methodology/references/search-intent-classification.md`.

**Note what that test does not distinguish.** It is a Dimension 1 test only, so an evaluating-stage "best plumber salt lake" and a decided-stage "emergency plumber near me" both score as money keywords despite very different conversion value. When two clusters tie on this tiering, break the tie on research stage: **decided-stage clusters outrank evaluating-stage clusters** at equal position and volume, because the realized loss is closer to the transaction. Read the stage manually per the shared reference; DFS does not return it.

The vertical overlays in that reference also apply here. In home services a DIY-flavoured informational query is genuinely Priority C, but in B2B SaaS an informational query at position 11+ may be a shortlist-forming term worth fixing, so do not apply the Priority C row mechanically across verticals.

**Top-3 cannibalization is the most damaging.** When competing pages rank in positions 1-3, you're already capturing visibility — the rotation between pages directly costs you clicks. Fix these first regardless of total impressions volume. Cannibalization at positions 20+ is theoretical loss; cannibalization at positions 1-3 is realized loss.

## False-Positive Guard: Seed Terms with Mixed Intent

Not every cluster of "2+ URLs ranking for the same query" is cannibalization. The most common false positive is the **ambiguous seed term** — a single-word query (e.g., `flushometer`, `manabloc`, `urinal`) where Google serves a SERP that mixes definitional, commercial, comparison, and adjacent-topic results. Two of the site's pages can rank in that SERP without competing for the same intent — they're answering different reader questions, both legitimately.

The auditor flags these as REVIEW tier (separate from Priority A/B/C) when both conditions are true:

1. **The query is an ambiguous seed term:**
   - 2 words or fewer
   - No service verbs (repair, install, replace, fix, clean, service, etc.)
   - No geographic modifiers (utah, salt lake, near me, sandy, etc.)
   - No intent qualifiers (best, top, emergency, how to, vs, review, etc.)

2. **The cluster URLs target meaningfully different topics:**
   - Measured by Jaccard similarity of normalized title + H1 + URL slug tokens
   - Falls below a threshold (currently 0.30)

When both apply, the cluster is downgraded to REVIEW. The recommendation is "manual review required before any consolidation work" — not auto-consolidation.

**Common REVIEW-tier patterns and their typical resolutions:**

| Pattern | Example | Typical resolution |
|---|---|---|
| Branded query (homepage + contact + city pages) | `beehive plumbing` | Skip — expected pattern for branded queries on multi-page sites |
| Definitional + adjacent-topic | `flushometer` (what-is page + pressure-toilets page) | Skip — pages serve distinct intents |
| Two location pages on a generic seed | `plumber` (West Valley page + Orem page) | Skip — geo-sibling pattern, intentional location pages |
| Informational + commercial-Utah on same topic | `manabloc` (definitional + Utah service) | Differentiate, not consolidate. Add cross-page internal links. |
| Two informational blog posts on different angles | `bidet toilet` (misconceptions + how-to) | Skip — different intents within informational SERP |

**Critical rule:** before treating any REVIEW-tier cluster as cannibalization, confirm by manual SERP inspection or content-fit review that the URLs are competing for the same intent. The fix-first instinct on a REVIEW cluster usually destroys legitimate traffic.

Run that confirmation through the tie-break in `Skills/seo-audit-methodology/references/search-intent-classification.md`: SERP furniture beats query text, and a query whose top 5 organic results split across two labels with no majority is a genuine mixed-intent seed term, not a cannibalization cluster. Two of the site's pages can hold that SERP legitimately. Check research stage as well as label, since two pages serving the same label at different stages (a definitional page and a book-now page) are not competing either.

## Winner Sanity Check + Architecture Fix Detection

After a cluster is detected and a winner candidate is selected on metrics (best position → most clicks → most backlinks → fewer internal links to update), the auditor verifies the winner is actually aligned with the query intent. Two checks run automatically:

**Geographic alignment:** the auditor extracts geographic modifiers from the query (e.g., "salt lake city", "utah", "near me") and checks whether the winner's URL/title/H1 contains the same geographic modifier OR a parent geo. A query about "salt lake city" matches a winner about Utah (parent state) but does NOT match a winner about Sugar House (different specific city).

**Service alignment:** the auditor extracts service intent (e.g., "emergency plumber", "drain cleaning", "water heater repair") and verifies the winner is a dedicated service page. Generic pages — homepage, About, Contact, Financing, Reviews — are flagged as service mismatches even when their metrics look strong.

When the winner fails alignment AND the auditor finds a non-cluster page on the site that DOES match the query intent, the cluster is moved to the **Architecture Fix** category. This is a different finding type from classic cannibalization with a different resolution.

### When the architecturally correct page is OUTSIDE the cluster

The classic cannibalization fix is "pick a winner from the cluster, redirect the losers." This is wrong when the right answer isn't in the cluster at all. Example:

> Query: "emergency plumber salt lake city"
> Cluster URLs: homepage, About, Sugar House plumber, Commercial Plumber Utah, Financing, Sugar House plumber, Sandy plumber, About
> Auditor's winner (by metrics): Sugar House plumber
> Architecturally correct page (NOT in cluster): /emergency-plumber/

The right action here is NOT to consolidate to the Sugar House page. It's to:

1. Strengthen `/emergency-plumber/` (improve content depth, add geographic signals if needed)
2. Tighten the cluster URLs so they no longer compete on this query — remove copy on the homepage / city pages / financing page that targets the query intent
3. Update internal anchor text so it points to `/emergency-plumber/`, not to the city pages
4. Do NOT 301-redirect the cluster URLs to `/emergency-plumber/`. They serve other legitimate functions (city pages target city queries, About answers brand queries). Redirecting them destroys those functions.

### Common architecture-fix patterns

| Pattern | Symptom | Fix |
|---|---|---|
| Homepage ranks for service queries | Homepage appears in many clusters with service+geo queries | Tighten homepage content; strengthen the dedicated service pages it should link to |
| City page ranks for service+other-city query | A page targeting City A ranks for a query about City B | The City B page (or a parent service page) is the canonical answer; pull the City A page off the query |
| Generic page (About, Contact) ranks for commercial query | Service queries surfacing About/Contact/Financing | Tighten the generic pages so they don't compete; strengthen the service page |
| Cluster missing the obvious canonical | Service+geo query ranks city pages and parent pages but the dedicated service page doesn't appear | Strengthen the dedicated service page (likely content-thin or under-linked) |

### When NO architecturally correct page exists

Some clusters surface in the Architecture Fix category but the auditor can't find a clean canonical. The match-strength score will be below 1.0 and may resolve to a blog post or weaker city page. This is a real signal: it means the site is missing a dedicated page for that query intent. The recommendation in those cases is either:

- Build the missing service page (e.g., a `/24-hour-plumber/` page if "24 hour plumber" queries are commercially valuable), OR
- Accept that the closest existing page is the canonical answer and route the cluster's signal toward it through content + linking

Either way, the resolution is content + internal linking. NOT 301 redirects.

## Detection Methods (in order of precision)

**1. SERP overlap (most precise)**
For two queries you suspect are cannibalizing, compare the top-10 SERP results. If more than 70% of the URLs overlap, Google sees them as the same intent. At that point you have a single intent, not two — the right move is one page targeting the higher-volume keyword, not two pages competing.

**2. GSC query/page filter**
In Google Search Console, filter Search Analytics by query and page. If the same keyword shows multiple URLs from the same domain ranking in top 30 with meaningful impressions (50+), that's a cannibalization cluster. This is the workhorse method for sites with GSC access.

**3. Position volatility / rotation battle**
A single URL's GSC position swinging by 20+ positions across a 30-day window is often Google rotating between competing pages. Web Linker's example: page introduced Feb 21, watched the rotation battle pull both pages out of the visible index within weeks.

**4. Document-name similarity (fallback)**
When GSC isn't available, cluster URLs by slug + page title + H1 similarity. This catches templated duplicates but misses semantic-overlap cases where titles differ.

**5. Year-versioned URL pattern**
URLs like `/best-tools-2024/`, `/best-tools-2025/`, plus an evergreen `/best-tools/` are a deterministic cannibalization pattern. Always consolidate to a single evergreen URL, update the content yearly. Do NOT publish year-specific URLs that you'll then have to consolidate later.

## Resolution Paths (4 options, in order of preference)

### 1. Consolidate (most common, most effective)
Pick the strongest URL using the multi-factor winner-selection rule below. Before redirecting losers, audit each loser page for unique content (sections, FAQs, examples, internal data) that isn't already in the winner — merge it in. Then 301-redirect the loser URLs to the winner. Update internal links across the site that pointed to the losers. The 301 is what moves the authority — a canonical is not the same.

### 2. Differentiate (when both pages should genuinely exist)
If one page is informational and one is transactional, rewrite each to target distinct intent. Different titles, different H1s, different primary content focus. The pages should reference each other with internal links so users moving from informational to transactional intent land correctly.

### 3. Canonicalize (least preferred among the first three)
For hub-and-deep-dive coexistence (e.g., a category hub plus detailed sub-pages), point a canonical from the deep-dive to the hub or vice versa. This is the weakest fix because canonical tags are hints, not commands — Google overrides them when content diverges enough. Only use when consolidation isn't viable for product/UX reasons.

### 4. Republish under new slug (last resort)
When consolidation hasn't moved rankings within 30+ days because Google's duplicate cluster is stuck on the old slugs, manual remove + no-index BOTH pages, then republish content under a fresh slug + new title + new H1. This loses backlink equity and resets ranking history. Only use when consolidation has demonstrably failed — typically after a 30-day wait with proper redirects in place and ranking still hasn't recovered.

## Winner Selection Rule (multi-factor, in order)

When consolidating, select the surviving URL by this priority order:

1. **Lowest current GSC position** for the target query (best existing rank wins)
2. **Highest 90-day GSC clicks** (proven user engagement)
3. **Most backlinks** pointing to the URL (strongest authority)
4. **Tie-breaker — fewer incoming internal links to update.** When two URLs are close on factors 1-3, keep the one that requires less internal-link rewiring. Reduces consolidation effort without affecting outcome.

## Strategic Recommendation: Sequence Matters

**Suggestion (not a rule):** When a site has detected cannibalization, finish resolving existing competition before publishing new content targeting the same query family. Adding new pages targeting the same intent extends the rotation problem rather than solving it.

This is a recommendation, not a hard workflow rule — the editorial team makes the final call on content sequencing. The principle is: cannibalization gets worse with more content effort, not better. Adding more content to a cannibalizing cluster is rarely the answer.

## Keyword-Target Consolidation (planning-stage)

When planning new content, run the SERP-overlap check BEFORE writing. If two keywords have >70% top-10 SERP overlap, Google treats them as the same intent. Pick the higher-volume keyword and target ONE page for both, mentioning the lower-volume term as a secondary entity in the same content.

This prevents cannibalization at the strategy stage, which is cheaper than fixing it post-publish. It also produces stronger pages — a single page consolidating both keywords' demand outperforms two thin pages splitting it.

## Communicating Findings to Clients

When explaining cannibalization in client deliverables, lead with the mechanism, not the symptom:

> "Cannibalization isn't a content-quality problem — it's a duplicate-entry problem in Google's index. Two pages on your site are semantically too close. BERT (Google's language model) can't tell them apart, and the canonical mechanism designed for technical duplicates doesn't catch this kind of semantic overlap. Google rotates between them, neither ranks consistently, and your traffic suffers."

Avoid:
- Calling it a "duplicate content problem" (technically accurate but misleading — clients think we mean copy/paste duplicates)
- Recommending "improve both pages" (this makes cannibalization worse)
- Treating canonicals as a real fix (they're hints, not commands)
- Including recovery timelines in client deliverables (per project audit-workflow rule, agency handles scheduling internally)

## Anti-Patterns to Watch For

- Publishing year-specific URLs (`/best-tools-2024/`, `/best-tools-2025/`) instead of one evergreen URL
- Adding new pages targeting the same query as existing pages without first auditing for cannibalization
- Treating high-position-volatility as a Google algorithm issue when it's actually a self-induced rotation battle
- Recommending cannibalization fixes for informational queries at deep positions — low ROI noise
- Reporting Search Console clicks as the only metric without checking whether competing pages are also splitting Map Pack, AI Overview, or other surface visibility

## Diagnostic Notes

- **High-volume sites:** GSC data on 1M+ click properties can hide queries unless you apply secondary filters. Run multiple filtered passes when auditing enterprise sites; default views miss data.
- **Diagnosis duration:** On high-volume sites, cannibalization rotation cycles can take a week to fully diagnose because pages rotate every few days. Don't draw conclusions from a 24-hour snapshot — pull at least 7 days of data.
- **Geo-sibling exclusion:** Pages that differ only by city slug (`/plumber-sandy/` vs `/plumber-orem/`) are intentional location pages, not cannibalization. The auditor handles this automatically; humans should too.

## When the Content-Expansion Workflow Calls This Skill

The `/page-content-expansion` slash command (and its supporting `Skills/content-expansion/SKILL.md`) runs an **expansion-vs-cannibalization gate** before recommending any new content for a target URL. The gate's logic lives in this skill — specifically:

- Before recommending a new section on the target page for an adjacent query, the gate checks whether another URL on the same site already holds the query stronger. If yes, recommend the user expand the OTHER page instead, or escalate to a cannibalization workflow.
- Before recommending a brand-new page for a cluster of queries, the gate confirms none of the queries is currently held in a tight cluster across multiple URLs. If a cluster is detected, this skill takes over — the expansion recommendation pauses until cannibalization is resolved.

The reverse is also true: if `/page-content-expansion` flags a query as "should be on a different page" and that different page already ranks for the query, it's not cannibalization — it's a routing decision. Use the decision logic in `Skills/content-expansion/SKILL.md` Step 5 to handle that case.

## References

- Reddit r/SEO (legitimate_salary_108): "Here's what I have learnt about keyword cannibalization"
- Edward Show episode 1,030: practitioner overlay including ROI-first prioritization
- Web Linker (r/SEO moderator): duplicative-entry mechanism explanation, rotation-battle example
- Matt Cutts (former Google head of web spam): "How does Google handle duplicate content?" video — clustering mechanism source
- Internal: `auditors/cannibalization_auditor.py` — the implementation
