"""Author Cudio's 1.7 analysis file and fill the tab. Evidence standard as the
other seven: live-verified positions, parsed winners, PAA quoted, fixtures
labelled (odoo.com is the dominant fixture on this client's SERPs)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fill_1_7  # noqa: E402

NL = chr(10)
CU = "https://www.cudio.com"


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


P = json.loads(Path("Clients/Cudio/gap_analysis/2026-08-page-clicks.json"
                    ).read_text(encoding="utf-8"))


def find(tokens):
    best, bc = None, -1
    for u, v in P.items():
        if any(t in u.lower() for t in tokens) and v["clicks"] >= bc:
            best, bc = u, v["clicks"]
    return best, (P.get(best, {}).get("clicks", 0) if best else 0)


sup_page, sup_clk = find(["support"])
dev_page, dev_clk = find(["development", "custom"])
qb_page, qb_clk = find(["quickbooks"])
print("mapping:", {"support": sup_page, "dev": dev_page, "qb": qb_page})

clusters = [
 cl("OpenERP legacy migration",
    "openerp software (5,400); odoo open erp (3,600); openerp demo (1,300); "
    "openerp project (70)", 10370,
    CU + "/blog/what-is-odoo-software", 514, "Commercial (migration prospects)",
    "o2btechnologies.com",
    "https://www.o2btechnologies.com/blog/odoo/top-best-opensource-erp-system-o2b-technologies",
    brief("ADD AN OPENERP LEGACY SECTION TO OUR BIGGEST PAGE - these searchers "
          "are running decade-old installs.",
     "OpenERP is Odoo's pre-2014 name, so 10,370/mo of searches on it are "
     "users of LEGACY systems - the exact profile of a migration prospect. "
     "odoo.com #2 and Wikipedia #3 are fixtures; the comparable is O2B's "
     "1,125-word explainer at #5. Our /blog/what-is-odoo-software is the "
     "site's biggest asset (265,621 impressions, 514 clicks) and never "
     "mentions the old name. PAA: 'Is Odoo fully free?', 'What are the "
     "disadvantages of Odoo?', 'What are the top 3 ERP systems?'.",
     ["Add H2 'OpenERP is now Odoo: what changed and what it means for your "
      "install' to /blog/what-is-odoo-software - name history, version "
      "timeline, and why a system still called OpenERP is 10+ versions "
      "behind.",
      "Add H2 'Still running OpenERP? Your upgrade path' - a short honest "
      "migration outline (data, custom modules, downtime) linking "
      "/services/odoo-migration, which is the revenue page this cluster "
      "feeds.",
      "Answer 'Is Odoo fully free?' and 'disadvantages of Odoo' honestly on "
      "the same page - candour is the pattern that ranks in this niche and "
      "both are PAA on the legacy query.",
      "EDIT WITH CARE: 514 clicks. Add sections; change nothing that "
      "currently ranks."],
     note="Highest-leverage cluster on this client: legacy searchers are "
          "pre-qualified migration buyers, and the target page already "
          "dominates its SERP family.",
     target="#4-#6 under odoo.com and Wikipedia; O2B's explainer slot is "
            "the one to take."),
    "Cluster 10,370/mo. Live-verified: O2B #5, us absent on the legacy "
    "variants. Target page: 265,621 impressions / 514 clicks - edit with "
    "care."),

 cl("Odoo partnership",
    "odoo partnership (1,000); odoo partners (1,000); become odoo partner "
    "(50)", 2050,
    CU + "/", 0, "Commercial (buyer choosing a partner)",
    "o2btechnologies.com",
    "https://www.o2btechnologies.com/blog/odoo/what-does-an-odoo-partnership-mean",
    brief("SERVE THE CHOOSE-A-PARTNER INTENT - odoo.com owns the program "
          "pages, nobody owns the buyer guide.",
     "odoo.com holds #1-#2 (its partner program page and its partner "
     "DIRECTORY - both fixtures), Reddit #4. O2B ranks with a 'what a "
     "partnership means' explainer. The PAA reveals the buyer intent "
     "underneath: 'Who are Odoo partners in the USA?', 'How much does it "
     "cost to be an Odoo partner?', 'Is Odoo a legit company?'. Nobody "
     "ranking answers 'how do I CHOOSE an Odoo partner'.",
     ["Publish the buyer-side guide on an existing services/about page or "
      "as a blog post: 'How to choose an Odoo partner' - certification "
      "tiers explained (Ready/Silver/Gold and what they actually signify), "
      "questions to ask, red flags (offshore body-shops vs implementation "
      "specialists).",
      "State Cudio's own partner status explicitly with proof - VERIFY the "
      "current certification tier with the owner first; do not publish an "
      "unconfirmed tier.",
      "Answer 'Who are Odoo partners in the USA?' honestly - the landscape "
      "including competitors, which earns the trust that converts.",
      "Ensure Cudio's listing on odoo.com's partner directory is complete "
      "and current - that directory IS the #2 ranking page, so presence "
      "there is ranking by proxy (also a section B row)."],
     target="#3-#5 under odoo.com's two fixture slots."),
    "Cluster 2,050/mo. Live-verified: odoo.com #1-#2 (fixtures), O2B "
    "ranking the explainer. Partner-tier claim gated on owner verification."),

 cl("Odoo support services",
    "odoo support (590)", 590,
    sup_page or CU + "/", sup_clk, "Commercial (retainer intent)",
    "o2btechnologies.com",
    "https://www.o2btechnologies.com/blog/odoo/need-odoo-support",
    brief("DO NOT CHASE THE BARE QUERY - odoo.com owns it outright; target "
          "the third-party variant.",
     "odoo.com holds #1, #2 AND #3 on 'odoo support' - its own support/"
     "contact pages. That SERP is navigational to the vendor and "
     "unwinnable. The reachable demand is the qualified variants "
     "('odoo support services', 'odoo support partner', 'third-party odoo "
     "support') where O2B's 8-referring-domain post ranks.",
     ["Build/strengthen the support-services page around the QUALIFIED "
      "phrases - title and H1 say 'Odoo Support Services' not 'Odoo "
      "Support'.",
      "Structure: response times, what a support retainer covers (bugs, "
      "upgrades, hosting, custom module maintenance), Community vs "
      "Enterprise support differences.",
      "Answer 'when you need a partner instead of Odoo SA support' - the "
      "honest triage that positions third-party support without "
      "disparaging the vendor.",
      "Link from the migration and implementation pages - support is the "
      "retainer that follows both."],
     note="The volume figure (590) belongs mostly to the unwinnable "
          "navigational SERP - treat the reachable share as smaller and "
          "the retainer value per win as high.",
     target="Top 5 on the qualified variants; the bare query stays "
            "odoo.com's."),
    "Cluster 590/mo with an honest reachability caveat: odoo.com holds "
    "#1-#3 on the bare query."),

 cl("Odoo ERP development services",
    "odoo erp development services (320); odoo erp development (70); odoo "
    "erp software development (40)", 430,
    dev_page or CU + "/", dev_clk, "Commercial",
    "o2btechnologies.com",
    "https://www.o2btechnologies.com/blog/odoo/how-to-develop-erp-with-odoo",
    brief("MATCH THE SERVICES-PAGE FORMAT THE WINNER USES - case studies "
          "are the differentiator.",
     "Itransition ranks #5 with a 1,884-word services page structured as: "
     "services offered / success stories / customer quotes / why Odoo. "
     "Medium and a dev-shop blog hold other slots - a real services page "
     "with proof beats content posts here. PAA: 'What are Odoo ERP "
     "services?', 'Which is better, SAP or Odoo?', 'How much does Odoo "
     "cost per month?'.",
     ["Structure the development-services page to the observed winner "
      "shape: concrete service list (custom modules, integrations, "
      "migrations, studio work), then ONE real anonymised case study with "
      "numbers, then the cost PAA answered with ranges.",
      "Answer 'SAP or Odoo?' in one honest paragraph linking the "
      "comparison content that already earns clicks (/blog/erpnext-vs-odoo "
      "pattern, 79 clicks).",
      "Cross-link /blog/odoo-implementation-costs (94 clicks) - the "
      "cost-research reader is this page's buyer one step earlier."],
     target="#3-#5; the SERP's strongest page is 1,884 words with no moat."),
    "Cluster 430/mo. Live-verified: Itransition #5. Small volume, "
    "straight-line service intent."),

 cl("Open source QuickBooks alternative",
    "open source quickbooks alternative (210); open source quickbooks "
    "(110); open source alternatives to quickbooks (70); linux quickbooks "
    "alternative (40)", 430,
    qb_page or CU + "/blog/odoo-community-vs-enterprise", qb_clk,
    "Commercial (switcher intent)", "o2btechnologies.com",
    "https://www.o2btechnologies.com/blog/quickbooks/best/open-source-quickbooks-alternative",
    brief("WRITE THE HONEST ALTERNATIVES LISTICLE - the ranking pages are "
          "GitHub, Reddit and one competitor post.",
     "GitHub #2 and Reddit #3 are fixtures (raw lists and threads); O2B #4 "
     "ranks a 1,226-word '5 Best Open-Source QuickBooks Alternatives' "
     "listicle. The PAA is switcher anxiety: 'Is there a program like "
     "QuickBooks but free?', 'Why do CPAs not like QuickBooks Online?', "
     "'Is QuickBooks Desktop going away in 2026?' - that last one is a "
     "live migration trigger.",
     ["Publish the comparison honestly: Odoo Community, ERPNext, GnuCash, "
      "Akaunting - real trade-offs each, with Odoo's accounting scope "
      "stated plainly (what Community includes vs Enterprise).",
      "Open with 'Is QuickBooks Desktop going away?' - the 2026 sunset "
      "anxiety is the reason this SERP exists right now; answer it "
      "factually with dates.",
      "Answer the CPA objection ('why CPAs prefer QuickBooks') honestly - "
      "then when switching still makes sense.",
      "Close with the migration path and link /services/ - the switcher "
      "who chooses Odoo needs an implementer, which is the entire point."],
     target="#3-#4 beside the GitHub/Reddit fixtures; O2B's listicle is "
            "the slot."),
    "Cluster 430/mo. Live-verified: O2B #4. QuickBooks Desktop sunset "
    "makes this seasonal-urgent."),
]

backlinks = [
 {"target": "odoo.com partner directory",
  "comp_page": "odoo.com/partners - ranks #2 on the partnership queries "
               "(fixture we can be INSIDE)",
  "our_page": CU + "/",
  "quality_note": "The highest-value listing in this niche: the vendor's own "
   "partner directory is a top-2 ranking page on partner-selection queries, "
   "so a complete, current Cudio profile there is ranking by proxy. Verify "
   "tier, references and regions are current.", "routed": "Y"},
 {"target": "top10erp.org",
  "comp_page": "ranks median #3.5 on 4 of Cudio's scoped money SERPs (ERP "
               "selection roundups)",
  "our_page": CU + "/",
  "quality_note": "The principalcenter.com of this niche: a roundup "
   "publisher the buyers and the AI assistants both read. Ask: inclusion in "
   "its Odoo/open-source ERP listings and consultant directory.",
  "routed": "Y"},
 {"target": "erpfocus.com",
  "comp_page": "ranks on 4 scoped SERPs (manufacturing ERP comparisons)",
  "our_page": CU + "/blog/best-erp-software-for-manufacturing",
  "quality_note": "ERP-selection publisher with consultant visibility. Our "
   "manufacturing ERP post (99,937 impressions) is the natural citable "
   "asset to pitch.", "routed": "Y"},
 {"target": "mie-solutions.com roundup",
  "comp_page": "its '10 Best Manufacturing ERP' post ranks #2-#3 on scoped "
               "manufacturing queries",
  "our_page": CU + "/",
  "quality_note": "CAUTION: MIE is itself a manufacturing-software vendor "
   "publishing a roundup. Inclusion ask is possible but expect editorial "
   "conflict; lower priority than the two publishers above.",
  "routed": "N"},
 {"target": "O2B / Ksolves / Bista domain gaps (2,400+ domains combined)",
  "comp_page": "the bulk of all three competitors' referring domains",
  "our_page": "n/a",
  "quality_note": "DO NOT CHASE. Offshore-agency profiles built on "
   "directory spam and guest-post networks at volume (two hit the 1,000-"
   "domain API cap). Their rankings on Odoo terms come from topical "
   "content, not these links - replicating the junk buys risk only.",
  "routed": "N"},
]

doc = {
 "competitor_set":
  "O2B Technologies (o2btechnologies.com), Bista Solutions "
  "(bistasolutions.com), Ksolves (ksolves.com). Chosen from 12 live US "
  "SERPs 2026-08-18: the Odoo partners that actually rank on Cudio's scoped "
  "queries (3, 2 and 2 of 12). odoo.com itself is the dominant FIXTURE "
  "(owns partnership and support SERPs outright); publishers top10erp.org/"
  "erpfocus.com are section B targets, not competitors. RELEVANCE NOTE: "
  "Ksolves' biggest rankings (React, Java, AI) are off-business and were "
  "excluded from gap candidates. Snapshot: gap_analysis/2026-08-serps.json",
 "baseline_note":
  "Baseline month - no stored prior SERP set. Snapshot saved; September "
  "answers this cell by diff.",
 "clusters": clusters, "backlinks": backlinks}

reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
out = Path(reg["cudio"]["folder"]) / "gap_analysis" / "analysis.yaml"
out.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True,
                              width=100), encoding="utf-8")
print(f"cudio: analysis.yaml ({len(clusters)} clusters)")
fill_1_7.main("cudio")
