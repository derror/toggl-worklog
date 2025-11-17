"""API client for Toggl."""
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any

import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .const import (
    API_ME_ENDPOINT,
    API_TIME_ENTRIES_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)

# API client configuration
API_TIMEOUT = 30  # seconds
API_MAX_RETRIES = 3
API_BACKOFF_FACTOR = 0.5  # will retry after 0.5s, 1s, 2s


class TogglApiError(Exception):
    """Exception to indicate a Toggl API error."""


class TogglApi:
    """API client for Toggl."""

    def __init__(self, api_token: str, workspace_id: str, sync_months: int = 3):
        """Initialize the API client."""
        self.api_token = api_token.strip()
        self.workspace_id = workspace_id
        self.sync_months = sync_months
        if not self.api_token:
            raise ValueError("API token cannot be empty")

        self.auth = HTTPBasicAuth(self.api_token, "api_token")

        token_preview = f"{self.api_token[:4]}...{self.api_token[-4:]}" if len(self.api_token) > 8 else "***"
        _LOGGER.info(
            "Initialized TogglApi for workspace %s (token: %s)",
            workspace_id, token_preview
        )

        self.session = self._create_session()
        self._all_entries_cache = None # Cache for all entries within the sync period

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=API_MAX_RETRIES,
            backoff_factor=API_BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    def _make_request(self, method: str, url: str, json: Optional[Dict] = None) -> Any:
        """Make a request to the Toggl API."""
        token_preview = f"{self.api_token[:4]}...{self.api_token[-4:]}" if len(self.api_token) > 8 else "***"
        _LOGGER.debug(
            "Making request to Toggl API: %s %s with json %s (workspace: %s, token: %s)",
            method, url, json, self.workspace_id, token_preview
        )

        try:
            response = self.session.request(
                method,
                url,
                auth=self.auth,
                json=json,
                timeout=API_TIMEOUT,
            )
            _LOGGER.debug("Toggl API response status: %s", response.status_code)
            response.raise_for_status()
            if response.content:
                return response.json()
            return None
        except requests.exceptions.Timeout as err:
            _LOGGER.error("Timeout communicating with Toggl API for workspace %s: %s", self.workspace_id, err)
            raise TogglApiError(f"Timeout communicating with Toggl API: {err}") from err
        except requests.exceptions.HTTPError as err:
            response_text = getattr(getattr(err, 'response', None), 'text', 'No response content')
            if err.response is not None and err.response.status_code in [401, 403]:
                _LOGGER.error(
                    "AUTHENTICATION FAILED for workspace %s: The API token is invalid or doesn't have access. Response: %s",
                    self.workspace_id, response_text
                )
            else:
                _LOGGER.error(
                    "HTTP error from Toggl API for workspace %s: %s - Response: %s",
                    self.workspace_id, err, response_text
                )
            raise TogglApiError(f"HTTP error from Toggl API: {err}") from err
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error communicating with Toggl API for workspace %s: %s", self.workspace_id, err)
            raise TogglApiError(f"Error communicating with Toggl API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error in API request for workspace %s: %s", self.workspace_id, err)
            raise TogglApiError(f"Unexpected error in API request: {err}") from err

    def _fetch_raw_time_entries(self, start_date: date, end_date: date) -> List[Dict]:
        """Fetch raw time entry groupings within a date range using the reports API."""
        endpoint = API_TIME_ENTRIES_ENDPOINT.format(workspace_id=self.workspace_id)
        
        payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        _LOGGER.debug("Getting raw time entries from %s to %s", start_date, end_date)

        try:
            entries = self._make_request("POST", endpoint, json=payload)
            _LOGGER.debug("Got %d raw groupings", len(entries) if entries else 0)
            return entries if entries else []
        except TogglApiError as err:
            _LOGGER.error("Error getting raw time entries: %s", err)
            return []
        except Exception as err:
            _LOGGER.error("Unexpected error getting raw time entries: %s", err)
            return []

    def get_time_entries(self, start_date: date, end_date: date) -> List[Dict]:
        """Get a flattened list of individual time entries within a date range."""
        raw_groupings = self._fetch_raw_time_entries(start_date, end_date)
        flattened_entries = []
        for grouping in raw_groupings:
            flattened_entries.extend(grouping.get('time_entries', []))
        _LOGGER.debug("Flattened %d raw groupings into %d individual time entries", len(raw_groupings), len(flattened_entries))
        return flattened_entries

    def _filter_entries_by_date(self, entries: List[Dict], start_date: date, end_date: date) -> List[Dict]:
        """Filter a flattened list of time entries by a given date range."""
        filtered_entries = []
        for entry in entries:
            entry_start_str = entry.get('start')
            if entry_start_str:
                # Parse the start date of the entry (e.g., "2025-11-17T09:26:56+01:00")
                # We only care about the date part for filtering
                entry_date = datetime.fromisoformat(entry_start_str).date()
                if start_date <= entry_date <= end_date:
                    filtered_entries.append(entry)
        return filtered_entries

    def _get_all_entries_for_sync_period(self) -> List[Dict]:
        """Fetch all time entries for the specified number of months and cache them."""
        if self._all_entries_cache is not None:
            return self._all_entries_cache

        today = date.today()
        start_date = today - timedelta(days=30 * self.sync_months) # Approximate months
        
        _LOGGER.debug("Fetching all entries for sync period (%d months) from %s to %s", self.sync_months, start_date, today)
        all_entries = self.get_time_entries(start_date, today)
        self._all_entries_cache = all_entries
        return all_entries

    def get_daily_time_entries(self) -> List[Dict]:
        """Get time entries for the last 24 hours."""
        today = date.today()
        start_date = today - timedelta(days=1)
        all_entries = self._get_all_entries_for_sync_period()
        return self._filter_entries_by_date(all_entries, start_date, today)

    def get_weekly_time_entries(self) -> List[Dict]:
        """Get time entries for the last 7 days."""
        today = date.today()
        start_date = today - timedelta(days=7)
        all_entries = self._get_all_entries_for_sync_period()
        return self._filter_entries_by_date(all_entries, start_date, today)

    def get_monthly_time_entries(self) -> List[Dict]:
        """Get time entries for the last 30 days."""
        today = date.today()
        start_date = today - timedelta(days=30)
        all_entries = self._get_all_entries_for_sync_period()
        return self._filter_entries_by_date(all_entries, start_date, today)

    def get_current_day_time_entries(self) -> List[Dict]:
        """Get time entries for the current calendar day (today)."""
        today = date.today()
        all_entries = self._get_all_entries_for_sync_period()
        return self._filter_entries_by_date(all_entries, today, today)

    def get_current_week_time_entries(self) -> List[Dict]:
        """Get time entries for the current calendar week (starting Monday)."""
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        all_entries = self._get_all_entries_for_sync_period()
        return self._filter_entries_by_date(all_entries, start_of_week, today)

    def get_current_month_time_entries(self) -> List[Dict]:
        """Get time entries for the current calendar month."""
        today = date.today()
        start_of_month = today.replace(day=1)
        all_entries = self._get_all_entries_for_sync_period()
        return self._filter_entries_by_date(all_entries, start_of_month, today)

    def calculate_total_duration(self, time_entries: List[Dict]) -> int:
        """Calculate the total duration from time entries in milliseconds."""
        total_duration = 0
        # The response is a list of groupings (by user/project/etc.)
        for grouping in time_entries:
            # Each grouping contains a list of actual time entries
            for entry in grouping.get('time_entries', []):
                if 'seconds' in entry and entry['seconds'] is not None:
                    total_duration += entry['seconds'] * 1000
        return total_duration

    def _get_worked_time_summary(self, entries_fetcher) -> Dict[str, Any]:
        """Helper to get and process time entries."""
        self._all_entries_cache = None # Clear cache for fresh data
        entries = entries_fetcher()
        total_duration_ms = self.calculate_total_duration(entries)
        
        return {
            "total_duration": total_duration_ms,
            "duration_hours": total_duration_ms // 3600000,
            "duration_minutes": (total_duration_ms % 3600000) // 60000,
            "entries_count": len(entries),
            "entries": entries,
        }

    def get_daily_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the last 24 hours."""
        return self._get_worked_time_summary(self.get_daily_time_entries)

    def get_weekly_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the last 7 days."""
        return self._get_worked_time_summary(self.get_weekly_time_entries)

    def get_monthly_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the last 30 days."""
        return self._get_worked_time_summary(self.get_monthly_time_entries)

    def get_current_day_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current calendar day."""
        return self._get_worked_time_summary(self.get_current_day_time_entries)

    def get_current_week_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current calendar week."""
        return self._get_worked_time_summary(self.get_current_week_time_entries)

    def get_current_month_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current calendar month."""
        return self._get_worked_time_summary(self.get_current_month_time_entries)

    def validate_api_token(self) -> bool:
        """Validate the API token by fetching user data."""
        try:
            response = self._make_request("GET", API_ME_ENDPOINT)

            # Case 1: New structure with "me" object
            if response and 'me' in response and isinstance(response['me'], dict):
                user_data = response['me']
                workspaces = user_data.get('workspaces', [])
                if any(ws.get('id') == int(self.workspace_id) for ws in workspaces):
                    return True
            
            # Case 2: Old structure with a list of users
            elif response and isinstance(response, list) and len(response) > 0:
                user_data = response[0]
                workspaces = user_data.get('workspaces', [])
                if any(ws.get('workspace_id') == int(self.workspace_id) for ws in workspaces):
                    return True

            # Case 3: Flat structure with default_workspace_id
            elif response and 'default_workspace_id' in response:
                if response.get('default_workspace_id') == int(self.workspace_id):
                    return True

            # If none of the above worked, log the failure
            _LOGGER.error("Workspace ID %s not found in user's workspaces or API response format is unexpected.", self.workspace_id)
            return False

        except TogglApiError:
            return False

    def close(self) -> None:
        """Close the API session."""
        if hasattr(self, 'session'):
            self.session.close()
            _LOGGER.debug("API session closed")