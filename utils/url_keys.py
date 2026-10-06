"""A join key that treats equivalent URL spellings as one page.

GSC, crawl exports and link exports spell the same page differently (trailing slash, www, http or https,
tracking parameters). Joining on the raw string reports a healthy page as missing. `url_key` collapses those
spellings for matching only; deliverables must still print the crawl's own URL, the one that serves 200.
"""

from __future__ import annotations

from urllib.parse import urlparse


def url_key(url: object) -> str:
    """Return a lowercase host-and-path key with no scheme, www, query, fragment or trailing slash."""
    if not isinstance(url, str) or not url.strip():
        return ""
    raw = url.strip()
    parsed = urlparse(raw if "//" in raw else f"//{raw}")
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    return f"{host}{path}".lower()


def host_key(url: object) -> str:
    """Return just the normalized host (no www), or an empty string."""
    key = url_key(url)
    return key.split("/", 1)[0] if key else ""
