# Robots.txt Framework for Ecommerce (+ General Sites)

**Purpose:** Internal framework for auditing and recommending robots.txt + crawl/indexation strategy across ecommerce and non-ecommerce sites. Covers the three tools (robots.txt / noindex / canonical), platform-specific implementation, AI bot policy, and decision matrices by store size and platform.

**Scope:** Used during technical SEO audits when evaluating crawl budget, URL parameters, faceted navigation, variant handling, and indexation strategy.

---

## Pipeline stage assignment

> **Stage 1 — Crawlability, primarily.** robots.txt is a *crawl* directive. See
> [stage-1-crawlability.md](stage-1-crawlability.md). But this file also carries stage-3
> decisions, and mixing them is the single most common error in this area.

| Section | Stage |
|---|---|
| 1. The Three Tools (robots.txt vs `noindex` vs canonical) | **1 + 3** — the whole point of the section is keeping them apart |
| 2–3. Why it matters, baseline rules | **1** |
| 4. Wildcard pattern trap | **1** |
| 5. Googlebot separate-block mistake | **1** |
| 6. Platform-specific implementation | **1** |
| 7. Variant URL decision framework (block **or noindex**) | **1** for blocking, **3** for `noindex` and canonical-child segmentation |
| 8. Decision matrix by store size | **1**, and scale-gated (see below) |
| 9. AI bot policy | **1** |
| 10. Template | **1** |

**The trap this ordering prevents:** `Disallow` + `noindex` on the same URL is
self-defeating, because Google cannot see the `noindex` if crawling is blocked. Blocking is
stage 1; excluding from the index is stage 3. Decide which outcome you actually want before
choosing the tool.

**Scale gate on the crawl-budget rationale in this file.** Crawl budget is a real constraint
at large scale or heavy churn and effectively a non-issue on small or new sites. Where a
recommendation here is justified only by crawl-budget efficiency, it is Infrastructure
Hygiene, and on a small site it may not be worth doing at all. Never state crawl-budget
savings as the expected benefit on a small or new build.

## 1. The Three Tools — Never Confuse Them

| Tool | Controls | Google Treats As | Blocks Crawling? | Blocks Indexing? |
|---|---|---|---|---|
| `robots.txt Disallow` | Crawling | Directive (usually respected) | Yes | No — page can still index if linked externally |
| `noindex` meta tag / X-Robots-Tag | Indexing | Directive | No | Yes |
| `rel="canonical"` | Indexation preference | **Hint** (can be ignored) | No | No — just consolidates signals |

**The Combination Trap (critical):** NEVER block a URL in robots.txt AND add noindex on the same URL. Google's own guidance: *"For the `noindex` rule to be effective, the page or resource must not be blocked by a robots.txt file, and it has to be otherwise accessible to the crawler."* If Google can't crawl the page, it can't see the noindex — and the URL can still appear in SERPs as a title-less, blocked result if discovered externally.

**Correct pairings:**
- **Crawl trap, no external links:** robots.txt Disallow only
- **Need to suppress from SERPs:** noindex only (allow crawling)
- **Duplicate content with equity to preserve:** rel=canonical only

---

## 2. Why Robots.txt Matters for Ecommerce

Ecommerce sites are the most common crawl budget disaster zones. Google's own Gary Illyes has confirmed parameter-generated URLs (variants, filters, sort orders) cause "crawl budget wastage." Faceted navigation and session IDs are the #1 category of low-value URLs Google flags as harmful to crawling/indexing.

Scale example: 200 products × 5 colors × 8 sizes = **8,000 variant URLs** before filters, sorts, or pagination. Enterprise catalogs can hit millions of crawlable-but-useless URLs.

Empirical benchmarks (from audits):
- Product-variant cannibalization can consume a **substantial share of crawl activity** on
  large faceted catalogs. ⚠️ **An earlier version of this line stated "18–32% of crawl
  budget" with no source. That figure is unverified and must not be repeated to a client or
  in a deliverable.** Measure the actual share per site from GSC Crawl Stats (crawl requests
  by response and by URL pattern) or server logs, and cite that instead. Per
  `~/.claude/rules/anthropic-patterns/no-unverified-claims.md`, an unsourced percentage in a
  client deliverable is a defect regardless of how plausible it sounds.
- Causes **12–28% impression leakage** on head commercial terms
- Canonical tags alone resolve only **55–70% of duplicate clustering** at enterprise scale — the rest requires explicit URL governance

### Server-cost benefit (often underweighted)

Aggressive bot crawling of low-value parameter URLs costs real hosting money on metered infrastructure: variable hosting tiers, CDN egress fees, application-server CPU on rendered routes, and log storage volume. For ecommerce clients with high-cardinality faceted nav (color × size × brand × price-range filter combinations), the hosting savings from blocking these patterns can be the largest single benefit of the fix — sometimes exceeding the SEO benefit in dollar terms.

When proposing faceted-nav cleanup or filter-URL blocking, raise this with the client explicitly. Two reasons:

1. **It frames the fix correctly per the Expected Outcome Classification.** Crawl-waste cleanup is Infrastructure Hygiene, not a Ranking Lever. Selling it on its real benefits (cleaner architecture + lower hosting cost + protected crawl budget) is more honest than implying ranking movement.
2. **It often unblocks the budget.** Clients who hesitate at "SEO infrastructure work" approve "cut hosting bill" immediately. Same fix, different conversation.

Pull the client's hosting/CDN bill if they'll share it. Compare crawl-pattern data (Search Console crawl stats, log files if available) against the bot-driven request volume. If parameter URLs account for 30%+ of bot requests, the fix has a tangible infrastructure-cost case.

---

## 3. Baseline Rules for ALL Ecommerce Sites

These apply regardless of platform or store size:

```
User-agent: *
Disallow: /admin/
Disallow: /cart/
Disallow: /checkout/
Disallow: /account/
Disallow: /orders/
Disallow: /search?
Sitemap: https://yourstore.com/sitemap.xml
```

**Why each line:**
- `/admin/`, `/account/`, `/orders/` — user-session, zero SEO value
- `/cart/`, `/checkout/` — transactional state, never rank
- `/search?` — internal search results create infinite thin content traps
- Sitemap declaration — aids canonical URL discovery

---

## 4. The Wildcard Pattern Trap (Common Audit Finding)

**Wrong pattern (frequently seen in published guides):**
```
Disallow: /*?variant=*
```

Why it fails: The `?` in robots.txt is literal, not a wildcard. This pattern only matches when `variant=` is the FIRST query parameter. URLs like `/products/shoe?color=red&variant=12345` **will NOT be blocked** because `variant=` is preceded by `&`.

**Correct pattern (covers all positions):**
```
Disallow: /*variant=
```

Or, for explicit coverage:
```
Disallow: /*?variant=
Disallow: /*&variant=
```

Apply this rule to ALL parameter-blocking directives — `sort_by`, `filter`, `utm_`, etc. Audit any robots.txt using `/*?param=*` and rewrite to `/*param=`.

---

## 5. The Googlebot Separate-Block Mistake

**Wrong (seen in many published templates):**
```
User-agent: Googlebot
Disallow:

User-agent: *
Disallow: /cart/
Disallow: /variant=
```

**Why it's broken:** Googlebot reads ONLY the most specific matching group. The empty `Disallow:` for Googlebot means Googlebot ignores the `User-agent: *` rules entirely — fully unblocking Googlebot while only blocking other bots. This is the OPPOSITE of the intended behavior.

**Correct approaches:**
- Use `User-agent: *` only (simplest, covers Google)
- OR explicitly repeat rules under `User-agent: Googlebot`
- OR use per-bot overrides only when you genuinely want different rules for Googlebot vs. others

Audit rule: If a client's robots.txt has a `Googlebot` block with `Disallow:` (empty), flag it — their Googlebot access is unrestricted regardless of rules below.

---

## 6. Platform-Specific Implementation

### Shopify

**Critical:** You cannot edit robots.txt directly. Shopify generates it dynamically via a Liquid template.

**To customize:**
1. Online Store → Themes → Edit code
2. Create `templates/robots.txt.liquid`
3. Use Shopify's `robots` Liquid object to keep their maintained defaults, then append custom rules

**Correct Shopify template:**
```liquid
{%- for group in robots.default_groups -%}
  {{- group.user_agent }}
  {%- for rule in group.rules -%}
    {{ rule }}
  {%- endfor -%}

  {%- if group.user_agent.value == '*' -%}
    {{ 'Disallow: /*variant=' }}
    {{ 'Disallow: /*sort_by=' }}
    {{ 'Disallow: /*filter' }}
    {{ 'Disallow: /*?q=' }}
    {{ 'Disallow: /collections/*+*' }}
    {{ 'Disallow: /collections/*%2B*' }}
    {{ 'Disallow: /collections/all' }}
  {%- endif -%}

  {%- if group.sitemap != blank -%}
    {{ group.sitemap }}
  {%- endif -%}
{%- endfor -%}
```

**Shopify-specific notes:**
- Variant URLs use numeric IDs (`?variant=12345678`) with zero keyword semantic value
- Shopify automatically adds `rel=canonical` to variant pages pointing to main product URL — this is built-in, don't remove it
- Collection + tag combinations (`/collections/mens-shoes/red+size-10`) multiply faster than variants — block with `/collections/*+*` and URL-encoded `*%2B*`
- `/collections/all` is a crawl trap — blocks the aggregate page, not individual collections
- Shopify Markets adds `?currency=USD` type parameters — may need separate handling

### WooCommerce

- No built-in canonical management for variations — you must add canonicals via Yoast/RankMath AND block variant URLs
- Block: `/*?orderby=`, `/*?filter_`, `/*?add-to-cart=`, `/*?remove_item=`
- Internal search: `/?s=` (different from Shopify's `/search?`)

### Magento

- Faceted nav is the dominant crawl budget killer, bigger than variants
- Block layered nav filters: `/*?p=`, `/*?dir=`, `/*?limit=`, `/*?mode=`, `/*?price=`
- Magento 2 has built-in canonical for category/product variations — verify it's enabled

### BigCommerce

- Parameter patterns vary by theme
- Key blocks: `/*?sort=`, `/*?page=` (if not using proper pagination), `/*?limit=`

### Custom / Headless

- You own everything — implement full URL parameter governance
- Typically need programmatic canonical management at the framework level

---

## 7. Variant URL Decision Framework

### Block (or noindex) variants when:
- URL uses numeric/opaque IDs with no semantic keyword value (Shopify's `?variant=12345`)
- Variant page content is identical to main product (title, images, copy)
- Store has thousands of variants creating measurable index bloat
- Enterprise scale where crawl budget is a measurable constraint

### Allow variants when:
- Specific color/size combinations have their own search demand (verified via keyword research — e.g., "navy blue slim fit chinos size 32")
- Each variant has UNIQUE content: distinct title, meta, images, copy
- Store is small with limited total URL count
- Variants have external backlinks (blocking causes title-less SERP entries)

### Path-based variants vs. parameter variants

If variants genuinely deserve separate indexation, use **descriptive path segments** not query parameters:

- ✅ `/products/iphone-16-pro-max-1tb-titanium-black` (indexable, keyword-rich)
- ❌ `/products/iphone-16-pro-max?variant=39474772910234` (numeric, zero semantic value)

This is fundamentally different from Shopify's default `?variant=` system. If a client needs indexable variants, the correct strategy is separate products (not variants) OR path-based structured URLs — NOT exposing the `?variant=` parameter.

### Canonical-child segmentation → value-gate → block (the "Alternative page with proper canonical" workflow)

When GSC's Page Indexing report shows a large and growing **"Alternative page with proper canonical tag"** count on a small/medium site, the canonicals are doing their job (Google is correctly excluding the variants) but the site is still spending crawl budget letting Google reach worthless parameter URLs in the first place. The fix is to stop Google reaching them — but **only after proving no indexed, traffic-earning URL depends on the path.** Never block a parameter blind.

The workflow (Foley Carter, GSC Lesson 5):

1. **Export** the "Alternative page with proper canonical tag" URL list from GSC.
2. **Segment by pattern.** In a sheet: freeze the header, add a filter, then split parameter-driven from static — `text contains "?"` → parameter tab; `does not contain "?"` → static tab. Break out each recurring parameter path into its own group (`?add-to-cart`, `?add_to_wishlist`, `?orderby=`, `?page=`, `?product=`, faceted `?color=`/`?size=`, session/tracking params). Remove each segmented group from the origin sheet as you go so nothing is double-counted.
3. **Value-gate before blocking (mandatory).** For each parameter token, GSC → Performance → **Search** → last 16 months → search the token (e.g. `add_to_wishlist`, `product=`). Only if clicks/impressions are **~zero** is it safe to block. This is the gate the rest of section 7 assumes — make it explicit.
4. **Dependency check (hard prerequisite).** Confirm that **no indexed URL the site actually wants ranked uses that path**. A parameter that a canonical, traffic-earning page depends on must never be blocked. (This is the same class of mistake as blocking `Disallow: /*?` when faceted pages carry real search demand — see §7 "Allow variants when.")
5. **Block at the source** so Google never reaches the variant to classify it: `Disallow: *add_to_wishlist` (etc.), added to the generic template in §10.

**When to prefer canonical-only (do nothing):** on small sites with few variants, or where the variants carry backlinks/traffic, leave the canonical to handle it — "Alternative page with proper canonical" is an expected, benign state (see [gsc-indexation-states.md](gsc-indexation-states.md)), not an error to chase. Blocking is warranted only when the count is large, growing, and value-gated to zero.

**Crawl-side cross-check (Screaming Frog):** Overview → Canonicals → "Contains canonical" / "Self-referencing." An all-unique-page site should be all self-referencing; canonical *children* in the crawl are the live-linked variants worth segmenting. Note GSC may list canonicalized URLs the crawl doesn't — those are Google's memory of past parameters, not live links, and don't need blocking.

---

## 8. Decision Matrix by Store Size + Platform

| Scenario | Recommended Approach |
|---|---|
| Shopify, <50 products, <500 variants | Rely on Shopify's automatic canonicals. No custom robots.txt needed. |
| Shopify, 50–500 products, 500–10K variants | `robots.txt.liquid` + `Disallow: /*variant=`. Keep sitemap clean. |
| Shopify, 500+ products, 10K+ variants | `robots.txt.liquid` full param block + verify canonicals + exclude variants from sitemap + monitor GSC Coverage weekly |
| WooCommerce, any size | Block variant/filter parameters + install Yoast/RankMath + enforce canonicals |
| Magento, any size | Faceted nav governance is priority #1 — block layered nav parameters aggressively |
| Custom/headless | Full programmatic URL governance — robots.txt + canonical + sitemap all managed in code |

---

## 9. AI Bot Policy (2026 Addition)

Ecommerce sites in 2026 must have an explicit policy on LLM crawlers. These are NOT search engine bots and do NOT drive traffic (yet). Decision factors:

**Consider BLOCKING** if:
- Concerned about product catalog / pricing / description theft for LLM training
- Competitors' AI-generated product pages could use your copy
- Brand positioning depends on exclusive content (luxury, premium)

**Consider ALLOWING** if:
- Want visibility in ChatGPT shopping, Perplexity shopping, Claude recommendations
- Brand wants to be referenced as an authority in conversational AI

**Major AI bots to decide on (2026):**
```
User-agent: GPTBot              # OpenAI training
User-agent: OAI-SearchBot       # ChatGPT search results
User-agent: ChatGPT-User        # ChatGPT live browsing
User-agent: ClaudeBot           # Anthropic training
User-agent: Claude-Web          # Claude live browsing
User-agent: PerplexityBot       # Perplexity training + search
User-agent: Google-Extended     # Bard/Gemini training (separate from Googlebot)
User-agent: Applebot-Extended   # Apple Intelligence training
User-agent: CCBot               # Common Crawl (used by many LLMs)
User-agent: Meta-ExternalAgent  # Meta AI
User-agent: Amazonbot           # Amazon Alexa/AI
```

**Recommended balanced policy for most ecommerce clients:**
- Allow: `OAI-SearchBot`, `ChatGPT-User`, `Claude-Web`, `PerplexityBot` (live search = potential traffic)
- Block: `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot` (training only = no traffic benefit, catalog theft risk)

Discuss with each client — there is no single right answer.

---

## 10. Complete Ecommerce robots.txt Template (Generic)

For non-Shopify sites, or as a reference for what Shopify's Liquid template should output:

```
# Baseline protected areas
User-agent: *
Disallow: /admin/
Disallow: /cart/
Disallow: /checkout/
Disallow: /account/
Disallow: /orders/
Disallow: /search?

# Product variants (numeric IDs, no SEO value)
Disallow: /*variant=

# Faceted navigation + filters
Disallow: /*sort_by=
Disallow: /*filter
Disallow: /*orderby=
Disallow: /*?pf

# Session + tracking parameters
Disallow: /*SID=
Disallow: /*utm_
Disallow: /*?ref=
Disallow: /*gclid=
Disallow: /*fbclid=

# Thin/technical pages
Disallow: /*.atom
Disallow: /*.oembed
Disallow: /blogs/*/tagged/*
Disallow: /collections/all

# Shopify-specific collection + tag combinations
Disallow: /collections/*+*
Disallow: /collections/*%2B*

# LLM training bots (block if catalog protection matters)
User-agent: GPTBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: CCBot
Disallow: /

Sitemap: https://yourstore.com/sitemap.xml
```

---

## 11. Non-Ecommerce Sites (Local Service, SaaS, Content)

The framework simplifies for non-ecommerce sites:

### Local Service Sites (IHS properties: Beehive, Comfort, SameDay, Superior)
```
User-agent: *
Disallow: /wp-admin/
Disallow: /wp-login.php
Disallow: /?s=
Disallow: /search/
Disallow: /*?utm_
Disallow: /*?gclid=
Disallow: /*?fbclid=

Sitemap: https://example.com/sitemap.xml
```

Service sites usually don't need aggressive parameter blocking — they have fewer URLs and less crawl budget pressure. Focus on:
- Wordpress admin paths
- Internal search
- UTM/tracking parameters (dilute page signals)
- AI bots decision per client

### SaaS / Content Sites
- Block: `/app/`, `/login/`, `/signup/`, `/dashboard/`, `/api/` (if not meant for public indexing)
- Allow: `/blog/`, `/resources/`, `/docs/`, marketing pages
- Internal search: always block

---

## 12. Audit Checklist

Run this checklist on every client's robots.txt during audits:

**Pre-audit data collection:**
- [ ] Pull current robots.txt from production
- [ ] Pull robots.txt from staging (if different)
- [ ] Check GSC Coverage report: "Indexed, though blocked by robots.txt" count
- [ ] Check GSC Coverage report: "Duplicate, Google chose different canonical than user" count
- [ ] Pull XML sitemap, verify no blocked URLs are submitted
- [ ] Check GSC Domain property (regex filter) for leaked staging/dev/UAT subdomains — see Section 14

**Pattern audit:**
- [ ] Flag any `/*?param=*` patterns — rewrite to `/*param=`
- [ ] Flag any separate `Googlebot` block with empty Disallow — fix by consolidating
- [ ] Flag any URL that's both robots.txt-blocked AND has noindex — break the trap
- [ ] Flag any URL in sitemap that's disallowed — remove from sitemap

**Platform-specific audit:**
- [ ] Shopify: confirm `robots.txt.liquid` uses `robots.default_groups` loop (not standalone rules)
- [ ] Shopify: verify `?variant=` is blocked
- [ ] Shopify: verify `/collections/*+*` and `/collections/*%2B*` blocked
- [ ] WooCommerce: verify Yoast/RankMath canonicals are enabled
- [ ] Magento: verify faceted nav parameters blocked

**AI bot policy:**
- [ ] Document current AI bot stance (block/allow/unspecified)
- [ ] Discuss with client their preference
- [ ] Implement chosen policy explicitly

**Post-implementation monitoring:**
- [ ] 2 weeks: GSC Coverage — "Indexed, though blocked" should decrease
- [ ] 4 weeks: GSC Crawl stats — crawl requests should redistribute to high-value URLs
- [ ] 8 weeks: Full-site recrawl to measure crawl budget efficiency change

---

## 13. Common Pitfalls to Flag During Audits

1. **Robots.txt blocking CSS/JS resources** — Google needs to render pages to evaluate them. Ensure `/wp-content/`, `/assets/`, `/_next/static/`, etc. are NOT blocked.
2. **Blocking legitimate product URLs with overly broad wildcards** — always test patterns on real URLs before deploying
3. **Redirects IN robots.txt** — some platforms redirect `/robots.txt` somewhere; Google needs a 200 response, not a 301
4. **Multi-subdomain stores** — each subdomain needs its own robots.txt (including staging, which should `Disallow: /`)
5. **Mixed HTTPS/HTTP** — ensure robots.txt matches the canonical protocol
6. **Crawl-delay directives** — Google ignores these; only use if Bing/Yandex performance is a concern
7. **Noindex in robots.txt** — Google stopped supporting this in 2019; it's silently ignored

---

## 14. Diagnosing Leaked Staging/Dev Environments (Domain Property + Regex)

Staging, dev, and UAT subdomains sometimes get discovered and partially indexed by Google — usually because a robots.txt or noindex was never applied before the environment went temporarily live, or because a link leaked externally (a shared preview link, a screenshot tool, a broken redirect).

**Diagnostic method:**

1. Set up (or confirm) a **Domain property** in Google Search Console, not just a URL-prefix property. Domain properties aggregate all subdomains and protocols, so a leaked `staging.` or `dev.` subdomain will surface even if the client only ever verified `www.`.
2. In Search Console → Performance, filter the Pages dimension with a regex query to catch common staging/dev subdomain patterns:
   ```
   (?i)://(www\.)?(staging|stg|stage|dev|dev2|develop|test|tst|uat|qa|qa2|demo|sandbox|sbx|beta|preview|preprod|pre-prod|nonprod|new|old|temp|tmp)[.-]
   ```
3. Any matches confirm a non-production environment has been crawled and is receiving impressions or clicks. Treat as Critical: apply `Disallow: /` plus a site-wide noindex to the environment immediately, and request removal via the URL Removals tool for anything already indexed.

Run this check during initial audit intake for any client known to run a staging/dev/UAT environment — ask directly, since this class of leak is invisible in a standard SF crawl of the production domain alone.

---

## 15. Verification References

Verified against these primary sources (April 2026):

- [Google Search Central: Robots.txt Introduction](https://developers.google.com/search/docs/crawling-indexing/robots/intro) — crawl vs. index directive distinction
- [Google Search Central: Block indexing with noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing) — noindex/robots.txt combination warning
- [Google Search Central: Ecommerce URL Structure](https://developers.google.com/search/docs/specialty/ecommerce/designing-a-url-structure-for-ecommerce-sites) — variant canonical guidance
- [Shopify: robots.txt.liquid template](https://shopify.dev/docs/storefronts/themes/architecture/templates/robots-txt-liquid) — Shopify implementation mechanics

Google deprecated the URL Parameters Tool in April 2022. Manual parameter control now lives in robots.txt + canonical + noindex.
