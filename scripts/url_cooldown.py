"""A URL worked in a prior workbook is off limits for 90 days.

    python scripts/url_cooldown.py <client> 2.3            # what is blocked
    python scripts/url_cooldown.py <client> 2.3 <url> ...  # check URLs

THE RULE (from the October 2026 template)
-----------------------------------------
One 90-day cooldown across the whole 2.3 tab. A URL that sat on any of the
old title-and-refresh tabs ("2.3-3.1 Refresh Log", "2.5 Quick Wins", the
September " Page Optimization") or on a Pages row of a "2.3 Page
Optimizations" tab in the previous COOLDOWN_MONTHS months is blocked from 2.3.
A page worked in August is back in play in December.

Rows carried over UNFINISHED from last month are exempt until they ship: a page
whose refresh was assigned and never completed is not a page we have optimized,
so the cooldown does not stand between it and the work. Finished means a Date
Done / Date Live on the old tabs, or no open Changes row plus a Date Live (or a
"No change needed" verdict) on a new-layout Pages row. See decide().

Both rules are OWNER-PENDING DEFAULTS (D1). Each sits behind one constant:

    COOLDOWN_MONTHS    = 3      # the window
    CARRYOVER_EXEMPT   = True   # False makes an unfinished carryover block too

Prior workbooks from before November have the old three-tab layout and
workbooks from November on have the new one, so a lookup reads whichever the
workbook has. Anything that WRITES the current month targets the new layout
only.

The cooldown is scoped to this tab family, not the whole workbook: a page worked
for internal links last month is not thereby blocked from a title rewrite,
because blocking across tabs freezes a site (1.1 relists the same top pages
every month by definition). Any tab key other than 2.3 keeps the older
prefix-matched behaviour, limited to the same month window.

WHY THIS IS CODE AND NOT A NOTE
-------------------------------
It was violated on 2026-09-08 after being stated: two Superior URLs were found
in the August workbook, the overlap was reported out loud, and they shipped
anyway on an exemption invented on the spot. A reminder had already failed, so
the check lives where it cannot be skipped. Call blocked() before writing any
candidate and assert_clear() to turn a violation into a crash rather than a
deliverable.

Public API, unchanged for existing callers: canon, prior_sheet_ids, blocked,
assert_clear, same_month, assert_no_same_month, COOLDOWN_MONTHS. New:
family_state (blocked + carryover-exempt), carried_over, workbook_family_urls,
family_rows (raw rows of a workbook's 2.3-family tabs, either layout), in_window.

A tab that cannot be read raises CooldownUnreadable instead of being skipped: a
gate that cannot see its source must not pass. Lookups take an optional `errors`
list for callers (the repeat checks) that would rather collect the failures and
report them than stop.
"""
from __future__ import annotations

import re
import sys
import time
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import page_opt_tab  # noqa: E402
import sheets_io  # noqa: E402

URL_RE = re.compile(r'https?://[^\s"\'<>,)\]]+', re.I)

# Owner-pending default D1: one 90-day cooldown across the whole 2.3 tab.
COOLDOWN_MONTHS = 3
# The 1.5 candidate gate looks further back than the 2.3 cooldown: a page worked or offered in ANY of the
# last six workbook months is not put forward as a candidate. Owner instruction 2026-10-06, for the 1.5 tab
# only. COOLDOWN_MONTHS stays the window for 2.3, 1.7 and 1.8.
CANDIDATE_LOOKBACK_MONTHS = 6
# Owner-pending default D1: rows carried over unfinished from last month are
# exempt until they ship. Set False and they block like any other row.
CARRYOVER_EXEMPT = True

# Tab keys that mean "the merged 2.3 family".
FAMILY_KEYS = ("2.3", "2.3 page optimizations")

# Tabs that carry title work. A URL on any of these is spoken for THIS month.
# "3.1" and "2.4" are deliberately gone: from October "3.1" is Internal Links.
TITLE_WORK_TABS = ("2.3 Page Optimizations", "2.3-3.1", "2.5",
                   "Page Optimization")

# How much of an old tab to read. The Refresh Log runs to column P.
OLD_TAB_RANGE = "A1:P100"


def canon(u: str) -> str:
    """Compare URLs the way a person would: no scheme, www, query or slash."""
    u = u.split("?")[0].split("#")[0].strip().lower()
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/")


def prior_sheet_ids(cfg: dict) -> dict[str, str]:
    """Every prior-month sheet the registry records for this client."""
    return {k.replace("sheet_id_", ""): v for k, v in cfg.items()
            if k.startswith("sheet_id_") and v}


# --- registry ---------------------------------------------------------------

def _registry() -> dict:
    return yaml.safe_load(
        Path("clients/registry.yaml").read_text(encoding="utf-8"))


def _client_key(reg: dict, client: str) -> str:
    key = next((k for k, v in reg.items()
                if isinstance(v, dict) and "folder" in v
                and client.lower() in (k.lower(), v["name"].lower())), None)
    if key is None:
        raise SystemExit(f"unknown client {client!r}")
    return key


# --- month window -----------------------------------------------------------

def months_ago(month_key: str, today: date) -> int | None:
    """Whole months between a registry month key ("2026_09") and today."""
    m = re.fullmatch(r"(\d{4})_(\d{2})", month_key)
    if not m:
        return None
    return (today.year - int(m.group(1))) * 12 + (today.month - int(m.group(2)))


def in_window(month_key: str, today: date,
              months: int = COOLDOWN_MONTHS) -> bool:
    """A prior month is inside the cooldown when it is 1..months months back."""
    ago = months_ago(month_key, today)
    return ago is not None and 1 <= ago <= months


# --- what is on the family tabs, by layout ----------------------------------

def tab_kind(name: str) -> str | None:
    """Which member of the 2.3 family a tab is, or None."""
    n = name.strip().lower()
    if n.startswith("2.3 page optimizations"):
        return "pages"
    if n.startswith("2.3-3.1"):
        return "refresh_log"
    if n.startswith("2.5"):
        return "quick_wins"
    if n.startswith("page optimization"):
        return "page_opt"
    return None


def _norm_h(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def _header(vals: list[list], first_cell: str) -> tuple[int, list[str]] | None:
    for i, row in enumerate(vals):
        if row and _norm_h(row[0]) == first_cell:
            return i, [_norm_h(c) for c in row]
    return None


def _cell(row: list, idx: int | None) -> str:
    return str(row[idx]).strip() if idx is not None and idx < len(row) else ""


def parse_refresh_log(vals: list[list]) -> list[tuple[str, bool, int]]:
    """(url, finished, row) from the old "2.3-3.1 Refresh Log". Done = Date Done."""
    h = _header(vals, "clickup task")
    if h is None:
        raise ValueError("no 'ClickUp Task' header row")
    at, hdr = h
    try:
        u_i, d_i = hdr.index("page url"), hdr.index("date done")
    except ValueError as e:
        raise ValueError(f"refresh log header drifted: {hdr}") from e
    out = []
    for i in range(at + 1, len(vals)):
        row = vals[i]
        if row and _norm_h(row[0]).startswith("unviable"):
            break
        url = _cell(row, u_i)
        if url.lower().startswith("http"):
            out.append((url, bool(_cell(row, d_i)), i + 1))
    return out


def parse_quick_wins(vals: list[list]) -> list[tuple[str, bool, int]]:
    """(url, finished, row) from the old "2.5 Quick Wins". Done = Date Live."""
    h = _header(vals, "page url")
    if h is None:
        raise ValueError("no 'Page URL' header row")
    at, hdr = h
    try:
        d_i = hdr.index("date live")
    except ValueError as e:
        raise ValueError(f"2.5 header drifted: {hdr}") from e
    out = []
    for i in range(at + 1, len(vals)):
        url = _cell(vals[i], 0)
        if url.lower().startswith("http"):
            out.append((url, bool(_cell(vals[i], d_i)), i + 1))
    return out


def parse_page_opt(vals: list[list]) -> list[tuple[str, bool, int]]:
    """(url, finished, first_row) from the September " Page Optimization".

    A page is finished when none of its rows is still "To do" or blank. The
    September tab had its header row twice on some workbooks, so a header row
    reads as no data.
    """
    u_i = s_i = None
    first: dict[str, int] = {}
    states: dict[str, list[str]] = {}
    for i, row in enumerate(vals):
        cells = [_norm_h(c) for c in row]
        if "url" in cells and "status" in cells:
            u_i, s_i = cells.index("url"), cells.index("status")
            continue
        if u_i is None:
            continue
        url = _cell(row, u_i)
        if not url.lower().startswith("http"):
            continue
        first.setdefault(url, i + 1)
        states.setdefault(url, []).append(_norm_h(_cell(row, s_i)))
    if u_i is None:
        raise ValueError("no URL/Status header row")
    return [(u, all(s not in ("", "to do") for s in st), first[u])
            for u, st in states.items()]


def parse_pages_tab(pages: list[page_opt_tab.PageRow],
                    changes: list[page_opt_tab.ChangeRow]
                    ) -> list[tuple[str, bool, int]]:
    """(url, finished, row) from a new-layout tab.

    Finished = no open ("To do") Changes row for the URL, AND some evidence the
    page was completed: a Date Live, a "No change needed" verdict, or a Done
    Changes row.
    """
    open_urls = {canon(c.url) for c in changes
                 if c.status.strip().lower() == "to do"}
    done_urls = {canon(c.url) for c in changes
                 if c.status.strip().lower() == "done"}
    out = []
    for p in pages:
        if not p.url.lower().startswith("http"):
            continue
        k = canon(p.url)
        evidence = (bool(p.date_live)
                    or p.change.strip().lower() == "no change needed"
                    or k in done_urls)
        out.append((p.url, k not in open_urls and evidence, p.row))
    return out


_PARSERS = {"refresh_log": parse_refresh_log, "quick_wins": parse_quick_wins,
            "page_opt": parse_page_opt}


class CooldownUnreadable(RuntimeError):
    """A tab the cooldown depends on could not be read.

    A gate that cannot read its source must not pass: an unread tab
    contributes no URLs, so continuing would quietly let blocked pages through.
    Pass an `errors` list to a lookup to collect these instead of raising.
    """


def _unreadable(name: str, e: Exception, errors: list[str] | None) -> None:
    detail = (str(e).splitlines() or [""])[0][:120]
    msg = f"could not read {name!r}: {e.__class__.__name__}: {detail}"
    if errors is None:
        raise CooldownUnreadable(
            f"{msg}. Its URLs would not be counted, so the cooldown cannot "
            f"be trusted. Re-run, or pass an errors list to collect this.") from e
    errors.append(msg)
    print(f"  !! {msg}. Its URLs are NOT counted.", file=sys.stderr)


def family_rows(sid: str, pause: float = 1.1,
                tabs: tuple[str, ...] | None = None,
                errors: list[str] | None = None
                ) -> list[tuple[str, bool, str, int]]:
    """[(url as written, finished, tab name, row)] across the family tabs.

    Reads whichever layout the workbook has. `tabs` optionally limits which
    tab names (prefix match) are read. A tab that cannot be read raises
    CooldownUnreadable unless `errors` is given, in which case the failure is
    appended there and the tab is skipped.
    """
    out: list[tuple[str, bool, str, int]] = []
    for name in sheets_io.tab_names(sid):
        kind = tab_kind(name)
        if kind is None:
            continue
        if tabs is not None and not name.strip().startswith(tabs):
            continue
        try:
            if kind == "pages":
                lay = page_opt_tab.locate(sid, check=False)
                rows = parse_pages_tab(page_opt_tab.read_pages(sid, lay),
                                       page_opt_tab.read_changes(sid, lay))
            else:
                rows = _PARSERS[kind](
                    sheets_io.read(sid, f"'{name}'!{OLD_TAB_RANGE}"))
        except Exception as e:  # noqa: BLE001 - raised or recorded, never lost
            _unreadable(name, e, errors)
            continue
        for url, finished, row in rows:
            out.append((url, finished, name, row))
        time.sleep(pause)
    return out


def _read_workbook(sid: str, pause: float = 1.1,
                   tabs: tuple[str, ...] | None = None,
                   errors: list[str] | None = None
                   ) -> list[tuple[str, bool, str, int]]:
    """Same as family_rows with the URL canonicalised for comparison."""
    return [(canon(u), fin, tab, row)
            for u, fin, tab, row in family_rows(sid, pause, tabs, errors)]


def decide(hist: dict[str, list[tuple[int, bool, list[str]]]],
           carryover_exempt: bool | None = None
           ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Split URLs into (blocked, carryover-exempt).

    `hist` maps a canonical URL to one entry per prior month it appeared in:
    (months_ago, finished_that_month, where-strings). A URL is exempt only when
    it was carried over unfinished from LAST month (months_ago == 1) and never
    shipped in any month of the window. Anything else inside the window blocks.
    `carryover_exempt` defaults to the module constant, read at call time.
    """
    if carryover_exempt is None:
        carryover_exempt = CARRYOVER_EXEMPT
    blocked: dict[str, list[str]] = {}
    exempt: dict[str, list[str]] = {}
    for url, months in hist.items():
        where = sorted({w for _, _, ws in months for w in ws})
        shipped = any(fin for _, fin, _ in months)
        carried = any((not fin) and ago == 1 for ago, fin, _ in months)
        if carryover_exempt and carried and not shipped:
            exempt[url] = where
        else:
            blocked[url] = where
    return blocked, exempt


def family_state(cfg: dict, today: date | None = None, pause: float = 1.1,
                 errors: list[str] | None = None, months: int = COOLDOWN_MONTHS
                 ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """(blocked, carryover-exempt) for the merged 2.3 family, from a registry cfg.

    Raises CooldownUnreadable if a prior tab cannot be read, unless `errors`
    is given to collect the failures."""
    today = today or date.today()
    hist: dict[str, list[tuple[int, bool, list[str]]]] = {}
    for month, sid in sorted(prior_sheet_ids(cfg).items()):
        if not in_window(month, today, months):
            continue
        ago = months_ago(month, today)
        per_url: dict[str, list[tuple[bool, str]]] = {}
        for url, fin, tab, row in _read_workbook(sid, pause, errors=errors):
            per_url.setdefault(url, []).append(
                (fin, f"{month} {tab.strip()} r{row}"))
        for url, items in per_url.items():
            hist.setdefault(url, []).append(
                (ago, all(f for f, _ in items), [w for _, w in items]))
    return decide(hist)


def workbook_family_urls(sid: str, pause: float = 1.1,
                         errors: list[str] | None = None
                         ) -> dict[str, list[str]]:
    """Canonical URL -> where it sits on ONE workbook's family tabs, any layout.

    No window and no carryover logic: this is "what did that month's tabs
    list". The month-over-month repeat checks use it.
    """
    out: dict[str, list[str]] = {}
    for url, _fin, tab, row in _read_workbook(sid, pause, errors=errors):
        out.setdefault(url, []).append(f"{tab.strip()} r{row}")
    return out


# --- public lookups ---------------------------------------------------------

def _blocked_legacy(cfg: dict, tab: str, pause: float, today: date,
                    errors: list[str] | None = None) -> dict[str, list[str]]:
    """Prefix-matched scan for any tab key other than the 2.3 family."""
    out: dict[str, list[str]] = {}
    for month, sid in prior_sheet_ids(cfg).items():
        if not in_window(month, today):
            continue
        for name in sheets_io.tab_names(sid):
            if not name.strip().lower().startswith(tab.strip().lower()):
                continue
            try:
                vals = sheets_io.read(sid, f"'{name}'!A1:N100")
            except Exception as e:  # noqa: BLE001
                _unreadable(name, e, errors)
                continue
            for i, row in enumerate(vals, 1):
                for cell in (row or []):
                    for u in URL_RE.findall(str(cell)):
                        out.setdefault(canon(u), []).append(
                            f"{month} {name} r{i}")
            time.sleep(pause)
    return out


def blocked(client: str, tab: str, pause: float = 1.1,
            today: date | None = None,
            errors: list[str] | None = None) -> dict[str, list[str]]:
    """Canonical URL -> where it was seen, inside this tab's cooldown.

    Tab key "2.3" is the merged family (all three old tabs in old-layout prior
    workbooks, the Pages section in new-layout ones) with the carryover
    exemption applied. Any other key is matched case-insensitively as a prefix
    of the tab name, as before. Raises CooldownUnreadable when a prior tab
    cannot be read (see that class), unless `errors` collects the failures.
    """
    reg = _registry()
    cfg = reg[_client_key(reg, client)]
    today = today or date.today()
    if tab.strip().lower() in FAMILY_KEYS:
        return family_state(cfg, today, pause, errors)[0]
    return _blocked_legacy(cfg, tab, pause, today, errors)


def carried_over(client: str, pause: float = 1.1,
                 today: date | None = None,
                 errors: list[str] | None = None) -> dict[str, list[str]]:
    """URLs the cooldown lets through only because they were carried over."""
    reg = _registry()
    cfg = reg[_client_key(reg, client)]
    return family_state(cfg, today or date.today(), pause, errors)[1]


def assert_clear(client: str, tab: str, urls: list[str],
                 known: dict[str, list[str]] | None = None) -> None:
    """Raise if any URL is inside this tab's cooldown. Call BEFORE writing."""
    seen = known if known is not None else blocked(client, tab)
    hits = [(u, sorted(set(seen[canon(u)]))[:4]) for u in urls
            if canon(u) in seen]
    if hits:
        lines = "\n".join(f"    {u}\n        seen: {w}" for u, w in hits)
        raise SystemExit(
            f"COOLDOWN VIOLATION - {len(hits)} of {len(urls)} URLs were on the "
            f"{tab} tab within the last {COOLDOWN_MONTHS} months:\n{lines}\n"
            "    Pick different pages for this tab.")


def same_month(client: str, tabs: tuple[str, ...] = TITLE_WORK_TABS,
               pause: float = 1.0) -> dict[str, list[str]]:
    """Canonical URL -> where it sits on THIS month's title-work tab(s).

    Separate from the 90-day cooldown: that stops repeating a page across
    months, this stops one page being listed twice in the same month. Under the
    October template the one 2.3 tab is the whole list, so in a current
    workbook this is simply the Pages rows already written. Tabs outside the
    2.3 family named in `tabs` fall back to a plain URL scan.
    """
    reg = _registry()
    sid = reg[_client_key(reg, client)]["sheet_id"]
    out: dict[str, list[str]] = {}
    for url, _fin, tab, row in _read_workbook(sid, pause, tabs=tabs):
        out.setdefault(url, []).append(f"{tab.strip()} r{row}")
    for name in sheets_io.tab_names(sid):
        if tab_kind(name) is not None or not name.strip().startswith(tabs):
            continue
        try:
            vals = sheets_io.read(sid, f"'{name}'!A1:N60")
        except Exception as e:  # noqa: BLE001
            _unreadable(name, e, None)
            continue
        for i, row in enumerate(vals, 1):
            for cell in (row or []):
                for u in URL_RE.findall(str(cell)):
                    out.setdefault(canon(u), []).append(f"{name.strip()} r{i}")
        time.sleep(pause)
    return out


def assert_no_same_month(client: str, urls: list[str],
                         known: dict[str, list[str]] | None = None) -> None:
    """Raise if a URL is already on this month's 2.3 tab."""
    seen = known if known is not None else same_month(client)
    hits = [(u, sorted(set(seen[canon(u)]))[:4]) for u in urls
            if canon(u) in seen]
    if hits:
        lines = "\n".join(f"    {u}\n        already on: {w}"
                          for u, w in hits)
        raise SystemExit(
            f"SAME-MONTH DUPLICATE - {len(hits)} of {len(urls)} URLs are "
            f"already on this month's 2.3 tab:\n{lines}\n"
            "    A URL gets one title-and-meta recommendation a month.")


def main() -> int:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    client, tab, urls = sys.argv[1], sys.argv[2], sys.argv[3:]
    seen = blocked(client, tab)
    print(f"{len(seen)} distinct URLs are inside the "
          f"{COOLDOWN_MONTHS}-month cooldown for {client} on tab {tab!r}")
    if tab.strip().lower() in FAMILY_KEYS and CARRYOVER_EXEMPT:
        n = len(carried_over(client))
        print(f"{n} more were carried over unfinished from last month and are "
              f"exempt until they ship")
    if not urls:
        for u in sorted(seen)[:60]:
            print(f"  {u[:96]}")
        return 0
    assert_clear(client, tab, urls, seen)
    print(f"\nall {len(urls)} URLs are clear of the cooldown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
