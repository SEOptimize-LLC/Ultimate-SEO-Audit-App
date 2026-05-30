"""CLI orchestrator for the semantic-site-map skill.

Usage:
    python run_semantic_map.py --client "<client-name>"
    python run_semantic_map.py --client "Education Walkthrough" \\
        --crawl "Clients/Education Walkthrough/Others/ew_crawl_filtered.csv" \\
        --gsc   "Clients/Education Walkthrough/data/gsc_performance.csv"

If --crawl is omitted, defaults to Clients/<client>/data/crawl_internal.csv.
If --gsc is omitted, defaults to Clients/<client>/data/gsc_performance.csv
(optional - skipped if absent).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Crawl4AI's startup banner prints non-ASCII glyphs (e.g. ->) via
# colorama. On Windows with the default cp1252 console codec, this
# crashes whenever stdout is redirected (tee, > file, CI capture).
# Force UTF-8 on stdout/stderr so the skill is safe to pipe.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

import pandas as pd
from dotenv import load_dotenv

from Skills.semantic_site_map.cluster import cluster_pages
from Skills.semantic_site_map.embedder import DEFAULT_MODEL, embed_pages
from Skills.semantic_site_map.report import build_outputs
from Skills.semantic_site_map.text_loader import load_page_text
from utils.file_parser import _read_csv_robust


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _resolve_paths(
    client: str,
    crawl: Optional[str],
    gsc: Optional[str],
    ga4: Optional[str] = None,
) -> tuple[Path, Optional[Path], Optional[Path], Path]:
    client_root = Path("Clients") / client
    if not client_root.exists():
        raise SystemExit(f"Client folder not found: {client_root}")

    crawl_path = (
        Path(crawl) if crawl
        else client_root / "data" / "crawl_internal.csv"
    )
    if not crawl_path.exists():
        raise SystemExit(f"Crawl file not found: {crawl_path}")

    gsc_path: Optional[Path] = (
        Path(gsc) if gsc
        else client_root / "data" / "gsc_performance.csv"
    )
    if gsc_path and not gsc_path.exists():
        gsc_path = None

    # GA4: look for the canonical pages CSV in data/ga4/, otherwise
    # accept an explicit path. Skip silently if neither exists - the
    # business-value scorer falls back to URL-pattern only.
    ga4_path: Optional[Path] = Path(ga4) if ga4 else None
    if ga4_path is None:
        ga4_dir = client_root / "data" / "ga4"
        if ga4_dir.exists():
            for name in (
                "pages.csv",
                "top_pages.csv",
                "organic_pages.csv",
            ):
                candidate = ga4_dir / name
                if candidate.exists():
                    ga4_path = candidate
                    break
    if ga4_path is not None and not ga4_path.exists():
        ga4_path = None

    out_dir = client_root / "Full SEO Audit" / "semantic_map"
    return crawl_path, gsc_path, ga4_path, out_dir


def _load_gsc(path: Optional[Path]) -> Optional[pd.DataFrame]:
    if path is None:
        return None
    df = _read_csv_robust(path)
    rename = {}
    for col in df.columns:
        low = col.lower().strip()
        if low in ("page", "address", "landing page"):
            rename[col] = "url"
        elif low in ("clicks", "url clicks"):
            rename[col] = "clicks"
        elif low == "impressions":
            rename[col] = "impressions"
    df = df.rename(columns=rename)
    needed = {"url", "clicks", "impressions"}
    if not needed.issubset(df.columns):
        logging.warning(
            "run_semantic_map: GSC file lacks expected columns "
            "(got %s) - skipping click overlay",
            list(df.columns),
        )
        return None
    # Coerce numeric columns - _read_csv_robust returns strings when
    # the file came from a non-pandas source (e.g. GSC MCP markdown
    # output reformatted to CSV).
    for num_col in ("clicks", "impressions"):
        df[num_col] = pd.to_numeric(
            df[num_col], errors="coerce"
        ).fillna(0)
    return df[list(needed)]


def _load_ga4(path: Optional[Path]) -> Optional[pd.DataFrame]:
    """Load a GA4 pages CSV into a (url, conversions) DataFrame.

    Accepts the canonical GA4 export shapes the project's GA4 fetcher
    produces (page path + key event/conversion columns), normalizes
    column names, and returns None when the file is unusable. The
    business-value scorer reads ``conversions`` only.
    """
    if path is None:
        return None
    try:
        df = _read_csv_robust(path)
    except Exception as exc:  # noqa: BLE001
        logging.warning(
            "run_semantic_map: GA4 file unreadable (%s) - "
            "skipping conversion boost", exc,
        )
        return None
    rename = {}
    for col in df.columns:
        low = col.lower().strip()
        if low in ("page", "page_path", "landing_page", "address"):
            rename[col] = "url"
        elif low in (
            "conversions",
            "key_events",
            "keyevents",
            "key events",
            "conversion",
        ):
            rename[col] = "conversions"
    df = df.rename(columns=rename)
    if "url" not in df.columns or "conversions" not in df.columns:
        logging.warning(
            "run_semantic_map: GA4 file lacks expected columns "
            "(got %s) - skipping conversion boost",
            list(df.columns),
        )
        return None
    try:
        df["conversions"] = pd.to_numeric(
            df["conversions"], errors="coerce"
        ).fillna(0)
    except Exception:  # noqa: BLE001
        return None
    return df[["url", "conversions"]]


def _normalize_crawl_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a 'url' column exists by renaming common SF aliases."""
    if "url" in df.columns:
        return df
    for col in df.columns:
        if col.lower() in ("address", "url"):
            return df.rename(columns={col: "url"})
    raise SystemExit(
        "Crawl CSV has no 'url' / 'Address' column - cannot proceed."
    )


async def _run(args: argparse.Namespace) -> None:
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENROUTER_API_KEY missing. "
            "Add it to .env or your environment."
        )

    crawl_path, gsc_path, ga4_path, out_dir = _resolve_paths(
        args.client, args.crawl, args.gsc, args.ga4,
    )
    cache_dir = out_dir.parent / "_cache_semantic_map"
    cache_dir.mkdir(parents=True, exist_ok=True)

    logging.info("run_semantic_map: client=%s", args.client)
    logging.info("run_semantic_map: crawl=%s", crawl_path)
    logging.info(
        "run_semantic_map: gsc=%s", gsc_path or "(none)"
    )
    logging.info(
        "run_semantic_map: ga4=%s", ga4_path or "(none)"
    )
    logging.info("run_semantic_map: out_dir=%s", out_dir)

    df = _read_csv_robust(crawl_path)
    df = _normalize_crawl_columns(df)

    text_cache = cache_dir / "page_text.csv"
    text_df = await load_page_text(df, cache_path=text_cache)
    logging.info("run_semantic_map: text rows=%d", len(text_df))

    if len(text_df) < 5:
        raise SystemExit(
            f"Only {len(text_df)} URLs survived eligibility filters "
            "- refusing to cluster."
        )

    embeddings = embed_pages(
        text_df,
        cache_dir=cache_dir,
        api_key=api_key,
        model=args.model,
    )
    logging.info(
        "run_semantic_map: embedding matrix shape=%s", embeddings.shape
    )

    if len(text_df) < 50:
        logging.warning(
            "run_semantic_map: only %d URLs (<50) - "
            "clustering will be coarse. "
            "Markdown report will flag this limitation.",
            len(text_df),
        )

    cluster_result = cluster_pages(text_df, embeddings, api_key=api_key)
    gsc = _load_gsc(gsc_path)
    ga4 = _load_ga4(ga4_path)

    paths = build_outputs(
        out_dir=out_dir,
        text_df=text_df,
        embeddings=embeddings,
        cluster_result=cluster_result,
        gsc=gsc,
        client_name=args.client,
        model_name=args.model,
        ga4=ga4,
    )

    print("\nOutputs written:")
    for label, p in paths.items():
        print(f"  {label:>20}  {p}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Semantic site map for a client.",
    )
    parser.add_argument(
        "--client",
        required=True,
        help="Client folder name under Clients/",
    )
    parser.add_argument(
        "--crawl",
        help="Path to SF Internal CSV "
        "(default: data/crawl_internal.csv)",
    )
    parser.add_argument(
        "--gsc",
        help="Path to GSC performance CSV "
        "(default: data/gsc_performance.csv)",
    )
    parser.add_argument(
        "--ga4",
        help="Path to GA4 pages CSV with a conversions column "
        "(default: data/ga4/pages.csv). Optional; enables the "
        "GA4 conversion boost in business-value scoring.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="OpenRouter embedding model id",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
