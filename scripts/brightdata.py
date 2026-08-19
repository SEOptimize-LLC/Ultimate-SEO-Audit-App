"""Bright Data API client for task 1.6 (AI visibility).

Auth is a single bearer token from Account Settings > API tokens, kept in .env
as BRIGHTDATA_API_TOKEN. The token is never printed, logged, or written into a
deliverable; .env is gitignored (.gitignore line 56).

    from brightdata import BrightData
    bd = BrightData()
    bd.scrapers()                       # discover dataset ids on this account
    bd.ai_query("chatgpt", "best classroom walkthrough software")

Docs verified 2026-08-18:
  https://docs.brightdata.com/api-reference/authentication
  https://docs.brightdata.com/api-reference/scrapers/synchronous-requests
  https://docs.brightdata.com/datasets/scrapers/chatgpt/introduction
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://api.brightdata.com"

# Read from this account on 2026-08-18 via scrapers(), not guessed. The ChatGPT
# id matches the one published in the docs, which cross-checks the discovery.
# There is NO Claude scraper on Bright Data, and DataForSEO has no Google AI Mode
# or Copilot. Neither provider covers what tab 1.6 asks for on its own.
KNOWN = {
    "chatgpt": "gd_m7aof0k82r803d5bjm",        # ChatGPT Search
    "perplexity": "gd_m7dhdot1vw9a7gc1n",      # Perplexity Search
    "gemini": "gd_mbz66arm2mf9cu856y",         # Gemini Search
    "google_ai_mode": "gd_mcswdt6z2elth3zqr2",  # Google AI Mode Search
    "copilot": "gd_m7di5jy6s9geokz8w",         # Bing Copilot Search
}

# Where each platform can be measured. Claude is DataForSEO only; AI Mode and
# Copilot are Bright Data only. Recorded here so a tab never claims coverage of
# a platform that was never actually queried.
COVERAGE = {
    "chatgpt": ("brightdata", "dataforseo"),
    "perplexity": ("brightdata", "dataforseo"),
    "gemini": ("brightdata", "dataforseo"),
    "claude": ("dataforseo",),
    "google_ai_mode": ("brightdata",),
    "copilot": ("brightdata",),
}

# Owner rule, 2026-08-18: AI visibility is measured from the US unless a task
# explicitly calls for a local view. It is a real variable, not a formality -
# the same prompt returns different brands and different citations by country,
# so an unset country would let the origin drift between months and turn a
# share-of-voice trend into noise. A local run is opt-in per call, never the
# default, and whatever was used gets stated on the tab.
DEFAULT_COUNTRY = "US"

BROWSE_CONTROL = {"chatgpt": True, "grok": True, "perplexity": False,
                  "gemini": False, "google_ai_mode": False, "copilot": False}


class BrightDataError(RuntimeError):
    pass


def _token() -> str:
    tok = os.environ.get("BRIGHTDATA_API_TOKEN", "").strip()
    if not tok:
        env = Path(".env")
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("BRIGHTDATA_API_TOKEN="):
                    tok = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not tok:
        raise BrightDataError(
            "BRIGHTDATA_API_TOKEN is empty. Add it to .env from Bright Data "
            "Account Settings > API tokens. Nothing here runs without it.")
    return tok


class BrightData:
    def __init__(self, token: str | None = None, timeout: int = 90):
        self._tok = token or _token()
        self.timeout = timeout

    def _req(self, method: str, path: str, body=None):
        url = path if path.startswith("http") else f"{BASE}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self._tok}",
            "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode("utf-8", "replace")
                try:
                    return r.status, json.loads(raw or "null")
                except json.JSONDecodeError:
                    return r.status, raw
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            # Never echo the token back inside an error string.
            raise BrightDataError(f"{method} {path} -> HTTP {e.code}: {detail}") from None

    def preflight(self) -> dict:
        """Whether this account can actually run a scrape.

        Do NOT test this by reading zones. Measured 2026-08-18: this account has
        zero zones and /status reports auth_fail_reason "zone_not_found", yet
        the dataset scrapers run perfectly. Zones belong to the proxy products
        (Browser API, Web Unlocker, SERP API); the dataset scrapers are billed
        per record and route through none of them. Reading zone state cost an
        afternoon of the owner configuring proxy products we never needed.

        The sync endpoint /datasets/v3/scrape IS zone-backed, which is why it
        returns 400 "Customer is not active" here. Async trigger is the path.
        """
        _, st = self._req("GET", "/status")
        ok = str(st.get("status")) == "active"
        return {"ready": ok, "status": st.get("status"),
                "customer": st.get("customer"),
                "note": "async trigger path; zone state is irrelevant here",
                "advice": "" if ok else "Account is not active. Check billing."}

    def scrapers(self) -> list[dict]:
        """Every scraper on this account, so dataset ids are read, not guessed."""
        _, body = self._req("GET", "/datasets/v3/scrapers")
        if isinstance(body, list):
            return body
        return (body or {}).get("scrapers", []) if isinstance(body, dict) else []

    def dataset_id(self, platform: str) -> str:
        p = platform.lower().replace("-", "_")
        if p in KNOWN:
            return KNOWN[p]
        want = p.replace("_", " ")
        for s in self.scrapers():
            name = str(s.get("name", "")).lower()
            if want in name:
                got = s.get("id") or s.get("dataset_id")
                if got:
                    return got
        raise BrightDataError(
            f"No dataset id found for {platform!r}. Run scrapers() to list what "
            f"this account has, then add it to KNOWN.")

    def scrape(self, dataset_id: str, inputs: list[dict], fmt: str = "json"):
        """Run inputs and return records, via the async trigger path.

        Async is not an optimisation here, it is the only path that works: the
        sync endpoint is zone-backed and 400s on this account. It is also the
        right shape for the real workload. A single ChatGPT prompt took 110s
        end to end, and a monthly run is 8 clients times ~10 prompts times
        several platforms, so sync would time out into a snapshot id on nearly
        every batch anyway.

        Note the payload: trigger takes a BARE list, not {"input": [...]}.
        """
        _, body = self._req(
            "POST", f"/datasets/v3/trigger?dataset_id={dataset_id}&format={fmt}",
            inputs)
        sid = (body or {}).get("snapshot_id") if isinstance(body, dict) else None
        if not sid:
            raise BrightDataError(f"trigger returned no snapshot_id: {str(body)[:200]}")
        return self.snapshot(sid)

    def snapshot(self, snapshot_id: str, tries: int = 30, pause: int = 10):
        for _ in range(tries):
            st, body = self._req("GET",
                                 f"/datasets/v3/snapshot/{snapshot_id}?format=json")
            running = isinstance(body, dict) and body.get("status") in (
                "running", "building", "collecting")
            if st == 200 and body and not running:
                return body if isinstance(body, list) else [body]
            time.sleep(pause)
        raise BrightDataError(
            f"snapshot {snapshot_id} not ready after {tries * pause}s")

    def ai_query(self, platform: str, prompt: str, web_search: bool | None = None,
                 country: str = DEFAULT_COUNTRY) -> list[dict]:
        """One prompt against one AI platform.

        Runs from the US by default. web_search is only sent where the platform
        actually supports it: asking Gemini to browse is ignored by the API, and
        sending it anyway would put an unsupported methodology claim on the tab.
        """
        row: dict = {"prompt": prompt}
        if platform.lower() == "chatgpt":
            row["url"] = "https://chatgpt.com/"
        if web_search is not None and BROWSE_CONTROL.get(platform.lower()):
            row["web_search"] = web_search
        if country:
            row["country"] = country
        out = self.scrape(self.dataset_id(platform), [row])
        return out if isinstance(out, list) else [out]


if __name__ == "__main__":
    try:
        bd = BrightData()
    except BrightDataError as e:
        raise SystemExit(f"NOT CONFIGURED: {e}")
    print(f"token loaded ({len(bd._tok)} chars)")
    pf = bd.preflight()
    print(f"ready={pf['ready']}  status={pf['status']}  {pf['note']}")
    if pf["advice"]:
        print("  ->", pf["advice"])
    try:
        found = bd.scrapers()
        print(f"scrapers visible on this account: {len(found)}")
        for s in found[:40]:
            print("  ", s.get("id") or s.get("dataset_id"), "-", s.get("name"))
    except BrightDataError as e:
        print("scraper discovery failed:", e)
