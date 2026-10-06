# Ultimate SEO Auditor

## Overview

Streamlit-based SEO audit tool that analyzes Screaming Frog crawl exports and generates AI-powered optimization recommendations. Produces scored health reports with prioritized issues across technical SEO, on-page SEO, backlinks, and competitor analysis.

**Status:** v1 live, v2 rebuild paused (Workstream A). Active work on Traffic Loss Analysis skill (Workstream B).

## Tech Stack

- **Language:** Python 3.x
- **Framework:** Streamlit
- **APIs:** OpenRouter (LLM), DataForSEO (backlinks/competitors), Google Search Console, GA4
- **Data:** Pandas for Screaming Frog CSV/Excel parsing (55+ column mappings)

## Project Structure

```
app.py                 # Main Streamlit app
models/                # Data models (AuditResult, Severity)
utils/                 # File parser for Screaming Frog exports
auditors/              # Audit modules (technical, onpage, backlink, competitor)
services/              # API clients (DataForSEO, OpenRouter, report generator)
prompts/               # LLM prompt templates per audit category
fetchers/              # Data collection scripts (GSC, GA4, AI visibility)
Skills/                # SEO knowledge base & agent skill definitions
templates/             # Report templates (traffic loss, etc.)
Clients/               # Per-client data directories (gitignored)
```

## Commands

```bash
# Run the app
streamlit run app.py

# Fetch client data
python run_fetch.py --client <name> --gsc-property <url> --ga4-property <id>

# Run tests
pytest tests/
```

## Conventions

- Auditor modules inherit from `auditors/base_auditor.py`
- All API clients live in `services/` — never call APIs directly from auditors
- Screaming Frog column mapping is centralized in `utils/file_parser.py`
- LLM prompts live in `prompts/` — one file per audit category
- Client data stored in `Clients/<name>/data/` (gitignored, may contain PII)
- Environment variables via `.env` (see `.env.example`) or `.streamlit/secrets.toml`

## Expanded Input Stack (leak-grounded audit)

Each leak-grounded analysis ties to specific Google API leak attributes (May 2024). Drop these inputs into `Clients/<name>/data/`:

| # | File (suggested name)        | Source                        | Required? | Unlocks                                                                  |
|---|------------------------------|-------------------------------|-----------|--------------------------------------------------------------------------|
| 1 | `crawl_internal.csv`         | SF HTML Internal export       | YES       | Core technical + on-page audit; a body-text column also lets the local auditor count addresses and phone numbers per location page |
| 2 | `backlinks_semrush.csv`      | SEMrush backlink export       | No        | Backlink profile checks (DR bands, dofollow split, anchor patterns, velocity). `sourceType` tiers / `siteAuthority` proxy are LLM-prompt guidance only — the SEMrush export lacks those columns |
| 3 | `anchors_internal.csv`       | SF Bulk Export → All Anchor   | No        | `anchorMismatchDemotion`, `phraseAnchorSpamRate/Penalty/Demoted`; with #5, `onsiteProminence` (priority pages linked from click-earning pages) |
| 4 | `content_dates.csv`          | SF custom extraction          | No        | `semanticDate`, `lastSignificantUpdate`, `dateUnreliabilityInfo`         |
| 5 | `gsc_performance.csv`        | GSC Search Analytics export   | No        | Position-adjusted CTR, NavBoost click-signal grounding; with #3, `onsiteProminence` |
| 6 | `topical_map_koray.md`       | Koray semantic SEO output     | No        | `siteFocusScore`, `siteRadius`, topical-outlier detection                |
| 7 | `gsc_crawled_not_indexed.csv` | GSC Page Indexing report → "Crawled - currently not indexed" (Export button on that status's detail view) | No | Content-quality non-indexation diagnosis — cross-references word count on the flagged URLs from the SF crawl |
| 8 | `gsc_discovered_not_indexed.csv` | GSC Page Indexing report → "Discovered - currently not indexed" (Export button on that status's detail view) | No | Crawl-budget / internal-linking diagnosis — cross-references internal link counts on the flagged URLs from the SF crawl |

Inputs #7 and #8 come from GSC's **Page indexing** report (Indexing → Pages in the Search Console left nav). Google has no bulk Index Coverage API, so — like the Koray topical map (#6) — these must be exported manually from the GSC UI, one status category per file, via the Export button on that status's detail view. Without these two inputs, the auditor is structurally blind to Google's own "Crawled — currently not indexed" and "Discovered — currently not indexed" judgments, since pure Screaming Frog crawl data can never reveal them — those are Google's own crawl/index decisions, not something visible in page source or HTTP status codes.

**Inputs #7/#8 are snapshots that lag URL Inspection — re-verify before diagnosing.** The Page indexing report routinely lists URLs that are already indexed by the time the export is read (report lag, not de-indexing). Before an audit consumes these files, run `python scripts/verify_gsc_exports.py <client>` — it fetches the current URL Inspection verdict for every export row and writes `Clients/<name>/data/gsc_export_verification.json`. The technical auditor picks that file up (via `load_audit_context`'s `gsc_export_verification_file` / the `gsc_export_verification` constructor param) and drops rows Google has since indexed; without it, the Crawled/Discovered-not-indexed findings carry an explicit unverified-snapshot caveat. Successive runs also build the report-accuracy trend (% of the bucket actually indexed): steady = lag noise, falling = genuine de-indexing. Full mechanics in `Skills/technical-seo-agent/references/gsc-indexation-states.md`. To monitor specific URLs under remediation month over month, use `python scripts/index_watchlist.py <client>` (watch set from a `watchlist:` key in `clients/registry.yaml` or `--urls-file`; state history accumulates next to the monthly `index_audit.json` caches).

The Streamlit app surfaces all eight slots in the upload panel and shows which leak-grounded analyses each input combination unlocks. Each input is optional (except #1) — the audit degrades gracefully and flags which analyses cannot run.

For the deep mechanics on each attribute, see `Skills/technical-seo-agent/references/seo-fundamentals-2026.md` and `Skills/technical-seo-agent/references/click-signals-abc-framework.md`.

## Critical Rules

- Never commit client data or credentials — `Clients/*/data/` and `.env` are gitignored
- DataForSEO integration uses direct REST API (not MCP) for Streamlit Cloud compatibility
- OpenRouter is the LLM gateway — supports model switching without code changes
- Screaming Frog exports vary wildly — always use the column mapping in `file_parser.py`, never hardcode column names
- Skills/ contains SEO knowledge used to build LLM prompts — changes here affect audit quality

## Audit Workflow Rules (Mandatory)

Before producing any client deliverable, all rules in [.claude/rules/audit-workflow.md](.claude/rules/audit-workflow.md) apply. Two rules deserve special emphasis because they catch errors that propagate directly into client implementations:

- **Rule 11** — Live verification for high-severity findings (content duplication, 404s on revenue pages, indexation failures)
- **Rule 12** — Verify every proposed target URL (redirect targets, canonical targets, link replacements) against the live site BEFORE publishing — regardless of severity, regardless of source. Reference case: Superior Water & Air Nov 24, 2025 GSC audit redirect corrections. A wrong target URL becomes a 301-cemented mistake the moment the developer implements it.

## Specialized Skills

When the user requests one of the following deliverables, invoke the matching skill:

- **`llms.txt` / `llms-full.txt` generation, audit, or fix** → use [Skills/llms-txt-builder/SKILL.md](Skills/llms-txt-builder/SKILL.md). Enforces Answer.AI spec compliance, curation rules, marketing-language blacklist, and the 2026 evidence base on what `llms.txt` does and doesn't do (research summary in `Skills/llms-txt-builder/references/llms-txt-best-practices-2026.md`).

- **Single-URL content expansion ("what should I add to this page?")** → use [Skills/content-expansion/SKILL.md](Skills/content-expansion/SKILL.md), typically via the `/page-content-expansion` slash command. Takes ONE URL, pulls its GSC query mix, classifies queries by intent + position, runs the expansion-vs-cannibalization gate, and produces a ranked deliverable (intra-page additions, new-page candidates, internal-link suggestions, semantic entities to surface). Use when a client asks "what should I add to this page?" or when an audit surfaces a single URL with strong impression volume and weak CTR (e.g., the Cudio `/services/odoo-migration` position-2.7 / 0.49% CTR case).

- **Monthly SEO workbook** → read [Skills/monthly-seo-workbook/REASONING.md](Skills/monthly-seo-workbook/REASONING.md) first (it outranks every task recipe), then the recipe for the task in [Skills/monthly-seo-workbook/tasks/](Skills/monthly-seo-workbook/tasks/) (1.x, 2.x and 4.x). Credentials and auth fixes are in [SETUP.md](Skills/monthly-seo-workbook/SETUP.md). Per-client monthly tasks, run one task at a time on request; not part of the full-site audit.
- **Competitor identification** → [Skills/competitor-identification/AGENT-PROMPT.md](Skills/competitor-identification/AGENT-PROMPT.md) is a self-contained agent prompt: fill in its parameters block and hand it to one agent per client.

## Data Analysis Infrastructure

A second layer of skills + subagents wraps around the SEO domain skills above. They handle data quality, verification, and pre-delivery QA — domain-agnostic infrastructure that every audit benefits from. This layer prevents mistakes the SEO skills can't catch on their own (wrong tech-stack assumptions, stale audit data, unverified target URLs, fabricated counts).

### Process skills vs site-variable skills (deliberate distinction)

The `data-analysis/*` skills below are **process skills**: they operate on the audit, not on
the website. They validate inputs, reconcile conflicting sources, track assumptions, and gate
delivery. **They carry no pipeline-stage assignment, deliberately**, because they do not
produce findings about a client's site.

Every skill that *does* produce site findings carries a "Pipeline stage assignment" block
mapping it to `CRAWLABILITY → RENDERING → INDEXABILITY → RANKING`. That distinction is what
keeps the count honest: QA steps are not audit variables, and they must never be sorted
alongside them in a prioritised deliverable.

### Always-on infrastructure skills

- **[Skills/data-analysis/data-quality-audit/SKILL.md](Skills/data-analysis/data-quality-audit/SKILL.md)** — Validates SEO input files (SF exports, GSC, GA4) at intake. Triggered when new data arrives in a client folder OR an audit is requested. Catches missing columns, stale data, row-count mismatches before analysis runs.
- **[Skills/data-analysis/metric-reconciliation/SKILL.md](Skills/data-analysis/metric-reconciliation/SKILL.md)** — Forces explicit reconciliation when two sources disagree on the same number. Defines the source-of-truth hierarchy (live HTML > GSC > current SF > older SF > prior audit doc).
- **[Skills/data-analysis/pre-delivery-qa/SKILL.md](Skills/data-analysis/pre-delivery-qa/SKILL.md)** — Mandatory 14-check QA pass before any client deliverable ships. Required dispatches: `tech-stack-fingerprint` (CHECK 1), `data-validator` (CHECK 2), `live-url-verifier` (CHECK 3). Triggered automatically when about to write any file under `Clients/<name>/Full SEO Audit/`.
- **[Skills/data-analysis/assumptions-log/SKILL.md](Skills/data-analysis/assumptions-log/SKILL.md)** — Tracks unverified assumptions per client in `Clients/<name>/assumptions_log.md`. Surfaces them in deliverables instead of hiding them.

### Subagents (dispatched for isolated heavy lifts)

Live in `.claude/agents/`. Dispatch via the Agent tool. Each runs in its own context window so heavy data work doesn't pollute the main audit context.

- **[`tech-stack-fingerprint`](.claude/agents/tech-stack-fingerprint.md)** — Detects CMS, page builder, theme, schema, analytics, hosting from the homepage HTML. Saves `Clients/<name>/site_fingerprint.json`. Run once per client at onboarding; refresh every 30 days. Backed by `scripts/fingerprint_site.py`.
- **[`live-url-verifier`](.claude/agents/live-url-verifier.md)** — Verifies a list of proposed URLs against the live site. Returns PASS/WARN/FAIL per URL. Mandatory before shipping any deliverable that proposes redirect targets, canonical targets, or "link to X" replacements (enforces Rule 12). Backed by `scripts/verify_urls.py`.
- **[`data-validator`](.claude/agents/data-validator.md)** — Independently re-derives every cited number in a draft deliverable from the source data files. Returns MATCH / MISMATCH / CANNOT VERIFY per claim. Mandatory before shipping any deliverable that cites specific counts.

### Slash commands

- **`/seo-retrospective`** — End-of-task lesson capture. Re-reads the session, identifies corrections + assumption mistakes, writes them into the right skill / rule / memory file. Run after the user gives corrective feedback or after completing a multi-step audit. Defined in [.claude/commands/seo-retrospective.md](.claude/commands/seo-retrospective.md).

- **`/page-content-expansion`** — Single-URL content-expansion analysis. User provides ONE target URL (and optionally a GSC property and client folder); the command runs a 6-step workflow: validate the URL, pull GSC query data, classify queries by intent and position, run the expansion-vs-cannibalization gate, group surviving queries into clusters and apply the expansion-vs-new-page decision logic, and surface semantic entities + internal link candidates. Produces a 6-section deliverable (page snapshot, intra-page additions, new-page candidates, internal links to add, cannibalization risks flagged, methodology footer) with full required-fields format per `.claude/rules/audit-workflow.md`. Defined in [.claude/commands/page-content-expansion.md](.claude/commands/page-content-expansion.md); methodology in [Skills/content-expansion/SKILL.md](Skills/content-expansion/SKILL.md).

- **`/discover-audit`** — **Standalone** Google Discover eligibility audit, run separately from the full-site SEO audit. Google Discover is the personalised content feed that surfaces content *outside a query* — a distinct traffic channel with its own GSC report, invisible to a standard SERP audit. Takes a Screaming Frog crawl export (and optionally a GSC Discover Performance export) and scores Discover-eligibility signals: informational/editorial vs commercial content, non-clickbait titles matched to content, author E-E-A-T, large high-quality lead images not preview-restricted (`max-image-preview:large`), mobile-first + CWV, and current/trending topic demand. Every finding ships as "raises/lowers Discover probability" (inclusion is non-deterministic — never pass/fail). Defined in [.claude/commands/discover-audit.md](.claude/commands/discover-audit.md), backed by [run_discover_audit.py](run_discover_audit.py) + [auditors/discover_auditor.py](auditors/discover_auditor.py); signal reference in [Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md](Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md) (Cluster 20) and `Skills/ai-search-optimization/references/google-discover.md`. **Intentionally NOT part of the default full-site audit** — invoke it only on explicit request, and only for sites with a content/editorial library (skip it for purely transactional sites rather than manufacturing a finding).

- **`/forum-reply`** — Turns a pasted forum thread (title + OP + optional comments) into a single copy/paste-ready reply. Platform agnostic. Exactly one reply target per run: either the OP or one non-OP comment. Enforces a conversational tone contract, a readability-first format contract (answer first, then mechanism, then actions, then caveat), a no-fabrication gate routed to the matching project SEO skill, and the `scripts/scrub_ai_tells.py` check. Fires `AskUserQuestion` when the target is ambiguous or the answer forks on a fact the thread omits. Defined in [.claude/commands/forum-reply.md](.claude/commands/forum-reply.md). Not an audit workflow — do not route client deliverables through it.

- **`/generate-redirect-map`** — Candidate redirect map generation at the START of a migration or restructure. Takes an old URL list (SF crawl or GSC export) and a new URL list (staging crawl or sitemap URL), runs [scripts/generate_redirect_map.py](scripts/generate_redirect_map.py) through staged matching: same-path, unique slug, structural token similarity, then optional OpenRouter-embedding semantic matching for the tail (reuses the semantic_site_map embedder + cache). Output is confidence-scored candidates plus a STRANDED review queue — never a homepage fallback (bulk redirects-to-home read as soft 404s). Output is Rule 12 upstream material: every target gets verified before any deliverable is drafted, and `/validate-redirects` closes the loop after implementation. Defined in [.claude/commands/generate-redirect-map.md](.claude/commands/generate-redirect-map.md).

- **`/validate-redirects`** — Post-implementation redirect map validation (enforces Rule 12f). Takes a redirect map CSV path or a client name (auto-discovers `*redirect*.csv` / `*rankmath*.csv` / `*migration*.csv` in the client folder), runs [scripts/validate_redirect_map.py](scripts/validate_redirect_map.py), and reports PASS/WARN/FAIL per row on whether each source URL actually lands on its approved target on the live site. Trailing-slash and http→https differences count as matches by default, and hops that only normalize scheme/slash/www don't trigger chain warnings. Retries transient timeouts/5xx before reporting them. Complements `verify_urls.py` (pre-ship target verification) — this one runs AFTER the developer or VA reports the map deployed. Defined in [.claude/commands/validate-redirects.md](.claude/commands/validate-redirects.md).

### How the layers fit together

```text
USER REQUEST: "Run the technical audit for SameDay"
       ↓
[data-quality-audit skill] validates SF/GSC/etc. files at intake
       ↓
[tech-stack-fingerprint subagent] writes site_fingerprint.json (if missing or stale)
       ↓
[assumptions-log skill] records load-bearing assumptions in Clients/<name>/assumptions_log.md
       ↓
[SEO domain skill: technical-seo-agent] performs the actual SEO analysis
       ↓
[metric-reconciliation skill] forces explicit reconciliation if sources disagree
       ↓
DRAFT DELIVERABLE
       ↓
[pre-delivery-qa skill] runs 14-check pass
       ├── dispatches data-validator (CHECK 2 — numbers traceable?)
       ├── dispatches live-url-verifier (CHECK 3 — proposed URLs work?)
       └── checks fingerprint match (CHECK 1 — instructions match real CMS?)
       ↓
SHIP / BLOCK
       ↓
(If user gives corrective feedback) → /seo-retrospective writes lessons back into skills
```
