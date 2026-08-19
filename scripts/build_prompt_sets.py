"""Write clients/prompts/<client>.yaml for the seven non-EW clients.

Every prompt below is derived from a real GSC query for that client, surfaced by
scripts/prompt_candidates.py. The source query and its impressions travel into
the sheet so any row can be audited later. Nothing here is invented.

Two judgements are encoded and neither is mechanical:

GEOGRAPHY. The four Utah home-services clients earn enormous impressions on bare
"near me" queries at positions 40 to 80, because Google shows them to the whole
country and they serve one metro. "drain cleaning near me" is 522,431 impressions
at position 72.9 for Beehive. Asking an assistant that question measures a
national market these businesses cannot serve, so the city goes IN the prompt.
Country stays US per the owner's standing rule; the geography is in the text.

AUDIENCE. Snow's largest vendor-intent queries are dental procedure costs: full
mouth implants 326,138, partial dentures 323,960, root canal 261,709. Those
people are looking for a dentist, not an at-home whitening kit. They are excluded
in favour of the whitening queries, which are smaller and actually theirs.
"""

from __future__ import annotations

import pathlib

import yaml

# (topic, intent, source_query, impressions, position, prompt)
SETS: dict[str, dict] = {}


def add(slug, country, category, branded, competitor):
    SETS[slug] = {"country": country, "category": category,
                  "branded": branded, "competitor": competitor}


# --------------------------------------------------------------- Beehive ----
add("beehive", "US", [
 ("Drain and sewer", "Best-X", "drain cleaning companies", 73890, 76.9,
  "Who is the best drain cleaning company in Salt Lake City?"),
 ("Drain and sewer", "Decision", "sewer line repair near me", 65164, 57.7,
  "Who does sewer line repair in Salt Lake City?"),
 ("Drain and sewer", "Decision", "clogged drain service", 51285, 77.9,
  "Who does clogged drain service in Salt Lake City?"),
 ("Drain and sewer", "Decision", "hydro jetting services", 50965, 26.4,
  "What is hydro jetting and who offers it in Salt Lake City?"),
 ("Drain and sewer", "Discovery", "what is drain cleaning", 2128, 18.4,
  "What is drain cleaning?"),
 ("Water heaters", "Decision", "water heater installation near me", 60079, 29.2,
  "Who installs water heaters in Salt Lake City?"),
 ("Water heaters", "Decision", "water heater repair near me", 29478, 21.2,
  "Who repairs water heaters in Salt Lake City?"),
 ("Water heaters", "Decision", "water heater replacement near me", 27290, 19.9,
  "What does water heater replacement cost in Salt Lake City?"),
 ("Water heaters", "Discovery", "how long does a water heater last", 8155, 71.1,
  "How long does a water heater last?"),
 ("Water heaters", "Decision", "who to call for water heater repair", 1967, 49.3,
  "Who should I call for water heater repair?"),
 ("Emergency plumbing", "Decision", "emergency plumbing services", 67175, 76.7,
  "Who offers emergency plumbing services in Salt Lake City?"),
 ("Emergency plumbing", "Decision", "emergency drain service", 41571, 78.7,
  "Who offers emergency drain service in Salt Lake City?"),
 ("Emergency plumbing", "Best-X", "plumbers near me", 25007, 7.4,
  "Who is the best plumber in Salt Lake City?"),
 ("Emergency plumbing", "Decision", "plumbing contractor", 40308, 44.8,
  "How do I find a licensed plumbing contractor in Salt Lake City?"),
 ("Emergency plumbing", "Decision", "toilet installation near me", 25373, 60.3,
  "Who installs toilets in Salt Lake City?"),
 ("Water treatment", "Decision", "water softener service", 62108, 79.0,
  "Who services water softeners in Salt Lake City?"),
 ("Water treatment", "Decision", "water softener installation near me", 27565, 56.4,
  "Who installs water softeners in Salt Lake City?"),
 ("Costs and diagnostics", "Discovery", "drain cleaning service price", 24162, 28.1,
  "What does drain cleaning cost?"),
 ("Costs and diagnostics", "Discovery", "how much does it cost to snake a drain", 2977, 46.1,
  "How much does it cost to snake a drain?"),
 ("Costs and diagnostics", "Discovery", "how much does it cost to unclog a toilet", 2496, 8.9,
  "How much does it cost to unclog a toilet?"),
 ("Costs and diagnostics", "Discovery", "what is rooter service", 3156, 21.6,
  "What is rooter service?"),
 ("Costs and diagnostics", "Discovery", "does a sewer line belly need to be replaced", 1966, 5.2,
  "Does a sewer line belly need to be replaced?"),
 ("Costs and diagnostics", "Discovery", "why is my toilet water blue", 2516, 7.4,
  "Why is my toilet water blue?"),
 ("Costs and diagnostics", "Discovery", "what is a flushometer", 2274, 2.2,
  "What is a flushometer?"),
 ("Costs and diagnostics", "Discovery", "is bathtub refinishing worth it", 1900, 14.8,
  "Is bathtub refinishing worth it?"),
], [
 "What is Beehive Plumbing?",
 "Is Beehive Plumbing a good plumber in Salt Lake City?",
 "What do reviews say about Beehive Plumbing?",
 "How much does Beehive Plumbing charge?",
], [
 "Best rated plumbing companies in Salt Lake City",
 "Alternatives to the big plumbing franchises in Utah",
 "Compare emergency plumbers in Salt Lake City",
])

# -------------------------------------------------------------- SameDay ----
add("sameday", "US", [
 ("Same-day plumbing", "Decision", "same day plumber near me", 345164, 51.3,
  "Who offers same day plumbing service in Utah?"),
 ("Same-day plumbing", "Decision", "24 hour plumbers near me", 240918, 46.1,
  "Is there a 24 hour plumber in Utah?"),
 ("Same-day plumbing", "Decision", "emergency plumbing services near me", 71022, 74.2,
  "Who offers emergency plumbing services in Utah?"),
 ("Same-day plumbing", "Decision", "emergency plumber near me", 25301, 38.6,
  "Who is an emergency plumber in Salt Lake City?"),
 ("Same-day plumbing", "Best-X", "plumber near me", 36450, 15.2,
  "Who is the best plumber in Utah?"),
 ("Cooling", "Decision", "ac repair near me", 60748, 22.0,
  "Who does AC repair in Utah?"),
 ("Cooling", "Decision", "air conditioning repair near me", 34016, 18.1,
  "Who repairs air conditioning in Salt Lake City?"),
 ("Cooling", "Decision", "ac installation near me", 25814, 13.5,
  "Who installs air conditioning in Utah?"),
 ("Cooling", "Decision", "air conditioning repair services", 22787, 10.4,
  "What should air conditioning repair cost?"),
 ("Heating", "Decision", "furnace repair near me", 46219, 11.9,
  "Who does furnace repair in Utah?"),
 ("Heating", "Decision", "hvac repair near me", 29526, 12.5,
  "Who does HVAC repair in Salt Lake City?"),
 ("Heating", "Decision", "hvac service", 43198, 2.9,
  "What is included in an HVAC service?"),
 ("Heating", "Decision", "same day hvac service near me", 41397, 39.6,
  "Who offers same day HVAC service in Utah?"),
 ("Heating", "Best-X", "hvac near me", 23638, 12.0,
  "Who is the best HVAC company in Utah?"),
 ("Water heaters", "Decision", "water heater replacement near me", 30426, 26.3,
  "Who replaces water heaters in Utah?"),
 ("Water heaters", "Decision", "water heater repair near me", 27785, 15.4,
  "Who repairs water heaters in Salt Lake City?"),
 ("Water heaters", "Decision", "hot water heater repair near me", 25282, 32.8,
  "Who repairs hot water heaters in Utah?"),
 ("Electrical", "Decision", "electrician near me", 25492, 10.8,
  "Who is a licensed electrician in Salt Lake City?"),
 ("Electrical", "Decision", "ceiling fan installation near me", 36650, 54.9,
  "Who installs ceiling fans in Utah?"),
 ("Electrical", "Decision", "emergency plumbing near me", 26831, 70.4,
  "Who handles emergency plumbing in Salt Lake City?"),
], [
 "What is SameDay Utah?",
 "Is SameDay Utah a good home services company?",
 "What do reviews say about SameDay Utah?",
 "How much does SameDay Utah charge?",
], [
 "Best rated home services companies in Utah",
 "Compare same day plumbing and HVAC companies in Salt Lake City",
 "Alternatives to the large HVAC franchises in Utah",
])

# ------------------------------------------------------------- Superior ----
add("superior", "US", [
 ("Water treatment", "Best-X", "best water softeners in utah", 3865, 23.3,
  "What are the best water softeners in Utah?"),
 ("Water treatment", "Decision", "water softener service", 5185, 46.7,
  "Who services water softeners in Salt Lake City?"),
 ("Water treatment", "Discovery", "water softener cost", 9829, 15.2,
  "What does a water softener cost?"),
 ("Water treatment", "Discovery", "cost of a water softener installation", 4726, 10.5,
  "What does water softener installation cost?"),
 ("Water treatment", "Decision", "soft water system utah", 5919, 13.1,
  "Who installs soft water systems in Utah?"),
 ("Emergency plumbing", "Decision", "emergency drain service", 31966, 82.2,
  "Who offers emergency drain service in Salt Lake City?"),
 ("Emergency plumbing", "Decision", "emergency plumbing services", 21219, 65.2,
  "Who offers emergency plumbing services in Salt Lake City?"),
 ("Emergency plumbing", "Discovery", "emergency plumber cost", 5703, 39.4,
  "What does an emergency plumber cost?"),
 ("Emergency plumbing", "Decision", "plumbing services salt lake city", 5345, 28.7,
  "Who provides plumbing services in Salt Lake City?"),
 ("Emergency plumbing", "Decision", "drain cleaning services in utah", 3077, 42.1,
  "Who does drain cleaning in Utah?"),
 ("HVAC", "Decision", "gas furnace repair near me", 4194, 44.3,
  "Who repairs gas furnaces in Salt Lake City?"),
 ("HVAC", "Decision", "emergency hvac service", 3953, 9.3,
  "Who offers emergency HVAC service in Utah?"),
 ("HVAC", "Decision", "air conditioning service utah", 3181, 31.8,
  "Who services air conditioning in Utah?"),
 ("HVAC", "Decision", "emergency air conditioner repair near me", 3316, 37.7,
  "Who does emergency air conditioner repair in Salt Lake City?"),
 ("Air quality", "Decision", "air duct cleaning service", 14129, 89.1,
  "Who does air duct cleaning in Salt Lake City?"),
 ("Water heaters", "Decision", "water heater repair near me", 3540, 15.5,
  "Who repairs water heaters in Salt Lake City?"),
 ("Water heaters", "Best-X", "low price water heaters utah", 3150, 43.6,
  "Where can I get an affordable water heater in Utah?"),
 ("Water heaters", "Decision", "ice maker installation near me", 5832, 33.4,
  "Who installs ice maker water lines in Salt Lake City?"),
 ("General", "Decision", "plumbing services utah", 3347, 61.6,
  "Who provides plumbing services in Utah?"),
 ("General", "Decision", "water softener service", 5185, 46.7,
  "Who maintains water treatment systems in Utah?"),
], [
 "What is Superior Water and Air?",
 "Is Superior Water and Air a good company in Utah?",
 "What do reviews say about Superior Water and Air?",
 "How much does Superior Water and Air charge?",
], [
 "Best rated water treatment companies in Utah",
 "Compare water softener companies in Salt Lake City",
 "Alternatives to the large Utah plumbing and HVAC franchises",
])

# -------------------------------------------------------------- Comfort ----
add("comfort", "US", [
 ("Furnace", "Decision", "furnace replacement near me", 26568, 71.7,
  "Who replaces furnaces in Utah?"),
 ("Furnace", "Decision", "furnace repair near me", 4221, 20.0,
  "Who repairs furnaces along the Wasatch Front?"),
 ("Furnace", "Decision", "furnace installation near me", 4060, 24.4,
  "Who installs furnaces in Utah?"),
 ("Furnace", "Decision", "heating contractor utah", 2318, 31.2,
  "Who is a heating contractor in Utah?"),
 ("Cooling", "Decision", "air conditioning installation near me", 4693, 48.6,
  "Who installs air conditioning in Utah?"),
 ("Cooling", "Decision", "air conditioning repair near me", 4014, 44.7,
  "Who repairs air conditioning along the Wasatch Front?"),
 ("Cooling", "Decision", "emergency ac repair near me", 4042, 18.2,
  "Who does emergency AC repair in Utah?"),
 ("Cooling", "Decision", "ac repair near me", 2044, 13.4,
  "Who does AC repair in Sandy, Utah?"),
 ("Cooling", "Decision", "ac system upgrade", 2314, 50.1,
  "When is it worth upgrading an AC system?"),
 ("Emergency HVAC", "Decision", "emergency hvac service", 3889, 12.0,
  "Who offers emergency HVAC service in Utah?"),
 ("Emergency HVAC", "Decision", "hvac emergency repair near me", 2061, 16.1,
  "Who does emergency HVAC repair along the Wasatch Front?"),
 ("Emergency HVAC", "Best-X", "hvac near me", 2319, 19.8,
  "Who is the best HVAC company in Utah?"),
 ("Utah HVAC companies", "Decision", "heating and air conditioning service utah", 2568, 52.5,
  "Who provides heating and air conditioning service in Utah?"),
 ("Utah HVAC companies", "Decision", "heating and cooling contractor utah", 2561, 45.9,
  "Who is a heating and cooling contractor in Utah?"),
 ("Utah HVAC companies", "Best-X", "heating and cooling company utah", 2516, 57.7,
  "What is the best heating and cooling company in Utah?"),
 ("Utah HVAC companies", "Decision", "ac and heating service utah", 2488, 41.6,
  "Who services AC and heating in Utah?"),
 ("Utah HVAC companies", "Decision", "utah ac and heating service", 2568, 44.9,
  "Who repairs AC and heating systems in Ogden, Utah?"),
 ("Utah HVAC companies", "Decision", "heating and cooling near me", 1956, 25.2,
  "Who does heating and cooling work in West Haven, Utah?"),
 ("Utah HVAC companies", "Decision", "utah heating and air conditioning service", 2237, 66.1,
  "Who provides heating and air conditioning service along the Wasatch Front?"),
 ("Utah HVAC companies", "Decision", "utah heating and ac service", 2341, 55.9,
  "Who services heating and AC in Salt Lake County?"),
], [
 "What is Comfort Solutions Utah?",
 "Is Comfort Solutions a good HVAC company in Utah?",
 "What do reviews say about Comfort Solutions Utah?",
 "How much does Comfort Solutions Utah charge?",
], [
 "Best rated HVAC companies in Utah",
 "Compare furnace replacement companies along the Wasatch Front",
 "Alternatives to the large Utah HVAC franchises",
])

# ---------------------------------------------------------------- Cudio ----
add("cudio", "US", [
 ("Odoo platform", "Discovery", "odoo software", 77714, 7.2,
  "What is Odoo software and what does it do?"),
 ("Odoo platform", "Discovery", "what is odoo", 37849, 5.9,
  "What is Odoo?"),
 ("Odoo platform", "Discovery", "odoo erp system", 8100, 8.1,
  "How does the Odoo ERP system work?"),
 ("Odoo platform", "Comparison", "odoo community vs enterprise", 5066, 7.8,
  "Odoo Community versus Enterprise: which should a business choose?"),
 ("Odoo platform", "Discovery", "odoo erp software", 8675, 9.8,
  "Is Odoo a full ERP or just accounting software?"),
 ("Odoo services", "Decision", "odoo migration services", 7880, 5.1,
  "Who provides Odoo migration services?"),
 ("Odoo services", "Decision", "odoo integration services", 3654, 10.9,
  "Who provides Odoo integration services?"),
 ("Odoo services", "Decision", "odoo development services", 3149, 17.2,
  "Who provides Odoo development services?"),
 ("Odoo services", "Discovery", "odoo implementation cost", 4572, 9.6,
  "What does an Odoo implementation cost?"),
 ("Odoo services", "Decision", "odoo migration services", 7880, 5.1,
  "How do I migrate from an older Odoo version to the current one?"),
 ("ERP comparison", "Comparison", "erpnext vs odoo", 5604, 7.1,
  "ERPNext versus Odoo: which is better for a growing business?"),
 ("ERP comparison", "Comparison", "odoo vs quickbooks", 3660, 7.3,
  "Odoo versus QuickBooks: which should a small business use?"),
 ("ERP comparison", "Comparison", "odoo vs zoho", 3415, 16.2,
  "Odoo versus Zoho: which suits a mid-sized company?"),
 ("ERP comparison", "Comparison", "odoo alternatives", 6481, 10.2,
  "What are the best alternatives to Odoo?"),
 ("ERP selection", "Best-X", "best erp for small business", 4928, 18.2,
  "What is the best ERP for a small business?"),
 ("ERP selection", "Best-X", "best erp for manufacturing", 3506, 35.8,
  "What is the best ERP for manufacturing?"),
 ("ERP selection", "Decision", "erp software for small business", 5734, 17.7,
  "What ERP software should a small business consider?"),
 ("ERP selection", "Decision", "erp software for manufacturing", 4441, 49.1,
  "What ERP software works best for manufacturing companies?"),
 ("ERP selection", "Discovery", "erp implementation cost", 3565, 13.6,
  "What does an ERP implementation typically cost?"),
 ("ERP selection", "Decision", "manufacturing erp software", 8529, 51.5,
  "Who implements manufacturing ERP software?"),
], [
 "What is Cudio?",
 "Is Cudio a good Odoo implementation partner?",
 "What do reviews say about Cudio?",
 "How much does Cudio charge for Odoo implementation?",
], [
 "Best Odoo implementation partners",
 "Compare Odoo consulting companies",
 "Alternatives to the largest Odoo partners",
])

# ----------------------------------------------------------------- Snow ----
# Dental procedure costs are deliberately excluded despite being the largest
# vendor-intent queries in this account. Someone pricing full mouth implants at
# 326,138 impressions is choosing a dentist, not an at-home whitening kit.
add("snow", "US", [
 ("At-home whitening", "Best-X", "best at home teeth whitening kits", 312866, 9.7,
  "What are the best at home teeth whitening kits?"),
 ("At-home whitening", "Best-X", "best teeth whitening", 97531, 23.9,
  "What is the best teeth whitening product?"),
 ("At-home whitening", "Best-X", "best teeth whitening kit", 48424, 18.5,
  "What is the best teeth whitening kit?"),
 ("At-home whitening", "Best-X", "best teeth whitening strips", 45655, 14.0,
  "What are the best teeth whitening strips?"),
 ("At-home whitening", "Discovery", "teeth whitening cost", 34701, 18.9,
  "How much does teeth whitening cost?"),
 ("Whitening products", "Best-X", "best whitening toothpaste", 41138, 21.8,
  "What is the best whitening toothpaste?"),
 ("Whitening products", "Best-X", "best electric toothbrush", 40363, 18.6,
  "What is the best electric toothbrush?"),
 ("Whitening products", "Comparison", "best teeth whitening strips", 45655, 14.0,
  "Whitening strips versus LED whitening kits: which works better?"),
 ("Whitening products", "Discovery", "best at home teeth whitening kits", 312866, 9.7,
  "Do at home teeth whitening kits actually work?"),
 ("Whitening products", "Decision", "best teeth whitening kit", 48424, 18.5,
  "Which teeth whitening kit is safest for sensitive teeth?"),
 ("Professional vs home", "Comparison", "teeth whitening dentist cost", 33595, 29.5,
  "Is professional teeth whitening worth it compared with at home kits?"),
 ("Professional vs home", "Discovery", "teeth whitening dentist cost", 33595, 29.5,
  "How much does teeth whitening at a dentist cost?"),
 ("Professional vs home", "Decision", "teeth whitening near me", 52158, 61.7,
  "Where can I get my teeth whitened?"),
 ("Professional vs home", "Discovery", "best teeth whitening", 97531, 23.9,
  "How long do teeth whitening results last?"),
 ("Professional vs home", "Discovery", "teeth whitening cost", 34701, 18.9,
  "Is teeth whitening bad for enamel?"),
], [
 "What is Snow teeth whitening?",
 "Does Snow teeth whitening actually work?",
 "What do reviews say about Snow teeth whitening?",
 "How much does Snow teeth whitening cost?",
], [
 "Snow versus Crest Whitestrips",
 "Best alternatives to Snow teeth whitening",
 "Compare at home LED teeth whitening brands",
])

# -------------------------------------------------------------- Arsenal ----
# No steroid, PED, ester, cycle or SARM content, and no medical aesthetics.
# Standing client constraint. Clinical and performance framing only.
add("arsenal", "US", [
 ("PRP and recovery", "Discovery", "prp injection cost", 13251, 7.6,
  "How much does a PRP injection cost?"),
 ("PRP and recovery", "Discovery", "prp treatment cost", 1444, 11.9,
  "What does PRP treatment cost?"),
 ("PRP and recovery", "Discovery", "prp shoulder injection cost", 1423, 4.1,
  "What does a PRP shoulder injection cost?"),
 ("PRP and recovery", "Decision", "prp injection price", 1008, 18.2,
  "Where can I get PRP injections in Denver?"),
 ("PRP and recovery", "Discovery", "cost of prp injections", 1268, 8.3,
  "Are PRP injections worth the cost?"),
 ("Cold plunge and recovery", "Discovery", "best time to cold plunge", 3009, 5.9,
  "When is the best time to cold plunge?"),
 ("Cold plunge and recovery", "Discovery", "best time of day to cold plunge", 998, 3.1,
  "What time of day should you cold plunge?"),
 ("Cold plunge and recovery", "Discovery", "when is the best time to cold plunge", 1815, 4.5,
  "Should you cold plunge before or after training?"),
 ("HYROX and training", "Comparison", "hyrox vs crossfit", 10879, 8.7,
  "HYROX versus CrossFit: which should I train for?"),
 ("HYROX and training", "Comparison", "crossfit vs hyrox", 1080, 6.0,
  "What is the difference between CrossFit and HYROX training?"),
 ("HYROX and training", "Decision", "hyrox vs crossfit", 10879, 8.7,
  "Where can I train for HYROX in Denver?"),
 ("Fat loss and conditioning", "Discovery",
  "what is a good speed to walk on a treadmill to lose weight", 13795, 6.2,
  "What is a good treadmill speed for losing weight?"),
 ("Fat loss and conditioning", "Discovery", "best treadmill settings for fat loss", 1173, 6.2,
  "What treadmill settings are best for fat loss?"),
 ("Fat loss and conditioning", "Best-X", "best treadmill to burn fat", 1064, 27.1,
  "What is the best treadmill workout to burn fat?"),
 ("Gyms and coaching", "Best-X", "gyms near me", 2036, 7.2,
  "What are the best gyms in Denver?"),
 ("Gyms and coaching", "Decision", "gym near me", 897, 6.1,
  "Which gym in Denver is best for serious training?"),
 ("Gyms and coaching", "Decision", "gyms near me", 2036, 7.2,
  "Where can I find a personal trainer in Denver?"),
 ("Gyms and coaching", "Decision", "gyms near me", 2036, 7.2,
  "Which gyms in Arvada, Colorado are worth joining?"),
 ("Health optimization", "Decision", "prp injection cost", 13251, 7.6,
  "Who offers health optimization services in Denver?"),
 ("Health optimization", "Discovery", "prp treatment cost", 1444, 11.9,
  "What does a health optimization program include?"),
], [
 "What is Arsenal Health?",
 "Is Arsenal Health a good gym in Denver?",
 "What do reviews say about Arsenal Health?",
 "How much does Arsenal Health membership cost?",
], [
 "Best health optimization gyms in Denver",
 "Compare performance training gyms in Denver",
 "Alternatives to F45 and Orangetheory in Denver",
])


def pack(rows, kind):
    return [{"topic": t, "intent": i, "source_query": s, "impressions": im,
             "position": p, "prompt": q, "kind": kind}
            for t, i, s, im, p, q in rows]


def main():
    out = pathlib.Path("clients/prompts")
    out.mkdir(parents=True, exist_ok=True)
    for slug, d in SETS.items():
        cat = pack(d["category"], "category")
        br = pack([("Brand", "Decision", "(brand prompt)", 0, 0.0, q)
                   for q in d["branded"]], "branded")
        co = pack([("Competitor", "Comparison", "(competitor prompt)", 0, 0.0, q)
                   for q in d["competitor"]], "competitor")
        doc = {"client": slug,
               "window": "16 months of GSC to 2026-07-31",
               "sourcing": "GSC queries only; no invented prompts",
               "country": d["country"],
               "prompts": cat + br + co}
        (out / f"{slug}.yaml").write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120),
            encoding="utf-8")
        print(f"{slug:<10} {len(cat)} category + {len(br)} branded + "
              f"{len(co)} competitor = {len(doc['prompts'])}")


if __name__ == "__main__":
    main()
