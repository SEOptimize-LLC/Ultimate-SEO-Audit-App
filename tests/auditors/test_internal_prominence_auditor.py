"""InternalProminenceAuditor: priority pages whose internal links come from no click-earning page."""

import pandas as pd

from auditors.internal_prominence_auditor import (
    MIN_SOURCE_CLICKS,
    InternalProminenceAuditor,
)
from models.audit_result import AuditCategory, Severity

SITE = "https://www.x.com"


def _crawl(extra_rows=None):
    pages = ["/", "/blog/hub-a/", "/services/", "/services/drain/", "/services/water-heater/",
             "/about/", "/contact/", "/thank-you/"]
    rows = [{"url": f"{SITE}{p}", "content_type": "text/html", "status_code": 200,
             "indexability": "Indexable", "internal_links_in": 2} for p in pages]
    rows += extra_rows or []
    return pd.DataFrame(rows)


def _gsc(overrides=None):
    # page, clicks, impressions, position
    data = {
        "/blog/hub-a/": (50, 1000, 2.0),
        "/services/": (30, 800, 3.0),
        "/services/drain/": (5, 500, 8.0),          # priority, linked only from a no-click page
        "/services/water-heater/": (4, 400, 6.0),   # priority, linked from a click-earning page
        "/about/": (20, 600, 1.5),                  # not priority: position 1.5
        "/thank-you/": (0, 300, 9.0),               # utility page: excluded
    }
    data.update(overrides or {})
    return pd.DataFrame([
        {"query": "q", "page": f"{SITE}{p}", "clicks": c, "impressions": i, "position": pos}
        for p, (c, i, pos) in data.items()
    ])


def _anchors(extra=None):
    rows = [
        (f"{SITE}/contact/", f"{SITE}/services/drain/", "Content"),
        (f"{SITE}/blog/hub-a/", f"{SITE}/services/water-heater/", "Content"),
        (f"{SITE}/", f"{SITE}/services/", "Navigation"),
    ]
    rows += extra or []
    return pd.DataFrame([{"source_url": s, "target_url": t, "link_position": p} for s, t, p in rows])


def _by_type(issues):
    return {i.issue_type: i for i in issues}


def test_flags_the_page_with_no_click_sourced_link_and_lists_candidates():
    issues = _by_type(InternalProminenceAuditor(_crawl(), _anchors(), _gsc()).run_audit())
    flagged = issues["priority_pages_without_click_sourced_links"]
    assert flagged.affected_urls == [f"{SITE}/services/drain/"]
    assert flagged.severity == Severity.MEDIUM and flagged.category == AuditCategory.INTERNAL_LINKS
    pages = flagged.additional_data["pages"][0]
    assert [c["url"] for c in pages["candidates"]][:2] == [f"{SITE}/blog/hub-a/", f"{SITE}/services/"]
    assert pages["candidates"][0]["clicks"] == 50
    assert pages["position"] == 8.0 and pages["linking_pages"] == 1
    assert "Inferred" in flagged.description and "Documented" in flagged.description


def test_page_linked_from_a_click_earning_page_is_not_flagged_and_utility_pages_are_excluded():
    flagged = _by_type(InternalProminenceAuditor(_crawl(), _anchors(), _gsc()).run_audit())[
        "priority_pages_without_click_sourced_links"]
    assert f"{SITE}/services/water-heater/" not in flagged.affected_urls
    assert f"{SITE}/thank-you/" not in flagged.affected_urls


def test_navigation_links_do_not_count_as_prominence():
    anchors = _anchors([(f"{SITE}/", f"{SITE}/services/water-heater/", "Navigation")])
    anchors = anchors[anchors["source_url"] != f"{SITE}/blog/hub-a/"]  # remove the contextual link
    anchors.loc[len(anchors)] = [f"{SITE}/services/", f"{SITE}/services/water-heater/", "Navigation"]
    flagged = _by_type(InternalProminenceAuditor(_crawl(), anchors, _gsc()).run_audit())[
        "priority_pages_without_click_sourced_links"]
    assert f"{SITE}/services/water-heater/" in flagged.affected_urls


def test_nofollow_links_do_not_count():
    anchors = _anchors()
    anchors["follow"] = True
    anchors.loc[anchors["source_url"] == f"{SITE}/blog/hub-a/", "follow"] = False
    flagged = _by_type(InternalProminenceAuditor(_crawl(), anchors, _gsc()).run_audit())[
        "priority_pages_without_click_sourced_links"]
    assert f"{SITE}/services/water-heater/" in flagged.affected_urls


def test_url_spellings_join_across_exports():
    gsc = _gsc()
    gsc["page"] = gsc["page"].str.replace("https://www.", "http://", regex=False).str.rstrip("/")
    anchors = _anchors()
    anchors["target_url"] = anchors["target_url"].str.rstrip("/")
    flagged = _by_type(InternalProminenceAuditor(_crawl(), anchors, gsc).run_audit())[
        "priority_pages_without_click_sourced_links"]
    assert flagged.affected_urls == [f"{SITE}/services/drain/"]  # reported with the crawl's own URL


def test_position_is_impressions_weighted_across_query_rows():
    gsc = _gsc({"/services/drain/": (5, 100, 3.0)})
    gsc = pd.concat([gsc, pd.DataFrame([{"query": "q2", "page": f"{SITE}/services/drain/", "clicks": 0,
                                          "impressions": 100, "position": 30.0}])])
    issues = _by_type(InternalProminenceAuditor(_crawl(), _anchors(), gsc).run_audit())
    assert issues["priority_pages_without_click_sourced_links"].additional_data["pages"][0]["position"] == 16.5
    top_only = _by_type(InternalProminenceAuditor(_crawl(), _anchors(), _gsc({"/services/drain/": (5, 100, 3.0)})).run_audit())
    assert "priority_pages_without_click_sourced_links" not in top_only


def test_missing_inputs_say_so_instead_of_passing():
    for anchors, gsc, phrase in [(None, _gsc(), "anchor-text export"), (_anchors(), None, "Search Console")]:
        issues = _by_type(InternalProminenceAuditor(_crawl(), anchors, gsc).run_audit())
        assert list(issues) == ["internal_prominence_not_run"]
        assert phrase in issues["internal_prominence_not_run"].description
        assert "No priority page is flagged or cleared" in issues["internal_prominence_not_run"].description


def test_incomplete_anchor_export_is_unverified_not_flagged():
    anchors = _anchors()
    anchors = anchors[anchors["target_url"] != f"{SITE}/services/drain/"]  # export lacks drain's links
    issues = _by_type(InternalProminenceAuditor(_crawl(), anchors, _gsc()).run_audit())
    assert "priority_pages_without_click_sourced_links" not in issues
    assert issues["internal_prominence_unverified"].affected_urls == [f"{SITE}/services/drain/"]


def test_summary_states_thresholds_and_template_link_handling():
    summary = _by_type(InternalProminenceAuditor(_crawl(), _anchors(), _gsc()).run_audit())["internal_prominence_checked"]
    assert str(MIN_SOURCE_CLICKS) in summary.description and "Navigation and footer links were excluded" in summary.description
    no_pos = _anchors().drop(columns=["link_position"])
    note = _by_type(InternalProminenceAuditor(_crawl(), no_pos, _gsc()).run_audit())["internal_prominence_checked"]
    assert "no link-position column" in note.description


def test_no_priority_pages_gives_only_the_summary():
    gsc = _gsc({"/services/drain/": (5, 500, 1.2), "/services/water-heater/": (4, 400, 1.4)})
    issues = _by_type(InternalProminenceAuditor(_crawl(), _anchors(), gsc).run_audit())
    assert list(issues) == ["internal_prominence_checked"]
