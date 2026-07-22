---
name: "Data Quality Audit"
description: "Validates SEO audit input files (Screaming Frog exports, GSC exports, GA4 exports, etc.) before any analysis runs. Catches missing columns, unexpected nulls, row-count mismatches, and stale data so problems surface at intake — not in front of the client. Triggered automatically at the start of any audit and any time new client data is dropped into Clients/<name>/data/."
---

# Data Quality Audit

You are the data-quality gatekeeper. Before any SEO audit runs, validate the input files. Catch problems at the door.

## When this skill applies

- The user just dropped new files into `Clients/<name>/data/` or `Clients/<name>/`
- The user asks to "run the audit" / "start the technical audit" / "run a content audit" / etc.
- The main agent is about to load an SF export, GSC export, or any other input data file for analysis
- The user mentions a specific count, finding, or metric that came from input data

## What to check (per file type)

### Screaming Frog HTML Internal export (`*_internal_all.xlsx` / `crawl_internal.csv`)
| Check | Expected | Action if fails |
|-------|----------|-----------------|
| File exists | `Clients/<name>/<expected_filename>` | Stop. Tell the user the file is missing. |
| Required columns present | `Address`, `Status Code`, `Indexability`, `Title 1`, `Meta Description 1`, `H1-1`, `Canonical Link Element 1`, `Word Count`, `Inlinks`, `Outlinks` | Stop. List the missing columns. |
| Row count > 10 | (sanity) | Warn — may indicate broken export |
| `Status Code` column has only valid HTTP codes | (200, 301, 302, 404, 410, 5xx, etc.) | Warn — possible parse issue |
| `Indexability` values are `Indexable` / `Non-Indexable` / `Redirected` | (no nulls) | Warn — column may be misnamed |

### Screaming Frog All Inlinks export (`*_all_inlinks.xlsx`)
| Check | Expected | Action if fails |
|-------|----------|-----------------|
| Required columns present | `Type`, `Source`, `Destination`, `Anchor`, `Alt Text`, `Status Code`, `Follow`, `Link Position` | Stop. List missing columns. |
| `Type` distribution sane | Hyperlink rows make up >40% of total | Warn — may indicate JS-only crawl |

### GSC Performance export (`gsc_performance.csv` / `gsc_api_data.csv`)
| Check | Expected | Action if fails |
|-------|----------|-----------------|
| Required columns | `Query` or `Page`, `Clicks`, `Impressions`, `CTR`, `Position` | Stop. List missing columns. |
| Date range present and not stale | Last data point ≤ 7 days old | Warn — flag freshness in deliverable |
| Position values numeric and 1-100 | (sanity) | Warn — possible parse issue |

**High-volume site anomaly (1M+ clicks/month properties):** GSC default views can hide queries on enterprise-scale sites. Applying a secondary filter (page, date range, country, device) sometimes reveals queries that don't show in the default export. When auditing high-volume sites, run multiple filtered passes — don't trust a single default export. Pages on these sites also rotate every few days, so cannibalization diagnosis can take a full week to stabilize. Source: Web Linker (r/SEO moderator) observation, 2026.

### Sitemap export (`*_sitemaps_all.xlsx`)
| Check | Expected | Action if fails |
|-------|----------|-----------------|
| Has `Address` column | (yes) | Stop. |
| URL count matches live sitemap (sample check) | Within ±10% of live `<sitemap>` count | Warn — sitemap may have changed since crawl |

### Backlink export (`backlinks_semrush.csv`)
| Check | Expected | Action if fails |
|-------|----------|-----------------|
| Required columns | `Source URL`, `Target URL`, `Anchor`, `Authority Score`, `Type` (follow/nofollow) | Stop. |
| Date range column populated | `First seen` or `Last seen` | Warn — cannot do velocity analysis |

### Site fingerprint (`Clients/<name>/site_fingerprint.json`)
| Check | Expected | Action if fails |
|-------|----------|-----------------|
| File exists for this client | (yes) | Dispatch `tech-stack-fingerprint` subagent to create it before continuing |
| `fetched_at` timestamp ≤ 30 days old | (yes) | Re-dispatch `tech-stack-fingerprint` subagent — site may have changed |
| `cms`, `page_builder.primary`, `theme.primary_theme` all populated | (yes) | Re-dispatch fingerprint with verbose flag |

## How to run the check

For the file types that need it, run a quick pandas one-liner via Bash:

```bash
python -c "
import pandas as pd
df = pd.read_excel('<path>', sheet_name=0)
print('SHAPE:', df.shape)
print('COLS:', list(df.columns))
required = ['Address', 'Status Code', 'Indexability', 'Title 1']
missing = [c for c in required if c not in df.columns]
print('MISSING REQUIRED:', missing)
print('Status Code value counts:')
print(df['Status Code'].value_counts().head(10) if 'Status Code' in df.columns else 'N/A')
"
```

Don't load 100k+ rows into your context — just print the metadata and a few aggregates.

## Output format

After running checks, report ONE of these three statuses:

### PASS — proceed with audit
```
Data Quality Check: <client> — PASS
Files validated:
- <filename>: <row_count> rows, all required columns present
- <filename>: <row_count> rows, all required columns present
Site fingerprint: present, dated <date>, CMS=<cms>, page_builder=<builder>
```

### WARN — proceed with caveats
```
Data Quality Check: <client> — WARN
Issues to flag in the deliverable:
- GSC data is 18 days old (last query date: 2026-04-11). Findings reflecting recent changes may be incomplete.
- Site fingerprint is 45 days old; recommend refresh.
Files validated: ... (as PASS)
Proceed with audit? Y/N (recommend yes, with caveats noted in deliverable)
```

### STOP — cannot proceed
```
Data Quality Check: <client> — STOP
Blocking issues:
- File not found: Clients/<name>/data/crawl_internal.csv
- File found but missing required columns: ['Indexability', 'Word Count']
Cannot run audit. Resolve the issues above and re-trigger.
```

## What this skill MUST NOT do

- Do not start the SEO analysis itself. Only validate inputs and hand control back.
- Do not modify the input files. Read-only checks.
- Do not skip the check because "the data looks fine" — run the actual pandas check.
- Do not load entire dataframes into the main context window. Use Bash + Python one-liners that print metadata only.

## Reference cases (incident → lesson)

### SameDay 45-vs-779 empty anchor count (April 2026)
The audit doc claimed "45 links with no anchor text." The SF all-inlinks export actually contained 779 truly-empty hyperlinks (no anchor + no alt). The discrepancy wasn't caught until the deliverable was nearly shipped. Lesson: any time the input data is referenced by a count, run the pandas check at intake — don't trust the prior audit doc's numbers.

### Superior plumbing page "Over 30 Years" (April 2026)
The semantic audit named the plumbing page as containing the "Over 30 Years" tenure claim. By the time the implementation report ran (3 weeks later), the page no longer contained that text — it had been edited in the interim. Lesson: when the audit input is older than 14 days and the deliverable depends on specific page text, dispatch live verification before trusting the input.
