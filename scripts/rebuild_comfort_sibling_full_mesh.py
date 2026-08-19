"""Rebuild the Comfort link-map sibling mesh as a full mesh.

Prior build linked every same-family sibling plus only the first 3 cross-family
pages, which left Traditional Gas Fireplaces with 3 inbound links while
Fireplace Repair had 10 -- an artifact of alphabetical sort, not a decision.
Owner decision 2026-08-18: furnace and fireplace pages cross-link both ways,
so every service page links to every other service page in its own city.
"""
import copy
import shutil
from pathlib import Path

import openpyxl

BOOK = Path("Clients/Comfort/Full SEO Audit/Comfort Solutions - City to Service Page Link Map.xlsx")
BRAND_FONT = "Red Hat Display"


def family(topic: str) -> str:
    t = topic.lower()
    if "fireplace" in t:
        return "1_fireplace" if "fireplace" in t else "z"
    if "furnace" in t or "heating" in t:
        return "2_furnace"
    if "hvac" in t:
        return "4_hvac"
    if t.startswith("ac ") or "air conditioning" in t or "air conditioner" in t:
        return "3_cooling"
    return "5_other"


def order_key(fam_self, page):
    """Same family first, then HVAC as the bridge, then the rest. Alpha inside."""
    fam = page["family"]
    if fam == fam_self:
        bucket = 0
    elif fam == "4_hvac":
        bucket = 1
    else:
        bucket = 2
    return (bucket, fam, page["topic"])


def main():
    wb = openpyxl.load_workbook(BOOK)
    mesh = wb["Sibling Link Mesh"]
    dev = wb["Dev Action List"]

    # ---- 1. inventory every service page from the existing mesh tab ----
    pages = []
    for row in mesh.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        pages.append({
            "city": row[0],
            "url": row[1],
            "topic": row[2],
            "heading": row[6],
            "builder": row[7],
            "family": family(row[2]),
        })

    by_city = {}
    for p in pages:
        by_city.setdefault(p["city"], []).append(p)

    # ---- 2. preserve any "already linked" statuses from the current P3 rows ----
    dev_rows = [list(r) for r in dev.iter_rows(min_row=2, values_only=True)]
    known_status = {
        (r[1], r[2]): r[6]
        for r in dev_rows
        if r[0] == "P3" and r[6] and not str(r[6]).startswith("ADD")
    }

    # ---- 3. build the full mesh ----
    mesh_rows, p3_rows = [], []
    for city in sorted(by_city):
        group = sorted(by_city[city], key=lambda p: p["topic"])
        for page in group:
            sibs = [s for s in group if s["url"] != page["url"]]
            sibs.sort(key=lambda s: order_key(page["family"], s))
            mesh_rows.append([
                city,
                page["url"],
                page["topic"],
                "\n".join(s["url"] for s in sibs),
                "\n".join(s["topic"] for s in sibs),
                len(sibs),
                page["heading"],
                page["builder"],
            ])
            for s in sibs:
                p3_rows.append([
                    "P3", page["url"], s["url"], s["topic"], page["builder"],
                    f'Module at the end of the page, heading "{page["heading"]}"',
                    known_status.get((page["url"], s["url"]),
                                     "ADD, no sibling links exist on this page"),
                ])

    # ---- 4. rewrite both tabs, cloning style from the first data row ----
    def rewrite(ws, new_rows, ncols):
        template = [copy.copy(ws.cell(2, c)._style) for c in range(1, ncols + 1)]
        ws.delete_rows(2, ws.max_row)
        for i, data in enumerate(new_rows, start=2):
            for c, value in enumerate(data, start=1):
                cell = ws.cell(i, c, value)
                cell._style = copy.copy(template[c - 1])

    rewrite(mesh, mesh_rows, 8)

    keep_before = [r for r in dev_rows if r[0] in ("P1", "P2")]
    keep_after = [r for r in dev_rows if r[0] == "P4"]
    rewrite(dev, keep_before + p3_rows + keep_after, 7)

    # ---- 5. brand font, applied through the shared font table ----
    for f in wb._fonts:
        f.name = BRAND_FONT
    for st in getattr(wb, "_named_styles", []):
        if getattr(st, "font", None) is not None:
            st.font.name = BRAND_FONT

    wb.save(BOOK)

    print(f"Sibling Link Mesh: {len(mesh_rows)} pages")
    print(f"Dev Action List P3: 205 -> {len(p3_rows)} rows "
          f"(total {len(keep_before) + len(p3_rows) + len(keep_after)})")
    for city in sorted(by_city):
        n = len(by_city[city])
        print(f"  {city}: {n} pages, {n - 1} links each")


if __name__ == "__main__":
    main()
