"""Task 1.4 - Verify AI crawler access and raw HTML rendering.

Fills sections A, B and D. Section C (server logs / CDN analytics) is left blank
by design: we do not have hosting or Cloudflare dashboard access for most of
these clients, so there is nothing to read. The tab already marks it optional.

    python scripts/run_1_4.py all
    python scripts/run_1_4.py arsenal

Two independent signals per bot, because either alone is misleading:

  robots.txt   authoritative and complete. Parsed properly: the most specific
               matching user-agent group wins, and `*` applies only when no
               named group matches.
  live fetch   the homepage requested with that bot's real user-agent string.

A live 403 is conclusive proof of blocking. A live 200 is NOT proof of access:
Cloudflare verifies AI bots by IP and signature, not by the UA string, so a
spoofed UA from our address can sail through while the real bot is blocked at
the edge. Six of eight clients sit behind Cloudflare. The notes say so on every
row rather than letting a green result overstate itself, and the WAF row stays
with the owner because reading that toggle needs dashboard access.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import time
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sheets_io as S              # noqa: E402
import crawl_targets as CT         # noqa: E402

TAB = "1.4 AI Access Check"
MARKS = {"oai": "OAI-SearchBot", "claude": "Claude-SearchBot",
         "plx": "PerplexityBot", "user": "User-triggered fetchers",
         "train": "GPTBot / CCBot", "waf": "Cloudflare/WAF",
         "bsec": "Page URL", "csec": "C. Server log", "dsec": "Fix"}

# The bots that matter for AI search visibility, split by what they are for.
# Training crawlers are a business decision, never an automatic fix.
SEARCH = {"OAI-SearchBot": "OpenAI, powers ChatGPT search results",
          "Claude-SearchBot": "Anthropic, powers Claude search results",
          "PerplexityBot": "Perplexity's index"}
FETCHERS = {"ChatGPT-User": "fetches a page when a user asks about it",
            "Claude-User": "same, for Claude",
            "Perplexity-User": "same, for Perplexity"}
TRAINING = {"GPTBot": "OpenAI model training",
            "CCBot": "Common Crawl, feeds many models",
            "Google-Extended": "Gemini training",
            "Applebot-Extended": "Apple Intelligence training"}

PACE = 0.4             # seconds between page fetches, see the note in main()
MIN_WORDS = 120        # below this, a page has no readable content without JS
PER_TEMPLATE = 5       # sampled URLs per template, plus the homepage always

# Sample per TEMPLATE, never as a percentage of the site. What section B tests
# is a property of the template: pages of one template come out of one code
# path, so a client-rendered template is caught by the first sample and the
# fortieth adds nothing. Arsenal would read identically at 3 URLs or 300,
# because every route serves a byte-identical shell.
#
# A percentage also misallocates. Snow is ~900 blog posts out of 1,009 in-scope
# URLs, so 2% would spend 18 of its 20 requests on posts and barely touch
# products and collections, which are the commercially important templates.
# Five per template spends the same 20 requests across all four.


def templates(sitemap: str, site: str, cfg: dict, keep: set[str]) -> dict[str, list[str]]:
    """Group in-scope URLs by template.

    Posts are identified from the SITEMAP GROUP they came from, not from their
    URL path. Superior's posts sit at the root (/why-is-my-toilet-running/) and
    its `posts` rule is the sitemap name `post-sitemap`, so path matching filed
    every single post as its own template. That is the third time a sitemap-name
    rule has been mistaken for a URL-substring rule; classify with
    crawl_targets.collect, which already knows the difference.

    Everything else groups on its top path folder, so /service-areas/ and
    /plumbing-services/ are treated as different templates, which they are.
    """
    post_pat = (cfg.get("crawl") or {}).get("posts") or ["post-sitemap"]
    root = site.rstrip("/")
    posts: set[str] = set()
    try:
        for name, entries in CT.collect(sitemap).items():
            if any(p.lower() in name.lower() for p in post_pat):
                posts |= {loc.rstrip("/") for loc, _ in entries}
    except Exception:
        pass

    out: dict[str, list[str]] = {}
    for u in sorted(keep):
        if u.rstrip("/") == root:
            continue
        if u.rstrip("/") in posts or any(p.lower() in u.lower() for p in post_pat
                                         if p.startswith("/")):
            key = "post"
        else:
            seg = [x for x in (u[len(root):] if u.startswith(root) else u).split("/") if x]
            key = seg[0] if seg else "root"
            if len(seg) == 1:
                # A flat architecture puts every money page at the root, so
                # first-segment grouping files each one as its own template:
                # Beehive produced 55 "templates" and Arsenal 30, which is just
                # a list of pages wearing a different hat. Root-level pages are
                # pooled into one group and sampled together.
                key = "money page (root level)"
        out.setdefault(key, []).append(u)
    return out


def sample(group: list[str], n: int = PER_TEMPLATE) -> list[str]:
    """Evenly spaced across the sorted group, not the first n.

    Taking the first n alphabetically clusters the sample in one corner of the
    template, which on a city-page set means five neighbouring towns.
    """
    g = sorted(group)
    if len(g) <= n:
        return g
    step = len(g) / n
    return [g[int(i * step)] for i in range(n)]


def fetch(url: str, ua: str, timeout: int = 25):
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": ua}), timeout=timeout)
        return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", dict(e.headers or {})
    except Exception as e:
        return e.__class__.__name__, "", {}


def parse_robots(text: str) -> dict[str, list[tuple[str, str]]]:
    """user-agent -> [(rule, path)], grouped the way the standard defines it.

    Consecutive User-agent lines share one rule block. Written out rather than
    using urllib.robotparser because that returns a yes/no and we need to show
    WHICH directive decided it, and on which user-agent group.
    """
    groups: dict[str, list[tuple[str, str]]] = {}
    current: list[str] = []
    fresh = True
    for raw in text.splitlines():
        line = raw.split("#")[0].strip()
        if not line or ":" not in line:
            continue
        field, _, value = line.partition(":")
        field, value = field.strip().lower(), value.strip()
        if field == "user-agent":
            if not fresh:
                current, fresh = [], True
            current.append(value.lower())
            groups.setdefault(value.lower(), [])
        elif field in ("allow", "disallow") and current:
            fresh = False
            for ua in current:
                groups.setdefault(ua, []).append((field, value))
    return groups


def robots_verdict(groups: dict, bot: str, path: str = "/") -> tuple[bool, str]:
    """Is `bot` allowed to fetch `path`, and which rule decided it.

    A named group wins outright over `*`, even when the named group is empty:
    that is the standard's behaviour and it is the usual way a site accidentally
    grants blanket access to one bot while restricting everything else.
    """
    key = bot.lower()
    named = key in groups
    rules = groups.get(key) if named else groups.get("*", [])
    src = f"its own User-agent: {bot} group" if named else "the User-agent: * group"
    if not rules:
        return True, (f"No rule for it. Matched {src}, which sets no Disallow, "
                      f"so it is allowed by default.")
    # Longest matching path wins; Allow beats Disallow at equal length.
    best, decided = -1, None
    for rule, value in rules:
        if not value:
            continue
        if path.startswith(value) and len(value) >= best:
            if len(value) > best or rule == "allow":
                best, decided = len(value), (rule, value)
    if decided is None:
        return True, f"Matched {src}; no directive covers {path}, so allowed."
    rule, value = decided
    return rule == "allow", (f"Matched {src}: {rule.title()}: {value}")


def _dfs_creds():
    """DataForSEO login/password from the environment or .env."""
    import os
    lo, pw = os.environ.get("DATAFORSEO_LOGIN"), os.environ.get("DATAFORSEO_PASSWORD")
    if not (lo and pw):
        env = pathlib.Path(".env")
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("DATAFORSEO_LOGIN="):
                    lo = line.split("=", 1)[1].strip()
                elif line.startswith("DATAFORSEO_PASSWORD="):
                    pw = line.split("=", 1)[1].strip()
    return lo, pw


def dfs_page(url: str, ua: str) -> dict | None:
    """Raw-HTML metrics fetched from DataForSEO's addresses instead of ours.

    This exists because a 403 to us is not evidence about the client's site.
    Education Walkthrough refuses this machine on every user-agent including
    plain Chrome, so section B recorded a Fail that said nothing about whether
    an AI crawler can read the page. Through DFS the same URL returns 200 with
    593 words and a real H1.

    JavaScript stays off: the question section B asks is what a crawler that
    does not execute JS receives, so rendering here would answer a different
    question and mark broken pages as fine.
    """
    import base64
    import json as _json
    lo, pw = _dfs_creds()
    if not (lo and pw):
        return None
    body = _json.dumps([{"url": url, "enable_javascript": False,
                         "custom_user_agent": ua}]).encode()
    tok = base64.b64encode(f"{lo}:{pw}".encode()).decode()
    req = urllib.request.Request(
        "https://api.dataforseo.com/v3/on_page/instant_pages", data=body,
        headers={"Authorization": f"Basic {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = _json.loads(r.read().decode("utf-8", "replace"))
        item = d["tasks"][0]["result"][0]["items"][0]
    except Exception:
        return None
    meta = item.get("meta") or {}
    h = meta.get("htags") or {}
    return {"status": item.get("status_code"),
            "words": ((meta.get("content") or {}).get("plain_text_word_count") or 0),
            "title": meta.get("title") or "",
            "h1": len(h.get("h1") or []), "h2": len(h.get("h2") or []),
            "links": meta.get("internal_links_count") or 0,
            "via": "DataForSEO (our address is blocked by this site)"}


def dfs_robots(site: str) -> tuple[str, str] | None:
    """robots.txt via DataForSEO when the site refuses us directly.

    Returns (synthetic_robots_text, caveat). This matters more than the render
    fallback: a 403 on robots.txt yields an EMPTY rule set, and an empty rule
    set parses as "no rule for this bot, therefore allowed". Section A then
    reports every AI crawler as Pass without a single byte of the file having
    been read. Education Walkthrough shipped exactly that.

    DFS returns parsed allow/disallow lists rather than raw text, so the
    user-agent groups are lost and everything is reconstructed under "*". That
    is enough to prove no blanket block exists, and NOT enough to prove a
    specific bot is unnamed. The caveat travels into the sheet rather than being
    dropped, because a verdict is only worth what its evidence supports.
    """
    import base64
    import json as _json
    lo, pw = _dfs_creds()
    if not (lo and pw):
        return None
    body = _json.dumps([{"url": site.rstrip("/") + "/robots.txt",
                         "enable_javascript": False}]).encode()
    tok = base64.b64encode(f"{lo}:{pw}".encode()).decode()
    req = urllib.request.Request(
        "https://api.dataforseo.com/v3/on_page/instant_pages", data=body,
        headers={"Authorization": f"Basic {tok}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = _json.loads(r.read().decode("utf-8", "replace"))
        meta = d["tasks"][0]["result"][0]["items"][0]["meta"]
    except Exception:
        return None
    lines = ["User-agent: *"]
    lines += [f"Disallow: {x}" for x in (meta.get("disallow_list") or [])]
    lines += [f"Allow: {x}" for x in (meta.get("allow_list") or [])]
    return "\n".join(lines), (
        "robots.txt read through DataForSEO because this site returns 403 to our "
        "address and to WebFetch. DFS returns parsed rules, so user-agent groups "
        "could not be recovered: this confirms no blanket Disallow exists, but "
        "cannot confirm whether a bot is named in its own group.")


def probe_render(url: str, ua: str) -> dict:
    """What an AI crawler that does not run JavaScript actually receives."""
    st, html, _ = fetch(url, ua, timeout=30)
    if not html:
        # Our address refused, which says nothing about the page. Ask from
        # somewhere else before recording a failure against the client.
        alt = dfs_page(url, ua)
        if alt:
            return alt
        return {"status": st, "words": 0, "h1": 0, "h2": 0, "links": 0, "title": ""}
    body = re.sub(r"(?is)<(script|style|noscript).*?</\1>", " ", html)
    txt = " ".join(re.sub(r"<[^>]+>", " ", body).split())
    host = re.escape(url.split("/")[2])
    links = set(re.findall(
        r"href=[\"']((?:/|https?://[^\"']*" + host + r")[^\"']*)", html))
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return {"status": st, "words": len(txt.split()),
            "title": (t.group(1).strip() if t else ""),
            "h1": len(re.findall(r"(?i)<h1[\s>]", html)),
            "h2": len(re.findall(r"(?i)<h2[\s>]", html)), "links": len(links)}


BASELINE = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def baseline_ok(site: str) -> tuple[bool, object]:
    """Can we reach this site at all right now, with an ordinary browser UA?

    THE CONTROL, and it is not optional. Without it a refusal cannot be
    attributed: Education Walkthrough returned 403 to every AI bot UA during
    testing and the run wrote three "unblock this bot" fixes plus a rendering
    failure. The site was in fact rate-limiting OUR address after repeated
    probing this session, and was refusing plain Chrome identically. Reporting
    our own throttling as the client's bot policy is the same mistake that put
    337 false sitemap findings and 20 false throttle findings into live sheets.

    Retries with backoff first, because a single 403 may just be pace.
    """
    import random
    import time
    last = None
    for attempt in range(3):
        st, _, _ = fetch(site, BASELINE, timeout=25)
        if st == 200:
            return True, st
        last = st
        time.sleep(2 ** attempt + random.random())
    # Stays FALSE when our address is refused, even though DFS can reach the
    # site. Two different questions share one flag otherwise, and conflating
    # them wrote four false "unblock this bot" fixes into a live sheet:
    #
    #   can WE reach it        -> decides whether a bot 403 is ATTRIBUTABLE.
    #                             The bot fetches leave from this address, so
    #                             if plain Chrome is refused here, a bot 403
    #                             here is evidence about our IP, not their
    #                             policy. That is what this function answers.
    #   is it reachable at all -> decides whether section B can be MEASURED,
    #                             which the DFS fallback can satisfy. See
    #                             `measurable` in audit().
    return False, last


def sitemap_for(cfg: dict, site: str) -> str:
    """The client's real sitemap URL.

    Assuming /sitemap_index.xml silently cost Cudio its whole section B sample:
    its sitemap is /sitemap.xml, the guess 404'd, the exception was swallowed and
    only the homepage got checked. The registered path is already recorded in the
    monthly index_audit cache, so read it rather than guessing.
    """
    import datetime as _dt
    import json as _json
    month = _dt.date.today().strftime("%Y-%m")
    cache = Path(cfg["folder"]) / "Monthly SEO Workbook" / month / "index_audit.json"
    if cache.exists():
        try:
            sms = _json.loads(cache.read_text(encoding="utf-8")).get("sitemaps") or []
            if sms:
                return sms[0]
        except Exception:
            pass
    root = site.rstrip("/")
    for cand in (f"{root}/sitemap_index.xml", f"{root}/sitemap.xml"):
        st, _, _ = fetch(cand, BASELINE, timeout=20)
        if st == 200:
            return cand
    return f"{root}/sitemap.xml"


def render_check(urls: list[str]) -> dict[str, dict]:
    """Render the pages that failed the raw check, to quantify what JS adds.

    Only ever called on failures, so it costs nothing on the seven clients whose
    raw HTML is already complete. On Arsenal it turns "FAIL, 8 words" into the
    number that actually makes the case: 1,810 words rendered against 8 raw, and
    a title that differs between the two.
    """
    out: dict[str, dict] = {}
    if not urls:
        return out
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return out
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page()
            for u in urls:
                try:
                    pg.goto(u, timeout=30000, wait_until="networkidle")
                    out[u] = pg.evaluate(
                        r"() => {const t=(document.body.innerText||'')"
                        r".replace(/\s+/g,' ').trim();"
                        "return {words:t.split(' ').length,"
                        "h1:document.querySelectorAll('h1').length,"
                        "h2:document.querySelectorAll('h2').length,"
                        "title:document.title,"
                        "jsonld:document.querySelectorAll("
                        "'script[type=\"application/ld+json\"]').length};}")
                except Exception:
                    pass
            b.close()
    except Exception:
        pass
    return out


def scope_fallback(cfg: dict, site: str) -> dict[str, list[str]]:
    """Template groups from Clients/<folder>/url_scope.txt when no sitemap.

    The scope file is generated from GSC pages, so it covers URLs that have had
    impressions and misses anything that has never ranked. Narrower than a
    sitemap and honest about it, which beats reporting the homepage alone as a
    completed check.
    """
    root = site.rstrip("/")
    f = pathlib.Path(cfg.get("folder", "")) / "url_scope.txt"
    if not f.exists():
        return {}
    urls = [l.strip() for l in f.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]
    money = {u.rstrip("/") for u in ((cfg.get("crawl") or {}).get("money_pages") or [])}
    pats = (cfg.get("crawl") or {}).get("money") or []
    out: dict[str, list[str]] = {}
    for u in sorted(set(urls)):
        if u.rstrip("/") == root:
            continue
        if u.rstrip("/") in money or any(p.lower() in u.lower() for p in pats):
            key = "money page (allowlist)"
        else:
            seg = [x for x in (u[len(root):] if u.startswith(root) else u).split("/") if x]
            key = "post" if len(seg) == 1 else (seg[0] if seg else "root")
        out.setdefault(key, []).append(u)
    return out


def audit(slug: str, cfg: dict) -> dict:
    site = cfg["gsc_property"]
    reachable, base_status = baseline_ok(site)
    # Reachable by SOME route. Section B only needs the page readable, and the
    # render probe already falls back to DFS, so a site that refuses us can
    # still be measured honestly. Never use this for bot attribution.
    measurable = reachable or bool(dfs_page(site, BASELINE))
    st, robots, _ = fetch(site.rstrip("/") + "/robots.txt", "Mozilla/5.0 (SEOAudit)")
    robots_caveat = ""
    if not (isinstance(st, int) and st == 200 and robots.strip()):
        alt = dfs_robots(site)
        if alt:
            robots, robots_caveat = alt
            st = 200
        else:
            robots = ""
    groups = parse_robots(robots if isinstance(st, int) and st == 200 else "")
    _, _, hdr = fetch(site, "Mozilla/5.0 (SEOAudit)")
    server = (hdr.get("server") or hdr.get("Server") or "unknown").lower()
    cf = "cloudflare" in server

    def check(bots: dict) -> list[dict]:
        out = []
        for bot, what in bots.items():
            ok, why = robots_verdict(groups, bot)
            live, _, _ = fetch(site, f"Mozilla/5.0 (compatible; {bot}/1.0)")
            out.append({"bot": bot, "what": what, "robots_ok": ok, "why": why,
                        "live": live})
        return out

    search, fetchers, training = check(SEARCH), check(FETCHERS), check(TRAINING)

    # Section B: the homepage always, plus up to PER_TEMPLATE per template, all
    # drawn from the owner's in-scope set so nothing outside the brief is graded.
    pages = [("homepage", site)]
    groups: dict[str, list[str]] = {}
    try:
        sm = sitemap_for(cfg, site)
        keep = CT.scope_urls(sm, site, cfg)
        groups = templates(sm, site, cfg, keep)
    except Exception:
        groups = {}
    if not groups:
        # The sitemap is unreachable. That happens when a site refuses our
        # address, and it used to reduce section B to the homepage alone while
        # still reporting a result, which reads as "checked" rather than "could
        # not check". GSC is the fallback inventory because it is the one list
        # of this site's URLs we can always read.
        #
        # Post-versus-money classification normally comes from the sitemap
        # group, which is gone here, so the money_pages allowlist decides it:
        # on a flat architecture like this one, every URL sits at the root and
        # first-segment grouping would file the entire blog as money pages.
        groups = scope_fallback(cfg, site)

    # Owner rule (set on EW, 2026-08-19): the render sample checks pages with
    # SEO value - content the client is trying to rank. Legal, utility and
    # sales-collateral templates are excluded per client via
    # crawl.access_exclude, applied HERE so it covers the sitemap path AND the
    # GSC scope fallback - the fallback is exactly where EW's terms/,
    # case-studies and instructional-look-fors rows slipped in.
    ex = [x.lower() for x in ((cfg.get("crawl") or {}).get("access_exclude") or [])]
    if ex:
        groups = {k: [u for u in v if not any(p in u.lower() for p in ex)]
                  for k, v in groups.items()}
        groups = {k: v for k, v in groups.items() if v}

    # When a locked monthly plan exists, its targets are the pages this
    # month's work depends on - check them BY NAME rather than leaving them
    # to the luck of even-spaced sampling.
    seen = {site.rstrip("/")}
    try:
        plan = yaml.safe_load((Path(cfg["folder"]) / "monthly_plan/plan.yaml")
                              .read_text(encoding="utf-8"))
        for t in (plan.get("targets") or []):
            u = str(t.get("url", ""))
            if u.startswith("http") and u.rstrip("/") not in seen:
                seen.add(u.rstrip("/"))
                pages.append(("1.8 target", u))
    except OSError:
        pass
    for key in sorted(groups):
        for u in sample(groups[key]):
            if u.rstrip("/") in seen:
                continue
            seen.add(u.rstrip("/"))
            pages.append((key, u))

    rend = []
    for label, u in pages:
        rend.append((label, u, probe_render(
            u, "Mozilla/5.0 (compatible; OAI-SearchBot/1.0)")))
        time.sleep(PACE)

    fails = [u for _, u, r in rend
             if r.get("status") == 200 and (r["words"] < MIN_WORDS or r["h1"] < 1)]
    rendered = render_check(fails) if measurable else {}

    return {"rendered": rendered,
            "cf": cf, "server": server, "robots_status": st,
            "search": search, "fetchers": fetchers, "training": training,
            "render": rend, "named": [b for b in groups if b != "*"],
            "reachable": reachable, "measurable": measurable,
            "base_status": base_status}


def write(slug: str, cfg: dict, a: dict) -> dict:
    sid = cfg["sheet_id"]
    p = S.find_rows(sid, TAB, MARKS)
    cfnote = (" Live 200 is not proof of access: this site is behind Cloudflare, "
              "which verifies AI bots by IP and signature rather than the "
              "user-agent string, so a real bot can still be blocked at the edge."
              if a["cf"] else "")
    n, fixes = 0, []
    refused = [i["bot"] for i in a["search"] + a["fetchers"]
               if isinstance(i["live"], int) and i["live"] in (401, 403, 429)]
    if not a["measurable"]:
        refusal = (f"LIVE TESTING INCONCLUSIVE: the site returned "
                   f"{a['base_status']} to an ordinary browser user-agent too, so "
                   f"it is rate-limiting or blocking our address rather than "
                   f"these bots specifically. robots.txt results below are still "
                   f"valid; the live-fetch column is not.")
    elif refused and a["reachable"]:
        refusal = (f"Refused in live testing: {', '.join(refused)}. An ordinary "
                   f"browser user-agent was served normally, so this is specific "
                   f"to those bots.")
    elif refused:
        # measurable-via-DFS but our own address is refused: the bot 403s are
        # NOT attributable. The previous message claimed the browser control
        # passed whenever ANY route worked, which asserted a control result
        # that never happened (caught on EW, 2026-08-19).
        refusal = (f"Live fetches returned {', '.join(sorted(set(str(x) for x in [i['live'] for i in a['search'] + a['fetchers']])))} "
                   f"for AI bot user-agents, but an ordinary browser user-agent "
                   f"is refused from our address too, so these refusals are NOT "
                   f"attributable to the site's bot policy. Rendering was "
                   f"measured through DataForSEO; re-test live fetches from a "
                   f"different network address to close the loop.")
    else:
        refusal = ("No AI bot user-agent was refused in live testing, which rules "
                   "out UA-level blocking but not IP-level blocking.")

    def row(key: str, item: dict) -> None:
        nonlocal n
        # A live refusal only means anything when the control got through.
        blocked_live = (a["reachable"] and isinstance(item["live"], int)
                        and item["live"] in (401, 403, 429))
        ok = item["robots_ok"] and not blocked_live
        note = (f"robots.txt: {'ALLOWED' if item['robots_ok'] else 'BLOCKED'}. "
                f"{item['why']} Live fetch with its user-agent returned "
                f"{item['live']}. {item['what']}.{cfnote}")
        n += S.write(sid, f"'{TAB}'!B{p[key]}:C{p[key]}",
                     [["Pass" if ok else "Issue Found", note]]).cells
        if not ok:
            fixes.append(f"Unblock {item['bot']} - {item['why']}")

    for key, item in zip(("oai", "claude", "plx"), a["search"]):
        row(key, item)

    f_ok = all(i["robots_ok"] for i in a["fetchers"]) and not (
        a["reachable"] and any(isinstance(i["live"], int)
                               and i["live"] in (401, 403, 429)
                               for i in a["fetchers"]))
    n += S.write(sid, f"'{TAB}'!B{p['user']}:C{p['user']}", [[
        "Pass" if f_ok else "Issue Found",
        "; ".join(f"{i['bot']}: {'allowed' if i['robots_ok'] else 'BLOCKED'} "
                  f"(live {i['live']})" for i in a["fetchers"])
        + ". These fetch a page only when a user asks about it, so blocking them "
          "removes the site from answers people are actively requesting." + cfnote]]).cells
    if not f_ok:
        fixes.append("Unblock the user-triggered fetchers (ChatGPT-User, "
                     "Claude-User, Perplexity-User)")

    # Training crawlers are flagged, never fixed. Allowing them is a decision
    # about whether the client wants their content in model training data, and
    # that is the client's call, not an SEO defect.
    n += S.write(sid, f"'{TAB}'!B{p['train']}:C{p['train']}", [[
        "Flagged",
        "BUSINESS DECISION, not a fix. "
        + "; ".join(f"{i['bot']}: {'allowed' if i['robots_ok'] else 'blocked'}"
                    for i in a["training"])
        + ". Allowing these puts the client's content into model training data. "
          "Blocking them does NOT affect whether the site appears in AI search "
          "answers, which is governed by the search bots above. Raise with the "
          "client; do not change it unilaterally."]]).cells

    n += S.write(sid, f"'{TAB}'!B{p['waf']}:C{p['waf']}", [[
        "Owner check",
        f"Server header reports '{a['server']}'. "
        + ("This site is behind Cloudflare, where 'Block AI bots' can be enabled "
           "in one click and is invisible from outside. " + refusal
           + " Confirm in the Cloudflare dashboard under Security > Bots that AI "
             "Scrapers and Crawlers blocking is OFF."
           if a["cf"] else
           "Not Cloudflare, so there is no default AI-bot toggle to check. "
           + refusal)]]).cells

    # Section B has only a handful of template rows before section C begins, so
    # a real sample has to make room rather than write over the next heading.
    b0 = p["bsec"] + 1
    avail = p["csec"] - 2 - b0
    body = []
    for label, url, r in a["render"]:
        st = r["status"]
        if not a["measurable"] or (isinstance(st, int) and st != 200):
            # Classify by status. One canned "this is our rate limit" note used
            # to cover every non-200, which told a reader that a dead page was a
            # network problem on our side. Comfort surfaced three /coupons/ URLs
            # returning 404 while still carrying GSC impressions, reported as
            # "Not measured, our rate limit". They are gone, and that is a
            # finding, not an absence of one.
            if isinstance(st, int) and st in (401, 403, 429):
                body.append([url, "Not measured",
                             f"Fetch returned {st} and an ordinary browser "
                             f"user-agent is refused identically, so this is our "
                             f"address being blocked, not a property of the page. "
                             f"DataForSEO could not reach it either."])
            elif isinstance(st, int) and st == 404:
                body.append([url, "FAIL",
                             f"Returns 404. This URL is in Search Console with "
                             f"recorded impressions, so it ranked recently and is "
                             f"now gone. Not a rendering problem: decide whether "
                             f"to restore it or 301 it to the nearest live page."])
                fixes.append(f"Resolve 404 on {url} - still carries impressions in "
                             f"Search Console. Restore or 301 to the closest live "
                             f"equivalent. This is NOT a rendering fix.")
            else:
                body.append([url, "Not measured",
                             f"Fetch returned {st}. Neither a direct request nor "
                             f"DataForSEO returned a readable page. Re-check "
                             f"before treating this as a site defect."])
            continue
        ok = r["words"] >= MIN_WORDS and r["h1"] >= 1
        note = (f"[{label}] Raw HTML, JavaScript disabled: {r['words']} words, "
                f"{r['h1']} H1, {r['h2']} H2, {r['links']} internal links.")
        if r.get("via"):
            note += (" Fetched via DataForSEO - this site refuses our own "
                     "address, so the direct route could not be used.")
        if ok:
            note += " Readable without JavaScript."
        else:
            rd = a["rendered"].get(url)
            # Two different defects fail this check and they need different
            # fixes. A page with 983 words and no H1 renders perfectly well;
            # calling that "sees effectively nothing" and routing it to
            # server-rendering sends a developer to rebuild a page that only
            # needs a heading.
            thin = r["words"] < MIN_WORDS
            if thin:
                note += (" An AI crawler that does not execute JavaScript sees "
                         "effectively nothing here.")
                if rd:
                    note += (f" Rendered in a browser the same page carries "
                             f"{rd['words']} words, {rd['h1']} H1, {rd['h2']} H2 "
                             f"and {rd['jsonld']} JSON-LD block(s), and its title "
                             f"is \"{rd['title']}\" against \"{r.get('title','?')}\" "
                             f"in raw HTML. Everything that identifies this page "
                             f"is assembled client-side.")
                fixes.append(f"Server-render or pre-render {url} - raw HTML "
                             f"carries only {r['words']} words")
            else:
                note += (f" The content IS in the raw HTML ({r['words']} words, "
                         f"{r['h2']} H2), so rendering is not the problem. What is "
                         f"missing is an H1: nothing on the page states what it is "
                         f"about in a heading, which is the element an assistant "
                         f"leans on hardest when deciding what a page covers.")
                fixes.append(f"Add an H1 to {url} - the page has {r['words']} words "
                             f"and {r['h2']} H2 but no H1. Rendering is fine, do NOT "
                             f"route this to server-rendering work")
        body.append([url, "Pass" if ok else "FAIL", note])

    need_rows = len(body) - avail
    if need_rows > 0:
        S.insert_rows(sid, TAB, p["csec"] - 1, need_rows)
        p = S.find_rows(sid, TAB, MARKS)      # anchors move when rows are added
    S.clear(sid, f"'{TAB}'!A{b0}:E{p['csec'] - 2}")
    n += S.write(sid, f"'{TAB}'!A{b0}:C{b0 + len(body) - 1}", body).cells

    d0 = p["dsec"] + 1
    S.clear(sid, f"'{TAB}'!A{d0}:B{d0 + 20}")
    if fixes:
        n += S.write(sid, f"'{TAB}'!A{d0}:B{d0 + len(fixes) - 1}",
                     [[f, ""] for f in fixes]).cells
    else:
        # Never claim a clean render pass when nothing was measured. The first
        # EW run wrote "every checked page is readable without JavaScript" on a
        # client where every fetch had been refused.
        measured = sum(1 for _, _, r in a["render"]
                       if a["measurable"] and r.get("status") == 200)
        msg = ("No fixes required from robots.txt: every AI search bot and "
               "user-triggered fetcher is allowed.")
        msg += (f" All {measured} checked page(s) are readable without JavaScript."
                if measured else
                " RENDERING NOT CHECKED: the site refused our requests, including "
                "from an ordinary browser user-agent, so section B is unmeasured. "
                "Re-run before treating this tab as complete.")
        n += S.write(sid, f"'{TAB}'!A{d0}:B{d0}", [[msg, "n/a"]]).cells
    return {"cells": n, "fixes": len(fixes)}


def main() -> int:
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    ap = argparse.ArgumentParser()
    ap.add_argument("client", nargs="?", default="all")
    a = ap.parse_args()
    todo = list(reg) if a.client == "all" else [a.client]
    print("%-22s %-11s %-9s %-7s %s" % ("client", "search bots", "render", "fixes", "server"))
    print("-" * 74)
    for slug in todo:
        try:
            res = audit(slug, reg[slug])
            w = write(slug, reg[slug], res)
            okb = sum(1 for i in res["search"] if i["robots_ok"])
            okr = sum(1 for _, _, r in res["render"]
                      if r["words"] >= MIN_WORDS and r["h1"] >= 1)
            print("%-22s %-11s %-9s %-7d %s"
                  % (slug, f"{okb}/3 allowed", f"{okr}/{len(res['render'])} pass",
                     w["fixes"], res["server"][:22]))
        except Exception as e:
            print(f"{slug:<22} FAILED {e.__class__.__name__}: {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
