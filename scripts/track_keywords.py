"""Task 2.3/2.4/3.1 step 9 - SEMrush Position Tracking, scripted.

    python scripts/track_keywords.py <client> [--tag aug-2026] [--dry-run]

Reads clients/registry.yaml (semrush_campaign) and the client's plan.yaml
(per-target `track:` keyword lists), then against the SEMrush Projects API:

  1. PUT /projects/{campaign}/keywords - adds every tracked keyword with the
     month tag (SEMrush merges keywords that already exist; 100 API units
     per keyword).
  2. PUT /projects/{campaign}/tags - applies the tag across the full list
     and RETURNS the campaign's keyword+tag state, which doubles as the
     verification read (100 API units per request).

Prints a per-keyword verification table. The N column on the Refresh Log is
filled from this output - tag + keywords + verified date - by fill or by
hand. The API key is read from the SEMrush MCP entry in ~/.claude.json and
is never printed.

Exists because the SOP makes Position Tracking the owner's step; this
script makes it a command instead of a UI chore (first run 2026-08-21, EW).
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import yaml

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent


def semrush_key() -> str:
    cfg = json.load(open(Path.home() / ".claude.json", encoding="utf-8"))
    out = []

    def find(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if str(k).lower() == "semrush" and isinstance(v, dict):
                    out.append(v["headers"]["Authorization"].split()[-1])
                else:
                    find(v)

    find(cfg)
    if not out:
        raise SystemExit("no SEMrush key found in ~/.claude.json mcpServers")
    return out[0]


def api(method: str, url: str, body=None):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode() if body is not None else None,
        method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:200]}")
        return None


def main(slug: str, tag: str, dry: bool) -> None:
    reg = yaml.safe_load((ROOT / "clients/registry.yaml").read_text(encoding="utf-8"))
    cfg = reg[slug]
    camp = cfg.get("semrush_campaign")
    if not camp:
        raise SystemExit(f"{slug}: no semrush_campaign in registry.yaml")
    plan = yaml.safe_load(
        (ROOT / cfg["folder"] / "monthly_plan/plan.yaml").read_text(encoding="utf-8"))
    kws: list[str] = []
    for t in plan["targets"]:
        for k in t.get("track") or []:
            if k not in kws:
                kws.append(k)
    if not kws:
        raise SystemExit(f"{slug}: no track: lists in plan.yaml targets")
    print(f"{cfg['name']} - campaign {camp} - {len(kws)} keyword(s), tag {tag}")
    if dry:
        for k in kws:
            print("  would track:", k)
        return
    key = semrush_key()
    api("PUT", f"https://api.semrush.com/management/v1/projects/{camp}/keywords?key={key}",
        {"keywords": [{"keyword": k, "tags": [tag]} for k in kws]})
    r = api("PUT", f"https://api.semrush.com/management/v1/projects/{camp}/tags?key={key}",
            [{"tag": tag, "keywords": kws}])
    state = {k.get("keyword", "").lower(): k.get("tags") or []
             for k in (r or {}).get("keywords", [])}
    ok = 0
    for k in kws:
        tags = state.get(k.lower())
        good = tags is not None and tag in tags
        ok += good
        print(f"  {'OK ' if good else '!! '}{k}")
    print(f"  -> {ok}/{len(kws)} tracked with tag {tag}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tag = "aug-2026"
    for a in sys.argv[1:]:
        if a.startswith("--tag"):
            tag = a.split("=", 1)[1] if "=" in a else "aug-2026"
    main(args[0], tag, "--dry-run" in sys.argv)
