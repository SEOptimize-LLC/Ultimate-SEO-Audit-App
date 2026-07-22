"""
Google Analytics 4 Data Fetcher
Pulls sessions by channel and top organic pages for a client.
Saves to Clients/{client}/data/ga4/
Usage: called by run_fetch.py or directly via python fetchers/fetch_ga4.py --client educationwalkthrough.com
"""

import json
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Metric, Dimension, FilterExpression, Filter
)

PROJECT_ROOT = Path(__file__).parent.parent


def get_client(service_account_path: str) -> BetaAnalyticsDataClient:
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    return BetaAnalyticsDataClient(credentials=credentials)


def report_to_dict(response) -> list:
    rows = []
    for row in response.rows:
        record = {}
        for i, dim in enumerate(response.dimension_headers):
            record[dim.name] = row.dimension_values[i].value
        for i, met in enumerate(response.metric_headers):
            record[met.name] = row.metric_values[i].value
        rows.append(record)
    return rows


def run(client_name: str, days: int = 90):
    config_path = PROJECT_ROOT / "Clients" / client_name / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    service_account_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_path:
        raise EnvironmentError("GOOGLE_SERVICE_ACCOUNT_JSON not set in environment")

    property_id = f"properties/{config['ga4_property_id']}"
    end_date = datetime.today().strftime("%Y-%m-%d")
    start_date = (datetime.today() - timedelta(days=days)).strftime("%Y-%m-%d")

    output_dir = PROJECT_ROOT / "Clients" / client_name / "data" / "ga4"
    output_dir.mkdir(parents=True, exist_ok=True)

    client = get_client(service_account_path)

    # Sessions by channel
    print(f"  Fetching GA4 sessions by channel ({start_date} → {end_date})...")
    channel_report = client.run_report(RunReportRequest(
        property=property_id,
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="conversions"),
        ],
    ))
    channels = report_to_dict(channel_report)
    channels_file = output_dir / f"channels_{days}d.json"
    with open(channels_file, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "period": {"start": start_date, "end": end_date}, "rows": channels}, f, indent=2)
    print(f"    Saved {len(channels)} channel rows → {channels_file.name}")

    # Top organic landing pages
    print(f"  Fetching GA4 organic landing pages ({start_date} → {end_date})...")
    organic_filter = FilterExpression(
        filter=Filter(
            field_name="sessionDefaultChannelGroup",
            string_filter=Filter.StringFilter(value="Organic Search", match_type=Filter.StringFilter.MatchType.EXACT),
        )
    )
    pages_report = client.run_report(RunReportRequest(
        property=property_id,
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="landingPage")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="engagementRate"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="conversions"),
        ],
        dimension_filter=organic_filter,
        limit=500,
    ))
    pages = report_to_dict(pages_report)
    pages_file = output_dir / f"organic_pages_{days}d.json"
    with open(pages_file, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "period": {"start": start_date, "end": end_date}, "rows": pages}, f, indent=2)
    print(f"    Saved {len(pages)} organic pages → {pages_file.name}")

    return {"channels": len(channels), "organic_pages": len(pages)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch GA4 data for a client")
    parser.add_argument("--client", required=True, help="Client folder name (e.g. educationwalkthrough.com)")
    parser.add_argument("--days", type=int, default=90, help="Number of days to fetch (default: 90)")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    result = run(args.client, args.days)
    print(f"\nGA4 fetch complete: {result}")
