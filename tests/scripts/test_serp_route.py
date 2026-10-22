"""serp_route.py: what holds a query's top 10, and whether it needs a page or a placement.

Run from the project root:

    pytest tests/scripts/test_serp_route.py -q

No network. The queue tests hand `run_checks` a fake DataForSEO call.
"""

from __future__ import annotations

import pytest

import serp_route as R


def org(*rows: tuple[str, str]) -> list[dict]:
    return [{"pos": i, "domain": d, "title": t, "url": f"https://{d}/"} for i, (d, t) in enumerate(rows, 1)]


@pytest.mark.parametrize("domain,title,kind", [
    ("yelp.com", "Top 10 Best Plumbers in Salt Lake City", "directory"),
    ("m.yelp.com", "Plumbers", "directory"),
    ("local.yahoo.com", "Asphalt Paving in Ann Arbor", "directory"),  # seen in the 2026-10-22 smoke run
    ("finance.yahoo.com", "Paving stocks", "business"),               # only Yahoo's listings host is a directory
    ("expertise.com", "5 Best Salt Lake City Plumbers", "directory"),
    ("reddit.com", "Any plumber recommendations?", "forum"),
    ("youtube.com", "How to fix a drain", "video"),
    ("facebook.com", "Acme Plumbing", "social"),
    ("slc.gov", "Permits", "reference"),
    ("en.wikipedia.org", "Plumbing", "reference"),
    ("ksl.com", "Plumbers raise prices", "news"),
    ("blog.example.com", "The 10 Best Plumbers in Salt Lake City (2026)", "listicle"),
    ("blog.example.com", "Top 7 HVAC Companies in Sandy", "listicle"),
    ("blog.example.com", "Top 10 Asphalt Paving Contractors near Ann Arbor", "listicle"),
    ("blog.example.com", "10 Best Odoo Alternatives", "listicle"),
    ("acmeplumbing.com", "Best Plumber in Salt Lake City | Acme Plumbing", "business"),
    ("acmeplumbing.com", "24/7 Emergency Plumbing", "business"),
    # A number in a business's own title is not a counted list of providers (python-reviewer, 2026-10-22).
    ("acme.com", "Best 24/7 Plumber in Sandy | Acme", "business"),
    ("acme.com", "Best 24 Hour Emergency Plumber", "business"),
    ("acme.com", "Top 5 Reasons to Choose Acme Plumbing", "business"),
    ("acme.com", "5 Best Practices for Drains | Acme", "business"),
    ("acme.com", "Top 3-Star Rated HVAC", "business"),
    ("acme.com", "Top 10 Plumbing Tips", "business"),
])
def test_classify(domain, title, kind):
    assert R.classify(domain, title) == kind


def test_a_best_title_without_a_count_stays_a_business_page():
    # Businesses title their own pages "Best X in City"; only a counted list is a listicle.
    assert R.classify("drainkings.com", "Best Drain Cleaning in Sandy, UT") == "business"


def test_composition_reads_only_the_top_10():
    rows = org(*[("biz%d.com" % i, "Plumbing") for i in range(12)])
    comp = R.composition(rows)
    assert comp["business"] == 10
    assert len(comp["top3"]) == 3


def test_composition_counts_one_business_once_however_many_slots_it_holds():
    comp = R.composition(org(("acme.com", "Home"), ("acme.com", "Drains"), ("acme.com", "Water heaters"),
                             ("yelp.com", "x")))
    assert comp["business"] == 1


def test_composition_skips_results_with_no_domain():
    rows = org(("acme.com", "x"), ("b.com", "x")) + [{"pos": 3, "domain": "", "title": "x", "url": None}]
    assert R.composition(rows)["business"] == 2


def test_composition_flags_a_top_3_held_by_non_business_sites():
    comp = R.composition(org(("yelp.com", "x"), ("angi.com", "x"), ("expertise.com", "x"),
                             ("a.com", "x"), ("b.com", "x"), ("c.com", "x")))
    assert comp["top3_non_business"] is True
    assert comp["business"] == 3


@pytest.mark.parametrize("business,top3_non_business,expected", [
    (3, False, "Our page"),
    (8, False, "Our page"),
    (2, False, "Placement"),
    (0, True, "Placement"),
    (5, True, "Both"),
])
def test_route(business, top3_non_business, expected):
    assert R.route(business, top3_non_business) == expected


def test_aggregate_takes_the_median_count_and_the_majority_top_3():
    checks = [{"business": 2, "top3_non_business": True},
              {"business": 3, "top3_non_business": False},
              {"business": 4, "top3_non_business": False}]
    agg = R.aggregate(checks)
    assert agg["business"] == 3
    assert agg["top3_non_business"] is False
    assert agg["route"] == "Our page"


def test_aggregate_with_no_reading():
    assert R.aggregate([])["route"] == "No reading"


def test_parse_task_keeps_organic_items_in_order():
    task = {"status_code": 20000, "data": {"tag": "0|1"}, "result": [{"items": [
        {"type": "local_pack", "domain": "maps.google.com", "title": "x", "rank_absolute": 1},
        {"type": "organic", "domain": "www.yelp.com", "title": "Top 10", "url": "u1", "rank_absolute": 2},
        {"type": "organic", "domain": "acme.com", "title": "Acme", "url": "u2", "rank_absolute": 3},
    ]}]}
    rows = R.parse_task(task)
    assert [r["domain"] for r in rows] == ["yelp.com", "acme.com"]


ITEMS = [{"type": "organic", "domain": "acme.com", "title": "Acme", "url": "u", "rank_absolute": 1}]


class FakeDfs:
    """Queue stand-in. `codes[keyword]` is the task_get status for that keyword's FIRST fetched task;
    every later task returns 20000. `never_ready` keywords stay queued forever."""

    def __init__(self, codes: dict | None = None, never_ready: set | None = None, items=ITEMS,
                 raise_on_ready: bool = False):
        self.posted: list[dict] = []
        self.ready: list[str] = []
        self.keyword_of: dict[str, str] = {}
        self.codes = dict(codes or {})
        self.never_ready = never_ready or set()
        self.items = items
        self.raise_on_ready = raise_on_ready
        self.n = 0

    def __call__(self, method, path, auth, payload=None):
        if path.endswith("/task_post"):
            tasks = []
            for task in payload:
                self.n += 1
                tid = f"t{self.n}"
                self.posted.append(task)
                self.keyword_of[tid] = task["keyword"]
                if task["keyword"] not in self.never_ready:
                    self.ready.append(tid)
                tasks.append({"id": tid, "status_code": 20100, "data": {"tag": task["tag"]}})
            return {"status_code": 20000, "tasks": tasks}
        if path.endswith("/tasks_ready"):
            if self.raise_on_ready:
                raise R.requests.ConnectionError("network down")
            ready, self.ready = self.ready, []
            # The vendor can list a task twice.
            return {"status_code": 20000, "tasks": [{"result": [{"id": t} for t in ready + ready[:1]]}]}
        if "/task_get/advanced/" in path:
            tid = path.rsplit("/", 1)[1]
            kw = self.keyword_of[tid]
            if kw in self.never_ready:
                return {"status_code": 20000, "tasks": [{"id": tid, "status_code": 40602}]}
            code = self.codes.pop(kw, 20000)
            if code != 20000:
                return {"status_code": 20000, "tasks": [{"id": tid, "status_code": code}]}
            return {"status_code": 20000,
                    "tasks": [{"id": tid, "status_code": 20000, "result": [{"items": self.items}]}]}
        raise AssertionError(path)


def run(fake, keywords, checks=2, **kw):
    return R.run_checks(keywords, "Sandy,Utah,United States", checks, auth=("u", "p"), call=fake,
                        sleep=lambda s: None, **kw)


def test_run_checks_posts_every_check_and_collects_them():
    fake = FakeDfs()
    out = run(fake, ["plumber sandy ut", "drain cleaning sandy"], checks=3)
    assert len(fake.posted) == 6
    assert {t["location_name"] for t in fake.posted} == {"Sandy,Utah,United States"}
    assert {t["depth"] for t in fake.posted} == {10}
    assert [len(v) for v in out.values()] == [3, 3]


def test_run_checks_reposts_a_transient_failure():
    fake = FakeDfs(codes={"b": 40101})
    out = run(fake, ["a", "b"])
    assert len(fake.posted) == 5
    assert len(out["b"]) == 2


def test_run_checks_never_reposts_a_final_vendor_answer():
    # 40102 is "no search results": billed and final. Posting it again pays twice for the same answer.
    fake = FakeDfs(codes={"b": 40102})
    out = run(fake, ["a", "b"])
    assert len(fake.posted) == 4
    assert len(out["b"]) == 1


def test_an_empty_results_page_is_no_reading_and_is_not_reposted():
    fake = FakeDfs(items=[])
    out = run(fake, ["a"])
    assert len(fake.posted) == 2
    assert out["a"] == []


def test_a_task_still_queued_at_the_deadline_is_kept_not_paid_for_again():
    fake = FakeDfs(never_ready={"b"})
    clock = iter(range(0, 10_000, 100))
    state: dict = {}
    out = run(fake, ["a", "b"], state=state, clock=lambda: next(clock), timeout_s=500)
    assert len(fake.posted) == 4                      # no re-post of b's two queued tasks
    assert len(out["a"]) == 2 and out["b"] == []
    assert sorted(state["pending"].values()) == ["b\tSandy,Utah,United States\t0",
                                                 "b\tSandy,Utah,United States\t1"]


def test_a_rerun_collects_queued_tasks_from_the_state_instead_of_posting_again():
    fake = FakeDfs(never_ready={"b"})
    state: dict = {}
    clock = iter(range(0, 10_000, 100))
    run(fake, ["a", "b"], state=state, clock=lambda: next(clock), timeout_s=500)
    fake.never_ready.clear()                          # the vendor finished them since

    out = run(fake, ["a", "b"], state=state)
    assert len(fake.posted) == 4                      # nothing new posted on the rerun
    assert len(out["b"]) == 2 and len(out["a"]) == 2  # a's readings came from the state
    assert state["pending"] == {}


def test_a_network_failure_while_polling_returns_what_was_paid_for():
    fake = FakeDfs(raise_on_ready=True)
    state: dict = {}
    out = run(fake, ["a"], state=state)
    assert out == {"a": []}
    assert len(state["pending"]) == 2                 # kept for the next run, not lost


class Resp:
    def __init__(self, status: int, body: dict | None = None):
        self.status_code, self._body, self.headers = status, body or {"status_code": 20000}, {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise R.requests.HTTPError(str(self.status_code))


def test_a_post_is_never_retried_on_a_server_error(monkeypatch):
    calls = []
    monkeypatch.setattr(R.requests, "request", lambda *a, **k: calls.append(1) or Resp(502))
    monkeypatch.setattr(R.time, "sleep", lambda s: None)
    with pytest.raises(R.requests.HTTPError):
        R.dfs_call("POST", "/serp/google/organic/task_post", ("u", "p"), [])
    assert len(calls) == 1                            # a 502 may mean the batch was accepted and billed


def test_a_get_is_retried_after_a_network_error(monkeypatch):
    outcomes = [R.requests.ConnectionError("blip"), Resp(200)]

    def request(*a, **k):
        out = outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out

    monkeypatch.setattr(R.requests, "request", request)
    monkeypatch.setattr(R.time, "sleep", lambda s: None)
    assert R.dfs_call("GET", "/serp/google/organic/tasks_ready", ("u", "p"))["status_code"] == 20000


def test_read_keywords_drops_an_excel_bom_header_and_keeps_commas_in_plain_files(tmp_path):
    csv_file = tmp_path / "kws.csv"
    csv_file.write_text("﻿keyword,volume\nplumber sandy,90\n", encoding="utf-8")
    txt_file = tmp_path / "kws.txt"
    txt_file.write_text("plumber sandy, ut\n\nPlumber Sandy, UT\n", encoding="utf-8")

    from types import SimpleNamespace
    assert R.read_keywords(SimpleNamespace(keywords=[], keywords_file=str(csv_file))) == ["plumber sandy"]
    assert R.read_keywords(SimpleNamespace(keywords=[], keywords_file=str(txt_file))) == ["plumber sandy, ut"]
