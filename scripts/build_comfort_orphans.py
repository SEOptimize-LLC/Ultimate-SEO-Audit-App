"""Build Comfort Solutions orphan/underlinked pages action plan Excel file."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

base = r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor/Clients/Comfort/Full SEO Audit/"
out = base + "comfort_orphans_internal_linking_plan.xlsx"

df_raw = pd.read_excel(base + "underlinked_pages.xlsx")


# =========================================================================
# Filter: SEO-relevant pages only.
# Exclude: PPC, coupons, WP taxonomy archives, testimonials, financing,
# events/promo, test pages, Elementor templates, legal pages, legacy
# subsite hubs (handled separately in migration plan).
# =========================================================================
def is_seo_relevant(url):
    u = url.lower()
    excluded_patterns = [
        "/coupons/",                    # conversion pages, not ranking pages
        "/testimonials/",               # trust pages, not ranking pages
        "/services-type/",              # WP taxonomy archives (duplicates)
        "/services/page/",              # pagination
        "brocolli-button-test",         # test page
        "homeshow",                     # event/promo
        "-ppc-",                        # PPC landing pages
        "home-elementor",               # Elementor template
        "financing",                    # conversion page, not ranking page
        "/privacy",                     # legal
        "/terms",                       # legal
        "fireplace-utah-homepage",      # legacy subsite hub
        "reviews-fireplace-utah",       # legacy subsite (trust page)
        "specials-fireplace-utah",      # legacy subsite (coupons)
        "free-estimate-fireplace-utah",  # legacy subsite (conversion)
        "blog-fireplace-utah",          # legacy blog hub (not content)
    ]
    for pattern in excluded_patterns:
        if pattern in u:
            return False
    return True


df = df_raw[df_raw["Address"].apply(is_seo_relevant)].copy().reset_index(drop=True)
print(f"Filtered {len(df_raw)} URLs \u2192 {len(df)} SEO-relevant URLs")


# =========================================================================
# Per-URL action plan
# =========================================================================
# Actions:
#   LINK_FROM = add internal links from specified hub/service pages (keep page)
#   NOINDEX   = keep page but remove from index (coupon/archive/test pages)
#   REDIRECT  = 301 to canonical destination (legacy duplicates)
#   CONSOLIDATE = merge into canonical page
#   DELETE    = remove entirely
# =========================================================================

url_plans = {
    # ========================================================================
    # 0 INLINKS (8 pages) — highest priority
    # ========================================================================
    "/homeshow/": {
        "action": "NOINDEX",
        "classification": "Event/Promo",
        "link_from": "N/A \u2014 noindex (seasonal event, not evergreen)",
        "anchor_text_suggestions": "N/A",
        "rationale": "Seasonal event page. No evergreen ranking potential. Noindex,follow. Keep live during Jan-Mar event season for direct/paid traffic only.",
        "priority": "P2",
    },
    "/services-type/hvac/": {
        "action": "NOINDEX",
        "classification": "WP Taxonomy Archive",
        "link_from": "N/A \u2014 noindex (WP auto-generated archive duplicates /services/hvac-systems/)",
        "anchor_text_suggestions": "N/A",
        "rationale": "WP auto-generated taxonomy archive. 0 inlinks confirms it's already isolated. Noindex,follow \u2014 do NOT delete (WP may break). Remove from sitemap.",
        "priority": "P1",
    },
    "/reviews-fireplace-utah/": {
        "action": "REDIRECT",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "N/A \u2014 301 redirect",
        "anchor_text_suggestions": "N/A",
        "rationale": "Legacy URL from pre-acquisition Fireplace Utah brand. 301-redirect to /testimonials/ hub (or new /reviews/ page with proper Review schema).",
        "priority": "P2",
    },
    "/services-type/plumbing/": {
        "action": "NOINDEX",
        "classification": "WP Taxonomy Archive",
        "link_from": "N/A \u2014 noindex",
        "anchor_text_suggestions": "N/A",
        "rationale": "WP taxonomy archive. Thin. Noindex,follow. Remove from sitemap.",
        "priority": "P1",
    },
    "/services-type/fireplace/": {
        "action": "NOINDEX",
        "classification": "WP Taxonomy Archive",
        "link_from": "N/A \u2014 noindex",
        "anchor_text_suggestions": "N/A",
        "rationale": "WP taxonomy archive. Noindex,follow. Remove from sitemap.",
        "priority": "P1",
    },
    "/services-type/24-7-emergency-furnace-services/": {
        "action": "NOINDEX",
        "classification": "WP Taxonomy Archive",
        "link_from": "N/A \u2014 noindex",
        "anchor_text_suggestions": "N/A",
        "rationale": "WP taxonomy archive. Duplicates /services/emergency-services/furnace-repair/. Noindex,follow.",
        "priority": "P1",
    },
    "/coupons/": {
        "action": "LINK_FROM",
        "classification": "Coupon Hub",
        "link_from": "Homepage footer | Main nav 'Specials' link | Every service page 'Save on this service' CTA | Blog posts (contextual)",
        "anchor_text_suggestions": "Current specials | HVAC coupons | Fireplace specials | Save on HVAC service",
        "rationale": "IMPORTANT hub \u2014 links to all individual coupon pages for site-wide conversion. Must be linked from homepage/nav. 303 words is fine for a hub (acts as an index). NOTE: Individual /coupons/* pages should be noindex, but the hub should be indexable.",
        "priority": "P0",
    },
    "/testimonials/": {
        "action": "LINK_FROM",
        "classification": "Testimonials Hub",
        "link_from": "Homepage (scroll section or footer) | Every service page (trust signal) | About page | Contact page",
        "anchor_text_suggestions": "See customer reviews | Read testimonials | What Utah homeowners say | Our reviews",
        "rationale": "IMPORTANT trust-signal hub. 564 words is reasonable but needs schema: aggregateRating + individual Review items. Link widely from service pages \u2014 this is a conversion accelerator.",
        "priority": "P0",
    },

    # ========================================================================
    # 1 INLINK (44 pages)
    # ========================================================================
    "/blog-fireplace-utah/": {
        "action": "REDIRECT",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "N/A \u2014 301 to /blog/",
        "anchor_text_suggestions": "N/A",
        "rationale": "Legacy blog URL. 301 to /blog/ (main blog). Fixing blog/category duplication is on the roadmap \u2014 handle together.",
        "priority": "P2",
    },
    "/furnace-tune-up-park-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/services/emergency-services/furnace-repair/ | /service-areas/park-city/ | /services/hvac-systems/heating/ | Footer city links | Related Park City pages (cross-link all PC services)",
        "anchor_text_suggestions": "Furnace tune-up in Park City | Park City furnace maintenance | Schedule Park City furnace tune-up",
        "rationale": "2,233 words of substantial content starved of equity. Classic PPC/local-SEO page built but never linked into the site graph. Critical to link from service area hub + parent service page.",
        "priority": "P0",
    },
    "/contemporary-fireplaces/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Category Page",
        "link_from": "/services/ hub | Napoleon product pages (ascent, altitude, truflame) | Fireplace style section if exists | /fireplace-services/ parent | Homepage fireplace module",
        "anchor_text_suggestions": "Contemporary fireplaces | Modern fireplace styles | Linear contemporary fireplaces",
        "rationale": "Style-category page \u2014 key navigation between product catalog and design preferences. Link from every Napoleon product page (each product is a contemporary/traditional option).",
        "priority": "P1",
    },
    "/custom-fireplaces/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Category Page",
        "link_from": "/services/ hub | /gallery-fireplace-utah/ | All Napoleon product pages | Homepage fireplace section | /build-your-fireplace-fireplace-utah/",
        "anchor_text_suggestions": "Custom fireplaces | Design your fireplace | Custom fireplace installation Utah",
        "rationale": "Custom fireplaces = high-value lead magnet. Showroom visit trigger. Must link from gallery, product pages, and homepage fireplace section.",
        "priority": "P1",
    },
    "/furnace-maintenance-park-city-utah/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/service-areas/park-city/ | /furnace-tune-up-park-city/ | /services/hvac-systems/heating/ | Other Park City pages",
        "anchor_text_suggestions": "Furnace maintenance Park City | Park City HVAC maintenance | Annual furnace service Park City",
        "rationale": "1,822 words of quality content orphaned. Critical to link from Park City service area hub + cross-link with other Park City service pages.",
        "priority": "P0",
    },
    "/gas-fireplace-repair-services-in-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace)",
        "link_from": "/services/ hub fireplace cluster | /service-areas/salt-lake-city/ | /fireplace-repair-service/ parent | Other SLC fireplace pages",
        "anchor_text_suggestions": "Gas fireplace repair Salt Lake City | SLC gas fireplace service | Fireplace repair in Salt Lake City",
        "rationale": "1,623-word quality city-service page. Link from SLC service area + fireplace-repair parent.",
        "priority": "P0",
    },
    "/furnace-replacement-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/services/emergency-services/furnace-repair/ | /service-areas/salt-lake-city/ | Financing page (replacement = financing lead) | Related SLC pages",
        "anchor_text_suggestions": "Furnace replacement Salt Lake City | SLC furnace installation | Replace your furnace in SLC",
        "rationale": "1,871-word commercial page. Replacement = high-ticket lead. Link prominently from SLC service area + financing page (replacements often financed).",
        "priority": "P0",
    },
    "/fireplace-utah-homepage/": {
        "action": "REDIRECT",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "N/A \u2014 301 to main homepage or /services/ fireplace hub",
        "anchor_text_suggestions": "N/A",
        "rationale": "Legacy Fireplace Utah brand homepage. 301 to main homepage or /services/fireplaces/. No need for two homepages.",
        "priority": "P2",
    },
    "/fireplace-service-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace)",
        "link_from": "/fireplace-repair-service/ parent | /service-areas/salt-lake-city/ | Related SLC pages (fireplace-repair-slc, gas-fireplace-repair-slc)",
        "anchor_text_suggestions": "Fireplace service Salt Lake City | SLC fireplace maintenance | Fireplace service in SLC",
        "rationale": "1,473-word city-service page. Cluster together with other SLC fireplace pages for topical authority.",
        "priority": "P0",
    },
    "/gas-fireplace-inserts-in-south-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace Insert)",
        "link_from": "/gas-wood-inserts/ parent | /service-areas/south-salt-lake-city/ or /service-areas/salt-lake-city/ | /fireplace-repair-service/ | Other fireplace insert pages",
        "anchor_text_suggestions": "Gas fireplace inserts South Salt Lake | Fireplace inserts in SSL | Gas insert installation South SLC",
        "rationale": "1,748-word niche city+product combo. Link from gas/wood inserts hub + service area.",
        "priority": "P0",
    },
    "/videos-fireplace-utah/": {
        "action": "CONSOLIDATE",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "If kept: link from homepage + all fireplace pages. If migrated: 301 old URL + link new location widely.",
        "anchor_text_suggestions": "Fireplace videos | See fireplace demos | Video gallery",
        "rationale": "Covered in thin_pages plan \u2014 migrate to /learning-center/fireplace-videos/ or /services/fireplaces/videos/. After migration, link from all fireplace pages.",
        "priority": "P2",
    },
    "/build-your-fireplace-fireplace-utah/": {
        "action": "CONSOLIDATE",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "After migration to /services/fireplaces/design-consultation/: link from homepage fireplace section + all Napoleon product pages + showroom pages",
        "anchor_text_suggestions": "Design your fireplace | Custom fireplace consultation | Start your fireplace project",
        "rationale": "Covered in thin_pages plan \u2014 migrate to proper /services/fireplaces/ hierarchy and expand content. Post-migration, link widely as the fireplace conversion entry point.",
        "priority": "P2",
    },
    "/specials-fireplace-utah/": {
        "action": "REDIRECT",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "N/A \u2014 301 to /coupons/",
        "anchor_text_suggestions": "N/A",
        "rationale": "Legacy URL. Duplicates /coupons/ functionality. 301-redirect.",
        "priority": "P2",
    },
    "/gas-furnaces-services-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/services/emergency-services/furnace-repair/ | /service-areas/salt-lake-city/ | Other SLC furnace pages",
        "anchor_text_suggestions": "Gas furnace services Salt Lake City | SLC gas furnace installation | Gas furnace repair & install SLC",
        "rationale": "2,361-word substantial commercial page starved of inlinks.",
        "priority": "P0",
    },
    "/furnace-installation-services-in-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/services/emergency-services/furnace-repair/ | /service-areas/salt-lake-city/ | /furnace-replacement-salt-lake-city/ (related) | Financing page",
        "anchor_text_suggestions": "Furnace installation Salt Lake City | SLC furnace installation services | New furnace installation SLC",
        "rationale": "1,681-word installation-focused page. Cross-link with replacement pages + financing.",
        "priority": "P0",
    },
    "/furnace-tune-up-salt-lake-city/": {
        "action": "CONSOLIDATE",
        "classification": "Duplicate City Service Page",
        "link_from": "DUPLICATE of /furnace-tune-up-services-salt-lake-city/ (2,138 vs 2,143 words \u2014 near-identical). Consolidate: pick canonical, 301 the other.",
        "anchor_text_suggestions": "Furnace tune-up Salt Lake City",
        "rationale": "DUPLICATE with /furnace-tune-up-services-salt-lake-city/. Near-identical word counts suggest same content with slight URL variation. Consolidate to one canonical URL, 301 the duplicate.",
        "priority": "P0",
    },
    "/furnace-tune-up-services-salt-lake-city/": {
        "action": "CONSOLIDATE",
        "classification": "Duplicate City Service Page",
        "link_from": "See above \u2014 duplicate of /furnace-tune-up-salt-lake-city/",
        "anchor_text_suggestions": "See canonical",
        "rationale": "DUPLICATE. Consolidate with /furnace-tune-up-salt-lake-city/.",
        "priority": "P0",
    },
    "/air-conditioning-ppc-001/": {
        "action": "NOINDEX",
        "classification": "PPC Landing Page",
        "link_from": "N/A \u2014 PPC pages should NOT be in organic sitemap or index",
        "anchor_text_suggestions": "N/A",
        "rationale": "PPC landing page (URL slug '-ppc-001'). Should never have been indexed. Noindex,follow. Remove from XML sitemap. Keep URL for paid traffic only.",
        "priority": "P1",
    },
    "/furnace-cleaning-park-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/service-areas/park-city/ | /furnace-tune-up-park-city/ | /furnace-maintenance-park-city-utah/ | Cluster all Park City furnace pages",
        "anchor_text_suggestions": "Furnace cleaning Park City | Park City furnace cleaning service",
        "rationale": "1,773-word page. Cluster all PC furnace pages (cleaning + tune-up + maintenance + replacement) with reciprocal links.",
        "priority": "P0",
    },
    "/furnace-replacement-park-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/service-areas/park-city/ | Related PC furnace pages | Financing page",
        "anchor_text_suggestions": "Furnace replacement Park City | Replace your furnace in Park City | New furnace Park City",
        "rationale": "2,011-word high-ticket commercial page. Link from PC service area + financing (replacements often financed).",
        "priority": "P0",
    },
    "/furnace-repair-services-in-orem/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/services/emergency-services/furnace-repair/ | /service-areas/orem/ if exists \u2014 else consider creating | Nearby city pages (Provo, Lehi if exists)",
        "anchor_text_suggestions": "Furnace repair Orem | Orem furnace repair service | Emergency furnace repair Orem",
        "rationale": "1,697-word page for Orem market. Check if /service-areas/orem/ exists; if not, create or route from parent furnace repair page.",
        "priority": "P0",
    },
    "/gas-fireplace-inserts-sandy/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace Insert)",
        "link_from": "/gas-wood-inserts/ parent | /service-areas/sandy/ | /electric-fireplace-services-in-sandy/ (related) | Sandy showroom page",
        "anchor_text_suggestions": "Gas fireplace inserts Sandy | Sandy fireplace inserts | Fireplace insert installation Sandy",
        "rationale": "1,698-word city+product page. Cluster Sandy-based fireplace pages together, link from Sandy showroom location page.",
        "priority": "P0",
    },
    "/heating-ppc-001/": {
        "action": "NOINDEX",
        "classification": "PPC Landing Page",
        "link_from": "N/A \u2014 PPC page",
        "anchor_text_suggestions": "N/A",
        "rationale": "PPC landing page. Noindex,follow. Remove from sitemap.",
        "priority": "P1",
    },
    "/electric-fireplace-services-in-sandy/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace)",
        "link_from": "/electric-fireplaces/ parent | /service-areas/sandy/ | /gas-fireplace-inserts-sandy/ (related) | Sandy showroom",
        "anchor_text_suggestions": "Electric fireplace Sandy | Sandy electric fireplace services | Electric fireplace installation Sandy",
        "rationale": "1,830-word city+product page. Cluster Sandy pages.",
        "priority": "P0",
    },
    "/home-elementor/": {
        "action": "DELETE",
        "classification": "Elementor Test/Template Page",
        "link_from": "N/A \u2014 delete",
        "anchor_text_suggestions": "N/A",
        "rationale": "Elementor page builder template/preview URL. Not a real page. Delete or at minimum noindex + remove from sitemap. Check it's not accidentally serving as homepage alternative.",
        "priority": "P1",
    },
    "/furnace-repair-services-in-ogden/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/services/emergency-services/furnace-repair/ | /service-areas/ogden/ or /service-areas/west-haven/ | West Haven showroom page | Other Ogden pages",
        "anchor_text_suggestions": "Furnace repair Ogden | Ogden furnace repair | Emergency furnace repair in Ogden",
        "rationale": "2,040-word substantial page. Ogden/West Haven is HQ \u2014 should be heavily linked from showroom page.",
        "priority": "P0",
    },
    "/furnace-installation-park-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/service-areas/park-city/ | /furnace-replacement-park-city/ (near-duplicate intent) | Financing",
        "anchor_text_suggestions": "Furnace installation Park City | PC furnace installation | New furnace install Park City",
        "rationale": "1,688-word page. Cluster with PC furnace pages. Note potential overlap with /furnace-replacement-park-city/ \u2014 review if consolidation needed.",
        "priority": "P0",
    },
    "/gas-log-sets/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Category",
        "link_from": "/services/ hub | Napoleon product pages | /gas-wood-inserts/ | /gas-wood-stoves/ | Fireplace category pages",
        "anchor_text_suggestions": "Gas log sets | Gas fireplace logs | Decorative gas logs",
        "rationale": "Product category page (499 words \u2014 borderline thin). Link from all gas fireplace product pages. Consider expanding content.",
        "priority": "P1",
    },
    "/outdoor-fireplace-contractor-in-sandy/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Outdoor Fireplace)",
        "link_from": "/outdoor-heating/ parent | /service-areas/sandy/ | Other Sandy fireplace pages | Homepage outdoor section",
        "anchor_text_suggestions": "Outdoor fireplace Sandy | Sandy outdoor fireplace installation | Outdoor fireplace contractor in Sandy",
        "rationale": "1,814-word specialty page. Outdoor fireplaces are a differentiator. Link from /outdoor-heating/ + Sandy service area.",
        "priority": "P1",
    },
    "/furnace-replacement-services-ogden/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/service-areas/ogden/ | West Haven showroom | /furnace-repair-services-in-ogden/ | Financing",
        "anchor_text_suggestions": "Furnace replacement Ogden | Ogden furnace installation | Replace furnace Ogden",
        "rationale": "1,836-word page. Cluster Ogden pages \u2014 HQ market.",
        "priority": "P0",
    },
    "/gallery-fireplace-utah/": {
        "action": "CONSOLIDATE",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "Post-migration to /services/fireplaces/gallery/: link from homepage + all fireplace product pages + showroom pages",
        "anchor_text_suggestions": "Fireplace gallery | See installation photos | Project gallery",
        "rationale": "Covered in thin_pages plan \u2014 migrate URL + expand. Post-migration, link widely.",
        "priority": "P2",
    },
    "/fireplace-repair-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace)",
        "link_from": "/fireplace-repair-service/ parent | /service-areas/salt-lake-city/ | /gas-fireplace-repair-services-in-salt-lake-city/ (related) | Cluster SLC fireplace pages",
        "anchor_text_suggestions": "Fireplace repair Salt Lake City | SLC fireplace repair | Fireplace service in SLC",
        "rationale": "1,893-word page. Cluster all SLC fireplace pages.",
        "priority": "P0",
    },
    "/fireplace-contractor-in-layton/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace)",
        "link_from": "/services/ fireplace hub | /service-areas/layton/ if exists | Related fireplace pages",
        "anchor_text_suggestions": "Fireplace contractor Layton | Fireplace installation Layton | Layton fireplace services",
        "rationale": "1,799-word page for Layton market. Verify /service-areas/layton/ exists or create.",
        "priority": "P1",
    },
    "/fireplace-repair-service/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Service Parent Page",
        "link_from": "/services/ hub fireplace cluster | Homepage fireplace section | All city-specific fireplace repair pages should link UP to this as parent | Main nav if not already",
        "anchor_text_suggestions": "Fireplace repair service | Fireplace repair | Fireplace service in Utah",
        "rationale": "This should be the PARENT for all city-specific fireplace-repair pages. Currently only 1 inlink \u2014 critical to fix. Should be a hub receiving links from every city variant and linking down to each city variant.",
        "priority": "P0",
    },
    "/emergency-furnace-repair-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Emergency Furnace)",
        "link_from": "/services/emergency-services/furnace-repair/ parent (CRITICAL) | /service-areas/salt-lake-city/ | Homepage emergency banner | All SLC furnace pages",
        "anchor_text_suggestions": "Emergency furnace repair Salt Lake City | 24/7 furnace repair SLC | Emergency HVAC Salt Lake City",
        "rationale": "1,975-word emergency page. HIGH commercial intent (emergency = convert). MUST link from emergency services parent and homepage emergency banner.",
        "priority": "P0",
    },
    "/furnace-repair-sandy/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/services/emergency-services/furnace-repair/ | /service-areas/sandy/ | Sandy showroom page | Cluster all Sandy HVAC pages",
        "anchor_text_suggestions": "Furnace repair Sandy | Sandy furnace repair | Emergency furnace Sandy",
        "rationale": "1,836-word page. Sandy is a showroom location \u2014 link prominently from Sandy showroom.",
        "priority": "P0",
    },
    "/electric-fireplace-south-salt-lake-city/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace)",
        "link_from": "/electric-fireplaces/ parent | /service-areas/salt-lake-city/ or south-salt-lake-city/ | /gas-fireplace-inserts-in-south-salt-lake-city/ (related)",
        "anchor_text_suggestions": "Electric fireplace South SLC | Electric fireplace South Salt Lake | SSLC electric fireplace",
        "rationale": "1,953-word page. Cluster South SLC fireplace pages.",
        "priority": "P0",
    },
    "/furnace-installation-services-in-sandy/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Furnace)",
        "link_from": "/service-areas/sandy/ | Sandy showroom | /furnace-repair-sandy/ | Cluster Sandy HVAC pages | Financing",
        "anchor_text_suggestions": "Furnace installation Sandy | Sandy furnace installation services | New furnace Sandy",
        "rationale": "1,800-word page. Sandy is showroom market \u2014 link from showroom.",
        "priority": "P0",
    },
    "/expert-ac-repair-davis-county/": {
        "action": "LINK_FROM",
        "classification": "County Service Page (AC)",
        "link_from": "/services/hvac-systems/air-conditioning/ parent | /service-areas/davis-county/ if exists | /gas-fireplace-contractor-in-davis-county/ (same county)",
        "anchor_text_suggestions": "AC repair Davis County | Davis County air conditioning repair | AC service Davis",
        "rationale": "1,808-word county-level page. Cluster Davis County services together.",
        "priority": "P0",
    },
    "/free-estimate-fireplace-utah/": {
        "action": "REDIRECT",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "N/A \u2014 301 to main contact/quote form",
        "anchor_text_suggestions": "N/A",
        "rationale": "Legacy URL. 301 to main /contact/ or /free-estimate/ page.",
        "priority": "P2",
    },
    "/fireplace-mantels/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Category",
        "link_from": "/services/ fireplace hub | All Napoleon product pages | /contemporary-fireplaces/ | /custom-fireplaces/ | /build-your-fireplace/",
        "anchor_text_suggestions": "Fireplace mantels | Custom mantels | Mantel options | Design your mantel",
        "rationale": "Accessory/customization page (477 words). Link from all fireplace product + design pages. Consider expanding content.",
        "priority": "P1",
    },
    "/fireplace-inserts-contractor-in-ogden/": {
        "action": "LINK_FROM",
        "classification": "City Service Page (Fireplace Insert)",
        "link_from": "/gas-wood-inserts/ parent | /service-areas/ogden/ | West Haven showroom | Other Ogden fireplace pages",
        "anchor_text_suggestions": "Fireplace inserts Ogden | Ogden fireplace insert contractor | Fireplace insert installation Ogden",
        "rationale": "1,842-word city+product page. Link from Ogden/West Haven showroom + inserts parent.",
        "priority": "P0",
    },
    "/gas-fireplace-contractor-in-davis-county/": {
        "action": "LINK_FROM",
        "classification": "County Service Page (Fireplace)",
        "link_from": "/services/ fireplace hub | /service-areas/davis-county/ if exists | /expert-ac-repair-davis-county/ (cross-link same county)",
        "anchor_text_suggestions": "Gas fireplace Davis County | Davis County fireplace contractor | Fireplace installation Davis",
        "rationale": "1,871-word county-level page. Cluster with other Davis County service pages.",
        "priority": "P0",
    },
    "/furnace-repair-park-city-utah/": {
        "action": "CONSOLIDATE",
        "classification": "Potentially Duplicate City Service Page",
        "link_from": "Check for duplication with other PC furnace pages. If unique, link from /service-areas/park-city/ and cluster with PC furnace pages.",
        "anchor_text_suggestions": "Furnace repair Park City",
        "rationale": "1,674-word page. Review for potential overlap with /furnace-tune-up-park-city/, /furnace-maintenance-park-city-utah/, /furnace-cleaning-park-city/, /furnace-replacement-park-city/, /furnace-installation-park-city/. That's 6 PC furnace pages \u2014 likely too fragmented. Consider consolidation into fewer, stronger pages.",
        "priority": "P1",
    },

    # ========================================================================
    # 2 INLINKS (15 pages)
    # ========================================================================
    "/starfire-52/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Page",
        "link_from": "/services/ fireplace hub | /gas-wood-stoves/ if it's a stove | /contemporary-fireplaces/ or style category | Other Napoleon product pages (cross-link)",
        "anchor_text_suggestions": "Starfire 52 | Napoleon Starfire 52 | Starfire 52 gas fireplace",
        "rationale": "Product page. 342 words is thin (see thin_pages plan \u2014 also flagged there). Link from fireplace hub + related product pages.",
        "priority": "P1",
    },
    "/coupons/free-smokeless-fire-pit-with-the-purchase-of-a-new-fireplace/": {
        "action": "NOINDEX",
        "classification": "Coupon",
        "link_from": "N/A \u2014 noindex (covered in thin_pages plan)",
        "anchor_text_suggestions": "N/A",
        "rationale": "Individual coupon page \u2014 noindex with other coupons. Already has 2 inlinks from coupon hub + footer, which is appropriate.",
        "priority": "P1",
    },
    "/showrooms-fireplace-utah/": {
        "action": "CONSOLIDATE",
        "classification": "Legacy Fireplace Subsite",
        "link_from": "Post-migration to /showrooms/ or /locations/: link from every page (showroom CTA is key conversion element)",
        "anchor_text_suggestions": "Visit our showrooms | See fireplaces in person | West Haven showroom | Sandy showroom",
        "rationale": "Showroom page has high commercial value but legacy URL. Migrate to /showrooms/ or /locations/ and link from every fireplace page + homepage.",
        "priority": "P1",
    },
    "/testimonials/ross-przybylski/": {
        "action": "CONSOLIDATE",
        "classification": "Individual Testimonial",
        "link_from": "N/A \u2014 consolidate into /testimonials/ hub (covered in thin_pages plan)",
        "anchor_text_suggestions": "N/A",
        "rationale": "Individual testimonial \u2014 batch consolidate all 7 individual testimonial pages into single /testimonials/ hub with Review schema. 301 individual URLs to hub.",
        "priority": "P2",
    },
    "/gas-wood-inserts/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Category",
        "link_from": "/services/ fireplace hub | Homepage fireplace section | All gas/wood insert city pages (ogden, sandy, SSL) should link UP to this parent",
        "anchor_text_suggestions": "Gas & wood fireplace inserts | Fireplace inserts | Gas wood inserts",
        "rationale": "PARENT for all fireplace insert city pages. Should receive links from every city-specific insert page + send links down. Currently under-linked parent.",
        "priority": "P0",
    },
    "/coupons/800-off-a-full-system/": {
        "action": "NOINDEX",
        "classification": "Coupon",
        "link_from": "N/A \u2014 noindex",
        "anchor_text_suggestions": "N/A",
        "rationale": "Coupon \u2014 noindex batch.",
        "priority": "P1",
    },
    "/truflame-direct-vent-luxury-fireplaces/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Page",
        "link_from": "/services/ fireplace hub | /contemporary-fireplaces/ | /custom-fireplaces/ | Homepage fireplace luxury section | Other Napoleon product pages",
        "anchor_text_suggestions": "TruFlame luxury fireplaces | Napoleon TruFlame | Luxury direct-vent fireplaces",
        "rationale": "Also in thin_pages plan (EXPAND to 1,500+ words). Once expanded, link widely from fireplace hub + luxury/custom category pages.",
        "priority": "P1",
    },
    "/ascent-multi-view/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Page",
        "link_from": "/services/ fireplace hub | Other Napoleon Ascent product pages | /custom-fireplaces/ | /contemporary-fireplaces/",
        "anchor_text_suggestions": "Ascent Multi-View | Napoleon Multi-View fireplace | See-through fireplace",
        "rationale": "Also in thin_pages plan (EXPAND). Post-expansion, link from product family + design category pages.",
        "priority": "P1",
    },
    "/electric-fireplaces/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Category",
        "link_from": "/services/ fireplace hub | Homepage fireplace section | All electric-fireplace city pages should link UP to this | Related categories (contemporary/custom)",
        "anchor_text_suggestions": "Electric fireplaces | Electric fireplace options | Electric fireplace installation Utah",
        "rationale": "PARENT for all electric-fireplace city pages. 649 words. Should be receiving links from every city-specific electric-fireplace page.",
        "priority": "P0",
    },
    "/plasmafire-vent-free/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Page",
        "link_from": "/services/ fireplace hub | /electric-fireplaces/ category | Other Napoleon product pages",
        "anchor_text_suggestions": "Plasmafire vent-free | Vent-free electric fireplace | Plasmafire fireplace",
        "rationale": "Product page (311 words \u2014 near thin threshold). Link from category + product cross-links.",
        "priority": "P1",
    },
    "/testimonials/john-jude-jj/": {
        "action": "CONSOLIDATE",
        "classification": "Individual Testimonial",
        "link_from": "N/A \u2014 consolidate",
        "anchor_text_suggestions": "N/A",
        "rationale": "Batch consolidate with other testimonials.",
        "priority": "P2",
    },
    "/altitude-x-series/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Page",
        "link_from": "/services/ fireplace hub | /contemporary-fireplaces/ | /custom-fireplaces/ | /truflame-direct-vent-luxury-fireplaces/ (premium cluster) | Other Napoleon product pages",
        "anchor_text_suggestions": "Altitude X Series | Napoleon Altitude X | Premium direct-vent fireplace",
        "rationale": "Also in thin_pages plan (EXPAND to 1,500+ words). Premium product \u2014 cluster with TruFlame for luxury tier.",
        "priority": "P1",
    },
    "/ascent-36/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Page",
        "link_from": "/services/ fireplace hub | /contemporary-fireplaces/ | /custom-fireplaces/ | Other Ascent product pages (multi-view, 30, 35, 42) | Homepage fireplace section",
        "anchor_text_suggestions": "Napoleon Ascent 36 | Ascent 36 gas fireplace | 36-inch gas fireplace",
        "rationale": "Also in thin_pages plan (EXPAND to 1,200+ words). Cluster Ascent family pages + category links.",
        "priority": "P1",
    },
    "/outdoor-heating/": {
        "action": "LINK_FROM",
        "classification": "Product Category (Outdoor)",
        "link_from": "/services/ hub | /outdoor-fireplace-contractor-in-sandy/ | Homepage outdoor section if exists | Related outdoor product pages",
        "anchor_text_suggestions": "Outdoor heating | Outdoor patio heaters | Outdoor heating solutions",
        "rationale": "Category page (509 words). Link from outdoor fireplace contractor pages (same cluster).",
        "priority": "P1",
    },
    "/gas-wood-stoves/": {
        "action": "LINK_FROM",
        "classification": "Fireplace Product Category",
        "link_from": "/services/ fireplace hub | /gas-wood-inserts/ related | /gas-log-sets/ related | Homepage fireplace section",
        "anchor_text_suggestions": "Gas & wood stoves | Wood-burning stoves | Gas stove fireplaces",
        "rationale": "Product category (559 words). Link from fireplace hub + related gas/wood pages.",
        "priority": "P1",
    },
}


# =========================================================================
# BUILD WORKBOOK
# =========================================================================

wb = Workbook()
ws = wb.active
ws.title = "Orphans & Internal Linking"

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
section_fill = PatternFill("solid", fgColor="DDEBF7")

ws["A1"] = "Comfort Solutions \u2014 Orphans & Underlinked Pages Action Plan"
ws["A1"].font = title_font
ws.merge_cells("A1:L1")
ws["A2"] = "67 underlinked URLs (8 with 0 inlinks, 44 with 1, 15 with 2) | 88 orphaned pages in sitemaps per SEMrush | Roadmap item #6 (P1)"
ws["A2"].font = subtitle_font
ws.merge_cells("A2:L2")
ws.row_dimensions[1].height = 22
ws.row_dimensions[2].height = 18

# Group headers
group_row = 3
ws.cell(row=group_row, column=1, value="PAGE DATA").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=1, end_row=group_row, end_column=5)
ws.cell(row=group_row, column=1).alignment = center
ws.cell(row=group_row, column=1).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=6, value="ACTION").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=6, end_row=group_row, end_column=7)
ws.cell(row=group_row, column=6).alignment = center
ws.cell(row=group_row, column=6).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=8, value="LINKING PLAN").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=8, end_row=group_row, end_column=10)
ws.cell(row=group_row, column=8).alignment = center
ws.cell(row=group_row, column=8).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

ws.cell(row=group_row, column=11, value="TRACKING").fill = section_fill
ws.merge_cells(start_row=group_row, start_column=11, end_row=group_row, end_column=12)
ws.cell(row=group_row, column=11).alignment = center
ws.cell(row=group_row, column=11).font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

for col in range(1, 13):
    c = ws.cell(row=group_row, column=col)
    if not c.fill.fgColor.rgb or c.fill.fgColor.rgb == "00000000":
        c.fill = section_fill
ws.row_dimensions[group_row].height = 20

headers = [
    "#", "URL", "Title", "Word Count", "Current Inlinks",
    "Action", "Classification",
    "Link FROM (Source Pages)", "Anchor Text Suggestions", "Rationale",
    "Priority", "Status",
]

for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.fill = header_fill
    c.font = header_font
    c.alignment = center
    c.border = border
ws.row_dimensions[4].height = 38

action_colors = {
    "LINK_FROM":   PatternFill("solid", fgColor="C6E0B4"),
    "NOINDEX":     PatternFill("solid", fgColor="FFF2CC"),
    "REDIRECT":    PatternFill("solid", fgColor="BDD7EE"),
    "CONSOLIDATE": PatternFill("solid", fgColor="D9E1F2"),
    "DELETE":      PatternFill("solid", fgColor="F8CBAD"),
}
action_font_colors = {
    "LINK_FROM":   "375623",
    "NOINDEX":     "7F6000",
    "REDIRECT":    "1F4E78",
    "CONSOLIDATE": "1F4E78",
    "DELETE":      "9C0006",
}

# Sort: 0 inlinks first, then by priority, then by action
def sort_key(row):
    key = row["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(key, {})
    inlinks = int(row["Unique Inlinks"])
    action = plan.get("action", "OTHER")
    action_order = {
        "LINK_FROM": 0, "CONSOLIDATE": 1, "REDIRECT": 2, "NOINDEX": 3, "DELETE": 4,
    }.get(action, 5)
    priority = plan.get("priority", "P3")
    return (inlinks, action_order, priority, key)


df["_sort_key"] = df.apply(sort_key, axis=1)
df_sorted = df.sort_values("_sort_key").reset_index(drop=True)

for i, row in df_sorted.iterrows():
    url_path = row["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(url_path, {})
    action = plan.get("action", "")
    r = i + 5
    title = row["Title 1"] if pd.notna(row["Title 1"]) else ""
    if len(str(title)) > 70:
        title = str(title)[:67] + "..."
    values = [
        i + 1,
        row["Address"],
        title,
        int(row["Word Count"]) if pd.notna(row["Word Count"]) else "",
        int(row["Unique Inlinks"]) if pd.notna(row["Unique Inlinks"]) else 0,
        action,
        plan.get("classification", ""),
        plan.get("link_from", ""),
        plan.get("anchor_text_suggestions", ""),
        plan.get("rationale", ""),
        plan.get("priority", ""),
        "Not Started",
    ]
    for col, v in enumerate(values, 1):
        c = ws.cell(row=r, column=col, value=v)
        c.font = cell_font_small if col >= 8 else cell_font
        c.border = border
        if col in (1, 4, 5, 6, 11):
            c.alignment = center
        else:
            c.alignment = left
        if col == 5 and isinstance(v, int) and v == 0:
            c.fill = red_fill
            c.font = Font(name="Calibri", size=10, bold=True, color="9C0006")
        if col == 6 and action in action_colors:
            c.fill = action_colors[action]
            c.font = Font(name="Calibri", size=10, bold=True, color=action_font_colors.get(action, "000000"))
        if col == 11:
            if v == "P0":
                c.fill = red_fill
                c.font = Font(name="Calibri", size=10, bold=True, color="9C0006")
            elif v == "P1":
                c.fill = yellow_fill
            elif v == "P2":
                c.fill = green_fill

widths = {
    "A": 4, "B": 58, "C": 42, "D": 9, "E": 9,
    "F": 13, "G": 32,
    "H": 65, "I": 45, "J": 65,
    "K": 9, "L": 13,
}
for col, w in widths.items():
    ws.column_dimensions[col].width = w

for r in range(5, 5 + len(df_sorted)):
    url_path = df_sorted.iloc[r - 5]["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(url_path, {})
    if plan.get("action") == "LINK_FROM":
        ws.row_dimensions[r].height = 130
    else:
        ws.row_dimensions[r].height = 70

ws.freeze_panes = "C5"

# =========================================================================
# SHEET 2 — Summary & Hub Strategy
# =========================================================================
ws2 = wb.create_sheet("Summary & Hub Strategy")
ws2["A1"] = "Orphans & Internal Linking \u2014 Summary & Hub Strategy"
ws2["A1"].font = title_font
ws2.merge_cells("A1:B1")

# Count by action
action_counts = {}
for i, row in df_sorted.iterrows():
    url_path = row["Address"].replace("https://www.comfortsolutionsutah.com", "")
    plan = url_plans.get(url_path, {})
    action = plan.get("action", "OTHER")
    action_counts[action] = action_counts.get(action, 0) + 1

p0_link_count = sum(1 for i, row in df_sorted.iterrows()
                    if url_plans.get(row["Address"].replace("https://www.comfortsolutionsutah.com", ""), {}).get("priority") == "P0"
                    and url_plans.get(row["Address"].replace("https://www.comfortsolutionsutah.com", ""), {}).get("action") == "LINK_FROM")

ctx = [
    ("", ""),
    ("=== OVERVIEW ===", ""),
    ("Raw underlinked URLs (SF crawl)", "67"),
    ("Filtered to SEO-relevant URLs", f"{len(df)} (excluded: PPC, coupons, financing, testimonials, WP archives, legal, events, test pages, legacy subsite hubs)"),
    ("Orphaned sitemap pages (SEMrush)", "88 (URL list not exported \u2014 raw count only)"),
    ("Source", "SF crawl \u2014 underlinked_pages.xlsx + SEMrush Site Health audit"),
    ("Audit reference", "Technical/On-Page Audit \u2014 roadmap item #6 (P1)"),
    ("", ""),
    ("=== SCOPE FILTER ===", ""),
    ("Why exclude non-SEO pages?", "Pages without ranking potential don't need internal link equity. Focus effort on content pages that can actually convert organic traffic."),
    ("Excluded (handled elsewhere)", "PPC landing pages, coupons, financing, testimonials, WP taxonomy archives, legal pages, event/promo pages, test pages, Elementor templates, legacy Fireplace Utah subsite hubs (migration in thin_pages plan)"),
    ("Included (SEO-relevant)", "City-specific service pages, fireplace product pages, fireplace product category pages, fireplace parent service pages, product accessory pages"),
    ("", ""),
    ("=== ACTION DISTRIBUTION ===", ""),
    ("LINK_FROM (add internal links, keep page)", f"{action_counts.get('LINK_FROM', 0)} pages \u2014 substantial content starved of equity"),
    ("CONSOLIDATE (merge or cluster)", f"{action_counts.get('CONSOLIDATE', 0)} pages \u2014 duplicates or needs migration"),
    ("", ""),
    ("=== URGENT HUB GAPS (parent pages missing equity) ===", ""),
    ("/services/ (Services Hub)", "Only 21 inlinks. See thin_pages plan \u2014 needs content expansion + more inlinks from homepage nav"),
    ("/fireplace-repair-service/ (Parent)", "P0 \u2014 Only 1 inlink. Should receive links from every city-specific fireplace repair page"),
    ("/gas-wood-inserts/ (Parent)", "P0 \u2014 Only 2 inlinks. Should receive links from every city+insert page (ogden, sandy, SSL)"),
    ("/electric-fireplaces/ (Parent)", "P0 \u2014 Only 2 inlinks. Should receive links from every city+electric-fireplace page"),
    ("", ""),
    ("=== RECOMMENDED HUB-AND-SPOKE LINKING PATTERN ===", ""),
    ("1. Parent service pages link DOWN to city variants", "/fireplace-repair-service/ \u2192 /fireplace-repair-salt-lake-city/, /fireplace-repair-sandy/, etc."),
    ("2. City variants link UP to parent", "Every /fireplace-repair-[city]/ page links back to /fireplace-repair-service/"),
    ("3. City variants cross-link horizontally (siblings)", "SLC fireplace pages link to each other as 'Related services in Salt Lake City'"),
    ("4. Service area pages act as city hubs", "/service-areas/park-city/ links to ALL Park City service pages (HVAC + fireplace + plumbing)"),
    ("5. Product pages link to category + product family", "/ascent-36/ \u2192 /contemporary-fireplaces/, /custom-fireplaces/, other Ascent models"),
    ("6. Showroom pages link to product pages", "West Haven + Sandy showroom pages link to fireplace product pages (showroom = conversion tool)"),
    ("", ""),
    ("=== CITY CLUSTER STRUCTURE (priority markets) ===", ""),
    ("Salt Lake City cluster", "11 orphaned city-service pages. Link all from /service-areas/salt-lake-city/ + cross-link horizontally."),
    ("Park City cluster", "6 orphaned PC furnace pages. DUPLICATION RISK \u2014 review if all 6 are needed or should consolidate."),
    ("Sandy cluster (showroom market)", "5 orphaned Sandy pages. Link from Sandy showroom page prominently."),
    ("Ogden/West Haven cluster (HQ market)", "4 orphaned Ogden pages. Link from West Haven showroom."),
    ("Davis County cluster", "2 county-level pages. Cross-link + create /service-areas/davis-county/ if missing."),
    ("Layton / Orem / South SLC", "Individual city pages. Verify service area pages exist for these cities."),
    ("", ""),
    ("=== DETECTED DUPLICATIONS TO RESOLVE ===", ""),
    ("/furnace-tune-up-salt-lake-city/ vs /furnace-tune-up-services-salt-lake-city/", "P0 \u2014 Near-identical word counts (2,138 vs 2,143). Consolidate, 301 the weaker URL."),
    ("6 Park City furnace pages", "P1 \u2014 /furnace-tune-up-park-city/, /furnace-maintenance-park-city-utah/, /furnace-cleaning-park-city/, /furnace-replacement-park-city/, /furnace-installation-park-city/, /furnace-repair-park-city-utah/. Review overlap \u2014 likely consolidate into 2-3 pages."),
    ("/fireplace-repair-salt-lake-city/ vs /fireplace-service-salt-lake-city/ vs /gas-fireplace-repair-services-in-salt-lake-city/", "P1 \u2014 Three SLC fireplace-repair/service pages. Review overlap."),
    ("", ""),
    ("=== QUICK WINS (start here) ===", ""),
    ("Consolidate duplicate SLC furnace tune-up pages", "Pick canonical, 301 the duplicate. 15 min."),
    ("Review 6 Park City furnace pages for consolidation", "Likely too fragmented \u2014 consolidate into 2-3 stronger pages."),
    ("Review 3 SLC fireplace repair/service pages for consolidation", "Evaluate overlap between /fireplace-repair-salt-lake-city/, /fireplace-service-salt-lake-city/, /gas-fireplace-repair-services-in-salt-lake-city/."),
    ("", ""),
    ("=== ABOUT THE 88 SEMRUSH ORPHAN COUNT ===", ""),
    ("Why 67 (SF) vs 88 (SEMrush)?", "SF crawl finds pages via internal links only. SEMrush also checks sitemap entries. The 21-page gap likely = pages in sitemap but NOT crawlable from internal links (true orphans)."),
    ("How to get the full 88 list", "Log into SEMrush, go to Site Audit \u2192 Issues \u2192 filter 'Orphaned pages in sitemaps' \u2014 export the full URL list."),
    ("Action for the additional 21 orphans", "Apply same framework: if SEO-relevant \u2192 add internal links; if not \u2192 remove from sitemap + noindex."),
    ("", ""),
    ("=== IMPLEMENTATION NOTES ===", ""),
    ("Add links contextually, not in footers", "Contextual in-body links pass more equity than footer links. Prefer sentence-level integration over nav/footer."),
    ("Use descriptive anchor text", "Avoid generic 'click here'. Use primary keyword variant (e.g., 'furnace repair in Park City' not 'Park City services')."),
    ("Avoid over-optimization", "Don't use exact-match anchor text on every link. Mix branded, descriptive, and keyword anchors."),
    ("Check for existing broken links", "When adding new links, verify destination URL. Roadmap item #1 flagged 21 legacy 404s from furnace-repair page \u2014 avoid re-creating."),
    ("Reciprocal linking is fine for clusters", "City-service siblings SHOULD reciprocally link. This is not 'link scheme' \u2014 it's proper topical clustering."),
    ("Re-crawl after changes", "Run SF crawl again 2-4 weeks after implementation. Target: 0 pages with <3 inlinks."),
]

for r, (k, v) in enumerate(ctx, 2):
    c1 = ws2.cell(row=r, column=1, value=k)
    c2 = ws2.cell(row=r, column=2, value=v)
    if k.startswith("==="):
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    elif k and not v:
        c1.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
    else:
        c1.font = Font(name="Calibri", size=10, bold=True)
        c2.font = cell_font
        c2.alignment = Alignment(wrap_text=True, vertical="top")

ws2.column_dimensions["A"].width = 55
ws2.column_dimensions["B"].width = 110

for r in range(2, 2 + len(ctx)):
    ws2.row_dimensions[r].height = 32

wb.save(out)
print(f"Saved: {out}")
print(f"Total URLs processed: {len(df_sorted)}")
print(f"Action distribution: {action_counts}")
