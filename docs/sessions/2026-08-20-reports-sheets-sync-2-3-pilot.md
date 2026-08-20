# Session save — 2026-08-20 (Reports day + Sheets sync + 2.3 pilot)

Continues from `2026-08-19-week2-start.md`. Everything below verified live on
2026-08-20 unless dated otherwise.

## OPEN DECISION — resume here tomorrow

Owner went to bed on this question: **fill the three verifiable SOP checkpoint
fields on the EW 2.3 Refresh Log row?**

- Outdated Cut → "Y - verified clean, nothing to cut (scan 2026-08-20: zero
  stale year refs in 3,978 words)"
- Answer-First Restructure → "Y - already in place per the page's Aug 13
  update (Key Takeaways + question H2s + FAQ, verified live)"
- Schema Valid → run GSC rich-results inspection, fill with Google's verdict
- All execution fields (Info Gain, Title+Meta, Outbound Links, Tracking,
  Live link, Date) stay BLANK until work ships; on "it's live" we re-verify
  against the live page before marking, same as the 2.1 closes.

Principle agreed in-session: checkpoint columns mean **verified done**, never
assumed done.

## Branded PDF work reports — 5 of 8 clients shipped

All in `Clients/<folder>/Reports/<name> - August 2026 SEO Work Report.pdf`,
all verify_pdf PASSED, all statuses live-verified before "Done, verified":

- **EW** (6pp) — 3 fixes Done-verified; firewall row REMOVED after owner
  correction: the blocked IP is the owner's VPN, not the agency office. No
  client-side whitelist ask. fixes.yaml #4 corrected to match.
- **Cudio** (6pp) — all 5 internal links verified live (fetched the linking
  pages, found each href); both link fixes Done-verified.
- **Comfort** (6pp) — 3 coupon 301s live in one hop, landing on /specials/
  (the coupons page itself moved there — redirects follow correctly);
  sitemap_index.xml live with current lastmods. Both Done-verified.
- **Beehive** (6pp) — fiberglass article RESTORED (200, ~7,900 words, clean
  self-canonical; the Rank Math self-loop is gone). ARCHITECTURE DECISION
  MADE by someone: /drain-cleaning-park-city-utah/ now 308s into
  /our-locations/park-city/drain-cleaning/, consistent with Orem — the
  /our-locations/ network won. Remaining: rest of the city map + de-orphan
  links + who deployed it. fixes.yaml rows 1 and 3 updated to match.
- **SameDay** (7pp) — honest open statuses. Headline framing: 90 pages
  (31% of sitemap) held out by Google's stale June 30 noindex record.

Server-response rows on all reports: "Awaiting field data" (never Done —
only next month's field numbers can confirm).

## SameDay verification battles (owner demanded, delivered)

- **90/90 noindex re-check, zero sampling**: every URL 200 with index,follow
  in meta AND no X-Robots-Tag noindex header. GSC URL Inspection on /cooling/
  still shows "Excluded by noindex", **last crawl 2026-06-30** — Google's
  record is stale, pages are clean. THE unlock: **Validate Fix in GSC +
  Request Indexing on the money subset — still not done, gates everything,
  highest-value click across all 8 clients.**
- **Mis-targeted redirect still live**: both /service-area/ Sandy plumbing
  patterns still 301 to the Sandy HEATING page (re-confirmed).
- **46 discovered-not-indexed deep dive** (owner asked "links or something
  else?"): all 46 = "Last Crawl: Never"; 15 decayed to "unknown to Google".
  40-page blog-archive crawl: 43/46 ARE linked but only from deep pagination
  (pages 6-18), zero contextual links. Verdict written into fixes.yaml #4 as
  three subgroups:
  - **A (36)**: old thin posts 2014-2020 (median ~410w) — DO NOT link yet;
    the 59 crawled-and-declined siblings prove links just move them to a
    different not-indexed bucket. Quality review decides first.
  - **B (6)**: current substantial posts — link NOW from named service pages
    + request indexing (incl. /blog/ac-repair-vs-replacement/, 3,577w,
    Jul 2026, linked from blog front page yet never crawled — evidence the
    whole site's crawl demand is suppressed; Validate Fix is upstream).
  - **C (4)**: money pages mis-bucketed — breaker-panel (request indexing),
    Orem heating + Sugar House AC (true orphans: hub links + indexing),
    American Fork "-2" (duplicate artifact → redirect cleanup, do NOT link).

## Sheets synced after reauth (surgical, owner data preserved)

gcloud ADC renewed. `scratchpad/patch_2_1_tabs.py` pattern: match rows by
position + URL-token sanity check, update only changed B/C/D cells, NEVER
write E:H, snapshot first. Results: SameDay (46-URL breakdown), EW (closed
WAF row + Airlift row), Beehive (decision + fiberglass), Superior (inserted
deleted-page row as #6 after fixing my own duplicate-insert; TTFB row kept
"Roger" and renumbered #7). All four reconciles green. **Candidate for
promotion to scripts/ as the standard post-edit refresh tool.**

## Still blocked / waiting on owner

1. **Owner's audit-issues Google Sheet** (id 14Pti1uBfQ0UpoM_qKPScHtmt3tG_
   yjuLDCa0IZZyCac): 403 for team@seoptimizellc.com — owner must share as
   Editor. Then write Group A/B/C labels into the SameDay Utah tab rows
   (classification ready in fixes.yaml + sameday_46_content.json).
2. **SameDay Validate Fix** (GSC UI, owner action) — see above.
3. **EW look-fors roles decision**: top-50 post = checklist asset? hub
   subfolder pages link into the canonical? (Duplicate already consolidated.)
4. Beehive: who deployed the Park City/Orem redirects + rest of map.

## Other work shipped today

- **Snow overlap verdict**: why-do-teeth-turn-yellow vs -yellow-with-age =
  same intent, ~80% territory overlap, both 0 impressions in 90d. Keep
  /why-do-teeth-turn-yellow (head-term URL), rebuild on the newer post's
  structure, 301 the age post in. June plan had both as independent
  "Optimize" — superseded.
- **Arsenal dev workbook**: `Clients/Arsenal Health/Arsenal Health - SEO
  Implementation Plan for Developer - 2026-08.xlsx` (4 tabs, Red Hat
  Display, dropdowns). Key new diagnosis: non-www→www redirect is **307
  temporary** site-wide (trailing-slash normalizer is already 308) — that's
  WHY Google picked the non-www form as canonical for /sports-massage-
  therapy. Fix #2 = flip host redirect to permanent (one config change).
  Both hyrox root→/blog/ pairs verified already 308 (fix #4 partially done).
- **Branded PDF system published**: history purged of Temp Docs (client PDF
  was in it), README rewritten impersonal, force-pushed to private
  github.com/SEOptimize-LLC/Branded-PDF-Reports. Team zip also at
  `AGENCY/SEOptimize Branded PDF Reports - Team Share.zip`. ClickUp Brain =
  read/Q&A only (Workspace GitHub connection needed); installs stay local.
- **ClickUp Brain research** (docs-verified): Connected Search ClickApp +
  App Center Workspace connection + Drive files shared org-wide with "Can
  find in search results". Custom-field Sheet links: Brain reads the field,
  contents only via the Drive index; explicit prompt pattern documented.

## 2.3 pilot (EW) — done except the open decision

- **Refresh Log populated**: 5 rows, baselines verbatim from 1.8 (80/5,117 ·
  166/3,858 · 49/3,067 · 70/7,653 · 19/3,760 May-Jul), step-0 gates embedded
  (walkthroughs Aug 13 revision pull; Danielson Aug 4 crash diagnose-first),
  AI-cited flags from 1.6. Checkpoints blank. Snapshot taken.
- **C5 corrected**: family is 6 URLs not 7 — the duplicate stub 301 shipped
  Aug 19/20 (verified via DFS final-url). Plan.yaml v3 statement superseded.
- **2.3 packet**: Aug 13 update already did the answer-first restructure;
  zero rot; SERP (Aug 19 winners data) rewards institutional checklist/
  download pages; gaps = downloadable checklist + PAA "What is a teacher
  observation checklist?" + consolidation links.
- **Title sanity-checked**: "Classroom Walkthrough Look-Fors: A Checklist of
  What to Observe" (63c; checker fixed a for/for root repeat). Meta (147c)
  HELD until the checklist actually exists on-page. **Standing EW
  constraint: if the template ever appends "| Education Walkthrough", no
  visible title may contain "Walkthrough".**
- EW page fetches from this machine 403 (owner's VPN IP on the BlogVault
  blocklist) — route via DFS instant_pages; raw_html retrieval by id does
  NOT work on instant fetches (two failed attempts today — use meta.htags +
  content_parsing instead).

## Tomorrow's queue (suggested order)

1. Resolve the open checkpoint-fill decision; run the GSC schema check.
2. Write `Skills/monthly-seo-workbook/tasks/2.3.md` recipe from the pilot
   (include: baselines verbatim from 1.8, packet steps, verified-done rule,
   house title rule beats the SOP's "≤60 chars" — flag template alignment).
3. Roll Refresh Log population to the other 7 clients (script the fill like
   fill_2_1; the EW fill logic is in scratchpad/fill_ew_23.py).
4. 2.4 packet (30-60-90 guide — ships first, summer peak) when owner says.
5. Owner shares the audit-issues sheet → write A/B/C groups.
