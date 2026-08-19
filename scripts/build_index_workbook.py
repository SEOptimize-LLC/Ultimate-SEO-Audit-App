"""Per-URL indexation workbook: one tab per client, one row per sitemap URL.

Reads the cached index audits written by index_audit.py. No API calls for the
verdicts themselves, so the workbook always matches what the sheets report.

    python scripts/build_index_workbook.py
    python scripts/build_index_workbook.py --month 2026-08
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import zipfile
from pathlib import Path

import openpyxl
import yaml
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))

BRAND_FONT = "Red Hat Display"

INDEXED = "Submitted and indexed"
BENIGN = {INDEXED, "Alternate page with proper canonical tag"}

# What each coverage state actually means for the reader, and who owns the fix.
# Written out per row because "Discovered - currently not indexed" tells a
# developer nothing about whether the problem is content, linking or the server.
UA = "Mozilla/5.0 (compatible; SEOAudit/1.0)"

MEANING = {
    INDEXED: ("In the index", "None"),
    "Alternate page with proper canonical tag": (
        "Correctly canonicalised to another URL", "None"),
    "Crawled - currently not indexed": (
        "Google fetched it and chose not to index it. A quality judgment, so "
        "resubmitting will not change it", "Content"),
    "Discovered - currently not indexed": (
        "Google knows the URL exists but has not crawled it", "Internal linking"),
    "URL is unknown to Google": (
        "In the sitemap but never discovered. Usually no internal link reaches it",
        "Internal linking"),
    "Duplicate without user-selected canonical": (
        "Near-identical to another page and no canonical was set, so Google "
        "picked one", "Dev"),
    "Duplicate, Google chose different canonical than user": (
        "A canonical is set and Google overruled it", "Content + Dev"),
    "Excluded by ‘noindex’ tag": (
        "Google last saw a noindex tag. VERIFY LIVE: the tag may already be gone",
        "Verify first"),
    "Soft 404": (
        "Returns 200 but the page looks empty to Google", "Content"),
    "Not found (404)": ("In the sitemap but the URL is gone", "Dev"),
    "Redirect error": ("The redirect could not be resolved", "Dev"),
    "Page with redirect": ("Redirects elsewhere, so it is not itself indexable",
                           "Sitemap hygiene"),
}

HEAD = ["URL", "Page type", "Indexed?", "Google's coverage state",
        "What it means", "Owner", "Noindex live now?", "Live robots tag",
        "Last crawled", "Days since crawl", "Fetch state", "Robots",
        "Google-selected canonical"]
WIDTH = [74, 11, 9, 34, 52, 14, 15, 40, 13, 9, 22, 16, 60]


def live_robots(urls: list[str]) -> dict[str, tuple[str, str]]:
    """Fetch each URL and read its live robots meta tag.

    Only called for URLs Google reports as excluded by noindex, because that is
    the one state where the API's answer and the live page routinely disagree
    and the two need opposite fixes. SameDay's 98 were all recorded on
    2026-06-30 and not one still carries the tag.

    Returns (verdict, raw tag) keyed by URL. Verdict is YES, NO, or UNREACHABLE,
    never a guess: a URL that will not load is reported as unchecked.
    """
    import re as _re
    import urllib.request
    from concurrent.futures import ThreadPoolExecutor

    def one(u: str) -> tuple[str, tuple[str, str]]:
        try:
            h = urllib.request.urlopen(
                urllib.request.Request(u, headers={"User-Agent": UA}),
                timeout=20).read().decode("utf-8", "replace")
        except Exception as e:
            return u, ("UNREACHABLE", e.__class__.__name__)
        m = _re.search(r"<meta[^>]*name=[\"']robots[\"'][^>]*content=[\"']([^\"']+)",
                       h, _re.I)
        tag = m.group(1).strip() if m else "(no robots meta tag)"
        return u, ("YES" if "noindex" in tag.lower() else "NO", tag)

    # 3 workers: every URL hits one domain and politeness here is correctness.
    with ThreadPoolExecutor(max_workers=3) as pool:
        return dict(pool.map(one, urls))


def page_types(cfg: dict, urls: list[str], sitemap: str | None) -> dict[str, str]:
    """Money / Post / Other for each URL, from the owner-supplied crawl rules.

    Delegates to crawl_targets.select, the same selection the health sweep
    crawls, so the workbook and the sheet can never disagree about what counts
    as a service page.

    Re-implementing the match here was tried and got Beehive wrong twice: its
    money rule is the child sitemap NAME `page-sitemap`, not a URL substring, so
    matching patterns against URLs alone found nothing and reported 0 money-page
    problems against a real 16. Only select() reads sitemap group names.
    """
    import crawl_targets as CT

    c = cfg.get("crawl") or {}
    out = {u: "Other" for u in urls}
    for pat in (c.get("posts") or []):
        for u in urls:
            if pat.lower() in u.lower():
                out[u] = "Post"

    money: set[str] = set()
    if c.get("money_pages"):
        money = {u.rstrip("/") for u in c["money_pages"]}
    elif sitemap:
        try:
            picked, _, _ = CT.select(sitemap, cfg["gsc_property"], cfg)
            money = {u.rstrip("/") for u in picked}
        except Exception:
            money = set()               # unreachable sitemap: leave as Other
    if not money:
        # Last resort for a client whose sitemap will not load. URL-substring
        # matching only, which misses sitemap-name rules, so it is a fallback
        # and never the primary path.
        drop = {u.rstrip("/") for u in (c.get("money_exclude") or [])}
        ex = [x.lower() for x in (c.get("exclude") or [])]
        for u in urls:
            low = u.lower()
            if (any(p.lower() in low for p in (c.get("money") or []))
                    and not any(x in low for x in CT.UTILITY)
                    and not any(x in low for x in ex)
                    and u.rstrip("/") not in drop):
                money.add(u.rstrip("/"))
    for u in urls:
        if u.rstrip("/") in money:
            out[u] = "Money"
    return out


def build(reg: dict, month: str, dest: Path) -> tuple[Path, list[tuple]]:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    today = dt.date.today()
    summary = []

    for slug, cfg in reg.items():
        cache = Path(cfg["folder"]) / "Monthly SEO Workbook" / month / "index_audit.json"
        if not cache.exists():
            continue
        d = json.loads(cache.read_text(encoding="utf-8"))
        rows = d["rows"]
        # Only the owner-defined scope. Out-of-scope URLs stay in the cache but
        # are not the client's audit: Cudio's /jobs/ and Snow's /pages/ are in
        # the sitemap and are neither services, products, collections nor posts.
        smtot = d.get("sitemapTotal") or len(rows)
        if any("inScope" in r for r in rows):
            rows = [r for r in rows if r.get("inScope")]
        urls = [r["url"] for r in rows]
        sms = d.get("sitemaps") or []
        types = page_types(cfg, urls, sms[0] if sms else None)

        nox = [r["url"] for r in rows if "noindex" in r["state"].lower()]
        live = live_robots(nox) if nox else {}
        if nox:
            still = sum(1 for v in live.values() if v[0] == "YES")
            print(f"  {cfg['name']}: {len(nox)} noindex-state URLs, "
                  f"{still} still carry the tag live", flush=True)

        ws = wb.create_sheet(cfg["name"][:31])
        sampled = bool(d.get("sampled"))
        idx = sum(1 for r in rows if r["state"] in BENIGN)
        pct = f"{100.0 * idx / len(rows):.0f}%" if rows else "n/a"

        ws["A1"] = f"{cfg['name']} - indexation by URL, {month}"
        ws["A1"].font = Font(name=BRAND_FONT, size=14, bold=True)
        ws["A2"] = (
            f"{len(rows)} in-scope URLs (money pages + posts + homepage), "
            f"{idx} indexed ({pct}). "
            + (f"The sitemap holds {smtot}; the other {smtot - len(rows)} are "
               f"outside the defined scope and are not counted here. "
               if smtot > len(rows) else "")
            + f"Source: Search Console URL Inspection, {today.isoformat()}. "
            + ("SAMPLE ONLY - the registered sitemap does not resolve, so this "
               "covers the top landing pages from 1.1, not the whole site. "
               if sampled else "")
            + "Every state below is Google's verdict AT ITS LAST CRAWL, not the "
              "live page. Check the crawl date before acting.")
        ws["A2"].font = Font(name=BRAND_FONT, size=9, italic=True)
        ws["A2"].alignment = Alignment(wrap_text=False)

        for i, h in enumerate(HEAD, 1):
            c = ws.cell(row=4, column=i, value=h)
            c.font = Font(name=BRAND_FONT, bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="1F3864")
            c.alignment = Alignment(vertical="center", wrap_text=True)
        ws.row_dimensions[4].height = 30

        # Worst first: a 400-row tab read top to bottom should open on the
        # problems, not on several hundred healthy URLs.
        order = {INDEXED: 3, "Alternate page with proper canonical tag": 2}
        rows = sorted(rows, key=lambda r: (order.get(r["state"], 0),
                                           types.get(r["url"], ""), r["url"]))

        for n, r in enumerate(rows, 5):
            st = r["state"]
            mean, owner = MEANING.get(st, ("State without a rule yet. Confirm one "
                                           "URL in Search Console.", "Review"))
            days = ""
            if r.get("lastCrawl"):
                try:
                    days = (today - dt.date.fromisoformat(r["lastCrawl"])).days
                except ValueError:
                    days = ""
            lv, tag = live.get(r["url"], ("", ""))
            # The live check has already run by this point, so the row states
            # its conclusion rather than telling the reader to go and verify.
            # The two outcomes need opposite work and must not read alike.
            if lv == "NO":
                mean = ("Tag is GONE. Google's record is stale and it has not "
                        "re-crawled. Nothing to change on the page")
                owner = "Request indexing"
            elif lv == "YES":
                mean = ("Tag is LIVE and confirmed. The sitemap submits this "
                        "page while the page forbids indexing")
                owner = "Dev"
            elif lv == "UNREACHABLE":
                mean = ("Google saw a noindex tag and the live check could not "
                        "load the URL. State unconfirmed")
                owner = "Verify first"
            vals = [r["url"], types.get(r["url"], "Other"),
                    "Yes" if st in BENIGN else "No", st, mean, owner,
                    lv, tag, r.get("lastCrawl") or "never", days,
                    r.get("fetch") or "", r.get("robots") or "",
                    r.get("canonical") or ""]
            for i, v in enumerate(vals, 1):
                c = ws.cell(row=n, column=i, value=v)
                c.font = Font(name=BRAND_FONT, size=10)
                c.alignment = Alignment(vertical="top", wrap_text=(i == 5))
            if st not in BENIGN:
                fill = PatternFill("solid", fgColor="FCE4E4")
                for i in range(1, len(HEAD) + 1):
                    ws.cell(row=n, column=i).fill = fill

        last = 4 + len(rows)
        for i, w in enumerate(WIDTH, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "A5"
        ws.auto_filter.ref = f"A4:{get_column_letter(len(HEAD))}{last}"

        dv = DataValidation(type="list", formula1='"Yes,No"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"C5:C{last}")

        summary.append((cfg["name"], len(rows), idx, pct,
                        sum(1 for r in rows if r["state"] not in BENIGN),
                        sum(1 for r in rows if types.get(r["url"]) == "Money"
                            and r["state"] not in BENIGN), sampled))

    dest.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dest)

    # Brand font through the shared font table, not cell by cell: one pass sets
    # the family everywhere and leaves size, weight and colour untouched. Index
    # 0 is the workbook default that untouched cells inherit, so skipping it
    # would leave anything typed later in the old face.
    wb2 = openpyxl.load_workbook(dest)
    for f in wb2._fonts:
        f.name = BRAND_FONT
    for st in getattr(wb2, "_named_styles", []):
        if getattr(st, "font", None) is not None:
            st.font.name = BRAND_FONT
    wb2.save(dest)
    return dest, summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default=dt.date.today().strftime("%Y-%m"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    reg = yaml.safe_load(open("clients/registry.yaml", encoding="utf-8"))
    dest = Path(a.out or f"Documents/Indexation by URL - all clients - {a.month}.xlsx")
    dest, summary = build(reg, a.month, dest)

    x = zipfile.ZipFile(dest).read("xl/styles.xml").decode("utf-8", "replace")
    bad = [f for f in ("Calibri", "Arial", "Aptos") if f in x]
    print(f"{dest}\n")
    print("%-24s %6s %8s %6s %8s %7s" % ("client", "URLs", "indexed", "%",
                                         "problems", "money"))
    for name, n, idx, pct, bad_n, money_bad, sampled in summary:
        print("%-24s %6d %8d %6s %8d %7d%s"
              % (name, n, idx, pct, bad_n, money_bad, "  (SAMPLE)" if sampled else ""))
    print(f"\nfont check: {'FAIL - ' + ', '.join(bad) if bad else 'clean, Red Hat Display only'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
