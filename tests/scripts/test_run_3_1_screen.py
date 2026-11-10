"""run_3_1: funnel counts from the engine log, and the index screen. No network."""
from __future__ import annotations

import json

import pandas as pd

import run_3_1 as R

LOG = """Pair-matcher funnel:
  Candidates in:                  1780
  Dropped: source-below-click-floor         163
  Dropped: cannibalization                  62
  Survived hard filters:          56
"""


def test_funnel_counts_read_the_last_block():
    got = R.funnel_counts(LOG + LOG.replace("163", "170"))
    assert got == {"source-below-click-floor": 170, "cannibalization": 62}
    assert R.funnel_counts("no funnel here") == {}


def test_index_screen_keeps_only_indexed_sources(tmp_path):
    month_dir = tmp_path / "Monthly SEO Workbook" / "2026-12"
    month_dir.mkdir(parents=True)
    (month_dir / "index_audit.json").write_text(json.dumps({"rows": [
        {"url": "https://x.com/a/", "state": "Submitted and indexed"},
        {"url": "https://x.com/b/", "state": "Crawled - currently not indexed"}]}), encoding="utf-8")
    final = pd.DataFrame({"Source URL": ["https://x.com/a/", "https://x.com/b/", "https://x.com/c/"]})
    kept, dropped = R.index_screen(final, {"folder": str(tmp_path)}, "2026-12")
    assert list(kept["Source URL"]) == ["https://x.com/a/"]
    assert {u for u, _ in dropped} == {"https://x.com/b/", "https://x.com/c/"}
