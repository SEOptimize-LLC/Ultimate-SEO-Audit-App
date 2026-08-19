# Stage 1 of 4: Crawlability

> **Pipeline position.** `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`
>
> This is the first stage. Nothing downstream of it can be earned back by work further
> along, which is why crawl-stage findings outrank every other category of finding
> regardless of how large or small the affected page count is. The canonical stage
> order lives in `seo-fundamentals-2026.md`; state it that way in every deliverable.

## What this stage decides

**Whether a crawler knows the URL exists, and whether it can successfully download what
the server returns.** That is the whole scope. It does not cover whether the content
renders, whether Google chooses to index it, or how it ranks.

The single most common reasoning error in the published literature on this topic is
importing indexability topics into it (measured: see the Stage Firewall section below).
Keep the boundary clean, because the fixes are different and the expected outcomes are
different.

---

## The two sub-phases that fail independently

Crawlability decomposes into two phases with separate failure modes and separate
diagnoses. Conflating them produces the wrong fix.

| Sub-phase | Question | Fails when | GSC symptom |
|---|---|---|---|
| **Discovery** | Does the crawler know this URL exists? | No inbound internal link, absent from sitemap, never submitted | URL absent from GSC entirely |
| **Retrieval** | Can the crawler download the content? | 4xx, 5xx, robots.txt block, timeout, slow response | URL known but uncrawled, or crawl error reported |

**The diagnostic that follows from the split:** a URL that does not appear in Search
Console at all has a *discovery* failure. A URL sitting in "Discovered, currently not
indexed" has succeeded at discovery and is stalled at *retrieval* (Google knows it
exists, has not fetched it). Those two states have almost nothing in common as fix
lists, so establish which one you are looking at before writing a recommendation.

Source: the discovery/retrieval decomposition is Star Diamond SEO's framing and it is
the most useful structure in the reviewed corpus. It aligns with the GSC state
definitions already documented in `gsc-indexation-states.md`.

---

## The five crawl sub-stages

Crawling itself decomposes further. Useful when you need to locate precisely where a
URL is failing rather than saying "it isn't being crawled."

1. **Discovery.** A URL enters the crawl queue, via a previously-crawled page being
   re-crawled, an XML sitemap entry, an internal link, an external link, or a manual
   submission.
2. **Fetching.** The crawler issues an HTTP request. The server's response code decides
   whether anything further happens.
3. **Parsing.** The returned HTML is analysed and three things are extracted: links
   (which go back into the discovery queue), resource references (images, CSS, JS,
   fetched separately), and metadata.
4. **Rendering.** JavaScript execution, if the URL got past the render-eligibility gate.
   This is where Stage 1 hands off to Stage 2, covered in `javascript-seo-framework.md`.
5. **Indexing.** Stage 3 territory. Covered in `stage-3-indexability.md`.

**The feedback loop in step 3 is the part worth internalising.** Parsing feeds discovery.
Crawling a page is how the next set of URLs gets discovered, which is why a broken or
JS-only navigation is a *discovery* failure and not merely a rendering one, and why a
page's crawlability depends on the crawlability of the pages that link to it.

Source: five-stage decomposition per StudioHawk. Stage ordering cross-checked against
`seo-fundamentals-2026.md`.

---

## Discovery mechanics

### The three discovery mechanisms

**Internal links are primary**, and the only mechanism fully under the site's control.
Googlebot follows links from pages it already knows. A page with no inbound internal
link from anywhere has no link path to reach it.

**The XML sitemap is secondary, and its guarantee is narrower than most people assume.**
A sitemap entry guarantees only that Google is *aware* the URL exists. It does not
guarantee crawling and it does not guarantee indexing. A site relying on the sitemap to
compensate for missing internal links has a discovery problem it has papered over rather
than fixed, because the orphan still receives no internal PageRank.

**External links are a third discovery path.** A backlink creates a crawl path, not just
an authority signal, and can accelerate discovery of a new URL relative to waiting for
internal-link or sitemap discovery. Corollary worth stating to clients: a backlink
pointing at a 404 is a wasted backlink in both senses.

### Orphan pages

Zero inbound internal links. Discoverable only via sitemap or external link, receiving
no internal PageRank, and signalling to Google that the site itself does not consider
the page worth linking to. Fix is internal links from contextually related pages, not a
sitemap entry.

### Crawl depth

Pages reachable in fewer clicks from the homepage get crawled more readily and receive
more internal PageRank, because more link paths terminate on them. Deeply buried pages
may not be reached before crawl allocation is spent on a large site.

The commonly cited target is **important pages within 3 clicks of the homepage**, with
some sources saying 3 to 4, and Star Diamond arguing for 2 to 3 via a pillar-and-cluster
architecture that caps depth at homepage → pillar → article. Treat 3 clicks as a working
heuristic rather than a Google-stated threshold, because no source in the corpus traces
it to Google documentation.

### Discovery blockers checklist

- Navigation or pagination links that exist only after JavaScript executes, leaving no
  crawlable path in the raw response
- `nofollow` on primary navigation links
- Broken links (4xx/5xx) in navigation, which terminate the crawl path for everything
  downstream of them
- Orphans with no inbound internal link
- Sitemap omissions: published content never added
- Sitemap pollution: entries that 404, redirect, or carry `noindex`, which dilutes the
  sitemap's signal about what the site considers important
- Pages reachable only from a robots.txt-blocked page

---

## Retrieval mechanics

### Response codes at the crawl stage

| Response | Retrieval outcome | Note |
|---|---|---|
| 200 | Success. HTML returned, links parsed, content passed downstream | |
| 301 / 302 | Followed, at the cost of a hop | Chains multiply the cost. See the redirect keep/remove decision tree in `SKILL.md` |
| 404 | URL does not exist | One 404 is minor. 404s that internal links point at are a crawl-path failure |
| 401 | Behind authentication | Fine if intentional; keep out of the sitemap |
| 403 | Forbidden. **Requires disambiguation** | A 403 to Screaming Frog does not prove Googlebot is blocked. Verify with GSC live test before recommending any WAF change |
| 429 | Rate-limit artifact, usually of your own crawl | Re-crawl slower before treating as a finding |
| 5xx | Server failed | Persistent 5xx on indexed pages leads to de-indexation |

Full 401/403/429 disambiguation is in `SKILL.md`. That material is stronger than
anything in the reviewed corpus, 29 of 31 sources of which treat all 4xx as equivalent.

### Server response time as a crawl constraint

Slow server responses reduce how many URLs a crawler completes per session, and Google
throttles request rate to avoid degrading the host. This is the most under-covered real
crawl constraint in the literature (4 of 31 sources mention it at all) and it is worth
checking explicitly, because it is invisible in a standard issue list.

**Where to check:** GSC Crawl Stats report (average response time, plus the host-status
breakdown).

**Attributed threshold:** Star Diamond SEO puts "consistently above 500ms" as the marker
of a hosting constraint affecting crawl frequency, and contrasts a 2-second response
against 200ms as the difference in pages-per-session. Both figures are that single
source's, not Google's. Use the direction of the claim, cite the number as theirs, and
prefer the client's own Crawl Stats trend as evidence.

**Fixes, in order of cost:** page and object caching, then CDN, then hosting upgrade.

---

## Crawl budget, correctly scoped

**Scale qualifier, mandatory on every mention.** Crawl budget is a real constraint at
large scale and effectively a non-issue on small or new sites. Google allocates it on
two inputs: host capacity to serve requests without degrading for users, and perceived
value of what it expects to find.

- **Small sites** (Star Diamond's figure: under roughly 1,000 pages, with decent
  hosting): Google can crawl everything in a session. Crawl budget is not the
  constraint, and citing it as a benefit of a fix is misleading. Discovery and retrieval
  are the real constraints at this size.
- **Large sites** (tens of thousands of URLs and up, or heavy churn): budget management
  becomes real, particularly where paginated archives, tag pages, faceted navigation and
  parameter URLs consume allocation that money pages need.

**Never state crawl budget as the expected benefit of a fix on a small or new site.**
This has produced a real error in this project's output. When a fix's only benefit is
crawl-budget efficiency, it is Infrastructure Hygiene, and on a small site it may not be
worth doing at all.

The levers, where budget genuinely applies: server response time, URL-space cleanliness,
and demonstrated content value over time. Ecommerce-specific parameter and faceted
handling is in `robots-txt-ecommerce-framework.md`.

---

## Crawl-stage issue catalog

Ordered by corpus consensus (n = 31 sources), which is a proxy for how routinely each
appears in real audits rather than a measure of severity.

### robots.txt misconfiguration (28/31)

The most powerful crawl control and the most dangerous when wrong. A single `Disallow`
on the wrong path removes a section from crawling.

- **Critical distinction:** robots.txt is a *crawl* directive, not an *index* directive.
  A blocked URL can still surface in results if externally linked. Combining `Disallow`
  with `noindex` on the same URL is self-defeating, because the `noindex` cannot be seen
  if crawling is blocked.
- **Detection:** read the file line by line. GSC robots.txt report, and Bing Webmaster's
  tester for cross-checking.
- **Root causes seen in the corpus:** overly broad directory rules, CMS defaults, and
  deployment reverting the file. Conductor documents a real case where a code deploy
  reverted robots.txt across an entire publisher's properties.
- **Validate before deploying**, and re-check after every deployment. This is a
  regression-prone file, not a set-and-forget one.

### Internal link and navigation failures (27/31)

Covered under Discovery above. The highest-consensus issue after robots.txt, and the one
most likely to be under-diagnosed because it presents as "pages aren't indexed" rather
than as an error.

### XML sitemap problems (25/31)

Missing content, stale entries, 404s and redirects inside the sitemap, `noindex` URLs
listed, and sitemaps not referenced from robots.txt. Audit for bloat and omission in
both directions.

### Broken links and 4xx (24/31)

Prioritise by whether internal links point at them. An unlinked 404 is inventory noise;
a 404 that navigation links to breaks the crawl path for everything beyond it. Report
unique URLs affected, not export row counts (per `.claude/rules/audit-workflow.md`
Rule 10).

### Site architecture and depth (16/31)

Covered under Crawl depth above.

### Server errors, 5xx (14/31)

Template-level 5xx matters far more than isolated instances. Persistent 5xx on indexed
URLs eventually removes them from the index, which makes this a Ranking Lever rather
than hygiene once pages have already dropped.

### Orphan pages (12/31)

Covered under Discovery above.

### Redirect chains and loops (10/31)

Each hop costs crawl efficiency. Most common origins are migrations, slug changes and
category restructures. **Do not bulk-clean these**: the keep/remove decision tree in
`SKILL.md` applies, and cosmetic redirects that already resolve correctly belong on a
leave-as-is list.

### Crawl traps (5/31)

Infinite URL spaces: calendars generating unbounded date URLs, faceted filter
combinations, session IDs in URLs, unbounded pagination. Under-covered in the literature
relative to how much damage it does on large sites.

### Log file analysis (11/31)

The only source of ground truth about what crawlers actually requested, as opposed to
what a crawl simulation predicts. Named by a third of the corpus but rarely with any
method attached.

---

## AI crawlers are a Stage 1 concern with different rules

AI crawler access is a crawlability question, not an "AI SEO" question, and it belongs at
this stage. Three properties make it behave differently from Googlebot:

**1. Most do not execute JavaScript at all.** Not "slowly" or "on a delayed queue", but
not at all, because of the resource cost at scale. Anything injected client-side is
invisible to them: titles, H1s, canonicals, internal links, product details, pricing,
primary body content. A render gap therefore costs AI visibility outright, on top of
whatever it costs in Google. Confirms and extends the position already in
`javascript-seo-framework.md`.

**2. There is no re-index request mechanism.** GSC's URL Inspection gives a manual
override for Google. No equivalent exists for most AI crawlers, so a first crawl that
finds thin content, a render gap, or an access block may not be retried, and there is no
button to ask. This inverts the usual "publish then fix" tolerance: technical
correctness at publish time carries more weight than it does for Google.

**3. Crawl behavior differs from Googlebot's.** Conductor's own monitoring data (their
figures, their content) shows AI crawlers hitting a page more frequently and sooner after
publication than Google or Bing, and in their Boston Globe Media case, AI crawlers
"frequently landed on 404 pages and bypassed navigational signals" where Google followed
predictable site paths. Treat the specific multiples as vendor-reported. The behavioral
direction is worth testing per client rather than assuming.

**What to check:**

- robots.txt directives for `GPTBot`, `ClaudeBot`, `PerplexityBot`, `CCBot`,
  `OAI-SearchBot`, and whether blocking them was a deliberate decision or inherited
  boilerplate. Blocking removes the site from AI answer consideration entirely.
- WAF, CDN and bot-protection rules blocking AI user agents. This is the most likely
  silent blocker, and it will not appear in robots.txt.
- Whether critical content, navigation and metadata exist in the **raw** HTML.
- Server logs or a monitoring tool for actual AI crawler hits. Absence of hits is itself
  the finding.
- Gated content decisions made deliberately rather than inherited from pre-AI practice.

---

## Stage firewall: what does NOT belong here

Measured across the 31-source corpus, these non-crawl topics appear under a
"crawlability" heading at these rates:

| Topic | Actually belongs to | Appears in |
|---|---|---|
| `noindex` | Stage 3, Indexability | 16/31 |
| Canonical tags | Stage 3, Indexability | 17/31 |
| Duplicate content | Stage 3, Indexability | 16/31 |
| JavaScript / CSR | Stage 2, Rendering | 19/31 |
| Core Web Vitals | Stage 4, Ranking | 8/31 |
| Backlinks / authority | Stage 4, Ranking | 9/31 |

**24 of 31 sources file at least one indexability topic as a crawlability issue.** Star
Diamond lists `noindex` and canonical conflicts under a heading called "Technical
Blockers That Kill Crawlability" and then contradicts itself correctly in its own FAQ:
"Crawlability is whether Google can access the page. Indexability is whether Google
chooses to add the page to its index after crawling it."

That contradiction inside a single well-reasoned source is the reason this firewall
section exists. **When a finding involves a directive that permits crawling but prevents
indexing, it is a Stage 3 finding.** `noindex` does not block crawling. Google must
crawl the page to see the `noindex` at all.

The one legitimate crawl-stage interaction: a `noindex` page still consumes crawl
resources, which matters only at the scale where crawl budget matters.

---

## Diagnostic decision tree

1. **Does the URL appear in GSC at all?**
   - No → discovery failure. Check inbound internal links, sitemap inclusion, whether
     the linking pages are themselves crawlable.
   - Yes → continue.
2. **What does the server return to a direct fetch?** (`curl -I`)
   - 4xx → disambiguate 401 / 403 / 429 before writing anything.
   - 5xx → server-side. Check whether it is template-wide.
   - 3xx → follow the chain; count hops; check the destination is a 200.
   - 200 → continue.
3. **Is the URL disallowed in robots.txt?**
   - Yes → is the block intentional? Check nothing important is reachable only through
     the blocked path.
   - No → continue.
4. **Is the crawl path intact?** Are navigation and pagination links present in the raw
   HTML, unbroken, and not `nofollow`ed?
5. **Is server response time constraining crawl?** GSC Crawl Stats, and check host
   status.
6. **Is crawl allocation being consumed by junk URLs?** Only ask this if the site is
   large enough for it to be a real constraint.
7. **All clean at this stage** → state the crawlability verdict as clean explicitly and
   move to Stage 2. Do not silently omit a clean verdict.

---

## Severity mapping for crawl-stage findings

Crawl-stage position raises severity, because everything downstream inherits the failure.

| Finding | Severity | Expected outcome tag |
|---|---|---|
| robots.txt blocking indexable money pages | Critical | Ranking Lever (unblocks invisible content) |
| Template-wide 5xx | Critical | Ranking Lever if pages already de-indexed |
| Money pages orphaned or unreachable in raw HTML | Critical | Ranking Lever |
| Navigation only present after JS execution | Critical | Ranking Lever |
| Broken links inside primary navigation | High | Ranking Lever if they gate real pages |
| Sitemap missing published money pages | High | Ranking Lever |
| Slow server response constraining crawl | High on large sites, Medium below | Infrastructure Hygiene, unless pages are going unindexed |
| Crawl traps generating unbounded URLs | High on large sites, Low below | Infrastructure Hygiene |
| Redirect chains, 3+ hops | Medium | Infrastructure Hygiene |
| Sitemap containing redirects or 404s | Medium | Infrastructure Hygiene |
| Crawl allocation on archive and tag URLs | Medium at scale, skip below | Infrastructure Hygiene |
| Cosmetic redirects already resolving correctly | Leave as-is | Not a finding |

Expected-outcome definitions are in `../seo-audit-methodology/SKILL.md`. The honesty
exception applies here more than anywhere: crawl-stage fixes that unblock previously
invisible content are genuine Ranking Levers, not hygiene.

---

## Unverified and single-source claims register

Per `~/.claude/rules/anthropic-patterns/no-unverified-claims.md`, these appear in the
corpus but are not independently verified. Attribute them or leave them out. **Do not
restate any of these as established fact in a client deliverable.**

| Claim | Source | Status |
|---|---|---|
| Server response consistently >500ms indicates a hosting constraint | Star Diamond SEO | Single source. Direction plausible, number is theirs |
| ~~Healthy sites show 90%+ of submitted URLs indexed~~ | Star Diamond SEO | **Moved to [stage-3-indexability.md](stage-3-indexability.md).** Submitted-to-indexed is an indexability metric, not a crawl metric. Kept here only as a pointer to avoid the claim being re-added at the wrong stage |
| New pages on healthy sites index within 24 to 72 hours | Star Diamond SEO | Single source, contradicted in tone by their own "few hours to a few days" FAQ answer |
| Crawl budget is not a constraint under ~1,000 pages | Star Diamond SEO | Single source. Scale principle is sound; treat the specific figure as theirs |
| Recrawl interval is typically every 4 to 30 days | Embryo | Single source, no methodology |
| Important pages should sit within 3 clicks of the homepage | SearchAtlas (3, and 3 to 4) | Widely repeated heuristic, not traced to Google documentation in any source reviewed |
| AI crawlers visited pages 100x more than Google or Bing | Conductor (own data) | Vendor-reported, single case |
| ChatGPT ~8x and Perplexity ~3x Google's crawl frequency, 5 days post-publish | Conductor (own data) | Vendor-reported, single page, one time window |
| AI crawlers frequently land on 404s and bypass navigational signals | Conductor, Boston Globe Media case | Single case study. Worth testing per client, not asserting |
| Google crawls and re-evaluates YMYL content more frequently | Star Diamond SEO | **Unsupported.** No corroboration found. Do not use |
| 41% of crawl requests going to 301s and 404s | contact.so | Figure from their own client screenshot. Not a general statistic |
| 96.55% of content gets zero Google traffic | Ahrefs study, via StudioHawk | Real published study. Attribute to Ahrefs if used |

### Corpus imprecisions not imported

- **"Search engines cannot crawl a fully client-side rendered site"** (Lumar) and
  **"crawlers cannot read HTML to understand content because pages are built with
  JavaScript"** (StudioHawk). Both overstate. Google demonstrably renders JavaScript.
  The accurate framing is render delay, render budget, the raw-HTML eligibility gate,
  and total non-rendering by most AI crawlers. Per `javascript-seo-framework.md`, never
  claim Google cannot render JavaScript.
- Several sources treat all 4xx responses as equivalent. They are not. See the
  disambiguation table above.

---

## Source corpus

35 sources supplied, 33 read (31 via extraction, 2 via fetch retry). Highest-value for
this stage: Star Diamond SEO (discovery/retrieval split), StudioHawk (five sub-stages),
Conductor (AI crawler behavior), Lumar blog (five-issue detection and fix detail),
SearchAtlas, Botify, seoClarity, Search Engine Land, Wix, Moz Academy, Ahrefs, Yoast,
Women in Tech SEO (AI crawlability).

**Not read, and therefore not cited anywhere above:** `thehoth.com/blog/crawlability/`
(403) and `voigtmarketing.com` (429). Two duplicate submissions of
`themarketingdistrict.com/insights/crawlability-101` were deduplicated;
`sunbeam.ai` is a homepage rather than a crawlability resource, and
`llmpulse.ai/geo-crawlability-checker` is a tool page.
