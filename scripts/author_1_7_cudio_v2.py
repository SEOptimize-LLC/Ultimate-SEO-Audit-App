"""Cudio 1.7 section A rebuild - service clusters first (owner correction 2026-08-18).

The first pass routed commercial clusters at blog posts and gave slots to
zero-click territory (partnership, support). This rebuild routes every cluster
at the live /services/ page for that line, demotes blogs to feeders, and parks
the rows that failed the click-viability gate, with reasons on the tab.

Evidence base (all collected 2026-08-19, on disk):
  gap_analysis/2026-08-serp-winners.json      - live top-10 + PAA + top-3 parses, 5 service queries
  gap_analysis/2026-08-serp-winners-v1.json   - v1 evidence (OpenERP cluster keeps it)
  gap_analysis/2026-08-service-evidence.json  - our 5 service pages parsed + volumes + GSC 2 windows
  gap_analysis/2026-08-page-clicks.json       - page-level May-Jul clicks
"""

import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GA = ROOT / "Clients/Cudio/gap_analysis"
sys.stdout.reconfigure(encoding="utf-8")

W = json.loads((GA / "2026-08-serp-winners.json").read_text(encoding="utf-8"))


def their(cluster: str, domain: str) -> str:
    """The ranking URL for a domain, read from the winners snapshot rather than
    retyped, so the tab cites exactly what was verified."""
    for r in W[cluster]["top10"]:
        if r["domain"] == domain:
            return r["url"]
    raise KeyError(f"{domain} not in winners top10 for {cluster}")


NL = "\n"


def brief(head, serp, dos, note=None, target=None):
    lines = [head, "", "WHAT THE LIVE SERP SHOWS: " + serp, "", "DO THIS:"]
    lines += [f"{i}. {d}" for i, d in enumerate(dos, 1)]
    if note:
        lines += ["", "NOTE: " + note]
    if target:
        lines += ["", "REALISTIC TARGET: " + target]
    return NL.join(lines)


def parked(head, why, reentry):
    return NL.join([
        "PARKED - NO BRIEF THIS MONTH. " + head, "",
        "WHY (kept for the record): " + why, "",
        "RE-ENTRY CONDITIONS: " + reentry])


clusters = [
    dict(
        cluster="Odoo migration services",
        keywords="odoo migration services (110); odoo migration service (90); odoo migration (70)",
        volume=270,
        clicks=26,
        intent="Commercial (core service line - strongest click evidence on the site)",
        competitor="webkul.com",
        their_url=their("Odoo migration services", "webkul.com"),
        our_page="https://www.cudio.com/services/odoo-migration",
        brief=brief(
            "DEFEND AND EXTEND THE FLAGSHIP SERVICE RANKING - this is the one service query already paying.",
            "webkul #2 (1,361 words; H2 structure: Types of Migration in Odoo / Parameters to Account for "
            "Before Migrating / Migration Process / FAQ - and its title leads with 'Odoo 19 Migration'); "
            "upgrade.odoo.com #3 is a FIXTURE (Odoo's own upgrade portal); GritXI #4 (1,139 words). O2B #8, "
            "OdooExpress #9. PAA: 'What is Odoo migration?', 'Which is better, SAP or Odoo?', 'Can Odoo "
            "replace QuickBooks?', 'What are the disadvantages of Odoo?'. GSC May-Jul: #5.9 average, 12 "
            "clicks, 2,501 impressions on the exact query - but the 2026-08-19 live pull does not show us "
            "in the visible top 10, so the position is volatile and this work is urgent, not optional. Our "
            "page: 2,886 words, 12 H2s, already carries process + risks + FAQ - deeper than every ranking page.",
            [
                "Version-currency pass: the winning titles name the current version. Add 'Odoo 19' and the "
                "supported upgrade paths (v12-v18 to 19) to the title and lead section - run the new title "
                "through the title rules before shipping.",
                "Add H2 'Types of Odoo migration' (version upgrade / platform migration / data migration) - "
                "webkul's ranking structure, and 'odoo data migration services' (472 impressions, #9.6) plus "
                "'odoo erp migration services' (404 impressions, #10.6) are live sub-queries the page can "
                "catch with one section each.",
                "Answer the PAA on-page: one short 'What is Odoo migration?' definition block up top; 'Can "
                "Odoo replace QuickBooks?' answered honestly with a link to /blog/quickbooks-to-odoo-migration "
                "(35 clicks) as the deep answer.",
                "Feeder pass: /blog/what-is-odoo-software (514 clicks - EDIT WITH CARE, add links only) and "
                "the QuickBooks migration post link here with 'Odoo migration services' anchors; today the "
                "blog earns the audience and the service page fights alone.",
            ],
            note="The whole migration family: 41 clicks / 7,880 impressions on the head query over 16 months. "
                 "This cluster is why the OpenERP row below exists - same revenue line, upstream audience.",
            target="Hold #4-#5 and push toward webkul's #2; upgrade.odoo.com keeps its fixture slot.",
        ),
        comments="Cluster 270/mo Ads volume, but GSC shows the real demand: 2,501 impressions May-Jul on the "
                 "head query alone. Live-verified 2026-08-19: webkul #2, us outside the visible top 10 against "
                 "a #5.9 May-Jul GSC average - volatile, defend now. Target page /services/odoo-migration: "
                 "26 clicks / 12,619 impressions May-Jul.",
    ),
    dict(
        cluster="OpenERP legacy migration",
        keywords="openerp software (5,400); odoo open erp (3,600); openerp demo (1,300); openerp project (70)",
        volume=10370,
        clicks=0,
        intent="Commercial (pre-qualified migration prospects on the legacy name)",
        competitor="o2btechnologies.com",
        their_url="https://www.o2btechnologies.com/blog/odoo/top-best-opensource-erp-system-o2b-technologies",
        our_page="NEW BUILD (owner sign-off): dedicated OpenERP-to-Odoo migration container under /services/ "
                 "- nearest existing page is /services/odoo-migration (26 clicks)",
        brief=brief(
            "BUILD THE DEDICATED OPENERP-TO-ODOO CONTAINER - the biggest demand pool in this table belongs "
            "to the migration line, not to a blog post.",
            "OpenERP is Odoo's pre-2014 name, so 10,370/mo of searches on it come from users of decade-old "
            "LEGACY installs - pre-qualified migration buyers. odoo.com #2 and Wikipedia #3 are fixtures; the "
            "comparable is O2B's 1,125-word explainer at #5 (v1 winners snapshot, on disk). PAA: 'Is Odoo "
            "fully free?', 'What are the disadvantages of Odoo?'. Google Ads shows 0 volume on 'openerp "
            "migration' - the legacy searcher searches the PRODUCT NAME, not the migration phrase, so the "
            "container must rank on the name terms with migration intent served on arrival.",
            [
                "NEW COMMERCIAL PAGE (allowed under the dedicated-page rule: the service exists, no page "
                "targets this audience). Proposed: /services/openerp-to-odoo-migration - OWNER SIGN-OFF "
                "REQUIRED on building it before any copy is written.",
                "Page structure from the observed SERP: 'OpenERP is now Odoo' name-history and version "
                "timeline (the explainer shape that ranks at #5), then 'Still running OpenERP? Your upgrade "
                "path' - data, custom modules, downtime, honestly stated - then the commercial close into "
                "the migration service.",
                "Answer 'Is Odoo fully free?' and the disadvantages PAA honestly - candour is the pattern "
                "that ranks in this niche.",
                "Feeder, not target: add a short 'OpenERP is now Odoo' H2 to /blog/what-is-odoo-software "
                "(514 clicks - EDIT WITH CARE, sections added, nothing that ranks changed) linking the new "
                "container. The blog keeps earning; the container converts.",
            ],
            note="Clicks column reads 0 because the container does not exist yet; the click evidence for the "
                 "territory is the migration cluster above (41 clicks 16-mo) plus the feeder blog's 514.",
            target="#4-#6 on the legacy name terms under odoo.com and Wikipedia; O2B's explainer slot is the "
                   "one to take.",
        ),
        comments="Highest-volume cluster (10,370/mo). Owner correction applied 2026-08-18: previously routed "
                 "at /blog/what-is-odoo-software (a TOFU explainer, not a commercial container). Rebuilt as a "
                 "NEW-BUILD row tied to the migration service line; blog demoted to feeder. New page requires "
                 "owner sign-off before build.",
    ),
    dict(
        cluster="Odoo implementation services",
        keywords="odoo implementation services (210); odoo implementation (170); odoo implementation partner "
                 "(170); odoo implementation company (70); odoo erp implementation (50)",
        volume=670,
        clicks=3,
        intent="Commercial (core service line)",
        competitor="gloriumtech.com",
        their_url=their("Odoo implementation services", "gloriumtech.com"),
        our_page="https://www.cudio.com/services/odoo-implementation",
        brief=brief(
            "PUT THE COST ANSWER ON THE SERVICE PAGE - every signal on this SERP is a cost signal.",
            "Glorium #2 (4,034 words) leads with 'Calculate the Costs. Plan Confidently' - an interactive "
            "cost estimator as the first H2; OdooExpress #3 ranks with only 820 words; odoo.com #4 is a "
            "FIXTURE (its own pricing page - Google reads this query as partly a cost query). O2B #5, "
            "Captivea #6, Reddit #8. First PAA: 'How much does it cost to implement Odoo?'. Our own "
            "/blog/odoo-implementation-costs already ranks #8.9 on 'odoo implementation cost' (1,596 "
            "impressions, 2 clicks May-Jul) - the cost asset exists but lives on the blog while the service "
            "page (3,092 words, process + pitfalls + FAQ + industries, but NO cost section in its 14 H2s) "
            "fights without it. GSC on the exact query: #16.6 May-Jul.",
            [
                "Add H2 'What Odoo implementation costs' to the service page: honest ranges by company size "
                "and scope, what moves the number - the summary version of the blog post, linking it for the "
                "deep dive. This is the single observable difference between our page and the #2 winner.",
                "Answer 'What services does Odoo offer?' (PAA) with a short module map linking the other "
                "/services/ pages - implementation is the entry service; the page should route.",
                "Feeder pass: /blog/odoo-implementation-costs (94 clicks) and /blogs/ideal-odoo-erp-"
                "implementation-partner (12 clicks) link here with 'Odoo implementation services' anchors.",
                "'odoo implementation partner' (170/mo, 3,099 impressions 16-mo at #26.9) belongs to this "
                "page too: one 'What to expect from an implementation partner' H2 covers it without a new page.",
            ],
            note="Page already carries success stories and a pitfalls section the 820-word #3 lacks - the "
                 "gap is the cost answer, not depth.",
            target="#5-#7 first (fixtures at #4 and #8 cap the field), then Glorium's tier once the cost "
                   "section matures.",
        ),
        comments="Cluster 670/mo. Live-verified 2026-08-19: Glorium #2, OdooExpress #3, us absent from the "
                 "visible top 10 (#16.6 GSC May-Jul on the head query). Target page: 3 clicks / 429 "
                 "impressions May-Jul - the cost blog feeder carries the family's clicks (94).",
    ),
    dict(
        cluster="Odoo integration services",
        keywords="odoo integration services (50); odoo integration (50); odoo shopify integration (50); "
                 "odoo stripe integration (30); shopify odoo integration (30)",
        volume=210,
        clicks=2,
        intent="Commercial (core service line)",
        competitor="odooexpress.com",
        their_url=their("Odoo integration services", "odooexpress.com"),
        our_page="https://www.cudio.com/services/odoo-integration",
        brief=brief(
            "ANSWER THE API QUESTIONS AND WIRE THE FEEDER - a 926-word page holds #2 on this SERP.",
            "OdooExpress #2 with only 926 words - a taxonomy page whose H2s name the integrations "
            "(Shopify, POS, payments, accounting, shipping, social); Itransition #4 (1,756 words), "
            "SilentInfotech #5 (1,373 words, opens with 'What is Odoo Integration?'). PAA: 'What are Odoo "
            "ERP integration services?', 'What does Odoo integrate with?', 'Does Odoo have API integration?', "
            "'Is Odoo API free?'. Our page (2,848 words, named-integration and process sections already "
            "present) sits #13.2 on the head query May-Jul, and our API integration guide "
            "(/odoo-api-integration-...) is the family's strongest asset: 85 clicks, 28,565 impressions, "
            "#9.5 on 'odoo api integration' (760 impressions May-Jul).",
            [
                "Add a compact 'Does Odoo have an API - and is it free?' H2 answering both API PAA questions "
                "in plain language, linking the API guide for depth. The guide already outranks the service "
                "page on API queries; today neither feeds the other.",
                "Open with a one-paragraph 'What are Odoo integration services?' definition - the "
                "SilentInfotech opening pattern, and the exact first PAA.",
                "Platform-name pass: the winning page's H2s NAME the platforms. Confirm ours names Shopify, "
                "Stripe, WooCommerce and QuickBooks explicitly - 'odoo shopify integration' (50/mo) and "
                "'odoo stripe integration' (30/mo) are live queries this page should catch with one named "
                "H3 each.",
                "Feeder pass: the API guide (85 clicks - EDIT WITH CARE, add links only) links here with "
                "'Odoo integration services' anchor; same for the WooCommerce payment-gateway content "
                "(1,989 impressions 16-mo, #10.6).",
            ],
            note="#13.2 with 2 clicks on the head query = just outside striking distance and closing; the "
                 "926-word incumbent shows the bar is answerability, not depth.",
            target="#4-#6 beside Itransition and SilentInfotech; OdooExpress's slot after the API sections land.",
        ),
        comments="Cluster 210/mo Ads volume; GSC family impressions tell the real story (3,654 on the head "
                 "query 16-mo, 2,598 on 'odoo api integration'). Live-verified 2026-08-19: OdooExpress #2 at "
                 "926 words, us absent from visible top 10. Target page: 2 clicks / 4,699 impressions May-Jul.",
    ),
    dict(
        cluster="Odoo development services",
        keywords="odoo erp development services (320); odoo development company (260); odoo development "
                 "services (140); odoo development (110); odoo erp development (70); odoo apps development (50)",
        volume=950,
        clicks=1,
        intent="Commercial (core service line)",
        competitor="gloriumtech.odoo.com",
        their_url=their("Odoo development services", "gloriumtech.odoo.com"),
        our_page="https://www.cudio.com/services/odoo-development",
        brief=brief(
            "MAKE THE DEVELOPMENT PAGE ANSWER WHO-AND-WHAT - the trust PAA is the whole SERP.",
            "Glorium #2 (2,279 words, official-partner framing in the first H2), Itransition #3 (1,884 "
            "words: services list / success stories / why-choose / FAQ), Medium #4 is a publisher FIXTURE, "
            "SDLC #5, O2B #6. The PAA is entirely trust and orientation: 'Is Odoo a legit company?', 'What "
            "does an Odoo developer do?', 'Who is behind Odoo?'. Our page (2,071 words, 14 H2s, process + "
            "FAQ + success-stories already present) sits #16.4 on 'odoo development services' (171 "
            "impressions May-Jul) and #7 16-mo on 'odoo erp development services' - this row absorbs the "
            "old ERP-development cluster, whose blog-targeted brief is superseded.",
            [
                "Add H2 'What does an Odoo developer actually do?' - the PAA answered with the concrete task "
                "list (custom modules, Studio work, API work, upgrades). No ranking page answers it; it is "
                "the cheapest differentiator on this SERP.",
                "Partner-status proof: Glorium's first H2 leads with official-partner framing. State Cudio's "
                "certification tier with proof - VERIFY the current tier with the owner first; do not publish "
                "unconfirmed (carried over from the v1 partnership row, where this gate already applied).",
                "Keyword-family pass: title/H1 currently say 'Odoo Development Services'; 'ERP' appears in "
                "the two biggest family terms (320 + 70/mo). Work 'ERP' into title or lead - run the result "
                "through the title rules.",
                "Template defect, fix while in there: two H2s are split heading fragments ('The Real Cost "
                "of' / 'Not Developing Custom Solutions') - one heading broken across two H2 tags. Merge "
                "into single elements; the same defect exists on the customization page.",
                "Feeder pass: /blogs/odoo-customization-vs-standard (124 clicks) and the API guide link "
                "here with 'Odoo development services' anchors.",
            ],
            note="'odoo erp development services' impressions collapsed May-Jul (1 impression vs 320/mo Ads "
                 "volume) - demand may be shifting to the bare phrase; the family view is the honest read.",
            target="#4-#6 beside Itransition; the Medium fixture caps one slot.",
        ),
        comments="Cluster 950/mo - largest Ads volume of the five service lines. Live-verified 2026-08-19: "
                 "Glorium #2, Itransition #3, us absent from visible top 10 (#16.4 May-Jul on the services "
                 "phrase). Absorbs the v1 'Odoo ERP development services' row (was blog-targeted; superseded). "
                 "Target page: 1 click / 811 impressions May-Jul.",
    ),
    dict(
        cluster="Odoo customization services",
        keywords="odoo customization services (90); odoo customization (70); odoo customization company (30); "
                 "odoo erp customization (20)",
        volume=210,
        clicks=1,
        intent="Commercial (core service line)",
        competitor="o2btechnologies.com",
        their_url=their("Odoo customization services", "o2btechnologies.com"),
        our_page="https://www.cudio.com/services/odoo-customization",
        brief=brief(
            "BRING THE THINNEST SERVICE PAGE UP TO THE PATTERN THE OTHER FOUR ALREADY FOLLOW - and fix the "
            "copy-paste defect while in there.",
            "O2B #2 (2,206 words; H2s: Odoo Modules We Customize / Configuration vs Studio vs Custom "
            "Development / Customization Process / Upgrade-Ready Customization), Itransition #3 (1,827 "
            "words with FAQ), odoo.com #4 FIXTURE. PAA: 'Can Odoo be customized?', 'What are the drawbacks "
            "of Odoo?'. Our page is the outlier of the five service pages: 1,397 words, 9 H2s, NO process "
            "section, NO FAQ - both of which our other four service pages carry - and one H2 reads 'Why "
            "Complex Businesses Choose Cudio for Odoo IMPLEMENTATION' on the CUSTOMIZATION page (copy-paste "
            "defect, verified in the 2026-08-19 parse). GSC: #19.8 on the services phrase, 1 click.",
            [
                "Fix the wrong-service H2 first ('...for Odoo Implementation' on the customization page) and "
                "merge the split heading fragments ('Is Your Tech Stack Powering Growth' / 'or Quietly "
                "Draining Margin?' - one heading across two H2 tags).",
                "Add H2 'Configuration vs Studio vs custom development' - O2B's winning differentiator "
                "section, and our /blogs/odoo-customization-vs-standard (124 clicks) is literally this "
                "topic: summarise on the service page, link the post for depth, and the post links back "
                "with 'Odoo customization services' anchor.",
                "Add H2 'Odoo modules we customize' naming the modules - the O2B taxonomy pattern.",
                "Add the process H2 and an FAQ block answering 'Can Odoo be customized?' and the drawbacks "
                "PAA honestly - matching what our own migration/implementation/integration/development "
                "pages already carry.",
            ],
            note="Weakest recent GSC of the five (#19.8, 1 click) and the thinnest page - last in priority "
                 "order, but the fix list is the most mechanical.",
            target="#4-#6 under the odoo.com fixture; O2B's #2 is the ceiling.",
        ),
        comments="Cluster 210/mo. Live-verified 2026-08-19: O2B #2 (2,206w), us absent from visible top 10. "
                 "Target page: 1 click / 592 impressions May-Jul, 1,397 words vs 2,206-word winner - the one "
                 "service page where depth genuinely is part of the gap.",
    ),
    dict(
        cluster="Odoo partnership - PARKED",
        keywords="odoo partnership (1,000); odoo partners (1,000); become odoo partner (50)",
        volume=2050,
        clicks=0,
        intent="Commercial (buyer choosing a partner)",
        competitor="o2btechnologies.com",
        their_url="https://www.o2btechnologies.com/blog/odoo/what-does-an-odoo-partnership-mean",
        our_page="None assigned - row parked, no refresh slot",
        brief=parked(
            "Owner correction 2026-08-18: zero clicks in this territory and no commercial container for it.",
            "odoo.com owns #1-#2 outright (its partner program page and partner directory - both fixtures), "
            "and Cudio has no page serving choose-a-partner intent, so this row failed both halves of the "
            "click-viability gate. The one action that survives is already in section B: Cudio's listing on "
            "odoo.com's partner directory IS the #2 ranking page - presence there is ranking by proxy.",
            "A partner-selection asset exists on a commercial page (or the owner asks for one as a new "
            "build) AND the partner-tier claim is verified with the owner. Until then the directory listing "
            "in section B carries this territory.",
        ),
        comments="PARKED per owner correction 2026-08-18: 0 clicks, fixture-owned SERP, no commercial "
                 "container. The odoo.com partner-directory action stays live in section B. Partner-tier "
                 "verification gate carried forward to the development row (Glorium precedent).",
    ),
    dict(
        cluster="Odoo support services - PARKED",
        keywords="odoo support (590)",
        volume=590,
        clicks=0,
        intent="Commercial (retainer intent)",
        competitor="o2btechnologies.com",
        their_url="https://www.o2btechnologies.com/blog/odoo/need-odoo-support",
        our_page="None assigned - row parked, no refresh slot",
        brief=parked(
            "Owner correction 2026-08-18: zero clicks, and the bare query is unwinnable.",
            "odoo.com holds #1, #2 AND #3 on 'odoo support' with its own support/contact pages - the SERP "
            "is navigational to the vendor. Our /odoo-support-services page: 0 clicks, 5 impressions "
            "May-Jul - no demand reaches it. The reachable share (qualified third-party variants) is small "
            "and unproven against the five service clusters above.",
            "Click or impression evidence appears on the qualified variants ('odoo support services', "
            "'third-party odoo support'), or support demand shows up in GSC after the five service pages "
            "ship their fixes. Retainer intent makes each win valuable - re-evaluate quarterly, not never.",
        ),
        comments="PARKED per owner correction 2026-08-18: 0 clicks, 5 impressions on our page; odoo.com "
                 "holds #1-#3 on the bare query (navigational fixture).",
    ),
    dict(
        cluster="Open source QuickBooks alternative - PARKED",
        keywords="open source quickbooks alternative (210); open source quickbooks (110); open source "
                 "alternatives to quickbooks (70); linux quickbooks alternative (40)",
        volume=430,
        clicks=40,
        intent="Commercial (switcher intent)",
        competitor="o2btechnologies.com",
        their_url="https://www.o2btechnologies.com/blog/quickbooks/best/open-source-quickbooks-alternative",
        our_page="https://www.cudio.com/blogs/odoo-vs-quickbooks (feeder - kept, not briefed)",
        brief=parked(
            "Deprioritized 2026-08-19 in favor of the five service clusters - not dead, parked.",
            "This cluster PASSES the click gate (40 clicks on /blogs/odoo-vs-quickbooks) and the SERP is "
            "genuinely winnable (O2B's listicle at #4, GitHub/Reddit fixtures above). But its winning format "
            "is comparison content - a feeder play, not a commercial container - and the owner's rule gives "
            "the month's slots to the main service lines. The v1 brief (honest alternatives listicle, "
            "QuickBooks Desktop 2026 sunset angle) is preserved in the v1 winners snapshot on disk.",
            "The five service-cluster briefs ship. Next selection round, this is the strongest waiting "
            "candidate - the Desktop-sunset urgency has a shelf life, so it should not park twice.",
        ),
        comments="PARKED (deprioritized, not failed): 40 clicks, live-verified winnable SERP, but it is a "
                 "blog/feeder play and the month's slots went to service containers per owner rule. "
                 "Strongest re-entry candidate next month; sunset-driven urgency noted.",
    ),
]

# Section B unchanged from v1 - the five targets were verified and routed already.
backlinks = [
    dict(
        target="odoo.com partner directory",
        comp_page="odoo.com/partners - ranks #2 on the partnership queries (fixture we can be INSIDE)",
        our_page="https://www.cudio.com/",
        quality_note="The highest-value listing in this niche: the vendor's own partner directory is a top-2 "
                     "ranking page on partner-selection queries, so a complete, current Cudio profile there "
                     "is ranking by proxy. Verify tier, references and regions are current.",
        routed="Y"),
    dict(
        target="top10erp.org",
        comp_page="ranks median #3.5 on 4 of Cudio's scoped money SERPs (ERP selection roundups)",
        our_page="https://www.cudio.com/",
        quality_note="The principalcenter.com of this niche: a roundup publisher the buyers and the AI "
                     "assistants both read. Ask: inclusion in its Odoo/open-source ERP listings and "
                     "consultant directory.",
        routed="Y"),
    dict(
        target="erpfocus.com",
        comp_page="ranks on 4 scoped SERPs (manufacturing ERP comparisons)",
        our_page="https://www.cudio.com/blog/best-erp-software-for-manufacturing",
        quality_note="ERP-selection publisher with consultant visibility. Our manufacturing ERP post (99,937 "
                     "impressions) is the natural citable asset to pitch.",
        routed="Y"),
    dict(
        target="mie-solutions.com roundup",
        comp_page="its '10 Best Manufacturing ERP' post ranks #2-#3 on scoped manufacturing queries",
        our_page="https://www.cudio.com/",
        quality_note="CAUTION: MIE is itself a manufacturing-software vendor publishing a roundup. Inclusion "
                     "ask is possible but expect editorial conflict; lower priority than the two publishers "
                     "above.",
        routed="N"),
    dict(
        target="O2B / Ksolves / Bista domain gaps (2,400+ domains combined)",
        comp_page="the bulk of all three competitors' referring domains",
        our_page="n/a",
        quality_note="DO NOT CHASE. Offshore-agency profiles built on directory spam and guest-post networks "
                     "at volume (two hit the 1,000-domain API cap). Their rankings on Odoo terms come from "
                     "topical content, not these links - replicating the junk buys risk only.",
        routed="N"),
]

data = dict(
    competitor_set=(
        "O2B Technologies (o2btechnologies.com), Bista Solutions (bistasolutions.com), Ksolves "
        "(ksolves.com). Chosen from 12 live US SERPs 2026-08-18: the Odoo partners that actually rank on "
        "Cudio's scoped queries (3, 2 and 2 of 12). odoo.com itself is the dominant FIXTURE. SERVICE-CLUSTER "
        "REBUILD NOTE 2026-08-19: the five service SERPs surfaced additional same-type Odoo service firms "
        "reverse-engineered per row - Webkul, GritXI, Glorium Tech, OdooExpress, Itransition, SilentInfotech; "
        "O2B remains the recurring named comparable (top 10 on all five service SERPs). Original approved set "
        "retained for section B and the September diff. Snapshots: gap_analysis/2026-08-serps.json + "
        "2026-08-serp-winners.json"),
    baseline_note=("Baseline month - no stored prior SERP set. Snapshot saved; September answers this cell "
                   "by diff. Section A rebuilt 2026-08-19 around the five /services/ lines per the owner's "
                   "commercial-routing correction; v1 rows preserved in analysis-v1.yaml + "
                   "2026-08-serp-winners-v1.json."),
    clusters=clusters,
    backlinks=backlinks,
)

if __name__ == "__main__":
    old = GA / "analysis.yaml"
    v1 = GA / "analysis-v1.yaml"
    if old.exists() and not v1.exists():
        shutil.copy(old, v1)
        print("backed up analysis.yaml -> analysis-v1.yaml")
    old.write_text(
        yaml.safe_dump(data, allow_unicode=True, width=95, sort_keys=False),
        encoding="utf-8")
    print(f"wrote {old}: {len(clusters)} clusters ({sum(1 for c in clusters if 'PARKED' in c['cluster'])} "
          f"parked), {len(backlinks)} backlink rows")
