#!/usr/bin/env python3
"""Test script for Toggl API integration."""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add the parent directory to the path so we can import the custom_components
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_components.toggl_worklog.api import TogglApi

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


def format_timestamp(timestamp_ms: int) -> str:
    """Format a timestamp in milliseconds to a human-readable string."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def format_duration(duration_ms: int) -> str:
    """Format a duration in milliseconds to a human-readable string."""
    total_seconds = duration_ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours}h {minutes}m {seconds}s"


def test_api_connection(api_token: str, workspace_id: str, user_id: Optional[str] = None) -> bool:
    """Test the API connection."""
    _LOGGER.info("Testing API connection...")
    api = TogglApi(api_token, workspace_id, user_id)
    
    try:
        valid = api.validate_api_token()
        if valid:
            _LOGGER.info("✅ API connection successful!")
        else:
            _LOGGER.error("❌ API connection failed: Invalid credentials")
        return valid
    except Exception as e:
        _LOGGER.error(f"❌ API connection failed: {e}")
        return False


def test_time_entries(api_token: str, workspace_id: str, user_id: Optional[str] = None) -> bool:
    """Test fetching time entries."""
    api = TogglApi(api_token, workspace_id, user_id)
    
    # Test daily time entries
    _LOGGER.info("\nTesting daily time entries...")
    try:
        daily_entries = api.get_daily_time_entries()
        _LOGGER.info(f"Found {len(daily_entries)} daily time entries")
        
        if daily_entries:
            _LOGGER.info("Sample daily time entry:")
            print_time_entry(daily_entries[0])
            
            daily_total = api.calculate_total_duration(daily_entries)
            _LOGGER.info(f"Daily total duration: {format_duration(daily_total)}")
        else:
            _LOGGER.warning("No daily time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Error fetching daily time entries: {e}")
        return False
    
    # Test weekly time entries
    _LOGGER.info("\nTesting weekly time entries...")
    try:
        weekly_entries = api.get_weekly_time_entries()
        _LOGGER.info(f"Found {len(weekly_entries)} weekly time entries")
        
        if weekly_entries:
            weekly_total = api.calculate_total_duration(weekly_entries)
            _LOGGER.info(f"Weekly total duration: {format_duration(weekly_total)}")
        else:
            _LOGGER.warning("No weekly time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Error fetching weekly time entries: {e}")
        return False
    
    # Test monthly time entries
    _LOGGER.info("\nTesting monthly time entries...")
    try:
        monthly_entries = api.get_monthly_time_entries()
        _LOGGER.info(f"Found {len(monthly_entries)} monthly time entries")
        
        if monthly_entries:
            monthly_total = api.calculate_total_duration(monthly_entries)
            _LOGGER.info(f"Monthly total duration: {format_duration(monthly_total)}")
        else:
            _LOGGER.warning("No monthly time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Error fetching monthly time entries: {e}")
        return False
    
    # Test custom period (3 months)
    _LOGGER.info("\nTesting custom period (3 months) time entries...")
    try:
        custom_entries = api.get_custom_period_time_entries(3)
        _LOGGER.info(f"Found {len(custom_entries)} time entries in the last 3 months")
        
        if custom_entries:
            custom_total = api.calculate_total_duration(custom_entries)
            _LOGGER.info(f"3-month total duration: {format_duration(custom_total)}")
        else:
            _LOGGER.warning("No time entries found in the last 3 months")
    except Exception as e:
        _LOGGER.error(f"❌ Error fetching custom period time entries: {e}")
        return False
    
    return True


def print_time_entry(entry: Dict[str, Any]) -> None:
    """Print a time entry in a readable format."""
    print(json.dumps(entry, indent=2))
    
    # Print some key information
    _LOGGER.info(f"  ID: {entry.get('id')}")
    _LOGGER.info(f"  Task: {entry.get('task', {}).get('name', 'N/A')}")
    
    start_time = entry.get('start')
    if start_time:
        _LOGGER.info(f"  Start: {format_timestamp(start_time)}")
    
    end_time = entry.get('end')
    if end_time:
        _LOGGER.info(f"  End: {format_timestamp(end_time)}")
    
    duration = entry.get('duration')
    if duration:
        _LOGGER.info(f"  Duration: {format_duration(duration)}")


def test_time_calculations(api_token: str, workspace_id: str, user_id: Optional[str] = None) -> bool:
    """Test the time calculations."""
    _LOGGER.info("\nTesting time calculations...")
    api = TogglApi(api_token, workspace_id, user_id)
    
    try:
        # Get daily worked time
        daily_data = api.get_daily_worked_time()
        _LOGGER.info(f"Daily worked time: {daily_data.get('duration_hours')}h {daily_data.get('duration_minutes')}m")
        _LOGGER.info(f"Daily entries count: {daily_data.get('entries_count')}")
        
        # Get weekly worked time
        weekly_data = api.get_weekly_worked_time()
        _LOGGER.info(f"Weekly worked time: {weekly_data.get('duration_hours')}h {weekly_data.get('duration_minutes')}m")
        _LOGGER.info(f"Weekly entries count: {weekly_data.get('entries_count')}")
        
        # Get monthly worked time
        monthly_data = api.get_monthly_worked_time()
        _LOGGER.info(f"Monthly worked time: {monthly_data.get('duration_hours')}h {monthly_data.get('duration_minutes')}m")
        _LOGGER.info(f"Monthly entries count: {monthly_data.get('entries_count')}")
        
        return True
    except Exception as e:
        _LOGGER.error(f"❌ Error testing time calculations: {e}")
        return False


def test_time_ranges(api_token: str, workspace_id: str, user_id: Optional[str] = None) -> bool:
    """Test the time ranges used for fetching entries."""
    _LOGGER.info("\nTesting time ranges...")
    api = TogglApi(api_token, workspace_id, user_id)
    
    now = int(time.time() * 1000)  # Current time in milliseconds
    
    # Test daily time range
    start_of_day = now - ((now % 86400000))
    _LOGGER.info(f"Daily time range: {format_timestamp(start_of_day)} to {format_timestamp(now)}")
    
    # Test weekly time range
    start_of_week = now - (7 * 86400000)
    _LOGGER.info(f"Weekly time range: {format_timestamp(start_of_week)} to {format_timestamp(now)}")
    
    # Test monthly time range
    start_of_month = now - (30 * 86400000)
    _LOGGER.info(f"Monthly time range: {format_timestamp(start_of_month)} to {format_timestamp(now)}")
    
    # Test custom period (3 months)
    start_of_3_months = now - (3 * 30 * 86400000)
    _LOGGER.info(f"3-month time range: {format_timestamp(start_of_3_months)} to {format_timestamp(now)}")
    
    return True


def main():
    """Run the tests."""
    parser = argparse.ArgumentParser(description='Test Toggl API integration')
    parser.add_argument('--api-token', required=True, help='Toggl API token')
    parser.add_argument('--workspace-id', required=True, help='Toggl workspace ID')
    parser.add_argument('--user-id', help='Toggl user ID (optional)')
    
    args = parser.parse_args()
    
    _LOGGER.info("Starting Toggl API integration tests...")
    
    # Test API connection
    if not test_api_connection(args.api_token, args.workspace_id, args.user_id):
        _LOGGER.error("API connection test failed. Exiting.")
        sys.exit(1)
    
    # Test time ranges
    test_time_ranges(args.api_token, args.workspace_id, args.user_id)
    
    # Test time entries
    if not test_time_entries(args.api_token, args.workspace_id, args.user_id):
        _LOGGER.error("Time entries test failed. Exiting.")
        sys.exit(1)
    
    # Test time calculations
    if not test_time_calculations(args.api_token, args.workspace_id, args.user_id):
        _LOGGER.error("Time calculations test failed. Exiting.")
        sys.exit(1)
    
    _LOGGER.info("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    main()