# SEO Audit Workflow Rules

## Two-Pass Audit Process (Mandatory)

Every client audit MUST follow a two-pass process. Never deliver findings after only Pass 1.

### Pass 1 — Audit Execution
- Run the full audit stack: technical SEO, on-page SEO, backlinks, crawl depth, AI search readiness
- Pull live data from GSC and DataForSEO where available
- Cross-reference with Screaming Frog exports when provided
- Generate findings with source attribution for every data point

### Pass 2 — Self-Review Before Delivery
Before presenting any audit findings to the user:

1. **Data traceability:** Verify every data point traces back to a specific source (SF column, GSC metric, DFS response). No invented numbers. If a number cannot be traced, remove it or flag it as estimated.

2. **Diagnosis-evidence alignment:** For every diagnosis, confirm the underlying data actually supports it. If the diagnosis says "thin content is the issue," the word count data must back that up. If the diagnosis says "internal linking problem," the inlink counts must confirm it.

3. **Cross-source contradiction check:** When multiple data sources cover the same metric, check they agree. If they conflict, flag the discrepancy and state which source is more authoritative and why.

4. **Client isolation:** Confirm no findings, data, or recommendations from another client have been carried into this audit. Each client audit is independent.

5. **Recommendation specificity:** Every recommendation must be actionable and specific to this client's data. No generic SEO advice. "Improve internal linking" is not acceptable. "Add internal links from the 3 HVAC service pages to the 5 indexed HVAC blog posts" is.

6. **Sanity check:** Read through the complete output and confirm it makes logical sense as a whole. Do the numbers in the summary match the numbers in the detail sections? Do the priorities reflect the actual severity of the findings?

7. **Exclude non-SEO pages from audit metrics.** When counting underlinked pages, zero-traffic pages, thin content, or any SEO metric — exclude pages that have no SEO value: paginated pages (/page/2/, /page/3/), PPC landing pages, thank-you pages, application forms, 404 error pages, login/admin pages, privacy policy, terms of service, and similar utility pages. These inflate issue counts and create noise. Only count pages that should rank in organic search.

8. **Ignore shared template elements when evaluating content duplication.** Navigation, footer, sidebar, testimonials carousels, financing sections, membership plan CTAs, service area lists, and other site-wide template blocks are standard CMS behavior — NOT content duplication. Screaming Frog's near-duplicate detection compares full rendered HTML including these elements, which inflates similarity scores. When assessing content uniqueness, evaluate only the page-specific body content (H1, hero text, service descriptions, FAQs, unique copy). Never recommend "reducing template footprint" or flag shared template elements as a duplication problem.

9. **Ignore ad tracking scripts and conversion pixels in redirect analysis.** Google Ads tracking tags (`googleads.g.doubleclick.net/pagead/id`), Facebook pixels, and similar marketing scripts appear in SF redirect chain exports because they return 302 responses. These are NOT redirect loops or broken links — they are standard ad tracking behavior embedded in the site template. Do not include them in redirect findings or roadmap items.

10. **Deduplicate row-level data before reporting counts.** Screaming Frog Technical Audit exports create one row per source-page-to-redirect pair — if 200 pages link to the same redirecting URL, that's 200 rows for 1 redirect. Always report the number of **unique URLs affected**, not the row count. The same applies to inlink reports, near-duplicate reports, and any export where relationships are stored as rows. When the raw row count and the unique count differ significantly, report both and explain the difference.

11. **Live verification for high-severity findings:** For any finding classified as Critical — especially content duplication, 404 errors on revenue pages, or complete indexation failures — verify against the live site using Playwright or DFS content parsing before including in the report. Screaming Frog near-duplicate detection compares full rendered HTML including shared template elements (nav, footer, sidebars) which can inflate similarity scores. Never claim pages serve "identical content" based solely on SF near-duplicate scores without verifying the actual rendered content.

12. **Verify every proposed target URL against the live site (no exceptions, regardless of severity).** This rule applies whenever a recommendation specifies a destination URL — redirect targets, canonical targets, internal link replacements, "link to X instead of Y" suggestions, "update the redirect to point to Z" actions, or any deliverable that names a specific URL the client should use. Severity is irrelevant — Medium and Low recommendations propagate just as widely as Critical ones, and a wrong target URL becomes a 301-cemented mistake the moment the developer implements it.

   **Triggers — apply this rule whenever any of these are true:**
   - A spreadsheet column is named "New Target," "Proposed New Target," "Redirect To," "Should Point To," "Replacement URL," or similar
   - A finding's recommendation field says "redirect to X," "update the link to point to Y," "use Z instead"
   - You're propagating recommendations from an upstream document (prior audit, GSC export, agency handoff doc, client-supplied list, or an AI-/script-generated candidate map such as `/generate-redirect-map` output) — **NEVER trust upstream targets without verification**
   - You're parsing action-item text with regex/extraction logic to pull URLs from prose

   **Required actions before publishing the deliverable:**

   a. **Existence check** — every proposed target URL must return 200 and be indexable. If it 301s elsewhere, propose the final destination instead. If it 404s, the recommendation is broken — flag the row and ask the user before publishing.

   b. **Architectural-decision-first** — when multiple rows propose redirects within the same vertical (e.g., 5 rows touching `/plumbing/` URLs, 11 rows touching service pages), group them by destination pattern BEFORE listing individual recommendations. Surface inconsistencies as a single "architecture decision needed" finding the user must resolve, then apply the resolution uniformly. Do NOT publish 11 individual rows that contradict each other on which subfolder is canonical.

   c. **Don't-fix-what-isn't-broken filter** — purely cosmetic redirects (singular vs plural like `/air-conditioner/` → `/air-conditioners/`, trailing-slash variants, hyphen vs underscore) that already 301 correctly should NOT be in the active correction list. Move them to a "leave as-is" tab. The user should not assign these to a developer. They burn implementation effort with zero ranking benefit and risk introducing new bugs in the redirect rules.

   d. **Cross-vertical sanity check** — if a recommendation moves a URL from one top-level subfolder to a different one (e.g., `/plumbing/water-heaters/` → `/water/water-heaters/`), it crosses an architectural boundary and requires explicit user confirmation. These are content architecture decisions, not redirect cleanups, and they should never be quietly bundled into a "redirect corrections" deliverable.

   e. **Source attribution** — every proposed target must cite where the target came from: live-site verification, GSC URL Inspection, prior agency audit (and which one), or "inferred from URL pattern." If the source is "extracted from action-item prose by regex," that is NOT sufficient — verify against the live site before publishing.

   f. **Post-implementation validation** — verification of the proposed targets (a–e) happens BEFORE the deliverable ships; this step closes the loop AFTER the developer or VA reports the redirect map implemented. Run the `/validate-redirects` command (which wraps `python scripts/validate_redirect_map.py --input <map.csv>` — the user never runs the script by hand) against the shipped map (it auto-detects generic source/target columns and Rank Math export layouts; pass `--base-url` for relative paths). The script fires a live request at every source URL and reports PASS/WARN/FAIL per row on whether it actually lands on the approved target. Trailing-slash and http→https differences count as matches by default (`--strict-slash` / `--strict-scheme` to tighten), and a hop that only normalizes scheme, slash, or www does not count against the chain — those site-wide normalization redirects are the first hop on most sources and are not mapping errors. Substantive findings: a source still returning 200 (redirect never implemented), a 302 where a 301 was specified, a landing URL that isn't the approved target, or a target that has since gone 404/noindex. Any FAIL reopens the implementation ticket with the report attached — do not wait for the next audit to catch it. This is also the standard Validation Method for redirect-map deliverables: one command validates the whole map instead of a per-row curl instruction.

   **The Superior Water & Air Nov 24 GSC audit incident (April 2026)** is the reference case for this rule. The original audit doc proposed targets that were inconsistent across rows (`/plumbing/` vs `/plumbing-services/` for similar URLs), included cosmetic fixes (singular→plural that didn't need fixing), and crossed verticals without justification (`/plumbing/water-heaters/` → `/water/water-heaters/`). The build script extracted those targets via regex without verification and produced a 29-correction list that the user's VA implemented before review. The fix is upstream — never publish a redirect target that hasn't been verified.

## GSC Access Is Mandatory

Do NOT proceed with the audit if Google Search Console access is unavailable. GSC provides indexation status, query performance, CTR data, and crawl diagnostics that cannot be reliably substituted by third-party tools. If GSC returns a 403 or any access error, STOP and tell the user immediately — do not attempt to work around it with DFS estimates or cached data. The user needs to resolve the access issue before the audit can proceed.

## Data Source Hierarchy

When data sources conflict, trust in this order:
1. Current crawl data (Screaming Frog) — most recent snapshot
2. GSC URL Inspection API — Google's own evaluation
3. GSC Search Analytics — actual performance data
4. DataForSEO — third-party estimation
5. Memory / prior session notes — verify before using

## Report Standards

- Every finding must name its data source
- Tables must not exceed 5-6 columns (wider tables break in Google Docs)
- Never include internal correction language, retraction notes, or strikethrough text in client-facing reports
- Never include recovery timelines unless explicitly requested — the agency handles scheduling internally
- Distinguish between "data says X" and "based on data, I conclude Y"
- When a finding is uncertain, state the confidence level rather than presenting it as definitive

## Expected Outcome Tagging (Mandatory on Recommendations)

Every recommendation in a client-facing deliverable (audit report, action plan, roadmap, Excel rewrite sheet) must explicitly state its **expected outcome type** alongside priority and effort. The four valid tags — defined in detail in `Skills/seo-audit-methodology/SKILL.md` (Expected Outcome Classification) — are:

| Tag | Meaning |
|---|---|
| **Ranking Lever** | Expect ranking movement on specific queries when shipped |
| **Infrastructure Hygiene** | Cleaner architecture / protected crawl budget. Do NOT expect ranking movement. |
| **Risk Mitigation** | Prevents a future problem. No direct ranking impact. |
| **UX (indirect ranking)** | Affects user behavior. Ranking effect comes through click signals (slower, harder to attribute). |

**Required format on every recommendation:**

```
[Recommendation title]
Priority: P0/P1/P2/P3/P4
Scope: [what the work consists of, in concrete terms]
Expected outcome: [one of the four tags above]
Likely effect: [one specific sentence describing what the client should observe]
Validation method: [one specific instruction the dev can run to confirm the fix shipped correctly]
```

**No time estimates. Owner's rule, set August 2026, no exceptions.** The former
`Effort: [estimate]` field is gone and must not be reintroduced under another
name. Do not write hours, days, "roughly an hour", "half a day", or any
duration attached to how long work takes. This applies to every
recommendation-bearing deliverable: .md reports, .xlsx sheets, action plans,
roadmaps, and branded PDFs.

**`Scope` replaces it, and carries the same information better.** The reason a
reader wants an effort figure is to judge how big the job is, and naming the
work answers that more usefully than a number that can be held against you
later. "Three dependency settings that already exist in the tool" tells a
developer more than "1 hour" does. Sequence is carried by `Priority`, which is
what it was always for.

Calendar language is unaffected. Recrawl windows ("Google needs three to four
weeks to re-read the site"), reporting periods and data ranges are all still
required wherever a finding depends on them.

**Why this rule exists:** clients who ship infrastructure-hygiene fixes and don't see rankings move conclude SEO doesn't work — when in fact those fixes were never going to move rankings (and we knew that). The fix is to tell them upfront, not to defend it after delivery. This rule applies to .md reports, .xlsx files, action plans, and any recommendation-bearing client communication.

**Reference case:** the LinkedIn post about a 500K → 7K filter-page cleanup that produced "no ranking movement" — a correct outcome that surprised the client only because expectations were never set. Tagging the recommendation as Infrastructure Hygiene at audit time prevents that conversation entirely.

**One important honesty exception:** some technical fixes look like hygiene but ARE ranking levers. Removing a `noindex` tag blocking a money page, fixing a canonical bug that suppresses an indexable URL, and recovering de-indexed revenue pages are Ranking Levers, not Hygiene — because they unblock content that was previously invisible to Google. Distinguish these explicitly. Don't downgrade a real ranking lever to Hygiene just to under-promise.

## Validation Method (Mandatory on Recommendations)

Every recommendation must include a **Validation method** — one specific instruction the client's developer can run to confirm the fix shipped correctly. This is the closing-the-loop field: without it, the dev marks the ticket "done" based on intent rather than evidence, and the next audit catches the same issue still live.

**What a good Validation method looks like:**

| Recommendation | Bad validation | Good validation |
|---|---|---|
| Remove `noindex` from `/blog/erp-implementation-checklist` | "Check the page is indexed" | "Re-fetch the URL in GSC URL Inspection and confirm 'Indexing allowed: Yes' and the meta robots line is absent or set to `index, follow`. Then re-curl the page and grep for `noindex` — should return no matches." |
| 301 `/contactus` to `/contact-us` | "Confirm the redirect" | "Run `curl -I https://www.cudio.com/contactus` and confirm the response shows `HTTP/1.1 301` with `Location: https://www.cudio.com/contact-us`. Verify in Screaming Frog the source URL no longer appears as a 200." |
| Add Service schema to `/services/odoo-migration` | "Verify schema" | "Paste the page URL into Google's Rich Results Test (https://search.google.com/test/rich-results) and confirm Service schema is detected with no errors. Cross-check `serviceType`, `provider`, `areaServed` populate correctly." |
| Serve Poppins locally | "Confirm fonts load locally" | "Open DevTools → Network → reload the page → filter by 'font' → confirm Poppins woff2 files load from `/web/content/` (own server), not from `fonts.gstatic.com`. Re-run Lighthouse and confirm render-blocking resources panel no longer lists `fonts.googleapis.com`." |

**Format rules:**

- One specific instruction, not a checklist. If the validation truly requires multiple steps, list them inline (numbered) — but keep it short enough that the dev can paste it into the ticket as-is.
- Name the exact tool (curl, GSC URL Inspection, Rich Results Test, Lighthouse, DevTools Network panel, Screaming Frog). "Check it works" is not a tool.
- Specify the exact field, header, or signal to verify. "Confirm 301" is too vague — "confirm `HTTP/1.1 301` with `Location: <target-URL>`" is precise.
- For findings that depend on Google's recrawl (indexation status, canonical changes, schema rich results), include the recrawl-dependency note: "Recrawl typically happens within 7–14 days; if status hasn't updated by then, request indexing manually in GSC."
- For Validation methods that require third-party tools the client may not have (Screaming Frog, Sitebulb), provide a free-tool alternative as a fallback.

**Why this rule exists:** the alternative — "I'll trust the dev marked it done" — is how findings recur audit after audit. A specific Validation method gives the dev unambiguous accept criteria, gives you (or the agency PM) a way to audit the ticket queue without re-running the full audit, and gives the client a way to confirm the value they paid for actually shipped. It's the field a senior consultant operates with by default.

**Source:** Adopted from Islam Eldiasti's technical-SEO-skill-claude (https://github.com/eslamdeasty/technical-seo-skill-claude), which makes Validation Method a required field on every audit recommendation. Cross-verified against standard senior-SEO-consultant practice.
