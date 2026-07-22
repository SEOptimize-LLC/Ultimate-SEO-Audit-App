---
description: Run a STANDALONE Google Discover eligibility audit for a client from a Screaming Frog crawl (and an optional GSC Discover Performance export). Identifies the editorial/article URL set, flags image-preview robots blockers (meta robots OR X-Robots-Tag), reports current Discover-earning pages and low-CTR opportunities when performance data is supplied, and surfaces the judgment-based eligibility checklist. This is a separate channel audit — it is NOT part of the full-site audit. Use for "discover audit", "discover SEO audit", or "google discover audit" requests.
---

# /discover-audit

You are running a **standalone Google Discover eligibility audit**. Google Discover is a query-independent content feed (the Android swipe feed, the Google app, the mobile homepage) with its own GSC report and its own eligibility model. It is invisible to a standard SERP-focused technical/on-page audit, so this command exists to assess it on its own.

**This is a separate channel audit. Do NOT fold it into the full-site audit** — the user triggers it deliberately and on demand. Present it as its own deliverable.

Trigger phrases: "discover audit", "discover SEO audit", "google discover audit", "check Discover eligibility".

## Required Inputs

1. **Crawl** — a Screaming Frog HTML Internal export (CSV or XLSX). If a client folder is given, default to `Clients/<name>/data/crawl_internal.csv`.

Optional:
2. **GSC Discover Performance export** — the page-level clicks/impressions/CTR export from the GSC Discover report. Supplying it unlocks the current-earning and high-impression/low-CTR opportunity findings. Without it, the audit runs the crawl-only eligibility assessment and says so.
3. **Client name** — for the report header, and to resolve the default crawl path.

## Workflow

1. **Resolve the crawl path.** Use the explicit path if given; otherwise `Clients/<name>/data/crawl_internal.csv`. If the file is missing, stop and tell the user which path you looked for.

2. **Run the auditor via the CLI runner:**

   ```bash
   python run_discover_audit.py --crawl "<crawl path>" \
       [--discover-perf "<GSC Discover export>"] \
       [--out "Clients/<name>/Full SEO Audit/discover_audit.md"] \
       [--client "<name>"]
   ```

   The runner loads the crawl through the standard Screaming Frog parser, optionally loads the Discover performance export, runs `DiscoverAuditor`, and writes/prints a clean Markdown report.

3. **Read the report and present the findings.** Lead with a one-line verdict (e.g. "N editorial pages eligible for Discover; K suppress image previews and are blocked"). Then walk the findings most-urgent-first:
   - **Image-preview suppressed (MEDIUM)** — the strongest, verifiable Discover blocker: articles whose `noimageindex` / `max-image-preview:none` directive (via meta robots OR the X-Robots-Tag header) removes them from an image-led feed. This is a concrete fix.
   - **Currently earning (INSIGHT)** — only when a Discover export is supplied: the pages the feed already surfaces. Mine them for shared traits.
   - **Low-CTR opportunity (LOW)** — high-impression, low-CTR Discover pages: usually a weak lead image or title, not a content problem.
   - **Eligibility review (INSIGHT)** — the article set to work the judgment checklist against (informational intent, honest titles, author E-E-A-T, mobile/CWV, large indexable lead image, topical timeliness).
   - **No editorial content (INSIGHT)** — a purely transactional site has little Discover opportunity; say so rather than manufacturing a finding.

## Framing rules (hard)

- Discover has **no deterministic inclusion levers** — only eligibility signals that raise or lower probability. Frame every recommendation as "raises Discover probability," never as a guarantee or a pass/fail ranking rule. The one exception is the image-preview blocker, which is a genuine disqualifier worth stating plainly.
- **Full URLs only** — never truncate a URL in the report (per `.claude/rules/report-formatting.md`).
- **No internal file paths / document names** in anything shown to the client (per `.claude/rules/report-formatting.md`).
- If the user gave a client folder, follow the deliverable QA and TL;DR-on-approval preferences.

## What NOT to do

- Don't wire this into or run it as part of the full-site audit — it is standalone by design.
- Don't claim a page "will" appear in Discover — inclusion is probabilistic.
- Don't manufacture a Discover strategy for a site with no editorial content library.
