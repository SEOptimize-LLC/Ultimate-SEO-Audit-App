---
description: Capture lessons from the current session and write them back into the right skill, rule, or memory file so the same mistake doesn't repeat next time. Use after completing an audit or after the user gives corrective feedback.
---

# /seo-retrospective

You are running an end-of-task retrospective. The goal is to extract durable lessons from this conversation and persist them so future sessions don't repeat the same mistakes.

## Step 1 — Identify the lessons

Re-read the current session's conversation. Look specifically for:

1. **Corrections** — moments where the user said "no", "wrong", "you missed X", "this is broken", or any explicit pushback
2. **Confirmations of non-obvious calls** — moments where you proposed an unusual approach and the user agreed without modification (these are validated judgment calls worth keeping)
3. **Assumption mistakes** — places where you assumed something without verifying (tech stack, data freshness, audit doc accuracy, page state) and were wrong
4. **Process gaps** — moments where the QA / verification layer SHOULD have caught a problem but didn't

For each lesson, write down:
- **What happened** (one sentence)
- **What you should have done differently**
- **Why** (the underlying principle)
- **How to apply it next time** (concrete trigger condition)

## Step 2 — Classify each lesson

For each lesson, decide where it belongs:

| Lesson type | Goes into |
|-------------|-----------|
| Corrects an assumption about a tech stack | `Skills/data-analysis/data-quality-audit/SKILL.md` Reference cases section |
| Corrects how to handle source disagreements | `Skills/data-analysis/metric-reconciliation/SKILL.md` Reference cases section |
| Corrects a delivery-time check that was missing | `Skills/data-analysis/pre-delivery-qa/SKILL.md` checklist |
| Corrects a CMS-specific instruction style | `Skills/data-analysis/data-quality-audit/SKILL.md` OR a new tech-stack-specific skill |
| User preference about deliverable format / tone | `~/.claude/projects/<project>/memory/feedback_*.md` (auto-memory) |
| Client-specific fact (founding year, profiles, services) | `~/.claude/projects/<project>/memory/project_<client>.md` (auto-memory) |
| Core methodology rule that applies project-wide | `.claude/rules/audit-workflow.md` or `.claude/rules/report-formatting.md` |
| Tool-decision rule (when to dispatch which subagent) | `CLAUDE.md` Specialized Skills section |
| Reusable code-level trick | A new skill, OR a comment in the relevant build script |

If a lesson doesn't fit cleanly, ask the user which file it should go into rather than guessing.

## Step 3 — Apply the changes

For each lesson:

1. **Read the target file** (Read tool)
2. **Edit the relevant section** — add the lesson as a "Reference case", checklist item, or rule
3. **Show the user the diff** — quote the before/after of what you're adding
4. **Get user confirmation** before saving — they may want to refine the wording

Format for adding a Reference case to a Skill:
```markdown
### <One-line title> (<date>)
- **What happened:** <one sentence>
- **What we should have done:** <one sentence>
- **Documented in:** <skill or rule that now codifies the fix>
```

Format for adding a checklist item to pre-delivery-qa:
```markdown
### CHECK N — <name> (added <date> from <session ref>)
<one paragraph: what to check, why, how to check>
```

## Step 4 — Cross-reference

After updating files, check whether the lesson should ALSO trigger updates to:
- `MEMORY.md` index (if a new memory file was created)
- `CLAUDE.md` (if a new subagent or skill was added that other agents need to know about)
- `audit-workflow.md` (if the lesson is a hard rule that must apply to all audits)

Update those too — and tell the user every file you modified at the end.

## Step 5 — Summarize the retrospective

End with a structured summary:

```
SEO Retrospective Summary — <date>
==================================

Lessons captured: <N>

1. <one-line title>
   → Added to <file>

2. <one-line title>
   → Added to <file>

3. <one-line title>
   → Added to <file>

Files updated:
- <file 1>
- <file 2>

Files created:
- <file 1>

Net effect: <one-sentence statement of how the next audit will be better because of these changes>
```

## What this command MUST NOT do

- Do not invent lessons that weren't actually evidenced in the conversation. If nothing was learned, say so and exit.
- Do not write changes without showing the diff and getting user confirmation.
- Do not capture the same lesson twice — check if the rule already exists before adding.
- Do not capture ephemeral conversation details (one-off task instructions, current status) — only durable lessons that apply to future sessions.
- Do not capture as a feedback rule something the user said once and might disagree with later. If unsure, ask.

## Anti-patterns to actively prevent

These are the patterns that have hurt audits in this project and should always trigger a lesson capture if observed:

1. **Assuming tech stack without fingerprinting** → triggers a check in pre-delivery-qa CHECK 1
2. **Trusting an audit doc's count without re-deriving** → triggers data-validator dispatch
3. **Proposing target URLs without live verification** → triggers live-url-verifier dispatch
4. **Shipping a finding that's already been silently fixed** → triggers live verification of high-sev findings
5. **Writing CMS-specific click-paths for the wrong CMS** → triggers fingerprint check before dashboard instructions
6. **Reading too much input data into main context** → triggers subagent dispatch for heavy data work

If any of these patterns appear in the current session, capture a reference case showing the specific incident.