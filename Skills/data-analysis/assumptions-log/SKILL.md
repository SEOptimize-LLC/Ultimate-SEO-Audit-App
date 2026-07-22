---
name: "Assumptions Log"
description: "Surfaces and records every unverified assumption made during an audit (tech stack, data freshness, client-confirmed facts, scope decisions). Forces explicit declaration of what was assumed vs. verified, so the client (and future-you) knows exactly which findings rest on solid ground. Triggered at the start of any audit and updated continuously as findings get drafted."
---

# Assumptions Log

Every audit makes assumptions. The dangerous ones are the ones you don't realize you made. This skill forces them to the surface.

## When this skill applies

- An audit is starting for any client
- A finding is being drafted that depends on something the agent didn't directly verify
- The user provides a fact verbally ("the founding year is 1956", "the contact form goes to X email") that becomes load-bearing for findings
- A finding's accuracy depends on a static crawl that's older than the analysis

## What counts as an assumption

Anything that could be wrong without changing the work the agent is doing right now. Common categories:

### Tech-stack assumptions
- "The site uses Elementor" (vs. Gutenberg, hand-coded, Divi, etc.)
- "The footer is editable in WP Admin → Widgets" (vs. theme PHP)
- "The redirects use Rank Math" (vs. Yoast, native, Redirection plugin)
- "The site has GA4" (vs. UA, no analytics)

### Data-freshness assumptions
- "The SF crawl reflects current site state" (when crawl is >7 days old)
- "The audit doc's findings are still present" (when audit is >14 days old)
- "GSC data is up to date" (when last data point is >3 days old)

### Client-confirmed facts
- "Founded in 1956" (client-stated; not visible on the site)
- "Sites X, Y, Z are competitors" (client-stated; not derived from SERP analysis)
- "Service area is Salt Lake County only" (client-stated; vs. what the site says)

### Scope assumptions
- "We're auditing the main domain only" (vs. subdomains, country variants)
- "Mobile and desktop have the same content" (vs. m-dot subdomain, AMP)
- "All blog posts are in scope" (vs. some are tagged for noindex)

### Methodology assumptions
- "The 'empty anchor' count means truly empty (no anchor + no alt)" (vs. just no anchor)
- "Page speed measured on the homepage represents the site" (vs. inner pages may differ)
- "GSC clicks = real organic clicks" (vs. brand search noise)

## How to log assumptions

For each audit, maintain a file at `Clients/<name>/assumptions_log.md`. Format:

```markdown
# Assumptions Log — <Client Name>

Last updated: <ISO date>

---

## Currently active assumptions

### A1 — Tech stack
**Assumed:** Site uses WordPress + Elementor on inner pages
**Source:** site_fingerprint.json (2026-04-29)
**Risk if wrong:** All "Edit with Elementor" instructions become useless
**Verification status:** VERIFIED via fingerprint — primary builder = Gutenberg + Elementor on /electrical/ only
**Date verified:** 2026-04-29

### A2 — Data freshness
**Assumed:** SF crawl reflects current site state
**Source:** sameday_internal_all.xlsx (crawled 2026-03-15)
**Risk if wrong:** Findings may reference pages or content that has been edited/removed since
**Verification status:** PARTIAL — high-severity findings live-verified 2026-04-28; low-severity findings rely on crawl
**Date verified:** 2026-04-28 (partial)

### A3 — Founding year
**Assumed:** SameDay was founded in 1956 (70 years as of 2026)
**Source:** Client verbal confirmation (Roger Marquez, 2026-04-27)
**Risk if wrong:** Founding-year deliverable would propagate the wrong number across all pages
**Verification status:** UNVERIFIED — no public source on the live site or third-party listings confirms this
**Date verified:** N/A

---

## Resolved / closed

### A0 — (example) Site uses Yoast SEO plugin
**Assumed:** Yes
**Source:** Initial guess
**Verified:** No — fingerprint shows Rank Math
**Resolution:** Updated all redirect-import instructions to use Rank Math CSV format
**Closed:** 2026-04-15
```

## When to update the log

- **At audit kickoff:** record the top 3-5 load-bearing assumptions for this audit
- **When drafting a finding:** if the finding depends on something not yet in the log, add it
- **When a subagent verifies an assumption:** update its verification status and date
- **When a client confirms or refutes an assumption:** update or close it

## How to use the log

The log is NOT a client deliverable. It's an internal record. But two things flow from it:

1. **Every assumption with status `UNVERIFIED` should be acknowledged in the deliverable** — typically as a footnote or in an "Open questions / approval items" section. Example:
   > "Founding year claim of 1956 is based on client verbal confirmation. Recommend cross-checking against business registration records or printed materials before adding `foundingDate` to schema markup."

2. **An assumption with `Risk if wrong: HIGH` and `Verification status: UNVERIFIED` should block delivery** until verified or explicitly accepted by the user.

## What this skill MUST NOT do

- Do not skip the log to save time. The log compounds over the audit — adding entries as you go is cheap.
- Do not bury an unverified assumption in a finding without surfacing it in the log.
- Do not present an assumed fact as verified in a deliverable. If status is unverified, the deliverable language must reflect that ("client-stated", "based on prior audit", "to be confirmed").
- Do not delete entries when they're resolved — move them to "Resolved / closed" with the resolution noted. Future audits learn from prior lookups.

## Example: how this would have helped on the SameDay Elementor mistake

If the assumptions log had been used:

```
### A1 — Tech stack (initial draft)
**Assumed:** Site uses Elementor (mentioned in passing context)
**Source:** Inferred from "WordPress" + "page builder" presence
**Risk if wrong:** All fix instructions become useless
**Verification status:** UNVERIFIED — no fingerprint run yet
**Date verified:** N/A
```

That `UNVERIFIED + HIGH RISK` row would have triggered the pre-delivery-qa skill's CHECK 1 and forced dispatch of the tech-stack-fingerprint subagent BEFORE writing any "Edit with Elementor" instructions. Mistake prevented before it reached the deliverable.
