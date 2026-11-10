---
description: Ultimate SEO Agent command for the Clients/ folder. Single-URL content expansion analysis. Pulls a page's GSC query data, classifies queries by intent and position, runs the cannibalization gate, and produces a ranked deliverable of intra-page additions, new-page candidates, internal-link suggestions, and semantic entities to add. Use when a client asks "what should I add to this page?" or when an audit surfaces a single URL with strong impression volume and weak CTR.
---

# /page-content-expansion

You are running a single-URL content-expansion analysis. The goal: take ONE URL the user provides, pull its GSC query mix, and produce a ranked, source-attributed plan for how to expand its topical coverage — without creating cannibalization or thin content.

This is the user-facing entry point for the `Skills/content-expansion/SKILL.md` methodology. Follow that skill's 6-step workflow exactly. This command file is the trigger and the input/output spec.

## Required Inputs

The user must provide:

1. **Target URL** — the single page to analyze (full URL with protocol and host)
2. **GSC property** — the GSC property the URL belongs to (e.g., `https://www.cudio.com/` or `sc-domain:cudio.com`). If the user does not provide this, infer from the URL host and confirm with the user before proceeding.

Optional inputs:

3. **Client folder** (e.g., `Clients/Cudio/`) — if provided, the deliverable is written to `Clients/<name>/Full SEO Audit/page_expansion_<slug>.md`. If not provided, the deliverable is returned inline in chat.
4. **GSC window** — defaults to 90 days. The user can override (e.g., "use 180 days").

If the URL is missing, ask for it. Do not proceed with placeholders.

## Pre-flight Checks (Before Any Analysis)

Run these in order. Stop and report the failure if any check fails — do not proceed to analysis on an invalid target.

1. **URL validity** — fetch the URL. Confirm 200 status. If 3xx, follow the chain and use the final destination (and tell the user the input was a redirect). If 4xx/5xx, stop.
2. **Indexability** — parse `<meta name="robots">` from the raw HTML. If `noindex` is present, stop and tell the user the page is non-indexable — expansion recommendations would be wasted.
3. **Canonical** — parse `<link rel="canonical">`. If the canonical points elsewhere, stop and recommend running the analysis against the canonical URL instead.
4. **GSC access** — run `mcp__gsc-mcp__list_properties` and confirm the property is accessible.
5. **Impression floor** — run `mcp__gsc-mcp__get_search_by_page_query` for the URL. If fewer than 50 impressions over the window, stop and tell the user the page is too low-volume for this workflow.

Report the pre-flight result in one short paragraph before proceeding.

## Workflow Execution

Invoke the `Skills/content-expansion/SKILL.md` methodology and follow its 6 steps verbatim. Specifically:

| Step | What you run |
|---|---|
| 1. Validate URL | Pre-flight checks above |
| 2. Pull GSC query data | `mcp__gsc-mcp__get_search_by_page_query` with the target URL and window |
| 3. Classify queries by intent and position | Apply the 4 intent buckets and 4 position buckets from the skill |
| 4. Run the cannibalization gate | For each expansion candidate query, run `mcp__gsc-mcp__get_advanced_search_analytics` with `dimensions=page` and `filter_dimension=query` to confirm no other URL on the site holds the query stronger. Block any query where another URL is stronger. |
| 5. Group queries into clusters and apply expansion-vs-new-page decision logic | Use the skill's decision table |
| 6. Identify semantic entities and internal links | Re-fetch the target page's HTML, grep for the entity terms in the queries, surface what's missing. For internal links, use `mcp__gsc-mcp__get_advanced_search_analytics` to find related-query URLs as link sources. |

## Deliverable Format

Produce the 6-section deliverable defined in the skill's "Required Output Structure":

1. Page Snapshot
2. Intra-Page Content Additions
3. New-Page Candidates
4. Internal Links to Add
5. Cannibalization Risks Flagged
6. Methodology Footer

Every recommendation row in sections 2, 3, and 4 must carry the required fields per `.claude/rules/audit-workflow.md`:

- Priority (P0–P3)
- Effort (hours)
- Expected outcome (Ranking Lever | Infrastructure Hygiene | Risk Mitigation | UX)
- Likely effect (one specific sentence)
- Validation method (one specific instruction)

## Output Routing

- **If a client folder was provided:** write the deliverable to `Clients/<name>/Full SEO Audit/page_expansion_<slug>.md` where `<slug>` is the target URL's last path segment (e.g., `services_odoo_migration` for `/services/odoo-migration`). Then show the user a 5-line summary (URL, total impressions analyzed, count of intra-page additions, count of new-page candidates, count of internal links to add) and the file path.
- **If no client folder was provided:** return the deliverable inline in the chat response. Compress where possible — the inline version should still be reviewable in 5 minutes.

## Pre-Delivery QA

Before considering the analysis complete, run these checks:

1. **Did every recommendation cite specific GSC queries?** Anything missing a query citation is incomplete. Fix or drop.
2. **Was the cannibalization gate run?** If you cannot point to the queries it checked, the gate did not run. Re-run it.
3. **Are the recommended entities actually missing from the page body?** Re-fetch the page and grep for each one. Drop any that are already present.
4. **Are there more than 8 intra-page additions or more than 3 new-page candidates?** If yes, you are over-recommending. Re-prioritize and cut.
5. **Does every recommendation carry the full required-fields format?** If not, fix.
6. **Does the deliverable open with the pre-flight result + GSC window?** If not, prepend.

If any of these fail, fix before delivering. If a client folder is involved, the standard `Skills/data-analysis/pre-delivery-qa/SKILL.md` checklist also applies — dispatch the data-validator and live-url-verifier subagents per that skill's rules.

## When to Punt to a Different Workflow

- **The page has no GSC impressions** → punt to competitive content gap analysis (not yet codified as a skill — note this in the output).
- **Multiple URLs cannibalize the page's primary query** → punt to `/cannibalization` workflow. Document the cannibalization but don't try to resolve it in this command.
- **The page is failing Core Web Vitals so badly that no on-page content fix matters** → flag the speed issue, recommend speed remediation first, then return to expansion.
- **The page is `noindex` or behind auth** → pre-flight will catch this. Tell the user and stop.

## Worked Example (Conceptual)

The clearest existing case in the project is Cudio's `/services/odoo-migration`:

- Position 2.7 for "odoo migration services" (824 impressions, 0.49% CTR over 28 days). Judge that against Cudio's own CTR at positions 1-4 from the same Search Console export, not a generic table: generic curves put position 2-3 at 12-18%, but some client sites earn a third of that, so a gap only counts when the page sits well below its own site's curve
- The page is technically strong but the SERP appearance is dragging CTR
- A run of this command would: (a) classify "odoo migration services" as transactional at striking-distance position, (b) confirm no other Cudio URL holds the query stronger (gate passes), (c) identify expansion clusters around migration timing, risks, downtime, rollback — all transactional adjacencies, (d) recommend 3-5 intra-page section additions and possibly 1 new page on "odoo migration cost calculator" if that cluster justifies it, (e) flag entities missing from the current page (rollback guarantee, downtime window, business size tiers)

The output would be a deliverable a developer can act on in a single sprint, not a 20-item wishlist.

## Related Skills and Commands

- `Skills/content-expansion/SKILL.md` — the methodology this command invokes
- `Skills/cannibalization/SKILL.md` — used as a guard in Step 4; escalated to when cannibalization is detected
- `Skills/onpage-seo-agent/SKILL.md` — content gap typology referenced in clustering
- `Skills/ai-search-optimization/SKILL.md` — referenced for semantic entity surfacing
- `Skills/data-analysis/pre-delivery-qa/SKILL.md` — required QA before any client deliverable ships
- `.claude/rules/audit-workflow.md` — required-fields format on every recommendation
- `/seo-audit` — site-wide companion; this command is the single-URL counterpart
