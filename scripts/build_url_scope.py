"""Write Clients/<folder>/url_scope.txt from GSC pages.

    python scripts/build_url_scope.py comfort

Task 1.4 falls back to this file when a client's sitemap cannot be read, which
happens for two different reasons seen so far: the site refuses our address
(Education Walkthrough returns 403 to everything from here) or the sitemap URL
simply 404s (Comfort). Either way section B silently shrinks to the homepage
alone and still reports a result, which reads as "checked" rather than "could
not check".

The limit is real and is written into the file header: GSC only knows URLs that
have had impressions, so a page that has never ranked is invisible here. That is
narrower than a sitemap and still far better than one row.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from task_1_5 import periods, sc  # noqa: E402

# Assets and archive listings are not templates and should never be sampled as
# though they were.
SKIP = re.compile(r"/wp-content/|/category/|/tag/|/page/\d|\.(pdf|jpg|jpeg|png|webp|xml)$",
                  re.I)


def build(slug: str, months: int = 15) -> Path:
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    cfg = reg[slug]
    (_, end), _ = periods()
    start = end - dt.timedelta(days=30 * months)
    svc = sc()
    rows, at = [], 0
    while True:
        r = svc.searchanalytics().query(siteUrl=cfg["gsc_property"], body={
            "startDate": str(start), "endDate": str(end),
            "dimensions": ["page"], "rowLimit": 25000, "startRow": at}
        ).execute().get("rows", [])
        rows += r
        if len(r) < 25000:
            break
        at += 25000
    ex = (cfg.get("crawl") or {}).get("exclude") or []
    urls: list[str] = []
    for x in rows:
        u = x["keys"][0].split("#")[0]
        if any(e in u for e in ex) or SKIP.search(u):
            continue
        if u not in urls:
            urls.append(u)
    out = Path(cfg["folder"]) / "url_scope.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"# In-scope URLs for {slug}, from GSC pages {start} to {end},\n"
        f"# written {dt.date.today()}. Used by task 1.4 when the sitemap cannot\n"
        f"# be read. Covers pages that have had impressions only, so a page that\n"
        f"# has never ranked is absent. State that wherever this is relied on.\n"
        + "\n".join(sorted(urls)) + "\n", encoding="utf-8")
    print(f"{slug:<10} {len(rows)} GSC page rows -> {len(urls)} in-scope -> {out}")
    return out


if __name__ == "__main__":
    for s in sys.argv[1:]:
        build(s)
