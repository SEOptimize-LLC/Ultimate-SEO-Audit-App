"""Layout of the "2.3 Page Optimizations" tab (October 2026 template onward).

One tab replaces three: "2.3-3.1 Refresh Log", "2.5 Quick Wins" and the
September " Page Optimization". Everything that reads or writes it goes through
this module so the layout is anchored in ONE place.

    Section 1 - Pages    header row, then up to 10 rows, A:I
        Type | Page | URL | Target Queries / Refresh Angle |
        Baseline (clicks / impr / pos / AI cited) |
        Keywords -> Position Tracking (tag) | Title/Meta Change |
        Date Live | Verdict (filled next month from 1.5)

    Section 2 - Changes  header row, then one row per change, A:J
        Type | Page | URL | What To Change | Currently On The Page |
        Use This Instead | Why It Matters | Owner | Status | Date Done

Row numbers are never hardcoded. locate() finds the two section headings by
their text ("Section 1", "Section 2") and checks both header rows, and it
raises instead of guessing when either has drifted. Prior-month workbooks have
the OLD three-tab layout and are read by url_cooldown.py, not here.

Division of labour on this tab: 1.8 (fill_1_8.py) writes the Pages rows ONCE.
fill_2_3.py writes the Changes rows and, from live evidence only, the
completion cells (Pages G:H, Changes I:J). track_keywords.py writes Pages F.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

import sheets_io

TAB = "2.3 Page Optimizations"
PAGES_HEADING = "Section 1"
CHANGES_HEADING = "Section 2"

PAGES_HEADER = [
    "Type", "Page", "URL", "Target Queries / Refresh Angle",
    "Baseline (clicks / impr / pos / AI cited)",
    "Keywords → Position Tracking (tag)", "Title/Meta Change",
    "Date Live", "Verdict (filled next month from 1.5)"]
CHANGES_HEADER = [
    "Type", "Page", "URL", "What To Change", "Currently On The Page",
    "Use This Instead", "Why It Matters", "Owner", "Status", "Date Done"]

# Dropdown values, copied from the template's data validation (read 2026-10-05).
TYPES = ("Refresh", "Quick Win")
PAGE_CHANGE_VALUES = ("Done", "No change needed")
WHAT = ("Read this first", "Page structure", "Title tag", "Title tag and H1",
        "Meta description", "Page content", "Internal links", "Schema")
STATUSES = ("To do", "Done", "No change needed", "Note")

# "What To Change" values that are a listing change. Pages column G summarises
# exactly these rows, and they are the ones a fetch can verify.
TITLE_META = ("Title tag", "Title tag and H1", "Meta description")

PAGES_CAP = 10          # up to 5 Refresh + up to 5 Quick Win
PAGES_CAP_PER_TYPE = 5
CHANGES_READ_SPAN = 200  # rows read below the Changes header
# Template data validation on Changes covers the first rows only; fill_2_3
# re-applies it when a client needs more.
TEMPLATE_VALIDATED_THROUGH = 40

# Pages columns (0-indexed within A:I)
P_TYPE, P_PAGE, P_URL, P_QUERIES, P_BASELINE, P_TRACKING, P_CHANGE, \
    P_LIVE, P_VERDICT = range(9)
# Changes columns (0-indexed within A:J)
C_TYPE, C_PAGE, C_URL, C_WHAT, C_CURRENT, C_USE, C_WHY, C_OWNER, \
    C_STATUS, C_DONE = range(10)


class LayoutError(RuntimeError):
    """The tab is missing or no longer looks like the October template."""


@dataclass(frozen=True)
class Layout:
    tab: str
    pages_heading: int
    pages_header: int
    changes_heading: int
    changes_header: int

    @property
    def pages_first(self) -> int:
        return self.pages_header + 1

    @property
    def pages_last(self) -> int:
        """Last row before the Changes heading. The cap is PAGES_CAP rows of
        data; the blank rows between are spacing and are never written."""
        return self.changes_heading - 1

    @property
    def changes_first(self) -> int:
        return self.changes_header + 1


@dataclass(frozen=True)
class PageRow:
    row: int
    type: str
    page: str
    url: str
    queries: str
    baseline: str
    tracking: str
    change: str
    date_live: str
    verdict: str


@dataclass(frozen=True)
class ChangeRow:
    row: int
    type: str
    page: str
    url: str
    what: str
    current: str
    use: str
    why: str
    owner: str
    status: str
    date_done: str


def tab_name(sheet_id: str) -> str | None:
    """The workbook's actual tab name (tolerates stray spaces), or None."""
    for t in sheets_io.tab_names(sheet_id):
        if t.strip().lower().startswith(TAB.lower()):
            return t
    return None


def locate(sheet_id: str, *, check: bool = True) -> Layout:
    """Anchor on the two headings and, when check=True, verify both headers.

    check=False is for read-only passes over a workbook we do not own the
    wording of (a prior month); anything that WRITES must use check=True.
    """
    tab = tab_name(sheet_id)
    if tab is None:
        raise LayoutError(f"no tab named {TAB!r} in workbook {sheet_id}")
    try:
        rows = sheets_io.find_rows(
            sheet_id, tab, {"pages": PAGES_HEADING, "changes": CHANGES_HEADING})
    except KeyError as e:
        raise LayoutError(str(e)) from e
    lay = Layout(tab=tab, pages_heading=rows["pages"],
                 pages_header=rows["pages"] + 1,
                 changes_heading=rows["changes"],
                 changes_header=rows["changes"] + 1)
    if lay.changes_heading <= lay.pages_header:
        raise LayoutError(f"{tab}: Section 2 sits above Section 1's header")
    if check:
        for hdr, exp, label in ((lay.pages_header, PAGES_HEADER, "Pages"),
                                (lay.changes_header, CHANGES_HEADER, "Changes")):
            chk = sheets_io.check_layout(
                sheet_id, f"'{tab}'!A{hdr}:{chr(64 + len(exp))}{hdr}", exp)
            if not chk.ok:
                raise LayoutError(
                    f"{tab}: {label} header at row {hdr} has drifted. "
                    f"expected {exp}, found {chk.found}")
    return lay


def _cells(row, n: int) -> list[str]:
    cells = [("" if c is None else str(c).strip()) for c in (row or [])]
    return (cells + [""] * n)[:n]


def parse_pages(values: list[list], first_row: int) -> list[PageRow]:
    """Rows of the Pages block that carry anything in Type, URL or Page."""
    out = []
    for i, raw in enumerate(values):
        c = _cells(raw, 9)
        if not (c[P_TYPE] or c[P_URL] or c[P_PAGE]):
            continue
        out.append(PageRow(first_row + i, c[P_TYPE], c[P_PAGE], c[P_URL],
                           c[P_QUERIES], c[P_BASELINE], c[P_TRACKING],
                           c[P_CHANGE], c[P_LIVE], c[P_VERDICT]))
    return out


def parse_changes(values: list[list], first_row: int) -> list[ChangeRow]:
    out = []
    for i, raw in enumerate(values):
        c = _cells(raw, 10)
        if not (c[C_TYPE] or c[C_URL] or c[C_WHAT]):
            continue
        out.append(ChangeRow(first_row + i, c[C_TYPE], c[C_PAGE], c[C_URL],
                             c[C_WHAT], c[C_CURRENT], c[C_USE], c[C_WHY],
                             c[C_OWNER], c[C_STATUS], c[C_DONE]))
    return out


def read_pages(sheet_id: str, lay: Layout) -> list[PageRow]:
    vals = sheets_io.read(
        sheet_id, f"'{lay.tab}'!A{lay.pages_first}:I{lay.pages_last}")
    return parse_pages(vals, lay.pages_first)


def read_changes(sheet_id: str, lay: Layout) -> list[ChangeRow]:
    last = lay.changes_first + CHANGES_READ_SPAN
    vals = sheets_io.read(
        sheet_id, f"'{lay.tab}'!A{lay.changes_first}:J{last}")
    return parse_changes(vals, lay.changes_first)


def client_cfg(client: str) -> tuple[str, dict]:
    """(registry key, config) for a client given as key or full name.

    Registry rows with no sheet_id (inactive clients) are refused here so an
    "all clients" loop cannot write to a workbook that does not exist.
    """
    reg = yaml.safe_load(
        Path("clients/registry.yaml").read_text(encoding="utf-8"))
    for key, v in reg.items():
        if (isinstance(v, dict) and "folder" in v
                and client.lower() in (key.lower(), str(v.get("name", "")).lower())):
            if not v.get("sheet_id"):
                raise SystemExit(f"{client}: no sheet_id in registry.yaml "
                                 f"(inactive client)")
            return key, v
    raise SystemExit(f"unknown client {client!r}")


def active_clients() -> list[tuple[str, dict]]:
    """Every registry client that has a current workbook."""
    reg = yaml.safe_load(
        Path("clients/registry.yaml").read_text(encoding="utf-8"))
    return [(k, v) for k, v in reg.items()
            if isinstance(v, dict) and "folder" in v and v.get("sheet_id")]
