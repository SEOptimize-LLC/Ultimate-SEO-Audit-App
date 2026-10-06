"""Count the distinct US addresses and phone numbers a page lists in its visible text.

Google's leaked LocalWWWInfoAddress documentation says addresses and phone numbers are populated only when a
document has four or fewer of each. These helpers count the distinct ones so an auditor can compare a page
against that limit. They are heuristics for US formats: a number or address repeated on the page (header and
footer, tel: link and visible text) counts once.
"""

from __future__ import annotations

import re

US_STATES = (
    "AL|AK|AZ|AR|CA|CO|CT|DE|DC|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|"
    "OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY"
)
_SUFFIXES = {
    "street": "street", "st": "street", "avenue": "avenue", "ave": "avenue", "road": "road", "rd": "road",
    "boulevard": "boulevard", "blvd": "boulevard", "drive": "drive", "dr": "drive", "lane": "lane", "ln": "lane",
    "way": "way", "court": "court", "ct": "court", "parkway": "parkway", "pkwy": "parkway", "highway": "highway",
    "hwy": "highway", "place": "place", "pl": "place", "circle": "circle", "cir": "circle", "trail": "trail",
    "trl": "trail", "square": "square", "sq": "square",
}
_DIRECTIONS = {"n": "north", "s": "south", "e": "east", "w": "west", "ne": "northeast", "nw": "northwest",
               "se": "southeast", "sw": "southwest"}
_SUFFIX_RE = "|".join(sorted(_SUFFIXES, key=len, reverse=True))
_DIR_RE = "|".join(sorted(list(_DIRECTIONS) + list(_DIRECTIONS.values()), key=len, reverse=True))

# number + street name + suffix, an optional suite, then "City, ST" (state abbreviation is case-sensitive so
# ordinary words cannot pass for one). Requiring the city and state keeps title-case headings such as
# "100 Reasons To Drive" from counting as addresses.
ADDRESS_RE = re.compile(
    rf"\b(?P<num>\d{{1,6}})\s+"
    rf"(?P<street>(?:(?i:{_DIR_RE})\.?\s+)?(?:[A-Za-z0-9][A-Za-z0-9.'-]*\s+){{0,3}}?(?i:{_SUFFIX_RE})\b\.?)"
    rf"(?:[,\s]+(?i:Suite|Ste|Unit|Apt|Bldg|Building|Floor|Fl|Room|Rm)\.?\s*#?\s*[\w-]+|[,\s]+#\s*[\w-]+)?"
    rf"[,\s]+(?P<city>[A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*){{0,2}}),?\s+(?P<state>{US_STATES})\b"
)

_PHONE_PAREN = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(\s*([2-9]\d{2})\s*\)[\s.-]*([2-9]\d{2})[\s.-]+(\d{4})(?!\d)")
_PHONE_PLAIN = re.compile(r"(?<![\d(])(?:\+?1[\s.-]?)?([2-9]\d{2})[\s.-]([2-9]\d{2})[\s.-](\d{4})(?!\d)")
_PHONE_TEL = re.compile(r"tel:\s*\+?1?[\s-]?([2-9]\d{2})[\s.-]?([2-9]\d{2})[\s.-]?(\d{4})(?!\d)", re.I)


def extract_phone_numbers(text: object) -> set[str]:
    """Return the distinct 10-digit US phone numbers in the text."""
    if not isinstance(text, str) or not text:
        return set()
    found: set[str] = set()
    for pattern in (_PHONE_PAREN, _PHONE_PLAIN, _PHONE_TEL):
        for m in pattern.finditer(text):
            found.add("".join(m.groups()))
    return found


def _normalize_street(street: str) -> str:
    words = re.sub(r"[.,]", " ", street.lower()).split()
    return " ".join(_DIRECTIONS.get(w, _SUFFIXES.get(w, w)) for w in words)


def extract_addresses(text: object) -> set[str]:
    """Return the distinct street addresses (number, street, state) in the text."""
    if not isinstance(text, str) or not text:
        return set()
    return {
        f"{m['num']} {_normalize_street(m['street'])} {m['state']}"
        for m in ADDRESS_RE.finditer(text)
    }
