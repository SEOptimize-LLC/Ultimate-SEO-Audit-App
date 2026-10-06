"""Counting the distinct addresses and phone numbers a page lists, and fetching text for location pages."""

import pandas as pd

from utils.local_text_extract import extract_addresses, extract_phone_numbers
from utils.location_page_text import load_location_page_text
from utils.url_keys import host_key, url_key


def test_same_address_in_two_spellings_counts_once():
    text = "1234 S. State Street, Sandy, UT 84070 ... footer: 1234 South State St, Sandy UT 84070"
    assert len(extract_addresses(text)) == 1


def test_distinct_addresses_across_lines_count_separately():
    text = "Sandy: 1234 State Street\nSandy, UT 84070\nProvo: 55 North University Ave\nProvo, UT 84601"
    assert len(extract_addresses(text)) == 2


def test_headings_and_prices_are_not_addresses():
    text = "100 Reasons To Drive Better. Call us 12 Main Street today. Price $1,200 Way better, Place in Utah."
    assert extract_addresses(text) == set()


def test_phone_formats_and_tel_links_dedupe_to_one_number():
    text = "Call (801) 555-1234 or 801.555.1234 or [Call](tel:+18015551234) or +1 801-555-1234."
    assert extract_phone_numbers(text) == {"8015551234"}


def test_distinct_phone_numbers_counted_and_non_phones_ignored():
    text = "(801) 555-1234, 385-555-0100, order 2024-01-15, ref 123 456 7890, id 801-555-12345"
    assert extract_phone_numbers(text) == {"8015551234", "3855550100"}


def test_non_string_input_is_empty():
    assert extract_addresses(None) == set() and extract_phone_numbers(float("nan")) == set()


def test_url_key_ignores_scheme_www_slash_query_and_case():
    variants = ["https://www.Example.com/a/b/", "http://example.com/a/b", "example.com/a/b?utm=1#top"]
    assert {url_key(v) for v in variants} == {"example.com/a/b"}
    assert url_key("https://example.com/") == "example.com"
    assert host_key("https://www.example.com/x") == "example.com"
    assert url_key(None) == ""


# ---- load_location_page_text ------------------------------------------------

def _is_loc(url):
    return "/service-areas/" in str(url)


def _crawl(**extra):
    base = {
        "url": ["https://x.com/service-areas/sandy/", "https://x.com/service-areas/orem/",
                "https://x.com/about/", "https://x.com/service-areas/noindexed/"],
        "status_code": [200, 200, 200, 200],
        "content_type": ["text/html"] * 4,
        "indexability": ["Indexable", "Indexable", "Indexable", "Non-Indexable"],
    }
    base.update(extra)
    return pd.DataFrame(base)


def test_fetches_only_indexable_location_pages():
    seen = []

    def fake_fetch(urls):
        seen.extend(urls)
        return {u: "text" for u in urls}

    out = load_location_page_text(_crawl(), _is_loc, fetch=fake_fetch)
    assert sorted(seen) == ["https://x.com/service-areas/orem/", "https://x.com/service-areas/sandy/"]
    assert set(out) == set(seen)


def test_uses_a_body_text_column_without_fetching():
    df = _crawl(Content=["Sandy text", "", "About text", "x"])

    def boom(urls):
        raise AssertionError("must not fetch when a body column exists")

    out = load_location_page_text(df, _is_loc, fetch=boom)
    assert out == {"https://x.com/service-areas/sandy/": "Sandy text"}


def test_fetch_failure_returns_empty_so_the_auditor_reports_unchecked():
    def failing(urls):
        raise RuntimeError("fetch failed")

    assert load_location_page_text(_crawl(), _is_loc, fetch=failing) == {}


def test_no_url_column_or_no_location_pages_returns_empty():
    assert load_location_page_text(pd.DataFrame({"x": [1]}), _is_loc) == {}
    assert load_location_page_text(pd.DataFrame({"url": ["https://x.com/about/"]}), _is_loc) == {}


def test_suite_number_with_a_hash_does_not_hide_an_address():
    # Real format from a live client page: the suite marker sits between the street and the city.
    text = "Contact us: 8141 2nd St Suite #545, Downey, CA 90241. Also 12 Oak Avenue, Ste. B, Provo, UT 84601."
    assert extract_addresses(text) == {"8141 2nd street CA", "12 oak avenue UT"}
