"""Author Beehive's and SameDay's 1.7 analysis files and fill both tabs.

Every position cited was live-verified in a Salt Lake City SERP this session;
every winner format claim comes from a parsed page in 2026-08-serp-winners.json;
link-gap verdicts come from 2026-08-linkgaps.json plus live fetches of the
candidate targets. Briefs follow the writer format locked on the EW pilot.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fill_1_7  # noqa: E402

NL = chr(10)


def page_clicks(folder):
    """Base-URL click totals: the GBP utm variants are the same page."""
    raw = json.loads(Path(folder, "gap_analysis", "2026-08-page-clicks.json"
                          ).read_text(encoding="utf-8"))
    out = {}
    for u, v in raw.items():
        base = u.split("?")[0]
        d = out.setdefault(base, {"clicks": 0, "imp": 0})
        d["clicks"] += v["clicks"]
        d["imp"] += v["imp"]
    return out


def find_page(pages, tokens, home=False):
    if home:
        base = min(pages, key=len)
        return base, pages[base]["clicks"]
    best, bc = None, -1
    for u, v in pages.items():
        low = u.lower()
        if any(t in low for t in tokens) and v["clicks"] >= bc:
            best, bc = u, v["clicks"]
    return (best, bc) if best else (None, 0)


def brief(head, serp, dos, note=None, target=None):
    lines = [head, "", "WHAT THE LIVE SERP SHOWS: " + serp, "", "DO THIS:"]
    lines += [f"{i}. {d}" for i, d in enumerate(dos, 1)]
    if note:
        lines += ["", "NOTE: " + note]
    if target:
        lines += ["", "REALISTIC TARGET: " + target]
    return NL.join(lines)


def cluster(name, kws, vol, page, clicks, intent, comp, curl, br, comments):
    return {"cluster": name, "keywords": kws, "volume": vol, "clicks": clicks,
            "intent": intent, "competitor": comp, "their_url": curl,
            "our_page": page or "NO DEDICATED PAGE FOUND - see brief",
            "brief": br, "comments": comments}


# ============================================================== BEEHIVE =====
def beehive():
    P = page_clicks("Clients/Beehive")
    home, home_clk = find_page(P, [], home=True)
    drain, drain_clk = find_page(P, ["drain"])
    soft, soft_clk = find_page(P, ["softener", "water-treatment", "soft-water"])
    hydro, hydro_clk = find_page(P, ["hydro"])
    mainl, mainl_clk = find_page(P, ["main-water", "water-line", "water-main"])
    sump, sump_clk = find_page(P, ["sump"])
    wh, wh_clk = find_page(P, ["water-heater"])
    provo, provo_clk = find_page(P, ["provo"])
    orem, orem_clk = find_page(P, ["orem"])
    print("beehive mapping:", {"drain": drain, "softener": soft, "hydro": hydro,
                               "mainline": mainl, "sump": sump, "wh": wh,
                               "provo": provo, "orem": orem})

    COST_PAT = ("Every scoped Utah plumbing SERP carries cost-question PAA. "
                "Answering price questions with real ranges is the single "
                "pattern the winners share and Beehive's pages avoid.")
    clusters = [
     cluster("Drain cleaning service",
      "drain service near me (5,400); drain unblocker service (110)", 5510,
      drain, drain_clk, "Commercial", "valleyplumbing.com",
      "https://www.valleyplumbing.com/plumbing/drain-cleaning/",
      brief("ANSWER THE COST QUESTIONS THE WINNERS DODGE on our drain cleaning page.",
       "Yelp holds #4 (directory fixture). The beatable field is national "
       "franchise copy: Roto-Rooter #6 (2,273 words) and Mr. Rooter #7 (4,154 "
       "words) rank with generic pages; Valley Plumbing #7 with a 0-backlink "
       "service page - this SERP is won on content. The PAA is entirely cost: "
       "'How much does it usually cost to clear a drain?', 'What is the average "
       "price to snake a drain?', 'Where can I get drain cleaning done in Salt "
       "Lake City?'. We sit #13.",
       ["Add H2 'What drain cleaning costs in Salt Lake City' with a real price "
        "range table: snake, hydro jet, camera inspection - the PAA question "
        "answered verbatim, which no ranking page does.",
        "Add H2 'Snaking vs hydro jetting: which your drain needs' - decision "
        "help, links our hydro jetting page.",
        "Add a local proof block: response time, SLC-area jobs completed, "
        "licensed-and-insured line - the franchise pages ranking above us are "
        "location-templated and cannot show real local proof.",
        "Internal links: the DIY drain and toilet posts (the blog's biggest "
        "click earners) must link this page with 'drain cleaning service' "
        "anchors - today they orphan it."],
       note=COST_PAT,
       target="#3-#5, under the Yelp fixture and above templated franchise copy."),
      "Cluster ~5,510/mo. Live-verified: Valley #7, us #13. All positions from "
      "SLC SERPs 2026-08-18."),

     cluster("Salt Lake City plumber head terms",
      "slc plumbing (2,400); plumbers slc (2,400); salt lake plumbing (2,400); "
      "salt lake city plumbing services (170)", 7370,
      home, home_clk, "Commercial (category head)", "millcreekplumbinginc.com",
      "https://millcreekplumbinginc.com/",
      brief("MAKE THE HOMEPAGE ANSWER WHAT SLC SEARCHERS ASK - Millcreek wins "
            "these terms with a 5,779-word homepage.",
       "Reddit #4 and Yelp #5 are fixtures. The comparable is Millcreek "
       "Plumbing's HOMEPAGE at #4-#9 across all variants: 5,779 words of "
       "service depth, family-owned framing and pricing candour on one URL. "
       "Our homepage (largest click asset, but thin on service content) sits "
       "#12 on 'plumbers slc' and absent on the others. PAA: 'How much do "
       "plumbers charge per hour in Utah?', 'What is the average call out "
       "charge?', 'Who are reputable plumbing contractors in Salt Lake City?'.",
       ["Add a pricing-transparency section to the homepage or SLC service "
        "page answering the hourly-rate and call-out PAA with Beehive's actual "
        "policy - even a range beats the silence every competitor keeps.",
        "Expand homepage service sections toward Millcreek's depth: each core "
        "service (drain, water heater, emergency, softener) gets a short block "
        "linking its service page - depth on one URL is the observed pattern.",
        "Add a reputable-proof block: license number, years, review count, "
        "guarantee - answering 'how to find a good plumber' signals.",
        "Internal anchor pass: posts mentioning 'salt lake city plumber' link "
        "the homepage/SLC page with that anchor."],
       target="#5-#8 first, behind the Reddit/Yelp fixtures; Millcreek's slot "
              "is the ceiling to work toward."),
      "Cluster ~7,370/mo. Live-verified: Millcreek #4-#9, us #12/absent."),

     cluster("Water softener installation",
      "water softener installation service (2,400)", 2400,
      soft, soft_clk, "Commercial", "bdexperts.com",
      "https://bdexperts.com/plumbing-services/water-softener-installation/",
      brief("ANSWER THE THREE INSTALL QUESTIONS - the SERP is fixtures plus "
            "one thin specialist.",
       "Intermountain Soft Water #5 (1,125 words), then Yelp #6 and Lowe's #7 "
       "- big-box is literally in the SERP, and the PAA is 'How much should "
       "water softener installation cost?', 'Do I need a plumber to install a "
       "water softener?', 'How much does Home Depot charge to install one?'. "
       "Black Diamond #8. We sit #23.",
       ["Add H2 'What water softener installation costs in Utah' with a range "
        "covering unit + install, and what changes the price (loop present, "
        "crawlspace, drain distance).",
        "Add H2 'Do you need a plumber to install a water softener?' - honest "
        "answer including when a handy homeowner can and when code requires a "
        "pro; this is the trust-winning move against big-box installers.",
        "Add a 'big-box vs licensed plumber install' comparison paragraph - "
        "Lowe's ranks here; differentiate on who actually shows up and "
        "warranty ownership.",
        "Utah water-hardness context block (SLC-area grains-per-gallon) - the "
        "local angle no national page carries."],
       target="#4-#6, beside the specialist and above Black Diamond."),
      "Cluster 2,400/mo. Live-verified: Black Diamond #8, us #23."),

     cluster("Hydro jetting",
      "hydro jet service near me (590); hydro jetting service near me (590); "
      "hydro jetting cost near me (320); hydro jet plumbing near me (210)", 1710,
      hydro, hydro_clk, "Commercial", "millcreekplumbinginc.com",
      "https://millcreekplumbinginc.com/hydro-jetting-salt-lake-city-utah/",
      brief("ADD THE WORTH-IT AND COST ANSWERS to our hydro jetting page.",
       "Millcreek #4 (1,507 words) and Valley #7 (2,516 words) - both "
       "content-ranked, 0 backlinks on Millcreek's page. PAA: 'Is hydro "
       "jetting worth the cost?', 'How much does it cost to hydrojet a drain "
       "line?', 'Can I do hydro jetting myself?', 'How long will hydro "
       "jetting last?'. Our GSC position on hydro terms is ~26.",
       ["H2 'What hydro jetting costs in Salt Lake City' - range plus what "
        "moves it (line length, access, severity).",
        "H2 'Is hydro jetting worth it?' - honest comparison vs snaking with "
        "the cases where snaking is enough; candour is the differentiator.",
        "H2 'Why hydro jetting is not DIY' - answers the PAA and converts it.",
        "H2 'How long results last' with maintenance guidance."],
       target="#3-#5; both comparables rank on content our page can out-answer."),
      "Cluster 1,710/mo. Live-verified: Millcreek #4, Valley #7."),

     cluster("Main water line repair",
      "main water line repair (880); main water line replacement (390); main "
      "water line leak repair (170); outside water line repair (70)", 1550,
      mainl, mainl_clk, "Commercial (emergency)", "millcreekplumbinginc.com",
      "https://millcreekplumbinginc.com/outdoor-plumber/main-water-line-repair-replacement-salt-lake-city/",
      brief("BUILD THE COST + EMERGENCY + INSURANCE ANSWERS for main line work.",
       "Millcreek #3 (1,508 words) is the only strong comparable; Reddit #5 "
       "and The Spruce #9 are fixtures/publishers. PAA: 'How much does it "
       "cost to fix a main waterline?', 'What to do if your main water line "
       "breaks?', 'Does homeowners insurance cover main water line repairs?'.",
       ["H2 'What main water line repair costs in Utah' - repair vs "
        "replacement ranges, trenchless vs dig.",
        "H2 'Main line break? Do this first' - a 5-step emergency checklist "
        "(shutoff location, city vs homeowner responsibility).",
        "H2 'Does homeowners insurance cover it?' - the PAA nobody ranking "
        "answers in plain language.",
        "Cross-link the emergency plumbing page both ways."],
       target="#3-#5 beside Millcreek; the SERP has one real competitor."),
      "Cluster 1,550/mo. Live-verified: Millcreek #3, us absent."),

     cluster("Sump pump service",
      "sump pumps service (1,000); sump pump repair service near me (90)", 1090,
      sump, sump_clk, "Commercial", "valleyplumbing.com",
      "https://www.valleyplumbing.com/plumbing/sump-pump/",
      brief("TAKE A SOFT SERP - a 384-word out-of-state page ranks #5.",
       "The #5 result is a 384-word page from a foundation-repair company in "
       "Iowa (davenportfoundationrepair.com) - direct evidence this SERP has "
       "no strong owner. Valley #7 (2,191 words), Black Diamond #8 (879 "
       "words). PAA: 'How often should a sump pump be serviced?', 'How much "
       "is a sump pump service?'.",
       ["H2 'Sump pump service and repair in Salt Lake City' with the "
        "maintenance-schedule answer (annually, before spring runoff - tie to "
        "Utah snowmelt).",
        "H2 'What sump pump service costs' - service visit and replacement "
        "ranges.",
        "H2 'The most common reason sump pumps fail' - answers the PAA, "
        "demonstrates expertise, sells the service plan."],
       target="#3-#5. Weakest incumbent field in this table."),
      "Cluster 1,090/mo. Live-verified: Valley #7, Black Diamond #8, us absent."),

     cluster("Independent plumber trust terms",
      "family owned plumber near me (390); family owned plumbing near me "
      "(390); small plumbing companies near me (320)", 1100,
      home, home_clk, "Commercial (trust)", "valleyplumbing.com",
      "https://www.valleyplumbing.com/salt-lake-county-plumber/",
      brief("CLAIM THE INDEPENDENT-PLUMBER POSITION - after verifying the claim.",
       "Valley ranks #5 with an 859-word county page leaning on family-owned "
       "framing; Mr. Rooter #6 is franchise copy. PAA: 'How to tell if a "
       "plumber is ripping you off?', 'What is an independent plumber?', 'Who "
       "are the best plumbers in Salt Lake City?'.",
       ["FIRST: confirm with the client how Beehive describes itself - "
        "family-owned, independent, local-only. Do not publish the claim "
        "until confirmed; Utah-only and non-franchise are already verifiable.",
        "Add an 'independent Utah plumber' block to the homepage/about: "
        "what independent means for pricing and accountability vs a franchise.",
        "Publish 'How to tell if a plumber is overcharging you' as a section "
        "or short post - answers the highest-trust PAA in the set and earns "
        "the kind of trust links section B wants."],
       note="The claim gate matters: an unverified 'family-owned' line in "
            "print is exactly the fabricated-fact class this workbook bans.",
       target="#4-#6."),
      "Cluster ~1,100/mo. Live-verified: Valley #5, us absent."),

     cluster("Water heater repair service",
      "hot water repair service near me (880)", 880,
      wh, wh_clk, "Commercial (emergency)", "valleyplumbing.com",
      "https://www.valleyplumbing.com/salt-lake-county-plumber/",
      brief("POINT THIS QUERY AT OUR WATER HEATER PAGE - it already exists.",
       "Valley catches this on a generic county page - no one ranks a "
       "dedicated repair page, and our water heater install page (a 1.5 "
       "candidate, page 3+) already covers the topic family.",
       ["Add H2 'Hot water not working? Same-day water heater repair' to the "
        "existing water heater page - the repair intent is currently served "
        "only by install content.",
        "Answer the repair-or-replace question with age/cost thresholds.",
        "One combined job with the 1.5 water heater work - not a second "
        "ticket."],
       target="#4-#6."),
      "Single-keyword cluster, 880/mo. Cross-references the 1.5 water heater "
      "candidate."),

     cluster("City plumber pages",
      "plumber provo utah (590); plumbing provo (590); provo utah plumbing "
      "(590); orem plumber (480); midvale plumbing (140) + variants (420); "
      "south jordan plumbing (340); utah county plumbers (320)", 4060,
      provo or orem, max(provo_clk, orem_clk), "Commercial (local)",
      "valleyplumbing.com", "https://www.valleyplumbing.com/provo-plumber/",
      brief("STRENGTHEN THE CITY PAGES THAT EXIST; ROUTE THE REST TO THE OWNER.",
       "The winning pattern is emphatically LOCAL: llewellynplumbing.com "
       "ranks #5 in Provo with a 454-word city page, beating Roto-Rooter's "
       "3,134-word template - thin-but-genuinely-local beats deep-but-"
       "templated. Valley runs a city-page network (Provo, Midvale, South "
       "Jordan, Farmington, Orem) that catches all these queries.",
       ["Audit our existing city pages (Orem and Park City confirmed live) "
        "against the 454-word local winner: each needs city-specific proof - "
        "neighbourhoods served, response time from the nearest tech, one "
        "local job example, city water quirks (Provo hard water, older "
        "Midvale mains).",
        "Add the cost PAA per city: 'How much do plumbers charge per hour in "
        "Utah?' answered once per page in local context.",
        "Provo, Midvale and South Jordan pages DO NOT EXIST for us - "
        "new-page proposals are out of this tab's scope, and Utah County "
        "service coverage needs owner confirmation first. Routed as a "
        "decision, not a recommendation."],
       target="#4-#6 per existing city page; fixtures (Yelp) hold the top."),
      "Cluster ~4,060/mo across 5 cities. Provo (2,360/mo) is the largest "
      "and has NO Beehive page - owner decision routed."),
    ]

    backlinks = [
     {"target": "bestofslc.com",
      "comp_page": "links to millcreekplumbinginc.com (the homepage that beats "
                   "us on every SLC head term; 64 page-level referring domains)",
      "our_page": "https://www.beehiveplumbing.com/",
      "quality_note": "Verified live: a real Salt Lake City best-of site (not "
       "a link farm). Exactly the relevance-over-authority target: local, "
       "on-niche, and already linking the competitor that outranks us. Ask: "
       "inclusion in its home-services/plumbing picks.", "routed": "Y"},
     {"target": "ksl.com",
      "comp_page": "links to westernheatingair.com (domain rank 23 in their "
                   "profile)",
      "our_page": "https://www.beehiveplumbing.com/",
      "quality_note": "Utah's dominant news/classifieds property. Highest-"
       "authority RELEVANT target in any competitor profile here. Realistic "
       "routes: KSL Homes contributor content (seasonal plumbing pieces) or "
       "expert commentary; not a directory submission.", "routed": "Y"},
     {"target": "Yelp / Angi / Thumbtack profiles",
      "comp_page": "these directories hold #4-#6 on nearly every scoped SLC "
                   "SERP (fixtures)",
      "our_page": "https://www.beehiveplumbing.com/",
      "quality_note": "Not backlink targets - SERP occupants. The ranking "
       "slots we cannot win as a website are won as a profile: completeness, "
       "categories, review velocity. Route to the citations/GBP workstream, "
       "not the backlinks team - listed so the slot is owned by someone.",
      "routed": "N"},
     {"target": "homes-improvements.com, wall-ebuilders.com, rustandruffleshome.com "
                "+ ~20 lookalikes",
      "comp_page": "the bulk of valleyplumbing.com's 398-domain gap",
      "our_page": "n/a",
      "quality_note": "DO NOT CHASE. Templated home-niche names with identical "
       "rank fingerprints - a guest-post/PBN network. This is what the "
       "competitor's 'link advantage' actually is, and buying into it is "
       "risk, not value. Listed so a raw export never turns it into a "
       "campaign.", "routed": "N"},
     {"target": "utahsbesthomepros.com",
      "comp_page": "links to justrightair.com (rank 48)",
      "our_page": "n/a",
      "quality_note": "Fetched live: despite the directory-sounding name it "
       "is a lead-gen service site ('Reliable HVAC & Plumbing Services in "
       "Salt Lake City'). A link here is a paid lead arrangement, not an "
       "earned citation. Owner call if lead-gen is wanted; not a backlink "
       "play.", "routed": "N"},
    ]

    return {
     "competitor_set":
      "Valley Plumbing (valleyplumbing.com), Millcreek Plumbing "
      "(millcreekplumbinginc.com), Black Diamond (bdexperts.com). Chosen from "
      "12 live Salt Lake City SERPs on the scoped commercial queries, "
      "2026-08-18: top-10 on 8, 6 and 4 of 12 respectively, all same-type "
      "local businesses. Roto-Rooter/Mr. Rooter/ARS excluded as national "
      "franchises (watchlist); Yelp/Reddit/Thumbtack/Angi are fixtures. "
      "NOTE: Black Diamond's largest gaps are HVAC (mini split repair, "
      "18,100/mo) - out of scope for a plumbing company and excluded on "
      "relevance. Snapshot: gap_analysis/2026-08-serps.json",
     "baseline_note":
      "Baseline month - no stored prior SERP set. This month's top-10 "
      "snapshot is saved; from September this cell is answered by diffing "
      "against it.",
     "clusters": clusters, "backlinks": backlinks}


# ============================================================== SAMEDAY =====
def sameday():
    P = page_clicks("Clients/SameDay")
    home, home_clk = find_page(P, [], home=True)
    ac, ac_clk = find_page(P, ["air-conditioning", "air-conditioner", "cooling"])
    plumb, plumb_clk = find_page(P, ["/plumbing"])
    heat, heat_clk = find_page(P, ["heating", "furnace"])
    sandy, sandy_clk = find_page(P, ["sandy"])
    print("sameday mapping:", {"ac": ac, "plumb": plumb, "heat": heat,
                               "sandy": sandy})

    clusters = [
     cluster("Air conditioning installation",
      "air conditioning installation (60,500); air con and installation "
      "(60,500); who installs air conditioning (50)", 121100,
      ac, ac_clk, "Commercial (highest volume in this workbook)",
      "justrightair.com",
      "https://justrightair.com/residential/air-conditioning/air-conditioning-install/",
      brief("BUILD THE AC INSTALLATION PAGE TO THE OBSERVED WINNING SHAPE - "
            "cost answer first.",
       "Just Right Air ranks #5 with 1,655 words whose second H2 is literally "
       "'How Much Does a New A/C Cost?' - the cost answer IS the format. Home "
       "Depot #6 (fixture), SOS Air #7 (2,095 words, signs-you-need-"
       "replacement structure). Their winning page has ZERO backlinks: pure "
       "content. PAA: 'How much does it cost to have air conditioning "
       "installed?', 'What AC brands to stay away from?', 'Can I install my "
       "AC unit myself?', 'How long does AC installation usually take?'. "
       "SameDay is ABSENT from this SERP; our AC pages earn 24 clicks/quarter.",
       ["Create/rebuild the dedicated AC installation page under /cooling/ "
        "with H2 'How much does AC installation cost in Utah?' - real ranges "
        "by system type, answered in the first half of the page.",
        "H2 'Signs your AC needs replacement, not repair' - the SOS structure "
        "that also ranks; links our repair page both ways.",
        "H2 'How long installation takes' and 'Can you install your own AC?' "
        "- both PAA, both trust-builders with honest answers.",
        "H2 'AC brands: what we install and why' - answers the brand PAA "
        "without trash-talking; name the lines SameDay actually carries.",
        "Internal links from the Layton and West Jordan AC city pages (the "
        "only service pages currently earning clicks) with 'AC installation' "
        "anchors."],
       note="Volume caveat: the two 60,500 variants almost certainly share "
            "one demand pool - treat ~60,500/mo as the honest opportunity, "
            "121,100 as the double-counted ceiling.",
       target="#4-#6 first (Home Depot fixture holds #6); Just Right's slot "
              "is the target after the page matures."),
      "Largest verified gap in the entire workbook. Live-verified: Just Right "
      "#5, us absent."),

     cluster("Toilet repair",
      "plumbing repairs toilets (40,500); commode repairs (12,100); toilet "
      "leak repair near me (70)", 52710,
      plumb, plumb_clk, "Commercial", "justrightair.com",
      "https://justrightair.com/residential/toilet-repairs/",
      brief("BUILD A DEDICATED TOILET REPAIR PAGE - the #1 result is 1,192 "
            "words and beatable.",
       "Just Right Air holds #1 with a 1,192-word page (structure: signs "
       "your toilet needs repair / repairs / maintenance); Valley #4 with "
       "2,699 words led by 'Most toilet problems are cheap to fix if you "
       "catch them early' - candour ranks. Thumbtack #5 fixture. PAA: 'How "
       "much do plumbers charge to fix toilets?', 'Can a handyman fix a "
       "toilet?', 'What is the average life expectancy of a toilet?'. We sit "
       "#16-#20 with the generic /plumbing/ hub.",
       ["Create the dedicated toilet repair page under /plumbing/ - the hub "
        "cannot win a service-specific SERP against dedicated pages.",
        "Open with the cost answer: 'What plumbers charge to fix a toilet' - "
        "flat-rate vs hourly, with SameDay's actual model.",
        "H2 'Signs your toilet needs repair' (running, rocking, ghost "
        "flushing, base leaks) - the structure both winners share.",
        "H2 'Repair or replace?' with the lifespan answer (the PAA) and an "
        "honest threshold.",
        "Same-day framing is the differentiator the brand name already owns: "
        "'fixed today' messaging nobody in this SERP uses."],
       target="#2-#4 beside Valley; the #1 page is 1,192 words with no moat."),
      "Live-verified: Just Right #1, us #16-#20. 52,710/mo cluster - second "
      "largest in the workbook."),

     cluster("Salt Lake City plumber head terms",
      "plumbers in salt lake city utah (2,400); plumbers slc (2,400); plumber "
      "salt lake city (2,400); hvac plumbers near me (480)", 7680,
      plumb, plumb_clk, "Commercial (category head)", "justrightair.com",
      "https://justrightair.com/residential/plumbing/",
      brief("GIVE /plumbing/ THE LOCAL DEPTH THE WINNERS CARRY.",
       "Reddit #4 and Yelp fixtures; the comparables are Copper Peaks #5 "
       "(1,323 words) and Just Right's plumbing hub (the only competitor "
       "page here with real links - 18 referring domains). PAA: hourly "
       "rates in Utah, call-out charges, 'Who are reputable plumbing "
       "contractors in Salt Lake City?'. Our /plumbing/ page earns 10 "
       "clicks a quarter.",
       ["Answer the rate PAA on /plumbing/: SameDay's call-out/dispatch "
        "model in plain language - the question every ranking page ducks.",
        "Add SLC-specific service depth: emergency response time, areas "
        "covered tonight, licensed plumber count - hub currently reads "
        "generic.",
        "Reputable-proof block: license, years, review count across "
        "platforms.",
        "This page is also the 1.5 candidate ('plumber near me' at 10.6-"
        "14.4) - one rebuild serves both tabs."],
       target="#5-#7 behind the fixtures; Copper Peaks' slot is winnable."),
      "Live-verified: us #24 area. Cross-references the 1.5 /plumbing "
      "candidate."),

     cluster("Furnace tune-up and inspection",
      "furnace tune up services (2,900); furnace inspection service (480); "
      "furnace tune-up companies (70)", 3450,
      heat, heat_clk, "Commercial (seasonal)", "justrightair.com",
      "https://justrightair.com/residential/furnaces/furnace-maintenance/",
      brief("BUILD THE TUNE-UP OFFER PAGE BEFORE HEATING SEASON.",
       "Just Right #5 (1,782 words), Black Diamond #6 (915 words), Mountain "
       "Home #7 (1,207 words) - a fully commercial SERP of maintenance "
       "pages. PAA: 'How much is a tune-up on a furnace?', 'Is it necessary "
       "to get a furnace tune-up?', 'How often?', 'Is it worth it?'. We sit "
       "#20.",
       ["H2 'What a furnace tune-up costs' with SameDay's actual price or "
        "range - every PAA here is cost/worth-it.",
        "H2 'What our 21-point tune-up includes' (use the real checklist "
        "count) - the winners all itemise.",
        "H2 'Is a tune-up worth it?' - honest math: tune-up price vs "
        "mid-January failure callout.",
        "Seasonal timing: page and internal links live before October; tie "
        "to the membership plan page (/green-shield-membership-plan/ "
        "already earns clicks)."],
       target="#4-#6 in a beatable all-commercial field."),
      "Live-verified: Just Right #5, us #20. Seasonal: ship before heating "
      "season."),

     cluster("Heating and AC repair",
      "air and heating repair (1,300); emergency heating repairs near me "
      "(720); local hvac repair service (210); repair heating and cooling "
      "(110)", 2340,
      ac, ac_clk, "Commercial (emergency)", "justrightair.com",
      "https://justrightair.com/city/salt-lake-city-ut/",
      brief("MAKE THE EMERGENCY REPAIR PATH EXPLICIT.",
       "Just Right #6 (2,154 words) and Utah Heating & Cooling #7 (970 "
       "words) - city-page and service-page formats both rank. PAA: 'How "
       "much is a service call for heating and air?', 'What is the $5000 "
       "rule for HVAC?', 'Who is a reputable HVAC contractor in Salt Lake "
       "City?'.",
       ["Answer the service-call cost PAA on the emergency/repair pages - "
        "dispatch fee policy in plain language.",
        "Add H2 'The $5,000 rule: repair or replace' (age x repair cost) - "
        "a PAA that positions honest advice and feeds the install page.",
        "Emergency framing: tonight/same-day availability, real response "
        "windows - the brand promise, unstated on these SERPs.",
        "Existing /emergency-services/air-conditioner-repair/ (24 clicks, "
        "our best service page) gets the same treatment for heating."],
       target="#4-#6."),
      "Live-verified: us absent/#20s. Fold with the AC-repair 1.5 candidate "
      "work."),

     cluster("Water leak and drain repair",
      "water leak repair near me (1,000); clogged drain repair (720); leak "
      "repair services (90); home leak repair (70)", 1880,
      plumb, plumb_clk, "Commercial (emergency)", "valleyplumbing.com",
      "https://www.valleyplumbing.com/plumbing/water-leak-detection/",
      brief("ADD LEAK DETECTION AND DRAIN SECTIONS TO THE PLUMBING PATH.",
       "Valley #6 (2,234 words) and American Leak Detection #7 (814 words); "
       "Yelp fixture on top. PAA: 'How much does it typically cost to fix a "
       "water leak?', 'Can a plumber fix a water leak?', 'Can a handyman "
       "fix a leaky pipe?'.",
       ["H2 'Water leak repair costs' - by scenario (visible pipe, in-wall, "
        "slab) with detection method noted.",
        "H2 'How we find hidden leaks' - detection tech builds the case for "
        "a pro over a handyman (the PAA distinction).",
        "H2 'Clogged drain repair' section with same-day framing - covers "
        "the 720/mo drain query on the same path.",
        "Route to dedicated sub-pages later if the sections earn "
        "impressions - sections first, pages when data justifies."],
       target="#4-#6."),
      "Live-verified: Valley #6, us absent."),

     cluster("City plumber pages",
      "plumbers sandy (320) + variants (580); plumber provo utah (590) + "
      "variants (1,180); plumber west valley city (210) x4 (840); midvale "
      "(560); plumbers lehi ut (390) + (210)", 4670,
      sandy, sandy_clk, "Commercial (local)", "justrightair.com",
      "https://justrightair.com/service-areas/salt-lake-county-ut/sandy/",
      brief("BUILD OUT THE SERVICE-AREA PLUMBING PAGES - competitors win "
            "these with thin local pages.",
       "Just Right's Sandy service-area page and Valley's city network "
       "(Provo, West Valley, Midvale, Lehi) catch every variant; the "
       "observed city-page bar is low (Valley's are a few hundred words "
       "with local anchors). Our /service-area/ pages exist for AC (Layton, "
       "West Jordan earn clicks) but plumbing city pages are missing or "
       "thin.",
       ["Extend the existing /service-area/ structure with plumbing pages "
        "for Sandy, West Valley, Midvale and Lehi - cities inside SameDay's "
        "confirmed metro coverage.",
        "Each page: response time from nearest tech, neighbourhoods, one "
        "local job note, the Utah hourly-rate PAA answered locally, link to "
        "/plumbing/ and emergency pages.",
        "Provo (1,770/mo) is Utah County - confirm coverage with the owner "
        "before building; routed as a decision.",
        "Mirror the AC city pages that already earn clicks (Layton 15, "
        "West Jordan 11) - the pattern is proven on our own site."],
       target="#4-#6 per city; Yelp fixtures cap the top."),
      "Cluster ~4,670/mo across 5 cities. Provo routed to owner (service "
      "area)."),
    ]

    backlinks = [
     {"target": "ksl.com",
      "comp_page": "links to westernheatingair.com (rank 23 in their profile)",
      "our_page": "https://samedayutah.com/",
      "quality_note": "Utah's dominant news property - the one high-authority "
       "RELEVANT domain in any comparable's profile. Realistic route: expert "
       "commentary or seasonal home-services contributions (furnace-season, "
       "frozen pipes), not a directory ask.", "routed": "Y"},
     {"target": "bestofslc.com",
      "comp_page": "links millcreekplumbinginc.com; ranks in local best-of "
                   "context",
      "our_page": "https://samedayutah.com/",
      "quality_note": "Verified live: genuine SLC best-of site. On-niche, "
       "local, already linking a plumber. Ask: home-services inclusion.",
      "routed": "Y"},
     {"target": "Yelp / Angi / Thumbtack profiles",
      "comp_page": "fixtures holding top-6 slots on nearly every scoped SERP",
      "our_page": "https://samedayutah.com/",
      "quality_note": "SERP occupants, not link targets. Profile "
       "completeness + review velocity = presence inside the pages that own "
       "the rankings. Route to citations/GBP workstream.", "routed": "N"},
     {"target": "friendlyhomeservice.com, hvackaysville.blogspot.com, "
                "mysrlocal.com, goodhvaccontractor.com + lookalikes",
      "comp_page": "the bulk of justrightair.com's 207-domain gap",
      "our_page": "n/a",
      "quality_note": "DO NOT CHASE. Blogspot spam and templated 'local "
       "service' link-network domains. Just Right's link 'advantage' is "
       "largely this junk plus 18 real page-level domains on its plumbing "
       "hub - the lesson is their CONTENT wins, not their links.",
      "routed": "N"},
     {"target": "utahsbesthomepros.com",
      "comp_page": "links justrightair.com (rank 48)",
      "our_page": "n/a",
      "quality_note": "Fetched live: a lead-gen service site, not a "
       "directory. A link is a paid-leads arrangement - owner call, not a "
       "backlink play.", "routed": "N"},
    ]

    return {
     "competitor_set":
      "Just Right Air (justrightair.com), Western Heating & Air "
      "(westernheatingair.com), Valley Plumbing (valleyplumbing.com). Chosen "
      "from 12 live Salt Lake City SERPs, 2026-08-18: top-10 on 10, 5 and 5 "
      "of 12. Just Right is the dominant organic comparable in the metro. "
      "Fixtures: Yelp (12/12), Thumbtack, Angi, Home Depot, Reddit. NOTE: "
      "SameDay itself appears in Comfort's SERPs and Beehive appears in "
      "SameDay's - IHS sibling properties are never treated as competitors. "
      "Snapshot: gap_analysis/2026-08-serps.json",
     "baseline_note":
      "Baseline month - no stored prior SERP set. Snapshot saved; September "
      "answers this cell by diff.",
     "clusters": clusters, "backlinks": backlinks}


def main():
    for slug, fn in (("beehive", beehive), ("sameday", sameday)):
        doc = fn()
        reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
        out = Path(reg[slug]["folder"]) / "gap_analysis" / "analysis.yaml"
        out.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True,
                                      width=100), encoding="utf-8")
        print(f"{slug}: analysis.yaml written ({len(doc['clusters'])} clusters, "
              f"{len(doc['backlinks'])} link rows)")
        fill_1_7.main(slug)


if __name__ == "__main__":
    main()
