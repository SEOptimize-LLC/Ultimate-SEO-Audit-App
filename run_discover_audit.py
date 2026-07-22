"""CLI runner for the standalone Google Discover eligibility audit.

Google Discover is a query-independent content feed with its own GSC report
and its own eligibility model — it is invisible to a standard SERP-focused
technical/on-page audit. This runner triggers the Discover auditor on its own,
SEPARATELY from the full-site audit, so the Discover channel can be assessed
on demand.

Usage:
    python run_discover_audit.py --crawl <path.csv|xlsx>
    python run_discover_audit.py --crawl crawl_internal.csv \\
        --discover-perf gsc_discover_export.csv \\
        --out discover_report.md --client "Education Walkthrough"

Inputs:
    --crawl         Screaming Frog HTML Internal export (CSV or XLSX). Required.
    --discover-perf Optional GSC Discover Performance export (page-level
                    clicks / impressions / CTR). Unlocks current-earning and
                    low-CTR opportunity findings.
    --out           Optional path for the Markdown report. Defaults to
                    stdout only.
    --client        Optional client name for the report header.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Match run_semantic_map.py: force UTF-8 on stdout/stderr so the report (which
# contains non-ASCII glyphs like em dashes and ≥) is safe to pipe/redirect on
# a Windows cp1252 console.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

import pandas as pd

from auditors.discover_auditor import DiscoverAuditor
from models.audit_result import AuditIssue
from utils.file_parser import _read_csv_robust, parse_screaming_frog_export

logger = logging.getLogger("run_discover_audit")


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _load_crawl(path: Path) -> pd.DataFrame:
    """Load a Screaming Frog crawl export into the standardized df."""
    if not path.exists():
        raise SystemExit(f"Crawl file not found: {path}")
    logger.info("Loading crawl: %s", path)
    return parse_screaming_frog_export(path)


def _load_discover_perf(path: Optional[Path]) -> Optional[pd.DataFrame]:
    """Load an optional GSC Discover Performance export.

    Column normalization is intentionally left to the auditor, which detects
    page/url, impressions, and clicks case-insensitively. Returns None (with a
    warning) when the file is absent or unreadable, so the audit degrades
    gracefully to the crawl-only eligibility assessment.
    """
    if path is None:
        return None
    if not path.exists():
        logger.warning(
            "Discover performance file not found: %s — running crawl-only "
            "eligibility assessment.",
            path,
        )
        return None
    logger.info("Loading Discover performance export: %s", path)
    try:
        suffix = path.suffix.lower()
        if suffix in (".xlsx", ".xls"):
            return pd.read_excel(path, engine="openpyxl")
        return _read_csv_robust(path)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Discover performance file unreadable (%s) — running crawl-only "
            "eligibility assessment.",
            exc,
        )
        return None


def _severity_label(issue: AuditIssue) -> str:
    return issue.severity.value.upper()


def build_report(
    issues: list[AuditIssue],
    client: Optional[str],
    has_perf: bool,
    url_sample_limit: int = 25,
) -> str:
    """Render the Discover findings as a clean, self-contained Markdown report.

    Full URLs are never truncated (per report-formatting rules) and no internal
    file paths appear in the output.
    """
    lines: list[str] = []
    header = "# Google Discover Eligibility Audit"
    if client:
        header += f" — {client}"
    lines.append(header)
    lines.append("")
    lines.append(
        "Standalone channel audit. Google Discover is a query-independent "
        "content feed, separate from standard Search — this report assesses "
        "Discover eligibility only and does not cover SERP technical/on-page "
        "issues."
    )
    lines.append("")
    lines.append(
        f"Discover performance export supplied: {'yes' if has_perf else 'no'}."
    )
    if not has_perf:
        lines.append("")
        lines.append(
            "> Without a GSC Discover Performance export, current-earning and "
            "low-CTR opportunity findings cannot be produced. The eligibility "
            "assessment below is derived from the crawl alone."
        )
    lines.append("")

    if not issues:
        lines.append("No Discover findings were produced.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"Findings: {len(issues)}")
    lines.append("")

    # Most urgent first.
    ordered = sorted(issues, key=lambda i: i.severity.priority)
    for idx, issue in enumerate(ordered, start=1):
        lines.append(f"## {idx}. [{_severity_label(issue)}] {issue.title}")
        lines.append("")
        if issue.description:
            lines.append(issue.description)
            lines.append("")
        if issue.recommendation:
            lines.append(f"**Recommendation:** {issue.recommendation}")
            lines.append("")
        if issue.impact:
            lines.append(f"**Impact:** {issue.impact}")
            lines.append("")
        if issue.affected_urls:
            shown = issue.affected_urls[:url_sample_limit]
            lines.append(
                f"**Affected URLs ({issue.count} total, "
                f"showing {len(shown)}):**"
            )
            for url in shown:
                lines.append(f"- {url}")
            lines.append("")

    return "\n".join(lines)


def _run(args: argparse.Namespace) -> None:
    crawl_df = _load_crawl(Path(args.crawl))

    perf_path = Path(args.discover_perf) if args.discover_perf else None
    perf_df = _load_discover_perf(perf_path)

    auditor = DiscoverAuditor(crawl_df, discover_performance_df=perf_df)
    issues = auditor.run_audit()
    logger.info("Discover audit produced %d finding(s).", len(issues))

    report = build_report(
        issues,
        client=args.client,
        has_perf=perf_df is not None and len(perf_df) > 0,
    )

    print(report)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        logger.info("Report written: %s", out_path)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Standalone Google Discover eligibility audit.",
    )
    parser.add_argument(
        "--crawl",
        required=True,
        help="Path to the Screaming Frog HTML Internal export (CSV or XLSX).",
    )
    parser.add_argument(
        "--discover-perf",
        dest="discover_perf",
        help="Optional GSC Discover Performance export "
        "(page-level clicks/impressions/CTR).",
    )
    parser.add_argument(
        "--out",
        help="Optional path to write the Markdown report "
        "(also printed to stdout).",
    )
    parser.add_argument(
        "--client",
        help="Optional client name for the report header.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)
    _run(args)


if __name__ == "__main__":
    main()
