"""Decide which URLs task 1.2 check 5 crawls, per client.

Two populations, resolved from the sitemap rather than guessed from URL shape:

  money pages   service and product pages. Not blog, not utility, not PPC.
  recent posts  the most recently published, by <lastmod>.

The previous version hardcoded `"/blog/" in url` and took the first 8 matches.
That found 0 posts on Education Walkthrough, whose 301 posts sit at the root
(`/teacher-coaching-blog/`), and "first 8" was never "recent" on any client
because <lastmod> was ignored entirely.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (compatible; SEOAudit/1.0)"}

# Never money pages, on any client. PPC landing pages are excluded per the
# project's own audit-workflow rule 7: they carry no organic value and inflate
# every count they appear in.
UTILITY = (
    "/ppc-", "ppc-", "/careers", "/privacy", "/terms", "/cookie", "/legal",
    "/thank-you", "/thanks", "/contact", "/about", "/testimonial", "/review",
    "/manual", "/financing", "/author/", "/tag/", "/category/", "/page/",
    "/cart", "/checkout", "/account", "/search", ".kml", ".xml", "/sitemap",
)


def _get(url: str, timeout: int = 30, tries: int = 4) -> str:
    """Fetch, retrying transient throttling.

    Client sites rate-limit. Snow returned 429 on 20 of 54 page requests and
    then on the sitemap itself, and both were written up as client findings.
    A 429 is our problem, so it is retried here rather than surfaced upward.
    """
    import random
    import time
    for attempt in range(tries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=timeout
            ).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (429, 503) or attempt == tries - 1:
                raise
            time.sleep(2 ** attempt + random.random())
    raise RuntimeError("unreachable")


def _entries(xml: str) -> list[tuple[str, str]]:
    """(loc, lastmod) for each <url> block. lastmod is '' when absent."""
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>(.*?)</loc>", block)
        if not loc:
            continue
        lm = re.search(r"<lastmod>(.*?)</lastmod>", block)
        out.append((loc.group(1).strip(), (lm.group(1)[:10] if lm else "")))
    return out


def collect(sitemap_url: str) -> dict[str, list[tuple[str, str]]]:
    """Every URL grouped by the child sitemap it came from.

    Flat sitemaps return a single group keyed by the sitemap's own filename, so
    both shapes are handled by the same caller.
    """
    body = _get(sitemap_url)
    if "<sitemapindex" not in body[:2000]:
        return {sitemap_url.split("/")[-1]: _entries(body)}

    kids = re.findall(r"<loc>(.*?)</loc>", body)

    def one(u: str) -> tuple[str, list[tuple[str, str]]]:
        try:
            return u.split("/")[-1].split("?")[0], _entries(_get(u))
        except Exception:
            return u.split("/")[-1].split("?")[0], []

    with ThreadPoolExecutor(max_workers=3) as pool:
        return dict(pool.map(one, kids))


def wp_recent_posts(site: str, n: int = 15) -> list[tuple[str, str]] | None:
    """(url, published_date) newest-first from the WordPress REST API.

    `<lastmod>` in a sitemap is last-MODIFIED, not published, and on these sites
    it is dominated by bulk edits: Education Walkthrough shows 108 posts sharing
    a July modification date and 13 sharing 2026-08-04. Selecting on it returns
    whatever was last re-saved, not what was last published.

    Returns None when the endpoint is absent (non-WordPress), so the caller can
    fall back to lastmod rather than losing the check entirely.
    """
    import json
    url = (f"{site.rstrip('/')}/wp-json/wp/v2/posts"
           f"?per_page={min(n, 100)}&orderby=date&order=desc&_fields=link,date")
    try:
        rows = json.loads(_get(url, timeout=25))
    except Exception:
        return None
    if not isinstance(rows, list) or not rows:
        return None
    return [(r["link"], r["date"][:10]) for r in rows if r.get("link")]


def shopify_recent_posts(site: str, blog: str = "news",
                         n: int = 15) -> list[tuple[str, str]] | None:
    """(url, published_date) from a Shopify blog's Atom feed.

    Shopify has no open posts API, but every blog exposes `/blogs/<blog>.atom`
    with a real <published> date per entry. Same reason as the WordPress path:
    sitemap lastmod is modification, not publication.
    """
    try:
        x = _get(f"{site.rstrip('/')}/blogs/{blog}.atom", timeout=25)
    except Exception:
        return None
    out = []
    for e in re.findall(r"<entry>(.*?)</entry>", x, re.S):
        link = re.search(r'<link[^>]*href="([^"]+)"', e)
        pub = re.search(r"<published>(.*?)</published>", e)
        if link and pub:
            out.append((link.group(1), pub.group(1)[:10]))
    return out[:n] or None


def scope_urls(sitemap_url: str, site: str, cfg: dict) -> set[str]:
    """Every URL in scope for this client: all money pages, ALL posts, homepage.

    `select()` returns the crawl TARGETS, which caps posts at the 15 newest
    because check 5 spot-checks recent publishing. This returns the full scope
    instead, for the indexation audit, which has to cover everything the owner
    considers part of the site.

    Anything outside it is excluded: Cudio's `/jobs/` and Snow's `/pages/` are
    in the sitemap but are not services, products, collections or posts, and
    counting them inflated every "not indexed" figure with URLs nobody asked
    about. Returned normalised without trailing slashes so callers can match
    against sitemap URLs directly.
    """
    crawl = cfg.get("crawl") or {}
    groups = collect(sitemap_url)
    post_pat = crawl.get("posts") or ["post-sitemap"]
    money_pat = crawl.get("money") or ["page-sitemap"]
    extra_ex = [x.lower() for x in (crawl.get("exclude") or [])]
    drop = {u.rstrip("/") for u in (crawl.get("money_exclude") or [])}
    allow = crawl.get("money_pages")

    keep: set[str] = {site.rstrip("/")}
    for name, entries in groups.items():
        for loc, _ in entries:
            low = loc.lower()
            if any(x in low for x in extra_ex):
                continue
            if _match(name, loc, post_pat):
                keep.add(loc.rstrip("/"))
            elif allow is None and _match(name, loc, money_pat) \
                    and not any(x in low for x in UTILITY) \
                    and loc.rstrip("/") not in drop:
                keep.add(loc.rstrip("/"))
    if allow:
        keep |= {u.rstrip("/") for u in allow}
    return keep


def _match(name: str, url: str, patterns: list[str]) -> bool:
    """A pattern hits either the child sitemap filename or the URL path."""
    return any(p in name or p in url for p in patterns)


def select(sitemap_url: str, site: str, cfg: dict,
           n_posts: int = 15) -> tuple[list[str], list[str], dict]:
    crawl = cfg.get("crawl") or {}

    # An explicit allowlist wins outright. A blocklist cannot anticipate every
    # client's junk pages (EW's sitemap yields /leave-a-review-3/,
    # /demo-thank-you/, /affiliate-disclosure/); an allowlist cannot be wrong.
    explicit = crawl.get("money_pages")

    groups = collect(sitemap_url)
    post_pat = crawl.get("posts") or ["post-sitemap"]
    money_pat = crawl.get("money") or ["page-sitemap"]
    extra_ex = crawl.get("exclude") or []

    def excluded(u: str) -> bool:
        low = u.lower()
        return any(x in low for x in UTILITY) or any(x in low for x in extra_ex)

    posts: list[tuple[str, str]] = []
    money: list[str] = []
    for name, entries in groups.items():
        for loc, lastmod in entries:
            if any(x in loc.lower() for x in extra_ex):
                continue
            if _match(name, loc, post_pat):
                posts.append((loc, lastmod))
            elif _match(name, loc, money_pat) and not excluded(loc):
                money.append(loc)

    # Most recently published first. Entries without <lastmod> sort last rather
    # than being dropped: no date is not the same as old.
    if explicit:
        money = list(explicit)

    # Owner-supplied exclusions, matched on the exact URL. Some clients are
    # easier to describe as "the page sitemap minus these" than as a list of
    # hundreds of keepers, and the generic UTILITY blocklist cannot know that
    # Beehive's /beehive-new-elements/, /master-plumbers/ and /our-work-gallery/
    # are not service pages. Trailing slashes are normalised so the list can be
    # pasted straight from a sitemap or a browser.
    drop = {u.rstrip("/") for u in (crawl.get("money_exclude") or [])}
    if drop:
        money = [u for u in money if u.rstrip("/") not in drop]

    # The homepage is a money page on every site and matches no path pattern.
    if not any(u.rstrip("/") == site.rstrip("/") for u in money):
        money.append(site)

    # Prefer real publish dates. Fall back to lastmod only where the REST API
    # is absent, and say which was used so the sheet never implies more
    # precision than the source supports.
    feed = wp_recent_posts(site, n_posts)
    src_name = "wp published date"
    if not feed:
        blog = (crawl.get("shopify_blog") or "news")
        feed = shopify_recent_posts(site, blog, n_posts)
        src_name = "shopify atom published date"
    if feed:
        recent = [u for u, _ in feed[:n_posts]]
        post_src, newest = src_name, feed[0][1]
        oldest = feed[min(n_posts, len(feed)) - 1][1]
    else:
        posts.sort(key=lambda t: (t[1] != "", t[1]), reverse=True)
        recent = [u for u, _ in posts[:n_posts]]
        post_src = "sitemap lastmod (no WP API; last-MODIFIED, not published)"
        newest = posts[0][1] if posts else ""
        oldest = posts[min(n_posts, len(posts)) - 1][1] if posts else ""

    stats = {"money_source": "allowlist" if explicit else "sitemap",
             "post_source": post_src,
             "groups": {k: len(v) for k, v in groups.items()},
             "posts_total": len(posts), "money_total": len(money),
             "newest": newest, "oldest_taken": oldest}
    return sorted(set(money)), recent, stats
