---
name: "On-Page SEO Agent"
description: "Ultimate SEO Agent audit skill: Analyzes content optimization, heading structure, meta elements, internal linking, and content quality for on-page SEO improvements"
---

# On-Page SEO Agent

You are an On-Page SEO Agent specialized in analyzing content quality, meta elements, heading structure, and internal linking. Use this knowledge to identify issues, explain their impact on rankings and user engagement, and recommend prioritized improvements.

## Pipeline stage assignment

> **Stage 4 — Ranking**, with two exceptions below.
> `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`

Everything in this skill is gated behind stages 1 to 3. See
[stage-4-ranking.md](../technical-seo-agent/references/stage-4-ranking.md) for the stage
contract. Concretely, **do not run on-page work on a URL that is not crawlable, does not
render its content into the raw HTML, or is not indexed.** There is no position to improve.

**Two exceptions that are not Stage 4:**

- **A title, H1 or meta element that exists only after JavaScript executes is a Stage 2
  finding**, and Critical rather than cosmetic, because those elements participate in the
  render-eligibility gate before the JS runs.
- **Internal linking is genuinely dual-stage**: a Stage 1 discovery mechanism and a Stage 4
  equity signal. When a page is not being crawled, treat internal links as Stage 1.

**Binding test before any element becomes a finding.** Name the loss. An absent H1 on a page
already ranking for its target terms is **Low / Infrastructure Hygiene**, because Google
derives topic from title, body and links. Weak titles on pages with **no impressions** are not
binding either, and the reason there are no impressions is the actual finding. Volume never
converts a non-binding absence into a binding one. Procedure in
[seo-audit-methodology/SKILL.md](../seo-audit-methodology/SKILL.md).

## Reference to Consult

Before running any on-page pass, load `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md`. It is the consolidated, leak-grounded checklist for the clusters this agent owns — title, meta, heading, content, internal-link, and content-quality — and it carries the underlying May 2024 Content Warehouse leak attributes with the same "documented in the leak, not a Google-confirmed lever" hedging used throughout this framework. Consult it for the attribute-level detail; this skill covers the diagnosis-and-recommendation workflow. Do not duplicate the checklist's attribute tables here — link to them.

## Title Tag Optimization

### Issues by Severity

**Critical:**
| Issue | Impact | Fix |
|-------|--------|-----|
| Title Tag Missing | No title in SERPs, poor CTR | Add descriptive title |
| Title Tag Empty | Same as missing | Add content to title |
| Title Outside Head | May not be recognized | Move to `<head>` |

**High:**
| Issue | Impact | Fix |
|-------|--------|-----|
| Multiple Title Tags | Inconsistent display | Keep single title |
| Duplicate Titles (site-wide) | Keyword cannibalization | Unique titles per page |

**Medium/Low:**
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

### Title–Query Alignment (`titlematchScore`)

Length and structure are not the whole title check. Run an explicit **title-to-query match check**: does the title lexically and semantically match the queries the page actually ranks for (from GSC) or is trying to win? The May 2024 Content Warehouse leak documents a `titlematchScore` attribute — and it sits in the site-level quality module (NSR), described as a site-level score of how well the site's titles match user queries. That placement matters: the *pattern* of title–query matching across the site is what gets scored, so a systemic misalignment (every service page titled with internal jargon, say) is a site-level finding, and title fixes compound — fixing one page helps that page, fixing the pattern moves the sitewide signal. Treat it as leak-derived and directional, not a confirmed weighting: Google has not confirmed how, or how heavily, it is used. The direction is consistent with the rest of the leak's click-signal picture, though — a title that doesn't overlap the query earns fewer clicks, which feeds NavBoost against the page.

How to check:
1. Pull the page's top queries by impressions from GSC (`get_search_by_page_query`).
2. Compare the title against those queries. Does the primary head term appear? Are the modifiers users actually search (e.g., "cost", "near me", "vs") reflected?
3. Flag a mismatch when the page is shown for (or ranks on) a query cluster the title never references. That is a title-query alignment gap — a distinct finding from "title too long" or "duplicate title."

Fix by front-loading the query the page is closest to winning, not the term the client wishes it ranked for. Do NOT keyword-stuff the title to force a match — an over-optimized title that no longer reads naturally depresses CTR, which is the very signal title-query alignment exists to protect. For the attribute-level detail, see the title cluster in `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md`.

### Title → H1 Rewrite Mechanism

Google does not always display the title you write. When it judges a `<title>` weak, truncated, keyword-stuffed, or mismatched against the page's actual content, it rewrites the displayed SERP title — and practitioner testing (Daniel Foley Carter, derived from his own before/after SERP monitoring) points to the page's **H1 as the most common source Google pulls the replacement from**. Treat this as a derived-from-testing observation, not a Google-confirmed rule: Google confirms it rewrites titles, but not the precise source hierarchy it draws from.

The practical consequences:

- **A strong H1 is your insurance against a bad rewrite.** If the title gets overridden, a clear, query-aligned H1 means the rewritten title lands on-target. A vague H1 ("Welcome", "Our Services") leaves Google nothing good to fall back on, and the auto-generated replacement is usually worse for CTR than a decent title would have been.
- **Title and H1 should align but not be identical** (see "Title Same as H1" above). Align them on the head term; let each cover slightly different modifiers so the page signals breadth without either element reading as a carbon copy of the other.
- **Diagnose rewrites in the field.** Compare the title you shipped against the title actually shown in the SERP (`mcp__dfs-mcp__serp_organic_live_advanced` or a manual search). A systematic rewrite across many pages is a template-level title mismatch — fix the title template, not one page at a time.

---

## Meta Description Optimization

### Issues by Severity

| Issue | Severity | Impact |
|-------|----------|--------|
| Meta Description Missing | High | Google auto-generates (often poorly) |
| Meta Description Empty | High | Same as missing |
| Meta Description Outside Head | High | May not be recognized |
| Multiple Meta Descriptions | Medium | Confusion on which to use |
| Too Short (<120 chars) | Low | Incomplete message |
| Too Long (>160 chars) | Low | Truncated |

### Best Practices

**Character Limits:**
- Desktop: ~155-160 characters
- Mobile: ~120-130 characters

**Pixel-width caveat for emojis, special characters, and non-ASCII content:**

Google truncates meta descriptions by **pixel width**, not character count. The character-count heuristic above is calibrated for standard Latin-1 ASCII content. Some characters consume significantly more pixel width than a single ASCII character, which means a meta description well under the 160-character limit can still truncate in the SERP. Watch for:

| Character type | Pixel width relative to ASCII | Impact on length budget |
|---|---|---|
| Standard ASCII (a-z, A-Z, 0-9, basic punctuation) | 1x | Baseline — 160 chars fits ~985px desktop |
| Wide ASCII characters (W, M, capital letters in general) | 1.3–1.6x | Heavy use of uppercase or wide letters shortens effective character budget |
| Emojis (★, ✓, ⚡, 🔥, ✨, etc.) | 2–3x | A single emoji eats the budget of 2–3 ASCII characters; emojis are also stripped or replaced by Google in many SERPs |
| En/em dashes (–, —), curly quotes ("", '') | ~1x but counted differently by some CMS character-counters | Cosmetic risk: CMS character counter says 158, actual budget consumed is similar |
| Spanish/accented characters (á, é, í, ó, ú, ñ, ¿, ¡) | ~1x | No meaningful pixel-width penalty; character-count heuristic remains accurate for Spanish content |

**Practical rules:**

1. **Hard cap on emojis: 2 per meta description, never adjacent.** Google strips most emojis from the SERP. The ones that survive (rare star/check marks in some categories) still eat 2–3x pixel budget. If a meta description contains emojis, treat each one as ~3 characters of budget consumed regardless of what the CMS counter says.
2. **Spanish content can use the same 155–160 character target as English.** The accented-character penalty is negligible. Don't over-engineer this.
3. **When in doubt, paste the meta into the Google SERP Snippet Preview tool** (or any pixel-accurate preview tool) before shipping. Don't trust the CMS character counter for any meta description containing emojis or unusual special characters.
4. **Title tags follow the same rule** — same emoji penalty, same Spanish parity, same advice to verify in a pixel-accurate preview when special characters are present.

**Why this exists:** A client's title or meta with "⚡ Free Shipping ⚡" looks fine at 145 characters in the CMS but truncates mid-word in the SERP because the lightning bolts consume the pixel budget of ~6 ASCII characters. Adopted (in scope-limited form) from Islam Eldiasti's technical-SEO-skill-claude framework, which raises the byte-vs-character issue more broadly. This project deliberately scopes the rule to emojis/special-character cases since the client roster is English and occasional Spanish — both of which the character-count heuristic handles accurately on its own.

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

### Proper Heading Structure

```html
<h1>Main Page Topic (One per page)</h1>
  <h2>Major Section 1</h2>
    <h3>Subsection 1.1</h3>
    <h3>Subsection 1.2</h3>
  <h2>Major Section 2</h2>
    <h3>Subsection 2.1</h3>
      <h4>Detail 2.1.1</h4>
```

**Common Mistakes to Identify:**
- Skipping levels (H1 → H3, no H2)
- Using headings for styling only
- Multiple H1s
- Non-descriptive headings ("More Information")
- Keyword stuffing in headings

### Headings Express Hierarchy, Not Keywords

Headings exist to express the **document's logical structure** — the outline a reader (and a parser) uses to navigate the page. They are not keyword slots. Practitioner method (Daniel Foley Carter, derived from testing): build the H2/H3 tree as if you were writing a table of contents for the topic, then check that each heading honestly labels the section beneath it. Stuffing the target keyword into every H2 does not add relevance — it degrades the structural signal and reads as low-effort to a model-based quality assessment (see Tone, Style & Internal Consistency below). Treat the "keywords in headings help ranking" belief as unsupported by his testing; the value is in the *tree*, not the terms it carries.

Practical rules:

- The hierarchy must be **semantically nested**, not just visually nested — an H3 must be a genuine sub-topic of the H2 above it. Skipped levels (H2 → H4) break the outline the parser reads.
- Prefer headings that **answer or name a sub-question** (aligned to the query clusters the page targets) over headings that repeat the head keyword. "How long does installation take?" is a stronger H2 than "Installation Keyword Services."
- One H1, then a clean H2/H3 descent. Judge the outline by whether someone could reconstruct the page's argument from the headings alone.

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

### Content-Format Matching (Derive Format From the SERP)

Word count answers "how much"; it does not answer "in what shape." Before recommending expansion, derive the required **format** from the SERP by finding the *repeating structural pattern* across the top ~8-10 intent-matched results. Practitioner method (Daniel Foley Carter, derived from testing): the format Google is already rewarding for a query is visible in what the ranking pages have in common — copy the winning shape rather than imposing a default long-form template. Treat as derived-from-testing and directional, not a confirmed algorithm rule.

What to read off the SERP:

- **Snippet-unit vs long-form.** If the top results are short, scannable, digestible units (definition boxes, step lists, short direct answers, comparison tables), the query wants **short digestible snippet units** — not a 2,000-word essay. If they are deep long-form guides, it wants long-form. Match the dominant shape, don't fight it.
- **Mandatory imagery.** If the SERP is image-driven (an image pack, results with prominent thumbnails, how-tos with step photos), original imagery is **not optional** — a text-only page is structurally under-built for that query regardless of word count. This ties into Media Embeddings as an Engagement & Quality Lever below.
- **Structural furniture.** Tables, FAQ blocks, numbered steps, calculators — if most of the top results share a structural element, treat it as table stakes for the format.

The anti-pattern this prevents: **writing long, then hacking it short.** Don't draft a long-form article and trim it to imitate a snippet page — decide the format up front from the SERP, then write natively to it. A page written long-then-cut reads as padded and reads as the wrong shape for the query.

### Category / Collection Page Intent Guard

Never recommend article-length body content on a commercial category or collection page. Practitioner method (Daniel Foley Carter, derived from testing), consistent with the content-pruning auditor's rewrite logic: a category/collection page ranks on **commercial** intent — the searcher wants products, filters, and prices, not an essay. Bolting a 1,500-word guide onto a category page shifts the page's apparent intent from commercial toward informational, which can **drop the commercial rankings the page exists to win**.

Rules:

- Category/collection pages get a **short unique intro** (the 300-500 word "unique intro, not just product list" figure in the table above) plus optional supporting copy *below* the product grid — never a long article above it that pushes products below the fold.
- If a topic genuinely needs article-length treatment, put it on a **separate informational URL** (a guide or blog post) and link the category page to it — don't merge the two intents onto one URL.
- This is the on-page mirror of the guard in `auditors/content_pruning_auditor.py`: that auditor's Rewrite action explicitly warns against padding to hit a word count, and category pages are the clearest case where more words actively harm. When an audit flags a category page as "thin," the fix is a sharper intro and better product/facet coverage — not article body content.

### Thin Content Indicators

| Signal | Threshold | Action |
|--------|-----------|--------|
| Word count | <300 words | Expand or consolidate |
| Unique content ratio | <60% | Increase originality |
| Boilerplate ratio | >40% | Reduce repeated elements |
| No substantive paragraphs | - | Add meaningful content |

### Information Gain (unique value vs. what already ranks)

Word count and thin-content checks measure a page *in isolation*. **Information gain** measures it *against the SERP*: does this page add anything the pages already ranking for the query don't already say? Two pages can both clear the word-count floor and both read as "original" on their own, yet one is the tenth restatement of the same five points and the other adds a genuinely new data point, method, example, or perspective. Google's information-gain work is documented in its patent literature (the "information gain score" patents), where documents a user reads later in a session are scored on the *additional* information they contribute beyond what the user has already seen. Treat it as a directional concept, not a confirmed live weighting — but it is a distinct axis from the leak's `OriginalContentScore`, which only scores a short page's own originality without reference to what competitors already cover.

How to assess it:
1. Pull the top 5-10 ranking URLs for the target query (SERP tool or manual inspection).
2. List the sub-topics, data points, and angles they collectively cover — the "table stakes" set for the query.
3. Ask what the client's page contributes *beyond* that set: proprietary data, first-hand testing, a named process, a local specific, an updated figure, a defensible contrarian take, an original visual.
4. If the honest answer is "nothing the top results don't already have," more words will not help — the page needs a differentiated angle, not expansion.

Why it matters: adding length that only restates the consensus is exactly the failure mode information gain names — long enough to dilute focus, but adding nothing Google can't already get from the incumbents. This is the on-page counterpart to the content-expansion skill's information-gain gate; see `Skills/content-expansion/SKILL.md`. For the leak/patent attribute detail, see the content-quality cluster in `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md`.

### E-E-A-T Signals to Check

- **Experience**: First-hand knowledge demonstrated
- **Expertise**: Author credentials, depth of coverage
- **Authoritativeness**: Citations, external references
- **Trustworthiness**: Accurate info, clear sourcing

### Readability Factors

- Short paragraphs (2-4 sentences)
- Subheadings every 300-400 words
- Bulleted/numbered lists where appropriate
- Simple language (Flesch-Kincaid target: 60-70)

### Tone, Style & Internal Consistency

Flesch-Kincaid (above) only measures sentence and word mechanics. It says nothing about whether the writing is appropriate in **tone**, consistent in **style**, or free of **internal contradictions** — all of which are content-quality dimensions a human quality rater penalizes and which Google's model-based content assessment is positioned to catch. The May 2024 leak documents that Google applies model-based ("LLM-scored") judgments of content effort/quality per document, not just mechanical readability metrics; treat that as leak-derived evidence that prose quality is evaluated qualitatively — not as a confirmed scoring formula.

Check for:
- **Tone/sentiment mismatch with intent.** A transactional service page written in a detached, encyclopedic register (or a YMYL topic written in a flippant one) mismatches what the query wants. Match register to intent.
- **Style inconsistency within the page.** Point of view that switches between "we", "you", and "the company"; heading phrasing that flips between questions and noun phrases; formatting that changes mid-article. These read as low-effort, stitched-together content.
- **Internal contradictions.** The intro states one figure and the FAQ states a different one; the H1 promises "24/7 service" but the body says "business hours only"; a freshly-refreshed section contradicts an un-refreshed one. Contradictions undercut trust (the T in E-E-A-T) and are concrete, findable defects — flag every one.

Fix by editing to a single consistent voice, reconciling every conflicting fact against the source of truth, and matching tone to the query's intent. See the content-quality cluster in `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md`.

### Sentiment Polarity Matching

Beyond register and tone, match the **sentiment polarity** of the content to the polarity the query implies. Practitioner method (Daniel Foley Carter, derived from testing): queries carry an implicit evaluative charge, and pages whose polarity matches that charge tend to satisfy the searcher better — feeding the same click signals (`Skills/technical-seo-agent/references/click-signals-abc-framework.md`) that intent matching does. Treat as derived-from-testing and directional, not a confirmed weighting.

Examples:

- A query like "is X safe" or "X side effects" carries a cautionary polarity — a relentlessly upbeat sales page mismatches it. The page should acknowledge the concern directly *before* reassuring.
- "best X" / "is X worth it" carries a positive, evaluative polarity — the page should lead with a confident, affirmative verdict, not hedge for three paragraphs.
- Problem-shaped queries ("X not working", "fix X") want a solution-focused, empathetic polarity, not marketing gloss.

Check: read the query aloud, name the emotion behind it, then confirm the page's opening and framing match that emotion. A polarity mismatch is a findable, fixable defect — flag it alongside tone mismatches.

### Entity / Knowledge-Graph Mapping

Schema `@id` wiring (covered in the technical/schema references) is only the machine-readable half of entity SEO. The content half is **consistent entity naming**: refer to each key entity — the business, a product, a service, a person, a place — by the same canonical name throughout the page and the site, rather than rotating through synonyms, abbreviations, and near-variants. Inconsistent naming causes the same problem NAP inconsistency causes in local SEO — it makes Google's entity matching less confident about which real-world thing the content is about. The May 2024 leak documents that Google annotates documents with the entities it detects per page; treat that as leak-derived evidence entities are captured, not as a confirmed ranking weight.

Two practical checks:
- **Entity naming consistency.** Choose one canonical surface form per key entity and use it consistently. A first mention can gloss the variants ("Odoo, formerly OpenERP"), then settle on the one name.
- **Entity home.** Every entity worth ranking for should have one page that is its clear "home" — the definitive, most complete page for that entity — with internal links from supporting content pointing to it using the entity's canonical name as anchor text (this ties into Internal Linking Analysis below). Diffuse coverage, where five pages each half-cover an entity and none is its home, dilutes the signal.

This is beyond schema `@id`, and the two reinforce each other. For the schema `@id` entity-graph mechanics, see `Skills/technical-seo-agent/references/seo-fundamentals-2026.md`.

---

## Internal Linking Analysis

### Link Issues by Severity

**High:**
| Issue | Impact | Fix |
|-------|--------|-----|
| Orphan pages (no internal links) | Not discovered by crawlers | Add contextual links |
| Single inlink only | Low PageRank flow | Add more internal links |
| No outgoing links | Dead end for crawlers | Link to related content |

**Medium:**
| Issue | Impact | Fix |
|-------|--------|-----|
| Non-descriptive anchor text | Weak topical signals | Use descriptive anchors |
| Image links without alt text | No anchor text signal | Add descriptive alt |

### Anchor Text Guidelines

| Type | Example | Quality |
|------|---------|---------|
| Exact match | "SEO audit tools" | Good if natural |
| Partial match | "best tools for SEO audits" | Very good |
| Related | "website analysis software" | Good |
| Generic | "click here", "read more" | Poor |
| URL | "www.example.com/page" | Poor |

### PageRank Flow Concept

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
| No dimensions specified | Medium | CLS issues | Add width/height |
| Oversized images | Medium | Slow loading | Resize appropriately |

### Alt Text Guidelines

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

### Media Embeddings as an Engagement & Quality Lever

The issues above treat images as an accessibility concern (alt text) and a layout-stability concern (CLS / dimensions). Embedded media is also a **content-richness and engagement** lever in its own right. The May 2024 leak documents that Google stores per-document media data — images and video embedded on the page — as part of its content understanding, not merely as files to be indexed. Treat this as leak-derived and directional: it is evidence that original, relevant embedded media contributes to how the page is assessed and how well it holds the user (engagement feeding the click signals in `Skills/technical-seo-agent/references/click-signals-abc-framework.md`), not a confirmed standalone ranking weight.

What to look for:
- **Media presence on media-appropriate pages.** A how-to, product, or comparison page with zero supporting images/video/diagrams is under-built for its intent, independent of word count. Recommend original visuals (screenshots, process diagrams, product photography, a short demo video) that a text-only competitor lacks — this is an information-gain move as much as a media one.
- **Original vs. stock/duplicate media.** Stock imagery reused across the web carries little signal; original media (first-hand photos, custom diagrams, video the client produced) is what differentiates and what supports E-E-A-T "Experience."
- **Relevance over decoration.** Media should illustrate the content, not fill space. Decorative filler adds page weight — and, if overdone, a `clutterScore` risk — without adding value.

Alt text, dimensions, and file weight (the table above) still apply to every embed — this subsection is the *why include rich media at all* layer on top of the *how to ship it cleanly* layer.

---

## Content Cannibalization

### Signs of Cannibalization

1. Multiple pages ranking for same keyword
2. Ranking position volatility
3. Neither page ranking as well as expected
4. Traffic split between pages

### Resolution Strategies

| Scenario | Solution |
|----------|----------|
| Two pages, one better | 301 redirect worse → better |
| Two pages, both valuable | Merge into comprehensive page |
| Similar but different intent | Differentiate titles, content focus |
| Pagination | Implement rel=canonical to page 1 |
| Near-duplicate products | Unique descriptions, canonical to primary |

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

---

## Content Gap Types to Identify

1. **Keyword Gaps**: Competitors rank, you don't
2. **Topic Depth Gaps**: Surface-level coverage only
3. **Content Type Gaps**: Missing how-to, comparison, FAQ content
4. **Intent Gaps**: Only informational, no commercial content

### Gap Prioritization Formula

```
Priority = Search Volume × Relevance × Competition Gap × Conversion Potential
```

### Single-Page Content Expansion (Use When)

For the inverse pattern — analyzing what content a *specific existing page* should add based on its own GSC query mix (intra-page gaps rather than competitive gaps) — use `Skills/content-expansion/SKILL.md` and the `/page-content-expansion` slash command. This is the right tool when:

- A specific URL has strong impressions but weak CTR/position
- A client asks "what should I add to this page?"
- An audit surfaces a striking-distance page that needs a focused expansion plan

The content-expansion workflow runs an expansion-vs-cannibalization gate (calling `Skills/cannibalization/SKILL.md`) before recommending any new content, which the competitive gap analysis above does NOT do.
