#!/usr/bin/env python
"""Is AI share of voice on each of a client's tracker topics open, or held by one brand?

    python scripts/topic_lock.py <client>        # slug from clients/registry.yaml

Feeds the AI-channel half of Ranking Feasibility in the local-keyword-research skill. Read-only, from the
LLM tracker's stored scans; no vendor calls.

  * Scope matches 1.6: ChatGPT and Google AI Mode, category prompts (not branded, not naming a competitor),
    the latest complete week (tracker_reader.pick_week).
  * Locked = one tracked brand holds more than half the topic's brand mentions. Open otherwise.
  * Fewer than 20 answered samples is "Too few answers"; fewer than 10 brand mentions is "Too few mentions".
  * Tracked brands only. A topic an untracked rival dominates can still read Open.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
import tracker_reader as T  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def pct(share: float | None) -> str:
    return "-" if share is None else f"{round(share * 100)}%"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    slug = argv[1]
    cfg = yaml.safe_load((ROOT / "clients" / "registry.yaml").read_text(encoding="utf-8")).get(slug)
    if not cfg:
        print(f"{slug}: not in clients/registry.yaml")
        return 2

    conn = T.connect()
    try:
        cur = conn.cursor()
        try:
            cid = T.client_id(cur, cfg["domain"])
            week, _, why = T.pick_week(T.weeks(cur, cid))
        except RuntimeError as e:          # no tracker client, or no scanned week with answers yet
            print(f"{slug}: {e}. AI share of voice: not measured.")
            return 0
        name = T.client_name(cur, cid)
        topics = T.topic_stats(cur, cid, week)
    finally:
        conn.close()

    print(f"{slug}: week of {week} ({why}). ChatGPT and Google AI Mode, category prompts, tracked brands only.")
    print(f"Client share is {name}'s.")
    print(f"{'Topic':<44} {'Answered':>8}  {'Label':<16} {'Leader':<28} {'Lead':>5} {'Client':>7}")
    for t in topics:
        lock = T.topic_lock(t["answered"], t["mentions"], name)
        print(f"{t['topic'][:44]:<44} {t['answered']:>8}  {lock['label']:<16} {(lock['leader'] or '-')[:28]:<28} "
              f"{pct(lock['leader_share']):>5} {pct(lock['client_share']):>7}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
