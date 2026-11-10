# GSC Page-Indexing States — Diagnostic Playbook

> The operating manual for reading Google Search Console's Page Indexing report and the URL Inspection tool, and turning each status into a cause → remediation → validation action. The `ranking-factors-checklist-2026.md` tells you *which* indexation checks to run (Clusters 3–4); this file tells you *how* to diagnose and resolve each state the check surfaces. Grounded in the auditor's live behavior (`technical_auditor.py` `_check_crawled_not_indexed` / `_check_discovered_not_indexed` / `_check_declared_vs_selected_canonical`) and in repeated live client verification (Comfort Solutions, Superior Water & Air, Beehive — West Haven / Park City / June-content indexation checks, 2026-07).

## Why this file exists

Screaming Frog can tell you a URL's HTTP status, canonical, and robots directives — but it can **never** tell you Google's own indexing decision. "Crawled – currently not indexed," "Discovered – currently not indexed," and the canonical/duplicate states are Google's judgments, visible only in GSC. The recurring failure mode this playbook prevents: reading a GSC status label and stopping there, instead of running the state's specific diagnosis and verifying against the live site. Three real incidents this quarter all came from a status label being trusted without the live check behind it (see "The always-verify rule").

## The verification workflow (run before trusting any status)

GSC's Page Indexing data lags ~2 days and its cached inspection result can be weeks stale. For any high-severity finding, run the live check:

1. **URL Inspection → read the coverage state.** This is the per-URL version of the Page Indexing report's status.
2. **Test Live URL.** Fetches the page fresh with Googlebot. Confirms the current fetch, indexability and render *now*, not as of the last crawl. It does not confirm the canonical. Google's URL Inspection help: "You can determine the canonical version only in the indexed data; the live test cannot predict whether or not the tested version will be considered canonical." Read the Google-selected canonical from the indexed inspection result (Page indexing > Google-selected canonical), never from the live test. (added 2026-11-10)
3. **View Crawled/Tested Page → confirm the content rendered.** If Googlebot's HTML is empty or broken where a user sees content, the problem is rendering, not indexing (route to `javascript_rendering_auditor.py`). Foley's render-verification trick: copy Googlebot's HTML from "View Tested Page," open the live URL in Chrome, F12 → Elements → right-click `<html>` → Edit as HTML → paste → observe whether Google sees the page a user does.
4. **`site:` operator as an independent check.** `site:https://exact-url` confirms whether the URL is actually in the index, separate from the inspection cache.
5. **Cross-check the sitemap and internal links.** A URL "unknown to Google" or "Discovered – not indexed" that isn't in the sitemap and has zero internal links is orphaned by definition.

The **two-place block check** for a page that should index but doesn't (Foley GSC Lesson 2):
- **Page level:** View Source → search `robots` / `noindex`. `index, follow` = fine; any `noindex` (including `noindex, follow`) blocks it.
- **Site level:** fetch `domain/robots.txt` → look for a `Disallow:` matching the URL's path.

## The always-verify rule (hard rule)

**GSC's reported counts are almost always higher than what is true live**, because Google retains an index memory of URLs for months after they change (redirect memory persists months→years; a deleted page sits in "Not found" ~2–3 months). A status label is a *hypothesis to verify*, never a finding to ship. Before any indexation finding reaches a client deliverable, confirm the live state (per `.claude/rules/audit-workflow.md` Rules 11–12). Reference cases from live verification, 2026-07:
- **Slug mismatch masked as "not indexed":** a page reported unknown/not-indexed at the URL on the tracking sheet was live and indexed at a *different* slug (Comfort `/air-conditioning` vs live `/ac-services/`; Superior `/whole-home-air-filtration/` vs live `/whole-home-air-filtration-system/`). The status was correct for the URL inspected — but the inspected URL was wrong.
- **Trailing-slash canonical mismatch:** inspecting the non-slash URL returned "unknown to Google" / "Discovered – not indexed" while the real canonical (with trailing slash) was indexed (Comfort West Haven service pages).
- **Stale 404:** a page live and healthy *now* still showed "Not found (404)" because Google's last crawl predated the fix (Superior `/emergency-services/`, last crawl before publish). The fix is a reindex request, not a content change.

## The states

Severity and remediation below. "Auditor coverage" names the module that surfaces the state today, or `MANUAL` where it must be run by hand from a GSC export. Every remediation ends in a **Validation** method (per `.claude/rules/audit-workflow.md`) so the fix can be confirmed shipped.

### Indexed / benign states

| Status | What it means | Action |
|---|---|---|
| **Submitted and indexed** | In the sitemap and indexed. The target state. | None. In a deliverable, confirm the page is indexed — don't imply work is needed. |
| **Indexed, not submitted in sitemap** | Indexed but missing from the sitemap. | Add to the XML sitemap so Google has a reliable recrawl signal. Benign but worth cleaning up. **Validation:** confirm the URL appears in the live sitemap and re-inspect shows "Submitted and indexed." |
| **Alternate page with proper canonical tag** | Google found the URL, saw a canonical pointing elsewhere, and correctly excluded it. **Expected, not an error** — the parameter/variant is being consolidated as intended. | Usually leave as-is. Only investigate when these grow into the thousands on a small site → run the canonical-child segmentation workflow (`robots-txt-ecommerce-framework.md`) and consider blocking worthless parameter paths. **Validation:** confirm the excluded URL's canonical resolves to a live, indexed parent. |

### The Page indexing export lags — re-verify its rows before diagnosing them

The Page indexing report (and its per-status exports, audit inputs #7/#8) lags GSC's own URL Inspection verdicts, sometimes by weeks. In practice a material share of the URLs in a "Crawled – currently not indexed" or "Discovered – currently not indexed" export are **already indexed** by the time the export is read — the same stale-snapshot behavior seen first-hand on stale noindex records (SameDay: 98 URLs recorded as noindex-excluded whose tags were long gone) and stale 404s (Superior `/emergency-services/`). AJ Kohn reports the same pattern across clients (LinkedIn, 2026-08): he re-inspects the export sample on a cadence and trends the share actually indexed, because clients panic over "de-indexing" that is mostly report lag.

Operational consequences:

1. **Never diagnose export rows directly.** Run `scripts/verify_gsc_exports.py <client>` first — it fetches the current URL Inspection verdict for every row and writes `Clients/<name>/data/gsc_export_verification.json`. The technical auditor consumes that file and drops rows Google has since indexed, so findings count only confirmed URLs. Without it, the finding ships with an explicit unverified-snapshot caveat.
2. **Trend the accuracy, don't just measure it once.** Each verification run appends a summary (reported / actually indexed / % actually indexed). A **steady** actually-indexed share is ordinary report lag; a **falling** share across runs means Google is genuinely de-indexing pages from the bucket — that trend is the real early-warning signal, and neither number alone carries it.
3. **The export caps at 1,000 rows per status.** On sites larger than that, the export is a sample, not the population — say so wherever counts from it appear.

### Not-indexed states that are usually a problem

**Discovered – currently not indexed** — Google knows the URL exists but hasn't crawled it. No last-crawl date recorded.
- *Causes:* weak/zero internal linking (orphan), crawl-budget rationing on large sites, mass low-value URL generation diluting budget, perceived low value from similar pages already seen.
- *Diagnose:* is the URL in the sitemap? How many internal links point to it? The most common actionable driver is **orphaning** — a healthy, content-complete page with zero inbound internal links (reference case: Beehive Park City `/water-heater-installation/` — fully built, in sitemap, but the Park City hub linked to 8 sibling pages and skipped this one; its indexed siblings *were* linked).
- *Remediation:* add internal links from high-authority, frequently-crawled parents (homepage, hub pages, siblings) with descriptive anchor text; ensure it's in the sitemap; prune competing low-value URLs; then Request Indexing as a hint (it doesn't force indexing — signals do).
- *Validation:* view source on the linking hub and confirm the new link is present; then GSC URL Inspection → Request Indexing → confirm the state flips to "Submitted and indexed." Recrawl typically lands within 7–14 days; re-request if not.
- *Expected outcome:* **Ranking Lever** when it unblocks a finished money page (not Hygiene) — the page was invisible and becomes eligible to rank.
- *Auditor coverage:* `technical_auditor._check_discovered_not_indexed` (needs `gsc_discovered_not_indexed.csv`; cross-refs `internal_links_in`; drops rows `gsc_export_verification.json` shows as already indexed — see the report-lag section above).

**Crawled – currently not indexed** — Google crawled it and *chose* not to index. Not a verdict on its own: Google's Page indexing help calls it a common status that "doesn't necessarily indicate an issue", and the cause can be a render failure as easily as weak content.
- *Causes:* thin or low-value content lacking a reason to index, near-duplication that doesn't fit a formal duplicate category, weak internal + external signals, or rendering that leaves the page looking empty (including robots.txt blocking the theme's CSS or JavaScript).
- *Rule out rendering first:* run URL Inspection → Test live URL → View tested page on the important URLs. If the rendered HTML or screenshot is missing the main content, it is a Stage 2 problem (see [stage-3-indexability.md](stage-3-indexability.md) symptom decoder), and a content rewrite will not change it. Call it a quality judgment only when the render is complete, and treat it as a site-quality signal only when many pages show the status with no technical cause.
- *Diagnose:* compare body content against indexed siblings. Reference case: Superior `/plumbing-services/` — 200, indexable, in sitemap, but no H1, zero H2s, ~27 words of body copy (a bare hub linking to children) vs a sibling service page with an H1, 14 H2s, ~2,700 words. That thinness is the reason.
- *Remediation:* for each page ask "what reason does Google have to index this?" and provide one — depth, originality, genuine end-user value; merge/prune pages that can't clear the bar; strengthen internal links; verify the rendered HTML actually contains the content. **Re-submitting without an on-page change will not help** — Google already crawled and passed.
- *Validation:* re-fetch and confirm an H1 is present and body word count is materially higher and comparable to indexed siblings; then Request Indexing → confirm "Submitted and indexed."
- *Auditor coverage:* `technical_auditor._check_crawled_not_indexed` + `content_pruning_auditor.py` (needs `gsc_crawled_not_indexed.csv`; cross-refs `word_count`; drops rows `gsc_export_verification.json` shows as already indexed — see the report-lag section above).

**URL is unknown to Google** — Google has no record of the URL at all.
- *First, rule out the wrong-URL trap* (see the always-verify rule): confirm you inspected the exact live canonical (trailing slash, `www`/non-`www`, correct slug). A slug typo or slash variant produces this even when the real page is indexed.
- *If the URL is genuinely live:* it's undiscovered — not in the sitemap, no internal or external links. Add it to the sitemap, link to it internally, Request Indexing.
- *If the URL 404s:* the "content item" was never published (or lives at a different slug). This is a content-delivery gap, not an indexing issue — flag it for the content owner. Reference cases: Comfort `/emergency-ac-repair-west-haven/` and `/ac-tune-up-checklist-west-haven/`, Superior `/whole-home-air-filtration/` all returned 404 and were absent from the sitemap.
- *Validation:* confirm live 200 + presence in sitemap + Request Indexing → re-inspect for "Submitted and indexed."

### Duplicate / canonical states

**Duplicate without user-selected canonical** — near-duplicate pages with no canonical declared, so Google picked one for you.
- *Remediation:* declare a self-referencing canonical on the intended parent and canonicalize the variants to it; differentiate the content if both should stand alone. *Auditor coverage:* `technical_auditor._check_missing_canonical` (declares the gap; the duplicate grouping is `MANUAL` from the GSC export).

**Duplicate, Google chose a different canonical than the user** — you declared a canonical; Google overrode it. Google treats the declared canonical as a hint and judged another page the better representative.
- *Diagnose:* compare declared vs Google-selected in URL Inspection. Usually driven by near-duplicate content, an internal-linking imbalance, or conflicting sitemap/redirect signals.
- *Remediation:* if the declared canonical is correct, align every signal to it (internal links, sitemap, redirects) and differentiate the content from Google's pick; if Google's choice is genuinely better, update the declared canonical to match.
- *Validation:* re-inspect and confirm Google-selected canonical now equals the declared canonical. Allow time before the re-inspect. Google's canonicalization troubleshooting page: "Even after fixing content issues, Google might hold pages in a duplicate cluster for up to two weeks." (added 2026-11-10)
- *Auditor coverage:* `technical_auditor._check_declared_vs_selected_canonical` (needs the `Google-Selected Canonical` column from URL Inspection data in the crawl). Also flagged as a checklist item in `robots-txt-ecommerce-framework.md`.

### Redirect / removal states

**Page with redirect** — the source URL redirects; Google indexes the destination, not the source. Usually benign.
- *Keep vs remove is a decision, not an automatic cleanup.* Apply the redirect keep/remove decision tree in `technical-seo-agent/SKILL.md`: keep if the redirect is structural (HTTP→HTTPS, `www`/non-`www`, trailing-slash) OR the source has external backlinks OR it passes traffic; fix the *linking source* if it's an active redirect still linked internally or in the sitemap; only remove the rule if it's non-structural, unlinked, and traffic-less.
- *Always live-verify* — GSC's redirect list is not 100% accurate and reports source URLs that no longer redirect, plus far more than exist live (redirect memory). Bulk-check exported URLs against live status before acting.
- *Watch for hijacks:* a "Page with redirect" pointing to a spam/irrelevant destination is a real problem — address immediately.
- *Auditor coverage:* `technical_auditor._check_redirect_chains` / `_check_internal_links_to_redirects` (chains and internal links through redirects; the keep/remove judgment is `MANUAL`).

**Not found (404)** — the URL returns 404. Expected for genuinely deleted content; a problem when the page should exist.
- *Rule out the stale-404 trap:* Test Live URL. If it returns 200 now, the page was fixed after Google's last crawl — the record is stale; Request Indexing to force a recrawl (reference case: Superior `/emergency-services/`).
- *If genuinely gone:* leave it 404, or return 410 to drop it faster; 301 only if there's an equivalent destination (don't blanket-redirect to the homepage). Remove from the sitemap and fix internal links pointing to it.
- *Validation:* live test shows the expected status; if redirected, `curl -I` shows `301` + correct `Location`.
- *Auditor coverage:* `technical_auditor._check_404_errors`.

**Soft 404** — 200 status but the page looks like an error/empty page to Google.
- *Remediation:* if it's an error page, return a real 404/410; if it should exist and rank, add substantive unique content.
- *Auditor coverage:* `technical_auditor._check_soft_404s` (cross-refs GSC zero-impression signal when `gsc_performance.csv` is present).

### Blocked / excluded states

| Status | Meaning | Remediation | Auditor |
|---|---|---|---|
| **Excluded by 'noindex' tag** | A `noindex` directive is present. | If intentional, fine — keep it out of the sitemap. If the page should rank, remove the `noindex` (check meta robots **and** the X-Robots-Tag header — the header is invisible in view-source). Removing a `noindex` from a money page is a **Ranking Lever**, not hygiene. **Validation:** re-fetch, grep for `noindex` (none), re-inspect "Indexing allowed: Yes." | `_check_noindex_pages`, `_check_x_robots_tag_noindex`, `_check_noindex_in_body` |
| **Blocked by robots.txt** | A `Disallow` rule blocks the crawl. | Confirm the block is intended. If the page should index, remove the matching `Disallow`. Note a blocked page can still be indexed if externally linked. | `_check_blocked_by_robots` |
| **Blocked due to unauthorized request (401) / access forbidden (403)** | Auth or WAF/bot-protection returned 401/403. | Disambiguate first — a crawler-triggered 403 can be a false positive while Googlebot passes (this is why curl often returns 403 on WAF-protected sites that are indexed fine). Verify with URL Inspection's live test before recommending any WAF change. | `_check_401_errors`, `_check_403_errors` |
| **Page indexed without content / server error (5xx)** | Rendering or server failure at crawl time. | Fix the render (route to `javascript_rendering_auditor.py`) or the server error; then Request Indexing. | `_check_5xx_errors` |

## How to use this file

1. **Every indexation finding names its state and its live-verified evidence.** Don't ship "not indexed" — ship "Discovered – currently not indexed; live 200, indexable, in sitemap, zero internal links → orphaned" with the verification behind it.
2. **Match the remediation to the state's actual cause.** Discovered-not-indexed is (usually) an internal-linking fix; Crawled-not-indexed is a content fix; a stale 404 is a reindex request. Prescribing a content rewrite for an orphan, or a reindex for a thin page, wastes the client's effort.
3. **Tag the expected outcome.** Unblocking an indexable money page (orphan link, `noindex` removal, stale-404 reindex) is a **Ranking Lever**; cleaning benign "Alternate page with proper canonical" noise is **Infrastructure Hygiene**. Distinguish them per `.claude/rules/audit-workflow.md`.
4. **Never surface GSC status labels' internal reasoning as client copy beyond the plain status.** State the principle and the fix directly (`.claude/rules/report-formatting.md`).
5. **Re-verify Page indexing export rows before diagnosing them** (report-lag section above). To monitor whether specific URLs under remediation actually get indexed month over month, use `scripts/index_watchlist.py` — it snapshots the watch set's URL Inspection states alongside the monthly index audit and prints each URL's state progression.

## Source

Daniel Foley Carter, "GSC Lessons" series (Page Indexing, URL Inspection, Alternate-canonical, Page-with-redirect), knowledge-base transcripts; cross-referenced against Google Search Central's Page Indexing documentation and validated against live client indexation checks (Comfort Solutions, Superior Water & Air, Beehive Plumbing), 2026-07. Aligns with `technical_auditor.py` indexation checks and the redirect / robots.txt remediation workflows in `technical-seo-agent/SKILL.md` and `robots-txt-ecommerce-framework.md`.
