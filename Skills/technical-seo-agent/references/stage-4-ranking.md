# Stage 4 of 4: Ranking

> **Pipeline position.** `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`
>
> The last stage, and the only one that cannot be worked on directly. Everything here is
> conditional on stages 1 to 3 passing. This file is the **stage contract**: what gates
> this stage, how its findings are weighted, and where the variables live. It deliberately
> does not restate the variables, because the leak-grounded material already in this KB is
> stronger than anything available to summarise.

## What this stage decides

**Where an indexed document places for a given query, and whether it survives re-ranking.**

Ranking is the only stage with a genuinely different character from the first three. Stages
1 to 3 are **binary and diagnosable**: a URL is either reachable or not, renders or not, is
indexed or not, and you can verify each with a fetch. Stage 4 is **comparative, continuous,
and query-specific**. There is no "ranking is clean" verdict, only relative position
against competitors on specific queries.

This asymmetry has a practical consequence that governs the whole stage: **stage 1 to 3
findings can be closed, stage 4 findings can only be improved.** Treat them differently in
a deliverable, and never let stage 4 work displace an open stage 1 to 3 blocker.

---

## The gate

**No stage 4 work begins until stages 1 to 3 are clean or their failures are documented as
blockers.**

This is not a stylistic preference. A page that cannot be crawled, whose content does not
survive rendering, or that is not in the index has **no ranking position to improve**, and
every hour spent on its titles, content depth, schema or internal links returns nothing.

The checklist distribution makes the trap concrete: of the 143 variables in
[ranking-factors-checklist-2026.md](ranking-factors-checklist-2026.md), **116 sit in
clusters 5 to 20, which are predominantly stage 4.** Walking the checklist in numeric order
therefore spends roughly four fifths of the audit effort on this stage. Sort by stage
first. The full procedure, including the binding test, is in
[seo-audit-methodology/SKILL.md § The resolution procedure](../../seo-audit-methodology/SKILL.md).

**The one exception worth naming:** a fix that looks like stage 4 but actually unblocks
invisible content is not stage 4. Removing a `noindex` from a page that should be earning
is stage 3. Getting primary content into the raw HTML is stage 2. Do not file these as
ranking work just because the *goal* is a ranking improvement.

---

## Where the variables live

Stage 4 variables are **already documented and leak-grounded**. This file points; it does
not duplicate.

| Material | Location |
|---|---|
| 116 audit variables, clusters 5–20, with leak attribute, input file, severity, mode and owner per row | [ranking-factors-checklist-2026.md](ranking-factors-checklist-2026.md) |
| NavBoost, Glue, the documented click attributes (`goodClicks`, `badClicks`, `lastLongestClicks`), the ABC model, and what not to recommend | [click-signals-abc-framework.md](click-signals-abc-framework.md) |
| Twiddlers (re-rankers), QDF, QDD/host crowding, query-dependent vs query-independent signals, intent matching over keyword matching, the SEO myth list | [seo-fundamentals-2026.md](seo-fundamentals-2026.md) |
| Titles, meta, headings, content depth, internal links | [onpage-seo-agent/SKILL.md](../../onpage-seo-agent/SKILL.md) |
| Link profile, anchors, referring domains, quality assessment | [backlink-agent/SKILL.md](../../backlink-agent/SKILL.md) |
| Two URLs competing for one query | [cannibalization/SKILL.md](../../cannibalization/SKILL.md) — note this is really a **stage 3** index-selection problem |
| AI Overviews, LLM citation, GEO/AEO | [ai-search-optimization/SKILL.md](../../ai-search-optimization/SKILL.md) |
| Evidence hierarchy for contested ranking claims | [seo-audit-methodology/SKILL.md](../../seo-audit-methodology/SKILL.md) |

---

## Structural properties that change how findings are weighted

**1. Re-rankers sit on top of the core algorithm.** Twiddlers apply conditional
adjustments (local pack, freshness, diversity) after base ranking, which is why a page can
place differently on two near-identical queries. A ranking anomaly on one query and not its
sibling is a re-ranker signature, not a page defect. Do not write an on-page finding for it.

**2. Click signals are feedback, not input.** NavBoost cannot fire on a page that has never
ranked, so click-signal work is meaningless on a page with no impressions. Order matters:
earn a position first, then improve the click behaviour on it.

**3. Query-independent signals compound; query-dependent signals do not.** Query-independent
work (link equity, site quality, HTTPS, mobile, CWV) pays across every query the page can
serve. Query-dependent work (relevance and intent matching for one term) pays on that term
only. **Prefer query-independent fixes when severity is equal**, because the return is
multiplied across the query set rather than confined to one.

**4. Freshness is query-conditional.** Only QDF queries reward recency. Mechanically
updating dates on evergreen content is wasted effort and introduces error. Never recommend
a refresh without establishing that the target query deserves freshness.

**5. Intent mismatch outranks keyword optimisation as a cause.** When a page underperforms
on terms it should win, intent mismatch is the more likely explanation than keyword density,
schema, or link volume. Check what the SERP is actually rewarding before proposing on-page
changes.

---

## Severity mapping

Stage 4 severity is capped relative to earlier stages, because nothing here blocks
visibility outright.

| Finding | Severity | Expected outcome tag |
|---|---|---|
| Money pages ranking below competitors on primary commercial queries with a diagnosed, addressable cause | High | **Ranking Lever** |
| Intent mismatch on revenue pages (page type wrong for what the SERP rewards) | High | **Ranking Lever** |
| Thin or non-competitive content on pages that could realistically win | High | Ranking Lever |
| Link profile gap against specific ranking competitors on specific queries | High | Ranking Lever, slow |
| Demotion or suppression signals present (spam, anchor mismatch, site-quality drag) | High | Risk Mitigation, or Ranking Lever if already suppressed |
| Titles, meta or headings weak on pages with impressions and poor CTR | Medium | Ranking Lever via click signals, indirect |
| Core Web Vitals below threshold on revenue templates | Medium | **UX (indirect ranking)** |
| Internal link distribution starving money pages of equity | Medium | Ranking Lever, and a stage 1 discovery input too |
| Schema absent where a SERP feature is realistically available | Medium | Ranking Lever for feature eligibility, not for position |
| Freshness stale on a **confirmed QDF** query | Medium | Ranking Lever |
| Missing H1 on pages already ranking for their targets | **Low** | Infrastructure Hygiene |
| Titles, meta or headings weak on pages with no impressions | **Low** | Not binding yet. Fix the reason there are no impressions first |
| Click-signal work on pages with no impressions | **Not a finding** | Cannot fire |
| Freshness on non-QDF evergreen content | **Not a finding** | Wasted effort |
| "Ranking factor" claims with no leak, testimony, patent or documentation grounding | **Not a finding** | See the myth list in the fundamentals reference |

**Nothing at stage 4 is Critical while a stage 1 to 3 blocker is open.** If a money page is
`noindex`, its title tag is not a Critical finding; the `noindex` is.

---

## Stage firewall

Frequently filed as ranking work when it belongs upstream:

| Topic | Actually belongs to |
|---|---|
| Two URLs competing for one query | **Stage 3.** Index selection, same mechanism as canonicalisation |
| Pages not appearing in search at all | **Stage 3**, or **Stage 2** if the raw HTML is hollow |
| "Content isn't ranking" where the page is not indexed | **Stage 3** first. There is no position to improve |
| Internal linking as a discovery mechanism | **Stage 1.** It is a stage 4 equity signal *as well*, genuinely dual |
| Crawl frequency and recrawl latency on updated content | **Stage 1** |
| AI crawler access and blocking | **Stage 1** |
| Render-only content invisible to LLMs | **Stage 2** |
| `max-image-preview` and other robots directives affecting Discover | **Stage 3** |

---

## Corpus assessment: nothing imported

An 11-source ranking corpus was reviewed for this file (10 extracted, 21,258 words: Moz's
search-engine-operation guide, Semrush, Conductor, Shopify, We Are Yard, PageOnePower, plus
four crawlability-focused pieces and one agency service page). **Nothing from it was
imported**, and the measurement is the reason:

| KB concept | Sources covering it |
|---|---|
| 2024 Content Warehouse leak | **0 / 10** |
| Antitrust trial testimony | **0 / 10** |
| NavBoost | **0 / 10** |
| Click attributes (`goodClicks` etc.) | **0 / 10** |
| Twiddlers / re-rankers | **0 / 10** |
| QDF | **0 / 10** |
| QDD / host crowding | **0 / 10** |
| `siteAuthority` / NSR | **0 / 10** |
| Query-dependent vs query-independent | **0 / 10** |

What the corpus does cover is generic and already held: backlinks 10/10, internal linking
8/10, content quality 6/10, intent 4/10, E-E-A-T 3/10, Core Web Vitals 2/10.

**The one finding worth recording.** 6 of 10 sources present the pipeline as
**crawl → index → rank**, and only 2 of 10 mention rendering at all. The mainstream ranking
literature systematically omits rendering as a stage. That is the measured origin of the
three-stage error, and it is why this KB states the four-stage order explicitly in every
stage file rather than assuming it. Anyone learning the pipeline from ranking-focused
content will arrive missing stage 2 entirely.

**Not read:** `konstructdigital.com` (403, and an agency service page rather than reference
material).

---

## The stage contract

1. **Never open stage 4 with a stage 1–3 blocker outstanding.** Document the blocker, state
   that ranking work is gated behind it, and stop.
2. **There is no "clean" verdict here.** Report relative position against named competitors
   on named queries, not a pass/fail.
3. **Every finding needs a diagnosed cause**, not an observed gap. "Ranking below competitor
   X" is an observation; the finding is why.
4. **Ground every ranking-factor claim** in the leak, testimony, patents, or Google
   documentation, per the evidence hierarchy. Ungrounded factor claims do not ship.
5. **Prefer query-independent fixes** at equal severity.
6. **Tag the outcome type**, and be honest that most stage 4 work is slower and harder to
   attribute than stage 1–3 work. Say so at audit time rather than defending it later.
