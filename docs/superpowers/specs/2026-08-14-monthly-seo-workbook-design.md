# Monthly SEO Workbook — Execution Layer

**Date:** 2026-08-14
**Status:** Design, awaiting approval
**First client:** Superior

## The problem

The agency has adopted a monthly SEO template: 25 recurring ClickUp subtasks per
client per month, each writing its deliverable into one tab of a 21-tab Google
Sheet. Eight clients are live (Superior, SameDay, Cudio, Beehive, Comfort,
Education Walkthrough, Arsenal Health, Snow), so the steady state is roughly 200
task-instances a month.

The task *definitions* already exist and are complete, in
`Documents/Monthly-SEO-Task-Template.md`: Objective, Steps, Deliverable, Feeds,
Blocks, Blocked-by, Owner and Done-when for all 25 monthly tasks plus 7
quarterly. Nothing here duplicates them.

What is missing is the **execution layer**: for a given client and a given task,
which data source is queried with which parameters, how each cell is derived,
which exact range it lands in, and what must be true before the task is done.
That knowledge currently exists only inside a conversation, which means it
evaporates. This spec makes it durable.

**Success criterion:** next month, a session with no memory of this
conversation can run `/seo-subtask superior 1.1` and produce the same
deliverable to the same standard.

## Constraints established by testing

| Capability | Status |
|---|---|
| Read a client's Google Sheet | Works today via the Drive connector |
| Write cells via the Drive connector | **Not possible.** `update_file` alters file metadata only |
| Write cells via Sheets API + service account | Possible, needs `credentials/service-account-key.json` |
| Read ClickUp task definitions and post comments | Works, but the MCP returned server errors on 2 of 4 calls; needs a fallback |
| GSC, GA4, SEMrush, DataForSEO, Playwright | All connected and verified this session |

The workbook that matters is the **Google Sheet**, not the `.xlsx`. The xlsx is an
archive. Once Rahman, Samuel and Janelle are editing the Sheet, regenerating and
re-importing an xlsx would destroy their entries, so the import loop is not a
viable long-term path.

## Architecture

Six components. Each is independently useful and independently testable.

### 1. Client registry — `clients/registry.yaml`

One block per client holding every identifier a task might need, so no task
recipe ever hardcodes a client. This is the component that makes month two cheap.

```yaml
superior:
  name: Superior Water & Air
  domain: superiorwaterandair.com
  folder: Clients/Superior
  gsc_property: https://superiorwaterandair.com/
  ga4_property: properties/314969736
  sheet_id: 1uVDqUbPRpdFCgfn4IlsDDnwIdRpjwjdcBoh2LRH4jA0
  clickup_milestone: "86ak0e259"
  semrush_tag_pattern: "{mon}-{yyyy}"
  competitors: []          # filled at first 1.7 run
  is_local: true           # 4.4 GBP applies
  ecommerce: false         # 1.1 GA4 revenue row is N/A
```

Verified identifiers for all eight clients are in Appendix A, including five
ambiguities that need your decision rather than my guess.

### 2. Skill — `Skills/monthly-seo-workbook/SKILL.md`

The operating method, not the task list. Covers: how any task runs, the output
contract, the verification protocol, and the non-negotiables carried over from
the blueprint and the structural review:

- A clean pass is a valid deliverable. Monitoring tasks (1.2, 1.4, 4.1, 4.3)
  log "no action warranted" rather than being left blank.
- A row is done when it has a completion date. Never write a date for work that
  has not happened.
- Never fabricate a number. If a source is unreachable, the cell is left blank
  and the gap is reported, per `no-unverified-claims`.
- Client-facing output never carries DA scores, toxicity scores, raw exports,
  work-time figures or agency taglines.

### 3. Task recipes — `Skills/monthly-seo-workbook/tasks/<id>.md`

One file per task, added as we reach it. The machine-actionable layer:

- **Inputs** — exact MCP calls, parameters, date windows
- **Derivation** — how each cell is computed
- **Output contract** — tab, section, A1 range, exact column order
- **Gate** — what must be true to call it done (the blueprint's Done-when)
- **Automation class** — A, B or C (see below)
- **Known gaps** — cells that cannot be automated, and why

### 4. Command — `.claude/commands/seo-subtask.md`

`/seo-subtask <client> <task> [--month YYYY-MM] [--dry-run]`

**One subtask per invocation. There is no batch mode and no "run the month"
option, by design.** Tasks are run in whatever order the work actually demands,
which is often not numerical order: if 1.2 and 1.3 have no dependency between
them, either may run first.

Resolves the client from the registry, runs the **dependency gate** below, loads
the blueprint section plus the recipe, runs it, writes to the Sheet, verifies,
archives locally, and offers to post the ClickUp deliverable comment.
`--dry-run` produces the paste-ready block without writing.

#### The dependency gate

Before any task runs, its prerequisites are checked and **an unmet dependency
aborts the run**. The gate names what is missing and what to run first. It is
not a warning and cannot be skipped with a flag.

The graph is built from the blueprint's own `Blocked by` and `Blocks` lines,
taking the **union** of the ClickUp wiring and the written `Feeds` declarations
rather than either alone. This matters: the structural review found seven places
where a task's description declares a dependency that ClickUp does not enforce,
including the keystone 1.8, which reads seven Week 1 tasks while only four gate
it. Enforcing the union means this system holds the line ClickUp currently
does not.

A dependency counts as satisfied when its deliverable exists, established in
this order:

1. The month archive contains the task's output file.
2. Failing that, the task's tab in the Sheet contains data beyond the example
   row.
3. Failing that, it is unmet.

ClickUp status is deliberately *not* the test. A task can be marked complete
there without its deliverable existing, which is the failure mode the workbook's
own rule ("a tab with no data means the task is not done") exists to catch.

Worked example: `1.1` has no `Blocked by` line, so it runs freely. `1.8` is
blocked by all of `1.1` through `1.7` and will refuse until every one has a
deliverable.

### 5. Calibration — corrections captured into the recipes

The system is expected to be wrong at first. What matters is that it is wrong
**once** per issue rather than every month.

Every task recipe carries a `## Calibration` section that accumulates confirmed
decisions. It is written to at two moments:

- **On correction.** When a run produces something wrong and you say so, the
  correction is written into the recipe as a rule before moving on, along with
  the reason. Not "the number was wrong" but "GSC clicks must use complete
  calendar months when the month has closed, because that is what the client's
  report shows."
- **On approval.** When a run is right, whatever judgement made it right is
  written down too. Approval is the signal that gets missed, because the work
  landed and nothing feels broken, and then next month reproduces none of it.

Handling a correction **takes priority over continuing the task**. The rule is
captured first, then the work resumes, because a correction carried in
conversation is a correction lost at the end of the session.

Each entry records the date, what was wrong or confirmed, the rule now in force,
and any approach ruled out so it is not retried. A recipe whose Calibration
section is empty after several months is a recipe nobody is checking.

### 6. Month archive — `Clients/<Client>/Monthly SEO Workbook/<YYYY-MM>/<task>.md`

Not bureaucracy. The blueprint's chain is month-over-month: 1.5 needs last
month's optimizations, 4.3 needs last month's refreshed queries, 4.5's zero-delta
flag needs two months of history. The Sheet gets duplicated each month and
sessions end, so a local archive is the only durable source for that chain.

## Sheets write protocol

Every write follows the same four steps, and step 3 is the one that makes this
trustworthy:

0. **Confirm the layout.** Read the tab's header row and check it matches what
   the recipe expects before writing anything. Eight workbooks were created from
   one import, so they agree today, but a client sheet can drift once people edit
   it, and a stale range would write good data into the wrong cells. A layout
   mismatch aborts the run and reports rather than writing.
1. **Resolve the range** from the recipe's output contract. Only ranges listed
   there are writable. `4.5 Template Report` column C holds formulas and is on a
   permanent deny-list.
2. **Write** with `valueInputOption: USER_ENTERED`, so `2026-09-15` becomes a
   real date rather than text. Text dates would make the 4.5 counts silently read
   zero, which is the exact bug class already fixed once in this workbook.
3. **Read back and diff.** Re-read the range and compare against what was
   intended. A write is only reported as successful when the diff is clean. A
   mismatch is reported, never papered over.
4. **Archive** the same content to the month folder.

Dropdown columns only ever receive values from their own validation list. Tab
names containing spaces or `+` are quoted in A1 notation.

## Automation classes

Honest classification of where this actually saves time, across the 22 in-scope
tasks (25 monthly, less Week 5's three). **A** = I run it end-to-end. **B** = I
draft, you confirm. **C** = you or the team run it, I structure and QA the
output.

| Class | Tasks |
|---|---|
| **A** | 1.1 Data Snapshot · 1.4 AI Crawler Access · 4.3 Cannibalization |
| **B** | 1.2 Health Sweep · 1.3 Site Health Audit · 1.5 Candidate List · 1.6 AI Visibility · 1.7 Gap Analysis · 1.8 Lock Plan · 2.3/2.4/3.1 Refreshes · 2.5 Titles/Metas · 3.2 Internal Links · 3.3 Entity Consistency · 4.1 QA · 4.5 Report |
| **C** | 2.1 Technical Fixes (Samuel) · 2.2 Fix Sheet (Rahman) · 3.4 Mentions (outreach) · 4.2 Conversion Paths (form testing) · 4.4 GBP (no API access) |

Class B is the bulk, and that is the honest answer: most of these tasks need
judgment, and the value is a strong draft plus enforced consistency, not
unattended automation.

## First implementation: 1.1 Data Snapshot

Output contract, `1.1 Data Snapshot` tab:

| Section | Range | Content |
|---|---|---|
| Snapshot date | `B4` | Run date |
| A. Core metrics | `B8:E15` | 8 metric rows, this period / prior / YoY / notes |
| B. Position Tracking | `A19:F19` | Last month's tag row |
| C. Top landing pages | `A24:E33` | Top 10 by organic clicks |
| D. Anomalies | `A37:C40` | Drafted, you confirm |

Sources: GSC MCP for clicks, impressions, branded-query impressions and top
landing pages; analytics MCP for GA4 organic conversions and revenue; SEMrush
MCP for Position Tracking.

**Three cells I expect to flag rather than automate**, to be confirmed against
the live APIs during implementation rather than assumed now:

- **GSC Generative AI impressions** — a search-appearance filter that may not be
  exposed through the Search Analytics API.
- **GA4 ai-assistant channel sessions/conversions** — only exists where that
  custom channel group is configured on the property.
- **Anomaly flagging** — judgment. Drafted for confirmation.

Where a cell cannot be sourced, it stays blank and the gap is named in the run
report. It is never estimated.

## Out of scope

- Week 5 (5.1, 5.2, 5.3). Handled offline from the first four weeks' output.
- The Quarterly Block (Q1 to Q7). Separate system, separate cadence.
- Writing to ClickUp beyond posting a deliverable comment and setting status.
- Retrofitting the 230 existing workbooks in the repo to the brand font.

## Build order

1. Registry with all eight clients, ambiguities resolved
2. Skill skeleton
3. Sheets write module with read-back verification, tested against Superior on a
   scratch range before any real write
4. 1.1 recipe
5. `/seo-subtask` command
6. Run 1.1 for Superior end-to-end
7. Recipes 1.2 onward, one at a time

## Open questions

1. **Service account.** Needed before step 3. Sheets API enabled, JSON key at
   `credentials/service-account-key.json` (already gitignored), and the service
   account email given Editor on each workbook.
2. **Five registry ambiguities** in Appendix A.
3. **ClickUp comment posting** — automatic on task completion, or on request?

## Appendix A — verified identifiers

| Client | GSC property | GA4 property |
|---|---|---|
| Superior | `https://superiorwaterandair.com/` | `314969736` |
| SameDay | `https://samedayutah.com/` | `319451315` |
| Comfort | `https://www.comfortsolutionsutah.com/` | `371327071` ⚠ |
| Education Walkthrough | `https://educationwalkthrough.com/` | `304261130` |
| Cudio | `sc-domain:cudio.com` ⚠ | `404082865` |
| Beehive | `https://www.beehiveplumbing.com/` | `314808497` ⚠ |
| Arsenal Health | `https://www.arsenalhealth.com/` ⚠ | `359612721` |
| Snow | `sc-domain:trysnow.com` ⚠ | `402493455` ⚠ |

Sheet IDs are confirmed for all eight from Drive.

**Ambiguities requiring your decision:**

1. **Cudio** has both `sc-domain:cudio.com` and `https://www.cudio.com/`. The
   domain property is proposed as canonical.
2. **Snow** has both `sc-domain:trysnow.com` and `https://www.trysnow.com/`, and
   **nine** GA4 properties including two labelled "Test Property - DONT USE" and
   "JS Error Tracking Only". `402493455 trysnow.com - GA4` is proposed.
3. **Beehive** has three GA4 properties: Beehive Plumbing (`314808497`), Beehive
   Heating and Air Website (`264966827`), Beehive Heating and Air - GA4
   (`343116493`). Plumbing is proposed; confirm whether Heating and Air is a
   separate client engagement.
4. **Comfort** has two accounts: Comfort Solutions (`371327071`) and Comfort
   Solutions Fireplace (`400293742`). The business does both. Confirm whether the
   workbook covers one property or both.
5. **Arsenal Health** GSC access is `siteFullUser`, not `siteOwner`, and a
   separate `https://www.arsenalhealth.com/blog/` property exists. Confirm which
   is in scope, and whether the permission level blocks any GSC call.

None of these are guessed in the registry until you confirm them.
