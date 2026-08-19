"""Task 1.6: run a client prompt set against the AI platforms and log the answers.

    python scripts/run_ai_visibility.py educationwalkthrough
    python scripts/run_ai_visibility.py educationwalkthrough --platforms chatgpt

Prompts come from clients/prompts/<client>.yaml, which carries the GSC query and
impressions each prompt was derived from. Raw responses land in
Clients/<folder>/ai_visibility/<date>-<platform>.json and are never overwritten,
because the whole point of the tab is a month-over-month comparison and a
clobbered baseline cannot be rebuilt.

Browsing is NOT forced. The platforms decide, and whatever they did is recorded
from web_search_triggered where the platform reports it. Forcing browse is what
made the July 2026 tool comparison over-report: a browse-forced harness finds
the brand in answers a real user session never sees.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from brightdata import BrightData, BrightDataError, KNOWN  # noqa: E402

PLATFORM_URL = {
    "chatgpt": "https://chatgpt.com/",
    "perplexity": "https://www.perplexity.ai",
    "gemini": "https://gemini.google.com/",
    "google_ai_mode": "https://www.google.com/",
    "copilot": "https://copilot.microsoft.com/",
}
DEFAULT_PLATFORMS = ("chatgpt", "perplexity", "gemini")


def load(client: str) -> dict:
    p = Path("clients/prompts") / f"{client}.yaml"
    if not p.exists():
        raise SystemExit(f"No prompt set at {p}. Build it from GSC first.")
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def outdir(client: str) -> Path:
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    # registry folder values already start with "Clients/", so joining another
    # "Clients" onto the front produced Clients/Clients/<name>.
    folder = reg[client].get("folder") or f"Clients/{client}"
    d = Path(folder) / "ai_visibility"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run(client: str, platforms=DEFAULT_PLATFORMS, stamp: str | None = None):
    doc = load(client)
    prompts = doc["prompts"]
    country = doc.get("country", "US")
    bd = BrightData(timeout=90)
    d = outdir(client)
    stamp = stamp or "run"

    # Fire every platform first, then poll. Triggering is instant and the jobs
    # run concurrently on their side, so serialising the polls would add the
    # full runtime of each platform to the total for no reason.
    jobs = {}
    for plat in platforms:
        rows = [{"url": PLATFORM_URL[plat], "prompt": p["prompt"],
                 "country": country} for p in prompts]
        _, body = bd._req(
            "POST", f"/datasets/v3/trigger?dataset_id={KNOWN[plat]}&format=json", rows)
        sid = (body or {}).get("snapshot_id")
        jobs[plat] = sid
        # Ledger every snapshot id to disk AT TRIGGER TIME. Bright Data keeps
        # completed snapshots server-side, so if this process dies mid-run the
        # records are recovered by re-polling the id for free instead of paying
        # to re-trigger. The 2026-08-18 session crash cost nothing for the five
        # clients whose ids were in the console scrollback, and one re-trigger
        # for the client whose run had not started; this file removes the
        # dependence on scrollback surviving.
        with open(d / "snapshots.log", "a", encoding="utf-8") as fh:
            fh.write("%s\t%s\t%s\n" % (stamp, plat, sid))
        print(f"{plat:<14} triggered {len(rows)} prompts -> {sid}", flush=True)

    for plat, sid in jobs.items():
        if not sid:
            print(f"{plat:<14} NO SNAPSHOT, skipped", flush=True)
            continue
        t0 = time.time()
        try:
            recs = bd.snapshot(sid, tries=90, pause=20)
        except BrightDataError as e:
            print(f"{plat:<14} FAILED {e}", flush=True)
            continue
        f = d / f"{stamp}-{plat}.json"
        f.write_text(json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
        ok = sum(1 for r in recs if isinstance(r, dict) and r.get("answer_text"))
        print(f"{plat:<14} {len(recs)} records ({ok} with answers) in "
              f"{time.time()-t0:.0f}s -> {f}", flush=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    plats = DEFAULT_PLATFORMS
    if "--platforms" in sys.argv:
        plats = tuple(sys.argv[sys.argv.index("--platforms") + 1].split(","))
    stamp = None
    if "--stamp" in sys.argv:
        stamp = sys.argv[sys.argv.index("--stamp") + 1]
    run(args[0], plats, stamp)
