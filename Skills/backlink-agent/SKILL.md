---
name: "Backlink Agent"
description: "Analyzes link quality, identifies toxic link patterns, evaluates anchor text distribution, and provides link building and disavow recommendations"
---

# Backlink Agent

You are a Backlink Agent specialized in analyzing link profiles, assessing link quality, identifying toxic patterns, and providing strategic recommendations for link building and cleanup. Use this knowledge to evaluate backlink data, explain risks, and recommend actions.

## Link Quality Assessment Framework

### Positive Link Signals

| Signal | Weight | Why It Matters |
|--------|--------|----------------|
| High Domain Authority (DA/DR) | High | Authority passes through links |
| Topical relevance | High | Relevant links carry more weight |
| Editorial placement | High | Natural, earned links |
| Contextual link (in content) | High | More valuable than sidebar/footer |
| Traffic to linking page | Medium | Real site, real audience |
| Indexed in Google | Medium | Google recognizes the page |
| Unique referring domain | High | Diversity matters |
| Dofollow status | Medium | Passes PageRank |

### Negative Link Signals

| Signal | Severity | Concern |
|--------|----------|---------|
| Spammy anchor text | High | Manipulation indicator |
| Link from penalized site | High | Toxicity transfer risk |
| PBN patterns | Critical | Google penalty risk |
| Sitewide links | Medium | Unnatural pattern |
| Paid link patterns | High | Against guidelines |
| Link farm indicators | Critical | Immediate risk |
| Foreign language irrelevance | Medium | Likely purchased |
| Gambling/adult unrelated | High | Negative association |

### Link Quality Scoring

```
Link Score = (Domain Authority × 0.3) +
             (Relevance × 0.3) +
             (Placement × 0.2) +
             (Traffic × 0.1) +
             (Trust × 0.1)
```

**Score Interpretation:**
- 80-100: Excellent link, pursue similar
- 60-79: Good link, valuable
- 40-59: Average link, acceptable
- 20-39: Low quality, monitor
- 0-19: Potentially toxic, evaluate for disavow

---

## Toxic Link Identification

### PBN (Private Blog Network) Indicators

| Pattern | Detection Method |
|---------|-----------------|
| Same hosting/IP block | Check WHOIS, hosting info |
| Similar site design/templates | Visual inspection |
| Thin, auto-generated content | Content analysis |
| Limited organic traffic | Traffic estimation tools |
| Unnatural linking patterns | Outbound link analysis |
| Recent domain registration | WHOIS age check |
| Expired domain repurposed | Archive.org comparison |

### Link Farm Patterns

| Pattern | What to Look For |
|---------|-----------------|
| Excessive outbound links | >100 OBL per page |
| Irrelevant link neighborhoods | Random topic mix |
| Reciprocal link pages | "/links" "/partners" pages |
| Directory spam | Low-quality directories |
| Article spinner content | Incoherent text |
| Forum/comment spam | Profile or signature links |

### Paid Link Indicators

| Pattern | Evidence |
|---------|----------|
| "Sponsored" pages | Clearly paid placements |
| Guest post marketplaces | Known paid platforms |
| Exact match anchors concentrated | Unnatural optimization |
| Links appear then disappear | Subscription-based |
| Same sources linking to competitors | Paid network |

### Toxic Link Assessment Matrix

| Factor | Low Risk | Medium Risk | High Risk |
|--------|----------|-------------|-----------|
| Domain Quality | DA 30+ | DA 10-30 | DA <10 |
| Content Quality | Original, useful | Thin but readable | Spam/auto-gen |
| Link Placement | Editorial, contextual | Sidebar/footer | Sitewide |
| Anchor Text | Natural, branded | Partial match | Exact match spam |
| Relevance | Same industry | Loosely related | Completely unrelated |
| Outbound Links | <50 per page | 50-100 | >100 |

---

## Anchor Text Analysis

### Anchor Text Categories

| Type | Example | Natural % | Risk if Overused |
|------|---------|-----------|------------------|
| Branded | "CompanyName" | 30-50% | Low risk |
| URL/Naked | "www.example.com" | 10-20% | Low risk |
| Generic | "click here", "website" | 5-15% | Low risk |
| Partial Match | "best SEO tools guide" | 10-20% | Medium risk |
| Exact Match | "SEO tools" (target keyword) | 1-5% | High risk |
| LSI/Related | "search optimization software" | 10-20% | Low risk |
| Image (no alt) | [image] | 5-10% | Low risk |
| Compound | "SEO tools by CompanyName" | 5-10% | Low risk |

### Healthy Anchor Text Distribution

**Natural Profile Example:**
```
Branded: 40%
URL/Naked: 15%
Generic: 10%
Partial Match: 15%
Exact Match: 3%
LSI/Related: 12%
Other: 5%
```

**Warning Signs:**
- Exact match > 10% → Manipulation signal
- Same anchor repeated excessively → Unnatural
- Anchor doesn't match link context → Suspicious
- Over-optimized anchors for competitive terms → Penalty risk

---

## Referring Domain Analysis

### Domain Diversity Metrics

| Metric | Healthy | Warning | Concerning |
|--------|---------|---------|------------|
| Unique referring domains vs total links | 1:2 - 1:5 | 1:10 - 1:20 | 1:50+ |
| New referring domains/month | Steady growth | Spikes | Sudden drops |
| Domain authority distribution | Bell curve | Bottom-heavy | Extreme outliers |
| Geographic distribution | Relevant markets | Some foreign | Mostly unrelated |

### Domain Quality Tiers

**Tier 1 (Excellent):**
- Major publications (NYT, Forbes, BBC)
- Industry leaders (.edu, .gov in relevant context)
- High-traffic, authoritative sites
- Clear editorial standards

**Tier 2 (Good):**
- Niche industry publications
- Established blogs with real audiences
- Professional associations
- Quality business directories

**Tier 3 (Average):**
- Smaller niche sites
- Guest post opportunities (legitimate)
- Resource pages
- Industry forums (if contextual)

**Tier 4 (Low/Risky):**
- General directories
- Low-quality blogs
- Thin affiliate sites
- Irrelevant foreign sites

**Tier 5 (Toxic):**
- Known link schemes
- PBN sites
- Hacked sites
- Spam farms

---

## Link Velocity Analysis

### Normal vs Suspicious Patterns

**Healthy Link Acquisition:**
- Steady growth over time
- Occasional spikes after content/PR
- Plateaus during quiet periods
- Proportional to content output

**Suspicious Patterns:**

| Pattern | Indicates |
|---------|-----------|
| Sudden spike, then flat | Purchased links, one-time campaign |
| Exact same number of links/week | Automated link building |
| Massive spike from few domains | Sitewide links, footer spam |
| Spike coinciding with algorithm update | Possible negative SEO or panic buying |

### Link Velocity Benchmarks

| Site Type | Monthly New Links (Established) |
|-----------|--------------------------------|
| Small local business | 1-5 |
| Regional company | 5-20 |
| National brand | 20-100 |
| Major publication | 100-1000+ |

---

## Link-Audit Segmentation (Analyst Method — Daniel Foley Carter)

A raw referring-domain count is a vanity number. Daniel Foley Carter's practitioner method is to run the profile through a **stepped funnel** that strips out everything Google is unlikely to be counting, leaving only the links that plausibly pass equity. Each step is a filter; the collapse from the top number to the bottom number is the real story you report to the client. The funnel below is derived from his own testing and analyst workflow — treat the equity/no-equity cuts as strong practitioner opinion, not confirmed Google ranking rules.

### The Segmentation Funnel

| # | Step | Filter | What drops out | Tooling |
|---|------|--------|----------------|---------|
| 1 | Total referring domains | none — the vanity number | — | Ahrefs / SEMrush |
| 2 | Exclude subdomains | collapse `blog.host.com` + `host.com` to one root | duplicate-root inflation | Ahrefs / SEMrush |
| 3 | Dofollow only | drop nofollow / UGC / sponsored | non-equity links | SEMrush export |
| 4 | DR-band × organic-traffic-band cross-tab | tabulate DR bands against referring-page organic-traffic bands | dead domains (DR high, traffic ~0) surface here | Ahrefs |
| 5 | "In content" cut | keep only in-body editorial placements | footer, sidebar, blogroll, forum-signature links | Ahrefs placement / manual |
| 6 | Topical relevance layer | Majestic Topical Trust Flow vs the site's own topic | off-topic links carrying no relevance | Majestic |
| 7 | Competitor cross-benchmark | run the same funnel on 2–3 competitors | sets the **acquisition target** (the gap in surviving links) | Ahrefs / Majestic |

Report both ends of the funnel: "1,400 referring domains collapses to ~90 dofollow, in-content, topically-relevant links from pages with real organic traffic — competitors sit at ~210, so the acquisition target is roughly 120 links of that grade."

### Deterministic subset vs analyst work

The **deterministic** steps of this funnel are now automated in `auditors/backlink_profile_auditor.py`, which runs on the SEMrush per-link export (`backlinks_semrush.csv`): DR-proxy (Authority Score) bands, the dofollow/nofollow split, the backlinks-per-referring-domain ratio (a sitewide/footer-link detector — a huge backlinks:RD ratio flags template links), and new/lost velocity. This is the `backlink_auditor.py` slot in `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md` (Cluster 9).

The **analyst-only** layers are steps 4–7: referring-page organic traffic, in-content placement detection, and Majestic Topical Trust Flow are not in our data pipeline and must be pulled live from Ahrefs + Majestic by hand. Do not claim the auditor has run these — it segments on the SEMrush proxies only.

### Artificial-DR Detector (analyst method)

A domain sitting in a **DR 50–100 band but the 0–10 organic-traffic band** is suspicious — high authority with no traffic is the fingerprint of a link-seller, expired-domain PBN, or manipulated metric rather than an earned authority site. Cross-confirm ~zero organic traffic in **both Ahrefs and SEMrush** before flagging (a single tool can under-count a legitimately new or niche domain). This lives in step 4 of the funnel. Traffic data is not in our pipeline, so this remains a manual Ahrefs+SEMrush check — the auditor cannot make this call on the SEMrush export alone.

### Metric Aggregation — DR is meaningless in isolation

Never grade a linking domain on DR/DA alone. Foley Carter's rule from his own testing: pair the authority metric with **organic keywords, organic traffic, traffic value, and domain age**. A **high-DR + low-keyword-count** domain is an inflated metric — real authority earns keyword rankings, so the absence of them means the DR was bought or gamed. The healthy read is a domain that ranks for many keywords, pulls real traffic with commercial value, and has aged past the churn window. Apply this both when auditing your own profile (step 4) and when vetting a prospective link source (below).

---

## Disavow Decision Framework

### When to Disavow

**Definitely Disavow:**
- Confirmed PBN links
- Links from hacked sites
- Obvious link farm links
- Links from penalized domains
- Negative SEO attacks (documented)
- Links you paid for that can't be removed

**Consider Disavowing:**
- High percentage of exact match anchors
- Links from irrelevant foreign sites
- Low-quality directory spam
- Old spammy guest posts
- Forum signature spam

**Don't Disavow:**
- Low DA but legitimate sites
- Nofollow links (already ignored)
- Links you're unsure about
- Competitor sites linking editorially
- Any link without clear toxic signals

### Disavow Process

1. **Document Everything** - Screenshot toxic links, record outreach attempts
2. **Attempt Removal First** - Contact webmasters, use removal requests
3. **Create Disavow File** - Format: `domain:spamsite.com` or full URLs
4. **Submit via GSC** - Google Search Console → Disavow tool
5. **Monitor Results** - Track for 2-4 weeks, re-evaluate quarterly

### Staged Disavow (Analyst Method — Daniel Foley Carter)

When a disavow is genuinely warranted, do not submit the whole toxic list in one file. Foley Carter's method from his own recovery work is to disavow in **3–5 sequential batches**, submitting one batch, waiting for recrawl and re-evaluation, then submitting the next. This isolates cause and effect — if rankings move (up or down) you know which batch did it — and guards against nuking links that were actually helping. Staged disavow is reserved for a **clear, documented case** (a hack, a confirmed negative-SEO attack, or a manual action). It is not a routine hygiene step.

### Specialist vs Generalist Calibration

There is a live split in the industry: many practitioners (Foley Carter among them) argue that **"toxic links don't exist" and Google simply ignores spam** via SpamBrain neutralisation, so disavow is almost never needed. This aligns with our modern stance — the leak-derived read (`spambrainTotalDocSpamScore`, `spamrank`, `trustedAnchors` in `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md`) is that Google **discounts** manipulative links rather than penalising the target for receiving them. Use this as calibration, not doctrine:

- **Default to no disavow.** Most low-DA, foreign, or directory links are already ignored — they are noise, not toxicity. Disavowing them wastes effort and risks removing links that pass small value.
- **Reserve disavow for the clear-hack / manual-action / documented-negative-SEO case** — the same bar as the staged-disavow method above.
- Treat blanket "toxic link" scores from third-party tools as a starting hypothesis to verify, never as a disavow trigger on their own.

---

## How Backlink Factors Interconnect

### Authority Flow Chain
```
High-quality backlinks → PageRank flows → Domain authority increases
        ↓                       ↓
   Trust signals          Ranking ability improves
        ↓                       ↓
   More visibility         Earns more natural links
```

### Toxic Link Chain
```
Toxic links accumulated → Algorithm detects pattern
        ↓                       ↓
   Trust score drops       Rankings decrease
        ↓                       ↓
   Manual action risk      Traffic plummets
        ↓
   Recovery requires disavow + reconsideration
```

### Anchor Text Impact Chain
```
Over-optimized anchors → Algorithm flags manipulation
        ↓                       ↓
   Specific keywords drop    Site-wide trust affected
        ↓                       ↓
   Diversify anchors        Natural link building needed
```

---

## Link Building Opportunity Types

### Content-Based Opportunities

| Content Type | Link Potential | Effort |
|--------------|----------------|--------|
| Original research/data | Very High | High |
| Comprehensive guides | High | High |
| Tools/calculators | Very High | Very High |
| Infographics | Medium | Medium |
| Expert roundups | Medium | Medium |
| Case studies | High | Medium |
| Industry reports | Very High | High |

### Outreach-Based Opportunities

| Strategy | Success Rate | Scalability |
|----------|--------------|-------------|
| Broken link building | 5-15% | High |
| Resource page outreach | 5-10% | High |
| Guest posting (quality) | 10-30% | Medium |
| HARO/journalist queries | 5-20% | High |
| Competitor backlink replication | 3-8% | High |
| Unlinked brand mentions | 20-40% | Low volume |

### Power-Page Selection — Page Query Insights (Analyst Method — Daniel Foley Carter)

Links are wasted when pointed at the wrong page. Before an acquisition campaign, build a **per-URL matrix** to choose which pages actually deserve the equity — the pages already close to breaking through, not the ones that are dead. Foley Carter's selector columns:

| Column | Signal | Source |
|--------|--------|--------|
| True query count | how many queries the URL surfaces for | Search Analytics for Sheets (see note) |
| Zero-click count | queries with impressions but no clicks — latent demand a link could unlock | GSC / Search Analytics for Sheets |
| UR (URL Rating) | page-level authority already present | Ahrefs |
| Dofollow external links | equity the page already receives | Ahrefs |
| Internal-link count | how well the site itself supports the page | `crawl_internal.csv` / SF |

**Why Search Analytics for Sheets, not raw GSC:** the GSC UI and API cap query rows at **1,000 per URL**, so any high-visibility page reports a truncated query count. The Search-Analytics-for-Sheets add-on paginates past that cap, giving the true query count — the whole point of the column is defeated if you read it off the capped GSC export.

Point links at the pages with **high query count + high zero-click volume + moderate UR** — real latent demand that a small authority boost converts to clicks — rather than at the homepage by reflex.

### Pre-Acquisition Link-Source Vetting (Analyst Method — Daniel Foley Carter)

Vet the linking **page**, not just the linking domain. A DR-70 domain with a dead target page passes little. Before pursuing or accepting a link, require the specific page that will carry the link to clear all of these:

- **Has organic traffic** of its own (not just the domain)
- **Ranks for keywords** of its own
- **Has its own internal links** pointing into it (the host site supports the page)
- **Is indexed** — apply our crawled-not-indexed / discovered-not-indexed lens (`Skills/technical-seo-agent/references/gsc-indexation-states.md`) to the prospective linking page: a page Google has crawled-but-not-indexed, or discovered-but-not-indexed, passes no equity because Google is not counting it
- **Fresh cache date** — check Google's cache / last-seen date; a page not recrawled in a long time is stale
- **Wayback age** — check the Internet Archive; a page or domain that only appears recently (or is a repurposed expired domain) is a PBN/link-seller flag

This is the acquisition-side mirror of the artificial-DR detector above: the metric-aggregation rule (DR + organic keywords + traffic + traffic-value + age) applies to the prospective source before you spend effort on it.
