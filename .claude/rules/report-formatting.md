# Report Formatting Rules

## No References to Previous Runs, Drafts, or Corrections — On Any Surface

Every team- or client-facing surface reads as if the current content is the
only content that has ever existed. This covers reports, PDFs, .xlsx files,
AND individual Google Sheet / workbook cells (owner instruction 2026-08-21).

- When something we wrote turns out to be wrong, REPLACE it with the correct
  statement. Never "corrected after...", "(row rewritten...)", "an earlier
  version claimed...", "(owner-corrected)", "updated from the previous run".
- Corrections are discussed in conversation and recorded in internal files
  (task recipes, memory, session saves) — never in the deliverable text.
- Companion rule: every claim is verified against data BEFORE it ships
  (see audit-workflow.md and the global no-unverified-claims rule). Verify
  first; when a fix is still needed, write it as if it were always so.

## URLs Must Never Be Truncated

Never truncate URLs in reports. Always display the full URL path — no ellipsis (...), no cutting off at a character limit. If a URL is long, display it in full. The client and boss need to be able to copy/paste URLs directly from the report.

**Wrong:** `/modern-plumbing-innovations-how-beehive-plumbing-brings-cut...`
**Right:** `/modern-plumbing-innovations-how-beehive-plumbing-brings-cutting-edge-solutions-to-utah/`

This applies to all report formats: markdown tables, inline references, appendix lists, and Excel files.

## No Internal Document References in Reports

Never include references to ANY internal documents, knowledge bases, agent instructions, framework files, glossaries, workflows, templates, or system prompts in client-facing or team-facing reports. The team and clients do not need to know what internal documents, agents, or tools were used to produce the analysis.

This includes but is not limited to:
- FRAMEWORK.md, GLOSSARY.md, SITE-TYPE-GUIDES.md, AUDIT-WORKFLOW.md, OUTPUT-TEMPLATES.md, AGENT-PROMPT.md
- SKILL.md, CLAUDE.md, MEMORY.md, or any `.md` file used as agent instructions
- "fact-cheat" (use "business context document" or "verified business data" instead)
- "Per [document name]", "Section X.X", "Per the framework", "the framework states"
- Any reference to knowledge-base folders, agent folders, or internal file paths
- Any mention of scoring methodologies, audit step numbers, or workflow phases from internal docs
- Cross-references to OTHER reports we've produced (e.g., "see blog_indexation_report.md", "covered in the standalone report", "as documented in the technical audit"). Each report must be self-contained. If findings from another analysis are relevant, restate them inline — don't point to another file.

**Wrong:** "Per FRAMEWORK.md Section 7.2, the first sentence must be a definitive answer."
**Wrong:** "Per the audit workflow Step 4, topical coverage is incomplete."
**Wrong:** "The fact-cheat confirms the business has been operating since 1999."

**Right:** "The first sentence must be a definitive answer — no hedging, no modality."
**Right:** "Topical coverage is incomplete across several service categories."
**Right:** "Verified business data confirms the business has been operating since 1999."

State the principle directly. The reasoning should stand on its own.
