#!/usr/bin/env python3
"""Script to fix the Toggl API implementation."""
import argparse
import logging
import os
import sys
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


def fix_api_implementation():
    """Fix the Toggl API implementation."""
    api_file_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '..',
        'custom_components',
        'toggl_worklog',
        'api.py'
    ))

    _LOGGER.info(f"Fixing API implementation in: {api_file_path}")

    # Check if the file exists
    if not os.path.exists(api_file_path):
        _LOGGER.error(f"API file not found: {api_file_path}")
        return False

    # Read the current file
    with open(api_file_path, 'r') as f:
        content = f.read()

    # Make fixes

    # Fix 1: Improve time range calculation
    _LOGGER.info("Fixing time range calculation...")

    # Fix daily time range calculation
    content = content.replace(
        "start_of_day = now - ((now % 86400000))",
        "# Calculate start of day in user's local timezone\n"
        "        current_date = datetime.fromtimestamp(now / 1000).date()\n"
        "        start_of_day = int(datetime.combine(current_date, datetime.min.time()).timestamp() * 1000)"
    )

    # Fix weekly time range calculation
    content = content.replace(
        "start_of_week = now - (7 * 86400000)",
        "# Calculate start of week (7 days ago)\n"
        "        current_date = datetime.fromtimestamp(now / 1000).date()\n"
        "        start_of_week = int(datetime.combine(current_date - timedelta(days=7), datetime.min.time()).timestamp() * 1000)"
    )

    # Fix monthly time range calculation
    content = content.replace(
        "start_of_month = now - (30 * 86400000)",
        "# Calculate start of month (30 days ago)\n"
        "        current_date = datetime.fromtimestamp(now / 1000).date()\n"
        "        start_of_month = int(datetime.combine(current_date - timedelta(days=30), datetime.min.time()).timestamp() * 1000)"
    )

    # Fix 2: Improve duration calculation
    _LOGGER.info("Fixing duration calculation...")
    content = content.replace(
        "def calculate_total_duration(self, time_entries: List[Dict]) -> int:\n"
        "        """Calculate the total duration from time entries in milliseconds."""\n"
        "        total_duration = 0\n"
        "        \n"
        "        for entry in time_entries:\n"
        "            # Skip entries with negative duration (currently running)\n"
        "            if entry.get('duration') and entry.get('duration') > 0:\n"
        "                total_duration += entry.get('duration')\n"
        "                \n"
        "        return total_duration",

        "def calculate_total_duration(self, time_entries: List[Dict]) -> int:\n"
        "        """Calculate the total duration from time entries in milliseconds."""\n"
        "        total_duration = 0\n"
        "        \n"
        "        for entry in time_entries:\n"
        "            # Handle different duration formats\n"
        "            duration = entry.get('duration')\n"
        "            \n"
        "            # Skip entries with no duration\n"
        "            if duration is None:\n"
        "                continue\n"
        "                \n"
        "            # Skip entries with negative duration (currently running)\n"
        "            if isinstance(duration, (int, float)) and duration > 0:\n"
        "                total_duration += duration\n"
        "            # If duration is a string, try to convert it\n"
        "            elif isinstance(duration, str):\n"
        "                try:\n"
        "                    duration_value = int(duration)\n"
        "                    if duration_value > 0:\n"
        "                        total_duration += duration_value\n"
        "                except (ValueError, TypeError):\n"
        "                    _LOGGER.warning(f\"Could not parse duration: {duration}\")\n"
        "                \n"
        "        return total_duration"
    )

    # Fix 3: Improve imports
    _LOGGER.info("Fixing imports...")
    if "from datetime import datetime, timedelta" not in content:
        content = content.replace(
            "import time",
            "import time\nfrom datetime import datetime, timedelta"
        )

    # Fix 4: Improve error handling in get_time_entries
    _LOGGER.info("Fixing error handling in get_time_entries...")
    content = content.replace(
        "def get_time_entries(self, start_date: int, end_date: int) -> List[Dict]:\n"
        "        """Get time entries within a date range."""\n"
        "        endpoint = API_TIME_ENTRIES_ENDPOINT.format(workspace_id=self.workspace_id)\n"
        "        \n"
        "        params = {\n"
        "            \"start_date\": start_date,\n"
        "            \"end_date\": end_date,\n"
        "        }\n"
        "        \n"
        "        # If user_id is specified, add it to the params\n"
        "        if self.user_id:\n"
        "            params[\"assignee\"] = self.user_id\n"
        "        \n"
        "        _LOGGER.debug(\"Getting time entries from %s to %s\", start_date, end_date)\n"
        "        try:    \n"
        "            response = self._make_request(\"GET\", endpoint, params)\n"
        "            \n"
        "            if \"data\" not in response:\n"
        "                _LOGGER.error(\"Unexpected response from Toggl API: %s\", response)\n"
        "                return []\n"
        "                \n"
        "            _LOGGER.debug(\"Got %d time entries\", len(response[\"data\"])\n"
        "            return response[\"data\"]\n"
        "        except TogglApiError as err:\n"
        "            _LOGGER.error(\"Error getting time entries: %s\", err)\n"
        "            return []",

        "def get_time_entries(self, start_date: int, end_date: int) -> List[Dict]:\n"
        "        """Get time entries within a date range."""\n"
        "        endpoint = API_TIME_ENTRIES_ENDPOINT.format(workspace_id=self.workspace_id)\n"
        "        \n"
        "        params = {\n"
        "            \"start_date\": start_date,\n"
        "            \"end_date\": end_date,\n"
        "        }\n"
        "        \n"
        "        # If user_id is specified, add it to the params\n"
        "        if self.user_id:\n"
        "            params[\"assignee\"] = self.user_id\n"
        "        \n"
        "        _LOGGER.debug(\"Getting time entries from %s to %s\", \n"
        "                     datetime.fromtimestamp(start_date/1000).strftime('%Y-%m-%d %H:%M:%S'),\n"
        "                     datetime.fromtimestamp(end_date/1000).strftime('%Y-%m-%d %H:%M:%S'))\n"
        "        \n"
        "        try:    \n"
        "            response = self._make_request(\"GET\", endpoint, params)\n"
        "            \n"
        "            if \"data\" not in response:\n"
        "                _LOGGER.error(\"Unexpected response from Toggl API: %s\", response)\n"
        "                return []\n"
        "            \n"
        "            entries = response[\"data\"]\n"
        "            _LOGGER.debug(\"Got %d time entries\", len(entries))\n"
        "            \n"
        "            # Filter out entries with invalid duration\n"
        "            valid_entries = []\n"
        "            for entry in entries:\n"
        "                if \"duration\" in entry:\n"
        "                    valid_entries.append(entry)\n"
        "                else:\n"
        "                    _LOGGER.warning(\"Skipping entry without duration: %s\", entry.get(\"id\", \"unknown\"))\n"
        "            \n"
        "            if len(valid_entries) != len(entries):\n"
        "                _LOGGER.info(\"Filtered out %d entries with missing duration\", len(entries) - len(valid_entries))\n"
        "            \n"
        "            return valid_entries\n"
        "        except TogglApiError as err:\n"
        "            _LOGGER.error(\"Error getting time entries: %s\", err)\n"
        "            return []\n"
        "        except Exception as err:\n"
        "            _LOGGER.error(\"Unexpected error getting time entries: %s\", err)\n"
        "            return []"
    )

    # Write the fixed content back to the file
    with open(api_file_path, 'w') as f:
        f.write(content)

    _LOGGER.info("API implementation fixed successfully!")
    return True


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Fix Toggl API implementation')
    args = parser.parse_args()

    fix_api_implementation()


if __name__ == "__main__":
    main()