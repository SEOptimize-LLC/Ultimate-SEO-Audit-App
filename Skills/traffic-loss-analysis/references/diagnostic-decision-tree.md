# Diagnostic Decision Tree — Root Cause Identification

## How to Use This Decision Tree

After completing Phases 2-10 of the Traffic Loss Analysis, use this decision tree to systematically diagnose the root cause(s). Start with the loss pattern classification, then follow the branches based on evidence collected.

**Important:** Traffic losses frequently have MULTIPLE contributing causes. Score each potential cause independently (0-100 confidence) rather than stopping at the first match.

---

## Stage Overlay — read before Step 1

Every root cause below is either a **failure at one of the four pipeline stages** or a
**non-pipeline cause**. Establishing which, and which stage, narrows the search before any
evidence is gathered.

```
CRAWLABILITY → RENDERING → INDEXABILITY → RANKING
```

Stage mechanics: [stage-1-crawlability.md](../../technical-seo-agent/references/stage-1-crawlability.md),
[stage-2-rendering.md](../../technical-seo-agent/references/stage-2-rendering.md),
[stage-3-indexability.md](../../technical-seo-agent/references/stage-3-indexability.md),
[stage-4-ranking.md](../../technical-seo-agent/references/stage-4-ranking.md).

### The pattern predicts the stage

Stages 1 to 3 fail **binary**: a URL is reachable or it is not, renders or it does not, is
indexed or it is not. Stage 4 degrades **continuously**, as relative position against
competitors. That asymmetry means the shape of the loss curve constrains the cause before
you look at anything else.

| Loss shape | Usually | Rarely |
|---|---|---|
| **Cliff** (>20% in 1–2 weeks) | Stage 1, 2 or 3 binary failure, a measurement artifact, or a manual action | Gradual quality erosion. Quality does not fall off a cliff |
| **Slow bleed** (<10% MoM over 3+ months) | Stage 4 erosion, competitor gains, demand decline | A site-wide robots.txt block or template-wide `noindex`. Those produce cliffs. A page-level `noindex` is the exception: it takes effect only as Google recrawls each page, so Google's traffic-drop guide says it shows as a slower drop |
| **Step then plateau** | An algorithm update (Stage 4) **or** a partial technical failure that hit one template (Stages 1–3) | |
| **Accelerating decline** | Stage 4 compounding: quality, authority, or expanding cannibalisation | A single technical event |

**Use this as a prior, not a verdict.** It tells you which evidence to gather first, and it
rules out branches cheaply. A client reporting a slow six-month bleed does not need an
emergency robots.txt check.

### Clear the non-pipeline causes first

If the loss is not real, or not caused by organic search mechanics, pipeline work is wasted.
Phase 0 in the master skill covers the data integrity checks; these are the causes that
survive Phase 0 and still are not pipeline failures:

| Non-pipeline cause | Signature | Verify by |
|---|---|---|
| **Measurement artifact** | GA4 collapses while GSC clicks stay flat | Consent/tag gating (an Odoo-style cookie bar hard-blocking GTM until "Allow all" will do this), property config, filters. Test before/after consent |
| **Migration credit split** | Post-migration, GSC credits the OLD ranked URL while GA4 credits the NEW landed-on URL | Cross-check both before calling a rebuilt page dead |
| **Conversion tracking break** | Events go to zero at a release boundary | Confirm the event still fires; understated conversions are not lost conversions |
| **Demand decline / seasonality** | Impressions down in step with clicks; category-wide | Query-volume trend and a seasonality control window |
| **SERP feature displacement** | **Impressions flat or up, clicks down, position stable** | AI Overview or SERP-feature presence on the losing queries. Nothing on the site broke |
| **Channel cannibalisation** | Organic down, paid up, same queries | Branch F below |

**The displacement signature is the one most often misdiagnosed as a site problem.**
Impressions holding with clicks falling and position unchanged means the site still ranks
and the SERP changed around it. No pipeline stage failed, and on-page work will not recover
it.

### Branch → stage map

| Branch | Stage | Note |
|---|---|---|
| **A** Sudden drop | **1, 2 or 3** | Binary failure. Check in pipeline order: reachable → renders → indexed |
| **B** Gradual decline | **4** | Erosion. Verify demand held before diagnosing quality |
| **C** Stepped decline | **4** if update-correlated; **1–3** if one template broke | Segment by template before choosing |
| **D** Progressive acceleration | **4** | Compounding cause |
| **E** Keyword cannibalisation | **3** | Index selection between competing URLs, same mechanism as canonicalisation |
| **F** PPC cannibalisation | **Non-pipeline** | Channel shift |
| **G** Content-intent mismatch | **4** | |
| **H** Authority gap vs strategy misalignment | **4** | |
| **I** Devaluation vs slippage | **4** | |

**Note that E is a Stage 3 problem**, not a content problem. Two URLs competing for one query
is Google selecting a representative, which is canonicalisation behaviour. That reframing
changes the fix from "rewrite one page" to "consolidate or canonicalise."

### Sequencing rule

1. Confirm the loss is real (Phase 0) and not a non-pipeline cause from the table above.
2. Use the loss shape to set your prior on the stage.
3. Walk the pipeline **in order**. Do not diagnose Stage 4 with an open Stage 1–3 failure,
   because ranking cannot be assessed on a page that is not reachable, rendered and indexed.
4. Report the verdict per stage, including clean, per the stage-verdict contract in
   [technical-seo-agent/SKILL.md](../../technical-seo-agent/SKILL.md).

---

## Step 1: Classify the Loss Pattern

| Pattern | Definition | Most Likely Causes |
|---------|------------|-------------------|
| **Sudden Drop** | >20% decline in 1-2 weeks | Algorithm update, technical regression, manual action, site migration error |
| **Gradual Decline** | <10% decline month-over-month, sustained over 3+ months | Content decay, competitive displacement, AI Overview expansion, link profile erosion |
| **Stepped Decline** | Sudden drop followed by a plateau (doesn't recover but doesn't keep falling) | Algorithm update with partial stabilization, one-time technical issue |
| **Progressive Acceleration** | Decline that gets worse each month (accelerating) | Compounding issues — typically content decay + competitive displacement + possible technical debt |
| **Cyclical Decline** | Drop that follows a pattern (same time each year) | Seasonal demand shift — NOT an SEO problem (validate with YoY data and Google Trends) |
| **Segment-Specific** | Overall traffic stable but specific segment drops (mobile only, one country, non-brand only) | Segment-specific cause — narrow investigation to that segment |
| **Data Anomaly** | Drop appears in one data source but not others | False alarm — tracking issue, consent changes, GSC processing delay |

---

## Step 2: Evidence-Based Decision Branches

### Branch A: Sudden Drop (>20% in 1-2 weeks)

```
Q1: Does the drop align (within 7 days) with a known Google algorithm update?
├── YES → Go to A1: Algorithm Update Diagnosis
└── NO →
    Q2: Were there any site changes in the 2 weeks before the drop?
    ├── YES → Go to A2: Site Change / Technical Regression
    └── NO →
        Q3: Did backlinks drop significantly (>20% referring domains lost; unsourced heuristic, not a measured threshold, added 2026-11-10)?
        ├── YES → Go to A4: Backlink Loss Event
        └── NO → Go to A5: Unknown Sudden Drop (investigate further)
```

Manual actions are checked in Phase 0 (Step 0.5) on every analysis, whatever the loss shape. A listed action goes straight to A3.

#### A1: Algorithm Update Diagnosis

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| Non-brand keywords most affected + content quality issues found on losing pages | Core Update — Content Quality | High (85-95%) |
| Review-type content pages lost + lacks first-hand experience signals | Reviews / Core Update (helpfulness) Component | High (80-90%) |
| Pages with thin/auto-generated content lost most | Core Update (helpfulness) / Spam Component | High (85-95%) |
| Link-dependent keywords lost most + backlink profile has manipulation signals | Link Spam Component | Medium-High (70-85%) |
| Losses spread evenly across content types with no quality pattern | Core Update — Relevance/Authority shift | Medium (50-70%) |

**HCU naming (added 2026-11-10).** For losses after March 2024, the helpfulness components above are core-update components, because helpful content has been part of core ranking since March 2024 and there are no more standalone HCU updates (`algorithm-updates-timeline.md`, "HCU integration into core (March 2024)"). Use the HCU name only for losses tied to the 2022-2023 standalone Helpful Content Updates.

**Size the move first (added 2026-11-10).** Google's core updates page, for top pages and queries before and after the update: "Small drop in position (dropping from position 2 to 4): There's no need to take drastic action (in fact, we recommend avoiding making changes to content that's already performing well)." And: "Large drop in position (dropping from position 4 to 29): Do a deeper assessment."

**Recovery approach:** Fix content quality issues on losing pages. No quick fix exists for algorithm-based losses. On timing, Google's core updates page says: "some changes can take effect in a few days, but it could take several months for our systems to learn and confirm that the site as a whole is now producing helpful, reliable, people-first content in the long term. If it's been a few months and you still haven't seen any effect, that could mean waiting until the next core update." (added 2026-11-10, replacing an unsourced "3-6 month cycle")

#### A2: Site Change / Technical Regression

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| URL structure changed + redirect chains detected + GSC shows crawl errors | Migration/URL Change Error | High (90%+) |
| Pages deindexed (GSC URL inspection shows "not indexed") | Indexation Regression | High (90%+) |
| CWV scores degraded significantly (LCP >4s, CLS >0.25) | Performance Regression | Medium-High (70-85%) |
| robots.txt or noindex changes detected | Crawl Access Blocked | High (90%+) |
| HTTPS/SSL certificate issues | Security Regression | High (85-95%) |
| JavaScript rendering issues (content not visible to Googlebot) | Rendering Problem | Medium (60-80%) |

**Recovery approach:** Fix the technical issue. Recovery follows the fix and Google's re-crawl. (unsourced "1-4 weeks" timeline removed 2026-11-10)

#### A3: Manual Action

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| GSC shows "Unnatural links to your site" | Link Scheme Penalty | Confirmed (100%) |
| GSC shows "Thin content with little or no added value" | Thin Content Penalty | Confirmed (100%) |
| GSC shows "Pure spam" | Spam Penalty | Confirmed (100%) |
| GSC shows "User-generated spam" | UGC Spam Penalty | Confirmed (100%) |

**Recovery approach:** Address the specific violation, submit a reconsideration request. (unsourced "2-8 weeks" timeline removed 2026-11-10)

#### A4: Backlink Loss Event

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| High-DA referring domains lost + authority-dependent keywords dropped most | Lost Key Backlinks | High (80-90%) |
| Competitor gained the same links you lost | Competitor Link Displacement | Medium-High (70-85%) |
| Links lost were from a single source (e.g., guest post removed, sponsor ended) | Single Source Link Loss | High (85-95%) |

**Recovery approach:** Identify and replace lost links, pursue new link opportunities. Timeline: 2-4 months.

#### A5: Unknown Sudden Drop

If no clear cause is identified:
1. Check for negative SEO (sudden influx of toxic backlinks)
2. Check for SERP layout changes specific to your keywords
3. Look for Google Search bugs (check WebmasterWorld, Search Engine Roundtable for reports)
4. Consider data anomalies (GSC data processing issues, analytics tracking problems)
5. Expand investigation window — the cause may have occurred 2-4 weeks before visible impact

---

### Branch B: Gradual Decline (<10% MoM, 3+ months)

```
Q1: Is the decline primarily on informational / how-to content?
├── YES →
│   Q1a: Are impressions stable but clicks declining?
│   ├── YES → Go to B1: AI Overview / SERP Feature Displacement
│   └── NO (impressions also declining) →
│       Q1b: Are competitors publishing newer/better content on the same topics?
│       ├── YES → Go to B2: Content Decay + Competitive Displacement
│       └── NO → Go to B3: Content Decay (Standalone)
└── NO (affects commercial/transactional pages too) →
    Q2: Are competitors gaining positions on your losing keywords?
    ├── YES → Go to B4: Competitive Displacement
    └── NO →
        Q3: Has search demand for your keywords declined? (Check Google Trends)
        ├── YES → Go to B5: Market/Demand Shift
        └── NO → Go to B6: Authority Erosion (backlink profile weakening over time)
```

#### B1: AI Overview / SERP Feature Displacement

| Evidence | Confidence |
|----------|------------|
| CTR declining with stable positions | High (85-95%) |
| AI Overviews detected on >50% of losing keywords | High (85-95%) |
| Losses concentrate on informational intent queries | High (80-90%) |
| Decline timeline matches AI Overview expansion dates | Medium-High (70-85%) |

**Recovery approach:** This is NOT a traditional "recovery" — it requires content strategy adaptation. See AI Overview recovery strategies in `ai-overview-impact-data.md`. Timeline: 3-6 months of adaptation.

#### B2: Content Decay + Competitive Displacement

| Evidence | Confidence |
|----------|------------|
| Losing pages haven't been updated in 12+ months | High (80-90%) |
| Competitors have newer, more comprehensive content on same topics | High (85-95%) |
| Losing pages have outdated statistics, broken links, stale references | Medium-High (75-85%) |
| Competitor content has stronger E-E-A-T signals | Medium-High (70-85%) |

**Recovery approach:** Content refresh program for top losing pages. Prioritize by traffic impact. Timeline: 2-4 months for first results.

#### B3: Content Decay (Standalone)

| Evidence | Confidence |
|----------|------------|
| Pages peaked 12+ months ago and have been declining steadily | High (80-90%) |
| Content contains outdated information but no competitor displacement visible | Medium-High (70-85%) |
| No algorithm update correlation, no technical issues | Medium (60-75%) |

**Recovery approach:** Systematic content refresh. Timeline: 1-3 months per batch.

#### B4: Competitive Displacement

| Evidence | Confidence |
|----------|------------|
| Specific competitors gained positions on your losing keywords | High (85-95%) |
| Competitor content is objectively better (longer, more comprehensive, fresher) | High (80-90%) |
| New domains appearing in SERPs that weren't there 6 months ago | Medium-High (70-85%) |
| Competitor has stronger backlink profile for affected keywords | Medium (60-80%) |

**Recovery approach:** Competitor gap analysis → content improvement → link building. Timeline: 3-6 months.

#### B5: Market/Demand Shift

| Evidence | Confidence |
|----------|------------|
| Google Trends shows declining interest in your keywords | High (85-95%) |
| Industry-wide traffic declining (not just your site) | High (85-95%) |
| Seasonal pattern that repeats YoY | High (90%+) |

**Recovery approach:** This may not be an SEO problem. Diversify keyword targeting, expand into growing topics. If seasonal: plan content calendar around peaks.

#### B6: Authority Erosion

| Evidence | Confidence |
|----------|------------|
| Referring domains declining gradually over time | High (80-90%) |
| No new quality links being earned | Medium-High (70-85%) |
| Competitors building links faster | Medium (60-80%) |

**Recovery approach:** Proactive link building program. Timeline: 3-6 months.

---

### Branch C: Stepped Decline (sudden drop + plateau)

This pattern almost always indicates an algorithm update. Follow Branch A (Sudden Drop) for diagnosis, but note:
- The plateau suggests the algorithm has "reclassified" your site/pages
- Recovery requires addressing the quality issues the algorithm targeted
- Partial recovery may come with the next core update

---

### Branch D: Progressive Acceleration

```
Q1: Are multiple factors degrading simultaneously?
├── YES → Compound Causes — score each independently:
│   - Content decay accelerating (more pages aging out)
│   - Competitors improving while you're static
│   - Backlink profile weakening while competitors grow
│   - SERP feature displacement increasing over time
│   - Technical debt accumulating
└── NO →
    Q2: Is there a cascading effect?
    ├── YES → Initial cause triggered secondary effects:
    │   Example: Content decay → position drops → less link attraction →
    │   more position drops → less authority → more declines
    └── NO → Investigate for undetected root cause
```

**Recovery approach:** Address all contributing factors simultaneously. Prioritize by impact. This pattern requires the most comprehensive recovery plan.

---

### Branch E: Keyword Cannibalization

Keyword cannibalization occurs when multiple pages on the same domain compete for the same keyword, splitting authority and confusing Google about which page to rank.

**Detection from GSC data:**
- First drop every query with no single resolvable intent (`~/.claude/rules/common/cannibalization-needs-clear-intent.md`). Several pages surfacing for a topic head term is topical coverage, not cannibalization
- Pull `query,page` dimensions — any remaining keyword with 2+ URLs from the same domain is a cannibalization candidate
- Check for URL switching: keyword ranked on URL A in the before period, URL B in the after period
- Check for position instability: keyword fluctuates >5 positions week-to-week

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| Multiple URLs ranking for same keyword + both losing positions | Active cannibalization — neither page has clear authority | High (80-90%) |
| URL A replaced by URL B between periods + position dropped during switch | Google reclassified the canonical URL — transition cost | Medium-High (70-85%) |
| New page published on similar topic + original page's traffic dropped | New page cannibalized existing page | High (85-95%) |
| Losing keywords cluster in one topic area + multiple pages target that topic | Structural/topical cannibalization | Medium-High (70-85%) |

**Recovery approach:** Consolidate competing pages (merge + redirect), differentiate content to target distinct intents, fix internal linking to signal the preferred page. Timeline: 4-8 weeks for initial results after consolidation.

---

### Branch F: PPC Cannibalization

When paid search campaigns target the same keywords as organic listings, paid ads can steal clicks from organic results. This is a contributing factor, not usually the sole cause.

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| Organic clicks down + Paid sessions up + same keywords targeted | Active PPC cannibalization | Medium-High (70-85%) |
| PPC campaigns recently launched/expanded on organic keywords | New PPC overlap causing organic CTR drop | Medium (60-75%) |
| PPC recently paused + organic didn't compensate | PPC dependency — brand visibility from ads was driving organic clicks | Medium (50-70%) |

**Recovery approach:** Coordinate SEO and PPC keyword targeting. For keywords where organic ranks position 1-3, consider reducing PPC bids to let organic capture the clicks. For keywords where organic is weaker, maintain PPC. This is a budget optimization issue, not a technical fix.

---

### Branch G: Content-Intent Mismatch

Search intent evolves over time — Google's understanding of what users want for a query changes. A page can lose traffic without any changes to the page itself because the SERP expectations shifted.

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| SERP now shows different content format (e.g., product pages instead of blog posts) + your page is the old format | Format mismatch — Google now expects a different content type | High (80-90%) |
| SERP now dominated by video results + your page is text-only | Media type mismatch | Medium-High (70-85%) |
| SERP shows short, direct answers + your page is a long-form guide | Depth mismatch — Google wants concise answers, not comprehensive guides | Medium (60-75%) |
| Local pack appeared for a previously national query + your page has no local signals | Geo-intent shift | Medium-High (70-85%) |
| Intent classification changed (informational → commercial) + your page is still informational | Intent category shift | High (80-90%) |

**Key distinction:** Content-intent mismatch is NOT content decay. Content decay = your content degraded over time. Intent mismatch = your content is fine but Google now wants something different.

**Recovery approach:** Reformat content to match the dominant SERP pattern, create new content for the evolved intent, or accept the loss and target different keywords. Timeline: 4-8 weeks per page after reformatting.

---

### Branch H: Content Authority Gap vs Content Strategy Misalignment

**CRITICAL:** These are two distinct diagnoses that are often confused. The Content-Business Alignment analysis from Step 10.0 (using the Topical Authority Rings and Two-Hop Rule) is REQUIRED to distinguish between them.

#### H1: Content Authority Gap

The site covers topics that ARE relevant to its ICP (Ring 2), but the content fails to demonstrate the company's unique expertise. The content reads as generic — it could have been written by anyone with internet access, not by a company that serves this specific audience.

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| Ring 2 topics dominant among losers + Weak execution quality + core-update (helpfulness) timeline correlation (HCU timeline for 2022-2023 losses) + product/service pages relatively stable | Content Authority Gap — relevant topics without unique expertise | Medium-High (70-85%) |
| Ring 2 content lacks proprietary data, customer stories, or product-derived insights + competitors demonstrate stronger E-E-A-T on same topics | Competitive authority deficit on owned topics | Medium (60-75%) |

**Key distinction:** The TOPICS are right. The EXECUTION doesn't demonstrate the company's actual authority. Do NOT diagnose this as "Content Strategy Misalignment."

**Recovery approach:** Rewrite existing content with the company's unique data, product insights, customer stories, and ICP perspective. The content infrastructure (URLs, topics, internal links) can be preserved — only the depth and authority signals need upgrading.

#### H2: Content Strategy Misalignment

The site publishes content on topics that are genuinely outside its sphere of authority (Ring 3-4 dominant). The company has no special insight, data, or customer-derived knowledge on these topics.

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| Ring 3-4 topics dominant among losers + core-update (helpfulness) timeline correlation (HCU timeline for 2022-2023 losses) + sitewide decline across content types | Content Strategy Misalignment — off-topic content failing the core-update helpfulness assessment (the HCU classifier for 2022-2023 losses) | High (80-95%) |
| Ring 4 content was historically a top traffic driver but declined sharply after a core update (after a standalone HCU for 2022-2023 losses) | Core-update (helpfulness) vulnerability from off-topic traffic dependency | High (85-95%) |

**HCU naming in this branch (added 2026-11-10):** for losses after March 2024, read every helpfulness signal here as a core-update component, since the Helpful Content system has been part of core updates since March 2024 (`algorithm-updates-timeline.md`, "HCU integration into core (March 2024)"). Keep the HCU name only for the 2022-2023 standalone updates.

**Recovery approach:** Prune Ring 4 content (noindex or remove), redirect link equity from pruned pages to Ring 1-2 content, rebuild content strategy around Ring 1-2 topics only.

#### Confidence Modifiers (from Alignment Data)

When scoring "Content Strategy Misalignment" as a root cause:

- If >50% of losing pages are Ring 2 (any execution quality) → **decrease confidence by 20-30 points** and redirect to "Content Authority Gap" diagnosis instead
- If >50% of losing pages are Ring 3-4 → increase confidence by +10-15 points
- If >70% of losing pages are Ring 1-2 with Strong/Adequate execution → score below 20 (Unlikely)

When scoring "Core Update (helpfulness), site-wide" as a root cause (named "HCU Site-Wide Classifier" only for 2022-2023 losses; relabelled 2026-11-10):

- Ring 3-4 content >30% of total site content → increase confidence by +10
- Ring 2 Weak execution >50% of content → maintain confidence but note the specific vulnerability is execution quality, not topic selection
- Ring 1-2 Strong/Adequate execution dominant → decrease confidence by -15

---

### Branch I: Devaluation vs Slippage — Rewrite Eligibility Gate

Before recommending a rewrite/refresh for ANY losing page, classify its loss as **devaluation** or **slippage** using query-count movement (Phase 2, Step 2.0) and position-band migration (Phase 4, Step 4.2). This gate decides whether content work is even the right lever — the two verdicts have opposite recovery paths and confusing them wastes the recovery budget. (DERIVED-FROM-TESTING, Daniel Foley Carter.)

| Evidence | Sub-Diagnosis | Confidence |
|----------|--------------|------------|
| Distinct query count per URL FALLING over the two periods + queries evaporating out of the top-30 bands entirely | Devaluation — content problem, Google withdrew the page from queries | High (80-90%) when both signals agree |
| Query count HOLDING + clicks falling + positions stable or only sliding down a band (still ranking) | Slippage — rank/SERP-feature problem, content still valued | High (80-90%) |
| Query count RISING but a head term slipped | Not a loss to fix — Google is valuing the page more | High (85-95%) |

**Recovery approach by verdict:**
- **Devaluation** → substantive rebuild or consolidation. Terminal for tweaks — date-bumps and minor edits do not reverse devaluation, because the fix has to change what Google thinks the page *is*.
- **Slippage** → do NOT rewrite. Fix internal links, freshness signals, and the specific slipped terms; check AIO/PAA displacement (Branch B1 / Branch G) before assuming a rank fix is even needed. The content was never the cause.
- **Rising query count** → leave the page alone. Intervening on a page Google is actively expanding risks breaking a winner.

**Key distinction:** devaluation is Google withdrawing the page from queries (a judgment about the page's value); slippage is the page losing relative position on queries it still serves (a competitive/SERP-layout outcome). Query count is the discriminator — it moves on devaluation and holds on slippage.

---

## Step 3: Confidence Scoring

For each identified cause, score confidence based on evidence strength:

| Score | Level | Evidence Standard |
|-------|-------|-------------------|
| 90-100 | **Confirmed** | Direct evidence (e.g., manual action in GSC, confirmed deindexed pages) |
| 75-89 | **High Confidence** | Strong correlation + matching pattern + supporting data from multiple phases |
| 60-74 | **Medium-High** | Good correlation + pattern match but missing some supporting data |
| 40-59 | **Medium** | Some correlation but multiple possible explanations |
| 20-39 | **Low** | Weak signals, insufficient data, speculative |
| 0-19 | **Unlikely** | Evidence contradicts this cause |

## Step 4: Evidence Documentation

For each diagnosed cause, document:

1. **Diagnosis:** Clear statement of the root cause
2. **Confidence Score:** 0-100 with level label
3. **Supporting Evidence:** List specific data points that support this diagnosis
4. **Contradicting Evidence:** List any data points that argue against it (intellectual honesty)
5. **Data Gaps:** Note what additional data would strengthen or weaken this diagnosis
6. **Recovery Priority:** Based on traffic impact + implementation ease + confidence level

## Common Compound Cause Patterns

| Pattern | Frequency | Description |
|---------|-----------|-------------|
| Algorithm + Content Decay | Very Common | Core update hits site that already had aging content — the update just accelerated an existing trend |
| AI Overview + Content Decay | Common | AI Overviews reduce CTR on informational content that was already losing freshness |
| Technical + Algorithm | Common | Technical issues prevented Google from seeing content improvements, making algorithm impact worse |
| Competitive + Backlink Erosion | Common | Competitors building links while yours stagnate — gap widens over time |
| Multiple Algorithm Updates | Common | Site hit by HCU + subsequent core update — compounding damage |
| Cannibalization + Content Decay | Common | Aging content spawns multiple weak pages targeting the same topic — neither has enough authority to rank well |
| Intent Mismatch + AI Overview | Common | Google shifted to AI Overview answers for a query AND the remaining organic slots favor a different format than your page |
| PPC Cannibalization + Organic Decline | Occasional | PPC campaigns mask organic decline — when PPC budget is cut, the organic weakness is exposed |

---

## Anti-Patterns: Common Misdiagnoses

| Misdiagnosis | Reality | How to Avoid |
|---|---|---|
| "Algorithm penalty" when it's seasonal | YoY data shows same pattern | Always compare YoY before concluding |
| "Technical issue" when it's content quality | Technical metrics are fine, content is stale | Check content freshness and competitor content |
| "AI Overview displacement" when it's actually ranking loss | Positions DID drop, not just CTR | Always check position changes alongside CTR |
| "Competitor stole our traffic" when demand declined | Everyone in the niche lost traffic | Check Google Trends for market-wide demand |
| "We need more backlinks" when content is the problem | Link building won't fix thin content | Evaluate content quality before link strategy |
| Single cause when it's compound | Stopping at first match misses contributing factors | Score ALL potential causes independently |
| "We need more content" when it's cannibalization | Publishing more content on the same topic makes cannibalization worse | Check for cannibalization BEFORE publishing new pages on the same topic |
| "Our content is fine" when intent shifted | Content quality is unchanged but Google now wants a different format | Always check what content FORMAT dominates page 1, not just quality |
| "It's a tracking issue" when the drop is real | Dismissing a real drop as a GA4 glitch | Cross-validate GSC + GA4 + DFS before concluding it's a data issue |
| "Content is off-topic/tangential" when topics are ICP-relevant but poorly executed | The topics connect to the buyer's professional needs through a 1-2 hop chain (e.g., a walkthrough software company writing about teacher feedback IS on-topic), but the content lacks unique insight from the company's perspective — it reads like generic content anyone could write | Build the Business Context Model (Step 1.5) BEFORE classifying topics. Use the Two-Hop Rule to distinguish Ring 2 (ICP-relevant) from Ring 3-4 (truly off-topic). Separate topic relevance from execution quality. The correct diagnosis for relevant-but-generic content is "Content Authority Gap," NOT "Content Strategy Misalignment" |
| "Content strategy is fine" when Ring 3-4 content dominates but individual pages are well-written | Quality execution on off-topic content still triggers HCU — a CRM company writing excellent travel guides is still off-topic | Ring classification overrides execution quality for off-topic assessment. If >30% of content is Ring 3-4, flag strategy misalignment regardless of individual page quality |
| "This page lost traffic, so rewrite it" when the page is only slipping | Query count held — Google still serves the page for the same breadth of queries; it lost relative position, not value. A rewrite disturbs a page Google still trusts and does nothing about the actual cause (position slip or AIO displacement) | Run the Devaluation-vs-Slippage gate (Branch I) before any rewrite. Rewrite only pages whose distinct query count is FALLING; leave slipping pages to internal-link/freshness fixes |
