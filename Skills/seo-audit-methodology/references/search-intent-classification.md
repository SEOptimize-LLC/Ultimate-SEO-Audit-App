# Search Intent Classification — Shared Definition

> Single source of truth for how this project classifies query intent. Three skills classify
> intent independently and previously carried three separate definitions, so the same query
> could be "commercial" in one deliverable and "money-bearing" in another with nothing
> reconciling the two. This file is that reconciliation.

**Consumed by:**

| Consumer | What it uses this for |
|---|---|
| `Skills/content-expansion/SKILL.md` Step 3 + Step 5 | Classifying a page's GSC query mix, then deciding section-expansion vs new page |
| `Skills/cannibalization/SKILL.md` | Priority A/B/C tiering — which clusters are money-bearing |
| `Skills/traffic-loss-analysis/SKILL.md` Phase 4.3 | Whether losses concentrate on informational queries (AI Overview / HCU signal) |
| `auditors/cannibalization_auditor.py` (`COMMERCIAL_INTENT_VALUES`) | Programmatic money-query test |

Intent is classified on **two dimensions plus an optional secondary label**. Classify all of
them, or the downstream decision is running on partial information.

---

## Dimension 1 — Intent label (what the searcher wants)

Four labels, after Broder's 2002 *Taxonomy of Web Search* and Google's own Do-Know-Go framing.
These are the labels DataForSEO returns, so they are also the integration boundary.

| Label | The searcher wants | Query shape |
|---|---|---|
| **Informational** | To understand something | "what is", "how does", "why", "guide to", "explained" |
| **Commercial** | To choose between options | "best", "vs", "alternatives", "review", "compare" |
| **Transactional** | To act | "buy", "order", "book", "hire", "cost", "near me", "[service] company" |
| **Navigational** | To reach a specific place | brand name, product name, "[brand] login", "[brand] pricing page" |

**The label is read off the head term plus the SERP, never off the query text alone.** The
lexicon is a first pass. `Skills/content-expansion/SKILL.md` Step 3 carries the SERP-furniture
table that confirms it, and the confirmation is mandatory before any brief ships.

---

## Dimension 2 — Research stage (how far along the searcher is)

The same label covers searchers at completely different points in their research. "odoo
migration cost" and "odoo migration vs netsuite pricing" are both commercial-to-transactional,
but one wants a pricing block on a page that already exists and the other wants a comparison
page that does not. A framework with only Dimension 1 cannot tell them apart, so it routes both
to the same recommendation and one of the two is wrong.

**Read the stage off the modifier, not the head term.**

| Stage | The searcher is | Modifiers that signal it |
|---|---|---|
| **Early** | Still defining the problem; does not know the solution category yet | "what is", "why", "how does", "types of", "symptoms of", "causes of" |
| **Evaluating** | Knows the category; choosing between options or providers | "best", "vs", "alternatives", "review", "cost", "price", "how much", "for [use case]" |
| **Decided** | Has chosen; executing | "buy", "order", "book", "hire", "schedule", "near me", "emergency", "[brand] + [service]" |

**Why this changes the output.** A page can serve two stages only when its page type genuinely
serves both, which is rare. A service page built for decided-stage searchers that also tries to
absorb evaluating-stage queries becomes a hybrid that ranks for neither, because the SERP for
each stage rewards a different content type. Cluster on **intent + stage together**, and treat a
stage split as a page split.

The one combination that is almost always a misclassification: **informational + decided**. If
you have labelled a query that way, re-read the SERP. It is usually transactional with an
instructional-sounding modifier ("how to book a plumber").

---

## Secondary labels and the tie-break

A query may carry a **primary and a secondary label**. Local service queries almost always do.

**The rule: the primary determines the page type; the secondary determines section content.**

"plumber near me" is transactional (primary) plus local (secondary). Primary says build a
service page, not a guide. Secondary says that service page needs service-area content, NAP,
and a map embed. Getting this backwards produces a location page where a service page belonged.

**Local is always a secondary modifier, never a primary label.** There is no such thing as
"local intent" standing alone in this framework — there is a transactional query with a local
qualifier, or an informational query with a local qualifier.

**Tie-break order when the primary is genuinely contested:**

1. **SERP furniture wins over query text.** What Google renders is Google's own intent verdict,
   and it outranks any lexicon rule in this file.
2. **If the SERP is mixed,** the label held by the majority of the top 5 organic results is
   primary. Ignore ads for this test; ads skew commercial by construction.
3. **If still tied,** the primary is whichever label matches a page the client actually has or
   is willing to build. A contested query routed to a page type that does not exist is not a
   recommendation, it is a wish.

A genuinely mixed SERP that survives all three tests is a **mixed-intent seed term**, and the
false-positive guard in `Skills/cannibalization/SKILL.md` applies: two of the site's pages can
both rank there without competing, and consolidating them destroys legitimate traffic.

---

## Vertical overlays

The lexicon above is generic, and generic is where misclassification originates. "Emergency" is
decided-stage transactional for a plumber and early-stage informational for a SaaS blog. "Best"
is comparison-shopping in ecommerce and vendor-shortlisting in B2B, and those two want different
page types. Apply the overlay for the client's vertical on top of the base lexicon, and only the
terms that flip are listed.

### Home services (plumbing, HVAC, water treatment, restoration)

| Term | Reads as | Note |
|---|---|---|
| emergency, same day, 24 hour | Transactional / decided | Highest commercial value in the vertical. Never informational. |
| near me, in [city] | Transactional / decided + local secondary | Map Pack query. Set the DFS/SERP location to the city, not US-national. |
| cost, price, how much | Transactional / evaluating | Converts. Do NOT downgrade these to informational because of the question form. |
| how to fix, DIY, myself | Informational / early | **Low commercial value.** A searcher fixing it themselves is not a lead. Deprioritize regardless of impression volume. |
| [service] company, contractor, service | Transactional / decided | |
| [brand] + [city] | Navigational + local secondary | |

### B2B SaaS and professional services

| Term | Reads as | Note |
|---|---|---|
| best, vs, alternatives, competitors | Commercial / evaluating | **High value.** Long sales cycle means the shortlist forms here. |
| what is, guide to | Informational / early | **Still valuable**, unlike home services. B2B buying starts with category education and the vendor who teaches gets the shortlist slot. Do not deprioritize informational in this vertical. |
| pricing, cost, quote | Commercial / evaluating shading to decided | |
| implementation, migration, integration, setup | Transactional / decided | The searcher already owns or has chosen the product. |
| template, checklist, example, calculator | Informational / early | Lead-magnet intent. Value is capture, not ranking. |

### Ecommerce

| Term | Reads as | Note |
|---|---|---|
| best, top, review | Commercial / evaluating | SERP is listicle and affiliate dominated. A product page will not rank here. |
| for [use case], for [audience] | Commercial / evaluating | Attribute filtering. Often a collection page, not a product page. |
| cheap, discount, coupon, promo | Transactional / decided | Low margin, and frequently brand-hijacking traffic. Verify the searcher wants you, not a coupon. |
| how to use, how to clean, care | Informational / post-purchase | **Retention, not acquisition.** Distinct from early-stage pre-purchase. Do not count these as top-of-funnel wins. |

### Health and YMYL

| Term | Reads as | Note |
|---|---|---|
| symptoms, causes, is X normal | Informational / early | YMYL constraints apply. Never brief without named credentialed authorship. |
| treatment, therapy, procedure | Commercial / evaluating | |
| cost, insurance, covered by | Commercial / evaluating | Strong conversion signal despite the question form. |
| near me, clinic, doctor, specialist | Transactional / decided + local secondary | |

**Client-specific hard constraints override every row above.** Check the client's memory file
before briefing. Arsenal Health, for example, carries a standing exclusion on an entire content
category regardless of how the intent classifies.

---

## Order of operations

1. **Lexicon pass** — assign a provisional label and stage from the query text, using the base
   lexicon plus the vertical overlay.
2. **SERP confirmation** — read the furniture per `Skills/content-expansion/SKILL.md` Step 3.
   The SERP overrides the lexicon whenever they disagree.
3. **DFS cross-check** at scale — `mcp__dfs-mcp__dataforseo_labs_search_intent`, batching all
   keywords into a single call. DFS returns the Dimension 1 label only. It does not return
   research stage or vertical adjustment, so those stay manual.
4. **Confidence verdict** — see below.

## Confidence

Mark a classification **low confidence** when any of these is true:

- The lexicon pass and the SERP furniture disagree.
- DFS disagrees with the SERP furniture.
- The top 5 organic results split across two labels with no majority.
- The query is a seed term of two words or fewer with no service, geo, or intent modifier.

**A low-confidence classification may not be the sole justification for a new-page
recommendation.** Section expansion on an existing page is recoverable; a new page built on a
misread SERP is a cannibalization source that has to be redirected later. When confidence is
low, default to the reversible option and say so in the deliverable.

---

## DataForSEO mapping

DFS `search_intent` values map one-to-one onto Dimension 1. No translation layer is needed.

`COMMERCIAL_INTENT_VALUES = {"transactional", "commercial"}` in
`auditors/cannibalization_auditor.py` is the money-bearing test used for Priority A/B/C tiering,
and it stays as written. Note what it means: **money-bearing is a Dimension 1 test only.** It
does not distinguish an evaluating-stage "best plumber salt lake" from a decided-stage
"emergency plumber near me", and those have very different conversion value. When stage matters
to the prioritisation, read it manually.

---

## Provenance and limits

The four-label taxonomy is Broder (2002), corroborated by Google's Do-Know-Go framing, and is
stable industry canon.

The **research-stage dimension and the vertical-variance principle** were adopted from
Lazarina Stoy (MLforSEO), *Search Intent Classification with Machine Learning Approaches*,
analysed 2026-08-03. Both are structural observations rather than measured findings: the source
presents no labelled ground truth, no F1 scores, and no confusion matrix for any of its claims.
They are adopted as **method, not as measured fact**, and the specific stage boundaries and
vertical overlays in this file are this project's own construction, not the source's.

Treat both as a **testable hypothesis pending one implementation cycle.** Verify against real
client output before either is treated as settled, and revise this file rather than working
around it if the client output disagrees.

The same source's ML implementation layer (zero-shot transformer classification, Google Natural
Language API entity extraction with salience scoring) was evaluated and **deliberately not
adopted**. DFS already batch-classifies at the scale this project operates at, and adding a
Google NL API dependency sits outside the OpenRouter and DFS standard in `CLAUDE.md` for a
precision gain the source never quantified.
