# Handoff: give 3.1 target pages with no Search Console data a path to source candidates

Written 2026-11-10 in the Ultimate SEO Agent session, for a session working in the
**Internal Link Optimization Agent** folder. Owner's yes, 2026-11-10 ("Let's move forward with all your
suggestions and recommendations"). This plan changes the engine; the Ultimate SEO Agent session does not
edit that project.

## The problem

Monthly task 3.1 asks the engine for links into target pages that 2.1, 1.8 and 2.3 named. Many of those
pages are new or not yet crawled, so they have no Search Console queries. The engine builds its topical
map from Search Console query clusters (`internal_link_agent/.../topical_map.py:5`) and drops every pair
whose source or target is off that map (`topical_map.py:86`, `link_recommender.py:1018`). Those targets
can therefore never get a candidate, however well a post's body matches them.

Measured: "115 of 144 planned pages across seven clients had no row" in October (Ultimate SEO Agent,
`Skills/monthly-seo-workbook/tasks/3.1.md:61-62`). On Bart's, "20 of the 23" skipped targets had never been
crawled (`3.1.md:72-73`).

## The research behind it

Deep research run `AGENCY/Deep Research Agent/runs/2026-11-10-criteria-checklist-and-reasoning-for/`,
report.md: judge relevance from page content first and rank similarity within each target (report.md:70-71,
:80-81). Shared Search Console queries are an untested second score (report.md:91). Practitioner consensus,
not a calibrated rule.

## The change

1. **Scope:** only targets on `target_allowlist` (the 3.1 targets run_3_1.py passes in). Every other pair
   keeps the current map rule.
2. **Skip the off-map drop for those targets** when the source post's body names the target's primary
   entity, using the existing entity rule (`link_recommender.py:1856`). Score such a pair as T2
   (multiplier 1.0).
3. **Rank** those candidates by embedding similarity within each target (not against the site average),
   and send the top 10 per target to the link judge. Why 10: 3.1 allows at most 3 links per target
   (`3.1.md:41-44`), and the Cudio judge replay rejected 21.5% of pairs (engine `CLAUDE.md:207-208`),
   so 10 leaves room for heavy rejection. The owner can change the number.
4. **Pre-check:** the target's copy must be in `client_page_content`. If it is not, fetch that one page
   live and store it, then score.
5. **Keep every other gate**: the per-pair judge (its prompt already says missing target details are
   "never a reason to reject on their own", `link_judge.py:64`), the existing-link check, the source
   floor, and the per-source cap.

## How to check it worked

- Tests in the engine for: an allowlisted off-map target gets candidates when a post names its entity;
  a non-allowlisted off-map pair is still dropped; ranking is per target.
- After the December 3.1 run: count Skipped rows with reason `no source`, per client, against November's.
  run_3_1.py now writes the engine log to `Clients/<folder>/internal_links/<month>/run_3_1.log`, and
  `run_3_1.funnel_counts()` reads the drop counts from it.
- When it ships, the Ultimate SEO Agent session updates `3.1.md`'s "Why so many pages get no link"
  paragraph (`3.1.md:70-75`).

## Also raised by the research, engine side (not part of this change)

- The shared-query block (`cannibalization.py:40`, `:77`) has no intent test; the agency's rule
  `rules/common/cannibalization-needs-clear-intent.md` says a query with no resolvable intent is not
  cannibalization. Tracked separately in `~/.claude/analyses/2026-11-10-source-page-selection-research.md`.
