# Decision Log — Ultimate SEO Auditor

Why things are the way they are. Newest last. A reversal gets a new entry; the
original stays.

---

## 2026-09-03 — Client vocabulary is never length-filtered

**Decision.** `_service_terms()` in `scripts/run_1_5.py` harvests the client's
service vocabulary from money-page slugs at a 2-character floor, rejecting noise
by an explicit name list (`our`, `all`, `one`, `add`, `ons`, `pro`, `up`, `we`)
rather than by word length.

**Reasoning.** The previous `len(w) > 3` guard looked like harmless short-word
hygiene and deleted every industry acronym. "erp" — from
`/services/wholesale-erp-solutions` — never entered Cudio's term set, so
`/blog/erp-system-levels` scored Business Value Low and was dropped from
selection while carrying 11,853 impressions/mo at position 11.2. The grading was
also inconsistent: sibling ERP posts scored Medium purely because
"implementation" or "professional" happened to sit in their slugs. Rejected
alternative: filtering the noise list inside the shared `_terms()` helper, which
also feeds `_topic_fit()` and would have silently changed target-query selection
— a different task's output, changed without being asked. `_terms()` took a
`floor` parameter instead.

**Context.** Verified against real slugs across all 9 clients before choosing the
floor: `air`, `gas`, `tub`, `lot`, `saw`, `cut`, `kit`, `led`, `pen`, `ice`,
`lab`, `nad`, `ghk`, `gym`, `dtc`, `red`, `low`, `ac`, `iv`, `ev` are all real
service or product names. Same defect still live at
`scripts/verify_4_3_flags.py:112` (`slug_tokens`), deliberately not changed —
4.3 had not run for the month and shifting overlap thresholds unasked would move
findings.

---

## 2026-09-03 — An unworked 1.5 candidate rolls to 1.8, never back to 1.5

**Decision.** A URL that appeared on a prior workbook's 1.5 Candidate List is
blocked from 1.5 for three workbooks, whether or not it was worked. If it was
never worked (never reached 1.8 Monthly Plan or the 2.3-3.1 Refresh Log) it is
carried into the next month's **1.8** as its own scored signal, via
`read_carryforward()` in `scripts/plan_1_8.py`.

**Reasoning.** Two standing rules collided. "No URL repeats as a candidate" and
"unimplemented findings roll forward" cannot both hold if the only destination is
1.5. Routing the unworked population to 1.8 satisfies both: 1.5 owes a fresh
shortlist every month, and nothing identified as valuable falls out of the
workbook. Rejected alternatives: blocking the page outright for three months,
which benched SameDay's entire furnace cluster going into Utah heating season
(six pages offered in August, none worked); and re-offering it in 1.5, which
reproduces the repeat the owner has challenged repeatedly.

**Context.** Owner call, 2026-09-03. The gate previously read only 1.8 and the
Refresh Log — the tabs recording work *done* — so a page offered and skipped left
no trace and repeated freely. That let 7 URLs repeat across 5 clients.

---

## 2026-09-03 — Striking distance widened to position 4-20 at 50 impressions/mo

**Decision.** `SD_MAX` 15.0 → 20.0 and `SD_MIN_IMPR` 100 → 50 in
`scripts/task_1_5.py`.

**Reasoning.** The impression floor was the binding constraint, not the position
band — widening position alone moved Comfort from 2 candidate pages to 4, while
dropping the floor took it to 12 (Arsenal 9 → 21, Bart's 5 → 16). A 100/month
floor is written for national search volume and systematically excludes local
commercial queries, which are the revenue on this client base: "furnace repair
sandy utah" can carry 40 impressions a month and still be worth winning.
Position 20 is the floor the owner already works to, so page 2 → page 1 is in
scope and deeper is not.

**Context.** Triggered by 1.5 returning 0 rows for SameDay, Arsenal and Bart's
and 1 for Comfort. Measured on the August window before changing anything.

---

## 2026-09-03 — A release is 10% of the sitemap on one date, not 20%

**Decision.** `DEPLOY_SHARE` 0.20 → 0.10 in `scripts/run_1_5.py`, keeping
`DEPLOY_MIN = 10`.

**Reasoning.** A deploy restamps `lastmod` site-wide, and the 90-day recency gate
read that as content refresh and benched the pages. At 20% the detector missed
SameDay's 56-URL day (18.1%), Superior's 44, Comfort's 38 and Beehive's 70 — no
home-services team edits 40 pages in an afternoon. Every newly-caught date is
plainly a release; Beehive's includes 120 URLs on a single 2023 date. Rejected
alternative: scoring against a multiple of the median daily edit count, which is
cleverer and harder to audit, when a share plus an absolute floor already
separates the cases. Bart's and Snow flag nothing new at 10%, which is the
control showing it does not just flag everything.

**Context.** Freed 132 pages on SameDay, 83 Superior, 71 Comfort, 70 Beehive.
SameDay went 0 → 4 candidates on this change alone.

---

## 2026-09-03 — 1.5 Section A ships with the "after" columns empty

**Decision.** Section A carries target query, page, pre-change position and
clicks, the date the change went live, and an explicit note that the after
columns close in next month's workbook. `Pos After` and `Clicks After` are left
blank for September.

**Reasoning.** Every August edit landed 24-28 August, so August GSC data is
roughly 85% pre-change and September holds two days. Filling the after columns
would produce numbers that look measured and are actually the before-window
relabelled — the precise failure that makes a client conclude the work does not
move anything. Rejected alternative: using August as "after" against a July
"before", which is contaminated in the numerator and drifts seasonally in the
denominator. September is the first complete post-change month.

**Context.** `scripts/fill_1_5_section_a.py`, new. Work completion was verified
from sitemap `lastmod` rather than the Refresh Log, because the Date Done column
is blank on every client except Education Walkthrough — the work shipped but was
never recorded. Ship dates are reported as unconfirmed for Arsenal (Vercel
restamps the whole sitemap per deploy) and Snow (platform bumps product
timestamps), rather than guessed.

---

## 2026-09-04 — 1.7 evidence files are stamped by run month, not hardcoded

**Decision.** The five `gap_collect.py` evidence filenames (`serps`, `competitor-keywords`,
`verified-gaps`, `serp-winners`, `linkgaps`) take a `STAMP` derived from the run date instead of
the literal `2026-08` they carried.

**Reasoning.** August was the first 1.7 run, so the stamp was written as a constant. Running any
later month would have overwritten August's SERP snapshot on every client — and that snapshot is
precisely what the tab's "new competitor entered top 10?" header diffs against, so month two would
have destroyed the baseline it needs to answer its own question. Rejected alternative: passing the
stamp as a CLI argument on every phase, which puts the burden on whoever types the command and
fails silently when forgotten.

**Context.** Fixed before the September run touched any client. The diff worked on first use: it
found ars.com and mountainhomeutah.com gone from SameDay's top 10, sosairutah.com and ascendhvac.com
gone from Comfort's, and observationcopilot.com gone from Education Walkthrough's.

---

## 2026-09-04 — A client may have several SERP origins

**Decision.** `LOCATION` in `gap_collect.py` accepts a list as well as a string. Bart's Asphalt runs
at Ann Arbor, Lansing and Jackson; every other client is unchanged.

**Reasoning.** The existing rule was "local clients get local SERPs" because a national pull strips
the market. Bart's competes in three metros and the leader differs in each — T. Burke's tops Ann
Arbor, McKearney tops Lansing, Michigan Paving tops Jackson — while its scoped queries carry no city
modifier, so the SERP origin alone decides which market comes back. A single origin would have
discarded two thirds of the footprint. Rejected alternative: picking the HQ metro (Jackson), which
is defensible and would have hidden the two markets where Bart's is weakest.

**Context.** Matches how the competitor identification was run (60 searches across the same three
markets). Snapshot keys carry the market so next month diffs per market rather than collapsing them.

---

## 2026-09-04 — Competitor brand filtering keys on the brand token, not the domain stem

**Decision.** `gap_collect.py` derives brand tokens by stripping trade words from a competitor
domain (`alliedasphalt.com` -> `allied`) and matches them at word boundaries, using every competitor
in the registry rather than only the two or three chosen for the run. A `NON_BUYER` filter removes
recruitment, scam and complaint queries.

**Reasoning.** The recipe already said to junk-filter competitor brands; the code built its pattern
from the concatenated domain stem, which never matches the spaced form a searcher types. Twenty-seven
of Bart's 111 verified gaps were competitor brand terms ("allied paving", "mckearney asphalt",
"burton paving"), recruitment ("asphalt jobs near me") or "paving scam" — all navigational or
non-buyer, none winnable. Rejected alternative: filtering these by hand at the clustering gate, which
works once and is forgotten the month a different person runs it.

**Context.** Applied to Bart's existing verified gaps as a subtraction rather than re-running live
verification already paid for; the unfiltered list is preserved as `-v1.json`.

---

## 2026-09-04 — 1.5 Section A reports page-level metrics with a control, and never page average position

**Decision.** Section A carries query position, query clicks, page clicks, page impressions, page
CTR, and a control column showing how untouched pages moved over the same window. Page average
position is deliberately excluded.

**Reasoning.** Page average position is impression-weighted across every query a page surfaces for,
so a page that starts winning MORE terms reads as if it got worse — EW's Danielson page went 7.4 to
14.8 while clicks went 21 to 48. Putting that column on a sheet invites someone to report a win as a
loss. The control exists because without it seasonality reads as result: that same page gained 129%
clicks, and the question of whether that is our work is only answerable against the pages we did not
touch. Rejected alternative: comparing against one hand-picked sibling, which is what I did first and
which gave the opposite (wrong) answer to the population median.

**Context.** `scripts/fill_1_5_section_a.py`. Page totals come from the page dimension, never summed
from query rows — GSC withholds anonymized queries, which gave 1 click against the page dimension's
21 on the same page.

## 2026-09-04 - Snow's 1.7 clusters re-derived from the September gap set

**Decision.** Snow's `gap_analysis/analysis.yaml` is re-authored over
`2026-09-verified-gaps.json` rather than shipped as carried forward. Two live
clusters are added (teeth bleaching vocabulary, 255,700/mo; dentist-grade
whitening at home, 21,400/mo), the peroxide-free cluster is re-routed from
`/products/sensitive-hydroxyapatite-toothpaste` to `/collections/sensitive`, and
the competitor_set and baseline_note cells are rewritten with September figures.

**Reasoning.** The alternative was to ship the existing file, which
`author_1_7_snow_v2.py` wrote from the August snapshot on 2026-08-21. It was
authored before the September gap collection finished at 17:35 on 2026-09-04, so
every figure in it described August. The diff is not cosmetic: August held 434
verified gaps and September holds 672, and the four largest new gaps are
bleach-worded queries that do not appear in the August set at all. Shipping the
carried-forward file would have reported the largest new demand of the month as
absent. The re-route was forced separately: the hydroxyapatite toothpaste page
was listed in the August workbook and repeats are not carried into a second
consecutive month.

**Context.** Touches `Clients/Snow/gap_analysis/analysis.yaml` and Snow's 1.7
tab. Two filter defects surfaced and are worth knowing before the October run.
Competitor brand-stem queries survived `filter_1_7_brand_gaps.py` (opalesce
9,900, opalescent 9,900, opulescence 390): `spaced_stem()` requires every
character of the domain stem in order, and these are truncations or misspellings
of it, so 20,190/mo of navigational demand had to be excluded by hand.
Separately, `recluster_1_7.py` groups by competitor URL without stripping query
strings, and Opalescence carries a `srsltid` tracking parameter, so one page
presented as many one-keyword clusters until the URLs were normalised.

## 2026-09-04 - The 1.5 recency gate splits by pool

**Decision.** `run_1_5.py` keeps its 90-day sitemap-lastmod gate on the DECAY
pool and applies a new 28-day `RECRAWL_DAYS` gate to the STRIKING DISTANCE pool.

**Reasoning.** The alternative was the single 90-day gate applied to both, which
is what shipped. Its own rationale is decay-specific: a page edited inside the
measurement window is being compared against its own pre-refresh self, so the
comparison is invalid. Striking distance has no prior period and is measured on
current position, so that reasoning does not reach it. The cost was measurable
rather than theoretical: all 18 of Bart's candidates were gated on edits its own
CMS made 29 to 78 days ago, and the tab shipped empty for a client we have never
worked on. What striking distance does need is the recrawl window, so that a
page edited days ago is not briefed before its position settles. With the split,
Bart's returns 7 candidates and the line-striping page is still correctly held
at 21 days.

**Context.** `scripts/run_1_5.py`, constants block and the section-B loop.
Affects every client, but only Bart's was re-run - see the next entry.

## 2026-09-04 - The other eight clients are NOT re-run under the new gate

**Decision.** Only Bart's 1.5 is rebuilt after the gate change. The eight
clients whose 1.5 tabs were already complete keep the tabs they have, and the
looser gate applies to them from the October run.

**Reasoning.** The alternative was re-running 1.5 for all nine for consistency
within the month. Rejected because `run_1_5.py` re-ranks and rewrites section B
wholesale rather than appending, and `fill_1_8.py` has already synced each 1.5
tab's "Selected in 1.8?" column against the locked 1.8 targets. Re-running would
re-order section B, potentially drop a URL that 1.8 now depends on, and break
the rule that the two tabs carry the same URLs. Trading a locked, audited 1.8
lock for gate consistency inside one month is the worse deal; the inconsistency
is one month wide and self-clearing.

**Context.** Accepted cost: Bart's section B was built under a different gate
than the other eight this month. Worth stating if the tabs are compared.

## 2026-09-04 - Education Walkthrough 1.5 and 1.7 are blocked, not deferred

**Decision.** EW's 1.5 section B and 1.7 tab are left empty and reported as
blocked. No candidate list is written for EW this month until the block clears.

**Reasoning.** The alternative was to bypass the recency gate for EW, which
`preflight()` deliberately fails closed on. EW's BlogVault firewall returns 403
to this IP on every URL tested - sitemap_index.xml, robots.txt content and
article pages - under "Blocked because of Malicious Activities", Reference ID
20626643586a9b3dc1c8eed. The block is not a user-agent problem: it reproduces
with a browser UA, with a Googlebot UA, and inside a real Playwright browser.
Google itself is unaffected and downloaded the sitemap on 2026-09-02. With no
reachable lastmod and no reachable page, the gate has no input and a written tab
would be candidates nobody verified.

**Context.** Unblock is a BlogVault allowlist entry for this IP; the reference
ID is what their support needs. Also blocks live-state verification for any EW
deliverable, so it reaches beyond this task. EW's 1.6 tab is unaffected and
complete, and its 1.5 section A was filled earlier from Search Console, which
does not touch the site.

## 2026-09-15 — Weekly ranking reports run locally, not in n8n

**Decision.** The weekly client ranking pipeline (SEMrush CSV → branded PDF →
one email per client to team@) runs as a local Python job under Windows Task
Scheduler, not as an n8n workflow. `scripts/weekly_rankings.py --send`, wrapped
by `scripts/run_weekly_rankings.cmd`, registered via
`scripts/register_weekly_task.ps1`.

**Reasoning.** n8n was the expected home and was rejected: the branded PDF
engine needs Playwright with headless Chromium plus our Python renderer, and
the agency n8n runs on shared Bluehost hosting where neither can be installed.
Once the PDF has to be built on a controlled machine anyway, moving only the
send step into n8n buys nothing — the build already depends on that machine
being awake, so an always-up sender has nothing to send when it is not. A
hybrid (local build → Drive → n8n watches the folder and mails) was costed and
set aside: it adds a second moving part and puts the Gmail credential in n8n,
in exchange for an execution log. Still available if the team later wants that
visibility.

Also rejected upstream, on cost: SEMrush My Reports at $20 per report per send
($800/mo across 10 clients weekly), a Janelle seat at ~$80/mo (which does not
schedule anything), and the SEMrush API (needs a Business upgrade plus
undisclosed API-unit pricing). The manual Monday export costs $0 and 10-20
minutes.

**Context.** Verified end to end 2026-09-15: three clients built and delivered
to team@ over Gmail SMTP. Touches scripts/weekly_rankings.py, scripts/mailer.py,
Clients/_weekly_rankings/, and .env (GMAIL_USER / GMAIL_APP_PASSWORD /
RANKINGS_TO). The "where is the n8n workflow?" question has already come up
once; this entry exists so it does not need re-deciding.

## 2026-09-28 — Merge 2.3, 2.4, 2.5 and 3.1 into one page-optimization task

**Decision.** Propose to Janelle, effective October 2026, that the four page tasks become one ClickUp task, "2.3 Implement Page Optimizations (Refreshes + Quick Wins)", backed by one workbook tab "2.3 Page Optimizations" (Pages section: one row per page; Changes section: one row per change). It replaces the "2.3-3.1 Refresh Log", "2.5 Quick Wins" and " Page Optimization" tabs. The quick-win test (queries at positions 4-20 absent from BOTH title and meta, with real impressions/clicks) is the only basis for any title/meta change, run site-wide, max five quick-win pages, one title/meta recommendation per URL per month. 1.8, 2.1, 2.2 and 3.2 stay separate.

**Reasoning.** Rejected: blending only in ClickUp and keeping the tabs (recommended first, to spare ~12 scripts that read the tabs by name). The owner chose one tab because the same page's title/meta was being recorded in two tabs under two standards; script rework accepted. Rejected: two sections split by page type, which left the change list in two places. Rejected: 1.5 shortlist as the quick-win pool, which missed the largest gaps (Cudio /blog/what-is-odoo-software, 5,604 impressions, Aug 2026). 2.1/2.2 stay out as separate lanes (dev and VA, different formats and sources); 1.8 is the decision, not execution; 3.2's link log runs after refreshes.

**Context.** Proposal only. Janelle applies all ClickUp and workbook-template changes; we make no ClickUp edits. Our follow-up: switch every script that reads the three retired tabs to the new tab before October's Week 2 fill, and rewire the 4.5 Template Report formulas (rows 5 and 9).

## 2026-09-28 — Level 10 Leaders migration: Cloudflare Bulk Redirects with subpath matching on every row

**Decision.** thebreakthrough.co redirects to level10leaders.com via one Cloudflare Bulk Redirect list: every mapped URL, 6 archive patterns and the homepage row, all with subpath matching TRUE, include subdomains FALSE, preserve path suffix FALSE, listed for both apex and www (950 lines). The homepage row doubles as the catch-all. Page value was judged on two tests only: a top-20 non-branded leadership ranking with volume, or a followed link from an editorial site.

**Reasoning.** Rejected: a Single Redirect catch-all rule. Cloudflare runs Single Redirects before Bulk Redirects, so a wildcard catch-all would swallow every mapped URL. With subpath matching on every row, Cloudflare's documented most-specific-path rule makes page rows beat section rows beat the homepage. Rejected: Squarespace URL mappings on the old site, which cannot redirect "/" and only fire once each page is deleted, so the old site must stay live. Include subdomains stays off because go.thebreakthrough.co (HubSpot booking links used by the new site) and 48 TalentLMS client portals live under the old domain. Rejected as a value test: raw traffic or any ranking, since the old blog's rankings are almost entirely accidental matches (boat, time-zone and bar-menu queries).

**Context.** Prospect deliverable for Ryan Castle, Clients/Level 10 Leaders/Migration Plan/. No GSC, GA4 or Cloudflare access; data from DataForSEO and Semrush, so the plan requires a GSC recheck of the Retire list before go-live.

## 2026-09-29 — Level 10 Leaders migration: lean data-backed migration (Option A) replaces the relevance-based content plan

**Decision.** Only pages with a data reason move from thebreakthrough.co to level10leaders.com: relevant rankings, a followed link from a real site, or relevant traffic. That is 11 pages (4 industry pages, 5 blog posts, 2 podcast episodes). Every other content page is retired with a redirect: blog posts to /articles, episodes to /podcast. The 2026-09-28 relevance + depth plan (139 posts, 111-episode archive) is kept as Option B, an optional phase 2 content project, in its own sheet tabs and redirect list.
**Reasoning.** Rejected: the relevance-based plan as the core recommendation. Ryan asked for an 80/20 migration based on traffic, rankings and backlinks, not an SEO project. The data showed about 56 est. visits a month on in-scope pages (27 to the homepage), only 2 top-20 relevant rankings, and 155 of 167 linking domains pointing at the homepage. Nathan: migrating low-value content costs more than it returns and can hurt the new domain, so net-new content later is the better growth path. Also rejected: building a /podcast-archive. /podcast already exists on the new site.
**Context.** Reverses the content outcome of the 2026-09-28 entry. The Cloudflare redirect design from that entry stands unchanged. Working Google Sheet 1us6ybi3tt8IJlI0MnR-SoIDmTYrz_BFWqtok8PzQE4g, updated in place with Option A and Option B tabs. Hours for the quote live in an internal note, not the client PDF.

## 2026-09-29 — Quality Rater Guidelines page grader is built in Ultimate SEO Auditor, not Content AI Agent

**Decision.** The subsystem that grades every page against Google's Search Quality Rater Guidelines (Page Quality plus Intent Match), maps pages semantically and sizes them by GSC clicks is built in Ultimate SEO Auditor, in scripts/ and Skills/ rather than the paused Streamlit app. Whatever it needs from Content AI Agent (page-type classifier, commodity rubric, YMYL detector, keep/update/consolidate/delete overrides and related prompts) is ported into this project.
**Reasoning.** Rejected: Content AI Agent, recommended first because it already had four of the six parts (per-page LLM scoring, drift zones, keep/delete verdicts). The owner ruled capabilities portable between projects, so the deciding factor became where the rating is consumed and re-run. The monthly workbook here already waits on "the 1.8 quality review" (tasks/2.1.md) and routes pages to pruning (tasks/4.3.md), and the client registry, monthly GSC snapshot, month-close report and pre-delivery verification gates all live here. Rejected: Content Optimization, which works on one unpublished draft with no GSC data and is standalone by its 2026-09-14 decision. Content AI Agent keeps the rewriting of flagged pages (voice and drafting tools).
**Context.** Prompted by Dan Hinckley's LinkedIn post (2026-09-29) grading 1,600 pages on the rater scale. Analysis at ~/.claude/analyses/2026-09-29-hinckley-qrg-page-grading.md. Rubric source: the Quality Rater Guidelines dated September 11, 2025. Planning in progress, nothing built yet.

## 2026-09-29 — Quality Rater Guidelines grader is a standalone, on-demand subsystem, not part of the monthly workbook

**Decision.** The grader runs only when the owner invokes it for a client. It is not wired into the monthly SEO workbook, the 1.8 plan or any workbook task. Placement in Ultimate SEO Auditor (previous entry) stands.
**Reasoning.** The previous entry's main reason (the workbook already waits on "the 1.8 quality review") does not apply: the owner confirmed the subsystem has nothing to do with the workbook. Placement still holds on the remaining grounds, all of which live only here: body-text extraction (Skills/semantic_site_map/text_loader.py), the clustered semantic map sized by clicks, complete page-by-query Search Console pulls (scripts/gsc_api.py), per-client fact cheats (fact-cheats/) as the reputation input, and the pre-delivery verification agents. Rejected: feeding the workbook's quality review, which was an assumption and was never requested.
**Context.** Corrects the reasoning of the entry above, not its outcome. Planning in progress, nothing built yet.

## 2026-10-05 — Quick wins come from a site-wide 1.8 scan, not from the 1.5 list

**Decision.** The October workbook's 1.8 section A is a site-wide quick-win scan (`scan_title_gaps.py`, positions 4-20, query missing from title and meta). It is the only source of quick-win pages. The scripts that took 1.5 as the sole input (`build_2_5_candidates.py`, `build_2_5_from_1_5.py`, `widen_2_5_pool.py`) are moved to `scripts/_retired/`.
**Reasoning.** Reverses the 2026-08-24 rule that 2.5 reads 1.5 and nothing else. That rule was right while the task text named 1.5 as its input; the October template and the ClickUp 2.3 task now name the site-wide scan instead, so the named input changed. Rejected: keeping 1.5 as the only input. It hid the largest gaps (Cudio, 2026-08-25: 34 pages with a gap, six on the tab) and assumed the title was why a page was stuck.
**Context.** `fill_1_8.py` refuses a quick win the scan did not find or excluded, so the scan stays the single path. Touches tasks/1.8.md, tasks/2.3.md, scan_title_gaps.py, fill_1_8.py.

## 2026-10-05 — Every look back at a prior month goes through one reader, anchored on headings

**Decision.** `scripts/prior_work.py` reads what a prior workbook worked, in the old layout (1.8 section A, Refresh Log, 2.5 Quick Wins) and the new one (2.3 Pages), and 1.5's skip list, 1.8's carry-forward and 1.5 section A use it.
**Reasoning.** Rejected: leaving the fixed ranges (`B5:B14`, `B4:B14`) in each script. They read the wrong column the day a merged-2.3 workbook becomes the prior one and return an empty set without any error, so the three-month skip list would simply stop working in November.
**Context.** Other readers (`url_cooldown.py`, `gate_1_7_worked_pages.py`) were written separately by parallel agents and still carry their own copy; folding them into prior_work is open.

## 2026-10-05 — Provisional defaults taken for four open questions (owner has not answered)

**Decision.** (1) One 90-day cooldown across the whole 2.3 tab, with rows carried over unfinished exempt until they ship. (2) The ClickUp quick-win test (positions 4-20) is the entry condition; the house median-position band only blocks pages with median over 20. (3) 2.3 baselines use the 90-day window 1.5 uses. (4) Fix-sheet items resolved on 4.5 counts dated rows, as the template formula does.
**Reasoning.** The owner said to finish what was started and did not answer the four questions asked on 2026-10-05, so the recommended answer was used and each sits behind one named constant (`url_cooldown.COOLDOWN_MONTHS` / `CARRYOVER_EXEMPT`, `build_2_5_brief.BAND`, `fill_1_8.baseline_window`, `fix_4_5_section_a.COUNT_DISTINCT_FIX_ISSUES`). Rejected: blocking the framework work on answers.
**Context.** Reverse any of them by flipping the constant and the matching line in tasks/2.3.md. Not confirmed by the owner.

## 2026-10-05 — Cooldown window confirmed at three months, counted by workbook month

**Decision.** A page worked in a month is blocked for the next three months and eligible again in the fourth: worked in September, blocked October, November and December, eligible January. The month is the workbook month the page appeared in; pages carried over unfinished stay exempt until they ship. One constant, `url_cooldown.COOLDOWN_MONTHS = 3`, governs the 1.5, 1.7 and 1.8 gates, and `fill_1_8.py` enforces it when the plan is locked.
**Reasoning.** The owner asked whether the rule was six months; no six-month rule exists in the recipes, the code or memory, and the owner then chose three ("give 90 days after the optimization was implemented"). Rejected: six months, which would keep everything worked in August and September blocked until February and March and could starve candidates on sites with few money pages.
**Context.** Confirms default (1) of the 2026-10-05 provisional-defaults entry. Counting is by calendar month, not by the day a change shipped, because the workbook records the month, not the day.

## 2026-10-05 — 1.1 section B Flat is computed from entered and left, not as ranking minus improved minus declined

**Decision.** Flat = ranking + left - improved - declined, written only when `start - left + entered = ranking`; the Notes open with `ranking + not-ranking = tracked`.
**Reasoning.** SEMrush counts keywords that entered the top 100 as improved and keywords that left it as declined, so the recipe's old identity went negative (Superior Utah, -5) and understated Flat on every other row (Bart's read 6; the real figure is 12). Rejected: keeping the old identity and clamping negatives to zero, which would hide the error on the rows where it happens to stay positive.
**Context.** Evidence is internal to SEMrush's own response (top-3 band: 5 improved, only 2 keywords in the top 3 at the start). Changes `task_1_1.b_row`, tasks/1.1.md and every section B row written before this entry.

## 2026-10-05 — 1.2 findings are routed to 2.1 and 1.8 by script, as part of 1.2

**Decision.** `build_2_1_from_1_2.py` turns every 1.2 finding into 2.1 fix rows and 1.8 section C rows from the findings log and the per-URL index cache; `route_to_1_8.py` writes section C; `verify_routing.py` recounts every number and URL independently. "Unknown to Google" and "Discovered - currently not indexed" become one not-yet-crawled group. Never-crawled blog posts get a HOLD row when 10 or more posts of the same kind sit in Crawled - currently not indexed.
**Reasoning.** The owner said 1.2 has dependencies and the routed findings must populate 2.1 and 1.8. Rejected: hand-authoring fixes.yaml per client, which is how the SameDay September file drifted from its findings. Rejected: separate rows per Search Console label, because the API flips individual URLs between the two labels between inspections, so the split would change on a re-run. Rejected: link-building tasks for old posts Google has already declined in bulk, per the sequencing rule in tasks/2.1.md (links to a post the quality review may prune are double work).
**Context.** The threshold of 10 is a provisional default, not confirmed by the owner. Touches tasks/1.2.md, fill_1_8.py (merges the routed rows when the plan locks), fill_2_1.py (reconcile gate unchanged).

## 2026-10-05 — Leaked Content Warehouse docs live in a standalone primary-source index; commentary is a separate graded layer

**Decision.** `Skills/google-leak-reference/` holds a SQLite index parsed from the Hex package files (all six versions, 2,593 Model modules in 0.4.0, each with a grounded summary and an SEO-relevance grade), a lookup CLI, and a graded copy of 20 commentary sources. It is on-demand and standalone: no auditor, workbook step or QA gate calls it. Third-party claims never merge into the primary facts.
**Reasoning.** Chose the Hex tarballs over scraping hexdocs HTML because they give the same source in structured form, complete, with every version for diffing (0.5.0 onward is stripped to about 190 modules, so 0.4.0 is the only copy of the SEO material). Rejected loading the summaries into skill or prompt context: about 535k tokens of doc text, of which 316 modules grade medium or high. Rejected merging commentary into the facts: the digests cited eight attribute names that appear nowhere in the docs (`pageQualityScore`, `querySatisfactionScore`, `authorReputationScore`, `siteImpressions`, `siteClicks`, `siteNavBrandingScore`, `navBrandWeight`, `ractorScores`) and presented `anchorSpamPenalizer` as a field when the docs only mention an anchor spam penalizer in description text, and a name check cannot tell whether the claim built on a real name is right.
**Context.** Auditing the existing framework against the index found four wrong citations (`QualityAuthorityTopicEmbeddings`, `QualityNavboostCrapsCrapsUrlSignals`, `trustedAnchors`, the PerDocData version-history claim) and showed the 13-month click window is DOJ testimony, not in the leaked attribute docs. Fixed in seo-fundamentals-2026.md, click-signals-abc-framework.md, ranking-factors-checklist-2026.md, seo-audit-methodology/SKILL.md, backlink-agent/SKILL.md, prompts/backlink_prompt.py, auditors/click_signal_auditor.py and auditors/topical_authority_auditor.py. Sentence-level review of the remaining leak sections is not done.

## 2026-10-05 — Leak citations get a mandatory name-check in pre-delivery QA (CHECK 14), alongside the discretionary skill

**Decision.** `check_leak_citations.py` runs as CHECK 14 on any deliverable that names a leaked attribute or module or cites "the leak". Exit 1 (name absent from the docs) and exit 2 (could not run) block delivery; a draft with no leak identifiers is N/A. The `google-leak-reference` skill stays model-invoked for the judgment half: tagging each claim documented, inferred or DOJ-derived.
**Reasoning.** Chose script plus skill over the skill alone because the original wrong citations survived for months with nothing forcing a check, and the owner's standing rule is to change the mechanism when a reminder fails twice. Rejected making the script judge claims: a name check proves a name exists, not that the claim is right, so the tag step stays manual. Exit 2 blocks rather than passes so a missing index cannot read as clean.
**Context.** The first run on the real framework file found `locationDemotion`, an unsupported signal the earlier manual audit missed (the real field is `QualityNsrNsrData.localityScore`; the demotion framing is inferred). Retagged in seo-fundamentals-2026.md, ranking-factors-checklist-2026.md, prompts/technical_prompt.py and auditors/local_seo_auditor.py. Touches Skills/data-analysis/pre-delivery-qa/SKILL.md; CLAUDE.md's stale "10-check" count corrected to 14.

## 2026-10-05 — Registered skills are pointers to Skills/, and the scripted QA checks are enforced by a hook

**Decision.** The seven pointer skills in `.claude/skills/` hold only a frontmatter block and an instruction to read the library file in `Skills/`; `scripts/sync_registered_skills.py` keeps their name and description identical to the library and a test fails on drift. A PreToolUse and PostToolUse hook (`scripts/qa_gate_hook.py`) runs QA CHECK 12 (dashes) and CHECK 14 (leak citations) on anything written under `Clients/*/Full SEO Audit/`; the other twelve checks stay procedural. `tests/test_wiring.py` pins the remaining cross-file contracts: documented paths exist, the CLAUDE.md check count matches the QA skill, and every `Skills/` folder is registered or named in CLAUDE.md or a command.
**Reasoning.** The review first read the registered copies as stale and proposed mirroring the library into them. Rejected after finding that `ai-search-optimization` was already an owner-written pointer from 2026-08-21, whose stated purpose was to stop the two copies drifting; extending that pattern to the other six leaves one source of truth and keeps description-based triggering, where mirrored full copies would drift again. The hook gates only `Full SEO Audit/` because that is the QA skill's own trigger, and it fails open on its own errors (exit 1) so a hook bug cannot block work, while a real check failure or a missing leak index blocks (exit 2). Rejected a hook over all `Clients/` paths: `data/` holds raw exports whose dashes are not deliverable text. Hooks cannot see workbooks written by Bash scripts before the write, so `.xlsx` files are scanned right after, as feedback, not as a block.
**Context.** Came out of `/workflow-review`; the engine reported 0/10 because it expects `agents/` and `commands/` at the project root, and 27 raw findings failed hand verification. Real findings fixed: pointers and drift test, the hook, CLAUDE.md pointers for `monthly-seo-workbook` and `competitor-identification`, a "project" cue on five colliding descriptions, and the Projects-level CLAUDE.md trimmed of eight sections that duplicate `~/.claude/CLAUDE.md` (backup beside it). The hook loads from the next session. Monthly workbook output to Google Sheets is not covered by the hook.

## 2026-10-06 — Two leak-grounded checks built: location pages over four addresses or phones, and priority pages with no click-sourced internal links

**Decision.** `LocalSEOAuditor` gained `_check_stored_local_data_limit` (flags indexable location pages listing more than four distinct addresses or phone numbers) and a new `InternalProminenceAuditor` (flags indexable pages at average position 4 to 20 with impressions that no page earning 10 or more Search Console clicks links to, listing the top click-earning pages not yet linking to each). Both say "not checked" or "not run" when their inputs are missing, and neither reports a clean pass it could not compute. Findings label what the leaked docs state as Documented and what is a reading of them as Inferred.
**Reasoning.** The address and phone text comes from a body-text crawl column when one exists, otherwise a fetch of only the location pages, through a new raw-text path (`utils/location_page_text.py`) instead of the semantic map's `load_page_text`. Rejected reusing `load_page_text`: it strips lines repeated across pages as site chrome, which removes a shared footer full of addresses, exactly what this check must count. Rejected counting only crawl columns and JSON-LD: a real crawl (Snow) has no text columns, so the check would do nothing. Thresholds (4 per the documented limit; 10 clicks; positions 4 to 20, the quick-win window) are named constants, the last two being judgment calls. Navigation and footer links are excluded when the anchor export carries link positions, because template links reach every page. A priority page the anchor export never mentions, while the crawl counts inlinks to it, is reported as unverifiable, not as unlinked.
**Context.** A live-page check found the extractor missed `8141 2nd St Suite #545, Downey, CA` until the suite pattern accepted a `#`; fixed and pinned by a test. Check 2 has not been run against real anchor and Search Console exports, since none is saved locally; check 1's extractor was verified on one live page only. Not built, by decision: domain flags (exact-match domain, host age). Parked by the owner: measuring `contentEffort`. `app.py` also had a wrong module name in an analysis label (`QualityAuthorityTopicEmbeddings`), corrected.

## 2026-10-06 — 1.5 candidate gate looks back six workbook months; Bart's October 1.5 filled and verified

**Decision.** The 1.5 candidate gate and `check_1_5_repeats.py` use a six-month window (`url_cooldown.CANDIDATE_LOOKBACK_MONTHS = 6`). The shared `COOLDOWN_MONTHS = 3` is unchanged and still governs 2.3, 1.7 and 1.8. `/blog/how-much-does-asphalt-paving-cost` is excluded for Bart's through `crawl.candidate_exclude`. `scripts/verify_1_5.py` re-derives every figure on the tab from page-filtered requests and is a required gate in `tasks/1.5.md`.
**Reasoning.** The owner said, mid-run, that 1.5 candidates must not have been worked in the last six months of any workbook month. Chose a separate constant over changing `COOLDOWN_MONTHS` because the 2026-10-05 entry confirms three months and that constant moves four gates at once; the owner's instruction named the 1.5 check. Open question for the owner: whether the shared window should also be six. The excluded page is named in September's plan as one of two cost posts tied to the Ann Arbor paving work and its sitemap lastmod is 2026-09-15, but no workbook row lists it, so the structured gate could not see it. Rejected widening the gate to every URL mentioned in a prior row's text without asking: it would block reference mentions as well as work. Still open: whether it should.
**Context.** Defects fixed on the way, each pinned in `tests/test_workbook_1_5.py`: `all_pages()` overwrote slashed and unslashed rows instead of summing them (hid a page's real traffic and distorted the control figures); `page_queries()` matched only the URL as recorded, so pages recorded unslashed lost data; Section A notes quoted last month's whole target cell and said "no impressions at all" for pages that only lacked a target query; brand queries could become a page's tracked target; the first-month baseline note hardcoded "May-Jul" and "July". `run_1_5.py` now accepts per-row `action`, `note` and `intent` judgments in NOTES and writes no baseline note after a client's first month. Section A gains a `CLIENT CTR CURVE` row from the second month, which is a layout addition the owner has not seen. The tab holds four candidates against a "6-10" header: the pool is small after gates and thresholds, not padded.

## 2026-10-06 — 1.5 gate follows redirects, drops brand targets, and counts #anchor rows; the other seven clients' October 1.5 filled and verified

**Decision.** The 1.5 work-history gate, `check_1_5_repeats.py` and Section A resolve every recorded URL to the address that serves it now and stop the task if one cannot be read. Branded queries are never a Section B target. `candidate_exclude` accepts an exact address (trailing `$`). Page filters include `#anchor` rows. October 1.5 is written and verified (0 mismatches) for Bart's, Superior, SameDay, Beehive, Comfort, Cudio and Education Walkthrough; Arsenal and Snow have no October workbook because the owner put them on hold.
**Reasoning.** Chose resolving redirects at the gate over hand-listing moved URLs because SameDay moved its whole tree and a string comparison offered two September pages back as new. Chose a stop over a skip for unreadable URLs because a gate that silently stops working is the failure the 2026-09-03 rule names. Rejected excluding brand queries only in Section A, which was the earlier state, because EW offered three marketing pages for 'education walkthrough login'.
**Context.** Section A for SameDay now counts a moved page's old and new address together and prints the new one. The verifier had two defects of its own (a trailing slash on recorded URLs, and only one decay rationale shape), both fixed and pinned in `tests/test_workbook_1_5.py`. Per-row judgments live in `NOTES` in `scripts/run_1_5.py`; exclusions and their reasons live in `clients/registry.yaml`.

## 2026-10-06 — 1.5 reads every tab that names pages; cells are composed, not joined; retired task numbers never reach a sheet

**Decision.** The 1.5 gate and repeat check read every cell that is a page or a list of pages on the 1.3, 1.5, 1.8, 2.1, 2.2, 2.3 (and old 2.4, 2.5), 3.1 and 4.1 tabs of the last six workbooks (`scripts/worked_urls.py`). Prose that merely mentions a URL does not count. Notes and rationales are built with `sheets_io.compose()` (label plus bullets), `write()` warns on a paragraph and `verify_1_5.py` fails on one. Every page worked last month is labelled 2.3.
**Reasoning.** Chose all-tabs over the three tabs the earlier gate read because the owner's rule is "not taken into account in any of the last six months", and a page that only had a fix or new links was invisible. Rejected counting every URL typed in any cell: it removed `/service-areas/lehi-ut` from SameDay for being named in a redirect note. Rejected a reminder in the recipe for the format: it was already there and did not hold. The old 2.3, 2.4 and 3.1 labels were read from prior workbooks; the template (ClickUp, Bart's October milestone) merges all page work into 2.3 and makes 3.1 Internal Links.
**Context.** Also added: a 12-hour on-disk cache of where URLs land (`.cache/`), one slower retry pass before the gate gives up on a throttled URL, and unmerging stale merged rows under Section A (EW's fill failed on one). The 1.5 template asks for 6 to 10 candidates; SameDay, Comfort and Cudio have 1 because the gate removed the rest, and the owner has not yet ruled on padding them.

## 2026-10-07 — 1.6 reads the LLM tracker instead of running its own Bright Data prompt set

**Decision.** `scripts/fill_1_6_tracker.py` builds the 1.6 tab from the tracker's stored results (ChatGPT and Google AI Mode in SOV, Gemini as a note, no Perplexity, AI Overview excluded), from the tracker's approved non-branded prompts, using the latest week holding at least 70% of the prior week's samples. October 2026 is a baseline. `monthly_1_6.py` and the Bright Data flow are retired for this task.
**Reasoning.** Chose the tracker over the fixed 27 to 33 prompt Bright Data set because the owner judged the tracker's prompts better, because it runs on DataForSEO alone with five samples per prompt, and because every duplicate vendor call was spend on data that already exists. The same session lost an hour to a Bright Data Google AI Mode snapshot that stalled and a Perplexity run that came back 33 of 33 blocked. Rejected reading the tracker only for a section D beside the old SOV: two instruments for one figure.
**Context.** The tracker holds none of the old fixed prompts, so September cannot be compared; November is the first delta. The tracker is mid-migration to a new Supabase project (`TRACKER_DB=new` switches the reader). Bugs found in the tracker while reading it were handed to the owner, not fixed here. Departs from the ClickUp 1.6 text on prompt count and engines, with the owner's approval.

## 2026-11-10 — Click-signal auditor judges CTR against the site's own curve

**Decision.** `auditors/click_signal_auditor.py` builds a CTR baseline from the client's own GSC export in two-position bands, using a band only with 400+ impressions across 3+ pages; thinner bands fall back to the generic intent tables.
**Reasoning.** Rejected: keeping the fixed AWR/SISTRIX/FirstPageSage tables. Task 1.5 measured one client at about a third of typical CTR, so the fixed table flagged average pages as snippet failures. The research run of 2026-11-10 (CTR varies with SERP layout and site authority) points the same way. The 3-page minimum stops one page from setting its own baseline.
**Context.** Same day: reference edits from that research run (algorithm timeline, "Crawled - currently not indexed" routing, loss-shape table, Phase 0 pre-checks). Tests: `tests/auditors/test_click_signal_auditor.py`, 7 pass.
