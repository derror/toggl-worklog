#!/usr/bin/env python3
"""Standalone test script for Toggl API functionality."""
import argparse
import logging
import os
import sys
from unittest.mock import MagicMock

# --- Mock Home Assistant modules ---
# This is a workaround to allow importing the api module, which is part of a package
# that has dependencies on homeassistant core, without having homeassistant installed.
MOCK_MODULES = [
    'homeassistant',
    'homeassistant.config_entries',
    'homeassistant.core',
    'homeassistant.helpers',
    'homeassistant.helpers.config_validation',
    'homeassistant.helpers.update_coordinator', # Added for sensor.py imports
    'homeassistant.components.sensor', # Added for sensor.py imports
]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = MagicMock()
# --- End Mock ---

# Add the parent directory to the path so we can import the custom_components package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_components.toggl_worklog.api import TogglApi, TogglApiError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


def test_api(api_token: str, workspace_id: str):
    """Test the Toggl API functionality."""
    _LOGGER.info("Initializing Toggl API client...")
    try:
        api = TogglApi(api_token=api_token, workspace_id=workspace_id)
    except ValueError as e:
        _LOGGER.error(f"❌ Failed to initialize API client: {e}")
        return False

    # Test API connection and validation
    _LOGGER.info("\nTesting API connection and credentials...")
    try:
        valid = api.validate_api_token()
        if valid:
            _LOGGER.info("✅ API connection and credentials are valid!")
        else:
            _LOGGER.error("❌ API connection failed: The API token or Workspace ID is invalid.")
            api.close()
            return False
    except TogglApiError as e:
        _LOGGER.error(f"❌ API connection failed with an error: {e}")
        api.close()
        return False
    except Exception as e:
        _LOGGER.error(f"❌ An unexpected error occurred during validation: {e}")
        api.close()
        return False

    # --- Test fetching data ---
    _LOGGER.info("\n--- Testing Data Fetching Summaries ---")

    test_cases = {
        "Last 24 Hours": api.get_daily_worked_time,
        "Last 7 Days": api.get_weekly_worked_time,
        "Last 30 Days": api.get_monthly_worked_time,
        "Current Calendar Day": api.get_current_day_worked_time,
        "Current Calendar Week": api.get_current_week_worked_time,
        "Current Calendar Month": api.get_current_month_worked_time,
    }

    all_successful = True
    for name, method in test_cases.items():
        _LOGGER.info(f"\nTesting: {name}...")
        try:
            data = method()
            if data:
                hours = data.get("duration_hours", 0)
                minutes = data.get("duration_minutes", 0)
                entries_count = data.get("entries_count", 0)
                _LOGGER.info(f"  ✅ Success! Found {entries_count} entries.")
                _LOGGER.info(f"     Total time: {hours}h {minutes}m")
            else:
                _LOGGER.warning(f"  ⚠️ Could not fetch data for {name}.")
                all_successful = False
        except TogglApiError as e:
            _LOGGER.error(f"  ❌ Failed to fetch data for {name}: {e}")
            all_successful = False
        except Exception as e:
            _LOGGER.error(f"  ❌ An unexpected error occurred for {name}: {e}")
            all_successful = False

    api.close()
    _LOGGER.info("\n--- Test Complete ---")
    if all_successful:
        _LOGGER.info("✅ All tested endpoints returned data successfully.")
    else:
        _LOGGER.warning("⚠️ Some endpoints failed or returned no data.")

    return all_successful


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Test Toggl API functionality')
    parser.add_argument('--api-token', required=True, help='Toggl API token')
    parser.add_argument('--workspace-id', required=True, help='Toggl workspace ID')

    args = parser.parse_args()

    test_api(args.api_token, args.workspace_id)


if __name__ == "__main__":
    main()