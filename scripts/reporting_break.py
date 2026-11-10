#!/usr/bin/env python
"""Which Search Console comparisons can read impressions and position? Google's documented logging error.

    python scripts/reporting_break.py

Google's Data Anomalies page (support.google.com/webmasters/answer/6211453, read 2026-11-10):
"A logging error prevented Search Console from accurately reporting impressions from May 13, 2025 until
April 27, 2026. ... Only impressions and related metrics - CTR and average position - were affected; clicks
were not affected by the error."

So for every property: clicks compare across any window; impressions, CTR and average position compare only
between windows that start on or after April 27, 2026. Ranking and demand are read against May-July 2026,
the first full quarter of clean data. A decline that shows in clicks but predates May 2026 is labelled
"cause not readable in Search Console".

Reverses the same-day per-site test (August to October 2025 impressions down, position up), which used
October-December 2025 as its reference: that quarter sits inside the misreported period. Decision log,
2026-11-10. The function names stay so the callers did not change shape.
"""
from __future__ import annotations

import datetime as dt
import sys

ERROR_FROM = dt.date(2025, 5, 13)
CLEAN_FROM = dt.date(2026, 4, 27)                         # Google: misreported until April 27, 2026
POST = (dt.date(2026, 5, 1), dt.date(2026, 7, 31))        # first full clean quarter
POST_LABEL = "May-Jul 2026"
NOTE = ("Search Console misreported impressions, CTR and position from May 13, 2025 to April 27, 2026 "
        "(Google's Data Anomalies page); clicks were not affected")


def has_break(svc=None, prop: str | None = None) -> bool:
    """True for every property: Google's logging error was not site-specific."""
    return True


def affects(start: dt.date, broken: bool = True) -> bool:
    """True when a comparison window starting at `start` reads impressions or position from the error period."""
    return broken and start < CLEAN_FROM


def main() -> int:
    print(f"{NOTE}.\nImpressions and position compare only between windows starting on or after {CLEAN_FROM}; "
          f"the reference quarter for ranking and demand is {POST_LABEL}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
