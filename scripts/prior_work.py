"""What a prior month's workbook says we worked on, in either tab layout.

Workbooks up to September 2026 record page work on three tabs ("1.8 Monthly
Plan" section A, "2.3-3.1 Refresh Log", "2.5 Quick Wins"). From October 2026
it is one tab, "2.3 Page Optimizations", Pages section. Every script that looks
BACK at a prior month needs both readings, and three of them each carried their
own fixed-range copy (`B5:B14` and friends). Those ranges read the wrong
column, silently, the day a new-layout workbook becomes the prior one, so the
reading lives here once and anchors on heading text.

    worked_pages(sheet_id)  -> [{"page", "kind", "task", "query", "source"}]
    worked_urls(sheet_id)   -> {canonical url, ...}
    recent_urls(cfg, n)     -> URLs offered or worked in the last n workbooks
    previous_workbook(cfg, today) -> (registry key, sheet id) for last month
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sheets_io as S  # noqa: E402

NEW_TAB = "2.3 Page Optimizations"
REFRESH = "Refresh"
QUICK = "Quick Win"


def canon(url: str) -> str:
    """Trailing-slash-insensitive form; the tabs disagree about slashes."""
    return str(url or "").strip().rstrip("/")


def _is_url(v) -> bool:
    return str(v or "").strip().startswith("http")


def _tab(names: list[str], prefix: str) -> str | None:
    return next((t for t in names if t.strip().startswith(prefix)), None)


def layout(sheet_id: str, names: list[str] | None = None) -> str:
    """'new' when the workbook carries the merged 2.3 tab, otherwise 'old'."""
    names = names if names is not None else S.tab_names(sheet_id)
    return "new" if _tab(names, NEW_TAB) else "old"


def _first_target(cell: str) -> str:
    """First target query out of a plan cell, without volume or numbering.

    Handles the labelled form (a TARGETS label, then '• query - 534 impr') and the older
    inline form ('1. query (534 impr); query two ... AI prompts ...').
    """
    text = str(cell or "")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("•"):
            return re.split(r"\s+-\s+\d", line.lstrip("• ").strip())[0].strip()
    first = text.split("AI prompt")[0].split(";")[0]
    first = re.sub(r"^\s*\d+\.\s*", "", first)
    first = re.sub(r"\([^)]*\)", "", first)
    return first.strip(" ,;:-")


def _new_layout(sid: str, tab: str) -> list[dict]:
    p = S.find_rows(sid, tab, {"hdr": "Type", "sec2": "Section 2"})
    rows = S.read(sid, f"'{tab}'!A{p['hdr'] + 1}:I{p['sec2'] - 1}")
    out = []
    for r in rows:
        r = list(r) + [""] * (9 - len(r))
        if not _is_url(r[2]):
            continue
        kind = str(r[0]).strip() or REFRESH
        out.append({"page": str(r[2]).strip(), "kind": kind, "task": "2.3",
                    "query": _first_target(r[3]) or str(r[5]).split("\n")[0].strip(),
                    "source": tab})
    return out


def _old_layout(sid: str, names: list[str]) -> list[dict]:
    out: list[dict] = []
    t18 = _tab(names, "1.8")
    if t18:
        try:
            p = S.find_rows(sid, t18, {"a": "A. Selected targets",
                                       "b": "B. Content-calendar"})
            for r in S.read(sid, f"'{t18}'!A{p['a'] + 2}:F{p['b'] - 1}"):
                r = list(r) + [""] * (6 - len(r))
                if _is_url(r[1]):
                    out.append({"page": str(r[1]).strip(), "kind": REFRESH,
                                "task": str(r[2]).strip(),
                                "query": _first_target(r[3]),
                                "source": t18})
        except KeyError:
            pass
    tlog = _tab(names, "2.3-3.1")
    if tlog:
        for r in S.read(sid, f"'{tlog}'!A5:C30"):
            r = list(r) + [""] * (3 - len(r))
            if _is_url(r[1]):
                out.append({"page": str(r[1]).strip(), "kind": REFRESH,
                            "task": str(r[0]).strip(),
                            "query": _first_target(r[2]), "source": tlog})
    tqw = _tab(names, "2.5")
    if tqw:
        for r in S.read(sid, f"'{tqw}'!A5:I30"):
            r = list(r) + [""] * (9 - len(r))
            if _is_url(r[0]):
                out.append({"page": str(r[0]).strip(), "kind": QUICK, "task": "2.5",
                            "query": str(r[7]).strip(), "source": tqw})
    return out


def worked_pages(sheet_id: str) -> list[dict]:
    """Pages this workbook worked or planned to work, one entry per URL."""
    names = S.tab_names(sheet_id)
    tab = _tab(names, NEW_TAB)
    found = _new_layout(sheet_id, tab) if tab else _old_layout(sheet_id, names)
    seen: dict[str, dict] = {}
    for d in found:
        seen.setdefault(canon(d["page"]), d)
    return list(seen.values())


def worked_urls(sheet_id: str) -> set[str]:
    return {canon(d["page"]) for d in worked_pages(sheet_id)}


def offered_urls(sheet_id: str) -> set[str]:
    """URLs on the 1.5 ranked-candidates list (offered, not necessarily worked)."""
    names = S.tab_names(sheet_id)
    tab = _tab(names, "1.5")
    if not tab:
        return set()
    b = S.find_rows(sheet_id, tab, {"b": "B. Ranked candidates"})["b"]
    return {canon(r[1]) for r in S.read(sheet_id, f"'{tab}'!A{b + 2}:B{b + 20}")
            if len(r) > 1 and _is_url(r[1])}


def prior_ids(cfg: dict, n: int) -> list[tuple[str, str]]:
    """The n most recent prior workbooks, newest first, as (key, sheet id).

    Owner rule 2026-09-03: a page worked in August is skipped in September,
    October and November and is eligible again in December. Taking every
    sheet_id_* key would widen the exclusion by one month per month the
    registry accumulates.
    """
    keys = sorted((k for k in cfg if k.startswith("sheet_id_") and cfg.get(k)),
                  reverse=True)
    return [(k, cfg[k]) for k in keys[:n]]


def recent_urls(cfg: dict, n: int) -> set[str]:
    """URLs offered on 1.5 or worked in the last n workbooks, either layout."""
    urls: set[str] = set()
    for _key, sid in prior_ids(cfg, n):
        for fn in (offered_urls, worked_urls):
            try:
                urls |= fn(sid)
            except KeyError as e:
                # A renamed heading must be loud. Swallowing it is how a
                # cooldown silently stops working.
                raise KeyError(f"prior workbook {sid}: {e}") from e
    return urls


def previous_workbook(cfg: dict, today: dt.date | None = None) -> tuple[str, str] | tuple[None, None]:
    """(registry key, sheet id) of last calendar month's workbook, else the newest prior."""
    today = today or dt.date.today()
    last = today.replace(day=1) - dt.timedelta(days=1)
    key = f"sheet_id_{last.year}_{last.month:02d}"
    if cfg.get(key):
        return key, cfg[key]
    ids = prior_ids(cfg, 1)
    return ids[0] if ids else (None, None)
