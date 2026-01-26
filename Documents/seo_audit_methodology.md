# SEO Audit Methodology & Best Practices

> This document provides the overarching framework for conducting SEO audits, prioritizing recommendations, and communicating findings effectively.

## Audit Frequency Framework

| Audit Type | Frequency | Scope |
|------------|-----------|-------|
| Full Comprehensive Audit | Quarterly | Technical + Content + Links + Competition |
| Technical Health Check | Monthly | Crawling, indexing, Core Web Vitals |
| Content Review | Bi-annually | Quality, freshness, gaps |
| Competitive Analysis | Bi-annually | Keyword gaps, SERP changes |
| Quick Issue Scan | Weekly | Critical errors, 5xx, broken pages |

## Audit Scope by Type

### Full Audit Components
1. **Technical SEO** - Crawlability, indexing, site speed, mobile, architecture
2. **On-Page SEO** - Titles, meta, headings, content quality, internal links
3. **Off-Page SEO** - Backlink profile, brand mentions, referring domains
4. **User Experience** - Core Web Vitals, navigation, page usability
5. **Competitive Analysis** - Keyword gaps, content opportunities

### Specialized Audits
- **Technical-only**: Focus on crawling, rendering, indexation
- **Content-only**: Quality, E-E-A-T, keyword targeting, gaps
- **Backlink-only**: Profile health, toxic links, anchor distribution
- **Local SEO**: GMB, citations, local content, reviews

---

## Prioritization Framework

### Impact × Effort Scoring

**Scoring Method:**
```
Priority Score = (Impact Score + Inverse Effort Score) / 2

Impact: 1 (minimal) to 5 (major business impact)
Effort: 5 (simple fix) to 1 (major development)
```

**Score Interpretation:**
| Score | Priority | Action |
|-------|----------|--------|
| 4.5-5.0 | Critical | Implement immediately |
| 3.5-4.4 | High | Schedule this sprint |
| 2.5-3.4 | Medium | Add to backlog |
| 1.5-2.4 | Low | Opportunistic |
| 1.0-1.4 | Minimal | Consider skipping |

### Quick Prioritization Matrix

```
                    HIGH EFFORT
                        ↑
    Strategic      |   Major
    Investments    |   Projects
    (plan carefully) | (requires resources)
    ←──────────────┼──────────────→
    LOW IMPACT     |           HIGH IMPACT
    Quick Wins     |   Do First
    (batch these)  |   (immediate action)
                        ↓
                    LOW EFFORT
```

### Prioritization Criteria

1. **Business alignment** - Does it support key business goals?
2. **Traffic potential** - How many URLs/users affected?
3. **Competitive gap** - Are competitors doing this better?
4. **Technical dependency** - Does it unblock other work?
5. **Resource availability** - Can it be done now?

---

## Presentation Best Practices

### Report Structure

```
1. Executive Summary (1 page)
   - Site health score
   - Top 3 critical issues
   - Top 3 quick wins
   - Estimated impact

2. Priority Issues (by category)
   - High Impact (fix now)
   - Medium Impact (schedule soon)
   - Low Impact (backlog)

3. Detailed Findings
   - Technical SEO
   - On-Page SEO
   - Backlink Analysis
   - Competitive Insights

4. Action Plan
   - Prioritized task list
   - Effort estimates
   - Dependencies noted

5. Appendix
   - Full issue export
   - Supporting data
```

### Communication Principles

**Key insight from Aleyda Solis:**
> "The purpose is not recommending solutions, it's getting them implemented."

**Effective communication:**
- Lead with business impact, not technical jargon
- Include screenshots and visual evidence
- Explain WHY each issue matters for rankings/traffic
- Provide specific, actionable steps
- Understand platform limitations before finalizing recommendations
- Ask developers their preferred format/style

### Stakeholder-Specific Formats

| Stakeholder | Focus On | Avoid |
|-------------|----------|-------|
| Executives | Business impact, ROI, competitive position | Technical details |
| Marketing | Traffic, conversions, content gaps | Code-level issues |
| Developers | Specific fixes, code examples, priority | Business strategy |
| Content Team | E-E-A-T, quality issues, gaps | Technical jargon |

---

## E-E-A-T Framework

### The Four Components

| Component | Definition | How to Demonstrate |
|-----------|------------|-------------------|
| **Experience** | First-hand knowledge | Product reviews from users, personal case studies |
| **Expertise** | Subject matter knowledge | Author credentials, certifications, depth of coverage |
| **Authoritativeness** | Industry recognition | Backlinks from authoritative sources, citations, awards |
| **Trustworthiness** | Reliability signals | HTTPS, contact info, privacy policy, accurate info |

### E-E-A-T Implementation Checklist

**Author Credibility:**
- [ ] Detailed author bios with credentials
- [ ] Professional author photos
- [ ] Links to author's other work/profiles
- [ ] Relevant certifications displayed

**Content Quality:**
- [ ] Cite authoritative sources
- [ ] Keep information current
- [ ] Address primary and follow-up questions
- [ ] Match complexity to audience level

**Brand Transparency:**
- [ ] Clear contact information
- [ ] Physical address displayed
- [ ] SSL/HTTPS implemented
- [ ] Privacy policy present
- [ ] Active, verified social profiles

**YMYL Content (Extra Scrutiny):**
- [ ] Expert authors for health/finance/legal
- [ ] Citations to authoritative sources
- [ ] Regular content updates
- [ ] Clear disclaimers where appropriate

---

## Crawl Budget Optimization

### Factors Affecting Crawl Budget

| Factor | Impact | Optimization |
|--------|--------|--------------|
| Site size | More pages = more competition for crawl | Prune low-value pages |
| Server speed | Slow response = fewer pages crawled | Improve TTFB |
| Content quality | Low quality = reduced crawl priority | Improve or remove thin content |
| Update frequency | Fresh content = more frequent crawling | Regular updates to key pages |
| Internal linking | Poorly linked = missed pages | Improve internal link structure |

### Crawl Budget Optimization Strategies

1. **Eliminate crawl waste:**
   - Block faceted navigation with robots.txt
   - Consolidate duplicate content
   - Remove or noindex thin pages
   - Fix redirect chains

2. **Improve crawl efficiency:**
   - Reduce server response time
   - Flatten site architecture
   - Submit updated XML sitemaps
   - Fix broken internal links

3. **Prioritize important pages:**
   - More internal links to key pages
   - Fresh content on priority pages
   - Submit high-priority URLs in sitemap

### Crawl Waste Indicators

| Issue | Crawl Waste Impact | Fix |
|-------|-------------------|-----|
| Parameter variations | High - infinite URLs | URL parameters in GSC |
| Session IDs in URLs | High - duplicate crawling | Server-side sessions |
| Infinite scroll pagination | Medium - resource waste | Proper pagination |
| Calendar widgets | High - years of URLs | Limit date ranges |
| Search results pages | Medium - thin pages | Noindex, disallow |

---

## JavaScript SEO Considerations

### Rendering Approaches

| Approach | Description | SEO Impact |
|----------|-------------|------------|
| Server-Side Rendering (SSR) | HTML generated on server | Best - content immediately available |
| Static Site Generation | Pre-built HTML | Excellent - fast and crawlable |
| Client-Side Rendering (CSR) | JS renders in browser | Risky - may not be indexed |
| Dynamic Rendering | Server for bots, client for users | Good - but maintenance overhead |
| Hybrid Rendering | SSR for critical, CSR for interactive | Good - balance of both |

### JavaScript SEO Checklist

- [ ] Critical content visible in initial HTML
- [ ] No content behind user interactions (clicks, scrolls)
- [ ] Internal links in `<a href="">` format (not onClick)
- [ ] Lazy-loaded content uses Intersection Observer
- [ ] Test rendering with Google's URL Inspection tool
- [ ] Check for rendering delays affecting crawl budget
- [ ] Ensure JavaScript files not blocked in robots.txt

### Common JavaScript SEO Issues

1. **Links as onclick events** - Not discovered by crawlers
2. **Content loaded on scroll** - May not be rendered
3. **Infinite scroll without pagination** - Poor crawl structure
4. **Single Page Applications (SPAs)** - Require special handling
5. **Delayed content injection** - May timeout before indexed
6. **JS errors blocking render** - Content not visible to Google

---

## Structured Data Implementation

### Priority Schema Types by Site Type

| Site Type | Must Have | Should Have | Nice to Have |
|-----------|-----------|-------------|--------------|
| E-commerce | Product, BreadcrumbList, Organization | Review, FAQ, Offer | HowTo, Video |
| Publisher | Article, BreadcrumbList, Organization | Person, FAQ | Video, HowTo |
| Local Business | LocalBusiness, BreadcrumbList | Review, FAQ | Event, Menu |
| SaaS | Organization, BreadcrumbList, FAQ | SoftwareApplication | HowTo, Video |

### Schema Validation Process

1. **Implement schema** using JSON-LD (recommended format)
2. **Validate syntax** with Schema.org validator
3. **Test rich results** with Google Rich Results Test
4. **Deploy and monitor** in GSC Rich Results report
5. **Iterate** based on validation errors

### Schema Best Practices

- Use JSON-LD format (Google recommended)
- One schema type per purpose (don't duplicate)
- Ensure data accuracy (match visible content)
- Keep schema updated when content changes
- Don't mark up hidden content
- Test in both staging and production

---

## SERP Features Optimization

### Feature Types and Requirements

| Feature | Content Format | Schema Required | Key Optimization |
|---------|---------------|-----------------|------------------|
| Featured Snippet | Paragraph, list, table | No (but helps) | Direct answer in 40-60 words |
| People Also Ask | Question + answer format | FAQPage helps | Clear Q&A structure |
| Knowledge Panel | Entity information | Organization/Person | Brand signals, Wikipedia |
| Rich Snippets | Varies by type | Yes - type specific | Accurate schema data |
| AI Overview | Comprehensive, authoritative | Helps | E-E-A-T, structure, freshness |
| Local Pack | Business listing | LocalBusiness | GMB optimization |

### Featured Snippet Optimization

**Paragraph Snippets (most common):**
- Lead with the answer (40-60 words)
- Use question as H2/H3 heading
- Follow with supporting details
- Keep sentences simple and direct

**List Snippets:**
- Use proper HTML lists (`<ol>` or `<ul>`)
- Start with action verbs
- Keep items parallel in structure
- 5-8 items optimal

**Table Snippets:**
- Use proper HTML tables
- Include clear headers
- Data should be comparative
- Accurate, up-to-date figures

---

## AI Search Optimization

### Optimizing for AI Overviews

**Content Characteristics:**
- Comprehensive, authoritative coverage
- Clear, scannable structure
- Factual accuracy with citations
- Fresh, regularly updated content
- Strong E-E-A-T signals

**Technical Requirements:**
- Allow AI crawlers (check robots.txt)
- Fast, accessible pages
- Structured data implementation
- Mobile-friendly design

### AI Crawler Considerations

| Crawler | Owner | robots.txt directive |
|---------|-------|---------------------|
| GPTBot | OpenAI | User-agent: GPTBot |
| Anthropic-AI | Anthropic | User-agent: anthropic-ai |
| PerplexityBot | Perplexity | User-agent: PerplexityBot |

**Decision Framework:**
- Want AI training: Allow AI bots
- Want AI search traffic: Allow AI bots + optimize
- Block AI training only: Selective bot blocking
- Block all AI: Block all AI user-agents

---

## Common Audit Mistakes to Avoid

### Methodology Mistakes
- Relying solely on automated tool output
- Not manually reviewing key pages
- Generic recommendations without site context
- Ignoring platform/CMS limitations
- Overwhelming stakeholders with too many issues

### Prioritization Mistakes
- Treating all issues equally
- Ignoring effort required for fixes
- Not considering business impact
- Missing quick wins
- Over-focusing on minor issues

### Communication Mistakes
- Too technical for audience
- No clear action items
- Missing impact explanation
- No visual evidence
- Recommendations without implementation steps

### Follow-up Mistakes
- No verification of fixes
- Not tracking impact of changes
- Skipping re-audit after major fixes
- Not documenting what was done
