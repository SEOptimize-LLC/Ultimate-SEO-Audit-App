"""
SEO Data Fetcher — Orchestrator
Fetches GSC, GA4, and AI visibility data for a client in one command.

Usage:
  python run_fetch.py --client educationwalkthrough.com
  python run_fetch.py --client educationwalkthrough.com --sources gsc,ga4
  python run_fetch.py --client educationwalkthrough.com --days 30

Available sources: gsc, ga4, ai
Default: all sources
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

# Add project root to path so fetchers can import shared utilities
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Fetch SEO data for a client")
    parser.add_argument("--client", required=True, help="Client folder name (e.g. educationwalkthrough.com)")
    parser.add_argument("--sources", default="gsc,ga4,ai", help="Comma-separated list of sources: gsc,ga4,ai (default: all)")
    parser.add_argument("--days", type=int, default=90, help="Days of historical data to fetch (default: 90)")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",")]
    client = args.client
    days = args.days

    config_path = PROJECT_ROOT / "Clients" / client / "config.json"
    if not config_path.exists():
        print(f"Error: No config found at {config_path}")
        print(f"Create a config.json in Clients/{client}/ first.")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  Fetching data for: {client}")
    print(f"  Sources: {', '.join(sources)}")
    print(f"  Period: last {days} days")
    print(f"{'='*50}\n")

    results = {}

    if "gsc" in sources:
        print("[1/3] Google Search Console")
        try:
            from fetchers.fetch_gsc import run as fetch_gsc
            results["gsc"] = fetch_gsc(client, days)
        except Exception as e:
            print(f"  GSC error: {e}")
            results["gsc"] = {"error": str(e)}

    if "ga4" in sources:
        print("\n[2/3] Google Analytics 4")
        try:
            from fetchers.fetch_ga4 import run as fetch_ga4
            results["ga4"] = fetch_ga4(client, days)
        except Exception as e:
            print(f"  GA4 error: {e}")
            results["ga4"] = {"error": str(e)}

    if "ai" in sources:
        print("\n[3/3] AI Visibility (DataForSEO)")
        try:
            from fetchers.fetch_ai_visibility import run as fetch_ai
            results["ai"] = fetch_ai(client)
        except Exception as e:
            print(f"  AI visibility error: {e}")
            results["ai"] = {"error": str(e)}

    print(f"\n{'='*50}")
    print("  Fetch complete. Data saved to:")
    print(f"  Clients/{client}/data/")
    print(f"\n  Summary:")
    for source, result in results.items():
        if "error" in result:
            print(f"    {source.upper()}: FAILED — {result['error']}")
        else:
            print(f"    {source.upper()}: OK — {result}")
    print(f"{'='*50}\n")
    print("Open Claude Code in this directory and start asking questions.")
    print("Example: 'Which GSC pages have high impressions but low CTR?'")
    print("Example: 'Group my GSC queries by topic cluster and show me the top opportunities.'")
    print("Example: 'Which pages rank well in GSC but have high bounce rates in GA4?'")


if __name__ == "__main__":
    main()
