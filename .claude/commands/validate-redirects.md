---
description: Validate an implemented redirect map against the live site. Takes a redirect map CSV (or a client name and auto-discovers the map), runs scripts/validate_redirect_map.py, and reports per row whether each source URL actually lands on the approved target. Use after a developer or VA reports a redirect map deployed (Rule 12f), or any time the user asks "did the redirects get implemented correctly?"
---

# /validate-redirects

You are validating a shipped redirect map on behalf of the user. The user typed `/validate-redirects <map.csv path | client name> [base URL]` and expects you to find the map, run the validator, and translate the results into decisions. The user never runs the Python script themselves — that is your job.

## Step 1 — Resolve the redirect map CSV

The argument is whatever follows `/validate-redirects`.

**If the argument is a path to an existing CSV file:** use it directly.

**If the argument is a client name:** find the map in their folder. Glob in order, collecting all matches:

1. `Clients/<name>/**/*redirect*.csv`
2. `Clients/<name>/**/*rankmath*.csv`
3. `Clients/<name>/**/*migration*.csv`

If exactly one candidate: confirm it with the user by filename and proceed. If multiple: list them with full paths and ask which one is the shipped map. If none: tell the user no redirect map CSV was found in the client folder and ask for the path — do not guess.

**If no argument:** list `Clients/*` and ask which client, then follow the client-name path above.

## Step 2 — Inspect the CSV before running

Read the first 3 lines of the map (Read with `limit=3`).

1. **Column check.** The script auto-detects generic layouts ("Current URL"/"Target URL", "Source"/"Destination", "Old URL"/"New Target", etc.) and Rank Math exports (`source`/`matching`/`destination`). If the headers don't obviously contain a source column and a target column, identify the right two columns yourself from the header row and pass them explicitly via `--source-col` and `--target-col`. If you cannot tell which columns are which, show the user the header row and ask.
2. **Relative path check.** If source or target values are paths (`/old-page/`) rather than absolute URLs — always the case for Rank Math exports — the run needs `--base-url`. Take it from the command argument if given; otherwise infer the client's domain from the client folder and project memory and confirm it with the user in one line before running.

## Step 3 — Run the validator

Execute via Bash, saving both outputs next to the input map:

```bash
python scripts/validate_redirect_map.py \
    --input "<map path>" \
    [--base-url <https://domain.com>] \
    [--source-col "<col>" --target-col "<col>"] \
    --output "<map folder>/<map stem>_validation_<YYYY-MM-DD>.json" \
    --csv "<map folder>/<map stem>_validation_<YYYY-MM-DD>.csv"
```

Run in the foreground. Defaults (10 workers, 15s timeout, lenient trailing-slash and http/https matching) are correct for almost every run — only pass `--strict-slash` / `--strict-scheme` if the user explicitly asks for exact-state validation.

**Exit code 1 means FAIL rows exist, not that the script crashed.** A stderr summary line like `Summary: 40 PASS / 3 WARN / 2 FAIL` is a successful run. Only treat it as a script error if there is a traceback or no summary line.

**Retry transient failures before reporting them.** If any FAIL reasons are "Request timed out", "Fetch error", or a 5xx, write just those source→target rows to a temp CSV in the scratchpad and re-run with `--workers 3`. Use the re-run verdicts for those rows. A client server that rate-limits is not a broken redirect.

## Step 4 — Report the results

Read the JSON output and present, in this order:

1. **One-line verdict first.** "All N redirects land on their approved targets" or "X of N redirects are not implemented correctly."
2. **FAIL rows — every one, never truncated.** For each: full source URL, full expected target, full actual final URL (or status), and the reason in plain English. Full URLs always — the user copy/pastes these into tickets. If more than ~15 FAILs, group them by failure type (no redirect fired / wrong destination / target broken) and list every URL under its group.
3. **WARN rows, grouped by type:** 302-instead-of-301, multi-hop chains, noindex targets, self-referential rows. Explain once per group what the issue means and whether it needs dev action.
4. **Skipped-row stats** from the JSON (`skipped_rows`) if any are nonzero — say why rows were skipped (DELETE rows, regex rules, inactive, duplicates) so counts reconcile against the source file (Rule 10).
5. **Next actions.** FAILs reopen the implementation ticket with the CSV report attached. Point the user at the saved report files by full path.

Formatting rules apply as everywhere: no em dashes, no time estimates, tables max 6 columns, full URLs.

## What this command MUST NOT do

- Do not report a timeout or 5xx as a broken redirect without the Step 3 retry.
- Do not summarize FAILs as a count only — every failing source URL is listed in full.
- Do not interpret exit code 1 as a crash and re-run the whole map in a loop.
- Do not edit the redirect map or propose new targets from this command. If FAILs reveal the map itself was wrong (target now 404s), that goes back through Rule 12 verification (`scripts/verify_urls.py` / the live-url-verifier subagent) before anyone touches the map.
- Do not fabricate results if the script errors — surface the traceback and stop.

## Background

The validator and its logic (normalization toggles, trivial-hop chain analysis, Rank Math handling) are documented in the docstring of [scripts/validate_redirect_map.py](../../scripts/validate_redirect_map.py). The workflow rule this command enforces is Rule 12f in [.claude/rules/audit-workflow.md](../rules/audit-workflow.md).
