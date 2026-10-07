"""1.5 workbook scripts: the URL-variant, note-text and lookback defects found on Bart's October run.

Each test pins a defect that reached a client sheet, or nearly did:
  * all_pages() let a 3-impression unslashed stub overwrite a 10,985-impression page;
  * page_queries() looked a page up by exact URL, so a page recorded without its trailing slash lost
    the traffic Search Console files under the slashed spelling;
  * the notes quoted last month's whole target cell, and called a page "no impressions at all" when it
    only had no recorded target query.
"""
import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fill_1_5_section_a as F  # noqa: E402
import task_1_5 as T  # noqa: E402
import url_cooldown as UC  # noqa: E402


class FakeSvc:
    """Search Console stand-in that returns canned rows and records the request body."""

    def __init__(self, rows):
        self.rows, self.bodies = rows, []

    def searchanalytics(self):
        return self

    def query(self, siteUrl, body):  # noqa: N803 - mirrors the API
        self.bodies.append(body)
        return self

    def execute(self):
        return {"rows": self.rows}


def _row(page, clicks, impr, pos):
    return {"keys": [page], "clicks": clicks, "impressions": impr, "position": pos}


def test_all_pages_sums_slashed_and_unslashed_spellings():
    svc = FakeSvc([
        _row("https://x.com/blog/a/", 76, 10985, 6.0),
        _row("https://x.com/blog/a", 0, 3, 40.0),        # the stub that used to win
        _row("https://x.com/blog/a/#toc-1", 0, 12, 6.5),  # an anchor variant
    ])
    page = F.all_pages(svc, "https://x.com/", dt.date(2026, 9, 1), dt.date(2026, 9, 30))["https://x.com/blog/a"]
    assert page["clicks"] == 76 and page["impressions"] == 11000


def test_page_queries_matches_both_spellings_of_the_page():
    svc = FakeSvc([])
    F.page_queries(svc, "https://x.com/", "https://x.com/blog/a", dt.date(2026, 9, 1), dt.date(2026, 9, 30))
    flt = svc.bodies[0]["dimensionFilterGroups"][0]["filters"][0]
    assert flt["operator"] == "includingRegex" and flt["expression"] == r"^https://x\.com/blog/a/?(?:#.*)?$"
    svc2 = FakeSvc([])
    F.page_queries(svc2, "https://x.com/", "https://x.com/blog/a/", dt.date(2026, 9, 1), dt.date(2026, 9, 30))
    assert svc2.bodies[0]["dimensionFilterGroups"][0]["filters"][0]["expression"] == flt["expression"]


@pytest.mark.parametrize("cell,expected", [
    ("commercial paving ann arbor \n2. asphalt paving company ann arbor \n3. x", "commercial paving ann arbor"),
    ("1. furnace repair salt lake city (116 impr)", "furnace repair salt lake city"),
    ("NO NON-BRANDED TARGET QUALIFIES ON THIS PAGE THIS MONTH\n\n- reasoning", ""),
    ("", ""),
    (None, ""),
])
def test_target_label_takes_one_query_and_ignores_headings(cell, expected):
    assert F.target_label(cell) == expected


def test_brand_queries_are_dropped_across_spellings():
    brands = F.brand_keys({"brand_token": "bart's asphalt"})
    rows = {"barts asphalt": 1, "bart's asphalt": 2, "asphalt paving ann arbor": 3}
    assert set(F.without_brand(rows, brands)) == {"asphalt paving ann arbor"}
    assert F.without_brand(rows, set()) == rows


def test_ctr_curve_keeps_only_bands_with_enough_impressions():
    sd = [{"pos": 4.5, "clicks": 3, "impr": 500}, {"pos": 9.1, "clicks": 1, "impr": 100}]
    assert T.ctr_curve_text(sd) == "pos 4-5 0.60%"
    assert T.ctr_curve_text([]) == "n/a"


def test_one_to_five_lookback_is_six_months_and_the_shared_cooldown_is_unchanged():
    assert UC.CANDIDATE_LOOKBACK_MONTHS == 6 and UC.COOLDOWN_MONTHS == 3
    today = dt.date(2026, 10, 6)
    assert UC.in_window("2026_04", today, UC.CANDIDATE_LOOKBACK_MONTHS)
    assert not UC.in_window("2026_03", today, UC.CANDIDATE_LOOKBACK_MONTHS)
    assert not UC.in_window("2026_06", today)  # the 2.3 cooldown still stops at three months


# --- the work-history gate follows redirects --------------------------------------------------
import run_1_5 as R  # noqa: E402


def _stub_pages(monkeypatch, table):
    monkeypatch.setattr(R, "_SECOND_PASS_WAIT", 0)
    monkeypatch.setattr(R, "_resolve", lambda u: table[u])


def test_worked_url_that_moved_is_blocked_at_its_new_address(monkeypatch):
    old = "https://x.com/plumbing/drain-cleaning/"
    _stub_pages(monkeypatch, {old: {"status": 200, "final": "https://x.com/plumbing/sewer-and-drains/drain-cleaning/?a=1"}})
    got = R._with_destinations({old})
    assert "https://x.com/plumbing/sewer-and-drains/drain-cleaning" in got and old in got


def test_worked_url_that_is_gone_adds_nothing_and_does_not_stop_the_gate(monkeypatch):
    old = "https://x.com/old/"
    _stub_pages(monkeypatch, {old: {"status": 404, "final": old}})
    assert R._with_destinations({old}) == {old}


@pytest.mark.parametrize("page", [None, {"status": 403, "final": "u"}, {"status": 503, "final": "u"}])
def test_worked_url_that_cannot_be_read_stops_the_gate(monkeypatch, page):
    _stub_pages(monkeypatch, {"https://x.com/a/": page})
    with pytest.raises(R.GateUnavailable):
        R._with_destinations({"https://x.com/a/"})


def test_verifier_matches_a_url_recorded_with_a_trailing_slash_in_both_spellings():
    import verify_1_5 as V
    rx = V.Pull(FakeSvc([]), "https://x.com/").rx
    assert rx("https://x.com/a/b/") == rx("https://x.com/a/b") == r"^https://x\.com/a/b/?(?:#.*)?$"


def test_page_queries_sums_the_address_a_page_moved_from():
    svc = FakeSvc([])
    F.page_queries(svc, "https://x.com/", "https://x.com/new/a/", dt.date(2026, 9, 1), dt.date(2026, 9, 30),
                   also=("https://x.com/old/a",))
    assert svc.bodies[0]["dimensionFilterGroups"][0]["filters"][0]["expression"] == r"^(?:https://x\.com/new/a|https://x\.com/old/a)/?(?:#.*)?$"


def test_combine_adds_clicks_and_weights_position_by_impressions():
    got = F.combine({"clicks": 1, "impressions": 100, "position": 10.0}, None,
                    {"clicks": 3, "impressions": 300, "position": 20.0})
    assert got["clicks"] == 4 and got["impressions"] == 400 and got["position"] == 17.5
    assert F.combine(None, None) is None


def test_landing_follows_a_redirect_and_refuses_an_unreadable_url(monkeypatch):
    pages = {"https://x.com/old/": {"status": 200, "final": "https://x.com/new/?utm=1"},
             "https://x.com/gone/": {"status": 404, "final": "https://x.com/gone/"},
             "https://x.com/blocked/": {"status": 403, "final": "u"}}
    monkeypatch.setattr(F.R, "_resolve", lambda u: pages[u])
    assert F.landing("https://x.com/old/") == "https://x.com/new/"
    assert F.landing("https://x.com/gone/") == "https://x.com/gone/"
    with pytest.raises(RuntimeError):
        F.landing("https://x.com/blocked/")


def test_candidate_exclude_dollar_names_one_address_and_plain_patterns_stay_substrings():
    cfg = {"crawl": {"candidate_exclude": ["https://x.com$", "/locations"]}}
    assert R._excluded("https://x.com", cfg) and R._excluded("https://x.com/", cfg)
    assert not R._excluded("https://x.com/pricing", cfg)
    assert R._excluded("https://x.com/locations/dtc", cfg)


def test_brand_queries_are_recognised_across_spellings_and_login_is_a_brand_query():
    brands = R._brand_keys({"brand_token": "education walkthrough"})
    assert R._is_brand("education walkthrough login", brands)
    assert R._is_brand("Education-Walkthrough app", brands)
    assert not R._is_brand("classroom walkthrough template", brands)
    assert not R._is_brand("anything", set())


def test_repeat_checker_follows_a_moved_url_and_adds_the_scheme_canon_drops(monkeypatch):
    import check_1_5_repeats as C
    seen = []

    def fake(u):
        seen.append(u)
        return {"status": 200, "final": "https://x.com/new/a/?q=1"}
    monkeypatch.setattr(C.R, "_resolve", fake)
    assert C.landing("x.com/old/a") == C.canon("https://x.com/new/a")
    assert seen == ["https://x.com/old/a"]
    monkeypatch.setattr(C.R, "_resolve", lambda u: {"status": 403, "final": u})
    with pytest.raises(C.ReadFailed):
        C.landing("x.com/old/a")


def test_compose_makes_label_and_bullets_one_sentence_each_and_drops_empty_blocks():
    import sheets_io as S
    got = S.compose(("Action", ["Name one owner."]), ("Why", "Three URLs touch it (269 impressions, position 15.3). The title stays."),
                    ("Empty", []))
    assert got == "ACTION\n• Name one owner.\n\nWHY\n• Three URLs touch it (269 impressions, position 15.3).\n• The title stays."
    assert S.is_formatted(got) and not S.is_formatted("word " * 60)
    assert S.is_formatted("short note")


def test_section_a_notes_never_carry_a_retired_task_number():
    import inspect
    src = inspect.getsource(F.build)
    assert 'd["task"]' not in src and "quick win" not in src


def test_only_cells_that_are_pages_count_as_worked_not_prose_that_mentions_one():
    import worked_urls as W
    assert W.is_url_cell("https://x.com/a/")
    assert W.is_url_cell("• https://x.com/a/\n• https://x.com/b/")
    assert not W.is_url_cell("178 URLs, 58% of the sitemap. Every instance points at https://x.com/service-areas/lehi-ut/ and")
    assert W.urls_in([["https://x.com/a/", "points at https://x.com/b/ for every page in the template"]], "x.com") == {"x.com/a"}


def test_a_cell_that_is_only_urls_is_not_a_paragraph():
    import sheets_io as S
    assert S.is_formatted("\n".join(f"https://example.com/some/long/path/number-{i}/" for i in range(6)))
    assert not S.is_formatted("See https://example.com/a/ and then " + "word " * 40)
