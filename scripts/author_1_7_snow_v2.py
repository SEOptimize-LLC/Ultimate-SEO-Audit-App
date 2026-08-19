"""Author Snow's REBUILT 1.7 analysis (v2) and refill the tab.

Owner redirection 2026-08-18: competitor set = Lumineux / Auraglow /
Opalescence (Crest and Colgate EXCLUDED as multi-category CPG fixtures);
coverage = the full whitening product range; routing = commercial-first
(product/collection pages are the targets, blog posts are feeders). All
positions live-verified this session; winner formats parsed; PAA quoted.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fill_1_7  # noqa: E402

NL = chr(10)
SN = "https://www.trysnow.com"

RICH = ("The observed winning format across every cluster: SPECIALIST PRODUCT "
        "PAGES WITH ARTICLE DEPTH - education, mechanism and FAQ living on "
        "the product page itself, below the buy box.")


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


clusters = [
 cl("Whitening strips",
    "teeth white strips (60,500); dental whitening strip (60,500); bleaching "
    "strips for teeth (60,500); at-home teeth whitening strips (5,400); "
    "whitening strip variants (~5,000 more across 41 verified queries)", 193170,
    SN + "/products/teeth-whitening-strips", 981,
    "Commercial (core product line)", "opalescence.com",
    "https://opalescence.com/products/whitening-strips",
    brief("ENRICH THE STRIPS PRODUCT PAGE TO THE OBSERVED SPECIALIST FORMAT.",
     "Opalescence ranks #3 with a 1,231-word PRODUCT page; Amazon #4 and "
     "NBC's roundup #5 are fixtures. The PAA is efficacy-anxiety: 'Do tooth "
     "whitening strips really work?', 'What are the negatives of teeth "
     "whitening strips?', 'Which teeth whitening strips are the best?'. Our "
     "strips page earns 981 clicks - real traction on a page that answers "
     "none of these on-page.",
     ["Add a below-buy-box education block to /products/teeth-whitening-"
      "strips: H2 'Do whitening strips really work?' (mechanism, peroxide "
      "percentage, expected shades), H2 'The negatives, honestly' "
      "(sensitivity, gum contact, enamel questions answered with the "
      "hydroxyapatite angle Snow uniquely owns).",
      "Fold the dissolving-strips differentiator into the same page's copy "
      "- 'no-rinse dissolving strips' is a genuine format advantage no "
      "ranking page mentions.",
      "FAQ schema on the added Q&As.",
      "Feeder pass: the strips blog posts (do-purple-strips-work 460 "
      "clicks, strips-expire, left-on-too-long) all link the product page "
      "with commercial anchors - today they end without routing the "
      "reader.",
      "EDIT WITH CARE: 981 clicks; nothing above the buy box changes."],
     note=RICH + " Volume caveat: the three 60,500 heads are one demand "
          "pool - honest opportunity ~65,000/mo, not 193k.",
     target="#4-#6 beside Opalescence, above the thin Amazon card."),
    "Cluster 193,170/mo nominal / ~65,000 honest. Live-verified: "
    "Opalescence #3 on 41 strip queries, us absent on the heads while our "
    "product page earns 981 clicks on the tail."),

 cl("Whitening kits and LED devices",
    "teeth whitening products (18,100); teeth whitening kit (12,100); white "
    "teeth kits (12,100); tooth bleaching kits (12,100); teeth whitening "
    "system (6,600); led whitening teeth kit (1,900); led teeth whitening "
    "device (1,000); + 80 more verified variants", 232260,
    SN + "/products/teeth-whitening-kit", 1385,
    "Commercial (flagship product)", "lumineuxhealth.com",
    "https://lumineuxhealth.com/products/whitening-kit-all",
    brief("MAKE THE KIT PAGE THE DEEPEST PRODUCT PAGE ON THE SERP - the "
          "winner is a 2,555-word product page.",
     "Lumineux #3 (2,555-word product page), Auraglow #4 (1,466 words), "
     "Forbes #5 (publisher fixture). PAA: 'What teeth whitening kit works "
     "best?', 'What is the best at-home teeth whitening kit?', 'Can old "
     "yellow teeth be whitened?'. Our kit page is the site's #1 product "
     "asset (88,182 impressions, 1,385 clicks) and competes at a fraction "
     "of the winners' on-page depth.",
     ["Expand /products/teeth-whitening-kit below the buy box to "
      "Lumineux-class depth: how the LED system works (wavelength, serum "
      "chemistry), what results to expect by week, 'can old/yellow teeth "
      "be whitened' answered honestly (intrinsic vs extrinsic staining).",
      "Add an on-page comparison row: Snow vs generic LED kits vs strips "
      "vs dentist trays - the 'what works best' PAA answered with candour "
      "including when a cheaper option is enough.",
      "Surface the DiamondSeries wireless kit as the pro-tier upsell "
      "within the same page's narrative rather than a separate orphan.",
      "Feeder pass: the HYROX-class asset here is the review/press "
      "coverage - link press mentions into the product page.",
      "EDIT WITH CARE: 1,385 clicks; additions only."],
     note=RICH + " The 60,500 'professional teeth whiteners' head from the "
          "earlier run also lands here - kit positioning against the "
          "dentist chair (Opalescence's home turf).",
     target="#4-#6 among the specialists; Forbes holds the publisher slot."),
    "Cluster ~232,260/mo nominal, heavy shared pools (honest ~50-60k). "
    "Live-verified: Lumineux #3, Auraglow #4. Our page: 1,385 clicks - "
    "the flagship."),

 cl("Whitening pen",
    "teeth whitening pen (9,900); bleaching pen (4,400); whitening pen "
    "(4,400); white pen teeth (880); + overnight/serum variants", 20620,
    SN + "/products/teeth-whitening-pen", 647,
    "Commercial (striking distance with click evidence)",
    "lumineuxhealth.com",
    "https://lumineuxhealth.com/products/bright-teeth-whitening-pen",
    brief("THE CLEANEST WIN ON THIS TAB - a 489-word DTC page ranks #5.",
     "Lumineux #4 (1,797 words), novashinesmile.com #5 with only 489 words "
     "- a small DTC brand holds a top-5 slot with a thin page, which "
     "means this SERP is soft. Allure #6 is the publisher. PAA: 'Does the "
     "teeth whitening pen really work?', 'How long do I leave a teeth "
     "whitening pen on?', 'What are the potential side effects?'. Our pen "
     "page already earns 647 clicks - the exact striking-distance profile "
     "(traction + reachable SERP).",
     ["Enrich /products/teeth-whitening-pen with the usage answers: 'how "
      "long to leave it on', 'how often', 'does it really work' with the "
      "serum mechanism - the PAA is usage anxiety and no winner answers "
      "it well.",
      "Position the Overnight Pen and Purple Serum as variants ON this "
      "page (use-case selector) so the pen family consolidates rather "
      "than splitting three thin pages.",
      "Side-effects honesty section (sensitivity, gum contact) - the "
      "trust answer that converts.",
      "FAQ schema on the added Q&As."],
     target="#3-#5 - displacing a 489-word page with a 647-click asset is "
            "the most winnable head-term slot in Snow's workbook."),
    "Cluster 20,620/mo. Live-verified: 489-word page at #5 (soft SERP). "
    "Our page: 647 clicks - best viability profile on this tab."),

 cl("Whitening toothpaste and hydroxyapatite",
    "paste for whitening teeth (49,500 family head); 10 nano hydroxyapatite "
    "toothpaste (2,400); hydroxyapatite/sensitive variants; purple "
    "toothpaste family (site already ranks)", 52000,
    SN + "/collections/toothpaste", 327,
    "Commercial (product line + differentiator)", "opalescence.com",
    "https://opalescence.com/products/complete-whitening-toothpaste",
    brief("ROUTE THE TOOTHPASTE DEMAND AT THE COLLECTION AND PRODUCT PAGES "
          "- the 40-post blog library becomes the feeder network.",
     "Amazon #2 (fixture), Opalescence #4 with a 1,223-word product page, "
     "health.com #5 (publisher). PAA: 'Which paste is best for teeth "
     "whitening?', 'What paste do dentists use?', 'Does tooth whitening "
     "paste actually work?'. Lumineux ranks #10 on '10 nano hydroxyapatite "
     "toothpaste' - a product Snow LITERALLY SELLS (10% Hydroxyapatite "
     "Toothpaste) with no page contesting it. Our collection earns 327 "
     "clicks; the 40+ toothpaste blog posts earn scattered clicks and "
     "link products weakly.",
     ["Enrich /collections/toothpaste with a buying-guide block: whitening "
      "mechanism comparison (peroxide vs hydroxyapatite vs abrasive), "
      "'which is best for you' selector by need (sensitive, purple "
      "color-correct, extra strength).",
      "Give the 10% Hydroxyapatite product page the nano-HA search "
      "framing in title and copy - 2,400/mo names our exact product and "
      "Lumineux takes it at #10 with a listicle.",
      "Feeder pass across the toothpaste blog library: every post links "
      "the collection or the specific product with commercial anchors; "
      "the earlier-run rebuild of the best-whitening-toothpaste guide "
      "stays, repositioned as the library's hub POINTING at products.",
      "Fix the anchor-fragment URL splitting on these posts (GSC shows "
      "dozens of #section phantom rows) - same TOC issue as EW."],
     note=RICH,
     target="#4-#6 beside Opalescence; Amazon holds #2."),
    "Cluster ~52,000/mo honest. Live-verified: Opalescence #4, Lumineux "
    "#10 on our own product's name-term. Collection: 327 clicks."),

 cl("Peroxide-free and sensitive whitening",
    "peroxide free teeth whitening strips (8,100); enamel safe whitening "
    "strips (1,900); peroxide free teeth whitening (1,000); "
    "desensitizing/sensitive whitening variants (~7,000)", 27000,
    SN + "/products/sensitive-hydroxyapatite-toothpaste", 78,
    "Commercial (positioning territory)", "lumineuxhealth.com",
    "https://lumineuxhealth.com/products/super-pack-whitening-strips-21-treatments",
    brief("CONTEST LUMINEUX'S HOME TURF WITH THE HYDROXYAPATITE STORY - "
          "this is a positioning battle, not a page count.",
     "This cluster IS Lumineux's brand positioning ('peroxide-free, "
     "enamel-safe') - their 2,129-word super-pack page ranks #4 with "
     "Amazon #3 and a dental trade publication #6. PAA: 'Are peroxide-free "
     "strips effective?', 'What are the safest whitening strips?'. Snow's "
     "counter-asset is real: hydroxyapatite products (sensitive toothpaste, "
     "HA powder) and dissolving strips - but no page tells the "
     "enamel-safety story as a story.",
     ["Build the enamel-safe/sensitive angle INTO the relevant product "
      "pages (sensitive HA toothpaste, dissolving strips): what "
      "hydroxyapatite does for enamel, peroxide-free options in the range, "
      "'safest way to whiten' answered honestly including when peroxide "
      "is fine.",
      "One comparison block: peroxide vs peroxide-free trade-offs "
      "(speed vs sensitivity) - the efficacy PAA answered with candour "
      "Lumineux's marketing page avoids.",
      "Do NOT spin up a standalone informational hub first - route the "
      "story through the pages that sell the products; the blog library "
      "supports with existing sensitivity posts linked as feeders."],
     target="#4-#6; Lumineux will hold its brand-positioning slot, the "
            "target is standing beside it as the hydroxyapatite "
            "alternative."),
    "Cluster ~27,000/mo. Live-verified: Lumineux #4 (their positioning "
    "turf), Amazon #3. Our angle: hydroxyapatite, which they cannot "
    "claim."),
]

backlinks = [
 {"target": "NBC Select / Forbes / Allure / health.com whitening roundups",
  "comp_page": "these publisher pages rank INSIDE all five cluster SERPs "
               "(NBC #5 strips, Forbes #5 kits, Allure #6 pens, health.com "
               "#2/#5) and are the AI assistants' cited sources (1.6)",
  "our_page": SN + "/products/teeth-whitening-kit",
  "quality_note": "The dual-channel play: one roundup inclusion moves the "
   "SERP slot AND the AI answer (1.6 showed Snow losing to Crest in "
   "publisher-fed AI responses). Product-PR outreach with test units; the "
   "dissolving-strips format and hydroxyapatite line are the fresh angles "
   "editors need. Route to PR.", "routed": "Y"},
 {"target": "electricteeth.com and independent review sites",
  "comp_page": "review sites in the scoped SERPs' tails",
  "our_page": SN + "/",
  "quality_note": "Niche oral-care reviewers - relevance-first targets for "
   "test-unit submissions.", "routed": "Y"},
 {"target": "us.dental-tribune.com",
  "comp_page": "ranks #6 on the peroxide-free cluster",
  "our_page": SN + "/products/sensitive-hydroxyapatite-toothpaste",
  "quality_note": "Dental trade press ranking on consumer whitening-safety "
   "queries - a hydroxyapatite clinical angle could earn coverage that "
   "serves both authority and the sensitive cluster.", "routed": "Y"},
 {"target": "Lumineux/Auraglow/Opalescence domain gaps (1,828 domains)",
  "comp_page": "the bulk of all three competitors' profiles",
  "our_page": "n/a",
  "quality_note": "DO NOT CHASE domain-by-domain: affiliate and coupon "
   "volume (Opalescence hit the API cap). Their page-level link counts on "
   "the RANKING pages are 1-4 - these SERPs are won on-page. The "
   "reachable equivalent of their press volume is the PR row above.",
  "routed": "N"},
]

doc = {
 "competitor_set":
  "Lumineux (lumineuxhealth.com), Auraglow (auraglow.com), Opalescence "
  "(opalescence.com) - owner-confirmed set 2026-08-18. Crest and Colgate "
  "EXCLUDED by owner decision as multi-category CPG authorities: they "
  "dominate SERPs on domain weight, not whitening-specialist strategy, so "
  "benchmarking against them measures authority we cannot copy. 434 gaps "
  "live-verified against the specialist set across the full product range. "
  "PRODUCT-LINE FLAGS for the owner (demand competitors capture with "
  "products Snow does not sell - merchandising decisions, not SEO briefs): "
  "whitening trays (~17,000/mo, Opalescence Go) and whitening mouthwash "
  "(~15,000/mo, Lumineux). In-office/dentist queries and competitor blog "
  "fluff excluded on relevance. Snapshot: gap_analysis/2026-08-serps.json",
 "baseline_note":
  "Baseline month - no stored prior SERP set. Snapshot saved; September "
  "answers this cell by diff. Routing rule applied per owner correction: "
  "product/collection pages are the investment targets, blog posts are "
  "internal-link feeders.",
 "clusters": clusters, "backlinks": backlinks}

reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
out = Path(reg["snow"]["folder"]) / "gap_analysis" / "analysis.yaml"
out.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True,
                              width=100), encoding="utf-8")
print(f"snow v2: analysis.yaml ({len(clusters)} clusters)")
fill_1_7.main("snow")
