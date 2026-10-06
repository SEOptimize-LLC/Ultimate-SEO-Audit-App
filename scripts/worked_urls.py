"""Every URL a prior workbook took into account, read from every tab that records work.

    python scripts/worked_urls.py <client> [months]

Owner rule, restated 2026-10-06: a URL that any of the last six workbooks took into account is not
put forward again. "Took into account" is wider than "optimized", so this reads every tab that names
pages for a task, not just the three the earlier gate read:

    1.3 + 2.2  fix sheet            2.1  technical fixes         2.3  page optimizations (merged;
    1.5  candidate list             1.8  monthly plan                 old 2.3 / 2.4 / 2.5 tabs too)
    3.1  internal links             4.1  QA of changed pages

4.2 and 4.3 are left out on purpose: they inspect top landing pages and cannibalization pairs, which
is checking, not work. Each tab is read in full and every http(s) URL on the client's own host is taken
from it, so a page named only inside a note ("link to X from Y") counts. Matching is on the canonical
URL (scheme, www, trailing slash and #anchor ignored).
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prior_work as PW  # noqa: E402
import sheets_io as S    # noqa: E402

# Tab names start with their task number in every layout the workbook has had.
TASK_TABS = ("1.3", "1.5", "1.8", "2.1", "2.2", "2.3", "2.4", "2.5", "3.1", "4.1")
_URL = re.compile(r"https?://[^\s<>\"')\]|;,]+", re.I)
READ_RANGE = "A1:Z400"


def host_of(url: str) -> str:
    return urlsplit(url if "://" in url else "https://" + url).netloc.lower().removeprefix("www.")


def key(url: str) -> str:
    """scheme-less, www-less, slash-less, anchor-less, query-less."""
    p = urlsplit(url.strip().rstrip(".,"))
    return (p.netloc.lower().removeprefix("www.") + p.path).rstrip("/").lower()


def tab_wanted(name: str) -> bool:
    return any(name.strip().startswith(t) for t in TASK_TABS)


def is_url_cell(text: str) -> bool:
    """True when the cell IS a page (or a list of pages), not prose that mentions one.

    A fix-sheet note such as "every instance points at https://x.com/service-areas/lehi-ut/" names a
    redirect target; it does not mean that page was worked. Counting those removed SameDay's
    /service-areas/lehi-ut from the October candidates for being mentioned in a sentence. A cell counts
    when nothing but URLs, separators and list markers is left once its URLs are taken out.
    """
    rest = _URL.sub(" ", str(text))
    return len(re.sub(r"[\s,;|•\-–*0-9.()]+", "", rest)) <= 6


def urls_in(grid, host: str) -> set[str]:
    out = set()
    for row in grid:
        for c in row:
            if not is_url_cell(c):
                continue
            for m in _URL.findall(str(c)):
                if host_of(m) == host:
                    out.add(key(m))
    return out


def workbook_urls(sheet_id: str, host: str, pause: float = 1.1) -> dict[str, set[str]]:
    """{canonical url: {tab names}} for one workbook. A tab that cannot be read raises."""
    found: dict[str, set[str]] = {}
    for name in S.tab_names(sheet_id):
        if not tab_wanted(name):
            continue
        time.sleep(pause)
        try:
            grid = S.read(sheet_id, f"'{name}'!{READ_RANGE}")
        except Exception as e:  # a gate that cannot read its source must not pass
            raise RuntimeError(f"worked-URL gate: tab {name!r} of {sheet_id} could not be read "
                               f"({e.__class__.__name__})") from e
        for u in urls_in(grid, host):
            found.setdefault(u, set()).add(name)
    return found


def prior_worked(cfg: dict, months: int) -> dict[str, list[str]]:
    """{canonical url: ['2026_09 2.3 Page Optimizations', ...]} across the last `months` workbooks."""
    host = host_of(cfg["gsc_property"])
    out: dict[str, list[str]] = {}
    for month_key, sid in PW.prior_ids(cfg, months):
        for u, tabs in workbook_urls(sid, host).items():
            for t in sorted(tabs):
                out.setdefault(u, []).append(f"{month_key.removeprefix('sheet_id_')} {t}")
    return out


if __name__ == "__main__":
    import yaml
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    cfg = reg[sys.argv[1]]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    got = prior_worked(cfg, n)
    print(f"{sys.argv[1]}: {len(got)} URLs taken into account in the last {n} workbooks")
    for u, where in sorted(got.items())[:40]:
        print(f"  {u}  <- {'; '.join(where)[:90]}")
