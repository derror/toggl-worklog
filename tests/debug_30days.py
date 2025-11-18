#!/usr/bin/env python3
"""Debug script to see what entries are in the last 30 days."""
import argparse
import json
import logging
import os
import sys
from unittest.mock import MagicMock
from datetime import date, timedelta

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Debug 30 days entries')
    parser.add_argument('--api-token', required=True, help='Toggl API token')
    parser.add_argument('--workspace-id', required=True, help='Toggl workspace ID')

    args = parser.parse_args()

    api = TogglApi(api_token=args.api_token, workspace_id=args.workspace_id)

    today = date.today()
    _LOGGER.info(f"Today: {today}")
    _LOGGER.info(f"30 days ago: {today - timedelta(days=30)}")

    # Get all entries
    all_entries = api._get_all_entries_for_sync_period()
    _LOGGER.info(f"\nTotal entries in cache: {len(all_entries)}")

    # Get entries for last 30 days
    monthly_entries = api.get_monthly_time_entries()
    _LOGGER.info(f"\nEntries for last 30 days: {len(monthly_entries)}")

    for entry in monthly_entries:
        seconds = entry.get('seconds', 0)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        _LOGGER.info(f"  Start: {entry.get('start')}, Duration: {hours}h {minutes}m ({seconds}s)")

    # Calculate total
    total_duration = api.calculate_total_duration(monthly_entries)
    hours = total_duration // 3600000
    minutes = (total_duration % 3600000) // 60000
    _LOGGER.info(f"\nTotal duration: {hours}h {minutes}m")

    api.close()


if __name__ == "__main__":
    main()
