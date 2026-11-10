# SEO Fundamentals (2026)

> Reference document for the Technical SEO Agent and any auditor that produces SEO recommendations. Use this as the source of truth when reasoning about how Google actually works in 2026, what to recommend, and what NOT to recommend. This document focuses on durable principles — not tactics that change with each algorithm update.

## Core Principle

**No SEO change should worsen user experience. None. No exceptions.**

Every recommendation in every audit should be evaluated against this rule. If a fix would make the site worse to use — even if it might help rankings — it is not a valid recommendation. Google's algorithms are increasingly engineered to align ranking signals with user-experience quality. Working against UX to game rankings is fighting the direction of the system.

## How Search Engines Actually Work in 2026

### The Pipeline

**Four stages, in this order. State it this way, always.**

```
CRAWLABILITY → RENDERING → INDEXABILITY → RANKING
```

Every audit decision inherits this sequence, because a failure at any stage makes every stage downstream of it unreachable. No amount of ranking work rescues a page that cannot be indexed, and no indexing work rescues a page whose content only exists after a render that never happened.

Expanded, with the mechanism inside each stage:

```
Crawl → Initial HTML processing → Render-eligibility gate (raw-HTML directives)
   → Render Queue (if JS) → Web Rendering Service → Index → Ranking (with re-rankers)
```

**Naming discipline on the gate.** The render-eligibility gate is a checkpoint inside the crawl-to-render transition. It is NOT the Indexability stage. Earlier versions of this file called it the "indexability decision" and placed it before Rendering in the chain, which produced audit output that stated the stage order wrongly and read as not knowing the fundamentals. The gate decides whether a URL proceeds to the renderer. Indexability is the later stage that decides whether the rendered document enters the index. Two different things, and the four-stage order above is what gets stated first in any deliverable, prioritization framework, or client explanation.

Several things follow from this pipeline that shape every audit decision:

- **Render-eligibility is judged on raw HTML** before the renderer runs. JS-injected canonicals, robots directives, and status indicators may be skipped entirely, and if the raw response signals non-indexability the page never reaches the renderer at all. This is the December 2025 Google clarification: pages with non-200 status codes may not be rendered.
- **Rendering is queued, and budgeted on a virtual clock rather than wall-clock time.** The widely repeated "5-second render window" is a mistranslation: Martin Splitt's five seconds was the **median queue wait**, not a render timeout. The Web Rendering Service runs a virtual clock that it **pauses while network requests are in flight**, so network latency does not spend render budget. What spends it is JavaScript execution and parse cost. A separate real-time ceiling of roughly 52 seconds cancels outstanding requests. Practical consequence: never tell a client to speed up their server so Googlebot can "finish rendering in time" — target JS execution cost instead. Full mechanics, measurements and attribution in [javascript-seo-framework.md](javascript-seo-framework.md), section "The render budget, correctly stated".
- **Re-rankers ("Twiddlers") sit on top of the core algorithm.** They handle conditional re-ranking — local pack signals, freshness boosts, query-deserves-diversity adjustments. This is why a page can rank differently for two near-identical queries. (Enumerated with per-layer diagnostic questions in the Twiddler catalog below.)
- **AI crawlers do not render JavaScript at all.** ChatGPT, Claude, Perplexity, Bing's AI Overviews scrape raw HTML. Render-only content is invisible to AI search visibility.

### What Counts as a Ranking Signal

Distinguish three categories of signal:

1. **Query-independent signals** — properties of the page that don't change with the query. Examples: PageRank (link equity), domain authority (the real concept, not the Moz metric), HTTPS, mobile-friendliness, Core Web Vitals, content quality.
2. **Query-dependent signals** — relevance and intent matching for a specific query. Examples: lexical match, semantic relevance, freshness (only when the query deserves freshness), content type alignment with intent.
3. **User context signals** — location, device, search history, language. These cause ranking variability between users for the same query.

When auditing, separate query-independent fixes (which compound across all queries) from query-dependent fixes (which only help specific queries). Most "quick wins" are query-independent.

### Intent Matching Beats Keyword Matching

Modern Google heavily weighs intent matching. Pages that lexically match the query but don't satisfy the underlying intent will lose to pages that satisfy intent even with weaker keyword presence. When a page is ranking poorly for terms it should win, the most likely cause is intent mismatch — not keyword density, schema, or backlinks.

**Search intent shifts seasonally.** A query like "halloween costume" is informational in August (research) and commercial in October (purchase). Google re-ranks based on the dominant intent for the current moment. Pages built for the wrong seasonal intent underperform until the intent matches.

### Freshness Is Query-Dependent

Some queries demand freshness (news, current events, year-tagged terms, recurring annual events). Most queries don't. Pages should only be updated for "freshness" when the query genuinely demands it. Mechanically updating dates on evergreen content is wasted effort and can introduce errors.

This mechanism has a name inside Google's system: **QDF — Query Deserves Freshness** — a query-level determination of whether recent content should be boosted for that query. QDF is distinct from **QDD (Query Deserves Diversity)**, the host-crowding mechanism covered below. Freshness is applied as a re-ranker (a Twiddler), not a base-index property — which is why the same evergreen page can rank steadily on non-QDF queries yet lose ground on QDF ones the moment a fresher competitor publishes. The freshness a QDF query rewards is tied to genuine `lastSignificantUpdate` (see the per-document signals section), not the displayed byline date.

For seasonal terms ("best christmas gifts 2026"), keep the same URL each year, update the year in the title and content, and 301-redirect any year-suffixed URLs from prior years to the current canonical.

### Twiddlers: The Re-Ranker Catalog

The re-rankers referenced in the pipeline ("Twiddlers") sit on top of the core ranking score and adjust it conditionally — per query, per user, per moment. They are LEAK-DERIVED (documented as real mechanisms in the May 2024 Content Warehouse leak and corroborated by DOJ antitrust testimony) — not confirmed weightings you can dial. Treat them as re-ranking layers to diagnose against, not levers to pull. The catalog worth knowing for audits:

| Twiddler | What it does | Diagnostic question for the audit |
|---|---|---|
| Freshness boost (QDF) | Boosts recent content on queries that deserve freshness | Is this a QDF query, and is the page's `lastSignificantUpdate` recent enough to compete? |
| Click boost (NavBoost) | Re-ranks on ~13 months of `goodClicks` / `badClicks` / `lastLongestClicks` | Do the page's GSC click signals read as satisfaction, or is a competitor winning the last-longest click? |
| Host-crowding / diversity (QDD) | Caps how many results one host holds per query | Is the site already at its host cap for this query, so a second URL can't win a slot? |
| Official-page boost | Promotes the recognized official/home entity for a brand or entity query | For a branded/entity query, is the canonical official page the one Google can identify? |
| Local pack | Applies proximity + GBP signals for local-intent queries | Is the query local-intent, and are GBP / proximity / citation signals in place? |
| hostAge sandbox | Constrains fresh domains to filter launching spam | Is the domain new enough that host-age sandboxing is suppressing otherwise-rankable content? |

**Evidence note:** the leaked docs name only three twiddlers (`SiteBoostTwiddler`, `FreshnessTwiddler`, `WebImageBoostTwiddler`) and document `hostAge` as feeding a twiddler that sandboxes fresh spam at serving time. The click boost, host-crowding, official-page and local-pack rows above are not twiddlers named in the leaked docs; treat them as INFERRED unless a primary source is cited.

Because a Twiddler adjusts the score *after* base ranking, a page can carry strong base signals and still be re-ranked down — the audit job is to identify which layer is acting, not to assume the base score is wrong. For the itemized, signal-by-signal companion list, see `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md`.

### Host-Crowding and the Result-Diversity Cap (QDD)

Google limits how many results a single host can occupy on one SERP — the query-deserves-diversity (QDD) mechanism. Once a domain holds its allotted slots for a query, additional URLs from that domain generally cannot claim another position no matter how well-optimized, because the diversity cap — not relevance — is the binding constraint.

**Consequence for cannibalization and consolidation strategy:** when two of a site's URLs both rank for the same query, the ceiling on combined SERP real estate is usually one slot (occasionally two) regardless. Splitting intent across two pages does not double the site's share — it divides one capped allocation. This strengthens the consolidation case in the Cannibalization section below: merging two competing URLs into one stronger page concentrates signal into the slot the host is allowed to hold, rather than fragmenting it across pages that contest the same capped position.

**Consequence for realistic SERP-share expectations:** don't promise a client "we'll take positions 1, 2, and 3." Host-crowding makes multi-slot domination unrealistic for most queries. Set the expectation at one strong organic slot — plus, where applicable, a separate surface such as a featured snippet or a Map Pack entry, which are not subject to the same host cap — rather than wholesale SERP ownership.

## Indexing & Canonicalization

### The Three Tools and Their Roles

These three are commonly conflated. They control different things:

| Tool | What it controls | Where it lives |
|---|---|---|
| `robots.txt` | **Crawling** — whether the bot fetches the URL | Root file |
| `noindex` meta / X-Robots-Tag | **Indexing** — whether the URL appears in results | HTML `<head>` or HTTP header |
| `rel="canonical"` | **Consolidation** — which URL receives the ranking signal | HTML `<head>` |

Critical implications:

- **`robots.txt` does NOT prevent indexing.** Pages blocked by robots.txt can still be indexed if external links point to them. The result is an "indexed but not crawled" entry — Google has the URL but no content.
- **`noindex` in `robots.txt` no longer works.** Google ignores it. To prevent indexing, use the `noindex` meta tag or `X-Robots-Tag` header.
- **Canonical tags are hints, not directives.** Google routinely overrides them when the canonical target's content differs significantly from the source. Setting a canonical does not "solve" duplication unless the canonical target genuinely covers the source's content.
- **`noindex` declarations must be in the `<head>`.** Body placement is ignored.
- **Pages with `noindex` eventually have their links treated as `nofollow`.** Don't rely on noindexed pages for internal link equity flow.
- **Don't block CSS or JS files in `robots.txt`.** Google needs them to render the page accurately. Blocking renderer resources can cause layout-based failures and incorrect indexability decisions.

### URL Hygiene

URLs are case-sensitive. `/Page` and `/page` are different URLs. Stick to lowercase consistently.

`/page` and `/page/` (with vs without trailing slash) are different URLs. Pick one convention and 301-redirect the other.

`www.example.com` and `example.com` are different hostnames. Pick one and 301-redirect the other.

`http://` and `https://` are different. Always 301 from HTTP to HTTPS.

When any of these have multiple accessible variants, you have duplicate content. Choose canonical and redirect all alternatives.

### Sitemaps

XML sitemaps should contain only canonical, indexable URLs. Non-indexable entries (redirects, 404s, canonicalized URLs) send crawlers to dead ends and dilute the signal about what the site considers important.

**Two corrections to the common framing of sitemaps:**

- **A sitemap is a discovery mechanism and does not directly influence crawl budget or crawl demand.** Bad entries spend crawl activity on dead ends, which matters at a scale where crawl budget binds, but the sitemap itself is not a lever on how much Google crawls.
- **Unprocessed child sitemaps ("0 discovered URLs") are a symptom, not a defect.** The chain runs: rendering or quality problems make pages look empty → crawl demand falls → Google deprioritises sitemap processing. Resubmitting, splitting or restructuring the sitemap will not fix it. Fix the upstream cause and processing follows. Source: Barry Hunter, Google Search Central Community, Oct 2025; full detail in [stage-2-rendering.md](stage-2-rendering.md).

HTML sitemaps are unnecessary if the site is well-linked from a clear hierarchy. They're a UX patch for sites with weak internal linking.

Video sitemaps and product feeds are useful for surfacing content types that don't get crawled efficiently from on-page links alone.

### Hreflang

Hreflang signals the language and region of equivalent content. Rules:

- Declare hreflang in exactly one location: on-page tags, sitemap, OR HTTP headers — never multiple. Conflicting declarations cause issues.
- Use `x-default` on region/language selector pages for users who don't match any specific variant.
- Hreflang can work cross-domain (link `.co.uk` to `.com.au`).
- Subfolders (`mysite.com/en-gb/`) outperform subdomains or separate TLDs for most multi-region SEO use cases. The subfolder inherits domain authority; the subdomain or separate TLD has to build its own.

## Internal Linking

Internal linking is the most underused SEO lever. It does several things at once: signals page importance, distributes link equity, and helps search engines understand topical relationships.

### Principles

- **Anchor text matters.** A link with the target keyword in the anchor outperforms identical content that lacks descriptive anchor text.
- **Link position matters.** Links higher in the page (header, top of content) signal more importance than footer or sidebar links.
- **Click depth matters.** Pages closer to the homepage in click depth tend to be treated as more important. Pages buried 5+ clicks deep often underperform regardless of content quality.
- **Don't link through redirects.** When you change a URL, update internal links to point directly to the new URL. Don't rely on the redirect to do the work — it loses equity per hop.
- **Don't put critical pages behind JavaScript-only navigation.** Crawlers that don't render can't follow JS-injected links. AI crawlers in particular don't render at all.

### When to Use Nofollow on Internal Links

Mostly: don't. Internal nofollows are now treated as hints by Google, not as directives, but they still leak signal and create complexity. The historic use case (sculpting PageRank by nofollowing low-value internal pages) doesn't work the way it used to.

If a page truly shouldn't accumulate signal, the right answer is usually noindex (with the understanding that links from it eventually count as nofollow anyway), not internal nofollow.

### Orphan Pages

A page with zero internal links pointing to it is orphaned. It exists only via the sitemap or external discovery. Orphan pages typically rank poorly because they receive no internal link equity and signal low importance to Google.

When auditing orphans, exclude pages that have no SEO value to begin with: PPC landing pages, thank-you pages, application forms, terms of service, privacy policy, the 404 page itself. Orphan status on these is correct and shouldn't be flagged.

### High-Authority Pages Should Link Out

The homepage and other high-authority pages are not "special" — they accumulate link equity because external sites link to them. The way to use that authority is to link out to the pages that need ranking help. A homepage that doesn't link to category and service pages is leaving equity on the table.

### Source Internal Links From Pages That Earn Search Clicks (`onsiteProminence`)

The leak documents `onsiteProminence` — a measure of a page's importance within its own site, computed by propagating simulated traffic from the homepage and from pages with strong click signals. That gives internal linking a second axis: taxonomy ("what relates to what") is one axis, user flow is the other, and search clicks are the evidence for it. LEAK-DOCUMENTED: the attribute and its propagation description are in the files; the audit method below is the reading most consistent with them.

- **Choose source pages from the GSC clicks report, not from the sitemap or taxonomy alone.** The pages that earn the most search clicks are the strongest candidates on the click axis (wording changed 2026-11-10). Most sites waste them by linking out of template shells and archive pages no visitor reads.
- **Clicks, not sessions.** The documented signal propagates from click data, so build the source list from Search Console clicks. A page with heavy direct or social traffic but no search clicks is a different asset — on this reading it is not the one lending prominence.
- **Run links from broad-reach pages into narrow, conversion-adjacent pages** you are trying to move, and keep each anchor aligned with the target's topic (on the strictest reading, `anchorMismatchDemotion` reaches internal anchors too — see the anchor section).
- **On link-map deliverables, record the source page's GSC clicks next to each proposed link** so the map is sortable on the equity axis, and flag any proposed link whose source page earns zero search clicks — that row's equity case rests on taxonomy alone, and it should say so.
- **The homepage is a second starting point (added 2026-11-10).** The leak text reads: "It is computed by propagating simulated traffic from the homepage and high craps click pages" (`Skills/google-leak-reference/data/batches/batch_13.txt:81`). On this reading, pages close to the homepage in the internal link graph lend prominence too, so clicks are one axis, not the only one.
- **The click reading is untested (added 2026-11-10).** No public test shows that a source page's traffic changes what its internal links pass. The nearest evidence is Ahrefs' 2019 correlational study of external links, which found traffic to linking domains added virtually nothing over a plain count of linking domains; it applies to internal sources only by analogy (<https://ahrefs.com/blog/links-with-traffic-study/>, 2019-02-19, vendor research).
- **Automated check:** `internal_prominence_auditor.py` flags priority pages (average position 4 to 20, with impressions) that no page earning 10 or more search clicks links to, and lists candidate linking pages ranked by clicks. Navigation and footer links are excluded when the anchor export has link positions. Topic fit is judged by hand.

## Content Strategy

### Quality Over Quantity, Always

The web is short of quality, not quantity. Adding more content rarely produces ranking gains. Improving the content already on the site usually does.

A single pillar piece that genuinely answers a high-value query and earns links will outperform 52 weeks of 500-word blog posts. Content velocity is not a ranking factor. The myth that "Google rewards sites that publish frequently" comes from large publishers whose competitive advantage is depth and authority, not frequency.

### Word Count Is Not a Target

There is no word-count target that produces ranking gains. Word count correlates with ranking only because longer content tends to be more thorough — and thoroughness wins. Padding a page to hit a word count produces filler that hurts UX.

When recommending content expansion, identify the specific gaps: subtopics not addressed, questions left unanswered, comparisons missing, evidence absent. Recommend filling those gaps. Word count will follow as a side effect.

### Information Gain

Originality on its own is not enough; what matters is **information gain** — how much *new* value a page adds relative to what already **ranks** for the query, not whether the page is unique in isolation. Google holds patents describing an information-gain score that measures the incremental information a document provides beyond documents the user has already seen. The practical distinction: a page can be 100% original (nothing copied) and still add near-zero information gain, because it only restates what the top-ranking results already cover.

This sharpens the `OriginalContentScore` framing in the per-document signals section. `OriginalContentScore` (a LEAK-DERIVED attribute) evaluates a short page in isolation; information gain evaluates a page against the competitive set that already ranks. Audit implication: when a page satisfies intent but plateaus, don't recommend "add more words" or "make it more unique" — recommend adding something the ranking set lacks: primary data, first-hand testing, a comparison the incumbents skip, an updated figure, an expert quote. Information gain is the concept behind why the tenth "ultimate guide to X" fails to rank even when it is well-written and original — it carries no gain over the nine that precede it.

### Content Format Follows Idea

Decide what to communicate before deciding the format. The common anti-pattern is "we need an infographic" or "we need a video" before knowing what idea it should convey. The audit signal that matters is whether the page satisfies query intent — not whether it has a particular format.

### Cannibalization

When two or more URLs from the same domain target the same query intent, they split ranking signals between them. Neither ranks as well as a single consolidated page would. This is one of the most common and most underdiagnosed SEO problems. It compounds with the host-crowding cap (QDD) covered earlier: because Google limits how many results one host holds per query, two URLs competing for the same query aren't just splitting signal — they're contesting a single capped slot, so consolidation recovers share that fragmentation can never win back.

Detecting it:
- Multiple URLs ranking for the same query in GSC
- Ranking position volatility on key terms
- Site search (`site:domain.com intitle:"keyphrase"`) returning multiple matching pages

Resolving it:
1. **Consolidate** — merge content into the better page, 301 the weaker URL
2. **Differentiate** — if both pages should exist, rewrite each for distinct intent (e.g., transactional vs. informational)
3. **Canonicalize** — if pages must coexist with similar content (e.g., a hub and a deep-dive), canonical the deep-dive to the hub or vice versa, knowing canonicals are hints

The wrong answer is "do nothing" or "improve both pages independently." Cannibalization gets worse with more content effort, not better.

### Content Pruning

The instinct to delete content with no traffic is usually wrong. Mark's hierarchy is correct:

1. **Consolidate** — merge into another page that covers the same intent better
2. **Rewrite** — improve the content if the page still matters for its topic
3. **Reformat** — change the content type (text → video, single page → series) if format is the issue
4. **Redirect** — 301 to the most relevant live page if the content is genuinely obsolete
5. **Delete** — only if there's no relevant target and no signal worth preserving

Deletion should be the last option. Pages with even minimal backlink history are worth more as 301 sources than as 410s. Discontinued products in particular should be updated to "discontinued, see alternatives" with a link to the replacement, not deleted.

### Sale and Promotional Pages

When a sale ends, don't delete the URL. The sale page often accumulated links during the campaign. 301-redirect the sale URL to the relevant evergreen page (category, product, or homepage as appropriate) to preserve the equity. Keep the redirects in place indefinitely.

For recurring sales (Black Friday, Christmas), keep the same URL each year and update the content. Don't create `/black-friday-2025/`, `/black-friday-2026/` — that fragments link equity across yearly siblings.

## Site Migrations

Site migrations are where bad SEO decisions cause the most damage. The default approach should be cautious and minimal.

### Principles

- **Change as few things as possible.** Don't combine HTTPS migration, URL restructure, redesign, and replatforming into a single move. Each change introduces risk; combining them makes diagnosis impossible if rankings drop.
- **Don't change page titles during a migration.** Reduce variables. Optimize titles before or after the migration, not during.
- **Migrate in low-traffic periods.** If rankings drop temporarily, the absolute traffic impact is smaller, and you have more recovery time before a high-traffic season.
- **Don't migrate URLs that aren't in the internal link structure.** Hidden URLs (the ones SEMrush or Ahrefs found but you didn't link to) often hold rank-contributing backlinks. Migrating them without keeping the rank can drop the site materially.
- **Don't use the GSC URL Removal Tool during a migration.** It actively delays Google's re-crawl of the new URLs.
- **Keep redirects in place indefinitely.** Don't "clean up" redirect rules a year later. The links pointing to old URLs may still exist.
- **Calculate at-risk traffic using unbranded traffic only.** Branded traffic almost always survives a migration; unbranded is what's at risk and what should drive risk assessment.

### Pre-Launch Checklist

- All old URLs map to new URLs (1:1 where possible)
- 301 redirects in place at the edge level (Cloudflare or equivalent), not at the database/PHP level — for speed
- Internal links updated to new URLs (don't rely on redirects internally)
- Sitemap updated to new URLs
- Canonical tags updated
- Hreflang updated
- GSC properties added for the new domain/protocol
- Backup of pre-migration state for diagnostic comparison

## Local SEO

### Google Business Profile (GBP, formerly GMB)

- Choose categories carefully. Fewer specific categories outperform many general ones. Category is a primary ranking factor for the local pack.
- Don't add keywords to the business name. It violates GBP guidelines and risks suspension. (Exception: Google now permits service-specific qualifiers like "[Brand Name] Plumbing" if that's the actual registered business name, and "delivery available" / "takeout available" type modifiers.)
- Reviews matter. Specifically, reviews containing the target query terms boost visibility for those terms.
- Photos matter. 360-degree photos and recent, high-quality photos correlate with better local visibility.
- Don't list the main business address as a service page. Use service-area pages for territory coverage.

### NAP Consistency

Name, Address, Phone (NAP) consistency across the web is foundational for local SEO. Inconsistencies — abbreviations, formatting differences, old phone numbers on legacy directories — confuse Google's entity matching.

Audit citations regularly. Fix the highest-authority citations first (Google Business Profile, Apple Maps, Bing Places, Yelp, BBB, industry directories).

### Local Pack Ranking Factors

The local pack uses partially different ranking signals than the standard organic ranking. Factors with more weight in local:
- Proximity (where the searcher is)
- GBP completeness and signals
- Review quantity, recency, and content
- Citation consistency
- Local link signals (links from geographically proximate or topically relevant local sites)

Factors that matter less in local than in organic:
- Domain authority of the parent site
- Content depth on the local landing page (still matters, just less than for organic)

## Schema and Structured Data

### What Schema Does

Structured data doesn't directly improve rankings. It improves how the page is presented in SERPs (rich results, FAQ blocks, review stars, video carousels, etc.) — which improves CTR and visibility, which can produce indirect ranking benefits.

### Implementation Rules

- Use schema.org. The data-vocabulary.org standard is deprecated.
- Connect schema with `@id` rather than fragmenting it. An Article should reference its WebPage, Author, and Organization via `@id` so Google can build an entity graph.
- Self-referential canonical tags should be on every indexable page (prevents query-string scraping issues).
- Schema markup mistakes can trigger penalties (manual actions for misleading structured data). Follow Google's docs precisely.
- Product schema now appears in Google Images for ecommerce. This is a meaningful traffic source that's often overlooked.
- Review stars: Google killed in-search stars for first-party reviews on company-owned pages. Stars now require Google Business Profile reviews or third-party review platform schema.

### FAQ and How-To Schema

Both are supported and can produce rich results. Add them only when users would actually read FAQs or how-to steps on the page. Mechanical addition of FAQ schema to every page produces noise without value and can be flagged as spam.

## Site Speed and Core Web Vitals

### Real Data Beats Synthetic Data

PageSpeed Insights "lab data" varies between runs. The "field data" section (CrUX-derived real-user metrics) is the more meaningful signal because it reflects what actual users experience.

When auditing speed, use field data first. Lab data is for diagnostic deep-dives, not for tracking trends.

### Calibration: CWV Is Infrastructure Hygiene, Not a Ranking Lever

Daniel Foley Carter argues, from his own testing (DERIVED-FROM-TESTING, not leak-confirmed and not a Google-stated weighting), that a page's Core Web Vitals *score* carries close to no direct ranking benefit — his figure is "under 5%, effectively zero." Treat that number as his unverified tested opinion, not a measured weight. His actual claim is subtler: what moves ranking is not the Lighthouse number but the **behavioural consequence of genuine slowness**. A page slow enough that users abandon it before it renders loses the click signal (`badClicks`, forfeited `lastLongestClicks`) — and it is that behaviour, not the score, that feeds the ranking system.

This does NOT mean drop CWV from audits, and it does NOT mean lowering the score is worthless. It means **tag CWV correctly**. Under the project's Expected Outcome Classification (`Skills/seo-audit-methodology/SKILL.md`), a CWV fix on an already-indexed, already-rendering page is **Infrastructure Hygiene** or **UX (indirect ranking)** — never a **Ranking Lever**. Do not sell a client "pass CWV → rankings move." The honest promise is: faster pages get abandoned less, and less abandonment protects the click signals that do feed ranking (a slower, harder-to-attribute path).

The exception that genuinely IS a ranking lever is a different fix wearing a performance costume: render-blocking JavaScript that hides the H1 and primary content from the rendered DOM. That moves rankings because it unblocks previously-invisible content (see "What an Audit Is Worth" below), not because the CWV score improved. Keep the CWV checks (field data first, per above) — just don't overstate the score's direct effect, and don't drop the checks on the strength of DFC's "effectively zero" either. His figure is a tested read, not a confirmed fact.

### Mobile-First Indexing

Google indexes the mobile version of the site. If the mobile version has stripped-down content compared to desktop, the stripped-down version is what gets indexed. Content parity between mobile and desktop is non-negotiable.

Common failure modes:
- Mobile versions that hide content behind "Read More" without rendering it in the DOM
- Mobile versions with reduced navigation or fewer internal links
- Mobile versions with slimmed-down product/service descriptions

### HTTPS

HTTPS is foundational, not optional. Browsers mark HTTP pages as "Not Secure," which damages CTR and trust. Google has confirmed HTTPS as a ranking signal — modest direct effect, larger indirect effect via UX.

## Diagnostic Tools and What They Tell You

### GSC URL Inspection

The most accurate view of what Google has actually indexed for a given URL. Shows the rendered DOM, server response, screenshot, indexability status, and last-crawled date.

Use this — not the deprecated `cache:` operator — for debugging indexing issues.

### Site: Operator

`site:domain.com` gives a rough count of indexed URLs but is not authoritative. Numbers vary between runs and don't account for personalization. Use GSC's Coverage report for actual indexed counts.

### Server Log Analysis

Server logs show how Googlebot actually interacts with the site — what it crawls, how often, and what status codes it hits. This is invaluable for diagnosing crawl-budget problems on large sites and for catching bot-specific issues that synthetic crawls miss.

### Screaming Frog (or equivalent)

A full-site crawl is the foundation of most technical audits. Run it with JavaScript Rendering enabled to capture the rendered HTML and the response-vs-render comparison data.

Common gotchas:
- Web Application Firewalls and Cloudflare default to blocking crawler user-agents. Whitelist the crawler IP or rotate user-agents.
- Set a custom `X-Forwarded-For` header in Screaming Frog to bypass reverse-IP checks if needed.
- Enable "Render JavaScript" mode for any modern site.

## DMCA and Content Theft

If a scraper site copies your content and outranks you, file a DMCA notice. Upheld DMCA actions are a documented signal Google uses in ranking — sites with a history of accepted DMCA complaints against them get penalized.

Note: filing fake DMCA notices has legal consequences. Use it only for genuine copyright infringement.

## Featured Snippets and Position Zero

Featured snippets appear in roughly a quarter of SERPs. Owning the snippet does NOT remove the page from the standard #1 position anymore — Google changed this behavior. A page can hold both.

If a page is ranking #0 (snippet) but you'd prefer the standard #1 listing for higher CTR, add the `nosnippet` meta tag. Use the `&num=9` parameter on the SERP to preview where the page would rank without the snippet.

Featured snippet rankings are unstable and rotate frequently. Treat them as a bonus, not a permanent ranking.

**A site-level quality score gates feature eligibility.** Independent empirical work (Mark Williams-Cook's team, via a Google endpoint discovery reported through Google's Vulnerability Reward Program, December 2024) surfaced a per-site `site_quality_score` on a 0–1 scale: sites below roughly 0.4 did not receive People Also Ask or featured-snippet eligibility, and the observed inputs relate to branded anchor counts and branded search demand. This is not from the leak files — grade it as independent empirical from a single research team. Diagnostic use: a site with zero snippet/PAA presence across its whole query set despite competitive positions may sit under the quality gate, and the lever consistent with the observed inputs is brand demand and site quality, not snippet formatting.

## What Google Doesn't Use as a Ranking Signal

Stating these explicitly because they keep coming up in client conversations and consultant reports:

- **Analytics-style bounce rate** (the Google Analytics metric specifically) is not a ranking factor. Google does not pull GA data into the ranking algorithm. This is distinct from in-SERP click signals — see the next section.
- **Social signals** (Facebook likes, Twitter shares, LinkedIn engagement) are not ranking factors. Social can drive earned links — those links are the SEO signal, not the share count.
- **Domain Authority (the Moz metric)** is not a Google ranking factor. The underlying concept of domain-level authority is real; the Moz score is an external estimate.
- **Paying for Google Ads** does not boost organic rankings.
- **Meta keywords tag** has been ignored since approximately 2009.
- **TF-IDF and LSI keywords** as targets a writer can optimize for. LSI is not what Google uses. TF-IDF is real but not actionable in the way "use these LSI keywords" advice implies.
- **Keyword density** as a target ratio. There is no correct density.

## What Google DOES Use That's Often Misunderstood

Several signals get incorrectly dismissed as "Google doesn't use that." This section documents what's actually confirmed by primary sources (the May 2024 Google API leak, US v. Google antitrust testimony, Google patents), with the critical distinction that these are **outcomes you earn, not levers you can pull directly**.

### In-SERP click signals are real ranking inputs

Per DOJ antitrust testimony, Google operates a system called **NavBoost** that memorizes ~13 months of user click data and uses it to re-rank results. The 13-month window comes from that testimony: no attribute in the leaked documentation states it. The leaked schema lists the click attributes below as fields, and `goodClicks`, `badClicks` and `lastLongestClicks` carry no description there, so the meanings given are inferred from the field names (INFERRED):

- `goodClicks` — long clicks where the user stayed on the destination page rather than returning to the SERP
- `badClicks` — short clicks where the user bounced back to the SERP quickly
- `lastLongestClicks` — the click that ended the user's search session for that query (the "satisfying" result)
- `impressions` — how often a URL appears in results (not all SERP appearances are equal — Google "tests" URLs in different positions)

A second system called **Glue** uses click data to assemble and re-rank the SERP. **RankEmbedBERT** (and its successor used to ground AI Overview / AI Mode answers) trains on ~70 days of search log data plus human-rater scores.

**This is NOT the same as "optimize for dwell time" or "boost your CTR."** Google explicitly notes that click signals are noisy, gets squashed and weighted by query/position/device/location/user-type, and operates on a 13-month rolling window. You can't game it with click farms (the data is too noisy and the windows too long), and you can't optimize "dwell time" as a tactical lever the way a writer optimizes a heading.

What you CAN do is earn good click signals as a side effect of:

1. **Earning the click** — accurate, intent-matching SERP snippet (no clickbait, since the system specifically penalizes mismatched titles vs content)
2. **Proving usefulness** — page actually helps the user complete the task they searched for (this is what produces `goodClicks`)
3. **Proving satisfaction** — page resolves the user's question fully so they don't need to search again (this is what produces `lastLongestClicks`)

The ABC framing some Google engineers use internally: **A**nchors (links), **B**ody (content), **C**licks (user behavior) as the three durable ranking inputs. None of the three are tactical levers — all three are outcomes of doing other things well.

**Practical implication for audit recommendations:**

- Don't recommend "improve dwell time" or "reduce bounce rate" as standalone tactics — those aren't actionable.
- DO recommend the underlying causes that produce good click signals: snippet accuracy, intent matching, content depth, answering follow-up questions, providing evidence and next steps.
- Don't promise a specific "click-signal lift" timeline — NavBoost has a 13-month memory window. Changes propagate over weeks to months, not days.
- Don't recommend CTR-manipulation tactics (click farms, bot clicks). The signal is noisy, squashed, and contextual — manipulation is detectable and short-lived.

**Calibration — engagement is proportional to the query, not absolute.** Daniel Foley Carter's framing (DERIVED-FROM-TESTING): there is no universal "good dwell time." Engagement must be judged against the behaviour the query *expects*. 44 seconds on a page is a bad signal for a "how to reroute a bathroom vent" how-to (the user needed far longer to complete the task) but a perfect signal for "what temperature to bake chicken" (the user got the fact and left — a short visit IS the satisfying `lastLongestClick`). A short click is only a `badClick` when the query expected a longer engagement. This is the mechanism-level reason "reduce bounce rate" / "increase dwell time" fail as universal tactics (consistent with the NavBoost caveat above): the target behaviour is query-dependent, so there is no site-wide number to optimise toward.

His stronger claim is his tested opinion, not leak-confirmed: aggregated poor engagement across a site — many pages consistently failing to deliver the engagement their queries expect — drives *site-wide* demotion, which he attributes to the Helpful Content Update (HCU). Treat the site-wide-demotion attribution as DFC's read. It is corroborated *in direction* by the leak's real signals (`serpDemotion` applied per page; NSR / `lowQuality` at the site level) but the specific HCU mechanism is not confirmed.

**Audit implication:** When judging whether a page's GSC click signals read as satisfaction — the SERP-demotion diagnostic in the demotion checklist below — calibrate against the query's expected engagement. Don't flag a short dwell on a quick-fact query as dissatisfaction, and don't excuse a short dwell on a task-completion query as fine. The same short number means opposite things depending on what the query asked for.

### Sitewide quality and authority signals are real

The May 2024 Google API leak documented a module called `QualityNsrNsrData` ("Neural Site Rank") that confirms Google maintains site-level quality and authority scores — distinct from per-page signals. The clearest framework-impact findings:

**Sitewide authority is measured.** Attributes like `nsr` (Neural Site Rank), `priorAdjustedNsr`, `siteAutopilotScore`, and `tofu` (a content-based site quality predictor) confirm that Google computes a score for the site as a whole that gets applied to all pages on it. This validates the long-standing intuition that "low-authority sites struggle to rank even with great individual pages" — there's a measurable site-level signal feeding that.

**Practical implication:** Don't treat each page as if it ranks on its own. A page on a high-NSR site has a tailwind; a page on a low-NSR site has a headwind. Improving sitewide quality (removing thin pages, fixing template duplication, building topical depth across the site, accumulating quality backlinks) lifts every page on the domain.

**Chrome browsing data feeds rankings.** The `chromeInTotal` attribute records "Site-level Chrome views." This contradicts John Mueller's prior public denial that Chrome data influences rankings. Sites that get heavy Chrome traffic (people typing the URL directly, navigating from bookmarks, clicking links in non-Google sources) accumulate a sitewide signal Google uses.

**Practical implication:** Brand traffic and direct navigation aren't just nice-to-have — they feed a measurable signal. This reinforces brand-building as an SEO investment, not just a marketing one.

**Sitewide "clutter" is a documented demotion.** The `clutterScore` attribute is described as "delta site-level signal in `Q*` penalizing sites with a large number of distracting/annoying resources loaded by the site." Translation: sites with too many third-party scripts, intrusive ads, popup overlays, and other distracting elements get sitewide demotion in the `Q*` ranking system.

**Practical implication:** When a site has aggressive ad density, multiple chat widgets, excessive popups, or heavy third-party tag stacks, this isn't just a UX problem — it's a measurable Google signal. Audit recommendations to reduce intrusive elements have a real ranking justification, not just a CRO one.

**AI-generated content is detected at the site level.** The `racterScores` attribute is described as "Site-level AGC classification score" (AGC = AI-Generated Content). This confirms Google has site-level AI-content classifiers. A site that's predominantly AI-generated gets flagged — even pages that LOOK well-written individually inherit the site-level classification.

**Practical implication:** When a client has been publishing AI-written content at scale, the risk isn't that one post gets flagged — it's that the cumulative classification taints the whole site. Mixing AI content with substantial human-edited content, fact-checking, and original research helps avoid the site-level flag.

**Small personal sites get an explicit promotion.** The `smallPersonalSite` attribute is described as "Score of small personal site promotion." Google explicitly boosts small, personal/independent sites.

**Practical implication:** The "you need backlinks and authority to rank" framing is incomplete. Small genuine sites with focused content can rank without traditional authority signals — Google has an explicit promotion for them. Don't dismiss client recommendations as impossible just because the client lacks traditional authority.

**Site type classification affects how signals are weighted.** Attributes like `isVideoFocusedSite` (>50% video URLs), `isCovidLocalAuthority`, `isElectionAuthority` confirm Google classifies sites by type/topic and applies different signal weights based on the classification. A primarily-video site is ranked differently from a primarily-text site for the same query.

**NSR fallback for new sites.** The `nsrdataFromFallbackPatternKey` attribute, when true, indicates "we do not have NSR data computed for the chunk, and instead the data is coming from an average of other host chunks." Translation: new or small sites without enough data inherit averaged scores from similar sites until they have enough usage to compute their own. This is a quasi-sandbox at the NSR level — new sites can't fully benefit from NSR signals until they accumulate enough independent data.

**Practical implication:** Setting client expectations on new domains. Even with great content and backlinks, a brand-new domain can't fully express its NSR-driven ranking potential for some period of time until Google has independent NSR data. This reinforces that domain age and trust accumulation are real constraints.

**Quality is measured as a distribution, not just an average.** The `siteQualityStddev` attribute is LEAK-DERIVED and captures the *variance* of quality across a domain's URLs. A site with uniformly solid pages reads differently from one with a handful of strong pages sitting on top of a large junk tail — even at a similar average. High variance (a few good pages, many weak ones) is itself a signal.

**Practical implication:** The junk tail is not neutral. Thin, abandoned, auto-generated, or near-duplicate pages don't merely fail to help — they widen the site's quality variance and can drag the site-level read down. This is a second, independent mechanism (alongside topical drift and the index-tier system) behind the content-pruning and consolidation recommendations: trimming the weak tail tightens the distribution, not only the average.

**Human-rater "gold" flags exist at the document level.** The leak references gold-standard / "golden document" rater signals — pages that human quality raters (or curated processes) have marked as exemplary for a query or topic. These are LEAK-DERIVED and function as calibration/training signals rather than a dial an SEO can set, but they confirm that human-rater judgments attach to specific documents and feed the quality models.

**Practical implication:** You can't request a gold flag, but you can build the page a rater would mark as one — the clearest-answer, most-complete, most-trustworthy result for the query. Optimizing toward "what a trained rater would call the best result for this query" is the durable move; the public Quality Rater Guidelines are the closest proxy for what those raters look for.

**Media quality is scored at the site level too.** Alongside the site-type classifiers, the leak documents media-specific site-quality scores — LEAK-DERIVED attributes along the lines of a `videoScore`, an image-quality signal tied to click behaviour (`imageQualityClickSignals`), and a `shoppingScore` for commercial sites. Google evaluates not just text quality but the quality of a site's video, image, and shopping content as its own inputs.

**Practical implication:** For video-heavy, image-heavy, or ecommerce sites, media quality is part of the site-level quality read, not a side concern. Recommend genuine investment in original, high-quality media (real product photography, useful video, well-structured shopping data) over stock filler — it feeds a measured signal for those site types.

**NSR is versioned and has a predicted baseline.** Beyond the `nsr` score itself, the leak documents that Neural Site Rank is tracked over versions (a trajectory, not a single snapshot) and carries a `predictedDefaultNsr` — a baseline the system expects for the site before newer data adjusts it. Combined with `priorAdjustedNsr`, this shows Google reasoning about where a site's quality is heading, not only where it is now. These are LEAK-DERIVED.

**Practical implication:** Direction matters, not just current state. A site on an improving quality trajectory is modeled differently from one that spiked and decayed. This rewards sustained, consistent quality work over one-time cleanups — it is the site-level counterpart to the per-document version history below.

### Site behaviour over time (a temporal signal single-snapshot audits miss)

Several of the LEAK-DERIVED signals above are explicitly *temporal* — `hostAge`, the versioned NSR trajectory, `lastSignificantUpdate`, and the anchor-spam velocity windows (`phraseAnchorSpamDays` / `phraseAnchorSpamRate`, covered in the anchor-links section) all measure change over time rather than a single state. Taken together they imply Google watches a site's behaviour as a time series. Three patterns are worth naming as a unified signal:

- **Content-production spikes** — a site that suddenly publishes hundreds of pages in a short window (mass programmatic launch, AI-content dump) looks different from steady publishing. Sudden inflow, especially of low-`contentEffort` pages, is the pattern the 2024 scaled-content-abuse policy targets.
- **URL-inflow surges** — rapid growth in the count of indexable URLs (faceted-nav explosions, parameter sprawl, thin auto-generated pages) is a temporal crawl/quality signal, not just a static crawl-budget issue.
- **Link-inflow consistency** — natural backlink profiles accumulate gradually with diverse anchors; spikes of similar anchors over a short window trigger the anchor-spam velocity flags. Consistency over time reads as legitimate; spikes read as manipulation regardless of intent.

**Audit implication:** A single crawl is a snapshot and is structurally blind to all of this. When a ranking change doesn't correlate with any on-page state in the current crawl, suspect a temporal cause and flag it as **needing a two-crawl comparison** (or a GSC / backlink-tool time series): compare page counts, URL inflow, publish cadence, and anchor accumulation between two dates. The trajectory, not the snapshot, is often the story.

### Per-document signals: what Google captures per page

The leaked `PerDocData` module documents the per-page signal container. Several attributes there are framework-impactful in their own right.

**The Google sandbox is real.** The `hostAge` attribute is described as: "The earliest firstseen date of all pages in this host/domain. These data are used in twiddler to sandbox fresh spam in serving time." This directly contradicts John Mueller's prior public denial that the Google sandbox exists. Fresh domains face an algorithmic constraint based on host age — particularly to filter out spam launching new domains.

**Practical implication:** A brand-new domain can't expect to rank competitively for ~6-12 months even with strong content and links. This isn't agency hand-waving — it's documented sandbox behavior at the host-age level. Set client expectations on new domains accordingly. Don't recommend aggressive ranking timelines for newly registered sites.

**Original content scoring is binary.** The `OriginalContentScore` attribute (7-bit, 0-127) is described as "Only pages with little content have this field." Google specifically scores short pages for originality. Short pages without originality (templated thin content, AI-generated boilerplate, scraped excerpts) get demoted; short pages WITH originality (a focused tip, a specific tool description, a curated resource) can still rank well.

**Practical implication:** Don't pad short pages with filler to hit a word-count target. Either keep them short and original, or expand them with genuinely substantive content. Padding hits the worst of both worlds — long enough to dilute focus, but with low original-content density.

**Effort is scored, and it is not the same as originality.** The `contentEffort` attribute is LEAK-DERIVED and described as an LLM-based estimate of the effort invested in producing a page — roughly, the work a human would have to expend to create it. It is distinct from `OriginalContentScore`: a page can be original (nothing copied) yet low-effort (a thin, templated, auto-assembled listing), and `contentEffort` is what separates the two. Mass-produced pages built from an identical skeleton with only a variable swapped — spun location pages, doorway pages, programmatic pages with no unique substance — are exactly what a low-effort estimate targets.

**Practical implication:** Templated page programs (location pages, programmatic SEO at scale) are the highest-risk pattern here. If every page in a set is the same skeleton with the city name or product attribute swapped, a low-`contentEffort` read is the likely outcome. Recommend genuine per-page substance — local specifics, unique data, real photos, distinct copy — not city-name-swapped boilerplate. This is the leak-grounded mechanism behind the long-standing "don't ship doorway pages" advice, and it connects to the 2024 scaled-content-abuse policy noted in the demotion section below.

**Term weight is visual, not just textual.** The `avgTermWeight` attribute is LEAK-DERIVED and reflects that Google weights a term's on-page relevance partly by its visual prominence — emphasis (bold/strong), font size, and heading weight all raise a term's contribution to what the page is "about." A keyword in the H1 and a prominent intro carries more relevance weight than the same keyword buried in body text or a footer. Because this is measured on the rendered page, it belongs to the rendering/relevance layer, not the raw-HTML pass.

**Practical implication:** Heading hierarchy and emphasis are relevance signals, not just readability aids. When a page targets a term, that term (or a close variant) should appear in the H1 and be visually prominent early — genuinely present where the page's structure signals importance, not stuffed. Conversely, a page whose visually prominent terms don't match its target query is sending a relevance signal at odds with its intent. Don't over-apply this into keyword-stuffed headings; the point is alignment between visual prominence and the page's actual topic.

**YMYL is a measured classifier.** `ymylHealthScore` and `ymylNewsScore` are described as "Stores scores of ymyl [health/news] classifier as defined at go/ymyl-classifier-dd." YMYL (Your Money Your Life) isn't just a Quality Rater Guidelines concept — it's a measured classifier signal that affects how content gets ranked.

**Practical implication:** Health, finance, news, legal, and safety content gets routed through additional quality classifiers. E-E-A-T signals (named author, citations, expertise indicators) carry more weight on YMYL content than on other content. Recommend higher author/expertise investment for clients in these verticals.

**Knowledge-Based Trust (KBT): cite to authoritative sources on "best / top / YMYL" content.** Google holds a Knowledge-Based Trust patent describing a model that scores a page's trustworthiness by the *factual accuracy* of its claims — checked against what authoritative sources agree on — rather than by links. Daniel Foley Carter operationalises this (DERIVED-FROM-TESTING) for "best X," "top X," ranking/recommendation, and YMYL content: every factual claim should be cited, and the picks themselves should have **cross-source reinforcement** — the entities named as "best" should be corroborated by independent authoritative sources, not asserted in isolation. A "best plumbers in Denver" page whose picks are corroborated across directories, reviews, and industry bodies reads as more trustworthy than one asserting picks with no external agreement.

**Audit implication:** On best/top/recommendation/YMYL pages, flag uncited factual claims and picks that no authoritative source corroborates. The fix is cross-source reinforcement — cite every factual claim to a primary/authoritative source, and choose picks that independent sources agree on. This sits beneath `unauthoritativeScore` and the YMYL classifiers above: KBT is the "are the claims actually true and corroborated" layer under the "does the page display expertise indicators" layer. Treat KBT itself as a patent-documented model, not a confirmed live ranking dial; the citation discipline it implies is durable regardless.

**Google extracts dates from three independent sources.** The `semanticDate` attribute extracts dates from "contents of the document" — distinct from `bylineDate` (snippet/byline date) and `syntacticDate` (date from URL or title). Google then cross-checks these. Inconsistency across the three signals causes confidence loss.

**Practical implication:** When a page has a published date in the byline (e.g., "March 2024"), the URL slug (e.g., `/2024/03/article-title/`), and the body content (e.g., "in our 2026 update"), these need to align. Mismatches confuse Google's freshness signal — recommend updating ALL three sources together when refreshing content.

The leaked `QualityTimebasedDateUnreliability` signal goes further: when the three date sources disagree significantly, Google flags the date as **unreliable** rather than picking one. An unreliable date signal hurts ranking on any query where freshness matters. This means the WORST outcome isn't "Google picks the wrong date" — it's "Google picks neither and treats the page as date-unreliable."

**Audit checklist for date alignment:** When auditing freshness for a page that should rank on time-sensitive queries:

1. Check the byline date in the rendered page (visible to users)
2. Check the URL slug for any embedded date
3. Check the body content for year references and dated claims
4. Check the article-published structured data (`datePublished` and `dateModified`)
5. Check the XML sitemap `<lastmod>` value
6. Check the HTTP `Last-Modified` header

All six should align. Sites that update content but only refresh some of these sources accumulate `dateUnreliabilityInfo` flags that hurt ranking on freshness-sensitive queries.

**"Significant updates" are tracked separately.** The `lastSignificantUpdate` attribute is distinct from publish/modified date. Google distinguishes between trivial edits (changing the date, fixing a typo, swapping an image) and substantive ones (rewriting sections, adding new information, restructuring content).

**Practical implication:** Don't recommend "just update the date" as a freshness tactic. Google's freshness signal is driven by `lastSignificantUpdate`, not the publish date displayed to users. Genuine content updates trigger the signal; metadata-only updates don't. This is the underlying mechanism behind the long-standing observation that "republishing with a new date doesn't help unless you actually update the content."

**Google keeps a limited change history per URL.** The leaked `CompositeDocIndexingInfo.urlHistory` field is documented as the URL change history for a document, and "if a doc has more than 20 changes, we only keep the last 20 changes". That much is LEAK-DERIVED. The docs do not say whether full prior page versions are stored. `lastSignificantUpdate` is documented as computed by an `LSUSelector` from various signals, and as derived from a shingle-based `ContentAge` signal, which points to content comparison across crawls (INFERRED): the system appears able to tell a substantive rewrite from a cosmetic touch.

**Practical implication:** You cannot fake a page's history by editing it once. A page that was thin for years and gets a single overhaul still carries that trajectory; sustained improvement reads differently from a one-time refresh. It also means an abrupt wholesale content swap on an established URL (repurposing a ranking page for an unrelated topic) is visible as a discontinuity, not a clean slate — prefer a new URL when the topic genuinely changes rather than overwriting a page's accumulated history.

**Multi-layered spam scoring.** Three separate spam attributes exist:

- `spambrainTotalDocSpamScore` (0-1, ML-driven SpamBrain score)
- `DocLevelSpamScore` (7-bit, 0-127)
- `spamrank` (0-65535, "the likelihood that this document links to known spammers")

The third one is the most actionable: outbound links to known spam sites are measured per-document. Linking to spammy sites — including in comments, user-submitted content, or footer sponsor sections — accumulates spam signal on YOUR pages.

**Practical implication:** Audit recommendations on link hygiene matter. Sites with comment sections, forums, or user-generated content that allow unmoderated linking are accumulating measurable `spamrank`. Recommend nofollow on user-submitted links, comment moderation, and audits of footer/sidebar sponsor links.

**The index tier system is documented.** The `scaledSelectionTierRank` attribute (0-32767, normalized over the serving tier) confirms Google's tiered index. Top-tier pages (served from SSD) get crawled more often, surface more often, and have stronger ranking influence. Lower-tier pages (served from disk-based TeraGoogle) are slower to be reached, less likely to be considered for ranking, and pass less link equity.

**Practical implication:** When a site has a long tail of thin/old/low-traffic pages, those pages are likely in lower index tiers — and any links from them carry less equity than the same links from top-tier pages would. Consolidating thin pages into stronger ones (the existing content-pruning recommendation) has a real index-tier mechanism behind it: fewer pages, but more of them in the top tier.

**Author entities are captured per document.** The `authorObfuscatedGaiaStr` attribute confirms Google captures author profile identifiers (Gaia is Google's internal identity system) per page. This validates that "author" isn't just an E-E-A-T concept — it's a real entity Google tracks.

**Practical implication:** Adding visible author bylines, author bio pages, structured data Author markup, and consistent author attribution across the site materially helps for E-E-A-T signal accumulation. The author entity is captured even when client doesn't think to optimize for it — but explicit author markup makes it more reliable.

### Documented demotion factors

The leaked `CompressedQualitySignals` module documents the named demotion factors Google applies. This is one of the most actionable parts of the leak because demotions are diagnostic — when a site is underperforming, knowing which specific demotions are documented gives an audit checklist for what to investigate.

**The Q* ranking system applies these demotions:**

**1. Panda demotion** (`pandaDemotion`, `babyPandaDemotion`, `babyPandaV2Demotion`)

The classic Panda quality demotion is real and documented. The leak shows three layers: original `pandaDemotion`, `babyPandaDemotion` (described as "converted from QualityBoost.rendered.boost"), and `babyPandaV2Demotion` ("applied on top of Panda. Meant to replace babyPandaDemotion"). Multiple demotion layers can stack on the same page.

**Audit implication:** A site struggling to rank despite good individual page quality may be carrying site-level Panda demotion. Diagnostic check: are there many thin pages, low-effort templated pages, or near-duplicate pages dragging down the site-level quality score? Recommend pruning, consolidation, and template-deduplication.

**2. Anchor mismatch demotion** (`anchorMismatchDemotion`)

Described as "converted from QualityBoost.mismatched.boost." When a link's anchor text doesn't match the destination page's actual topic, the link gets demoted. This is bilateral — relevance is required on both sides of the link.

**Audit implication:** Links with mismatched anchor text don't pass equity. When auditing internal linking, recommend descriptive anchor text that matches the destination page's topic. When auditing inbound links, links from off-topic sites pass less than they appear to. This also explains why generic "click here" anchors fail — anchor text mismatch.

**3. SERP demotion** (`serpDemotion`)

Described as "applied in Qstar." Demotion based on observed user dissatisfaction signals from the SERP itself — almost certainly tied to the click-signal feedback discussed earlier (high `badClicks`, low `lastLongestClicks`, users returning to SERP and clicking competitors).

**Audit implication:** This is the click-signal feedback loop applied as a demotion. A page that consistently fails to satisfy users for the queries it ranks on accumulates SERP demotion. Recommend the click-signal-earning workflow (intent matching, content depth, satisfaction) for affected pages.

**4. Nav demotion** (`navDemotion`)

Described as "converted from QualityBoost.nav_demoted.boost." Demotion for poor navigation and user experience — confusing site structure, broken navigation, hostile UX patterns.

**Audit implication:** Audit recommendations on navigation clarity, breadcrumb implementation, and site architecture have a measurable Google signal behind them, not just UX justification. Sites with confusing nav (overly nested menus, dead-end pages, missing breadcrumbs) may be carrying nav demotion.

**5. Exact-match domain demotion** (`exactMatchDomainDemotion`)

Described as "converted from QualityBoost.emd.boost." The classic 2012 EMD update is still a documented signal. Sites whose domain is just an exact-match keyword (e.g., `bestplumbingsanjose.com`) get demoted vs. branded domains.

**Audit implication:** Don't recommend exact-match-domain registration as an SEO tactic. Clients with exact-match domains face a documented headwind that brand investment can partially offset (brand searches, branded backlinks, etc.) but never fully eliminate.

**Calibration — the demotion is conditional, not automatic.** Daniel Foley Carter reports (DERIVED-FROM-TESTING) owning an exact-match domain that has held #1 for its head term for over a decade. His read: `exactMatchDomainDemotion` is real — the leak confirms the attribute — but it is *conditional*, not an automatic cap. A strong user-signal profile (branded search demand, `goodClicks` / `lastLongestClicks`, genuine accumulated authority) can offset it. Audit framing: treat an EMD as a documented headwind to *note*, not a verdict to *pronounce*. Before telling a client their EMD is holding them back, verify the user-signal profile first — an established, well-signalled EMD may be carrying no net demotion at all. The tactic advice is unchanged: don't register a *fresh* EMD, which carries the headwind without the accumulated signals that offset it.

**6. Product review demotions** (`productReviewPDemotePage`, `productReviewPDemoteSite`, with corresponding `productReviewPPromotePage`, `productReviewPPromoteSite`)

The 2023 Product Reviews Update created explicit per-page and per-site demotions/promotions for product review content. Pages get classified as review pages (`productReviewPReviewPage`), and high-quality review pages get scored separately (`productReviewPUhqPage` = "high quality review page").

**Audit implication:** For clients in affiliate or product-review verticals, the Product Reviews quality bar is a hard one. Recommend deep first-hand product testing, original photos, comparison data, and substantive recommendation rationale — not the templated "best [X] of 2026" content that triggers the demotion.

**7. Low-quality demotion** (`lowQuality`)

Described as "S2V low quality score: converted from quality_nsr.NsrData, applied in Qstar." A general low-quality flag derived from the Neural Site Rank module discussed earlier. The leak also distinguishes a harsher **VLQ (very low quality)** band from ordinary `lowQuality`: VLQ is the bottom tier applied to the weakest pages (near-empty, auto-generated, no original value), while `lowQuality` covers a broader mediocre range. They are not the same threshold — a page can clear VLQ and still carry `lowQuality`.

**Audit implication:** Pages with low NSR-derived quality get demoted in Q*. The fix is upstream: improve site-level NSR signals (depth, originality, link quality, click signals) — not just the affected page. Pages in the VLQ band are pruning/consolidation candidates first — they contribute nothing and widen the site's quality variance (`siteQualityStddev`) discussed earlier.

**8. Scam demotion** (`scamness`)

Described as "Scam model score. Used as one of the web page quality qstar signals. Value range from 0 to 1023." Pages classified as scams get demoted.

**Audit implication:** Sites with patterns Google's scam classifier picks up on (deceptive claims, fake urgency, sketchy testimonials, hidden costs) carry measurable demotion. Recommend transparent pricing, real testimonials with verifiable sources, clear refund policies, and honest claims.

**9. Unauthoritative score** (`unauthoritativeScore`)

"Unauthoritative score. Used as one of the web page quality qstar signals." A counter-signal to authority — pages that appear unauthoritative (no author credentials, no citations, no expertise indicators on YMYL topics) get demoted.

**Audit implication:** Especially relevant for YMYL content. Recommend visible author credentials, citations to primary sources, and explicit expertise indicators (qualifications, professional affiliations, original research).

**10. Location / localness** (`localityScore`; no `locationDemotion` attribute exists)

The leaked `QualityNsrNsrData.localityScore` is documented as the "locality component of the LocalAuthority signal" at site level. No attribute documents a location demotion, so the idea that a generic or national page is demoted on locally-intended queries is INFERRED from that signal. It still matters to local-service clients: a broad "national" page competing on a query the user meant locally likely faces a headwind relative to pages carrying real local signals.

**Audit implication:** For local-service businesses, a single generic service page trying to rank everywhere is fighting a localness headwind on locally-intended queries. This is the demotion-side counterpart to the Local SEO guidance above — recommend genuinely local pages (real service-area specifics, local proof, NAP-consistent signals) rather than one location-agnostic page, and don't expect a national page to hold locally-intended queries.

### Demotions vs. Promotions: how to think about them

The same module also documents **promotions**:

- `authorityPromotion` — "converted from QualityBoost.authority.boost"
- `productReviewPPromotePage`, `productReviewPPromoteSite` — counter-signals to the demotion variants
- `siteAuthority` — sitewide authority signal already discussed

The framework here: Google applies BOTH demotions (penalties) AND promotions (boosts) on top of base ranking. Sites accumulate both kinds of signals simultaneously. The net effect is the sum.

**Practical implication for audits:**

When recommending fixes, separate the "stop the bleeding" work (reducing demotions) from the "build advantages" work (earning promotions). Sites with severe demotion signals — Panda, scamness, unauthoritative — need the demotion work first; promotion work is wasted effort while a demotion is dragging the site down. Sites with clean demotion profiles can focus on accumulating promotions: earning authority signals, building product review quality, accumulating positive click signals.

**The demotion checklist for audit findings:**

| Demotion | Diagnostic question for the audit |
|---|---|
| Panda / babyPanda | Is there a long tail of thin or templated pages? |
| Anchor mismatch | Are internal anchors descriptive and topic-aligned? |
| SERP demotion | Are the page's GSC click signals (CTR, position-adjusted) consistent with user satisfaction? |
| Nav demotion | Is the site navigation clear, with consistent breadcrumbs and reachable pages? |
| Exact-match domain | Is the domain an exact keyword match? (A documented but *conditional* headwind — a strong user-signal / brand profile can offset it; note it, don't treat it as a verdict) |
| Product review | If the site has reviews, are they first-hand and substantive vs. templated? |
| Low-quality | What's the NSR signal direction? (Most fixes are upstream at the site level) |
| Scamness | Are there deceptive elements (fake urgency, hidden costs, unsupported claims)? |
| Unauthoritative | Are author credentials, citations, and expertise indicators visible? |
| Location / localness | For locally-intended queries, does the page carry real local signals, or is it a generic/national page? |
| VLQ (very low quality) | Are any pages in the bottom quality band — near-empty, auto-generated, no original value? |

**Beyond the leaked demotions: the 2024 spam-policy actions.** Three demotions introduced with Google's March 2024 spam policies are not in the leaked `CompressedQualitySignals` module, but they belong on the same audit path because a technical or on-page audit is often where their symptoms first surface:

- **Scaled content abuse** — mass-produced low-value pages (the temporal content-production spike above; the low-`contentEffort` pattern). Diagnostic: is there a large, recently-published set of templated or auto-generated pages?
- **Site reputation abuse** ("parasite SEO") — third-party or unrelated content published on an authoritative host to exploit its ranking. Diagnostic: are there hosted sections (coupon pages, sponsored posts, subfolders leased to third parties) off-topic to the site's core?
- **Expired-domain abuse** — acquiring an expired domain to reuse its residual authority for unrelated content. Diagnostic: did the domain change ownership or topic, and is old authority being repurposed?

These are covered in depth in the traffic-loss workflow (`Skills/traffic-loss-analysis/`); they are surfaced here so a technical or on-page audit path doesn't miss them. See also the itemized checklist at `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md`.

### Topical authority is measured numerically

The leaked `QualityAuthorityTopicEmbeddingsVersionedItem` module documents two specific attributes that quantify topical focus and cohesion:

- **`siteFocusScore`** — "Number denoting how much a site is focused on one topic"
- **`siteRadius`** — "The measure of how far page_embeddings deviate from the site_embedding"

Both attributes are paired with `pageEmbedding` and `siteEmbedding` (compressed vector representations of page and site content). Translation: Google computes a site-level topic embedding by aggregating across the site's pages, then measures (a) how concentrated the site's content is on a single topic, and (b) for each individual page, how far it drifts from the site's central topic.

This is the algorithmic mechanism behind the long-standing intuition that "topical authority" matters. It's not just a concept — it's measured.

**Practical implication 1: Site-level topical drift is a real problem.**

When a plumbing services site publishes a blog post about home decor, that post has a high `siteRadius` (it's far from the site's central topic embedding). Google can detect this. The off-topic post itself doesn't rank well, AND its presence dilutes the site's `siteFocusScore` — which affects how every other page on the site ranks.

This validates the existing framework recommendation against off-topic content sprawl. The mechanism is now documented: off-topic pages reduce site-level topic concentration, weakening the topical-authority signal that flows to all on-topic pages.

**Practical implication 2: Cluster-aware content pruning is more important than generic pruning.**

When auditing for content pruning, prioritize pages that are BOTH low-traffic AND high-`siteRadius` (off-topic). These are the worst offenders — they don't earn traffic AND they dilute the site's topical signal. Generic "low-traffic content pruning" works; topic-aware pruning works better because it specifically targets the pages dragging down the site-level focus.

**Practical implication 3: Topical clusters need to actually cluster.**

The cluster-mapping work documented in content-funnel plans (parent service hub → related blog posts) creates a measurable benefit: blog posts that align with the site's central topic embedding contribute positively to `siteFocusScore`. Blog posts that don't (a plumbing site with travel content, an HVAC site with cooking recipes) work against the site's topical signal regardless of how good the individual posts are.

This is the documented mechanism behind the "stay in your lane" advice. The lane is measured. Pages outside the lane have a measurable distance score (`siteRadius`).

**Practical implication 4: New content decisions should pass a topic-fit check.**

Before publishing a new piece of content, ask: "Is this on-topic for this site, or am I about to publish something with high `siteRadius`?" If the latter, either reconsider publishing it, or accept that the post will fight a topical-fit headwind that limits its individual ranking AND slightly dilutes the site's overall topic signal.

For agencies running content programs, this is a useful filter against client requests like "we should also write about [adjacent industry]." If the adjacent industry has a different topic embedding, the agency is being asked to dilute the site's central topic signal — and the resulting posts will underperform regardless of quality. Better to launch a separate site for the adjacent topic, or pass on the work.

### Anchor links: tiered quality and spam velocity

The leaked `AnchorsAnchor` module documents how Google evaluates inbound anchor links. Two findings are framework-impacting.

**Anchor links are tiered by source page quality.** The `sourceType` attribute classifies every link source into one of:

- `TYPE_HIGH_QUALITY` — base documents (top-tier indexed pages, served from SSD)
- `TYPE_MEDIUM_QUALITY` — medium quality docs
- `TYPE_LOW_QUALITY` — low quality docs (often serving from lower-tier index)
- `TYPE_FRESHDOCS` — fresh content, special-cased and treated as high quality

Translation: not all backlinks are equal. A link from a high-quality source page passes substantially more equity than the same link from a low-quality source. This connects directly to the index-tier system from `PerDocData` — links from pages in the top serving tier carry the most weight.

**Practical implication for backlink audits:** The classic "100 backlinks vs 10 high-authority backlinks" tradeoff is now grounded in a documented signal. When evaluating a client's backlink profile, the breakdown that matters isn't just "how many links" — it's "what tier are the source pages in?" A site with 1,000 backlinks predominantly from `TYPE_LOW_QUALITY` sources is materially weaker than one with 200 backlinks from `TYPE_HIGH_QUALITY` sources.

When recommending link acquisition, prioritize earning links from pages that are themselves in the top index tier (frequently crawled, well-linked, on established sites) over volume-based link building.

**Trusted anchors appear only in spam handling.** The leak has no `trustedAnchors` attribute. The nearest documented fields are the `trusted*` counters in `IndexingDocjoinerAnchorSpamInfo` (`trustedTotal`, `trustedMatching`, `trustedDemoted`, described as counts of trusted anchors used when computing anchor spam probability) and `IndexingDocjoinerAnchorTrustedInfo.trustedScore` ("fraction of pages with newsy anchors on the site, >0 for trusted sites"). Neither documents seed-set, TrustRank-style weighting of links by distance from trusted sites. That idea may well describe Google, but it is not leak-derived: present it as INFERRED.

**Practical implication:** A small number of links from genuinely trusted, established sources outweigh a large volume from the undifferentiated middle. When advising link acquisition, "closer to the trusted seed set" — recognized institutions, established publications, authoritative industry bodies — is the target, not raw referring-domain count.

**A link's value is weighted by the linking site's homepage trust.** The `homepagePagerankNs` attribute is LEAK-DERIVED and ties a source's link value to the trust/PageRank of that source *site's homepage*, not just the specific linking page. A link from a deep page of a site whose homepage is highly trusted inherits some of that site-level standing.

**Practical implication:** Evaluate a prospective link by the whole site's standing, not only the single page it sits on. A link from an obscure page of a strongly trusted domain can outperform a link from the "best" page of a weak one. This dovetails with the source-tier model — site-level homepage trust and page-level index tier both feed how much a given link is worth.

**Anchor spam velocity is measured.** The `IndexingDocjoinerAnchorPhraseSpamInfo` module documents Google's anchor-text spam detection at the phrase level:

- `phraseAnchorSpamCount` — how many spam phrases appear among unique linking domains
- `phraseAnchorSpamDays` — over how many days 80% of those phrases were discovered (the spike-detection window)
- `phraseAnchorSpamRate` — average daily rate of spam anchor discovery
- `phraseAnchorSpamStart` / `phraseAnchorSpamEnd` — start/end of detected spam spikes
- `phraseAnchorSpamDemoted` — total number of demoted anchors
- `phraseAnchorSpamFraq` — fraction of all anchors that are spam
- `phraseAnchorSpamPenalty` — combined penalty applied

Translation: Google specifically measures **velocity** of spammy anchor accumulation, not just total volume. Rapid spikes of similar anchor text from many domains over a short window get flagged and trigger anchor-text demotion.

**Practical implication 1:** Negative SEO via anchor-spam injection is a real risk. If a competitor or bad actor builds 500 spam links to a client's site over 2 weeks all using the same exact-match keyword anchor, the spike triggers `phraseAnchorSpam` flags and the resulting anchors get demoted (`phraseAnchorSpamDemoted`) — but the demotion can also generalize to legitimate similar anchors.

**Practical implication 2:** Link-building campaigns themselves can self-trigger this. When an agency runs an aggressive link campaign that produces 100+ exact-match anchor links over a short window, the `phraseAnchorSpamRate` signal fires regardless of whether the links are technically legitimate. The fix is link velocity discipline — natural backlink profiles accumulate gradually, with diverse anchor text. Sudden spikes of identical anchors look like manipulation regardless of intent.

**Practical implication 3 (audit checklist):** When auditing a client whose ranking suddenly dropped, check for recent anchor-text spikes via tools like Ahrefs/Majestic. A `phraseAnchorSpam` event leaves a documented signature — a sharp uptick in similar anchors, then a demotion event. This explains otherwise mysterious ranking drops that don't correlate with on-site changes or known algorithm updates.

**The link-quality decision matrix:**

| Source page tier | Anchor diversity | Velocity | Equity passed |
|---|---|---|---|
| TYPE_HIGH_QUALITY | Diverse | Natural | Maximum |
| TYPE_HIGH_QUALITY | Repetitive | Spiked | Demoted (anchor-spam flag) |
| TYPE_MEDIUM_QUALITY | Diverse | Natural | Substantial |
| TYPE_LOW_QUALITY | Any | Any | Marginal |
| TYPE_FRESHDOCS | Diverse | Natural | High (treated as TYPE_HIGH_QUALITY) |

Audit recommendations on link building should explicitly target the top row: high-quality source pages, diverse anchor text patterns, natural accumulation velocity. Volume-only or velocity-only strategies that ignore source-page quality and anchor diversity are fighting the documented signals.

## What an Audit Is Worth

An SEO audit is only valuable when:

1. The team has resources to deploy the recommended changes
2. SEO investment is sustained (not a one-time engagement)

For small sites without backlinks, technical fixes alone won't move rankings — without link equity and content depth, the technical foundation has nothing to support. Set expectations accordingly.

A more precise framing applies regardless of site size: most technical fixes are infrastructure hygiene (crawl-waste cleanup, redirect-chain flattening, JS/CSS minification on already-indexed pages) and should NOT be sold to clients as ranking levers. They protect crawl budget, reduce bot-induced server cost, and prevent future problems — those are real benefits worth doing, but they are not the same benefit as moving rankings.

A subset of technical fixes ARE ranking levers — but only because they unblock content that was previously invisible to Google. Examples: removing a noindex tag suppressing a money page; fixing a canonical bug that points indexable URLs to the wrong destination; recovering de-indexed revenue pages; resolving render-blocking JavaScript that was hiding the H1 and primary content from the rendered DOM. These move rankings because they make previously-suppressed content rankable, not because Google rewards "technical health" as such.

Distinguish the two when communicating to clients. The audit methodology's Expected Outcome Classification (`Skills/seo-audit-methodology/SKILL.md`) is the framework for tagging every recommendation correctly.

When estimating organic traffic value, the floor is set by PPC: if comparable terms cost $X per click via Ads, then organic traffic for those terms is worth at minimum $X × volume. If organic conversion value is below the PPC market rate, competitors will outbid the site indefinitely.

### Additional Documented Fields (verified against the leaked docs, package 0.4.0)

Each item is quoted or paraphrased from the attribute documentation. These are LEAK-DERIVED existence facts: none carries a documented weight, and none is a confirmed ranking lever.

- **Local business data on every document.** `CompositeDoc` carries `LocalWWWInfo`, which stores `wrapptorItem` entries (business name, address fingerprint, phone fingerprint), `hours`, `isLargeChain` ("widely-distributed chain"), `siteSiblings` (documented as per-document signals independent of any particular address), `geotopicality` and `brickAndMortarStrength` (no description in the docs). The docs also state that addresses and phone numbers are populated only if the document has four or fewer of each, "primarily for space reasons". INFERRED audit use: business name, address and phone are parsed and fingerprinted per page, so inconsistent NAP formatting across a client's own pages is machine-readable, not only a citation-consistency problem. A page that lists more than four locations or phone numbers would have none stored, which supports keeping each location page to its own address and number. `local_seo_auditor.py` checks this per location page when it has the page text.
- **Mobile interstitials.** `SmartphonePerDocData.violatesMobileInterstitialPolicy` is documented as indicating that the page "is violating mobile interstitial policy and should be demoted".
- **Spam scores.** `PerDocData.uacSpamScore` is 7 bits (0 to 127) with a documented threshold of 64, and a score of 64 or above is considered UAC spam. `spamtokensContentScore` is used in `SiteBoostTwiddler` to decide whether a page is UGC spam. `KeywordStuffingScore` is 0 to 127 with no documented threshold.
- **Repeat links to one domain.** `AnchorsAnchor.parallelLinks` is "the number of additional links from the same source page to the same target domain" and is not populated for local links. The docs do not say how the count is used.

Look up any module or attribute with the `google-leak-reference` skill before citing the leak in a deliverable.

## Source

Synthesized from Mark Williams-Cook's #unsolicitedSEOtips compilation (over 500 tips), Google's current published documentation, public statements from Google search engineers (Gary Illyes, Martin Splitt, John Mueller), the May 2024 Content Warehouse leak (all leaked attributes flagged LEAK-DERIVED — documented in the leak, not Google-confirmed ranking levers), and audit experience across the IHS portfolio. Last updated: 2026-07-21.
