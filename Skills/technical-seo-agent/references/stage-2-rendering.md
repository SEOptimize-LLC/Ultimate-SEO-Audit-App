# Stage 2 of 4: Rendering

> **Pipeline position.** `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`
>
> Rendering sits between crawling and indexing. A bot that fetches a document it cannot
> render hands a hollow page to the indexing stage, and the page is judged on what
> arrived rather than on what a user would see. Deep mechanics live in
> [javascript-seo-framework.md](javascript-seo-framework.md); this file is the stage
> definition, the diagnostic logic, and the strategy decision.

## What this stage decides

**Whether the document that reaches the indexer contains the content a user would see.**
Not whether the URL was reachable (Stage 1) and not whether Google chooses to index the
result (Stage 3).

---

## The diagnostic principle for this stage

**A render failure presents as an indexability symptom.** The cause sits one stage
upstream of where the symptom appears.

The usual manifestation is **"Crawled, currently not indexed."** Google fetched the URL,
evaluated a rendered document that was empty or thin, and declined to index it. Nothing
in that status names rendering, which is why the fix gets misdiagnosed as a content
problem when it is a delivery problem, or as a crawl problem when crawling worked fine.

This is also the mechanical reason the literature conflates the stages. Measured across
the 34-source rendering corpus reviewed for this file, **zero sources connect render
failure to the "Crawled, currently not indexed" status**, and zero cover JS-injected
canonical or robots directives as a failure mode. The corpus is strong on rendering
strategy and silent on the diagnostic chain.

**Practical rule:** before accepting any "thin content" or "quality" diagnosis on a
non-indexed page, check the raw HTML. If the raw document is hollow and the rendered one
is not, the finding is Stage 2, not Stage 3, and no amount of content editing will fix it.

---

## The render-eligibility gate

**Render-eligibility is judged on the raw HTML, before the renderer runs.** Status code,
meta robots, canonical. If the raw response signals non-indexability, the URL never
reaches the renderer, and JavaScript that would have corrected the directive never
executes.

Corroboration is strong: **30 of 34** sources in the reviewed corpus address the
raw-HTML-versus-rendered distinction. This is settled ground, not a fringe reading.

**Consequences that follow, and that clients get wrong:**

- A canonical, `meta robots`, `title` or `H1` injected by JavaScript is a **critical**
  defect, not a cosmetic one, because those elements participate in a decision made
  before the JS runs. Use the `X-Robots-Tag` HTTP header when JS injection is unavoidable.
- **Your crawler will hide this from you.** Most crawl tools render by default and will
  show a clean canonical that Google never saw. You and Googlebot end up looking at two
  different documents, and only one of you gets a vote.
- Per Google's December 2025 clarification: pages with a 200 status are sent to
  rendering; this may not be the case for non-200 statuses.

**Never call this gate an "indexability decision."** That name collides with Stage 3 and
has already produced a stage-order error in this project's output. It decides whether the
URL proceeds to the renderer. Stage 3 decides whether the rendered document enters the
index.

---

## Render budget

The full corrected mechanics are in
[javascript-seo-framework.md § The render budget, correctly stated](javascript-seo-framework.md).
Summary of what matters for triage:

- **There is no 5-second wall-clock render limit.** That figure is a mistranslation of
  Martin Splitt's statement that five seconds was the **median queue wait**.
- The Web Rendering Service runs a **virtual clock it pauses during network requests**, so
  latency does not spend render budget.
- What spends the budget is **JavaScript execution and parse cost**.
- A **real-time ceiling around 52 seconds** cancels outstanding requests.
- **The live test is more patient than real indexing** (~16-18 iterations live vs ~10
  during indexing, per Dave Smart). A page that renders correctly in URL Inspection's
  live test can still fail in the indexing pipeline.

**Corpus note:** the 5-second claim appears in only **1 of 34** sources reviewed, and the
virtual-clock mechanism appears in **0 of 34**. The corpus neither propagates the myth
widely nor explains the real mechanism. The accurate model comes from Dave Smart and Tony
McCreath, both recommended by John Mueller, neither of whom was in the supplied source
set.

---

## Rendering strategies, and what Google actually recommends

### Google's own position

From Google's Chrome team on web.dev: *"Broadly speaking, we encourage developers to
consider server-side rendering or static rendering over a full rehydration approach."*

That sentence is the most authoritative single statement in this corpus, and it points at
static and server rendering, not at hydration-heavy SPA architectures.

### The strategies

| Strategy | What it is | SEO risk | Best for |
|---|---|---|---|
| **Static / SSG** | HTML generated at build time, one file per URL | Lowest | Marketing pages, blogs, docs, catalogs that change predictably |
| **SSR** | HTML generated per request on the server | Low | Most cases, ecommerce PDP/PLP, personalised pages |
| **ISR** | Static, regenerated incrementally | Low | Large, frequently-updated catalogs |
| **Dynamic rendering** | Different response by user-agent | Medium, and deprecated | Legacy migration only. See below |
| **CSR** | Browser renders everything via JS | High | Authenticated dashboards and apps, NOT public SEO content |

### Static versus SSR, per Google

Static rendering gives a consistently fast TTFB because nothing is generated per request,
and it is CDN-edge-cacheable. Its limit is that it needs one HTML file per URL, which
becomes infeasible when URLs cannot be enumerated ahead of time.

SSR handles live data and personalisation that static cannot, at the cost of compute per
request and a slower TTFB. Google notes React's `renderToString()` is synchronous and
single-threaded and therefore slow; streaming server DOM APIs get initial HTML out sooner.

### The rehydration trap

**Google's own measured position:** *"Performance metrics collected from real websites
using server-side rendering and rehydration indicate that it's rarely the best option."*

The failure mode is specific and it is an SEO problem as well as a UX one: the page looks
loaded but cannot respond to input until client scripts execute and handlers attach.
Rehydration also ships the UI twice, once as server-rendered HTML and again as serialized
data plus the client implementation, which inflates payload and blocks the main thread.

Mitigations Google names: streaming SSR, progressive rehydration, partial rehydration.
Partial rehydration is described as difficult to implement in practice.

### Diagnostic: is it static rendering or prerendering?

Google's own test, and it takes ten seconds: **disable JavaScript and load the page.**
Statically rendered pages keep most interactive features. Prerendered pages may keep
links but are otherwise inert. Useful because the two are routinely conflated in vendor
marketing and they behave differently under a crawler.

---

## Dynamic rendering is a deprecated workaround

**Google's documentation, quoted in the corpus:** *"Dynamic rendering is a workaround and
not a long-term solution for problems with JavaScript-generated content in search
engines."*

**12 of 34** sources flag it as a workaround, temporary, deprecated, or not recommended.
Google's own earlier framing was already conditional: *"we recommend dynamic rendering as
a workaround solution to this problem."* Google emphasises SSR should be chosen over
dynamic rendering where possible. Reasons given across sources: infrastructure
complexity, maintenance burden, and the fact that it serves different content by
user-agent, which sits uncomfortably close to cloaking.

**Two source-quality warnings on this topic:**

1. **Three sources in the supplied set sell prerendering or dynamic-rendering services**
   (`prerender.io`, `prerendering.com`, `huckabuy.com`). They have a commercial interest
   in the conclusion they argue for. They are outnumbered by their own industry here, and
   should not be counted as independent corroboration.
2. **Google contradicts itself across its own properties.** The web.dev article still
   lists dynamic rendering as "an option worth considering," while Search Central
   documentation calls it a workaround and not a long-term solution. When Google's
   properties disagree, Search Central is the operative guidance for search behavior and
   web.dev is the operative guidance for performance architecture.

**Recommendation posture:** do not propose dynamic rendering as a target state. If a
client already runs it, treat it as technical debt with a migration path to SSR or static,
not as a finding requiring immediate remediation.

---

## AI crawlers do not render

**Most AI crawlers do not execute JavaScript at all**, not slowly and not on a deferred
queue. They consume raw HTML. Now corroborated by **13 of 34** sources in this corpus plus
Conductor's monitoring data, so this is no longer a single-source claim.

Phrasing discipline: say **"most"**, not "all". Some AI crawlers have limited or
inconsistent rendering. The safe operating assumption is raw-HTML-only.

**Consequences:**

- A render gap costs AI search visibility outright, on top of its cost in Google.
- There is **no re-index request mechanism** for most AI crawlers. No URL Inspection
  equivalent exists, so a first crawl finding a hollow page may never be retried. This
  inverts the usual publish-then-fix tolerance.
- GPTBot specifically is reported as struggling with JS-heavy sites.

Access and blocking questions (robots.txt directives, WAF and CDN rules) are Stage 1, and
covered in [stage-1-crawlability.md](stage-1-crawlability.md).

---

## Detection and diagnosis

**A worked example from building this file.** Google's own community guide titled "A Guide
to Diagnosing Failed Rendering" returned **13 words** to a raw HTTP fetch, because
`support.google.com` is client-side rendered. Google's documentation about rendering
failures is itself invisible without rendering. If it can happen there, assume it can
happen on any client's site, and never trust a raw fetch alone to tell you a page is empty
of content.

**The diagnostic ladder:**

1. **Raw versus rendered diff.** Fetch the raw HTML (`curl`, or a crawler set to raw) and
   compare against the rendered DOM. The Raw vs Rendered HTML Diff Protocol in
   [javascript-seo-framework.md](javascript-seo-framework.md) is the full method, with
   detection thresholds for the nine documented failure patterns.
2. **Word-count ratio.** Rendered word count several times raw means the document is
   hollow to anything that does not render.
3. **Element presence in raw.** Check `title`, `canonical`, `meta robots`, `H1`, and
   primary navigation links exist in the **raw** response specifically.
4. **JavaScript-disabled load.** Distinguishes static rendering from prerendering, and
   surfaces what a non-rendering consumer receives.
5. **GSC URL Inspection.** Use "View Crawled Page" and "View Tested Page" to see
   Googlebot's own HTML. **Remember the live test is more patient than indexing**, so a
   pass here is necessary but not sufficient.
6. **View Rendered Source** (Chrome extension) for a fast side-by-side. Named by only 2
   of 34 sources but it is the quickest manual check available.
7. **Log files** for whether the renderer actually returned, and for AI crawler hits.

### Reading URL Inspection correctly

Source for this subsection: Barry Hunter (Diamond Product Expert), "A Guide to Diagnosing
Failed Rendering", Google Search Central Community, Oct 2025. Senior-practitioner tier, not
Google staff, and the guide self-declares AI assistance in drafting. Treat mechanics as
credible and thresholds as experience-based.

**"View Crawled Page" versus "View Tested Page" are not the same evidence.**

| | View Crawled Page | View Tested Page (Live Test) |
|---|---|---|
| What it shows | The DOM from the **last real crawl** | A **current, synthetic, standalone** render |
| Screenshot | **None.** You must read the HTML | Yes |
| Realism | What Googlebot actually got | Isolated, not resource-constrained like a mass crawl |
| User-agent | Regular Googlebot | A distinct interactive testing agent |
| Timeout | Variable, crawl-dependent | Strict and short, around 5–7 seconds |

**The asymmetry that governs how you read a result:** *a Live Test failure is conclusive; a
Live Test pass is not.* If the Live Test shows problems, assume the real Googlebot has them
too. If it passes, keep checking, because the isolated test is more generous than a
production crawl on JS execution while also having its own hard interactive wall.

**Practical trick worth using.** Copy the entire "View Crawled Page" HTML into a local
`.html` file and open it in a browser. That approximates how complete Googlebot's output
actually was, and it substitutes for the screenshot that view does not provide.

**Diagnostic signals in the tool:**

- **"Something went wrong. If the issue persists, try again in a few hours."** Not a
  transient glitch. It means the page is **too heavy or too slow to render** within the
  interactive timeout. Causes named: excessive DOM size, heavy or slow JavaScript, or
  stalling on a large external resource including unoptimised images and video. **Treat it
  as evidence the real Googlebot will struggle too.**
- **"Other Error" during page rendering** is reported as more likely a crawl-demand issue
  than a technical rendering fault. Check crawl demand before chasing code.
- **"More Info" → "Page resources"** lists resources that failed to load. Anything blocked by
  `robots.txt` or erroring is a candidate cause of render failure, and blocked CSS/JS is a
  **Stage 1 cause with a Stage 2 effect**.

### Viewport distortion: the `100vh` trap

Googlebot renders with a **narrow** viewport (mobile-like) but a **very tall** one, because
it does not scroll and needs height to trigger lazy-loaded content. That combination breaks a
common CSS pattern.

**Any element sized in viewport-height units expands enormously in that tall viewport.** A
`100vh` hero image, or a heading scaled to viewport height, can grow until it pushes the real
content out of the area Google uses for indexing. The page looks fine to every human who
checks it.

**And the Live Test understates it:** the Live Test uses a tall viewport, but the real
Googlebot can use a taller one still, so a problem that looks marginal in testing can be
worse in production.

This corroborates the viewport-resize behaviour measured independently by Tony McCreath (two
resize events near the render threshold, the second expanding viewport height into the
millions of pixels). Two sources, different methods, same mechanism.

**Check for it:** grep the CSS for `vh` units on hero, banner, heading and section containers
on any template where content sits below a full-height element.

### Page weight as render risk

Experience-based thresholds from the same source. **These are one practitioner's judgment,
not Google specifications**, so cite them as such:

- Full load over **5–7 seconds** → high risk of rendering issues
- Over **10 seconds** → serious danger
- Total resource size over **500KB** → approaching danger; **several MB** → red alert

The stated conclusion: speed is not a direct ranking factor, but heavier and slower pages are
"exponentially more likely to suffer from rendering failures during the high-volume,
resource-constrained real Googlebot crawl." PageSpeed Insights is noted as more patient than
the GSC Live Test, which makes it a useful second opinion when the Live Test hard-fails.

**Reconciles cleanly with the render-budget correction:** latency is free because the virtual
clock pauses on network waits, but **work is not**. DOM size, resource count, payload and JS
execution all cost. "Speed up the server" is the wrong recommendation; "reduce page weight"
is the right one.

### The sitemap-processing red herring

A causal chain worth knowing, because it sends people to fix the wrong thing:

```
failed rendering → pages look empty/low-quality → crawl demand falls
   → Google deprioritises sitemap processing → child sitemaps show "0 discovered URLs"
```

**Sitemaps are a discovery mechanism and do not directly influence crawl budget or demand.**
So unprocessed child sitemaps are a **confirmatory symptom of low crawl demand**, not a
sitemap defect. Resubmitting, restructuring or splitting the sitemap will not help. Fix the
rendering, crawl demand recovers, and sitemap processing follows.

This is the same symptom-far-from-cause pattern as "Crawled, currently not indexed": the
report that surfaces the problem is several steps downstream of what broke.

### Failure types to expect

Failed rendering produces three distinct classes of damage, and they need naming separately
in a deliverable because they have different owners:

1. **Content omission.** JS-loaded content missed entirely, so the page cannot rank for the
   queries that content targets.
2. **Indexing gaps.** Google indexes an empty or partial version, which then reads as a low
   quality signal.
3. **Link discovery failure.** JS-generated internal links never discovered, which
   interrupts equity flow **and** prevents other pages being crawled and indexed. This is the
   Stage 2 → Stage 1 feedback loop: a render failure on one page becomes a discovery failure
   for every page it should have linked to.

---

## Severity mapping for render-stage findings

| Finding | Severity | Expected outcome tag |
|---|---|---|
| Primary content absent from raw HTML on money pages (SPA shell) | Critical | Ranking Lever |
| `canonical`, `meta robots` or `title` injected by JavaScript | Critical | Ranking Lever |
| Rendered/raw word ratio ≥3 on indexable templates | Critical | Ranking Lever |
| Primary navigation or pagination JS-injected | Critical | Ranking Lever (Stage 1 discovery impact too) |
| Non-indexed pages where raw HTML is hollow | Critical | Ranking Lever, and reclassify any "thin content" finding on those URLs |
| Content behind click, hover or scroll gating | High | Ranking Lever |
| Heavy JS execution cost consuming render budget | High | Ranking Lever if content is being missed, else UX |
| Lazy-loaded content below the second-resize viewport | High | Ranking Lever |
| Running dynamic rendering as the permanent architecture | Medium | Risk Mitigation, migration path to SSR |
| SSR-with-rehydration hurting interactivity | Medium | UX (indirect ranking) |
| CSR on authenticated, non-indexable app routes | Not a finding | n/a |

Note the pattern: most genuine render-stage failures are **Ranking Levers**, not hygiene,
because they unblock content that was invisible. Do not downgrade them to hygiene to
under-promise.

---

## Stage firewall

Belongs elsewhere despite appearing under rendering headings in the corpus:

| Topic | Actually belongs to |
|---|---|
| robots.txt and WAF blocking of any crawler | Stage 1, Crawlability |
| Server response time and crawl rate | Stage 1 (crawl rate) and Stage 4 (CWV) |
| `noindex` and canonical *decisions* | Stage 3, Indexability |
| "Crawled, currently not indexed" as a status | Stage 3 symptom, frequently a Stage 2 cause |
| Core Web Vitals scores | Stage 4, Ranking |

**Do not tell a client to speed up their server so Googlebot can finish rendering.**
Network latency pauses the render clock. Server speed matters at Stage 1 and Stage 4, not
here.

---

## Attribution and exclusion register

| Claim | Source | Status |
|---|---|---|
| Encourage SSR or static over full rehydration | Google, web.dev | Google's own position. Safe to state and cite |
| SSR-with-rehydration rarely the best option | Google, web.dev, citing real-site metrics | Google's own. Metrics not published in detail |
| Dynamic rendering is a workaround, not a long-term solution | Google Search Central, quoted across corpus | Google's own. Safe to state |
| Most AI crawlers do not execute JavaScript | 13/34 sources + Conductor | Well corroborated. Say "most", never "all" |
| No re-index request mechanism for AI crawlers | Conductor | Single source, mechanically plausible. Attribute if load-bearing |
| ~5.25s virtual-clock target, 52s real-time ceiling, viewport resize behavior | Tony McCreath, own test pages | One researcher's measurements. Mechanism well-evidenced, exact figures are his |
| Live test ~16-18 iterations vs ~10 during indexing | Dave Smart, own test | Single experiment. Directionally important, treat numbers as indicative |
| Googlebot caches JS/CSS with a 30-day TTL | McCreath, citing Google | Not independently verified here |
| GPTBot struggles with JS-heavy sites | Corpus, reported secondhand | Attribute, do not state as measured |

### Excluded from this file

**Lumar's JavaScript SEO ebook** (`lumar.io/ebooks/javascript-seo-guide/how-javascript-rendering-works/`)
is excluded as stale. It describes Google rendering via **headless Chrome 41**, cites an
"892 new Chrome features" gap, and references 2017 testing. Google moved to evergreen
Chromium in 2019. Corpus check: **Chrome 41 appears in 0 of the other 34 sources** and
evergreen Chromium appears in 10, so this ebook is the lone outdated source rather than a
minority position. Its two-wave-indexing framing and "minutes to a week" render delay
range are also inherited from that era and are not carried forward here.

**Not read, therefore not cited:** `seobility.net/en/wiki/Rendering` (403),
`prerender.io` (403, and a vendor homepage), `fatjoe.com` (429),
`webmasters.stackexchange.com` (403). Both `support.google.com` pages returned 13 words to
a raw fetch and are pending a rendered retrieval; the failed-rendering guide's substance
is not represented above.

## Source corpus

39 URLs supplied (40 unique from 41 submitted, one duplicate). 34 extracted, 64,742 words.
Highest-value: **web.dev** (Google's Chrome team, rendering strategy and the rehydration
verdict), **Sitebulb** (two guides), Botify (two), Onely, OnCrawl, DebugBear, seoClarity,
Semrush, Next.js, Search Engine Journal (two, including the Martin Splitt takeaways and
the 5-second test coverage), and John Mueller's post, which is what led to the render
budget correction.
