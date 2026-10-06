"""Answer one question: is any URL in this month's 1.5 tab one we worked on before?

Run it any time. It does not trust the gate inside run_1_5.py; it reads the
sheets directly and diffs the URLs, which is how the owner checks it by hand.

    python scripts/check_1_5_repeats.py [client]

"This month" is each client's sheet_id in clients/registry.yaml; the prior
workbooks are its sheet_id_YYYY_MM entries inside the 1.5 lookback window
(url_cooldown.CANDIDATE_LOOKBACK_MONTHS, six months). A URL counts as worked before when it was:

  - a 1.5 candidate in a prior workbook,
  - selected in a prior 1.8 (old-layout workbooks only), or
  - on the 2.3 tab family of a prior workbook: the Refresh Log, 2.5 Quick Wins
    or Page Optimization tab (old layout), or a Pages row of "2.3 Page
    Optimizations" (new layout).

The 2.3 part applies the cooldown's carryover exemption: a page carried over
UNFINISHED from last month is not a repeat until it ships, and is reported on
its own line as exempt rather than as a hit.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_1_5 as R  # noqa: E402
import sheets_io as S  # noqa: E402
import url_cooldown  # noqa: E402

# (tab, section heading, next heading or None, URL column, label)
SECTIONS = [("1.5 Candidate List", "B. Ranked candidates", None, "B",
             "was a 1.5 candidate"),
            ("1.8 Monthly Plan", "A. Selected targets",
             "B. Content-calendar", "B", "was selected in 1.8")]
SPAN = 30


class ReadFailed(RuntimeError):
    """A section could not be read. Never the same thing as "no URLs"."""


def canon(u: str) -> str:
    return url_cooldown.canon(u)


def section_urls(sid: str, tab: str, start: str, end: str | None,
                 col: str) -> set[str] | None:
    """URLs in `col` between two headings; None when the heading is missing.

    A prior workbook in the new layout has no "A. Selected targets", so a
    missing heading is expected there; the caller decides what it means. A
    failed read raises ReadFailed."""
    try:
        rows = S.find_rows(sid, tab, {"a": start, **({"b": end} if end else {})})
    except KeyError:
        return None
    first = rows["a"] + 2
    last = rows["b"] - 1 if end else first + SPAN
    try:
        vals = S.read(sid, f"'{tab}'!{col}{first}:{col}{max(last, first)}")
    except Exception as e:  # noqa: BLE001 - a failed read must not look clean
        raise ReadFailed(f"{tab}: {e.__class__.__name__}") from e
    return {canon(str(r[0])) for r in vals
            if r and str(r[0]).strip().startswith("http")}


def landing(url: str) -> str:
    """Where a recorded URL lands now. A site that moves its tree leaves every address a prior workbook
    recorded redirecting, and comparing the old string to this month's new one calls a worked page fresh
    (SameDay, October: /plumbing/drain-cleaning/ became /plumbing/sewer-and-drains/drain-cleaning/).
    Raises ReadFailed when the address cannot be read, never passes it."""
    url = url if url.startswith("http") else "https://" + url   # canon() drops the scheme
    page = R._onpage(url)
    status = (page or {}).get("status")
    if page is None or (status and status not in (200, 404, 410)):
        raise ReadFailed(f"{url} could not be resolved ({'no response' if page is None else 'HTTP ' + str(status)})")
    return canon((page.get("final") or url).split("?")[0]) if status == 200 else canon(url)


def main() -> int:
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    only = sys.argv[1] if len(sys.argv) > 1 else None
    hits, exempt, checked, skipped, incomplete = [], [], 0, [], []
    for slug, cfg in reg.items():
        if not isinstance(cfg, dict) or not cfg.get("sheet_id"):
            continue
        if only and slug != only:
            continue
        try:
            now = section_urls(cfg["sheet_id"], *SECTIONS[0][:4])
        except ReadFailed as e:
            skipped.append((slug, f"NOT READ: {e}"))
            continue
        if now is None:
            skipped.append((slug, f"heading {SECTIONS[0][1]!r} not found in "
                                  f"the current 1.5 tab"))
            continue
        if not now:
            skipped.append((slug, "1.5 tab is empty"))
            continue
        priors = url_cooldown.prior_sheet_ids(cfg)
        in_window = {m: s for m, s in priors.items()
                     if url_cooldown.in_window(
                         m, date.today(), url_cooldown.CANDIDATE_LOOKBACK_MONTHS)}
        if not in_window:
            skipped.append((slug, "no prior workbook (first month)"))
            continue
        checked += 1
        for month, sid in sorted(in_window.items(), reverse=True):
            for tab, start, end, col, what in SECTIONS:
                try:
                    found = section_urls(sid, tab, start, end, col) or set()
                    found = found | {landing(u) for u in found}
                except ReadFailed as e:
                    incomplete.append((slug, f"{month} {e}"))
                    continue
                for u in now & found:
                    hits.append((slug, month, u, what))
        errs: list[str] = []
        blocked, carried = url_cooldown.family_state(
            cfg, pause=0.5, errors=errs,
            months=url_cooldown.CANDIDATE_LOOKBACK_MONTHS)
        incomplete += [(slug, e[:90]) for e in errs]
        reach = {}
        for k, v in blocked.items():
            reach.setdefault(k, v)
            try:
                reach.setdefault(landing(k), v)
            except ReadFailed as e:
                incomplete.append((slug, str(e)[:90]))
        for u in sorted(now & set(reach)):
            hits.append((slug, "cooldown", u,
                         f"was optimized ({reach[u][0]})"))
        for u in sorted(now & set(carried)):
            exempt.append((slug, u, carried[u][0]))
    print(f"clients checked: {checked}")
    for slug, why in skipped:
        print(f"  skipped {slug:<22} {why}")
    for slug, why in incomplete:
        print(f"  NOT READ {slug:<21} {why}")
    print()
    for slug, u, where in exempt:
        print(f"  exempt  {slug:<22} {u}  (carried over unfinished: {where})")
    if hits:
        print(f"ANSWER: YES - {len(hits)} repeat(s)")
        for slug, month, u, what in hits:
            print(f"  {slug:<22} {u}  ({what} in {month})")
        return 1
    if not checked:
        print("ANSWER: NOT CHECKED - no client has a filled 1.5 tab and a "
              "prior workbook to compare yet")
        return 2
    if incomplete:
        print("ANSWER: UNKNOWN - no repeat in what could be read, but "
              f"{len(incomplete)} source(s) were NOT READ (listed above)")
        return 2
    print("ANSWER: NO - no URL on any current 1.5 tab appears in a prior "
          f"workbook inside the {url_cooldown.CANDIDATE_LOOKBACK_MONTHS}-month window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
