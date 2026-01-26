"""Screaming Frog export file parser.

Handles CSV and Excel files from Screaming Frog crawl exports,
auto-detecting columns and identifying integration data (GSC, PageSpeed, GA4).
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union
from io import BytesIO, StringIO
import re
import csv


def _read_csv_robust(file: Union[BytesIO, str, Path]) -> pd.DataFrame:
    """Read CSV with robust error handling for malformed rows.

    Handles common issues with Screaming Frog exports:
    - Inconsistent column counts (commas in content fields)
    - Different encodings (UTF-8, Latin-1)
    - Various quoting styles

    Args:
        file: File path or BytesIO object

    Returns:
        DataFrame with parsed data
    """
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            # Reset file position if BytesIO
            if isinstance(file, BytesIO):
                file.seek(0)

            # First try: standard pandas with flexible error handling
            try:
                df = pd.read_csv(
                    file,
                    encoding=encoding,
                    on_bad_lines="warn",  # Skip malformed rows with warning
                    low_memory=False,
                    dtype=str,  # Read all as strings first to avoid type issues
                )
                if len(df) > 0:
                    return df
            except TypeError:
                # Older pandas version - use error_bad_lines
                if isinstance(file, BytesIO):
                    file.seek(0)
                df = pd.read_csv(
                    file,
                    encoding=encoding,
                    error_bad_lines=False,
                    warn_bad_lines=True,
                    low_memory=False,
                    dtype=str,
                )
                if len(df) > 0:
                    return df

        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError:
            # Try Python engine which is more flexible
            try:
                if isinstance(file, BytesIO):
                    file.seek(0)
                df = pd.read_csv(
                    file,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="skip",
                    dtype=str,
                )
                if len(df) > 0:
                    return df
            except Exception:
                continue
        except Exception:
            continue

    # Final fallback: read line by line and handle manually
    if isinstance(file, BytesIO):
        file.seek(0)
        content = file.read()
        for encoding in encodings:
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = content.decode("utf-8", errors="ignore")
    else:
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    # Parse manually with csv module
    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty CSV file")

    reader = csv.reader(StringIO(text))
    rows = list(reader)

    if not rows:
        raise ValueError("No data in CSV file")

    # Use first row as header
    header = rows[0]
    num_cols = len(header)

    # Filter rows to match header column count (allow slight variance)
    valid_rows = []
    for row in rows[1:]:
        if len(row) == num_cols:
            valid_rows.append(row)
        elif len(row) > num_cols:
            # Truncate extra columns
            valid_rows.append(row[:num_cols])
        elif len(row) >= num_cols - 2:
            # Pad missing columns
            valid_rows.append(row + [""] * (num_cols - len(row)))

    if not valid_rows:
        raise ValueError("No valid data rows found in CSV")

    return pd.DataFrame(valid_rows, columns=header)


# Screaming Frog column name mappings
# Maps SF export column names to internal standardized names
SCREAMING_FROG_COLUMNS = {
    # Core URL data
    "Address": "url",
    "Content Type": "content_type",
    "Status Code": "status_code",
    "Status": "status",
    "Indexability": "indexability",
    "Indexability Status": "indexability_status",

    # Title tag
    "Title 1": "title",
    "Title 1 Length": "title_length",
    "Title 1 Pixel Width": "title_pixel_width",
    "Title 2": "title_2",  # Multiple titles detected

    # Meta description
    "Meta Description 1": "meta_description",
    "Meta Description 1 Length": "meta_desc_length",
    "Meta Description 1 Pixel Width": "meta_desc_pixel_width",
    "Meta Description 2": "meta_description_2",  # Multiple meta descs

    # Headings
    "H1-1": "h1",
    "H1-1 Length": "h1_length",
    "H1-2": "h1_2",  # Multiple H1s
    "H2-1": "h2",
    "H2-1 Length": "h2_length",

    # Content metrics
    "Word Count": "word_count",
    "Sentence Count": "sentence_count",
    "Average Words Per Sentence": "avg_words_per_sentence",
    "Flesch Reading Ease Score": "flesch_score",
    "Readability": "readability",
    "Text Ratio": "text_ratio",

    # Technical - Canonicals
    "Canonical Link Element 1": "canonical",
    "Canonical Link Element 2": "canonical_2",
    "rel=\"canonical\"": "has_canonical",
    "Canonical Link Element Source": "canonical_source",

    # Technical - Robots
    "Meta Robots 1": "meta_robots",
    "Meta Robots 2": "meta_robots_2",
    "X-Robots-Tag 1": "x_robots_tag",
    "Robots.txt Status": "robots_txt_status",

    # Redirects
    "Redirect URL": "redirect_url",
    "Redirect Type": "redirect_type",
    "Redirect Chain": "redirect_chain",
    "Number of Redirects": "redirect_count",

    # Links
    "Unique Inlinks": "internal_links_in",
    "Unique Outlinks": "internal_links_out",
    "External Outlinks": "external_links_out",
    "Follow": "follow_links",
    "No Follow": "nofollow_links",
    "Sponsored": "sponsored_links",
    "UGC": "ugc_links",
    "Unique JS Inlinks": "js_inlinks",
    "Unique JS Outlinks": "js_outlinks",
    "Link Score": "link_score",

    # Images
    "Images": "image_count",
    "Images with Missing Alt Text": "missing_alt",
    "Images Over 100KB": "large_images",

    # Structured Data
    "Structured Data": "structured_data",
    "Contains Structured Data": "has_structured_data",

    # URL properties
    "URL Length": "url_length",
    "Path Length": "path_length",
    "Depth": "url_depth",
    "Query String": "query_string",
    "Contains Underscores": "has_underscores",
    "Contains Uppercase": "has_uppercase",
    "Contains Multiple Slashes": "has_multiple_slashes",
    "Contains Repetitive Paths": "has_repetitive_paths",
    "Contains Parameters": "has_parameters",

    # Response
    "Response Time": "response_time",
    "Last Modified": "last_modified",
    "Size (Bytes)": "size_bytes",
    "Transfer Encoding": "transfer_encoding",
    "HTTP/2": "http2",

    # Crawl info
    "Crawl Depth": "crawl_depth",
    "Found At": "found_at",
    "Link Type": "link_type",
    "Link Path": "link_path",

    # GSC Integration (optional)
    "Clicks": "gsc_clicks",
    "Impressions": "gsc_impressions",
    "CTR": "gsc_ctr",
    "Position": "gsc_position",
    "GSC URL": "gsc_url",

    # PageSpeed Integration (optional)
    "Largest Contentful Paint Time (s)": "lcp",
    "Total Blocking Time (ms)": "tbt",
    "Cumulative Layout Shift": "cls",
    "First Contentful Paint Time (s)": "fcp",
    "Speed Index (s)": "speed_index",
    "Time to Interactive (s)": "tti",
    "Performance Score": "performance_score",
    "Accessibility Score": "accessibility_score",
    "Best Practices Score": "best_practices_score",
    "SEO Score": "seo_score",

    # GA4 Integration (optional)
    "Sessions": "ga_sessions",
    "Page Views": "ga_pageviews",
    "Bounce Rate": "ga_bounce_rate",
    "Avg. Session Duration": "ga_avg_session_duration",
    "Conversions": "ga_conversions",
    "Revenue": "ga_revenue",
}

# Reverse mapping for lookup
COLUMN_TO_SF = {v: k for k, v in SCREAMING_FROG_COLUMNS.items()}


def parse_screaming_frog_export(
    file: BytesIO | str | Path,
    file_type: Optional[str] = None
) -> pd.DataFrame:
    """Parse a Screaming Frog export file.

    Args:
        file: File path, BytesIO object, or Path object
        file_type: Optional file type hint ('csv' or 'xlsx')

    Returns:
        DataFrame with standardized column names
    """
    # Determine file type
    if file_type is None:
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            file_type = file_path.suffix.lower().replace(".", "")
        elif hasattr(file, "name"):
            file_type = Path(file.name).suffix.lower().replace(".", "")
        else:
            # Try to detect from content
            file_type = "xlsx"  # Default to Excel

    # Read file
    if file_type in ["xlsx", "xls"]:
        df = pd.read_excel(file, engine="openpyxl")
    elif file_type == "csv":
        df = _read_csv_robust(file)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    # Rename columns to standardized names
    df = rename_columns(df)

    # Clean data
    df = clean_data(df)

    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns from Screaming Frog names to standardized names.

    Args:
        df: DataFrame with original column names

    Returns:
        DataFrame with standardized column names
    """
    rename_map = {}
    for col in df.columns:
        # Direct match
        if col in SCREAMING_FROG_COLUMNS:
            rename_map[col] = SCREAMING_FROG_COLUMNS[col]
        else:
            # Case-insensitive match
            col_lower = col.lower().strip()
            for sf_col, std_col in SCREAMING_FROG_COLUMNS.items():
                if sf_col.lower() == col_lower:
                    rename_map[col] = std_col
                    break

    return df.rename(columns=rename_map)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize data in the DataFrame.

    Args:
        df: DataFrame to clean

    Returns:
        Cleaned DataFrame
    """
    # Convert status code to integer
    if "status_code" in df.columns:
        df["status_code"] = pd.to_numeric(df["status_code"], errors="coerce").fillna(0).astype(int)

    # Convert numeric columns
    numeric_columns = [
        "title_length", "meta_desc_length", "h1_length", "word_count",
        "internal_links_in", "internal_links_out", "missing_alt",
        "url_length", "url_depth", "response_time", "size_bytes",
        "gsc_clicks", "gsc_impressions", "gsc_position",
        "lcp", "tbt", "cls", "performance_score",
        "redirect_count", "crawl_depth"
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert percentage columns (remove % if present)
    pct_columns = ["gsc_ctr", "text_ratio", "ga_bounce_rate"]
    for col in pct_columns:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace("%", "").str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalize boolean-like columns
    bool_columns = ["has_canonical", "has_structured_data", "has_underscores",
                    "has_uppercase", "has_parameters", "http2"]
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().isin(["true", "yes", "1", "✓"])

    # Strip whitespace from string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        # Replace "nan" strings with empty
        df[col] = df[col].replace("nan", "")

    return df


def detect_columns(df: pd.DataFrame) -> dict:
    """Detect which Screaming Frog columns are available.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary with column availability info
    """
    available = {
        "core": [],
        "title": [],
        "meta": [],
        "headings": [],
        "content": [],
        "technical": [],
        "links": [],
        "images": [],
        "gsc": [],
        "pagespeed": [],
        "ga4": [],
    }

    # Map columns to categories
    category_mapping = {
        "core": ["url", "content_type", "status_code", "status", "indexability", "indexability_status"],
        "title": ["title", "title_length", "title_pixel_width", "title_2"],
        "meta": ["meta_description", "meta_desc_length", "meta_description_2"],
        "headings": ["h1", "h1_length", "h1_2", "h2", "h2_length"],
        "content": ["word_count", "sentence_count", "flesch_score", "readability", "text_ratio"],
        "technical": ["canonical", "canonical_2", "meta_robots", "x_robots_tag", "robots_txt_status",
                      "redirect_url", "redirect_type", "redirect_count", "response_time", "http2"],
        "links": ["internal_links_in", "internal_links_out", "external_links_out",
                  "follow_links", "nofollow_links", "link_score"],
        "images": ["image_count", "missing_alt", "large_images"],
        "gsc": ["gsc_clicks", "gsc_impressions", "gsc_ctr", "gsc_position"],
        "pagespeed": ["lcp", "tbt", "cls", "fcp", "speed_index", "tti", "performance_score"],
        "ga4": ["ga_sessions", "ga_pageviews", "ga_bounce_rate", "ga_conversions"],
    }

    for category, columns in category_mapping.items():
        available[category] = [col for col in columns if col in df.columns]

    return available


def detect_integrations(df: pd.DataFrame) -> dict:
    """Detect which Screaming Frog integrations have data.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary with integration status
    """
    columns = detect_columns(df)

    # Check if columns exist AND have non-null data
    def has_data(column_list: list) -> bool:
        for col in column_list:
            if col in df.columns:
                non_null = df[col].notna().sum()
                if non_null > 0:
                    return True
        return False

    return {
        "gsc": has_data(columns["gsc"]),
        "pagespeed": has_data(columns["pagespeed"]),
        "ga4": has_data(columns["ga4"]),
        "has_titles": has_data(columns["title"]),
        "has_meta": has_data(columns["meta"]),
        "has_content_metrics": has_data(columns["content"]),
        "has_link_metrics": has_data(columns["links"]),
    }


def get_domain_from_urls(df: pd.DataFrame) -> Optional[str]:
    """Extract the primary domain from URLs in the DataFrame.

    Args:
        df: DataFrame with 'url' column

    Returns:
        Primary domain or None
    """
    if "url" not in df.columns:
        return None

    # Get first valid URL
    urls = df["url"].dropna()
    if urls.empty:
        return None

    first_url = urls.iloc[0]

    # Extract domain
    domain_pattern = r"https?://([^/]+)"
    match = re.match(domain_pattern, str(first_url))
    if match:
        return match.group(1)

    return None


def get_export_summary(df: pd.DataFrame) -> dict:
    """Get summary statistics about the export.

    Args:
        df: DataFrame to summarize

    Returns:
        Dictionary with summary statistics
    """
    integrations = detect_integrations(df)
    columns = detect_columns(df)

    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "domain": get_domain_from_urls(df),
        "integrations": integrations,
        "column_categories": {k: len(v) for k, v in columns.items()},
    }

    # Count by status code
    if "status_code" in df.columns:
        status_counts = df["status_code"].value_counts().to_dict()
        summary["status_codes"] = {
            "2xx": sum(v for k, v in status_counts.items() if 200 <= k < 300),
            "3xx": sum(v for k, v in status_counts.items() if 300 <= k < 400),
            "4xx": sum(v for k, v in status_counts.items() if 400 <= k < 500),
            "5xx": sum(v for k, v in status_counts.items() if 500 <= k < 600),
        }

    # Count by indexability
    if "indexability" in df.columns:
        indexability_counts = df["indexability"].value_counts().to_dict()
        summary["indexability"] = indexability_counts

    # Content type breakdown
    if "content_type" in df.columns:
        content_types = df["content_type"].value_counts().head(5).to_dict()
        summary["content_types"] = content_types

    return summary
