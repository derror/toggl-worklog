#!/usr/bin/env python3
"""Test parallel data loading similar to Home Assistant coordinator."""
import argparse
import logging
import os
import sys
from unittest.mock import MagicMock
import concurrent.futures

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


def simulate_coordinator_update(api):
    """Simulate what the coordinator does: clear cache then fetch all data in parallel."""
    _LOGGER.info("\n=== Simulating Coordinator Update (like first integration setup) ===")

    # Clear cache (like coordinator does)
    api.clear_cache()

    # Fetch all data in parallel (like coordinator does)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            'daily': executor.submit(api.get_daily_worked_time),
            'weekly': executor.submit(api.get_weekly_worked_time),
            'monthly': executor.submit(api.get_monthly_worked_time),
            'current_day': executor.submit(api.get_current_day_worked_time),
            'current_week': executor.submit(api.get_current_week_worked_time),
            'current_month': executor.submit(api.get_current_month_worked_time),
        }

        results = {}
        for name, future in futures.items():
            results[name] = future.result()

    return results


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Test parallel data loading')
    parser.add_argument('--api-token', required=True, help='Toggl API token')
    parser.add_argument('--workspace-id', required=True, help='Toggl workspace ID')

    args = parser.parse_args()

    api = TogglApi(api_token=args.api_token, workspace_id=args.workspace_id)

    # Simulate first setup (like when integration is added)
    _LOGGER.info("Simulating FIRST integration setup...")
    results1 = simulate_coordinator_update(api)

    _LOGGER.info("\n=== First Update Results ===")
    for name, data in results1.items():
        hours = data.get('duration_hours', 0)
        minutes = data.get('duration_minutes', 0)
        count = data.get('entries_count', 0)
        _LOGGER.info(f"{name:15s}: {hours}h {minutes}m ({count} entries)")

    # Simulate second update (after scan_interval)
    _LOGGER.info("\n\nSimulating SECOND update (after scan interval)...")
    results2 = simulate_coordinator_update(api)

    _LOGGER.info("\n=== Second Update Results ===")
    for name, data in results2.items():
        hours = data.get('duration_hours', 0)
        minutes = data.get('duration_minutes', 0)
        count = data.get('entries_count', 0)
        _LOGGER.info(f"{name:15s}: {hours}h {minutes}m ({count} entries)")

    # Verify results are consistent
    _LOGGER.info("\n=== Verification ===")
    all_match = True
    for name in results1.keys():
        if results1[name]['total_duration'] != results2[name]['total_duration']:
            _LOGGER.error(f"❌ {name} results don't match!")
            all_match = False

    if all_match:
        _LOGGER.info("✅ All results are consistent between updates!")

    api.close()


if __name__ == "__main__":
    main()
