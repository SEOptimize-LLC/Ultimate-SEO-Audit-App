---
description: Verify that a set of URLs (e.g. content items published this month) are indexed correctly in Google. Runs GSC URL Inspection + live-site verification + sitemap cross-check for each URL, catches the slug-mismatch / trailing-slash / stale-404 / orphan traps, classifies each per the GSC indexation-states playbook, and produces a status report (optionally an Excel). Use for "confirm these pages are indexed" requests.
---

# /verify-indexation

You are verifying whether a specific list of URLs is indexed correctly in Google. This is the exact workflow validated across live client checks (Comfort Solutions, Superior Water & Air, Beehive — 2026-07). The governing reference is [Skills/technical-seo-agent/references/gsc-indexation-states.md](../../Skills/technical-seo-agent/references/gsc-indexation-states.md) — read it; this command is the trigger and the input/output spec.

**Core discipline (hard rule): GSC's status is a hypothesis, never a shippable finding.** Every URL gets both a GSC verdict AND a live-site check, and any "not indexed" conclusion must survive the trap checks below before it reaches the user. Per `.claude/rules/audit-workflow.md` Rules 11–12 and `no-unverified-claims`.

## Required Inputs

1. **Site / GSC property** — e.g. `https://www.beehiveplumbing.com/`. If only a domain is given, resolve the exact GSC property with `mcp__gsc-mcp__list_properties` (URL-prefix vs `sc-domain:`; `www` vs non-`www` matters).
2. **The URL list** — the slugs/paths or full URLs to verify (the "content items published in June," etc.).

Optional:
3. **Client folder** (e.g. `Clients/Beehive/`) — if provided, also write an Excel deliverable there (two tabs: Indexation Status + Action Items) and open it. Otherwise report inline.

If GSC access to the property fails (403 / not listed), STOP and tell the user — GSC is mandatory for indexation checks (`.claude/rules/audit-workflow.md`). Do not substitute DFS estimates.

## Workflow

Run these in order. Batch where possible; keep a real browser session for the live checks (curl is frequently WAF-blocked with 403 on sites that are indexed fine — use Playwright).

1. **Resolve property + build canonical URLs.** Match protocol and host to the GSC property. Note the site's trailing-slash convention (most WordPress sites canonicalize *with* a trailing slash) — you will re-check both variants if the first inspection says "unknown."

2. **GSC URL Inspection (batch).** `mcp__gsc-mcp__batch_url_inspection` on the full list. Record per URL: coverage state, last-crawl date, whether the Google-selected canonical differs.

3. **Live-site verification (real browser).** For every URL, fetch and record: HTTP status, final URL after redirects, `<link rel=canonical>`, `<meta robots>`, and a content signal (H1 present + body word count). This is what catches the traps.

4. **Run the trap checks** — do NOT report "not indexed" until each of these is ruled out:
   - **Trailing-slash / host canonical:** if GSC said "unknown"/"Discovered – not indexed" on the URL as given, re-inspect the page's *actual* self-canonical (with/without trailing slash, `www`/non-`www`). The real canonical is often indexed while the variant isn't. (Comfort West Haven case.)
   - **Slug mismatch:** if the given URL 404s or is unknown, search the XML sitemap for a near-variant slug (e.g. `/ac-services/` vs `/air-conditioning/`; `/whole-home-air-filtration-system/` vs `/whole-home-air-filtration/`). The real page may be live and indexed at a different slug — the tracking sheet was wrong, not the site. (Comfort / Superior cases.)
   - **Stale 404:** if GSC says "Not found (404)" but the live test returns 200, the page was fixed after Google's last crawl — the record is stale. The fix is a reindex request, not content work. (Superior `/emergency-services/` case.)
   - **Orphan (Discovered – not indexed):** if the page is live, indexable, in the sitemap, but not indexed, check internal links — fetch the parent hub and confirm whether it links to the page. Zero inbound internal links = orphan; the fix is internal linking, not content. (Beehive `/water-heater-installation/` case.)

5. **Sitemap cross-check.** Fetch the sitemap index + sub-sitemaps; record whether each target URL (and, for a 404/unknown, any variant slug) is present. Absence + 404 = not published (a content-delivery gap, flag for the owner), not an indexing issue.

6. **Classify + remediate.** For each URL, assign its state and remediation per [gsc-indexation-states.md](../../Skills/technical-seo-agent/references/gsc-indexation-states.md), with a Validation method and an Expected-outcome tag (per `.claude/rules/audit-workflow.md`): unblocking an indexable money page (orphan link, `noindex` removal, stale-404 reindex) is a **Ranking Lever**; benign canonical noise is **Infrastructure Hygiene**.

## Output

A clear verdict first ("N of M indexed and healthy; K need action"), then:

- **Status table** — one row per URL: URL (full, never truncated per `.claude/rules/report-formatting.md`), live HTTP, indexable, in sitemap, GSC verdict, last crawled, result (color/emoji-coded: indexed / not indexed / 404 / stale). Add a row for any real-slug variant discovered.
- **Action items** — only the URLs needing work, each with: problem, solution, priority, expected outcome, likely effect, and a specific validation method (the exact GSC / curl / DevTools step to confirm the fix shipped).
- **Slug corrections** — call out any tracking-sheet URL that differs from the live/indexed slug.

If a client folder was given, also generate the Excel (Indexation Status + Action Items tabs, color-coded) into `Clients/<name>/…`, open it with `start`, and follow the deliverable QA + TL;DR-on-approval preferences in memory.

## What NOT to do

- Don't report "not indexed" from GSC alone — run the trap checks first.
- Don't recommend a content rewrite for an orphan, or a reindex for a thin page — match the remediation to the state's real cause.
- Don't trust curl's 403 as the page's real status — use the real-browser session.
- Don't propose any target/redirect URL without live-verifying it (Rule 12).
