# Traffic Loss Analysis Report — [CLIENT_NAME]

**Domain:** [DOMAIN]
**Analysis Date:** [DATE]
**Comparison Period:** [BEFORE_START] to [BEFORE_END] (before) vs [AFTER_START] to [AFTER_END] (after)
**Analyst:** Claude Traffic Loss Analysis Skill

---

## Executive Summary

[1-2 paragraph summary of: what happened (magnitude of loss), when it started (onset date), the diagnosed root cause(s) with confidence levels, and the recommended recovery approach. This section should be understandable by a non-technical stakeholder.]

**Bottom Line:** [One sentence: "The primary cause of the [X]% organic traffic decline is [ROOT_CAUSE] with [CONFIDENCE]% confidence. The recommended recovery path is [HIGH_LEVEL_APPROACH]."]

---

## 0. Data Validation (Pre-Flight)

### Validation Results

| Check | Result | Notes |
|-------|--------|-------|
| GSC data integrity | [Pass/Fail/Warning] | [Details] |
| GA4 data integrity | [Pass/Fail/Warning/Not Available] | [Details] |
| Cross-source validation (GSC vs GA4) | [Consistent/Inconsistent] | [Details] |
| Third-party confirmation (DFS) | [Confirms drop/Does not confirm/Partial] | [Details] |

**Validation Conclusion:** [Drop confirmed / False alarm — tracking issue / Ambiguous — proceed with caution]

[If false alarm: describe the tracking/measurement issue found and recommended fix. Analysis stops here.]

---

## 1. Traffic Loss Overview

### Loss Summary

| Metric | Before Period | After Period | Change | % Change |
|--------|-------------|-------------|--------|----------|
| Total Organic Clicks | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Total Impressions | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Average CTR | [VALUE]% | [VALUE]% | [VALUE]pp | [VALUE]% |
| Average Position | [VALUE] | [VALUE] | [VALUE] | — |

### Loss Onset Date
**Identified onset:** [DATE or WEEK]
**Loss pattern:** [Sudden Drop / Gradual Decline / Stepped Decline / Progressive Acceleration / Cyclical]

### Severity Classification
**Severity:** [Minor / Moderate / Significant / Severe / Catastrophic]
**Estimated Annual Revenue Impact:** [VALUE if calculable, or "Not calculated — insufficient conversion data"]

### Segment Breakdown

#### Brand vs Non-Brand
| Segment | Before Clicks | After Clicks | Change | % Change |
|---------|-------------|-------------|--------|----------|
| Brand | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Non-Brand | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |

**Diagnostic Signal:** [Interpretation — e.g., "Non-brand keywords drive 95% of the loss, indicating an SEO/algorithm/competitive issue rather than a brand awareness problem."]

#### Device Breakdown
| Device | Before Clicks | After Clicks | Change | % Change |
|--------|-------------|-------------|--------|----------|
| Desktop | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Mobile | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Tablet | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |

#### Geographic Breakdown
| Country/Region | Before Clicks | After Clicks | Change | % Change |
|-------|-------------|-------------|--------|----------|
| [COUNTRY] | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |

#### Search Type Breakdown
| Search Type | Before Clicks | After Clicks | Change | % Change |
|-------------|-------------|-------------|--------|----------|
| Web | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Image | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Video | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| News | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |

### Behavioral Context (GA4)

| Metric | Before Period | After Period | Change |
|--------|-------------|-------------|--------|
| Organic Sessions | [VALUE] | [VALUE] | [VALUE]% |
| Engagement Rate | [VALUE]% | [VALUE]% | [VALUE]pp |
| Bounce Rate | [VALUE]% | [VALUE]% | [VALUE]pp |
| Avg Session Duration | [VALUE]s | [VALUE]s | [VALUE]% |
| Conversions (Organic) | [VALUE] | [VALUE] | [VALUE]% |

[Note: If GA4 data was not available, state: "GA4 data was not available for this analysis. Behavioral metrics are limited to GSC search performance data."]

### PPC Cross-Channel Analysis (GA4)

| Channel | Before Sessions | After Sessions | Change | % Change |
|---------|----------------|---------------|--------|----------|
| Organic Search | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Paid Search | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |
| Direct | [VALUE] | [VALUE] | [VALUE] | [VALUE]% |

**PPC Cannibalization Assessment:** [No PPC overlap detected / PPC targeting overlapping keywords — contributing factor / PPC recently paused — may have reduced organic CTR]

[Note: If GA4 data was not available, state: "Cross-channel analysis not available without GA4 data."]

---

## 2. Timeline & Correlation

### Loss Timeline vs Known Events

| Date/Week | Event | Correlation |
|-----------|-------|-------------|
| [DATE] | Traffic decline onset detected | — |
| [DATE] | [Algorithm update / Site change / Market event] | [Strong / Moderate / Weak / None] |
| [DATE] | [Additional event] | [Correlation strength] |

### Algorithm Update Correlation
[Description of which algorithm updates, if any, align with the loss onset. Include dates and correlation strength assessment.]

### Site Change Correlation
[Description of any site changes that align with the loss. If none reported by client, state that.]

### Seasonal/Market Context
[YoY comparison results. Google Trends data for key terms. Was there a market-wide demand shift?]

---

## 3. Keyword Impact Analysis

### Top 20 Losing Keywords

| # | Keyword | Before | After | Loss | % | Before Pos | After Pos | Pos Change |
|---|---------|--------|-------|------|---|-----------|----------|------------|
| 1 | [KEYWORD] | [VALUE] | [VALUE] | [VALUE] | [VALUE]% | [VALUE] | [VALUE] | [VALUE] |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

*Note: Cover CTR analysis, intent classification, and probable cause per keyword in narrative text below. Keep the table compact for readability.*

### Keyword Loss by Intent

| Intent | Keywords Affected | Total Click Loss | % of Total Loss |
|--------|------------------|-----------------|-----------------|
| Informational | [VALUE] | [VALUE] | [VALUE]% |
| Commercial | [VALUE] | [VALUE] | [VALUE]% |
| Transactional | [VALUE] | [VALUE] | [VALUE]% |
| Navigational | [VALUE] | [VALUE] | [VALUE]% |

### Search Demand Validation
[Were the keyword losses due to actual ranking drops, or did search demand decline? Google Trends / search volume data comparison.]

### Keyword Cluster Analysis
[Group losing keywords by topic/theme. Identify if specific topics were disproportionately affected.]

### Keyword Cannibalization

| Keyword | URL A | URL B | Severity | Impact |
|---------|-------|-------|----------|--------|
| [KEYWORD] | [URL] | [URL] | [Critical/High/Medium/Low] | [DESCRIPTION] |

**Cannibalization Summary:**
- Keywords with 2+ competing URLs: [VALUE]
- Keywords with URL switching between periods: [VALUE]
- Estimated click loss from cannibalization: [VALUE] clicks ([VALUE]% of total loss)

[If significant: Describe the cannibalization pattern and recommended consolidation strategy.]

---

## 4. Page Impact Analysis

### Top 20 Losing Pages

| # | URL | Before | After | Loss | % | Pos Change | Language |
|---|-----|--------|-------|------|---|------------|----------|
| 1 | [URL] | [VALUE] | [VALUE] | [VALUE] | [VALUE]% | [VALUE] | [LANG] |
| ... | ... | ... | ... | ... | ... | ... | ... |

*Note: Cover page type, keyword counts, and key issues in narrative text below. Keep the table compact for readability.*

### Page Loss by Type

| Page Type | Pages Affected | Total Click Loss | % of Total Loss |
|-----------|---------------|-----------------|-----------------|
| Blog/Content | [VALUE] | [VALUE] | [VALUE]% |
| Service/Product | [VALUE] | [VALUE] | [VALUE]% |
| Category/Hub | [VALUE] | [VALUE] | [VALUE]% |
| Homepage | [VALUE] | [VALUE] | [VALUE]% |
| Other | [VALUE] | [VALUE] | [VALUE]% |

### On-Page Health Summary
[Summary of on-page issues found across losing pages: title tags, meta descriptions, content length, internal linking, duplicate content flags.]

### Landing Page Engagement (GA4)

| URL | Before Sessions | After Sessions | Engagement Rate Change | Bounce Rate Change |
|-----|----------------|---------------|----------------------|-------------------|
| [URL] | [VALUE] | [VALUE] | [VALUE]pp | [VALUE]pp |

[Note: If GA4 data was not available, omit this section and note the gap.]

### Site Structure & Internal Linking Health

| URL | Internal Links In | Internal Links Out | Click Depth | In Sitemap | Structural Flag |
|-----|------------------|-------------------|-------------|-----------|----------------|
| [URL] | [VALUE] | [VALUE] | [VALUE] | [Yes/No] | [Orphan/Deep/OK] |

**Structural Summary:**
- Pages with <3 internal links (orphan risk): [VALUE] ([VALUE]% of losing pages)
- Pages with click depth >4: [VALUE]
- Pages missing from sitemap: [VALUE]
- Broken internal links found: [VALUE]

[If significant: Describe the structural pattern and its contribution to traffic loss.]

---

## 5. SERP & AI Overview Displacement

### AI Overview Detection Results

| Keyword | AI Overview Present | Site Cited in AIO | SERP Features Count | Position | CTR Before | CTR After | CTR Change |
|---------|-------------------|-------------------|--------------------| ---------|-----------|----------|------------|
| [KEYWORD] | [Yes/No] | [Yes/No] | [VALUE] | [VALUE] | [VALUE]% | [VALUE]% | [VALUE]% |

### Summary Statistics

| Metric | Value |
|--------|-------|
| Keywords checked | [VALUE] |
| AI Overviews detected | [VALUE] ([VALUE]%) |
| Site cited in AIO | [VALUE] ([VALUE]%) |
| Keywords with CTR anomaly (>30% CTR drop, stable position) | [VALUE] ([VALUE]%) |
| Estimated click loss attributable to AIO displacement | [VALUE] clicks ([VALUE]% of total loss) |

### Zero-Click Risk Assessment
[Assessment of which keyword categories face the highest zero-click risk and recommended response.]

---

## 6. Competitive Displacement

### Top Competing Domains

| Competitor | Keyword Overlap | Keywords They Gained | Estimated Traffic Gained |
|-----------|----------------|---------------------|------------------------|
| [DOMAIN] | [VALUE] | [VALUE] | [VALUE] |

### Competitive Content Analysis
[What are competitors doing differently on the keywords where they gained? Content depth, freshness, E-E-A-T signals, structured data.]

### New Entrants
[Any new domains appearing for previously held keywords?]

---

## 7. Backlink Health

### Profile Overview

| Metric | Current | Trend |
|--------|---------|-------|
| Total Backlinks | [VALUE] | [Stable/Growing/Declining] |
| Referring Domains | [VALUE] | [Stable/Growing/Declining] |
| Domain Authority (est.) | [VALUE] | [Stable/Growing/Declining] |

### Link Velocity (around loss onset)

| Period | New Links | Lost Links | Net Change |
|--------|----------|-----------|------------|
| [MONTH before loss] | [VALUE] | [VALUE] | [VALUE] |
| [MONTH of loss onset] | [VALUE] | [VALUE] | [VALUE] |
| [MONTH after loss] | [VALUE] | [VALUE] | [VALUE] |

### Lost High-Value Links
[List of significant lost referring domains with their authority and relevance.]

### Anchor Text Distribution

| Anchor Type | Percentage | Health Status |
|-------------|-----------|---------------|
| Branded | [VALUE]% | [Healthy/Concern] |
| URL/Naked | [VALUE]% | [Healthy/Concern] |
| Exact Match | [VALUE]% | [Healthy/Concern] |
| Partial Match | [VALUE]% | [Healthy/Concern] |
| Generic | [VALUE]% | [Healthy/Concern] |
| Other | [VALUE]% | [Healthy/Concern] |

### Competitor Backlink Comparison
[How does the link profile compare to top competitors?]

---

## 8. Technical Assessment

### Indexation Status

| Check | Result |
|-------|--------|
| Pages checked | [VALUE] |
| Pages indexed | [VALUE] |
| Pages not indexed | [VALUE] |
| Indexing issues detected | [LIST] |

### Core Web Vitals

| Page | LCP | CLS | INP | Performance Score | Status |
|------|-----|-----|-----|------------------|--------|
| [URL] | [VALUE]s | [VALUE] | [VALUE]ms | [VALUE] | [Pass/Fail] |

### Technical Issues Found
[List of technical issues: crawl errors, redirect chains, mobile usability, robots.txt blocks, canonical errors, etc.]

---

## 9. Content Quality Assessment

### Content-Business Alignment Analysis

**Business Context Model:**

| Element | Description |
|---------|-------------|
| **Core Business** | [Product/service category, primary function, industry vertical] |
| **Ideal Customer (ICP)** | [Primary buyer titles/roles, organization type, key professional concerns] |
| **Value Chain** | Pre-purchase: [problems ICP faces] / During use: [activities product supports] / Outcomes: [results achieved] |

**Alignment Classification (Losing Pages):**

| Ring | Pages | % of Losing Pages | Description |
|------|-------|-------------------|-------------|
| Ring 1 (Core) | [VALUE] | [VALUE]% | Directly about the product/service and its use cases |
| Ring 2 (ICP-Relevant) | [VALUE] | [VALUE]% | Topics the ICP deals with professionally |
| Ring 3 (Industry Adjacent) | [VALUE] | [VALUE]% | Same industry, but no special company insight |
| Ring 4 (Off-Topic) | [VALUE] | [VALUE]% | No meaningful business connection |

**Ring 2 Execution Quality:**

| Quality Level | Pages | % of Ring 2 | Description |
|--------------|-------|-------------|-------------|
| Strong | [VALUE] | [VALUE]% | Demonstrates the company's unique perspective and data |
| Adequate | [VALUE] | [VALUE]% | Competent but not differentiated from generic content |
| Weak | [VALUE] | [VALUE]% | Generic content with no unique company insight |

**Per-Page Alignment Detail (Top Losing Pages):**

| URL | Topic | Ring | Reasoning | Execution | Verdict |
|-----|-------|------|-----------|-----------|---------|
| [URL] | [TOPIC] | [RING] | [HOP CHAIN] | [Strong/Adequate/Weak] | [Topic aligned/Off-topic + execution assessment] |

**Alignment Diagnosis:**
[Narrative explaining whether the traffic loss is driven by genuinely off-topic content (Ring 3-4 = strategy misalignment) or by on-topic content that fails to demonstrate authority (Ring 2 weak execution = content authority gap). These are different problems with different recovery paths.]

### E-E-A-T Assessment (Top Losing Pages)

*Note: E-E-A-T scores below are contextualized by the alignment classification above. Ring 2 pages are scored on whether the content demonstrates the company's unique vantage point, not just general topic knowledge.*

| URL | Ring | Experience | Expertise | Authority | Trust | Composite Score | Risk Level |
|-----|------|-----------|-----------|-----------|-------|----------------|------------|
| [URL] | [RING] | [1-5] | [1-5] | [1-5] | [1-5] | [VALUE] | [Low/Medium/High/Critical] |

### Content Freshness

| URL | Last Updated | Content Age | Competitor Avg Age | Freshness Gap |
|-----|-------------|-------------|-------------------|---------------|
| [URL] | [DATE] | [MONTHS] | [MONTHS] | [VALUE months behind] |

### Helpful Content Risk Flags

[Assessment using alignment data from above. Distinguish between:
- **Content Strategy Misalignment** (Ring 3-4 dominant): off-topic content the site has no business publishing
- **Content Authority Gap** (Ring 2 Weak execution dominant): relevant topics where the content doesn't demonstrate the company's unique expertise
These require fundamentally different recovery approaches.]

### Content-Intent Mismatch Analysis

| Keyword | Current Page Format | SERP Dominant Format | Mismatch Type | Severity |
|---------|-------------------|---------------------|---------------|----------|
| [KEYWORD] | [FORMAT] | [FORMAT] | [Format/Media/Depth/Geo/None] | [High/Medium/Low] |

**Intent Mismatch Summary:**
- Keywords with confirmed format mismatch: [VALUE] ([VALUE]% of top losing keywords)
- Keywords where SERP intent shifted: [VALUE]
- Estimated click loss from intent mismatch: [VALUE] clicks ([VALUE]% of total loss)

[If significant: Describe the intent evolution pattern and recommended content reformatting strategy.]

---

## 10. Root Cause Diagnosis

### Diagnosed Causes (Ranked by Confidence)

| # | Root Cause | Confidence | Traffic Impact | Supporting Evidence | Contradicting Evidence |
|---|-----------|------------|---------------|--------------------|-----------------------|
| 1 | [PRIMARY CAUSE] | [VALUE]% — [Level] | [VALUE] clicks ([VALUE]%) | [Evidence list] | [Evidence list or "None"] |
| 2 | [SECONDARY CAUSE] | [VALUE]% — [Level] | [VALUE] clicks ([VALUE]%) | [Evidence list] | [Evidence list or "None"] |
| 3 | [CONTRIBUTING FACTOR] | [VALUE]% — [Level] | [VALUE] clicks ([VALUE]%) | [Evidence list] | [Evidence list or "None"] |

### Diagnosis Narrative
[2-3 paragraphs explaining the root cause diagnosis in plain language. How the evidence connects. Why alternative explanations were ruled out or ranked lower.]

### Data Gaps
[List any areas where additional data would strengthen or change the diagnosis.]

---

## 11. Recovery Plan

### Priority Scoring Method
```
Priority = (Traffic Impact x 0.4) + (Implementation Ease x 0.3) + (Confidence x 0.3)
```

### Critical Priority

Actions that address active harm or the primary root cause. These should be tackled first to stop further traffic loss.

| # | Action | Priority Score | Owner | Addresses Root Cause |
|---|--------|---------------|-------|---------------------|
| 1 | [ACTION] | [VALUE] | [ROLE] | [CAUSE #] |

### High Priority

Actions that directly support recovery and address confirmed contributing factors. These should follow once critical items are underway.

| # | Action | Priority Score | Owner | Addresses Root Cause |
|---|--------|---------------|-------|---------------------|
| 1 | [ACTION] | [VALUE] | [ROLE] | [CAUSE #] |

### Medium Priority

Actions that strengthen long-term positioning, close competitive gaps, and prevent recurrence. Schedule these once higher-priority work is in progress.

| # | Action | Priority Score | Owner | Addresses Root Cause |
|---|--------|---------------|-------|---------------------|
| 1 | [ACTION] | [VALUE] | [ROLE] | [CAUSE #] |

### Quick Wins (High Impact + Low Effort)
[List 3-5 actions that can be implemented immediately with minimal resources.]

---

*Report generated by Claude Traffic Loss Analysis Skill — [DATE]*
