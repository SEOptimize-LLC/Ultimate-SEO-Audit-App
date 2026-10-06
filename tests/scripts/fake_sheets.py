"""An in-memory stand-in for the parts of scripts/sheets_io.py the 2.3 scripts use.

No network and no credentials: tests patch sheets_io's read/write/tab_names with
this and assert on what the scripts would have sent. Rows are 0-indexed lists of
strings, row 1 of the sheet is workbook[sid][tab][0].
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import sheets_io  # noqa: E402

_RANGE = re.compile(r"([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$")


def col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


class FakeSheets:
    """workbooks: {sheet_id: {tab_name: [[cell, ...], ...]}}"""

    def __init__(self, workbooks: dict[str, dict[str, list[list]]]):
        self.wb = workbooks
        self.writes: list[tuple[str, str, list[list]]] = []
        self.cleared: list[tuple[str, str]] = []
        self.snapshots: list[tuple[str, str]] = []

    # -- reads -------------------------------------------------------------
    def tab_names(self, sid):
        return list(self.wb[sid])

    def read(self, sid, a1):
        tab, _, rng = a1.rpartition("!")
        tab = tab.strip("'")
        grid = self.wb[sid][tab]
        m = _RANGE.match(rng)
        if m is None:
            raise ValueError(f"fake read cannot parse {a1}")
        c1, r1, c2, r2 = m.groups()
        r1 = int(r1)
        r2 = int(r2) if r2 else r1
        lo = col_index(c1)
        hi = col_index(c2) if c2 else lo
        out = []
        for row in grid[r1 - 1:r2]:
            cells = [("" if c is None else c) for c in row[lo:hi + 1]]
            while cells and cells[-1] == "":
                cells.pop()
            out.append(cells)
        while out and not out[-1]:
            out.pop()
        return out

    # -- writes ------------------------------------------------------------
    def write(self, sid, a1, values, **_kw):
        self.writes.append((sid, a1, values))
        tab, _, rng = a1.rpartition("!")
        tab = tab.strip("'")
        m = _RANGE.match(rng)
        c1, r1 = m.group(1), int(m.group(2))
        grid = self.wb[sid][tab]
        for dr, row in enumerate(values):
            while len(grid) < r1 + dr:
                grid.append([])
            target = grid[r1 - 1 + dr]
            for dc, v in enumerate(row):
                idx = col_index(c1) + dc
                while len(target) <= idx:
                    target.append("")
                target[idx] = v

        class _R:
            cells = sum(len(r) for r in values)
            verified = True
        return _R()

    def clear(self, sid, a1):
        self.cleared.append((sid, a1))

    def snapshot_tab(self, sid, tab, folder, rng="A1:J60"):
        self.snapshots.append((sid, tab))
        return "snapshot"

    def install(self, monkeypatch, *modules):
        """Patch sheets_io, and every module that bound its own names."""
        monkeypatch.setattr(sheets_io, "read", self.read)
        monkeypatch.setattr(sheets_io, "tab_names", self.tab_names)
        monkeypatch.setattr(sheets_io, "write", self.write)
        monkeypatch.setattr(sheets_io, "clear", self.clear)
        monkeypatch.setattr(sheets_io, "snapshot_tab", self.snapshot_tab)
        return self


def new_layout_tab(pages: list[list], changes: list[list]) -> list[list]:
    """A "2.3 Page Optimizations" grid shaped like the October template.

    Heading row 4, header row 5, Pages from row 6, Section 2 heading row 18,
    header row 19, Changes from row 20.
    """
    from page_opt_tab import CHANGES_HEADER, PAGES_HEADER
    grid: list[list] = [[] for _ in range(19)]
    grid[0] = ["2.3 Implement Page Optimizations (Refreshes + Quick Wins)"]
    grid[3] = ["Section 1 — Pages (one row per page)"]
    grid[4] = list(PAGES_HEADER)
    for i, r in enumerate(pages):
        grid[5 + i] = list(r)
    grid[17] = ["Section 2 — Changes (one row per change)"]
    grid[18] = list(CHANGES_HEADER)
    grid.extend(list(r) for r in changes)
    return grid
