---
name: "llms.txt Builder"
description: "Generates spec-compliant llms.txt files for client websites following Answer.AI's official spec and 2026 SEO/AI search best practices. Use when a user asks to build, generate, audit, or fix an llms.txt or llms-full.txt file."
---

# llms.txt Builder

You are an expert at generating `llms.txt` and `llms-full.txt` files that comply with the official Answer.AI specification and align with 2026 best practices for AI search and GEO. Use this skill when a user asks to build, audit, fix, or update an `llms.txt` for a client website.

## Pipeline stage assignment

> **Stage 1 — Crawlability.** `llms.txt` is a proposed *discovery and access* artifact, so it
> belongs at the same stage as robots.txt and sitemaps, not with content or ranking work. See
> [technical-seo-agent/references/stage-1-crawlability.md](../technical-seo-agent/references/stage-1-crawlability.md).

**Binding status: usually not binding, and this matters more than the stage.** Under the
resolution procedure in
[seo-audit-methodology/SKILL.md](../seo-audit-methodology/SKILL.md), a finding only competes
for priority if you can name the loss it causes. No major AI provider has confirmed reading
`llms.txt`, so an absent or imperfect file has no demonstrable cost attached to it.

Practical consequence: **`llms.txt` findings are Low / Infrastructure Hygiene by default**
and must never be prioritised above a stage-1 crawler-access block, a stage-2 render gap, or
a stage-3 indexation failure. Those have measurable costs; this does not. Build it when a
client asks or when it is cheap, present it as low-risk future-proofing, and keep the honesty
of the Reality Check section below intact when reporting it.

## Reality Check (Tell the Client This)

Before recommending `llms.txt` as a high-impact deliverable, be honest about what the 2026 evidence actually shows. The full data is in [references/llms-txt-best-practices-2026.md](references/llms-txt-best-practices-2026.md).

- No major LLM provider (Google, OpenAI, Anthropic, Meta) has confirmed parsing external `llms.txt` files for ranking or citation
- A 300,000-domain study found zero correlation between having `llms.txt` and AI citation rate
- OtterlyAI server-log data: `/llms.txt` received only 0.1% of AI bot traffic — performed near the bottom of all crawled URLs
- Real value sits in: (a) AI agent + developer-tool integration when the LLM is *already pointed at the domain*, (b) reducing hallucinations when an AI is explicitly asked about the brand, (c) future-proofing
- Implementation cost is low (2–4 hours per site for standard businesses), so it's a reasonable forward-compatible bet — but it's not the lever that earns AI citations

Do not pitch `llms.txt` as an "AI ranking" deliverable. Position it as inference-time infrastructure. Earned media, brand mention density, and original data move citations — `llms.txt` does not.

---

## When to Build llms.txt

Use the right scope for the site type:

| Site type | Approach | Target size |
|-----------|----------|-------------|
| Service business / local | Single `llms.txt`, 15–35 curated links | < 5 KB |
| Ecommerce | `llms.txt` covering categories + key products + brand pages | < 8 KB |
| SaaS / docs-heavy | `llms.txt` index + `llms-full.txt` companion | Index < 10 KB |
| Developer tool / API | `llms.txt` + `llms-full.txt` + per-language exports | Multiple files |

For most SEO clients, a single curated `llms.txt` is the right deliverable.

---

## Required Inputs

Before generating, confirm with the user (or pull from the client folder):

1. **Site URL** (root domain)
2. **Business type** — service, ecommerce, SaaS, blog, docs (changes curation)
3. **Curation method** — pick one:
   - User dictates the page list explicitly
   - Topical map or content hierarchy if provided
   - Top GSC pages by impressions/clicks (last 90 days)
   - Top inlink-count pages from Screaming Frog crawl
   - Live-crawl the homepage + main hubs (default if no other input)
4. **Brand voice / one-line description** — either the user writes it or you draft from the homepage and they approve
5. **Pages to exclude** — paginated archives, thank-you pages, PPC landing pages, internal-only pages

---

## Build Workflow

### Step 1 — Crawl the site to map content

Use `WebFetch` to pull:
- Homepage (extract nav, primary services, contact info, license/credentials)
- Each top-level service hub (extract sub-service URLs and short descriptions)
- About page (founding year, certifications, mission, sister-page links)
- Service-areas hub if applicable (do NOT individually list every city page — link the hub)

Run these fetches in parallel where possible to save time.

### Step 2 — Curate the link list

Apply the 80/20 rule: the 20% of pages that answer 80% of user questions go in the first 20% of the file.

**Include:**
- Homepage (implicit — the H1 + blockquote IS the homepage representation)
- Core service category hubs
- Sub-service pages (the actual revenue-driving / answer-driving URLs)
- Authority pages: About, Reviews/Testimonials, Service Areas hub
- High-intent secondary pages: Contact, FAQ
- Cornerstone blog posts ONLY if they're genuinely high-signal — never the full blog feed

**Exclude:**
- Tag pages, category archives, paginated lists
- Privacy policy, terms of service, cookie policy
- Thin content, near-duplicates, outdated content
- PPC-only landing pages
- Thank-you pages, form-confirmation pages
- Admin / search / account pages
- 50+ city-level service-area pages (link the hub instead — listing all 50 bloats the file and dilutes signal)

**Cap link count:**
- Service businesses: 15–35 links total
- Ecommerce: 25–50 links total
- Docs sites: 30–80 links total

### Step 3 — Write the file using the strict spec structure

The Answer.AI spec defines a strict content order. Deviating breaks compliance.

```markdown
# Brand Name

> One-sentence summary of what the business does, who it serves, and the primary trust signal (years in business, certifications, brand partnerships, geography).

Optional prose section. No headings allowed here. Use plain paragraphs to add context: regions served, phone numbers, license numbers, hours, primary brand partners. Keep it factual — no marketing language.

## Core service categories

- [Page Title](https://full.url/): One-sentence factual description of what the page covers.
- [Page Title](https://full.url/): One-sentence factual description.

## [Category 2]

- [Page Title](https://full.url/): Description.

## [Category 3]

- [Page Title](https://full.url/): Description.

## About the company

- [About](https://full.url/about/): Description.
- [Reviews](https://full.url/reviews/): Description.
- [Service Areas](https://full.url/service-areas/): Description.

## Resources

- [Blog](https://full.url/blog/): Description.
- [FAQ](https://full.url/faq/): Description.

## Optional

- [Careers](https://full.url/careers/): Description.
- [Financing](https://full.url/financing/): Description.
- [Coupons](https://full.url/coupons/): Description.
```

### Step 4 — Self-audit before delivery

Run this checklist. The file is NOT shippable until every item passes.

**Structure compliance:**
- [ ] Exactly one H1 at the top, brand name only (no tagline, no slogan)
- [ ] Blockquote (`>`) directly under H1 with one-sentence summary
- [ ] Optional prose section uses paragraphs only — no headings, no lists with sub-headings
- [ ] All section headers are H2 (`##`) — never H3 or deeper
- [ ] Every link uses exact format: `- [Title](URL): Description.`
- [ ] `## Optional` section exists and contains lower-priority links (careers, financing, coupons, protection plans, legacy pages)

**Content quality:**
- [ ] H1 contains brand name only (not "Brand — tagline")
- [ ] Blockquote summary is neutral, factual, no marketing words ("innovative," "leading," "best-in-class," "premium," "industry-leading," "endless," "unparalleled," "exceptional")
- [ ] Every description is one sentence, jargon-free, action-oriented (says what the page DOES, not what it IS)
- [ ] No first-person language ("we," "our," "us")
- [ ] No promotional adjectives in descriptions
- [ ] Phone numbers, license numbers, and certifications match what's published on the live site exactly (consistency-across-channels signal)

**Curation quality:**
- [ ] Total link count is appropriate for site type (see size table above)
- [ ] First 20% of the file contains the highest-value pages (core services, primary categories)
- [ ] Sections are organized by user intent, not internal CMS taxonomy
- [ ] City-level service-area pages collapsed to a single hub link (never enumerated individually)
- [ ] No paginated, thin, or duplicate URLs
- [ ] No PPC, thank-you, or admin URLs

**Technical:**
- [ ] All linked URLs use the canonical form (https, trailing slash matching site convention, no UTM parameters)
- [ ] File saves with `.txt` extension and is plain UTF-8 markdown
- [ ] File size is within target (< 10 KB for most sites)

### Step 5 — Save to the right location

Save the file at: `Clients/<client-name>/llms.txt`

NOT inside subfolders like `Full SEO Audit/`. The dev team uploads it to the **site root** (`https://domain.com/llms.txt`), so keeping it at the top of the client folder makes hand-off cleaner.

If generating `llms-full.txt` (see decision tree below), save alongside as `Clients/<client-name>/llms-full.txt`.

### Step 6 — Hand-off note

After generating, tell the user:
- File location
- Curation choices made (what was included, what was excluded and why)
- Open questions / approval items (blockquote summary, brand voice, page list)
- Dev team action: upload to site root at `https://domain.com/llms.txt`, serve with `Content-Type: text/plain` or `text/markdown`, return HTTP 200 (no redirects)
- Optional follow-ups: also create `.md` versions of key pages, monitor server logs for AI bot traffic to `/llms.txt`

---

## Decision Tree: Do We Also Build llms-full.txt?

`llms-full.txt` inlines the actual content of every linked page as one long markdown document. Bigger lift, better for AI agents that ingest content for RAG / IDE indexing.

**Build llms-full.txt when:**
- Client has 50+ pages of substantive documentation (SaaS, dev tools, knowledge bases)
- Client has a developer-tool integration story (their users ask AI assistants about the product)
- Client explicitly asks for it
- Client is positioning for IDE / agent integration (Cursor, Windsurf, Copilot)

**Do NOT build llms-full.txt for:**
- Standard service businesses (HVAC, plumbing, lawyers, dentists) — wasted effort
- Ecommerce stores under 100 products — `llms.txt` is sufficient
- Sites where the linked content is heavily image- or video-driven (the markdown export will be thin)

---

## Marketing-Language Blacklist

Strip these words and phrases from the blockquote and all descriptions. They trigger marketing-fluff signals and reduce LLM trust per the best-practices doc.

**Banned adjectives:**
innovative, groundbreaking, industry-leading, world-class, best-in-class, premium, unparalleled, exceptional, cutting-edge, state-of-the-art, top-tier, market-leading, revolutionary, next-generation

**Banned phrases:**
"endless [anything]," "ultimate solution," "trusted by," "leader in," "your one-stop shop," "go-to," "go above and beyond," "second to none," "you can count on us"

**Banned voice patterns:**
- First-person: "we," "our," "us"
- Direct address marketing: "you deserve," "you'll love"
- Superlatives without proof: "the best," "the fastest," "the most reliable"

**Replace with:**
- Concrete facts (year founded, license number, brands carried, regions served)
- Verbs that describe the actual service ("installs," "diagnoses," "treats," "filters," "replaces")
- Neutral category descriptors ("residential," "commercial," "24/7," "licensed")

---

## Common Mistakes

These are the failure patterns to actively prevent:

1. **Treating llms.txt like sitemap.xml** — dumping every URL on the site. Spec says CURATE.
2. **Listing all city-level service-area pages individually** — produces 50+ near-identical link rows. Link the hub.
3. **Marketing copy in the blockquote** — "innovative provider of cutting-edge solutions" is a smell. Be factual.
4. **Forgetting the `## Optional` section** — careers, financing, coupons, legacy pages belong here.
5. **Using H3 or deeper headings** — spec only allows H1 (once) + H2 sections.
6. **Linking to non-canonical URLs** — UTM-tagged, paginated, or non-trailing-slash variants of pages that exist elsewhere.
7. **Promoting llms.txt as a ranking factor in client deliverables** — it isn't. Positioning matters.

---

## Reference

Full evidence base, adoption data, and 2026 best-practices research lives in [references/llms-txt-best-practices-2026.md](references/llms-txt-best-practices-2026.md). Read it before generating if the user asks "is this still worth doing?" or pushes back on the deliverable.
