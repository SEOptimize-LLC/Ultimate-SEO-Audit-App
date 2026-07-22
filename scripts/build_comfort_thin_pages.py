"""Build Comfort Solutions thin pages expansion plan Excel file."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Comfort/Full SEO Audit/"
out = base + "comfort_thin_pages_expansion_plan.xlsx"

thin = pd.read_excel(base + "thin_pages.xlsx")


def classify(url):
    u = url.lower()
    if "/coupons/" in u:
        return "Coupon"
    if "/testimonials/" in u:
        return "Testimonial"
    if "/services-type/" in u:
        return "Archive (Services-Type)"
    if "/services/page/" in u:
        return "Archive (Pagination)"
    if "brocolli-button-test" in u:
        return "Test Page"
    if "homeshow" in u:
        return "Event/Promo"
    if "fireplace-utah" in u:
        return "Legacy Fireplace Subsite"
    if any(m in u for m in ["ascent", "altitude", "truflame"]):
        return "Product Page (Fireplace Model)"
    if "financing" in u:
        return "Financing"
    if u.endswith("/services/"):
        return "Services Hub"
    return "Other"


thin["Classification"] = thin["Address"].apply(classify)


# =========================================================================
# Per-URL recommendation map: action + rationale + writer brief
# =========================================================================
# Action types:
#   EXPAND = keep & write new content (SEO-relevant)
#   NOINDEX = keep live but remove from index
#   REDIRECT = 301 to relevant page
#   DELETE = remove entirely
#   CONSOLIDATE = merge into existing page
# =========================================================================

url_plans = {
    # TEST PAGE
    "/brocolli-button-test/": {
        "action": "DELETE",
        "action_rationale": "Live test page 100% duplicate of real service pages. Flagged in audit roadmap item #7. No SEO value, dilutes quality signals.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "N/A",
        "angle": "N/A — delete or 404",
        "must_have": "Remove from WordPress. Verify no internal links point to it. Let it 404 (no redirect needed).",
        "priority": "P0",
        "effort": "5 min",
    },
    # ARCHIVES (Services-Type) — WP auto-generated taxonomy archives
    "/services-type/fireplace/": {
        "action": "NOINDEX",
        "action_rationale": "WP auto-generated taxonomy archive. Thin content (192 words). Confuses with proper /services/ hub. 0 inlinks = already orphaned.",
        "primary_kw": "N/A (covered by /services/ + fireplace service pages)",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "N/A",
        "angle": "Add noindex meta tag. Keep URL for WP admin but remove from Google.",
        "must_have": "Set noindex,follow via Yoast/RankMath. Remove from XML sitemap. Do NOT delete — WP may break if taxonomy URL is removed.",
        "priority": "P1",
        "effort": "5 min",
    },
    "/services-type/24-7-emergency-furnace-services/": {
        "action": "NOINDEX",
        "action_rationale": "WP auto-generated taxonomy archive. 196 words, 0 inlinks. Duplicates /services/emergency-services/furnace-repair/ which has 1,698 words and 217 inlinks.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "N/A",
        "angle": "Noindex. Ensure all internal links point to the proper /services/emergency-services/furnace-repair/ page instead.",
        "must_have": "Noindex. Audit internal links — replace any pointing here with /services/emergency-services/furnace-repair/.",
        "priority": "P1",
        "effort": "10 min",
    },
    "/services-type/plumbing/": {
        "action": "NOINDEX",
        "action_rationale": "WP taxonomy archive. 210 words, 0 inlinks. Plumbing has dedicated service pages; this adds no unique value.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "N/A",
        "angle": "Noindex. Audit & redirect internal links if any exist.",
        "must_have": "Noindex,follow. Remove from sitemap.",
        "priority": "P1",
        "effort": "5 min",
    },
    "/services-type/hvac/": {
        "action": "NOINDEX",
        "action_rationale": "WP taxonomy archive. 222 words, 0 inlinks. HVAC has full /services/hvac-systems/ hierarchy; this archive is redundant.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "N/A",
        "angle": "Noindex. Route internal links to /services/hvac-systems/ if any exist.",
        "must_have": "Noindex,follow. Remove from sitemap.",
        "priority": "P1",
        "effort": "5 min",
    },
    # PAGINATION
    "/services/page/2/": {
        "action": "NOINDEX",
        "action_rationale": "Pagination URL. Should always be noindex. 206 words of navigation, 0 inlinks. Crawl budget waste if indexed.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "N/A",
        "angle": "Standard pagination handling — noindex via rel=prev/next or robots meta.",
        "must_have": "Apply noindex to all /services/page/N/ URLs. Verify /services/ hub has all services linked directly to avoid needing pagination.",
        "priority": "P1",
        "effort": "5 min",
    },
    # COUPONS — 9 pages, all thin, all near-duplicate structure
    "/coupons/5600-in-rebates/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon pages have conversion value but no SEO value. Thin by design. 3 inlinks from coupon hub + footer. Should live on-site but stay out of index.",
        "primary_kw": "N/A (conversion page, not ranking page)",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor in quote/checkout flow",
        "angle": "Keep on-site for conversion. Noindex all /coupons/* URLs.",
        "must_have": "Apply noindex to entire /coupons/ directory. Ensure coupon hub page links to each coupon. Verify expiry dates + disclaimers present.",
        "priority": "P1",
        "effort": "10 min (batch with other coupons)",
    },
    "/coupons/350-off-fireplace-installation/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon page — conversion tool, not ranking page. Noindex all coupons as a batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor",
        "angle": "Noindex. Keep on-site.",
        "must_have": "Noindex via /coupons/ directory rule. Add expiry + T&Cs.",
        "priority": "P1",
        "effort": "Batch with other coupons",
    },
    "/coupons/350-off-new-furnace/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon page. Noindex batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor",
        "angle": "Noindex.",
        "must_have": "Batch noindex.",
        "priority": "P1",
        "effort": "Batch",
    },
    "/coupons/pre-season-fireplace-tune-up-special/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon page. Seasonal — add start/end dates.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor in off-season",
        "angle": "Noindex. Add seasonal validity window.",
        "must_have": "Batch noindex + expiry date.",
        "priority": "P1",
        "effort": "Batch",
    },
    "/coupons/69-furnace-tune-up/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon page. Noindex batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor",
        "angle": "Noindex.",
        "must_have": "Batch noindex.",
        "priority": "P1",
        "effort": "Batch",
    },
    "/coupons/800-off-a-full-system/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon page. Noindex batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor",
        "angle": "Noindex.",
        "must_have": "Batch noindex.",
        "priority": "P1",
        "effort": "Batch",
    },
    "/coupons/59-off-any-fireplace-repair-or-upgrade/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon page. Noindex batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor",
        "angle": "Noindex.",
        "must_have": "Batch noindex.",
        "priority": "P1",
        "effort": "Batch",
    },
    "/coupons/59-off-any-ac-or-heating-repair-or-replacement/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon page. Noindex batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor",
        "angle": "Noindex.",
        "must_have": "Batch noindex.",
        "priority": "P1",
        "effort": "Batch",
    },
    "/coupons/free-smokeless-fire-pit-with-the-purchase-of-a-new-fireplace/": {
        "action": "NOINDEX",
        "action_rationale": "Coupon page. Noindex batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Existing site visitor",
        "angle": "Noindex.",
        "must_have": "Batch noindex.",
        "priority": "P1",
        "effort": "Batch",
    },
    # HOMESHOW
    "/homeshow/": {
        "action": "NOINDEX",
        "action_rationale": "Event/promo page. Temporal relevance only. No evergreen ranking potential. 217 words, 0 inlinks.",
        "primary_kw": "N/A (event, not evergreen)",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Utah homeowners attending Utah Home Show (seasonal)",
        "angle": "Noindex. Keep live during event season (Jan-Mar) for referrers.",
        "must_have": "Noindex,follow. Add next event date when known. Point CTA to quote form or showroom visit.",
        "priority": "P2",
        "effort": "10 min",
    },
    # LEGACY FIREPLACE SUBSITE — 5 pages (fireplace-utah suffix)
    "/build-your-fireplace-fireplace-utah/": {
        "action": "CONSOLIDATE",
        "action_rationale": "Legacy Fireplace Utah brand pages (pre-acquisition). 197 words, 1 inlink. Should be merged into main /services/fireplace-services/ pages — 'fireplace-utah' URL pattern is technical debt from merger.",
        "primary_kw": "custom fireplace design utah | build your fireplace",
        "secondary_kws": "fireplace installation design, fireplace showroom utah, custom fireplace consultation, fireplace builder, design your fireplace",
        "entities": "Napoleon, Valor, Regency, Mendota, Empire, gas fireplace, electric fireplace, wood burning, fireplace insert, fireplace surround, mantel, showroom, West Haven, Sandy, design consultation",
        "icp": "Utah homeowner (35-65) planning a new fireplace install or remodel. Often early in decision process — browsing showroom options. High commercial intent (fireplace installs = $5K-$25K).",
        "angle": "Merge into a proper /services/fireplaces/design-consultation/ page. Content: 'How to design a custom fireplace — Comfort Solutions' showroom walkthrough, brand catalog (Napoleon + others), design process, consultation booking.",
        "must_have": "1. Merge into /services/fireplaces/ subtree. 2. 301-redirect this URL to new destination. 3. New page: 1,200+ words covering brand options, design process, showroom visit CTA, financing mention. 4. Include Napoleon dealer authority signal prominently. 5. Link from homepage fireplace section.",
        "priority": "P2",
        "effort": "Medium — requires new page creation + redirect",
    },
    "/specials-fireplace-utah/": {
        "action": "REDIRECT",
        "action_rationale": "Legacy URL. 241 words. 1 inlink. Duplicates functionality of /coupons/ hub.",
        "primary_kw": "fireplace specials utah, fireplace deals",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "N/A — redirect to coupon hub",
        "angle": "301-redirect to /coupons/ hub page. No content needed.",
        "must_have": "301 → /coupons/. Verify WP redirect plugin is handling. Internal link sweep.",
        "priority": "P2",
        "effort": "5 min",
    },
    "/gallery-fireplace-utah/": {
        "action": "EXPAND",
        "action_rationale": "Visual content has SEO value for fireplace showroom queries. 244 words, 1 inlink. Needs expansion + reorganization, not deletion. Key differentiator: Comfort has TWO physical showrooms.",
        "primary_kw": "fireplace gallery utah",
        "secondary_kws": "fireplace showroom utah, fireplace installation photos, fireplace design ideas utah, ogden fireplace showroom, sandy fireplace showroom, napoleon fireplace gallery, custom fireplace photos",
        "entities": "Napoleon Ascent, Napoleon Altitude, TruFlame, gas fireplace photos, electric fireplace photos, stone surround, tile surround, mantel, linear fireplace, traditional fireplace, contemporary fireplace, West Haven showroom, Sandy showroom",
        "icp": "Utah homeowner (35-65) in discovery/design phase. Visual-first shopping — want to see real installations before booking a showroom visit. High commercial intent.",
        "angle": "Real project gallery — 'See 50+ Utah fireplace installations from Comfort Solutions.' Organize by style (traditional/contemporary/transitional), fuel type (gas/electric/wood), and location (living room/bedroom/outdoor). Each photo should have: brand, model, fuel type, install location, customer city.",
        "must_have": "1. Consider 301-redirect this URL to /services/fireplaces/gallery/ under proper hierarchy. 2. Expand to 800+ words of body copy. 3. Min 30 real project photos with captions. 4. Filter by style/fuel type. 5. 'Visit our showroom' CTA for both locations. 6. Schema: ImageGallery + LocalBusiness. 7. Link from homepage + fireplace service pages.",
        "priority": "P2",
        "effort": "High — photography + new page structure",
    },
    "/videos-fireplace-utah/": {
        "action": "EXPAND",
        "action_rationale": "Video content is high-value for fireplace queries + AI Overview citation. 262 words, 1 inlink. Legacy URL but can be restructured.",
        "primary_kw": "fireplace videos utah | fireplace installation video",
        "secondary_kws": "napoleon fireplace demo, fireplace how-to videos, fireplace maintenance video, fireplace installation timelapse, fireplace safety videos, youtube fireplace utah",
        "entities": "YouTube embed, Napoleon demo videos, fireplace walkthrough, showroom tour, installation process, maintenance tutorials, lighting pilot, changing logs, winter prep",
        "icp": "Utah homeowner in research phase — wants to see products in action. Also existing customers seeking maintenance/usage help.",
        "angle": "Move to /services/fireplaces/videos/ or /learning-center/fireplace-videos/. Combine branded Napoleon demos + original Comfort Solutions tutorials. Position as educational hub for fireplace owners + browsers.",
        "must_have": "1. Migrate under proper /services/ or /learning-center/ hierarchy with 301. 2. Min 8 embedded videos. 3. Each video: title + 100-word description + transcript. 4. Categories: product demos, installation process, maintenance how-to, safety, design inspiration. 5. Schema: VideoObject. 6. Transcripts boost word count + indexability.",
        "priority": "P2",
        "effort": "High — video production + schema setup",
    },
    "/reviews-fireplace-utah/": {
        "action": "REDIRECT",
        "action_rationale": "Legacy reviews page. 268 words, 0 inlinks. Testimonial/review content should live in one place — either /testimonials/ or a proper /reviews/ page with schema.",
        "primary_kw": "comfort solutions fireplace reviews",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "N/A — redirect",
        "angle": "301-redirect to /testimonials/ or a new consolidated /reviews/ page. Do NOT keep as-is.",
        "must_have": "301 → /testimonials/. Verify internal links. Ensure destination has Review schema with aggregate rating.",
        "priority": "P2",
        "effort": "5 min",
    },
    # TESTIMONIALS — 7 pages, all thin (individual testimonial pages)
    "/testimonials/marisa-brough/": {
        "action": "CONSOLIDATE",
        "action_rationale": "Individual testimonial pages add minimal SEO value alone but have brand/trust value. 232 words. Better consolidated into /testimonials/ hub with proper Review schema than kept as individual thin pages.",
        "primary_kw": "N/A (trust signal, not ranking page)",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Site visitor evaluating trust — mostly comes from service pages",
        "angle": "Option A (preferred): Consolidate all 7 individual testimonial pages into single /testimonials/ hub page with Review schema. 301-redirect individual URLs to hub. Option B: Noindex individual pages, keep for direct sharing, proper schema on hub.",
        "must_have": "If consolidating: 301 to hub. If keeping: noindex individual pages, add full Review schema with rating, date, reviewer name, service type. Hub page must have aggregateRating schema.",
        "priority": "P2",
        "effort": "Medium — schema setup + redirects",
    },
    "/testimonials/micheal-johnson/": {
        "action": "CONSOLIDATE",
        "action_rationale": "Batch with other testimonial pages. See /marisa-brough/ recommendation.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Site visitor",
        "angle": "Batch decision with all 7 testimonials.",
        "must_have": "Apply same rule as other testimonials. NOTE: 'Micheal' appears to be misspelled ('Michael'). Fix URL slug if page is kept.",
        "priority": "P2",
        "effort": "Batch",
    },
    "/testimonials/justin-richins/": {
        "action": "CONSOLIDATE",
        "action_rationale": "Batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Site visitor",
        "angle": "Batch.",
        "must_have": "Batch.",
        "priority": "P2",
        "effort": "Batch",
    },
    "/testimonials/john-jude-jj/": {
        "action": "CONSOLIDATE",
        "action_rationale": "Batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Site visitor",
        "angle": "Batch.",
        "must_have": "Batch.",
        "priority": "P2",
        "effort": "Batch",
    },
    "/testimonials/belinda-rounkles/": {
        "action": "CONSOLIDATE",
        "action_rationale": "Batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Site visitor",
        "angle": "Batch.",
        "must_have": "Batch.",
        "priority": "P2",
        "effort": "Batch",
    },
    "/testimonials/utahnna-rasmussen/": {
        "action": "CONSOLIDATE",
        "action_rationale": "Batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Site visitor",
        "angle": "Batch.",
        "must_have": "Batch.",
        "priority": "P2",
        "effort": "Batch",
    },
    "/testimonials/ross-przybylski/": {
        "action": "CONSOLIDATE",
        "action_rationale": "Batch.",
        "primary_kw": "N/A",
        "secondary_kws": "N/A",
        "entities": "N/A",
        "icp": "Site visitor",
        "angle": "Batch.",
        "must_have": "Batch.",
        "priority": "P2",
        "effort": "Batch",
    },
    # SERVICES HUB — needs expansion, not removal
    "/services/": {
        "action": "EXPAND",
        "action_rationale": "CRITICAL: This is the top-level services hub. 232 words is unacceptably thin for the hub page that should distribute equity to all service categories. Has 21 inlinks — it's important, just underdeveloped. Crawl depth 4.",
        "primary_kw": "hvac and fireplace services utah | home services sandy ogden",
        "secondary_kws": "heating cooling fireplace services utah, comfort solutions services, home comfort services utah, sandy ogden hvac services, west haven hvac, fireplace installation utah, plumbing services utah",
        "entities": "HVAC systems, residential heating, air conditioning, furnace repair, emergency services, fireplace design, fireplace installation, fireplace service, plumbing, water heater, drain cleaning, service areas (Sandy, Ogden, West Haven, Salt Lake City, West Valley City), Trane, Napoleon, Rinnai, Daikin, Goodman, Carrier, NATE-certified",
        "icp": "Utah homeowner (30-65) in initial research — unsure exactly which service they need OR returning visitor navigating to specific service. Both discovery + navigation use cases.",
        "angle": "True hub page — 3 cluster buckets (HVAC, Fireplaces, Plumbing) with category descriptions, featured services, and clear navigation to sub-pages. Position Comfort's three authority signals (Trane Comfort Specialist, Napoleon dealer, 25+ years) prominently.",
        "must_have": "1. Expand to 1,500+ words. 2. 3-cluster structure: HVAC Services / Fireplace Services / Plumbing Services. 3. Each cluster: icon, 150-word description, 4-6 featured service links. 4. Hero section with 3 authority signals. 5. Service area map. 6. Showroom locations (West Haven, Sandy) with CTAs. 7. Emergency contact banner. 8. FAQ schema (5-7 questions). 9. LocalBusiness schema. 10. Reduce crawl depth — link from main nav directly to /services/.",
        "priority": "P0",
        "effort": "High — content + design update",
    },
    # FIREPLACE PRODUCT PAGES — Napoleon models
    "/ascent-36/": {
        "action": "EXPAND",
        "action_rationale": "SEO-VALUABLE: Napoleon Ascent 36 is a specific fireplace model. Product pages for specific models can rank for branded/transactional queries ('napoleon ascent 36 utah', 'ascent 36 reviews'). 268 words is too thin to compete with Napoleon's own product page or distributor reviews.",
        "primary_kw": "napoleon ascent 36 utah | napoleon ascent 36 gas fireplace",
        "secondary_kws": "ascent 36 review, ascent 36 price utah, ascent 36 installation, ascent 36 specs, napoleon ascent gas fireplace, ascent 36 vs altitude, napoleon fireplace dealer utah",
        "entities": "Napoleon, Ascent series, 36-inch fireplace, direct vent, natural gas, propane, BTU rating, efficiency rating, ember bed, log set, safety screen, wall switch, remote control, heat circulation, venting, NFI certification, CSA certification, Energuide",
        "icp": "Utah homeowner (35-65) shopping for a mid-size gas fireplace. Already narrowed to Napoleon brand (likely from showroom visit or online research). Comparing Ascent 36 to other sizes/models. High commercial intent — $3K-$6K install.",
        "angle": "Authoritative dealer product page — 'Everything you need to know about the Napoleon Ascent 36 in Utah.' Beat Napoleon's own page by adding: local pricing, install lead time, Utah-specific considerations (elevation affects BTU output), real install photos, financing options.",
        "must_have": "1. Expand to 1,200+ words. 2. Hero image + 360 view if available. 3. Specs table (BTU, dimensions, venting, efficiency). 4. What's included vs. optional accessories. 5. Utah-specific notes (high-altitude derating, permit requirements). 6. Installation process + timeline. 7. Pricing range (transparent — 'starting at $X installed'). 8. Financing mention. 9. Compare to other Ascent models (30/35/36/42). 10. Showroom CTA — 'See the Ascent 36 in person at West Haven or Sandy.' 11. Product schema. 12. FAQ schema.",
        "priority": "P1",
        "effort": "Medium",
    },
    "/altitude-x-series/": {
        "action": "EXPAND",
        "action_rationale": "SEO-VALUABLE: Napoleon Altitude X is a premium direct-vent series. 283 words is thin. This is Comfort's premium fireplace offering — key differentiator for high-value leads.",
        "primary_kw": "napoleon altitude x series utah | altitude x fireplace",
        "secondary_kws": "altitude x42, altitude x36, altitude x series review, napoleon premium fireplace, direct vent gas fireplace, modern linear fireplace, altitude x price utah, altitude vs ascent",
        "entities": "Napoleon, Altitude X series, X36/X42 sizes, direct vent, NIGHT LIGHT bed, LED lighting, Hi-Def YELLOW FLAME, cabinet construction, modern linear, ember bed, glass media, MIRRO-FLAME panels, premium build quality, heat output, remote, thermostat, smart home compatibility",
        "icp": "Utah homeowner (40-70), higher income ($150K+), designing new construction or major remodel. Premium-conscious — value quality/aesthetics over price. Long decision cycle. $6K-$12K install.",
        "angle": "Premium product showcase — 'Napoleon Altitude X Series: The flagship direct-vent fireplace.' Emphasize design quality, flame aesthetics, Napoleon's premium craftsmanship. Position Comfort as the authorized Utah dealer.",
        "must_have": "1. Expand to 1,500+ words. 2. Hero video of active flame (sells the product). 3. Available sizes table (X36 vs X42). 4. Flame technology explanation (Hi-Def YELLOW, MIRRO-FLAME, NIGHT LIGHT). 5. Customization options (front finishes, glass media colors). 6. Utah considerations. 7. Lead time + installation process. 8. Premium pricing tier — 'starting at $X installed'. 9. Side-by-side with Ascent series. 10. Showroom CTA — 'See it lit up at our Sandy showroom.' 11. Financing options. 12. Product + FAQ schema.",
        "priority": "P1",
        "effort": "Medium",
    },
    "/ascent-multi-view/": {
        "action": "EXPAND",
        "action_rationale": "SEO-VALUABLE: Multi-view (see-through/peninsula/three-sided) fireplaces are a specialty niche with less competition. 286 words. Can rank well for specific queries with proper depth.",
        "primary_kw": "napoleon ascent multi-view utah | multi view gas fireplace",
        "secondary_kws": "see-through fireplace, peninsula fireplace, three sided fireplace, multi-sided gas fireplace, ascent multi-view review, open concept fireplace, room divider fireplace",
        "entities": "Napoleon Ascent Multi-View, see-through configuration, peninsula configuration, three-sided, four-sided island, open concept, room divider, venting complexity, dual-sided flame, glass enclosure, burner design, installation requirements, structural considerations, BTU rating, direct vent",
        "icp": "Utah homeowner (35-70), usually in new construction or major remodel. Open-concept floor plan. Architecturally conscious. Often works with a designer or architect. $8K-$18K install due to complexity.",
        "angle": "Specialty fireplace guide — 'Multi-view fireplaces: When they work, when they don't, and what they cost in Utah.' Address the unique structural + venting requirements. Position Comfort as the experienced installer for these complex projects.",
        "must_have": "1. Expand to 1,200+ words. 2. Configuration diagrams (see-through, peninsula, three-sided). 3. Best use cases (open concept, between kitchen/living, between bedroom/bath). 4. Structural/venting requirements — this is where Comfort's expertise matters. 5. Utah building code notes. 6. Pricing (range — complexity-dependent). 7. Project gallery of real Utah installs. 8. Design consultation CTA. 9. Compare to single-sided Ascent. 10. Product + FAQ schema.",
        "priority": "P1",
        "effort": "Medium",
    },
    "/truflame-direct-vent-luxury-fireplaces/": {
        "action": "EXPAND",
        "action_rationale": "SEO-VALUABLE: TruFlame is Napoleon's flagship luxury line. 296 words is at the threshold but still thin for a premium-product page. Less search volume but high commercial value per click.",
        "primary_kw": "napoleon truflame utah | truflame luxury fireplace",
        "secondary_kws": "truflame direct vent, luxury gas fireplace utah, high-end fireplace, napoleon luxury series, truflame review, custom fireplace utah, designer fireplace",
        "entities": "Napoleon TruFlame, direct vent, luxury tier, realistic flame pattern, premium materials, custom sizing, high BTU output, designer finishes, glass media options, decorative rocks, driftwood log sets, smart controls, zero-clearance, certification (CSA, P4)",
        "icp": "Utah homeowner (45-75), ultra-premium segment ($200K+ income). Custom home or luxury remodel. Often works with architect/interior designer. $10K-$25K+ install. Very long sales cycle.",
        "angle": "Luxury product showcase — 'TruFlame by Napoleon: Direct-vent luxury fireplaces in Utah.' Sophisticated positioning — less about specs, more about craftsmanship, design options, and the Comfort showroom experience.",
        "must_have": "1. Expand to 1,500+ words. 2. Professional photography — lifestyle + detail shots. 3. Available sizes + custom options. 4. Design consultation process (white-glove service). 5. Material + finish options (gallery). 6. Flame technology (how TruFlame differs from Ascent/Altitude). 7. 'For architects/designers' section with tech specs, CAD files mention. 8. Utah-specific: high-altitude tuning available. 9. Pricing positioning — 'custom quote based on configuration' (premium signaling). 10. Showroom demo CTA — both locations. 11. Financing (even premium buyers use it). 12. Product + FAQ schema.",
        "priority": "P1",
        "effort": "Medium-High",
    },
    # FINANCING
    "/financing-payment-options/": {
        "action": "EXPAND",
        "action_rationale": "SEO-VALUABLE: 'hvac financing utah' and 'fireplace financing utah' are commercial queries. 217 inlinks = crucial site-wide resource. 296 words + crawl depth 3 is a conversion accelerator. Expansion helps AI Overview citation + ranks well.",
        "primary_kw": "hvac financing utah | comfort solutions financing",
        "secondary_kws": "furnace financing utah, ac financing utah, fireplace financing utah, same-as-cash hvac, 0% apr heating cooling, hvac payment plan, affordable furnace replacement, monthly payment hvac",
        "entities": "financing partners (likely Synchrony, Service Finance, GreenSky — verify), promotional APR, same-as-cash offers, fixed APR, credit check, loan terms, monthly payment, approved credit, down payment, utility rebates, manufacturer rebates (Trane/Napoleon), Utah energy rebates, tax credits (IRA), application process",
        "icp": "Utah homeowner (30-60), mid-income ($60K-$120K), facing unexpected HVAC failure or planned upgrade. Price-sensitive but needs the work done. Very high conversion intent — financing is often the decision point.",
        "angle": "Complete financing guide — 'How to finance your HVAC or fireplace project in Utah.' Transparent: partners, terms, approval process, what credit scores qualify, current promotions, how to apply. Link to manufacturer + utility rebates.",
        "must_have": "1. Expand to 1,200+ words. 2. Financing partner logos + links (Synchrony, GreenSky, Service Finance — verify which). 3. Current promotional offers (same-as-cash, 0% APR windows). 4. Application process walkthrough. 5. 'What credit score qualifies?' (honest answer). 6. Combined with rebates section (manufacturer, utility, IRS tax credits). 7. Monthly payment calculator (embedded tool or example table). 8. FAQ schema. 9. Apply Now CTA. 10. Linked from every service page (should already be — verify).",
        "priority": "P0",
        "effort": "Medium",
    },
}


# =========================================================================
# BUILD WORKBOOK
# =========================================================================

wb = Workbook()
ws = wb.active
ws.title = "Thin Pages Expansion Plan"

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
title_font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
subtitle_font = Font(name="Calibri", size=10, italic=True, color="595959")
cell_font = Font(name="Calibri", size=10)
cell_font_small = Font(name="Calibri", size=9)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="top", wrap_text=True)
thin_border = Side(border_style="thin", color="BFBFBF")
border = Border(left=thin_border, right=thin_border, top=thin_border, bottom=thin_border)

red_fill = PatternFill("solid", fgColor="F8CBAD")
yellow_fill = PatternFill("solid", fgColor="FFF2CC")
green_fill = PatternFill("solid", fgColor="C6E0B4")
blue_fill = PatternFill("solid", fgColor="D9E1F2")
gray_fill = PatternFill("solid", fgColor="E7E6E6")
section_fill = PatternFill("solid", fgColor="DDEBF7")

ws["A1"] = "Comfort Solutions \u2014 Thin Pages Expansion Plan"
ws["A1"].font = title_font
ws.merge_cells("A1:R1")
ws["A2"] = "34 pages under 300 words (16% of indexable pages) | Classified by action: EXPAND (write content) / NOINDEX / REDIRECT / CONSOLIDATE / DELETE"
ws["A2"].font = subtitle_font
ws.merge_cells("A2:R2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

# Group headers
group_row = 3
ws.cell(row=group_row, column=1, value="PAGE DATA").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=1, end_row=group_row, end_column=7)
ws.cell(row=group_row, column=1).alignment = center
ws.cell(row=group_row, column=1).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=8, value="ACTION DECISION").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=8, end_row=group_row, end_column=9)
ws.cell(row=group_row, column=8).alignment = center
ws.cell(row=group_row, column=8).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=10, value="KEYWORD STRATEGY").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=10, end_row=group_row, end_column=12)
ws.cell(row=group_row, column=10).alignment = center
ws.cell(row=group_row, column=10).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=13, value="WRITER BRIEF").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=13, end_row=group_row, end_column=15)
ws.cell(row=group_row, column=13).alignment = center
ws.cell(row=group_row, column=13).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=16, value="EXECUTION").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=16, end_row=group_row, end_column=18)
ws.cell(row=group_row, column=16).alignment = center
ws.cell(row=group_row, column=16).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

for col in range(1, 19):
    c = ws.cell(row=group_row, column=col)
    if not c.fill.fgColor.rgb or c.fill.fgColor.rgb == "00000000":
        c.fill = section_fill
ws.row_dimensions[group_row].height = 20

headers = [
    # PAGE DATA (1-7)
    "#", "URL", "Title", "Word Count", "Inlinks", "Crawl Depth", "Classification",
    # ACTION (8-9)
    "Action", "Action Rationale",
    # KEYWORDS (10-12)
    "Primary Keyword", "Secondary Keywords", "Entities to Cover",
    # WRITER BRIEF (13-15)
    "ICP", "Content Angle", "Must-Have Sections",
    # EXECUTION (16-18)
    "Priority", "Effort", "Status",
]

for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 38

# Color palette per action
action_colors = {
    "EXPAND": PatternFill("solid", fgColor="C6E0B4"),       # green — SEO-relevant, write content
    "NOINDEX": PatternFill("solid", fgColor="FFF2CC"),      # yellow — keep but de-index
    "REDIRECT": PatternFill("solid", fgColor="BDD7EE"),     # light blue — 301
    "CONSOLIDATE": PatternFill("solid", fgColor="D9E1F2"),  # pale blue — merge
    "DELETE": PatternFill("solid", fgColor="F8CBAD"),       # red — remove
}
action_font_colors = {
    "EXPAND": "375623",
    "NOINDEX": "7F6000",
    "REDIRECT": "1F4E78",
    "CONSOLIDATE": "1F4E78",
    "DELETE": "9C0006",
}

# Sort: EXPAND (by priority) first, then others alphabetically by action, then by URL
def sort_key(row):
    key = row["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(key, {})
    action = plan.get("action", "OTHER")
    action_order = {"EXPAND": 0, "CONSOLIDATE": 1, "REDIRECT": 2, "NOINDEX": 3, "DELETE": 4}.get(action, 5)
    priority = plan.get("priority", "P3")
    return (action_order, priority, key)

thin["_sort_key"] = thin.apply(sort_key, axis=1)
thin = thin.sort_values("_sort_key").reset_index(drop=True)

for i, row in thin.iterrows():
    url_path = row["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(url_path, {})
    action = plan.get("action", "")
    r = i + 5
    values = [
        i + 1,
        row["Address"],
        row["Title 1"][:80] if pd.notna(row["Title 1"]) else "",
        int(row["Word Count"]) if pd.notna(row["Word Count"]) else "",
        int(row["Unique Inlinks"]) if pd.notna(row["Unique Inlinks"]) else 0,
        int(row["Crawl Depth"]) if pd.notna(row["Crawl Depth"]) else "N/A",
        row["Classification"],
        action,
        plan.get("action_rationale", ""),
        plan.get("primary_kw", ""),
        plan.get("secondary_kws", ""),
        plan.get("entities", ""),
        plan.get("icp", ""),
        plan.get("angle", ""),
        plan.get("must_have", ""),
        plan.get("priority", ""),
        plan.get("effort", ""),
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col >= 10 else cell_font
        c.border = border
        if col in (1, 4, 5, 6, 8, 16):
            c.alignment = center
        else:
            c.alignment = left
        # Action coloring
        if col == 8 and action in action_colors:
            c.fill = action_colors[action]
            c.font = Font(name="Calibri", size=10, bold=True, color=action_font_colors.get(action, "000000"))
        # Priority coloring
        if col == 16:
            if v == "P0":
                c.fill = red_fill
                c.font = Font(name="Calibri", size=10, bold=True, color="9C0006")
            elif v == "P1":
                c.fill = yellow_fill
            elif v == "P2":
                c.fill = green_fill
        # Thin word count flag
        if col == 4 and isinstance(v, int) and v < 200:
            c.fill = red_fill
        # Inlinks flag
        if col == 5 and isinstance(v, int) and v == 0:
            c.fill = red_fill

widths = {
    "A": 4, "B": 58, "C": 42, "D": 8, "E": 8, "F": 9, "G": 28,
    "H": 13, "I": 50,
    "J": 32, "K": 45, "L": 50,
    "M": 45, "N": 55, "O": 70,
    "P": 9, "Q": 22, "R": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for r in range(5, 5 + len(thin)):
    # Bigger rows for EXPAND (full brief), smaller for batch actions
    url_path = thin.iloc[r - 5]["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(url_path, {})
    if plan.get("action") == "EXPAND" or plan.get("action") == "CONSOLIDATE" and "Marisa" in thin.iloc[r - 5]["Address"]:
        ws.row_dimensions[r].height = 220
    elif plan.get("action") in ("EXPAND",):
        ws.row_dimensions[r].height = 220
    elif plan.get("action") in ("CONSOLIDATE", "REDIRECT"):
        ws.row_dimensions[r].height = 90
    else:
        ws.row_dimensions[r].height = 75

# Override for EXPAND rows — ensure enough space
for i, row in thin.iterrows():
    url_path = row["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(url_path, {})
    r = i + 5
    if plan.get("action") == "EXPAND":
        ws.row_dimensions[r].height = 240

ws.freeze_panes = "C5"

# =========================================================================
# SHEET 2 — Summary & Batch Action Plan
# =========================================================================
ws2 = wb.create_sheet("Summary & Batch Plan")
ws2["A1"] = "Thin Pages Recovery \u2014 Summary & Execution Plan"
ws2["A1"].font = title_font
ws2.merge_cells("A1:B1")

# Count by action
action_counts = {}
for i, row in thin.iterrows():
    url_path = row["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(url_path, {})
    action = plan.get("action", "OTHER")
    action_counts[action] = action_counts.get(action, 0) + 1

ctx = [
    ("", ""),
    ("=== OVERVIEW ===", ""),
    ("Total thin pages (<300 words)", "34"),
    ("% of indexable pages", "16% (highest across IHS properties)"),
    ("Source", "SF crawl \u2014 thin_pages.xlsx in Full SEO Audit folder"),
    ("Audit reference", "Technical/On-Page Audit \u2014 roadmap item #4 (P1)"),
    ("", ""),
    ("=== ACTION DISTRIBUTION ===", ""),
    (f"EXPAND (write new content)", f"{action_counts.get('EXPAND', 0)} pages \u2014 SEO-relevant, worth the effort"),
    (f"CONSOLIDATE (merge into hub)", f"{action_counts.get('CONSOLIDATE', 0)} pages \u2014 trust signals, belong on a single page with schema"),
    (f"REDIRECT (301)", f"{action_counts.get('REDIRECT', 0)} pages \u2014 legacy URLs, merge equity into proper page"),
    (f"NOINDEX (keep but de-index)", f"{action_counts.get('NOINDEX', 0)} pages \u2014 coupons/archives/pagination, conversion value only"),
    (f"DELETE (remove entirely)", f"{action_counts.get('DELETE', 0)} pages \u2014 test pages, no value"),
    ("", ""),
    ("=== SEO-RELEVANT PAGES TO EXPAND (6 pages) ===", ""),
    ("/services/ (Services Hub)", "P0 \u2014 232 words, 21 inlinks, critical hub. Expand to 1,500+ words with 3-cluster structure."),
    ("/financing-payment-options/", "P0 \u2014 296 words, 217 inlinks (site-wide). Conversion page + ranks for financing queries. Expand to 1,200+ words."),
    ("/ascent-36/", "P1 \u2014 Napoleon Ascent 36 product page. Expand to 1,200+ words with specs, pricing, install process."),
    ("/altitude-x-series/", "P1 \u2014 Napoleon Altitude X premium fireplace series. Expand to 1,500+ words, premium positioning."),
    ("/ascent-multi-view/", "P1 \u2014 Napoleon Ascent Multi-View (specialty). Expand to 1,200+ words, niche SEO opportunity."),
    ("/truflame-direct-vent-luxury-fireplaces/", "P1 \u2014 Napoleon TruFlame luxury line. Expand to 1,500+ words, luxury positioning."),
    ("", ""),
    ("=== BATCH ACTIONS (do these first \u2014 quick wins) ===", ""),
    ("Batch 1: Delete test page", "/brocolli-button-test/ \u2014 5 min. Just delete. No redirect needed."),
    ("Batch 2: Noindex coupons (9 pages)", "Apply noindex,follow to /coupons/* via Yoast/RankMath directory rule. ~10 min total."),
    ("Batch 3: Noindex services-type archives (4 pages)", "Apply noindex to WP taxonomy archives. 10 min."),
    ("Batch 4: Noindex pagination (/services/page/2/)", "5 min. Standard pagination rule."),
    ("Batch 5: Noindex homeshow", "5 min. Seasonal event page."),
    ("Batch 6: Consolidate testimonials (7 pages)", "Decision: consolidate into /testimonials/ hub with Review schema + 301 redirects, OR noindex individual pages + keep hub. Recommend consolidation."),
    ("Batch 7: Redirect legacy 'fireplace-utah' subsite (5 pages)", "Plan migration to proper /services/fireplaces/ hierarchy. Mix of redirects (/specials/, /reviews/) and expansion (/gallery/, /videos/, /build-your-fireplace/)."),
    ("", ""),
    ("=== CONTENT WRITING QUEUE (6 pages, priority order) ===", ""),
    ("Week 1: /services/", "P0 \u2014 Hub page. Highest leverage (21 direct inlinks, distributes equity)."),
    ("Week 1: /financing-payment-options/", "P0 \u2014 Conversion page. 217 inlinks site-wide. High commercial impact."),
    ("Week 2: /ascent-36/", "P1 \u2014 Most popular Napoleon model. Highest search volume of the 4 product pages."),
    ("Week 2: /altitude-x-series/", "P1 \u2014 Premium tier differentiator."),
    ("Week 3: /truflame-direct-vent-luxury-fireplaces/", "P1 \u2014 Luxury tier. Long sales cycle, high-value leads."),
    ("Week 3: /ascent-multi-view/", "P1 \u2014 Specialty niche. Low competition."),
    ("Week 4: /gallery-fireplace-utah/ migration", "P2 \u2014 Requires photography + new URL structure."),
    ("Week 4: /videos-fireplace-utah/ migration", "P2 \u2014 Requires video production or curation + transcripts."),
    ("", ""),
    ("=== KEY BRAND SIGNALS TO INCLUDE (all expanded pages) ===", ""),
    ("Trane Comfort Specialist", "Largest Trane Comfort Specialist in the Rocky Mountain Region \u2014 use on HVAC content"),
    ("Napoleon dealer", "Among nation's largest Napoleon fireplace suppliers \u2014 use on ALL fireplace content"),
    ("Two physical showrooms", "West Haven (Ogden) + Sandy \u2014 always include showroom CTA on product pages"),
    ("Founded 2000, 100+ employees", "25+ years in business, 100+ NATE-certified technicians \u2014 authority signal"),
    ("Multi-brand capability", "Trane, Napoleon, Rinnai, Daikin, Goodman, Carrier partnerships"),
    ("Acquired brands", "Lloyd's Heating and Air, Elite Fireplace, Robert Love Heating, Airworx HVAC \u2014 reach/consolidation story"),
    ("", ""),
    ("=== ICP \u2014 COMFORT SOLUTIONS IDEAL READER ===", ""),
    ("Geography", "Utah \u2014 Sandy, Ogden, West Haven, Salt Lake City, West Valley City and surrounding Wasatch Front"),
    ("Primary demographic", "Homeowners, 30-70, suburban single-family homes"),
    ("Fireplace buyer sub-segment", "Older (40-70), higher income ($120K+), remodel or new-build. Long decision cycle. Showroom-visit conversion."),
    ("HVAC emergency sub-segment", "All ages, immediate pain (furnace out in winter, AC out in summer). Fast conversion, financing common."),
    ("Plumbing sub-segment", "All ages, urgent or semi-urgent (water heater, drain, leak). Price-compare at first, convert on trust signals."),
    ("Decision triggers", "Transparency on price + process, financing availability, manufacturer authority (Trane/Napoleon), local trust (Utah-based, showroom-visible), speed (emergencies)"),
    ("", ""),
    ("=== WRITING STANDARDS ===", ""),
    ("Definition-first", "First sentence must directly answer the query. No modality ('one of the best', 'arguably')."),
    ("Utah local angle", "Every page needs Utah-specific content: high altitude, seasonal extremes, building codes, specific cities served."),
    ("Authority signals", "Mention Trane Comfort Specialist / Napoleon dealer status where relevant. These are genuine competitive moats."),
    ("Showroom CTA", "All product/fireplace pages: 'See it at our West Haven or Sandy showroom.'"),
    ("Title tags", "Max 60 chars. Include primary keyword + Utah geo modifier."),
    ("Meta descriptions", "Max 155 chars. Include primary benefit + CTA hint."),
    ("Schema", "Service + Product + FAQ + LocalBusiness where applicable. Review schema on testimonials hub."),
    ("Word count targets", "Hub pages: 1,500+ | Product pages: 1,200+ | Sub-service pages: 1,000+ | Landing pages: 800+"),
]

for r, (k, v) in enumerate(ctx, 2):
    c1 = ws2.cell(row=r, column=1, value=k)
    c2 = ws2.cell(row=r, column=2, value=v)
    if k and not v:
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    elif k.startswith("==="):
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    else:
        c1.font = Font(name="Calibri", size=10, bold=True)
        c2.font = cell_font
        c2.alignment = Alignment(wrap_text=True, vertical="top")

ws2.column_dimensions["A"].width = 50
ws2.column_dimensions["B"].width = 110

for r in range(2, 2 + len(ctx)):
    ws2.row_dimensions[r].height = 32

wb.save(out)
print(f"Saved: {out}")
