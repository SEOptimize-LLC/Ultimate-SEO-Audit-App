"""run_index_checks.render_gate and the split it drives. No network."""
from __future__ import annotations

import run_index_checks as RC

SITE = "https://x.com/"
ROBOTS = "User-agent: *\nDisallow: /wp-includes/\n"


def fake(pages):
    def fetch(url, ua, timeout=25):
        return pages.get(url, (404, "", {}))
    return fetch


def page(words, extra=""):
    return (200, f"<html><head>{extra}</head><body>{'word ' * words}</body></html>", {})


def test_blocked_asset_hollow_page_clean_and_unfetched():
    pages = {
        "https://x.com/a": page(400, '<script src="/wp-includes/js/app.js"></script>'),
        "https://x.com/b": page(10),
        "https://x.com/c": page(400, '<link rel="stylesheet" href="https://cdn.other.com/x.css">'),
    }
    g = RC.render_gate(["https://x.com/a", "https://x.com/b", "https://x.com/c", "https://x.com/d"],
                       SITE, fetch=fake(pages), robots_text=ROBOTS)
    assert g["https://x.com/a"] == "blocked: /wp-includes/js/app.js"
    assert g["https://x.com/b"].startswith("hollow")
    assert g["https://x.com/c"] == "clean"
    assert g["https://x.com/d"].startswith("not checked")


def test_no_gate_never_reads_as_clean():
    bad, clean, unchecked = RC.split_by_gate(["u1", "u2"], None)
    assert not bad and not clean and unchecked == ["u1", "u2"]


def test_findings_route_render_faults_to_2_1_and_clean_to_1_8():
    gate = {"https://x.com/a": "blocked: /js/a.js", "https://x.com/c": "clean"}
    rows = RC.gate_findings("URL(s) Crawled - currently not indexed", list(gate), gate, "Watch")
    assert [r[3] for r in rows] == ["2.1", "1.8"]
