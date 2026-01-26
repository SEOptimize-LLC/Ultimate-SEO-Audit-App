# Competitor Analysis Knowledge Base

> This document trains the Competitor Agent on competitive SEO analysis, keyword gap identification, content opportunity scoring, and market positioning strategies.

## Competitor Identification Framework

### Types of SEO Competitors

| Type | Definition | Analysis Priority |
|------|------------|-------------------|
| Direct Competitors | Same products/services, same market | Highest |
| SERP Competitors | Rank for your target keywords | High |
| Content Competitors | Same topics, different business | Medium |
| Indirect Competitors | Adjacent solutions, same audience | Lower |

### Competitor Discovery Methods

**1. SERP Analysis:**
- Search top 20 target keywords
- Note domains appearing 3+ times
- These are your SERP competitors

**2. Market Knowledge:**
- Known business competitors
- Industry leaders in your space
- New market entrants

**3. Tool-Based Discovery:**
- DataForSEO Competitors Domain API
- SEMrush/Ahrefs competitor reports
- Similar organic traffic profiles

### Competitor Prioritization Matrix

```
Priority Score = (Keyword Overlap × 0.4) +
                 (Market Overlap × 0.3) +
                 (Authority Similarity × 0.2) +
                 (Growth Trajectory × 0.1)
```

**Resulting Tiers:**
- Tier 1: Primary competitors (analyze deeply)
- Tier 2: Secondary competitors (monitor quarterly)
- Tier 3: Tertiary (occasional review)

---

## Keyword Gap Analysis

### Gap Categories

| Gap Type | Definition | Opportunity Level |
|----------|------------|-------------------|
| Full Gap | Competitor ranks, you don't rank at all | High |
| Positioning Gap | Both rank, competitor significantly higher | Medium-High |
| Featured Snippet Gap | Competitor has SERP feature, you don't | High |
| New Keyword Gap | Competitor targeting keywords you haven't identified | Medium |

### Keyword Gap Prioritization

**High Priority Gaps:**
```
Criteria:
- Search volume > 500/month
- Keyword difficulty < your site's capability
- High commercial intent
- Competitor ranks top 5
- Clear content creation path
```

**Medium Priority Gaps:**
```
Criteria:
- Search volume 100-500/month
- Moderate competition
- Informational or mixed intent
- Competitor ranks 5-20
- Would require moderate effort
```

**Lower Priority Gaps:**
```
Criteria:
- Search volume < 100/month OR
- Very high difficulty OR
- Low business relevance
- Would require significant investment
```

### Gap Analysis Process

1. **Pull Ranked Keywords:**
   - Your site's ranked keywords
   - Top 5 competitors' ranked keywords

2. **Categorize Overlap:**
   ```
   Your Keywords: [A, B, C, D, E]
   Competitor 1:  [A, B, F, G, H]
   Competitor 2:  [A, C, F, I, J]

   Shared by all: [A]
   Your unique: [D, E]
   Competitor-only: [F, G, H, I, J] ← Gaps
   ```

3. **Score Each Gap:**
   - Volume
   - Difficulty
   - Relevance
   - Intent match

4. **Prioritize Action:**
   - Quick wins (low difficulty, high opportunity)
   - Strategic investments (high difficulty, high value)
   - Pass (low opportunity relative to effort)

---

## Content Gap Analysis

### Content Gap Types

**1. Topic Coverage Gaps:**
- Subtopics competitors cover that you don't
- Depth of coverage differences
- Content format gaps (video, tools, guides)

**2. Content Quality Gaps:**
- Your content is thinner/older
- Competitor content more comprehensive
- Better E-E-A-T signals in competitor content

**3. Content Freshness Gaps:**
- Competitor content recently updated
- Your content outdated
- Missing trending topics

### Content Comparison Framework

| Metric | Your Page | Competitor A | Competitor B | Gap? |
|--------|-----------|--------------|--------------|------|
| Word Count | 1,200 | 3,500 | 2,800 | Yes |
| Headings/Structure | 5 H2s | 12 H2s + H3s | 10 H2s | Yes |
| Images/Media | 2 | 8 + video | 5 | Yes |
| Internal Links | 3 | 15 | 12 | Yes |
| External Links | 1 | 8 | 5 | Yes |
| Last Updated | 2023 | 2025 | 2024 | Yes |
| Backlinks to Page | 12 | 89 | 45 | Yes |
| Rankings (1-10) | Position 8 | Position 1 | Position 3 | Yes |

### Content Opportunity Scoring

```
Opportunity Score =
  (Search Volume × 0.25) +
  (Current Ranking Gap × 0.25) +
  (Content Quality Gap × 0.20) +
  (Business Value × 0.20) +
  (Implementation Feasibility × 0.10)
```

**Score Interpretation:**
- 80-100: Immediate priority
- 60-79: High priority, schedule soon
- 40-59: Medium priority, add to roadmap
- 20-39: Low priority, opportunistic
- 0-19: Skip or deprioritize

---

## SERP Feature Analysis

### Feature Type Comparison

| SERP Feature | Your Site | Competitor A | Competitor B | Opportunity |
|--------------|-----------|--------------|--------------|-------------|
| Featured Snippet | 5% | 18% | 12% | High |
| People Also Ask | 8% | 25% | 20% | High |
| Knowledge Panel | No | Yes | No | Medium |
| Image Pack | 3% | 12% | 8% | Medium |
| Video Carousel | 0% | 8% | 5% | High |
| AI Overview | 2% | 15% | 10% | High |

### SERP Feature Optimization Priorities

**Featured Snippets:**
- Identify competitor-held snippets
- Analyze snippet format (paragraph, list, table)
- Create better-structured content
- Match format to query type

**AI Overviews:**
- Analyze structure of AIO appearances
- Identify source patterns
- Optimize for extractability (40-60 word answers)
- Build topical authority clusters

**People Also Ask:**
- Map competitor PAA appearances
- Create content answering those questions
- Structure with clear question headings
- Provide concise, direct answers

---

## Technical SEO Comparison

### Site Performance Comparison

| Metric | Your Site | Competitor A | Competitor B | Benchmark |
|--------|-----------|--------------|--------------|-----------|
| Domain Authority | 35 | 52 | 48 | Competitor avg |
| Indexed Pages | 500 | 2,000 | 1,500 | Larger = more surface |
| Avg Page Speed | 3.2s | 1.8s | 2.1s | <2.5s |
| Mobile Score | 65 | 85 | 78 | >80 |
| Core Web Vitals Pass | 45% | 78% | 65% | >75% |

### Technical Advantage Identification

**Areas Where Competitors Excel:**
- Faster page speed → Better user experience → Rankings
- More indexed pages → More keyword coverage
- Better mobile experience → Mobile-first indexing advantage
- Cleaner site architecture → Efficient crawling

**Your Technical Advantages:**
- Identify where you outperform
- Leverage these strengths
- Communicate in content marketing

---

## Backlink Competitive Analysis

### Link Profile Comparison

| Metric | Your Site | Competitor A | Competitor B |
|--------|-----------|--------------|--------------|
| Total Backlinks | 5,000 | 25,000 | 18,000 |
| Referring Domains | 450 | 1,800 | 1,200 |
| DR 50+ Links | 45 | 180 | 120 |
| New Links/Month | 25 | 150 | 80 |
| Link Velocity Trend | Flat | Growing | Growing |

### Link Acquisition Gap Analysis

**1. Shared Link Sources:**
- Domains linking to multiple competitors
- High-value, accessible opportunities
- Often indicates easy wins

**2. Unique Competitor Links:**
- Analyze how competitor earned them
- Determine if replicable
- Prioritize by domain quality

**3. Link Type Distribution:**
- Compare content types earning links
- Identify successful link bait formats
- Adapt strategy accordingly

---

## Competitive Positioning Strategy

### Market Position Mapping

```
                    HIGH AUTHORITY
                         ↑
    Niche Expert    |    Market Leader
    (specialized)   |    (broad + strong)
    ←───────────────┼───────────────→
    NARROW          |             BROAD
    FOCUS           |             FOCUS
    Emerging Player |    Generalist
    (opportunity)   |    (vulnerable)
                         ↓
                    LOW AUTHORITY
```

### Positioning Strategy by Position

**If You're Emerging Player:**
- Focus on niche dominance first
- Depth over breadth
- Build authority in specific topics
- Expand gradually

**If You're Niche Expert:**
- Expand topic coverage
- Maintain depth while growing breadth
- Cross-link to new topic areas
- Leverage existing authority

**If You're Generalist:**
- Improve content quality
- Build authority signals
- Consider niche focus
- Compete on specific verticals

**If You're Market Leader:**
- Defend positions
- Expand into adjacent areas
- Monitor for emerging threats
- Innovate on content formats

---

## Quick Win Identification

### Quick Win Criteria

| Factor | Quick Win | Not Quick Win |
|--------|-----------|---------------|
| Effort Required | <1 week | >1 month |
| Resources Needed | Existing team | New hires/contractors |
| Content Exists | Yes, needs update | Create from scratch |
| Ranking Gap | Position 4-15 | Not ranking at all |
| Technical Blockers | None | Major issues |
| Competitor Weakness | Clear weakness | Strong position |

### Quick Win Examples

**Content Quick Wins:**
- Update outdated top 20 rankings
- Add missing sections to existing content
- Improve title tags for better CTR
- Add internal links to orphan content
- Optimize for featured snippets you almost have

**Technical Quick Wins:**
- Fix broken links discovered in audit
- Add missing meta descriptions
- Optimize largest images
- Fix mobile usability issues
- Implement missing schema

**Link Quick Wins:**
- Claim unlinked brand mentions
- Fix broken backlinks
- Request links from partners/vendors
- Update outdated profiles/directory listings

---

## Competitive Monitoring

### Key Metrics to Track Monthly

| Metric | Why Track | Tool |
|--------|-----------|------|
| Ranking changes | Position shifts | Rank tracker |
| New content published | Competitive moves | Alerts/manual |
| Backlinks gained | Link building activity | Backlink monitors |
| SERP feature changes | Feature opportunities | SERP trackers |
| Traffic estimates | Market share shifts | SEMrush/Ahrefs |

### Competitive Alert Triggers

**Immediate Response Needed:**
- Competitor launches major content initiative
- New competitor enters market
- Algorithm update impacts competitive landscape
- Competitor gains significant link advantage

**Quarterly Review:**
- Overall market position shifts
- Content gap changes
- Technical improvements by competitors
- New keyword opportunities

---

## How Competitive Factors Interconnect

### Market Position Chain
```
Competitor content gaps → Your opportunity
        ↓
Create superior content → Earn links naturally
        ↓
Authority increases → Rankings improve
        ↓
Traffic grows → More opportunities identified
```

### Competitive Response Chain
```
Competitor improves → Your relative position drops
        ↓
Identify their changes → Analyze what worked
        ↓
Adapt strategy → Reclaim or exceed position
        ↓
Monitor results → Iterate
```

### Market Share Dynamics
```
Total organic opportunity = Fixed (for any keyword set)
        ↓
Your share + Competitor shares = 100%
        ↓
To grow your share → Must take from competitors
        ↓
Strategy: Better content, more links, better UX
```
