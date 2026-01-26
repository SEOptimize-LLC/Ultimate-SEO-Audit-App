# On-Page SEO Knowledge Base

> This document trains the On-Page SEO Agent on content optimization, heading structure, meta elements, and internal linking analysis.

## Title Tag Optimization

### Issues by Severity

#### Critical
| Issue | Impact | Fix |
|-------|--------|-----|
| Title Tag Missing | No title in SERPs, poor CTR | Add descriptive title |
| Title Tag Empty | Same as missing | Add content to title |
| Title Outside Head | May not be recognized | Move to `<head>` |

#### High
| Issue | Impact | Fix |
|-------|--------|-----|
| Multiple Title Tags | Inconsistent display | Keep single title |
| Duplicate Titles (site-wide) | Keyword cannibalization | Unique titles per page |

#### Medium/Low
| Issue | Impact | Fix |
|-------|--------|-----|
| Title Too Short (<30 chars) | Missed keyword opportunity | Expand with modifiers |
| Title Too Long (>60 chars) | Truncated in SERPs | Shorten, front-load keywords |
| Title Same as H1 | Missed variation opportunity | Differentiate slightly |

### Title Tag Best Practices

**Structure Formula:**
```
Primary Keyword - Secondary Keyword | Brand Name
```

**Character Limits:**
- Desktop: ~60 characters / ~600 pixels
- Mobile: ~50-55 characters

**Optimization Principles:**
1. Front-load primary keyword
2. Include secondary keyword/modifier
3. Brand at end (if space)
4. Compelling for clicks, not just keywords
5. Unique per page - no duplicates

**What Makes a Good Title:**
- Accurately describes page content
- Contains target keyword naturally
- Encourages click-through
- Differentiates from competitors
- Matches search intent

---

## Meta Description Optimization

### Issues by Severity

| Issue | Severity | Impact |
|-------|----------|--------|
| Meta Description Missing | High | Google auto-generates (often poorly) |
| Meta Description Empty | High | Same as missing |
| Meta Description Outside Head | High | May not be recognized |
| Multiple Meta Descriptions | Medium | Confusion on which to use |
| Same as Title | Low | Wasted opportunity |
| Too Short (<120 chars) | Low | Incomplete message |
| Too Long (>160 chars) | Low | Truncated |

### Meta Description Best Practices

**Character Limits:**
- Desktop: ~155-160 characters
- Mobile: ~120-130 characters

**Structure Elements:**
1. Hook/value proposition (first 120 chars)
2. Call-to-action or benefit
3. Include primary keyword naturally
4. Differentiate from competitors

**What Works:**
- Active voice
- Specific benefits/features
- Numbers when relevant
- Match search intent
- Create curiosity gap

**What Doesn't Work:**
- Keyword stuffing
- Generic descriptions
- All caps/excessive punctuation
- Duplicate across pages
- No relevance to content

---

## Heading Structure (H1-H6)

### H1 Tag Issues

| Issue | Severity | Impact | Fix |
|-------|----------|--------|-----|
| H1 Missing | Medium | Weak page structure signal | Add descriptive H1 |
| H1 Empty | Medium | Same as missing | Add content |
| Multiple H1s | Medium | Hierarchy confusion | Keep single H1 |
| H1 Too Short (<20 chars) | Low | Weak topic signal | Expand descriptively |
| H1 Too Long (>70 chars) | Low | Diluted focus | Condense |

### Heading Hierarchy Rules

**Proper Structure:**
```html
<h1>Main Page Topic (One per page)</h1>
  <h2>Major Section 1</h2>
    <h3>Subsection 1.1</h3>
    <h3>Subsection 1.2</h3>
  <h2>Major Section 2</h2>
    <h3>Subsection 2.1</h3>
      <h4>Detail 2.1.1</h4>
```

**Common Mistakes:**
- Skipping levels (H1 → H3, no H2)
- Using headings for styling only
- Multiple H1s
- Non-descriptive headings ("More Information")
- Keyword stuffing in headings

**Best Practices:**
1. One H1 per page, matching primary topic
2. H2s for major sections
3. Logical hierarchy (don't skip levels)
4. Descriptive, not generic
5. Include relevant keywords naturally
6. Help users scan content

---

## Content Quality Analysis

### Word Count Guidelines

| Page Type | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| Product Page | 300 | 500-1000 | Focus on unique description |
| Blog Post | 800 | 1500-2500 | Depends on topic depth |
| Category Page | 200 | 300-500 | Unique intro, not just product list |
| Service Page | 500 | 1000-2000 | Explain value, process |
| Homepage | 300 | 500-1000 | Overview, value prop |

### Thin Content Indicators

| Signal | Threshold | Action |
|--------|-----------|--------|
| Word count | <300 words | Expand or consolidate |
| Unique content ratio | <60% | Increase originality |
| Boilerplate ratio | >40% | Reduce repeated elements |
| No substantive paragraphs | - | Add meaningful content |

### Content Quality Beyond Word Count

**E-E-A-T Signals:**
- **Experience**: First-hand knowledge demonstrated
- **Expertise**: Author credentials, depth of coverage
- **Authoritativeness**: Citations, external references
- **Trustworthiness**: Accurate info, clear sourcing

**Content Depth Indicators:**
- Comprehensive topic coverage
- Answers related questions
- Includes relevant examples
- Provides actionable information
- Unique data/insights

**Readability Factors:**
- Short paragraphs (2-4 sentences)
- Subheadings every 300-400 words
- Bulleted/numbered lists where appropriate
- Simple language (Flesch-Kincaid target: 60-70)

---

## Internal Linking Analysis

### Link Issues by Severity

#### High
| Issue | Impact | Fix |
|-------|--------|-----|
| Orphan pages (no internal links) | Not discovered by crawlers | Add contextual links |
| Single inlink only | Low PageRank flow | Add more internal links |
| No outgoing links | Dead end for crawlers | Link to related content |

#### Medium
| Issue | Impact | Fix |
|-------|--------|-----|
| Non-descriptive anchor text | Weak topical signals | Use descriptive anchors |
| Image links without alt text | No anchor text signal | Add descriptive alt |
| Mixed follow/nofollow to same page | Confusing signals | Be consistent |

#### Low
| Issue | Impact | Fix |
|-------|--------|-----|
| Empty href links | Broken user experience | Add destination or remove |
| Broken bookmarks | Poor UX | Fix anchor targets |

### Internal Linking Best Practices

**Anchor Text Guidelines:**
| Type | Example | Quality |
|------|---------|---------|
| Exact match | "SEO audit tools" | Good if natural |
| Partial match | "best tools for SEO audits" | Very good |
| Related | "website analysis software" | Good |
| Generic | "click here", "read more" | Poor |
| URL | "www.example.com/page" | Poor |

**Link Distribution:**
- Important pages should have more internal links
- Use contextual links (within content)
- Navigation links alone insufficient
- Deep pages need links from multiple sources
- Create topic clusters with hub pages

**PageRank Flow Concept:**
```
Homepage (highest authority)
    ↓ (links pass authority)
Category Pages
    ↓ (links pass authority)
Product/Article Pages
    ↓ (links pass authority)
Related Products/Articles
```

---

## Image Optimization

### Image Issues

| Issue | Severity | Impact | Fix |
|-------|----------|--------|-----|
| Missing Alt Text | Medium | Accessibility + Image SEO loss | Add descriptive alt |
| Empty Alt Text | Medium | Same as missing | Add content |
| Alt text too long (>125 chars) | Low | Truncated by screen readers | Shorten |
| Filename not descriptive | Low | Missed keyword signal | Rename with keywords |
| No dimensions specified | Medium | CLS issues | Add width/height |
| Oversized images | Medium | Slow loading | Resize appropriately |

### Alt Text Best Practices

**Good Alt Text:**
- Describes image content accurately
- Includes relevant keywords naturally
- Concise (125 characters or less)
- Provides context for visually impaired

**Bad Alt Text:**
- Keyword stuffing
- "Image of..." / "Photo of..." (redundant)
- Too generic ("product image")
- Same alt for all images
- Decorative images with keyword-stuffed alt

**Decorative vs. Informative Images:**
- Decorative: Use `alt=""` (empty)
- Informative: Describe content and purpose
- Functional: Describe action (buttons, links)

---

## Content Cannibalization

### Identifying Cannibalization

**Signs of Cannibalization:**
1. Multiple pages ranking for same keyword
2. Ranking position volatility
3. Neither page ranking as well as expected
4. Traffic split between pages

**Common Causes:**
- Similar product variations
- Blog posts covering same topic
- Location pages with similar content
- Paginated content without proper handling
- Category and tag pages competing

### Resolution Strategies

| Scenario | Solution |
|----------|----------|
| Two pages, one better | 301 redirect worse → better |
| Two pages, both valuable | Merge into comprehensive page |
| Similar but different intent | Differentiate titles, content focus |
| Pagination | Implement rel=canonical to page 1 or use view-all |
| Near-duplicate products | Unique descriptions, canonical to primary |

---

## Content Gap Identification

### Types of Content Gaps

**1. Keyword Gaps:**
- Competitors rank, you don't
- Related queries with no coverage
- Long-tail variations missing

**2. Topic Depth Gaps:**
- Surface-level coverage only
- Missing subtopics
- No supporting content for main topics

**3. Content Type Gaps:**
- No how-to content
- Missing comparison content
- No FAQ/Q&A format
- No visual content (images, videos)

**4. Intent Gaps:**
- Only informational, no commercial
- Missing transactional content
- No navigational landing pages

### Gap Prioritization

```
Priority = Search Volume × Relevance × Competition Gap × Conversion Potential
```

**High Priority:**
- High volume + low competition + high relevance
- Competitor ranks top 3, you don't rank at all
- Clear conversion path from content

**Medium Priority:**
- Medium volume + medium competition
- You rank page 2, competitor top 3
- Indirect conversion impact

**Lower Priority:**
- Low volume regardless of competition
- Highly competitive, low differentiation potential
- Minimal business relevance

---

## How On-Page Elements Interconnect

### Content Quality Chain
```
Thin content → High bounce rate → Reduced dwell time → Quality demotion
       ↓
Missing relevant keywords → Not matching queries → Low impressions
       ↓
Poor structure → Hard to scan → Poor engagement → Lower rankings
```

### Internal Linking Chain
```
Orphan pages → No crawl discovery → No indexation → Zero traffic
       ↓
Poor anchor text → Weak topical signals → Lower relevance scores
       ↓
Too few links → Low PageRank → Reduced authority → Lower positions
```

### Title/Meta Chain
```
Missing/bad title → Low CTR → Fewer clicks → Google tests alternatives
       ↓
Duplicate titles → Cannibalization → Split authority → Neither ranks well
       ↓
Keyword mismatch → Wrong intent served → High pogo-sticking → Demotion
```
