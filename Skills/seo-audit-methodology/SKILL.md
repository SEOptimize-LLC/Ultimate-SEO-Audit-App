---
name: "SEO Audit Methodology"
description: "Provides the overarching framework for conducting SEO audits, prioritizing recommendations, E-E-A-T assessment, and communicating findings effectively"
---

# SEO Audit Methodology

You are an SEO Audit Methodology expert that provides the overarching framework for conducting comprehensive SEO audits. Use this knowledge to structure audits, prioritize findings, and communicate recommendations effectively to different stakeholders.

## Site Type Classification (Mandatory Step 0)

Before scoping the audit, classify the client into one of the categories below. The classification determines which audit areas get extra emphasis, which checks are non-negotiable, and which findings are likely to be high-severity. Skipping this step is how auditors miss site-type-specific issues — e.g., running a generic technical audit on a news publisher and overlooking Top Stories eligibility, or auditing an e-commerce site without checking faceted-navigation handling.

**Run the classification once per client at onboarding** and re-check whenever the client expands into a new business model (e.g., a SaaS company launching an e-commerce arm, a local business adding a blog).

| Site Type | Primary Identifier | Audit Emphasis | Non-Negotiable Checks |
|---|---|---|---|
| **Local Service Business** | Geographic targeting; service pages by city; GBP-dependent | Local schema (LocalBusiness, Service, GeoCoordinates), GBP optimization, NAP consistency, citation profile, location landing pages, review schema | GBP-website parity, LocalBusiness schema, hours/phone/address visible in raw HTML, service-area markup, review snippets |
| **E-commerce** | Product catalog; faceted navigation; cart/checkout flow | Product schema, faceted URL handling, canonical strategy for variants, robots.txt parameter rules, inventory/availability signals, internal search hygiene | Product schema with `offers`, faceted nav not creating thin duplicates, out-of-stock handling, internal search not indexed, breadcrumb schema |
| **SaaS / Lead-gen** | Conversion-driven; demo/trial CTAs; long-form blog supporting funnel | Conversion tracking reliability, GA4/GTM/server-side tagging, comparison/alternatives content, landing-page schema, demo/pricing page indexation, JS rendering for marketing pages | Conversion event firing on canonical URL, no `noindex` on money pages, comparison pages have unique value, blog supports funnel not just traffic |
| **News / Publisher** | Daily content output; bylines; date-sensitive; Top Stories visibility | NewsArticle vs Article schema, `dateModified` discipline, `max-snippet` / `max-image-preview` directives, author E-E-A-T, publisher logo (raster ≤600×60), Discover readiness, sitemap freshness | NewsArticle schema, accurate `datePublished`/`dateModified`, author pages with credentials, publisher logo correct format, news sitemap separate from main sitemap |
| **Content / Blog (non-news)** | Educational content; longer publication cadence; authority-building | Article schema, FAQPage schema for comparison/how-to posts, author schema with credentials, internal linking around topical clusters, content freshness signals | Article schema with author, FAQPage on Q&A-style posts, topical cluster integrity, no thin tag/category pages, dateModified updated when content materially changes |
| **JS-heavy / SPA** | Next.js / Nuxt / Vue / React with client-side routing | Raw HTML vs rendered HTML diff (per `technical-seo-agent` JS framework), pre-render indexability decision, AI-crawler visibility, render budget, hash-routing detection | Critical SEO elements (title, canonical, meta robots, H1, schema) in raw HTML; AI-crawler-equivalent `curl -A "ChatGPT-User"` passes; no JS-injected canonicals or robots directives |
| **Multi-tenant / Multi-location** | Single platform serving many locations/brands | Hreflang or geo-targeting strategy, location-page differentiation, duplicate-content risk across locations, sitemap segmentation | Each location page has unique value beyond city-name swaps, hreflang or geo-signals correctly implemented, no canonical war between location pages |

### Cross-cutting classifications (apply on top of primary)

Some sites carry one or more cross-cutting characteristics that adjust the audit emphasis regardless of primary type:

- **Bilingual / Multilingual (EN + ES, EN + FR_CA, etc.)** — Hreflang implementation, language-specific GSC properties, locale-specific schema, localized meta descriptions (not just translated copy). Every URL-level finding needs to be applied to both/all locales unless explicitly stated otherwise.
- **Behind Cloudflare / CDN with script-rewriting features** — Rocket Loader, Email Obfuscation, and similar features can mask script behavior in audits. Tech-stack fingerprint must capture this, and Core Web Vitals findings should account for it.
- **Recently migrated (within 6 months)** — Redirect chains, broken inlinks, hreflang regressions, schema drift are all elevated risks. Include a migration-specific section in findings.

### How to use the classification

1. Determine the primary site type in 30 seconds based on the homepage + a sample of internal pages. If unclear, ask the client directly — don't guess.
2. Note any cross-cutting classifications.
3. Carry the classification forward into the audit deliverable's opening context (e.g., "Cudio is a SaaS / Lead-gen site on Odoo Website Builder, bilingual EN + fr_CA, behind Cloudflare with Rocket Loader active").
4. Use the Non-Negotiable Checks column as a hard checklist — every audit must report a verdict on each of those checks for the relevant site type, even if the verdict is "no issue found." A missing verdict on a non-negotiable check is an audit defect.
5. Use the Audit Emphasis column to allocate analysis depth. Don't run a 4-hour faceted-navigation analysis on a SaaS site; don't run a 4-hour conversion-tracking analysis on a news site.

**Adopted from** Islam Eldiasti's technical-SEO-skill-claude (https://github.com/eslamdeasty/technical-seo-skill-claude), which uses a similar 5-category site-type matrix to gate audit emphasis. Extended here with Local Service Business (primary use case for this framework), Multi-tenant, and cross-cutting classifications.

## Ranking-Factors Coverage (mandatory verdicts)

The Non-Negotiable Checks column above gates site-type-specific findings. A parallel contract gates ranking-factor coverage across every audit — technical, on-page, keyword, or full-site. Both work the same way: a defined list of checks, and a required verdict on each relevant one, even when the verdict is "no issue found." Skipping a check silently is the failure mode both rules exist to prevent.

The master list lives in the leak-grounded ranking-factors checklist at `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md`. Walk it — don't duplicate it here. The checklist is sharded into **19 audit-execution clusters** that mirror the existing auditor/skill split, so each item lands with the stage that owns it:

1. Crawl Accessibility & Bot Access
2. Rendering & JavaScript
3. Indexation & Canonicalization
4. Non-Value Content & Crawl Budget
5. On-Page (Titles / Meta / Headings)
6. Content Quality & Originality
7. Relevance & Query Matching
8. Internal Linking & Anchors
9. Backlinks & Off-Page
10. Click Signals & User Behaviour (NavBoost)
11. Domain-Level Quality & NSR
12. Demotions, Spam & Suppression
13. SERP Context & Twiddlers
14. Schema & Structured Data
15. Freshness & Dates
16. Page Experience & UX
17. Locale & International
18. Entity, Author & Brand
19. AI Search / LLM Visibility (GEO/AEO)

### The coverage contract

1. **Every audit walks the clusters relevant to its scope and returns a verdict on each in-scope cluster in the deliverable — even "no issue found."** A technical-only audit walks the crawl/rendering/indexation/crawl-budget/schema/page-experience clusters; an on-page audit walks the on-page/content-quality/relevance/internal-linking/schema/entity clusters; a keyword audit walks relevance/query-matching/click-signal/SERP-context clusters; a full-site audit walks all 19. Scope determines which clusters are in-scope, not whether the walk happens.
2. **A missing verdict on an in-scope cluster is an audit defect** — the same standard as a missing verdict on a Step 0 Non-Negotiable Check. The Pass 2 self-review (see `.claude/rules/audit-workflow.md`) must confirm every in-scope cluster carries a verdict before the deliverable ships.
3. **Clusters whose required input file is absent are skipped-and-flagged, not silently dropped.** This follows the Expanded Input Stack graceful-degradation contract: when the input that unlocks a cluster (e.g. `anchors_internal.csv` for anchor/demotion analysis, `backlinks_semrush.csv` for off-page NSR proxies, the Koray topical map for `siteFocusScore`/`siteRadius`, the GSC Page-indexing exports for Crawled/Discovered-not-indexed) is not present, record the cluster's verdict as "not assessed — missing input [file], flagged" rather than omitting it. A skipped-and-flagged cluster satisfies the contract; a missing cluster does not.
4. **Leaked attributes cited by the checklist are LEAK-DERIVED.** Clusters 10–12 (click signals, NSR/domain quality, demotions/spam) lean on attributes documented in the May 2024 Content Warehouse leak — `goodClicks`/`badClicks`/`lastLongestClicks`, `siteAuthority`, `clutterScore`, `hostAge`, the various demotion signals. State these as leak-derived, not as confirmed Google ranking weights, using the same hedged framing the rest of this framework applies to leaked signals (see the Evidence Hierarchy section below).

## Search Intent Classification (shared definition)

Three skills classify query intent independently — `Skills/content-expansion` (Step 3 and Step 5), `Skills/cannibalization` (Priority A/B/C tiering), and `Skills/traffic-loss-analysis` (Phase 4.3) — plus `auditors/cannibalization_auditor.py` programmatically. They previously carried three separate definitions, so the same query could be "commercial" in one deliverable and "money-bearing" in another with nothing reconciling the two.

The single definition now lives at [references/search-intent-classification.md](references/search-intent-classification.md). Walk it — don't duplicate it. It carries:

- The four-label taxonomy (Broder 2002 / Do-Know-Go), which is also the DataForSEO integration boundary
- The **research-stage dimension** (early / evaluating / decided), which separates queries the label alone collapses together and which DFS does not return
- **Vertical overlays** for home services, B2B SaaS, ecommerce, and health/YMYL, because the same modifier flips meaning between them
- The primary/secondary label rule and the tie-break for contested queries
- The confidence rule, and the constraint that a low-confidence classification cannot on its own justify a new page

The stage dimension and the vertical-variance principle are adopted as **method pending one implementation cycle**, not as measured fact — provenance and limits are stated at the foot of that file.

## Audit Frequency Framework

| Audit Type | Frequency | Scope |
|------------|-----------|-------|
| Full Comprehensive Audit | Quarterly | Technical + Content + Links + Competition |
| Technical Health Check | Monthly | Crawling, indexing, Core Web Vitals |
| Content Review | Bi-annually | Quality, freshness, gaps |
| Competitive Analysis | Bi-annually | Keyword gaps, SERP changes |
| Quick Issue Scan | Weekly | Critical errors, 5xx, broken pages |

## Audit Scope by Type

### Full Audit Components
1. **Technical SEO** - Crawlability, indexing, site speed, mobile, architecture
2. **On-Page SEO** - Titles, meta, headings, content quality, internal links
3. **Off-Page SEO** - Backlink profile, brand mentions, referring domains
4. **User Experience** - Core Web Vitals, navigation, page usability
5. **Competitive Analysis** - Keyword gaps, content opportunities

### Specialized Audits
- **Technical-only**: Focus on crawling, rendering, indexation
- **Content-only**: Quality, E-E-A-T, keyword targeting, gaps
- **Backlink-only**: Profile health, toxic links, anchor distribution
- **Local SEO**: GMB, citations, local content, reviews

---

## Prioritization Framework

### The resolution procedure (run this before any scoring)

Impact × Effort cannot answer "which of these two findings first?" because it has no concept
of dependency. Two findings can score identically and still have a correct order between
them. Run these five tests in sequence. **The first test that separates them decides it.**

```
1. STAGE GATE      → which pipeline stage does each finding belong to?
2. BINDING TEST    → is the variable actually causing a loss on THIS site?
3. PAGE VALUE      → does the affected set contain revenue or lead pages?
4. OUTCOME TYPE    → Ranking Lever > Risk Mitigation > UX > Hygiene
5. EFFORT          → cheapest first, among what survives
```

**1. Stage gate.** `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`. The lower stage
wins, always, regardless of volume or severity label. A failure at any stage makes
everything downstream unreachable, so ranking work on a page that cannot be crawled,
rendered or indexed returns nothing. Stage assignment for all 143 checklist variables is in
[ranking-factors-checklist-2026.md § Stage Index](../technical-seo-agent/references/ranking-factors-checklist-2026.md).

**2. Binding test.** *Is the absence actually causing a loss, or is it merely an absence?*
This is the test that gets skipped, and skipping it is what fills deliverables with items
that cannot move anything. Ask: **what specifically is broken as a result of this?** If you
cannot name the loss, the finding is not binding and it does not compete for priority.

A directive that is absent but correctly inferred by Google is not binding. A signal that is
missing on pages that already rank for their target terms is not binding. **Volume never
converts a non-binding absence into a binding one.** Five hundred instances of something
that costs nothing still costs nothing.

**3. Page value.** Does the affected set include money pages? Volume is a **multiplier on
the value of the affected pages**, never an axis of its own. One broken revenue page beats
five hundred broken tag archives. Filter out non-SEO URLs (pagination, PPC landers,
thank-you pages, utility pages) per `.claude/rules/audit-workflow.md` Rule 7 before volume
influences anything, and report unique URLs rather than export row counts per Rule 10.

**4. Outcome type.** Within the same stage, a Ranking Lever precedes Risk Mitigation,
which precedes UX, which precedes Infrastructure Hygiene. See Expected Outcome
Classification below.

**5. Effort.** Only now does cost break the tie.

### Worked example: 50 missing H1s vs 20 missing canonicals

The question a senior consultant actually gets asked, and the reasoning matters more than
the answer.

**Test 1, stage gate.** Canonicals are Stage 3 (Indexability, cluster 3). H1s are Stage 4
(Ranking, cluster 5). Stage 3 gates Stage 4, so **the canonicals win on ordering and the
50-vs-20 volume difference is irrelevant.** Volume lost the moment the two findings landed
in different stages.

**But test 2 is where the real answer lives**, and it can reverse the outcome:

- **Are those 20 URLs part of a duplicate cluster?** If competing variants exist
  (parameters, filters, `www`/non-`www`, trailing-slash pairs, print versions), the missing
  canonical means Google is choosing the representative URL for you. That is a live
  index-selection failure, it is binding, and it is a **Ranking Lever**. Ship it first.
- **Are they single, unduplicated URLs?** Then Google self-canonicalises them correctly by
  default and nothing is broken. The finding is **Low, Infrastructure Hygiene**, and it
  should not be near the top of any list. Verify with GSC URL Inspection: if the
  Google-selected canonical already equals the URL itself, the absence costs nothing.
- **Are the 50 H1-less pages ranking for their target terms?** If yes, H1 absence is not
  binding on those pages. Google derives topic from the title, body and links. If those
  pages are *not* ranking, H1 is still unlikely to be the binding constraint, and treating
  it as one substitutes a checkbox for a diagnosis.

**The verdict on the example as posed:** if any of the 20 sit in a duplicate cluster,
canonicals ship first on stage order alone. If none do, **neither finding is urgent**, and
the more important observation is that the audit is reporting *absences* rather than
*losses*. Two findings that both fail the binding test should not be consuming a
prioritisation conversation at all, and the audit should go back and find what actually is
binding.

**The general lesson.** Stage order settles sequence. The binding test settles whether an
item belongs on the list. Most bloated audits fail the second test, not the first, and
volume is the number most often mistaken for importance.

### Tie-breaker: Impact × Effort Scoring

**Scoring Method:**
```
Priority Score = (Impact Score + Inverse Effort Score) / 2

Impact: 1 (minimal) to 5 (major business impact)
Effort: 5 (simple fix) to 1 (major development)
```

**Score Interpretation:**
| Score | Priority | Action |
|-------|----------|--------|
| 4.5-5.0 | Critical | Implement immediately |
| 3.5-4.4 | High | Schedule this sprint |
| 2.5-3.4 | Medium | Add to backlog |
| 1.5-2.4 | Low | Opportunistic |
| 1.0-1.4 | Minimal | Consider skipping |

### Quick Prioritization Matrix

```
                    HIGH EFFORT
                        ↑
    Strategic      |   Major
    Investments    |   Projects
    (plan carefully) | (requires resources)
    ←──────────────┼──────────────→
    LOW IMPACT     |           HIGH IMPACT
    Quick Wins     |   Do First
    (batch these)  |   (immediate action)
                        ↓
                    LOW EFFORT
```

### Prioritization Criteria

1. **Business alignment** - Does it support key business goals?
2. **Traffic potential** - How many URLs/users affected?
3. **Competitive gap** - Are competitors doing this better?
4. **Technical dependency** - Does it unblock other work?
5. **Resource availability** - Can it be done now?

---

## Expected Outcome Classification

Every recommendation in a client-facing audit should be tagged with one of four expected-outcome categories. Priority and effort tell the client WHEN to do something. Expected outcome tells the client WHAT TO EXPECT when it ships. Without this, clients fix infrastructure issues and conclude SEO doesn't work when rankings don't move — because no one told them not to expect ranking movement from infrastructure work.

### The Four Outcome Types

| Type | Definition | Example recommendations | What to tell the client |
|---|---|---|---|
| **Ranking Lever** | Likely to move rankings on specific queries when shipped | Recover de-indexed money pages; rewrite thin content on revenue pages; fix canonical bugs that suppress indexable URLs; consolidate near-duplicate cannibalizing pages; remove noindex tags blocking commercial pages | "Expect movement on [specific queries] within [reasonable window]. Track via GSC." |
| **Infrastructure Hygiene** | Cleaner architecture; rankings should NOT be expected to move | Crawl-waste cleanup (faceted nav, filter URLs); flatten redirect chains; minify JS/CSS on already-indexed pages; noindex paginated category pages; consolidate sitemap entries | **Scale-dependent phrasing.** Large site or heavy churn: "this protects crawl budget and gives Google a cleaner picture of the site. Don't expect ranking movement." Small or new site: **do not cite crawl budget at all** — it is not the constraint at that size. Say "this gives Google a cleaner picture of the site and removes places for future bugs to hide. Don't expect ranking movement." |
| **Risk Mitigation** | Prevents future ranking damage; no immediate ranking impact | Fix mixed-content warnings; resolve security headers; correct hreflang errors before they cause de-indexation; address E-E-A-T signal contradictions before a quality-update penalty | "This stops a future problem. The cost of NOT doing it is bigger than the upside of doing it." |
| **UX (indirect ranking)** | Improves user behavior; ranking effect is indirect via click signals | Improve LCP on revenue pages; fix cumulative layout shift on conversion templates; improve CTAs/internal CTA placement | "This affects how users behave on the page. Ranking effect comes through click-signal feedback (NavBoost), so it's slower and harder to attribute, but real over time." |

### Classification Rules

1. **Tag every recommendation.** No exceptions. If you can't classify it, the recommendation is too vague.
2. **A recommendation can be ONE type, not multiple.** "Fix faceted nav" is Infrastructure Hygiene, not "hygiene + ranking." Picking one forces honesty about the dominant expected outcome.
3. **Bundle related fixes that share an outcome type.** "Flatten 19 redirect chains + fix 14 redirect loops" is one Infrastructure Hygiene line item, not 33.
4. **A "Ranking Lever" tag is a load-bearing claim.** If you say a fix is a ranking lever and it ships clean and rankings don't move within the stated window, the client will (rightly) ask why. Don't over-classify into this bucket. When in doubt, downgrade to Hygiene or UX.
5. **Cross-check with the Click-Signals framework.** UX-tagged recommendations should reference the ABC framework (Anchors / Body / Clicks) — these are click-signal-mediated and behave differently from direct ranking levers.

### Why this rule exists

Mainstream technical SEO consensus: most "feels impactful" infrastructure fixes (crawl-waste cleanup, redirect flattening, minification, sitemap hygiene) do NOT directly move rankings. They protect crawl budget, reduce bot-induced server cost, and prevent future problems. Selling them as ranking levers — even implicitly, by listing them next to actual ranking levers without distinction — burns client trust when results don't materialize. The one-line outcome tag fixes this without making audits longer or more complex.

---

## Presentation Best Practices

### Report Structure

```
1. Executive Summary (1 page)
   - Site health score
   - Top 5 critical issues
   - Top 5 quick wins (preview — full list lives in Section 5)
   - Estimated impact

2. Priority Issues (by category)
   - High Impact (fix now)
   - Medium Impact (schedule soon)
   - Low Impact (backlog)

3. Detailed Findings
   - Technical SEO
   - On-Page SEO
   - Backlink Analysis
   - Competitive Insights
   - Ranking-Factors cluster verdicts — one verdict per in-scope checklist cluster (even "no issue found"), per the Ranking-Factors Coverage contract above

4. Action Plan
   - Prioritized task list
   - Priority (P0–P4)
   - Effort estimates
   - Expected outcome tag (per audit-workflow rule)
   - Likely effect (one specific sentence)
   - Validation method (one specific instruction per audit-workflow rule)
   - Dependencies noted

5. Quick Wins (dedicated section)
   - High-impact fixes under 1 hour each
   - Suitable for ad-hoc dev sprints between major releases
   - Same format as Action Plan rows (priority, effort, expected outcome, likely effect, validation method)
   - Surfacing these separately gives clients a path to immediate, low-risk progress while
     the larger Action Plan items go through scoping. Adopted from the Islam Eldiasti
     technical-SEO-skill-claude framework where Quick Wins is a standalone audit section.

6. Appendix
   - Full issue export
   - Supporting data
```

**Required format for every Action Plan row and every Quick Win row:**

```
[Recommendation title]
Priority: P0/P1/P2/P3/P4
Effort: [estimate]
Expected outcome: [Ranking Lever | Infrastructure Hygiene | Risk Mitigation | UX]
Likely effect: [one specific sentence describing what the client should observe]
Validation method: [one specific instruction the dev can run to confirm the fix shipped correctly]
```

The Expected outcome and Validation method fields are enforced by `.claude/rules/audit-workflow.md`. See that file for the rationale and examples of good vs bad validation methods.

### Communication Principles

**Key insight:**
> "The purpose is not recommending solutions, it's getting them implemented."

**Effective communication:**
- Lead with business impact, not technical jargon
- Include screenshots and visual evidence
- Explain WHY each issue matters for rankings/traffic
- Provide specific, actionable steps
- Understand platform limitations before finalizing recommendations
- Ask developers their preferred format/style

### Setting Realistic Timelines (Click-Signal Aware)

When recommendations touch user-engagement signals (CTR improvements, snippet rewrites, intent matching, content depth changes), the timeline language MUST account for how Google's click-signal systems propagate. Clients commonly expect "we shipped the change Monday, can we re-evaluate Friday?" — that expectation is wrong and needs to be reset before the work begins, not after.

**The mechanics:**

- **NavBoost** memorizes ~13 months of click data per query (per the Google API leak and DOJ antitrust testimony). Changes need enough new clicks to overcome the historical baseline.
- **RankEmbedBERT and FastSearch** train on ~70 days of search log data.
- Click signals are **squashed and contextually weighted** — Google filters noise before signals affect rankings, which means small changes need a meaningful sample to register.

**Standard timeline language to use in audit recommendations and client messages:**

- **First 2-4 weeks after change:** Google re-crawls and re-indexes. New title/snippet may start showing in SERPs. Click-signal feedback loop has barely begun. "Don't panic if rankings haven't moved yet."
- **Weeks 4-8:** Click signals from the new snippet/content start accumulating. Initial directional signal becomes visible if the change was meaningful. Position shifts may be modest.
- **Weeks 8-16:** Full click-signal feedback through NavBoost. This is when the bulk of the ranking impact (positive or negative) materializes.
- **Beyond 16 weeks:** Signals continue to update against the 13-month rolling window. A page that started moving up at week 8 may continue to drift up over months as the historical baseline fades.

**What NOT to say to clients:**

- "Expect rankings to improve within 2 weeks." (Too aggressive — sets up disappointment.)
- "Check Search Console daily after we ship the change." (Encourages noise-watching that obscures the signal.)
- "We'll see CTR-driven ranking lift by end of month." (Overly specific and likely wrong.)

**What TO say:**

- "Initial directional signal in 4-8 weeks; full impact takes 8-16 weeks to materialize through Google's click-signal systems."
- "Don't evaluate this change in less than 6 weeks — the click-signal feedback Google uses operates on a multi-month window."
- "Expect ranking positions to drift over the coming quarter rather than jump suddenly."

This timeline guidance applies specifically to changes affecting click signals (snippets, titles, intent matching, content depth, internal linking patterns). Pure technical fixes (broken canonicals, redirect chains, indexation errors) propagate faster and have shorter expected timelines (1-4 weeks).

### Stakeholder-Specific Formats

| Stakeholder | Focus On | Avoid |
|-------------|----------|-------|
| Executives | Business impact, ROI, competitive position | Technical details |
| Marketing | Traffic, conversions, content gaps | Code-level issues |
| Developers | Specific fixes, code examples, priority | Business strategy |
| Content Team | E-E-A-T, quality issues, gaps | Technical jargon |

---

## E-E-A-T Framework

### The Four Components

| Component | Definition | How to Demonstrate |
|-----------|------------|-------------------|
| **Experience** | First-hand knowledge | Product reviews from users, personal case studies |
| **Expertise** | Subject matter knowledge | Author credentials, certifications, depth of coverage |
| **Authoritativeness** | Industry recognition | Backlinks from authoritative sources, citations, awards |
| **Trustworthiness** | Reliability signals | HTTPS, contact info, privacy policy, accurate info |

### E-E-A-T Implementation Checklist

**Author Credibility:**
- [ ] Detailed author bios with credentials
- [ ] Professional author photos
- [ ] Links to author's other work/profiles
- [ ] Relevant certifications displayed

**Content Quality:**
- [ ] Cite authoritative sources
- [ ] Keep information current
- [ ] Address primary and follow-up questions
- [ ] Match complexity to audience level

**Brand Transparency:**
- [ ] Clear contact information
- [ ] Physical address displayed
- [ ] SSL/HTTPS implemented
- [ ] Privacy policy present
- [ ] Active, verified social profiles

**YMYL Content (Extra Scrutiny):**
- [ ] Expert authors for health/finance/legal
- [ ] Citations to authoritative sources
- [ ] Regular content updates
- [ ] Clear disclaimers where appropriate

---

## Crawl Budget Optimization

### Factors Affecting Crawl Budget

| Factor | Impact | Optimization |
|--------|--------|--------------|
| Site size | More pages = more competition for crawl | Prune low-value pages |
| Server speed | Slow response = fewer pages crawled | Improve TTFB |
| Content quality | Low quality = reduced crawl priority | Improve or remove thin content |
| Update frequency | Fresh content = more frequent crawling | Regular updates to key pages |
| Internal linking | Poorly linked = missed pages | Improve internal link structure |

### Crawl Budget Optimization Strategies

1. **Eliminate crawl waste:**
   - Block faceted navigation with robots.txt
   - Consolidate duplicate content
   - Remove or noindex thin pages
   - Fix redirect chains

2. **Improve crawl efficiency:**
   - Reduce server response time
   - Flatten site architecture
   - Submit updated XML sitemaps
   - Fix broken internal links

3. **Prioritize important pages:**
   - More internal links to key pages
   - Fresh content on priority pages
   - Submit high-priority URLs in sitemap

---

## JavaScript SEO Considerations

### Rendering Approaches

| Approach | Description | SEO Impact |
|----------|-------------|------------|
| Server-Side Rendering (SSR) | HTML generated on server | Best - content immediately available |
| Static Site Generation | Pre-built HTML | Excellent - fast and crawlable |
| Client-Side Rendering (CSR) | JS renders in browser | Risky - may not be indexed |
| Dynamic Rendering | Server for bots, client for users | Good - but maintenance overhead |
| Hybrid Rendering | SSR for critical, CSR for interactive | Good - balance of both |

### JavaScript SEO Checklist

- [ ] Critical content visible in initial HTML
- [ ] No content behind user interactions (clicks, scrolls)
- [ ] Internal links in `<a href="">` format (not onClick)
- [ ] Lazy-loaded content uses Intersection Observer
- [ ] Test rendering with Google's URL Inspection tool
- [ ] Ensure JavaScript files not blocked in robots.txt

---

## Structured Data Implementation

### Priority Schema Types by Site Type

| Site Type | Must Have | Should Have | Nice to Have |
|-----------|-----------|-------------|--------------|
| E-commerce | Product, BreadcrumbList, Organization | Review, FAQ, Offer | HowTo, Video |
| Publisher | Article, BreadcrumbList, Organization | Person, FAQ | Video, HowTo |
| Local Business | LocalBusiness, BreadcrumbList | Review, FAQ | Event, Menu |
| SaaS | Organization, BreadcrumbList, FAQ | SoftwareApplication | HowTo, Video |

### Schema Best Practices

- Use JSON-LD format (Google recommended)
- One schema type per purpose (don't duplicate)
- Ensure data accuracy (match visible content)
- Keep schema updated when content changes
- Don't mark up hidden content
- Test in both staging and production

---

## SERP Features Optimization

### Feature Types and Requirements

| Feature | Content Format | Schema Required | Key Optimization |
|---------|---------------|-----------------|------------------|
| Featured Snippet | Paragraph, list, table | No (but helps) | Direct answer in 40-60 words |
| People Also Ask | Question + answer format | FAQPage helps | Clear Q&A structure |
| Knowledge Panel | Entity information | Organization/Person | Brand signals, Wikipedia |
| Rich Snippets | Varies by type | Yes - type specific | Accurate schema data |
| AI Overview | Comprehensive, authoritative | Helps | E-E-A-T, structure, freshness |
| Local Pack | Business listing | LocalBusiness | GMB optimization |

---

## Keyword Strategy: Cannibalization-Aware Planning

When recommending new content or new keyword targets, run two checks BEFORE the content is written. These are planning-stage rules — fixing cannibalization at the strategy stage is dramatically cheaper than fixing it post-publish.

### SERP-overlap check (the 70% rule)

For any pair of keywords being considered as separate page targets, look at the live top-10 SERP for each. If more than 70% of the URLs overlap, Google sees them as the same intent. Don't write separate pages for them. Instead:

1. Pick the higher-volume keyword as the primary target
2. Write a single page targeting that keyword
3. Mention the lower-volume keyword as a secondary entity in the same content
4. Internal-link the page from related supporting content

This produces a stronger page than two thin pages splitting the same intent's demand. It also prevents you from creating a cannibalization problem you'll have to fix later.

### Sequence rule (recommendation, not requirement)

When a site has detected cannibalization in a topic cluster, finish resolving the existing competition before publishing new content targeting the same query family. Adding new pages targeting an already-cannibalizing intent extends the rotation problem rather than solving it.

This is a recommendation — the editorial team makes the final call on content sequencing based on broader business priorities. The principle: cannibalization gets worse with more content effort, not better. The auditor's output flags clusters as Priority A/B/C using ROI scoring; resolving Priority A clusters before publishing new content in the same family is good practice.

For full detection methodology, mechanism explanation, resolution paths, and winner-selection rules, see `Skills/cannibalization/SKILL.md`.

## Common Audit Mistakes to Avoid

### Methodology Mistakes
- Relying solely on automated tool output
- Not manually reviewing key pages
- Generic recommendations without site context
- Ignoring platform/CMS limitations
- Overwhelming stakeholders with too many issues

### Prioritization Mistakes
- Treating all issues equally
- Ignoring effort required for fixes
- Not considering business impact
- Missing quick wins
- Over-focusing on minor issues

### Communication Mistakes
- Too technical for audience
- No clear action items
- Missing impact explanation
- No visual evidence
- Recommendations without implementation steps

### Follow-up Mistakes
- No verification of fixes
- Not tracking impact of changes
- Skipping re-audit after major fixes
- Not documenting what was done

## Evidence Hierarchy: Which Sources Carry Weight

When recommendations require citing evidence (especially for ranking-signal claims, algorithm behavior, or contested SEO topics), use this hierarchy. Higher-tier sources should override lower-tier sources when they conflict.

### Tier 1 — Primary Source Documents (Highest Authority)

These are first-hand evidence from inside Google or the legal record:

- **Google API Content Warehouse Leak (May 2024)** — Leaked internal documentation that exposed many of Google's actual ranking-signal data structures, including NavBoost click attributes (goodClicks, badClicks, lastLongestClicks), squashed signal handling, and slicing by query/position/device. When the leak documents a signal, treat it as confirmed-real — even if Google publicly downplays it.

- **US v. Google Antitrust Trial Testimony (2024-2025)** — DOJ trial record includes sworn testimony from Google engineers confirming click signals as fundamental ranking inputs, the role of user click data as Google's competitive moat, and specific systems (NavBoost, Glue) by name. Public record.

- **Google Patents** — Long-click ratios (US8661029B1), re-ranking based on engagement, and many other ranking-signal mechanics are documented in filed patents. Patents describe what Google has implemented or considered implementing.

- **Google's Official Documentation** — Search Central docs, developer guides, GSC help center. Authoritative for current stated behavior, but Google's published statements occasionally minimize or omit signals confirmed by the leak/testimony.

### Tier 2 — Senior Practitioner Synthesis

Industry voices who synthesize multiple primary sources and have a track record of accurate, evidence-grounded analysis:

- **Cyrus Shepard (Zyppy)** — Notable for grounding claims in the API leak, antitrust testimony, and patents.
- **Mark Williams-Cook** — Practical, evidence-based observations from large-scale client work.
- **Rand Fishkin (SparkToro)** — Original publisher of the Google API leak documents.
- **Mike King (iPullRank)** — Deep technical analyses of leaked documents.
- **Glenn Gabe** — Algorithm-update analysis with consistent forensic rigor.

Treat their claims as reliable when they cite primary sources. Treat their unsupported assertions as opinion to be verified.

### Tier 3 — Google Employee Public Statements

Google engineers (Gary Illyes, John Mueller, Martin Splitt, Danny Sullivan) on Twitter/X, podcasts, and conference talks. Useful for understanding Google's official stance and for clarifications of edge cases.

**Caveat:** Google employees have a documented pattern of downplaying or denying signals that the API leak later confirmed exist. Treat denials with skepticism when they conflict with leaked documentation. Treat confirmations as durable.

### Tier 4 — Industry Studies & Tool Vendor Data

Published studies from established SEO companies (Backlinko, SEMrush, Ahrefs, Moz, SISTRIX) often contain useful correlations and observed patterns. **Correlation studies are not causation.** Use them to identify patterns worth investigating, not as proof of causal mechanisms.

### Tier 5 — Anecdotal Reports & Forum Discussions

Reddit threads, blog posts, Twitter screenshots showing specific behavior on specific sites. Useful as leads for further investigation; not as evidence.

### What This Means for Audit Recommendations

When making a claim in a recommendation:

1. **If a Tier 1 source confirms it**, you can state it as fact without hedging.
2. **If only Tier 2-3 sources confirm it**, frame as "documented by multiple practitioners" or "Google has stated."
3. **If only Tier 4 sources show it**, frame as "industry studies suggest" — and don't promise causal outcomes.
4. **If only Tier 5 sources show it**, don't include it in a client deliverable.

When a Tier 3 statement conflicts with a Tier 1 source, the Tier 1 source wins. Don't cite a Google denial of a signal that the leaked documentation confirms exists.

### Quick Reference: Common Claims and Their Sources

| Claim | Strongest source |
|---|---|
| NavBoost / Glue use click signals for ranking | Tier 1 (API leak + DOJ testimony) |
| 13-month NavBoost memory window | Tier 1 (API leak) |
| RankEmbedBERT trains on 70 days of search logs | Tier 1 (court documents) |
| `goodClicks`, `badClicks`, `lastLongestClicks` exist as ranking attributes | Tier 1 (API leak schema) |
| Pages with backlinks from Tier-1 publications outperform | Tier 4 (correlation studies) |
| Specific dwell-time thresholds correlate with rankings | Tier 4 (Backlinko et al.) — directional only, not causal |
| Long titles get truncated in SERPs at ~60 chars | Tier 1 (Google docs + observation) |
| HTTPS is a ranking signal | Tier 3 (Google employee statements) |

When in doubt, cite the source, note the tier, and let the reader weigh it.
