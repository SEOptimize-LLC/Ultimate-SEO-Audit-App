"""Rewrite EW's 1.7 Expansion Angle column from OBSERVED evidence only.

Replaces the first-draft briefs, which were built on a two-page diff and
generalised "what Google rewards" from a single competitor page - in the
Danielson cluster that meant prescribing the strategy of the page ranking LAST.
Every claim below cites what the live top-3 winners actually are, their parsed
lengths and headings, and the People Also Ask questions Google attaches to the
query. Where the winners share no pattern, the brief says so instead of
manufacturing a consensus. Evidence: gap_analysis/2026-08-serp-winners.json.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io as S  # noqa: E402

TAB = "1.7 Gap Analysis"

BRIEFS = {
 "Danielson rubric": (
  "RESTRUCTURE /danielson-rubric/ INTO THE UNGATED RUBRIC RESOURCE.\n\nWHAT THE LIVE SERP SHO"
  "WS: do NOT expand for depth. Observed top 3 on 'danielson rubrics': a Washington state e"
  "ducation page (296 words), danielsongroup.org (615 words - and its rubric download is GA"
  "TED behind 'Log In or Register To Download'), and an NYC education portal (227 words). S"
  "hort authoritative pages that hand over the document win here; the 5,000-word guide (2gn"
  "o) ranks LAST at #10. What to build:\n\nDO THIS:\n1. A free, ungated, downloadable one-page"
  " Danielson rubric PDF as the page's centrepiece, offered in the first screen - the #3 re"
  "sult gates theirs, which is the opening.\n2. A components table directly answering the PA"
  "A question 'How many components are in the Danielson framework?': 22 components across 4"
  " domains, listed by name under each domain.\n3. A short 'Danielson performance levels' se"
  "ction answering the PAA 'What is a highly effective score?': the four levels and what sc"
  "ore maps to each.\n4. One worked example answering 'What is an example of a rubric?' - a "
  "filled-in component row.\n\nNOTE: Keep total length modest; the page's current 2,178 words"
  " is already above every winner. Deliver the resource, do not write a treatise."
 ),
 "T-TESS depth": (
  "RESTRUCTURE /t-tess-rubric/ AROUND SCORING QUESTIONS and add the document.\n\nWHAT THE LIV"
  "E SERP SHOWS: Observed top of SERP: teachfortexas.org official PDFs at #2 and #4 (the ac"
  "tual state rubric documents), ies.ed.gov download page (585 words) at #5. People search "
  "this to GET the rubric and understand SCORES - the PAA is explicit: 'What is a good TTES"
  "S score?', 'How to calculate your TTESS score?', 'What are the four domains of the T-TES"
  "S assessment?', 'What are good TTESS goals?'. What to do on our existing 2,318-word page"
  " (292 clicks - restructure, cut nothing):\n\nDO THIS:\n1. Add H2s answering each PAA questi"
  "on verbatim: 'What is a good T-TESS score?' (the five ratings: Distinguished, Accomplish"
  "ed, Proficient, Developing, Improvement Needed, and what counts as strong), 'How T-TESS "
  "scoring is calculated', 'The four T-TESS domains and 16 dimensions' with every dimension"
  " named, 'T-TESS goal examples'.\n2. Add a downloadable rubric summary PDF - the SERP is d"
  "ocuments, so offer one.\n3. Add a 'T-TESS resources' section linking our four existing T-"
  "TESS posts (cycle, pre-conference, ratings impact, preparation).\n\nNOTE: Same page as the"
  " 1.5 candidate - one combined rebuild."
 ),
 "Reinforcement vs refinement": (
  "WRITE THE ARTICLE THIS SERP DOES NOT HAVE.\n\nWHAT THE LIVE SERP SHOWS: with an honest vol"
  "ume caveat. Observed top results: a South Carolina DOE PDF, a TeachersPayTeachers produc"
  "t card (181 words, selling a template for exactly this), and a Reddit thread. No substan"
  "tive owned article ranks; Mosaic sits at #6 with a bare tag page. A real piece on our /g"
  "iving-feedback-to-teachers-after-observation/ page (currently 460 words, 5 clicks - noth"
  "ing at risk) can take this. Structure:\n\nDO THIS:\n1. H2 'Reinforcement vs refinement: wha"
  "t each means in a post-observation conference' - crisp two-sentence definitions first (n"
  "o strong page owns the snippet).\n2. H2s 'How to choose your reinforcement objective' / '"
  "How to choose your refinement objective' - one each, evidence-based, highest-leverage.\n3"
  ". A worked example: short observation scenario, then the two objectives a principal woul"
  "d pick, with the actual conference sentences. The TpT paid template proves practitioners"
  " want the worked format free.\n\nNOTE: CAVEAT for expectations: the PAA on this query is b"
  "ehavioural-psychology ('two main types of reinforcement'), so a share of the 590 monthly"
  " searches is a different audience; treat the volume as partly ours, not wholly."
 ),
 "Classroom walkthroughs head term": (
  "FIX WHICH PAGE RANKS, THEN MATCH THE OBSERVED GUIDE FORMAT.\n\nWHAT THE LIVE SERP SHOWS: M"
  "easured fact: our HOMEPAGE ranks #13 on this query, not /what-is-a-classroom-walkthrough"
  "/ - internal links across the blog say 'classroom walkthrough' without linking the guide"
  ", so Google picks the homepage. Fix first: internal-linking pass pointing every natural "
  "mention to the guide with that anchor. Observed winners are practice-structured guides o"
  "f 1,342-2,027 words (nextgenlearning.org's 'Focus Walks' strategy piece; ensemblelearnin"
  "g.org structured as 'Key Practice 1: Establish a clear purpose... Key Practice 2: Commun"
  "icate the purpose...'). Our 1,214 words is in range - format, not length. What to change"
  " on the guide:\n\nDO THIS:\n1. Open with a two-sentence definition answering the #1 PAA ver"
  "batim: 'What is a classroom walkthrough?' - the snippet slot is winnable.\n2. Restructure"
  " the middle into named key practices (purpose, communication with staff, what to capture"
  ", follow-up conversation), the shape both winning articles share.\n3. Keep our formal-vs-"
  "informal and benefits sections; add a 'Walkthrough vs observation vs evaluation' compari"
  "son table - no winner has one; it is the differentiator, and it matches the PAA 'What is"
  " a teacher walk through?'."
 ),
 "Classroom observation": (
  "ADD THE TYPES AND EXAMPLES THE PAA ASKS FOR.\n\nWHAT THE LIVE SERP SHOWS: no length change"
  ". Observed SERP has NO format consensus: a university forms hub at 459 words ranks besid"
  "e a 2,803-word culture essay (nextgenlearning.org), which means intent is mixed and no o"
  "ne has resolved it; the page that answers the PAA directly has the opening. The PAA: 'Wh"
  "at are the five types of classroom observation?', 'What are 5 examples of an observation"
  "?', 'Can you provide an example of a class observation?'. On our existing 2,929-word pag"
  "e:\n\nDO THIS:\n1. Add H2 'The five types of classroom observation' - formal, informal/ wal"
  "kthrough, peer, virtual, self-directed video - one paragraph each with typical length an"
  "d who conducts it.\n2. Add H2 'Classroom observation examples' with one short written exa"
  "mple of an actual observation note - the PAA asks for examples twice and no winner provi"
  "des one.\n3. Link our observation forms/templates page prominently: a bare university FOR"
  "MS hub ranking #2 at 459 words is direct evidence searchers want the documents.\n4. Tight"
  "en the intro to answer 'what is classroom observation of teaching' in the first two sent"
  "ences."
 ),
 "Observation apps": (
  "RE-TARGET TO THE QUALIFIED PHRASE.\n\nWHAT THE LIVE SERP SHOWS: the bare query is polluted"
  ". Observed top 3 on 'observation apps': observation.org, Google Play and the App Store -"
  " all for a NATURE-identification app (ObsIdentify); the PAA is about nature and activity"
  " tracking. The education meaning barely surfaces (2gno's teacher listicle at #9), so mos"
  "t of the 90 monthly searches are not our buyer, and chasing the bare phrase would be cha"
  "sing the wrong SERP. What to do on /classroom-observation-app-features-that-support-teac"
  "her-growth/:\n\nDO THIS:\n1. Optimize for the QUALIFIED variants - 'teacher observation app"
  "', 'classroom observation app' - in title, H1 and headings; those SERPs are education-ow"
  "ned and are where our GSC impressions actually sit.\n2. Add an honest comparison section "
  "naming the real alternatives (Classroom Mosaic, Observation Copilot, GoReact, IRIS Conne"
  "ct, Education Walkthrough) with one paragraph each on fit - 2gno's comparison listicle i"
  "s the only education result that cracks even the polluted SERP, and comparison is also w"
  "hat the AI assistants cite (1.6 finding).\n3. Verify EW's own App Store / Google Play lis"
  "tings are complete and keyword-accurate - store listings rank organically on app queries"
  ", and ours is a rankable asset we control."
 ),
 "Marzano depth": (
  "DEPTH IS OBSERVED HERE.\n\nWHAT THE LIVE SERP SHOWS: fold PAA-anchored sections into the 1"
  ".5 rebuild of /marzano-framework/. Unlike the Danielson SERP, the Marzano winners ARE co"
  "mprehensive: marzanoevaluationcenter.com at 3,037 words ('Why the Marzano Elements Work'"
  ", the research behind the model) and 2gno at 5,378 words ('Breaking Down the Marzano Rub"
  "ric's Four Domains', 'How Marzano Measures Teacher Performance'). Our page is 3,017 word"
  "s - length is fine; the gap is the specific sections. Add, answering the PAA directly:\n\n"
  "DO THIS:\n1. H2 'The four domains of the Marzano evaluation model' - named, with element "
  "counts (our page covers the nine strategies but never the domain structure people search"
  ").\n2. H2 'The Marzano scale' - Not Using / Beginning / Developing / Applying / Innovatin"
  "g, with what an observer records at each level.\n3. Short FAQ entries for the remaining P"
  "AA: 'Marzano's six steps', 'the 5 dimensions of learning', 'what is domain 4' - two-3 se"
  "ntences each.\n4. One comparison line linking /danielson-rubric/.\n\nNOTE: Same page as 1.5"
  "'s #1 candidate (208 clicks, 12-month slide): one ticket, not two."
 ),
 "Walkthrough forms": (
  "MAKE THE FORMS VISIBLE AND DOWNLOADABLE.\n\nWHAT THE LIVE SERP SHOWS: the SERP splits betw"
  "een guidance and downloads. Observed winners: principalcenter.com's 2,112-word essay on "
  "when forms help ('Two Advantages of Forms', 'When Forms Are The Right Tool', 'Narrow Foc"
  "us, Or Eyes Wide Open?') and TeachersPayTeachers product cards ('FREE 5-Minute Classroom"
  " Walkthrough Checklist | Principal & Administrator Tool'). A weak 73-word help page also"
  " ranks #2, so this SERP is takeable. Our /teacher-observation-templates/ (3,038 words, 2"
  "06 clicks - edit with care) already has the substance; what it lacks:\n\nDO THIS:\n1. The w"
  "ord 'forms' - the page says 'templates' throughout; add H2 'Classroom walkthrough forms'"
  " and use both vocabularies naturally.\n2. A visible download grid near the top: form name"
  ", framework it fits, length, download link - the TpT cards winning here are essentially "
  "download grids.\n3. A '5-minute walkthrough checklist' as a named download - that exact f"
  "raming is the top TpT product, proving the demand.\n4. A short 'when to use a form vs ope"
  "n notes' section - principalcenter's guidance angle, condensed, so the page serves both "
  "intents the SERP shows."
 ),
}

NOTE = (" BRIEF REBUILT 2026-08-18 from parsed top-3 winners + People Also Ask "
        "(gap_analysis/2026-08-serp-winners.json) after the first draft was "
        "found generalising from a single competitor page.")


def main():
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    sid = reg["educationwalkthrough"]["sheet_id"]
    rows = S.read(sid, f"'{TAB}'!A9:J16")
    body_i, body_j = [], []
    for r in rows:
        cl = str(r[0]).strip()
        assert cl in BRIEFS, f"unknown cluster row: {cl!r}"
        body_i.append([BRIEFS[cl]])
        body_j.append([str(r[9]) + NOTE if len(r) > 9 else NOTE])
    S.write(sid, f"'{TAB}'!I9:I16", body_i)
    S.write(sid, f"'{TAB}'!J9:J16", body_j)
    print(f"rewrote {len(body_i)} briefs + notes")


if __name__ == "__main__":
    main()
