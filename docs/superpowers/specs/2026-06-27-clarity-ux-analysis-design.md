# Microsoft Clarity UX Analysis & Reporting — Design Spec

**Date:** 2026-06-27
**Status:** Approved design — pending implementation plan
**Author:** SEOptimize (with Claude)

---

## 1. Context & Problem

The original request was to "integrate Microsoft Clarity via API so we can fetch any and all required data" for analysis and reporting. Investigation of the [Clarity Data Export API](https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-data-export-api) showed it is **unfit for that purpose**:

- `numOfDays` accepts only `1`, `2`, or `3` — **no historical range, no 30/60/90-day option** (the 30/90-day filter exists only in the dashboard UI, not the API).
- Max **10 requests per project per day**, max **1,000 rows**, no pagination, max 3 dimensions.
- Returns **aggregate metrics only** — **no heatmap overlays, no session recordings, no click coordinates**. You get "page X had N rage clicks," never *where*.

**Decision:** abandon the API. Instead, the user exports heatmap data manually from the Clarity dashboard (which supports 30/90-day ranges and the full heatmap suite), and this project builds the **ingestion + analysis + reporting layer** on top of those exports.

This produces both an **internal** (technical/CRO) report and a **client-facing** (formal, business-impact) report from Clarity Click, Scroll, and Attention exports.

## 2. Ground Truth — Real Export Format

Verified against real exports in `Clients/Beehive/Clarity/` (homepage, last 30 days, PC):

Each file is a **per-page, per-device, per-metric** export. Filenames encode everything:
`Clarity_<Project>_<Metric>[-_]<Device>_<MM-DD-YYYY HH MM AM/PM>.(csv|png)`
(Note: metric/device separator is inconsistent — `Attention-PC.png` but `Attention_PC.csv`. Parser must accept both.)

CSV structure = a **metadata preamble** (quoted key/value rows), a blank-line gap, then a **data table** with its own header:

- **Click CSV** — preamble adds `Total clicks`; table = `Rank, Button (full CSS selector), Clicks, % of clicks`. Beehive homepage: 83 elements, of which **7 are `wp-admin-bar` rows** (logged-in owner = noise to exclude).
- **Scroll CSV** — table = `Scroll depth (5–100), No. of visitors, % drop off`. Beehive: 60.6% never pass 5% depth; only 4.2% reach 100%.
- **Attention CSV** — table = `Scroll depth, Avg time spent (HH:MM:SS), % of session length`. Beehive: 34% of session in first 5%, secondary spike at 90–95%.
- **PNG heatmaps** (Scroll, Attention) — interpreted visually by the analyst, not parsed.

Selectors are **Elementor/WordPress** (confirms Beehive's stack), enabling region + widget-type + interactivity inference.

## 3. Approach (chosen: A)

Skill-driven analysis + Python normalizer + slash command — matching how `semantic-map`, `content-expansion`, and `traffic-loss-analysis` already work in this repo. Deterministic parsing in code; heatmap-image interpretation and UX judgment with the analyst, governed by an enforced methodology skill.

Rejected: (B) fully-automated LLM pipeline — over-engineered, weak on image interpretation, riskier auto-written recs; (C) parser-only — no repeatable methodology or report structure.

## 4. Architecture & Components

| Component | Path | Responsibility |
|---|---|---|
| Normalizer | `utils/clarity_parser.py` | Parse 3 CSV shapes + filename/preamble metadata; humanize CSS selectors; filter & reconcile noise; compute metrics |
| Methodology skill | `Skills/clarity-ux-analysis/SKILL.md` (+ `references/`) | Interpretation frameworks; CSV-vs-dashboard capability boundary; ICE + mandatory-field recs; both report structures; QA checklist |
| Slash command | `.claude/commands/clarity-report.md` | Entry point: discover → normalize → interpret PNGs → optional GA4 → write reports |
| Tests | `tests/test_clarity_parser.py` | Unit tests on trimmed in-repo fixtures |

**Data flow:**
```
Clients/<name>/Clarity/*.csv + *.png
  → clarity_parser.py (discover, group by page+device+metric, normalize, compute)
  → analyst reads PNG heatmaps + applies clarity-ux-analysis skill
  → optional: GA4 conversion data (fetch_ga4 / GA4 MCP) when revenue numbers requested
  → Internal report + Client report → Clients/<name>/Clarity/reports/
```

## 5. Normalizer — Data Contracts (`utils/clarity_parser.py`)

Frozen dataclasses (PEP 8, type-annotated, immutable per project style):

- `ClarityMeta` — project, date_range_start/end, url_regex, page_views, total_clicks (optional), device, metric, source_file.
- `ScrollProfile` — `rows[(depth, visitors, pct_dropoff)]` + computed: pct reaching 25/50/75/100, `attention_cliff_depth` (where cumulative drop-off crosses 50%), steepest-drop band.
- `AttentionProfile` — `rows[(depth, avg_seconds, pct_session)]` + computed: above-vs-below-fold split, top attention bands, secondary-spike (false-floor) detection.
- `ClickProfile` — `elements[ClickElement]` + computed: region distribution (header/main/footer %), head-vs-tail concentration, dead-click-candidate list, admin-noise (count + clicks excluded, reconciled to totals).
- `ClickElement` — rank, raw_selector, clicks, pct_clicks + humanized: region, component_type, interactivity, label, is_admin_noise, is_dead_click_candidate.

Key functions: `discover_clarity_files()`, `parse_clarity_csv()`, `humanize_selector()`, per-metric `compute_*` helpers, `parse_time_to_seconds()`, and a top-level `normalize(client)` that returns grouped profiles and optionally dumps normalized JSON to `Clients/<name>/Clarity/_normalized/`.

**Selector humanizer logic:**
- Region: `HEADER.elementor-location-header` → Header; `FOOTER.elementor-location-footer` → Footer; `#wp-admin-bar` → Admin bar (noise); `#main`/`.page-content` → Main.
- Component: last meaningful `elementor-widget-*` class or terminal tag (nav-menu, button, social-icons, image-carousel, form, heading, background-overlay, swiper arrow, sub-arrow).
- Interactivity: terminal `A`/`BUTTON`/`INPUT` = interactive; `SECTION`/`DIV.*background-overlay`/`Hx`/non-button `SPAN`/`IMG` = non-interactive → **dead-click candidate**.

**Robustness:** custom line-based parse (not raw `pandas.read_csv` — the preamble breaks it); detect metric from the `Metric` row with filename fallback; accept both `-`/`_` separators; UTF-8/Latin-1 tolerance per `file_parser.py` philosophy.

## 6. Analysis Methodology (`Skills/clarity-ux-analysis/SKILL.md`)

Encodes a **CSV-grounded** adaptation of the two supplied guides (curated into `references/`). Core elements kept from the guides:

- Three-heatmap interpretation frameworks (Click/Scroll/Attention) mapped to the actual CSV columns.
- Friction-signal taxonomies with severity; attention-click correlation; attention-cliff / false-bottom concepts.
- ICE prioritization (Impact × Confidence × Ease) + traffic weighting + revenue-throughput tie-break.
- Scenario-diagnostics matrices; recommendation-by-page-type; Four-Pillars / Dual-Audience framing.
- Behavioral health benchmarks (sample ≥~1,000 users; rage <2%; scroll depth >65%; dead-click <3%) as confidence gates.
- Guide-2 technical boundaries (100k pageviews/heatmap; body-only scroll; 65,535px cap; dynamic/hover elements invisible to static PNGs; 13-month retention) as data-quality caveats.
- **Async dead-click misclassification check** before any dead-click claim.

### 6.1 CSV-vs-Dashboard capability boundary (mandatory section)

Because only **All-Clicks + Scroll + Attention** are exported, the skill states explicitly what is provable vs. inferred:

- **Provable from CSV:** scroll reach/cliff, attention distribution, ranked element clicks, region split.
- **Inferred only (must be labeled, flagged for verification):** dead-click *candidates* (from selector interactivity). Not Clarity-confirmed dead clicks.
- **Not available (must not be presented as run):** Dead/Rage/First/Last-click maps, session recordings, conversion/area maps, GA4-linked revenue.

Parser is shaped so genuine Dead/Rage CSVs (same export format) can be added later with no rework.

## 7. Reporting

Both reports: **no timeline/calendar language** (logical sequencing only), **≤6-column tables**, **full URLs never truncated**, **no internal-doc references**.

- **Internal report** — full element tables, dead-click candidates, ICE-scored backlog, cross-metric findings, data-quality notes, methodology.
- **Client report** — Four-Pillars framing; "What's working" + top 3 opportunities; plain language; **real GA4 numbers only** (no conversion data → qualitative, no invented figures).

Every recommendation carries **ICE score + mandatory fields** per `.claude/rules/audit-workflow.md`: Priority (P0–P4), Effort, Expected outcome (Ranking Lever | Infrastructure Hygiene | Risk Mitigation | UX-indirect; UX/conversion framing for Clarity), Likely effect, Validation method.

Output → `Clients/<name>/Clarity/reports/` (e.g. `clarity_ux_internal_<page-slug>_<device>.md`, `clarity_ux_client_<page-slug>_<device>.md`).

## 8. Slash Command (`.claude/commands/clarity-report.md`)

Modeled on `page-content-expansion.md`. Inputs: client folder name (required); optional page/device filter, `--with-ga4` (revenue), report type (internal|client|both). Pre-flight discovers files, prints sample sizes + data-quality caveats, and stops if neither Scroll nor Click is present. Workflow: normalize → read PNGs → apply skill → optional GA4 pull → write reports → pre-delivery QA.

## 9. Quality Gates

- Pre-flight sample-size + data-quality report before analysis.
- Pre-delivery QA via existing `Skills/data-analysis/pre-delivery-qa/SKILL.md`, dispatching: `data-validator` (every cited number), `recommendation-sanity-checker` (proposed copy/CTA rewrites), `live-url-verifier` (any rec naming a target URL).
- No-unverified-claims: dead-click candidates labeled inferred; revenue only from real GA4; admin noise reconciled to totals.

## 10. Testing (`tests/test_clarity_parser.py`)

Fixtures: trimmed copies of the three Beehive CSVs committed under `tests/fixtures/clarity/` (Clients/ is gitignored). Cover: filename parsing (both separators), preamble extraction per metric, table parsing, time→seconds, selector humanization (nav / button / background-overlay / admin-bar), admin-noise reconciliation, scroll/attention/click computed metrics, graceful degradation when a metric file is missing.

## 11. Scope Boundaries (YAGNI)

Out of scope: the Data Export API; the daily-accumulator snapshot store; the fully-automated LLM report pipeline (approach B); Dead/Rage/conversion-map ingestion (user chose the 3 CSVs); live-DOM selector resolution via Playwright (noted as a future enhancement, not v1).

## 12. Decisions Log

1. **Data source:** manual dashboard exports, not the API (API can't do 30 days or heatmaps).
2. **Build:** Approach A (skill + normalizer + command).
3. **Click data scope:** 3 CSVs only (All-Clicks + Scroll + Attention); infer/label dead-click candidates.
4. **Revenue framing:** real GA4 conversion numbers only; otherwise qualitative.
5. **Prioritization:** ICE score + the project's mandatory recommendation fields.
6. **Reports location:** `Clients/<name>/Clarity/reports/`.
