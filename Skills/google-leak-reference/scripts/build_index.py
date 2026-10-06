"""Build a queryable SQLite index of the google_api_content_warehouse Hex package.

Primary source: the package tarballs on repo.hex.pm (the same source hexdocs is
generated from). Every version is indexed so the 0.2.0-0.4.0 content that was
later stripped can be diffed against what remains.

    python scripts/build_index.py            # download (cached) + parse + write data/leak.sqlite
    python scripts/build_index.py --offline  # parse cached tarballs only

Tables
    modules(version, module, moduledoc, file)
    attributes(version, module, attr, type, default_val, description)
    edges(version, src_module, attr, dst_module)   -- attribute type -> another Model module
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sqlite3
import sys
import tarfile
import urllib.request
from pathlib import Path

PACKAGE = "google_api_content_warehouse"
VERSIONS = ["0.2.0", "0.3.0", "0.4.0", "0.5.0", "0.6.0", "0.6.1"]
TARBALL_URL = "https://repo.hex.pm/tarballs/{pkg}-{ver}.tar"
MODEL_PREFIX = "GoogleApi.ContentWarehouse.V1.Model."

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "leak.sqlite"
SUMMARIES = ROOT / "summaries" / "module_summaries.jsonl"
CLAIMS = ROOT / "commentary" / "claims.jsonl"

MODULE_RE = re.compile(r"defmodule\s+(GoogleApi\.ContentWarehouse\.[\w.]+)\s+do")
ATTR_RE = re.compile(
    r"^\s{2}\*\s{3}`(?P<name>\w+)`\s+\(\*type:\*\s+`(?P<type>.*?)`,\s+\*default:\*\s+`(?P<default>.*?)`\)\s*-?\s*(?P<desc>.*)$"
)
MODEL_REF_RE = re.compile(r"GoogleApi\.ContentWarehouse\.V1\.Model\.(\w+)")


def fetch(version: str, offline: bool) -> bytes:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{PACKAGE}-{version}.tar"
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    if offline:
        raise FileNotFoundError(f"{path} missing and --offline set")
    url = TARBALL_URL.format(pkg=PACKAGE, ver=version)
    with urllib.request.urlopen(url, timeout=60) as resp:
        if resp.status != 200:
            raise RuntimeError(f"{url} returned {resp.status}")
        data = resp.read()
    path.write_bytes(data)
    return data


def contents_files(tarball: bytes):
    """Yield (relative path, text) for every .ex file inside the package's contents.tar.gz."""
    with tarfile.open(fileobj=io.BytesIO(tarball)) as outer:
        member = outer.extractfile("contents.tar.gz")
        if member is None:
            raise RuntimeError("contents.tar.gz not found in tarball")
        with tarfile.open(fileobj=io.BytesIO(member.read()), mode="r:gz") as inner:
            for info in inner.getmembers():
                if info.isfile() and info.name.endswith(".ex"):
                    f = inner.extractfile(info)
                    if f is not None:
                        yield info.name, f.read().decode("utf-8", "replace")


def parse_module(text: str):
    """Return (module, moduledoc, [(attr, type, default, desc)]) or None."""
    m = MODULE_RE.search(text)
    if not m:
        return None
    module = m.group(1)

    doc_match = re.search(r'@moduledoc\s+"""\n(.*?)\n\s*"""', text, re.S)
    doc = doc_match.group(1) if doc_match else ""
    # moduledoc proper = text before "## Attributes"
    head, _, attr_block = doc.partition("## Attributes")
    moduledoc = "\n".join(line[2:] if line.startswith("  ") else line for line in head.strip().splitlines()).strip()

    attrs = []
    current = None
    for line in attr_block.splitlines():
        am = ATTR_RE.match(line)
        if am:
            if current:
                attrs.append(current)
            current = [am["name"], am["type"], am["default"], am["desc"].strip()]
        elif current is not None and line.strip():
            current[3] = (current[3] + " " + line.strip()).strip()
    if current:
        attrs.append(current)
    return module, moduledoc, [tuple(a) for a in attrs]


def build(offline: bool) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE modules(version TEXT, module TEXT, moduledoc TEXT, file TEXT);
        CREATE TABLE attributes(version TEXT, module TEXT, attr TEXT, type TEXT, default_val TEXT, description TEXT);
        CREATE TABLE edges(version TEXT, src_module TEXT, attr TEXT, dst_module TEXT);
        CREATE INDEX ix_mod ON modules(version, module);
        CREATE INDEX ix_attr ON attributes(version, module);
        CREATE INDEX ix_attr_name ON attributes(attr);
        CREATE INDEX ix_edge_src ON edges(version, src_module);
        CREATE INDEX ix_edge_dst ON edges(version, dst_module);
        """
    )
    for version in VERSIONS:
        tarball = fetch(version, offline)
        n_mod = n_attr = n_edge = 0
        for name, text in contents_files(tarball):
            parsed = parse_module(text)
            if not parsed:
                continue
            module, moduledoc, attrs = parsed
            db.execute("INSERT INTO modules VALUES (?,?,?,?)", (version, module, moduledoc, name))
            n_mod += 1
            for attr, typ, default, desc in attrs:
                db.execute("INSERT INTO attributes VALUES (?,?,?,?,?,?)", (version, module, attr, typ, default, desc))
                n_attr += 1
                for dst in sorted(set(MODEL_REF_RE.findall(typ))):
                    db.execute("INSERT INTO edges VALUES (?,?,?,?)", (version, module, attr, MODEL_PREFIX + dst))
                    n_edge += 1
        print(f"{version}: {n_mod} modules, {n_attr} attributes, {n_edge} edges")
    load_summaries(db)
    load_claims(db)
    db.commit()
    db.close()
    print(f"wrote {DB_PATH}")


def load_summaries(db: sqlite3.Connection) -> None:
    """Load the committed module summaries (written by merge_summaries.py), if present."""
    db.execute("CREATE TABLE summaries(module TEXT PRIMARY KEY, summary TEXT, seo TEXT, why TEXT)")
    if not SUMMARIES.exists():
        print("summaries: none found (run merge_summaries.py to add them)")
        return
    n = 0
    for line in SUMMARIES.read_text(encoding="utf-8").splitlines():
        if line.strip():
            o = json.loads(line)
            db.execute("INSERT INTO summaries VALUES (?,?,?,?)", (o["module"], o["summary"], o["seo"], o["why"]))
            n += 1
    print(f"summaries: {n} loaded")




def load_claims(db: sqlite3.Connection) -> None:
    """Load graded third-party commentary (written by build_commentary.py), if present."""
    db.execute("CREATE TABLE claims(id TEXT PRIMARY KEY, source TEXT, names TEXT, name_check TEXT, "
               "claim TEXT, class TEXT, call TEXT, reason TEXT)")
    if not CLAIMS.exists():
        print("claims: none found (run build_commentary.py to add them)")
        return
    n = 0
    for line in CLAIMS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            o = json.loads(line)
            db.execute("INSERT INTO claims VALUES (?,?,?,?,?,?,?,?)",
                       (o["id"], o["source"], " ".join(o["names"]), o["name_check"], o["claim"],
                        o["class"], o["call"], o["reason"]))
            n += 1
    print(f"claims: {n} loaded")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="use cached tarballs only")
    args = ap.parse_args()
    try:
        build(args.offline)
    except Exception as exc:  # fail loud: a half-built index is worse than none
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
