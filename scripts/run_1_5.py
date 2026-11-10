"""Fill 1.5 for the remaining seven clients.

Candidates are pooled from decay AND striking distance, because on the
home-services clients the decayed pages are DIY blog posts while the money sits
in striking distance on service pages against local commercial queries. Ranking
on click loss alone would fill four tabs with garbage-disposal how-tos and miss
"furnace repair salt lake city" at position 7.
"""
import datetime as dt
import re
import sys

import yaml
from pathlib import Path

sys.path.insert(0, "scripts")
import prior_work as PW
import worked_urls as WU
import url_cooldown as UC
import sheets_io as S
from task_1_5 import sc, analyse, ctr_curve_text

TAB = "1.5 Candidate List"

# Commercial intent of the QUERY, judged per client business model. This is the
# judgement the whole tab exists for, so it is written out rather than derived.
BUY = ("repair", "replace", "install", "near me", "service", "cost", "price",
       "quote", "emergency", "company", "companies", "contractor", "plumber",
       "buy", "best", "vs", "review", "migration", "consultant", "partner")
DIY = ("how to", "how-to", "diy", "why do", "what is", "can i", "can you",
       "signs", "tips", "ideas", "examples", "thank", "guide to")


def commercial(text):
    t = text.lower()
    if any(k in t for k in DIY):
        return False
    return any(k in t for k in BUY)


def cause(d):
    move = d["pos"] - d["pos_before"]
    ib, ia = d.get("impr_before", 0), d["impr"]
    if move >= 1.5:
        return ("RANKING LOSS", f"position {d['pos_before']:.1f} to {d['pos']:.1f}, "
                f"clicks {d['before']} to {d['after']} on {ia:,} impressions")
    if ib and ia < ib * 0.85:
        return ("DEMAND FALL", f"position held at {d['pos_before']:.1f} to "
                f"{d['pos']:.1f} while impressions fell {ib:,} to {ia:,}, clicks "
                f"{d['before']} to {d['after']}")
    return ("CTR GAP", f"position {d['pos_before']:.1f} to {d['pos']:.1f}, "
            f"impressions {ib:,} to {ia:,}, clicks {d['before']} to {d['after']}")


ACTION = {
    "RANKING LOSS": "content depth and internal links",
    "DEMAND FALL": "validate seasonality year over year BEFORE any rewrite",
    "CTR GAP": "check the SERP for an AI Overview, snippet or PAA first (evidence_1_5.py), then title and "
               "meta judged against this site's own CTR curve",
}


# --- candidacy gates -------------------------------------------------------

RECENT_DAYS = 90           # site-side: sitemap lastmod inside 90 days
# our-side: skip a page for six workbook months after we work or offer it.
# Owner instruction 2026-10-06, for the 1.5 candidate gate only, so it has its
# own constant (url_cooldown.CANDIDATE_LOOKBACK_MONTHS). The shared
# COOLDOWN_MONTHS (three) still governs 2.3, 1.7 and 1.8.
LOOKBACK_WORKBOOKS = UC.CANDIDATE_LOOKBACK_MONTHS

# The 90-day gate above exists because DECAY compares a page against its own
# earlier self, and a page edited inside the window is being compared against a
# different page. That reasoning does not carry to STRIKING DISTANCE, which is
# measured on current position and needs no prior period at all. Applying 90
# days there gated every one of Bart's 18 candidates on edits its own CMS made
# 29 to 78 days ago, and emptied the tab on a client we have never touched.
#
# What striking distance does need is the recrawl window: a page edited days ago
# has not been re-read yet, so its position is not settled and any brief written
# against it would re-touch work that has not had a chance to land.
RECRAWL_DAYS = 28          # site-side, striking distance only: recrawl window

STOP = {"a", "an", "the", "in", "on", "of", "for", "to", "and", "or", "is", "it",
        "my", "your", "how", "much", "does", "do", "what", "near", "me", "best"}


def _lastmod(cfg):
    """URL -> date of last sitemap lastmod. Empty dict if no sitemap is reachable."""
    out = {}
    try:
        import crawl_targets as CT
        # Ask Search Console rather than guessing the filename. Guessing
        # sitemap_index.xml blocked Arsenal, Cudio and Snow, all of which use
        # sitemap.xml, and it presented as "no sitemap reachable".
        sm = cfg.get("sitemap")
        if not sm:
            from googleapiclient.discovery import build as _build
            import task_1_1 as _T1
            _svc = _build("searchconsole", "v1", credentials=_T1.creds(),
                          cache_discovery=False)
            reg_sm = _svc.sitemaps().list(
                siteUrl=cfg["gsc_property"]).execute().get("sitemap", [])
            sm = reg_sm[0]["path"] if reg_sm else None
        if not sm:
            return {}
        for _name, entries in CT.collect(sm).items():
            for loc, lm in entries:
                if not lm:
                    continue
                try:
                    out[loc.rstrip("/")] = dt.date.fromisoformat(str(lm)[:10])
                except ValueError:
                    pass
    except Exception:
        pass
    return out


_PAGE_CACHE = {}


def _onpage(url):
    """{'hay': title+meta+H1, 'topic': title+H1}, both lowercase. None on failure.

    `hay` answers "does the page already say this". `topic` answers "what is this
    page about", and they are different questions: a cost guide mentions the
    service in its meta while its subject is the price.
    """
    if url in _PAGE_CACHE:
        return _PAGE_CACHE[url]
    import re as _re
    import ssl as _ssl
    import urllib.request as _u
    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    # Rate limits and gateway errors are retried with a growing pause and never cached:
    # superiorwaterandair.com answers 429 under load, and a cached 429 read as "returns
    # HTTP 429" dropped healthy pages from a candidate list and left worked URLs unresolved.
    import time as _time
    for attempt in range(4):
        try:
            req = _u.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SEOAudit/1.0)"})
            resp = _u.urlopen(req, timeout=30, context=ctx)
            html = resp.read().decode("utf-8", "replace")
            status, final = resp.status, resp.geturl()
            break
        except Exception as e:
            code = getattr(e, "code", None)
            if code in (429, 502, 503, 504) and attempt < 3:
                _time.sleep(4 * (attempt + 1))
                continue
            if code:
                _PAGE_CACHE[url] = {"hay": None, "topic": "", "status": code, "final": url}
                return _PAGE_CACHE[url]
            return None

    def g(pat):
        m = _re.search(pat, html, _re.I | _re.S)
        return _re.sub(r"<[^>]+>", " ", m.group(1)) if m else ""

    meta = _re.search(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"'](.*?)[\"']",
                      html, _re.I | _re.S)
    title, h1 = g(r"<title[^>]*>(.*?)</title>"), g(r"<h1[^>]*>(.*?)</h1>")
    norm = lambda x: _re.sub(r"\s+", " ", x).lower().strip()
    _PAGE_CACHE[url] = {"hay": norm(" ".join([title, meta.group(1) if meta else "", h1])),
                        "topic": norm(title + " " + h1),
                        "status": status, "final": final}
    return _PAGE_CACHE[url]


def _terms(text, floor=3):
    """Meaningful words in a string. floor=3 for topic fit, where two-letter
    tokens are noise; floor=2 for service matching, where "ac", "iv" and "ev"
    are the whole service name."""
    return [w for w in re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
            if w not in STOP and len(w) >= floor]


def _topic_fit(query, topic):
    """How many of the query's terms the page's own title and H1 also use."""
    t = _terms(topic)
    hits = 0
    for w in _terms(query):
        if any(w == x or (len(w) >= 5 and x.startswith(w[:5])) or
               (len(x) >= 5 and w.startswith(x[:5])) for x in t):
            hits += 1
    return hits



def _resolves_clean(url, page):
    """(ok, reason). A candidate must be the URL that actually serves the page.

    Owner rule 2026-09-03. Arsenal is on Vercel, where /locations/ 308-redirects
    to /locations, so GSC can report a URL that is not the page anyone would
    edit. Optimizing a redirecting URL means editing the wrong page, or none.
    """
    if page is None:
        return False, "could not fetch, status unknown"
    st = page.get("status")
    if st and st != 200:
        return False, f"returns HTTP {st}"
    final = (page.get("final") or url).split("?")[0]
    if final.rstrip("/") != url.rstrip("/"):
        return False, f"redirects to {final}"
    return True, ""


def _has_gap(query, hay):
    """True when a meaningful term of the query is missing from title/meta/H1.

    Owner rule: a page enters an optimization list only if it ranks for a query
    absent from its own title and meta. A page already saying the words is not a
    candidate, and adding them again is keyword stuffing.
    """
    if hay is None:
        return True                      # could not read the page: do not silently drop
    for t in _terms(query):
        if t in hay:
            continue
        if len(t) >= 6 and t[:6] in hay:  # sealcoating / sealcoat
            continue
        return True
    return False



# Words that appear in money-page slugs on every site and name no service.
_SLUG_NOISE = {"blog", "area", "calc", "index", "page", "home", "about", "contact",
               "services", "service", "areas", "post", "news", "category",
               # Short words that appear in money-page slugs and name nothing the
               # client sells. Needed because the length floor below is 2, not 4:
               # a floor of 4 silently dropped "erp" - Cudio's entire business -
               # along with "ac", "iv", "ev", "gas", "air", "lot" and "saw".
               "our", "all", "one", "add", "ons", "pro", "up", "we"}


def _service_terms(cfg, money):
    """The words this client's own money pages use to name what they sell.

    Business value must be reasoned from the client's business, not from a
    generic buy-intent word list. "How often should you seal coat your driveway"
    scored Low on a keyword list while sealcoating is the client's core service.
    """
    terms = set()
    for u in money:
        slug = u.rstrip("/").rsplit("/", 1)[-1]
        for w in re.split(r"[-_]", slug):
            w = w.lower()
            if len(w) > 1 and w not in STOP and w not in _SLUG_NOISE:
                terms.add(w)
    for path in (cfg.get("crawl") or {}).get("money", []):
        for w in re.split(r"[-_/]", str(path)):
            w = w.lower()
            if len(w) > 1 and w not in STOP and w not in _SLUG_NOISE:
                terms.add(w)
    return terms


def _service_rel(text, terms):
    """True when the text names something this client sells."""
    for w in _terms(text, floor=2):
        if w in terms:
            return True
        if len(w) >= 5 and any(t.startswith(w[:5]) or w.startswith(t[:5])
                               for t in terms if len(t) >= 5):
            return True
    return False




def _excluded(url, cfg):
    """Paths this client handles outside 1.5, so they never become candidates."""
    pats = (cfg.get("crawl") or {}).get("candidate_exclude") or []
    u = url.lower()
    # A pattern ending in "$" names ONE address exactly, which is the only way to exclude a homepage:
    # its path is empty, so a substring would match every URL on the site.
    return any((u.rstrip("/") == str(x).lower()[:-1].rstrip("/")) if str(x).endswith("$")
               else str(x).lower() in u for x in pats)


def _brand_keys(cfg):
    """Brand spellings reduced to letters and digits, so "barts asphalt" matches "bart's asphalt"."""
    raw = cfg.get("brand_token") or []
    raw = [raw] if isinstance(raw, str) else list(raw)
    return {k for k in (re.sub(r"[^a-z0-9]", "", str(b).lower()) for b in raw) if k}


def _is_brand(query, brands):
    """A branded query is not a target. Its position says nothing about a page's wording, and a login
    or brand search is navigational, so no title or body change moves it."""
    squashed = re.sub(r"[^a-z0-9]", "", query.lower())
    return any(b in squashed for b in brands)



# Lowered from 0.20 on 2026-09-03. A fifth of the site on one date was too
# blunt: it missed SameDay's 56-URL day (18.1%), Superior's 44, Comfort's 38 and
# Beehive's 70, all obviously releases - no home-services team edits 40 pages in
# an afternoon. Paired with DEPLOY_MIN it cannot fire on a small site's normal
# editing. Bart's and Snow flag nothing new at 10%, which is the control.
DEPLOY_SHARE = 0.10        # one date carrying a tenth of the site is a release
DEPLOY_MIN = 10
DEPLOY_WINDOW_DAYS = 14
DEPLOY_WINDOW_SHARE = 0.60


def _deploy_dates(lastmod):
    """Dates where the whole site moved at once, which is a release, not editing.

    A content refresh touches a handful of pages; a deploy or migration rewrites
    every lastmod on the site. Arsenal shipped its rendering fix and 92% of its
    110 URLs took a date inside ten days, which made every candidate look
    freshly refreshed and emptied its tab. Bart's, editing page by page, peaks
    at 6% on any one date and is unaffected.
    """
    from collections import Counter
    if not lastmod:
        return set()
    counts = Counter(lastmod.values())
    n = len(lastmod)
    out = {d for d, k in counts.items()
           if k >= DEPLOY_MIN and k >= n * DEPLOY_SHARE}
    # A staged rollout spreads over days without any single date dominating.
    for anchor in sorted(counts):
        span = [d for d in counts
                if 0 <= (d - anchor).days < DEPLOY_WINDOW_DAYS]
        if sum(counts[d] for d in span) >= n * DEPLOY_WINDOW_SHARE and len(span) > 1:
            out |= set(span)
    return out


def _worked_recently(cfg):
    """URLs already offered or worked in a recent month's workbook.

    Owner rule 2026-09-03: a page we worked on is off the candidate list.
    Re-selecting it the month after it shipped spends the budget twice and
    reads as if the work never happened. The window was 90 days; the owner made
    it six workbook months on 2026-10-06.

    The 1.5 Candidate List itself is a source, not just 1.8 and the refresh log.
    Owner restated 2026-09-03: "no URLs listed in the candidate list in the 1.5
    task were also selected as candidate during August." Reading only the tabs
    that record work missed every page that was OFFERED last month and never
    picked up, which let 7 URLs repeat across 5 clients.
    """
    # The most recent LOOKBACK_WORKBOOKS workbooks, newest first, in either tab layout.
    # prior_work anchors on headings; the fixed ranges this replaced read the
    # wrong column the day a merged-2.3 workbook became the prior one.
    urls = set(PW.recent_urls(cfg, LOOKBACK_WORKBOOKS))
    # Every tab that names pages for a task, not only the three PW reads (owner, 2026-10-06): a page
    # that only had a fix or new internal links was taken into account too.
    urls |= {"https://" + k for k in WU.prior_worked(cfg, LOOKBACK_WORKBOOKS)}
    resolved = _with_destinations(urls)
    return resolved | {WU.key(u) for u in resolved}


def _is_worked(url, worked):
    return url.rstrip("/") in worked or WU.key(url) in worked


_LANDING_FILE = Path(__file__).resolve().parent.parent / ".cache" / "landings.json"
_LANDING_TTL = 12 * 3600
_SECOND_PASS_WAIT = 45   # seconds before the slow second pass over throttled URLs


def _resolve(url):
    """{'status', 'final'} for a URL, cached on disk for twelve hours.

    One 1.5 run resolves a few hundred recorded URLs, and the filler, the verifier and the repeat checker
    each need the same answers. Fetching them four times, one at a time behind retry pauses, was most of the
    run time. Only settled answers are stored: a 429, 5xx or no response is retried next time, never kept.
    """
    import json
    import time as _t
    try:
        cache = json.loads(_LANDING_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    hit = cache.get(url)
    if hit and _t.time() - hit["at"] < _LANDING_TTL:
        return {"status": hit["status"], "final": hit["final"]}
    page = _onpage(url)
    if page is not None and page.get("status") in (200, 404, 410):
        cache[url] = {"status": page["status"], "final": page.get("final") or url, "at": _t.time()}
        try:
            _LANDING_FILE.parent.mkdir(exist_ok=True)
            _LANDING_FILE.write_text(json.dumps(cache), encoding="utf-8")
        except OSError:
            pass
    return page


def _with_destinations(urls):
    """The recorded URLs plus every address they now redirect to.

    A workbook records the URL as it stood that month. SameDay moved its whole
    site tree after September: /plumbing/drain-cleaning/ became
    /plumbing/sewer-and-drains/drain-cleaning/, and /emergency-services/air-conditioner-repair/
    became /cooling/air-conditioning-repair/. Comparing strings let both come back
    as fresh candidates a month after they were worked. A page that is gone (404 or
    410) has no destination and adds nothing. A URL the check could not read is
    raised, never skipped, because that is how the gate stops working unnoticed.
    """
    pages = list(urls)
    results = [_resolve(u) for u in pages]   # one at a time: parallel fetches trip the sites' rate limits
    # A site that is still throttling after the per-URL retries gets one slower second pass over just the
    # unread URLs before the gate gives up (Superior's /service-areas/kearns-utah answered 429 for a whole
    # run, then 200 a minute later).
    import time as _t
    stuck = [i for i, r in enumerate(results)
             if r is None or ((r.get("status") or 200) not in (200, 404, 410))]
    if stuck:
        _t.sleep(_SECOND_PASS_WAIT)
        for i in stuck:
            results[i] = _resolve(pages[i])
    out, unread = set(urls), []
    for url, page in zip(pages, results):
        status = (page or {}).get("status")
        if page is None or (status and status not in (200, 404, 410)):
            unread.append(f"{url} ({'no response' if page is None else 'HTTP ' + str(status)})")
        elif status == 200:
            out.add(PW.canon((page.get("final") or url).split("?")[0]))
    if unread:
        raise GateUnavailable(
            f"work-history gate: {len(unread)} previously worked URL(s) could not be resolved to "
            "where they land now: " + "; ".join(unread[:4]))
    return out


def _usable_query(q):
    """A target has to be a query someone types, not a sentence GSC returned.

    EW surfaced 'she also displayed learner-centred guidance by using open-e...'
    as a target because a long sentence always contains a word the title lacks,
    so the gap gate rated it highly. Nobody can optimize for that.
    """
    q = q.strip().strip('"').strip()
    return bool(q) and not q.startswith("(") and 0 < len(q.split()) <= 8



class GateUnavailable(RuntimeError):
    """A gate's input is missing, so the tab must not be written.

    Owner rule 2026-09-03: a gate that cannot run must stop the task, not skip
    itself. EW's sitemap 403s this network, so the recency gate silently had no
    data and the client got a candidate list containing pages we had just
    finished optimizing. Reporting that afterwards is too late; the row was
    already on a client tab.
    """


def preflight(cfg, lastmod, worked):
    """Every gate must have its input before any candidate is written."""
    missing = []
    if not lastmod:
        missing.append("recency gate: no sitemap lastmod reachable for this client")
    if not any(k.startswith("sheet_id_") and cfg.get(k) for k in cfg):
        # A first month has no history and that is correct, not a gap. 1.5's own
        # section A says as much. Blocking Barts on it was wrong.
        pass
    elif not worked:
        missing.append("work-history gate: prior workbook readable but lists no "
                       "optimized pages, which is unexpected after a completed month")
    return missing


def build(slug, cfg, svc, notes):
    site = cfg["gsc_property"]
    B = site.rstrip("/")
    res = analyse(svc, site, cfg)

    curve_txt = ctr_curve_text(res["sd"])

    import task_1_5 as _T
    money_set, _posts, _scope = _T.scope(cfg)
    lastmod = _lastmod(cfg)
    deploys = _deploy_dates(lastmod)
    worked = _worked_recently(cfg)
    today = dt.date.today()
    dropped = []
    if deploys:
        recent = sorted(d for d in deploys if (today - d).days < RECENT_DAYS)
        if recent:
            dropped.append(("(site-wide)", "release detected on " +
                            ", ".join(str(d) for d in recent[:4]) +
                            " - those dates are not treated as content refreshes"))
    gaps = preflight(cfg, lastmod, worked)
    if gaps:
        raise GateUnavailable("; ".join(gaps))
    pool = []
    for d in res["decay"]:
        if d["value"] == "Other":
            continue
        # A page refreshed inside the window is being compared against its own
        # pre-refresh self, which is not decay. Worse, a refresh MOVES the
        # metrics, so without this gate the detector preferentially surfaces the
        # pages we just rewrote. Barts: all six candidates were rewritten on 18
        # or 24 June, inside the Jun-Aug window.
        if _excluded(d["url"], cfg):
            dropped.append((d["url"], "excluded for this client (candidate_exclude)"))
            continue
        if _is_worked(d["url"], worked):
            dropped.append((d["url"], "already offered or worked in a recent workbook"))
            continue
        lm = lastmod.get(d["url"].rstrip("/"))
        if lm and lm not in deploys and (today - lm).days < RECENT_DAYS:
            dropped.append((d["url"], f"refreshed {(today - lm).days}d ago"))
            continue
        ok, why = _resolves_clean(d["url"], _onpage(d["url"]))
        if not ok:
            dropped.append((d["url"], why))
            continue
        kind, ev = cause(d)
        pool.append({"url": d["url"], "src": "Decay", "q": "(page-level decay)",
                     "pos": d["pos"], "impr": d["impr"], "value": d["value"],
                     "opp": d["before"] - d["after"], "kind": kind, "ev": ev,
                     "buy": commercial(d["url"])})
    # Choose each page's target query from the ones it does NOT already say,
    # highest impressions first. Taking the biggest query outright picked
    # "driveway sealcoating" for a guide that says sealcoating 68 times, which
    # is a row with nothing to do. A page whose every ranking query is already
    # covered is not a candidate at all.
    by_url, skips = {}, {}
    for d in res["sd"]:
        if d["value"] == "Other":
            continue
        # Every exclusion is recorded. A silently skipped candidate is
        # indistinguishable from one that was never found.
        if _excluded(d["url"], cfg):
            skips[d["url"]] = "excluded for this client (candidate_exclude)"
            continue
        if _is_worked(d["url"], worked):
            skips[d["url"]] = "already offered or worked in a recent workbook"
            continue
        lm = lastmod.get(d["url"].rstrip("/"))
        if lm and lm not in deploys and (today - lm).days < RECRAWL_DAYS:
            skips[d["url"]] = (f"edited {(today - lm).days}d ago, inside the "
                               "recrawl window")
            continue
        by_url.setdefault(d["url"], []).append(d)
    dropped.extend(sorted(skips.items()))
    best = {}
    brands = _brand_keys(cfg)
    for k, ds in by_url.items():
        page = _onpage(k)
        ok, why = _resolves_clean(k, page)
        if not ok:
            skips[k] = why
            continue
        hay = page["hay"] if page else None
        topic = page["topic"] if page else ""
        # Rank the page's own ranking queries by how well each matches what the
        # page is about, then by size. Taking the biggest query outright gave a
        # Michigan sealcoating COST guide the target "driveway sealcoating",
        # a service query the page is not written to answer.
        unbranded = [d for d in ds if not _is_brand(d["query"], brands)]
        elig = [d for d in unbranded
                if " near me" not in (" " + d["query"])
                and _usable_query(d["query"])
                and _has_gap(d["query"], hay)]
        if not elig:
            top = max(ds, key=lambda x: x["impr"])
            dropped.append((k, f'only branded queries (largest: "{top["query"]}")' if not unbranded else
                            f'no gap on any of its {len(unbranded)} ranking queries '
                            f'(largest: "{max(unbranded, key=lambda x: x["impr"])["query"]}")'))
            continue
        elig.sort(key=lambda d: (-_topic_fit(d["query"], topic), -d["impr"]))
        best[k] = elig[0]
    for d in best.values():
        pool.append({"url": d["url"], "src": "Striking Distance", "q": d["query"],
                     "pos": d["pos"], "impr": d["impr"], "value": d["value"],
                     "opp": d["impr"] * 0.04, "kind": "STRIKING DISTANCE",
                     "ev": f"position {d['pos']:.1f} on {d['impr']:,} impressions "
                           f"for \"{d['query']}\", {d['clicks']} clicks",
                     "buy": commercial(d["query"])})

    # Business value: who the page reaches and whether the query is someone
    # ready to buy. A money page on a commercial query is the top of this scale
    # on every one of these clients.
    # A MONEY PAGE IS HIGH, full stop. The client designated it as a page that
    # sells; that settles its business value and no keyword test improves on it.
    # A keyword heuristic graded Snow's product pages Medium because "purple
    # teeth whitening strips" contains no word from a buy-intent list, when
    # someone searching a product by name is as close to buying as it gets.
    # Only POSTS need an intent judgement, because a post can serve a buyer
    # (cost, comparison, "near me") or a DIY reader who will never convert.
    # Two independent questions, not one. Service relevance asks whether the
    # query is about something this client sells; purchase proximity asks how
    # close the searcher is to buying. Grading on proximity alone buried core
    # service content: sealcoating frequency is maximum relevance for a
    # sealcoating contractor and scored Low. Owner rule, 2026-09-03.
    svc_terms = _service_terms(cfg, money_set)
    for r in pool:
        if r["value"] == "Money page":
            r["bv"] = "High"
        else:
            # A decay row has no target query, so relevance is judged on the page.
            subject = r["url"] if r["q"].startswith("(") else r["q"]
            svc, buy = _service_rel(subject, svc_terms), r["buy"]
            r["bv"] = "High" if (svc and buy) else ("Medium" if (svc or buy) else "Low")
        r["score"] = r["opp"] * {"High": 4.0, "Medium": 1.5, "Low": 0.4}[r["bv"]]

    # Rank by value band first, so a Low/N row can never head the list. Beehive
    # and Cudio both put a Low informational post at rank 1 on raw impressions.
    order = {"High": 0, "Medium": 1, "Low": 2}
    pool.sort(key=lambda r: (order[r["bv"]], -r["score"]))
    seen, rows = set(), []
    for r in pool:
        if r["url"] in seen:
            continue
        seen.add(r["url"])
        # Owner rule: a page only enters the list if it ranks for something its
        # own title and meta do not already say. Barts' sealcoating guide sat at
        # position 6.5 for "driveway sealcoating" while saying "sealcoating" 68
        # times, so there was nothing to add and the row was work for its own sake.
        if r["src"] == "Striking Distance" and not _has_gap(r["q"], _onpage(r["url"])):
            dropped.append((r["url"], f'no gap: title/meta/H1 already cover "{r["q"]}"'))
            continue
        rows.append(r)
        if len(rows) >= 10:
            break

    def _override(url):
        """A note is a string (appended) or a dict of per-row judgments.

        Dict keys: action (replaces the templated action phrase), note (appended
        after the evidence), intent (replaces the templated intent sentence, "" to
        drop it). The templates answer for a typical row; a row whose own data
        contradicts the template says so here, in writing, instead of shipping it.
        """
        n = notes.get(url.replace(B, ""), "")
        return n if isinstance(n, dict) else {"note": n}

    body = []
    for i, r in enumerate(rows, 1):
        ov = _override(r["url"])
        act = ov.get("action") or ("close the gap to top 5" if r["kind"] == "STRIKING DISTANCE"
                                   else ACTION[r["kind"]])
        intent = ov["intent"] if "intent" in ov else (
            "Commercial-intent query, so the searcher is close to buying." if r["buy"] else
            "Informational intent: useful for reach, further from revenue.")
        why = S.compose(("Action", [act[0].upper() + act[1:] + "."]),
                        ("Evidence", [f"{r['kind']}: {r['ev']}."]),
                        ("Why this row", ov.get("note", "")),
                        ("Intent", intent),
                        where=r["url"])
        body.append([i, r["url"], r["src"], r["q"], round(r["pos"], 1),
                     int(r["impr"]), why, r["bv"],
                     "Y" if r["bv"] in ("High", "Medium") else "N"])

    p = S.find_rows(cfg["sheet_id"], TAB, {"a": "Keyword", "b": "Rank"})
    n = 0
    # The baseline note belongs to a client's FIRST workbook only. From the second
    # month Section A is written by fill_1_5_section_a.py from last month's record
    # of work, so writing a baseline here would put "nothing to measure" over it.
    if not any(k.startswith("sheet_id_") and cfg.get(k) for k in cfg):
        worked_month = res["periods"][0][1].strftime("%B")
        curve_month = res["month"][0].strftime("%B %Y")
        n = S.write(cfg["sheet_id"], f"'{TAB}'!A{p['a']+1}:G{p['a']+1}", [[
            "BASELINE MONTH - nothing to measure yet", "", "", "", "", "",
            S.compose(
                ("Nothing to measure yet", f"First run of the workbook, so there is no recorded set of "
                 f"{worked_month} optimizations to compare against. Fills from next month using whatever "
                 "1.8 selects. Do not back-fill from ranking history: a position change with no record "
                 "of a change made is not a before/after."),
                ("Client CTR curve", [f"{curve_month}: {curve_txt}.",
                                      "Judge any CTR claim against this, not a generic curve."]))]]).cells
    else:
        print(f"{slug:<22} section A left to fill_1_5_section_a.py (a prior workbook exists)")
    # Clear the whole candidate block first. A shorter list than last run would
    # otherwise leave the old rows standing underneath, and Barts ended up with
    # the same URL twice carrying two different target queries.
    S.clear(cfg["sheet_id"], f"'{TAB}'!A{p['b']+1}:I{p['b']+30}")
    n += S.write(cfg["sheet_id"], f"'{TAB}'!A{p['b']+1}:I{p['b']+len(body)}", body).cells
    ys = sum(1 for b in body if b[8] == "Y")
    print(f"{slug:<22} rows {len(body):>2}  Y {ys}  N {len(body)-ys}  cells {n}"
          f"  gated {len(dropped)}")
    import os as _os
    _cap = int(_os.environ.get("GATE_LOG", "12"))
    # Console only - the sheet always carries the full URL. Stripping the site
    # root leaves the homepage as an empty string, which reads as a bug.
    def _short(u):
        return u.replace(B, "") or "/"

    for u, why in dropped[:_cap]:
        print(f"     GATED {_short(u):<58} {why}")
    for b in body[:4]:
        print(f"     {b[0]} {b[7]:<7}{b[8]} {b[2]:<18}{_short(b[1])[:40]:<40} "
              f"pos {b[4]:<5} {b[5]:>8,}")
    return len(body)


NOTES = {
 "barts": {
    "/blog/asphalt-resurfacing-costs": {
        "action": "snippet work, then re-read next month (add 'parking lot' to the title and H1)",
        "note": "The page is new: first impressions came in August (42) and September had 441 "
                "impressions and 1 click, so its position has not settled and this is an early "
                "reading. The title and H1 say 'asphalt resurfacing cost' and never 'parking lot', "
                "the wording of its biggest query."},
    "/industries-we-serve/manufacturing-asphalt-solutions": {
        "action": "close the gap to top 5 by naming 'industrial asphalt' in the title and H1",
        "note": "Small prize: the page has not earned a click in the eleven months of history and its "
                "best month was 146 impressions. Its title says 'Michigan Manufacturing Facilities', not the "
                "query's 'industrial asphalt solutions'.",
        "intent": "Money page: an industry page the client designated as selling, so it grades High "
                  "whatever the query size."},
    "/blog/parking-lot-maintenance-checklist": {
        "note": "Last year cannot be compared: the page has no 2025 impressions (history starts "
                "December 2025). Its core queries lost ground between Apr-Jun and Jul-Sep: 'parking "
                "lot maintenance checklist' 5.8 to 14.4, 'parking lot maintenance plan' 8.6 to 18.7, "
                "'asphalt parking lot maintenance guidelines' 9.8 to 29.6. The page average of 32.7 "
                "is also pulled down by a head term it now surfaces for ('parking lot maintenance', "
                "3,239 impressions at position 43.2), so judge it on the core queries."},
    "/blog/ada-and-line-striping-essentials": {
        "action": "protect what works: add internal links only, no title or body rewrite",
        "note": "The page is mid-climb: average position 56.3 in July, 30.7 in August, 11.3 in "
                "September, with clicks 1, 17, 22. The target query is small; the real volume is "
                "'ada handicap parking painting' (955 impressions in September at position 14.8), and "
                "the title already carries it, so there is no snippet gap to close. Re-read in a month."},
    "/blog/how-much-does-asphalt-paving-cost": {
        "action": "protect what works: add a driveway section without touching the title",
        "note": "Already performing: 99 clicks on 13,857 impressions at position 7.7 "
                "in Jul-Sep (4 clicks in Apr-Jun), 37 clicks at position 6.0 in September. 'Asphalt "
                "driveway' is a head term off the page's cost subject, so treat this as a small "
                "extension, not a rewrite.",
        "intent": "The target query is informational, but the page's own demand is cost, pricing and "
                  "quote queries ('asphalt paving pricing' 138 impressions, 'asphalt paving quote' 74 "
                  "in Jul-Sep), which sit close to buying."},
 },
 "superior": {
    "/service-areas/provo-utah": {
        "action": "name one owner for 'water heater replacement in provo ut' and link to it from this page, with no title change",
        "note": "Three URLs touch the query: this city page (269 impressions, position 15.3), "
                "/water/water-heater-replacement-services-in-provo/ (165, position 18.1), which Google "
                "treats as an alternate of /service-areas/provo-utah/water-heater-replacement/, and that "
                "indexed page itself, which holds only 22 impressions. The city title is the service "
                "range and stays."},
    "/water/office-drinking-water": {
        "action": "snippet work: name 'office water cooler service' in the title and keep the H1",
        "note": "Neither the title nor the meta says 'water cooler' (title: 'Office Drinking Water "
                "Services'), and the body never does. The page holds 559 impressions on 'office water "
                "cooler service' at position 19.5 and 396 on the plural at 28.2, and it is the only page "
                "ranking for either. Same window last year: 18 clicks on 7,119 impressions; this year 4 "
                "on 5,444."},
    "/service-areas/ogden-utah": {
        "action": "add 'water heater repair' to the meta description and keep the range title",
        "note": "This city page is the page ranking for the query (449 impressions at 11.4 in Jul-Sep). "
                "Its meta opens with weather copy and never names the service. "
                "/service-areas/ogden-utah/water-heater-replacement/ also surfaces for it, at 6.4 on 69 "
                "impressions, so link the two with 'water heater repair Ogden' as the anchor."},
    "/service-areas/orem-utah/furnace-repair": {
        "action": "protect what works: leave the title, and put 'heater repair' in the meta only",
        "note": "The page is new (first impressions August 2026), so there is no last-year comparison, "
                "and September's 1,449 impressions include the start of heating season. The title "
                "already says 'Furnace Repair Services Orem'; 'orem heater repair services' is a second "
                "phrasing of the same service, held at 7.2 on 128 impressions. The larger prize is "
                "'furnace repair orem' (347 impressions, position 11.3), which the title already "
                "carries, so the lever there is internal links."},
    "/service-areas/orem-utah": {
        "action": "link only: leave the title and body, and point to the Orem water heater replacement page",
        "note": "This city page is the only page ranking for 'water heater replacement orem ut' (275 "
                "impressions, position 11.0) because /service-areas/orem-utah/water-heater-replacement/ "
                "is discovered but not indexed. Replacement wording added here moves work off the page "
                "that should own it; getting that page crawled and linked from here is the lever."},
    "/service-areas/kaysville-utah": {
        "action": "add a short 'HVAC repair in Kaysville' line to the HVAC section and the meta, and keep the range title",
        "note": "The body says 'repair' 26 times but never 'hvac repair'. The query sits at 15.0 on 147 "
                "impressions and its twin 'hvac repair services kaysville, ut' at 15.9 on 122, so one "
                "line serves both. The page's clicks went 3 to 6 against Apr-Jun."},
    "/service-areas/clinton-utah": {
        "action": "add 'water heater repair' to the meta and keep the range title, then re-read next month",
        "note": "Small prize: 268 impressions in Jul-Sep at position 30.8, and no month of the last eleven "
                "has had more than 1 click. In September alone the query sat at 15.6 on 59 impressions, "
                "so it is moving up. The body already says 'water heater repair' 3 times."},
    "/service-areas/south-jordan-utah": {
        "action": "protect what works: no title or meta change, add internal links only",
        "note": "The query is already at position 4.2 (169 impressions in Jul-Sep), so there is no "
                "ranking gap, and its 0 clicks match this client's own curve (0.16% at positions 4-5), "
                "so the snippet is not the problem. The page is climbing: clicks 2 to 12 against "
                "Apr-Jun, average position 31.2 to 25.4. 'plumber south jordan' (323 impressions at "
                "15.9) is the larger prize."},
    "/service-areas/provo-utah/water-heater-repair": {
        "action": "protect what works: no change for 'tankless', re-read in a month",
        "note": "The page is new (first impressions August 2026). 'tankless water heater provo' is an "
                "install query on a repair page, so it stays out of the title; the page already says "
                "'tankless' 12 times. Its own repair queries are near the top: 'provo water heater "
                "repair' 4.7 and 'water heater repair provo' 8.9.",
        "intent": ""},
    "/does-utah-have-hard-water": {
        "action": "refresh the opening so 'what is water hardness' is answered in the first lines",
        "note": "The page lost most of its impressions in one step: 621 in March, 220 in April, then 102 "
                "to 176 a month since May. Same window last year: 1,730 impressions and 2 clicks; this "
                "year 464 and none. The target holds position 8.1 on 52 impressions. The page says 'what "
                "is water hardness' 0 times and 'what is hard water' once."},
 },
 "sameday": {
    "/emergency-services": {
        "action": "add 'emergency HVAC repair' to the meta and one H2, and keep the range title",
        "note": "This is the emergency hub, so its title stays the HVAC-and-plumbing range, and the body "
                "never says 'hvac repair'. The query sits at 16.8 on 569 impressions in Jul-Sep and its "
                "twin 'hvac emergency repair' at 9.8 on 671. The page already has an 'Emergency Heating "
                "Services' section, yet 'emergency heating repair' (2,041 impressions) sits at 58.6. "
                "Same window last year: 13,879 impressions and 0 clicks; this year 19,277 and 4."},
    "/service-areas/lehi-ut": {
        "action": "add a 'furnace repair in Lehi' line to the Heating section and the meta, and keep the range title",
        "note": "The page is new (first impressions July 2026: 304 in July, 89 in August, 4,553 in "
                "September), so its position has not settled and this is an early reading. The body says "
                "'furnace repair' once. The query holds 19.6 on 64 impressions here, while the older "
                "/service-area/lehi-ut/heating/ URL still collects 122 impressions on 'furnace repair "
                "lehi' at 46.3."},
 },
 "beehive": {
    "/reverse-osmosis-systems-utah": {
        "action": "expand the body with an installation and maintenance section that names Utah County, and keep the title",
        "note": "The page is thin (about 408 words) and says 'installation' once and 'utah county' and "
                "'maintenance' never, yet it holds 216 impressions at 16.1 on 'ro system installation "
                "utah county' (the only page ranking for it) and 154 at 31.3 on 'ro system maintenance "
                "salt lake'. Same window last year: 4 clicks on 3,634 impressions; this year 0 on 847."},
    "/our-locations/murray": {
        "action": "put 'licensed plumber in Murray' in the meta and keep the range title",
        "note": "The page is new (first impressions May 2026; 640 in July, 1,597 in August, 1,572 in "
                "September), so this is an early reading. It says 'licensed' 6 times but neither the "
                "title nor the meta does. Its larger queries are service ones: 'water heater replacement "
                "in murray ut' (151 impressions at 17.4) and 'sewer line repair in murray ut' (121 at 28.3)."},
    "/what-are-the-different-types-of-urinals": {
        "action": "protect what works: no title or body change, because the gap is clicks and not rank",
        "note": "'urinal toilet' sits at position 2.9 on 3,573 impressions in Jul-Sep and earned 2 clicks "
                "(0.06%), already inside the top 5. The title and meta describe 'types of urinals', not a "
                "urinal toilet. 'types of urinals' (615 impressions at 10.8) is the query the page is "
                "built for."},
    "/6-diy-methods-to-unclog-drains": {
        "action": "protect what works: no rewrite, add a link to the drain cleaning page and re-read next month",
        "note": "Impressions went from 351 in August to 9,734 in September (position 33.1 to 8.8), so the "
                "position has not settled and clicks lag it: 0 clicks on 8,959 impressions for 'how to "
                "unclog a drain' at 7.8. The target is a small variant of that query (202 impressions at "
                "7.4), and the title already matches it."},
    "/trenchless-pipe-lining-101-what-you-need-to-know": {
        "action": "link only: point to the pipe lining service page, with no rewrite for 'plumbing liner'",
        "note": "'plumbing liner' (364 impressions at 10.9) is a synonym the page never says, and 'pipe "
                "liner' (665 at 5.3) already ranks. Same window last year: 13 clicks on 50,919 "
                "impressions; this year 1 on 18,910. Its largest query, 'pipe lining' (3,144 impressions "
                "at 19.0), is also won by /what-is-a-pipe-lining/ (3,033 at 19.5)."},
    "/comparing-traditional-tankless-water-heaters": {
        "action": "link only: point to /tankless-water-heaters-utah/ with 'tankless water heaters Utah' as the anchor, and leave this page's wording",
        "note": "This comparison post ranks 11.2 for 'tankless water heaters utah' (64 impressions) while "
                "the service page /tankless-water-heaters-utah/ ranks 26.3 for it on 785. A comparison "
                "post should not own a service query; the link sends the demand to the page that sells. "
                "The post is new to the query: 3 impressions in July, 204 in September.",
        "intent": ""},
    "/shower-not-turning-on": {
        "action": "protect what works: no rewrite, add internal links to the matching service page only",
        "note": "Already earning: 247 clicks on 28,371 impressions in Jul-Sep (176 clicks in Apr-Jun) at "
                "an average position of 13.0. The target is a small variant at 6.0 (194 impressions, 3 "
                "clicks) of queries the page already wins. The larger gaps are 'shower not working' (410 "
                "impressions at 27.6) and 'no water in shower' (310 at 29.7)."},
    "/what-is-a-pipe-lining": {
        "action": "add a short sewer-line section that names 'sanitary sewer pipe lining'",
        "note": "The body never says 'sewer' or 'sanitary' while this query sits at 18.0 on 65 "
                "impressions. Small prize, but the page is recovering: 629 impressions in July, 2,162 in "
                "August, 2,854 in September (position 42.1 to 23.0). Its largest query, 'pipe lining' "
                "(3,033 impressions at 19.5), is shared with /trenchless-pipe-lining-101-what-you-need-to-know/."},
    "/everything-you-need-to-know-about-bathroom-repair": {
        "action": "leave as is: 'bathroom fix' is a synonym of a query the title already carries",
        "note": "The title says 'Bathroom Repair' and the page ranks for 'bathroom plumbing repair' (5,174 "
                "impressions at 18.6) and 'bathroom repair' (4,438 at 26.1); 'bathroom fix' (364 at 6.3) "
                "adds nothing the title lacks. Not selected. Impressions climbed from 2,609 in April to "
                "5,038 in September, position 28.7 to 17.0."},
 },
 "comfort": {
    "/services/plumbing/drain-cleaning": {
        "action": "protect what works: no title or body change, and re-read next month",
        "note": "The page came back from almost nothing: 10 impressions in August, 375 in September "
                "(position 46.8 to 7.9), so the position has not settled. It already ranks 3.5 to 6.7 on "
                "four Utah drain cleaning queries (0 clicks on 271 impressions, in line with this client's "
                "own curve of 0.45% at positions 4-5). The weaker queries are local: 'drain cleaning ogden "
                "ut' at 14.2 and 'drain cleaning salt lake city' at 21.8."},
 },
 "educationwalkthrough": {
    "/what-are-the-iste-standards-how-do-they-impact-education": {
        "action": "add a 2025-2026 updates section and name it in the meta, and keep the title",
        "note": "The page is surging (780 impressions in Apr-Jun, 3,907 in Jul-Sep; position 40.6 to 14.2), "
                "so this is an early reading. The query holds 1,899 impressions at 9.7 with 0 clicks, and "
                "this is the only page ranking for it. The body says '2026' once and never '2025' or "
                "'updates'."},
    "/top-10-must-listen-podcasts-for-principals-transform-your-leadership-today": {
        "action": "refresh the list of ten with current episodes and the year, and keep the title",
        "note": "Query by query: 'principal podcasts' went 3.5 to 8.1 and 'educational leadership "
                "podcast' 13.8 to 37.4. Clicks were 54 in June, then 11, 3 and 3. The title, meta and "
                "body name no year. Same window last year: 246 clicks on 6,635 impressions."},
    "/navigating-the-evaluation-landscape-a-state-by-state-guide-to-teacher-evaluation-systems-in-the-us": {
        "action": "refresh the state sections and link the Ohio and New York sections to their own pages",
        "note": "The state queries hold ('teacher effectiveness alabama' sits at 8.3) while the generic ones "
                "slid: 'teacher evaluation systems' 24.4 to 35.9 and 'teacher evaluation models' 26.1 to "
                "48.3. Clicks were 27 in April, then 14, 15, 9, 8 and 12 in September. Same window last "
                "year: 246 clicks on 16,648 impressions. Separate pages exist for Ohio (OTES 2.0) and "
                "New York (APPR)."},
    "/instructional-coach-interview-questions": {
        "action": "refresh the answers and add an 'academic coach' section, and keep the title",
        "note": "Not seasonal: the same window last year had 402 clicks on 12,532 impressions, and the "
                "step down came in April (1,730 impressions in March, 669 in April). Its largest "
                "queries barely moved ('instructional coach interview questions' 318 to 278 impressions). "
                "'academic coach interview questions' has 248 impressions at 8.4 and 0 clicks, and the "
                "title says 'Instructional Coach'."},
    "/understanding-the-role-of-modeling-in-education": {
        "action": "no title or meta change: leave the page and re-read next month",
        "note": "Its CTR is 0.37% (25 clicks on 6,731 impressions) against this client's own 0.30% at "
                "positions 14-15, so the snippet is not underperforming. Position is flat; the loss is "
                "year over year (236 clicks on 24,784 impressions). New queries about model students and "
                "model schools ('model student meaning' 139 impressions at 10.5, 'model school "
                "definition' 132 at 21.7) are a different subject from the page's."},
    "/a-complete-guide-to-classroom-observation-frameworks": {
        "action": "add depth on each framework the guide names, and link to each framework's own page",
        "note": "The head queries slipped: 'observation framework' 4.7 to 32.0 and 'classroom "
                "observations' 49.5 to 71.6. September is already better (7 clicks at position 10.6 "
                "against 4 at 23.0 in August). The guide runs about 1,500 words, and the site has "
                "separate pages on Danielson, Marzano and T-TESS."},
    "/classroom-observation": {
        "action": "protect what works: no rewrite and no Spanish copy, add internal links only",
        "note": "The target is a Spanish query ('tipos de observación educativa', 100 impressions at 5.9, "
                "6 clicks) on an English page. The page is already earning: 105 clicks on 8,149 "
                "impressions in Jul-Sep (26 in Apr-Jun), and its English head query 'classroom "
                "observation' sits at 28.4 on 185 impressions. Its other leading queries are Spanish and "
                "Hindi."},
    "/otes-2-0-a-guide-to-the-upgraded-ohio-evaluation-system": {
        "action": "insert 'Teacher' in the title so it reads 'Ohio Teacher Evaluation System'",
        "note": "The page is surging (302 impressions in July, 6,661 in September; 52 clicks in "
                "September), so this is an early reading. 'ohio teacher evaluation system' holds 393 "
                "impressions at 13.5 and the title says 'Ohio Evaluation System'. 'otes 2.0' (2,826 "
                "impressions at 9.4) already matches the title. Not selected."},
    "/california-cstp-framework-for-teaching": {
        "action": "protect what works: no change",
        "note": "The largest page in this list: 1,084 clicks on 34,911 impressions in Jul-Sep (158 in "
                "Apr-Jun) at an average position of 6.6, and 'cstp standards 2026' earns 261 clicks at "
                "2.6. The target is the long form of 'cstp' (749 impressions at 9.5, 20 clicks), which "
                "the title does not spell out. Not selected."},
    "/how-the-ohio-teacher-evaluation-system-otes-helps-teachers-ensure-high-quality-instruction": {
        "action": "add an 'OTES self-assessment' section and keep the title",
        "note": "The query holds 153 impressions at 6.4 with 1 click, and the body runs about 894 words. "
                "The page's head query 'otes' (10,072 impressions at 7.4) earned 2 clicks. Not selected."},
 },
 "arsenal": {"/locations/dtc": "Physical location page, drives foot traffic.",
             "/peptide-therapy-2": "Duplicate of /peptide-therapy: resolve "
                                   "cannibalization before optimising either."},
 "cudio": {
    "/blog/best-odoo-development-companies": {
        "action": "add 'Odoo application development' to the 'What Odoo Development Actually Includes' section and keep the title",
        "note": "The page is new (first impressions August 2026: 596 in August, 1,641 in September), so "
                "this is an early reading, and it is already earning: 18 clicks on 2,237 impressions "
                "(0.8%, against this client's own 0.09% at positions 10-11). The body says 'application "
                "development' twice and 'app development' once. The larger query is 'odoo development "
                "company' (601 impressions at 12.9, 2 clicks), which the title already carries, and this "
                "is the only page ranking for either."},
 },
 "snow": {"/products/teeth-whitening-strips": "Core product.",
          "/products/purple-teeth-whitening-strips": "Purple range is the growth line."},
}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("client", nargs="?", default="all")
    a = ap.parse_args()
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    svc = sc()
    # registry holds non-client keys (ihs_group); skip them
    todo = [k for k, v in reg.items() if isinstance(v, dict) and v.get("sheet_id")] if a.client == "all" else [a.client]
    blocked = []
    for slug in todo:
        try:
            build(slug, reg[slug], svc, NOTES.get(slug, {}))
        except GateUnavailable as e:
            blocked.append((slug, str(e)))
            print(f"{slug:<22} BLOCKED, nothing written  {e}")
        except Exception as e:
            print(f"{slug:<22} FAILED {e.__class__.__name__}: {e}")

    if blocked:
        print(chr(10) + "=" * 74)
        print("BLOCKED - a gate had no input, so nothing was written for these clients")
        print("=" * 74)
        for slug, why in blocked:
            print("  %-22s %s" % (slug, why))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


_UNUSED = ["superior", "sameday", "beehive", "comfort", "arsenal", "cudio", "snow"]
for slug in []:
    pass
