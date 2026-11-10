# Google Algorithm Updates Timeline (2023-2026)

> **Last updated:** 2026-11-10 (December 2025 to September 2026 checked against the dashboard feed)
> **Purpose:** Correlate observed traffic drops with confirmed Google algorithm changes.
> **Maintained by:** Traffic Loss Analysis Skill

---

## How to Use This Reference

When analyzing traffic losses, overlay the loss onset date against this timeline. Follow this process:

1. **Identify the drop onset date** from Google Search Console or analytics data (use the first day of measurable decline, not when you noticed it).
2. **Scan the timeline below** for any confirmed updates within a 14-day window before the drop onset.
3. **Check the Impact Signatures table** to see if the observed loss pattern matches the typical fingerprint of that update type.
4. **Assess correlation strength** using the Correlation Strength Guide at the bottom of this document.

A traffic drop within 1-2 weeks of a confirmed update is a strong correlation signal, though not proof of causation. Multiple factors can overlap, and Google frequently runs updates in parallel. Always investigate site-specific factors (technical issues, content changes, competitor movements) alongside algorithm correlation.

---

## Update Type Legend

| Update Type | Description |
|---|---|
| **Core Update** | Broad quality and relevance update affecting all search results. Reassesses content quality, authority, and user satisfaction signals across the entire index. Typically rolls out over 2-4 weeks. |
| **Helpful Content Update (HCU)** | Targets sites with substantial amounts of unhelpful, unsatisfying, or search-engine-first content. Uses a site-wide classifier that can suppress an entire domain based on aggregate content quality. Absorbed into core updates as of March 2024. |
| **Spam Update** | Targets specific web spam violations including cloaking, hacked content, auto-generated spam, scraper sites, and manipulative redirect schemes. Can result in manual actions or algorithmic demotions. |
| **Link Spam Update** | Specifically targets manipulative link-building practices including paid links, link exchanges, PBN (Private Blog Network) usage, and large-scale guest posting for links. Neutralizes or devalues manipulative links. |
| **Reviews Update** | Evaluates review-type content for depth, first-hand experience, and genuine expertise. Initially product-focused, expanded in 2023 to cover services, destinations, media, and all review content types. |
| **Local/Maps Update** | Affects local pack rankings, Google Maps results, and local business visibility. Adjusts proximity weighting, GBP signal importance, and local relevance factors. |
| **AI Overview Expansion** | Not a traditional ranking update. Expands the presence of AI-generated overview panels in search results, which intercept clicks from organic listings without changing organic positions. Causes CTR erosion rather than ranking loss. |
| **Page Experience Update** | Evaluates Core Web Vitals (LCP, INP, CLS), mobile usability, HTTPS, and intrusive interstitial signals as ranking factors. |

---

## Timeline

### 2023

#### Q1 2023

**March 2023 Core Update**
- **Dates:** March 15 - April 4, 2023
- **Type:** Core Update (Quality)
- **Duration:** 20 days
- **Summary:** Broad quality update with moderate volatility across most verticals. This was a standard core update that reassessed content quality and relevance. E-E-A-T signals (Experience, Expertise, Authoritativeness, Trustworthiness) continued to gain weight. Sites with thin content or outdated information saw declines, while sites demonstrating genuine expertise saw gains.
- **Key Impact Areas:** Health/medical, finance (YMYL), product review sites, news publishers

#### Q2 2023

**April 2023 Reviews Update**
- **Dates:** April 12 - April 25, 2023
- **Type:** Reviews Update
- **Duration:** 13 days
- **Summary:** Landmark expansion of the reviews system beyond product reviews to encompass ALL review-type content including services, businesses, destinations, media, games, and more. The system began evaluating whether review content demonstrates first-hand experience, original research, and genuine insight rather than surface-level summaries. Previously named "Product Reviews Update," Google dropped "Product" from the name to reflect the broader scope.
- **Key Impact Areas:** Affiliate sites, comparison sites, "best of" listicle publishers, travel review content

#### Q3 2023

**August 2023 Core Update**
- **Dates:** August 22 - September 7, 2023
- **Type:** Core Update (Quality)
- **Duration:** 16 days
- **Summary:** Significant volatility across verticals. One of the more impactful core updates of 2023, many sites experienced double-digit traffic swings. This update appeared to further refine quality signals and penalize sites relying on programmatic content at scale.
- **Key Impact Areas:** Content-heavy publishers, programmatic SEO sites, forums, UGC platforms

**September 2023 Helpful Content Update**
- **Dates:** September 14 - September 28, 2023
- **Type:** Helpful Content Update
- **Duration:** 14 days
- **Summary:** **The single most destructive algorithm update for content publishers in recent memory.** This update introduced a refined "site-wide classifier" that evaluated domains holistically. If Google determined that a site had a substantial proportion of unhelpful content, the classifier could suppress the entire domain in rankings — including pages that were individually high-quality. The impact was devastating and unprecedented: many established content sites lost 50-90% of their organic traffic virtually overnight. The classifier proved extremely difficult to recover from, and many affected sites had still not recovered by 2025-2026. This update fundamentally changed how Google evaluated content sites and established that domain-level quality signals could override page-level quality.
- **Key Impact Areas:** Independent publishers, niche content sites, sites mixing quality content with filler, AI-assisted content farms, sites with large archives of outdated content
- **Recovery Note:** Many sites have NEVER recovered from this update. Recovery, when possible, required aggressive pruning of low-value content, complete content strategy overhauls, and waiting for subsequent core updates to reassess. The HCU classifier appears to be persistent and slow to lift.

#### Q4 2023

**October 2023 Core Update**
- **Dates:** October 5 - October 19, 2023
- **Type:** Core Update (Quality)
- **Duration:** 14 days
- **Summary:** This core update began rolling out while the September HCU was still settling, making attribution particularly difficult. Some sites that dropped during HCU saw further declines, while a small number saw partial recovery signals. The overlapping rollout created significant confusion in the SEO community about which update was responsible for observed changes.
- **Key Impact Areas:** Continued quality refinement across all verticals

**October 2023 Spam Update**
- **Dates:** October 4 - October 20, 2023
- **Type:** Spam Update
- **Duration:** 16 days
- **Summary:** Ran concurrently with the October Core Update. Targeted cloaking (showing different content to Googlebot vs. users), hacked content, auto-generated spam at scale, and doorway pages. Sites engaging in overt manipulation saw severe penalties including complete deindexing.
- **Key Impact Areas:** Hacked/compromised sites, cloaking operations, auto-generated content farms

**November 2023 Core Update**
- **Dates:** November 2 - November 28, 2023
- **Type:** Core Update (Quality)
- **Duration:** 26 days
- **Summary:** The final core update of 2023 and one of the longer rollouts of the year. Some SEO analysts observed partial recovery for sites hit by HCU, though this was inconsistent. The update continued Google's trajectory of rewarding content demonstrating genuine expertise and first-hand experience.
- **Key Impact Areas:** Broad quality reassessment across all verticals

**November 2023 Reviews Update**
- **Dates:** November 8 - December 7, 2023
- **Type:** Reviews Update
- **Duration:** 29 days
- **Summary:** The last standalone Reviews Update that Google would run. This was subsequently integrated into the core ranking system. The long rollout period (nearly a month) suggested significant changes to how review content was evaluated. After this update, review quality signals became a permanent part of core ranking rather than a separate periodic update.
- **Key Impact Areas:** All review-type content — product, service, destination, media reviews

---

### 2024

#### Q1 2024

**March 2024 Core Update**
- **Dates:** March 5 - April 19, 2024
- **Type:** Core Update (Quality) + HCU Integration
- **Duration:** 45 days
- **Summary:** **The most significant algorithm update of 2024 and arguably one of the most consequential in Google's history.** This massive 45-day rollout formally absorbed the Helpful Content system into the core ranking algorithm, eliminating standalone HCU updates going forward. The update introduced three new spam policies targeting emerging abuse patterns:
  - **Scaled Content Abuse:** Targeting mass-produced content (whether AI or human-generated) created primarily to manipulate search rankings, not serve users.
  - **Site Reputation Abuse ("Parasite SEO"):** Targeting third-party content hosted on reputable domains primarily to exploit the host site's ranking signals (e.g., coupon pages, sponsored content sections on news sites).
  - **Expired Domain Abuse:** Targeting the purchase of expired domains with existing authority to host low-quality or unrelated content.
  Google stated this update would reduce low-quality, unoriginal content in search results by 40%. Some sites affected by the September 2023 HCU saw partial recovery, though recovery was inconsistent and incomplete for most.
- **Key Impact Areas:** AI content farms, parasite SEO operations, expired domain networks, programmatic content sites, HCU-affected sites (some recovery)

**March 2024 Spam Update**
- **Dates:** March 5 - March 20, 2024
- **Type:** Spam Update
- **Duration:** 15 days
- **Summary:** Launched simultaneously with the March Core Update to enforce the three new spam policies. Targeted the same abuse patterns: scaled content abuse, site reputation abuse, and expired domain abuse. Sites found in violation faced manual actions and algorithmic demotions. This was one of the most aggressive spam enforcement actions Google had taken in years.
- **Key Impact Areas:** Same targets as the core update spam policies

#### Q2 2024

**May 2024 — AI Overview Launch**
- **Date:** May 14, 2024 (Google I/O announcement and initial US rollout)
- **Type:** AI Overview Expansion (Search Feature Launch)
- **Summary:** Google officially launched AI Overviews (formerly Search Generative Experience / SGE) in US search results. Initially deployed conservatively, appearing primarily for informational queries where Google had high confidence in the generated response. AI Overviews appeared at the top of search results, above organic listings, providing AI-generated answers with cited sources. The immediate impact on organic CTR was measurable but moderate, as Google limited the feature to a subset of queries. This marked the beginning of a fundamental shift in how search results were presented.
- **Key Impact Areas:** Informational queries, health queries, how-to content, definition/explanation queries

**June 2024 Core Update**
- **Dates:** June 20 - July 10, 2024
- **Type:** Core Update (Quality)
- **Duration:** 20 days
- **Summary:** A follow-up core update that continued refining the changes introduced in March 2024. Notably, this update provided additional recovery signals for some sites that had been affected by the September 2023 HCU and March 2024 core update. However, recovery was partial and selective — Google appeared to be incrementally re-evaluating sites that had made substantial quality improvements rather than broadly reversing previous actions.
- **Key Impact Areas:** Partial HCU recovery for improved sites, continued quality refinement

#### Q3 2024

**August 2024 Core Update**
- **Dates:** August 15 - September 3, 2024
- **Type:** Core Update (Quality)
- **Duration:** 19 days
- **Summary:** Another core update in the ongoing series of quality refinements. More HCU partial recoveries were observed, giving hope to publishers who had invested months in content quality improvements. The update also appeared to adjust how Google weighted user engagement signals and content freshness.
- **Key Impact Areas:** Additional HCU recovery, engagement signal refinement, content freshness

**August 2024 — AI Overview Expansion**
- **Dates:** Throughout August 2024
- **Type:** AI Overview Expansion
- **Summary:** Google significantly expanded AI Overviews to cover more query types and began rolling out to additional countries beyond the US. The expansion included more commercial queries, comparison queries, and multi-step informational queries. Publishers began reporting measurable CTR declines for queries where AI Overviews now appeared, even when their organic rankings remained stable.
- **Key Impact Areas:** Expanded query coverage, international rollout, increased CTR impact on informational content

#### Q4 2024

**November 2024 Core Update**
- **Dates:** November 11 - December 5, 2024
- **Type:** Core Update (Quality)
- **Duration:** 24 days
- **Summary:** Year-end quality update continuing the trajectory of 2024's focus on content quality, E-E-A-T signals, and user satisfaction. This update appeared to further integrate AI-driven quality assessment into the core algorithm. Some sites reported significant position changes in competitive verticals.
- **Key Impact Areas:** Competitive verticals, YMYL content, authority signals

**November 2024 — AI Overview Expansion**
- **Dates:** Throughout November 2024
- **Type:** AI Overview Expansion
- **Summary:** Significant expansion of AI Overview triggers. Google began showing AI Overviews for a substantially larger percentage of queries, including more navigational and transactional query types that had previously been excluded. The expansion included more sophisticated multi-source synthesis and improved citation handling. CTR impact became more pronounced across a wider range of content types.
- **Key Impact Areas:** Broader query type coverage, navigational queries, transactional queries, increased publisher CTR erosion

**December 2024 Spam Update**
- **Dates:** December 2024
- **Type:** Spam Update / Link Spam Update
- **Summary:** End-of-year spam targeting update focused on link spam and manipulation patterns. Targeted sophisticated link schemes including tiered link building, link insertions into existing content, and coordinated link exchange networks. Also addressed new forms of AI-generated link spam and automated outreach manipulation.
- **Key Impact Areas:** Sites relying on manipulative link building, PBN networks, paid link schemes, AI-generated link spam

---

### 2025

#### Q1 2025

**January 2025 — AI Overview Expansion**
- **Dates:** January 2025
- **Type:** AI Overview Expansion
- **Summary:** AI Overviews rolled out to additional countries and languages. Query coverage expanded further with improved handling of nuanced, multi-faceted queries. Google introduced enhanced citation formatting and source attribution within AI Overviews. The feature began appearing for a broader range of local and service queries.
- **Key Impact Areas:** International markets, local queries, service queries, multi-language support

**February 2025 — AI Overview Expansion (Shopping & Local)**
- **Dates:** February 2025
- **Type:** AI Overview Expansion
- **Summary:** Google integrated shopping results and local business information directly into AI Overviews. Product comparisons, pricing information, and local business recommendations began appearing within the AI-generated panels. This represented a significant expansion into commercial intent queries and increased the competitive pressure on e-commerce and local business websites.
- **Key Impact Areas:** E-commerce sites, local businesses, product comparison content, shopping queries, local service queries

**March 2025 Core Update**
- **Dates:** March 2025
- **Type:** Core Update (Quality)
- **Summary:** First core update of 2025. Continued the integration of helpfulness signals into core ranking. Some analysts observed this update placed increased weight on originality and unique value-add, further disadvantaging content that merely synthesizes existing information without adding new insight. Sites with strong topical authority and original research appeared to benefit.
- **Key Impact Areas:** Content originality, topical authority, unique value signals, continued quality refinement

#### Q2-Q4 2025

**June 2025 Core Update**
- **Dates:** June 2025 (estimated)
- **Type:** Core Update (Quality)
- **Summary:** Mid-year quality update. Reports indicated increased emphasis on user interaction signals and content that directly satisfies search intent. Sites with high engagement metrics (time on page, low bounce rate for informational queries) appeared to benefit.
- **Key Impact Areas:** User engagement signals, intent satisfaction, content depth

**Ongoing Throughout 2025 — AI Overview Feature Expansion**
- **Type:** AI Overview Expansion (Continuous)
- **Summary:** Throughout 2025, Google continued expanding AI Overview capabilities. Key developments included:
  - Multi-step reasoning for complex queries (follow-up questions within the overview)
  - Enhanced visual elements (images, charts, comparison tables within AI Overviews)
  - Deeper integration with Google Shopping, Maps, and other Google properties
  - Expanded citation model allowing more source diversity
  - Introduction of AI Overviews for more "near me" and hyperlocal queries
  - Video content references within AI Overviews
  - Increasing query coverage across all intent types
- **Cumulative Impact:** By the end of 2025, AI Overviews were triggering on an estimated 30-40% of all search queries (up from roughly 10-15% at May 2024 launch). The cumulative CTR impact on organic results became a primary concern for publishers and SEO professionals, particularly for informational and commercial investigation queries.

---

### 2025 — Confirmed updates added 2026-05-20 (previously missing from this file)

**March 2025 Core Update**
- **Dates:** March 13 – March 27, 2025
- **Type:** Core Update (Quality)
- **Duration:** 15 days
- **Source:** https://status.search.google.com/incidents/zpmwuSwifjDjfrVdaZUx
- **Summary:** First core update of 2025. Continued the trend of integrating helpfulness signals into core ranking. Many sites with informational/blog-heavy content reported visible declines that propagated for weeks after the rollout completed (i.e., the click impact accumulated through April–May 2025 rather than ending at the rollout-end date).
- **Key Impact Areas:** Content quality refinement, informational content sites, E-E-A-T-weak content

**June 2025 — Indexing Issue**
- **Dates:** June 12 – June 13, 2025
- **Type:** Indexing infrastructure incident
- **Source:** https://status.search.google.com/incidents/wNcefVMLpVGGoFLzgMEg
- **Summary:** Short-lived but confirmed Google Search indexing issue. Some sites saw temporary impressions/clicks drops during the incident window. Recovery was generally rapid but in some cases the incident catalyzed a downward step that the next core update (June 30) then compounded.

**June 2025 Core Update**
- **Dates:** June 30 – July 17, 2025
- **Type:** Core Update (Quality)
- **Duration:** 18 days
- **Source:** https://status.search.google.com/incidents/riq1AuqETW46NfBCe5NT
- **Summary:** Mid-year quality update. Continued the trajectory of refining how Google evaluates user-satisfaction signals and content depth. Sites that had been weakened by the March 2025 update commonly saw further declines here — the two updates often compound on the same set of sites.
- **Key Impact Areas:** Same set of vulnerable content profiles as March 2025; recovery from March is uncommon during this window

**August 2025 Spam Update**
- **Dates:** August 26 – September 22, 2025
- **Type:** Spam Update
- **Duration:** 28 days
- **Source:** https://status.search.google.com/incidents/a7Aainy6E9rZsmfq82xt
- **Summary:** Global spam-related update applying to all languages. Larger-than-typical spam-update impact. The full 28-day rollout window means click data shows a sustained decline across the entire window rather than a single-day cliff — the bottom is typically reached at or just after the rollout-end date. **For affected sites, this is frequently the largest single update-driven decline of the 2025 cycle.**
- **Key Impact Areas:** Sites with even partial spam-classifier concerns; sites already weakened by earlier 2025 core updates; e-commerce sites with thin product descriptions and AI-assisted content; sites with manipulative anchor-text patterns

**October 2025 — Search Serving Issue**
- **Dates:** October 3 – October 6, 2025
- **Type:** Serving infrastructure incident
- **Source:** unconfirmed. The incident ID this entry used to cite (`DsirqJ1gpPRgVQeccPRv`) is the December 2025 core update (checked 2026-11-10), so this entry has no verified source. Confirm it on the dashboard history page before using it in a diagnosis.
- **Summary:** Brief Google Search serving issue. For some sites the post-incident period coincided with the start of a recovery from the Aug 2025 Spam Update — possibly because Google's fix recalibrated something in the ranking pipeline that had been holding sites suppressed.

---

### 2025-12 to 2026 — confirmed against the Search Status Dashboard on 2026-11-10

Every entry below is copied from `https://status.search.google.com/incidents.json` (begin and end dates as published). An earlier "January 2026 Core Update" entry was removed: it had no source and the dashboard lists no such update.

**December 2025 Core Update**
- **Dates:** December 11 – December 29, 2025
- **Type:** Core Update
- **Source:** https://status.search.google.com/incidents/DsirqJ1gpPRgVQeccPRv

**February 2026 Discover Update**
- **Dates:** February 5 – February 27, 2026
- **Type:** Discover core update (English-language users in the US). Affects Discover traffic, not web search rankings
- **Source:** https://status.search.google.com/incidents/mYbNTqV1ytDc2fA8hUz4

**February 2026 — Serving Issue**
- **Dates:** February 25, 2026
- **Type:** Serving infrastructure incident
- **Source:** https://status.search.google.com/incidents/TZF4pLmbzFdoBPP6o3iv

**March 2026 Spam Update**
- **Dates:** March 24 – March 25, 2026
- **Type:** Spam Update
- **Source:** https://status.search.google.com/incidents/VbnSXAH4SmEcxPtx4YSD
- **Note:** It ended two days before the March core update began, so ranking data cannot cleanly separate the two.

**March 2026 Core Update**
- **Dates:** March 27 – April 8, 2026
- **Type:** Core Update
- **Source:** https://status.search.google.com/incidents/7eTbAa2jWdToLkraZj5y

**May 2026 Core Update**
- **Dates:** May 21 – June 2, 2026
- **Type:** Core Update
- **Source:** https://status.search.google.com/incidents/wdAXJk6LRRihEjpzEeWE

**June 2026 Spam Update**
- **Dates:** June 24 – June 26, 2026
- **Type:** Spam Update
- **Source:** https://status.search.google.com/incidents/YUX1peHev5a4fkxLDiUQ

**August 2026 Spam Update**
- **Dates:** August 18 – August 21, 2026
- **Type:** Spam Update
- **Source:** https://status.search.google.com/incidents/LEubPCm2octf2uMqCFKE

**September 2026 Spam Update**
- **Dates:** September 24 – October 8, 2026
- **Type:** Spam Update
- **Source:** https://status.search.google.com/incidents/XhUDXP7A67iHCD2kmbVu

**Read the live feed first.** This file goes stale between edits. Phase 3.1 reads `incidents.json` before this file, the same feed task 1.2 uses. The feed holds only the most recent incidents (9 on 2026-11-10, back to December 2025), so drops older than that need this file or the dashboard history page: https://status.search.google.com/products/rGHU1u7OQJGH69TPLS2FnGHp/history

---

## Impact Signatures by Update Type

Use this table to match observed traffic loss patterns against known update type fingerprints:

| Update Type | Typical Impact Pattern | Recovery Timeline | Key Diagnostic Signal |
|---|---|---|---|
| **Core Update (Quality)** | 10-40% traffic shift over 2-4 weeks, then stabilizes. Non-brand keywords most affected. Impacts tend to be page-level or section-level rather than sitewide. | 3-6 months (typically requires next core update for reassessment) | Content quality issues on losing pages; competitors who gained have demonstrably better content, more depth, or stronger E-E-A-T signals |
| **Helpful Content Update** | Sitewide classifier suppresses entire domain, not just low-quality pages. Can cause 50-90% traffic loss across the board. Even strong individual pages are dragged down. Onset is rapid (days, not weeks). | 6-12+ months; many sites NEVER recovered. Requires massive content pruning and quality overhaul, then waiting for core update reassessment. | Site has substantial thin, AI-generated, or search-engine-first content — even if some pages are genuinely excellent. The ratio of helpful to unhelpful content is the key factor. |
| **Spam Update** | Sudden, severe drops on specific pages or sections. Can escalate to sitewide if violations are pervasive. Manual actions may appear in GSC. | Varies widely — fix the violation, submit reconsideration request (if manual action), then wait for next spam update to lift algorithmic suppression. | Specific manipulation patterns identifiable: cloaking, hacked content injection, doorway pages, auto-generated spam, hidden text/links |
| **Link Spam Update** | Authority-dependent keywords most affected — rankings that relied on manipulative links drop while brand queries remain stable. The drop is typically for competitive, high-value keywords. | 3-6 months after cleaning link profile (disavow + removal outreach), then waiting for next link spam or core update. | Backlink profile analysis reveals PBN links, paid links, excessive exact-match anchor text, link exchange networks, or other unnatural patterns. Rankings for easy/low-competition keywords may be unaffected. |
| **Reviews Update** | Affects review-type content pages specifically (product reviews, service reviews, comparison articles, "best of" lists). Non-review content on the same domain is typically unaffected. | Next reviews update cycle (pre-2024) or next core update (post-March 2024 integration). | Review content lacks first-hand experience, original testing, or unique insight. Thin comparison tables, affiliate-heavy content, and reviews that merely aggregate other reviews are typical losers. |
| **Local/Maps Update** | Shifts in local pack rankings, changes in proximity weighting. Business visibility in Maps may change. Local organic results may also be affected. | Varies — depends on the nature of the change. Some shifts are permanent recalibrations. | GBP optimization gaps, citation inconsistencies, proximity factor changes, review signal reweighting |
| **AI Overview Expansion** | Impressions remain stable or even grow, but clicks decline. Organic positions remain unchanged. The loss is gradual (weeks/months) rather than sudden. CTR drops while rank holds. | No traditional "recovery" — this is a structural shift in search behavior, not a penalty. Must adapt content strategy to earn citations within AI Overviews or target queries where AI Overviews don't trigger. | CTR decline with stable positions is the hallmark signal. Informational queries most affected. Check if AI Overviews are triggering for your target keywords by searching in an incognito browser. |
| **Page Experience Update** | Moderate impact (typically 5-15% traffic change). Affects mobile rankings more than desktop. Sites failing Core Web Vitals thresholds are most impacted. | 1-3 months after fixing technical issues and passing CWV assessment. | Core Web Vitals scores in GSC show "Poor" or "Needs Improvement" for affected pages. LCP, INP, and CLS metrics are the key signals. |

---

## Correlation Strength Guide

When assessing whether a traffic drop is related to a known algorithm update, use these confidence tiers:

### Strong Correlation (>80% Confidence)
- Traffic drop onset is within **7 days** of the confirmed update start date
- The observed impact pattern matches the update type signature from the table above
- Affected pages and keywords align with the known focus of the update (e.g., review content dropped during a reviews update)
- Multiple independent data sources confirm the same pattern (GSC, analytics, rank tracking)
- Industry-wide reports confirm similar impacts on comparable sites

### Moderate Correlation (50-80% Confidence)
- Traffic drop onset is within **14 days** of the confirmed update start date
- Partial signature match — some elements align but not all
- Some affected keywords align with update focus, but others don't fit the pattern
- The site has characteristics that would make it vulnerable to the update type, but impact is mixed

### Weak Correlation (<50% Confidence)
- Traffic drop onset is within **30 days** of the confirmed update — could be coincidental
- Mixed signals — the impact pattern doesn't cleanly match any single update type
- Multiple updates occurred within the same window, making attribution ambiguous
- Site-specific factors (technical issues, content changes, seasonal patterns) could explain the drop equally well

### No Correlation
- Traffic drop timing does not align with any confirmed update window
- The update type does not match the affected content type or keyword profile
- The drop is better explained by site-specific factors: server issues, robots.txt changes, content removal, manual penalty, seasonal traffic patterns, or competitor actions

---

## Important Notes

- **Overlapping updates:** Google frequently runs multiple updates simultaneously or in rapid succession. The October 2023 period (Core + Spam updates overlapping) and March 2024 (Core + Spam launched on the same day) are prime examples. Do not assume a single cause — investigate all updates within the relevant window.

- **September 2023 HCU long-tail impact:** The September 2023 Helpful Content Update was uniquely destructive. Many sites that were classified as "unhelpful" have STILL not recovered as of 2025-2026, even after significant content improvements. If a site's traffic decline traces back to September 2023, this is the most likely cause, and recovery requires a comprehensive content strategy overhaul rather than tactical fixes.

- **HCU integration into core (March 2024):** Since March 2024, the Helpful Content system is integrated into core updates. There will be no more standalone HCU updates. Recovery from HCU-related suppression now happens (if at all) during core update reassessments.

- **AI Overview expansion is continuous:** Unlike traditional algorithm updates with defined start and end dates, AI Overview expansion is gradual and ongoing. There is no single "launch date" after the initial May 2024 rollout. Traffic losses attributed to AI Overviews will appear as a slow, steady CTR decline rather than a sudden drop.

- **Official source of truth:** Always verify update dates against [Google's Search Status Dashboard](https://status.search.google.com/products/rGHU1u7OQJGH69TPLS2FnGHp/history). Community reports and SEO tool volatility trackers (Semrush Sensor, Moz MozCast, Advanced Web Ranking) provide supporting evidence but are not authoritative for confirmed dates.

- **Seasonal factors:** Always rule out seasonal traffic patterns before attributing a drop to an algorithm update. Many verticals have predictable seasonal peaks and valleys that can coincide with update windows purely by chance. Compare year-over-year data to establish baseline seasonal patterns.

- **Technical audit first:** Before investigating algorithm correlations, always rule out technical causes: server downtime, robots.txt changes, noindex tags added in error, site migration issues, CDN problems, or manual actions in Google Search Console. A technical issue that coincides with an update window can lead to misattribution.
