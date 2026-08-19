# Monthly SEO Task Template — Blueprint Capture

**Status:** `CAPTURE COMPLETE` — **32 tasks: 25 monthly (Weeks 1–5) + 7 quarterly (Q1–Q7).** Counts excluded the 5 week containers and the standing `MASTER — Repeated Tasks` parent, which was never supplied. Analysis passes run 2026-08-10; structural review published.

> **Count correction (2026-08-10):** an earlier draft of this file said 21 monthly tasks and the published review said 32 total as "28". Both were arithmetic errors on my part, caught by Roger. Correct figures: 8 + 5 + 4 + 5 + 3 = **25 monthly**, plus **7 quarterly** = **32**.
**Source:** Boss-authored ClickUp master template (monthly recurring milestone, deployed per client).
**Capture started:** 2026-08-10
**Purpose of this file:** hold the full template verbatim so per-task feedback can be given with the dependency graph in hand, instead of flagging gaps that a sibling task already covers.

**Capture rule:** descriptions are recorded as delivered, including anything that looks wrong. Template defects are findings. Do not tidy on the way in.

---

## Master Template Description

> This is the master template. Do not work tasks here — deploy a copy into the client's SEO list each month.

### How to deploy (monthly, per client — done in 5.3 of the prior month)

1. Duplicate this milestone (or use it via Template Center once saved as a task template) into the client's SEO list. Rename to `[Month] [Year] SEO Tasks`.
2. Set due dates: Week 1 container → end of first full week; Weeks 2–5 → each following Friday; milestone due date → last business day of the month.
3. Every 3rd month for the client: also duplicate the Quarterly Block container into the deployed milestone (its tasks slot into Weeks 2–3 capacity).
4. Task 1.8 populates the target-page tasks (2.3, 2.4, 3.1) with URLs, keywords, and refresh angles — they deploy as shells by design.
5. The standing `MASTER — Repeated Tasks` parent is separate and built once per client (not monthly).

### Workflow rules (every task)

- **Default owner: Roger.** Roger executes or reassigns implementation to Samuel (dev) or Rahman (VA) at his discretion. Rahman directly owns 1.3, 1.7, 2.2, 4.4, Q4, Q7.
- Every task ends at **"Ready for Janelle's Review"** — or **"Deliver to Client"** when the output is client-facing and ready to send. Janelle owns all client delivery and closes tasks. Questions go to Janelle first; loop Nathan in only when needed.
- Every task posts its deliverable in the task (comment or linked doc). Downstream tasks consume these outputs — **a task with no logged output is not done.**
- **Keyword tracking rule:** any task optimizing a page for a keyword includes adding that keyword to SEMrush Position Tracking, tagged with the month (e.g. `aug-2026`). Roger owns this step even when the task is delegated.
- Dependencies enforce the order — if your task is blocked, the blocking task's deliverable is what you're waiting for.

### Why this order (stated design intent)

> Week 1 produces data and a decision — nothing is optimized on habit. Weeks 2–3 execute in leverage order (blockers → page refreshes → links/entity/mentions). Week 4 ships, QAs, and compiles proof of work. Month-end reports, meets, and decides — the month cannot close without selecting next month's targets.

### Role map

| Person | Role |
| --- | --- |
| Roger | Default owner / executor, routes work |
| Samuel | Dev implementation |
| Rahman | VA — direct owner of 1.3, 1.7, 2.2, 4.4, Q4, Q7 |
| Janelle | Review gate + all client delivery, closes tasks |
| Nathan | Escalation only |

---

## Week 1 — Diagnose & Plan

### 1.1 Pull Monthly Data Snapshot (GSC, GA4, AI Traffic)

**Owner:** Roger (per default rule; not on Rahman's list)

**Objective:** One dated, source-of-truth snapshot that every Week 1 task and the monthly report work from. Without this, every later task pulls its own numbers and they won't match.

**Steps — refresh/export the client dashboard with:**

- GSC clicks + impressions: last 30d vs prior 30d, and YoY where clean. ⚠️ Impressions May 2025–Apr 2026 are inflated by a confirmed Google logging bug — use clicks for any comparison touching that window.
- GA4 organic conversions/leads (and revenue if e-comm).
- GA4 `ai-assistant` channel sessions + conversions.
- GSC Generative AI impressions report.
- Branded-query impressions trend.
- SEMrush Position Tracking snapshot — filter by last month's tag to see how last month's worked keywords moved.

**Deliverable:** Snapshot link + a comment flagging anomalies (spikes, drops, tracking gaps) in plain language.

**Feeds (per description):** 1.5 (decay baseline) · 1.8 (plan decision) · 4.2 (top landing pages list) · 5.1 (report numbers)

**Blocks (per ClickUp dependency):** 1.5 · 1.8 · 4.2

**Done when:** Snapshot posted and anomalies flagged → set Ready for Janelle's Review.

> ⚑ **Logged discrepancy (not yet analyzed):** description names **5.1** as a consumer, but the ClickUp blocking list is 1.5 / 1.8 / 4.2 only. Either 5.1's dependency isn't wired in the tool, or the Feeds line is aspirational. Verify with Roger before the analysis pass.

---

### 1.2 Run Technical Health Sweep in GSC (Indexing, Crawl, CWV)

**Objective:** Catch indexing loss, crawl damage, and Core Web Vitals regressions before they compound. Google actively prunes its index now — pages silently drop out, and this sweep is how we notice within 30 days instead of 6 months.

**Steps:**

- GSC Page Indexing vs last month: flag growth in "Crawled – currently not indexed"; check whether affected URLs were previously indexed (= deindexed = quality/consolidation problem, not technical — route to 1.8, not 2.1).
- GSC Crawl Stats: error spikes.
- Screaming Frog list-mode crawl of money pages + recent posts: broken links, redirect chains, accidental noindex/canonical issues.
- Sitemap URL count vs indexed count.
- CWV field data (PSI/CrUX) on top 3 templates vs last month — flag real failures only, not score-chasing.

**Deliverable:** Findings comment: each issue with URL(s), severity (Blocker / Fix this month / Watch), and routing — technical fixes → 2.1; quality/deindexing patterns → 1.8. A stated "no issues" is a valid outcome.

**Feeds (per description):** 2.1 (its fix list is this comment) · 1.8 (quality issues inform target selection)

**Blocks (per ClickUp dependency):** 2.1

**Done when:** Findings posted → set Ready for Janelle's Review.

> ⚑ **Logged (not yet analyzed):** same Feeds-vs-Blocks pattern as 1.1. Description names 1.8 as a consumer; only 2.1 is wired as a blocking dependency. See open flag #2.

---

### 1.3 Run SEMrush Site Health Audit & Build Fix Sheet

**Owner:** Rahman. Roger reviews/approves the fix sheet; Rahman implements the approved sheet in 2.2.

**Objective:** Automated second net alongside 1.2 — catches template-level issues across the whole site that the targeted GSC sweep won't. The deliverable is a fix sheet, never a raw export — audit exports shipped as deliverables are the #1 filler complaint clients have about SEO retainers.

**Steps:**

- Run/refresh the SEMrush Site Audit for this client.
- Record the Site Health score in the tracker (the trend matters more than the number).
- If score < 92% — or any new Errors appeared regardless of score — build the fix sheet in Google Sheets: one row per issue with issue type, affected URLs, exactly what to change (the specific redirect target, the specific tag to remove), and proposed owner (Rahman / Samuel). Prioritize Errors; include Warnings only when meaningful; ignore Notices — chasing a 100 score is documented busywork.
- Post the sheet for Roger's review; Roger approves/edits line-items in comments. Approval here is what unlocks 2.2.

**Deliverable:** Health score logged + Roger-approved fix sheet (or "score ≥92%, no new errors" stated).

**Feeds (per description):** 2.2 (Rahman implements the approved sheet there) · 5.1 (resolved-issues count for the report)

**Blocks (per ClickUp dependency):** 2.2

**Done when:** Score logged, sheet approved by Roger or clean bill stated → set Ready for Janelle's Review.

---

### 1.4 Verify AI Crawler Access & Raw HTML Rendering

**Objective:** Confirm AI engines can fetch and read the site. AI crawlers do not execute JavaScript, and Cloudflare-type CDNs now block AI bots by default — a client can silently vanish from ChatGPT/Perplexity/AI Overviews while Google looks fine.

**Steps:**

- robots.txt: OAI-SearchBot, Claude-SearchBot, PerplexityBot and user-triggered fetchers must be allowed. (GPTBot/CCBot training access is a client business decision — flag it, don't change it.)
- If the client is on Cloudflare/WAF: check AI-crawler/bot-management settings for default blocks.
- View raw HTML (JS disabled) on homepage + 2 money pages: primary content, headings, and internal links must be present without JS.
- If server logs/CDN analytics are available: confirm AI bots are actually hitting the site.

**Deliverable:** Pass/fail table — bot access, CDN status, per-page rendering — with fix items routed to 2.1.

**Feeds (per description):** 2.1 (fix list) · 1.6 (explains zero-visibility results if access is blocked)

**Blocks (per ClickUp dependency):** 2.1

**Done when:** Table posted → set Ready for Janelle's Review.

---

### 1.5 Build Decay & Striking-Distance Candidate List

**Objective:** Produce the ranked candidate list for this month's page optimizations. This is the engine of the whole retainer — refreshing declining and almost-ranking pages is the highest-documented-ROI recurring motion in SEO (controlled studies: ~+450% sessions on refreshed pages while untouched pages decline ~20%).

**Steps — in GSC, last 90d vs prior 90d:**

- Decay: formerly-performing pages with clicks down >20%.
- Striking distance: queries at positions 4–15 with real impressions, mapped to their pages.
- CTR anomalies: stable impressions, falling CTR (title/meta problem).
- Measure our own work: pull last month's worked keywords from SEMrush Position Tracking (last month's tag) and log their before/after.

Score candidates: business value (money page > blog) × trend × effort.

**Deliverable:** Ranked list of 6–10 candidate pages with a one-line rationale each (e.g., "striking distance pos. 6 for [query], 2.4k imp/mo") + before/after results of last month's optimizations.

**Feeds (per description):** 1.7 (gap analysis runs on these candidates + last month's keywords) · 1.8 (selection) · 5.1 (last month's results are report material)

**Blocks (per ClickUp dependency):** 1.7 · 1.8

**Blocked by (per ClickUp dependency):** 1.1

**Done when:** Ranked list + last-month results posted → set Ready for Janelle's Review.

> ⚑ **Logged (not yet analyzed):** two things to resolve at verdict time.
>
> 1. **Window mismatch with its own blocker.** 1.5 works "in GSC, last 90d vs prior 90d." 1.1 produces a 30d vs prior-30d snapshot. So 1.5 cannot source its core analysis from 1.1's deliverable and appears to pull GSC directly. Question for Roger: is 1.1 a real data input to 1.5, or is the dependency just sequencing? If the latter, the graph is claiming a handoff that doesn't happen.
> 2. **Duplicated SEMrush pull.** See the duplicate-coverage section below.

---

### 1.6 Run AI Visibility Prompt Set & Log Share of Voice

**Owner:** Roger (Rahman handoff candidate).

**Objective:** Measure where the client shows up — and doesn't — in AI answers, using the same fixed prompt set every month. This is polling, not rank tracking: single runs are noisy; the month-over-month trend on a consistent prompt set is the signal.

**Steps:**

- Run the client's standing prompt set (15–25 prompts: discovery / comparison / "best X" / decision intent — set up once, changed only in Q3) across ChatGPT, Claude, Google AI Overviews/AI Mode, and Perplexity.
- For each prompt, log in the SOV tracker: brand mentioned Y/N · prominence (1st/2nd/3rd+ mention) · competitors named · URLs cited (client's and third-party).

**Deliverable:** Updated SOV tracker + a comment covering: (a) SOV % vs last month, (b) money prompts where competitors appear and we don't, (c) the specific third-party pages (listicles, review sites, forums) AI cites where the client is absent.

**Feeds (per description):** 1.8 (gaps inform target selection) · 3.4 (item c IS its target list) · 5.1 (SOV trend for report)

**Blocks (per ClickUp dependency):** 1.8 · 3.4

**Blocked by (per ClickUp dependency):** *none*

**Done when:** Tracker updated, comment posted → set Ready for Janelle's Review.

> ⚑ **CONFIRMED GAP.** 1.6 has no blockers wired at all, so it can start before 1.4. 1.4's Feeds line explicitly names 1.6 as a consumer ("explains zero-visibility results if access is blocked"), but nothing enforces that order. This is no longer inference — the dependency data confirms it. See open flag #3.

---

### 1.7 Run Competitor Keyword Gap & Backlink Gap Analysis (Active Keywords)

**Owner:** Roger. Roger consumes the output in 1.8. (can be assigned to Rahman if clear instructions are provided).

> ⚑ **Ownership conflict.** The master workflow rules state "Rahman directly owns 1.3, 1.7, 2.2, 4.4, Q4, Q7." This task's own description says Roger owns it and Rahman is conditional. 1.3 checks out (says "Owner: Rahman", matching the master), so 1.7 is the outlier. One of the two is wrong. See open flag #5.

**Objective:** Know exactly who we're fighting and with what — scoped to the keywords in play, not the whole market. Two outputs: (a) keyword gaps that sharpen this month's refresh angles, (b) a backlink gap list that becomes the handoff to the backlinks team (link building itself is outside this template; this intel is what makes it targeted).

**Scope:** last month's worked keywords (from 1.5's before/after) + this month's top candidates (1.5's ranked list) + keywords within content calendar.

**Steps:**

- **Keyword gap** — SEMrush Keyword Gap: client vs the 2–3 competitors actually ranking for these terms. Log keywords in this topic space where competitors rank top 10 and we don't (or trail), with volume + intent. Flag which of our candidate pages could absorb each gap — expansion angles for existing pages, not new-page proposals.
- **Backlink gap** — SEMrush Backlink Gap on the specific competitor URLs outranking us for the active keywords: which referring domains do their ranking pages have that ours don't? Log realistic, quality targets only (relevant sites, real traffic — skip spam/unattainable).
- Note any new competitor that entered the top 10 on our keywords since last month.

**Deliverable:** One sheet, two tabs — Keyword Gaps (keyword, volume, competitor, our best page, expansion angle) and Backlink Gaps (target domain, competitor page it links to, our equivalent page).

**Feeds (per description):** 1.8 (keyword gaps → refresh angles) · **backlinks team** (Janelle routes the Backlink Gaps tab into the link-building workflow) · 5.1 (competitive movement note)

**Blocks (per ClickUp dependency):** 1.8

**Blocked by (per ClickUp dependency):** 1.5

**Done when:** Sheet posted, backlink tab routed → set Ready for Janelle's Review.

> ⚑ **First external edge.** The Backlink Gaps tab leaves the template entirely and enters the link-building workflow, with no return path. Nothing downstream consumes it, nothing verifies it was received, and no task asks whether last month's routed targets were ever worked. Every other Feeds edge in this template terminates in a task that can be checked. See open flag #6.

---

### 1.8 Lock Monthly Plan & Populate Weeks 2–4

**Objective:** Convert Week 1's data into the month's committed work. This task is why the template never goes stale: the skeleton is fixed, but the targets are chosen fresh from data every month.

**Steps:**

- Review the deliverables of 1.1–1.7.
- Select 3–5 target pages from the 1.5 list, cross-referenced with 1.6 AI-visibility gaps and 1.7 keyword gaps. A page that fixes a ranking gap, an AI-visibility gap, AND absorbs a competitor keyword gap outranks any single-purpose target.
- Cross-check the client's content calendar (Content list) before locking targets:
  - If a candidate page is already scheduled for content work this month → skip it or deliberately sequence it (content ships first, SEO layer next month). **One team touches a page per month.**
  - **Scope rule:** a refresh here is optimization-scope — structure, outdated-info fixes, titles/metas, added data/quotes, internal links, schema — completable by Roger within the task's estimate. If a candidate needs substantial new copy or a full rewrite → it's a content-calendar item: route it to the client's Content list (Rewrite/Optimization) through the normal content process. It does not take a refresh slot here.
- For each target, edit the matching Week 2/3 task (2.3, 2.4, 3.1): paste in the URL, target queries/prompts, current baseline, and the refresh angle in one sentence (e.g., "outdated pricing, no direct answer paragraph, competitor X winning [gap keyword], losing AIO citation to [competitor]").
- Confirm the 1.2 / 1.4 fix items are captured in 2.1, and that the 1.3 fix sheet is approved so 2.2 can start.
- Note anything client-approval-dependent for Janelle.

**Deliverable:** Weeks 2–4 tasks populated with named targets + a 3-bullet plan summary posted here (Janelle uses it for the client's Monday update) + any pages routed to the content calendar noted.

**Feeds (per description):** Every execution task in Weeks 2–3 · **content calendar** (routed pages) · client comms via Janelle

**Blocks (per ClickUp dependency):** 2.3 · 2.4 · 2.5 · 3.1

**Blocked by (per ClickUp dependency):** 1.1 · 1.5 · 1.6 · 1.7

**Done when:** Targets populated, summary posted → set Ready for Janelle's Review (Janelle relays the plan in the weekly update).

> ⚑ **CONFIRMED ENFORCEMENT GAP — and this is the keystone task, so it matters more than the 1.4 → 1.6 one.**
>
> The **first step** says "review the deliverables of **1.1–1.7**." The **second-to-last step** says "confirm the **1.2 / 1.4** fix items are captured in 2.1, and that the **1.3** fix sheet is approved so 2.2 can start." So the task text explicitly requires 1.2, 1.3 and 1.4 to be done. The wiring gates it on only 1.1, 1.5, 1.6, 1.7.
>
> Consequence: 1.8 can be marked done while 1.2, 1.3 and 1.4 are still open, and that confirm step silently becomes a no-op. Nothing in the tool prevents it and nothing downstream catches it.
>
> ⚑ **Citation correction 2026-08-10 (caught by Roger):** an earlier version of this note cited the confirm step as "step 6." It is **step 5** counting the two content-calendar sub-bullets as part of step 3, which is how the task reads. Step 6 is "note anything client-approval-dependent for Janelle." The finding is unaffected (the step exists verbatim and the blocker list is 1.1/1.5/1.6/1.7), but the citation was wrong. **Cite steps by their opening words, not by number, in any numbered list that contains sub-bullets.**
>
> Note this also fully explains open flag #2's outlier: 1.2 → 1.8 is unwired, and so are 1.3 → 1.8 and 1.4 → 1.8 by implication. The pattern is not "soft edges go unwired," it is "the three technical-diagnostic tasks are missing from the keystone's blocker set."

**Two smaller flags on the same task:**

> ⚑ **Feeds line overstates its own wiring.** "Every execution task in Weeks 2–3" vs four wired blocks (2.3, 2.4, 2.5, 3.1). 2.1, 2.2 and 3.4 are execution tasks in Weeks 2–3 that 1.8 does not block. Defensible, since those are fed by 1.2/1.3/1.6 instead, but the sentence as written is wrong and someone reading it will expect a gate that isn't there.
>
> ⚑ **Second external edge:** content calendar (routed pages). Same shape as 1.7's backlinks handoff. See open flag #6.

**Strong design worth keeping:** the "one team touches a page per month" collision rule and the optimization-scope-vs-rewrite boundary are both well drawn. They are the two things that stop this task quietly turning into a content-production queue.

---

## Week 2 — Execute I: Fixes & First Refreshes

### 2.1 Implement Technical Fixes From Week 1

> ✅ **CLOSED — the "1.4" mismatch was a paste slip.** This description was originally pasted under the 1.4 heading. Re-supplied under 2.1 on 2026-08-10, verbatim identical, with dependencies confirming blocked-by 1.2 and 1.4. No template defect.

**Owner:** Roger — routes dev work to Samuel as needed. (Rahman's approved site-health fix sheet is implemented separately in 2.2.)

**Objective:** Clear the technical issues found in 1.2 and 1.4 while they're fresh. Priority order matters: indexation blockers cost the most per day they exist.

**Steps — work the fix list top-down:**

1. Indexation blockers — accidental noindex, canonical conflicts, robots/CDN blocks (including AI-bot blocks from 1.4).
2. Broken links & redirect chains.
3. Genuine CWV failures — heavy third-party scripts, oversized media.

For anything not completable this month, comment scope + blocker so it lands in next month's 1.8.

**Deliverable:** One-line log per fix — what, where, verified-how (re-crawled URL, indexing requested where warranted).

**Feeds (per description):** 4.1 (QA re-verifies) · 4.5 (activity log) · 5.1 (report)

**Blocks (per ClickUp dependency):** 4.1

**Blocked by (per ClickUp dependency):** 1.2 · 1.4

**Done when:** All fixes deployed + verified, log posted → set Ready for Janelle's Review.

> ⚑ **Minor, same class as the others:** 2.1 feeds 4.5 (activity log) but doesn't block it, so the proof-of-work compile can run before this month's fixes are logged. Lower stakes than the 1.8 hole — the failure mode is an incomplete activity log, not a wrong diagnosis. Watch whether anything blocks 4.5 when it arrives.

---

### 2.2 Implement Approved Site Health Fix Sheet

**Owner:** Rahman. Executes only what Roger approved in 1.3 — if a fix isn't on the approved sheet, it doesn't get made here. *(Ownership consistent with master rule — checks out.)*

**Objective:** Close out the site-health issues Rahman surfaced in 1.3, with a clean audit trail from finding → approval → implementation. (Roger/Samuel handle the GSC + AI-access fixes separately in 2.1.)

**Steps:**

- Work the approved fix sheet top-down, one row at a time — make exactly the change specified (the exact redirect target, the exact tag change).
- Mark each row done with the date and a link/note showing the fix live.
- Anything that turns out to need dev access or is bigger than specified: don't improvise — flag the row for Roger to route to Samuel or next month's plan.
- When the sheet is complete, re-run the SEMrush Site Audit and log the new Site Health score next to the 1.3 baseline.

**Deliverable:** Completed fix sheet (every row dated done or flagged) + before/after Site Health score.

**Feeds (per description):** 4.1 (QA re-verifies changed pages) · 4.5 (activity log — "issues resolved" is client-visible proof of work) · 5.1 (report) · **next month's 1.3** (score should hold ≥92%)

**Blocks (per ClickUp dependency):** 4.1

**Blocked by (per ClickUp dependency):** 1.3

**Done when:** All approved rows implemented or flagged, re-audit score logged → set Ready for Janelle's Review.

> ✅ **First cross-month edge, and it's carried correctly.** 2.2 → next month's 1.3 is not a wired dependency and doesn't need to be. The SEMrush tracker is a shared artifact that carries state across months, and 1.3's threshold logic (score < 92% or new Errors) reads it. This is the right way to do continuity.
>
> ⚑ **But the tracker now holds two scores per month** — 1.3's baseline and 2.2's post-fix re-audit — and nothing states which one next month's 1.3 compares against. Comparing next month's baseline to this month's post-fix score measures decay; comparing it to this month's baseline measures net progress. Both are legitimate, they answer different questions, and picking the wrong one silently inverts the trend. Label the two score types in the tracker and say which one drives the <92% trigger.

### 2.3 Optimize Target Page #1 — [URL filled by 1.8]

**Objective:** Full refresh of the month's highest-value target (named by 1.8). Targeted improvement, not a rewrite — the data shows structural cleanup + outdated-info removal + added original value beats rewriting or padding length.

**Target (filled by 1.8):** URL · Target queries/prompts · Baseline (clicks / impressions / avg position / AI citations) · Refresh angle

**Steps — the Refresh SOP:**

- **Baseline** — log current clicks, impressions, avg position, AI citations (from 1.6) above. No baseline = we can't prove the win.
- **Intent check** — review the current top 3 results for the target query: what do they cover that we don't? What do we know that they can't say? Use the 1.7 keyword-gap tab for expansion angles.
- **Cut the rot** — remove/update outdated facts, dates, prices, screenshots, dead examples.
- **Answer-first restructure** — direct 40–60-word answer under the lead heading; H2s phrased as the real sub-questions; comparison table where the content is tabular; key facts in the first third of the page.
- **Add information gain** — at least one thing no competitor has: first-hand detail, original data point, expert quote, real project example. This is what earns both rankings and AI citations.
- **Title + meta** — ≤60 chars, matches dominant intent and real prompt phrasing; check whether Google is currently rewriting our title.
- **Schema** — validate/update the page's markup (supported types only).
- **Outbound internal links** — update this page's links + anchors to current targets.
- **Track it (Roger)** — add this page's target keyword(s) to SEMrush Position Tracking, tagged with the month (e.g., `aug-2026`). Roger owns this step even when the refresh is delegated — untracked work is unmeasurable work.

**Scope boundary:** this task is optimization-scope only. If mid-refresh the page turns out to need substantial new copy or a full rewrite — stop, comment the recommendation, and Roger routes it to the client's content calendar (Content list) through the normal content process. Do not pull the content team into this task, and don't force a shallow refresh on a page that needs real content work.

**Deliverable:** Before/after summary comment: baseline numbers, what changed (one line per step), live URL or staged link, keywords confirmed in Position Tracking.

**Feeds (per description):** 3.2 (links INTO this page) · 4.1 (QA) · 4.3 (cannibalization check) · **next month's 1.1/1.5** (Position Tracking tag = measurement)

**Blocks (per ClickUp dependency):** 3.2 · 4.1 · 4.3

**Blocked by (per ClickUp dependency):** 1.8

**Done when:** Changes live or staged per client workflow, summary posted, keywords tracked → set Ready for Janelle's Review (→ Deliver to Client if client approval is required before publish).

> ✅ **First task whose Feeds and Blocks match exactly.** Every declared consumer is wired, and the only unwired edge is the cross-month one, which is correctly carried by the Position Tracking month tag rather than a dependency. This is the shape the rest of the template should be measured against.
>
> ⚑ **The flagship work doesn't declare a route to the report or the activity log.** 2.1 and 2.2 both feed 4.5 and 5.1. 2.3 feeds neither, despite producing a before/after summary that is the single most report-worthy artifact the month generates. Either the convention is inconsistent, or 5.1 is expected to go hunting for it. Same check needed on 2.4, 2.5 and 3.1.
>
> ⚑ **"Title + meta — ≤60 chars" conflicts with the house title-tag standard.** The team's documented rule is a **65-character budget for the page-specific portion, with the brand suffix excluded from the count**, on the reasoning that Google preserves the brand suffix in the SERP and counting it starves the page-specific information. This step says ≤60 and is silent on the brand suffix, so a writer following it will either under-use the budget or count the suffix and starve the title. Two monthly refreshes a month across every client is enough volume for the two standards to visibly diverge. Align the number and state the brand-suffix handling explicitly. The house rule also carries a no-repeated-token check (no word, root, or city twice, brand suffix included) that this step doesn't mention.

---

### 2.4 Optimize Target Page #2 — [URL filled by 1.8]

Same Refresh SOP as 2.3 (all 9 steps, including step 9 keyword tracking — Roger-owned), for the second 1.8 target.

**Target (filled by 1.8):** URL · Target queries/prompts · Baseline (clicks / impressions / avg position / AI citations) · Refresh angle

**Deliverable:** Before/after summary comment: baseline numbers, what changed per step, live/staged link, keywords confirmed in Position Tracking.

**Feeds (per description):** 3.2 · 4.1 · 4.3 · next month's 1.1/1.5

**Blocks (per ClickUp dependency):** 3.2 · 4.1 · 4.3

**Blocked by (per ClickUp dependency):** 1.8

**Done when:** Changes live or staged, summary posted, keywords tracked → set Ready for Janelle's Review (→ Deliver to Client if client approval required).

> ✅ **Referencing 2.3's SOP instead of restating it is the right call** — one place to update, no drift between the two refresh tasks.
>
> ⚑ **Confirms the 2.3 pattern:** no 4.5 or 5.1 edge here either. Both refresh tasks route to QA, internal links and cannibalization, but neither declares a path to the activity log or the client report.
>
> ⚑ **Structural: the Refresh SOP has no canonical home.** It is the core methodology of the whole retainer, and it lives inside a task description that gets duplicated fresh every month. Anyone who improves it mid-month improves only that month's deployed copy; the master template never learns. Over a year that is the single highest-value document in the system with no version history and no accumulation. Candidate fix: lift the SOP into one linked doc that 2.3, 2.4 and 3.1 all point at, so improvements compound instead of being discarded at month end.

---

### 2.5 Rewrite Titles/Metas on Striking-Distance Quick Wins

**Owner:** Roger (Rahman handoff candidate).

**Objective:** Capture cheap CTR gains on up to 5 pages from the 1.5 list that don't warrant a full refresh. Title work is one of the highest-leverage 10-minute tasks in SEO — it wins a bigger share of a smaller click pool.

**Steps:**

- For each page (list confirmed in 1.8): log baseline position + CTR.
- Rewrite title — ≤60 chars, front-load the query language, match intent, no clickbait — and meta description.
- Publish.
- Then (Roger): confirm each page's target keyword is in SEMrush Position Tracking with this month's tag.

**Deliverable:** Before/after table — URL, old title, new title, baseline CTR/position — with keywords confirmed tracked.

**Feeds (per description):** 4.1 (QA) · **next month's 1.5** (CTR delta check on exactly these pages)

**Blocks (per ClickUp dependency):** 4.1

**Blocked by (per ClickUp dependency):** 1.8

**Done when:** All changes live, table posted, keywords tracked → set Ready for Janelle's Review.

> ⚑ **The pages most likely to cannibalize are the ones excluded from the cannibalization check.** 2.3 and 2.4 both block 4.3 (Spot-Check Query Cannibalization on This Month's Targets). 2.5 does not. But 2.5 retargets **up to 5 pages** by front-loading query language into their titles, which is precisely the intervention most likely to create or worsen query overlap — and all 5 come from the same 1.5 candidate pool as the refresh targets, so they are topically adjacent by construction. 4.3 will inspect the 3–5 refreshed pages and skip the 5 retargeted ones. Wire 2.5 → 4.3.
>
> ⚑ **Second instance of the ≤60-char title spec** (see 2.3). Now systemic rather than a one-off. Same conflict with the house 65-char / brand-suffix-excluded rule, and the no-repeated-token check is again absent — which matters more here, because rewriting 5 titles in one sitting toward the same topical cluster is exactly how repeated tokens and stacked synonyms creep in.
>
> ⚑ **Meta description has no length spec** while the title has one. Minor, but if the title is worth a character budget the meta is too, and "and meta description" tacked onto the end of the title step reads like an afterthought on the one element that most directly drives the CTR this task exists to win.
>
> ⚑ **No 4.5 / 5.1 edge**, consistent with 2.3 and 2.4. All three page-level tasks route to QA but not to the report or the activity log.
>
> ✅ **Cross-month measurement edge is well specified** — "next month's 1.5 (CTR delta check on exactly these pages)" names both the consumer and the metric, which is tighter than most Feeds lines in the template.

**Capacity note (not a defect):** 2.3 + 2.4 + 3.1 cover 3–5 target pages, and 2.5 adds up to 5 more. Up to 10 pages touched per client per month, all funnelling into 4.1 for QA.

## Week 3 — Execute II: Refreshes, Links, Entity & Mentions

### 3.1 Optimize Target Pages #3–5 — [URLs filled by 1.8]

Same Refresh SOP as 2.3 (all 9 steps, including step 9 keyword tracking — Roger-owned), for the remaining 1.8 targets. **Estimate is per page.**

**Targets (filled by 1.8):** URL(s) · Target queries/prompts · Baselines · Refresh angles

**If a target proves unviable mid-work:** stop — don't force it. Comment the recommendation and route it: intent shifted / should be merged → next month's 1.8 or the quarterly pruning round (**Q2**); needs substantial new copy or a full rewrite → the client's content calendar (Content list) through the normal content process. Same scope boundary as 2.3: optimization-scope only; the content team is never pulled into this task.

**Deliverable:** Before/after summary comment per page, keywords confirmed in Position Tracking.

**Feeds (per description):** 3.2 · 4.1 · 4.3 · next month's 1.1/1.5

**Blocks (per ClickUp dependency):** 3.2 · 4.1 · 4.3

**Blocked by (per ClickUp dependency):** 1.8

**Done when:** Changes live or staged, summaries posted, keywords tracked → set Ready for Janelle's Review (→ Deliver to Client if client approval required).

> ✅ **"Estimate is per page"** — small line, real effect. Stops three pages being scoped as one ticket.
>
> ⚑ **The SOP is drifting, and the improvement landed in the wrong task.** 3.1 carries a three-way escape hatch for an unviable target: intent shifted / should be merged → next month's 1.8 or the Q2 pruning round; needs a rewrite → content calendar. 2.3 — the canonical SOP that both 2.4 and 3.1 point at — only carries the rewrite route. So the richer routing logic exists only in the task that inherits the SOP, not in the SOP itself. A page that proves unviable during 2.3 or 2.4 has no documented "merge it" route.
>
> This is the "no canonical home" problem (see 2.4) already happening in the live template rather than hypothetically. Fix both at once: lift the SOP out, and fold 3.1's escape hatch into it.
>
> ⚑ **No 4.5 / 5.1 edge.** Fourth and final confirmation — all four page-level execution tasks (2.3, 2.4, 2.5, 3.1) route to QA and none declare a path to the activity log or the client report.

---

### 3.2 Add Internal Links Into This Month's Refreshed Pages

**Owner:** Roger (Rahman handoff candidate).

**Objective:** Concentrate authority into the pages we just improved, and into money pages. Internal linking is the most underused lever we fully control — a refresh without inbound links is half a refresh.

**Steps:**

- For each page refreshed this month (2.3, 2.4, 3.1): add 3–8 contextual links into it from topically relevant existing pages, with descriptive, varied anchors.
- Orphan check on recently published content (crawl vs sitemap) — link any orphans found.
- Verify money pages remain ≤3 clicks from the homepage.
- Fix internal links that pass through redirects on pages touched this month.

**Deliverable:** Link log — from-page → to-page → anchor, one row per link.

**Feeds (per description):** 4.1 (QA verifies links live) · 4.5 (activity log)

**Blocks (per ClickUp dependency):** 4.1

**Blocked by (per ClickUp dependency):** 2.3 · 2.4 · 3.1

**Done when:** Links live, log posted → set Ready for Janelle's Review.

> ⚑ **DANGLING INPUT — two of the four steps need a full site crawl that no task in the template produces.** Orphan detection (step 2) and click-depth verification (step 3) both require a spider crawl from the homepage plus a sitemap diff. The only crawl the template generates is 1.2's **list-mode** Screaming Frog run over money pages and recent posts, and list mode crawls only the URLs you hand it — by construction it cannot surface a page nothing links to, and it computes no depth from the homepage. So either these two steps get quietly skipped every month, or someone runs an unscoped full crawl that appears in nobody's estimate. Fix: add a full crawl to 1.2's steps and route it here, or move both checks to the Quarterly Block where a full crawl is affordable.
>
> ⚑ **Anchor guidance is thin for the volume this task generates.** 3–8 links into each of 3–5 refreshed pages is up to 40 new internal links a month per client, all pointing at a small target set, and "descriptive, varied" is the only constraint. At that volume the anchor distribution itself becomes a pattern. Given the team already enforces a no-repeated-token rule on titles, the same discipline belongs here: cap exact-match anchors across the link set, or state that no two links into the same target may share an anchor.
>
> ⚑ **4.5 unwired again.** Third task to feed the activity log without blocking it (2.1, 2.2, 3.2). Nothing blocks 4.5 so far.

### 3.3 Verify Schema & Entity Consistency

**Owner:** Roger (Rahman handoff candidate).

**Objective:** Keep the machine-readable brand data accurate — this is what grounds the client in Google's Knowledge Graph and in how LLMs understand the brand. Inconsistent brand data across the web weakens entity recognition in AI answers.

**Steps:**

- Validate schema on every page changed this month (Rich Results Test).
- Confirm sitewide Organization/LocalBusiness schema: accurate, stable `@id`, `sameAs` pointing to live profiles (GBP, LinkedIn, Wikidata if it exists, verified socials).
- Spot-check brand name/description/category consistency across the site's About page, GBP, and LinkedIn.
- Note missing entity assets (no Wikidata item, thin About page) — do not build them now; they're **Q5's** job.

**Deliverable:** Validation results + inconsistencies fixed or logged for Q5.

**Feeds (per description):** Q5 (entity review backlog) · 4.5 (activity log)

**Blocks (per ClickUp dependency):** *none*

**Blocked by (per ClickUp dependency):** *none*

**Done when:** Results posted → set Ready for Janelle's Review.

> ⚑ **FIRST FULLY DISCONNECTED TASK.** 3.3 has zero wired edges in either direction. Both its declared consumers (Q5, 4.5) are unwired, and nothing gates it.
>
> ⚑ **And its first step is scoped to work it cannot know is finished.** "Validate schema on every page changed this month" is definitionally downstream of 2.1, 2.2, 2.3, 2.4, 2.5 and 3.1. With no blockers, 3.3 can run before those pages are changed, or run mid-week and miss everything changed after it. There is no mechanism by which it learns the set is complete. Same failure class as the 1.4 → 1.6 and 1.8 gaps, but this one is unambiguous, because the step names the dependency in its own text.
>
> ⚑ **Schema validation is done twice with no stated relationship.** 2.3's Refresh SOP step 7 already says "Schema — validate/update the page's markup (supported types only)," per page, during the refresh. 3.3 step 1 then validates schema on every changed page. That is defensible as a do-then-verify split, and an independent verification pass is genuinely good practice — but nothing in either task says that's the intent, and with no dependency wired the "verification" can legitimately run first. Either state the do-then-verify relationship and wire it, or drop the duplicate.
>
> ✅ **Clean scope boundary.** "Do not build them now; they're Q5's job" is exactly right, and it's the third time this template has successfully fenced monthly work off from bigger projects (see also 1.8's rewrite routing and 3.1's escape hatch).

---

### 3.4 Pursue 1–2 AI-Cited Mention Targets

**Objective:** Get the client onto the third-party pages AI engines actually cite. Brand mentions correlate ~3x more strongly with AI visibility than backlinks, and ~63% of LLM citations point to listicle/comparison pages. This is not link building or PR — it's earning presence on cited pages, review platforms, and communities.

**Steps:** Take the top 1–2 cited-but-absent opportunities from 1.6's deliverable (item c). For each, execute one concrete step this month:

- Listicle/roundup → find the editor/author, pitch inclusion with a genuine differentiator (data, unique service, product access). **Value, never payment.**
- Review platform category → complete/optimize the client's profile fully.
- Community thread → post a genuinely helpful answer with disclosed affiliation.

Log outcomes; carry live conversations forward to next month's 3.4.

**Deliverable:** Mentions tracker updated — target, action taken, response/status.

**Feeds (per description):** next month's 3.4 (carry-forwards) · 1.6 (watch for the citation to appear) · 5.1 (report)

**Blocks (per ClickUp dependency):** *none*

**Blocked by (per ClickUp dependency):** 1.6

**Done when:** Steps executed, tracker updated → set Ready for Janelle's Review.

> ⚑ **"Top 1–2" has no selection criterion.** 1.6 item (c) can easily return 20+ cited-but-absent pages. Nothing says how "top" is decided: citation frequency across the prompt set, weighting toward money prompts, attainability, or gut feel. Since this is the only task converting AI-visibility findings into action, and it converts at most two per month, the ranking rule *is* the strategy. Define it.
>
> ⚑ **Carry-forward has no stale-out rule.** "Carry live conversations forward to next month's 3.4" with no condition for closing a dead thread. Six months in, the tracker is carrying unanswered pitches indefinitely and the task's real capacity shrinks each month. Add a rule: no response after N months → close as no-response.
>
> ⚑ **Inconsistent cross-month labelling in one sentence.** The Feeds line qualifies "next month's 3.4" but leaves "1.6" bare, when it must also mean next month's 1.6 — 3.4 is blocked by this month's 1.6, so an edge back to it would be circular. Small, but this template has already produced one genuine-looking circular reference, and unqualified cross-month edges are how the next one hides.
>
> ⚑ **Two load-bearing stats, no source.** The ~3x mentions-vs-backlinks correlation and the ~63% listicle-citation figure are the entire justification for the task existing, and they will be repeated to clients once they travel through 5.1 and Janelle's updates. Record the source and date next to them so they can be re-checked, or soften the precision. An uncited number in an internal template becomes a cited number in a client conversation.
>
> ✅ **"Value, never payment"** and the disclosed-affiliation requirement are the right guardrails, and matching three action types to three opportunity types keeps the task concrete rather than aspirational.

## Week 4 — Ship, QA & Proof of Work

### 4.1 QA All Changed Pages & Request Indexing

**Owner:** Roger (Rahman handoff candidate).

**Objective:** Verify everything touched this month is live, correct, crawlable, and submitted. This is the safety net — one accidental noindex on a refreshed page erases the month's best work.

**Steps — for every page changed this month (2.1–3.2):**

- Live check desktop + mobile — changes rendered correctly.
- No accidental noindex/canonical/robots issue introduced.
- Schema still validates.
- Content present in raw HTML (JS disabled).
- Internal links from 3.2 live.
- Request indexing in GSC.
- Confirm target keywords appear in SEMrush Position Tracking with this month's tag — flag Roger if missing.

**Deliverable:** QA checklist comment, one row per page — URL, checks passed, submitted Y, tracked Y.

**Feeds (per description):** 4.5 (activity log) · **next month's 1.2** (verified-clean baseline)

**Blocks (per ClickUp dependency):** 4.5

**Blocked by (per ClickUp dependency):** 2.1 · 2.2 · 2.3 · 2.4 · 2.5 · 3.1 · 3.2 *(all seven execution tasks)*

**Done when:** Every page passes or has a fix task created → set Ready for Janelle's Review.

> ✅ **Best-wired task in the template.** Seven blockers covering every execution task, and it carries an explicit failure branch ("or has a fix task created") — one of the few tasks that says what happens when the check fails rather than assuming it passes.
>
> ✅ **This also resolves the earlier 4.5 concern.** 4.5 is gated on 4.1, and 4.1 is gated on all seven execution tasks, so 4.5 is transitively covered. The flags raised at 2.1 and 3.2 about feeding 4.5 without blocking it are **withdrawn** — the path exists, just indirectly. The one real exception is 3.3, which feeds 4.5 and has no path to it at all.
>
> ⚑ **Schema is now validated three times.** 2.3 SOP step 7 (do it, during the refresh) → 3.3 step 1 (verify, ungated) → 4.1 step 3 (verify again, correctly gated). Only the third pass is reliably sequenced. Contrast with how the template handles keyword tracking: done in 2.3 step 9 and 2.5 step 4, verified exactly once in 4.1 step 7. That is the correct do-then-verify shape, and the template clearly knows it — it just applied it inconsistently to schema. Cutting 3.3's step 1 and leaving schema verification to 4.1 would remove the redundancy without losing any coverage.
>
> ⚑ **Scope defined by ID range.** "For every page changed this month (2.1–3.2)" is fragile: adding a 2.6 or a 3.5 silently changes what QA covers, and 3.3/3.4 sit outside the range. Since this template is actively being edited, name the tasks explicitly rather than using a range.

---

### 4.2 Check Conversion Paths on Top Organic Landing Pages

**Objective:** With industry-wide click decline, every organic visit must work harder. This is conversion-aware SEO, not a CRO program: we make sure the traffic we win can actually convert.

**Steps — for the top 5 organic landing pages (from 1.1):**

- Clear next-step CTA above the fold.
- Forms and click-to-call actually work — test-submit them.
- The page states who it's for and why choose the client (this also improves AI recommendability).
- Nothing broken by this month's changes.

Fix small items directly; route bigger ones to Samuel or flag for the client via Janelle.

**Deliverable:** Findings log — page, issue, fixed / routed-to.

**Feeds (per description):** 5.1 (report) · client comms via Janelle for anything needing their action

**Blocks (per ClickUp dependency):** *none*

**Blocked by (per ClickUp dependency):** 1.1

**Done when:** All 5 checked, log posted → set Ready for Janelle's Review.

> ⚑ **CONFIRMED DANGLING INPUT — 1.1 promises a top-landing-pages list it never produces.** 1.1's Feeds line says "4.2 (top landing pages list)," and 4.2's step header says "from 1.1." But 1.1's actual steps are all site-level aggregates: clicks/impressions totals, GA4 conversions, AI-channel sessions, the Generative AI report, branded-query trend, and a Position Tracking snapshot. Nothing in them produces a page-level export. 1.2 doesn't either (indexing, crawl stats, list-mode crawl, sitemap counts, CWV). 1.5 does work at page level, but 4.2 isn't gated on 1.5. So whoever runs 4.2 has to pull the list themselves, off-book. **Fix: add "top landing pages by organic clicks, with period-over-period delta" to 1.1's step list.** Second confirmed dangling input, after 3.2's missing full crawl.
>
> ⚑ **Step 4 is a legitimate check with the wrong gate.** "Nothing broken by this month's changes" on the top 5 organic landing pages is *not* redundant with 4.1 — 4.1 QAs the pages that were changed, while this catches collateral damage on high-value pages that weren't touched directly, which is exactly where template-level changes do their quiet damage. Good check. But 4.2 is gated only on 1.1, so it can run in Week 4 before, during, or after the changes it is meant to detect. Wire it after 4.1.
>
> ⚑ **Test-submitting a form is not the same as confirming the conversion registered.** Step 2 already has someone submitting the forms, which is the expensive part. Confirming the event actually landed in GA4 costs one extra look and catches the single highest-cost silent failure in the stack: a conversion event that stops firing. The team has been bitten by exactly this (a client's booking-form event went from 28 fires to 0 at a relaunch and understated conversions for weeks). Add: "confirm the test submission registered as a conversion event in GA4."
>
> ✅ **"Conversion-aware SEO, not a CRO program"** is a well-drawn boundary, and "test-submit them" is the right level of concrete — it's the difference between looking at a form and knowing it works.

---

### 4.3 Spot-Check Query Cannibalization on This Month's Targets

**Objective:** Confirm this month's refreshes didn't create competing pages, and catch existing overlap. Two weak pages splitting one query lose to one strong page — especially under AI retrieval.

**Steps:** For each target query worked this month: GSC → filter by query → Pages. If two client URLs swap or split impressions for one query: recommend consolidate (merge + 301) or differentiate (re-target one page), with the keeper identified by clicks + links.

**Deliverable:** Check log per query + recommendations (if any) routed to next month's 1.8 or the quarterly pruning round (Q2).

**Feeds (per description):** 1.8 *(next month's, per the Deliverable line)* · Q2

**Blocks (per ClickUp dependency):** *none*

**Blocked by (per ClickUp dependency):** 2.3 · 2.4 · 3.1

**Done when:** All target queries checked → set Ready for Janelle's Review.

> ⚑ **HALF THIS TASK CANNOT WORK IN WEEK 4 — the data isn't there yet.** The objective has two halves and they have different data requirements.
>
> *"Catch existing overlap"* works fine now. GSC already holds the impression history for queries where two URLs have long been splitting, and Week 4 is as good a time as any.
>
> *"Confirm this month's refreshes didn't create competing pages"* cannot work in Week 4. Those pages shipped in Weeks 2–3. GSC lags 2–3 days on reporting, and far more importantly, Google has to re-crawl, re-index and re-rank before a refresh changes which URL surfaces for a query. In Week 4 the query→Pages report still largely reflects the pre-refresh state, so the check returns "no new cannibalization" almost by construction — a clean result that means nothing. The failure mode is the worst kind: it looks like a passing check.
>
> **Fix:** split the two halves by cadence. Keep existing-overlap detection here (or move it to Week 1 where GSC analysis is already happening). Move new-cannibalization detection to next month, folded into **1.5**, which already pulls last month's worked keywords from Position Tracking and logs before/after — it has exactly the right data and exactly the right latency.
>
> ⚑ **CONFIRMED FROM BOTH SIDES — 2.5 is excluded.** Flagged at 2.5 as an inference from its Feeds line; 4.3's blocker list (2.3, 2.4, 3.1 only) confirms it. Up to 5 pages get their titles retargeted toward query language each month and none of them are checked for the overlap that retargeting causes.
>
> ⚑ **"Keeper identified by clicks + links" — no source for the links half.** Clicks come from GSC. Nothing in the template produces per-page backlink counts for the client's own URLs; 1.7 pulls backlink data but scoped to competitor pages. Either name the source (SEMrush Backlink Analytics on the two candidate URLs) or drop links from the tiebreak and decide on clicks plus internal links, which 3.2's log does provide.
>
> ⚑ **Feeds line under-qualified again.** Says "1.8"; the Deliverable line correctly says "next month's 1.8." Same pattern as 3.4. Worth standardising the notation across the template.

---

### 4.4 Verify GBP Fundamentals (Categories, Services, Hours) [If applicable]

**Owner:** Rahman. Skip for clients with no physical/local presence. *(Ownership consistent with master rule — checks out.)*

**Objective:** The GBP fields that actually move local rankings: primary/secondary categories, the Services list, and hours — "open at time of search" is now a top-5 local pack factor, so wrong holiday hours literally cost rankings.

**Steps:**

- Primary + secondary categories still optimal — compare against the categories the top 3 local competitors use.
- Services list complete — add any newly available predefined services (a validated ranking factor).
- Set special hours for any holidays in the next 6 weeks.
- Review Google-suggested edits to the profile; revert bad ones.
- Scan the local pack for competitor spam (keyword-stuffed business names) — report via the redressal form.

**Deliverable:** Checklist log — each item verified, changes made, spam reported.

**Feeds (per description):** 4.5 (activity log) · 5.1 (report)

**Blocks (per ClickUp dependency):** *none*

**Blocked by (per ClickUp dependency):** *none*

**Done when:** All items logged → set Ready for Janelle's Review.

> ✅ **Disconnected, and correctly so.** Second task with zero wired edges, but unlike 3.3 this one is right: nothing 4.4 does depends on any other task's output, and no other task needs its result to proceed. Worth stating explicitly so the graph audit doesn't flag it as a defect by pattern-match. The contrast with 3.3 is the point — 3.3's own step text named its dependency, 4.4's doesn't.
>
> ✅ **First task with an explicit skip condition.** "[If applicable]" plus a stated rule is good, and more tasks could use it. One process note: say how a skip gets recorded. A task marked "N/A — no local presence" keeps the deployed milestone auditable; a task deleted or left silently open does not.
>
> ⚑ **CADENCE — two of the five steps are quarterly work sitting in a monthly task.** Category optimality (step 1) and newly-available predefined services (step 2) both move on a timescale of quarters. Competitors rarely change primary categories, and Google adds predefined services occasionally, not monthly. Run monthly, these two produce "no change" roughly eleven times a year, which is how a checklist trains its owner to skim. The other three are correctly monthly: holiday hours on a 6-week lookahead is well designed (the overlap means no holiday falls through the gap between runs), Google-suggested edits go live immediately and want frequent review, and spam scanning is fine monthly. **Split it: move steps 1–2 to the Quarterly Block, keep 3–5 here.**
>
> ⚑ **4.5 gap, same as 3.3.** 4.4 feeds the activity log but nothing wires it, and 4.5 is gated only on 4.1. So the two tasks that feed 4.5 without a path (3.3 and 4.4) are both Week 3–4 work that can finish after the log is compiled.
>
> ⚑ **Reviews are absent from the only GBP task in the template.** The title scopes this to categories, services and hours, which is a legitimate scope for one task. But nothing anywhere else in Weeks 1–5 touches review velocity, review response rate, or the Q&A section, and for a local client those move rankings and conversion at least as much as a category check. Either it's deliberately owned by another service line, or it's a coverage hole. Question for the structural verdict, not a defect in 4.4.
>
> ⚑ **Third uncited load-bearing stat** ("open at time of search is now a top-5 local pack factor"), after 3.4's two. Now a pattern rather than a one-off. Same fix: record source and date beside each, since these travel to clients through 5.1.

---

### 4.5 Compile Monthly Activity Log

**Owner:** Roger (Rahman handoff candidate).

**Objective:** The visible-work record that anchors the report and proves the retainer's value. Clients churn when they can't see the work — this log is why every task in this milestone requires a logged deliverable.

**Steps:** Compile **from task comments (not memory)**: pages optimized (URLs), titles/metas rewritten, technical fixes + fix-sheet items shipped, internal links added, GBP actions, mention/citation progress, gap-analysis handoffs to the backlinks team — with dates. Group by workstream.

**Deliverable:** The month's activity log, formatted for direct inclusion in the report.

**Feeds (per description):** 5.1 (report section 5) · Janelle's Friday update

**Blocks (per ClickUp dependency):** 5.1

**Blocked by (per ClickUp dependency):** 4.1

**Done when:** Log complete and linked in 5.1 → set Ready for Janelle's Review.

> ✅ **"Compile from task comments (not memory)"** is the strongest single line in the template. It is an explicit anti-fabrication control on the one artifact most likely to get padded, and it retroactively justifies the "a task with no logged output is not done" rule in the master workflow section. Keep it exactly as written.
>
> ✅ **CORRECTION to an earlier flag.** I recorded at 2.3, 2.4, 2.5 and 3.1 that the page-refresh work never reaches the activity log, because none of those tasks declare a 4.5 edge. That was wrong. 4.5's step list explicitly collects "pages optimized (URLs)" and "titles/metas rewritten," so the work is captured — it is pulled by the consumer rather than pushed by the producer. **Open flag #11 is downgraded**: the coverage exists, only the declaration is missing. The remaining point is narrower and cosmetic — the Feeds lines under-describe the real graph, so anyone auditing edges will keep reaching the wrong conclusion I did.
>
> ⚑ **One genuine race: 4.4 → 4.5.** 4.5 compiles "GBP actions," which only 4.4 produces. 4.4 sits in the same week, has zero dependencies, and does not block 4.5. Nothing prevents the log being compiled before the GBP work is done. The other two ungated sources are lower risk by position: 1.7's backlink handoff is Week 1 and 3.4's mention progress is Week 3, both almost certainly complete by the time 4.5 runs. Wire 4.4 → 4.5 and the compile is fully covered.
>
> ⚑ **Two workstreams perform fixes that the compile list doesn't collect.** 4.2 says "fix small items directly" and 3.3 says "inconsistencies fixed" — both are work done, and neither appears in 4.5's list of what to gather. 4.3 is analysis rather than activity so its absence is defensible, but conversion-path fixes and entity-consistency fixes are exactly the kind of unglamorous work clients never see unless it is written down. Add both to the compile list.
>
> ⚑ **Minor wording loop in the Done-when.** "Log complete and linked in 5.1" while 4.5 blocks 5.1. It resolves fine in practice (comment the link on the blocked task), but it reads as circular to whoever picks it up cold. "Linked in the 5.1 task" would be unambiguous.

## Week 5 — Report & Decide

### 5.1 Build Monthly Report (Revenue → AI Visibility → Activity)

**Objective:** Answer the only three questions clients care about: are we progressing toward business goals, what did you do and what did it change, what happens next.

**Steps — build in this exact order:**

- Conversions/leads/revenue from organic + GA4 `ai-assistant` channel — the headline.
- AI visibility — SOV trend from 1.6, citation wins/losses.
- Branded search trend (demand proxy).
- Rankings + clicks context — last month's worked keywords (Position Tracking tag) before/after, competitive movement from 1.7. Annotate any Google update this month. Caveat impressions comparisons touching the May 2025–Apr 2026 GSC bug window.
- Activity log from 4.5 (including 1.3 issues resolved).
- Before → Now → Next — 3 bullets what changed, 3 bullets what's next (from 1.8 + carry-forwards).

**Never include:** DA/authority scores, toxicity scores, raw tool exports, unexplained graphs.

**Deliverable:** Client-ready report.

**Feeds (per description):** 5.2 (call agenda comes from this) · Janelle delivers to the client

**Blocks (per ClickUp dependency):** 5.2

**Blocked by (per ClickUp dependency):** 4.5

**Done when:** Report finished 48 hrs before the client call → set **Deliver to Client** (Janelle sends).

> ✅ **The "Never include" list is the second-best line in the template**, after 4.5's compile-from-comments rule. Naming what must not appear is rarer and more useful than naming what must, and it is consistent with 1.3's "the deliverable is a fix sheet, never a raw export." Two tasks independently defending the same standard is a sign the standard is real.
>
> ✅ **Ordering conversions first, rankings fourth** is the right call and worth protecting — it is the structural difference between a report that survives a CFO reading it and one that doesn't.
>
> ⚑ **"What's next (from 1.8)" points at the wrong month.** This month's 1.8 locked *this* month's plan, which by Week 5 is work already done. Next month's targets are selected in **5.3**, which runs after 5.1 and after 5.2. So the report promises the client a "what's next" that has not been decided yet, sourced from a task describing what already happened. Either "what's next" is carry-forwards only — in which case "from 1.8" is mislabeled — or the report genuinely needs 5.3's output, in which case target selection has to move ahead of the report. **Flagging as unresolved pending 5.3's description.**
>
> ⚑ **The 48-hour rule and the deploy instructions can contradict each other.** Master deploy step 2 sets Weeks 2–5 to "each following Friday." 5.1's completion condition is "48 hrs before the client call," and the call date is nowhere in the template. A Monday call needs the report done Thursday, not Friday. Fix in the deploy step: capture the client call date at deployment and back-date 5.1 from it rather than defaulting to Friday.
>
> ⚑ **THIRD DANGLING INPUT — "annotate any Google update this month" has no upstream source.** No task in Weeks 1–4 monitors algorithm updates or SERP volatility. The annotation depends entirely on whoever writes the report happening to remember, which is least reliable in exactly the months it matters most. Either assign update-monitoring to 1.1 or 1.2, or add it as a standing item.
>
> ⚑ **Week 4's three check tasks gate nothing, so the report can outrun them.** 4.2, 4.3 and 4.4 all block zero tasks. 4.2 and 4.4 explicitly feed 5.1 and 4.5. The only Week 4 chain is 4.1 → 4.5 → 5.1, so the report is properly gated on execution work and not gated at all on the checks performed alongside it. Week 1 sources (1.1, 1.6, 1.7, 1.8) are safe by position; the Week 4 ones are not.
>
> ⚑ **The bug-window caveat could be stated as a rule rather than a judgement call.** "Caveat impressions comparisons touching the May 2025–Apr 2026 window" is correct but leaves the reader to work out what touches it. Through the April 2027 report, every YoY impressions comparison does, because the prior-year period always falls inside the window. Stating that directly, with its expiry date, removes the monthly re-derivation.

---

### 5.2 Hold Monthly Strategy Call & Send Recap

**Owner:** Janelle. Roger attends as needed.

**Objective:** The call is a steering and retention tool, not a report readout. The client should leave knowing exactly what happened and what's next.

**Steps:**

- Send agenda to the client in advance — 3 items max.
- Open with: "Anything top of mind you want us to prioritize?"
- Walk Before → Now → Next — not the full report.
- Confirm next month's direction + surface client-side blockers (approvals, access, content inputs).
- Same-day recap email: agreements + next steps + owners. The call never ends in ambiguity.

**Deliverable:** Recap email (copy pasted into this task) + client-side action items created as tasks.

**Feeds (per description):** 5.3 (client direction) · next month's 1.8

**Blocks (per ClickUp dependency):** 5.3

**Blocked by (per ClickUp dependency):** 5.1

**Done when:** Call held, recap sent same day → **Completed** (Janelle closes directly).

> ✅ **First and only task that doesn't end at "Ready for Janelle's Review," and the exception is coherent** — Janelle owns the task, so routing it to herself for review would be circular. Clean handling.
>
> ✅ **Opening with "anything top of mind you want us to prioritize?" before walking the work** is the right sequence for a retention call, and "walk Before → Now → Next, not the full report" names the exact failure mode these calls default into.
>
> ✅ **DOWNGRADES the 5.1 "what's next" flag.** With 5.2 in view the sequence is coherent: 5.1 *proposes* next steps, 5.2 *confirms* direction with the client, 5.3 *locks* it. Propose → confirm → lock is correct, and target selection does not need to move ahead of the report. What remains is a labelling error, not a structural one: 5.1 says "what's next (from 1.8)" when the actual sources are carry-forwards, unworked candidates from 1.5 and 1.7, and 4.3's consolidation recommendations. Fix the attribution, leave the order alone.
>
> ⚑ **THE CRITICAL PATH FOR NEXT MONTH RUNS THROUGH A CLIENT SHOWING UP TO A CALL.** 5.2 blocks 5.3, and 5.3 both closes the month and spawns next month's milestone. Monthly client calls get rescheduled constantly. If the call slips two weeks, next month's milestone is not deployed, Week 1 does not start on time, and the entire following cycle runs late — for a reason nobody on the team controls. This is the single biggest operational fragility in the template, and it will surface within the first few months of running it.
>
> **Fix:** give 5.3 a timeout path. If the call has not happened by the last business day, deploy next month's milestone using Roger's proposed direction from 5.1 and adjust the targets after the call actually happens. The month's work should never be gated on the client's calendar; only the *confirmation* of direction should be.
>
> ⚑ **No location specified for "client-side action items created as tasks."** Which list do they land in — the client's SEO list, a shared list, Janelle's? Small, but unassigned client obligations are how "we were waiting on you" arguments start.

---

### 5.3 Close Month & Spawn Next Month's Milestone

**Objective:** The month never ends without a decision. This step is what keeps a fixed template strategic instead of stale.

**Steps:**

- Note which of this month's refreshes/fixes next month's 1.5 must measure (the Position Tracking monthly tag makes this automatic).
- Flag any task that produced no value for the second straight month → quarterly template review (**Q6**) for kill-or-redesign.
- Create next month's `[Month] [Year] SEO Tasks` milestone from the MASTER TEMPLATE (deploy steps are in the master's description).
- Triage incomplete items deliberately — re-scope into next month's plan or drop with a reason. **Never auto-roll.**
- Pre-fill next month's 1.8 with anything already decided (from 5.2's recap).

**Deliverable:** Next month's milestone exists and is populated; carry-forward log posted here.

**Feeds (per description):** Next month's entire cycle

**Blocks (per ClickUp dependency):** *none* (terminal task; hands off by creating an artifact, not by gating one)

**Blocked by (per ClickUp dependency):** 5.2

**Done when:** This milestone closes → set Ready for Janelle's Review.

> ✅ **This task is the reason the template can survive contact with a year of use.** Two mechanisms carry it: a self-pruning rule (tasks producing no value twice running go to Q6 for kill-or-redesign) and a no-auto-roll rule on incomplete work. Most recurring templates have neither, which is why they silently accumulate dead steps until the whole thing gets skimmed. Keep both.
>
> ⚑ **BUT THE KILL RULE IS UNDEFINED, AND AS WRITTEN IT WILL EAT THE SAFETY NETS FIRST.** "Any task that produced no value for the second straight month" has no definition of value. 1.2 explicitly states that "a stated 'no issues' is a valid outcome." So a technical health sweep that comes back clean twice, or a crawler-access check that finds nothing blocked twice, or a QA pass where everything passed twice, all read as "no value" under a naive reading — when returning clean *is* the value. The tasks most likely to be flagged are exactly the insurance tasks whose whole point is producing nothing most of the time, and whose absence is only discovered the month something breaks.
>
> **Fix:** define value as *output produced and consumed*, not *problems found*. A task earns its slot if it produced a logged deliverable that a downstream task or the report actually used. Kill candidates are tasks that were skipped, produced nothing, or produced something nobody read — never tasks that ran and reported clean.
>
> **ESCALATED after Q6.** The same criterion appears a second time, phrased worse: Q6 step 1 tests for "measurable deltas." This is a system-level problem applied at two points, not a wording slip in one task. Fix both together.
>
> **SOLVED — the template already contains the answer, in Q7.** Q7 pre-declares its own null result as success: *"log 'no action warranted' with the export attached — the expected outcome most quarters."* Applying that one sentence to 1.2, 1.4, 4.1 and 4.3 inoculates every insurance task against the kill test, without needing to get the kill criterion's wording perfect. Cheaper and more durable than rewriting the criterion alone, and the precedent is the boss's own.
>
> ⚑ **The Quarterly Block cadence has no counter.** Master deploy step 3 says "every 3rd month for the client, also duplicate the Quarterly Block," and 5.3 is where deployment happens — but nothing records which month is quarter-start for which client. Across a roster of clients on different start dates this is tracked entirely in someone's head. Either stamp the quarter cycle on the client's SEO list, or add the next-quarterly-due month to the carry-forward log so it travels with the milestone.
>
> ⚑ **No timeout path — confirms the 5.2 fragility.** 5.3 is blocked by 5.2 with no alternative route, so next month's milestone genuinely cannot be created until the client attends a call. This is where the fix belongs: allow 5.3 to deploy on the last business day using 5.1's proposed direction, with targets adjusted after the call.
>
> ⚑ **Self-referential Done-when.** "This milestone closes" is the completion condition for a task *inside* that milestone, and the milestone cannot close until its tasks are done. It resolves in practice as "everything else is finished," but for the one task that gates month-end, the condition should be its own Deliverable: next month's milestone exists and is populated, carry-forward log posted.
>
> ⚑ **Nothing verifies the deploy was done correctly.** The master's deploy sequence has five steps including a conditional one. A missed rename, a wrong due-date pattern, or a forgotten Quarterly Block is invisible until someone opens next month's milestone and finds it wrong. A three-line confirmation in the carry-forward log (renamed / due dates set / quarterly block Y-N) closes that.

## Quarterly Block (QB)

Deployed every 3rd month, slots into Weeks 2–3 capacity.

### Q1 Run Full Technical Crawl & Rendering Parity Audit

**Cadence:** every 3rd month.

**Steps:**

- Full Screaming Frog crawl with comparison vs last quarter's crawl: new issues, index bloat, orphan pages, redirect debt.
- Rendering parity on key templates: raw HTML vs rendered vs what AI bots receive.
- Log-file / CDN-analytics review of crawler behavior if available (which bots, what they fetch, 200s vs blocks).

**Deliverable:** Prioritized findings list; fix tasks created into next month's 1.8.

**Feeds (per description):** 1.8 · 2.1 *(both presumably next month's, per the Deliverable line)*

**Dependencies:** *none supplied*

**Done when:** Findings + routed tasks posted → set Ready for Janelle's Review.

> ✅ **RESOLVES the 3.2 dangling input — and changes the recommendation.** I flagged that 3.2's orphan check and click-depth check need a full spider crawl no task produces. The full crawl exists; it lives here, quarterly. That refines rather than withdraws the finding:
>
> 1. 3.2 runs **monthly**, so in two months out of every three its orphan and depth checks still have no data source.
> 2. In the third month, 3.2's orphan check **duplicates Q1's**, which already covers orphan pages across the whole site rather than just recent content.
>
> **The fix is now clear, and it's the cheaper of the two options I originally offered: strip the orphan and depth checks out of 3.2 and leave them in Q1.** Don't add a monthly full crawl. 3.2 keeps what it can actually do monthly — contextual links into refreshed pages, and fixing links that pass through redirects on pages touched this month.
>
> ✅ **The rendering-parity split is done right, and it's the model the schema checks should have followed.** 1.4 does a monthly light version (raw HTML on the homepage plus 2 money pages, AI bots hitting the site at all); Q1 does the quarterly deep version (parity across key templates, what bots actually receive, log-file evidence). Light-monthly plus deep-quarterly is a real division of labour. Contrast with schema, which is simply validated three times at the same depth.
>
> ⚑ **No severity tiers, and no same-month escalation route.** 1.2 classifies every finding Blocker / Fix this month / Watch and routes accordingly. Q1 produces a "prioritized findings list" and sends everything to *next* month's 1.8 regardless of what it found. A full quarterly crawl is the single most likely task in the template to surface something urgent — mass deindexation, a robots rule blocking a section, redirect debt eating crawl budget — and as written all of it waits a month. Borrow 1.2's vocabulary and give Blockers a direct route into **this** month's 2.1.
>
> ⚑ **"Comparison vs last quarter's crawl" assumes the last crawl is retrievable.** No archive location is specified. The comparison is the entire value of step 1, and it silently degrades to a plain crawl the first time someone can't find the previous file. Name where crawls are stored, with the client and date in the filename.
>
> ⚑ **Cross-month labelling again.** Deliverable says "next month's 1.8"; Feeds says "1.8 · 2.1" unqualified. Third instance after 3.4 and 4.3. Worth one standard notation across the template.
>
> **Placement tradeoff (not a defect):** sitting in Weeks 2–3 means Q1's findings can never inform the plan that was locked in Week 1, so quarterly technical work is always actioned in the following month. That is a defensible capacity choice and it's stated honestly — but it is exactly why the Blocker escalation route above matters.

### Q2 Execute Content Pruning & Consolidation Round

**Cadence:** every 3rd month.

**Objective:** Site-level quality drag is real — dead weight hurts the whole domain, and cannibalizing weak pages split relevance under AI retrieval.

**Steps:**

- Review pages with ~zero clicks/impressions over 6+ months + the quarter's 4.3 cannibalization flags.
- Decide per page: improve / consolidate (merge + 301 to the strongest URL, port unique content, update internal links) / delete + 301 / noindex / leave.
- Execute approved consolidations; verify redirects + updated internal links.

**Deliverable:** Decision log; merges/redirects executed and verified.

**Feeds (per description):** 1.2 (cleaner index) · 1.5

**Dependencies:** *none*

**Done when:** Log posted, changes verified → set Ready for Janelle's Review.

> ⚑ **THE HIGHEST-RISK TASK IN THE TEMPLATE HAS THE WEAKEST SAFETY RAILS.** Q2 deletes pages, merges content, issues 301s and applies noindex — the only irreversible, high-blast-radius work anywhere in the system. Compare how the template guards far smaller changes:
>
> - 1.3 → 2.2: a *site-health fix sheet* requires Roger's line-by-line approval before Rahman may touch anything, and "if a fix isn't on the approved sheet, it doesn't get made."
> - 2.5: a *title tag rewrite* is gated behind 4.1's independent QA pass.
> - 4.1: every page changed in 2.1–3.2 gets live-checked, indexation-checked, schema-checked by someone verifying rather than doing.
>
> Q2 has none of that. "Execute **approved** consolidations" never says who approves. 4.1's scope is "every page changed this month (2.1–3.2)," which excludes Q-numbered tasks, so deletions and redirects bypass the QA gate entirely and are verified only by the person who made them. A title tag gets an independent check; deleting a page does not. **Fix: add a named approval gate before step 3 (Roger at minimum, client sign-off where content is being deleted rather than merged), and put Q2's changed URLs into 4.1's QA scope.**
>
> ⚑ **FOURTH DANGLING INPUT — nothing produces the zero-click page list.** "Pages with ~zero clicks/impressions over 6+ months" has no producer. 1.1 is site-level aggregates. 1.5 finds *declining* pages (clicks down >20%), which is a different population — a page that never had clicks never declined. GSC holds 16 months so the data exists, but no task pulls it. Add an explicit step: pull GSC page-level performance over the trailing 6 months, filter to zero or near-zero clicks.
>
> ⚑ **Deleting on organic metrics alone will eventually delete a page that converts.** The decision criteria are clicks and impressions only. A page with zero organic clicks can still take email, paid or direct traffic and convert on it — PPC landing pages are the obvious case, and the team's own audit rules already say to exclude PPC landing pages, thank-you pages and similar utility URLs from SEO metrics precisely because they distort counts. Add a gate before step 2: check GA4 for non-organic sessions and conversions on every deletion candidate, and exclude anything with either.
>
> ⚑ **"The quarter's 4.3 flags" — which three months?** Q2 sits in Weeks 2–3 and 4.3 runs in Week 4, so in the quarter month Q2 runs *before* that month's 4.3. Whether a flag raised this month waits one month or four depends on a boundary nobody has stated. Name the window.
>
> ✅ **The decision options are well enumerated**, and "port unique content" plus "update internal links" are the two steps people actually skip in a merge. Keeping them inside the option text rather than in a separate note is the right call.

---

### Q3 Map Topic Cluster & Prompt Coverage Gaps

**Cadence:** every 3rd month.

**Steps:**

- For the client's 2–3 money topics: map the sub-query/fan-out space (PAA mining, AlsoAsked, 1.6 prompt history, 1.7 keyword-gap history) against existing pages.
- Gaps fillable by expanding existing pages → monthly refresh queue. Genuinely new pages → content team pipeline (outside this template).
- Review the standing AI prompt set (used by 1.6): add/retire prompts as the client's market shifts. **This is the only place the prompt set changes — consistency is what makes the monthly trend meaningful.**

**Deliverable:** Gap map; refresh queue updated; prompt set current.

**Feeds (per description):** 1.5 · 1.6 · content pipeline

**Dependencies:** *none* (research task — correctly ungated, same as 4.4)

**Done when:** Posted → set Ready for Janelle's Review.

> ⚑ **CHANGING THE PROMPT SET BREAKS THE EXACT METRIC IT EXISTS TO PROTECT.** 1.6's entire premise is that "single runs are noisy; the month-over-month trend on a consistent prompt set is the signal," and Q3 correctly makes itself the only place the set may change. But adding or retiring prompts changes the denominator of SOV %. The month after a Q3 revision, 1.6 reports "SOV % vs last month" and 5.1 reports an SOV trend, and neither knows the basis moved. A quarterly step change gets read as a performance change, in a metric the client is being shown as headline evidence.
>
> **Fix, and the template already has the pattern for it:** the GSC impressions bug is handled by naming the affected window and caveating every comparison that touches it. Do the same here. Stamp the prompt-set version and change date, have 1.6 report SOV on the stable subset alongside the full set for the following month, and give 5.1 a caveat line for the revision month.
>
> ⚑ **FIRST DANGLING OUTPUT — Q3 pushes to a queue nothing reads.** "Gaps fillable by expanding existing pages → monthly refresh queue," and Feeds names 1.5. But 1.5's four steps are all GSC-derived (decay, striking distance, CTR anomalies, measuring last month's work) and none of them consults a standing refresh queue. So Q3's expansion candidates enter an artifact that 1.5 never opens, and a quarter's topic-gap work quietly fails to reach the task that selects targets. Every other gap so far has been a missing *input*; this is the mirror case. **Fix: add a fifth source to 1.5's step list — "pull any open items from the Q3 refresh queue."**
>
> ⚑ **Third feed into an external pipeline with no return path.** 1.7 → backlinks team, 1.8 → content calendar, and now Q3 → content pipeline. Two of those three are the same content pipeline fed from two different tasks, and nothing anywhere asks whether a routed item was ever picked up or shipped. Worth one standing check somewhere in Week 1 or Q6.
>
> ✅ **"This is the only place the prompt set changes"** is exactly the right constraint, stated with its reason. Single-owner rules for shared artifacts are how measurement stays comparable — the flaw above is in the handling of the change, not in the decision to centralise it.

### Q4 Verify Citations & Listings Integrity [If applicable]

**Owner:** Rahman. **Cadence:** every 3rd month. Skip for clients with no physical/local presence. *(Ownership consistent with master rule — checks out.)*

**Objective:** Consistency maintenance only — these listings now feed AI entity grounding more than Google rankings. **No new bulk citation building.**

**Steps:**

- NAP + categories + hours consistency across the majors: GBP, Apple Business Connect (Apple Maps usage nearly doubled to 27%), Bing Places, Yelp, Facebook, top data aggregators, and the client's 10–20 vertical directories.
- Fix drift.
- Confirm renewal-based listings (Data Axle, Neustar, Foursquare, YP, etc.) are current.

**Deliverable:** Consistency checklist + corrections log.

**Feeds (per description):** 3.3 · "AI entity grounding"

**Dependencies:** *none*

**Done when:** Posted → set Ready for Janelle's Review.

> ✅ **Second correct light-monthly / deep-quarterly split.** 3.3 spot-checks brand consistency across three sources every month; Q4 sweeps the full platform set quarterly. Same shape as 1.4 / Q1 on rendering, and it works for the same reason: the monthly version is cheap enough to actually get done, the quarterly version is thorough enough to catch what the spot-check misses. Two of these now, against one badly-split case (schema, D3).
>
> ✅ **"No new bulk citation building"** is the right boundary and worth defending — it's the difference between maintenance and the citation-spam treadmill agencies sell by the hundred.
>
> ⚑ **STRUCTURAL — the template runs on at least nine standing per-client artifacts and none of them has a stated home or owner.** Q4 needs "the client's 10–20 vertical directories," which exists nowhere in the template. The full list of artifacts the monthly cycle assumes: the client dashboard (1.1), the SEMrush Site Health tracker (1.3), the SOV tracker (1.6), the standing AI prompt set (1.6/Q3), the mentions tracker (3.4), SEMrush Position Tracking with month tags (throughout), last quarter's crawl archive (Q1), the monthly refresh queue (Q3), and this directory list. Every one is assumed to exist, be findable, and be current. **This may be exactly what the standing `MASTER — Repeated Tasks` parent is for — holding until that arrives before calling it a defect.** If it isn't, this is the quiet failure mode that breaks a template on client number four.
>
> ⚑ **"AI entity grounding" is a phantom Feeds edge.** Every other Feeds entry in the template names a task or a named team. This one names an outcome. It reads fine in prose but it means the edge cannot be audited or wired, and Q4's only real consumer is 3.3.
>
> ⚑ **Cross-month labelling, fourth instance.** "Feeds: 3.3" must mean next month's 3.3 — Q4 corrects the baseline that a future spot-check works from. Unqualified again.
>
> ⚑ **Fourth uncited load-bearing stat** (Apple Maps at 27%), after 3.4's two and 4.4's one. Tallying, not re-arguing — the fix is one convention applied everywhere.
>
> **Reviews remain absent.** Local coverage is now better than it looked at 4.4: monthly GBP fundamentals plus quarterly citation integrity. But review velocity, review response and Q&A appear nowhere in either. That is the one genuine local hole, and it stays on the list for the structural verdict.

---

### Q5 Review & Strengthen Entity Infrastructure

**Cadence:** every 3rd month.

**Objective:** The entity home + consistent brand data is what Google's Knowledge Graph and LLMs use to understand who the client is. Better grounding → better AI answers about the brand.

**Steps:**

- Audit the entity home (usually `/about`): clearly states who / what / where / for whom, with Organization schema, stable `@id`, complete `sameAs` array.
- Create or update the Wikidata item (any real business qualifies — no notability bar).
- Check the knowledge panel (if one exists) for accuracy.
- Brand-consistency scan: same name/description/category across site, GBP, LinkedIn, Crunchbase, review profiles.
- Work the backlog of entity gaps logged by 3.3 over the quarter.

**Deliverable:** Entity audit log; fixes made; larger items routed to 1.8.

**Feeds (per description):** 3.3 · 1.6 (better grounding → better AI answers)

**Dependencies:** *none*

**Done when:** Posted → set Ready for Janelle's Review.

> ⚑ **FACTUAL ERROR, AND AN OPERATIONALLY RISKY ONE — "any real business qualifies, no notability bar" is not true of Wikidata.** Wikidata has a notability policy with three criteria. The broad one (criterion 2) admits any clearly identifiable entity that "can be described using **serious and publicly available references**." That is genuinely permissive and many businesses do clear it — but the reference requirement is real. An item whose only sources are the client's own website and directory listings can be, and routinely is, nominated for deletion.
>
> Written as an absolute, this instruction sends someone to create client items every quarter on the assumption they always stick. Consequences: wasted quarterly effort when items are deleted, and — more seriously — an account that repeatedly creates promotional items for paying clients attracts scrutiny, which is a worse outcome than never having created them.
>
> **Fix:** replace with "verify serious, independent, publicly available references exist before creating an item; where they don't, log it as an entity gap rather than creating a thin item." And name who holds the Wikidata account, with a note on disclosing the paid relationship — editing for clients without disclosure is against community norms, and a flagged account taints every client it has touched.
>
> ⚑ **Q4 and Q5 duplicate brand-consistency scanning at the same cadence, in the same month.** Q4 step 1 scans NAP + categories + hours across GBP, Apple, Bing, Yelp, Facebook, aggregators and vertical directories. Q5 step 4 scans name/description/category across site, GBP, LinkedIn, Crunchbase and review profiles. Both run in the quarter month, both cover GBP, both check name and category. This is not the light-monthly/deep-quarterly split that works elsewhere (1.4 / Q1, 3.3 / Q4) — it is two same-cadence tasks doing overlapping work with no stated boundary. **Fix: Q4 owns listing-level NAP and hours; Q5 owns name, description and category as entity attributes; or Q5 simply consumes Q4's corrections log rather than re-scanning.**
>
> ⚑ **Brand-consistency now appears in three tasks** (3.3 monthly, Q4 quarterly, Q5 quarterly). The 3.3 → Q4 relationship is a clean spot-check/sweep split. The Q4 → Q5 relationship is redundancy.
>
> ⚑ **Cross-month labelling, fifth instance** ("larger items routed to 1.8" — next month's).
>
> ✅ **The entity-home audit criteria are well chosen** — who/what/where/for whom plus stable `@id` and a complete `sameAs` array is the right minimum, and it lines up exactly with what 3.3 checks monthly, so the backlog handoff from 3.3 works cleanly.

---

### Q6 Run Template & Strategy Health Check

**Owner:** Roger → review template changes with Nathan. **Cadence:** every 3rd month.

**Objective:** The anti-staleness mechanism for the whole system. Templated retainers die when tasks keep shipping without producing deltas — this is where tasks get killed or redesigned.

**Steps:**

- Review the quarter's 5.3 flags: which tasks produced measurable deltas, which produced none twice+ → kill or redesign.
- Which new tactic (from industry movement) earns a trial slot next quarter?
- Re-confirm the client's goals/KPIs haven't shifted.
- Write the next quarter's emphasis for this client.

**Deliverable:** Written quarter plan + any master-template change requests (loop Nathan on template changes).

**Feeds (per description):** MASTER TEMPLATE · next 3 months of 1.8

**Dependencies:** *none*

**Done when:** Posted → set Ready for Janelle's Review.

> ✅ **The system has a real maintenance loop, which is rare.** 5.3 flags monthly → Q6 decides quarterly → the MASTER TEMPLATE changes. Most recurring templates have no mechanism for changing themselves and simply rot. This one does, and routing template changes through Nathan gives the "loop Nathan in only when needed" rule from the master a concrete trigger.
>
> ⚑ **BUT THE KILL CRITERION NOW APPEARS TWICE, AND BOTH PHRASINGS TARGET THE SAFETY NETS.** 5.3 flags tasks that "produced no value for the second straight month." Q6 step 1 restates it as "which tasks produced **measurable deltas**, which produced none twice+ → kill or redesign." The Q6 phrasing is the more dangerous of the two. A technical health sweep that finds nothing, a crawler-access check where nothing is blocked, a QA pass where every page passes — none of these produce a measurable delta, and all three are working exactly as designed. 1.2 explicitly states that "a stated 'no issues' is a valid outcome," and Q6's criterion would kill it.
>
> This is no longer a one-line ambiguity in 5.3. It is a system-level criterion applied at two points, and left as written it will progressively strip out the insurance tasks and keep the ones that always find something to do. **Fix in both places: define value as *output produced and consumed*, never as *problems found*.** A task earns its slot if it produced a logged deliverable a downstream task or the report used. Kill candidates are tasks that were skipped, produced nothing, or produced something nobody read.
>
> ⚑ **Q6 has a route to the master but no step that goes looking for drift.** This partly answers the "Refresh SOP has no canonical home" concern from 2.4 — improvements *can* reach the master, via change requests here. But none of Q6's four steps is "compare a deployed milestone against the master and fold in what changed in flight." The known live example: 3.1 carries a three-way escape hatch for an unviable target that 2.3, the SOP it inherits from, does not. Nothing currently prompts anyone to notice. **Add a fifth step: diff a recent deployed milestone against the master template.**
>
> ⚑ **The add mechanism and the kill mechanism are in the same task but unlinked, so the template only grows.** Step 1 kills, step 2 grants "a trial slot" to a new tactic. Nothing connects them. Killing is always harder than adding — it requires admitting something didn't work — so over eight quarters the realistic trajectory is a task count that climbs while the kill list stays empty. Pair them: a trial slot is funded by a kill, or by explicit capacity approval.
>
> ⚑ **"Re-confirm the client's goals/KPIs haven't shifted" is an internal task making an external claim.** Roger and Nathan cannot re-confirm a client's goals between themselves; that's inference. The client-facing surface already exists in 5.2, which surfaces direction monthly. Either route this through Janelle as an explicit quarterly question on the 5.2 agenda, or reword it to "review whether anything in the quarter's 5.2 recaps indicates a shift."

---

### Q7 Review Backlink Profile for Spam Attacks & Manual Actions

**Owner:** Rahman → Roger approves any action. **Cadence:** every 3rd month. *(Ownership consistent with master rule — checks out.)*

**Objective:** Defensive monitoring only. Routine "toxic link" disavows are actively discouraged: Google states disavow is only for manual actions or links you built yourself; SEMrush toxicity scores heavily over-flag harmless links, and disavowing them throws away real link equity. **The trigger for action is an attack pattern, not a toxicity score.**

**Steps:**

- Check GSC Manual Actions (should be a 10-second "none").
- Export new referring domains for the quarter (SEMrush/GSC).
- Look for genuine attack patterns only: sudden spikes of hundreds of spam domains, hacked-site link injections, spammy exact-match anchors at volume, links pointing at pages that don't exist. Ignore ordinary low-quality directories/scrapers — Google already ignores them.
- If (and only if) a real attack or manual action exists: build the disavow list at domain level → Roger reviews + approves every entry → Rahman submits via the Disavow Tool and logs the date.
- Otherwise: log "no action warranted" with the export attached — **the expected outcome most quarters.**

**Deliverable:** Quarterly review log — manual-action status, new-domain summary, action taken or "none warranted."

**Feeds (per description):** 5.1 (only if action was taken — never report toxicity scores to clients)

**Dependencies:** *none*

**Done when:** Review logged, any disavow approved + submitted → set Ready for Janelle's Review.

> ✅ **THE BEST-WRITTEN TASK IN THE TEMPLATE, AND IT CONTAINS THE FIX FOR THE KILL-CRITERION PROBLEM.** The line *"log 'no action warranted' with the export attached — the expected outcome most quarters"* pre-declares its own null result as success. It is the only task in the entire system that inoculates itself against 5.3's and Q6's "produced no value / no measurable delta" kill test.
>
> **So the fix I recommended at 5.3 and Q6 already exists inside the template — it just isn't applied consistently.** Give 1.2, 1.4, 4.1 and 4.3 the same sentence: state the expected null outcome as the normal, successful result. That is a cheaper and more durable fix than rewriting the kill criterion alone, and it has a precedent the boss already wrote.
>
> ✅ **Correctly rejects the toxicity-score disavow habit, with reasoning.** Google's actual position, the over-flagging problem, and the cost of discarding real equity are all stated. Most agency templates get this wrong in the opposite direction and bill for it quarterly.
>
> ✅ **Third independent statement of the same reporting standard** — 1.3's "never a raw export," 5.1's "never include DA/toxicity scores," Q7's "never report toxicity scores to clients." Three tasks defending the same line without cross-referencing each other is how you can tell a standard is real rather than decorative.
>
> ⚑ **THE MANUAL-ACTIONS CHECK SHOULD BE MONTHLY, AND THE TASK ITSELF MAKES THE ARGUMENT.** It is described as a "10-second 'none'." A manual action is the single highest-severity event in search, and checking quarterly means worst-case detection lag is roughly 90 days. Moving just that one step into 1.2 costs about 20 extra seconds a year and cuts the lag to 30 days. Leave the backlink-profile analysis quarterly — it is genuinely quarterly work. Split the check from the analysis.
>
> ⚑ **The approval asymmetry with Q2 is now stark, and it sharpens that finding.** Q7 guards a *reversible* defensive action — a disavow file can be replaced — behind Roger approving **every single entry** before submission. Q2 deletes pages, merges content and issues permanent 301s with an unnamed approver, no independent QA, and no client sign-off. The template applies its tightest control to its more recoverable action and its loosest to its least recoverable one. Q7 is the model; Q2 should copy it.
>
> ⚑ **Nothing re-verifies a submitted disavow persists.** Disavow files can be lost when a property is re-verified or a domain property replaces a URL-prefix one. If a disavow was ever submitted, next quarter's Q7 should confirm it is still in place. One line.

## MASTER — Repeated Tasks *(awaiting)*

Standing parent, built once per client, not monthly.

---

## Dependency Ledger

Populated as tasks arrive. `Feeds` = stated in the task description. `Blocks` = wired as a ClickUp dependency.

| Task | Feeds (per description) | Blocks (per ClickUp) | Blocked by | Discrepancy |
| --- | --- | --- | --- | --- |
| 1.1 | 1.5, 1.8, 4.2, 5.1 | 1.5, 1.8, 4.2 | — | 5.1 named in Feeds, absent from Blocks |
| 1.2 | 2.1, 1.8 | 2.1 | — | 1.8 named in Feeds, absent from Blocks |
| 1.3 | 2.2, 5.1 | 2.2 | — | 5.1 named in Feeds, absent from Blocks |
| 1.4 | 2.1, 1.6 | 2.1 | — | 1.6 named in Feeds, absent from Blocks — **and 1.6 is same-week** |
| 1.5 | 1.7, 1.8, 5.1 | 1.7, 1.8 | 1.1 | 5.1 unwired (consistent); 90d window vs 1.1's 30d snapshot |
| 1.6 | 1.8, 3.4, 5.1 | 1.8, 3.4 | **none** | 5.1 unwired (consistent); **1.4 feeds it but is unwired — confirmed gap** |
| 1.7 | 1.8, *backlinks team (external)*, 5.1 | 1.8 | 1.5 | 5.1 unwired (consistent); external edge has no return path |
| 1.8 | "every execution task in Weeks 2–3", *content calendar (external)*, client comms | 2.3, 2.4, 2.5, 3.1 | 1.1, 1.5, 1.6, 1.7 | **1.2, 1.3, 1.4 required by its own steps but unwired**; Feeds overstates ("every execution task" ≠ 4 wired) |
| 2.3 | 3.2, 4.1, 4.3, *next month's 1.1/1.5* | 3.2, 4.1, 4.3 | 1.8 | **Exact match** — only unwired edge is cross-month, correctly carried by the Position Tracking tag. No 4.5 / 5.1 edge though. |
| 3.2 | 4.1, 4.5 | 4.1 | 2.3, 2.4, 3.1 | 4.5 unwired; **steps 2–3 need a full crawl no task produces** |
| 3.3 | Q5, 4.5 | **none** | **none** | **Fully disconnected node.** Step 1 is scoped to "every page changed this month" with nothing gating it. |
| 4.3 | *next month's* 1.8, Q2 | **none** | 2.3, 2.4, 3.1 | **2.5 excluded (confirmed both sides)**; half the task runs too early for GSC to show anything |
| 2.4 | 3.2, 4.1, 4.3, *next month's 1.1/1.5* | 3.2, 4.1, 4.3 | 1.8 | Exact match, same as 2.3. No 4.5 / 5.1 edge. |
| 2.5 | 4.1, *next month's 1.5* | 4.1 | 1.8 | Not in master's shell list; **no 4.3 edge though 2.3/2.4 have one**; no 4.5 / 5.1 |
| 3.1 | 3.2, 4.1, 4.3, *next month's 1.1/1.5* | 3.2, 4.1, 4.3 | 1.8 | Exact match, same as 2.3/2.4. No 4.5 / 5.1 edge. Carries a richer escape hatch than the SOP it inherits. |
| 3.4 | *next month's* 3.4, *next month's* 1.6, 5.1 | **none** | 1.6 | Terminal node within the month (correct for outreach). 5.1 unwired. Cross-month edges inconsistently labelled. |
| 2.1 | 4.1, 4.5, 5.1 | 4.1 | 1.2, 1.4 | 4.5 and 5.1 unwired |
| 4.1 | 4.5, *next month's 1.2* | 4.5 | 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2 | **Best-wired task.** All seven execution tasks gate it. Excludes 3.3, 3.4. |
| 5.1 | 5.2, client delivery | 5.2 | 4.5 | Consumes 1.1, 1.3, 1.6, 1.7, 1.8, 3.4, 4.2, 4.4 — none wired. Week 1 sources safe by position; 4.2/4.4 are not. |
| 5.2 | 5.3, *next month's* 1.8 | 5.3 | 5.1 | Owned + closed by Janelle (only task not routed to her for review). **Gates next month's deployment on a client attending a call.** |
| 5.3 | next month's entire cycle | **none** | 5.2 | Terminal task. Hands off by creating an artifact, not by gating one. No timeout path. |
| 4.2 | 5.1, client comms | **none** | 1.1 | 5.1 unwired; **"top landing pages from 1.1" is not something 1.1 produces**; step 4 gated only on 1.1 |
| 4.4 | 4.5, 5.1 | **none** | **none** | Disconnected, but **correctly** so (contrast 3.3). 4.5 edge unwired. Steps 1–2 are quarterly work. |
| 4.5 | 5.1, Janelle's Friday update | 5.1 | 4.1 | Transitively gated on the seven execution tasks via 4.1. **Compiles by pull, not push** — collects from tasks that never declare a 4.5 edge. Real race: 4.4 (same week, ungated). |
| 2.2 | 4.1, 4.5, 5.1, *next month's 1.3* | 4.1 | 1.3 | 4.5 and 5.1 unwired; cross-month edge carried by the SEMrush tracker (correct) |

### Emerging pattern — Feeds vs Blocks

Three for three: every task so far names more consumers in `Feeds` than it wires in `Blocks`, and the unwired edge is always a soft informational hand-off.

- **5.1 is never wired** as a blocking dependency by anything (unwired from 1.1 and 1.3, and named again by 2.1). This looks deliberate and correct. The month-end report naturally follows everything, and fanning every task into it as a hard block would add graph noise with no operational value.
- **1.8 is inconsistent.** 1.1 → 1.8 is wired; 1.2 → 1.8 is not. Both explicitly feed the same planning decision. Watch whether 1.5 through 1.7 wire into 1.8 or not.
- **1.4 → 1.6 is a CONFIRMED gap, and it affects correctness rather than tidiness.** 1.6's dependency list has no blockers at all, so nothing stops it running before 1.4. If 1.6 reports zero AI visibility first, that finding is uninterpretable until 1.4 establishes whether the CDN was blocking every AI bot the whole time. Wrong order here doesn't just delay work, it produces a wrong diagnosis that then flows into 1.8 target selection and 3.4's mention-target list. Candidate fix at verdict time: wire 1.4 → 1.6 as a hard block, or fold the access check into 1.6's first step.
- **5.1 is now unwired from four sources** (1.1, 1.3, 1.5, 1.6) and named by a fifth (2.1). Treating this as settled design intent rather than a defect.

---

## Duplicate coverage candidates

Logged as found, not yet adjudicated. Some of these may be deliberate redundancy (a second net), which is a defensible design choice — the test is whether the second pass adds signal or just repeats the first.

| # | Overlap | Where | Note |
| --- | --- | --- | --- |
| D1 | **SEMrush Position Tracking, filtered by last month's tag** | 1.1 step 6 and 1.5 step 4 | Same pull, same filter, same purpose (see how last month's worked keywords moved). 1.1 calls it a "snapshot"; 1.5 calls it "measure our own work" and logs before/after. Since 1.1 blocks 1.5, the second pull is redundant unless 1.5 needs a different cut. Likely fix: 1.1 captures it, 1.5 interprets it. |
| D2 | **Technical issue discovery** | 1.2 (GSC sweep) and 1.3 (SEMrush Site Audit) | Explicitly framed as intentional ("automated second net alongside 1.2"), and the two tools genuinely surface different classes of issue. Keep. |
| D6 | **Brand-consistency scanning, three passes** | 3.3 step 3 (monthly, 3 sources), Q4 step 1 (quarterly, listings), Q5 step 4 (quarterly, entity attrs) | 3.3 → Q4 is a clean spot-check/sweep split, keep. **Q4 → Q5 is same-cadence redundancy in the same month** — both cover GBP, name and category. Draw the boundary or have Q5 consume Q4's log. |
| D4 | **Orphan-page detection** | 3.2 step 2 (monthly) and Q1 step 1 (quarterly) | Q1 covers the whole site; 3.2 covers "recently published content" but has no crawl to do it with 2 months in 3. Cut from 3.2. |
| D5 | **Raw-HTML / rendering parity** | 1.4 step 3 (monthly, 3 pages) and Q1 step 2 (quarterly, key templates + bot's-eye view) | **Deliberate and correct** — light-monthly, deep-quarterly. Keep. This is the split D3 should have used. |
| D3 | **Schema validation, three passes** | 2.3 SOP step 7, 3.3 step 1, 4.1 step 3 | Do → verify → verify again. Only 4.1's pass is correctly gated. Cutting 3.3 step 1 loses no coverage. Contrast keyword tracking, which the template handles correctly: done in 2.3/2.5, verified once in 4.1. |
| D2a | **Fix-list overlap downstream of D2** | 2.1 and 2.2 | 2.2 states the boundary ("Roger/Samuel handle the GSC + AI-access fixes separately in 2.1"), but the boundary is drawn **by source tool, not by issue**. Broken links and redirect chains appear in both 1.2's and 1.3's output, so the same URL can legitimately land on both fix lists, worked twice by two people in the same week. Needs an issue-level rule, e.g. "if it appears on both, it belongs to 2.2 and 2.1 drops it." |

---

## Open Flags — logged, not yet analyzed

1. ~~**"1.4" title/description mismatch + self-reference.**~~ **RESOLVED 2026-08-10** — paste slip. The orphan description belongs to **2.1 Implement Technical Fixes From Week 1**, confirmed by the routing line in 1.2. No template defect. 1.4's real description still outstanding.
2. **Feeds vs Blocks divergence.** 1.1 names 5.1 but doesn't wire it; 1.2 names 1.8 but doesn't wire it. See the pattern note in the Dependency Ledger. Determines how much weight the dependency graph can carry in the final verdict.
3. **CONFIRMED — 1.4 → 1.6 order is not enforced.** 1.6 carries zero blockers. A zero-AI-visibility reading taken before the crawler-access check is a wrong diagnosis, and it propagates into 1.8 (target selection) and 3.4 (mention targets). Highest-severity graph finding so far.
4. **Review-gate cost on non-decision artifacts.** The blanket "every task ends at Ready for Janelle's Review" rule puts an approval gate between raw input tasks and the tasks consuming them (1.1 → 1.5/1.8/4.2). Raised at 1.1; hold for the structural verdict.
5. **Ownership conflict on 1.7.** Master rules assign it to Rahman directly; the task description assigns it to Roger with Rahman as conditional. 1.3 is consistent between the two, so 1.7 is the outlier. Cheap to fix, but it decides who picks the task up on deploy day. Check the same for 2.2, 4.4, Q4, Q7 as they arrive.
6. **External handoffs with no return path.** Two now: 1.7 → backlinks team, and 1.8 → content calendar. Nothing verifies receipt, and no task asks whether last month's routed items were ever worked. Contrast with 1.5, which explicitly measures last month's keyword work before/after. The template audits its own page-optimization loop but neither of the two loops it exports.
7. **CONFIRMED — 1.8 is gated on 4 of the 7 tasks it says it consumes.** Its own step 1 says "review the deliverables of 1.1–1.7" and step 6 requires 1.2, 1.3 and 1.4 outputs specifically, but only 1.1, 1.5, 1.6 and 1.7 are wired as blockers. The month's plan can therefore be locked while the three technical-diagnostic tasks are still open, turning step 6 into a no-op. **Highest-severity finding so far**, since 1.8 is the keystone and everything in Weeks 2–3 inherits from it. This also resolves open flag #2: the unwired edges were never about "soft vs hard," they are the three technical tasks missing from the keystone's blocker set.
8. **CONFIRMED — 2.5 is excluded from the cannibalization check.** 2.3 and 2.4 both block 4.3; 2.5 does not, despite retargeting up to 5 pages by front-loading query language into their titles. That is the intervention most likely to create query overlap, and all 5 pages come from the same 1.5 candidate pool as the refresh targets, so they are topically adjacent by construction. Fix: wire 2.5 → 4.3.
9. **Title character spec conflicts with the house standard, in two places.** 2.3 and 2.5 both say "≤60 chars" and neither addresses the brand suffix. Documented house rule is a 65-char budget for the page-specific portion with the suffix excluded, plus a no-repeated-token check. Systemic, not a one-off.
10. **REFINED after Q1 — 3.2 steps 2 and 3 duplicate quarterly work and lack data in the other two months.** The full crawl exists in **Q1**, quarterly. So 3.2's monthly orphan and depth checks have no data source two months in three, and in the third month they duplicate Q1's site-wide orphan pass. **Fix: strip both checks from 3.2 and leave them in Q1.** Do not add a monthly full crawl.
11. ~~**The four page-refresh tasks are the only execution work absent from the activity log.**~~ **DOWNGRADED after 4.5** — I was wrong. 4.5's step list explicitly collects "pages optimized (URLs)" and "titles/metas rewritten," so the refresh work does reach the log; it is pulled by the consumer rather than pushed by the producer. What remains is cosmetic: the Feeds lines under-describe the real graph, so an edge audit reaches a false conclusion. Real residue: **4.4 → 4.5 is a genuine same-week race** (4.5 compiles GBP actions, 4.4 is ungated and unwired), and **4.2's and 3.3's fixes are missing from the compile list**.
12. **3.3 is a fully disconnected node.** Zero wired edges in either direction, while its first step is explicitly scoped to "every page changed this month" — work owned by six other tasks. It can run before the changes exist or miss everything changed after it. The most clear-cut ordering defect in the template, because the step names its own dependency in plain text.
13. **Schema validated THREE times** (updated after 4.1). 2.3 SOP step 7 does it during the refresh; 3.3 step 1 verifies, ungated; 4.1 step 3 verifies again, correctly gated on all seven execution tasks. Only the third pass is reliably sequenced. The template already demonstrates the right shape with keyword tracking — done in 2.3/2.5, verified exactly once in 4.1 — so this is inconsistency rather than ignorance. Cutting 3.3 step 1 loses no coverage.
14. **2.5 missing from the master deploy note.** Master step 4 says "Task 1.8 populates the target-page tasks (2.3, 2.4, 3.1)." 2.5 is also blocked by 1.8 and also needs targets. Either the master list is stale or 2.5 is populated some other way.

---

## Analysis passes to run once status is COMPLETE

- [ ] **Orphans** — tasks whose deliverable feeds nothing downstream
- [ ] **Dangling inputs** — tasks consuming an output no task produces (4 found: 3.2 full crawl, 4.2 top-landing-pages list, 5.1 Google-update annotation, Q2 zero-click page list)
- [ ] **Dangling outputs** — tasks producing something no task consumes (1 found: Q3's refresh queue, which 1.5 never reads)
- [ ] **Metric-basis changes** — points where the definition of a reported metric shifts without the report knowing (1 found: Q3's quarterly prompt-set revision vs 1.6's SOV %)
- [ ] **Circular references** — (one already found under "1.4")
- [ ] **Duplicate coverage** — same work under two IDs in different weeks, including Quarterly Block and MASTER Repeated Tasks overlap
- [ ] **Cadence fit** — what in here is not genuinely monthly work (weekly-or-nothing, or quarterly at best)
- [ ] **Data-latency fit** — separate from cadence: which checks run before the data they need can possibly exist. First instance found at 4.3 (new-cannibalization detection in the same month the pages shipped). Re-check every task that measures the effect of this month's own work.
- [ ] **Blocking paths** — where a week can stall behind a review gate on a non-decision artifact
- [ ] **Feeds vs Blocks reconciliation** — every stated Feeds edge should exist as a wired dependency, or the description is lying about the graph
- [ ] **Threshold/trigger coverage** — which tasks say "review X" with no pass/fail condition, and therefore won't be run consistently or auditably
- [ ] **Failure paths** — which tasks have no branch for "the data source is unavailable" or "dev has no capacity"
- [ ] **Ownership boundaries** — where Roger/Samuel/Rahman scope overlaps without a written boundary
