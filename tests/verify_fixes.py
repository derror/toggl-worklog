#!/usr/bin/env python3
"""Script to verify the fixes to the Toggl Worklog integration."""
import argparse
import logging
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import the custom_components
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_components.toggl_worklog.api import TogglApi

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


def format_duration(duration_ms):
    """Format a duration in milliseconds to a human-readable string."""
    total_seconds = duration_ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours}h {minutes}m {seconds}s"


def verify_fixes(api_token, workspace_id, user_id=None):
    """Verify the fixes to the Toggl Worklog integration."""
    _LOGGER.info("Verifying fixes to the Toggl Worklog integration...")
    
    # Create the API client
    api = TogglApi(api_token, workspace_id, user_id)
    
    # Test API connection
    _LOGGER.info("Testing API connection...")
    try:
        valid = api.validate_api_token()
        if valid:
            _LOGGER.info("✅ API connection successful!")
        else:
            _LOGGER.error("❌ API connection failed: Invalid credentials")
            return False
    except Exception as e:
        _LOGGER.error(f"❌ API connection failed: {e}")
        return False
    
    # Test daily worked time
    _LOGGER.info("\nTesting daily worked time...")
    try:
        daily_data = api.get_daily_worked_time()
        _LOGGER.info(f"Daily worked time: {daily_data.get('duration_hours')}h {daily_data.get('duration_minutes')}m")
        _LOGGER.info(f"Daily entries count: {daily_data.get('entries_count')}")
        
        if daily_data.get('entries_count', 0) > 0:
            _LOGGER.info("✅ Daily worked time calculation successful!")
        else:
            _LOGGER.warning("⚠️ No daily time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Daily worked time calculation failed: {e}")
        return False
    
    # Test weekly worked time
    _LOGGER.info("\nTesting weekly worked time...")
    try:
        weekly_data = api.get_weekly_worked_time()
        _LOGGER.info(f"Weekly worked time: {weekly_data.get('duration_hours')}h {weekly_data.get('duration_minutes')}m")
        _LOGGER.info(f"Weekly entries count: {weekly_data.get('entries_count')}")
        
        if weekly_data.get('entries_count', 0) > 0:
            _LOGGER.info("✅ Weekly worked time calculation successful!")
        else:
            _LOGGER.warning("⚠️ No weekly time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Weekly worked time calculation failed: {e}")
        return False
    
    # Test monthly worked time
    _LOGGER.info("\nTesting monthly worked time...")
    try:
        monthly_data = api.get_monthly_worked_time()
        _LOGGER.info(f"Monthly worked time: {monthly_data.get('duration_hours')}h {monthly_data.get('duration_minutes')}m")
        _LOGGER.info(f"Monthly entries count: {monthly_data.get('entries_count')}")
        
        if monthly_data.get('entries_count', 0) > 0:
            _LOGGER.info("✅ Monthly worked time calculation successful!")
        else:
            _LOGGER.warning("⚠️ No monthly time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Monthly worked time calculation failed: {e}")
        return False
    
    # Test custom period (3 months)
    _LOGGER.info("\nTesting custom period (3 months)...")
    try:
        entries = api.get_custom_period_time_entries(3)
        total_duration = api.calculate_total_duration(entries)
        hours = total_duration // 3600000
        minutes = (total_duration % 3600000) // 60000
        
        _LOGGER.info(f"Custom period (3 months) entries count: {len(entries)}")
        _LOGGER.info(f"Custom period (3 months) total duration: {hours}h {minutes}m")
        
        if len(entries) > 0:
            _LOGGER.info("✅ Custom period calculation successful!")
        else:
            _LOGGER.warning("⚠️ No custom period time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Custom period calculation failed: {e}")
        return False
    
    _LOGGER.info("\n✅ All tests completed successfully!")
    return True


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Verify fixes to the Toggl Worklog integration')
    parser.add_argument('--api-token', required=True, help='Toggl API token')
    parser.add_argument('--workspace-id', required=True, help='Toggl workspace ID')
    parser.add_argument('--user-id', help='Toggl user ID (optional)')
    
    args = parser.parse_args()
    
    verify_fixes(args.api_token, args.workspace_id, args.user_id)


if __name__ == "__main__":
    main()