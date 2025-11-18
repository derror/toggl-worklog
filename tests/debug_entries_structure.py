#!/usr/bin/env python3
"""Debug script to see the actual structure of time entries."""
import argparse
import json
import logging
import os
import sys
from unittest.mock import MagicMock

# --- Mock Home Assistant modules ---
MOCK_MODULES = [
    'homeassistant',
    'homeassistant.config_entries',
    'homeassistant.core',
    'homeassistant.helpers',
    'homeassistant.helpers.config_validation',
    'homeassistant.helpers.update_coordinator',
    'homeassistant.components.sensor',
]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()
# --- End Mock ---

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_components.toggl_worklog.api import TogglApi
from datetime import date, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Debug time entries structure')
    parser.add_argument('--api-token', required=True, help='Toggl API token')
    parser.add_argument('--workspace-id', required=True, help='Toggl workspace ID')

    args = parser.parse_args()

    api = TogglApi(api_token=args.api_token, workspace_id=args.workspace_id)

    # Fetch entries for last 30 days
    today = date.today()
    start_date = today - timedelta(days=30)

    _LOGGER.info("Fetching raw time entries...")
    raw_groupings = api._fetch_raw_time_entries(start_date, today)

    _LOGGER.info(f"\n=== RAW GROUPINGS (count: {len(raw_groupings)}) ===")
    for i, grouping in enumerate(raw_groupings[:2]):  # Show first 2 groupings
        _LOGGER.info(f"\nGrouping {i}:")
        _LOGGER.info(f"Keys: {list(grouping.keys())}")
        if 'time_entries' in grouping:
            _LOGGER.info(f"Number of time_entries: {len(grouping['time_entries'])}")
            if grouping['time_entries']:
                _LOGGER.info(f"First entry keys: {list(grouping['time_entries'][0].keys())}")
                _LOGGER.info(f"First entry: {json.dumps(grouping['time_entries'][0], indent=2)}")

    _LOGGER.info("\n=== FLATTENED ENTRIES ===")
    flattened = api.get_time_entries(start_date, today)
    _LOGGER.info(f"Count: {len(flattened)}")
    if flattened:
        _LOGGER.info(f"First entry keys: {list(flattened[0].keys())}")
        _LOGGER.info(f"First entry: {json.dumps(flattened[0], indent=2)}")

    _LOGGER.info("\n=== TESTING calculate_total_duration ===")

    # Test with raw groupings (what the function expects based on the code)
    _LOGGER.info("\nTesting with raw groupings:")
    duration_from_raw = api.calculate_total_duration(raw_groupings)
    _LOGGER.info(f"Duration: {duration_from_raw} ms ({duration_from_raw // 3600000}h {(duration_from_raw % 3600000) // 60000}m)")

    # Test with flattened entries (what actually gets passed)
    _LOGGER.info("\nTesting with flattened entries:")
    duration_from_flat = api.calculate_total_duration(flattened)
    _LOGGER.info(f"Duration: {duration_from_flat} ms ({duration_from_flat // 3600000}h {(duration_from_flat % 3600000) // 60000}m)")

    api.close()


if __name__ == "__main__":
    main()
