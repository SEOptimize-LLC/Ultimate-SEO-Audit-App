# Click Signals & The ABC Framework (2026)

> Reference for understanding how Google uses in-SERP click signals as ranking inputs, and the practical framework for making recommendations grounded in those signals. Synthesized from the May 2024 Google API leak, US v. Google antitrust testimony (2024-2025), Google patents, and Cyrus Shepard's analysis at Zyppy Signal (March 2026).

## The Core Principle

Click signals are **outcomes you earn, not levers you pull directly.**

The framework dismisses two common misframings:

1. **"Click signals don't exist as a ranking factor."** Wrong. Google's NavBoost, Glue, and RankEmbedBERT systems all use click data as core inputs.
2. **"Optimize CTR / dwell time directly."** Also wrong. The signals are noisy, squashed, contextually weighted, and operate on long windows. You cannot tactically lift "dwell time" by adding scrollytelling or autoplay video.

The right framing: **click signals reflect genuine relevance, usefulness, and satisfaction. Optimize for those, and the click signals follow.**

## How Google Uses Click Data

### NavBoost

Documented in the Google API leak (May 2024) and confirmed in DOJ antitrust testimony. NavBoost is a ranking algorithm that:

- **Memorizes ~13 months of user click data** per query
- **Re-ranks results** based on how users have historically engaged with them
- **Weights signals by query, position, device, location, language, user type** (this "slicing" is what prevents simple manipulation)
- Functions as one of Google's "most important" ranking systems per leaked internal docs

**CRAPS — where NavBoost's click data lives.** In the leaked API the click attributes below are not stored under a module literally named "NavBoost." They live in a sub-module the leak calls `QualityNavboostCraps*` (e.g. `QualityNavboostCrapsCrapsData`, `QualityNavboostCrapsCrapsUrlSignals`). "CRAPS" is the leak's own internal name for the NavBoost click-and-impression signal container; the SEO community commonly back-formats it as "Click And Results Prediction System," but that expansion is *not* itself in the leak. Practically: when you meet "CRAPS" in a leak write-up or a conference talk, it is NavBoost's click data by another name — everything in this section (goodClicks, badClicks, lastLongestClicks, squashing, the 13-month window) is CRAPS. This mapping is LEAK-DERIVED — the module names are documented in the May 2024 Content Warehouse leak, not confirmed by Google as a live ranking lever.

The 13-month window matters operationally: changes you make to a page take **weeks to months** to fully propagate through NavBoost. Don't promise a client "we'll see CTR-driven ranking lift in 30 days."

### Host- and Topic-Level Click Aggregation

NavBoost does not only score clicks at the individual URL. The leak documents click aggregation **above the URL** — at the host (whole-site) level and, through query grouping, at the topic-cluster level:

- **Host-level.** The leaked `crapsAbsoluteHostSignals` (and related host-scoped CRAPS fields) record click behaviour aggregated across the entire host, not just one page. A site that consistently earns satisfying clicks accumulates a host-level click reputation that travels to its other pages.
- **Topic / query-cluster level.** Because NavBoost memorises click behaviour *per query* and slices by query, the aggregate of the related queries a site wins becomes a topic-level signal. Winning the clicks across a coherent cluster of queries is the click-signal side of topical authority.

This is the mechanism that links in-SERP click behaviour to **topical authority**: a page's clicks don't just help that page — sustained satisfying clicks across a topic feed a host- and topic-level reputation that lifts sibling pages on the same theme. It is the click-signal counterpart to the embedding-based topic measurement documented in [seo-fundamentals-2026.md — "Topical authority is measured numerically"](./seo-fundamentals-2026.md#topical-authority-is-measured-numerically): one side measures topic focus from content vectors, the other from where users actually click.

Two host-level attributes reinforce this from outside the query stream:

- **`chromeInTotal`** — "Site-level Chrome views," aggregate Chrome browsing volume to the host (covered in the sitewide-signals section of [seo-fundamentals-2026.md](./seo-fundamentals-2026.md)).
- **`directFrac`** — a distinct host-level attribute described in leak analyses as the **proportion of a site's traffic that is direct / branded** (users arriving by typing the URL or via branded navigation rather than through ranked results). A high `directFrac` reads as real users seeking the brand out directly, independent of any single query's click data — a different host-level signal from `chromeInTotal`, not a synonym for it.

All of the above are LEAK-DERIVED — documented in the May 2024 leak as recorded attributes, not confirmed by Google as weighted ranking levers. Treat them as evidence that click behaviour is aggregated above the page, not as dials to turn.

### Per-Locale Slicing: Segment Before You Diagnose

Because NavBoost weights and stores click signals **separately by country, device, and language** (the "slicing" noted above), a page's blended CTR can hide the real problem. A page can satisfy desktop users in one country while pogo-sticking on mobile or in another locale — and because those are scored in different slices, the mobile or secondary-market failure never gets averaged away inside Google, even though it disappears inside a single blended GSC number.

**Analysis guidance:** when a click-signal finding looks ambiguous, segment GSC Search Analytics before concluding:

- Split by **device** (Desktop / Mobile / Tablet) and compare position-adjusted CTR per device. A page at baseline on desktop but well below baseline on mobile is a mobile-experience or mobile-snippet problem, not a sitewide one.
- Split by **country** — a page that performs in its primary market but not in a secondary one points to intent/locale mismatch, not a universal snippet defect.
- Split by **query / search appearance** where relevant — the slice that underperforms tells you which snippet or intent to fix.

Diagnose and recommend at the slice that is actually failing. Recommending a global title rewrite because blended CTR looks low — when only the mobile slice is weak — wastes editorial cycles and can regress the slice that was already winning.

### Glue

A second click-data system that assembles and re-ranks the SERP itself — deciding which results, snippets, AI Overview citations, "People Also Ask" boxes, and other features appear and in what order.

### RankEmbedBERT and FastSearch

Used to ground AI Overview and AI Mode responses. Trained on **70 days of search log data** plus human-rater scores. This is the click-signal feedback loop that determines which content gets cited in AI answers — which means click signals indirectly drive AI search visibility too.

## The Documented Click Attributes

From the Google API Content Warehouse leak, specific attributes Google records:

| Attribute | What it captures | Practical signal |
|---|---|---|
| `impressions` | URL appears in SERP | Not all SERP appearances are equal — Google "tests" URLs in different positions |
| `goodClicks` | Long click — user stayed on the destination | Page was useful for the query |
| `badClicks` | Short click — user bounced back to SERP quickly | Page mismatched the query intent |
| `lastLongestClicks` | The click that ended the session for that query | Page fully resolved the user's question |

**Important:** Google explicitly notes click signals are noisy. Position, snippet appearance, brand recognition, and many other factors skew the raw data. The "squashing" in the leaked code refers to Google filtering out manipulated and noisy signals before they affect rankings.

### How Squashing Vets Clicks

"Squashing" is the leak's term for the filtering NavBoost applies so raw click counts can't be gamed — the mechanism behind the "click signals are noisy" caveat above. The leak and the DOJ testimony together describe several vetting layers:

- **IP / cookie priors.** Clicks are weighted against per-IP and per-cookie priors, so a burst of clicks from one source (or a narrow set of sources) is discounted rather than counted at face value. One machine can't vote a hundred times.
- **Voter-token limits.** Clicks are treated like votes with per-voter limits — a single user/session contributes a bounded amount of signal, capping how much any one actor can move a query.
- **`unicornClicks` — the vetted subset.** The leak names `unicornClicks` as the clicks that survive filtering (the "clean" clicks that count), alongside `unsquashedClicks` (the raw, pre-squashing count). NavBoost leans on the squashed/vetted subset, not the raw total. Both `unicornClicks` and `unsquashedClicks` are already referenced as leak-grounded inputs in `auditors/click_signal_auditor.py` — `unicornClicks` is present as the *vetted* count, not absent.
- **Log-style compression.** High click counts are squashed (compressed) so a page with 100× the clicks does not get 100× the signal — this blunts brute-force volume attacks.

**Why this matters for recommendations:** the "don't buy click traffic / don't run click farms" guidance in [Things You Cannot Do](#things-you-cannot-do-and-why) rests on this mechanism, not on assertion. Purchased or botted clicks share IPs, cookies, and timing patterns that the priors and voter-token limits are built to discount; they land in `unsquashedClicks` but largely fail to become `unicornClicks`. The squashing layer is why the effect is small, short-lived, and detectable — and why the durable path is earning genuine clicks, not manufacturing them. All squashing detail here is LEAK-DERIVED (May 2024 leak plus DOJ antitrust testimony), not a Google-confirmed weighting.

## The ABC Mental Model

Some Google engineers internally describe the three durable ranking inputs as:

- **A** — **Anchors** (links, particularly anchor text from external pages)
- **B** — **Body** (page content, structure, depth, intent matching)
- **C** — **Clicks** (in-SERP user behavior, weighted and contextualized)

None of the three are tactical levers a marketer can directly pull. All three are outcomes of doing the underlying work well:

- Anchors come from publishing content worth linking to
- Body comes from genuinely answering query intent with depth and accuracy
- Clicks come from earning the click, proving usefulness, and proving satisfaction

When making recommendations, address the underlying causes — not the metrics that show whether the underlying work succeeded.

## The Three-Step Practitioner Framework

Adapted from Cyrus Shepard's framing, mapped to the documented click attributes.

### Step 1: Earn the Click (improves `impressions → clicks` ratio)

Goal: get the user to choose your result over the others on the SERP.

**Recommendations to make:**

- **Match query intent in the title** — the title should signal "this page answers exactly what you searched for." If the searcher typed "best running shoes for flat feet" and your title says "Running Shoes Guide," you've lost before the click.
- **Front-load the primary keyword** in the title.
- **Write meta descriptions that promise the deliverable**, not generic site boilerplate. Specific value proposition in the first 120 characters (the part that always shows on mobile).
- **Don't clickbait** — Google has metrics that specifically penalize titles that mismatch content. The signal feeds back through `badClicks` (short return-to-SERP behavior).
- **Build brand recognition** — branded queries and recognized site names get higher CTR at the same position. Brand investment compounds.

**Recommendations NOT to make:**

- "Use power words like 'ultimate' and 'best' to drive clicks" — overused and often classified as clickbait if not backed by the content.
- "A/B test 50 title variants" — without enough impressions, the noise dominates the signal. Title testing only produces meaningful data on high-impression pages.

### Step 2: Prove Usefulness (improves `goodClicks` vs `badClicks` ratio)

Goal: when a user clicks, they stay long enough to get value rather than bouncing back to the SERP.

**Recommendations to make:**

- **Match the page's content to the title's promise** — the #1 cause of `badClicks` is title-content mismatch.
- **Deliver the answer above the fold** — don't bury the answer behind 600 words of throat-clearing. Users who skim and don't see what they came for bounce fast.
- **Improve loading performance** — slow pages are abandoned before content even renders. Connect this to the existing Core Web Vitals work.
- **Make content actually skimmable** — clear headings, short paragraphs, useful subheads. Users decide in 5 seconds whether to stay.

**Recommendations NOT to make:**

- "Increase time on page by adding a video at the top" — autoplay video often kills the very metric it's intended to lift.
- "Add a related-articles section to lower bounce rate" — bounce rate isn't the signal Google uses (Analytics bounce rate is irrelevant); engagement quality on the actual content is.
- "Pad word count to increase dwell time" — filler creates the opposite of what we want. Google's content-quality systems specifically deprioritize padded content.

### Step 3: Prove Satisfaction (improves `lastLongestClicks` ratio)

Goal: the user gets their full answer from your page and doesn't need to click another result.

**Recommendations to make:**

- **Answer the obvious follow-up questions on the same page** — if someone searches "how do tankless water heaters work" and reads your article, they're going to wonder "are tankless heaters worth the cost?" next. Address it inline. If you don't, they go back to the SERP and click a competitor.
- **Provide evidence for claims** — citations, screenshots, examples, data, original photos. Pages that just assert things lose to pages that prove things.
- **Show the next step** — "if you decide to install one, here's what to expect." Anticipate the user's next move.
- **Local example:** A directory listing should show competitor information so the user doesn't have to leave to compare. Sounds counterintuitive — but the page that fully serves the user wins the `lastLongestClicks` signal.

**Recommendations NOT to make:**

- "Add 5 internal links to keep them on your site" — internal linking matters but for a different reason (PageRank flow, topical authority). Click satisfaction isn't about keeping users captive on your domain; it's about resolving their query.

## Reading GSC Performance Data Honestly (interpretation caveats)

Before any click-signal finding ships, the GSC Performance numbers behind it have to be read correctly. These caveats (Foley Carter, GSC Lesson 1) keep the auditor from drawing wrong conclusions from a right-looking number:

- **"Average position" is a time-weighted worldwide average, not current rank.** A page showing position 7.8 over 12 months may sit at 3 today and 15 six months ago. Never read the default figure as "where it ranks now." To approximate current rank, **filter by the relevant country AND narrow the timeframe** (e.g. last 28 days, single market) before quoting a position. The `click_signal_auditor` already slices by country/device/language and reads the correct window — honour that slicing when interpreting, and state the filter/timeframe context alongside any position number in a deliverable.
- **Clicks down + impressions flat while still on page 1 = intra-page-1 slippage, not a demand or indexation loss.** As a URL drifts from #1 toward the bottom of page 1, clicks fall but impressions hold (it's still being shown). Don't diagnose this as lost traffic-demand or a deindexation; it's a ranking-within-page-1 problem — a click-signal / relevance issue, exactly the ABC levers below.
- **Lost / deindexed-URL detection needs zero on BOTH metrics.** A URL is "dropped from the index" only if it has **zero clicks AND zero impressions** in the current period (having had traffic in the prior period). Zero clicks with non-zero impressions ≠ gone — the page was still served, it just wasn't clicked. When flagging "pages Google dropped," gate on both columns being zero, then live-verify the URL still resolves (a live-200 page with zero impressions was dropped by Google, not removed by the site).
- **CTR bands are a coarse triage heuristic, subordinate to position-adjusted CTR.** As a rough read: <1% very poor, 1–2% needs improvement, 3–4% acceptable, 5%+ good; branded queries and brand misspellings run much higher by nature and should never be benchmarked against non-brand bands. But the auditor's **position-adjusted** CTR baseline (is CTR below expected *for this position*?) is the stronger signal — use the flat bands only as a sanity check, never in place of the position-adjusted comparison.
- **Mind the data caps.** GSC's UI is capped at ~1,000 rows, retains ~16 months, and lags ~2 days. "Top queries" means the first 1,000 for the property, not all of them. A finding built on a truncated export ("this page has no queries") may just be hitting the cap — pull via the API (uncapped by the 1,000-row limit) for anything load-bearing.

## What This Means for Audit Recommendations

When the auditor surfaces a finding like "Page X has low CTR" or "Page Y has high bounce-back behavior," frame the recommendation around the **underlying cause**, not the metric:

| Surface metric | Wrong recommendation | Right recommendation |
|---|---|---|
| Low CTR at position 8 | "Improve CTR with power words" | "Snippet doesn't match query intent — rewrite to lead with the specific deliverable users searched for" |
| High bounce-back behavior | "Reduce bounce rate by 20%" | "First 100 words don't match the title's promise — restructure the intro to deliver the answer faster" |
| Page rarely cited in AI Overviews | "Optimize for AI Overviews" | "Page doesn't fully answer the follow-up questions users are asking — expand to cover [specific gaps]" |
| Page ranks but converts poorly | "Improve dwell time" | "Visitors aren't matching the page's intent — review SERP queries and align content to actual searcher needs" |

## Things You Cannot Do (and Why)

- **Click farms / bot clicks** — Google's click signals are squashed and contextually weighted. Bot traffic doesn't match the patterns of real human click sequences (mouse movement, dwell distribution, query-context relationships). Detection is high; effects are short-lived; risks include manual action. See [How Squashing Vets Clicks](#how-squashing-vets-clicks) for the IP-prior / voter-token / `unicornClicks` mechanism that makes this true — the guidance rests on how the filtering works, not on assertion.
- **Promise specific timelines on click-signal-driven ranking changes** — NavBoost's 13-month memory means changes propagate over weeks to months. The page needs to accumulate enough new click data to overcome the historical baseline. Don't quote 30-day timelines.
- **Optimize click-by-click metric tactically** — the signals are systemic outcomes. Fixing one thing on one page produces small effects; fixing the underlying cause across the site produces larger effects.

## Connection to Other Framework Documents

- **[seo-fundamentals-2026.md](./seo-fundamentals-2026.md)** — General SEO fundamentals; the "What Google DOES Use" section summarizes click signals. This document goes deeper.
- **[ranking-factors-checklist-2026.md](./ranking-factors-checklist-2026.md)** — Practitioner ranking-factors checklist. Its **Click Signals cluster** operationalises this document into pass/fail audit checks. Use the checklist as the "what to check" list and this document as the "why it works" mechanism reference — don't duplicate the checklist items here.
- **[Skills/quick-win/](../../quick-win/)** — Striking-distance ranking analysis. When recommending CTR improvements on striking-distance pages, use the position-adjusted baseline guidance, not raw "is CTR low or high" framing.
- **[Skills/ai-search-optimization/](../../ai-search-optimization/)** — AI Overview citations. Click signals feed AI Overview selection through the FastSearch / RankEmbedBERT loop documented above.

## Sources

- **Google API Content Warehouse leak** (May 2024) — leaked internal documentation of ranking signals, including NavBoost attribute schema and click-signal data structures.
- **US v. Google antitrust testimony** (2024-2025) — Department of Justice trial testimony confirming click signals as fundamental ranking inputs and the role of user data in Google's competitive moat.
- **Google patent US8661029B1** — describes long-click ratios and re-ranking based on click duration.
- **Cyrus Shepard, Zyppy Signal — "Google Click Signals and SEO Rankings"** (March 25, 2026) — practitioner-focused synthesis of the leak, antitrust testimony, and patents into a usable workflow. https://signal.zyppy.com/p/google-click-signals
- **Google's published statements** — Google has acknowledged using click data in ranking; engineers (Gary Illyes, John Mueller) have qualified that the signals are noisy, squashed, and not directly optimizable.
