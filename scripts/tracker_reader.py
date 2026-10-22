"""Read-only access to the GEO-AEO-LLM-Tracker database, for the 1.6 AI visibility task.

The tracker (a separate project) scans each client's approved prompts every week through DataForSEO and
stores the answers, a judgement of every brand named, and every citation, in Postgres schema `geo_tracker`.
1.6 reads those results instead of running its own collection (owner decision, 2026-10-07), so the workbook
makes no vendor calls for this task.

Connection: the tracker's own `.env` holds the URL. `TRACKER_DB=old` (default) uses DATABASE_URL, `new` uses
NEW_DATABASE_URL (the dedicated project the owner is migrating to). The session is read-only.

Everything here is category-prompt scoped the way the tracker scopes share of voice: prompts that are not
branded and do not name a competitor. Branded prompts are returned separately.
"""
from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import psycopg2

TRACKER_ENV = Path(__file__).resolve().parents[2] / "GEO-AEO-LLM-Tracker" / ".env"
SOV_ENGINES = ("chatgpt", "ai_mode")      # the tab's two filled columns
NOTE_ENGINES = ("gemini",)                # reported in a note, never in SOV (recipe 1.6)
THIN_WEEK_SHARE = 0.7                     # a week below this share of the prior week's samples is partial
LOCK_SHARE = 0.5                          # one brand above this share of a topic's brand mentions holds it
# 20 answered samples per TOPIC. The number is the tracker's high-confidence count (lib/scoring/confidence.ts),
# which it applies per prompt per engine; applied to a whole topic it is looser (two prompts on two engines at
# the default five samples). A per-prompt-per-engine bar would never be met at the default settings.
TOPIC_MIN_SAMPLES = 20
TOPIC_MIN_MENTIONS = 10                   # a share over fewer brand mentions is noise, not a lock

# Tracker intent labels -> the tab's dropdown. A vocabulary map, not a judgement about the client.
INTENT_MAP = {"local_best_of": "Best-X", "buying": "Decision", "comparison": "Comparison",
              "alternatives": "Comparison", "definition": "Discovery", "use_case": "Discovery"}


def intent_label(tracker_intent: str | None) -> str:
    return INTENT_MAP.get(tracker_intent or "", "Discovery")


def _env() -> dict:
    out = {}
    for ln in TRACKER_ENV.read_text(encoding="utf-8").splitlines():
        if "=" in ln and not ln.lstrip().startswith("#"):
            k, v = ln.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def connect():
    env = _env()
    key = "NEW_DATABASE_URL" if os.environ.get("TRACKER_DB", "old") == "new" else "DATABASE_URL"
    conn = psycopg2.connect(env[key], connect_timeout=20)
    conn.set_session(readonly=True, autocommit=True)
    return conn


def client_id(cur, domain: str) -> str:
    cur.execute("select id from geo_tracker.clients where replace(domain, 'www.', '') = %s",
                (domain.replace("www.", ""),))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"no tracker client for domain {domain}")
    return row[0]


def pick_week(weeks: list[tuple[str, int]]) -> tuple[str, str | None, str]:
    """(week, prior week or None, why). `weeks` is [(week_start, answered samples)], any order.

    The newest week is used unless it holds under THIN_WEEK_SHARE of the week before it, which means the
    weekly scan had not finished (Cudio and Education Walkthrough on 2026-10-07); then the week before is
    used and the tab says so.
    """
    ws = sorted((w for w in weeks if w[1] > 0), reverse=True)
    if not ws:
        raise RuntimeError("no scanned week with answers")
    if len(ws) >= 2 and ws[0][1] < THIN_WEEK_SHARE * ws[1][1]:
        prior = ws[2][0] if len(ws) > 2 else None
        return ws[1][0], prior, f"{ws[0][0]} was a partial scan ({ws[0][1]} samples against {ws[1][1]})"
    return ws[0][0], (ws[1][0] if len(ws) > 1 else None), "latest complete week"


def weeks(cur, cid: str) -> list[tuple[str, int]]:
    cur.execute("""select b.week_start::text, count(*) from geo_tracker.scan_batches b
                   join geo_tracker.samples s on s.batch_id = b.id
                   join geo_tracker.prompts p on p.id = s.prompt_id
                   where b.client_id = %s and s.engine = 'chatgpt' and s.status in ('done','empty')
                         and not p.is_branded and not p.names_competitor
                   group by 1""", (cid,))
    return [(w, n) for w, n in cur.fetchall()]


_BASE = """
with b as (select id from geo_tracker.scan_batches where client_id = %(cid)s and week_start = %(week)s),
base as (
  select s.id sid, s.engine, p.id pid, p.text, p.intent, p.priority, p.ai_search_volume, k.keyword
  from geo_tracker.samples s
  join b on b.id = s.batch_id
  join geo_tracker.prompts p on p.id = s.prompt_id
  left join geo_tracker.keywords k on k.id = p.keyword_id
  where s.status in ('done','empty') and s.engine = any(%(engines)s)
        and p.is_branded = %(branded)s and not p.names_competitor)
"""


def totals(cur, cid: str, week: str, branded: bool = False, engines=SOV_ENGINES + NOTE_ENGINES) -> dict:
    """{engine: {answered, mentioned, cited, recommended}} over the week's answered samples."""
    cur.execute(_BASE + """
      select engine, count(*),
        count(*) filter (where exists (select 1 from geo_tracker.judgements j where j.sample_id = sid
                         and j.brand_kind = 'client' and j.mentioned)),
        count(*) filter (where exists (select 1 from geo_tracker.citations c where c.sample_id = sid and c.is_client)),
        count(*) filter (where exists (select 1 from geo_tracker.judgements j where j.sample_id = sid
                         and j.brand_kind = 'client' and j.recommended))
      from base group by engine""", dict(cid=cid, week=week, engines=list(engines), branded=branded))
    return {e: dict(answered=a, mentioned=m, cited=c, recommended=r) for e, a, m, c, r in cur.fetchall()}


def prompt_stats(cur, cid: str, week: str, engines=SOV_ENGINES) -> list[dict]:
    """One dict per category prompt, ordered by AI search volume, then priority, then text."""
    args = dict(cid=cid, week=week, engines=list(engines), branded=False)
    cur.execute(_BASE + """
      select pid, text, intent, priority, ai_search_volume, keyword, engine, count(*),
        count(*) filter (where exists (select 1 from geo_tracker.judgements j where j.sample_id = sid
                         and j.brand_kind = 'client' and j.mentioned)),
        min((select min(j.position_rank) from geo_tracker.judgements j where j.sample_id = sid
             and j.brand_kind = 'client' and j.mentioned))
      from base group by 1,2,3,4,5,6,7""", args)
    prompts: dict[str, dict] = {}
    for pid, text, intent, prio, vol, kw, eng, n, m, rank in cur.fetchall():
        p = prompts.setdefault(pid, dict(pid=pid, text=text, intent=intent, priority=prio, volume=vol,
                                         keyword=kw, engines={}, best_rank=None,
                                         competitors=Counter(), own_urls=[], third=Counter(),
                                         third_urls=Counter()))
        p["engines"][eng] = dict(answered=n, mentioned=m)
        if rank is not None:
            p["best_rank"] = rank if p["best_rank"] is None else min(p["best_rank"], rank)
    cur.execute(_BASE + """
      select pid, j.brand_name, count(distinct sid) from base
      join geo_tracker.judgements j on j.sample_id = sid and j.brand_kind = 'competitor' and j.mentioned
      group by 1,2""", args)
    for pid, name, n in cur.fetchall():
        prompts[pid]["competitors"][name] += n
    cur.execute(_BASE + """
      select pid, c.domain, c.url, c.is_client, count(distinct sid) from base
      join geo_tracker.citations c on c.sample_id = sid group by 1,2,3,4""", args)
    for pid, domain, url, is_client, n in cur.fetchall():
        if is_client:
            if url not in prompts[pid]["own_urls"]:
                prompts[pid]["own_urls"].append(url)
        else:
            prompts[pid]["third"][domain] += n
            prompts[pid]["third_urls"][url] += n
    out = list(prompts.values())
    out.sort(key=lambda p: (-(p["volume"] or 0), -(p["priority"] or 0), p["text"]))
    return out


def client_name(cur, cid: str) -> str:
    cur.execute("select name from geo_tracker.clients where id = %s", (cid,))
    return cur.fetchone()[0]


def topic_stats(cur, cid: str, week: str, engines=SOV_ENGINES) -> list[dict]:
    """One dict per tracker topic (keyword): answered category samples and mentions per tracked brand."""
    args = dict(cid=cid, week=week, engines=list(engines), branded=False)
    cur.execute(_BASE + "select coalesce(keyword, '(no topic)'), count(distinct sid) from base group by 1", args)
    topics = {k: dict(topic=k, answered=n, mentions=Counter()) for k, n in cur.fetchall()}
    cur.execute(_BASE + """
      select coalesce(keyword, '(no topic)'), j.brand_name, count(distinct sid) from base
      join geo_tracker.judgements j on j.sample_id = sid and j.mentioned
      group by 1,2""", args)
    for k, name, n in cur.fetchall():
        topics[k]["mentions"][name] += n
    return sorted(topics.values(), key=lambda t: (-t["answered"], t["topic"]))


def topic_lock(answered: int, mentions: dict[str, int], client: str) -> dict:
    """Open or Locked for one topic, for the keyword-research feasibility score.

    Share is the tracker's share of voice: a brand's mentions over every tracked brand's mentions. Tracked
    brands only, so a topic an untracked rival dominates can still read Open; say so wherever this is used.
    """
    total = sum(mentions.values())
    out = dict(answered=answered, leader=None, leader_share=None, client_share=None)
    if answered < TOPIC_MIN_SAMPLES:
        return {**out, "label": "Too few answers"}
    if not total:
        return {**out, "label": "No brands named"}
    if total < TOPIC_MIN_MENTIONS:
        return {**out, "label": "Too few mentions"}
    leader, n = max(mentions.items(), key=lambda kv: (kv[1], kv[0] == client))
    return {**out, "leader": leader, "leader_share": round(n / total, 2),
            "client_share": round(mentions.get(client, 0) / total, 2),
            "label": "Locked" if n / total > LOCK_SHARE else "Open"}


def snapshot(domain: str) -> dict:
    """Everything 1.6 needs for one client, plus the week choice and why."""
    conn = connect()
    try:
        cur = conn.cursor()
        cid = client_id(cur, domain)
        week, prior, why = pick_week(weeks(cur, cid))
        return dict(client_id=cid, week=week, prior=prior, why=why,
                    totals=totals(cur, cid, week), branded=totals(cur, cid, week, branded=True),
                    prompts=prompt_stats(cur, cid, week),
                    prior_totals=totals(cur, cid, prior) if prior else None)
    finally:
        conn.close()
