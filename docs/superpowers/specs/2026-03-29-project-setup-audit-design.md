# Design: /project-setup Upgrade + /project-audit Command

**Date:** 2026-03-29
**Status:** Approved → Implemented
**Scope:** Two global commands + 6 global Anthropic pattern rule files + updated CLAUDE.md template + project-specific skill scaffolding

---

## Problem

The existing `/project-setup` command creates reasonable scaffolding but:
- Generates verbose CLAUDE.md files that duplicate global rules
- Doesn't install the universal AI instruction patterns extracted from Anthropic's own system prompts
- No way to audit/optimize existing projects against best practices
- Missing the `.claude/` anatomy (rules/, commands/, skills/, agents/) that the community consensus recommends

## Solution

### Architecture

```
~/.claude/
├── commands/
│   ├── project-setup.md        ← UPGRADED
│   └── project-audit.md        ← NEW
├── rules/
│   ├── common/                 ← existing ECC (untouched)
│   └── anthropic-patterns/     ← NEW — 6 universal AI instruction rules
│       ├── instruction-architecture.md
│       ├── tool-decisions.md
│       ├── quality-gates.md
│       ├── output-formatting.md
│       ├── error-handling.md
│       └── guardrails.md
└── templates/
    └── project-setup/
        └── CLAUDE.md.template  ← UPGRADED — lean, project-focused
```

### Design Decisions

1. **Hybrid approach** — CLAUDE.md holds project-specific content only. Universal Anthropic patterns live in `~/.claude/rules/anthropic-patterns/` as modular rule files.
2. **Global defaults, project overrides** — Anthropic rules installed once globally. Projects can override with local `.claude/rules/` files when needed.
3. **Report + offer to fix** — `/project-audit` shows scored report, then asks "Want me to fix?" one time. Not per-issue.

---

## Component 1: Anthropic Pattern Rule Files

Six rule files derived from Anthropic's system prompts (Claude Opus 4.6, Sonnet 4.5, Claude Code, UserStyle Modes):

| File | Content |
|------|---------|
| instruction-architecture.md | 6-block modular design: Role → Tool Decisions → Quality Gates → Output Formatting → Error Handling → Guardrails |
| tool-decisions.md | Conditional IF/THEN decision trees, priority ordering, pre-tool verification |
| quality-gates.md | 4-stage verification: pre-check → execute → post-verify → fallback |
| output-formatting.md | Minimal-first defaults, length calibration, 3 communication modes |
| error-handling.md | Graduated responses, honest accountability, graceful degradation |
| guardrails.md | Input validation, secret management, verify-before-recommend, continuous monitoring |

---

## Component 2: /project-setup (Upgraded)

### Phase Changes from Current

| Phase | Current | Upgraded |
|-------|---------|----------|
| 1. Discovery | 5 questions | +1: "Who is the audience?" |
| 2. CLAUDE.md | Generic template with global rules mixed in | Lean template — project-specific only, < 200 lines |
| 3. Structure | Basic src/ layout | Full .claude/ anatomy + docs/ |
| 4. Settings | Permissions only | + .gitignore entries for local files |
| 5. Agents | Standard trio | Same |
| 6. Skills | Domain matching | Same |
| 7. Git | Basic init | + .env.example |
| 8. Validation | Smoke test | + verify global Anthropic rules installed |

### New CLAUDE.md Template (Lean)

Sections: Overview, Tech Stack, Commands, Conventions (project-specific only), Critical Rules (project-specific only), Tool Decision Overrides (only if deviating from global), Current Phase.

No duplicating security rules, naming conventions, or formatting preferences that live in global rules.

---

## Component 3: /project-audit

### Scoring Categories (31 points total)

**1. Structure Check (/8)**
- .claude/ directory, settings.json, rules/, commands/, docs/, .gitignore entries, README.md, .env.example

**2. CLAUDE.md Quality (/8)**
- Exists, under 200 lines, has required sections, no anti-patterns (bloat, duplication, hardcoded values, generic filler)

**3. Rules Coverage (/6)**
- Global common/ rules exist, global anthropic-patterns/ exist, no conflicts, proper naming, no duplication between CLAUDE.md and rules

**4. Anthropic Patterns Compliance (/6)**
- All 6 pattern files installed globally

**5. Commands & Agents (/3)**
- Project-specific command exists, agents directory for medium+ projects, references project context

### Audit Flow

1. Run all 5 scoring categories
2. Display scored report with PASS/WARN/FAIL per item
3. Show total score out of 31
4. Ask: "Want me to fix these issues?"
5. If yes → auto-fix FAIL items, flag WARN items for review

---

## Component 4: Project-Specific Skill Scaffolding (Added Post-Design)

During Phase 1 of `/project-setup`, the user is asked to identify 2-5 core repeatable workflows. Each workflow gets a dedicated SKILL.md scaffolded in `.claude/skills/{workflow-slug}/SKILL.md`.

### Two-Layer Framework

**Layer 1 (Global):** Universal structure — Anthropic pattern rules, CLAUDE.md template, `.claude/` anatomy standard, `/project-setup` and `/project-audit` commands. Same for every project.

**Layer 2 (Project):** Tailored content — CLAUDE.md filled with this project's specifics, skills for this project's workflows, agents for this project's domain, commands for this project's operations, tool decision trees for this project's data sources.

### SKILL.md Structure

Each project skill contains:
- Name and description (for trigger accuracy)
- Tool Decision Tree (project-specific IF/THEN for which APIs to use)
- Process steps (step-by-step workflow)
- Quality Gates (what to verify before delivering)
- Output Format (how results should be structured)
- Error Handling (fallbacks specific to this workflow)

### Audit Integration

`/project-audit` Category 5 checks whether project skills exist and have proper structure. Simple projects get automatic PASS (they use global skills only).

---

## Sources

Patterns extracted from:
- Anthropic system prompts: Claude Opus 4.6, Claude 4, Sonnet 4.5, Claude Code, UserStyle Modes
- Community: Brij Kishore Pandey infographics (2 versions), Analytics Vidhya architecture guide, "Anatomy of .claude/ folder" reference, Reddit r/ClaudeAI discussions, UX Planet best practices
- Existing: ECC rules, current /project-setup command, CLAUDE.md template
