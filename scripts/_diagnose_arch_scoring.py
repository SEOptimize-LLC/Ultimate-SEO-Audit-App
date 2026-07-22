"""Diagnose why blog posts are beating service pages in arch-fit scoring."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auditors.cannibalization_auditor import CannibalizationAuditor


def main():
    sf_df = pd.read_excel(ROOT / "Clients/Beehive/beehive_internal_all.xlsx")
    sf_df.columns = [c.strip().lower().replace(" ", "_") for c in sf_df.columns]
    for old, new in [("address", "url"), ("title_1", "title"), ("h1-1", "h1_1")]:
        if old in sf_df.columns and new not in sf_df.columns:
            sf_df = sf_df.rename(columns={old: new})

    auditor = CannibalizationAuditor(df=sf_df)

    # Reproduce the scoring for "drain cleaning salt lake city"
    query = "drain cleaning salt lake city"
    modifiers = auditor._extract_query_modifiers(query)
    print(f"Query: {query}")
    print(f"Modifiers: {modifiers}\n")

    # Walk through candidates
    import re
    from urllib.parse import urlparse
    from auditors.cannibalization_auditor import (
        PRIMARY_SERVICE_KEYWORDS,
        SERVICE_VERB_KEYWORDS,
        GEO_TOKEN_PATTERN,
        GENERIC_PAGE_SLUGS,
    )

    query_services_set = set(
        s.lower().replace("-", "").replace(" ", "")
        for s in modifiers["primary_services"]
    )
    query_verbs_set = set(
        v.lower().replace("-", "").replace(" ", "")
        for v in modifiers["service_verbs"]
    )

    interesting_urls = [
        "https://www.beehiveplumbing.com/drain-cleaning-utah/",
        "https://www.beehiveplumbing.com/sewer-drain-services-utah/",
        "https://www.beehiveplumbing.com/warning-signs-that-you-have-a-drain-cleaning-emergency/",
        "https://www.beehiveplumbing.com/water-heater-repair-utah/",
    ]
    cluster_urls = set()  # empty so all become candidates
    scope = auditor._get_indexable_html()

    for url in interesting_urls:
        match = scope[scope["url"] == url]
        if match.empty:
            print(f"  {url}: NOT IN SF CRAWL")
            continue
        row = match.iloc[0]
        path = urlparse(url).path or ""
        if GENERIC_PAGE_SLUGS.match(path):
            print(f"  {url}: GENERIC PAGE — skipped")
            continue
        slug = auditor._extract_slug(url) or ""
        slug_text = slug.replace("-", " ").replace("_", " ")
        title = row.get("title", "") or ""
        h1 = row.get("h1_1") or row.get("h1") or ""
        page_text = f"{path} {slug_text} {title} {h1}".lower()

        page_services = set(
            m.group(0).lower().replace("-", "").replace(" ", "")
            for m in PRIMARY_SERVICE_KEYWORDS.finditer(page_text)
        )
        page_verbs = set(
            m.group(0).lower().replace("-", "").replace(" ", "")
            for m in SERVICE_VERB_KEYWORDS.finditer(page_text)
        )

        service_match = query_services_set.issubset(page_services)
        service_score = len(query_services_set & page_services) / max(1, len(query_services_set))
        verb_score = (
            len(query_verbs_set & page_verbs) / max(1, len(query_verbs_set))
            if query_verbs_set else 0.5
        )
        slug_score = 1.0 if any(
            s in slug.lower().replace("-", "")
            for s in query_services_set
        ) else 0.5
        overall = (service_score * 0.4) + (verb_score * 0.3) + (slug_score * 0.3)

        print(f"\n  {url}")
        print(f"    title: {title}")
        print(f"    slug: {slug}")
        print(f"    page_services: {page_services}")
        print(f"    page_verbs: {page_verbs}")
        print(f"    service_match (issubset): {service_match}")
        print(f"    service_score: {service_score}, verb_score: {verb_score}, slug_score: {slug_score}")
        print(f"    OVERALL: {overall}")


if __name__ == "__main__":
    main()
