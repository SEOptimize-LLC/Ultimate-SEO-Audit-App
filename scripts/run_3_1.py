"""Task 3.1 - this month's internal links, found by the Internal Link Optimization Agent.

    python scripts/run_3_1.py <client>

The agent (sibling project ../Internal Link Optimization Agent) does the work
with its own pipeline and its Supabase data: entities, core topics, topical
map, embeddings, prior recommendations, the stored page copy in
client_page_content, its gates (posts-only sources, cannibalization, geo
anchors, topical tiers, already-linked) and its anchor and copy enrichment.
This script only points it at the workbook's targets and keeps what the
workbook asks for:

  1. Pass 1: run.py --fresh with the workbook targets as its allowlist
     (plan_3_1.py writes them), the owner's click floor and 3 links a source.
  2. Keep each target's best rows by the agent's own priority:
     2.1 pages 2, 2.1 posts 1, 1.8 and 2.3 refresh 3; at most 3 per source.
  3. Pass 2: run.py --resume with those source pages fetched live, so every
     Placement Hint is a sentence the page carries today. Same selection.
  4. scripts/verify_link_workbook.py (the agent's live verifier). Failing
     rows are dropped and listed, never shipped.
  5. Section B from the agent's link data: sitemap URLs changed in 60 days,
     no impressions, no internal link in client_inlinks or the stored copy.

Writes Clients/<folder>/internal_links/<YYYY-MM>/<name> - 3.1 <YYYY-MM>.xlsx for
scripts/fill_3_1.py. Decision record: decisions/log.md, 2026-10-12 / 10-13.
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
ILA = ROOT.parent / "Internal Link Optimization Agent"
QUOTA = {"2.1 pages": 2, "2.1 posts": 1, "1.8 routed": 3, "2.3 refresh": 3}
PER_SOURCE = 3
ORPHAN_DAYS = 60
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def norm(u: str) -> str:
    return str(u or "").strip().rstrip("/").lower()


def tab_links(sid: str) -> list[dict]:
    """Section A link rows already on the 3.1 tab (Skipped rows excluded)."""
    sys.path.insert(0, str(Path(__file__).parent))
    import sheets_io
    t = next(x for x in sheets_io.tab_names(sid) if x.startswith("3.1"))
    rows = sheets_io.read(sid, f"'{t}'!A1:I200")
    hi = next(i for i, r in enumerate(rows) if r and "Source URL" in r)
    h = rows[hi]
    si, ti, st = h.index("Source URL"), h.index("Target URL (refresh/money page)"), h.index("Status")
    out = []
    for r in rows[hi + 1:]:
        if not any(str(x).strip() for x in r):
            break
        r = list(r) + [""] * (len(h) - len(r))
        if str(r[st]).strip().lower() != "skipped" and str(r[si]).startswith("http"):
            out.append({"source": norm(r[si]), "target": norm(r[ti])})
    return out


def ila_config(domain: str) -> Path:
    for f in sorted((ILA / "configs").glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(d, dict) and domain.split(".")[0] in str(d.get("gsc_property", "")):
            return f
    raise SystemExit(f"no Internal Link Optimization Agent config for {domain}")


AGENT_LOG: Path | None = None    # set per run in main(); the engine's output is copied here


def agent(cmd: list[str]) -> None:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    print("  $", " ".join(cmd[2:]))
    if AGENT_LOG is None:
        subprocess.run([sys.executable, "-u", "-W", "ignore", *cmd], cwd=ILA, env=env, check=True)
        return
    AGENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen([sys.executable, "-u", "-W", "ignore", *cmd], cwd=ILA, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          encoding="utf-8", errors="replace") as proc, \
            AGENT_LOG.open("a", encoding="utf-8") as log:
        for line in proc.stdout:
            print(line, end="")
            log.write(line)
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


FUNNEL = re.compile(r"Dropped: (\S+)\s+(\d+)")


def funnel_counts(log_text: str) -> dict[str, int]:
    """Drop counts from the LAST 'Pair-matcher funnel:' block in an engine log."""
    blocks = log_text.split("Pair-matcher funnel:")
    if len(blocks) < 2:
        return {}
    last = blocks[-1].split("Survived hard filters")[0]
    return {k: int(v) for k, v in FUNNEL.findall(last)}


def index_screen(final, slug_cfg: dict, month: str):
    """Trial (research 2026-11-10, owner's yes): with a click floor of 0, drop any source page whose URL
    Inspection verdict in this month's index_audit cache is not 'Submitted and indexed', or that the cache
    does not carry. Returns (kept frame, dropped [(url, reason)])."""
    cache = Path(slug_cfg["folder"]) / "Monthly SEO Workbook" / month / "index_audit.json"
    if not cache.exists():
        raise SystemExit(f"index screen on, but no index_audit.json for {month}: run index_audit.py first")
    rows = json.loads(cache.read_text(encoding="utf-8")).get("rows", [])
    state = {r["url"].split("#")[0].rstrip("/"): r.get("state", "") for r in rows}
    dropped = []
    for u in sorted(set(final["Source URL"])):
        st = state.get(str(u).rstrip("/"))
        if st != "Submitted and indexed":
            dropped.append((u, st or "not in this month's index audit"))
    bad = {u for u, _ in dropped}
    return final[~final["Source URL"].isin(bad)], dropped


def latest_recs(client_name: str) -> Path:
    safe = re.sub(r"[^a-z0-9_-]", "_", client_name.lower())
    hits = sorted((ILA / "outputs").glob(f"{safe}_*/{safe}_link_recommendations.xlsx"),
                  key=lambda p: p.stat().st_mtime)
    if not hits:
        raise SystemExit(f"the agent wrote no recommendations workbook for {client_name}")
    return hits[-1]


def select(recs: pd.DataFrame, targets: dict[str, dict],
           used: dict[str, int] | None = None) -> pd.DataFrame:
    """Each target's best rows by the agent's own ranking, within the quota.
    `used` counts the links each source already got this month (--missing)."""
    recs = recs.copy()
    recs["_t"] = recs["Target URL"].map(norm)
    recs = recs[recs["_t"].isin(targets)]
    by = [c for c in ("Priority", "Priority Score") if c in recs.columns]
    recs = recs.sort_values(by, ascending=[True, False][:len(by)]) if by else recs
    per_source: dict[str, int] = dict(used or {})
    per_target: dict[str, int] = {}
    keep = []
    for i, r in recs.iterrows():
        t, s = r["_t"], norm(r["Source URL"])
        if per_target.get(t, 0) >= QUOTA[targets[t]["group"]] + (1 if targets[t]["group"] == "2.1 pages" else 0):
            continue                      # 2.1 pages: 2 contextual + 1 structural
        if per_source.get(s, 0) >= PER_SOURCE:
            continue
        keep.append(i)
        per_target[t] = per_target.get(t, 0) + 1
        per_source[s] = per_source.get(s, 0) + 1
    out = recs.loc[keep].drop(columns="_t")
    out["Group"] = out["Target URL"].map(lambda u: targets[norm(u)]["group"])
    return out


_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_JOINERS = re.compile(r"^(?:[,;:—–-]\s*)?(?:and|but|so|which|while|because|as|since|where)?\s*",
                      re.IGNORECASE)


WORD = re.compile(r"[a-z0-9']+")
FRAGMENT = re.compile(r"(?:though|although|making|which|while|because|as|so|and|but|since|where|when|if|"
                      r"is|are|was|were|has|have|can|will|does)\b", re.IGNORECASE)
BANNED = ("understanding", "exploring", "reviewing", "learning", "learn ", "discover",
          "if you want to", "whether you")
FOLLOW_PROMPT = """Write ONE sentence to place right after this sentence in a blog post.

Sentence already on the page: "{hint}"
It must contain this exact phrase once, which will link to {url}: "{anchor}"
That page is about: {topic}

Rules: one complete, grammatical sentence of at most 25 words that follows naturally
from the sentence above; plain words the post's author would use; no numbers, prices,
years, statistics or claims about the company; no em dashes; do not repeat the sentence
above; do not start with Understanding, Exploring, Reviewing, Learning or Discover.
Return JSON only: {{"sentence": "..."}}"""


def overlap(a: str, b: str) -> float:
    """Shared words as a share of the SHORTER text, so a rewrite that restates
    the original sentence plus a clause reads as a restatement (Bart's row 4)."""
    wa, wb = set(WORD.findall(a.lower())), set(WORD.findall(b.lower()))
    return len(wa & wb) / max(1, min(len(wa), len(wb)))


def follow_sentence(hint: str, anchor: str, url: str, topic: str) -> str | None:
    """One new sentence after the untouched placement sentence, written by the
    agent's own model client, carrying the agent's own anchor."""
    sys.path.insert(0, str(ILA))
    from dotenv import load_dotenv
    load_dotenv(ILA / ".env")
    from internal_link_agent.utils.openrouter import chat_completion
    for _ in range(2):
        try:
            out = chat_completion(messages=[{"role": "user", "content": FOLLOW_PROMPT.format(
                hint=hint, anchor=anchor, url=url, topic=topic or anchor)}],
                response_format="json", temperature=0.3)
        except Exception:
            continue
        sent = " ".join(str(out.get("sentence", "")).split()).replace("[", "").replace("]", "")
        hits = list(re.finditer(re.escape(anchor), sent, re.IGNORECASE))
        if (len(hits) == 1 and sent.endswith((".", "!", "?")) and len(sent) <= 220
                and not re.search(r"[\d$%—–]", sent.replace(hits[0].group(0), ""))
                and not sent.lower().startswith(BANNED) and not FRAGMENT.match(sent)
                and overlap(sent, hint) < 0.5):
            h = hits[0]
            return sent[:h.start()] + f"[{h.group(0)}]({url})" + sent[h.end():]
    return None


_PAGE_CACHE: dict[str, list[str]] = {}


def page_sentences(url: str) -> list[str]:
    """The source page's body sentences, live."""
    if url not in _PAGE_CACHE:
        from bs4 import BeautifulSoup
        try:
            html = requests.get(url, headers=UA, timeout=40).text
        except requests.RequestException:
            html = ""
        soup = BeautifulSoup(html, "html.parser")
        for t in soup.select("header, footer, nav, script, style"):
            t.decompose()
        text = " ".join(soup.get_text(" ", strip=True).split())
        _PAGE_CACHE[url] = [x for x in re.split(r"(?<=[.!?])\s+", text) if len(x) > 30]
        time.sleep(1)
    return _PAGE_CACHE[url]


def repeats_page(added: str, url: str, anchor: str) -> bool:
    """The agent often rewrites a NEARBY sentence; appended after the placement
    sentence that duplicates text already on the page (Superior, 2026-10-13)."""
    plain = _LINK.sub(r"", added).replace(anchor, " ")
    return any(overlap(plain, sent) >= 0.6 for sent in page_sentences(url))


def repair(hint: str, snippet: str, anchor: str, url: str, topic: str = "") -> tuple[str, str, str] | None:
    """Reshape the agent's copy snippet into the placement-hint contract: the
    whole original sentence survives untouched.

    The agent's enrichment usually REWRITES the sentence with the link inside
    it. Pasted after the original that duplicates the text, and its own
    verifier rejects it as dropping the original wording (all 17 of Bart's
    first quota-run rows). So:
      wrap   - the anchor is already a phrase of the sentence: link it in place;
      append - the agent wrote a genuinely new sentence: keep it after the
               original; otherwise the agent's model client writes one new
               sentence after the original, with the agent's anchor.
    Returns (mode, anchor, snippet) or None."""
    m = re.search(re.escape(anchor), hint, re.IGNORECASE)
    if m:
        a = m.group(0)
        return "wrap", a, hint[:m.start()] + f"[{a}]({url})" + hint[m.end():]
    lk = _LINK.search(snippet)
    if not lk or lk.group(2).rstrip("/") != url.rstrip("/"):
        return None
    rest = snippet[len(hint):].strip() if snippet.startswith(hint) else ""
    plain = _LINK.sub(r"\1", rest or snippet)
    claims = re.search(r"[\d$%—–]|thousands|millions|hundreds", plain.replace(lk.group(1), ""), re.I)
    if (plain[:1].isupper() and not FRAGMENT.match(plain) and overlap(plain, hint) < 0.5
            and plain.endswith((".", "!", "?")) and not plain.lower().startswith(BANNED)
            and not claims):
        return "append", lk.group(1), f"{hint} {rest or snippet.strip()}"
    sent = follow_sentence(hint, lk.group(1), url, topic)
    if not sent:
        return None
    return "append", _LINK.search(sent).group(1), f"{hint} {sent}"


def mode_of(hint: str, snippet: str) -> str:
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(snippet))
    if " ".join(plain.split()) == " ".join(str(hint).split()):
        return "wrap"
    if plain.startswith(str(hint)):
        return "append"
    return "replace"


def post_urls(base: str, posts_rule: str) -> set[str]:
    """Every post URL by the client's own rule: a sitemap name (post-sitemap,
    numbered splits included) or a path prefix (/blog/)."""
    out: set[str] = set()
    for name in ("/sitemap_index.xml", "/sitemap.xml"):
        r = requests.get(base.rstrip("/") + name, headers=UA, timeout=40)
        if r.status_code == 200 and "<loc>" in r.text:
            break
    maps = re.findall(r"<loc>([^<]+)</loc>", r.text) if "<sitemapindex" in r.text else [base.rstrip("/") + name]
    for sm in maps:
        stem = Path(urlparse(sm.strip()).path).stem
        if not posts_rule.startswith("/") and not re.fullmatch(re.escape(posts_rule) + r"\d*", stem):
            continue
        x = requests.get(sm.strip(), headers=UA, timeout=40).text
        for u in re.findall(r"<loc>([^<]+)</loc>", x):
            if not posts_rule.startswith("/") or urlparse(u).path.startswith(posts_rule):
                out.add(norm(u.strip()))
        time.sleep(1)
    return out


def section_b(client_name: str, base: str, impressions: dict[str, float]) -> pd.DataFrame:
    """Sitemap URLs changed in the last 60 days with no impressions and no
    internal link pointing at them, by the agent's link data."""
    sys.path.insert(0, str(ILA))
    from dotenv import load_dotenv
    load_dotenv(ILA / ".env")
    from internal_link_agent.utils.supabase_client import get_client, load_client_page_content
    linked: set[str] = set()
    sb = get_client()
    start = 0
    while True:
        rows = (sb.table("client_inlinks").select("destination_url")
                .eq("client_name", client_name).range(start, start + 999).execute().data or [])
        linked |= {norm(r["destination_url"]) for r in rows}
        if len(rows) < 1000:
            break
        start += 1000
    for src, md in load_client_page_content(client_name).items():
        for href in re.findall(r"\]\(([^)\s]+)", md):
            linked.add(norm(urljoin(src, href.split("#")[0])))

    urls = []
    for name in ("/sitemap_index.xml", "/sitemap.xml"):
        r = requests.get(base.rstrip("/") + name, headers=UA, timeout=40)
        if r.status_code == 200 and "<loc>" in r.text:
            break
    children = re.findall(r"<loc>([^<]+)</loc>", r.text) if "<sitemapindex" in r.text else [base.rstrip("/") + name]
    for sm in children:
        x = requests.get(sm.strip(), headers=UA, timeout=40).text
        urls += re.findall(r"<url>\s*<loc>([^<]+)</loc>(?:\s*<lastmod>([^<]+)</lastmod>)?", x)
        time.sleep(1)
    cutoff = (date.today() - timedelta(days=ORPHAN_DAYS)).isoformat()
    rows = [{"URL": u.strip(), "Lastmod": (lm or "")[:10]} for u, lm in urls
            if (lm or "")[:10] >= cutoff and impressions.get(norm(u), 0) == 0
            and norm(u) not in linked and not u.endswith((".kml", ".xml"))]
    return pd.DataFrame(rows, columns=["URL", "Lastmod"])


def main(slug: str) -> None:
    c = yaml.safe_load((ROOT / "clients/registry.yaml").read_text(encoding="utf-8"))[slug]
    month = date.today().strftime("%Y-%m")
    here = ROOT / c["folder"] / "internal_links" / month
    global AGENT_LOG
    AGENT_LOG = here / "run_3_1.log"       # engine output, so the month's drop counts are on file
    tfile = here / "3.1-targets.csv"
    if not tfile.exists():
        raise SystemExit(f"run scripts/plan_3_1.py {slug} first: {tfile} is missing")
    targets = {norm(r["target_url"]): r for r in csv.DictReader(tfile.open(encoding="utf-8"))}
    used: dict[str, int] = {}
    missing = "--missing" in sys.argv
    if missing:
        on_tab = tab_links(c["sheet_id"])
        targets = {t: r for t, r in targets.items() if t not in {x["target"] for x in on_tab}}
        for x in on_tab:
            used[x["source"]] = used.get(x["source"], 0) + 1
        print(f"  --missing: {len(targets)} planned target(s) have no row on the 3.1 tab; "
              f"{len(used)} source page(s) already carry links this month")
        if not targets:
            return

    cfg_path = ila_config(c["domain"])
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    tun = dict(cfg.get("link_recommender_tunables") or {})
    tun.update({"target_allowlist": [r["target_url"] for r in targets.values()],
                "target_quota": {r["target_url"]: QUOTA[r["group"]] + (r["group"] == "2.1 pages")
                                 for r in targets.values()},
                "min_source_clicks": int(c.get("links_min_clicks", 10)),
                "min_source_impressions": int(c.get("links_min_impressions", 0))})
    run_cfg = {**cfg, "link_recommender_tunables": tun,
               "content_from_client_page_content": True, "skip_supabase_writes": False}
    # The agent reads stored embeddings only through `embeddings_csv`. A client
    # loaded through run_3_1's own loader path (Education Walkthrough, Oct 2026)
    # has its file under outputs/workbook-3.1/.
    built = ILA / "outputs" / "workbook-3.1" / f"{slug}_embeddings.csv"
    if not cfg.get("embeddings_csv") and built.exists():
        run_cfg["embeddings_csv"] = built.relative_to(ILA).as_posix()
    work = ILA / "outputs" / "workbook-3.1" / slug / month
    work.mkdir(parents=True, exist_ok=True)
    p1 = work / "pass1_config.json"
    p1.write_text(json.dumps(run_cfg, indent=2), encoding="utf-8")

    reuse = "--reuse" in sys.argv
    print(f"=== {c['name']}: {len(targets)} targets" + (" (reusing the agent's last output)" if reuse else ""))
    if reuse:
        recs_path = latest_recs(cfg["client_name"])
        final = select(pd.read_excel(recs_path, "Link Recommendations"), targets, used)
    else:
        recs_path, final = run_agent(slug, cfg, run_cfg, work, targets, used)
    return finish(slug, c, cfg, month, here, work, targets, recs_path, final, missing)


def run_agent(slug, cfg, run_cfg, work, targets, used=None):
    p1 = work / "pass1_config.json"
    print("=== pass 1 (agent)")
    # Same-day rerun: reuse today's GSC, clustering and taxonomy checkpoints.
    safe = re.sub(r"[^a-z0-9_-]", "_", cfg["client_name"].lower())
    today_ckpt = ILA / "outputs" / f"{safe}_{date.today():%Y%m%d}" / "_checkpoints"
    first = "--resume" if any(today_ckpt.glob("04_taxonomy*")) else "--fresh"
    agent(["scripts/run.py", "--config", p1.relative_to(ILA).as_posix(), first])
    shortlist = select(pd.read_excel(latest_recs(cfg["client_name"]), "Link Recommendations"),
                       targets, used)
    sources = sorted(set(shortlist["Source URL"]))
    print(f"  pass 1 kept {len(shortlist)} rows from {len(sources)} source pages")

    p2 = work / "pass2_config.json"
    p2.write_text(json.dumps({**run_cfg, "live_refresh_urls": sources}, indent=2), encoding="utf-8")
    print("=== pass 2 (agent, resume, shortlisted sources fetched live)")
    agent(["scripts/run.py", "--config", p2.relative_to(ILA).as_posix(), "--resume"])
    recs_path = latest_recs(cfg["client_name"])
    return recs_path, select(pd.read_excel(recs_path, "Link Recommendations"), targets, used)


def finish(slug, c, cfg, month, here, work, targets, recs_path, final, missing=False):
    final = final.copy()
    final["Mode"] = ""
    # P0, posts-only sources (the agent's .claude/rules/source-must-be-post.md).
    # The agent's URL guard does not cover /service-areas/ and its classifier
    # let Comfort's West Haven city page through as a source (2026-10-13).
    posts_rule = (c.get("crawl", {}).get("posts") or ["post-sitemap"])[0]
    posts = post_urls(cfg["gsc_property"], posts_rule)
    not_post = final[~final["Source URL"].map(norm).isin(posts)]
    if len(not_post):
        print(f"  P0: dropped {len(not_post)} rows whose source is not a post: "
              f"{sorted(set(not_post['Source URL']))}")
    final = final[final["Source URL"].map(norm).isin(posts)]
    if int(c.get("links_min_clicks", 10)) == 0 or c.get("links_index_screen"):
        final, dropped = index_screen(final, c, month)
        for u, why in dropped:
            print(f"  index screen: dropped source {u} ({why})")
    fixed, unrepairable = [], []
    for i, r in final.iterrows():
        res = repair(str(r["Placement Hint"]), str(r["Copy Snippet"]), str(r["Anchor Text"]),
                     str(r["Target URL"]), str(r.get("Target Core Topic", "") or ""))
        if res is None:
            unrepairable.append(i)
            continue
        mode, anchor, snip = res
        if mode == "append":
            added = snip[len(str(r["Placement Hint"])):].strip()
            if repeats_page(added, str(r["Source URL"]), anchor):
                sent = follow_sentence(str(r["Placement Hint"]), anchor, str(r["Target URL"]),
                                       str(r.get("Target Core Topic", "") or ""))
                if not sent or repeats_page(sent, str(r["Source URL"]), anchor):
                    unrepairable.append(i)
                    continue
                anchor = _LINK.search(sent).group(1)
                snip = f'{r["Placement Hint"]} {sent}'
        final.at[i, "Mode"], final.at[i, "Anchor Text"], final.at[i, "Copy Snippet"] = mode, anchor, snip
        fixed.append(i)
    print(f"  placement contract: {len(fixed)} rows reshaped (wrap/append), "
          f"{len(unrepairable)} could not be and are dropped")
    unfixable = final.loc[unrepairable]
    final = final.loc[fixed]

    out = here / f"{c['name']} - 3.1 {month}{' missing' if missing else ''}.xlsx"
    verify_rel = (work / "verify.xlsx").relative_to(ILA).as_posix()
    final[["Source URL", "Target URL", "Anchor Text", "Placement Hint", "Copy Snippet", "Mode"]] \
        .to_excel(ILA / verify_rel, sheet_name="Verify", index=False)
    vcfg_path = ILA / "configs" / "link_verify.json"
    vcfg = json.loads(vcfg_path.read_text(encoding="utf-8"))
    base = cfg["gsc_property"].rstrip("/")
    extra = next((v.get("extra_strip_selectors", []) for v in vcfg["clients"].values()
                  if v["base_url"].rstrip("/") == base), [])
    key = f"{slug}_{month.replace('-', '_')}"
    vcfg["clients"][key] = {"base_url": base, "workbook": verify_rel, "workbook_sheet": "Verify",
                            "snippet_format": "markdown", "template_anchors": [],
                            "extra_strip_selectors": extra, "client_config": None,
                            "__note": "Monthly workbook 3.1, the agent's own recommendations "
                                      "for the workbook's targets (scripts/run_3_1.py)."}
    vcfg_path.write_text(json.dumps(vcfg, indent=2) + "\n", encoding="utf-8")
    print("=== live verification")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    v = subprocess.run([sys.executable, "-W", "ignore", "scripts/verify_link_workbook.py",
                        "--client", key], cwd=ILA, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(v.stdout[-3000:])
    failing = {int(m) for m in re.findall(r"FAIL row (\d+)", v.stdout)}
    failed = pd.concat([final.iloc[sorted(failing)] if failing else final.iloc[0:0], unfixable, not_post])
    final = final.drop(final.index[sorted(failing)]) if failing else final

    gsc_pages = pd.read_excel(recs_path.parent / recs_path.name.replace(
        "_link_recommendations.xlsx", "_page_taxonomy.xlsx"))
    cols = {col.lower(): col for col in gsc_pages.columns}
    impressions = ({norm(u): v for u, v in zip(gsc_pages[cols["url"]], gsc_pages[cols["impressions"]])}
                   if "url" in cols and "impressions" in cols else {})
    new_urls = section_b(cfg["client_name"], base, impressions)

    # Every planned target leaves with a row (owner, 2026-10-26): one with
    # Built 0 carries why, and fill_3_1.py writes it to the tab as Skipped.
    proposed = set(pd.read_excel(recs_path, "Link Recommendations")["Target URL"].map(norm))
    notes = []
    for t, r in targets.items():
        got = final[final["Target URL"].map(norm) == t]
        reason = "" if len(got) else ("failed checks" if t in proposed else "no source")
        notes.append({"Target URL": r["target_url"], "Group": r["group"],
                      "Wanted": QUOTA[r["group"]], "Built": len(got), "Reason": reason})
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        final.to_excel(xw, sheet_name="Link Recommendations", index=False)
        pd.DataFrame(notes).to_excel(xw, sheet_name="Target Notes", index=False)
        new_urls.to_excel(xw, sheet_name="New URLs", index=False)
        failed.to_excel(xw, sheet_name="Failed Live Check", index=False)
    print(f"\nwrote {out}")
    print(f"  {len(final)} rows into {final['Target URL'].map(norm).nunique()} of {len(targets)} "
          f"targets; {len(failed)} dropped by the live check; section B {len(new_urls)} URLs")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    main(sys.argv[1])
