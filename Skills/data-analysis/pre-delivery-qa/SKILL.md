---
name: "Pre-Delivery QA"
description: "Mandatory checklist that runs BEFORE any client deliverable (.xlsx, .md report, action plan) ships. Forces dispatch of validation subagents, confirms tech-stack-aware fix instructions, and blocks delivery if any check fails. Triggered automatically when the main agent is about to write/save a file under Clients/<name>/Full SEO Audit/ or any client-facing report."
---

# Pre-Delivery QA

Nothing ships to the client until this checklist passes. This skill is the last line of defense before mistakes hit the real world.

## When this skill applies

- About to write a file under `Clients/<name>/Full SEO Audit/`
- About to write a `.xlsx` or `.md` deliverable in any client folder
- About to draft a client-facing message that cites specific findings
- The user says "ship this", "send to client", "finalize", "let's deliver"

## The mandatory checklist

Run every applicable check below. If ANY check fails, do not ship. Tell the user what failed and what needs to be fixed.

### CHECK 1 — Tech-stack awareness (always required)

Does the deliverable contain instructions referencing CMS-specific features?

Examples of CMS-specific instructions:
- "WP Admin → Edit with Elementor"
- "Edit theme template"
- "Add aria-label in Elementor widget"
- "Customize → Site Identity"
- "Shopify → Online Store → Themes → Edit code"
- "Webflow CMS → Collection"

If YES → confirm `Clients/<name>/site_fingerprint.json` exists and is recent (≤30 days). The instructions MUST match what the fingerprint says is actually editable on this site. If the fingerprint is missing or stale, dispatch the `tech-stack-fingerprint` subagent before continuing.

**Common failure mode (the SameDay incident):** writing "Edit with Elementor" instructions for a site that doesn't use Elementor on the relevant pages.

### CHECK 2 — Number traceability (required if deliverable cites counts)

Does the deliverable cite specific counts, metrics, or percentages?

Examples: "45 links", "284 sitemap entries", "5 PPC pages", "70 years", "78% of pages got faster", "5,340 impressions"

If YES → dispatch the `data-validator` subagent with the list of cited numbers AND the source files used. Subagent must return PASS for every cited number before delivery.

**Common failure mode:** trusting an upstream audit doc's count without re-deriving it from raw data.

### CHECK 3 — Target URL verification (required if deliverable proposes URLs)

Does the deliverable propose specific destination URLs?

Examples: "redirect to X", "use Y as canonical", "link to Z instead", "the new target is W", "fix the URL to point at..."

If YES → dispatch the `live-url-verifier` subagent with the full list of proposed URLs. Subagent must return PASS or WARN with explicit acknowledgement; any FAIL blocks delivery until resolved.

**Common failure mode (the Superior Nov 24 incident):** propagating an upstream audit's proposed targets without verifying they exist on the live site.

### CHECK 4 — Live verification of high-severity findings (required for Critical findings)

Is any finding classified as Critical, P0, or High?

Examples: "content duplication on revenue pages", "404 on top-traffic page", "complete indexation failure", "site-wide LCP crisis"

If YES → live-fetch the affected page(s) within the last 24 hours and confirm the issue is still present. Findings that have been silently fixed since the original audit should be marked RESOLVED, not pushed into the deliverable.

**Common failure mode:** shipping a P1 finding that was already fixed by the dev team last week.

### CHECK 5 — Scope filter (required for any "list of pages" finding)

Does the deliverable list specific URLs as targets for fixing?

If YES → confirm none of the URLs are non-SEO pages (per `audit-workflow.md` Rule 7):
- Paginated URLs (`/page/2/`, `/page/3/`)
- PPC landing pages
- Thank-you pages, application forms
- 404 error pages
- Login / admin pages
- Privacy policy, terms of service
- Site search results pages

If any non-SEO pages are in the list, remove them or move them to a separate "exclude from audit" tab.

### CHECK 6 — Internal-document leakage (always required)

Does the deliverable reference any internal document, framework, agent, or memory?

Examples to check for: `FRAMEWORK.md`, `GLOSSARY.md`, `SKILL.md`, `CLAUDE.md`, `MEMORY.md`, `audit-workflow.md`, "fact-cheat", "Per Section X", "the framework states", "knowledge base", "agent prompt"

If YES → strip or rewrite. The client never sees internal scaffolding. (See `report-formatting.md` rules.)

### CHECK 7 — Cross-report references (always required)

Does the deliverable say "see [other report]", "covered in standalone report", "as documented in...", or otherwise depend on the reader having another file open?

If YES → restate the relevant context inline. Each deliverable must be self-contained.

### CHECK 8 — URL truncation (always required)

Are any URLs in the deliverable truncated with ellipsis (`...`) or shortened to fit a column?

If YES → display the full URL. The dev team needs to copy/paste exact URLs.

### CHECK 9 — Marketing language audit (required for client-facing copy)

Does the deliverable contain proposed body copy for the client's website?

If YES → strip the banned-phrase blacklist:
- Banned adjectives: innovative, groundbreaking, industry-leading, best-in-class, premium, unparalleled, exceptional, cutting-edge, state-of-the-art, top-tier, market-leading, revolutionary
- Banned voice: first-person ("we", "our", "us"), unproven superlatives ("the best", "the fastest")
- Banned phrases: "endless [anything]", "your one-stop shop", "trusted by", "leader in"

### CHECK 10 — Audience match (always required)

Who is the human reader of this deliverable?
- **Internal team / boss (Nathan)** → can include data analysis context, methodology notes, reconciliation explanations
- **Web dev (Samuel)** → needs concrete code-level instructions matching the actual tech stack
- **Client admin (e.g., Rachel Smith @ Comfort)** → needs dashboard-level click-paths matching the actual CMS
- **Client executive** → needs business outcomes, not technical detail

If the deliverable is mismatched (e.g., dev-level code instructions in a client-exec report), rewrite for the right audience.

### CHECK 11 — Recommendation prose sanity (required if deliverable proposes rewrites)

Does the deliverable propose rewritten content — title tags, H1s, meta descriptions, body copy, anchor text, CTAs?

Examples that trigger this check:
- "New title pattern: '[City] Plumber: ...'"
- "Proposed H1: 'Trusted HVAC in Salt Lake City'"
- "Meta description: 'Same-day drain cleaning ...'"
- Excel column named "New Title", "Proposed Rewrite", "New Meta", "Suggested H1"

If YES → dispatch the `recommendation-sanity-checker` subagent with the full list of proposed rewrites. The subagent reads each rewrite as a human reader would and flags:

- **Token repetition** — same word, root, or city name appearing twice in a single title/H1/meta (per `feedback_title_tag_rewrite_rules.md` Rule 4)
- **Keyword stuffing** — 3+ commercial keywords stacked unnaturally
- **Stacked synonyms** — "Plumber" + "Plumbing", "Heat" + "Heating" in the same tag
- **Banned marketing language** — see CHECK 9 blacklist
- **Unnatural assembly** — phrasing a competent human SEO would not write from scratch
- **Brand suffix conflicts** — visible title repeats a token already in the brand suffix

Subagent must return PASS for every proposed rewrite before delivery. Any FLAG blocks delivery until the rewrite is fixed.

**Common failure mode (the Beehive local pages incident, May 2026):** shipping a title pattern that reads "[City] Plumber: Drain, Water Heater & Emergency Plumbing in [City], UT | Beehive Plumbing" — city repeated twice, "Plumber"/"Plumbing" stacked three times. The data-validator and live-url-verifier subagents pass it because the URLs and numbers are correct; the prose quality is what fails. CHECK 11 is the only check that catches this.

### CHECK 12: AI-tell scrub (always required)

**Rule:** No deliverable may contain an em dash (—), en dash (–), horizontal bar (―), or Unicode minus (−). The user's boss and clients read these as proof the document was machine-written, which discredits the work regardless of its accuracy.

Real hyphens are fine and must be preserved: `K-12`, `top-of-page`, `district-wide`.

**How to run it:**

```bash
python scripts/scrub_ai_tells.py "Clients/<name>/Full SEO Audit/<file>.md"
```

Exit 0 = clean. Exit 1 = dashes found, delivery blocked. The script also scans `.xlsx` cell text, so it covers Excel deliverables.

`--fix` auto-corrects only the unambiguous mechanical cases (heading separators, bold-label separators, lone dashes in table cells). **Dashes inside sentences must be rewritten by hand** — replacing one with a comma reliably produces a clunky sentence. Recast the sentence instead: use a colon before an explanation, commas or parentheses for an aside, or split into two sentences.

The script also reports AI vocabulary (`delve`, `leverage`, `robust`, `seamless`, `crucial`, `underscore`, `furthermore`, `in today's`, and similar) as advisory. Those don't block delivery, but plainer words are almost always better.

**Source:** the Education Walkthrough teacher evaluation software report, July 2026, which shipped with 46 em dashes and had to be rewritten after the user flagged it.

### CHECK 13: Prose quality (always required, internal reports included)

**Rule:** A report must read as connected human writing, not as bullet points with the bullets removed. This is a **recurring** correction, so treat it as blocking rather than advisory, and apply it to internal reports as well as client-facing ones.

Read the narrative sections and check each of these:

- **No stacked declaratives.** Three consecutive sentences that each open with a noun and state a fact is the signature failure. Connect them with "which", "until", "so", "because", "even as".
- **No figure repeated in adjacent sentences.** State a number once, then refer back to it in words ("that increase", "the entire gain").
- **Varied sentence length.** A short sentence only lands when it follows a longer one.
- **One argument per paragraph,** handing off to the next. No jumping between ideas mid-paragraph or between sections without a transition.
- **Tables carry data, prose carries meaning.** Never narrate a table back in sentences. After a table, explain what it means.
- **Interpretation over recitation.** "Mobile did not just grow, it changed places with desktop" beats "Mobile grew 74.1%."

**Watch the interaction with CHECK 12.** Removing an em dash without rewriting the sentence is what produces this failure: the subordinate clause the dash was carrying becomes an orphaned fragment. Never satisfy the dash rule by chopping a sentence in two. Recast it so the clause is carried by a comma, colon, semicolon or parentheses.

**How to run it:** read the narrative sections aloud. If it sounds like a machine reading a spreadsheet, rewrite before shipping. The scrub script cannot detect this; it is a judgement check.

**Source:** the SameDay Utah 30-day post-relaunch report, July 31 2026. Data, findings and structure were all accepted; the report was rejected on writing quality alone, with the user noting this had come up multiple times before.

### CHECK 14: Leaked-document citations (required if the deliverable names a leaked Google attribute or module, or cites "the leak")

**Rule:** Every leaked attribute or module name must exist in the leaked docs, and every claim about one carries a tag: documented (the doc text says it), inferred (the description is empty or the claim goes past the text), or DOJ-derived (the source is testimony, not the docs).

**How to run it:**

```bash
python Skills/google-leak-reference/scripts/check_leak_citations.py "Clients/<name>/Full SEO Audit/<file>.md"
```

Exit 0 is a pass, or "no leak identifiers found" (mark N/A). Exit 1 means a name is absent from the docs: delivery is blocked until the name is corrected or the claim removed. Exit 2 means the check could not run (index missing, file unreadable): delivery stays blocked, since a check that did not run is not a pass. Run `python Skills/google-leak-reference/scripts/build_index.py`, then re-run. The script reads `.xlsx` cell text too.

The script proves a name exists, not that the claim made about it is right. Settle every WARN and NOTE line by hand with the `google-leak-reference` skill: quote the doc text or tag the claim inferred or DOJ-derived. The 13-month click window and the 70-day RankEmbedBERT window are testimony, never documented.

**Source:** the October 2026 audit of the framework against the leaked docs, which found wrong module names, an invented `trustedAnchors` attribute and an unsupported `locationDemotion` signal that no reviewer had caught.

## How to run the QA pass

Before saving the file, mentally walk through each check above. For checks that require subagent dispatch (1, 2, 3, 4), actually dispatch the subagent — don't shortcut by "I think it's probably fine."

Output a brief QA report to the user before saving:

```
Pre-Delivery QA: <deliverable filename>
========================================
CHECK 1 (tech stack): PASS — fingerprint confirms WordPress + Gutenberg, instructions match
CHECK 2 (numbers): PASS — data-validator confirmed 779 / 5 / 1956 / 70
CHECK 3 (target URLs): PASS — live-url-verifier returned 23/23 PASS
CHECK 4 (high-sev live verify): N/A — no Critical findings
CHECK 5 (scope filter): PASS — no non-SEO pages in target list
CHECK 6 (internal leakage): PASS — no framework references found
CHECK 7 (cross-refs): PASS — self-contained
CHECK 8 (URL truncation): PASS — all URLs full-length
CHECK 9 (marketing lang): N/A — no body copy proposed
CHECK 10 (audience): PASS — written for client Elementor admin
CHECK 11 (rec prose): N/A — no rewrites proposed
CHECK 13 (prose quality): PASS — read aloud, connected paragraphs, no stacked declaratives
CHECK 12 (AI-tell scrub): PASS — scrub_ai_tells.py exit 0, zero dashes
CHECK 14 (leak citations): PASS — check_leak_citations.py exit 0, 12 identifiers exact, claims tagged

Deliverable approved for delivery: Clients/<name>/Full SEO Audit/<file>.xlsx
```

If any check FAILS:
```
Pre-Delivery QA: <deliverable filename>
========================================
CHECK 2 (numbers): FAIL — data-validator flagged "45 empty anchors" claim; actual count from SF data is 779
CHECK 3 (target URLs): WARN — 3 of 24 URLs return 301 redirects; recommend updating targets to final destinations

Deliverable BLOCKED. Fix the issues above before shipping.
```

## What this skill MUST NOT do

- Do not silently approve the deliverable to "save time."
- Do not approve a check by inspection when the check requires a subagent dispatch.
- Do not run the checks AFTER the file is saved — run them BEFORE.
- Do not strip context from the user. If a check fails, explain what failed and how to fix.
