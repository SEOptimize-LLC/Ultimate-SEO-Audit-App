"""The whole monthly 1.6 run in one command.

    python scripts/monthly_1_6.py 2026-09          # all eight clients
    python scripts/monthly_1_6.py 2026-09 beehive  # one client

Per client: collect from ChatGPT, Google AI Mode and Perplexity via Bright Data
(prompts from clients/prompts/<client>.yaml, snapshot ids ledgered to
Clients/<folder>/ai_visibility/snapshots.log), then fill the 1.6 tab (sections
A, B, C, SOV header, month-over-month against last month's stored records).

Skips collection for any platform whose file for this stamp already exists, so
re-running after an interruption never re-pays for records already on disk. If
a run died between trigger and download, recover the records for free first:

    python -c "import sys; sys.path.insert(0,'scripts'); \\
        from brightdata import BrightData; \\
        print(BrightData().snapshot('<sd_... from snapshots.log>'))"

Prompt sets are FIXED between months by owner rule (tab row 2): section C
proposes swaps, the owner approves them, and only then does the YAML change.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from run_ai_visibility import run as collect  # noqa: E402
from fill_1_6_all import BRAND, fill  # noqa: E402

TRACKED = ("chatgpt", "google_ai_mode", "perplexity")


def main(stamp: str, only: str | None = None):
    reg = yaml.safe_load(Path("clients/registry.yaml").read_text(encoding="utf-8"))
    slugs = [only] if only else list(BRAND.keys())
    for slug in slugs:
        d = Path(reg[slug]["folder"]) / "ai_visibility"
        need = [p for p in TRACKED if not (d / f"{stamp}-{p}.json").exists()]
        if need:
            print(f"{slug}: collecting {', '.join(need)}", flush=True)
            collect(slug, tuple(need), stamp)
        else:
            print(f"{slug}: all {stamp} records already on disk, "
                  f"skipping collection", flush=True)
        fill(slug, stamp)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
