"""Compare the live HTML of /coupons/, /specials/, and /specials-fireplace-utah/."""
from __future__ import annotations

import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DIR = "/tmp/comfort_coupons"


def extract_text(html: str) -> str:
    html = re.sub(r"<script[^>]*>.*?</script>", "", html,
                  flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html,
                  flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<nav[^>]*>.*?</nav>", "", html,
                  flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<footer[^>]*>.*?</footer>", "", html,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_coupon_links(html: str) -> list[str]:
    pattern = (
        r'href=["\']https://www\.comfortsolutionsutah\.com'
        r'(/coupons/[^"\'?#]+)'
    )
    matches = re.findall(pattern, html)
    return sorted(set(matches))


def find_specials_links(html: str) -> list[str]:
    pattern = (
        r'href=["\']https://www\.comfortsolutionsutah\.com'
        r'(/specials[^"\'?#]*)'
    )
    matches = re.findall(pattern, html)
    return sorted(set(matches))


def find_dollar_offers(text: str) -> list[str]:
    pattern = r"(\$\d{2,5}[^$\n]{0,80})"
    return re.findall(pattern, text)


for fname in ["coupons.html", "specials.html", "specials-fireplace-utah.html"]:
    path = os.path.join(DIR, fname)
    if not os.path.exists(path):
        print(f"MISSING: {path}")
        continue
    with open(path, encoding="utf-8") as f:
        html = f.read()
    text = extract_text(html)

    print(f"=== {fname} ===")
    print(f"  HTML bytes: {len(html)}")
    print(f"  Visible text bytes: {len(text)}")

    coupon_links = find_coupon_links(html)
    specials_links = find_specials_links(html)
    print(f"  Distinct /coupons/<slug>/ links: {len(coupon_links)}")
    for c in coupon_links[:15]:
        print(f"    {c}")
    print(f"  Distinct /specials/* links: {len(specials_links)}")
    for s in specials_links[:5]:
        print(f"    {s}")

    # Dollar offers visible in text
    offers = find_dollar_offers(text)
    print(f"  Dollar offers visible: {len(offers)}")
    for o in offers[:10]:
        print(f"    {o.strip()[:120]}")
    print()
