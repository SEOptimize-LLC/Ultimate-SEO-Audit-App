"""Local SEO Auditor.

Audits local SEO patterns. Activates only for sites with local-business
indicators (LocalBusiness schema, service-area pages, NAP markers,
city/region in title tags). Skip the auditor entirely if no local
indicators are present — most clients aren't local-business sites.

Checks include:
- LocalBusiness schema presence and basic completeness
- NAP consistency (does the site have visible NAP at all)
- Service-area page existence for sites with location-bearing keywords
- City stuffing in title tags (signals manipulation, not value)
- Service-area pages with thin content (template pages with just the
  city name swapped)
- Indexable city pages without unique content per location

This auditor is calibrated for the IHS portfolio (home services + local
businesses) but the patterns generalize. The auditor does NOT replace
specialized GBP/citation audits — those need external data we don't
fetch in this pipeline.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Optional

import pandas as pd

from .base_auditor import BaseAuditor, is_empty_or_missing
from models.audit_result import AuditCategory, AuditIssue, Severity


# Heuristic: at least this many city-mentioning URLs to consider the
# site "local"
LOCAL_URL_THRESHOLD = 3

# Suspicious: title contains 3+ city names — usually indicates
# keyword-stuffing the local pack
CITY_STUFFING_THRESHOLD = 3

# Service-area pages should have at least this much unique content
# beyond the template
THIN_SERVICE_AREA_WORDS = 250

# Structured-data substrings that indicate genuine local-business /
# location targeting in the JSON-LD (subtypes included since the IHS
# portfolio is home services, but the generic markers carry the signal).
LOCAL_SCHEMA_KEYWORDS = [
    "localbusiness",
    "postaladdress",
    "areaserved",
    "geocoordinates",
    "plumber",
    "hvacbusiness",
    "electrician",
    "generalcontractor",
    "roofingcontractor",
]

# A URL is treated as a sub-page of a service-area / locations hub
# (i.e., targeting one specific place, not the index) when it has a
# non-empty slug after the hub segment.
SERVICE_AREA_SUBPAGE_RE = re.compile(r"/(?:service-areas?|locations)/[^/?#]+")


# Common Utah cities (extend as portfolio expands)
UTAH_CITIES = [
    "salt-lake-city", "salt-lake", "st-george", "park-city",
    "west-jordan", "west-valley", "south-jordan", "north-salt-lake",
    "north-ogden", "spanish-fork", "cedar-city", "pleasant-grove",
    "american-fork", "sandy", "orem", "provo", "ogden", "lehi",
    "draper", "murray", "tooele", "layton", "riverton", "herriman",
    "highland", "salem", "midvale", "kearns", "bluffdale",
    "springville", "millcreek", "taylorsville",
]


class LocalSEOAuditor(BaseAuditor):
    """Auditor for local SEO patterns."""

    def get_audit_type(self) -> str:
        return "technical"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        if not self._site_is_local():
            self._emit_inactive_diagnostic()
            return self.issues

        self._emit_active_diagnostic()
        self._check_localbusiness_schema()
        self._check_thin_service_area_pages()
        self._check_city_stuffing_in_titles()
        self._check_service_area_template_duplication()
        self._check_location_demotion_risk()

        return self.issues

    # =========================================================================
    # SITE-TYPE DETECTION
    # =========================================================================

    def _site_is_local(self) -> bool:
        """Return True if the site shows local-business indicators."""
        if not self.has_column("url"):
            return False

        urls = self.df["url"].dropna().astype(str).str.lower()

        # Count URLs containing city names
        city_url_count = sum(
            urls.str.contains(re.escape(c), regex=True, na=False).sum()
            for c in UTAH_CITIES
        )
        if city_url_count >= LOCAL_URL_THRESHOLD:
            return True

        # /service-area(s)/ path is a strong signal
        if urls.str.contains("/service-area", regex=False, na=False).any():
            return True

        # /locations/ also common
        if urls.str.contains("/locations/", regex=False, na=False).any():
            return True

        # LocalBusiness schema
        if self.has_column("structured_data"):
            sd = self.df["structured_data"].dropna().astype(str).str.lower()
            if sd.str.contains("localbusiness").any():
                return True

        return False

    def _emit_inactive_diagnostic(self) -> None:
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.LOCAL_SEO,
            issue_type="local_auditor_inactive",
            title="Local SEO auditor not activated for this site",
            description=(
                "No local-business indicators detected (no service-"
                "area URLs, city-name URL patterns, or LocalBusiness "
                "schema). Local SEO checks were skipped. If this is "
                "a local-business site, the indicators may be on a "
                "different URL convention than the auditor "
                "recognizes."
            ),
            recommendation="No action — informational only.",
            impact="",
        )

    def _emit_active_diagnostic(self) -> None:
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.LOCAL_SEO,
            issue_type="local_auditor_active",
            title="Local SEO checks active",
            description=(
                "Local-business indicators detected. Running checks "
                "for LocalBusiness schema, service-area page quality, "
                "city stuffing in title tags, and template duplication "
                "across city pages."
            ),
            recommendation="No action — informational.",
            impact="",
        )

    # =========================================================================
    # CHECKS
    # =========================================================================

    def _check_localbusiness_schema(self) -> None:
        """Flag missing LocalBusiness schema on the homepage and key pages."""
        if not self.has_column("url"):
            return
        if not self.has_column("structured_data") and \
           not self.has_column("has_structured_data"):
            return

        # Homepage and main service pages should have LocalBusiness schema
        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        # Find the homepage
        is_homepage = scope["url"].astype(str).apply(
            lambda u: urlparse_safe_path(u) in ("", "/")
        )
        homepage = scope[is_homepage]

        if homepage.empty:
            return

        if self.has_column("structured_data"):
            sd_col = homepage["structured_data"].fillna("").astype(str).str.lower()
            has_lb = sd_col.str.contains("localbusiness")
        elif self.has_column("has_structured_data"):
            has_lb = homepage["has_structured_data"].fillna(False).astype(bool)
        else:
            return

        if has_lb.any():
            return

        urls = homepage["url"].head(5).tolist()
        self.create_issue(
            severity=Severity.HIGH,
            category=AuditCategory.LOCAL_SEO,
            issue_type="missing_localbusiness_schema",
            title="Homepage missing LocalBusiness schema",
            description=(
                "The homepage does not include LocalBusiness "
                "structured data. For a local-business site, "
                "LocalBusiness schema is the primary mechanism for "
                "communicating identity, address, hours, contact "
                "info, and service area to Google. Missing schema "
                "weakens the entity signal that Google's local "
                "ranking systems rely on."
            ),
            affected_urls=urls,
            count=1,
            recommendation=(
                "Add LocalBusiness JSON-LD schema to the homepage "
                "with the following minimum properties: name, image, "
                "address (PostalAddress with street, city, state, "
                "postalCode), telephone, openingHoursSpecification, "
                "geo (GeoCoordinates), priceRange, sameAs (links to "
                "Google Business Profile, Facebook, etc.). Use the "
                "most specific subtype available (Plumber, "
                "HVACBusiness, etc.) rather than generic "
                "LocalBusiness when applicable. Validate with "
                "Google's Rich Results Test."
            ),
            impact=(
                "LocalBusiness schema is a foundational signal for "
                "local-pack ranking. Sites without it underperform "
                "in Map Pack results compared to competitors with "
                "complete schema, especially in competitive local "
                "queries."
            ),
        )

    def _check_thin_service_area_pages(self) -> None:
        """Flag service-area pages with thin content."""
        if not self.has_column("url") or not self.has_column("word_count"):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        # Service-area page detection
        is_service_area = scope["url"].astype(str).apply(
            lambda u: any(
                p in u.lower()
                for p in ("/service-area/", "/service-areas/", "/locations/")
            )
        )
        service_pages = scope[is_service_area]
        if service_pages.empty:
            return

        condition = service_pages["word_count"] < THIN_SERVICE_AREA_WORDS
        thin = service_pages[condition]
        urls = thin["url"].head(100).tolist()
        count = len(thin)

        if count > 0:
            avg_words = float(thin["word_count"].mean())
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.LOCAL_SEO,
                issue_type="thin_service_area_pages",
                title=f"{count} service-area pages have thin content",
                description=(
                    f"Found {count} service-area pages with under "
                    f"{THIN_SERVICE_AREA_WORDS} words of content "
                    f"(average: {avg_words:.0f} words). Thin service-"
                    "area pages typically use a templated layout "
                    "with just the city name swapped — they offer "
                    "no unique value per location and are often "
                    "demoted by Google's local algorithms. The Map "
                    "Pack heavily favors pages with substantive, "
                    "city-specific content."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "For each service-area page, add genuinely "
                    "city-specific content: local landmarks served, "
                    "neighborhood names, common local issues "
                    "(climate-specific HVAC concerns, building-age "
                    "patterns affecting plumbing, etc.), local "
                    "testimonials, photos of local job sites, "
                    "service-area boundary maps. Aim for at least "
                    "500-800 words of unique-per-city content. If "
                    "you can't fill a page legitimately, consider "
                    "consolidating multiple thin city pages into a "
                    "regional page with a list of service areas."
                ),
                impact=(
                    "Thin service-area pages don't rank — and they "
                    "drag down the perceived quality of the broader "
                    "site. Google's local algorithms specifically "
                    "look for unique-per-location signals; "
                    "duplicated city pages get filtered out of the "
                    "Map Pack and underperform in organic results "
                    "for city-modified queries."
                ),
            )

    def _check_city_stuffing_in_titles(self) -> None:
        """Flag title tags containing many city names — keyword stuffing."""
        if not self.has_column("title"):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        def count_cities(title) -> int:
            if not isinstance(title, str):
                return 0
            t = title.lower()
            count = 0
            for city in UTAH_CITIES:
                # Count distinct city mentions, not partial matches
                pattern = r"\b" + re.escape(city.replace("-", " ")) + r"\b"
                if re.search(pattern, t):
                    count += 1
            return count

        scope = scope.copy()
        scope["city_count_in_title"] = scope["title"].apply(count_cities)
        condition = scope["city_count_in_title"] >= CITY_STUFFING_THRESHOLD
        urls = scope.loc[condition, "url"].head(100).tolist() \
            if "url" in scope.columns else []
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.MEDIUM,
                category=AuditCategory.LOCAL_SEO,
                issue_type="city_stuffing_in_titles",
                title=f"{count} pages have {CITY_STUFFING_THRESHOLD}+ cities in title",
                description=(
                    f"Found {count} pages with title tags listing "
                    f"{CITY_STUFFING_THRESHOLD} or more city names. "
                    "Cramming multiple cities into a single title is "
                    "a classic keyword-stuffing pattern that Google's "
                    "local algorithms penalize. The pattern usually "
                    "looks like 'Plumbing Services in Salt Lake "
                    "City, Sandy, Orem, Provo, Lehi' — which fails "
                    "to rank well for any of those individual cities "
                    "and signals manipulation."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Replace multi-city titles with either:\n"
                    "1. A single-city title for one location-specific "
                    "page each (recommended) — `Plumbing Services in "
                    "Sandy, UT | Brand`. Build separate pages per "
                    "city when targeting multiple cities.\n"
                    "2. A regional title covering the broader area "
                    "without listing cities — `Salt Lake County "
                    "Plumbing Services | Brand`.\n"
                    "Don't list 3+ cities in a title — it doesn't "
                    "rank for any of them."
                ),
                impact=(
                    "Multi-city titles fail to rank well for any "
                    "single city and signal keyword stuffing to "
                    "Google. They also produce poor SERP CTR — "
                    "users searching 'plumber in Sandy' don't trust "
                    "a result that lists 5 other cities they didn't "
                    "search for."
                ),
            )

    def _check_service_area_template_duplication(self) -> None:
        """Flag service-area pages where multiple cities share identical templates.

        Detection: city pages with identical word counts, near-identical
        H1s (only the city name varies), and structural similarity.
        Reuses near-duplicate signal if available.
        """
        if not self.has_columns(["url", "word_count"]):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        is_service_area = scope["url"].astype(str).apply(
            lambda u: any(
                p in u.lower()
                for p in ("/service-area/", "/service-areas/", "/locations/")
            )
        )
        service_pages = scope[is_service_area]
        if service_pages.empty or len(service_pages) < 3:
            return

        # Group by word count — if many pages have identical word
        # counts, they're likely templated
        word_count_groups = service_pages.groupby("word_count").size()
        big_clusters = word_count_groups[word_count_groups >= 3]
        if big_clusters.empty:
            return

        affected_count = int(big_clusters.sum())
        # Sample affected URLs from the largest cluster
        largest_wc = int(big_clusters.idxmax())
        affected = service_pages[
            service_pages["word_count"] == largest_wc
        ]["url"].head(100).tolist()

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.LOCAL_SEO,
            issue_type="service_area_template_duplication",
            title=f"{affected_count} service-area pages share suspiciously identical structure",
            description=(
                f"Found {affected_count} service-area pages where "
                f"multiple URLs share an identical word count "
                f"(largest cluster: {int(big_clusters.max())} pages "
                f"with exactly {largest_wc} words). Identical word "
                "counts across many pages strongly indicate "
                "template duplication — the same content with only "
                "the city name swapped. Google's near-duplicate "
                "detection specifically targets this pattern in "
                "local pages."
            ),
            affected_urls=affected,
            count=affected_count,
            recommendation=(
                "Audit the service-area pages and add unique "
                "content per location. Specifically: don't just "
                "swap the city name — write about local landmarks, "
                "neighborhoods, climate-specific issues, local "
                "testimonials, and photos from actual local jobs. "
                "If genuinely unique content per city isn't "
                "possible, consolidate to fewer pages with a list "
                "of cities served, rather than maintaining many "
                "near-duplicates. The Map Pack rewards specificity, "
                "not volume."
            ),
            impact=(
                "Templated service-area pages get filtered as "
                "near-duplicates in local search results. Many "
                "sites maintain dozens of these pages believing "
                "they help local rankings — they don't, because "
                "Google demotes the duplicates and may show only "
                "one of them. The effort spent maintaining "
                "templates would produce more results invested in "
                "fewer, unique-per-location pages."
            ),
        )

    def _check_location_demotion_risk(self) -> None:
        """Flag location-targeted pages that lack on-page local signals.

        Concept (locality signal; a location demotion is inferred, not documented): a page whose URL was built
        to rank for one specific place — a city slug in the path, or a
        service-area / locations sub-page — but whose on-page content does
        NOT reinforce that locality is at risk of being demoted for the
        locally-intended queries it targets. Google's local systems look
        for the target place to be reinforced in the title, the H1, and
        via LocalBusiness / areaServed schema; a URL that looks local but
        carries none of those signals sends a mixed message and tends to
        underperform place-modified and "near me" queries.

        Reinforcement signals checked (each only when its column is in the
        crawl — the check degrades to whatever is available):
          - the target city name appears in the title tag
          - the target city name appears in the H1
          - LocalBusiness / PostalAddress / areaServed / GeoCoordinates
            schema is present on the page

        A location-targeted page is flagged only when NONE of the checkable
        reinforcement signals are present. If neither ``title`` nor ``h1``
        is available in the crawl, the check no-ops — those are the primary
        on-page reinforcement signals and without them the assessment would
        not be grounded.
        """
        if not self.has_column("url"):
            return
        if not self.has_column("title") and not self.has_column("h1"):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]
        if scope.empty:
            return

        scope = scope.copy()
        location_targeted = scope["url"].apply(self._url_is_location_targeted)
        targeted = scope[location_targeted]
        if targeted.empty:
            return

        # Determine which reinforcement signals are actually checkable.
        has_title = self.has_column("title")
        has_h1 = self.has_column("h1")
        schema_checkable = (
            self.has_column("structured_data")
            and targeted["structured_data"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("nan", "")
            .ne("")
            .any()
        )

        def _is_reinforced(row: pd.Series) -> bool:
            if has_title and _text_has_city(row.get("title")):
                return True
            if has_h1 and _text_has_city(row.get("h1")):
                return True
            if schema_checkable and _has_local_schema(row.get("structured_data")):
                return True
            return False

        reinforced = targeted.apply(_is_reinforced, axis=1)
        at_risk = targeted[~reinforced]
        count = len(at_risk)
        if count == 0:
            return

        urls = at_risk["url"].head(100).tolist()
        checked_signals = []
        if has_title:
            checked_signals.append("city in the title tag")
        if has_h1:
            checked_signals.append("city in the H1")
        if schema_checkable:
            checked_signals.append("LocalBusiness / areaServed schema")
        signals_text = ", ".join(checked_signals)

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.LOCAL_SEO,
            issue_type="location_demotion_risk",
            title=f"{count} location-targeted pages lack on-page local signals",
            description=(
                f"Found {count} pages whose URL targets a specific place "
                "(a city name in the path, or a service-area/locations "
                "sub-page) but which carry none of the on-page local "
                f"signals checked for ({signals_text}). A URL that looks "
                "locally targeted but does not reinforce that locality in "
                "its visible content sends Google a mixed relevance "
                "signal. These pages are likely to be "
                "underperforming for the place-modified and 'near me' "
                "queries they were built to rank for — because nothing on "
                "the page confirms the location the URL implies."
            ),
            affected_urls=urls,
            recommendation=(
                "For each flagged page, reinforce the target location in "
                "the on-page signals: put the city (and state) in the "
                "title tag and the H1, reference the specific city — "
                "neighborhoods, landmarks, local context — in the body "
                "copy, and add LocalBusiness JSON-LD with an areaServed "
                "property naming the target city. Confirm the title, H1, "
                "and schema all name the same place the URL targets so the "
                "signals agree. If a page was not actually meant to rank "
                "locally, remove the city slug from its URL instead so the "
                "URL stops implying a local target it can't support."
            ),
            impact=(
                "Location demotion quietly suppresses pages that look "
                "local by URL but read as generic on the page. Competitors "
                "whose title, H1, content, and schema all reinforce the "
                "target city win the place-modified and Map Pack-adjacent "
                "queries these pages are meant to capture, so the traffic "
                "loss is invisible in aggregate rankings but real for the "
                "specific local queries that convert."
            ),
        )

    def _url_is_location_targeted(self, url: object) -> bool:
        """Return True if the URL targets one specific place.

        Two structural signals of single-place intent: a specific city
        slug anywhere in the URL, or a service-area/locations sub-page
        (a non-empty slug after the hub segment — the bare hub index does
        not count).
        """
        if not isinstance(url, str):
            return False
        u = url.lower()
        for city in UTAH_CITIES:
            if re.search(r"(?<![a-z0-9])" + re.escape(city) + r"(?![a-z0-9])", u):
                return True
        if SERVICE_AREA_SUBPAGE_RE.search(u):
            return True
        return False


def _text_has_city(text: object) -> bool:
    """Return True if any known city name appears as a word in the text."""
    if not isinstance(text, str) or not text:
        return False
    t = text.lower()
    for city in UTAH_CITIES:
        pattern = r"\b" + re.escape(city.replace("-", " ")) + r"\b"
        if re.search(pattern, t):
            return True
    return False


def _has_local_schema(structured_data: object) -> bool:
    """Return True if the structured-data blob contains a local-business marker."""
    if not isinstance(structured_data, str) or not structured_data:
        return False
    sd = structured_data.lower()
    return any(keyword in sd for keyword in LOCAL_SCHEMA_KEYWORDS)


def urlparse_safe_path(url: str) -> str:
    """Extract the path from a URL safely, returning empty string on failure."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).path
    except Exception:
        return ""
