"""DataForSEO API Client.

Handles backlink and competitor analysis API calls.
https://dataforseo.com/apis
"""

import requests
import base64
import time
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class BacklinkData:
    """Backlink analysis results."""
    total_backlinks: int = 0
    referring_domains: int = 0
    dofollow_backlinks: int = 0
    nofollow_backlinks: int = 0
    backlinks: list = field(default_factory=list)
    anchors: list = field(default_factory=list)
    referring_domain_list: list = field(default_factory=list)
    domain_rank: Optional[float] = None


@dataclass
class CompetitorData:
    """Competitor analysis results."""
    target_domain: str = ""
    competitors: list = field(default_factory=list)
    ranked_keywords: list = field(default_factory=list)
    total_keywords: int = 0


class DataForSEOClient:
    """Client for DataForSEO APIs.

    Supports:
    - Backlinks API (backlinks, anchors, referring domains)
    - DataForSEO Labs API (competitors, ranked keywords)
    """

    BASE_URL = "https://api.dataforseo.com/v3"

    def __init__(self, login: str, password: str):
        """Initialize the client with credentials.

        Args:
            login: DataForSEO login (email)
            password: DataForSEO API password
        """
        self.login = login
        self.password = password
        self._auth_header = self._create_auth_header()

    def _create_auth_header(self) -> str:
        """Create Basic Auth header."""
        credentials = f"{self.login}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _make_request(
        self,
        endpoint: str,
        data: list,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> dict:
        """Make a POST request to the API.

        Args:
            endpoint: API endpoint path
            data: Request payload
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries (seconds)

        Returns:
            API response as dictionary

        Raises:
            Exception: If request fails after retries
        """
        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "Authorization": self._auth_header,
            "Content-Type": "application/json"
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=data, headers=headers, timeout=60)
                response.raise_for_status()

                result = response.json()

                # Check for API-level errors
                if result.get("status_code") != 20000:
                    error_msg = result.get("status_message", "Unknown API error")
                    raise Exception(f"API Error: {error_msg}")

                return result

            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                continue

        raise Exception(f"Request failed after {max_retries} attempts: {last_error}")

    def test_connection(self) -> bool:
        """Test API connection and credentials.

        Returns:
            True if connection successful
        """
        try:
            # Use a minimal endpoint to test
            url = f"{self.BASE_URL}/appendix/user_data"
            headers = {"Authorization": self._auth_header}
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    # =========================================================================
    # BACKLINKS API
    # =========================================================================

    def get_backlinks(
        self,
        target: str,
        limit: int = 1000,
        order_by: str = "rank,desc"
    ) -> list:
        """Get backlinks for a target domain.

        Args:
            target: Domain or URL to analyze
            limit: Maximum number of backlinks to return
            order_by: Sort order (default: by rank descending)

        Returns:
            List of backlink dictionaries
        """
        data = [{
            "target": target,
            "limit": limit,
            "order_by": [order_by],
            "filters": ["dofollow", "=", True]  # Focus on dofollow links
        }]

        try:
            result = self._make_request("backlinks/backlinks/live", data)
            tasks = result.get("tasks", [])
            if tasks and tasks[0].get("result"):
                items = tasks[0]["result"][0].get("items", [])
                return items
            return []
        except Exception as e:
            print(f"Error fetching backlinks: {e}")
            return []

    def get_anchors(
        self,
        target: str,
        limit: int = 1000
    ) -> list:
        """Get anchor text distribution for a target.

        Args:
            target: Domain or URL to analyze
            limit: Maximum number of anchors to return

        Returns:
            List of anchor text dictionaries
        """
        data = [{
            "target": target,
            "limit": limit,
            "order_by": ["backlinks,desc"]
        }]

        try:
            result = self._make_request("backlinks/anchors/live", data)
            tasks = result.get("tasks", [])
            if tasks and tasks[0].get("result"):
                items = tasks[0]["result"][0].get("items", [])
                return items
            return []
        except Exception as e:
            print(f"Error fetching anchors: {e}")
            return []

    def get_referring_domains(
        self,
        target: str,
        limit: int = 1000
    ) -> list:
        """Get referring domains for a target.

        Args:
            target: Domain or URL to analyze
            limit: Maximum number of domains to return

        Returns:
            List of referring domain dictionaries
        """
        data = [{
            "target": target,
            "limit": limit,
            "order_by": ["rank,desc"]
        }]

        try:
            result = self._make_request("backlinks/referring_domains/live", data)
            tasks = result.get("tasks", [])
            if tasks and tasks[0].get("result"):
                items = tasks[0]["result"][0].get("items", [])
                return items
            return []
        except Exception as e:
            print(f"Error fetching referring domains: {e}")
            return []

    def get_backlink_summary(self, target: str) -> dict:
        """Get backlink summary statistics for a target.

        Args:
            target: Domain to analyze

        Returns:
            Dictionary with summary statistics
        """
        data = [{
            "target": target
        }]

        try:
            result = self._make_request("backlinks/summary/live", data)
            tasks = result.get("tasks", [])
            if tasks and tasks[0].get("result"):
                return tasks[0]["result"][0]
            return {}
        except Exception as e:
            print(f"Error fetching backlink summary: {e}")
            return {}

    def get_full_backlink_analysis(
        self,
        target: str,
        backlink_limit: int = 500,
        anchor_limit: int = 200,
        domain_limit: int = 200
    ) -> BacklinkData:
        """Get comprehensive backlink analysis.

        Args:
            target: Domain to analyze
            backlink_limit: Max backlinks to fetch
            anchor_limit: Max anchors to fetch
            domain_limit: Max referring domains to fetch

        Returns:
            BacklinkData object with all results
        """
        # Get summary first
        summary = self.get_backlink_summary(target)

        # Get detailed data
        backlinks = self.get_backlinks(target, limit=backlink_limit)
        anchors = self.get_anchors(target, limit=anchor_limit)
        domains = self.get_referring_domains(target, limit=domain_limit)

        return BacklinkData(
            total_backlinks=summary.get("backlinks", 0),
            referring_domains=summary.get("referring_domains", 0),
            dofollow_backlinks=summary.get("backlinks_nofollow", 0),  # Note: API naming
            nofollow_backlinks=summary.get("backlinks_nofollow", 0),
            backlinks=backlinks,
            anchors=anchors,
            referring_domain_list=domains,
            domain_rank=summary.get("rank", None)
        )

    # =========================================================================
    # DATAFORSEO LABS API (Competitors)
    # =========================================================================

    def get_competitors(
        self,
        target: str,
        location_code: int = 2840,  # US
        language_code: str = "en",
        limit: int = 20
    ) -> list:
        """Find organic competitors for a domain.

        Args:
            target: Domain to analyze
            location_code: Location code (2840 = US)
            language_code: Language code
            limit: Maximum competitors to return

        Returns:
            List of competitor dictionaries
        """
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit,
            "order_by": ["intersections,desc"]
        }]

        try:
            result = self._make_request(
                "dataforseo_labs/google/competitors_domain/live",
                data
            )
            tasks = result.get("tasks", [])
            if tasks and tasks[0].get("result"):
                items = tasks[0]["result"][0].get("items", [])
                return items
            return []
        except Exception as e:
            print(f"Error fetching competitors: {e}")
            return []

    def get_ranked_keywords(
        self,
        target: str,
        location_code: int = 2840,
        language_code: str = "en",
        limit: int = 1000
    ) -> list:
        """Get keywords a domain ranks for.

        Args:
            target: Domain to analyze
            location_code: Location code (2840 = US)
            language_code: Language code
            limit: Maximum keywords to return

        Returns:
            List of keyword dictionaries
        """
        data = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit,
            "order_by": ["keyword_data.keyword_info.search_volume,desc"]
        }]

        try:
            result = self._make_request(
                "dataforseo_labs/google/ranked_keywords/live",
                data
            )
            tasks = result.get("tasks", [])
            if tasks and tasks[0].get("result"):
                items = tasks[0]["result"][0].get("items", [])
                return items
            return []
        except Exception as e:
            print(f"Error fetching ranked keywords: {e}")
            return []

    def get_keyword_intersection(
        self,
        targets: list[str],
        location_code: int = 2840,
        language_code: str = "en",
        limit: int = 1000
    ) -> list:
        """Get keywords that multiple domains share or don't share.

        Args:
            targets: List of domains to compare (2-3 domains)
            location_code: Location code
            language_code: Language code
            limit: Maximum keywords to return

        Returns:
            List of keyword intersection data
        """
        data = [{
            "targets": targets,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit,
            "order_by": ["keyword_data.keyword_info.search_volume,desc"]
        }]

        try:
            result = self._make_request(
                "dataforseo_labs/google/keywords_for_site/live",
                data
            )
            tasks = result.get("tasks", [])
            if tasks and tasks[0].get("result"):
                items = tasks[0]["result"][0].get("items", [])
                return items
            return []
        except Exception as e:
            print(f"Error fetching keyword intersection: {e}")
            return []

    def get_full_competitor_analysis(
        self,
        target: str,
        competitor_domains: Optional[list[str]] = None,
        location_code: int = 2840,
        language_code: str = "en",
        keyword_limit: int = 500
    ) -> CompetitorData:
        """Get comprehensive competitor analysis.

        Args:
            target: Your domain
            competitor_domains: Optional list of specific competitors
            location_code: Location code
            language_code: Language code
            keyword_limit: Max keywords to fetch

        Returns:
            CompetitorData object with all results
        """
        # Get competitors if not provided
        if competitor_domains is None:
            competitor_list = self.get_competitors(
                target,
                location_code=location_code,
                language_code=language_code,
                limit=10
            )
        else:
            competitor_list = [{"domain": d} for d in competitor_domains]

        # Get ranked keywords for target
        ranked_keywords = self.get_ranked_keywords(
            target,
            location_code=location_code,
            language_code=language_code,
            limit=keyword_limit
        )

        return CompetitorData(
            target_domain=target,
            competitors=competitor_list,
            ranked_keywords=ranked_keywords,
            total_keywords=len(ranked_keywords)
        )


def create_client_from_streamlit() -> Optional[DataForSEOClient]:
    """Create DataForSEO client from Streamlit secrets.

    Returns:
        DataForSEOClient if credentials available, None otherwise
    """
    try:
        import streamlit as st
        login = st.secrets.get("DATAFORSEO_LOGIN")
        password = st.secrets.get("DATAFORSEO_PASSWORD")

        if login and password:
            return DataForSEOClient(login, password)
        return None
    except Exception:
        return None
