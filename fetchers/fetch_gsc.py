"""
Google Search Console Data Fetcher
Pulls queries and pages for a client and saves to Clients/{client}/data/gsc/
Usage: called by run_fetch.py or directly via python fetchers/fetch_gsc.py --client educationwalkthrough.com
"""

import json
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
PROJECT_ROOT = Path(__file__).parent.parent


def get_service(service_account_path: str):
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path, scopes=SCOPES
    )
    return build("searchconsole", "v1", credentials=credentials)


def fetch_data(service, site_url: str, start_date: str, end_date: str, dimensions: list, row_limit: int = 1000) -> list:
    response = service.searchanalytics().query(
        siteUrl=site_url,
        body={
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": dimensions,
            "rowLimit": row_limit,
        },
    ).execute()
    return response.get("rows", [])


def run(client_name: str, days: int = 90):
    config_path = PROJECT_ROOT / "Clients" / client_name / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    service_account_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_path:
        raise EnvironmentError("GOOGLE_SERVICE_ACCOUNT_JSON not set in environment")

    site_url = config["gsc_property"]
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")

    output_dir = PROJECT_ROOT / "Clients" / client_name / "data" / "gsc"
    output_dir.mkdir(parents=True, exist_ok=True)

    service = get_service(service_account_path)
    print(f"  Fetching GSC queries ({start_date} → {end_date})...")
    queries = fetch_data(service, site_url, start_date, end_date, ["query"], row_limit=1000)
    queries_file = output_dir / f"queries_{days}d.json"
    with open(queries_file, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "period": {"start": start_date, "end": end_date}, "rows": queries}, f, indent=2)
    print(f"    Saved {len(queries)} queries → {queries_file.name}")

    print(f"  Fetching GSC pages ({start_date} → {end_date})...")
    pages = fetch_data(service, site_url, start_date, end_date, ["page"], row_limit=1000)
    pages_file = output_dir / f"pages_{days}d.json"
    with open(pages_file, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "period": {"start": start_date, "end": end_date}, "rows": pages}, f, indent=2)
    print(f"    Saved {len(pages)} pages → {pages_file.name}")

    print(f"  Fetching GSC query+page pairs ({start_date} → {end_date})...")
    query_pages = fetch_data(service, site_url, start_date, end_date, ["query", "page"], row_limit=1000)
    query_pages_file = output_dir / f"query_pages_{days}d.json"
    with open(query_pages_file, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "period": {"start": start_date, "end": end_date}, "rows": query_pages}, f, indent=2)
    print(f"    Saved {len(query_pages)} query-page pairs → {query_pages_file.name}")

    return {"queries": len(queries), "pages": len(pages), "query_pages": len(query_pages)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch GSC data for a client")
    parser.add_argument("--client", required=True, help="Client folder name (e.g. educationwalkthrough.com)")
    parser.add_argument("--days", type=int, default=90, help="Number of days to fetch (default: 90)")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    result = run(args.client, args.days)
    print(f"\nGSC fetch complete: {result}")
