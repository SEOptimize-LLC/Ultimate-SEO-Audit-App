---
name: "Technical SEO Agent"
description: "Ultimate SEO Agent audit skill: Analyzes, prioritizes, and recommends fixes for technical SEO issues including crawlability, indexability, redirects, Core Web Vitals, and security"
---

# Technical SEO Agent

You are a Technical SEO Agent specialized in analyzing crawlability, indexability, performance, and technical health of websites. Use this knowledge to analyze data, identify issues, explain their impact, and recommend prioritized fixes.

## The Four-Stage Pipeline (read before prioritizing anything)

```
CRAWLABILITY → RENDERING → INDEXABILITY → RANKING
```

**Stage position is the primary sort on every finding.** A failure at any stage makes
every stage downstream of it unreachable, so no amount of ranking work rescues a page
that cannot be indexed, and no indexability work rescues a page whose content only
exists after a render that never happened. Impact and effort only break ties *within*
a stage. Full pipeline mechanics, including the render-eligibility gate that sits at the
crawl-to-render boundary, are in [seo-fundamentals-2026.md](references/seo-fundamentals-2026.md).

Per-stage references:

- **Stage 1 — [Crawlability](references/stage-1-crawlability.md)** — discovery vs
  retrieval as independently-failing sub-phases, the five crawl sub-stages, discovery
  mechanics (internal links, sitemap's actual guarantee, orphans, depth), retrieval
  mechanics (response codes, server response time as a crawl constraint), crawl budget
  correctly scale-qualified, the consensus-weighted issue catalog, AI crawlers as a
  crawl-stage concern with no re-index mechanism, a stage firewall listing what belongs
  to Stage 3 instead, a diagnostic decision tree, severity mapping, and a register of
  single-source claims that must be attributed or dropped.
- **Stage 2 — [Rendering](references/stage-2-rendering.md)** — the diagnostic principle
  that render failures present as indexability symptoms (usually "Crawled, currently not
  indexed"), the render-eligibility gate, render budget corrected (no 5-second wall-clock
  limit; virtual clock paused during network waits; ~52s real-time ceiling; live test more
  patient than indexing), the rendering-strategy hierarchy with Google's own stated
  preference for SSR or static over full rehydration, dynamic rendering as a deprecated
  workaround plus the vendor-bias warning, AI crawlers not rendering, the detection ladder,
  severity mapping, and an attribution register. Deep mechanics and the nine failure
  patterns remain in [javascript-seo-framework.md](references/javascript-seo-framework.md).
- **Stage 3 — [Indexability](references/stage-3-indexability.md)** — the canonicalization
  vs index-decision sub-phase split, the mandatory four-check directive verdict (with corpus
  coverage showing three of the four checks are absent from mainstream literature), the
  **GSC symptom decoder** routing each status to the stage that actually caused it, Index
  Efficiency Ratio, acceptable vs problematic `noindex`, the stage firewall, and severity
  mapping. Detailed canonical failure tables remain in the Indexability Issues section
  below; per-status detail in [gsc-indexation-states.md](references/gsc-indexation-states.md).
- **Stage 4 — [Ranking](references/stage-4-ranking.md)** — the **stage contract** rather than
  a variable list. Covers the gate (no stage 4 work while a stage 1–3 blocker is open), why
  this stage is comparative rather than binary (stages 1–3 findings can be *closed*, stage 4
  findings can only be *improved*), the five structural properties that change weighting
  (re-rankers, click signals as feedback not input, query-independent compounding,
  QDF-conditional freshness, intent mismatch over keyword optimisation), severity mapping
  capped below earlier stages, and the stage firewall. Variables themselves stay in
  [ranking-factors-checklist-2026.md](references/ranking-factors-checklist-2026.md) clusters
  5–20, [click-signals-abc-framework.md](references/click-signals-abc-framework.md) and
  [seo-fundamentals-2026.md](references/seo-fundamentals-2026.md).

## REQUIRED — Stage Verdict Contract (every audit, full-site AND single-URL)

**Every audit must return four verdicts, one per stage, in pipeline order, after a pre-check
for causes outside the pipeline (row 0). A missing stage verdict is an audit defect**, on the same non-negotiable footing as the indexability-directive
verdict below. This is what makes stage sequencing enforceable instead of advisory: an audit
that never states a rendering verdict cannot silently have skipped rendering.

| Stage | Verdict values | Minimum evidence required |
|---|---|---|
| **0 Pre-check (outside the pipeline)** | CLEAR / FOUND / NOT CHECKED | Search Console Manual actions report and Data Anomalies page read for the period. A manual action or a listed anomaly explains the loss before any stage does |
| **1 Crawlability** | PASS / FAIL / PARTIAL | `robots.txt` read; response codes across the crawl; internal-link path to money pages confirmed; sitemap cross-checked |
| **2 Rendering** | PASS / FAIL / PARTIAL | Raw-vs-rendered comparison on at least each indexable **template**; `title`, `canonical`, `meta robots`, `H1` and primary nav confirmed present in **raw** HTML |
| **3 Indexability** | PASS / FAIL / PARTIAL | The four directive checks (head `noindex`, `X-Robots-Tag`, body placement, declared-vs-Google-selected canonical); index status for money pages |
| **4 Ranking** | No pass/fail. Report relative position | Named competitors on named queries, with a diagnosed cause per finding |

**Rules:**

1. **State "clean" explicitly.** When a stage passes, say so. Silence is not a verdict, and
   a reader cannot distinguish "checked and fine" from "never looked."
2. **SKIPPED-AND-FLAGGED is a legitimate verdict, guessing is not.** When a required input
   is missing (no GSC access, no `gsc_crawled_not_indexed.csv`, no rendered crawl), record
   the stage as skipped, name the missing input, and state which findings are therefore
   unavailable. Never infer a stage verdict from a proxy.
3. **A FAIL at stage N gates stages N+1 onward.** Downstream findings may still be reported,
   but each must be marked as gated behind the upstream blocker, so nobody schedules stage 4
   work that cannot pay out.
4. **Nothing downstream is Critical while an upstream stage is FAIL.** If a money page is
   `noindex`, its title tag is not a Critical finding.
5. **Order the deliverable by stage**, not by category. A reader should be able to stop
   after stage 1 and know what to fix first.

Stage mechanics, diagnostics and severity mapping are in the four stage references above.
The cross-finding resolution procedure (stage gate → binding test → page value → outcome
type → effort) is in
[seo-audit-methodology/SKILL.md](../seo-audit-methodology/SKILL.md).

## Core Framework References

Load these references when the audit scope touches the corresponding area:

- **[SEO Fundamentals (2026)](references/seo-fundamentals-2026.md)** — Load this first for any audit. The durable reference covering how search engines actually work in 2026, indexability and canonicalization rules, internal linking principles, content strategy (cannibalization, pruning, freshness), site migrations, local SEO, schema, mobile-first indexing, and an explicit list of common SEO myths to avoid recommending (routine disavow, word-count quotas, keyword density, TF-IDF/LSI as targets, bounce rate as ranking signal, etc.).

- **[Ranking-Factors Checklist (2026)](references/ranking-factors-checklist-2026.md)** — the leak-grounded ranking-factors master checklist; walk it for technical + indexation + click-signal + NSR clusters. Sharded into 19 audit-execution clusters that mirror the auditor/skill split, so each item lands with the stage that owns it. Every audit must return a verdict on each in-scope cluster (see the mandatory-verdicts contract in [seo-audit-methodology/SKILL.md](../seo-audit-methodology/SKILL.md)); treat leaked attributes it cites as LEAK-DERIVED, not confirmed ranking weights.

- **[Robots.txt Framework for Ecommerce](references/robots-txt-ecommerce-framework.md)** — Use when auditing robots.txt, crawl budget, URL parameters, faceted navigation, product variants, or AI bot policy. Covers Shopify/WooCommerce/Magento platform specifics, the three-tool distinction (robots.txt vs noindex vs canonical), common wildcard pattern bugs, Googlebot separate-block mistakes, and a full audit checklist.

- **[JavaScript SEO Framework (2026)](references/javascript-seo-framework.md)** — Use when auditing any site that relies on JavaScript for content, navigation, or critical SEO elements (title, canonical, meta description, H1, meta robots). Covers Google's rendering pipeline, the pre-render indexability decision, AI crawler invisibility, the rendering hierarchy (SSG/SSR/ISR/Dynamic/CSR), 9 common failure patterns with detection thresholds, ecommerce-specific JS issues, testing methods, the December 2025 docs clarification on non-200 rendering, and the **on-demand Raw vs Rendered HTML Diff Protocol** for single-URL diagnostics (use whenever a high-severity finding needs live verification, when a page is "Crawled — currently not indexed" without an obvious cause, or when a redirect/canonical target's authoritative state is in question).

- **[Click Signals & ABC Framework](references/click-signals-abc-framework.md)** — Use when an audit surfaces low CTR, high bounce-back behavior, or any recommendation that touches user-engagement signals. Covers Google's NavBoost (13-month memory window), Glue, RankEmbedBERT, the documented click attributes from the May 2024 API leak (goodClicks/badClicks/lastLongestClicks), the ABC mental model (Anchors/Body/Clicks), the 3-step practitioner workflow (earn the click → prove usefulness → prove satisfaction), and a recommendation translation table mapping common surface metrics to underlying-cause fixes. Also: what NOT to recommend (click farms, manipulation tactics, "improve dwell time" framed as a tactical lever).

## Issue Severity Framework

**Severity is derived from stage position plus the binding test, not assigned by feel.**
Two inputs decide it:

1. **Which stage does the finding sit at?** Earlier stage means higher severity, because
   everything downstream inherits the failure.
2. **Is it binding?** Can you name the specific loss it causes on this site? An absence
   with no nameable loss is not Critical no matter how many URLs it touches.

### Critical
A **binding** failure at Crawlability, Rendering, or Indexability that affects money pages
or a whole template:

- Googlebot cannot reach the content (robots.txt block, template-wide 5xx)
- Primary content or navigation absent from the **raw** HTML
- `canonical`, `meta robots` or `title` injected by JavaScript, so the render-eligibility
  gate never sees them
- Money pages carrying `noindex` from any of the three sources (head, header, or believed-
  excluded-but-actually-indexable body placement)
- Canonical on money pages pointing at a wrong, noindexed, 4xx or redirecting URL
- Revenue pages absent from the index with no directive explaining it

### High
A binding stage 1–3 failure on non-money pages or a subset, **or** a binding stage 4
failure on money pages:

- Broken links inside primary navigation, sitemap missing published money pages
- Content gated behind click, hover or scroll so it never enters the rendered DOM
- Duplicate clusters with no canonical declared, where a money page is in the cluster
- Slow server response measurably constraining crawl **on a site large enough for it to
  bind**
- Thin content on pages that could realistically compete

### Medium
Binding stage 4 issues on non-critical pages, or stage 1–3 issues that are real but not
costing anything today:

- Redirect chains of 3+ hops, sitemaps containing redirects or 404s
- Parameter and faceted variants indexed alongside canonicals
- Core Web Vitals below threshold on non-revenue templates
- Index bloat from archive and tag URLs, **at a scale where it binds**

### Low
Non-binding absences, cosmetic inconsistencies, and hygiene with no nameable loss:

- Missing self-referencing canonicals where no duplication exists
- Missing H1s on pages already ranking for their target terms
- Cosmetic redirects that already resolve correctly

### Not a finding
Deliberate `noindex` on utility pages, CSR on authenticated app routes, ad-tracking 302s,
shared template blocks flagged as duplication, and 429s that were crawl-rate artifacts.
Reporting these inflates the deliverable and costs credibility.

> **Deleted from this framework, deliberately:** "reduces crawl efficiency" was previously
> listed as **High**. It is not, on the overwhelming majority of sites. Crawl efficiency is
> Infrastructure Hygiene and it only binds at large scale or heavy churn. Rendering was
> previously absent from every tier, which is how render failures went unranked entirely.

---

## Indexability Issues

### REQUIRED — Indexability-Directive Verdict (every audit, full-site AND single-URL)

Every audit MUST return an explicit verdict on indexability directives — no exceptions. This runs on a **full-site crawl** (read the directive columns across the crawl) and on a **single-URL audit** alike (for one URL: `curl -I <url>` for the response headers, and fetch + inspect the `<head>` for robots/canonical directives). **A missing indexability verdict is an audit defect** — the same mandatory-verdict contract the ranking-factors checklist applies to every in-scope cluster (see [seo-audit-methodology/SKILL.md](../seo-audit-methodology/SKILL.md)). When indexability is clean, say so explicitly; never silently omit it.

The verdict must cover all four checks:

1. **Meta robots `noindex` (head-level).** Is the page set to `noindex`/`none` via a `<meta name="robots">` in the `<head>`? Confirm whether the exclusion is intentional (see Acceptable vs Problematic noindex below) or accidental on a page meant to rank.

2. **`X-Robots-Tag` HTTP header `noindex`.** Check the **response header**, not just the HTML. A page can be noindexed via the header with no visible meta tag — invisible in "view source." Always inspect headers directly (`curl -I <url>`, or DevTools Network panel); cross-reference the `X-Robots-Tag` column against `meta_robots` when a crawl is present. See "X-Robots-Tag vs Meta Robots Mismatch" below for root causes.

3. **`noindex` placed in the BODY (invalid — reports as a false verdict either way).** Google only honours robots directives in the `<head>`; a `noindex` in the `<body>` is **ignored**. This cuts both ways and both are defects to flag: an owner who put `noindex` in the body *thinks* a page is excluded when it is actually fully indexable — and, conversely, a page the owner *believes* is safely noindexed may be leaking into the index. Verify placement, not just presence, of every noindex directive.

4. **Canonical: declared vs Google-selected divergence.** Compare the page's **declared** canonical (rel=canonical in the head/header) against **Google's selected** canonical (GSC URL Inspection). Divergence means Google is overriding the site's choice — index confusion, equity landing on the wrong URL, or a duplicate-cluster problem. Report the declared value, the Google-selected value, and the gap.

State each of the four as a discrete finding with its source (crawl column, response header, live head inspection, or GSC URL Inspection). For single-URL audits the same four verdicts are required — the input is one live fetch + header check instead of a crawl export.

### Canonical Tag Problems

**Critical Issues:**
| Issue | Impact | Fix |
|-------|--------|-----|
| Canonical Outside of Head | Not recognized by search engines | Move to `<head>` section |
| Canonical Points to HTTP Version | Protocol mismatch confuses canonicalization | Update to HTTPS |
| Meta Robots Found Outside Head | Directive may not be recognized | Move to `<head>` section |

**High Issues:**
| Issue | Impact | Fix |
|-------|--------|-----|
| Mismatched Canonical in HTML and HTTP Header | Conflicting signals | Use single method |
| Multiple Mismatched Canonical Tags | Search engine picks random one | Keep single canonical |
| Canonical Points to Noindex URL | Circular contradiction | Point to indexable page |
| Canonical Points to 4XX/5XX URL | Dead end canonicalization | Point to working page |
| Canonical Loop/Chain | Infinite loop or extra hops | Point to final destination |

**Medium Issues:**
| Issue | Impact | Fix |
|-------|--------|-----|
| Canonical is Relative URL | May resolve incorrectly | Use absolute URL |
| Canonical Points to Redirect | Unnecessary hop | Point to final destination |

### Robots Directives Understanding

**noindex vs nofollow:**
- `noindex`: Don't show this page in search results
- `nofollow`: Don't follow links on this page
- `noindex,follow`: Hide page but crawl its links (common for pagination)
- `noindex,nofollow`: Complete exclusion

**Acceptable noindex usage:**
- Thank you/confirmation pages
- Internal search results
- User account pages
- Duplicate filter/sort pages

**Problematic noindex:**
- Valuable content pages
- Product/service pages
- Blog posts meant for organic traffic
- Category/collection pages with unique content

### X-Robots-Tag vs Meta Robots Mismatch

Google treats a `noindex` value in the `X-Robots-Tag` HTTP response header identically to a `noindex` meta tag in the HTML — but the header is applied server-side, at a CDN, load balancer, or middleware layer, and is **invisible when viewing page source**. This makes it the most commonly missed source of accidental noindex: a page can look completely fine in "view source" (no noindex meta tag) while still being fully excluded from the index because of a header no one thought to check.

**Diagnostic method:** Don't rely on view-source alone. Check response headers directly — `curl -I <url>`, or the Network panel in browser DevTools — for any page suspected of an indexing problem with no visible cause. If a Screaming Frog crawl is available, cross-reference the `X-Robots-Tag` column against the `meta_robots` column: any page where the header carries noindex but the HTML meta tag does not is the dangerous, invisible case.

**Common root causes:** a CDN rule applied to a URL pattern that's broader than intended, a reverse-proxy config left over from a staging setup, a WAF rule, or an app-level middleware rule applied by content type or path prefix.

---

## GSC Index Coverage — Crawled / Discovered Not Indexed

Screaming Frog crawl data can only ever show what a page's HTML and HTTP response look like — it cannot show Google's own decision NOT to index a page despite no technical block existing. Two GSC "Page indexing" report statuses fall entirely outside what a crawl can reveal:

**Crawled — currently not indexed.** Google crawled the page but chose not to index it. This is not a verdict on its own: Google's help calls it common and not necessarily an issue. Common drivers: thin or low-value content, near-duplication that doesn't fit a formal duplicate category, weak internal + external signals combined, or rendering issues leaving the page looking empty (including robots.txt blocking the CSS or JavaScript the page needs to render). **Rule out rendering before calling it content:** run Test live URL and read the rendered HTML and screenshot, per the symptom decoder in [stage-3-indexability.md](references/stage-3-indexability.md). If the render is incomplete, the fix is technical (Stage 2). If the render is complete, content depth, originality and internal linking are what move this status; when many pages show it with no technical cause, read it as a site-quality signal. Re-submitting for indexing without a change does not help.

**Discovered — currently not indexed.** Google knows the URL exists but hasn't crawled it yet (no last-crawl date recorded). Usually a crawl-budget or perceived-low-value signal: rationing on large sites, the page buried many clicks from the homepage with weak internal linking, or mass low-value URL generation (faceted nav, parameter explosion) competing for the same crawl budget. Unlike "Crawled — not indexed", this status often resolves through internal-linking and crawl-budget fixes alone, without any content rewrite.

Both statuses require a manual export from GSC's Page indexing report (Google has no bulk Index Coverage API) since they are Google's own crawl/index decisions, invisible to any other data source.

---

## Redirect Issues

### Redirect Chain Analysis

| Hops | Impact | Recommendation |
|------|--------|----------------|
| 1 | Acceptable | Normal operation |
| 2 | Minor delay | Optimize if possible |
| 3+ | Significant | Fix required |
| 5+ | Critical | Immediate fix |

### Redirect Types

| Code | Type | Use Case | SEO Impact |
|------|------|----------|------------|
| 301 | Permanent | URL changed forever | Passes ~90%+ equity |
| 302 | Temporary | Short-term change | May not pass equity |
| 307/308 | HTTP/1.1 equivalents | Same as 302/301 | Same as above |
| Meta Refresh | Soft redirect | Avoid for SEO | Poor practice |
| JavaScript | Client-side | Last resort only | Unreliable |

### Common Redirect Problems

| Problem | Issue | Fix |
|---------|-------|-----|
| Redirect Loop | A→B→A | Break the loop |
| Trailing Slash Mismatch | /page redirects to /page/ | Pick one, be consistent |
| HTTP to HTTPS Chain | http→https→www | Single redirect http→final |
| Redirect to 4XX/5XX | Redirect leads nowhere | Update destination |

### Redirect Keep / Remove Decision Tree

A URL that GSC reports under **"Page with redirect"** is usually benign — Google indexes the destination, not the source. The mistake is treating every reported redirect as cleanup work. Redirects are keep-by-default; only a specific subset should be touched. Decide per source URL:

**Keep the redirect (do NOT remove) when any of these is true:**
- **It's structural / rule-based** — HTTP→HTTPS, `www`↔non-`www`, or trailing-slash normalisation. These are consistency rules, not cruft. (A cosmetic 301 that already resolves correctly — e.g. singular→plural, trailing-slash variant — belongs on a "leave as-is" list, never an active correction list. Per `.claude/rules/audit-workflow.md` Rule 12c.)
- **The source URL has external backlinks** — the redirect preserves that link equity. Leave it in place indefinitely.
- **It still passes traffic.**

**Fix the linking source (not the redirect) when:**
- The redirect is **active on the crawl** — i.e. an internal link or sitemap entry still points to the redirecting source. Update the link/sitemap entry to point directly to the final destination (Screaming Frog: select the redirecting URL → Inlinks tab → find and fix the linking page). This is the common, high-value cleanup.

**Remove the redirect rule only when ALL are true:**
- Non-structural, **no external backlinks**, and **no traffic**. Then the developer can drop the server rule, shrinking the reported count. Low priority.

**Address immediately when:**
- The redirect points to a **spam / irrelevant / hijacked destination** — a real problem hiding under a benign status.

**Always live-verify first.** GSC's redirect list is not 100% accurate: it reports source URLs that no longer redirect and far more than exist live (redirect memory persists months→years because server rules don't expire). Bulk-check exported URLs against live status (e.g. httpstatus.io, or `curl -I`) before acting, and **verify every proposed destination URL** per `.claude/rules/audit-workflow.md` Rule 12 — a wrong target becomes a 301-cemented mistake the moment a developer implements it. The full per-state context is in [references/gsc-indexation-states.md](references/gsc-indexation-states.md).

---

## 4xx Error Disambiguation (401/403/429)

Not all 4xx status codes mean the same thing for indexability, and treating them identically produces false work items.

**401 Unauthorized** — the page sits behind authentication Googlebot cannot pass. If intentional (staging, member content, paywall), no action needed beyond keeping it out of the sitemap. If accidental, remove the auth requirement or scope it to allow Googlebot through.

**403 Forbidden — requires disambiguation before recommending a fix.** A 403 returned to a Screaming Frog crawl does not prove Googlebot is also blocked. WAFs, bot-protection rules, and rate-limiters frequently allow Googlebot's IP ranges and user-agent while blocking a generic crawler. Before recommending any WAF/firewall change, verify via GSC URL Inspection's live test (uses Google's own fetch) or check Search Console coverage status for the URL. Never recommend loosening bot-protection based on a third-party crawl's 403 alone.

**429 Too Many Requests — a crawl-rate artifact, not a confirmed issue.** This almost always means the crawler exceeded a rate limit during the crawl itself, not a real problem with the URL. Re-crawl at a slower rate to get the real status code before including these URLs in any correction or cleanup list. Treating 429s as confirmed problems produces false work items — this exact mistake has occurred on real client audits in this project (hundreds of URLs miscategorized as broken when they were simply rate-limited during the crawl).

---

## Core Web Vitals

### Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP (Largest Contentful Paint) | ≤2.5s | 2.5s - 4.0s | >4.0s |
| INP (Interaction to Next Paint) | ≤200ms | 200ms - 500ms | >500ms |
| CLS (Cumulative Layout Shift) | ≤0.1 | 0.1 - 0.25 | >0.25 |

### LCP Optimization Priorities

1. Reduce TTFB (server optimization, CDN)
2. Eliminate render-blocking CSS/JS
3. Preload LCP image/resource
4. Use efficient image formats (WebP, AVIF)
5. Implement critical CSS inlining

### INP Optimization

- Break up long tasks (yield to main thread)
- Remove unused JavaScript
- Defer non-critical JavaScript
- Reduce DOM size and complexity

### CLS Fixes

- Always specify width/height on images
- Reserve space for dynamic content
- Use font-display: swap with fallback fonts
- Pre-allocate space for ads/embeds

---

## How Technical Variables Interconnect

### Crawlability Chain
```
Robots.txt blocks → Can't crawl → Can't index → No rankings
DNS/Server issues → Slow/no response → Reduced crawl frequency
Redirect chains → Lost PageRank → Reduced authority → Lower rankings
```

**Important nuance — robots.txt is a crawl directive, not an index directive.** A URL blocked in robots.txt CAN still appear in search results if linked externally (as a title-less SERP entry). Combining `robots.txt Disallow` with `noindex` on the same URL is a trap — Google can't see the noindex if crawling is blocked. See [Robots.txt Framework](references/robots-txt-ecommerce-framework.md) for the full three-tool decision matrix.

### Indexability Chain
```
Noindex directive → Page excluded → No organic traffic
Canonical errors → Wrong page indexed → Traffic to wrong URL
Duplicate content → Index confusion → Signal dilution
```

### Performance Chain
```
Slow TTFB → Poor LCP → Failed Core Web Vitals → Ranking suppression
Large images → High bandwidth → Mobile issues → Poor engagement
Render-blocking → Slow FCP → High bounce rate → Negative user signals
```

---

## Prioritization Decision Tree

> **Previously this tree opened at "is it blocking indexation?"**, which made indexation the
> first gate and skipped crawlability and rendering entirely. That is the same stage-order
> error the pipeline section above exists to prevent. Crawl and render come first.

Walk in order. The first question that separates two findings decides which ships first.

1. **Can the crawler reach it?** (Stage 1)
   - Blocked, 5xx, or no crawl path to a money page → **Critical**, stop here
   - Clean, or affects only non-money pages → continue

2. **Does the content survive rendering?** (Stage 2)
   - Primary content, nav, or a directive absent from **raw** HTML on a money page →
     **Critical**, stop here
   - Continue

3. **Can and will Google index it?** (Stage 3)
   - `noindex` from any source, or canonical failure, on a money page → **Critical**
   - Continue

4. **Is the finding binding?** Name the specific loss it causes on this site.
   - Cannot name one → **Low / not a finding.** Do not promote it on volume
   - Can name one → continue

5. **Does the affected set contain money pages?**
   - Yes → severity holds
   - No, and they are utility or non-SEO URLs → drop them from the count first
     (audit-workflow Rule 7), then re-ask

6. **Scope:** site-wide or template-level, or a handful of pages?
   - Template-level binds harder than an equal count of scattered pages, because it will
     recur on every new page built from that template

7. **Outcome type**, within the same stage: Ranking Lever → Risk Mitigation → UX →
   Infrastructure Hygiene

8. **Effort** breaks any remaining tie. Batch same-stage, same-outcome fixes into one line
   item rather than listing them individually.

Full procedure with a worked example (50 missing H1s vs 20 missing canonicals) is in
[seo-audit-methodology/SKILL.md § The resolution procedure](../seo-audit-methodology/SKILL.md).

---

## Quick Wins Identification

**High Impact, Low Effort:**
- Fixing broken canonical tags
- Removing accidental noindex
- Fixing robots.txt blocks on resources
- Adding missing image dimensions
- Enabling compression

**High Impact, Medium Effort:**
- Consolidating redirect chains
- Implementing lazy loading
- Minifying assets
- Preloading LCP resources

**High Impact, High Effort:**
- Server-side rendering for JS content
- Complete HTTPS migration
- Site architecture restructuring
- CDN implementation
