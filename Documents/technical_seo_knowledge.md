# Technical SEO Knowledge Base

> This document trains the Technical SEO Agent on how to analyze, prioritize, and recommend fixes for technical SEO issues.

## Issue Severity Framework

### Critical Issues (Immediate Action Required)
Issues that prevent crawling, indexing, or cause major ranking damage.

**Characteristics:**
- Blocks Googlebot from accessing content
- Prevents pages from being indexed
- Causes site-wide ranking suppression
- Server errors affecting large portions of site

### High Severity (Priority Fix)
Issues that significantly degrade ranking potential or user experience.

**Characteristics:**
- Reduces crawl efficiency
- Creates indexation confusion
- Degrades Core Web Vitals
- Affects important page templates

### Medium Severity (Should Address)
Issues that reduce optimization potential but don't block functionality.

**Characteristics:**
- Suboptimal configurations
- Minor signal dilution
- Missed best practices
- Affects subset of pages

### Low Severity (Nice to Have)
Minor issues or informational findings.

---

## Indexability Issues

### Canonical Tag Problems

#### Critical
| Issue | Impact | Fix |
|-------|--------|-----|
| Canonical Outside of Head | Not recognized by search engines | Move to `<head>` section |
| Canonical Points to HTTP Version | Protocol mismatch confuses canonicalization | Update to HTTPS |
| Canonical Contains Invalid Attributes | May be ignored entirely | Remove invalid attributes |
| Meta Robots Found Outside Head | Directive may not be recognized | Move to `<head>` section |
| Head Contains Invalid HTML Elements | Early head termination | Remove invalid elements |

#### High
| Issue | Impact | Fix |
|-------|--------|-----|
| Mismatched Canonical in HTML and HTTP Header | Conflicting signals | Use single method |
| Multiple Mismatched Canonical Tags | Search engine picks random one | Keep single canonical |
| Canonical is Malformed or Empty | No canonicalization | Add valid href |
| Canonical Points to Noindex URL | Circular contradiction | Point to indexable page |
| Canonical Points to 4XX/5XX URL | Dead end canonicalization | Point to working page |
| Canonical Loop | Infinite loop detected | Break the loop |
| Canonical Chain | Points to another canonicalized URL | Point to final destination |

#### Medium
| Issue | Impact | Fix |
|-------|--------|-----|
| Canonical is Relative URL | May resolve incorrectly | Use absolute URL |
| Canonical Points to Redirect | Unnecessary hop | Point to final destination |
| Canonical Points to Homepage | Content signal dilution | Point to correct page |

### Robots Directives

**Understanding noindex vs nofollow:**
- `noindex`: Don't show this page in search results
- `nofollow`: Don't follow links on this page
- `noindex,follow`: Hide page but crawl its links (common for pagination)
- `noindex,nofollow`: Complete exclusion

**When noindex is acceptable:**
- Thank you/confirmation pages
- Internal search results
- Paginated pages (debatable - use rel=prev/next instead)
- User account pages
- Duplicate filter/sort pages

**When noindex is problematic:**
- Valuable content pages
- Product/service pages
- Blog posts meant for organic traffic
- Category/collection pages with unique content

### Crawlability Issues

#### Robots.txt Analysis
| Issue | Impact | Fix |
|-------|--------|-----|
| Disallowed JavaScript File | Rendering fails | Allow in robots.txt |
| Disallowed CSS File | Layout breaks | Allow in robots.txt |
| Disallowed Images | Missing media in cache | Allow in robots.txt |
| Blocking valuable content | Pages not indexed | Review disallow rules |

**Robots.txt Best Practices:**
- Never block CSS/JS files
- Use Disallow sparingly
- Test with Google's robots.txt tester
- Remember: robots.txt is a suggestion, not security

---

## Redirect Issues

### Redirect Chain Analysis

**Impact by Chain Length:**
| Hops | Impact | Recommendation |
|------|--------|----------------|
| 1 | Acceptable | Normal operation |
| 2 | Minor delay | Optimize if possible |
| 3+ | Significant | Fix required |
| 5+ | Critical | Immediate fix |

**PageRank Loss per Redirect:**
- Each 301 redirect loses ~10-15% PageRank (historically)
- Modern understanding: minimal loss if chain is short
- Long chains compound the loss significantly

### Redirect Types

| Code | Type | Use Case | SEO Impact |
|------|------|----------|------------|
| 301 | Permanent | URL changed forever | Passes ~90%+ equity |
| 302 | Temporary | Short-term change | May not pass equity |
| 307 | Temporary (HTTP/1.1) | Same as 302 | May not pass equity |
| 308 | Permanent (HTTP/1.1) | Same as 301 | Passes equity |
| Meta Refresh | Soft redirect | Avoid for SEO | Poor practice |
| JavaScript | Client-side | Last resort only | Unreliable |

### Common Redirect Problems

| Problem | Issue | Fix |
|---------|-------|-----|
| Redirect Loop | A→B→A | Break the loop |
| Trailing Slash Mismatch | /page redirects to /page/ | Pick one, be consistent |
| Case Normalization | /Page redirects to /page | Use lowercase consistently |
| HTTP to HTTPS Chain | http→https→www | Single redirect http→final |
| Mixed Protocol Chain | https→http→https | Remove HTTP hop |
| Redirect to 4XX/5XX | Redirect leads nowhere | Update destination |

---

## Core Web Vitals

### Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP (Largest Contentful Paint) | ≤2.5s | 2.5s - 4.0s | >4.0s |
| INP (Interaction to Next Paint) | ≤200ms | 200ms - 500ms | >500ms |
| CLS (Cumulative Layout Shift) | ≤0.1 | 0.1 - 0.25 | >0.25 |

### LCP Optimization

**Common Causes of Poor LCP:**
1. Slow server response (TTFB)
2. Render-blocking resources
3. Slow resource load times
4. Client-side rendering

**Fixes by Priority:**
1. Reduce TTFB (server optimization, CDN)
2. Eliminate render-blocking CSS/JS
3. Preload LCP image/resource
4. Use efficient image formats (WebP, AVIF)
5. Implement critical CSS inlining

### INP Optimization

**Common Causes:**
1. Heavy JavaScript execution
2. Long tasks blocking main thread
3. Large DOM size
4. Third-party scripts

**Fixes:**
1. Break up long tasks (yield to main thread)
2. Remove unused JavaScript
3. Defer non-critical JavaScript
4. Reduce DOM size and complexity

### CLS Optimization

**Common Causes:**
1. Images without dimensions
2. Dynamically injected content
3. Web fonts causing FOIT/FOUT
4. Ads/embeds without reserved space

**Fixes:**
1. Always specify width/height on images
2. Reserve space for dynamic content
3. Use font-display: swap with fallback fonts
4. Pre-allocate space for ads/embeds

---

## Performance Issues

### Critical Performance Issues

| Issue | Why Critical | Fix |
|-------|--------------|-----|
| Render-blocking resources | Delays First Paint | Defer, async, or inline critical |
| Enormous network payloads | Slow load, poor mobile | Compress, lazy-load, optimize |
| No efficient cache policy | Repeated downloads | Set Cache-Control headers |

### High Priority Performance

| Issue | Impact | Fix |
|-------|--------|-----|
| Unoptimized images | Slow load, high bandwidth | Compress, resize, modern formats |
| Unminified JS/CSS | Larger file sizes | Minify all production assets |
| High TTFB | Everything waits | Server optimization, CDN |
| No text compression | Larger transfers | Enable gzip/brotli |

### Medium Priority Performance

| Issue | Impact | Fix |
|-------|--------|-----|
| No lazy loading | Loads offscreen content | Implement loading="lazy" |
| Not using HTTP/2 | Slower multiplexing | Upgrade server/CDN |
| No image dimensions | CLS issues | Add width/height attributes |
| Unused CSS/JS | Bloated bundles | Tree-shaking, code splitting |

---

## Security Issues

### HTTPS Configuration

| Issue | Severity | Fix |
|-------|----------|-----|
| HTTP pages (no HTTPS) | Critical | Implement SSL, redirect |
| Mixed content | High | Update all resources to HTTPS |
| Expired certificate | Critical | Renew immediately |
| Invalid certificate | Critical | Fix certificate chain |

### Security Headers

Recommended headers for SEO-relevant security:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `Strict-Transport-Security` (HSTS)

---

## How Variables Interconnect

### Crawlability Chain
```
Robots.txt blocks → Can't crawl → Can't index → No rankings
DNS/Server issues → Slow/no response → Reduced crawl frequency
Redirect chains → Lost PageRank → Reduced authority → Lower rankings
```

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

### Compound Effects

**Example 1: Faceted Navigation**
```
Faceted URLs crawled → Duplicate content generated → Crawl budget wasted
                    ↓                               ↓
            Thin content indexed          Important pages under-crawled
                    ↓                               ↓
            Quality signals degraded        Slow indexation of new content
```

**Example 2: JavaScript Rendering Issues**
```
JS-rendered content → Googlebot can't render → Empty page indexed
                   ↓                          ↓
            Links not discovered        Zero keyword rankings
                   ↓                          ↓
            Orphan pages created        Lost organic traffic
```

---

## Prioritization Decision Tree

```
1. Is it blocking indexation of important pages?
   YES → Critical priority
   NO  → Continue

2. Does it affect site-wide or template-level?
   SITE-WIDE → High priority
   TEMPLATE  → Medium-High priority
   FEW PAGES → Medium priority

3. Is it causing user experience issues?
   YES + measurable impact → High priority
   YES + minor impact → Medium priority
   NO → Lower priority

4. Is there a clear ROI case?
   YES → Prioritize accordingly
   NO → Batch with similar fixes
```

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
