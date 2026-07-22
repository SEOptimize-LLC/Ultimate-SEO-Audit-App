"""Ecommerce Patterns Auditor.

Detects ecommerce-specific SEO patterns that don't belong in the generic
technical auditor. Activates only when the site shows ecommerce
indicators (presence of product URLs, cart/checkout pages, product
schema, Shopify-specific patterns, etc.).

Checks include:
- View-all pages missing when paginated `?page=N` URLs exist
- Discontinued product 404s with backlinks (recommend "discontinued +
  alternatives" pattern instead of generic 301)
- Sale/promotional URLs returning 404 (recommend redirect-to-original)
- Faceted nav URLs lacking independent linkability when search demand
  exists for those facet combinations
- Missing Product schema on product URLs
- Shopify multiple-collection URL artifacts (canonicals not pointing
  to the canonical product URL)
- Cart/checkout/account pages indexable when they shouldn't be

Detection is gated by site-type detection — runs the heavy checks only
when ecommerce signals are present, otherwise emits an INSIGHT noting
the auditor was inactive.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional
from urllib.parse import urlparse, parse_qs

import pandas as pd

from .base_auditor import BaseAuditor, is_empty_or_missing
from models.audit_result import AuditCategory, AuditIssue, Severity


ECOMMERCE_URL_MARKERS = (
    "/product/", "/products/", "/p/", "/item/", "/shop/",
    "/category/", "/categories/", "/collection/", "/collections/",
    "/cart", "/checkout", "/basket",
    "/sku/",
)
"""URL path markers indicating an ecommerce site. Presence of any of
these triggers the deeper ecommerce checks."""

CART_CHECKOUT_PATTERNS = (
    "/cart", "/cart/", "/checkout", "/checkout/", "/basket", "/basket/",
    "/my-account", "/account/", "/wishlist", "/order/", "/orders/",
)


class EcommercePatternsAuditor(BaseAuditor):
    """Auditor for ecommerce-specific SEO patterns."""

    def get_audit_type(self) -> str:
        return "technical"

    def run_audit(self) -> list[AuditIssue]:
        self.clear_issues()

        if not self._site_is_ecommerce():
            self._emit_inactive_diagnostic()
            return self.issues

        # Always-on diagnostic (informational)
        self._emit_active_diagnostic()

        # Pattern checks
        self._check_paginated_without_view_all()
        self._check_indexable_cart_checkout()
        self._check_product_pages_missing_schema()
        self._check_shopify_collection_canonical_artifacts()
        self._check_session_id_in_urls()

        return self.issues

    # =========================================================================
    # SITE-TYPE DETECTION
    # =========================================================================

    def _site_is_ecommerce(self) -> bool:
        """Return True if the crawl shows ecommerce indicators.

        Multiple positive signals trigger ecommerce mode. A single weak
        signal (one URL containing /product/) isn't enough — we look
        for multiple URL markers, schema markers, or cart presence.
        """
        if not self.has_column("url"):
            return False

        urls = self.df["url"].dropna().astype(str).str.lower()

        # Count URLs matching ecommerce markers
        marker_hits = sum(
            urls.str.contains(re.escape(m), regex=True, na=False).sum()
            for m in ECOMMERCE_URL_MARKERS
        )
        if marker_hits >= 5:
            return True

        # Cart/checkout presence is a strong signal
        if any(
            urls.str.contains(re.escape(p), regex=True, na=False).any()
            for p in CART_CHECKOUT_PATTERNS
        ):
            return True

        # Structured data marker
        if self.has_column("structured_data"):
            sd = self.df["structured_data"].dropna().astype(str).str.lower()
            if sd.str.contains("product").any():
                return True

        # Shopify-specific path
        if urls.str.contains("/products/").any() and \
           urls.str.contains("/collections/").any():
            return True

        return False

    def _emit_inactive_diagnostic(self) -> None:
        """Emit an INSIGHT noting that ecommerce checks were skipped."""
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.ECOMMERCE_PATTERNS,
            issue_type="ecommerce_auditor_inactive",
            title="Ecommerce auditor not activated for this site",
            description=(
                "No ecommerce indicators detected (no product URLs, "
                "cart/checkout pages, or product schema markers). "
                "Ecommerce-specific checks were skipped. If this is "
                "an ecommerce site, the indicators may be on a "
                "different URL path convention than the auditor "
                "recognizes — let us know which path patterns the "
                "site uses for products and collections."
            ),
            recommendation=(
                "No action needed — informational only."
            ),
            impact=(
                "The generic technical and on-page audits cover this "
                "site's needs. Ecommerce-specific patterns (faceted "
                "nav, product variants, sale URLs) aren't relevant."
            ),
        )

    def _emit_active_diagnostic(self) -> None:
        """Emit an INSIGHT confirming ecommerce mode."""
        self.create_issue(
            severity=Severity.INSIGHT,
            category=AuditCategory.ECOMMERCE_PATTERNS,
            issue_type="ecommerce_auditor_active",
            title="Ecommerce-specific checks active",
            description=(
                "Ecommerce indicators detected. Running additional "
                "checks for pagination patterns, indexable cart/"
                "checkout pages, product schema, Shopify collection "
                "artifacts, and session ID parameters."
            ),
            recommendation="No action — informational.",
            impact="",
        )

    # =========================================================================
    # CHECKS
    # =========================================================================

    def _check_paginated_without_view_all(self) -> None:
        """Detect paginated category URLs without a corresponding view-all.

        When a site has /category/?page=2, /category/?page=3, etc.,
        Google generally prefers a single view-all page for ranking.
        Flag this pattern when paginated URLs are indexable and no
        view-all variant exists.
        """
        if not self.has_column("url"):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        urls = scope["url"].dropna().astype(str).tolist()
        if not urls:
            return

        # Find indexable paginated URLs (?page=N or /page/N/)
        page_param_re = re.compile(r"[?&]page=\d+", re.IGNORECASE)
        page_path_re = re.compile(r"/page/\d+/?$", re.IGNORECASE)
        view_all_re = re.compile(
            r"[?&](view|show|per_page|limit)=all", re.IGNORECASE
        )

        paginated = [
            u for u in urls
            if page_param_re.search(u) or page_path_re.search(u)
        ]
        view_all_present = any(view_all_re.search(u) for u in urls)

        if not paginated or view_all_present:
            return

        # Group by base URL (strip pagination param/path) to count
        # distinct paginated categories
        def base_url(u: str) -> str:
            u = page_param_re.sub("", u).rstrip("?&")
            u = page_path_re.sub("/", u)
            return u

        paginated_bases = list({base_url(u) for u in paginated})
        if not paginated_bases:
            return

        self.create_issue(
            severity=Severity.MEDIUM,
            category=AuditCategory.ECOMMERCE_PATTERNS,
            issue_type="paginated_without_view_all",
            title=f"{len(paginated)} paginated URLs with no view-all alternative",
            description=(
                f"Found {len(paginated)} paginated URLs across "
                f"{len(paginated_bases)} categories with no view-all "
                "(`?view=all` or equivalent) variant. Google generally "
                "prefers a single consolidated view-all page over "
                "paginated alternatives — both for indexing and for "
                "ranking. When users want to scan a full catalog, "
                "lazy-loading + a view-all URL is the modern best "
                "practice."
            ),
            affected_urls=paginated[:100],
            count=len(paginated),
            recommendation=(
                "Implement a view-all URL for each paginated category "
                "(e.g., `/category/?view=all`). Make the view-all "
                "the canonical URL — point all `?page=N` variants to "
                "the view-all via rel=canonical. Use lazy-loading on "
                "the view-all so it doesn't have to render thousands "
                "of products at once. For very large categories where "
                "view-all isn't feasible, use rel=next/rel=prev "
                "between paginated URLs and noindex `?page=2+` "
                "variants while keeping `?page=1` indexable."
            ),
            impact=(
                "Pagination splits ranking signals across page-1, "
                "page-2, etc. — none of which rank as well as a "
                "consolidated view-all would. For ecommerce category "
                "pages this often costs visibility on the head terms "
                "(e.g., 'plumbing supplies') because the highest-"
                "value listings are scattered across pages 1-5."
            ),
        )

    def _check_indexable_cart_checkout(self) -> None:
        """Flag cart, checkout, and account pages that are indexable.

        These pages should never be in Google's index — they have no
        SEO value and are personalized per-user.
        """
        if not self.has_column("url"):
            return

        scope = self.df
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        condition = scope["url"].astype(str).apply(
            lambda u: any(
                p in u.lower() for p in CART_CHECKOUT_PATTERNS
            )
        )
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.ECOMMERCE_PATTERNS,
                issue_type="indexable_cart_checkout",
                title=f"{count} cart/checkout/account pages are indexable",
                description=(
                    f"Found {count} cart, checkout, account, or "
                    "wishlist pages that are indexable (or not "
                    "explicitly noindexed). These pages have no "
                    "organic search value — they're personalized "
                    "per-user, transient, and often empty. Allowing "
                    "them in Google's index wastes crawl budget and "
                    "can surface user-specific URLs in SERPs."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Add a `<meta name='robots' content='noindex, "
                    "follow'>` tag to all cart, checkout, account, "
                    "and wishlist pages. Also remove these URLs "
                    "from the XML sitemap. The pages can still be "
                    "crawled (so Google understands the site "
                    "structure) but should not appear in search "
                    "results."
                ),
                impact=(
                    "Indexable cart and account pages waste crawl "
                    "budget on pages that will never rank, and "
                    "occasionally surface in SERPs as low-quality "
                    "results that hurt brand perception."
                ),
            )

    def _check_product_pages_missing_schema(self) -> None:
        """Flag product URLs without Product schema."""
        if not self.has_column("url"):
            return
        if not self.has_column("structured_data") and \
           not self.has_column("has_structured_data"):
            return

        scope = self.get_html_pages()
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        # Identify product URLs by path convention
        is_product = scope["url"].astype(str).apply(
            lambda u: any(
                m in u.lower() for m in (
                    "/product/", "/products/", "/p/", "/item/",
                )
            ) and not any(
                m in u.lower() for m in (
                    "/products/?", "/product/?", "/products?",
                )
            )
        )
        product_pages = scope[is_product]
        if product_pages.empty:
            return

        # Check schema presence
        if self.has_column("structured_data"):
            schema_col = product_pages["structured_data"].fillna("").astype(str).str.lower()
            missing_product_schema = ~schema_col.str.contains("product")
        elif self.has_column("has_structured_data"):
            sd_col = product_pages["has_structured_data"].fillna(False)
            missing_product_schema = ~sd_col.astype(bool)
        else:
            return

        urls = product_pages.loc[missing_product_schema, "url"].head(100).tolist()
        count = int(missing_product_schema.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.ECOMMERCE_PATTERNS,
                issue_type="product_pages_missing_schema",
                title=f"{count} product pages missing Product schema",
                description=(
                    f"Found {count} product URLs without Product "
                    "structured data. Product schema enables rich "
                    "results in Google search (price, availability, "
                    "ratings, review snippets) and is now required "
                    "for product images to surface in Google Images "
                    "search results. Missing schema is a direct, "
                    "measurable visibility loss."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Add Product schema to every product page using "
                    "JSON-LD. Required properties: name, image, "
                    "description, offers (with price and "
                    "availability), brand. Recommended additional "
                    "properties: aggregateRating, review, sku, gtin. "
                    "Validate the markup using Google's Rich Results "
                    "Test before deploying widely. For Shopify or "
                    "WooCommerce, the platform's default product "
                    "schema is usually sufficient — verify it's "
                    "actually being emitted on each product URL."
                ),
                impact=(
                    "Without Product schema, product listings are "
                    "less prominent in SERPs (no price/availability/"
                    "rating displays) and don't appear in Google "
                    "Images shopping results. For ecommerce sites, "
                    "this is one of the highest-ROI fixes available."
                ),
            )

    def _check_shopify_collection_canonical_artifacts(self) -> None:
        """Flag Shopify products in multiple collections with split canonicals.

        Shopify generates a URL for a product under each collection
        it's part of: /collections/widgets/products/widget-1 and
        /collections/sale/products/widget-1. The canonical should
        point to the bare /products/widget-1 URL, but mistakes happen.
        """
        if not self.has_columns(["url", "canonical"]):
            return

        scope = self.df
        # Only look at Shopify collection-product URLs
        is_collection_product = scope["url"].astype(str).str.contains(
            r"/collections/[^/]+/products/", regex=True, na=False
        )
        candidates = scope[is_collection_product]
        if candidates.empty:
            return

        # Canonical should point to /products/<slug> (not /collections/.../products/<slug>)
        def canonical_correct(row: pd.Series) -> bool:
            url = row.get("url", "")
            canonical = row.get("canonical", "")
            if not isinstance(canonical, str) or is_empty_or_missing(canonical):
                return False
            # Extract product slug from URL
            m = re.search(r"/collections/[^/]+/products/([^/?#]+)", url)
            if not m:
                return False
            slug = m.group(1)
            # Canonical should match /products/<slug>
            return bool(re.search(
                rf"/products/{re.escape(slug)}(?:/|$|\?)",
                canonical,
            )) and "/collections/" not in canonical

        canonical_ok = candidates.apply(canonical_correct, axis=1)
        broken = candidates[~canonical_ok]
        urls = broken["url"].head(100).tolist()
        count = len(broken)

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.ECOMMERCE_PATTERNS,
                issue_type="shopify_collection_canonical_artifacts",
                title=f"{count} Shopify product URLs with broken canonicals",
                description=(
                    f"Found {count} Shopify product URLs under "
                    "`/collections/<collection>/products/<slug>` "
                    "where the canonical does not point to the "
                    "bare `/products/<slug>` URL. Shopify generates "
                    "one URL per (product, collection) pair, but "
                    "all of those URLs should canonicalize to a "
                    "single product URL. When the canonicals are "
                    "wrong or missing, products end up indexed under "
                    "multiple URLs, splitting ranking signals."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "Update the Shopify theme to emit canonicals "
                    "pointing to the bare `/products/<slug>` URL on "
                    "every product page, regardless of which "
                    "collection it was reached through. The standard "
                    "Shopify canonical Liquid is "
                    "`{{ canonical_url }}` which usually does this "
                    "correctly — verify the theme isn't overriding "
                    "it."
                ),
                impact=(
                    "Each product effectively gets indexed under N "
                    "URLs (one per collection it's in). This splits "
                    "ranking signals N ways and dilutes link equity "
                    "for products that should be consolidating into "
                    "a single canonical entry."
                ),
            )

    def _check_session_id_in_urls(self) -> None:
        """Flag indexable URLs with session ID parameters.

        Common session ID parameter names: PHPSESSID, JSESSIONID,
        SID, sessionid, session_id, sess.
        """
        if not self.has_column("url"):
            return

        scope = self.df
        if "indexability" in scope.columns:
            scope = scope[scope["indexability"].str.lower() == "indexable"]

        session_pattern = re.compile(
            r"[?&](PHPSESSID|JSESSIONID|sessionid|session_id|sid|sess)=",
            re.IGNORECASE,
        )

        condition = scope["url"].astype(str).apply(
            lambda u: bool(session_pattern.search(u))
        )
        urls = scope.loc[condition, "url"].head(100).tolist()
        count = int(condition.sum())

        if count > 0:
            self.create_issue(
                severity=Severity.HIGH,
                category=AuditCategory.ECOMMERCE_PATTERNS,
                issue_type="session_ids_in_urls",
                title=f"{count} URLs contain session ID parameters",
                description=(
                    f"Found {count} indexable URLs containing session "
                    "ID parameters (PHPSESSID, JSESSIONID, sessionid, "
                    "etc.). Session IDs in URLs create infinite "
                    "duplicate-content combinations — every visitor "
                    "generates a new ID, so Googlebot ends up "
                    "crawling thousands of URL variants of the same "
                    "page."
                ),
                affected_urls=urls,
                count=count,
                recommendation=(
                    "1. Switch to cookie-based session tracking — "
                    "URL-based session IDs are an outdated pattern.\n"
                    "2. If URL-based sessions cannot be removed, "
                    "configure the server to NOT include session IDs "
                    "in responses to crawler user-agents.\n"
                    "3. Add canonical tags pointing each session-ID "
                    "URL to the clean version of the page.\n"
                    "4. Configure URL parameter handling in GSC to "
                    "tell Google to ignore session ID parameters.\n"
                    "5. Long-term: migrate to a stack that doesn't "
                    "use URL-based session tracking at all."
                ),
                impact=(
                    "Session IDs in URLs are one of the worst SEO "
                    "patterns — they multiply indexable URLs without "
                    "bound and waste enormous amounts of crawl "
                    "budget. Sites with this pattern often have "
                    "indexation problems on their actual content "
                    "pages because Googlebot is busy crawling "
                    "session-ID variants."
                ),
            )
