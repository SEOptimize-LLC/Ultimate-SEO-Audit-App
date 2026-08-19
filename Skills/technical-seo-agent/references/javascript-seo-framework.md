# JavaScript SEO Framework (2026)

> Reference document for the Technical SEO Agent. Use this when auditing any site that uses JavaScript for content rendering, navigation, or critical SEO elements. Synthesized from current Google documentation, Sitebulb's advanced rendering guide, Conductor, deltavdigital, similar.ai, FratreSEO, Zumeirah, Search Engine Journal, and the December 2025 Google docs clarification on non-200 rendering.

## Core Principle

The framing has shifted in 2026. The old binary — "Google can or can't render JS" — is settled: **Google can render JavaScript**, and confirmed it officially in the March 2026 docs update by removing the long-standing "Design for accessibility" warning that told developers to test with JS disabled.

But the more important question is no longer about Googlebot. It's:

> **Is the indexable content present in the raw HTML — visible to every crawler instantly — or is it gated behind JavaScript execution that only Googlebot eventually catches up to?**

Three forces make raw HTML matter more than ever:

1. **Google decides indexability before rendering.** Status codes, robots meta, canonical tags, and soft-404 indicators in the raw HTML determine whether a page even reaches the renderer. JS-injected directives can be skipped entirely (December 2025 clarification).

2. **AI crawlers do not render JavaScript.** ChatGPT, Claude, Perplexity, and Bing AI Overviews scrape raw HTML. Anything JS-injected is invisible to them — and AI search visibility is a fast-growing distribution channel.

3. **Google's render budget is real, but it is NOT a 5-second wall-clock window.** See "The render budget, correctly stated" below. The constraint is CPU-time on a virtual clock plus a real-time ceiling, and getting this wrong sends clients to fix the wrong thing.

## The render budget, correctly stated

> **Correction, 2026-08-01.** An earlier version of this file asserted "the Web Rendering
> Service operates within an approximate 5-second snapshot window." That is the industry's
> mistranslation of a Google statement and it was wrong in a way that misdirects fixes.
> John Mueller publicly recommends the two sources that debunk it (Dave Smart / Tame the
> Bots, Tony McCreath / Web Site Advantage), so this is well-supported, not contrarian.

**Where the 5-second figure actually came from.** Martin Splitt, roughly 18 minutes into a
presentation: *"In median, a page's rendering queued for five seconds."* That is the
**median time a page waits in the render queue**, not a limit on how long rendering runs.
The industry converted a queue-wait median into a render timeout.

**The WRS runs on a virtual clock it controls.** It can speed up, slow down, or pause time
for the headless Chrome instance. Critically, **it freezes the clock while network requests
are in flight.** Dave Smart's test page ran a `setInterval` counter and two POST requests
with real delays of 5s and 4s; both returned, their content was rendered, and the page's own
reported elapsed time was **0.02 seconds**. Network waiting does not spend render budget.

**What the clock actually measures: CPU work.** Tony McCreath measured 162ms of Googlebot
time against roughly 10 seconds of real time under sustained CPU load. The virtual clock
advances slowly during execution, but it does advance. JavaScript parse and execution cost
is what consumes the budget.

**The observed sequence near the threshold** (McCreath, measured):

| Googlebot clock | What happens |
|---|---|
| ~5.0s | "Prepares for the end." First resize event: scale 0.42 → 1.0, outer dimensions to 1×1px |
| ~5.3s | Second resize: viewport height expands enormously (>1,000,000px in testing) to simulate deep scroll and trigger lazy-loaded content |
| ~5.25s target | Rendered HTML captured |

**The real-time ceiling is about 52 seconds.** If rendering has not completed within ~52s of
actual time, Googlebot cancels all outstanding network requests so it can reach its virtual
target and finish. Googlebot also proactively cancels requests it judges unimportant
(fonts) or that are disallowed or failing.

**Live test is more patient than real indexing.** Smart's infinite-loop test cut off at
16–18 iterations (~48–54s) under live testing, but only 10 iterations (~30s) during actual
indexing. **A page that renders correctly in URL Inspection's live test can still fail in
the indexing pipeline.** Never accept a passing live test as proof that indexing rendered
the page; check the indexed result.

**What this changes in recommendations:**

- ❌ Do NOT tell a client "speed up your **server** so Googlebot can finish rendering in
  time." Network latency and TTFB pause the virtual clock. Server response speed is a
  Stage 1 crawl-rate concern and a Stage 4 Core Web Vitals concern, not a render-budget
  concern.
- ✅ DO tell them to reduce **page weight**, and keep the distinction sharp, because these
  two get collapsed constantly. DOM size, resource count, total payload and JS execution
  cost all consume render budget or trip the renderer outright. *Latency is free; work is
  not.* Barry Hunter's Search Central Community guide puts it plainly: heavy and slow pages
  are "exponentially more likely to suffer from rendering failures during the high-volume,
  resource-constrained real Googlebot crawl", and names excessive DOM size, heavy JS, and
  stalling on a large external resource (unoptimised images, video) as the causes of a hard
  render failure.
- ✅ DO target JavaScript execution and parse cost, long tasks, and main-thread work. That
  is what actually spends the budget.
- ✅ DO flag pathological resource chains that could approach the ~52s real-time ceiling.
- ✅ DO expect lazy-loaded content below the second-resize viewport to be missed, and treat
  the two resize events as the mechanism that makes most lazy loading work at all.
- ⚠️ Googlebot caches JS/CSS resources aggressively (30-day TTL per Google, cited by
  McCreath), so a repeat crawl may render against stale assets rather than your new build.

**Attribution:** Dave Smart, `tamethebots.com/blog-n-bits/the-5-second-google-render-limit-myth`;
Tony McCreath, "Tony's Theory of Googlebot Relativity", `bigcommerce.websiteadvantage.com.au`.
Both recommended by John Mueller. Secondary coverage: Search Engine Journal, 2026-07-28.
The specific millisecond and viewport figures are McCreath's measurements from his own test
pages, not Google-published specifications. Treat the mechanism as well-evidenced and the
exact numbers as one researcher's observations.

## Google's Rendering Pipeline

The four-stage order is **Crawlability → Rendering → Indexability → Ranking** (see `seo-fundamentals-2026.md`). Always state it that way. What follows zooms into the crawl-to-render transition and must never be presented as a substitute for the stage order.

```
Crawl Queue
    ↓
Initial HTML fetch (raw response)
    ↓
Render-eligibility gate  ←  Judged on RAW HTML only
    ↓ (if eligible)            (status, robots meta, canonical)
Render Queue (delayed, budgeted)
    ↓
Web Rendering Service (~5s window, headless Chromium)
    ↓
Index
```

**Do not call this gate an "indexability decision."** That name collides with the Indexability stage and has already produced output that stated the pipeline order wrongly, placing indexability ahead of rendering. The gate decides whether a URL proceeds to the renderer. Indexability is the later stage deciding whether the rendered document enters the index.

Critical insight from Sitebulb: **if the raw HTML signals non-indexability, the page never reaches the renderer**, even if JS would later "fix" it.

Per Google's December 2025 docs clarification: *"pages with a 200 HTTP status code are sent to rendering, this might not be the case for pages with a non-200 HTTP status code."*

## Rendering Hierarchy by SEO Risk

| Strategy | SEO Risk | Best For |
|---|---|---|
| **SSG** (Static Site Generation) | Lowest | Marketing pages, blogs, documentation |
| **SSR** (Server-Side Rendering) | Low | Most use cases, ecommerce PDPs/PLPs |
| **ISR** (Incremental Static Regeneration) | Low | Frequently updated catalogs |
| **Dynamic Rendering** (cloak by user-agent) | Medium | Legacy migrations only — Google calls it a temporary workaround |
| **CSR** (Client-Side Rendering) | High | Authenticated dashboards/apps — NOT public SEO content |

Frameworks that get this right out of the box: Next.js (SSR/SSG/ISR), Nuxt.js, Astro, Remix, Eleventy, SvelteKit.

## The 9 JS-Rendering Failure Patterns to Audit

### 1. Empty raw HTML (SPA shell)
**Pattern:** Raw HTML is essentially `<div id="root"></div>`. All content injected by JS.
**Detect:** Raw word count <100, rendered word count >300.
**Severity:** Critical.
**Fix:** Migrate to SSR or SSG. Goal: passes the View Source test — main content present in raw HTML.

### 2. Content visibility gap
**Pattern:** Significant content (FAQs, product copy, related sections) only appears after JS executes.
**Detect:** Rendered word count is 1.5x–3x raw word count.
**Severity:** High.
**Fix:** Move primary content blocks into the raw HTML response. Reserve JS for purely interactive elements.

### 3. Critical render gap
**Pattern:** Page is hollow in raw HTML — rendered content is more than 3x raw.
**Detect:** Rendered/raw word ratio ≥3.0 with raw ≥100 words.
**Severity:** Critical.
**Fix:** SSR/SSG migration. Stopgap: prerender these specific page types.

### 4. Render-only critical SEO elements
**Pattern:** `<title>`, `<meta description>`, `<link rel="canonical">`, `<h1>`, or `<meta robots>` is set by JavaScript.
**Detect:** Field present in rendered HTML, missing from raw HTML.
**Severity:** Critical (for canonical, meta robots, title), High (for description, H1).
**Fix:** Emit these elements in the raw HTML `<head>`/body. Use the X-Robots-Tag HTTP header for robots directives if JS injection is unavoidable.
**Why it matters most:** These elements participate in the **pre-render indexability decision**. JS-injected versions can be skipped entirely.

### 5. Link discovery gap
**Pattern:** Primary navigation, pagination, or related-content links are JS-injected.
**Detect:** Rendered outlinks ≥2x raw outlinks, with absolute gap ≥5.
**Severity:** High.
**Fix:** Render primary nav and pagination in raw HTML. JS-inject only filters, modals, and accordions.
**Why:** AI crawlers don't follow JS-discovered links. Google follows them slowly, weakening internal link equity flow.

### 6. Click/hover/scroll-gated content
**Pattern:** Significant content lives inside accordions, tabs, "Load More" buttons, or modals that require user interaction to reveal.
**Detect:** Heuristic — DOM contains many `<button>` elements with `data-toggle`, accordion class names, or aria-expanded patterns near content blocks. Often correlates with high render-gap ratio.
**Severity:** High.
**Fix:** Reveal content by default, or move it inline. Use `<details>`/`<summary>` (visible to crawlers) instead of JS-only accordions.
**Why:** Googlebot does NOT trigger user interactions. Content behind clicks is invisible.

### 7. Hash-based routing
**Pattern:** URLs use `#/` or `#!` as routing markers (e.g., `/#/product/123`).
**Detect:** URL contains `#/` or `#!` patterns.
**Severity:** Critical.
**Fix:** Migrate to History API push state. Replace `/#/category/shoes` with `/category/shoes/`.
**Why:** Google treats everything before the `#` as the canonical URL. All ranking signals collapse onto the parent URL; deep pages become invisible.

### 8. Render budget exposure
**Pattern:** Long JS tasks block the main thread long enough that critical content doesn't paint within Google's 5-second snapshot window.
**Detect:** TBT >1.5s; correlates with INP >500ms.
**Severity:** High.
**Fix:** Break up long tasks (>50ms). Code-split heavy bundles. Defer non-critical scripts. Audit DevTools Coverage panel for unused JS.

### 9. CSS viewport traps
**Pattern:** `100vh` without max-height creates oversized "above the fold" regions. Google's renderer simulates a 1,750px mobile / 10,000px desktop viewport — content can be pushed below that window and treated as below-the-fold or missed entirely.
**Detect:** Manual review when LCP and CLS are anomalous, or when "Crawled: currently not indexed" status appears for visually-fine pages.
**Severity:** Medium.
**Fix:** Constrain hero/landing sections to reasonable max-heights.

## Ecommerce-Specific Patterns

| Pattern | Why It's Bad | Fix |
|---|---|---|
| Product grids fully JS-rendered | Crawlers see empty PLP shells | SSR product cards with structured markup |
| Infinite scroll without paginated fallback | Products below the fold never crawled | Implement `rel="next"` paginated URLs alongside infinite scroll |
| Hash-routed faceted nav (`#/category/shoes/red`) | Filters can't be indexed independently | Use `?color=red` query parameters or path segments |
| Product variants only rendered on swatch click | Variant content invisible to crawlers | Render all variants in raw HTML or use separate URLs |
| Cart-state-dependent canonicals | Canonical changes based on JS state | Emit canonical server-side; never make it depend on client state |
| Lazy-loaded above-the-fold images | Hero images miss LCP measurement | `loading="eager"` for above-the-fold; `loading="lazy"` only below fold |

## How to Test What Google Sees

1. **Google Search Console URL Inspection.** Most accurate view. Shows raw response, rendered DOM, screenshot, and rendering metadata. Check Coverage reports for "Discovered — currently not indexed" pages.
2. **Rich Results Test.** Comparable accuracy to URL Inspection without GSC access.
3. **View Source vs DevTools Elements.** Compare side-by-side. View Source = raw HTML; Elements = rendered DOM. Anything in Elements but not View Source is JS-injected.
4. **`curl` test.** `curl -A "ChatGPT-User" https://example.com/page` shows what AI crawlers see. If main content isn't there, it's invisible to AI search.
5. **Screaming Frog with JS Rendering enabled.** Configuration → Spider → Rendering → JavaScript. Then export the **Response vs Render Report** for the raw-vs-rendered comparison this auditor consumes.
6. **Sitebulb's Response vs Render report.** Equivalent comparison data.

## Raw HTML vs Rendered HTML Diff Protocol (On-Demand Diagnostic)

The 9-pattern framework above describes *what* to look for in a Screaming Frog Response vs Render export across a full crawl. This protocol covers the *single-URL* case — when the auditor needs to quickly diagnose one page without a fresh JS-rendered crawl, or when a finding needs live verification under Rules 11/12.

Run this protocol whenever:
- The auditor is verifying a single critical finding live (per audit-workflow Rule 11)
- A client reports "the page looks fine but Google says it's not indexed"
- A page is "Crawled — currently not indexed" in GSC and the cause isn't obvious from the Response vs Render export
- The site is a known JS-heavy / SPA / Next.js / Webflow / Wix build
- A redirect or canonical target is in question and the page's authoritative state matters

### Step 1 — Capture the raw HTML

```bash
curl -s -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" "<URL>" > /tmp/raw.html
```

This is what Googlebot sees on first pass, before the renderer runs. Status code, meta robots, canonical, hreflang, and any indexability directive in this file are the ones Google trusts.

For AI-crawler equivalence (ChatGPT, Claude, Perplexity), repeat with `-A "ChatGPT-User"` — the result should be identical, but if the origin server cloaks by user-agent, you'll catch it here.

### Step 2 — Capture the rendered HTML

Two options, in preference order:

1. **GSC URL Inspection (when GSC access exists)** — Inspect URL → View Tested Page → HTML tab → copy. This is Google's actual renderer, with Google's actual budget. Authoritative.
2. **DevTools Elements panel (no GSC needed)** — Load the page in Chrome → right-click → Inspect → Elements → right-click `<html>` → Copy → Copy outerHTML. Equivalent to a successful render with a generous budget. May overstate what Google actually captures if the render takes longer than ~5 seconds.

Avoid `curl` with a headless-browser library for this step unless the rendering environment matches Google's WRS (Chromium, mobile viewport, ~5s budget) — most quick scripts overstate rendering success.

### Step 3 — Diff the two

Quick visual diff (works for spot checks):

```bash
diff <(curl -s "<URL>" | grep -oE '<(title|h1|meta|link rel="canonical")[^>]*>.*</?(title|h1)?>' ) /tmp/rendered_extracts.txt
```

Better: extract specific critical-path elements from both files and compare. The 7 elements that matter most:

| Element | Why it matters | Raw must contain |
|---|---|---|
| `<title>` | Determines SERP snippet + ranking | The final, intended title |
| `<meta name="robots">` | Indexability directive | The final directive (December 2025 Google clarification: JS-injected robots directives may be skipped) |
| `<link rel="canonical">` | Canonical target | The final canonical (JS-injected canonicals are unreliable signals) |
| `<h1>` | Primary topical signal | The final H1 text |
| Primary body copy (first 200 words) | Topical relevance signal | Substantive text, not just a loading skeleton |
| Internal links in `<a href="">` | Crawl-path discovery | Real anchor hrefs, not `<a onclick="...">` patterns |
| Schema (JSON-LD blocks) | Rich-result eligibility | The final, valid schema (JS-injected schema is often missed by AI crawlers entirely) |

### Step 4 — Classify the diff

| Diff result | Severity | What to call it |
|---|---|---|
| All 7 elements identical (raw == rendered for critical path) | Pass | "JS rendering is decorative — SEO-critical content is server-rendered." |
| Body copy or schema present in rendered, missing from raw | High | "Render-dependent critical content — invisible to AI crawlers; risk to Google first-pass indexation." |
| Title, canonical, or meta robots differ between raw and rendered | Critical | "Render-only [element] — Google may use the raw version regardless. December 2025 clarification means JS-injected directives can be skipped." |
| Raw HTML is essentially an empty shell (`<div id="root">` only) | Critical | "SPA shell — pattern #1 from the 9-pattern framework above." |
| Rendered HTML has 3x+ the word count of raw | Critical | "Critical render gap — pattern #3 from the 9-pattern framework." |
| Raw returns non-200 but rendered would have rendered fine | Critical | "Indexability decision happens on raw HTML before rendering — page never reaches the renderer." |

### Step 5 — Convert to recommendation

The recommendation must specify *which* element fails the raw test and *which* fix applies:

- If title/canonical/meta robots are render-only → **server-side render those specific elements** (Next.js: `<Head>` from `next/head`; Nuxt: `useHead()`; static export: emit at build time). Recommendation must include the framework-specific implementation path, not a generic "make it SSR."
- If body copy is render-only → SSR or SSG the route. Prerendering is a stopgap, not a durable fix.
- If schema is render-only → emit JSON-LD server-side. AI crawlers won't render it; this directly affects Perplexity / ChatGPT / Claude citation eligibility.
- If internal links are render-only (e.g., `<a onclick>` instead of `<a href>`) → rewrite to real anchor tags. Crawl-discovery dies otherwise.

### What this protocol does NOT do

- It does not replace a full Screaming Frog JS-rendered crawl for site-wide analysis. That's still the right tool for >10-URL audits.
- It does not measure render budget (use Lighthouse / PSI for TBT).
- It does not test third-party-script-injected content (Optimizely experiments, GTM-injected scripts) — those run later and aren't part of the Google render pipeline anyway.
- It does not validate AI-crawler behavior beyond raw-HTML parity — if you need to verify what ChatGPT actually cites, run a citation test in the live ChatGPT product.

### Worked example: a render-only canonical

A client reports their page's canonical is pointing to the right URL. View Source shows `<link rel="canonical" href="https://example.com/page-A">`. GSC URL Inspection shows `<link rel="canonical" href="https://example.com/page-B">` in the rendered tab.

**Diagnosis:** Render-only canonical. The raw HTML emits canonical to page-A. JavaScript on the page overwrites it to page-B post-load. Per Google's December 2025 documentation update, JS-injected directives may be skipped — Google is likely treating page-A as canonical despite the visual evidence in DevTools.

**Fix:** Emit the correct canonical server-side. The JS that overwrites it should be removed entirely (don't try to "fix" the override — fix the source).

**Validation method:** Re-fetch the URL with `curl`, confirm canonical in raw HTML matches the intended target, then re-inspect in GSC URL Inspection to confirm Google's rendered canonical matches.

## What This Auditor Detects (Implementation)

The `JavaScriptRenderingAuditor` runs against any Screaming Frog export. It activates progressive layers based on what columns are present:

**Layer A — works without JS-rendered crawls:**
- Hash-based routing (URL pattern check)
- Render budget exposure (TBT correlation)

**Layer B — requires JS-rendered crawl with Response vs Render export:**
- Empty raw HTML / SPA shell detection
- Content visibility gap (1.5x–3x ratio)
- Critical render gap (>3x ratio)
- Render-only title / canonical / meta description / H1 / meta robots
- Link discovery gap

If only Layer A runs, the auditor emits an INSIGHT issue telling the user how to unlock Layer B (re-crawl with JS Rendering enabled).

## Anti-Patterns to Avoid in Recommendations

- **Don't recommend "just disable JS"** — that's not a fix. JS is fine; render the result server-side.
- **Don't recommend Dynamic Rendering as a long-term solution** — Google explicitly calls it a temporary workaround in current docs.
- **Don't conflate JS rendering issues with Core Web Vitals issues.** They overlap (TBT/INP) but are separate problems with separate fixes.
- **Don't recommend prerendering as the default fix.** It's a stopgap. SSR or SSG is the durable solution for most cases.
- **Don't claim "Google can't render JS"** — that contradicts Google's official 2026 stance. Frame the issue as render delay, render budget, AI crawler invisibility, and pre-render indexability decisions.

## Quick Reference: Severity Mapping

| Issue | Severity |
|---|---|
| Empty raw HTML (SPA shell) | Critical |
| Render-only canonical | Critical |
| Render-only meta robots | Critical |
| Render-only title | Critical |
| Hash-based routing | Critical |
| Critical render gap (>3x) | Critical |
| Render-only meta description | High |
| Render-only H1 | High |
| Content visibility gap (1.5–3x) | High |
| Link discovery gap | High |
| Render budget exposure (high TBT) | High |
| CSS viewport traps | Medium |
| Click-gated content (heuristic) | Medium–High |

## Connection to AI Search Visibility

JS rendering isn't only a Google SEO concern. The same audit findings predict AI search visibility:

- **Pages flagged with empty raw HTML or critical render gap** are nearly impossible for ChatGPT, Claude, and Perplexity to cite. These crawlers don't render JS at all.
- **Sites that fix render-only critical elements** typically see improvements in both Google indexing reliability AND AI search citation rates.
- **The fastest path to AI search visibility is durable raw HTML output.** SSR/SSG isn't just a Google fix — it's the foundation for being citable across the entire AI search ecosystem.
