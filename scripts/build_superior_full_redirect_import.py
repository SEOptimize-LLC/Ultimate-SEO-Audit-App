"""
Superior Water & Air — Full Rank Math Redirect Import (cleaned set).

Produces ONE CSV file that, when imported into Rank Math, will:
  1. DELETE every existing redirect we identified as conflict/junk/stale
     (Chain Risk, Stale Destination, Malformed, Obsolete Path, Image Redirects)
  2. KEEP the 34 existing redirects that don't conflict with the migration
     (no rows for these — they stay in the database untouched)
  3. ADD the 112 new migration redirects from the URL architecture migration

Output format (per Rank Math CSV import docs:
https://rankmath.com/kb/how-to-manage-redirects-via-csv/):
  - Comma-separated
  - Header row with columns: id, source, matching, destination, type,
    category, status, ignore (case-sensitive lowercase)
  - For deletions: existing ID + destination = "DELETE" (case-sensitive)
  - For new: empty ID + full row data

Inputs:
    Clients/Superior/superiorwaterampair_rank-math-redirections-2026-04-26_14-23-39.csv
    Clients/Superior/Full SEO Audit/superior_redirects_rankmath_import.csv
    /tmp/superior_indexable.json

Output:
    Clients/Superior/Full SEO Audit/superior_rankmath_redirects_cleaned_full_import.csv
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = (
    r"c:/Users/admin/Documents/Marketing/Roger SEO/AI Automations/Claude/"
    r"Claude Code + VS Code/SEO/Projects/Projects/Ultimate SEO Auditor"
)
EXISTING_CSV = os.path.join(
    ROOT,
    "Clients/Superior/superiorwaterampair_rank-math-redirections-2026-04-26_14-23-39.csv",
)
NEW_CSV = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_redirects_rankmath_import.csv",
)
INDEXABLE_JSON = "/tmp/superior_indexable.json"
OUT_CSV = os.path.join(
    ROOT,
    "Clients/Superior/Full SEO Audit/superior_rankmath_redirects_cleaned_full_import.csv",
)

DOMAIN = "https://superiorwaterandair.com"


def normalize_path(s: str) -> str:
    s = s.replace(DOMAIN, "")
    s = s.lstrip("/").rstrip("/")
    return s.lower()


def is_malformed(source: str) -> bool:
    if "//1000" in source:
        return True
    if "?mobile_switch" in source:
        return True
    if source.endswith("/feed/") or source.endswith("/feed"):
        return True
    m = re.match(r"^service-areas/([^/]+)/?$", source)
    if m:
        slug = m.group(1)
        base = re.sub(r"-(utah|ut)$", "", slug)
        if len(base) <= 5 and not re.search(r"[bcdfghjklmnpqrstvwxz]{2,}", base):
            return True
        if base in (
            "e", "se", "le", "ne", "rem", "use", "pine", "ial",
            "lpine", "pringville", "racuse", "yracuse", "ringville",
            "acuse", "ennial", "gville", "ine",
        ):
            return True
    if source == "service-areas/-utah/":
        return True
    return False


def load_existing():
    rows = []
    with open(EXISTING_CSV, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # header
        for row in reader:
            if len(row) < 4 or not row[1]:
                continue
            rows.append({
                "id": row[0],
                "source": row[1],
                "destination": row[3],
                "type": row[4] if len(row) > 4 else "301",
                "category": row[5] if len(row) > 5 else "",
                "status": row[6] if len(row) > 6 else "active",
                "ignore": row[7] if len(row) > 7 else "",
            })
    return rows


def load_new_plan():
    rows = []
    with open(NEW_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "source": r["source url"],
                "destination": r["destination url"],
            })
    return rows


def load_indexable():
    data = json.load(open(INDEXABLE_JSON, encoding="utf-8"))
    return {normalize_path(p["url"]) for p in data}


def categorize_existing(existing, new_plan, indexable):
    """Categorize each existing redirect ROW by category.

    Note: Rank Math allows multiple source URLs per redirect rule (one
    rule, several sources). The CSV export emits one row per source, all
    sharing the same ID. This function categorizes per-row but the caller
    should deduplicate by ID when writing DELETE rows to the import file.

    Categories: 'CHAIN_RISK', 'STALE_DEST', 'MALFORMED', 'OBSOLETE_PATH',
                'IMAGE_REDIRECT', 'KEEP'

    Returns a list of (existing_row, category) tuples preserving order.
    """
    new_sources = {r["source"].lstrip("/").rstrip("/").lower() for r in new_plan}
    existing_sources = {
        x["source"].lstrip("/").rstrip("/").lower() for x in existing
    }
    result = []

    for e in existing:
        src = e["source"].lstrip("/").rstrip("/").lower()
        dest = e["destination"]
        dest_path = normalize_path(dest)

        if src.startswith("wp-content/uploads/"):
            cat = "IMAGE_REDIRECT"
        elif is_malformed(src):
            cat = "MALFORMED"
        elif dest_path in new_sources:
            cat = "CHAIN_RISK"
        elif dest_path and dest_path not in indexable:
            if dest_path in existing_sources:
                cat = "CHAIN_RISK"
            else:
                cat = "STALE_DEST"
        elif dest_path.startswith(("water/", "hvac/", "plumbing-services/")):
            if dest_path in new_sources:
                cat = "CHAIN_RISK"
            else:
                cat = "OBSOLETE_PATH"
        else:
            cat = "KEEP"

        result.append((e, cat))

    return result


def main():
    existing = load_existing()
    new_plan = load_new_plan()
    indexable = load_indexable()
    categorized = categorize_existing(existing, new_plan, indexable)

    # Per-row counts (one row per source — Rank Math export expands groups)
    from collections import Counter, defaultdict
    counts = Counter(cat for _, cat in categorized)
    print("Per-row categorization (each source URL counted separately):")
    for cat, n in counts.most_common():
        print(f"  {cat:18s}: {n}")
    print(f"  TOTAL ROWS         : {len(categorized)}")

    # Group by ID — Rank Math stores some redirects as "one rule, multiple
    # source URLs". Deleting needs to happen per-rule (one DELETE row per ID),
    # not per-source-URL.
    delete_categories = {
        "CHAIN_RISK", "STALE_DEST", "MALFORMED",
        "OBSOLETE_PATH", "IMAGE_REDIRECT",
    }
    rules_to_delete: dict[str, dict] = {}
    rules_to_keep: dict[str, dict] = {}
    for row, cat in categorized:
        rid = row["id"]
        if cat in delete_categories:
            # Use the first row encountered as the representative for the delete
            if rid not in rules_to_delete:
                rules_to_delete[rid] = row
            # Note: if a rule has mixed-category rows (some DELETE, some KEEP),
            # DELETE wins because the entire rule is being removed.
            rules_to_keep.pop(rid, None)
        else:  # KEEP
            if rid not in rules_to_delete and rid not in rules_to_keep:
                rules_to_keep[rid] = row

    print()
    print(f"Group-by-ID summary (Rank Math rules, not rows):")
    print(f"  Unique rules in existing set: {len(rules_to_delete) + len(rules_to_keep)}")
    print(f"  Rules to DELETE: {len(rules_to_delete)}")
    print(f"  Rules to KEEP:   {len(rules_to_keep)}")

    print()
    print(f"Output CSV will contain:")
    print(f"  {len(rules_to_delete)} DELETE rows (one per rule, not per source)")
    print(f"  {len(new_plan)} new redirect rows")
    print(f"  Total: {len(rules_to_delete) + len(new_plan)}")
    print()
    print(f"End state after import:")
    print(f"  {len(rules_to_keep)} kept + {len(new_plan)} new = "
          f"{len(rules_to_keep) + len(new_plan)} active redirect rules")

    # Sanity: confirm no new-plan source URL collides with a kept-rule source
    kept_sources_normalized = set()
    for row, cat in categorized:
        if cat == "KEEP":
            kept_sources_normalized.add(
                row["source"].lstrip("/").rstrip("/").lower()
            )
    new_source_collisions = []
    for r in new_plan:
        ns = r["source"].lstrip("/").rstrip("/").lower()
        if ns in kept_sources_normalized:
            new_source_collisions.append(r)
    if new_source_collisions:
        print()
        print(f"WARNING: {len(new_source_collisions)} new-plan sources collide "
              f"with kept-rule sources. These would create duplicate redirects on import.")
        for r in new_source_collisions[:10]:
            print(f"    {r['source']} -> {r['destination']}")

    # Write the import CSV
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "source", "matching", "destination",
            "type", "category", "status", "ignore",
        ])

        # Section 1: Deletions — one row per RULE (not per source URL)
        for rid, row in rules_to_delete.items():
            writer.writerow([
                rid,            # ID of existing rule to delete
                row["source"],  # any source from the rule (Rank Math identifies by ID)
                "exact",
                "DELETE",       # case-sensitive deletion marker
                "301",
                "",
                "active",
                "",
            ])

        # Section 2: New migration redirects (empty ID = create new)
        for r in new_plan:
            src_relative = r["source"].lstrip("/")
            writer.writerow([
                "",                    # empty ID = create new
                src_relative,
                "exact",
                r["destination"],
                "301",
                "URL Migration 2026",  # category tag for traceability
                "active",
                "",
            ])

    print(f"\nSaved: {OUT_CSV}")

    # Verification pass: read the file back
    with open(OUT_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print()
    print(f"Verification of output file:")
    print(f"  Total rows: {len(rows)}")
    deletions = sum(1 for r in rows if r["destination"] == "DELETE")
    new_redirects = sum(1 for r in rows if r["destination"] != "DELETE")
    print(f"  DELETE rows: {deletions}")
    print(f"  NEW redirect rows: {new_redirects}")
    suspicious = [r for r in rows if r["id"] and r["destination"] != "DELETE"]
    print(f"  Suspicious (ID + non-DELETE, would be UPDATE): {len(suspicious)}")
    new_sources_in_csv = [
        r["source"] for r in rows if r["destination"] != "DELETE"
    ]
    dup_count = len(new_sources_in_csv) - len(set(new_sources_in_csv))
    print(f"  Duplicate sources in NEW section: {dup_count}")
    delete_ids = [r["id"] for r in rows if r["destination"] == "DELETE"]
    dup_delete = len(delete_ids) - len(set(delete_ids))
    print(f"  Duplicate IDs in DELETE section: {dup_delete}")


if __name__ == "__main__":
    main()
