# Stage 3 of 4: Indexability

> **Pipeline position.** `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`
>
> Crawlability is about **access**. Indexability is about **inclusion**: whether a crawled
> and rendered document gets stored and becomes eligible to appear in results. Detailed
> canonical failure tables and the full robots-directive reference live in
> [SKILL.md § Indexability Issues](../SKILL.md); this file is the stage model, the
> sub-phase split, the symptom decoder, and the severity logic.

## What this stage decides

**Whether Google stores the rendered document and makes it eligible to rank.** Two
independent things have to go right: Google must pick this URL as the canonical
representative of its content, and it must judge the content worth keeping.

**Critical boundary:** a `noindex` directive does not block crawling. Google must crawl
the page to see the directive at all. Anything that permits crawling but prevents
inclusion is a Stage 3 finding, not Stage 1.

---

## The two sub-phases

Like Stage 1 (Discovery vs Retrieval), this stage decomposes into two phases that fail
independently and need different fixes.

| Sub-phase | Question | Fails when | Typical symptom |
|---|---|---|---|
| **Canonicalization** | Which URL represents this content? | Duplicate cluster, conflicting or wrong canonical, parameter sprawl | Wrong URL indexed; "Duplicate, Google chose different canonical"; declared canonical ignored |
| **Index decision** | Is this document worth storing? | Thin, templated or low-value content; fails quality threshold; explicit `noindex` | "Crawled, currently not indexed"; "Excluded by noindex tag" |

Canonicalization runs **before** the index decision. Search Engine Land's pipeline places
it as a discrete step: discovery → rendering → **canonicalization** → indexing. That
ordering explains why canonical faults are disproportionately damaging: they operate at a
gate upstream of the storage decision, so a wrong canonical can suppress an otherwise
perfectly indexable page without any quality problem existing.

---

## REQUIRED: the four-check directive verdict

**Every audit must return an explicit verdict on indexability directives, and a missing
verdict is an audit defect.** This holds for full-site crawls and single-URL audits alike.
When directives are clean, say so explicitly. Never silently omit it.

The four checks, with corpus coverage noted because three of them are effectively absent
from the mainstream literature and will not be caught by following a typical checklist:

1. **Meta robots `noindex` in the `<head>`.** Is the page excluded via
   `<meta name="robots">`? Confirm whether the exclusion is intentional. *Corpus coverage:
   16 of 24.*

2. **`X-Robots-Tag` HTTP header `noindex`.** Check the **response header**, not just the
   HTML. A page can be noindexed via header with no visible meta tag, making it invisible
   in view-source. Applied at CDN, load balancer or middleware. Use `curl -I` or the
   DevTools Network panel; on a crawl, cross-reference the `X-Robots-Tag` column against
   `meta_robots`. *Corpus coverage: **3 of 24**. This is the most commonly missed source of
   accidental noindex and almost nobody writes about it.*

3. **`noindex` placed in the `<body>` (invalid, and a defect in both directions).** Google
   honours robots directives only in the `<head>`. A `noindex` in the body is **ignored**.
   Both failure directions must be flagged: an owner who put `noindex` in the body believes
   a page is excluded when it is fully indexable, and conversely a page believed safely
   excluded may be leaking into the index. Verify **placement**, not just presence.
   *Corpus coverage: **0 of 24**.*

4. **Canonical: declared versus Google-selected.** Compare the page's declared
   `rel=canonical` against Google's selected canonical in GSC URL Inspection. Divergence
   means Google is overriding the site's choice, which signals index confusion, equity
   landing on the wrong URL, or an unresolved duplicate cluster. Report the declared value,
   the Google-selected value, and the gap. *Corpus coverage: **1 of 24**.*

Each is a discrete finding with its source named: crawl column, response header, live head
inspection, or GSC URL Inspection.

---

## Canonicalization

Google picks one URL to represent a set of duplicates or near-duplicates. The site's
canonical tag is a **hint**, not a directive, which is why declared-versus-selected
divergence is the check that matters rather than "is a canonical present."

**What to verify:**

- Money pages use **self-referencing** canonicals unless deliberate consolidation is
  intended, and the canonical matches the live URL exactly: protocol, subdomain, trailing
  slash, case.
- No **conflicting** canonicals (pages pointing at each other rather than at one source).
- No **cross-domain** canonicals sending authority off-site unintentionally.
- Canonical is in the `<head>`, is absolute, and does not point at a `noindex`, 4xx, 5xx,
  or redirecting URL.
- Parameter and faceted variants resolve to a single canonical.

Full failure tables by severity are in [SKILL.md § Canonical Tag Problems](../SKILL.md).

**Consolidation choice:** redirect duplicates to the stronger version with a 301 where the
duplicate serves no independent purpose. Use a canonical where both URLs must remain
reachable. Redirects are the stronger signal; canonicals preserve access.

---

## The index decision

Passing canonicalization does not earn inclusion. Google evaluates:

**Technical signals.** 200 status, no `noindex` from any source, canonical resolving to
self or to an intended target, structured data present and valid.

**Quality signals.** Uniqueness, depth, usefulness, semantic relevance to a real query,
and clarity of structure. Pages that are thin, templated, auto-generated, or near-duplicate
get crawled and then dropped.

**Internal signal strength.** Pages many clicks deep with few inbound internal links are
deprioritised for indexing even when technically clean. This is where Stage 1 and Stage 3
genuinely interact rather than being conflated: internal linking is a Stage 1 *discovery*
mechanism and simultaneously a Stage 3 *importance* signal.

### Partial indexing is not automatically a defect

**The goal is not everything indexed; it is the right things indexed.** Google
deliberately skips near-duplicates and low-demand URLs. Before writing a finding about
non-indexed pages, confirm the pages in question *should* be indexed. Per
`.claude/rules/audit-workflow.md` Rule 7, exclude paginated pages, PPC landers, thank-you
pages, internal search results, account pages and utility URLs from the count first, or
the finding is inflated noise.

---

## Symptom decoder: routing GSC statuses to their real stage

This is the highest-value table in this file, because each status names where Google
stopped, not what caused it. **The cause frequently sits upstream of the symptom.**

| GSC status | What Google did | Real cause usually lives at | First check |
|---|---|---|---|
| **Crawled, currently not indexed** | Fetched and rendered; declined to store | **Stage 2 or Stage 3** | Is the raw HTML hollow? If yes it is a render failure, not a content failure. If raw is fine, it is a genuine quality or duplication judgment |
| **Discovered, currently not indexed** | Knows the URL; has not fetched it | **Stage 1** | Internal link count, crawl depth, sitemap presence, crawl allocation on large sites |
| **Excluded by 'noindex' tag** | Honoured a directive | Stage 3, config | Intentional? Check all three noindex sources including the header |
| **Duplicate, Google chose different canonical** | Canonicalisation went against you | Stage 3, canonicalisation | Declared vs selected; is the chosen URL actually the better one? |
| **Duplicate without user-selected canonical** | No canonical declared | Stage 3, canonicalisation | Add a self-referencing canonical |
| **Soft 404** | Page returned 200 but looked empty or error-like | **Stage 2 or Stage 3** | Render check first: an empty render reads as a soft 404. Then check for genuine thin content |
| **Blocked by robots.txt** | Never crawled | **Stage 1** | Is the block intentional? Note a blocked URL can still be indexed if externally linked |
| **Page with redirect** | Source redirects; destination indexed | Stage 1, usually benign | Apply the keep/remove decision tree; do not bulk-clean |
| **Crawl anomaly / server error** | Fetch failed | **Stage 1** | Template-wide or isolated? |

**The two that get misdiagnosed most:**

- **Crawled, currently not indexed** is the single most common place a delivery problem
  gets written up as a content problem. Check raw HTML before proposing a rewrite. Google
  rendered the page, but if the raw document was hollow and the render came back thin,
  editing the copy will not change the outcome.
- **Soft 404** on a 200-status page with real content in the browser is almost always a
  render failure.

**Neither status is reachable from crawl data alone.** Both require manual export from
GSC's Page indexing report, since Google has no bulk Index Coverage API. Per the project's
input stack, these are inputs #7 and #8. Without them the audit is structurally blind to
Google's own indexing judgments.

---

## Measurement

**Index Efficiency Ratio (IER)** = indexed pages ÷ intended indexable pages.

Ten thousand pages intended, six thousand indexed, IER 0.6, so 40% of intended content is
not visible. Attributed to SEO Clarity via Search Engine Land. Star Diamond SEO describes
the same concept as a "submitted-to-indexed ratio" and puts a healthy site at 90%+; two
independent sources converging on the metric, though the 90% threshold is one source's and
should be cited as such rather than stated as a benchmark.

**The denominator is the hard part and it is where the metric usually goes wrong.**
"Intended indexable" must exclude every deliberately-excluded URL. Compute it from a
filtered set, not from total crawled URLs, or the ratio measures your own noise.

**Track over time, not as a snapshot.** A falling ratio after a release points at a
template-level `noindex`, a canonical regression, or a broken redirect. Trend beats
absolute value, and the same is true of crawl-error counts.

---

## Deliberate noindex: acceptable versus problematic

**Acceptable:** thank-you and confirmation pages, internal search results, user account
and login pages, cart and checkout, duplicate filter and sort variants, staging content,
thin tag and date archives on sites that do not need them.

**Problematic, treat as Ranking Lever when found on these:** service and product pages,
blog posts meant to earn traffic, category pages with unique content, any page carrying
external links or historical traffic.

**The launch-and-redesign trap:** a global `noindex` applied during a build and left on a
template. Always check high-value templates specifically rather than sampling, because this
failure is template-scoped and a random sample can miss it entirely.

---

## Stage firewall

Measured bleed in the reviewed corpus: **Stage 1 topics appear in 24 of 24** indexability
documents, Stage 4 topics in 20 of 24, Stage 2 in 13 of 24. This is the least stage-pure
corpus of the three reviewed so far, largely because most sources cover crawlability and
indexability as a single subject.

| Topic | Actually belongs to |
|---|---|
| robots.txt blocking (24/24 of these docs discuss it) | **Stage 1.** It prevents crawling, not indexing |
| XML sitemaps, internal links, orphans, crawl depth | **Stage 1** |
| Crawl budget | **Stage 1**, and only material at large scale |
| Redirect chains | **Stage 1** |
| JavaScript and rendering mechanics | **Stage 2** |
| Core Web Vitals, E-E-A-T, backlinks, authority | **Stage 4** |

**The legitimate interactions**, which are not conflation:

- **robots.txt + noindex together is a trap.** Blocking crawl means Google never sees the
  noindex. If you want a URL out of the index, allow the crawl and serve the directive.
- **Internal linking is genuinely dual-stage**: a discovery mechanism at Stage 1 and an
  importance signal at Stage 3.
- **Render failure causes index failure.** Stage 2 is the cause; Stage 3 is where it shows.

---

## Severity mapping

| Finding | Severity | Expected outcome tag |
|---|---|---|
| `noindex` on money pages from any of the three sources | Critical | **Ranking Lever** (unblocks invisible content) |
| Template-wide `noindex` left from a build | Critical | **Ranking Lever** |
| Canonical on money pages pointing to a wrong, noindexed, 4xx or redirecting URL | Critical | **Ranking Lever** |
| Google-selected canonical diverging from declared on revenue pages | Critical | **Ranking Lever** |
| Revenue pages absent from the index with no directive explaining it | Critical | **Ranking Lever**, and check raw HTML before calling it quality |
| `noindex` in `<body>` on pages the owner believes are excluded | High | Risk Mitigation |
| Duplicate clusters with no canonical declared | High | Ranking Lever if a money page is in the cluster |
| Parameter and faceted variants indexed alongside canonicals | High at scale, Medium below | Infrastructure Hygiene |
| Thin or templated content failing the quality threshold | High | Ranking Lever only if the page can realistically compete; otherwise consolidate or noindex |
| Index bloat from archive, tag and date URLs | Medium at scale, skip on small sites | Infrastructure Hygiene |
| Sitemap containing noindex or non-canonical URLs | Medium | Infrastructure Hygiene |
| Missing self-referencing canonicals where no duplication exists | Low | Infrastructure Hygiene |
| Deliberate `noindex` on utility pages | Not a finding | n/a |

**Honesty note that applies harder here than anywhere:** removing a `noindex` from a page
that should be earning, or fixing a canonical suppressing an indexable URL, is a **Ranking
Lever**, not hygiene, because it makes previously invisible content visible. Do not
downgrade these to hygiene to be conservative.

---

## Indexing in a multi-surface world

Indexed content now feeds Google Search, Discover, AI Overviews, Bing Copilot, Perplexity
and ChatGPT, and each surface interprets the same index differently.

**AI systems use indexed data as input, then apply their own layers** of semantic
relevance, trust and intent matching. A page can be fully indexed and still never appear
in an AI Overview if its semantic signals are too weak for the model to build an answer
from. (Search Engine Land attributes these points to Botify, Backlinko and Conductor; treat
as reported synthesis rather than measured fact.)

**The practical consequence:** indexation is necessary but no longer sufficient for
visibility. It is a floor, not a finish line. Consistency of structured data, metadata and
canonical signals matters more when several surfaces read the same index for different
purposes.

Access-side AI crawler questions (robots.txt directives, WAF rules) are Stage 1. Their
inability to render is Stage 2.

---

## Attribution register

| Claim | Source | Status |
|---|---|---|
| Initial HTML `noindex` prevents the page reaching the renderer | Search Engine Land, citing Google Developers | **Independent corroboration** of the render-eligibility gate. Safe to state |
| Canonicalization is a discrete pipeline step before indexing | Search Engine Land | Single source for the explicit ordering, mechanically consistent with observed behavior |
| Crawled-not-indexed implies a value or similarity judgment | Search Engine Land, plus existing KB | Well supported |
| Discovered-not-indexed points to crawl budget, internal linking or rendering | Search Engine Land, plus existing KB | Well supported |
| Index Efficiency Ratio | SEO Clarity via Search Engine Land | Named metric, attribute it |
| Healthy sites show 90%+ submitted-to-indexed | Star Diamond SEO (batch 1) | Single source, no methodology. Cite as theirs |
| AI Overviews apply extra semantic layers over indexed data | Search Engine Land citing Botify, Backlinko, Conductor | Reported synthesis, not measured. Attribute |

**Corpus assessment.** This corpus is competent on the basics (duplicate content 19/24,
`noindex` 16/24, canonical 16/24) and near-silent on the diagnostics that decide real
audits. Nothing in it required changing the existing KB position, and the existing
four-check verdict is stronger than any single source reviewed. The one genuine addition is
canonicalization as a named pipeline step.

**Not read, therefore not cited:** both `lumar.io/learn/seo/indexability` pages (403),
`clutch.co` (403), `pureseo.com` (403), `interactivepalette.com` (403). Tool pages
(`indexguru`, `rankability`) and the `codefinity` course page contained no reference
substance. Three submissions were internal duplicates and two (`yoast.com`,
`logicalposition.com`) were already read in batch 1.

## Source corpus

34 URLs submitted, 29 unique and new, 24 extracted, 50,302 words. Highest-value: **Search
Engine Land** (pipeline ordering, GSC status semantics, IER), Sitebulb hints,
StudioHawk, Semrush, Search Engine Journal, Netpeak (the only source addressing 410 vs
404), Intergrowth, Discovered Labs (AI indexing), 2Ten Tech (the only source on
declared-vs-selected canonical).
