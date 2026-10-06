"""url_cooldown: one 90-day cooldown across the merged 2.3 tab (decision D1).

Sheets are faked in memory (tests/scripts/fake_sheets.py); nothing touches the
network.
"""
from datetime import date

import pytest

import url_cooldown as uc
from fake_sheets import FakeSheets, new_layout_tab

A = "https://client.example/a/"
B = "https://client.example/b/"
C = "https://client.example/c/"
D = "https://client.example/d/"
E = "https://client.example/e/"
OCT_5 = date(2026, 10, 5)


# --- old-layout workbook builders ------------------------------------------

def refresh_log(rows):
    """rows: [(url, date_done)] -> an old "2.3-3.1 Refresh Log" grid."""
    hdr = ["ClickUp Task", "Page URL", "Target Queries", "Baseline Clicks",
           "Baseline Impr", "Baseline Pos", "AI Cited (1.6)?", "Outdated Cut",
           "Answer-First Restructure", "Info Gain Added (what?)",
           "Title + Meta Rewritten", "Schema Valid", "Outbound Links Updated",
           "Keywords → Position Tracking (tag)", "Live / Staged Link",
           "Date Done"]
    grid = [["2.3 / 2.4 / 3.1 — Optimize Target Pages"], ["rules"], [],
            hdr]
    for url, done in rows:
        r = ["2.3", url] + [""] * 14
        r[15] = done
        grid.append(r)
    grid += [[], ["Unviable mid-work? Stop and route"]]
    return grid


def quick_wins(rows):
    """rows: [(url, date_live)]"""
    hdr = ["Page URL", "Old Title", "New Title", "New Meta Description",
           "Baseline Pos", "Baseline CTR", "Date Live",
           "Primary Keyword (track in SEMrush)", "-> Position Tracking (Y)"]
    grid = [["2.5 Rewrite Titles/Metas"], ["rules"], [], hdr]
    for url, live in rows:
        grid.append([url, "old", "new", "meta", "8", "0.1%", live])
    return grid


def page_opt(rows):
    """rows: [(url, status)] -> the September " Page Optimization" grid,
    with its header row printed twice like the real workbooks."""
    hdr = ["Task", "Page", "URL", "What To Change", "Currently On The Page",
           "Use This Instead", "Why It Matters", "Owner", "Status"]
    grid = [["Client - Page Optimization"], ["rules"], [], list(hdr), list(hdr)]
    for url, status in rows:
        grid.append(["2.3", "p", url, "Title tag", "x", "y", "z", "SEO VA",
                     status])
    return grid


def old_workbook(rl=(), qw=(), po=()):
    return {"2.3-3.1 Refresh Log": refresh_log(rl),
            "2.5 Quick Wins": quick_wins(qw),
            " Page Optimization": page_opt(po),
            "3.2 Internal Links": [["3.2"], [], [], ["Source URL"], [A]]}


def page_row(typ, url, change="", live=""):
    return [typ, "page", url, "", "", "", change, live, ""]


def change_row(typ, url, what, status, done=""):
    return [typ, "page", url, what, "cur", "use", "why", "Roger / VA", status,
            done]


@pytest.fixture
def fake(monkeypatch):
    def make(workbooks):
        f = FakeSheets(workbooks)
        f.install(monkeypatch)
        return f
    return make


# --- month window -----------------------------------------------------------

class TestWindow:
    def test_three_prior_months_are_inside(self):
        assert uc.in_window("2026_09", OCT_5)
        assert uc.in_window("2026_08", OCT_5)
        assert uc.in_window("2026_07", OCT_5)

    def test_older_is_outside_and_so_is_the_current_or_a_future_month(self):
        assert not uc.in_window("2026_06", OCT_5)
        assert not uc.in_window("2026_10", OCT_5)
        assert not uc.in_window("2026_11", OCT_5)

    def test_august_work_returns_in_december(self):
        assert uc.in_window("2026_08", date(2026, 11, 20))
        assert not uc.in_window("2026_08", date(2026, 12, 1))

    def test_unparseable_key_is_never_inside(self):
        assert not uc.in_window("sept", OCT_5)

    def test_prior_sheet_ids_unchanged(self):
        cfg = {"sheet_id": "now", "sheet_id_2026_09": "s9", "sheet_id_x": ""}
        assert uc.prior_sheet_ids(cfg) == {"2026_09": "s9"}


class TestTabKind:
    @pytest.mark.parametrize("name,kind", [
        ("2.3 Page Optimizations", "pages"),
        ("2.3-3.1 Refresh Log", "refresh_log"),
        ("2.5 Quick Wins", "quick_wins"),
        (" Page Optimization", "page_opt"),
        ("3.1 Internal Links", None),
        ("3.2 Internal Links", None),
        ("2.1 Technical Fixes", None),
    ])
    def test_kind(self, name, kind):
        assert uc.tab_kind(name) == kind


# --- parsers ----------------------------------------------------------------

class TestParsers:
    def test_refresh_log_done_means_date_done(self):
        got = uc.parse_refresh_log(refresh_log([(A, ""), (B, "2026-09-20")]))
        assert [(u, f) for u, f, _ in got] == [(A, False), (B, True)]

    def test_refresh_log_stops_at_the_unviable_block(self):
        grid = refresh_log([(A, "")]) + [["2.3", C]]
        assert [u for u, _, _ in uc.parse_refresh_log(grid)] == [A]

    def test_refresh_log_header_drift_fails_loudly(self):
        grid = refresh_log([(A, "")])
        grid[3][15] = "Finished"
        with pytest.raises(ValueError):
            uc.parse_refresh_log(grid)

    def test_quick_wins_done_means_date_live(self):
        got = uc.parse_quick_wins(quick_wins([(A, "09/08/2026"), (B, "")]))
        assert [(u, f) for u, f, _ in got] == [(A, True), (B, False)]

    def test_page_opt_is_finished_only_when_no_row_is_open(self):
        grid = page_opt([(A, "Live"), (A, "To do"), (B, "Live"),
                         (B, "No change needed"), (C, "")])
        got = {u: f for u, f, _ in uc.parse_page_opt(grid)}
        assert got == {A: False, B: True, C: False}

    def test_page_opt_header_rows_are_not_data(self):
        assert uc.parse_page_opt(page_opt([])) == []

    def test_pages_tab_finished_needs_evidence_and_no_open_change(self):
        from page_opt_tab import parse_changes, parse_pages
        pages = parse_pages([
            page_row("Quick Win", A, "Done", "2026-10-09"),
            page_row("Refresh", B, "Done", "2026-10-09"),
            page_row("Refresh", C, "No change needed"),
            page_row("Refresh", D),
        ], 6)
        changes = parse_changes([
            change_row("Refresh", B, "Page content", "To do"),
            change_row("Refresh", D, "Page content", "Done", "2026-10-10"),
        ], 20)
        got = {u: f for u, f, _ in uc.parse_pages_tab(pages, changes)}
        assert got == {A: True, B: False, C: True, D: True}


# --- decide(): the carryover exemption ---------------------------------------

class TestDecide:
    def test_unfinished_carryover_from_last_month_is_exempt(self):
        blocked, exempt = uc.decide({"a": [(1, False, ["2026_09 r5"])]})
        assert blocked == {} and list(exempt) == ["a"]

    def test_finished_last_month_blocks(self):
        blocked, exempt = uc.decide({"a": [(1, True, ["2026_09 r5"])]})
        assert list(blocked) == ["a"] and exempt == {}

    def test_unfinished_two_months_back_blocks(self):
        # Never carried into last month, so it is not a carryover.
        blocked, _ = uc.decide({"a": [(2, False, ["2026_08 r5"])]})
        assert list(blocked) == ["a"]

    def test_shipped_earlier_then_unfinished_again_blocks(self):
        hist = {"a": [(2, True, ["2026_08 r5"]), (1, False, ["2026_09 r5"])]}
        blocked, exempt = uc.decide(hist)
        assert list(blocked) == ["a"] and exempt == {}

    def test_unfinished_in_both_months_is_one_carryover_chain(self):
        hist = {"a": [(2, False, ["2026_08 r5"]), (1, False, ["2026_09 r5"])]}
        blocked, exempt = uc.decide(hist)
        assert blocked == {} and list(exempt) == ["a"]

    def test_exemption_is_one_constant(self):
        hist = {"a": [(1, False, ["2026_09 r5"])]}
        blocked, exempt = uc.decide(hist, carryover_exempt=False)
        assert list(blocked) == ["a"] and exempt == {}
        assert uc.CARRYOVER_EXEMPT is True
        assert uc.COOLDOWN_MONTHS == 3


# --- reading a whole workbook, old layout and new ----------------------------

class TestReadWorkbook:
    def test_old_layout_reads_all_three_tabs_and_not_internal_links(self, fake):
        f = fake({"s9": old_workbook(rl=[(A, "")], qw=[(B, "09/08/2026")],
                                     po=[(C, "Live")])})
        got = uc._read_workbook("s9", pause=0)
        assert {(u, fin) for u, fin, _, _ in got} == {
            (uc.canon(A), False), (uc.canon(B), True), (uc.canon(C), True)}
        # the 3.2 Internal Links tab lists A as a source URL: never counted
        assert all("Internal" not in tab for _, _, tab, _ in got)
        assert f.writes == []

    def test_new_layout_reads_the_pages_section_only(self, fake):
        grid = new_layout_tab(
            pages=[page_row("Quick Win", A, "Done", "2026-10-09"),
                   page_row("Refresh", B)],
            changes=[change_row("Refresh", B, "Page content", "To do"),
                     # a URL mentioned only in a change row's text is not a page
                     change_row("Refresh", B, "Internal links", "To do")])
        fake({"s10": {"2.3 Page Optimizations": grid}})
        got = {(u, fin) for u, fin, _, _ in uc._read_workbook("s10", pause=0)}
        assert got == {(uc.canon(A), True), (uc.canon(B), False)}

    def test_an_unreadable_tab_raises_rather_than_passing_quietly(self, fake):
        wb = old_workbook(rl=[(A, "")])
        wb["2.3-3.1 Refresh Log"][3][15] = "Finished"      # header drift
        fake({"s9": wb})
        with pytest.raises(uc.CooldownUnreadable) as e:
            uc._read_workbook("s9", pause=0)
        assert "2.3-3.1 Refresh Log" in str(e.value)

    def test_an_errors_list_collects_the_failure_and_reads_the_rest(
            self, fake, capsys):
        wb = old_workbook(rl=[(A, "")], qw=[(B, "09/08/2026")])
        wb["2.3-3.1 Refresh Log"][3][15] = "Finished"      # header drift
        fake({"s9": wb})
        errors = []
        got = uc._read_workbook("s9", pause=0, errors=errors)
        assert [u for u, *_ in got] == [uc.canon(B)]
        assert len(errors) == 1 and "could not read" in errors[0]
        assert "NOT counted" in capsys.readouterr().err


# --- family_state: the merged cooldown across layouts ------------------------

class TestFamilyState:
    def cfg(self, **sheets):
        return {"name": "Client", "folder": "Clients/X",
                **{f"sheet_id_{k}": v for k, v in sheets.items()}}

    def test_october_reads_two_old_layout_months(self, fake):
        fake({
            "s9": old_workbook(rl=[(A, "2026-09-20"), (B, "")],
                               qw=[(C, "09/08/2026")]),
            "s8": old_workbook(rl=[(D, "2026-08-21")], po=[(E, "Live")]),
            "s6": old_workbook(rl=[("https://client.example/old/", "x")]),
        })
        blocked, exempt = uc.family_state(
            self.cfg(**{"2026_09": "s9", "2026_08": "s8", "2026_06": "s6"}),
            OCT_5, pause=0)
        # A and C shipped in September, D and E in August: all blocked.
        assert set(blocked) == {uc.canon(x) for x in (A, C, D, E)}
        # B sat unfinished on September's log: carried over, exempt.
        assert set(exempt) == {uc.canon(B)}
        # June is outside the window.
        assert uc.canon("https://client.example/old/") not in blocked
        assert "2026_09 2.3-3.1 Refresh Log r5" in blocked[uc.canon(A)]

    def test_december_reads_new_layout_then_old(self, fake):
        new = new_layout_tab(
            pages=[page_row("Quick Win", A, "Done", "2026-11-12"),
                   page_row("Refresh", B)],
            changes=[change_row("Refresh", B, "Page content", "To do")])
        fake({"s11": {"2.3 Page Optimizations": new},
              "s10": {"2.3 Page Optimizations": new_layout_tab(
                  pages=[page_row("Refresh", C, "Done", "2026-10-09")],
                  changes=[])},
              "s9": old_workbook(rl=[(D, "2026-09-20")])})
        blocked, exempt = uc.family_state(
            self.cfg(**{"2026_11": "s11", "2026_10": "s10", "2026_09": "s9"}),
            date(2026, 12, 3), pause=0)
        assert set(blocked) == {uc.canon(x) for x in (A, C, D)}
        assert set(exempt) == {uc.canon(B)}

    def test_exemption_off_makes_a_carryover_block(self, fake, monkeypatch):
        fake({"s9": old_workbook(rl=[(B, "")])})
        cfg = self.cfg(**{"2026_09": "s9"})
        blocked, exempt = uc.family_state(cfg, OCT_5, pause=0)
        assert blocked == {} and set(exempt) == {uc.canon(B)}
        monkeypatch.setattr(uc, "CARRYOVER_EXEMPT", False)
        blocked, exempt = uc.family_state(cfg, OCT_5, pause=0)
        assert set(blocked) == {uc.canon(B)} and exempt == {}


class TestPublicLookups:
    def patch_registry(self, monkeypatch, cfg):
        monkeypatch.setattr(uc, "_registry", lambda: {"client": cfg})

    def test_blocked_2_3_applies_the_family_rule(self, fake, monkeypatch):
        fake({"s9": old_workbook(rl=[(A, "2026-09-20"), (B, "")])})
        self.patch_registry(monkeypatch, {
            "name": "Client", "folder": "Clients/X", "sheet_id_2026_09": "s9"})
        got = uc.blocked("client", "2.3", pause=0, today=OCT_5)
        assert set(got) == {uc.canon(A)}
        assert set(uc.carried_over("client", pause=0, today=OCT_5)) == {
            uc.canon(B)}

    def test_blocked_fails_closed_when_a_prior_tab_cannot_be_read(
            self, fake, monkeypatch):
        wb = old_workbook(rl=[(A, "2026-09-20")])
        wb["2.5 Quick Wins"][3][6] = "Went Live"             # header drift
        fake({"s9": wb})
        self.patch_registry(monkeypatch, {
            "name": "Client", "folder": "Clients/X", "sheet_id_2026_09": "s9"})
        with pytest.raises(uc.CooldownUnreadable):
            uc.blocked("client", "2.3", pause=0, today=OCT_5)
        errors = []
        got = uc.blocked("client", "2.3", pause=0, today=OCT_5, errors=errors)
        assert set(got) == {uc.canon(A)} and len(errors) == 1

    def test_assert_clear_raises_on_a_blocked_url(self, fake, monkeypatch):
        fake({"s9": old_workbook(rl=[(A, "2026-09-20")])})
        self.patch_registry(monkeypatch, {
            "name": "Client", "folder": "Clients/X", "sheet_id_2026_09": "s9"})
        seen = uc.blocked("client", "2.3", pause=0, today=OCT_5)
        with pytest.raises(SystemExit) as e:
            uc.assert_clear("client", "2.3", [A.rstrip("/").upper().lower()],
                            known=seen)
        assert "COOLDOWN VIOLATION" in str(e.value)
        uc.assert_clear("client", "2.3", [B], known=seen)       # clear

    def test_other_tab_keys_keep_prefix_matching_inside_the_window(
            self, fake, monkeypatch):
        fake({"s9": old_workbook(), "s6": old_workbook()})
        self.patch_registry(monkeypatch, {
            "name": "Client", "folder": "Clients/X",
            "sheet_id_2026_09": "s9", "sheet_id_2026_06": "s6"})
        got = uc.blocked("client", "3.2", pause=0, today=OCT_5)
        assert list(got) == [uc.canon(A)]
        assert got[uc.canon(A)] == ["2026_09 3.2 Internal Links r5"]

    def test_same_month_reads_only_the_current_2_3_tab(self, fake, monkeypatch):
        cur = new_layout_tab(pages=[page_row("Refresh", A)], changes=[])
        fake({"now": {"2.3 Page Optimizations": cur,
                      "3.1 Internal Links": [["x"], [], [], ["Source URL"], [B]]}})
        self.patch_registry(monkeypatch, {
            "name": "Client", "folder": "Clients/X", "sheet_id": "now"})
        got = uc.same_month("client", pause=0)
        assert set(got) == {uc.canon(A)}
        with pytest.raises(SystemExit):
            uc.assert_no_same_month("client", [A], known=got)
        uc.assert_no_same_month("client", [B], known=got)
