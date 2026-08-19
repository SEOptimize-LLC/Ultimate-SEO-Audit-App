# Monthly SEO Workbook: credentials and setup

Everything here has cost a session at least once. Read it before debugging auth.

---

## Google (Sheets + Search Console)

**This is the working command. Nothing else works.**

```bash
gcloud auth application-default login \
  --client-id-file=credentials/oauth-client.json \
  --scopes="openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/webmasters.readonly"
```

Four ways this goes wrong, all of them seen:

**Plain `gcloud auth application-default login` grants only `cloud-platform`.**
Sheets then returns `403 ACCESS_TOKEN_SCOPE_INSUFFICIENT`. The scopes are not
optional.

**PowerShell splits the scope list at the commas** because comma is its array
operator, and gcloud receives one scope. It reports
`cloud-platform scope is required but not requested` while cloud-platform is
visibly in the command. **Quote the whole value.**

**Without `--client-id-file`, Google blocks the request** with "This app is
blocked. This app tried to access sensitive info in your Google Account."
Google's built-in gcloud client is not permitted to request Sheets scope. The
custom desktop OAuth client at `credentials/oauth-client.json` (project
`gsc-connector-460221`) is what makes it work.

**A browser page reading "You are now authenticated with the gcloud CLI!" is not
proof.** That page can be left over from an earlier `gcloud auth login` while
this command failed with `missing_code` on the localhost callback. Verify instead:

```bash
python -c "import sys;sys.path.insert(0,'scripts');import sheets_io as S;print(len(S.read('<sheet_id>','A1:A2')))"
```

### Why it expires so often

The credential is `authorized_user`, subject to the Workspace reauth policy on
`team@seoptimizellc.com`. It dies on a schedule regardless of recent use.

**A service account would be exempt, and this org blocks it.** The account
`sheets-workbook-writer@local-seo-473700.iam.gserviceaccount.com` exists, but key
creation is refused by the org policy `constraints/iam.disableServiceAccountKeyCreation`.
That is a sensible security control; do not try to route around it.

`sheets_io.service()` already prefers `credentials/sheets-service-account.json`
if a valid one ever appears, and falls back to ADC otherwise. It validates the
file's contents rather than its existence, because the blocked `keys create` call
still leaves an **empty file** behind, and an existence check sends every call
into a `JSONDecodeError` that names json instead of auth.

The durable fix is on the Workspace side: Admin console, Security, Access and
data control, Google Cloud session control.

---

## Bright Data (task 1.6)

`.env` holds `BRIGHTDATA_API_TOKEN`. `.env` is gitignored (line 56). Token
permission level `user` is sufficient; **do not grant `admin`** to a
never-expiring token stored in a file. `finance` is only needed to read billing
programmatically, which is a convenience, not a requirement.

Check the account before a run:

```bash
python scripts/brightdata.py
```

**Do not diagnose Bright Data by reading zones.** This account has zero zones and
`/status` reports `auth_fail_reason: zone_not_found`, yet every dataset scraper
works. Zones belong to the proxy products (Browser API, Web Unlocker, SERP API).
The dataset scrapers are billed per record and route through none of them. Only
the sync scrape endpoint is zone-backed, which is why it returns the misleading
`400 Customer is not active`.

---

## DataForSEO

`DATAFORSEO_LOGIN` and `DATAFORSEO_PASSWORD` in `.env`.

Beyond its normal uses, DFS is **the fallback fetcher for task 1.4**. It fetches
from its own addresses, so it reaches clients whose WAF refuses ours. See
`tasks/1.4.md` for the full chain.

---

## Console encoding on Windows

Sheet contents contain `→`, `·` and smart quotes, and the default cp1252 console
raises `UnicodeEncodeError` when printing them. Prefix reads with
`PYTHONIOENCODING=utf-8`.
