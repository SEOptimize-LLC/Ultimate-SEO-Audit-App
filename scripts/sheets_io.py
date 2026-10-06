"""Google Sheets read/write for the Monthly SEO Workbook.

Authenticates with Application Default Credentials (see credentials/ setup in
docs/superpowers/specs/2026-08-14-monthly-seo-workbook-design.md).

The contract this module exists to enforce: a write is never reported as
successful until the range has been read back and matched. Everything else here
is guardrails around that.
"""

from __future__ import annotations

import re
import pathlib
from dataclasses import dataclass, field

import google.auth
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Ranges that must never be written, whatever a recipe claims. 4.5 column C
# holds the auto-count formulas; overwriting one with a literal would silently
# turn a live count into a frozen number nobody notices.
DENY_PATTERNS = [
    re.compile(r"^'?4\.5 Template Report'?!C", re.I),
]

_service = None


# A service account key here wins over ADC, and that is the point. ADC on this
# machine is an authorized_user credential belonging to team@seoptimizellc.com,
# so it is subject to the Workspace reauth policy and dies on a fixed schedule
# regardless of how recently anyone logged in. That failure lands mid-run, which
# is the worst possible time: some tabs written, others not. A service account
# key is exempt from user session controls and does not expire.
#
# Each workbook must be shared with the service account address as Editor, or
# every call returns 404 rather than a permission error, because the account
# genuinely cannot see a file nobody shared with it.
SA_KEY = "credentials/sheets-service-account.json"

# Minted by scripts/auth_sheets.py. This is the credential that actually works
# here; see the note in service() for why the other two do not.
OAUTH_TOKEN = "credentials/sheets-token.json"


def reset() -> None:
    """Drop the cached client so a newly minted token is picked up."""
    global _service
    _service = None


def service():
    """Cached Sheets client.

    Credential order, most durable first:

    1. Service account key. Never expires, no human in the loop. Currently
       unavailable here: org policy blocks key creation and this account has no
       organization IAM permission to change that.
    2. Our own OAuth token at credentials/sheets-token.json, minted by
       scripts/auth_sheets.py. This is the one that actually works. Same
       pattern the Search Console scripts use.
    3. Application Default Credentials. Left last on purpose. ADC is a user
       credential and this Workspace enforces Google Cloud session control, so
       it dies on a timer, and re-consenting it for Sheets scopes is refused
       outright with "This app is blocked".
    """
    global _service
    if _service is None:
        # Validity, not existence. A blocked `gcloud ... keys create` still
        # creates the output file and leaves it empty, so an existence check
        # sends every call into a JSONDecodeError instead of falling through,
        # and the error names json rather than auth.
        creds = None
        try:
            import json
            info = json.loads(pathlib.Path(SA_KEY).read_text(encoding="utf-8"))
            if info.get("client_email") and info.get("token_uri"):
                from google.oauth2 import service_account
                creds = service_account.Credentials.from_service_account_info(
                    info, scopes=SCOPES)
        except (OSError, ValueError):
            creds = None

        if creds is None:
            try:
                import json
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                tok = pathlib.Path(OAUTH_TOKEN)
                info = json.loads(tok.read_text(encoding="utf-8"))
                c = Credentials.from_authorized_user_info(info)
                if not c.valid and c.expired and c.refresh_token:
                    c.refresh(Request())
                    tok.write_text(c.to_json(), encoding="utf-8")
                if c.valid:
                    creds = c
            except (OSError, ValueError, KeyError):
                creds = None

        if creds is None:
            creds, _ = google.auth.default(scopes=SCOPES)
        _service = build("sheets", "v4", credentials=creds,
                         cache_discovery=False)
    return _service


def _values():
    return service().spreadsheets().values()


def _call(req, tries: int = 5):
    """Execute a Sheets request, backing off on rate limits.

    Sheets allows 60 reads and 60 writes per minute per user. A batch across
    eight workbooks blows through that, and the failure is a 429 mid-run that
    leaves some tabs written and others not. Retrying is the difference between
    a slow run and a half-finished one.
    """
    import random
    import socket
    import ssl
    import time
    from googleapiclient.errors import HttpError

    for attempt in range(tries):
        try:
            return req.execute()
        except HttpError as e:
            transient = e.resp.status in (429, 500, 502, 503)
            if not transient or attempt == tries - 1:
                raise
            time.sleep(min(2 ** attempt, 30) + random.random())
        except (TimeoutError, socket.timeout, ssl.SSLError, ConnectionError, OSError):
            # Socket-level failures are transient network state, not API
            # verdicts, and they are NOT HttpError, so the branch above never
            # sees them. Before this branch existed, a single TLS read timeout
            # killed an eight-workbook run halfway through (2026-08-18), which
            # is the worst outcome: some tabs written, others not, and the
            # console blaming an "API error" that was really a dropped socket.
            if attempt == tries - 1:
                raise
            time.sleep(min(2 ** attempt, 30) + random.random())


# --- read -------------------------------------------------------------------

def read(sheet_id: str, a1: str) -> list[list]:
    """Return the range as a list of rows. Trailing empty cells are not padded."""
    resp = _call(_values().get(spreadsheetId=sheet_id, range=a1))
    return resp.get("values", [])


def tab_names(sheet_id: str) -> list[str]:
    meta = _call(service().spreadsheets().get(
        spreadsheetId=sheet_id, fields="sheets.properties.title"))
    return [s["properties"]["title"] for s in meta["sheets"]]


# --- layout guard -----------------------------------------------------------

@dataclass
class LayoutCheck:
    ok: bool
    expected: list[str]
    found: list[str]
    detail: str = ""


def check_layout(sheet_id: str, header_a1: str, expected: list[str]) -> LayoutCheck:
    """Confirm a tab still looks how the recipe expects before writing to it.

    Eight workbooks were created from one import so they agree today, but a
    client sheet can drift once people edit it, and a stale range would put good
    data in the wrong cells.
    """
    rows = read(sheet_id, header_a1)
    found = [str(c).strip() for c in (rows[0] if rows else [])]
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    ok = [norm(x) for x in found[:len(expected)]] == [norm(x) for x in expected]
    return LayoutCheck(
        ok=ok, expected=expected, found=found,
        detail="" if ok else f"header mismatch at {header_a1}")


# --- write ------------------------------------------------------------------

class WriteRefused(RuntimeError):
    """Raised before any API call when a write violates a guardrail."""


class WriteUnverified(RuntimeError):
    """Raised when the read-back does not match what was sent."""


@dataclass
class WriteResult:
    a1: str
    cells: int
    verified: bool
    mismatches: list[tuple] = field(default_factory=list)


def _norm_cell(v) -> str:
    """Compare loosely: Sheets echoes numbers/dates in its own display form."""
    if v is None:
        return ""
    s = str(v).strip()
    try:
        f = float(s.replace(",", ""))
        return f"{f:g}"
    except ValueError:
        return s.lower()


BULLET = "•"
CELL_MAX = 950          # characters. Past this nobody reads the cell.
LABEL_MAX = 34          # an uppercase label is a label, not a sentence.

_MD = re.compile(r"\*\*|__|`")
_BULLET_LINE = re.compile(r"^\s*[-*]\s+")
# A label may carry a lowercase parenthetical tail: "AI PROMPT (absent on 2)".
_LABEL_LINE = re.compile(r"^[A-Z0-9][A-Z0-9 ,'/&–-]{2,}(\([^)]*\))?$")


def cell(text: str) -> str:
    """House format for a multi-line sheet cell. Mechanical, idempotent.

    Sheets renders no markdown, so `**bold**` arrives as literal asterisks.
    What reads is a short uppercase label, a blank line, then bullets.

    This exists because the format was written into five task files and
    enforced by nothing, so it decayed back to a wall of text every month.
    Prose that says "format it nicely" is not a mechanism; this is.
    """
    s = _MD.sub("", str(text or "")).replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    for raw in s.split("\n"):
        ln = raw.rstrip()
        if _BULLET_LINE.match(ln):
            ln = _BULLET_LINE.sub(f"{BULLET} ", ln.lstrip())
        # A bulleted line that is really a label reads as a stray bullet.
        # Promote it back so the verdict still sits above its detail.
        body = ln.strip().lstrip(BULLET).strip()
        if ln.strip().startswith(BULLET) and _LABEL_LINE.match(body):
            ln = body
        stripped = ln.strip()
        # A label gets air above it so the verdict reads before the detail.
        if stripped and _LABEL_LINE.match(stripped) and out and out[-1].strip():
            out.append("")
        out.append(ln)
    # Never more than one blank line in a row.
    tidy: list[str] = []
    for ln in out:
        if not ln.strip() and tidy and not tidy[-1].strip():
            continue
        tidy.append(ln)
    return "\n".join(tidy).strip()


def sentences(text: str) -> list[str]:
    """Split prose into one sentence per bullet. A dot between digits or inside a path is not a break."""
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+(?=[A-Z'\"(])", str(text or "").strip()) if p.strip()]


def compose(*blocks: tuple[str, object], where: str = "") -> str:
    """Build a cell the way a person reads it: LABEL, then bullets, a blank line between blocks.

    Each block is (label, items); items is one string or a list. A string is split into sentences, one
    bullet each. Empty blocks are dropped. Goes through check_cell, so a cell over the cap or a label over
    the limit raises. Callers compose cells with this instead of joining prose, which is how a paragraph
    reached a client sheet five times despite the rule.
    """
    out = []
    for label, items in blocks:
        items = sentences(items) if isinstance(items, str) else [str(i).strip() for i in items if str(i).strip()]
        if items:
            out.append(label.upper() + "\n" + "\n".join(f"{BULLET} {i}" for i in items))
    return check_cell("\n\n".join(out), where)


def is_formatted(text: str) -> bool:
    """True when a long cell is a label plus bullets, False for a paragraph. Short cells always pass."""
    s = str(text or "").strip()
    if len(s) <= 160:
        return True
    lines = [ln.strip() for ln in s.split("\n") if ln.strip()]
    return bool(lines) and bool(_LABEL_LINE.match(lines[0])) and any(ln.startswith(BULLET) for ln in lines[1:])


def check_cell(text: str, where: str = "") -> str:
    """cell(), plus the two limits that need a human to fix the CONTENT."""
    s = cell(text)
    if len(s) > CELL_MAX:
        raise ValueError(
            f"cell {where or '(unnamed)'} is {len(s)} chars, over the "
            f"{CELL_MAX} limit. Cut it - do not raise the limit. A cell this "
            f"long is a wall of text and will not be read.")
    for ln in s.split("\n"):
        t = ln.strip()
        if _LABEL_LINE.match(t) and len(t) > LABEL_MAX:
            raise ValueError(
                f"cell {where or '(unnamed)'} has a {len(t)}-char uppercase "
                f"label: {t!r}. A label carries the verdict in a few words; "
                f"put the sentence in a bullet under it.")
    return s


def write(sheet_id: str, a1: str, values: list[list], *, verify: bool = True,
          autoformat: bool = True) -> WriteResult:
    """Write a 2D block, then read it back and prove it landed.

    USER_ENTERED is deliberate: it makes '2026-09-15' a real date rather than
    text. Text dates would make the 4.5 COUNT formulas read zero, which is the
    exact bug class already fixed once in this workbook.

    Every multi-line string is passed through cell() on the way out, so the
    house format cannot be forgotten by a caller.
    """
    for pat in DENY_PATTERNS:
        if pat.search(a1):
            raise WriteRefused(
                f"{a1} is on the deny-list (formula range). Refusing to write.")

    values = [[cell(v) if isinstance(v, str) and "\n" in v else v for v in row]
              for row in values]
    for r, row in enumerate(values):
        for c, v in enumerate(row):
            if isinstance(v, str) and len(v) > CELL_MAX:
                print(f"  !! long cell in {a1} (row {r + 1}, col {c + 1}): "
                      f"{len(v)} chars, over {CELL_MAX} - shorten it")
            if isinstance(v, str) and not is_formatted(v):
                print(f"  !! paragraph in {a1} (row {r + 1}, col {c + 1}): {len(v)} chars with no label and "
                      "bullets - build it with sheets_io.compose()")

    _call(_values().update(
        spreadsheetId=sheet_id, range=a1,
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ))

    cells = sum(len(r) for r in values)
    # Format runs after the values land and before verification, so a read-back
    # sees the formatted cell and the two never disagree.
    if autoformat:
        try:
            _autoformat(sheet_id, a1, values)
        except Exception:
            pass          # a formatting failure must never fail a good write
        try:
            set_font_size(sheet_id, a1)
        except Exception:
            pass
    if not verify:
        return WriteResult(a1=a1, cells=cells, verified=False)

    back = read(sheet_id, a1)
    mismatches = []
    for r, row in enumerate(values):
        got_row = back[r] if r < len(back) else []
        for c, want in enumerate(row):
            got = got_row[c] if c < len(got_row) else ""
            if _norm_cell(want) != _norm_cell(got):
                mismatches.append((r, c, want, got))

    if mismatches:
        raise WriteUnverified(
            f"{a1}: {len(mismatches)} cell(s) did not match after write. "
            f"First: row {mismatches[0][0]} col {mismatches[0][1]} "
            f"sent={mismatches[0][2]!r} got={mismatches[0][3]!r}")

    return WriteResult(a1=a1, cells=cells, verified=True, mismatches=[])


# --- locating sections ------------------------------------------------------

def find_rows(sheet_id: str, tab: str, prefixes: dict[str, str],
              scan_to: int = 80) -> dict[str, int]:
    """Map name -> 1-indexed row, by matching the start of column A.

    Never hardcode row numbers against these workbooks. Eight people share
    them and a single inserted row silently shifts every fixed range, which
    would put good data in the wrong cells. Anchoring on the heading text
    survives inserts, and fails loudly if a heading is renamed.
    """
    col = read(sheet_id, f"'{tab}'!A1:A{scan_to}")
    flat = [(r[0].strip() if r else "") for r in col]
    out: dict[str, int] = {}
    for name, prefix in prefixes.items():
        for i, val in enumerate(flat, start=1):
            if val.startswith(prefix):
                out[name] = i
                break
        else:
            raise KeyError(f"{tab}: no row starting {prefix!r} in the first {scan_to} rows")
    return out


# --- formatting -------------------------------------------------------------

# Every cell written through this module is set to 10pt. Owner rule,
# 2026-08-19: populated data was landing at the spreadsheet default and he was
# manually resizing every fill. Font SIZE only - family, weight and colour are
# left alone so headers and any styling the team applies survive.
FONT_SIZE = 10

# Thousands separators. Counts read as counts rather than as long digit strings.
FMT_INT = "#,##0"
# Deltas carry their sign, matching how the workbook's own example rows wrote
# them ("+41"). Zero shows bare rather than "+0".
FMT_DELTA = "+#,##0;-#,##0;0"
FMT_PCT = "0.0%"

_A1_RE = re.compile(
    r"^'?(?P<tab>[^'!]+)'?!(?P<c1>[A-Z]+)(?P<r1>\d+)(?::(?P<c2>[A-Z]+)(?P<r2>\d+))?$")


def _col_to_index(col: str) -> int:
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def tab_id(sheet_id: str, tab_name: str) -> int:
    meta = _call(service().spreadsheets().get(
        spreadsheetId=sheet_id, fields="sheets.properties(sheetId,title)"))
    for s in meta["sheets"]:
        if s["properties"]["title"] == tab_name:
            return s["properties"]["sheetId"]
    raise KeyError(f"no tab named {tab_name!r}")


def set_font_size(sheet_id: str, a1: str, size: int = FONT_SIZE) -> int:
    """Set only textFormat.fontSize on a range; every other format survives."""
    m = _A1_RE.match(a1)
    if not m:
        raise ValueError(f"cannot parse range: {a1}")
    g = m.groupdict()
    grid = {
        "sheetId": tab_id(sheet_id, g["tab"]),
        "startRowIndex": int(g["r1"]) - 1,
        "endRowIndex": int(g["r2"] or g["r1"]),
        "startColumnIndex": _col_to_index(g["c1"]),
        "endColumnIndex": _col_to_index(g["c2"] or g["c1"]) + 1,
    }
    _call(service().spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"repeatCell": {
            "range": grid,
            "cell": {"userEnteredFormat": {"textFormat": {"fontSize": size}}},
            "fields": "userEnteredFormat.textFormat.fontSize",
        }}]},
    ))
    return ((grid["endRowIndex"] - grid["startRowIndex"])
            * (grid["endColumnIndex"] - grid["startColumnIndex"]))


def set_number_format(sheet_id: str, a1: str, pattern: str) -> int:
    """Apply a number format to a range. Text cells in range are unaffected."""
    m = _A1_RE.match(a1)
    if not m:
        raise ValueError(f"cannot parse range: {a1}")
    g = m.groupdict()
    grid = {
        "sheetId": tab_id(sheet_id, g["tab"]),
        "startRowIndex": int(g["r1"]) - 1,
        "endRowIndex": int(g["r2"] or g["r1"]),
        "startColumnIndex": _col_to_index(g["c1"]),
        "endColumnIndex": _col_to_index(g["c2"] or g["c1"]) + 1,
    }
    _call(service().spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"repeatCell": {
            "range": grid,
            "cell": {"userEnteredFormat": {
                "numberFormat": {"type": "NUMBER", "pattern": pattern}}},
            "fields": "userEnteredFormat.numberFormat",
        }}]},
    ))
    rows = grid["endRowIndex"] - grid["startRowIndex"]
    cols = grid["endColumnIndex"] - grid["startColumnIndex"]
    return rows * cols


def _autoformat(sheet_id: str, a1: str, values: list[list]) -> int:
    """Give every number written through here a human-readable format.

    Owner's standing rule, and it is not specific to any one task: whenever data
    is written, 25864 must read as 25,864. Applied as a cell FORMAT rather than
    by writing a formatted string, so the cell still holds a real number and
    stays sortable, filterable and usable in a formula.

    Column by column, because a range mixes types: impressions want thousands
    separators, an average position wants one decimal and neither wants the
    other. Years are deliberately skipped - 2026 must not become 2,026.
    """
    if not values:
        return 0
    tab, _, rng = a1.rpartition("!")
    tab = tab.strip("'")
    m = re.match(r"([A-Z]+)(\d+):?([A-Z]+)?(\d+)?", rng.replace("$", ""))
    if not m:
        return 0
    first_col, first_row = m.group(1), int(m.group(2))
    n = 0
    width = max(len(r) for r in values)
    for ci in range(width):
        col = [r[ci] for r in values if ci < len(r) and r[ci] not in ("", None)]
        if not col or not all(isinstance(v, (int, float)) and not isinstance(v, bool)
                              for v in col):
            continue
        if any(isinstance(v, float) and v != int(v) for v in col):
            pattern = "0.0"
        elif all(1900 <= v <= 2100 for v in col):
            continue                     # years, not quantities
        elif max(abs(v) for v in col) < 1000:
            continue                     # separators add nothing below 1,000
        else:
            pattern = FMT_INT
        letter = _index_to_col(_col_to_index(first_col) + ci)
        n += set_number_format(
            sheet_id,
            f"'{tab}'!{letter}{first_row}:{letter}{first_row + len(values) - 1}",
            pattern)
    return n


def _index_to_col(idx: int) -> str:
    out = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        out = chr(65 + rem) + out
    return out


def snapshot_tab(sheet_id: str, tab: str, folder, rng: str = "A1:J60") -> str:
    """Save a tab's current values to a timestamped JSON before overwriting.

    Exists because a 1.8 refill overwrote the owner's manual tab edits with
    no way back (2026-08-19). Every fill script calls this before its first
    write, so any overwrite is recoverable from
    <folder>/tab-backups/<tab>-<stamp>.json.
    """
    import datetime as _dt
    import json as _json
    import pathlib as _pl
    d = _pl.Path(folder) / "tab-backups"
    d.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    safe = re.sub(r"[^A-Za-z0-9.-]+", "_", tab)
    p = d / f"{safe}-{stamp}.json"
    p.write_text(_json.dumps(read(sheet_id, f"'{tab}'!{rng}"),
                             ensure_ascii=False, indent=1), encoding="utf-8")
    return str(p)


def insert_rows(sheet_id: str, tab: str, at_row: int, count: int) -> int:
    """Insert `count` blank rows above `at_row`, shifting everything below down.

    Section B of the 1.4 tab has four rows before section C begins. Writing a
    real sample of checked URLs into it would overwrite the C and D headings, so
    the rows have to be made rather than borrowed.
    """
    if count <= 0:
        return 0
    _call(service().spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"insertDimension": {
            "range": {"sheetId": tab_id(sheet_id, tab), "dimension": "ROWS",
                      "startIndex": at_row - 1, "endIndex": at_row - 1 + count},
            "inheritFromBefore": False}}]}))
    return count


def delete_rows(sheet_id: str, tab: str, at_row: int, count: int) -> int:
    """Remove rows, so a re-run does not leave last month's sample behind."""
    if count <= 0:
        return 0
    _call(service().spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"deleteDimension": {
            "range": {"sheetId": tab_id(sheet_id, tab), "dimension": "ROWS",
                      "startIndex": at_row - 1, "endIndex": at_row - 1 + count}}}]}))
    return count


def append_rows(sheet_id: str, tab: str, count: int) -> int:
    """Add `count` blank rows at the BOTTOM, leaving the column count alone.

    insert_rows cannot do this: startIndex must fall inside the existing grid
    when inheritFromBefore is false, so appending past the last row is a 400.
    Growing the grid by letting a write run off the end is worse - Sheets
    expands to its own default of 26 columns and the new columns inherit the
    last column's formatting.
    """
    if count <= 0:
        return 0
    _call(service().spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"appendDimension": {
            "sheetId": tab_id(sheet_id, tab), "dimension": "ROWS",
            "length": count}}]}))
    return count


def grid_size(sheet_id: str, tab: str) -> tuple[int, int]:
    """(rows, cols) the tab actually has. Addressing past these GROWS the grid."""
    meta = service().spreadsheets().get(
        spreadsheetId=sheet_id, includeGridData=False).execute()
    for sh in meta["sheets"]:
        if sh["properties"]["title"] == tab:
            g = sh["properties"]["gridProperties"]
            return int(g.get("rowCount", 0)), int(g.get("columnCount", 0))
    raise KeyError(f"tab {tab!r} not found")


def last_row(sheet_id: str, tab: str) -> int:
    """Index of the last row holding a value, 0 if the tab is empty."""
    return len(read(sheet_id, f"'{tab}'!A:A"))


def clear(sheet_id: str, a1: str) -> None:
    for pat in DENY_PATTERNS:
        if pat.search(a1):
            raise WriteRefused(f"{a1} is on the deny-list. Refusing to clear.")
    _call(_values().clear(spreadsheetId=sheet_id, range=a1, body={}))
