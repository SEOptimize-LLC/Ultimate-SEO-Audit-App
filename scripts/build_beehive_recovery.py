"""Build Beehive Plumbing blog recovery Excel file for writing team."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Beehive/Full Site SEO Audit/"
out = base + "beehive_blog_recovery_plan_v2.xlsx"

decline_df = pd.read_excel(base + "top_declining_blog_posts.xlsx")
blog_df = pd.read_excel(base + "content_inventory_by_type.xlsx", sheet_name="Blog Post")

decline_df["URL_key"] = decline_df["URL"].str.strip("/").str.lower()
blog_df["URL_key"] = (
    blog_df["Landing Page"]
    .str.replace("https://beehiveplumbing.com", "", regex=False)
    .str.replace("https://www.beehiveplumbing.com", "", regex=False)
    .str.strip("/")
    .str.lower()
)
blog_df = blog_df.drop_duplicates(subset="URL_key", keep="first")
merged = decline_df.merge(blog_df, on="URL_key", how="left")
merged = merged.drop_duplicates(subset="URL_key", keep="first").reset_index(drop=True)

# =========================================================================
# Writer brief per URL — primary kw, secondaries, entities, ICP, angle,
# competitors to beat, content structure guidance
# =========================================================================
writer_briefs = {
    "5-reasons-your-shower-is-not-working-and-what-to-do-about-it": {
        "primary_kw": "shower not turning on",
        "primary_sv": "Top performer: 19 clicks/711 imps at pos 4.2 (90d)",
        "secondary_kws": "shower won't turn on | shower stopped working | why is my shower not turning on | my shower won't turn on | bathroom shower not working",
        "entities": "shower valve, mixing valve, shower cartridge, water supply, pressure-balancing valve, diverter valve, scald-guard, hot water heater, main water shutoff, shower head",
        "icp": "Utah homeowner (30-55), DIY-curious but cautious, hit pause mid-morning or evening when shower failed. Needs to diagnose in 5 mins before calling a plumber. Suburban SLC/Wasatch Front.",
        "angle": "Fast diagnostic guide — 'Here's why in 30 seconds.' Lead with the 5 most common causes ranked by likelihood. DIY fix vs call-a-plumber decision for each cause. Include 'what NOT to do' warnings to protect valves/fittings.",
        "serp_intent": "Informational w/ local commercial bridge — users in troubleshooting mode but many convert to service calls when cause = valve/pipe issue.",
        "link_targets": "/services/shower-repair/ (or plumbing-repair), /services/emergency-plumber/, /services/water-heaters/",
        "must_have_sections": "1) Quick diagnostic table (symptom → likely cause). 2) Each of 5 causes with: symptom, DIY check, fix difficulty (1-5), when to call a plumber. 3) FAQ schema block. 4) Tools needed list. 5) Utah-specific note (hard water accelerates cartridge wear). 6) Strong CTA to emergency line.",
        "priority": "P0",
    },
    "can-a-crack-in-a-fiberglass-tub-be-repaired": {
        "primary_kw": "how to fix fiberglass tub crack",
        "primary_sv": "Ranking weakly: ~60 imp/month at pos 7.7 | Related: 'how to fix a cracked fiberglass tub' (pos 8.7), 'how to repair a crack in a fiberglass tub' (pos 8.0)",
        "secondary_kws": "fiberglass tub repair | bathtub crack repair kit | how to repair a cracked fiberglass bathtub | gelcoat crack repair | acrylic tub repair | bathtub repair putty",
        "entities": "fiberglass, gelcoat, epoxy resin, fiberglass mesh, bondo, acrylic, tub liner, surround panel, reglazing, refinishing, underlayment, drain flange",
        "icp": "Utah homeowner (35-65) with older (15+ year) fiberglass tub showing stress cracks. Budget-conscious — weighing DIY repair kit ($30-80) vs pro repair ($200-400) vs replacement ($1,500+). Handy but not a contractor.",
        "angle": "Cost-decision guide — 'Here's when repair works, when it won't, and what each option costs in 2026.' Be honest: some cracks can't be repaired. Show repair → refinish → replace decision tree. Include 'how long will the repair last?' (most guides skip this).",
        "serp_intent": "Mixed DIY/commercial — most want to DIY the fix but significant portion convert to service when they see the crack is structural.",
        "link_targets": "/services/bathroom-plumbing/, /services/plumbing-installation/, /services/plumbing-repair/",
        "must_have_sections": "1) Crack type visual guide (hairline / stress / structural). 2) 'Can it be repaired?' decision tree. 3) 2026 cost table: DIY kit / pro repair / refinish / replace. 4) Step-by-step DIY for hairline cracks. 5) When to call a pro (load-bearing cracks, leaks, large spiderwebs). 6) FAQ schema.",
        "priority": "P0",
    },
    "give-a-little-whistle-why-your-faucet-makes-a-squealing-noise": {
        "primary_kw": "why is my faucet squealing",
        "primary_sv": "Low traffic: 1 click/44 imp at pos 2.8 | Related: 'faucet squealing noise' (pos 3.3), 'squeaky faucet handle' (pos 2.5, 139 imp), 'faucet makes high pitched noise when off' (pos 5.9)",
        "secondary_kws": "faucet squealing noise | squeaky faucet handle | squeaky kitchen faucet handle | faucet makes high pitched noise | how to fix squeaky kitchen faucet handle | bathroom faucet squeaks",
        "entities": "faucet cartridge, washer, O-ring, valve seat, aerator, packing nut, ceramic disc, compression faucet, ball faucet, pressure regulator, water hammer",
        "icp": "Utah homeowner (30-60), hearing a new/worsening sound and worried about damage. DIY-comfortable for basic fixes. Usually investigating 1-3 bathrooms/kitchens in a single home.",
        "angle": "Sound-identification guide — 'What your faucet is trying to tell you.' Match specific sounds (squeal vs whistle vs hiss vs hum) to specific causes. Lead with: 'If it only happens when you turn it on → X. If it happens all the time → Y.'",
        "serp_intent": "Pure informational/DIY — low commercial conversion. Use this as a top-of-funnel educational piece with service-page links for repairs the homeowner won't do themselves.",
        "link_targets": "/services/faucet-repair/, /services/plumbing-repair/, /services/water-softeners/ (hard water is a Utah-specific cause)",
        "must_have_sections": "1) Rewrite title — drop the quirky 'Give a Little Whistle.' Use direct query-matching title. 2) Sound → cause diagnostic table. 3) 5 most common causes with DIY fixes. 4) Utah hard water angle (mineral buildup is #1 local cause). 5) When to replace vs repair the faucet. 6) FAQ schema.",
        "priority": "P0",
    },
    "flush-it-once-flush-it-twice-why-your-toilet-wont-flush-all-the-way": {
        "primary_kw": "why do i have to flush my toilet twice",
        "primary_sv": "Decent traffic: 4 clicks/73 imp at pos 4.0 ('have to flush toilet twice'), 2 clicks/151 imp pos 3.4 | Related: 'dual flush toilet not flushing completely' (pos 8), 'toilet takes two flushes' (pos 6.9)",
        "secondary_kws": "have to flush toilet twice | toilet takes two flushes | dual flush toilet not flushing completely | toilet needs to be flushed several times | toilet wont flush all the way | all toilets in house not flushing well",
        "entities": "flapper, fill valve, flush valve, float, tank water level, jets (rim jets + siphon jet), trapway, vent stack, wax ring, handle chain, drain line, sewer line",
        "icp": "Utah homeowner (25-65), annoyed but not panicked. Usually a slow-developing issue. Mix of DIY-comfortable and call-a-plumber. Often has a dual-flush toilet (popular in UT due to water-conservation incentives).",
        "angle": "Diagnostic flowchart — 'Toilet won't flush all the way? Start here.' Lead with a 3-question diagnostic: (1) Does water rise high in bowl? (2) Is flush weak from start or dies mid-flush? (3) Multiple toilets or just one? Each path leads to specific causes.",
        "serp_intent": "Informational w/ commercial bridge — 60% DIY, 40% convert to service calls when cause = drain line, vent stack, or sewer issue.",
        "link_targets": "/services/toilet-repair/, /services/drain-cleaning-utah/, /services/sewer-repair/",
        "must_have_sections": "1) Rewrite title — 'Toilet Won't Flush All the Way? 7 Causes & Fixes (2026 Guide)'. 2) 3-question diagnostic flowchart. 3) 7 causes in order of likelihood + fix difficulty. 4) 'Just one toilet vs all toilets' section (critical: multiple toilets = drain/sewer issue, needs pro). 5) FAQ schema. 6) Cost-to-fix table per cause.",
        "priority": "P0",
    },
    "how-to-thaw-frozen-pipes": {
        "primary_kw": "how to thaw frozen pipes",
        "primary_sv": "Dropped: 4 clicks/675 imp (90d) | Related: 'best way to thaw frozen pipes' (pos 84 — opportunity), 'how to unfreeze a pipe' (pos 38.5), 'will salt thaw a frozen drain' (pos 1.7 — 495 imp)",
        "secondary_kws": "how to unfreeze pipes | best way to thaw frozen pipes | how to thaw frozen water pipes | will salt thaw a frozen drain | at what temperature do pipes freeze | how to thaw frozen pipes in a wall",
        "entities": "pipe insulation, heat tape, heat cable, hair dryer, space heater, pipe burst, water expansion, main shutoff valve, frost line, freeze point, PEX, copper pipe, exterior wall, crawl space",
        "icp": "PANICKED Utah homeowner (all ages), caught in a cold snap (Utah gets -20°F). Needs answer NOW, likely on mobile. High emergency-plumber conversion if they think pipe may have burst.",
        "angle": "Emergency-first guide — 'Do these 3 things RIGHT NOW' at top of page. Then diagnostic: is it a frozen pipe or a burst pipe? Then thawing steps by pipe type and location. Utah-specific: emphasize crawl-space pipes and exterior-wall pipes which are the biggest Utah failure points.",
        "serp_intent": "Emergency informational — HIGHEST commercial conversion in this list. People reading this are scared. Strong emergency CTA placement throughout.",
        "link_targets": "/services/emergency-plumber/, /services/pipe-repair/, /services/frozen-pipe-repair/ if exists",
        "must_have_sections": "1) 'DO THIS FIRST' box at top (locate shutoff, open faucet to relieve pressure). 2) Diagnostic: frozen vs burst. 3) Thawing methods ranked by safety/speed. 4) What NOT to do (open flame, blowtorch). 5) How to prevent re-freezing. 6) Utah-specific: crawl spaces, rim joists, hose bibs. 7) Emergency CTA every ~400 words. 8) Expand from 541 to 1,400+ words. 9) FAQ schema. 10) Publish in October before winter.",
        "priority": "P0",
    },
    "pros-and-cons-of-blue-water-toilet-tablets": {
        "primary_kw": "are blue toilet tablets bad",
        "primary_sv": "STRONG performer: 12 clicks/139 imp at pos 1.4 | Related: 'do toilet bowl tablets work' (7 clicks, pos 2.7), 'do blue toilet tablets damage the toilet' (5 clicks, pos 2.5), 'blue toilet water' (4 clicks, 753 imp, pos 3.4)",
        "secondary_kws": "do toilet tablets work | are blue toilet tablets bad for toilet | do blue toilet tablets damage the toilet | is blue toilet water dangerous | toilet cleaning tablets | toilet tank blue tablets | are toilet tank tablets safe",
        "entities": "toilet tank, flapper, rubber gasket, chlorine tablet, bleach tablet, brand names (Clorox Automatic, Vanish, Fluidmaster, 2000 Flushes), fill valve, flush valve, tank-to-bowl gasket, acidic cleaners",
        "icp": "Utah homeowner (30-65), price-conscious, looking to save time on bathroom cleaning. Split between 'I use them, should I stop?' and 'thinking of buying, are they worth it?'",
        "angle": "Honest evidence-based take — most competitor articles are wishy-washy. Take a clear position: 'The short answer is no, and here's exactly why.' Include teardown of 3 popular brands. Cost-of-damage calculation ($5 tablets vs $300 flapper/gasket replacement).",
        "serp_intent": "Pure informational — but high-authority evidence-based position builds brand trust. LOW commercial conversion but strong for AI Overview citation.",
        "link_targets": "/services/toilet-repair/, /services/plumbing-repair/",
        "must_have_sections": "1) TL;DR answer box (Google AI Overview bait). 2) What's actually IN these tablets (chemistry). 3) What they damage (with timeline). 4) Brand teardown (3-4 popular tablets). 5) Safer alternatives. 6) What to do if you've been using them. 7) FAQ schema. 8) Fix orphan status — link from /services/toilet-repair/ and related blog posts.",
        "priority": "P1",
    },
    "what-is-the-typical-cost-for-a-toilet-repair": {
        "primary_kw": "toilet repair cost 2026",
        "primary_sv": "ZERO clicks currently — 62 imp at avg pos 30+ | Huge query pool: 'average cost to unclog a toilet' (14 imp, pos 17.3), 'average toilet replacement cost' (pos 21.2), 'blocked toilet plumber cost' (pos 27.3)",
        "secondary_kws": "toilet repair cost | average cost to unclog a toilet | average cost to replace a toilet | toilet plumber cost | cost to fix a running toilet | cost to replace toilet flapper | how much does a plumber charge to unclog a toilet",
        "entities": "flapper, fill valve, flush valve, wax ring, supply line, plunger, auger, closet auger, toilet flange, tank bolts, tank-to-bowl gasket, labor hourly rate, service call fee, emergency fee",
        "icp": "Utah homeowner (all demographics), actively price-shopping after a toilet issue. Comparing DIY costs to plumber costs. High commercial intent — they WILL hire someone soon.",
        "angle": "Comprehensive 2026 Utah pricing guide — 'exactly what your toilet repair should cost, broken down by problem type.' No 'ranges from $X to $Y' vagueness. Give specific 2026 numbers. Beat HomeAdvisor/Angi with local Utah pricing.",
        "serp_intent": "HIGHEST commercial intent in this list. Cost query = lead query. Every cost answer should bridge to 'get a free Beehive quote' CTA.",
        "link_targets": "/services/toilet-repair/ (primary), /services/emergency-plumber/, /services/plumbing-repair/",
        "must_have_sections": "1) 2026 cost table: repair type → parts cost → labor cost → total range. 2) Breakdown by problem: running toilet, clog, leak, flapper, fill valve, wax ring, full replacement. 3) DIY vs pro decision matrix (skills + tools + time required). 4) Why Utah pricing differs (labor rates, hard water accelerates wear). 5) Free quote CTA. 6) FAQ schema. 7) Get out of crawl depth 8 — needs inlink from homepage + service page.",
        "priority": "P0",
    },
    "whats-a-sewer-line-belly-how-do-you-fix-it": {
        "primary_kw": "what is a belly in a sewer line",
        "primary_sv": "Niche but convertible: 1 click/116 imp pos 10.1 | Related: 'bellied sewer line' (62 imp, pos 19.2), 'belly in main sewer line' (pos 29.5), 'bellied pipe' (18 imp, pos 19) — all striking-distance opportunities",
        "secondary_kws": "bellied sewer line | belly in sewer line | sewer line belly fix | bellied pipe | back pitched pipe | negative slope sewer line | sagging sewer line | low spot sewer line",
        "entities": "sewer line, main drain, trap, vent stack, cleanout, sewer camera inspection, hydro jetting, trenchless repair, pipe bursting, cured-in-place pipe (CIPP), excavation, sewer pipe materials (cast iron, clay, PVC, Orangeburg), bedding material, pipe slope, frost heave",
        "icp": "Utah homeowner (40-70), typically diagnosed by a plumber already ('you have a belly in your line'). Now researching what it means + cost to fix. VERY high commercial intent — this is a $3K-15K repair conversation.",
        "angle": "Expert explainer — 'A plumber told you your sewer line has a belly. Here's what that means, why it matters, and what fixing it costs in 2026.' Include video/imagery of camera-scope footage. Show the three repair options with pros/cons/costs.",
        "serp_intent": "HIGH commercial — these searchers are mid-funnel, often getting second opinions on quotes. Position as the authoritative, no-BS source.",
        "link_targets": "/services/sewer-repair/, /services/drain-cleaning-utah/, /services/sewer-camera-inspection/ if exists",
        "must_have_sections": "1) Visual diagram of sewer belly. 2) How a plumber diagnoses (camera scope). 3) Why bellies form (soil settling, frost heave, poor bedding, pipe material). 4) Symptoms homeowner notices. 5) 3 repair options: spot excavation, pipe bursting, CIPP lining — with 2026 Utah pricing. 6) Can it wait? (risk matrix). 7) Strong CTA for sewer scope inspection. 8) FAQ schema.",
        "priority": "P1",
    },
    "how-much-is-a-shower-faucet-repair": {
        "primary_kw": "shower faucet repair cost",
        "primary_sv": "Struggling: 1 click/33 imp pos 10.3 | Related: 'how much does a shower valve replacement cost' (pos 15.3), 'shower control valve' (pos 6.7)",
        "secondary_kws": "shower valve replacement cost | how much to replace a shower cartridge | shower faucet repair cost | cost to fix leaky shower | plumber cost to fix shower | shower diverter replacement cost",
        "entities": "shower cartridge, pressure-balancing valve, thermostatic valve, diverter, trim kit, rough-in valve, shower handle, escutcheon plate, valve seat, Moen/Delta/Kohler branded parts, access panel",
        "icp": "Utah homeowner (35-65) with a specific shower issue (drip, temperature fluctuation, handle stuck). Already identified it's a faucet problem. Price-shopping repair vs replacement.",
        "angle": "Plumber-insider cost guide — 'What your shower faucet repair will really cost, by symptom.' Break down by problem (drip, temp swing, stuck handle, diverter not working). Show parts cost + labor separately. Utah-specific: note hard-water damage common on cartridges.",
        "serp_intent": "HIGH commercial intent cost query. Convert heavily to service.",
        "link_targets": "/services/shower-repair/, /services/faucet-repair/, /services/plumbing-repair/",
        "must_have_sections": "1) 2026 cost table by symptom. 2) Parts vs labor breakdown. 3) When to DIY (cartridge swap) vs call pro (valve body replacement). 4) Branded part costs (Moen/Delta/Kohler). 5) Utah-specific: hard water accelerates cartridge wear. 6) Free quote CTA. 7) FAQ schema.",
        "priority": "P1",
    },
    "what-are-the-three-stages-of-new-construction-plumbing": {
        "primary_kw": "stages of new construction plumbing",
        "primary_sv": "ZERO clicks / 38 imp (90d) — page has lost relevance | Related: 'construction plumbing' (pos 1.0, 3 imp), 'describe the three different stages of plumbing work...' (pos 7) — mostly student homework queries, not commercial",
        "secondary_kws": "new construction plumbing phases | rough-in plumbing | top-out plumbing | finish plumbing | plumbing phases in construction | new home plumbing installation stages | plumbing construction timeline",
        "entities": "underground plumbing, rough-in plumbing, top-out (second rough), finish plumbing (trim-out), DWV (drain-waste-vent), water supply lines, manifold, fixtures, pressure test, inspection, building permit, P-trap, shower pan",
        "icp": "TWO audiences: (1) Utah homeowner building custom or major remodel (high commercial value, rare). (2) Students/contractors researching process (low commercial value, high volume). Write for audience 1 primarily.",
        "angle": "Utah homeowner's guide to new-construction plumbing — 'What happens when, what to inspect, what costs where, and what to watch for.' Don't write a textbook. Write it for the homeowner building or buying new construction who wants to know what they're paying for.",
        "serp_intent": "Low-to-medium commercial. This page is borderline — consider if it should be kept or noindexed. If kept, pivot toward custom-home/remodel audience.",
        "link_targets": "/services/new-construction-plumbing/, /services/remodel-plumbing/, /services/plumbing-installation/",
        "must_have_sections": "1) Decision: KEEP or NOINDEX? Recommend keeping and pivoting angle. 2) Stages with homeowner decision points at each. 3) What each stage costs in 2026. 4) Permit/inspection checkpoints. 5) Red flags to look for. 6) Utah-specific codes. 7) FAQ schema. 8) De-dupe from crawl depth 8 — needs homepage or /services/ inlink.",
        "priority": "P1",
    },
    "what-is-a-manabloc-system-and-is-it-worth-it": {
        "primary_kw": "what is a manabloc plumbing system",
        "primary_sv": "Has traffic: 12 clicks/2,874 imp (90d) at avg pos 3-5 | 'manabloc' (1 click, 1083 imp, pos 3.4), 'manabloc system' (pos 4.4), 'manabloc manifold' (pos 5.5, 480 imp) — striking distance to top 3",
        "secondary_kws": "manabloc plumbing system | manabloc manifold | manabloc pex | viega manabloc | pex manifold plumbing system | home run plumbing system | manabloc vs traditional plumbing | is manabloc worth it",
        "entities": "Viega ManaBloc, PEX tubing, home-run plumbing, manifold plumbing, crimp fittings, shut-off valves, cold/hot water distribution, fixture runs, water hammer arrestor, expansion tank, PEX-a vs PEX-b, trunk-and-branch plumbing",
        "icp": "Utah homeowner (35-65), usually found/inherited a ManaBloc in a newer home and researching it. Secondary: remodelers/new-construction buyers considering it. Medium commercial intent — mostly 'how do I use/maintain it' queries.",
        "angle": "Definitive ManaBloc guide for homeowners — 'You found it, here's how it works and whether it was worth the extra cost.' Mix educational with practical maintenance + when to call a plumber.",
        "serp_intent": "Informational w/ repair-service conversion — ManaBloc issues (leaks, stuck valves) require a plumber familiar with the system. Position Beehive as Utah ManaBloc experts.",
        "link_targets": "/services/plumbing-installation/, /services/pipe-repair/, /services/remodel-plumbing/",
        "must_have_sections": "1) How ManaBloc works (diagram). 2) ManaBloc vs traditional trunk-and-branch (comparison table). 3) Pros/cons. 4) Identifying ManaBloc parts + valve labels. 5) Common issues + fixes. 6) Maintenance schedule. 7) When to call a plumber familiar with ManaBloc. 8) Fix orphan status. 9) FAQ schema.",
        "priority": "P2",
    },
    "4-common-reasons-for-low-water-pressure": {
        "primary_kw": "causes of low water pressure in house",
        "primary_sv": "Currently 0 clicks / 91 imp at avg pos 50+ (buried) | Huge underserved pool: 'can a bad valve cause low water pressure' (14 imp, pos 1.0), 'house water pressure low' (25 imp, pos 88)",
        "secondary_kws": "low water pressure in house | causes of low water pressure | why is my water pressure low | sudden low water pressure | low water pressure in whole house | low water pressure one faucet | pressure regulator bad",
        "entities": "pressure regulator, pressure-reducing valve (PRV), main shutoff valve, water meter, aerator, mineral buildup, galvanized pipes, corroded pipes, leak, clogged fixture, main line, city water supply, well pump, pressure tank",
        "icp": "Utah homeowner (30-70), recently noticed pressure drop. Split between 'whole house' problem (main line/PRV issue — higher commercial) and 'one fixture' problem (aerator/supply line — DIY). Diagnostic mindset.",
        "angle": "Expand from 4 causes to 8-10 — competitors own this with comprehensive lists. Lead with the critical diagnostic: 'Is it ONE fixture or the WHOLE house?' That split determines everything. Utah-specific: hard water aerator clogs + older galvanized pipes in 1960s-70s SLC homes.",
        "serp_intent": "Mixed informational/commercial. Whole-house issues convert well. One-fixture issues stay DIY.",
        "link_targets": "/services/plumbing-repair/, /services/water-line-repair/, /services/water-softeners/",
        "must_have_sections": "1) 'One fixture vs whole house' diagnostic at top. 2) 8-10 causes (expand from 4). 3) DIY checks per cause. 4) Utah-specific: galvanized pipe aging, hard water aerator clogs, PRV life (7-12 years). 5) When to call a plumber. 6) Pressure measurement how-to (pressure gauge on hose bib). 7) FAQ schema. 8) Flowchart image.",
        "priority": "P1",
    },
    "what-is-a-flushometer-and-what-is-it-used-for": {
        "primary_kw": "what is a flushometer",
        "primary_sv": "STRONG: 8 clicks/437 imp at pos 1.9 | 'flushometer' (4 clicks, 5,413 imp at pos 3.2 — HUGE opportunity), 'flushometer toilet' (2,480 imp pos 2.5), 'flushometer valve' (1,143 imp pos 3.5)",
        "secondary_kws": "flushometer | flushometer toilet | flushometer valve | flushometer vs flush valve | diaphragm flushometer | piston flushometer | sloan flushometer | commercial toilet flush valve | manual vs automatic flushometer",
        "entities": "diaphragm flushometer, piston flushometer, manual handle, sensor/auto flush, Sloan, Zurn, Kohler, American Standard, flush valve, water-closet, urinal flushometer, ADA compliance, low-flow (1.6 gpf, 1.28 gpf), rebuild kit, vacuum breaker",
        "icp": "TWO audiences: (1) Commercial property owner/facilities manager (office building, school, restaurant in UT) — HIGH commercial value. (2) Curious homeowner who saw one at work/public restroom. Write for audience 1.",
        "angle": "Commercial-first rewrite — 'The complete guide to flushometers for commercial property owners.' Position Beehive as commercial plumbing experts. Include maintenance schedules, rebuild vs replace decision, ADA compliance, water savings ROI.",
        "serp_intent": "Mostly informational but high-value B2B lead for commercial plumbing services.",
        "link_targets": "/services/commercial-plumbing/, /services/toilet-repair/, /services/plumbing-installation/",
        "must_have_sections": "1) What a flushometer is (diagram). 2) Diaphragm vs piston (table). 3) Manual vs sensor/auto. 4) Major brands comparison (Sloan, Zurn, Kohler). 5) ADA compliance requirements. 6) Rebuild vs replace decision. 7) Water-savings ROI (old 3.5 gpf → new 1.28 gpf). 8) Commercial plumbing CTA. 9) FAQ schema. 10) Fix orphan status — link from /services/commercial-plumbing/.",
        "priority": "P2",
    },
    "signs-water-main-leak": {
        "primary_kw": "signs of a water main leak",
        "primary_sv": "Page is non-indexable in crawl (0 words) but STILL has impressions: 4 clicks/289 imp | 'main line water leak' (pos 18.1, 242 imp), 'what is a water main leak' (pos 3.1)",
        "secondary_kws": "water main leak symptoms | main water line leak | signs of underground water leak | how to tell if water main is leaking | water main leak detection | broken water main signs | sewer line vs water main leak",
        "entities": "water main, service line, main shutoff valve, city meter, curb stop, leak detection equipment (acoustic, thermal), slab leak, frost heave, ground settling, water pressure drop, wet spots in yard, sinkhole, water bill spike, municipal vs private responsibility",
        "icp": "PANICKED Utah homeowner (35-70), noticed one or more symptoms (wet spot, high bill, low pressure, sinking yard). Water main leaks are $5K-20K repairs. EXTREMELY HIGH commercial intent + emergency.",
        "angle": "EMERGENCY FIRST — Page is currently broken (0 words crawled, non-indexable). Fix the indexation issue FIRST, then rebuild as Beehive's authority page on water main leaks. 'The 9 signs you have a water main leak — and what to do TODAY.'",
        "serp_intent": "EMERGENCY COMMERCIAL — highest $ per click of any URL in this list. A water main repair is $5K-20K. Every sign-recognition section needs an emergency CTA.",
        "link_targets": "/services/water-main-repair/, /services/leak-detection/, /services/emergency-plumber/",
        "must_have_sections": "1) FIX INDEXATION FIRST — run GSC URL Inspection, check for noindex tag, fix 0-word issue, verify content renders. 2) DO THIS FIRST emergency box (shut off main valve, call plumber, document for insurance). 3) 9 signs (wet spots, water bill spike, pressure drop, discolored water, sinkholes, cracked foundation, mold/mildew, sound of running water with taps off, yard damage). 4) Who is responsible (homeowner vs city) — curb stop line. 5) Leak detection methods. 6) Repair cost ranges 2026. 7) Utah-specific: frost heave, clay soil settling, expansive soils. 8) Emergency CTA every section. 9) FAQ schema. 10) Inlink from homepage + /services/water-main-repair/.",
        "priority": "P0",
    },
}

wb = Workbook()
ws = wb.active
ws.title = "Blog Recovery Plan"

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
subtitle_font = Font(name="Calibri", size=10, italic=True, color="595959")
cell_font = Font(name="Calibri", size=10)
cell_font_small = Font(name="Calibri", size=9)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="top", wrap_text=True)
thin = Side(border_style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

red_fill = PatternFill("solid", fgColor="F8CBAD")
yellow_fill = PatternFill("solid", fgColor="FFF2CC")
green_fill = PatternFill("solid", fgColor="C6E0B4")
section_fill = PatternFill("solid", fgColor="DDEBF7")

ws["A1"] = "Beehive Plumbing \u2014 Blog Post Recovery Plan (Writer Brief)"
ws["A1"].font = title_font
ws.merge_cells("A1:X1")
ws["A2"] = "Top 14 blog posts driving 84.3% of YoY click decline (Jan 2025 vs Jan 2026) | Total clicks lost: -3,388 | Primary KWs sourced from live GSC data (90d)"
ws["A2"].font = subtitle_font
ws.merge_cells("A2:X2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

# Column groups — Traffic Data, Diagnostic Signals, Keyword Strategy, Writer Brief, Actions
group_row = 3
ws.cell(row=group_row, column=1, value="").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=1, end_row=group_row, end_column=6)
ws.cell(row=group_row, column=1, value="TRAFFIC DATA").alignment = center
ws.cell(row=group_row, column=1).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=7, value="DIAGNOSTIC SIGNALS").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=7, end_row=group_row, end_column=11)
ws.cell(row=group_row, column=7).alignment = center
ws.cell(row=group_row, column=7).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=12, value="KEYWORD STRATEGY (GSC 90d)").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=12, end_row=group_row, end_column=15)
ws.cell(row=group_row, column=12).alignment = center
ws.cell(row=group_row, column=12).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=16, value="WRITER BRIEF").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=16, end_row=group_row, end_column=20)
ws.cell(row=group_row, column=16).alignment = center
ws.cell(row=group_row, column=16).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=21, value="ACTIONS & TRACKING").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=21, end_row=group_row, end_column=24)
ws.cell(row=group_row, column=21).alignment = center
ws.cell(row=group_row, column=21).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

for col in range(1, 25):
    c = ws.cell(row=group_row, column=col)
    if not c.fill.fgColor.rgb or c.fill.fgColor.rgb == "00000000":
        c.fill = section_fill

ws.row_dimensions[group_row].height = 20

headers = [
    # TRAFFIC DATA (1-6)
    "#", "URL", "Clicks Jan 2025", "Clicks Jan 2026", "Clicks Lost", "% of Decline",
    # DIAGNOSTIC (7-11)
    "Indexation", "Word Count", "Crawl Depth", "Unique Inlinks", "Perf Score",
    # KEYWORD STRATEGY (12-15)
    "Primary Keyword", "Current Ranking Data", "Secondary Keywords", "Entities to Cover",
    # WRITER BRIEF (16-20)
    "ICP (Who We're Writing For)", "Content Angle", "SERP Intent & Conversion", "Internal Link Targets", "Must-Have Sections",
    # ACTIONS & TRACKING (21-24)
    "Priority", "Status", "Owner", "Writer Notes",
]

for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 42

for i, row in merged.iterrows():
    key = row["URL_key"]
    brief = writer_briefs.get(key, {})
    r = i + 5
    values = [
        i + 1,
        row["URL"],
        int(row["Clicks Jan 2025"]) if pd.notna(row["Clicks Jan 2025"]) else "",
        int(row["Clicks Jan 2026"]) if pd.notna(row["Clicks Jan 2026"]) else "",
        int(row["Clicks Lost"]) if pd.notna(row["Clicks Lost"]) else "",
        row["Cumulative %"],
        row.get("Indexed Status", "") if pd.notna(row.get("Indexed Status")) else "",
        int(row["Word Count"]) if pd.notna(row.get("Word Count")) else "",
        int(row["Crawl Depth"]) if pd.notna(row.get("Crawl Depth")) else "N/A",
        int(row["Unique InLinks"]) if pd.notna(row.get("Unique InLinks")) else "",
        int(row["Perf Score"]) if pd.notna(row.get("Perf Score")) else "N/A",
        brief.get("primary_kw", ""),
        brief.get("primary_sv", ""),
        brief.get("secondary_kws", ""),
        brief.get("entities", ""),
        brief.get("icp", ""),
        brief.get("angle", ""),
        brief.get("serp_intent", ""),
        brief.get("link_targets", ""),
        brief.get("must_have_sections", ""),
        brief.get("priority", "P1"),
        "Not Started",
        "",
        "",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col >= 12 else cell_font
        c.border = border
        if col in (1, 3, 4, 5, 6, 8, 9, 10, 11, 21, 22):
            c.alignment = center
        else:
            c.alignment = left
        if col == 7 and v == "Non-Indexable":
            c.fill = red_fill
            c.font = Font(name="Calibri", size=10, bold=True, color="9C0006")
        if col == 11 and isinstance(v, int):
            if v < 40:
                c.fill = red_fill
            elif v < 70:
                c.fill = yellow_fill
        if col == 10 and isinstance(v, int) and v <= 2:
            c.fill = red_fill
        if col == 21:
            if v == "P0":
                c.fill = red_fill
                c.font = Font(name="Calibri", size=10, bold=True, color="9C0006")
            elif v == "P1":
                c.fill = yellow_fill
            elif v == "P2":
                c.fill = green_fill

widths = {
    "A": 4, "B": 45, "C": 10, "D": 10, "E": 10, "F": 10,
    "G": 14, "H": 10, "I": 10, "J": 11, "K": 10,
    "L": 30, "M": 45, "N": 50, "O": 50,
    "P": 50, "Q": 55, "R": 40, "S": 35, "T": 70,
    "U": 9, "V": 13, "W": 14, "X": 22,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for r in range(5, 5 + len(merged)):
    ws.row_dimensions[r].height = 240

ws.freeze_panes = "C5"

# ========================================================================
# SHEET 2 — Summary & Writing Standards
# ========================================================================
ws2 = wb.create_sheet("Summary & Writing Standards")
ws2["A1"] = "Recovery Context & Writing Standards"
ws2["A1"].font = title_font
ws2.merge_cells("A1:B1")

ctx = [
    ("", ""),
    ("=== THE NUMBERS ===", ""),
    ("Total clicks lost (14 posts)", "-3,388"),
    ("% of total blog click decline", "84.3%"),
    ("% of total site click decline", "73.8% (of 4,590 total)"),
    ("Comparison window", "Jan 2025 vs Jan 2026 (GSC)"),
    ("Data source for primary KWs", "Live GSC query data, last 90 days (April 17 2026)"),
    ("", ""),
    ("=== ROOT CAUSES ===", ""),
    ("1. Site-wide CWV failure", "Median LCP 19.8s (threshold 2.5s) \u2014 every post ranked below speed-competitive rivals"),
    ("2. Orphan/underlinked content", "Median 2 inlinks (mostly from pagination) \u2014 no equity flow from service/home pages"),
    ("3. Deep crawl depth", "Median depth 6-8 \u2014 Google deprioritizes buried content"),
    ("4. Content not refreshed", "Most posts 1-2 years old; competitors ship updated content quarterly"),
    ("5. Template title tags", "54% of site has titles >60 chars (truncated in SERP = lower CTR)"),
    ("6. Missing FAQ schema", "AI Overviews + PAA features likely eating clicks"),
    ("7. Content outside topical border", "Some posts (bidets, urinals) attract non-converting global traffic"),
    ("", ""),
    ("=== PRIORITY BATCHES ===", ""),
    ("P0 \u2014 Start this week (7 posts)", "shower not working, fiberglass tub, faucet squealing, toilet flush twice, thaw frozen pipes, typical cost toilet repair, signs water main leak"),
    ("P1 \u2014 Start next 2 weeks (5 posts)", "sewer line belly, shower faucet repair, new construction plumbing, 4 reasons low water pressure, blue water toilet tablets"),
    ("P2 \u2014 Queue for month 2 (2 posts)", "manabloc system, flushometer"),
    ("", ""),
    ("=== WRITING STANDARDS (from semantic audit) ===", ""),
    ("Definition-first sentence", "First sentence must be a direct, definitive answer to the query. NO modality ('one of the most trusted', 'arguably the best'). NO PAS openings. Example: 'A shower that won't turn on is usually caused by one of 5 things: [list].'"),
    ("Macro/micro balance target", "70-80% macro content (core information), 20-30% micro (supporting detail). Strip marketing fluff."),
    ("Entity-Attribute-Value triples", "Every fact gets a value. 'Drain cleaning costs $150-$300' beats 'Drain cleaning is affordable.' Concrete > vague."),
    ("Content funnel rule", "Every blog post must link to at least one /services/ page. Currently ~13 of 14 posts fail this."),
    ("Title tag rule", "Max 60 characters. Benefit + query match. No cute/clever if it hurts clarity."),
    ("Meta description rule", "Max 155 characters. Lead with specific benefit + clear CTA hint."),
    ("FAQ schema", "Add 3-5 Q&As to every post with proper schema.org/FAQPage markup. Answers should be 2-3 sentences max."),
    ("Utah local angle", "Every post needs 1 Utah-specific section where possible (hard water, climate, local codes, service areas, frost heave, etc.)"),
    ("Author E-E-A-T", "Add named technician byline with credentials (Licensed Master Plumber, X years, Utah license #)"),
    ("Content freshness", "Update publish date to 2026 when content is refreshed. Google uses modified-date as a freshness signal."),
    ("", ""),
    ("=== ICP DEFINITION (Beehive ideal reader) ===", ""),
    ("Geography", "Utah \u2014 Salt Lake City metro, Wasatch Front, primary service areas"),
    ("Primary demographic", "Homeowners, age 30-65, household income $75K-$200K, suburban single-family homes"),
    ("Mindset at time of reading", "Problem-aware (something is broken/sounds wrong/costs too much). Either DIY-curious or decision-making about hiring."),
    ("Technical level", "Not a contractor. Knows enough to change a washer but not enough to rebuild a valve. Respects expert guidance without condescension."),
    ("Decision triggers", "Cost transparency, speed (emergency = convert), local trust (Utah technician, real address, real license)"),
    ("Utility-specific concerns", "Hard water (#1 Utah plumbing issue), old galvanized pipes in SLC (1950s-70s), frost heave on sewer lines, clay expansive soils"),
    ("", ""),
    ("=== APPLY TO EACH POST (10 steps) ===", ""),
    ("1. Indexation check", "Run GSC URL Inspection \u2014 confirm indexed, no noindex tag, canonical correct"),
    ("2. SERP analysis", "Pull top 3 competitors. Match their depth + entity coverage. Find their gaps."),
    ("3. Rewrite opening", "Definition-first sentence. NO PAS. NO modality."),
    ("4. Expand entity coverage", "Use the entities list from the brief \u2014 every entity gets at least 1 sentence of coverage."),
    ("5. Add FAQ schema", "3-5 common questions from the GSC 'Current Ranking Data' column"),
    ("6. Rewrite title + meta", "Use primary keyword. Max 60 chars title. 155 chars meta. Benefit-forward."),
    ("7. Internal linking", "Add 2-3 inlinks FROM service pages TO this post. Add 2-3 inlinks FROM this post TO service pages."),
    ("8. Refresh dates + signals", "Update publish date. Update any stats/pricing to 2026."),
    ("9. Resubmit to GSC", "Request re-indexing after changes via GSC URL Inspection"),
    ("10. Track for 8 weeks", "Monitor clicks, impressions, position weekly. Expect first movement in 3-4 weeks."),
]

for r, (k, v) in enumerate(ctx, 2):
    c1 = ws2.cell(row=r, column=1, value=k)
    c2 = ws2.cell(row=r, column=2, value=v)
    if k and not v:
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    else:
        c1.font = Font(name="Calibri", size=10, bold=True)
        c2.font = cell_font
        c2.alignment = Alignment(wrap_text=True, vertical="top")

ws2.column_dimensions["A"].width = 42
ws2.column_dimensions["B"].width = 110

for r in range(2, 2 + len(ctx)):
    ws2.row_dimensions[r].height = 38

wb.save(out)
print(f"Saved: {out}")
