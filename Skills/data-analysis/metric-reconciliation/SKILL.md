---
name: "Metric Reconciliation"
description: "When two or more data sources disagree on the same metric (audit doc says X, SF crawl says Y, GSC says Z), force explicit reconciliation BEFORE the number lands in a client deliverable. Defines the source-of-truth hierarchy and the protocol for resolving discrepancies. Triggered whenever the same fact appears in two sources with different values."
---

# Metric Reconciliation

When sources disagree, the worst thing you can do is silently pick one. The second-worst is to pick the wrong one. This skill forces explicit reconciliation.

## When this skill applies

- The same metric, count, or fact appears in two or more sources with different values
- An audit doc says one number; the underlying data file says another
- GSC, GA4, DataForSEO, and SF crawl data disagree on URL counts / impression numbers / position
- Live HTML disagrees with what a static crawl reported (page was edited since)
- A client's verbal confirmation disagrees with what the website displays

## Source-of-truth hierarchy (when in doubt)

Ranked from most authoritative to least, for SEO-related claims:

| Rank | Source | Use for |
|------|--------|---------|
| 1 | **Live HTML (today)** | Page content, current meta tags, current copy, specific text claims |
| 2 | **GSC URL Inspection API** | Indexation status, Google's view of canonical, last-crawl date |
| 3 | **GSC Search Analytics** | Actual organic performance — clicks, impressions, position, CTR |
| 4 | **Current Screaming Frog crawl** (≤7 days old) | Site structure, internal linking, technical issues |
| 5 | **DataForSEO live SERP / backlink** | Third-party backlink + SERP estimation |
| 6 | **Older Screaming Frog crawl** (>7 days old) | Historical reference only — re-verify before citing |
| 7 | **Prior audit doc** (markdown / Excel) | Reference only — never the primary citation |
| 8 | **Memory / prior session notes** | Verify before using |
| 9 | **Vendor-provided estimates** (SEMrush traffic estimates, etc.) | Lowest weight — directional only |

When two sources disagree, the higher-ranked source wins by default — but always document the disagreement.

## The reconciliation protocol

When you detect a discrepancy:

### Step 1 — Make the disagreement explicit

State both values, with attribution:
> "Source A (audit doc, 2026-04-08) says 45 empty-anchor links.
> Source B (SF all-inlinks export, same date) says 779 empty-anchor links."

### Step 2 — Run the math yourself (don't trust either source blindly)

Dispatch the `data-validator` subagent to independently re-derive the number from the most authoritative available source. Get a third value if the two existing sources disagree.

### Step 3 — Identify the cause of disagreement

The most common causes, in order of frequency:

1. **Different filter/dedup logic** — e.g., "Source A counted unique destinations, Source B counted all link instances"
2. **Different time window** — Source A pulled data on day X, Source B on day Y
3. **Different scope filter** — e.g., one source excluded paginated pages, the other didn't
4. **Stale data** — the underlying pages changed between the two captures
5. **Tool bug or export issue** — column was misnamed, encoding broke a delimiter, etc.

### Step 4 — Pick the canonical number

Always the value from the highest-ranked source you can defend. Document why.

### Step 5 — Surface the reconciliation in the deliverable

Don't hide it. The deliverable should state:
> "Reported count vs. actual: The April 8 audit doc cited 45 empty-anchor links. Live SF data shows 779 truly-empty hyperlinks (no anchor + no alt). The 779 figure is correct; the discrepancy is likely due to the audit doc deduplicating by destination URL (~18 unique destinations). 779 is the count used in this implementation plan."

This both corrects the record AND demonstrates rigor to the client.

## When the discrepancy is small (off-by-one, rounding)

If two sources differ by <5% AND the smaller source is the more authoritative one, you can use the larger number with a note like "approximately X" without full reconciliation. If the more authoritative source is larger, use the larger number without comment.

## When the discrepancy is large (order of magnitude)

Always full reconciliation. Always document. Never quietly pick one.

## Common reconciliation patterns by audit type

| Discrepancy | First check | Source of truth |
|-------------|-------------|-----------------|
| Audit count vs. actual SF count | Run pandas filter on raw SF export | SF export wins — but check dedup logic |
| Live page text vs. audit-quoted text | Live fetch the page now | Live HTML wins (page may have been edited) |
| GSC clicks vs. GA4 sessions | Both correct; they measure different things | Don't reconcile — explain the difference |
| GSC impressions vs. SEMrush "Traffic" | GSC | GSC is real Google data; SEMrush is estimated |
| DataForSEO SERP position vs. user's manual check | Run live SERP fetch with location param | DFS live with correct geo |
| Prior audit's "X is broken" vs. current state | Live verify | Live state wins |

## What this skill MUST NOT do

- Never silently pick a number when sources disagree.
- Never present a metric without source attribution.
- Don't override the source-of-truth hierarchy without a documented reason in the deliverable.
- Don't skip Step 5 (surfacing the reconciliation in the deliverable). The reconciliation IS part of the value the client is paying for.

## Reference cases

### SameDay empty anchor count (April 2026)
- Audit doc: 45 links
- SF all-inlinks export: 2,301 hyperlinks with empty anchor; 779 truly empty (no anchor + no alt)
- Reconciled to: 779 (SF export wins; audit doc likely deduplicated by destination URL)
- Documented in: `Clients/SameDay/Full SEO Audit/sameday_empty_anchors_plan.xlsx` Summary sheet

### Superior plumbing page "Over 30 Years" (April 2026)
- Semantic audit: "Over 30 Years" claim on plumbing page
- Live verification (3 weeks later): no tenure claim on the page
- Reconciled to: page was edited; the audit's flagged text is no longer present
- Documented in: `Clients/Superior/Full SEO Audit/superior_founding_year_plan.xlsx` Pages-to-Sweep sheet
