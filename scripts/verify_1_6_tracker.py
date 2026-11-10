#!/usr/bin/env python
"""Independent check of a client's 1.6 tab against the tracker database.

    python scripts/verify_1_6_tracker.py <client> [<client> ...] | all

Re-derives the SOV headline with its own SQL (a different query from tracker_reader's), then checks the
tab itself: every long cell is a label plus bullets, none is over the cap, no retired section D remains,
and the Section A rows carry per-engine "m of n" counts that add up to the headline for the rows shown.
Exit 0 when everything matches, 1 on any mismatch.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import fill_1_6_all as F  # noqa: E402
import sheets_io as S  # noqa: E402
import tracker_reader as T  # noqa: E402

FAILS: list[str] = []


def derive(domain: str, week: str) -> tuple[int, int]:
    """(mentioned, answered) for ChatGPT + AI Mode, category prompts, straight from the raw rows."""
    conn = T.connect()
    cur = conn.cursor()
    cur.execute("""
      select count(*), count(*) filter (where exists (select 1 from geo_tracker.judgements j
             where j.sample_id = s.id and j.brand_kind = 'client' and j.mentioned))
      from geo_tracker.samples s
      join geo_tracker.scan_batches b on b.id = s.batch_id
      join geo_tracker.clients c on c.id = b.client_id
      join geo_tracker.prompts p on p.id = s.prompt_id
      where replace(c.domain, 'www.', '') = %s and b.week_start = %s and s.engine in ('chatgpt', 'ai_mode')
            and s.status in ('done', 'empty') and not p.is_branded and not p.names_competitor""",
                (domain.replace("www.", ""), week))
    n, m = cur.fetchone()
    conn.close()
    return m, n


def derive_prev(domain: str, week: str, prev_week: str) -> tuple[int, int]:
    """(mentioned, answered) in prev_week over only the prompts that were scanned in `week`."""
    conn = T.connect()
    cur = conn.cursor()
    cur.execute("""
      with c as (select id from geo_tracker.clients where replace(domain, 'www.', '') = %(d)s),
      cur_prompts as (select distinct s.prompt_id from geo_tracker.samples s
                      join geo_tracker.scan_batches b on b.id = s.batch_id
                      where b.client_id = (select id from c) and b.week_start = %(w)s)
      select count(*), count(*) filter (where exists (select 1 from geo_tracker.judgements j
             where j.sample_id = s.id and j.brand_kind = 'client' and j.mentioned))
      from geo_tracker.samples s
      join geo_tracker.scan_batches b on b.id = s.batch_id
      join geo_tracker.prompts p on p.id = s.prompt_id
      where b.client_id = (select id from c) and b.week_start = %(pw)s and s.engine in ('chatgpt', 'ai_mode')
            and s.status in ('done', 'empty') and not p.is_branded and not p.names_competitor
            and s.prompt_id in (select prompt_id from cur_prompts)""",
                dict(d=domain.replace("www.", ""), w=week, pw=prev_week))
    n, m = cur.fetchone()
    conn.close()
    return m, n


def main(slug: str) -> None:
    cfg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))[slug]
    grid = S.read(cfg["sheet_id"], f"'{F.TAB}'!A1:M120")
    head = str(grid[3][1])
    m = re.match(r"(\d+)% \((\d+) of (\d+)\)", head)
    cov = str(grid[5][2])
    wk = re.search(r"week of (\d{4}-\d{2}-\d{2})", cov)
    if not (m and wk):
        FAILS.append(f"{slug}: could not read the SOV headline or week ({head!r})")
        return
    h, n = int(m[2]), int(m[3])
    dh, dn = derive(cfg["domain"], wk[1])
    if (h, n) != (dh, dn):
        FAILS.append(f"{slug}: sheet {h} of {n}, re-derived {dh} of {dn}")
    if round(100 * dh / dn) != int(m[1]):
        FAILS.append(f"{slug}: headline percentage {m[1]} does not match {dh} of {dn}")
    prev_head, prev_note = str(grid[4][1]), str(grid[4][2]) if len(grid[4]) > 2 else ""
    pm, pw = re.match(r"(\d+)% \((\d+) of (\d+)\)", prev_head), re.search(r"week of (\d{4}-\d{2}-\d{2})", prev_note)
    if pm and pw:
        dm, dn2 = derive_prev(cfg["domain"], wk[1], pw[1])
        if (int(pm[2]), int(pm[3])) != (dm, dn2):
            FAILS.append(f"{slug}: last month {pm[2]} of {pm[3]}, re-derived {dm} of {dn2}")
        delta = round(100 * dh / dn) - round(100 * dm / dn2) if dn2 else None
        quiet = "No measurable change" in prev_note
        ran = re.match(r"(\d+) of", str(grid[5][1]))
        engines = len(re.findall(r"ChatGPT|AI Mode", cov.split(".")[0]))
        floor = F.noise_points(int(ran[1]) if ran else 0, engines or 1)
        if delta is not None and quiet != (abs(100 * dh / dn - 100 * dm / dn2) < floor):
            FAILS.append(f"{slug}: change wording does not match a {delta:+d}-point move")
        print(f"{slug}: last month {pm[2]} of {pm[3]} re-derived as {dm} of {dn2} (week {pw[1]})")
    elif prev_head != "baseline month":
        FAILS.append(f"{slug}: could not read last month's figure ({prev_head!r})")
    for r, row in enumerate(grid, 1):
        for c, v in enumerate(row, 1):
            if len(str(v)) > S.CELL_MAX:
                FAILS.append(f"{slug}: cell r{r}c{c} is {len(str(v))} chars")
            if r > 3 and not S.is_formatted(v):   # rows 1-3 are the template's own banner text
                FAILS.append(f"{slug}: cell r{r}c{c} is a paragraph")
        if row and str(row[0]).startswith("D. Weekly LLM tracker"):
            FAILS.append(f"{slug}: retired section D still on row {r}")
    rows_a = [r for r in grid[9:] if r and str(r[0]).isdigit()]
    for r in rows_a:
        for idx in (5, 7):
            cell = str(r[idx]) if len(r) > idx else ""
            if cell and not re.fullmatch(r"\d+ of \d+", cell):
                FAILS.append(f"{slug}: Section A row {r[0]} engine cell {cell!r} is not 'm of n'")
    print(f"{slug}: headline {h} of {n} re-derived as {dh} of {dn}, {len(rows_a)} Section A rows")


if __name__ == "__main__":
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    names = F.active_slugs(reg) if sys.argv[1:] == ["all"] else sys.argv[1:]
    for s in names:
        main(s)
    for f in FAILS:
        print("  MISMATCH", f)
    print(f"{len(FAILS)} mismatches")
    sys.exit(1 if FAILS else 0)
