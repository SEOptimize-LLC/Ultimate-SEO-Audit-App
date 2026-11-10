"""Turn a client's 1.2 findings into 2.1 fix rows and 1.8 routed items.

    python scripts/build_2_1_from_1_2.py <client|all> [--dry-run]

1.2 feeds 2.1 (the fix queue) and 1.8 (the plan). The "Routed To" column on the
1.2 findings log says where each finding goes; this authors both destinations:

    Clients/<folder>/monthly_plan/fixes.yaml           -> fill_2_1.py
    Clients/<folder>/monthly_plan/routed_to_1_8.yaml   -> route_to_1_8.py,
                                                          and fill_1_8.py merges it

Rows are self-contained (tasks/2.1.md): every page named by its FULL URL, steps a
person can do, a verify step, no pointer to another tab or file. A URL list too
long for a 950-character cell is split into numbered rows ("1 OF 3"), each one a
batch somebody can be assigned. The one exception is a list Search Console itself
holds in full (stale-noindex, crawled-not-indexed): those name the first URLs and
the report to open, which tasks/2.1.md allows ("naming a TOOL location is an
instruction, not a pointer").

Facts are read here, at build time: the stale-noindex pages are ALL fetched live
(no sampling, tasks/2.1.md) and the 404 URL is fetched before it is called a 404.
An existing fixes.yaml is moved to fixes-<yyyy-mm>.yaml first, never overwritten.

Search Console flips URLs between "URL is unknown to Google" and "Discovered -
currently not indexed" from one inspection to the next, so both are ONE group,
"not yet crawled by Google": the work is identical.

Sequencing (tasks/2.1.md): old-tail blog posts that Google has not crawled WAIT
when the same kind of post is already sitting in "Crawled - currently not
indexed" (HOLD_CNI_POSTS or more). Linking to posts a quality review may prune is
double work, so those get a HOLD row that says so, not a link-building task.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crawl_targets as CT  # noqa: E402
import sheets_io as S  # noqa: E402
import verify_1_2 as V  # noqa: E402  (fetch(): live status, noindex, canonical)

TAB = "1.2 Health Sweep"
UNK = "URL is unknown to Google"
DNI = "Discovered - currently not indexed"
CNI = "Crawled - currently not indexed"
INDEXED = "Submitted and indexed"
CELL_MAX = 950
HOLD_CNI_POSTS = 10          # crawled-not-indexed posts at or above this: hold post link-building
SAMPLE = 6                   # URLs named in a HOLD / tool-location row
MAX_BATCHES = 5              # rows a single URL list may split into


def _yaml_str(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _yaml_str)


# ------------------------------------------------------------------ inputs

def read_findings(sid: str) -> list[dict]:
    p = S.find_rows(sid, TAB, {"b": "B. Findings log"})
    out = []
    for r in S.read(sid, f"'{TAB}'!A{p['b'] + 2}:F{p['b'] + 70}"):
        r = (list(r) + [""] * 6)[:6]
        if str(r[1]).strip():
            out.append({"issue": str(r[1]),
                        "urls": [u.strip() for u in str(r[2]).split(";") if u.strip().startswith("http")],
                        "sev": str(r[3]), "route": str(r[4]).strip(), "notes": str(r[5])})
    return out


def cache_path(cfg: dict, month: str) -> Path:
    return Path(cfg["folder"]) / "Monthly SEO Workbook" / month / "index_audit.json"


def load_cache(cfg: dict, month: str) -> dict | None:
    f = cache_path(cfg, month)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def post_urls(cfg: dict) -> set[str]:
    """Every sitemap URL the 1.2 sweep treats as a blog post (same patterns as crawl_targets)."""
    import google.auth
    from googleapiclient.discovery import build as gbuild
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    sc = gbuild("searchconsole", "v1", credentials=creds, cache_discovery=False)
    path = sc.sitemaps().list(siteUrl=cfg["gsc_property"]).execute()["sitemap"][0]["path"]
    pats = (cfg.get("crawl") or {}).get("posts") or ["post-sitemap"]
    out = set()
    for name, entries in CT.collect(path).items():
        for loc, _lm in entries:
            if CT._match(name, loc, pats):
                out.add(loc)
    return out


# --------------------------------------------------------------- composition

def depth_key(u: str) -> tuple[int, str]:
    """Shallower URLs first: a hub or service page outranks its children."""
    return (len([s for s in urlparse(u).path.split("/") if s]), u)


def compose(head: list[str], urls: list[str], tail: list[str]) -> str:
    return "\n".join(head + [f"• {u}" for u in urls] + tail)


def fit(head: list[str], urls: list[str], tail: list[str]) -> str:
    """One cell naming as many leading URLs as the cap allows."""
    shown = list(urls[:SAMPLE])
    while shown and len(compose(head, shown, tail)) > CELL_MAX:
        shown.pop()
    return compose(head, shown, tail)


def batches(title: str, head: list[str], urls: list[str], tail: list[str]) -> list[tuple[str, list[str]]]:
    """Split a URL list across as many cells as the 950-character cap needs.

    Greedy: each cell takes URLs until the next one would not fit. Titles carry
    "N OF M" once the count is known. Past MAX_BATCHES the remaining URLs are
    counted in the last cell, never silently dropped.
    """
    probe = f"{title}, 9 OF 9"
    chunks: list[list[str]] = []
    cur: list[str] = []
    for u in urls:
        if cur and len(compose([probe, ""] + head, cur + [u], tail)) > CELL_MAX:
            chunks.append(cur)
            cur = [u]
        else:
            cur.append(u)
    if cur:
        chunks.append(cur)
    left: list[str] = []
    if len(chunks) > MAX_BATCHES:
        left = [u for c in chunks[MAX_BATCHES:] for u in c]
        chunks = chunks[:MAX_BATCHES]
    n = len(chunks)
    out = []
    for i, c in enumerate(chunks, 1):
        t = title if n == 1 else f"{title}, {i} OF {n}"
        c = list(c)
        if left and i == n:
            # The overflow line costs characters too: give URLs back until it fits.
            while True:
                extra = [f"• +{len(left)} more URLs read the same state."]
                if len(compose([t, ""] + head, c, extra + tail)) <= CELL_MAX or len(c) == 1:
                    break
                left.insert(0, c.pop())
            out.append((compose([t, ""] + head, c, extra + tail), c))
        else:
            out.append((compose([t, ""] + head, c, tail), c))
    return out


def as_rows(cells: list[tuple[str, list[str]]], source: str = "1.2") -> list[dict]:
    return [{"source": source,
             "where": urls[0] + (f" + {len(urls) - 1} more" if len(urls) > 1 else ""),
             "fix": text} for text, urls in cells]


# ------------------------------------------------------------------ 2.1 rows

def fix_stale_noindex(rows: list[dict]) -> dict | None:
    held = [r["url"] for r in rows if "noindex" in r["state"].lower()]
    if not held:
        return None
    with ThreadPoolExecutor(max_workers=3) as pool:
        recs = list(pool.map(V.fetch, held))
    still = [r["url"] for r in recs if r["noindex"]]
    gone = sorted([r["url"] for r in recs if r["status"] == 200 and not r["noindex"]], key=depth_key)
    other = [r["url"] for r in recs if r["status"] != 200 and not r["noindex"]]
    head = ["STALE NOINDEX VERDICT (BLOCKER)", "",
            f"• Search Console holds {len(held)} sitemap URLs out of the index as \"Excluded by 'noindex' tag\".",
            f"• All {len(held)} were fetched live on {dt.date.today().isoformat()}: {len(gone)} return 200 with no noindex, "
            f"{len(still)} still serve noindex, {len(other)} do not return 200.",
            "• Google last crawled them before the tag came off, so the verdict is out of date, not the pages.",
            "• Highest-level pages first:"]
    tail = ["", "DO",
            "• Search Console > Pages > Excluded by 'noindex' tag > VALIDATE FIX." + (
                f" The {len(still)} that still serve noindex need the tag removed first." if still else ""),
            "• URL Inspection > Request indexing on the pages above, then resubmit the sitemap.",
            "", "VERIFY",
            "• URL Inspection on each: Indexing allowed reads Yes and the page leaves the Excluded report."]
    return {"source": "1.2", "where": f"{len(held)} URLs; full list: Search Console > Pages > Excluded by 'noindex' tag",
            "fix": fit(head, gone, tail)}


def fix_404(urls: list[str]) -> dict | None:
    if not urls:
        return None
    u = urls[0]
    rec = V.fetch(u)
    live = f"returns HTTP {rec['status']}" if rec["status"] else f"could not be fetched ({rec['error']})"
    head = ["SITEMAP URL THAT DOES NOT RESOLVE", "",
            f"• {u} {live} on the live site (fetched {dt.date.today().isoformat()}), "
            "and Search Console records it as Not found (404)."]
    tail = ["", "DO",
            "• If the page should exist, restore it. If it was retired, take it out of the sitemap.",
            "• If a live replacement exists, 301 to it only after fetching the replacement and confirming it returns 200.",
            "", "VERIFY",
            "• curl -I the URL: 200, or one 301 to a 200. Then resubmit the sitemap in Search Console."]
    return {"source": "1.2", "where": u, "fix": "\n".join(head + tail)}


def fix_not_crawled(rows: list[dict], posts: set[str]) -> tuple[list[dict], list[str]]:
    """Pages (act now) and posts (act, or HOLD) that Google has not crawled."""
    notes: list[str] = []
    nc = [r for r in rows if r["state"] in (UNK, DNI)]
    if not nc:
        return [], notes
    dated = [r["url"] for r in nc if r.get("lastCrawl")]
    if dated:
        notes.append(f"{len(dated)} not-crawled URL(s) carry a last-crawl date")
    pages = sorted([r["url"] for r in nc if r["url"] not in posts], key=depth_key)
    blog = sorted([r["url"] for r in nc if r["url"] in posts], key=depth_key)
    out: list[dict] = []

    head = ["• No Google crawl on record (Search Console: \"unknown to Google\" or "
            "\"Discovered - currently not indexed\")."]
    tail = ["", "DO",
            "• Link each page from one already-crawled page (its parent service page, the blog index or a related post).",
            "• URL Inspection > Request indexing, a few a day (Search Console caps daily requests).",
            "", "VERIFY",
            "• URL Inspection: the page shows a last-crawl date within 4 weeks."]
    if pages:
        out += as_rows(batches("NOT YET CRAWLED, PAGES", head, pages, tail))

    cni_posts = sum(1 for r in rows if r["state"] == CNI and r["url"] in posts)
    if blog and cni_posts >= HOLD_CNI_POSTS:
        head_h = [f"• Hold. {len(blog)} blog posts have no Google crawl on record. Examples:"]
        tail_h = ["", "WHY HOLD",
                  f"• Google already crawled and declined {cni_posts} posts of the same kind (Crawled - currently not indexed).",
                  "• Links to a post the content-quality review later merges or prunes are wasted work.",
                  "", "DO",
                  "• Wait for the review. Link only to the posts that survive it, then request indexing.",
                  "", "VERIFY",
                  "• Next month's check: the not-crawled post count falls once survivors are linked."]
        out.append({"source": "1.2", "where": f"{len(blog)} blog posts, no Google crawl on record",
                    "fix": fit(["NOT YET CRAWLED, POSTS: HOLD", ""] + head_h, blog, tail_h)})
    elif blog:
        out += as_rows(batches("NOT YET CRAWLED, POSTS", head, blog, tail))
    return out, notes


def fix_recency(f: dict, rows: list[dict], asof: dt.date) -> dict | None:
    m = re.match(r"(\d+) URL\(s\) \((\d+)%\) not crawled in 90\+ days", f["issue"])
    if not m:
        return None
    med = re.search(r"Median last-crawl age across the site is (\d+) days", f["notes"])
    stale = sorted([r["url"] for r in rows if r.get("lastCrawl")
                    and (asof - dt.date.fromisoformat(r["lastCrawl"])).days > 90], key=depth_key)
    head = ["STALE CRAWL COVERAGE", "",
            f"• {m.group(1)} sitemap URLs ({m.group(2)}%) were last crawled over 90 days ago"
            + (f"; the site's median last-crawl age is {med.group(1)} days." if med else "."),
            "• Counts URLs, not Googlebot requests. A watch measure, not a defect. Highest-level pages first:"]
    tail = ["", "DO",
            "• Clear the stale noindex verdicts and not-yet-crawled pages in the rows above first: that work refreshes most of this group.",
            "• Check the sitemap lastmod is accurate for pages that change.",
            "", "VERIFY",
            "• Next month's check: the 90+ day share falls."]
    return {"source": "1.2", "where": f"{m.group(1)} sitemap URLs not crawled in 90+ days",
            "fix": fit(head, stale, tail)}


def fix_ttfb(fs: list[dict]) -> dict | None:
    vals = []
    for f in fs:
        m = re.match(r"(.+?) template: TTFB (\d+)ms", f["issue"])
        if m and f["urls"]:
            vals.append((m.group(1), int(m.group(2)), f["urls"][0]))
    if not vals:
        return None
    urls = list(dict.fromkeys(u for _n, _v, u in vals))
    measured = "; ".join(f"{n} {v:,} ms" for n, v, _u in vals)
    worst = max(v for _n, v, _u in vals)
    head = ["SLOW SERVER RESPONSE (TTFB)", "",
            f"• Chrome UX Report field data (mobile, 75th percentile) rates time to first byte AVERAGE: {measured}.",
            "• Not a Core Web Vital: server response work, not a CWV fix. Measured pages:"]
    tail = ["", "DO",
            "• Time each page from a cold cache, then warm: curl -s -o /dev/null -w \"%{time_starttransfer}\" <url>.",
            "• Check the HTML comes from page cache (a cache header such as x-cache, cf-cache-status or x-litespeed-cache), not rebuilt per request.",
            "• If uncached TTFB stays high, profile the slowest plugin or database work behind it and fix the largest.",
            "", "VERIFY",
            f"• Warm curl TTFB reads well under {worst:,} ms. After 28 days, PageSpeed Insights field TTFB should be under 800 ms."]
    return {"source": "1.2", "where": "; ".join(urls), "fix": compose(head, urls, tail)}


def fixes_from_1_4(sid: str) -> list[dict]:
    """1.4 section D fix items, which tasks/1.4.md routes to 2.1.

    A fix 1.4 already wrote as a brief (it has line breaks) is copied as is; a
    one-line fix is wrapped in the same DO / VERIFY shape. "No fixes required"
    is not a fix.
    """
    tab = "1.4 AI Access Check"
    p = S.find_rows(sid, tab, {"d": "Fix"})
    out = []
    for r in S.read(sid, f"'{tab}'!A{p['d'] + 1}:B{p['d'] + 25}"):
        text = str(r[0]).strip() if r else ""
        if not text or text.lower().startswith("no fixes required"):
            continue
        if "\n" not in text:
            title = re.split(r" - |\. ", text)[0].upper()[:34]
            text = "\n".join([title, "", f"• {text}", "", "DO", "• Make the change named above.",
                              "", "VERIFY", "• Re-run the 1.4 check for this item and confirm it passes."])
        urls = re.findall(r"https?://[^\s)]+", text)
        out.append({"source": "1.4", "where": urls[0] if urls else "", "fix": text})
    return out


def fix_generic(f: dict) -> dict:
    """A 2.1-routed finding no specific builder knows. Surfaced loudly, never dropped."""
    head = [f["issue"].upper()[:34], "", f"• {f['issue']}"] + ([f"• {f['notes']}"] if f["notes"] else [])
    tail = ["", "DO", "• Fix at source and re-run the check that raised it.", "", "VERIFY",
            "• Re-run the 1.2 check for this item and confirm it no longer fires."]
    return {"source": "1.2", "where": f["urls"][0] if f["urls"] else "", "fix": fit(head, f["urls"], tail)}


# ------------------------------------------------------------------ 1.8 rows

def need_dropped(rows: list[dict], prev_rows: list[dict]) -> list[dict]:
    prev = {r["url"]: r["state"] for r in prev_rows}
    gone = sorted([(r["url"], r["state"]) for r in rows if prev.get(r["url"]) == INDEXED and r["state"] != INDEXED],
                  key=lambda t: depth_key(t[0]))
    if not gone:
        return []
    states = ", ".join(sorted({s for _u, s in gone}))
    head = [f"• {len(gone)} URLs were indexed last month and are not indexed now (Search Console: {states}).",
            "• Highest-level pages first:"]
    tail = ["", "DECIDE",
            "• Per page: refresh, merge into a stronger page, or leave. Compare each against pages Google still indexes (word count, uniqueness, internal links) first."]
    cells = batches("DROPPED OUT OF THE INDEX", head, [u for u, _s in gone], tail)
    return [{"need": text, "source": "1.2 (Blocker)", "task": ""} for text, _u in cells]


def need_cni(f: dict, rows: list[dict]) -> list[dict]:
    cni = sorted([r["url"] for r in rows if r["state"] == CNI], key=depth_key)
    if not cni:
        return []
    m = re.search(r"\((\d+)% of sitemap\)(?: \(was (\d+) last month\))?", f["issue"])
    pct = m.group(1) if m else "?"
    was = f"; last month {m.group(2)}" if m and m.group(2) else ""
    head = ["CRAWLED, NOT INDEXED", "",
            f"• {len(cni)} URLs Google crawled and chose not to index ({pct}% of the sitemap{was}).",
            "• Highest-level pages first. Full list: Search Console > Pages > Crawled - currently not indexed:"]
    tail = ["", "DECIDE",
            "• Read the 1.2 render check first: a page whose stylesheets or scripts are blocked, or whose raw HTML is near empty, is a rendering fix, not a quality call.",
            "• For pages that render clean, it is a quality reading, so resubmitting will not fix it. Confirm with Test live URL, then improve, merge or prune after comparing against indexed pages (word count, uniqueness)."]
    return [{"need": fit(head, cni, tail), "source": "1.2", "task": ""}]


# --------------------------------------------------------------------- driver

def build(slug: str, cfg: dict) -> tuple[list[dict], list[dict], list[str]]:
    sid = cfg["sheet_id"]
    F = read_findings(sid)
    today = dt.date.today()
    month = today.strftime("%Y-%m")
    prev_month = (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    cur, prev = load_cache(cfg, month), load_cache(cfg, prev_month)
    rows = cur["rows"] if cur else []
    prev_rows = prev["rows"] if prev else []
    asof = dt.date.fromtimestamp(cache_path(cfg, month).stat().st_mtime) if cur else today
    notes: list[str] = []
    posts: set[str] = set()
    try:
        posts = post_urls(cfg)
    except Exception as e:                      # noqa: BLE001
        notes.append(f"post classification fell back to /blog/ paths ({e.__class__.__name__})")
    if not posts:
        posts = {r["url"] for r in rows if "/blog/" in r["url"]}

    fixes: list[dict] = []
    # priority: indexation blockers > redirects/dead URLs > crawl coverage > performance
    x = fix_stale_noindex(rows)
    if x:
        fixes.append(x)
    f404 = next((f for f in F if "Not found (404)" in f["issue"]), None)
    if f404:
        x = fix_404(f404["urls"])
        if x:
            fixes.append(x)
    # 1.4 fixes (an AI crawler refused at the server, a page that does not
    # render) sit with the indexation blockers: an assistant that cannot read
    # the site cannot cite it, whatever the crawl coverage looks like.
    try:
        fixes += fixes_from_1_4(sid)
    except KeyError:
        notes.append("1.4 tab not found: no 1.4 fixes carried")
    nc, n_notes = fix_not_crawled(rows, posts)
    fixes += nc
    notes += n_notes
    frec = next((f for f in F if "not crawled in 90+" in f["issue"]), None)
    if frec:
        x = fix_recency(frec, rows, asof)
        if x:
            fixes.append(x)
    x = fix_ttfb([f for f in F if "TTFB" in f["issue"] and f["route"] == "2.1"])
    if x:
        fixes.append(x)

    # anything routed to 2.1 that no builder above covers: written generically, and said so
    known = ("TTFB", "Not found (404)", "not crawled in 90+", "STALE noindex",
             "Discovered - currently not indexed", "unknown to Google")
    for f in F:
        if f["route"] == "2.1" and not any(k in f["issue"] for k in known):
            fixes.append(fix_generic(f))
            notes.append(f"generic row for: {f['issue'][:50]}")

    routed = need_dropped(rows, prev_rows)
    for f in F:
        if f["route"] == "1.8" and "Crawled - currently not indexed" in f["issue"]:
            routed += need_cni(f, rows)
    return fixes, routed, notes


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    dry = "--dry-run" in sys.argv
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    todo = ([k for k, v in reg.items() if isinstance(v, dict) and v.get("sheet_id") and v.get("active") is not False]
            if sys.argv[1] == "all" else [sys.argv[1]])
    for slug in todo:
        cfg = reg[slug]
        fixes, routed, notes = build(slug, cfg)
        d = Path(cfg["folder"]) / "monthly_plan"
        print(f"{slug:<22} 2.1 rows: {len(fixes)}  1.8 routed: {len(routed)}"
              + (f"   [{'; '.join(notes)}]" if notes else ""))
        for x in fixes:
            over = "  !! OVER CAP" if len(x["fix"]) > CELL_MAX else ""
            print(f"     2.1  {x['fix'].splitlines()[0]:<42} {len(x['fix'])} chars{over}")
        for x in routed:
            over = "  !! OVER CAP" if len(x["need"]) > CELL_MAX else ""
            print(f"     1.8  {x['need'].splitlines()[0]:<42} {len(x['need'])} chars{over}")
        if dry:
            continue
        d.mkdir(parents=True, exist_ok=True)
        old = d / "fixes.yaml"
        if old.exists():
            stamp = dt.date.fromtimestamp(old.stat().st_mtime).strftime("%Y-%m")
            bak = d / f"fixes-{stamp}.yaml"
            if not bak.exists():
                old.replace(bak)
        (d / "fixes.yaml").write_text(
            yaml.dump({"fixes": fixes, "overflow": [], "score_note": False},
                      allow_unicode=True, sort_keys=False, width=100000), encoding="utf-8")
        (d / "routed_to_1_8.yaml").write_text(
            yaml.dump({"routed": routed}, allow_unicode=True, sort_keys=False, width=100000),
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
