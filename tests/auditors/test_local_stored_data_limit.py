"""LocalSEOAuditor: location pages that list more addresses or phone numbers than Google stores."""

import pandas as pd

from auditors.local_seo_auditor import MAX_STORED_LOCAL_ITEMS, LocalSEOAuditor
from models.audit_result import Severity

ADDR = "{n} Main Street, Sandy, UT 84070"


def _addresses(count):
    return " | ".join(f"{100 + i} Elm Street, Sandy, UT 84070" for i in range(count))


def _phones(count):
    return " ".join(f"(801) 555-{1000 + i}" for i in range(count))


def _df():
    urls = [
        "https://x.com/service-areas/sandy/",
        "https://x.com/service-areas/orem/",
        "https://x.com/service-areas/lehi/",
        "https://x.com/service-areas/",
        "https://x.com/about/",
    ]
    return pd.DataFrame({
        "url": urls,
        "content_type": ["text/html"] * 5,
        "status_code": [200] * 5,
        "indexability": ["Indexable"] * 5,
        "title": ["t"] * 5,
    })


def _types(issues):
    return {i.issue_type: i for i in issues}


def test_flags_pages_over_the_limit_and_names_the_documented_threshold():
    text = {
        "https://x.com/service-areas/sandy/": _addresses(6),
        "https://x.com/service-areas/orem/": f"{_addresses(2)} {_phones(5)}",
        "https://x.com/service-areas/lehi/": f"{_addresses(1)} {_phones(1)}",
    }
    issues = _types(LocalSEOAuditor(_df(), page_text=text).run_audit())
    flagged = issues["local_data_over_storage_limit"]
    assert set(flagged.affected_urls) == {"https://x.com/service-areas/sandy/", "https://x.com/service-areas/orem/"}
    assert flagged.severity == Severity.LOW
    assert "4 or fewer" in flagged.description and "Inferred" in flagged.description
    assert "https://x.com/service-areas/sandy/ (6 addresses" in flagged.description  # full URL, not truncated
    assert "location_page_text_unavailable" not in issues


def test_exactly_four_is_within_the_limit():
    text = {u: f"{_addresses(MAX_STORED_LOCAL_ITEMS)} {_phones(MAX_STORED_LOCAL_ITEMS)}"
            for u in ["https://x.com/service-areas/sandy/", "https://x.com/service-areas/orem/",
                      "https://x.com/service-areas/lehi/"]}
    issues = _types(LocalSEOAuditor(_df(), page_text=text).run_audit())
    assert "local_data_over_storage_limit" not in issues
    assert "local_data_within_storage_limit" in issues


def test_no_page_text_reports_unchecked_never_clean():
    issues = _types(LocalSEOAuditor(_df()).run_audit())
    gap = issues["location_page_text_unavailable"]
    assert len(gap.affected_urls) == 3 and "neither flagged nor cleared" in gap.description
    assert "local_data_within_storage_limit" not in issues
    assert "local_data_over_storage_limit" not in issues


def test_partial_text_checks_what_it_has_and_reports_the_rest():
    text = {"https://x.com/service-areas/sandy/": _addresses(6)}
    issues = _types(LocalSEOAuditor(_df(), page_text=text).run_audit())
    assert issues["local_data_over_storage_limit"].affected_urls == ["https://x.com/service-areas/sandy/"]
    assert len(issues["location_page_text_unavailable"].affected_urls) == 2


def test_text_keys_match_across_trailing_slash_and_www():
    text = {"http://www.x.com/service-areas/sandy": _addresses(6)}
    issues = _types(LocalSEOAuditor(_df(), page_text=text).run_audit())
    assert "https://x.com/service-areas/sandy/" in issues["local_data_over_storage_limit"].affected_urls


def test_hub_page_listing_many_locations_is_not_checked():
    text = {"https://x.com/service-areas/": _addresses(12)}
    issues = _types(LocalSEOAuditor(_df(), page_text=text).run_audit())
    assert "local_data_over_storage_limit" not in issues
    assert "https://x.com/service-areas/" not in issues["location_page_text_unavailable"].affected_urls


def test_same_address_repeated_in_header_and_footer_counts_once():
    block = "1234 S. State Street, Sandy, UT 84070"
    text = {u: f"{block} body {block} footer {block}" for u in
            ["https://x.com/service-areas/sandy/", "https://x.com/service-areas/orem/",
             "https://x.com/service-areas/lehi/"]}
    issues = _types(LocalSEOAuditor(_df(), page_text=text).run_audit())
    assert "local_data_over_storage_limit" not in issues
