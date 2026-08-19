"""Author Snow's and Arsenal's 1.7 analysis files and fill both tabs - the
final two of eight. Same evidence standard throughout; Arsenal's briefs lead
with the 1.4 SPA blocker because content work on unreadable pages is wasted."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fill_1_7  # noqa: E402

NL = chr(10)
SN = "https://www.trysnow.com"
AR = "https://www.arsenalhealth.com"


def brief(head, serp, dos, note=None, target=None):
    lines = [head, "", "WHAT THE LIVE SERP SHOWS: " + serp, "", "DO THIS:"]
    lines += [f"{i}. {d}" for i, d in enumerate(dos, 1)]
    if note:
        lines += ["", "NOTE: " + note]
    if target:
        lines += ["", "REALISTIC TARGET: " + target]
    return NL.join(lines)


def cl(name, kws, vol, page, clicks, intent, comp, curl, br, comments):
    return {"cluster": name, "keywords": kws, "volume": vol, "clicks": clicks,
            "intent": intent, "competitor": comp, "their_url": curl,
            "our_page": page, "brief": br, "comments": comments}


def snow():
    clusters = [
     cl("Whitening toothpaste family",
        "best toothpaste for whitening (49,500); best rated toothpaste for "
        "whitening (49,500); whitening teeth with toothpaste (49,500); good "
        "toothpaste for teeth whitening (49,500); toothpaste that whitens "
        "teeth (49,500); teeth whitening toothpaste (8,100); what toothpaste "
        "is best for whitening teeth (8,100); what toothpaste whitens the "
        "best (8,100); fluoride toothpaste for teeth whitening (2,900)", 274700,
        SN + "/blogs/news/best-whitening-toothpaste", 6,
        "Commercial (product family Snow sells)", "crest.com",
        "https://crest.com/en-us/oral-care-tips/toothpaste/best-whitening-toothpaste",
        brief("REBUILD THE BEST-WHITENING-TOOTHPASTE GUIDE INTO THE HONEST "
              "RANKED LIST - Snow already owns the supporting library.",
         "health.com holds #2 (publisher fixture) and an NCBI stub sits #4; "
         "the comparables are Crest's 1,113-word advice page at #5 and "
         "Supersmile's PRODUCT page ranking across variants. The PAA is a "
         "ranking demand: 'What is the #1 teeth whitening toothpaste?', "
         "'What is the most effective whitening toothpaste?', 'What ... "
         "actually works?'. Snow's own /blogs/news/best-whitening-toothpaste "
         "earns 6 clicks - while the site holds 40+ supporting toothpaste "
         "posts and a toothpaste collection earning 327 clicks. The library "
         "exists; the flagship page does not rank.",
         ["Rebuild /blogs/news/best-whitening-toothpaste as a genuine ranked "
          "list that answers 'what is the #1' directly: include Crest, "
          "Colgate Optic White and hydroxyapatite options alongside Snow's - "
          "the honest-comparison pattern is what both the SERP and the 1.6 "
          "AI answers reward, and a Snow-only page reads as an ad.",
          "One mechanism section: peroxide vs hydroxyapatite vs abrasives - "
          "what actually whitens vs what polishes (the 'actually works' "
          "PAA), citing the existing deep posts.",
          "Internal-linking pass: the 40+ toothpaste posts link the flagship "
          "guide with 'best whitening toothpaste' anchors; today they link "
          "products or nothing, splitting the topic's authority.",
          "Fix the anchor-fragment splitting visible in GSC (dozens of "
          "#section rows on these posts) - same Elementor-style TOC issue "
          "found on EW; impressions are being scattered across phantom "
          "URLs."],
         note="Volume caveat: the five 49,500 variants share one demand pool "
              "- treat ~50-60k/mo as the honest opportunity, not 274k. "
              "Publisher fixtures (health.com, Forbes-class) cap the top; "
              "they are also section B targets.",
         target="#4-#6 beside Crest's advice page. Ranking the guide also "
                "feeds the 1.6 AI gap - assistants cite exactly this page "
                "type."),
        "Cluster ~274,700/mo nominal, ~55,000 honest (shared pools). "
        "Live-verified: Crest #5, Supersmile product page across variants, "
        "us absent with a 6-click page."),

     cl("Professional teeth whitening kits",
        "professional teeth whiteners (60,500)", 60500,
        SN + "/products/teeth-whitening-kit", 1385,
        "Commercial (core product)", "supersmile.com",
        "https://www.supersmile.com/products/professional-teeth-whitening-system-home-kit-sensi",
        brief("POSITION THE KIT PAGE AGAINST THE PROFESSIONAL QUESTION - "
              "the PAA is a dentist-vs-home decision.",
         "Opalescence #2 (2,128 words - a dentist-channel brand), a med-spa "
         "at #4, Supersmile's kit product page at top-10. PAA: 'What do "
         "professional dentists use to whiten teeth?', 'Is it worth getting "
         "your teeth professionally whitened?', 'What is the most effective "
         "whitening agent?'. The searcher is deciding between the dentist "
         "chair and a professional-grade home kit - our "
         "/products/teeth-whitening-kit (88,182 impressions, 1,385 clicks) "
         "is the answer but never engages the question.",
         ["Add a 'Professional whitening at home vs the dentist chair' "
          "section to the kit page: same active agents (peroxide "
          "concentrations compared honestly), cost per session vs the kit, "
          "when the dentist is genuinely the right call.",
          "Answer 'what do dentists use' factually (opalescence-class "
          "trays, in-office light systems) - naming the dentist-channel "
          "reality earns the credibility that converts the at-home buyer.",
          "Surface the strongest proof on-page: clinical/whitening-agent "
          "specifics and review volume - Opalescence wins on authority "
          "signals, not page depth.",
          "EDIT WITH CARE: 1,385 clicks. Add sections below the buy box; "
          "touch nothing above it."],
         target="#4-#6; Opalescence's dentist-brand slot is the ceiling."),
        "Single-keyword cluster, 60,500/mo. Live-verified: Supersmile top-10 "
        "with a product page. Our kit page: 88,182 impressions / 1,385 "
        "clicks - edit with care."),
    ]

    backlinks = [
     {"target": "Forbes / Fortune / NYTimes (Wirecutter) / USNews whitening "
                "roundups",
      "comp_page": "these publisher pages hold 4+ slots on every scoped Snow "
                   "SERP and are the AI assistants' top-cited sources (1.6)",
      "our_page": SN + "/products/teeth-whitening-kit",
      "quality_note": "Snow's SERPs are publisher-owned: the same roundups "
       "rank in Google AND feed ChatGPT/Gemini answers where Crest wins "
       "(1.6 finding). Product-PR outreach for roundup inclusion is the "
       "single highest-leverage visibility play for this client - one "
       "placement moves both channels. Route to PR, not classic "
       "link-building.", "routed": "Y"},
     {"target": "electricteeth.com",
      "comp_page": "review site appearing in scoped SERPs (single hits)",
      "our_page": SN + "/",
      "quality_note": "Independent oral-care review site - niche-relevant, "
       "review-driven. Ask: product submission for testing.", "routed": "Y"},
     {"target": "crest.com / supersmile.com domain gaps (1,388 domains "
                "combined)",
      "comp_page": "the bulk of both competitors' referring domains",
      "our_page": "n/a",
      "quality_note": "DO NOT CHASE. CPG-scale profiles (Crest hit the "
       "1,000-domain API cap) built on retail, coupon and press volume a "
       "DTC brand cannot and should not replicate link-by-link. The "
       "reachable equivalent is the roundup/PR row above.", "routed": "N"},
    ]

    return {
     "competitor_set":
      "Crest (crest.com), Supersmile (supersmile.com). The only same-type "
      "product brands ranking in Snow's 9 scoped live US SERPs 2026-08-18 - "
      "everything else on these SERPs is publisher fixtures (Forbes, "
      "Fortune, NYT, USNews), marketplaces (Amazon) or dentist practices. "
      "Gap discovery was topically filtered to whitening terms (Crest ranks "
      "for thousands of irrelevant oral-care keywords). Publishers are "
      "section B targets, not competitors. Snapshot: "
      "gap_analysis/2026-08-serps.json",
     "baseline_note":
      "Baseline month - no stored prior SERP set. Snapshot saved; September "
      "answers this cell by diff.",
     "clusters": clusters, "backlinks": backlinks}


def arsenal():
    GATE = ("PREREQUISITE (1.4 finding): arsenalhealth.com serves 8 words of "
            "raw HTML on every route - the site is a client-rendered SPA "
            "that AI crawlers cannot read and Google must render to index. "
            "The server-rendering fix routed in 1.4/2.1 comes before or "
            "alongside any content work below; new content on unreadable "
            "pages is wasted effort.")
    clusters = [
     cl("Personal training Denver",
        "athlete personal trainer (320); athlete personal training (210); "
        "male personal trainer (210); personal training club (170); club "
        "trainers (880 - partly competitor-brand, discounted)", 910,
        AR + "/gym/one-on-one-personal-training-denver", 0,
        "Commercial (documented worst competitive loss)",
        "clubformdenver.com", "https://www.clubformdenver.com/trainers",
        brief("REBUILD THE PERSONAL TRAINING PAGE AROUND PROOF AND PRICE - "
              "after the render fix.",
         "The SERP is soft: Rocky Mtn Athletics ranks #5 with 255 words, "
         "Unite Rehab #6 with 1,150, ZipRecruiter #7 is a fixture. Form's "
         "trainers page ranks on trainer-roster proof. PAA is price-led: "
         "'How much does an athletic trainer cost?', 'Is $400 a month a lot "
         "for a personal trainer?'. Arsenal's own blog already holds the "
         "cost asset (/blog/how-much-does-a-personal-trainer-cost, 5,855 "
         "impressions) while the service page "
         "/gym/one-on-one-personal-training-denver earns zero clicks. "
         "Context from the July analysis: 'personal trainer arvada' #48 vs "
         "a competitor at #12 - this is the client's named worst loss.",
         [GATE,
          "Rebuild the service page with a trainer roster (name, specialty, "
          "credential, photo) - the proof pattern Form's ranking page uses "
          "and ours lacks.",
          "Answer the price PAA on the service page: monthly ranges, what "
          "$400/month buys at Arsenal vs a big-box gym - and link the "
          "existing cost post both ways (it has the impressions; the "
          "service page has the conversion).",
          "Fold the pain-specific training pages (back/knee/shoulder, all "
          "near-zero) into the main page as sections unless each earns its "
          "keep - six thin SPA pages split what one strong page could "
          "hold.",
          "Female-trainer page (1,365 impressions) gets the same roster "
          "treatment - it is the only training page with real demand "
          "today."],
         note="A 255-word page ranks #5 here: the field is weak and the "
              "loss is fixable once pages are renderable.",
         target="#4-#6 post-render-fix; top 3 with roster + price "
                "transparency."),
        "Cluster ~910/mo relevant volume. Live-verified: 255-word page at "
        "#5 (soft field). Gated on the 1.4 SPA fix."),

     cl("Denver gym head terms",
        "the gym colorado (720); denver gym and fitness (590); private gym "
        "denver (40)", 1350,
        AR + "/gym", 0, "Commercial (category head)",
        "lohiathleticclub.com", "https://www.lohiathleticclub.com/",
        brief("MAKE /gym THE ANSWER TO 'BEST GYM IN DENVER' QUESTIONS - "
              "after the render fix.",
         "denvergymandfitness.com ranks #3 on its own brand-adjacent terms "
         "with 356 words; Instagram #5 and Yelp #6 are fixtures; LoHi "
         "Athletic (2,120/mo of brand demand) wins on neighbourhood "
         "identity. PAA: 'What is the best gym in Denver, Colorado?', "
         "'What is the name of the luxury gym in Denver?'. Arsenal's /gym "
         "page: 244 impressions, zero clicks - and 8 words of raw HTML.",
         [GATE,
          "Position /gym on the differentiator no Denver competitor owns: "
          "training gym + health optimization under one roof (HYROX "
          "prep, hormone/PRP clinic integration) - the 'luxury/serious "
          "gym' PAA is asking for exactly this positioning.",
          "Neighbourhood specificity: where in Denver, parking, distance "
          "from LoHi/RiNo/Highlands - LoHi Athletic wins on place identity; "
          "Arsenal's page names no neighbourhood.",
          "Leverage the HYROX authority (the blog's 157-click flagship "
          "post) with prominent links into /gym - the content engine "
          "already earns the audience; the service page never receives "
          "it.",
          "Answer 'best gym in Denver for serious training' with proof: "
          "coach credentials, member results, facility specifics."],
         note="LoHi's 1,600/mo brand demand shows what neighbourhood-"
              "identity branding earns; Arsenal cannot copy it but can own "
              "the training+health-optimization category.",
         target="#4-#6 among the fixtures once pages render."),
        "Cluster ~1,350/mo. Live-verified: 356-word page at #3 (soft "
        "field). Gated on the 1.4 SPA fix. Excluded on relevance: Form's "
        "rooftop-facility terms, DPM's medical clusters (dry needling, "
        "posture, stem cell - no Arsenal service pages exist), and all "
        "PED/aesthetics-adjacent territory per the standing client "
        "constraint."),
    ]

    backlinks = [
     {"target": "5280.com (Denver's city magazine)",
      "comp_page": "appears in Arsenal's scoped SERPs (gym/fitness "
                   "editorial)",
      "our_page": AR + "/gym",
      "quality_note": "THE Denver editorial authority - best-gyms and "
       "fitness roundups are its staple. HYROX-in-Denver is a genuinely "
       "pitchable story (Arsenal already beats F45/Orangetheory on HYROX "
       "terms). Route to PR.", "routed": "Y"},
     {"target": "LoHi/Form link sources - Denver neighbourhood and "
                "fitness-community sites",
      "comp_page": "lohiathleticclub.com (146 refdoms) and clubformdenver "
                   "(80) profiles",
      "our_page": AR + "/",
      "quality_note": "Both competitors' profiles are small and largely "
       "local/organic - neighbourhood associations, Denver fitness "
       "blogs, event listings. The replicable pattern is community "
       "presence (HYROX events, local partnerships), not link outreach at "
       "volume.", "routed": "Y"},
     {"target": "ZipRecruiter / Instagram / Yelp slots",
      "comp_page": "fixtures occupying the scoped SERPs",
      "our_page": AR + "/",
      "quality_note": "SERP occupants: complete the Yelp/Google profiles "
       "and keep Instagram active - routed to profiles/social, not "
       "backlinks.", "routed": "N"},
     {"target": "denverphysicalmedicine.com's medical-content linkers",
      "comp_page": "116-domain gap",
      "our_page": "n/a",
      "quality_note": "DO NOT CHASE: they link medical content (dry "
       "needling, physiatry) Arsenal does not offer; pursuing them would "
       "drag the site toward the YMYL medical territory the July analysis "
       "flagged as a quality drag.", "routed": "N"},
    ]

    return {
     "competitor_set":
      "Denver Physical Medicine (denverphysicalmedicine.com), Club Form "
      "(clubformdenver.com), LoHi Athletic Club (lohiathleticclub.com). "
      "Chosen from 12 live Denver SERPs 2026-08-18 - the actual local "
      "field. RELEVANCE CUTS: DPM's largest ranking clusters (dry "
      "needling, posture, stem cell, cupping, B12) have NO corresponding "
      "Arsenal service pages and were excluded; Form's rooftop-facility "
      "terms are facility-specific; PED/aesthetics territory excluded per "
      "standing client constraint. Publishers (5280.com) are section B. "
      "Snapshot: gap_analysis/2026-08-serps.json",
     "baseline_note":
      "Baseline month - no stored prior SERP set. Snapshot saved; "
      "September answers this cell by diff. Both clusters gated on the "
      "1.4 server-rendering fix.",
     "clusters": clusters, "backlinks": backlinks}


def main():
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    for slug, fn in (("snow", snow), ("arsenal", arsenal)):
        doc = fn()
        out = Path(reg[slug]["folder"]) / "gap_analysis" / "analysis.yaml"
        out.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True,
                                      width=100), encoding="utf-8")
        print(f"{slug}: analysis.yaml ({len(doc['clusters'])} clusters)")
        fill_1_7.main(slug)


if __name__ == "__main__":
    main()
