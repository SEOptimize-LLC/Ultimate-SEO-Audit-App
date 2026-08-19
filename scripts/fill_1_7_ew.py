"""Fill EW's 1.7 Gap Analysis tab - the pilot for the 1.7 engine.

One row per KEYWORD CLUSTER (owner restructure 2026-08-18): Keywords lists the
verified gap queries with volumes, Volume is the cluster sum (the opportunity),
Clicks is what our existing page earns today in GSC May-Jul (the baseline at
stake when a writer touches the page). Every position was verified against a
LIVE SERP this session; briefs are written for the writing team - what to add
or redraft so the page matches the intent Google is rewarding.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io as S  # noqa: E402

TAB = "1.7 Gap Analysis"
EW = "https://educationwalkthrough.com"

BRIEF_DAN = (
 "REDRAFT AND EXPAND /danielson-rubric/ (currently 2,178 words). The competitor "
 "(2gno.me) holds top 10 on six rubric-variant queries with posts of 4,800-5,800 "
 "words, so Google is rewarding DEPTH plus a downloadable rubric on this topic, "
 "and our page covers the four domains in summary only. What to add, in order: "
 "(1) A section per domain - Planning & Preparation, Classroom Environment, "
 "Instruction, Professional Responsibilities - and under each, list its "
 "components (22 total across the rubric) with a 2-3 sentence plain-English "
 "description of what a principal actually looks for during an observation. "
 "(2) A 'How the rubric is scored' section: the four performance levels "
 "(Unsatisfactory / Basic / Proficient / Distinguished), with one concrete "
 "classroom example per level for at least two components, because the "
 "competitor's examples are what make their page useful. (3) A downloadable "
 "one-page rubric summary PDF - the competitor gates theirs behind email; ours "
 "should be ungated, which is an advantage the writer should not waste. "
 "(4) A short 'Danielson vs Marzano' cross-link paragraph pointing to our "
 "/marzano-framework/ page. (5) Close with how walkthrough software captures "
 "rubric evidence - one paragraph, not a sales pitch. Keep the existing URL; "
 "do not create a new page.")
BRIEF_TTESS = (
 "RESTRUCTURE /t-tess-rubric/ (2,318 words - LONGER than the competitor's 1,139) "
 "- this gap is about STRUCTURE, not depth. Observation Copilot outranks us on "
 "every T-TESS sub-query with one page whose headings literally name each thing "
 "people search: 'The T-TESS domains and criteria', then 'Planning', "
 "'Instruction', 'Learning Environment', 'Professional Practices'. Our headings "
 "describe ('T-TESS Rubric Four Domains Explained: Components...') instead of "
 "naming. What to do: (1) Rename headings so each searched sub-topic has its own "
 "H2/H3: 'T-TESS Ratings: the 5 performance levels' (Distinguished / "
 "Accomplished / Proficient / Developing / Improvement Needed), 'T-TESS Domains "
 "and Dimensions' with all 16 dimensions listed by name, 'What does T-TESS stand "
 "for?' as a one-line definition high on the page, 'T-TESS look-fors by domain'. "
 "(2) Add a ratings-scale table: level name, what it means, what an observer "
 "records. (3) Add a short 'T-TESS resources' section linking our own cycle, "
 "pre-conference and ratings posts - we have four supporting T-TESS posts the "
 "page never links. This is also a 1.5 candidate page, so this work merges with "
 "that rebuild rather than being a second pass.")
BRIEF_REINF = (
 "EXPAND /giving-feedback-to-teachers-after-observation/ - at 460 words it is "
 "the thinnest page in this set and the topic is the exact vocabulary of our "
 "product's use case. 'Reinforcement vs refinement' is how post-observation "
 "conferences are structured in TEAM-model states (reinforcement = the one "
 "strength to keep doing, refinement = the one area to improve). Classroom "
 "Mosaic ranks #6 with only a tag page, so a real article wins this. What to "
 "write: (1) H2 'Reinforcement vs refinement: what they mean' - define both, "
 "note they come from the TEAM conference model, one paragraph each. "
 "(2) H2 'How to choose your reinforcement objective' and 'How to choose your "
 "refinement objective' - the selection logic (highest-leverage, evidence-based, "
 "one each, never a list of five). (3) Worked example: a short observation "
 "scenario, then the reinforcement and refinement a principal would pick, with "
 "the actual sentences they would say. (4) Work the phrase 'observation "
 "feedback' naturally into headings and intro - we are absent on that query too "
 "and this is its natural home. Target 1,200+ words.")
BRIEF_HEAD = (
 "FIX WHICH PAGE RANKS, then strengthen it. On 'classroom walkthroughs' Google "
 "currently shows our HOMEPAGE at #13, not /what-is-a-classroom-walkthrough/ - "
 "the guide is losing internally. Mosaic ranks #4 with a product page wrapped in "
 "explainer content. What to do: (1) Internal linking pass: every blog post that "
 "says 'classroom walkthrough(s)' should link to the guide page with that exact "
 "anchor; today the homepage absorbs those signals. (2) On the guide page, add "
 "an H2 'What is a classroom walkthrough?' with a crisp 2-sentence definition "
 "directly under the H1 (it currently opens into formal-vs-informal before "
 "defining the term). (3) Add a 'Walkthrough vs observation vs evaluation' "
 "comparison table - the distinction buyers ask about and no ranking page makes "
 "cleanly. (4) Keep the existing benefits and debates sections; they are good.")
BRIEF_OBS = (
 "STRENGTHEN /classroom-observation/ (2,929 words, already ranks 12-18 on "
 "observation queries). Mosaic ranks #8 on 'observation of classroom' with an "
 "1,145-word intro post, so this is winnable with targeted additions rather "
 "than a rewrite: (1) Add an H2 'Types and lengths of classroom observations' - "
 "the competitor's second heading, and the sub-topic our page treats only in "
 "passing: formal/informal, announced/unannounced, walkthrough vs full-lesson, "
 "with typical durations. (2) Add a 10-step 'How to conduct a classroom "
 "observation' numbered list near the top - our current 'Conducting a Classroom "
 "Observation' section is prose; Google is rewarding scannable steps here. "
 "(3) Compress the intro: the first 200 words should answer 'what is a "
 "classroom observation and who does it' before anything else.")
BRIEF_APPS = (
 "REDRAFT /classroom-observation-app-features-that-support-teacher-growth/ "
 "toward the comparison intent. 2gno ranks #9 on 'observation apps' with a "
 "5,733-word listicle ('4 Best Teacher Observation Apps') while our page is a "
 "features essay that never names an app - searchers here are CHOOSING SOFTWARE "
 "and Google rewards pages that compare. What to do: (1) Reframe the top of the "
 "page as 'What to look for in a classroom observation app' with a criteria "
 "checklist (offline mode, framework rubrics built in, immediate feedback "
 "sharing, evidence capture, reporting). (2) Add an honest comparison section "
 "naming the real alternatives (Classroom Mosaic, Observation Copilot, GoReact, "
 "IRIS Connect) - one paragraph each on who they fit, because credibility here "
 "is what earns the ranking, and include Education Walkthrough in the same "
 "frame. (3) Keep the growth-features content below as supporting depth. "
 "Smallest volume in this table, highest commercial intent: the buyer query.")
BRIEF_MARZ = (
 "FOLD INTO THE 1.5 REBUILD of /marzano-framework/ (already the top 1.5 "
 "candidate: position slid 7.0 to 11.5 over 12 months). While that rebuild "
 "happens, add the two sub-topics 2gno ranks on and we do not: (1) H2 'The "
 "Marzano domains' - name the four domains explicitly and list the elements "
 "count under each (our page covers the nine strategies but never uses the "
 "domain names people search). (2) H2 'The Marzano teacher evaluation rubric' - "
 "how the scale runs (Not Using through Innovating), what evidence an observer "
 "records at each level, and a comparison line to Danielson linking our "
 "/danielson-rubric/ page. One combined job with the 1.5 work, not a second "
 "ticket.")
BRIEF_FORMS = (
 "SHARPEN /teacher-observation-templates/ (3,038 words, 206 clicks - our "
 "second-strongest asset in this table, sitting #14 on 'walk through forms'). "
 "Mosaic ranks #5 with a form LIBRARY, so Google is rewarding a browsable "
 "collection over an essay. What to do: (1) Add an H2 'Classroom walkthrough "
 "forms' with the phrase used naturally - the page says 'templates' throughout "
 "and never 'forms', which is the variant searched here. (2) Present the "
 "downloads as a visible grid near the top (form name, framework it fits, "
 "length, download link) instead of prose descriptions. (3) Add 2-3 "
 "walkthrough-specific forms (3-minute walkthrough form, look-for checklist) if "
 "the pack lacks them - the existing pack skews to full observations.")

# cluster, keywords(+vol each), cluster vol, current page clicks (GSC May-Jul),
# intent, competitor, their URL, our page, brief, additional comments
CLUSTERS = [
 ("Danielson rubric",
  "danielson rubrics (2,900); charlotte danielson rubric (210); danielson's "
  "framework for teaching rubric (170); danielson framework for teaching rubric "
  "(170); teacher evaluation danielson rubric (140); danielson evaluation "
  "rubric (70); danielson observation rubric (50)",
  3710, 49, "Informational (admin buyer)", "2gno.me",
  "https://home.2gno.me/post/danielson-framework-rubric-app",
  EW + "/danielson-rubric/", BRIEF_DAN,
  "All 7 queries live-verified 2026-08-18: 2gno.me top 10 on every one "
  "(#3-#10), EW absent from the top 20 on all of them. Our page holds #3 on "
  "the base term 'danielson rubric' itself, so this expansion defends that "
  "position while capturing the variants."),
 ("T-TESS depth",
  "t-tess ratings (210); tess domains (210); t-tess levels (110); what does "
  "t-tess stand for (70); t tess standards (70); t tess resources (70); t tess "
  "look fors (70); t tess rating scale (50); t-tess evaluation rubric (50)",
  910, 292, "Informational (Texas admin)", "observationcopilot.com",
  "https://observationcopilot.com/frameworks/t-tess",
  EW + "/t-tess-rubric/", BRIEF_TTESS,
  "9 queries live-verified: Observation Copilot #6-#10 on all of them from ONE "
  "1,139-word page; EW absent or #16-#21 despite a 2,318-word page. A structure "
  "gap, not a depth gap. Same page as a top 1.5 candidate: one combined "
  "rebuild, not two tickets. 292 current clicks means edit with care - "
  "restructure headings, cut nothing."),
 ("Reinforcement vs refinement",
  "reinforcement vs refinement (590); refinement vs reinforcement (210); "
  "observation feedback (50)",
  850, 5, "Informational (coaching vocabulary)", "classroommosaic.com",
  "https://classroommosaic.com/library/tag/reinforcement-and-refinement",
  EW + "/giving-feedback-to-teachers-after-observation/", BRIEF_REINF,
  "Live-verified: Mosaic ranks #6 with only a TAG PAGE - the weakest ranking "
  "asset in this table - and our page is 460 words earning 5 clicks. "
  "Lowest-risk, highest-headroom row: a real article should win this cluster."),
 ("Classroom walkthroughs head term",
  "classroom walkthroughs (140); classroom walkthrough (140)",
  280, 19, "Commercial-informational (category head)", "classroommosaic.com",
  "https://classroommosaic.com/walkthroughs",
  EW + "/what-is-a-classroom-walkthrough/", BRIEF_HEAD,
  "Live-verified: Mosaic #4; EW #13 WITH THE HOMEPAGE, not the guide page - "
  "internal cannibalization is the first fix. This is the category head term "
  "for everything the client sells."),
 ("Classroom observation",
  "observation of classroom (590)",
  590, 37, "Informational", "classroommosaic.com",
  "https://classroommosaic.com/blog/an-introduction-to-classroom-observations",
  EW + "/classroom-observation/", BRIEF_OBS,
  "Live-verified: Mosaic #8 with 1,145 words against our 2,929 - winnable with "
  "targeted additions rather than a rewrite. Our page already sits 12-18 on "
  "adjacent observation queries."),
 ("Observation apps",
  "observation apps (90)",
  90, 4, "Commercial (software selection)", "2gno.me",
  "https://home.2gno.me/post/teacher-observation-apps",
  EW + "/classroom-observation-app-features-that-support-teacher-growth/",
  BRIEF_APPS,
  "Live-verified: 2gno #9 via a 5,733-word comparison listicle; us #20 with a "
  "features essay that names no product. Smallest volume in the table, highest "
  "commercial intent - the vendor-selection query. Also feeds the 1.6 AI "
  "finding: assistants recommend competitors on exactly this question."),
 ("Marzano depth",
  "marzano domains (70); marzano rubric (50); marzano rubric for teacher "
  "evaluation (50)",
  170, 208, "Informational (admin buyer)", "2gno.me",
  "https://home.2gno.me/post/marzano-framework-teacher-evaluation",
  EW + "/marzano-framework/", BRIEF_MARZ,
  "Live-verified: 2gno #6-#7 on all three; EW absent. Same page as the #1 "
  "candidate in 1.5 (208 clicks, 12-month slide) - fold these subtopics into "
  "that rebuild, one ticket not two."),
 ("Walkthrough forms",
  "walkthrough forms (70); walk through forms (50)",
  120, 206, "Commercial-leaning (template download)", "classroommosaic.com",
  "https://classroommosaic.com/library/category/walkthrough-forms",
  EW + "/teacher-observation-templates/", BRIEF_FORMS,
  "Live-verified: Mosaic #5 with a form library; us #14 with our "
  "second-strongest page in this table (206 clicks). Template seekers are tool "
  "prospects. Edit-with-care: the page already performs."),
]

BROWS = [
 ("principalcenter.com", "principalcenter.com/best-classroom-walkthrough-apps/ "
  "(features TeachBoost ONLY - verified by fetching the page)",
  EW + "/ + /features/",
  "The single highest-value target in this analysis. This one page ranks top 10 "
  "on 5 of our 11 scoped SERPs AND is one of the AI assistants' most-cited "
  "sources for walkthrough-app questions (it is why TeachBoost leads AI mentions "
  "while ranking nowhere itself). Education-niche authority, exactly on-topic. "
  "Ask: inclusion in the walkthrough-apps roundup. One placement moves both the "
  "SERP and AI channels.", "Y"),
 ("cesapurchasing.org", "links to 2gno.me (domain level)", EW + "/pricing/",
  "Wisconsin Cooperative Educational Service Agencies purchasing arm - an "
  "education PROCUREMENT body. Modest authority (rank 24) but a district buyer "
  "signal money cannot buy. Ask: vendor listing.", "Y"),
 ("graniteschools.org", "links to classroommosaic.com (domain level)", EW + "/",
  "An actual school district (Granite SD, Utah) linking out to a walkthrough "
  "vendor - low authority score, maximum relevance. Districts linking to tools "
  "is the exact pattern we want. Ask: resource-page inclusion alongside or "
  "instead of Mosaic.", "Y"),
 ("schooldataleadership.org", "links to 2gno.me (domain level)", EW + "/",
  "School data leadership organization, rank 224 - the rare target that is both "
  "authoritative AND on-niche. Ask: tool mention or guest contribution on "
  "observation data practice.", "Y"),
 ("edtech.com", "links to classroommosaic.com (domain level)", EW + "/",
  "EdTech directory, rank 40. Straightforward listing request; relevant "
  "category exists (observation/evaluation tools).", "Y"),
 ("tomwhitby.com", "links to 2gno.me (domain level)", EW + "/",
  "Veteran educator blogger (rank 75). Relevant audience; realistic ask is a "
  "mention in a tools post rather than a dedicated review.", "Y"),
 ("rdene915.com", "links to 2gno.me (domain level)", EW + "/",
  "Rachelle Dene Poth - educator author/blogger (rank 29). Same play as above; "
  "she writes tool roundups.", "Y"),
 ("colorado.edu", "links to observationcopilot.com (domain level)", EW + "/",
  ".edu education-school link. Hard to replicate on request; realistic route is "
  "our state-instrument guides (ATOT, T-TESS, OTES) as citable resources for "
  "teacher-prep coursework. Slow but durable.", "N"),
 ("edthena.com", "links to observationcopilot.com (their only high-rank link, "
  "213)", EW + "/",
  "NOT recommended for outreach: Edthena is itself a video-observation vendor - "
  "a competitor linking to a competitor. Listed so nobody chases it from a raw "
  "export.", "N"),
]


def main():
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    sid = reg["educationwalkthrough"]["sheet_id"]
    hdr = S.read(sid, f"'{TAB}'!A8:J8")
    print("section A header:", hdr[0] if hdr else "??")

    S.write(sid, f"'{TAB}'!B4", [[
        "Classroom Mosaic (classroommosaic.com), Observation Copilot "
        "(observationcopilot.com), 2gno.me. Chosen from LIVE top-10 SERPs pulled "
        "2026-08-18 across 11 scoped queries (1.5 candidates + vendor-intent "
        "queries): same-type walkthrough/observation software vendors only. "
        "Directories, state bodies (teachfortexas.org) and publishers "
        "(principalcenter.com) excluded from the set - principalcenter is a "
        "section B target instead. Larger AI-channel names (TeachBoost, "
        "Frontline) rank in ZERO scoped live SERPs. Snapshot: "
        "gap_analysis/2026-08-serps.json"]])
    S.write(sid, f"'{TAB}'!B5", [[
        "Baseline month - no stored prior SERP set to compare. This month's "
        "top-10 snapshot is saved; from September this cell is answered "
        "automatically by diffing against it."]])

    colA = S.read(sid, f"'{TAB}'!A1:A120")
    a_first = next(i for i, r in enumerate(colA, 1)
                   if r and str(r[0]).strip() == "Keyword Cluster") + 1
    body = [list(c) for c in CLUSTERS]
    n = S.write(sid, f"'{TAB}'!A{a_first}:J{a_first+len(body)-1}", body).cells
    print(f"section A: {len(body)} cluster rows, {n} cells")

    colA = S.read(sid, f"'{TAB}'!A1:A160")
    b_first = next(i for i, r in enumerate(colA, 1)
                   if r and str(r[0]).strip().startswith("Target Domain")) + 1
    nb = S.write(sid, f"'{TAB}'!A{b_first}:E{b_first+len(BROWS)-1}",
                 [list(r) for r in BROWS]).cells
    print(f"section B: {len(BROWS)} rows, {nb} cells")


if __name__ == "__main__":
    main()
