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


def _detect_delimiter(file: Union[BytesIO, str, Path], encoding: str = "utf-8") -> str:
    """Detect the delimiter used in a CSV file.

    Args:
        file: File path or BytesIO object
        encoding: Encoding to use for reading

    Returns:
        Detected delimiter character
    """
    try:
        if isinstance(file, BytesIO):
            file.seek(0)
            sample = file.read(8192).decode(encoding, errors="ignore")
            file.seek(0)
        else:
            with open(file, "r", encoding=encoding, errors="ignore") as f:
                sample = f.read(8192)

        # Count potential delimiters in the first line
        first_line = sample.split("\n")[0] if "\n" in sample else sample

        delimiters = {
            ";": first_line.count(";"),
            ",": first_line.count(","),
            "\t": first_line.count("\t"),
        }

        # Return delimiter with most occurrences (minimum 2 to be considered)
        best_delim = max(delimiters, key=delimiters.get)
        if delimiters[best_delim] >= 2:
            return best_delim

        return ","  # Default to comma
    except Exception:
        return ","


def _read_csv_robust(file: Union[BytesIO, str, Path]) -> pd.DataFrame:
    """Read CSV with robust error handling for malformed rows.

    Handles common issues with Screaming Frog exports:
    - Inconsistent column counts (commas in content fields)
    - Different encodings (UTF-8, Latin-1)
    - Various quoting styles
    - Different delimiters (comma, semicolon, tab)

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

            # Detect delimiter
            delimiter = _detect_delimiter(file, encoding)
            print(f"[DEBUG] Detected delimiter: '{delimiter}' (semicolon={delimiter==';'})")

            if isinstance(file, BytesIO):
                file.seek(0)

            # First try: standard pandas with flexible error handling
            try:
                df = pd.read_csv(
                    file,
                    encoding=encoding,
                    sep=delimiter,
                    on_bad_lines="warn",  # Skip malformed rows with warning
                    low_memory=False,
                    dtype=str,  # Read all as strings first to avoid type issues
                )
                if len(df) > 0:
                    print(f"[DEBUG] Successfully read {len(df)} rows with {len(df.columns)} columns")
                    return df
            except TypeError:
                # Older pandas version - use error_bad_lines
                if isinstance(file, BytesIO):
                    file.seek(0)
                df = pd.read_csv(
                    file,
                    encoding=encoding,
                    sep=delimiter,
                    error_bad_lines=False,
                    warn_bad_lines=True,
                    low_memory=False,
                    dtype=str,
                )
                if len(df) > 0:
                    print(f"[DEBUG] Successfully read {len(df)} rows with {len(df.columns)} columns")
                    return df

        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError:
            # Try Python engine which is more flexible
            try:
                if isinstance(file, BytesIO):
                    file.seek(0)
                delimiter = _detect_delimiter(file, encoding)
                if isinstance(file, BytesIO):
                    file.seek(0)
                df = pd.read_csv(
                    file,
                    encoding=encoding,
                    sep=delimiter,
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

    # Detect delimiter from text
    first_line = text.split("\n")[0] if "\n" in text else text
    delimiters = {";": first_line.count(";"), ",": first_line.count(","), "\t": first_line.count("\t")}
    delimiter = max(delimiters, key=delimiters.get) if max(delimiters.values()) >= 2 else ","

    # Parse manually with csv module
    lines = text.splitlines()
    if not lines:
        raise ValueError("Empty CSV file")

    reader = csv.reader(StringIO(text), delimiter=delimiter)
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
    "Meta Keywords 1": "meta_keywords",

    # Headings
    "H1-1": "h1",
    "H1-1 Length": "h1_length",
    "H1-2": "h1_2",  # Multiple H1s
    "H2-1": "h2",
    "H2-1 Length": "h2_length",
    "H2-2": "h2_2",

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
    "Meta Refresh 1": "meta_refresh",

    # Meta robots PLACEMENT (head vs body) — NOT a native Screaming Frog
    # column. Google ignores a noindex placed outside <head>, but a standard
    # SF crawl cannot tell where in the document the tag sits. This data only
    # exists when the crawl includes a custom extraction (XPath/regex) that
    # captures the tag's location. These header variants are the common names
    # such an extraction is given; they gate `_check_noindex_in_body` in the
    # technical auditor (which no-ops when the column is absent — by design).
    "Meta Robots Position": "meta_robots_position",
    "Meta Robots Placement": "meta_robots_position",
    "Robots Position": "robots_position",
    "Meta Robots Location": "meta_robots_location",

    # Redirects
    "Redirect URL": "redirect_url",
    "Redirect Type": "redirect_type",
    "Redirect Chain": "redirect_chain",
    "Number of Redirects": "redirect_count",

    # Links - support both "Inlinks" and "Unique Inlinks" naming
    "Inlinks": "inlinks_total",
    "Unique Inlinks": "internal_links_in",
    "Outlinks": "outlinks_total",
    "Unique Outlinks": "internal_links_out",
    "External Outlinks": "external_links_out",
    "Unique External Outlinks": "external_links_unique",
    "Unique External JS Outlinks": "external_js_outlinks",
    "% of Total": "inlinks_percent",
    "Follow": "follow_links",
    "No Follow": "nofollow_links",
    "Sponsored": "sponsored_links",
    "UGC": "ugc_links",
    "Unique JS Inlinks": "js_inlinks",
    "Unique JS Outlinks": "js_outlinks",
    "Link Score": "link_score",

    # JavaScript Rendering — comparison columns from Screaming Frog's
    # Response vs Render report (only present when JS rendering is enabled).
    # SF column naming varies by version, so map several known variants.
    "Raw Word Count": "raw_word_count",
    "Source Word Count": "raw_word_count",
    "Word Count (Raw)": "raw_word_count",
    "Rendered Word Count": "rendered_word_count",
    "Word Count (Rendered)": "rendered_word_count",
    "Raw HTML Word Count": "raw_word_count",
    "Rendered HTML Word Count": "rendered_word_count",
    "Source HTML Word Count": "raw_word_count",
    "Raw Outlinks": "raw_outlinks",
    "Rendered Outlinks": "rendered_outlinks",
    "Outlinks (Raw)": "raw_outlinks",
    "Outlinks (Rendered)": "rendered_outlinks",
    "Raw Inlinks": "raw_inlinks",
    "Rendered Inlinks": "rendered_inlinks",
    "Raw HTML Size (Bytes)": "raw_html_size",
    "Rendered HTML Size (Bytes)": "rendered_html_size",
    "Page Size (Raw)": "raw_html_size",
    "Page Size (Rendered)": "rendered_html_size",
    "DOM Size": "dom_size",
    "Total DOM Size": "dom_size",
    "Source: Title 1": "raw_title",
    "Raw Title 1": "raw_title",
    "Title 1 (Raw)": "raw_title",
    "Source: Meta Description 1": "raw_meta_description",
    "Raw Meta Description 1": "raw_meta_description",
    "Source: H1-1": "raw_h1",
    "Raw H1-1": "raw_h1",
    "Source: Canonical Link Element 1": "raw_canonical",
    "Raw Canonical Link Element 1": "raw_canonical",
    "Source: Meta Robots 1": "raw_meta_robots",
    "Raw Meta Robots 1": "raw_meta_robots",
    "Crawl Mode": "crawl_mode",
    "Rendered Crawl": "rendered_crawl",
    "JavaScript Rendered": "js_rendered",

    # Images
    "Images": "image_count",
    "Images with Missing Alt Text": "missing_alt",
    "Images Over 100KB": "large_images",

    # Structured Data
    "Structured Data": "structured_data",
    "Contains Structured Data": "has_structured_data",
    "Rich Results": "rich_results",
    "Rich Results Types": "rich_results_types",

    # URL properties
    "URL Length": "url_length",
    "Path Length": "path_length",
    "Depth": "url_depth",
    "Folder Depth": "folder_depth",
    "Query String": "query_string",
    "Contains Underscores": "has_underscores",
    "Contains Uppercase": "has_uppercase",
    "Contains Multiple Slashes": "has_multiple_slashes",
    "Contains Repetitive Paths": "has_repetitive_paths",
    "Contains Parameters": "has_parameters",
    "Hash": "url_hash",
    "URL Encoded Address": "url_encoded",

    # Response - support both casing
    "Response Time": "response_time",
    "Last Modified": "last_modified",
    "Size (Bytes)": "size_bytes",
    "Size (bytes)": "size_bytes",
    "Transferred (bytes)": "transferred_bytes",
    "Total Transferred (bytes)": "total_transferred_bytes",
    "Transfer Encoding": "transfer_encoding",
    "HTTP/2": "http2",
    "HTTP Version": "http_version",
    "Cookies": "cookies",
    "Language": "language",

    # Crawl info
    "Crawl Depth": "crawl_depth",
    "Found At": "found_at",
    "Link Type": "link_type",
    "Link Path": "link_path",
    "Crawl Timestamp": "crawl_timestamp",

    # Similarity/Duplicates
    "Closest Similarity Match": "similarity_match",
    "No. Near Duplicates": "near_duplicates",

    # Spelling/Grammar
    "Spelling Errors": "spelling_errors",
    "Grammar Errors": "grammar_errors",

    # Carbon/Environmental
    "CO2 (mg)": "co2_mg",
    "Carbon Rating": "carbon_rating",

    # GSC Integration (optional)
    "Clicks": "gsc_clicks",
    "Impressions": "gsc_impressions",
    "CTR": "gsc_ctr",
    "Position": "gsc_position",
    "GSC URL": "gsc_url",

    # GSC URL Inspection API
    "URL Inspection API Status": "url_inspection_status",
    "URL Inspection API Error": "url_inspection_error",
    "Summary": "url_inspection_summary",
    "Coverage": "url_inspection_coverage",
    "Last Crawl": "gsc_last_crawl",
    "Days Since Last Crawled": "days_since_crawled",
    "Crawled As": "crawled_as",
    "Crawl Allowed": "crawl_allowed",
    "Page Fetch": "page_fetch",
    "Indexing Allowed": "indexing_allowed",
    "User-Declared Canonical": "user_canonical",
    "Google-Selected Canonical": "google_canonical",
    "Mobile Usability": "mobile_usability",
    "Mobile Usability Issues": "mobile_usability_issues",
    "AMP Results": "amp_results",
    "AMP Issues": "amp_issues",
    "Rich Results Type Errors": "rich_results_errors",
    "Rich Results Type Warnings": "rich_results_warnings",

    # PageSpeed Integration (optional) - support both seconds and milliseconds
    "Largest Contentful Paint Time (s)": "lcp",
    "Largest Contentful Paint Time (ms)": "lcp_ms",
    "Total Blocking Time (ms)": "tbt",
    "Cumulative Layout Shift": "cls",
    "First Contentful Paint Time (s)": "fcp",
    "First Contentful Paint Time (ms)": "fcp_ms",
    "Speed Index (s)": "speed_index",
    "Speed Index Time (ms)": "speed_index_ms",
    "Time to Interactive (s)": "tti",
    "Time to Interactive (ms)": "tti_ms",
    "Time to First Byte (ms)": "ttfb_ms",
    "Performance Score": "performance_score",
    "Accessibility Score": "accessibility_score",
    "Best Practices Score": "best_practices_score",
    "SEO Score": "seo_score",

    # GA4 Integration (optional) - support both naming conventions
    "Sessions": "ga_sessions",
    "GA4 Sessions": "ga_sessions",
    "Page Views": "ga_pageviews",
    "GA4 Views": "ga_pageviews",
    "Bounce Rate": "ga_bounce_rate",
    "GA4 Bounce rate": "ga_bounce_rate",
    "Avg. Session Duration": "ga_avg_session_duration",
    "GA4 Average session duration": "ga_avg_session_duration",
    "Conversions": "ga_conversions",
    "Revenue": "ga_revenue",
    "GA4 Total users": "ga_total_users",
    "GA4 New users": "ga_new_users",

    # Mobile/AMP
    "amphtml Link Element": "amphtml_link",
    "Mobile Alternate Link": "mobile_alternate_link",

    # Hreflang / international — Screaming Frog stores each declared hreflang
    # annotation on a page as a numbered column pair (the alternate URL and its
    # language code). Header naming varies by SF version, so several known
    # variants map to the same internal name. The numbered variants (1..10) are
    # generated below and merged in — see _HREFLANG_COLUMN_VARIANTS.

    # Misc
    "Published Date 1": "published_date",
    "rel=\"next\" 1": "rel_next",
    "rel=\"prev\" 1": "rel_prev",
    "HTTP rel=\"next\" 1": "http_rel_next",
    "HTTP rel=\"prev\" 1": "http_rel_prev",
}

def _build_hreflang_column_variants(max_annotations: int = 10) -> dict:
    """Generate SF hreflang column-name variants -> internal names.

    Screaming Frog exports each declared hreflang annotation on a page as a
    numbered column. The alternate-URL column and (when languages are stored)
    the language-code column both vary in wording across SF versions, so every
    known variant for annotation ``i`` maps onto the internal names
    ``hreflang_{i}_url`` and ``hreflang_{i}_lang``.

    Args:
        max_annotations: Highest annotation index to generate columns for.

    Returns:
        Mapping of SF header string -> internal standardized column name.
    """
    variants: dict = {}
    for i in range(1, max_annotations + 1):
        url_name = f"hreflang_{i}_url"
        lang_name = f"hreflang_{i}_lang"
        for header in (
            f"hreflang {i}",
            f"hreflang {i} URL",
            f"HTML hreflang {i}",
            f"HTML hreflang {i} URL",
        ):
            variants[header] = url_name
        for header in (
            f"hreflang {i} Language",
            f"hreflang {i} Language Code",
            f"HTML hreflang {i} Language",
            f"HTML hreflang {i} Language Code",
        ):
            variants[header] = lang_name
    return variants


# Merge the generated hreflang variants in. Explicit entries in
# SCREAMING_FROG_COLUMNS win over generated ones if they ever collide.
_HREFLANG_COLUMN_VARIANTS = _build_hreflang_column_variants()
for _sf_header, _internal_name in _HREFLANG_COLUMN_VARIANTS.items():
    SCREAMING_FROG_COLUMNS.setdefault(_sf_header, _internal_name)


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
    # First, strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {}
    for col in df.columns:
        # Direct match
        if col in SCREAMING_FROG_COLUMNS:
            rename_map[col] = SCREAMING_FROG_COLUMNS[col]
        else:
            # Case-insensitive match
            col_lower = col.lower()
            for sf_col, std_col in SCREAMING_FROG_COLUMNS.items():
                if sf_col.lower() == col_lower:
                    rename_map[col] = std_col
                    break

    # Print debug info (can be seen in terminal)
    print(f"[DEBUG] Original columns ({len(df.columns)}): {list(df.columns)[:10]}...")
    print(f"[DEBUG] Mapped {len(rename_map)} columns: {list(rename_map.values())[:10]}...")

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
        "sentence_count", "avg_words_per_sentence", "flesch_score",
        "internal_links_in", "internal_links_out", "inlinks_total",
        "outlinks_total", "external_links_out", "missing_alt",
        "url_length", "url_depth", "folder_depth", "response_time",
        "size_bytes", "transferred_bytes",
        "gsc_clicks", "gsc_impressions", "gsc_position",
        "lcp", "lcp_ms", "tbt", "cls", "fcp", "fcp_ms",
        "speed_index", "speed_index_ms", "tti", "tti_ms", "ttfb_ms",
        "performance_score", "redirect_count", "crawl_depth",
        "near_duplicates", "spelling_errors", "grammar_errors",
        "ga_sessions", "ga_pageviews", "ga_total_users", "ga_new_users",
        "link_score", "image_count",
        # JS rendering comparison metrics
        "raw_word_count", "rendered_word_count",
        "raw_outlinks", "rendered_outlinks",
        "raw_inlinks", "rendered_inlinks",
        "raw_html_size", "rendered_html_size", "dom_size",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Convert millisecond PageSpeed metrics to seconds if not already present
    ms_to_s_conversions = {
        "lcp_ms": "lcp",
        "fcp_ms": "fcp",
        "speed_index_ms": "speed_index",
        "tti_ms": "tti",
        "ttfb_ms": "ttfb",
    }
    for ms_col, s_col in ms_to_s_conversions.items():
        if ms_col in df.columns and s_col not in df.columns:
            df[s_col] = df[ms_col] / 1000.0
            print(f"[DEBUG] Converted {ms_col} to {s_col} (ms -> seconds)")

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
        "core": ["url", "content_type", "status_code", "status",
                 "indexability", "indexability_status"],
        "title": ["title", "title_length", "title_pixel_width", "title_2"],
        "meta": ["meta_description", "meta_desc_length", "meta_description_2"],
        "headings": ["h1", "h1_length", "h1_2", "h2", "h2_length"],
        "content": ["word_count", "sentence_count", "flesch_score",
                    "readability", "text_ratio"],
        "technical": ["canonical", "canonical_2", "meta_robots", "x_robots_tag",
                      "robots_txt_status", "redirect_url", "redirect_type",
                      "redirect_count", "response_time", "http2"],
        "links": ["internal_links_in", "internal_links_out", "inlinks_total",
                  "outlinks_total", "external_links_out", "follow_links",
                  "nofollow_links", "link_score"],
        "images": ["image_count", "missing_alt", "large_images"],
        "gsc": ["gsc_clicks", "gsc_impressions", "gsc_ctr", "gsc_position"],
        "pagespeed": ["lcp", "lcp_ms", "tbt", "cls", "fcp", "fcp_ms",
                      "speed_index", "speed_index_ms", "tti", "tti_ms",
                      "ttfb_ms", "performance_score"],
        "ga4": ["ga_sessions", "ga_pageviews", "ga_bounce_rate",
                "ga_total_users", "ga_new_users", "ga_conversions"],
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


# ============================================================================
# Expanded Input Stack — leak-grounded framework inputs
# ============================================================================
#
# The Google API leak (May 2024) and Cyrus Shepard's click-signal analysis
# require additional inputs beyond the SF Internal HTML report to fully ground
# the audit in evidence:
#
#   1. SF HTML Internal report      — core crawl (already supported above)
#   2. SEMrush backlink report      — domain authority + anchor sourceType tiers
#   3. SF Anchor Text report        — anchorMismatchDemotion + phraseAnchorSpam
#   4. SF custom extraction (dates) — semanticDate / lastSignificantUpdate
#   5. GSC Search Analytics export  — position-adjusted CTR + click signals
#   6. Koray topical map (markdown) — siteFocusScore / siteRadius proxy
#
# Each parser below is defensive — it accepts varying column names from the
# common export sources and produces a standardized DataFrame for the auditor.


# SEMrush backlink export column mappings
SEMRUSH_BACKLINK_COLUMNS = {
    "Source URL": "source_url",
    "Source url": "source_url",
    "Page URL": "source_url",
    "Source Title": "source_title",
    "Target URL": "target_url",
    "Target url": "target_url",
    "Target Page": "target_url",
    "Anchor": "anchor_text",
    "Anchor Text": "anchor_text",
    "Source Domain": "source_domain",
    "Source Domain Authority": "source_authority",
    "Authority Score": "source_authority",
    "Page AS": "page_authority",
    "Domain AS": "source_authority",
    "Source IP": "source_ip",
    "Source Country": "source_country",
    "First Seen": "first_seen",
    "Last Seen": "last_seen",
    "Type": "link_type",
    "Link Type": "link_type",
    "Nofollow": "nofollow",
    "Newlink": "is_new",
    "Lostlink": "is_lost",
    "External Links": "external_links_on_page",
    "Internal Links": "internal_links_on_page",
}


def parse_semrush_backlinks(file: BytesIO | str | Path) -> pd.DataFrame:
    """Parse a SEMrush backlinks export.

    Args:
        file: File path or BytesIO object containing SEMrush backlink CSV/Excel

    Returns:
        DataFrame with standardized columns: source_url, target_url, anchor_text,
        source_domain, source_authority, link_type, nofollow, first_seen, last_seen
    """
    file_type = _infer_file_type(file)

    if file_type in ("xlsx", "xls"):
        df = pd.read_excel(file, engine="openpyxl")
    else:
        df = _read_csv_robust(file)

    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {}
    for col in df.columns:
        if col in SEMRUSH_BACKLINK_COLUMNS:
            rename_map[col] = SEMRUSH_BACKLINK_COLUMNS[col]
        else:
            col_lower = col.lower()
            for sr_col, std_col in SEMRUSH_BACKLINK_COLUMNS.items():
                if sr_col.lower() == col_lower:
                    rename_map[col] = std_col
                    break

    df = df.rename(columns=rename_map)

    if "source_authority" in df.columns:
        df["source_authority"] = pd.to_numeric(df["source_authority"], errors="coerce")

    if "nofollow" in df.columns:
        df["nofollow"] = df["nofollow"].astype(str).str.lower().isin(["true", "yes", "1"])

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace("nan", "")

    print(f"[DEBUG] SEMrush backlinks: {len(df)} rows, columns: {list(df.columns)[:10]}")
    return df


# Screaming Frog Anchor Text report column mappings
SF_ANCHOR_COLUMNS = {
    "Source": "source_url",
    "Source URL": "source_url",
    "Destination": "target_url",
    "Target": "target_url",
    "Destination URL": "target_url",
    "Anchor": "anchor_text",
    "Anchor Text": "anchor_text",
    "Alt Text": "alt_text",
    "Type": "link_type",
    "Link Type": "link_type",
    "Position": "link_position",
    "Link Position": "link_position",
    "Status Code": "target_status_code",
    "Status": "target_status",
    "Follow": "follow",
    "Rel": "rel",
    "Link Path": "link_path",
}


def parse_sf_anchor_report(file: BytesIO | str | Path) -> pd.DataFrame:
    """Parse a Screaming Frog Anchor Text (All Anchor Text) report.

    Args:
        file: File path or BytesIO containing SF anchor export

    Returns:
        DataFrame with: source_url, target_url, anchor_text, link_type, follow, rel
    """
    file_type = _infer_file_type(file)

    if file_type in ("xlsx", "xls"):
        df = pd.read_excel(file, engine="openpyxl")
    else:
        df = _read_csv_robust(file)

    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {}
    for col in df.columns:
        if col in SF_ANCHOR_COLUMNS:
            rename_map[col] = SF_ANCHOR_COLUMNS[col]
        else:
            col_lower = col.lower()
            for sf_col, std_col in SF_ANCHOR_COLUMNS.items():
                if sf_col.lower() == col_lower:
                    rename_map[col] = std_col
                    break

    df = df.rename(columns=rename_map)

    if "target_status_code" in df.columns:
        df["target_status_code"] = pd.to_numeric(
            df["target_status_code"], errors="coerce"
        ).fillna(0).astype(int)

    if "follow" in df.columns:
        df["follow"] = df["follow"].astype(str).str.lower().isin(["true", "yes", "1"])

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace("nan", "")

    print(f"[DEBUG] SF anchors: {len(df)} rows, columns: {list(df.columns)[:10]}")
    return df


# Content publish/update dates extraction column mappings
CONTENT_DATES_COLUMNS = {
    "Address": "url",
    "URL": "url",
    "Page URL": "url",
    "Published Date 1": "byline_date",
    "Published Date": "byline_date",
    "Byline Date": "byline_date",
    "Date Published": "byline_date",
    "Visible Date": "byline_date",
    "Article Published Date": "byline_date",
    "datePublished": "schema_published",
    "Schema Date Published": "schema_published",
    "Schema Published": "schema_published",
    "Schema datePublished": "schema_published",
    "dateModified": "schema_modified",
    "Schema Date Modified": "schema_modified",
    "Schema Modified": "schema_modified",
    "Schema dateModified": "schema_modified",
    "Last Modified": "last_modified",
    "HTTP Last Modified": "last_modified",
    "Last-Modified": "last_modified",
    "Author": "author",
    "Author Name": "author",
    "Schema Author": "schema_author",
}


def parse_content_dates(file: BytesIO | str | Path) -> pd.DataFrame:
    """Parse a Screaming Frog custom extraction report for content dates.

    Expected to contain at minimum: URL, byline date (visible), schema dates,
    and HTTP Last-Modified header. Used for date triangulation against
    semanticDate and lastSignificantUpdate signals.

    Args:
        file: File path or BytesIO containing custom extraction CSV/Excel

    Returns:
        DataFrame with: url, byline_date, schema_published, schema_modified,
        last_modified, author
    """
    file_type = _infer_file_type(file)

    if file_type in ("xlsx", "xls"):
        df = pd.read_excel(file, engine="openpyxl")
    else:
        df = _read_csv_robust(file)

    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {}
    for col in df.columns:
        if col in CONTENT_DATES_COLUMNS:
            rename_map[col] = CONTENT_DATES_COLUMNS[col]
        else:
            col_lower = col.lower()
            for sf_col, std_col in CONTENT_DATES_COLUMNS.items():
                if sf_col.lower() == col_lower:
                    rename_map[col] = std_col
                    break

    df = df.rename(columns=rename_map)

    date_columns = ["byline_date", "schema_published", "schema_modified", "last_modified"]
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace("nan", "")

    print(f"[DEBUG] Content dates: {len(df)} rows, columns: {list(df.columns)[:10]}")
    return df


# GSC Search Analytics export column mappings
GSC_PERFORMANCE_COLUMNS = {
    "Query": "query",
    "Top queries": "query",
    "Queries": "query",
    "Page": "page",
    "Pages": "page",
    "Top pages": "page",
    "Landing Page": "page",
    "Clicks": "clicks",
    "Impressions": "impressions",
    "CTR": "ctr",
    "Average CTR": "ctr",
    "Position": "position",
    "Average Position": "position",
    "Country": "country",
    "Device": "device",
    "Date": "date",
}


def parse_gsc_performance(file: BytesIO | str | Path) -> pd.DataFrame:
    """Parse a GSC Search Analytics export.

    Accepts the standard GSC web export (CSV) with query/page dimensions.
    Used for position-adjusted CTR analysis and click-signal grounding.

    Args:
        file: File path or BytesIO containing GSC export

    Returns:
        DataFrame with: query, page, clicks, impressions, ctr, position
    """
    file_type = _infer_file_type(file)

    if file_type in ("xlsx", "xls"):
        df = pd.read_excel(file, engine="openpyxl")
    else:
        df = _read_csv_robust(file)

    df.columns = [str(c).strip() for c in df.columns]

    rename_map = {}
    for col in df.columns:
        if col in GSC_PERFORMANCE_COLUMNS:
            rename_map[col] = GSC_PERFORMANCE_COLUMNS[col]
        else:
            col_lower = col.lower()
            for gsc_col, std_col in GSC_PERFORMANCE_COLUMNS.items():
                if gsc_col.lower() == col_lower:
                    rename_map[col] = std_col
                    break

    df = df.rename(columns=rename_map)

    if "clicks" in df.columns:
        df["clicks"] = pd.to_numeric(df["clicks"], errors="coerce").fillna(0).astype(int)
    if "impressions" in df.columns:
        df["impressions"] = pd.to_numeric(df["impressions"], errors="coerce").fillna(0).astype(int)
    if "position" in df.columns:
        df["position"] = pd.to_numeric(df["position"], errors="coerce")

    if "ctr" in df.columns:
        if df["ctr"].dtype == object:
            df["ctr"] = df["ctr"].astype(str).str.replace("%", "").str.strip()
        df["ctr"] = pd.to_numeric(df["ctr"], errors="coerce")
        if df["ctr"].max() and df["ctr"].max() > 1:
            df["ctr"] = df["ctr"] / 100.0

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip().replace("nan", "")

    print(f"[DEBUG] GSC performance: {len(df)} rows, columns: {list(df.columns)[:10]}")
    return df


def parse_gsc_index_coverage(
    file: BytesIO | str | Path, status_label: Optional[str] = None
) -> pd.DataFrame:
    """Parse a GSC Page Indexing report export for a single status category.

    Google Search Console has no bulk Index Coverage API — the "Page indexing"
    report (Indexing → Pages) must be exported one status at a time from the
    UI's Export button on that status's detail view. This parser is deliberately
    tolerant of column-name variation across GSC's export formats, since the
    exact header names aren't guaranteed stable across accounts/locales.

    Args:
        file: File path or BytesIO containing the GSC export
        status_label: Status name to tag every row with (e.g. "Crawled - currently
            not indexed"). Used when the export itself has no status/reason column
            — the normal case, since GSC's detail-view export is already filtered
            to one status and only lists URL + last-crawled date.

    Returns:
        DataFrame with: url, index_status, last_crawled (last_crawled only if
        present in the source export)
    """
    file_type = _infer_file_type(file)

    if file_type in ("xlsx", "xls"):
        df = pd.read_excel(file, engine="openpyxl")
    else:
        df = _read_csv_robust(file)

    df.columns = [str(c).strip() for c in df.columns]

    url_candidates = ["URL", "Page", "Address", "url", "page"]
    reason_candidates = ["Reason", "Coverage state", "Indexing state", "Status", "Verdict"]
    date_candidates = ["Last crawled", "Last Crawled", "Date crawled"]

    def _find_column(candidates: list[str]) -> Optional[str]:
        for candidate in candidates:
            for col in df.columns:
                if col.lower() == candidate.lower():
                    return col
        return None

    url_col = _find_column(url_candidates)
    if url_col is None:
        raise ValueError(
            "Could not find a URL column in the GSC Page Indexing export. "
            f"Columns found: {list(df.columns)}"
        )
    df = df.rename(columns={url_col: "url"})

    reason_col = _find_column(reason_candidates)
    if reason_col is not None:
        df = df.rename(columns={reason_col: "index_status"})
    else:
        df["index_status"] = status_label or "unknown"

    date_col = _find_column(date_candidates)
    if date_col is not None:
        df = df.rename(columns={date_col: "last_crawled"})
        df["last_crawled"] = pd.to_datetime(df["last_crawled"], errors="coerce")

    df["url"] = df["url"].astype(str).str.strip()

    keep_cols = [c for c in ("url", "index_status", "last_crawled") if c in df.columns]
    print(f"[DEBUG] GSC index coverage ({status_label or 'unlabeled'}): {len(df)} rows")
    return df[keep_cols]


def parse_topical_map(file: BytesIO | str | Path) -> dict:
    """Parse a Koray-style topical map markdown document.

    Expected structure (any subset is acceptable):
        # Topical Map for <site>
        ## Central Entity
        <one sentence describing what the site is about>
        ## Ring 1 — Core Topics
        - topic / page url
        ## Ring 2 — Supporting Topics
        ## Ring 3 — Peripheral Topics
        ## Outliers
        - off-topic page url

    Args:
        file: File path or BytesIO containing markdown

    Returns:
        Dict with: central_entity (str), rings (dict of ring_name -> list),
        outliers (list), raw_text (str), urls_by_ring (dict)
    """
    if isinstance(file, BytesIO):
        file.seek(0)
        content = file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("utf-8", errors="ignore")
    elif isinstance(file, (str, Path)):
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    else:
        text = str(file)

    result = {
        "central_entity": "",
        "rings": {},
        "outliers": [],
        "raw_text": text,
        "urls_by_ring": {},
    }

    current_section = None
    current_items = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        section_match = re.match(r"^#{1,3}\s+(.*)$", line)
        if section_match:
            if current_section and current_items:
                _assign_section(result, current_section, current_items)
            current_section = section_match.group(1).strip()
            current_items = []
            continue

        if line.startswith(("-", "*", "•")):
            current_items.append(line.lstrip("-*•").strip())
        elif current_section and current_section.lower().startswith("central"):
            current_items.append(line)

    if current_section and current_items:
        _assign_section(result, current_section, current_items)

    url_pattern = re.compile(r"https?://[^\s\)\]]+|/[A-Za-z0-9\-_/]+")
    for ring_name, items in result["rings"].items():
        urls = []
        for item in items:
            urls.extend(url_pattern.findall(item))
        result["urls_by_ring"][ring_name] = urls

    print(
        f"[DEBUG] Topical map: central='{result['central_entity'][:50]}...', "
        f"rings={list(result['rings'].keys())}, outliers={len(result['outliers'])}"
    )
    return result


def _assign_section(result: dict, section: str, items: list) -> None:
    """Helper to route a parsed markdown section into the topical map result."""
    section_lower = section.lower()
    if "central" in section_lower or "entity" in section_lower:
        result["central_entity"] = " ".join(items).strip()
    elif "outlier" in section_lower or "off-topic" in section_lower:
        result["outliers"].extend(items)
    elif "ring" in section_lower or "core" in section_lower or "supporting" in section_lower or "peripheral" in section_lower:
        result["rings"][section] = items


def _infer_file_type(file: BytesIO | str | Path) -> str:
    """Infer file extension from a path or named BytesIO."""
    if isinstance(file, (str, Path)):
        return Path(file).suffix.lower().replace(".", "") or "csv"
    if hasattr(file, "name") and file.name:
        return Path(file.name).suffix.lower().replace(".", "") or "csv"
    return "csv"


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
