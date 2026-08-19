"""Author Superior's and Comfort's 1.7 analysis files and fill both tabs.

Same evidence standard as Beehive/SameDay: every position live-verified in a
Salt Lake City SERP, every format claim from a parsed winner, PAA quoted from
the live pull, link targets relevance-filtered with deliberate-N junk warnings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fill_1_7  # noqa: E402

NL = chr(10)


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


SUP = "https://superiorwaterandair.com"
COM = "https://www.comfortsolutionsutah.com"


def superior():
    clusters = [
     cl("Water softener Utah",
        "water softener utah (480); soft water system utah (480); water "
        "softener installation utah (170); water softener repair utah (110); "
        "salt lake city water softener (110); expert water systems (90)", 1440,
        SUP + "/water/water-treatment/", 30, "Commercial (flagship line)",
        "nusoftwatersystems.com", "https://www.nusoftwatersystems.com/",
        brief("MAKE THE FLAGSHIP PAGE ANSWER UTAH'S THREE QUESTIONS - the PAA "
              "is entirely local.",
         "Reddit #4 is a fixture; the comparables are NuSoft's homepage #6 "
         "(1,570 words) and Kinetico Utah #7 (4,642 words) - specialist depth "
         "ranks. The PAA is remarkable in how local it is: 'Is a water "
         "softener worth it in Utah?', 'How much does a water softener cost "
         "in Utah?', 'Does Utah have hard or soft water?'. Our "
         "/water/water-treatment/ already carries 28,466 impressions for 30 "
         "clicks - the demand finds the page and does not click it.",
         ["H2 'Is a water softener worth it in Utah?' - answered with actual "
          "Wasatch Front hardness numbers (grains per gallon by city) and "
          "what that does to appliances. This is the #1 PAA and the page's "
          "natural opening argument.",
          "H2 'What a water softener costs in Utah' - equipment tiers plus "
          "installed ranges; the cost PAA appears twice in different forms.",
          "H2 'Softener repair or replace' section covering the repair-intent "
          "queries (110/mo) the page currently ignores.",
          "Named-system credibility: what Superior installs and why, against "
          "Kinetico's 4,642-word product depth - one honest comparison "
          "paragraph per tier, not a catalogue."],
         note="This is 1.5's flagship-line candidate - one combined rebuild. "
              "28k impressions means the ranking exists; the page loses the "
              "click.",
         target="#4-#6, beside NuSoft and above Kinetico's dealer page."),
        "Cluster ~1,440/mo. Live-verified: NuSoft #6, Kinetico #7, us outside. "
        "Our page: 28,466 impressions / 30 clicks May-Jul."),

     cl("Salt Lake City HVAC head terms",
        "salt lake city heating and air conditioning (210); heating and air "
        "utah variants via Manwill (420); contractors hvac utah (140); "
        "furnace repair utah (140); furnace replacement salt lake city (40)", 950,
        SUP + "/hvac/furnace-repair/", 2, "Commercial", "manwill.net",
        "https://manwill.net/",
        brief("GIVE THE HVAC PAGES THE COST ANSWERS - and mind the $5000 rule "
              "PAA.",
         "Yelp #4 fixture; Utah Heating & Cooling #5 ranks with only 970 "
         "words, Manwill #7 with 2,034 - this SERP is winnable at moderate "
         "depth. PAA: 'What is the $5000 rule for HVAC?', 'What are the best "
         "HVAC companies in Salt Lake City?'. Our /hvac/furnace-repair/ "
         "carries 20,609 impressions for TWO clicks - same pattern as the "
         "water page: ranked but unclicked.",
         ["H2 'The $5,000 rule: repair or replace your HVAC system' on the "
          "furnace/HVAC pages - age times repair cost, honest thresholds; "
          "the PAA every Utah HVAC SERP in this workbook shares.",
          "H2 'What HVAC service costs in Salt Lake City' - service call, "
          "repair ranges, and what changes them.",
          "Title/meta pass on /hvac/furnace-repair/: 20k impressions at 2 "
          "clicks is a snippet failure as much as a position issue - rewrite "
          "toward the question-answer framing the PAA shows.",
          "Cross-link the 1.5 candidate work on this exact page ('furnace "
          "repair salt lake city' at 7.1) - one rebuild, both tabs."],
         target="#5-#7 behind the Yelp fixture; UHC's 970-word slot shows "
                "the bar."),
        "Cluster ~950/mo. Live-verified: UHC #5, Manwill #7. Our furnace "
        "page: 20,609 impressions / 2 clicks."),

     cl("AC repair Salt Lake City",
        "a/c repair salt lake city (590); ac repair in salt lake city (50); "
        "utah air conditioner service (140); air conditioning service utah "
        "(140)", 920,
        SUP + "/services/emergency-services/", 5, "Commercial (seasonal)",
        "manwill.net", "https://manwill.net/air-conditioning/",
        brief("BUILD THE AC-REPAIR ANSWER PATH - Black Diamond ranks with 932 "
              "words.",
         "Yelp #4; Black Diamond #5 with a 932-word page, Manwill #7 with "
         "2,647. PAA: 'Where can I get my air conditioner repaired in Salt "
         "Lake City?', 'How much does it cost to repair an AC system?', "
         "'What is the most common problem in an AC unit?'.",
         ["Dedicated AC-repair content on the HVAC path answering the cost "
          "PAA with ranges by failure type (capacitor, refrigerant, "
          "compressor).",
          "H2 'The most common AC problems we see in Utah' - the PAA plus "
          "local credibility (evaporative vs refrigerated context along the "
          "Wasatch Front).",
          "Same-day/emergency framing tied to the emergency-services page "
          "that already collects impressions.",
          "Seasonal: this ships before cooling season or waits a year."],
         target="#4-#6; the 932-word incumbent is the bar to clear."),
        "Cluster ~920/mo. Live-verified: Black Diamond #5, Manwill #7, us "
        "outside top 10."),

     cl("City service pages (Millcreek, Murray)",
        "millcreek heating (590); plumbers murray (320); plumber murray utah "
        "(50)", 960,
        SUP + "/service-areas/ (hub - see brief)", 0, "Commercial (local)",
        "manwill.net", "https://manwill.net/service-locations/millcreek/",
        brief("FIX THE SERVICE-AREAS HUB BEFORE TOUCHING CITY CONTENT - then "
              "match the 682-word local winner.",
         "The #1 result for 'millcreek heating' is millcreekhtg.com - a "
         "company NAMED Millcreek Heating, with 682 words; brand-name "
         "geography is unbeatable head-on, so the realistic slots are below "
         "it. Manwill's Millcreek city page ranks #4 with 1,146 words. "
         "STRUCTURAL BLOCKER, verified this July: Superior's /service-areas/ "
         "hub renders an EMPTY main element - no H1, no links to any of its "
         "55 city pages - and the city pages have no inbound path at all.",
         ["The hub fix is prerequisite: /service-areas/ must render its city "
          "list before any city page can accumulate signals. Cross-reference "
          "the July internal-linking workbook (249-row link map already "
          "delivered) - this cluster is why that work matters.",
          "Then: Millcreek and Murray city pages to the Manwill pattern "
          "(1,146 words, services + local proof), not the current 470-word "
          "median.",
          "Answer the city PAA once per page: HVAC service call cost, the "
          "$5,000 rule in brief.",
          "Do not chase 'millcreek heating' #1 - the brand-name winner owns "
          "it; #3-#5 is the real target."],
         note="Murray/Millcreek pages: verify they exist in the 55-page set "
              "before writing; several city pages are known 470-word stubs.",
         target="#3-#5 under the eponymous local and the Yelp fixture."),
        "Cluster ~960/mo. Live-verified: millcreekhtg.com #1 (eponymous), "
        "Manwill #4. Blocked by the verified blank /service-areas/ hub."),
    ]

    backlinks = [
     {"target": "wellwatertesting.org",
      "comp_page": "links to nusoftwatersystems.com (rank 51)",
      "our_page": SUP + "/water/water-treatment/",
      "quality_note": "Water-quality niche resource linking the direct "
       "softener competitor - exactly the relevance-over-authority profile. "
       "Ask: resource inclusion for Utah hardness/testing content (the "
       "hardness-by-city data the cluster brief adds is the natural citable "
       "asset).", "routed": "Y"},
     {"target": "bestofslc.com",
      "comp_page": "links manwill.net (verified live earlier this session)",
      "our_page": SUP + "/",
      "quality_note": "Genuine SLC best-of site already linking an HVAC "
       "comparable. Ask: home-services inclusion.", "routed": "Y"},
     {"target": "ksl.com",
      "comp_page": "links westernheatingair.com (rank 23)",
      "our_page": SUP + "/",
      "quality_note": "Utah's dominant news property. Route: seasonal "
       "expert commentary (hard-water, furnace-season). Not a directory "
       "ask.", "routed": "Y"},
     {"target": "Yelp / Angi / Reddit presence",
      "comp_page": "fixtures at #4 on the scoped SERPs",
      "our_page": SUP + "/",
      "quality_note": "SERP occupants, not link targets - profile "
       "completeness and review velocity are the play; the Reddit thread "
       "ranking on softener queries is a monitor-and-participate-honestly "
       "channel, never astroturf. Route to citations/GBP.", "routed": "N"},
     {"target": "fixmysoftener.com, plumbernearme.shop",
      "comp_page": "the remainder of the competitors' domain gaps",
      "our_page": "n/a",
      "quality_note": "DO NOT CHASE - thin affiliate/lead domains. The "
       "comparables' link profiles are small (131-195 domains) and mostly "
       "low-value; these SERPs are won on content and completeness, not "
       "links.", "routed": "N"},
    ]

    return {
     "competitor_set":
      "NuSoft Water Systems (nusoftwatersystems.com), Intermountain Soft "
      "Water (intermountainsoftwater.com), Manwill (manwill.net). Chosen from "
      "12 live Salt Lake City SERPs 2026-08-18: the two water-treatment "
      "specialists cover the flagship line, Manwill covers the HVAC/plumbing "
      "flank (top-10 on 3 of 12 each; specialists dominate softener SERPs). "
      "Kinetico Utah is a watchlist dealer; Yelp/Reddit are fixtures. IHS "
      "siblings SameDay and Beehive appear in these SERPs and are never "
      "treated as competitors. Snapshot: gap_analysis/2026-08-serps.json",
     "baseline_note":
      "Baseline month - no stored prior SERP set. Snapshot saved; September "
      "answers this cell by diff.",
     "clusters": clusters, "backlinks": backlinks}


def comfort():
    clusters = [
     cl("Heating and cooling repair head terms",
        "heat & cooling repair (2,400); heating and air utah (320); heating "
        "and cooling utah (320); heating cooling and air (320); salt lake "
        "city furnace repair + variants (2,380)", 5740,
        COM + "/", 260, "Commercial (category head)",
        "utah-heatingcooling.com", "https://utah-heatingcooling.com/",
        brief("ANSWER THE COST PAA ON THE HOMEPAGE AND FURNACE PAGES - the "
              "970-word incumbent shows the bar is low.",
         "Utah Heating & Cooling holds #4 across these variants with a "
         "970-word homepage; coolingandheat.com #7 at 1,801 words. Yelp #5 "
         "fixture. PAA: 'What is the average cost of a HVAC service call?', "
         "'What is the $5000 rule for HVAC?', 'Where can I get my air "
         "conditioner repaired in Salt Lake City?'. Comfort's homepage "
         "already earns 260 clicks - the head-term rankings, not the page, "
         "are whats missing.",
         ["Homepage service blocks per line (furnace repair, AC repair, "
          "fireplace) with one-line cost anchors and links to the service "
          "pages - the UHC pattern at 970 words proves modest depth ranks "
          "when it answers directly.",
          "H2 'What an HVAC service call costs' on the service pages - the "
          "PAA verbatim, with Comfort's dispatch policy.",
          "H2 'The $5,000 rule' honest repair-vs-replace guidance feeding "
          "the replacement pages.",
          "Internal anchors: 'heating and cooling' mentions across the blog "
          "point at the homepage/service hub."],
         target="#4-#6 alongside UHC; Yelp caps the top."),
        "Cluster ~5,740/mo. Live-verified: UHC #4 with 970 words. Largest "
        "Comfort cluster."),

     cl("Furnace replacement and repair SLC",
        "furnace replacement service (260); salt lake city furnace repair "
        "(320); utah furnace repair (140); furnace repair experts (390)", 1110,
        COM + "/furnace-repair-salt-lake-city/", 0, "Commercial (core, seasonal)",
        "westernheatingair.com",
        "https://westernheatingair.com/service-area/salt-lake-city-ut/furnace/",
        brief("RESCUE THE ZERO-CLICK FURNACE PAGE - 14,261 impressions and "
              "not one click.",
         "Western ranks #5 with an 8,808-word city-service page and Just "
         "Right #6 with 1,362 words - both formats rank, so depth is "
         "optional; answering is not. PAA: 'Should a 25 year old furnace be "
         "replaced?', 'What is the most common furnace failure?', 'How many "
         "years does a furnace usually last?'. OUR PAGE ALREADY RANKS: "
         "/furnace-repair-salt-lake-city/ collected 14,261 impressions "
         "May-Jul and earned ZERO clicks - the worst impressions-to-clicks "
         "ratio in this workbook.",
         ["Title and meta first: a page seen 14,000 times without a click "
          "has a snippet problem before a content problem. Rewrite toward "
          "the question the searcher asked ('Furnace Repair in Salt Lake "
          "City - Same-Week Service & Honest Repair-or-Replace Advice' "
          "class, per the title rules).",
          "H2 'Repair or replace: the age test' - the 25-year PAA answered "
          "with honest thresholds, linking a replacement page.",
          "H2 'The most common furnace failures in Utah homes' with what "
          "each costs to fix - failure PAA plus the cost pattern.",
          "H2 'How long furnaces last here' - altitude/usage context.",
          "Ship before heating season; this cluster is Comfort's core "
          "revenue line."],
         note="Zero clicks on 14k impressions makes this the highest-"
              "leverage single page in Comfort's workbook.",
         target="#4-#6; both incumbents are beatable formats."),
        "Cluster ~1,110/mo. Our page: 14,261 impressions / 0 clicks - "
        "flagship fix."),

     cl("AC repair Salt Lake City",
        "a/c repair salt lake city (590); ac repair salt lake variants "
        "(250)", 840,
        COM + "/services/emergency-services/air-conditioner-repair/", 2,
        "Commercial (seasonal)", "manwill.net",
        "https://manwill.net/air-conditioning/",
        brief("SAME COST-ANSWER TREATMENT FOR THE AC PAGE - 11,701 "
              "impressions, 2 clicks.",
         "Black Diamond #5 (932 words), Manwill #7 (2,647). PAA: cost to "
         "repair an AC system, most common AC problem, where to get it "
         "repaired in SLC. Our emergency AC page collects 11,701 "
         "impressions for 2 clicks - the furnace pattern repeated.",
         ["Snippet rewrite first (title/meta) - same diagnosis as the "
          "furnace page.",
          "H2 'AC repair costs by failure type' - capacitor, refrigerant, "
          "compressor ranges.",
          "H2 'The most common AC problems in Utah' - PAA answer with "
          "same-day framing.",
          "Cross-link the ac-system-upgrades post (already earns clicks) "
          "for the repair-vs-upgrade path."],
         target="#4-#6 before cooling season ends; otherwise next May."),
        "Cluster ~840/mo. Our page: 11,701 impressions / 2 clicks."),

     cl("Emergency heating repair",
        "emergency heating repairs near me (720); gas heater installation "
        "near me (90)", 810,
        COM + "/services/emergency-services/", 3, "Commercial (emergency)",
        "westernheatingair.com",
        "https://westernheatingair.com/service-area/salt-lake-city-ut/plumber/",
        brief("MAKE THE EMERGENCY PAGE ANSWER THE EMERGENCY QUESTIONS.",
         "Western #5 (8,350-word mega city page), Valley #6. PAA: 'What is "
         "considered a heating emergency?', 'Who should I call if my "
         "furnace isn't working?', 'How much does it usually cost to fix a "
         "heater?'. Our emergency hub: 13,981 impressions, 3 clicks.",
         ["H2 'What counts as a heating emergency' - no-heat-below-freezing, "
          "gas smell, CO alarm; the triage PAA answered builds trust and "
          "filters calls.",
          "H2 'What emergency heating repair costs' - after-hours policy "
          "stated plainly; nobody ranking does.",
          "Response-window promise above the fold with the tap-to-call CTA.",
          "Winter-readiness internal links from the fireplace and furnace "
          "content."],
         target="#4-#6."),
        "Cluster ~810/mo. Our hub: 13,981 impressions / 3 clicks."),

     cl("City heating pages (Millcreek, Murray, Midway)",
        "millcreek heating (590); plumbers murray (320) - flagged, see "
        "brief; midway heating (260); midway heating and cooling (70)", 1240,
        COM + "/service-areas/sandy-utah/", 32, "Commercial (local)",
        "manwill.net", "https://manwill.net/service-locations/millcreek/",
        brief("EXTEND THE PROVEN SANDY PATTERN TO THE GAP CITIES - with two "
              "scope flags.",
         "millcreekhtg.com holds #1 on 'millcreek heating' with 682 words - "
         "an eponymous local that cannot be displaced on its own name; "
         "Manwill's city page ranks #4 with 1,146 words. Comfort's OWN "
         "/service-areas/sandy-utah/ (31,407 impressions, 32 clicks - the "
         "1.5 candidate) proves the city-page pattern already works for "
         "this site.",
         ["Build Millcreek and Murray HEATING pages on the Sandy template: "
          "services + response time + local proof at Manwill's 1,146-word "
          "bar, not the 470-word stub level.",
          "Answer the city PAA once per page: HVAC service-call cost, most "
          "reliable-company proof block (reviews, years).",
          "FLAG 1: 'plumbers murray' is a PLUMBING query - Comfort has no "
          "plumbing line beyond tankless water heaters; excluded from the "
          "brief, listed only for completeness.",
          "FLAG 2: Midway (Heber Valley) - confirm service coverage with "
          "the owner before building; routed as a decision, not a "
          "recommendation."],
         target="#3-#5 under the eponymous #1."),
        "Cluster ~1,240/mo counting flags. Sandy page (31k impressions) is "
        "the in-house proof of pattern. Midway routed to owner; Murray "
        "plumbing query excluded on relevance."),
    ]

    backlinks = [
     {"target": "ksl.com",
      "comp_page": "links westernheatingair.com (rank 23)",
      "our_page": COM + "/",
      "quality_note": "Utah's dominant news property, already linking the "
       "comparable that outranks Comfort on furnace queries. Route: "
       "furnace-season expert commentary or a fireplace-safety piece - "
       "Comfort's fireplace line is a genuinely distinctive angle for "
       "KSL Homes-style coverage.", "routed": "Y"},
     {"target": "bestofslc.com",
      "comp_page": "links manwill.net (rank 14; verified live this session)",
      "our_page": COM + "/",
      "quality_note": "Genuine SLC best-of site linking an HVAC comparable. "
       "Ask: HVAC/home-services inclusion.", "routed": "Y"},
     {"target": "Yelp / Angi profiles",
      "comp_page": "fixtures at #4-#5 on every scoped heating SERP",
      "our_page": COM + "/",
      "quality_note": "SERP occupants - completeness and review velocity, "
       "routed to citations/GBP workstream rather than backlinks.",
      "routed": "N"},
     {"target": "hometownguru.com, celebhomes.net, hvac.best, "
                "plumbernearme.shop",
      "comp_page": "the bulk of Western's 283-domain gap",
      "our_page": "n/a",
      "quality_note": "DO NOT CHASE - generic home-content and directory "
       "shells with no Utah relevance. Western's link count is not the "
       "reason it ranks; its 8,000-word city pages are.", "routed": "N"},
    ]

    return {
     "competitor_set":
      "Utah Heating & Cooling (utah-heatingcooling.com), Manwill "
      "(manwill.net), Western Heating & Air (westernheatingair.com). Chosen "
      "from 12 live Salt Lake City SERPs 2026-08-18: top-10 on 7, 11 and 4 "
      "of 12; UHC holds median #4 on the head terms. Fixtures: Yelp (11/12), "
      "Angi, Home Depot, Reddit. IHS sibling SameDay appears on 5 of 12 "
      "SERPs and is never treated as a competitor. Snapshot: "
      "gap_analysis/2026-08-serps.json",
     "baseline_note":
      "Baseline month - no stored prior SERP set. Snapshot saved; September "
      "answers this cell by diff.",
     "clusters": clusters, "backlinks": backlinks}


def main():
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    for slug, fn in (("superior", superior), ("comfort", comfort)):
        doc = fn()
        out = Path(reg[slug]["folder"]) / "gap_analysis" / "analysis.yaml"
        out.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True,
                                      width=100), encoding="utf-8")
        print(f"{slug}: analysis.yaml ({len(doc['clusters'])} clusters)")
        fill_1_7.main(slug)


if __name__ == "__main__":
    main()
