# Microsoft Clarity UX Analysis & Reporting — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Clarity heatmap ingestion + analysis + reporting capability that turns manually-exported Click/Scroll/Attention CSVs (+ PNGs) into an internal CRO report and a client-facing UX report.

**Architecture:** A stdlib-only Python normalizer (`utils/clarity_parser.py`) parses the three Clarity CSV shapes, humanizes Elementor CSS selectors, filters admin noise, and computes scroll/attention/click metrics into frozen dataclasses. A methodology skill (`Skills/clarity-ux-analysis/`) governs interpretation and report writing; a `/clarity-report` slash command is the entry point. The analyst interprets the PNG heatmaps; code never tries to.

**Tech Stack:** Python 3.10+ (stdlib `csv`, `re`, `dataclasses`, `pathlib` only — no new dependencies), pytest, Markdown skill + command files.

**Spec:** `docs/superpowers/specs/2026-06-27-clarity-ux-analysis-design.md`

## Global Constraints

- **No new runtime dependencies** — normalizer uses Python stdlib only.
- **Immutable data** — all parser output is `@dataclass(frozen=True)`, type-annotated (PEP 8).
- **CSV-only capability boundary** — dead clicks are *candidates inferred from selector interactivity*, never presented as Clarity-confirmed. Dead/Rage/First/Last maps, session recordings, conversion/area maps are NOT available and must not be presented as run.
- **Revenue = real GA4 only** — no invented lead/$ figures; no conversion data → client report stays qualitative.
- **Every recommendation carries** ICE score (Impact×Confidence×Ease) AND mandatory fields per `.claude/rules/audit-workflow.md`: Priority (P0–P4), Effort, Expected outcome, Likely effect, Validation method.
- **Report formatting** — no timeline/calendar language; tables ≤6 columns; full URLs never truncated; no internal-doc references in client-facing output.
- **Admin-bar noise** (`#wp-admin-bar*`) excluded from analysis but reconciled to totals in a footnote.
- **Commits:** conventional-commit style, no AI attribution line (per user global git settings). Work stays on branch `feat/clarity-ux-analysis`.
- **Filename grammar:** `Clarity_<Project>_<Metric>[-_]<Device>_<MM-DD-YYYY HH MM AM/PM>.(csv|png)` — metric/device separator may be `-` or `_`.

---

### Task 1: Scaffolding, fixtures, and filename parser

**Files:**
- Create: `utils/clarity_parser.py`
- Create: `tests/fixtures/clarity/Clarity_Beehive_Click_PC_06-27-2026 05 05 PM.csv`
- Create: `tests/fixtures/clarity/Clarity_Beehive_Scroll_PC_06-27-2026 05 06 PM.csv`
- Create: `tests/fixtures/clarity/Clarity_Beehive_Attention_PC_06-27-2026 05 07 PM.csv`
- Test: `tests/test_clarity_parser.py`

**Interfaces:**
- Produces: `ClarityFile` (frozen dataclass: `path: Path, project: str, metric: str, device: str, timestamp_raw: str, ext: str`); `parse_filename(name: str) -> ClarityFile | None`.

- [ ] **Step 1: Create the three trimmed fixtures** (exact content below; preserve blank lines and quoting)

`tests/fixtures/clarity/Clarity_Beehive_Click_PC_06-27-2026 05 05 PM.csv`:
```
"Project name","Beehive"
"Date range","05/29/2026 12:00 AM - 06/27/2026 11:59 PM"


"Visited URL matches regex","^https://www\.beehiveplumbing\.com/(\?.*)?$"

"Page views","1487"
"Total clicks","498"

"Metric","Click"

"Rank","Button","Clicks"," % of clicks"
"1","#topnav>SPAN.elementor-button-content-wrapper:nth-of-type(1)>SPAN.elementor-button-text:nth-of-type(1)","22","4.42%"
"2","HTML>BODY:nth-of-type(1)>HEADER.elementor.elementor-location-header:nth-of-type(1)>NAV.elementor-nav-menu--main:nth-of-type(1)>UL.elementor-nav-menu:nth-of-type(1)>LI.menu-item:nth-of-type(7)>A.elementor-item:nth-of-type(1)","12","2.41%"
"3","#main>DIV.page-content:nth-of-type(1)>SECTION.elementor-section:nth-of-type(1)>DIV.elementor-background-overlay:nth-of-type(1)","11","2.21%"
"10","#wp-admin-bar-site-name>A.ab-item:nth-of-type(1)","4","0.80%"
"12","#main>DIV.page-content:nth-of-type(1)>SECTION.elementor-section:nth-of-type(1)>H2.elementor-heading-title.elementor-size-default:nth-of-type(1)","4","0.80%"
```

`tests/fixtures/clarity/Clarity_Beehive_Scroll_PC_06-27-2026 05 06 PM.csv`:
```
"Project name","Beehive"
"Date range","05/29/2026 12:00 AM - 06/27/2026 11:59 PM"


"Visited URL matches regex","^https://www\.beehiveplumbing\.com/(\?.*)?$"

"Page views","1487"


"Metric","Scroll"

"Scroll depth","No. of visitors","% drop off"
"5","585","60.61"
"10","285","80.81"
"15","185","87.54"
"20","167","88.75"
"25","152","89.76"
"30","141","90.51"
"35","129","91.31"
"40","125","91.58"
"45","118","92.05"
"50","111","92.53"
"55","109","92.66"
"60","106","92.86"
"65","103","93.06"
"70","99","93.33"
"75","95","93.60"
"80","88","94.07"
"85","81","94.55"
"90","75","94.95"
"95","73","95.08"
"100","62","95.82"
```

`tests/fixtures/clarity/Clarity_Beehive_Attention_PC_06-27-2026 05 07 PM.csv`:
```
"Project name","Beehive"
"Date range","05/29/2026 12:00 AM - 06/27/2026 11:59 PM"


"Visited URL matches regex","^https://www\.beehiveplumbing\.com/(\?.*)?$"

"Page views","1487"


"Metric","Attention"

"Scroll depth","Avg time spent","% of session length"
"5","00:20:04","33.95%"
"10","00:11:52","20.08%"
"15","00:07:49","13.23%"
"20","00:03:40","6.21%"
"25","00:01:10","1.98%"
"30","00:00:01","0.05%"
"35","00:00:05","0.16%"
"40","00:00:06","0.19%"
"45","00:00:08","0.24%"
"50","00:00:12","0.35%"
"55","00:00:12","0.35%"
"60","00:00:22","0.65%"
"65","00:00:18","0.52%"
"70","00:00:14","0.42%"
"75","00:00:52","1.47%"
"80","00:02:02","3.45%"
"85","00:00:24","0.69%"
"90","00:03:03","5.18%"
"95","00:04:09","7.04%"
"100","00:02:14","3.79%"
```

- [ ] **Step 2: Write the failing test**

```python
"""Tests for the Microsoft Clarity export normalizer."""

from pathlib import Path

import pytest

from utils.clarity_parser import parse_filename, ClarityFile

FIXTURES = Path(__file__).parent / "fixtures" / "clarity"


def test_parse_filename_click_csv_underscore_separator():
    f = parse_filename("Clarity_Beehive_Click_PC_06-27-2026 05 05 PM.csv")
    assert f is not None
    assert f.project == "Beehive"
    assert f.metric == "Click"
    assert f.device == "PC"
    assert f.ext == "csv"


def test_parse_filename_png_hyphen_separator():
    f = parse_filename("Clarity_Beehive_Attention-PC_06-27-2026 05 07 PM.png")
    assert f is not None
    assert f.metric == "Attention"
    assert f.device == "PC"
    assert f.ext == "png"


def test_parse_filename_rejects_non_clarity():
    assert parse_filename("random_export.csv") is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_clarity_parser.py -v`
Expected: FAIL with `ImportError: cannot import name 'parse_filename'`

- [ ] **Step 4: Write minimal implementation** (create `utils/clarity_parser.py`)

```python
"""Microsoft Clarity export normalizer.

Parses manually-exported Clarity heatmap CSVs (Click / Scroll / Attention)
into immutable, analysis-ready dataclasses. Stdlib only.

Capability boundary: dead clicks here are CANDIDATES inferred from selector
interactivity, NOT Clarity-confirmed dead clicks. Dead/Rage/First/Last maps,
session recordings, and conversion/area maps are dashboard-only and absent.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

METRICS = ("Click", "Scroll", "Attention")
DEVICES = ("PC", "Mobile", "Tablet")

_FILENAME_RE = re.compile(
    r"^Clarity_(?P<project>.+?)_(?P<metric>Click|Scroll|Attention)"
    r"[-_](?P<device>PC|Mobile|Tablet)_(?P<ts>.+)\.(?P<ext>csv|png)$"
)


@dataclass(frozen=True)
class ClarityFile:
    path: Path
    project: str
    metric: str
    device: str
    timestamp_raw: str
    ext: str


def parse_filename(name: str, path: Optional[Path] = None) -> Optional[ClarityFile]:
    """Parse a Clarity export filename. Returns None if it isn't one."""
    m = _FILENAME_RE.match(name)
    if not m:
        return None
    return ClarityFile(
        path=path if path is not None else Path(name),
        project=m.group("project"),
        metric=m.group("metric"),
        device=m.group("device"),
        timestamp_raw=m.group("ts"),
        ext=m.group("ext"),
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_clarity_parser.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add utils/clarity_parser.py tests/test_clarity_parser.py "tests/fixtures/clarity/"
git commit -m "feat(clarity): add export filename parser + fixtures"
```

---

### Task 2: CSV preamble + table parser

**Files:**
- Modify: `utils/clarity_parser.py`
- Test: `tests/test_clarity_parser.py`

**Interfaces:**
- Consumes: `parse_filename`.
- Produces: `ClarityMeta` (frozen: `project, date_range, date_start, date_end, url_regex: str; page_views: int; total_clicks: Optional[int]; metric, device, source_file: str`); `ClarityExport` (frozen: `meta: ClarityMeta; header: tuple[str, ...]; rows: tuple[tuple[str, ...], ...]`); `parse_clarity_csv(path: Path, device: str = "") -> ClarityExport`; `parse_time_to_seconds(value: str) -> int`.

- [ ] **Step 1: Write the failing tests**

```python
from utils.clarity_parser import parse_clarity_csv, parse_time_to_seconds


def test_parse_click_csv_metadata():
    exp = parse_clarity_csv(FIXTURES / "Clarity_Beehive_Click_PC_06-27-2026 05 05 PM.csv", device="PC")
    assert exp.meta.project == "Beehive"
    assert exp.meta.metric == "Click"
    assert exp.meta.page_views == 1487
    assert exp.meta.total_clicks == 498
    assert exp.meta.url_regex == r"^https://www\.beehiveplumbing\.com/(\?.*)?$"
    assert exp.meta.date_start == "05/29/2026"
    assert exp.meta.date_end == "06/27/2026"
    assert exp.header == ("Rank", "Button", "Clicks", " % of clicks")
    assert len(exp.rows) == 5
    assert exp.rows[0][0] == "1"


def test_parse_scroll_csv_has_no_total_clicks():
    exp = parse_clarity_csv(FIXTURES / "Clarity_Beehive_Scroll_PC_06-27-2026 05 06 PM.csv", device="PC")
    assert exp.meta.metric == "Scroll"
    assert exp.meta.total_clicks is None
    assert len(exp.rows) == 20


def test_parse_time_to_seconds():
    assert parse_time_to_seconds("00:20:04") == 1204
    assert parse_time_to_seconds("00:00:01") == 1
    assert parse_time_to_seconds("01:02:03") == 3723
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_clarity_parser.py::test_parse_click_csv_metadata -v`
Expected: FAIL with `ImportError: cannot import name 'parse_clarity_csv'`

- [ ] **Step 3: Add the implementation** (append to `utils/clarity_parser.py`)

```python
@dataclass(frozen=True)
class ClarityMeta:
    project: str
    date_range: str
    date_start: str
    date_end: str
    url_regex: str
    page_views: int
    total_clicks: Optional[int]
    metric: str
    device: str
    source_file: str


@dataclass(frozen=True)
class ClarityExport:
    meta: ClarityMeta
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


def parse_time_to_seconds(value: str) -> int:
    """Convert 'HH:MM:SS' to total seconds."""
    parts = [int(p) for p in value.strip().split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts[-3], parts[-2], parts[-1]
    return h * 3600 + m * 60 + s


def _to_int(value: str) -> int:
    return int(re.sub(r"[^\d-]", "", value))


def parse_clarity_csv(path: Path, device: str = "") -> ClarityExport:
    """Parse a Clarity CSV (preamble + table) into a ClarityExport."""
    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as fh:
        records = [row for row in csv.reader(fh)]

    meta_kv: dict[str, str] = {}
    metric = ""
    table_start = None
    for i, row in enumerate(records):
        cells = [c.strip() for c in row]
        if not any(cells):
            continue
        if len(cells) >= 2 and cells[0] == "Metric":
            metric = cells[1]
            continue
        # The table header is the first non-empty row AFTER the Metric marker.
        if metric and table_start is None and len(cells) >= 2:
            table_start = i
            break
        if len(cells) >= 2:
            meta_kv[cells[0]] = cells[1]

    if table_start is None:
        raise ValueError(f"Could not locate data table in {path.name}")

    header = tuple(c.strip() for c in records[table_start])
    rows = tuple(
        tuple(c.strip() for c in r)
        for r in records[table_start + 1:]
        if any(c.strip() for c in r)
    )

    date_range = meta_kv.get("Date range", "")
    date_start, date_end = "", ""
    if " - " in date_range:
        left, right = date_range.split(" - ", 1)
        date_start = left.strip().split(" ")[0]
        date_end = right.strip().split(" ")[0]

    total = meta_kv.get("Total clicks")
    meta = ClarityMeta(
        project=meta_kv.get("Project name", ""),
        date_range=date_range,
        date_start=date_start,
        date_end=date_end,
        url_regex=meta_kv.get("Visited URL matches regex", ""),
        page_views=_to_int(meta_kv.get("Page views", "0")),
        total_clicks=_to_int(total) if total is not None else None,
        metric=metric,
        device=device,
        source_file=path.name,
    )
    return ClarityExport(meta=meta, header=header, rows=rows)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_clarity_parser.py -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add utils/clarity_parser.py tests/test_clarity_parser.py
git commit -m "feat(clarity): parse CSV preamble metadata + data table"
```

---

### Task 3: CSS selector humanizer

**Files:**
- Modify: `utils/clarity_parser.py`
- Test: `tests/test_clarity_parser.py`

**Interfaces:**
- Produces: `ElementLabel` (frozen: `region: str, component: str, interactivity: str, label: str, is_admin_noise: bool, is_dead_click_candidate: bool`); `humanize_selector(selector: str) -> ElementLabel`.

- [ ] **Step 1: Write the failing tests**

```python
from utils.clarity_parser import humanize_selector


def test_humanize_admin_bar_is_noise():
    lbl = humanize_selector("#wp-admin-bar-site-name>A.ab-item:nth-of-type(1)")
    assert lbl.is_admin_noise is True
    assert lbl.region == "Admin bar"
    # noise is never a dead-click candidate
    assert lbl.is_dead_click_candidate is False


def test_humanize_header_nav_link_is_interactive():
    sel = ("HTML>BODY:nth-of-type(1)>HEADER.elementor.elementor-location-header:nth-of-type(1)>"
           "NAV.elementor-nav-menu--main:nth-of-type(1)>UL.elementor-nav-menu:nth-of-type(1)>"
           "LI.menu-item:nth-of-type(7)>A.elementor-item:nth-of-type(1)")
    lbl = humanize_selector(sel)
    assert lbl.region == "Header"
    assert lbl.component == "Nav menu"
    assert lbl.interactivity == "interactive"
    assert lbl.is_dead_click_candidate is False


def test_humanize_background_overlay_is_dead_candidate():
    sel = ("#main>DIV.page-content:nth-of-type(1)>SECTION.elementor-section:nth-of-type(1)>"
           "DIV.elementor-background-overlay:nth-of-type(1)")
    lbl = humanize_selector(sel)
    assert lbl.region == "Main"
    assert lbl.interactivity == "non-interactive"
    assert lbl.is_dead_click_candidate is True


def test_humanize_heading_is_dead_candidate():
    sel = ("#main>DIV.page-content:nth-of-type(1)>SECTION.elementor-section:nth-of-type(1)>"
           "H2.elementor-heading-title.elementor-size-default:nth-of-type(1)")
    lbl = humanize_selector(sel)
    assert lbl.component == "Heading"
    assert lbl.is_dead_click_candidate is True


def test_humanize_button_inner_span_is_interactive():
    sel = ("#topnav>SPAN.elementor-button-content-wrapper:nth-of-type(1)>"
           "SPAN.elementor-button-text:nth-of-type(1)")
    lbl = humanize_selector(sel)
    assert lbl.region == "Header"
    assert lbl.component == "Button"
    assert lbl.interactivity == "interactive"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_clarity_parser.py -k humanize -v`
Expected: FAIL with `ImportError: cannot import name 'humanize_selector'`

- [ ] **Step 3: Add the implementation** (append to `utils/clarity_parser.py`)

```python
@dataclass(frozen=True)
class ElementLabel:
    region: str
    component: str
    interactivity: str
    label: str
    is_admin_noise: bool
    is_dead_click_candidate: bool


_INTERACTIVE_TAGS = {"A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"}
_INTERACTIVE_TOKENS = (
    "elementor-button-text",
    "elementor-button-content-wrapper",
    "elementor-button",
    "elementor-item",
    "elementor-sub-item",
    "elementor-social-icon",
    "swiper-button",
    "sub-arrow",
    "ab-item",
)


def _terminal_tag(segment: str) -> str:
    m = re.match(r"^([A-Za-z][A-Za-z0-9]*)", segment)
    return m.group(1).upper() if m else ""


def _region_of(selector: str) -> tuple[str, bool]:
    if "#wp-admin-bar" in selector:
        return "Admin bar", True
    if "elementor-location-header" in selector or selector.startswith("#topnav"):
        return "Header", False
    if "elementor-location-footer" in selector:
        return "Footer", False
    if "#main" in selector or "page-content" in selector:
        return "Main", False
    return "Unknown", False


def _component_of(selector: str, terminal: str, terminal_tag: str) -> str:
    if "wp-admin-bar" in selector:
        return "Admin bar"
    if "nav-menu" in selector or "menu-item" in selector or "elementor-item" in terminal:
        return "Nav menu"
    if "elementor-social-icon" in selector:
        return "Social icon"
    if "swiper" in selector or "image-carousel" in selector:
        return "Carousel"
    if "elementor-form" in selector or "elementor-widget-form" in selector:
        return "Form"
    if "elementor-button" in terminal or terminal_tag == "BUTTON":
        return "Button"
    if "background-overlay" in terminal:
        return "Section background"
    if terminal_tag.startswith("H") and terminal_tag[1:].isdigit():
        return "Heading"
    if "elementor-heading" in terminal:
        return "Heading"
    if terminal_tag == "SECTION":
        return "Section"
    return terminal_tag.title() or "Element"


def humanize_selector(selector: str) -> ElementLabel:
    """Translate a Clarity CSS-selector path into a human-readable element label."""
    segments = [s for s in selector.split(">") if s]
    terminal = segments[-1] if segments else selector
    terminal_tag = _terminal_tag(terminal)

    region, is_admin = _region_of(selector)
    component = _component_of(selector, terminal, terminal_tag)

    interactive = (
        terminal_tag in _INTERACTIVE_TAGS
        or any(tok in terminal for tok in _INTERACTIVE_TOKENS)
        or "elementor-button" in selector and "button-text" in terminal
    )
    interactivity = "interactive" if interactive else "non-interactive"
    is_dead = (not interactive) and (not is_admin)

    if is_admin:
        label = f"{region} → {component} (owner/admin click — excluded)"
    elif is_dead:
        label = f"{region} → {component} (non-interactive — dead-click candidate)"
    else:
        label = f"{region} → {component} (interactive)"

    return ElementLabel(
        region=region,
        component=component,
        interactivity=interactivity,
        label=label,
        is_admin_noise=is_admin,
        is_dead_click_candidate=is_dead,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_clarity_parser.py -k humanize -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add utils/clarity_parser.py tests/test_clarity_parser.py
git commit -m "feat(clarity): humanize Elementor CSS selectors + dead-click detection"
```

---

### Task 4: Profile builders + computed metrics

**Files:**
- Modify: `utils/clarity_parser.py`
- Test: `tests/test_clarity_parser.py`

**Interfaces:**
- Consumes: `ClarityExport`, `humanize_selector`, `parse_time_to_seconds`.
- Produces:
  - `ScrollProfile` (frozen: `rows: tuple[tuple[int,int,float],...]; page_views: int; reach_25/reach_50/reach_75/reach_100: float; attention_cliff_depth: Optional[int]; steepest_drop_band: tuple[int,int]`); `build_scroll_profile(exp) -> ScrollProfile`.
  - `AttentionProfile` (frozen: `rows: tuple[tuple[int,int,float],...]; top_band: tuple[int,float]; secondary_spike: Optional[tuple[int,float]]; pct_session_top25: float; pct_session_bottom25: float`); `build_attention_profile(exp) -> AttentionProfile`.
  - `ClickElement` (frozen: `rank: int; raw_selector: str; clicks: int; pct_clicks: float; label: ElementLabel`); `ClickProfile` (frozen: `elements: tuple[ClickElement,...]; total_clicks: int; admin_noise_rows: int; admin_noise_clicks: int; region_distribution: dict[str,float]; dead_click_candidates: tuple[ClickElement,...]; head_share_top5: float`); `build_click_profile(exp) -> ClickProfile`.

- [ ] **Step 1: Write the failing tests**

```python
from utils.clarity_parser import (
    build_scroll_profile, build_attention_profile, build_click_profile,
)


def _click_exp():
    return parse_clarity_csv(FIXTURES / "Clarity_Beehive_Click_PC_06-27-2026 05 05 PM.csv", device="PC")


def _scroll_exp():
    return parse_clarity_csv(FIXTURES / "Clarity_Beehive_Scroll_PC_06-27-2026 05 06 PM.csv", device="PC")


def _attn_exp():
    return parse_clarity_csv(FIXTURES / "Clarity_Beehive_Attention_PC_06-27-2026 05 07 PM.csv", device="PC")


def test_scroll_profile_reach_and_cliff():
    p = build_scroll_profile(_scroll_exp())
    assert p.reach_25 == pytest.approx(10.24, abs=0.01)
    assert p.reach_100 == pytest.approx(4.18, abs=0.01)
    assert p.attention_cliff_depth == 5
    assert p.steepest_drop_band == (5, 10)


def test_attention_profile_bands():
    p = build_attention_profile(_attn_exp())
    assert p.top_band == (5, pytest.approx(33.95, abs=0.01))
    assert p.secondary_spike[0] == 95
    assert p.pct_session_top25 == pytest.approx(75.45, abs=0.05)


def test_click_profile_excludes_admin_noise_and_finds_dead_candidates():
    p = build_click_profile(_click_exp())
    assert p.total_clicks == 498
    assert p.admin_noise_rows == 1
    assert p.admin_noise_clicks == 4
    assert len(p.elements) == 4            # 5 rows - 1 admin row
    assert len(p.dead_click_candidates) == 2   # background overlay + heading
    # region distribution over non-noise clicks (Header 34 of 49, Main 15 of 49)
    assert p.region_distribution["Header"] == pytest.approx(69.39, abs=0.1)
    assert p.region_distribution["Main"] == pytest.approx(30.61, abs=0.1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_clarity_parser.py -k "profile" -v`
Expected: FAIL with `ImportError` for `build_scroll_profile`

- [ ] **Step 3: Add the implementation** (append to `utils/clarity_parser.py`)

```python
def _pct(value: str) -> float:
    return float(value.replace("%", "").strip())


@dataclass(frozen=True)
class ScrollProfile:
    rows: tuple[tuple[int, int, float], ...]
    page_views: int
    reach_25: float
    reach_50: float
    reach_75: float
    reach_100: float
    attention_cliff_depth: Optional[int]
    steepest_drop_band: tuple[int, int]


def build_scroll_profile(exp: ClarityExport) -> ScrollProfile:
    rows = tuple((int(r[0]), _to_int(r[1]), _pct(r[2])) for r in exp.rows)
    by_depth = {d: (v, do) for d, v, do in rows}

    def reach(depth: int) -> float:
        if depth in by_depth:
            return round(100.0 - by_depth[depth][1], 2)
        return 0.0

    cliff = next((d for d, _v, do in rows if do >= 50.0), None)

    steepest = (0, 0)
    max_loss = -1
    for (d1, v1, _), (d2, v2, _) in zip(rows, rows[1:]):
        loss = v1 - v2
        if loss > max_loss:
            max_loss = loss
            steepest = (d1, d2)

    return ScrollProfile(
        rows=rows,
        page_views=exp.meta.page_views,
        reach_25=reach(25),
        reach_50=reach(50),
        reach_75=reach(75),
        reach_100=reach(100),
        attention_cliff_depth=cliff,
        steepest_drop_band=steepest,
    )


@dataclass(frozen=True)
class AttentionProfile:
    rows: tuple[tuple[int, int, float], ...]
    top_band: tuple[int, float]
    secondary_spike: Optional[tuple[int, float]]
    pct_session_top25: float
    pct_session_bottom25: float


def build_attention_profile(exp: ClarityExport) -> AttentionProfile:
    rows = tuple(
        (int(r[0]), parse_time_to_seconds(r[1]), _pct(r[2])) for r in exp.rows
    )
    top = max(rows, key=lambda t: t[2])
    top_band = (top[0], top[2])

    below = [(d, p) for d, _s, p in rows if d >= 60]
    secondary = max(below, key=lambda t: t[1]) if below else None

    top25 = round(sum(p for d, _s, p in rows if d <= 25), 2)
    bottom25 = round(sum(p for d, _s, p in rows if d >= 75), 2)

    return AttentionProfile(
        rows=rows,
        top_band=top_band,
        secondary_spike=secondary,
        pct_session_top25=top25,
        pct_session_bottom25=bottom25,
    )


@dataclass(frozen=True)
class ClickElement:
    rank: int
    raw_selector: str
    clicks: int
    pct_clicks: float
    label: ElementLabel


@dataclass(frozen=True)
class ClickProfile:
    elements: tuple[ClickElement, ...]
    total_clicks: int
    admin_noise_rows: int
    admin_noise_clicks: int
    region_distribution: dict
    dead_click_candidates: tuple[ClickElement, ...]
    head_share_top5: float


def build_click_profile(exp: ClarityExport) -> ClickProfile:
    all_elements = []
    for r in exp.rows:
        rank, selector, clicks, pct = int(r[0]), r[1], _to_int(r[2]), _pct(r[3])
        all_elements.append(
            ClickElement(rank, selector, clicks, pct, humanize_selector(selector))
        )

    noise = [e for e in all_elements if e.label.is_admin_noise]
    kept = tuple(e for e in all_elements if not e.label.is_admin_noise)

    kept_total = sum(e.clicks for e in kept)
    region_clicks: dict[str, int] = {}
    for e in kept:
        region_clicks[e.label.region] = region_clicks.get(e.label.region, 0) + e.clicks
    region_distribution = {
        region: round(c / kept_total * 100, 2) if kept_total else 0.0
        for region, c in region_clicks.items()
    }

    dead = tuple(e for e in kept if e.label.is_dead_click_candidate)
    top5 = sorted(kept, key=lambda e: e.clicks, reverse=True)[:5]
    head_share = round(sum(e.clicks for e in top5) / kept_total * 100, 2) if kept_total else 0.0

    return ClickProfile(
        elements=kept,
        total_clicks=exp.meta.total_clicks or 0,
        admin_noise_rows=len(noise),
        admin_noise_clicks=sum(e.clicks for e in noise),
        region_distribution=region_distribution,
        dead_click_candidates=dead,
        head_share_top5=head_share,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_clarity_parser.py -k "profile" -v`
Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add utils/clarity_parser.py tests/test_clarity_parser.py
git commit -m "feat(clarity): scroll/attention/click profile metrics"
```

---

### Task 5: `normalize()` orchestrator + graceful degradation

**Files:**
- Modify: `utils/clarity_parser.py`
- Test: `tests/test_clarity_parser.py`

**Interfaces:**
- Consumes: all builders above.
- Produces:
  - `DeviceAnalysis` (frozen: `device: str; meta: ClarityMeta; scroll: Optional[ScrollProfile]; attention: Optional[AttentionProfile]; click: Optional[ClickProfile]; missing_metrics: tuple[str,...]; png_files: tuple[Path,...]`).
  - `ClarityAnalysis` (frozen: `client: str; page_label: str; devices: tuple[DeviceAnalysis,...]; warnings: tuple[str,...]`).
  - `discover_clarity_files(clarity_dir: Path) -> tuple[ClarityFile,...]`.
  - `normalize(client: str, project_root: Optional[Path] = None) -> ClarityAnalysis`.

- [ ] **Step 1: Write the failing tests**

```python
from utils.clarity_parser import discover_clarity_files, normalize, ClarityAnalysis


def test_discover_groups_three_metrics(tmp_path):
    # copy the three fixtures into a fake client Clarity dir
    import shutil
    cdir = tmp_path / "Clients" / "Beehive" / "Clarity"
    cdir.mkdir(parents=True)
    for f in FIXTURES.glob("*.csv"):
        shutil.copy(f, cdir / f.name)
    found = discover_clarity_files(cdir)
    metrics = sorted(f.metric for f in found)
    assert metrics == ["Attention", "Click", "Scroll"]


def test_normalize_builds_one_device_with_all_profiles(tmp_path):
    import shutil
    cdir = tmp_path / "Clients" / "Beehive" / "Clarity"
    cdir.mkdir(parents=True)
    for f in FIXTURES.glob("*.csv"):
        shutil.copy(f, cdir / f.name)
    analysis = normalize("Beehive", project_root=tmp_path)
    assert isinstance(analysis, ClarityAnalysis)
    assert len(analysis.devices) == 1
    dev = analysis.devices[0]
    assert dev.device == "PC"
    assert dev.scroll is not None and dev.attention is not None and dev.click is not None
    assert dev.missing_metrics == ()


def test_normalize_flags_low_click_sample(tmp_path):
    import shutil
    cdir = tmp_path / "Clients" / "Beehive" / "Clarity"
    cdir.mkdir(parents=True)
    for f in FIXTURES.glob("*.csv"):
        shutil.copy(f, cdir / f.name)
    analysis = normalize("Beehive", project_root=tmp_path)
    # 498 clicks < 1000 → a directional-confidence warning must be present
    assert any("click" in w.lower() for w in analysis.warnings)


def test_normalize_missing_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        normalize("Nonexistent", project_root=tmp_path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_clarity_parser.py -k normalize -v`
Expected: FAIL with `ImportError` for `normalize`

- [ ] **Step 3: Add the implementation** (append to `utils/clarity_parser.py`)

```python
_MIN_RELIABLE_SAMPLE = 1000


@dataclass(frozen=True)
class DeviceAnalysis:
    device: str
    meta: ClarityMeta
    scroll: Optional[ScrollProfile]
    attention: Optional[AttentionProfile]
    click: Optional[ClickProfile]
    missing_metrics: tuple[str, ...]
    png_files: tuple[Path, ...]


@dataclass(frozen=True)
class ClarityAnalysis:
    client: str
    page_label: str
    devices: tuple[DeviceAnalysis, ...]
    warnings: tuple[str, ...]


def discover_clarity_files(clarity_dir: Path) -> tuple[ClarityFile, ...]:
    found = []
    for p in sorted(clarity_dir.iterdir()):
        if not p.is_file():
            continue
        cf = parse_filename(p.name, path=p)
        if cf is not None:
            found.append(cf)
    return tuple(found)


def normalize(client: str, project_root: Optional[Path] = None) -> ClarityAnalysis:
    root = project_root if project_root is not None else Path(__file__).parent.parent
    clarity_dir = root / "Clients" / client / "Clarity"
    if not clarity_dir.exists():
        raise FileNotFoundError(f"No Clarity directory found: {clarity_dir}")

    files = discover_clarity_files(clarity_dir)
    warnings: list[str] = []

    by_device: dict[str, dict[str, ClarityFile]] = {}
    pngs: dict[str, list[Path]] = {}
    for f in files:
        if f.ext == "png":
            pngs.setdefault(f.device, []).append(f.path)
            continue
        by_device.setdefault(f.device, {})[f.metric] = f

    devices: list[DeviceAnalysis] = []
    page_label = ""
    for device, metrics in sorted(by_device.items()):
        scroll = attention = click = None
        meta = None
        present = set()
        if "Scroll" in metrics:
            exp = parse_clarity_csv(metrics["Scroll"].path, device=device)
            scroll, meta, present = build_scroll_profile(exp), exp.meta, present | {"Scroll"}
        if "Attention" in metrics:
            exp = parse_clarity_csv(metrics["Attention"].path, device=device)
            attention = build_attention_profile(exp)
            meta = meta or exp.meta
            present |= {"Attention"}
        if "Click" in metrics:
            exp = parse_clarity_csv(metrics["Click"].path, device=device)
            click = build_click_profile(exp)
            meta = exp.meta  # prefer Click meta (has total_clicks)
            present |= {"Click"}
        if meta is None:
            continue
        page_label = page_label or meta.url_regex
        missing = tuple(m for m in METRICS if m not in present)

        if meta.page_views < _MIN_RELIABLE_SAMPLE:
            warnings.append(
                f"{device}: {meta.page_views} page views (<{_MIN_RELIABLE_SAMPLE}) — "
                f"scroll/attention are directional, not statistically reliable."
            )
        if click is not None and click.total_clicks < _MIN_RELIABLE_SAMPLE:
            warnings.append(
                f"{device}: {click.total_clicks} total clicks (<{_MIN_RELIABLE_SAMPLE}) — "
                f"click findings are directional."
            )
        for m in missing:
            warnings.append(f"{device}: '{m}' export missing — that analysis cannot run.")

        devices.append(DeviceAnalysis(
            device=device, meta=meta, scroll=scroll, attention=attention,
            click=click, missing_metrics=missing,
            png_files=tuple(pngs.get(device, [])),
        ))

    if not devices:
        warnings.append("No parseable Clarity CSV exports found.")

    return ClarityAnalysis(
        client=client, page_label=page_label,
        devices=tuple(devices), warnings=tuple(warnings),
    )
```

- [ ] **Step 4: Run the full test suite**

Run: `pytest tests/test_clarity_parser.py -v`
Expected: all passed

- [ ] **Step 5: Smoke-test against the real Beehive data**

Run: `python -c "from utils.clarity_parser import normalize; a = normalize('Beehive'); print(a.page_label); [print(d.device, d.missing_metrics, d.click.dead_click_candidates[:1] if d.click else None) for d in a.devices]; print(a.warnings)"`
Expected: prints the Beehive homepage regex, device `PC`, empty missing-metrics, a dead-click candidate, and the low-click-sample warning. (If it errors on the real files, fix the parser — the real Click CSV has 83 rows incl. 7 admin-bar.)

- [ ] **Step 6: Commit**

```bash
git add utils/clarity_parser.py tests/test_clarity_parser.py
git commit -m "feat(clarity): normalize() orchestrator with sample-size + missing-metric warnings"
```

---

### Task 6: Methodology skill + curated references

**Files:**
- Create: `Skills/clarity-ux-analysis/SKILL.md`
- Create: `Skills/clarity-ux-analysis/references/clarity-cro-methodology.md` (curated copy of `temp-files/Microsoft Clarity Heatmap Analysis  A Comprehensive CRO & UX Research Methodology Guide.md`)
- Create: `Skills/clarity-ux-analysis/references/clarity-technical-diagnostic.md` (curated copy of `temp-files/Microsoft Clarity Heatmap Analysis Framework.md`)

**Interfaces:** none (documentation). Referenced by the slash command and CLAUDE.md.

- [ ] **Step 1: Copy the two guides into the skill's references folder**

```bash
mkdir -p "Skills/clarity-ux-analysis/references"
cp "temp-files/Microsoft Clarity Heatmap Analysis  A Comprehensive CRO & UX Research Methodology Guide.md" "Skills/clarity-ux-analysis/references/clarity-cro-methodology.md"
cp "temp-files/Microsoft Clarity Heatmap Analysis Framework.md" "Skills/clarity-ux-analysis/references/clarity-technical-diagnostic.md"
```

- [ ] **Step 2: Write `Skills/clarity-ux-analysis/SKILL.md`** with this exact content:

````markdown
---
name: clarity-ux-analysis
description: Analyze Microsoft Clarity heatmap exports (Click/Scroll/Attention CSVs + PNGs) into an internal CRO report and a client-facing UX report. Use when a client has Clarity data and asks "what are users doing on this page / why aren't they converting", or when an audit needs behavioral evidence. NOT an API integration — ingests manual dashboard exports from Clients/<name>/Clarity/.
---

# Clarity UX Analysis

## When to use
A client folder has Clarity exports under `Clients/<name>/Clarity/` (Click/Scroll/Attention CSVs, optional PNG heatmaps) and you need behavioral findings + prioritized UX/CRO recommendations. Driven by the `/clarity-report` command.

## Inputs & prerequisites
- Required: at least a Scroll or Click CSV. Best: all three metrics per device.
- Optional: PNG heatmaps (you interpret these visually), GA4 conversion data (for revenue numbers).
- Run `utils/clarity_parser.normalize("<client>")` to get a `ClarityAnalysis` (per-device profiles + warnings). Read PNGs directly with the Read tool.

## Capability boundary (READ FIRST — non-negotiable)
The export contains **All-Clicks + Scroll + Attention only**. Therefore:
- **Provable:** scroll reach/cliff, attention distribution, ranked element clicks, region split.
- **Inferred only — label as such, flag for verification:** dead-click *candidates* (non-interactive elements receiving clicks). NEVER call these "Clarity-confirmed dead clicks."
- **Absent — never present as run:** Dead/Rage/First/Last-click maps, session recordings, conversion/area maps, GA4-linked revenue.
- Before asserting any dead-click finding, apply the **async-misclassification check** (`references/clarity-technical-diagnostic.md`): on JS-driven elements a delayed DOM update can look like a dead click. Beehive is Elementor/WordPress (low risk) but state the caveat.

## Data-quality gates
- Heatmap reliability needs ≈1,000+ users/page. Below that, label findings "directional." (Parser emits these warnings — surface them.)
- Admin-bar clicks (`#wp-admin-bar*`) are the logged-in owner: excluded from analysis, reconciled in a footnote.
- Static-PNG blind spots: dropdowns/hover/modals aren't captured; scroll tracks `<body>` only; layouts >65,535px don't render. Note when relevant.

## Interpretation framework
Per metric, combine the parser's computed numbers with judgment (full taxonomies in `references/clarity-cro-methodology.md`):
- **Scroll** — fold vs. CTA placement; the attention-cliff depth; false-bottom risk.
- **Attention** — where genuine dwell sits vs. skipped content; secondary spikes (footer/contact pull).
- **Click** — region pull (header/main/footer %), head-vs-tail concentration, dead-click candidates.
- **Cross-metric synthesis (highest value):** attention-click correlation (high attention + low clicks = copy failing; high attention + dead-click candidate = critical friction); "X% of clicks target elements below the Y% fold only Z% of visitors reach."

## Prioritization — ICE + mandatory fields
Score each recommendation ICE (Impact × Confidence × Ease, 1–10 each; Confidence capped at ~5 when based on heatmap alone, higher only with corroborating GA4/recording evidence). Then attach the mandatory fields from `.claude/rules/audit-workflow.md`:
- Priority (P0–P4), Effort, Expected outcome (Ranking Lever | Infrastructure Hygiene | Risk Mitigation | UX-indirect — most Clarity findings are UX/conversion), Likely effect (one sentence), Validation method (one specific instruction).

## Revenue framing
Include lead/$ impact ONLY when grounded in real GA4 conversion data the user supplied. Otherwise keep it qualitative or as a clearly-labeled conditional ("IF completions rose 20%, that's ~N leads/mo — estimate, assumption stated"). Never invent hard figures.

## Internal report structure
`Clients/<name>/Clarity/reports/clarity_ux_internal_<page-slug>_<device>.md`
1. Summary (sessions, devices, top 3 findings) 2. Analysis parameters + data-quality notes 3. Click findings (incl. dead-click candidates table) 4. Scroll findings 5. Attention findings 6. Cross-metric findings 7. ICE-scored backlog (≤6 cols) 8. Methodology footer.

## Client report structure
`Clients/<name>/Clarity/reports/clarity_ux_client_<page-slug>_<device>.md`
1. Overview (plain language) 2. What's working well 3. Top 3 opportunities (What we found / What it means / What we recommend — each with ICE + mandatory fields) 4. Quick wins 5. Recommended next steps (≤6-col table, NO timelines). Real GA4 numbers only. No internal-doc references. Full URLs.

## Pre-delivery QA
Run `Skills/data-analysis/pre-delivery-qa/SKILL.md`. Dispatch: `data-validator` (every cited number), `recommendation-sanity-checker` (proposed copy/CTA rewrites), `live-url-verifier` (any rec naming a target URL). Confirm: dead-click claims labeled inferred; admin noise reconciled; no timeline language; tables ≤6 cols; URLs full.

## References
- `references/clarity-cro-methodology.md` — friction taxonomies, scenario matrices, report templates, health benchmarks.
- `references/clarity-technical-diagnostic.md` — DOM-elements tracking, technical boundaries, async dead-click misclassification, dual-audience matrix.
````

- [ ] **Step 3: Verify the files exist and the skill frontmatter is valid**

Run: `ls -1 "Skills/clarity-ux-analysis" "Skills/clarity-ux-analysis/references" && head -4 "Skills/clarity-ux-analysis/SKILL.md"`
Expected: lists `SKILL.md` + `references/` with both `.md` files; frontmatter shows `name: clarity-ux-analysis`.

- [ ] **Step 4: Commit**

```bash
git add "Skills/clarity-ux-analysis/"
git commit -m "feat(clarity): add clarity-ux-analysis skill + curated references"
```

---

### Task 7: `/clarity-report` slash command

**Files:**
- Create: `.claude/commands/clarity-report.md`

**Interfaces:** none (command). Invokes the skill above.

- [ ] **Step 1: Write `.claude/commands/clarity-report.md`** with this exact content:

````markdown
---
description: Analyze a client's Microsoft Clarity heatmap exports (Click/Scroll/Attention CSVs + PNGs) and produce an internal CRO report and a client-facing UX report. Ingests manual dashboard exports from Clients/<name>/Clarity/ — not the Clarity API. Use when a client has Clarity data and you need behavioral findings + prioritized UX recommendations.
---

# /clarity-report

You are running a Clarity heatmap UX analysis. Take a client's manually-exported Clarity data and produce an internal CRO report and a client-facing UX report, following `Skills/clarity-ux-analysis/SKILL.md` exactly.

## Required inputs
1. **Client folder name** (e.g. `Beehive`) — must contain `Clients/<name>/Clarity/` with at least one CSV.

Optional:
2. **Device filter** (PC | Mobile | Tablet) — default: analyze every device present.
3. **Report type** (internal | client | both) — default: both.
4. **GA4 conversion data** — `--with-ga4` to pull conversion numbers for revenue framing (uses `fetchers/fetch_ga4.py` / GA4 MCP). Without it, the client report stays qualitative.

If the client name is missing, ask. Do not proceed with placeholders.

## Pre-flight (before any analysis)
1. Run `python -c "from utils.clarity_parser import normalize; ..."` (or import in-session) to get the `ClarityAnalysis`.
2. If `Clients/<name>/Clarity/` is missing → stop, tell the user where to drop exports.
3. Print a one-paragraph data-quality summary FIRST: page label, devices found, metrics present/missing per device, page views + total clicks, and every `analysis.warnings` entry (sample size, missing metrics).
4. If only PNGs and no CSVs → tell the user CSVs are required for quantitative findings; offer image-only qualitative read.

## Workflow
Follow the skill's methodology verbatim:
1. Normalize the CSVs (`utils/clarity_parser.normalize`).
2. Read each PNG heatmap with the Read tool and interpret it visually.
3. Apply the interpretation framework + cross-metric synthesis.
4. If `--with-ga4`, pull conversion data and ground revenue numbers; else keep qualitative.
5. Score recommendations ICE + attach mandatory fields.
6. Write the report(s).

## Deliverables
Per the skill's "Internal report structure" and "Client report structure". Every recommendation carries ICE score + Priority/Effort/Expected-outcome/Likely-effect/Validation-method. No timeline language. Tables ≤6 columns. Full URLs. No internal-doc references in the client report.

## Output routing
Write to `Clients/<name>/Clarity/reports/`:
- `clarity_ux_internal_<page-slug>_<device>.md`
- `clarity_ux_client_<page-slug>_<device>.md`
`<page-slug>` derives from the export's URL regex (homepage → `home`). Then show the user a 5-line summary + file paths.

## Pre-delivery QA
Run `Skills/data-analysis/pre-delivery-qa/SKILL.md` and dispatch `data-validator`, `recommendation-sanity-checker`, and (if any target URL is proposed) `live-url-verifier`. Confirm dead-click claims are labeled inferred and admin noise is reconciled.

## Capability boundary (state in every report's methodology footer)
This analysis uses All-Clicks + Scroll + Attention exports only. Dead clicks are candidates inferred from element interactivity, not Clarity-confirmed. Dead/Rage/First/Last maps, session recordings, and conversion maps are dashboard-only and were not used.

## Related
- `Skills/clarity-ux-analysis/SKILL.md` — the methodology this command runs
- `utils/clarity_parser.py` — the normalizer
- `.claude/rules/audit-workflow.md` — mandatory recommendation fields
- `Skills/data-analysis/pre-delivery-qa/SKILL.md` — required QA before delivery
````

- [ ] **Step 2: Verify the command file**

Run: `head -4 ".claude/commands/clarity-report.md"`
Expected: frontmatter `description:` present and starts the file.

- [ ] **Step 3: Commit**

```bash
git add ".claude/commands/clarity-report.md"
git commit -m "feat(clarity): add /clarity-report slash command"
```

---

### Task 8: Wire into project docs + final verification

**Files:**
- Modify: `CLAUDE.md` (Specialized Skills section)
- Modify: `requirements.txt` (only if a comment line is wanted; no new deps)

**Interfaces:** none.

- [ ] **Step 1: Add a "Specialized Skills" entry to `CLAUDE.md`**

Under the `## Specialized Skills` list, add this bullet (match the existing bullet style):

```markdown
- **Microsoft Clarity heatmap UX analysis ("analyze our Clarity data", "why aren't users converting on this page")** → use [Skills/clarity-ux-analysis/SKILL.md](Skills/clarity-ux-analysis/SKILL.md) via the `/clarity-report` command. Ingests manual Clarity dashboard exports (Click/Scroll/Attention CSVs + PNGs) from `Clients/<name>/Clarity/` and produces an internal CRO report + a client-facing UX report. NOT the Clarity API (the API caps at 3 days and exposes no heatmaps). Normalizer: `utils/clarity_parser.py`.
```

- [ ] **Step 2: Run the full parser test suite once more**

Run: `pytest tests/test_clarity_parser.py -v`
Expected: all passed.

- [ ] **Step 3: Confirm no stray dependency was introduced**

Run: `python -c "import ast,sys; src=open('utils/clarity_parser.py').read(); mods={n.module.split('.')[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom) and n.module}; mods|={a.name.split('.')[0] for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import) for a in n.names}; print(sorted(mods))"`
Expected: only stdlib names (`__future__`, `csv`, `dataclasses`, `pathlib`, `re`, `typing`). If anything else appears, remove it.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(clarity): register clarity-ux-analysis skill + /clarity-report in CLAUDE.md"
```

---

## Self-Review (completed by plan author)

**Spec coverage:** normalizer (Tasks 1–5), skill + references (Task 6), command (Task 7), tests (Tasks 1–5), docs wiring (Task 8), capability boundary + revenue + ICE + formatting constraints (Global Constraints + Tasks 6–7). All spec sections map to a task.

**Placeholder scan:** all code and markdown content is provided in full; no TBD/TODO/"similar to" references.

**Type consistency:** `ClarityFile`, `ClarityMeta`, `ClarityExport`, `ElementLabel`, `ScrollProfile`, `AttentionProfile`, `ClickElement`, `ClickProfile`, `DeviceAnalysis`, `ClarityAnalysis` and functions `parse_filename`, `parse_clarity_csv`, `parse_time_to_seconds`, `humanize_selector`, `build_scroll_profile`, `build_attention_profile`, `build_click_profile`, `discover_clarity_files`, `normalize` are defined once and consumed with matching signatures across tasks.
