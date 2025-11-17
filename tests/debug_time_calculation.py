#!/usr/bin/env python3
"""Debug script for time calculation logic."""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import the custom_components
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_components.toggl_worklog.api import TogglApi

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


def format_timestamp(timestamp_ms):
    """Format a timestamp in milliseconds to a human-readable string."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def debug_time_calculation(api_token, workspace_id, user_id=None):
    """Debug the time calculation logic."""
    api = TogglApi(api_token, workspace_id, user_id)
    
    # Get current time
    now = int(time.time() * 1000)
    _LOGGER.debug(f"Current time: {format_timestamp(now)}")
    
    # Debug daily time calculation
    _LOGGER.info("\n=== Debugging Daily Time Calculation ===")
    start_of_day = now - ((now % 86400000))
    _LOGGER.debug(f"Start of day: {format_timestamp(start_of_day)}")
    
    daily_entries = api.get_time_entries(start_of_day, now)
    _LOGGER.info(f"Found {len(daily_entries)} daily time entries")
    
    # Print each entry
    if daily_entries:
        _LOGGER.info("Daily time entries:")
        for i, entry in enumerate(daily_entries[:5]):  # Show first 5 entries
            _LOGGER.info(f"Entry {i+1}:")
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
                hours = duration // 3600000
                minutes = (duration % 3600000) // 60000
                _LOGGER.info(f"  Duration: {hours}h {minutes}m ({duration} ms)")
        
        if len(daily_entries) > 5:
            _LOGGER.info(f"... and {len(daily_entries) - 5} more entries")
    
    # Calculate total duration
    total_duration = api.calculate_total_duration(daily_entries)
    hours = total_duration // 3600000
    minutes = (total_duration % 3600000) // 60000
    _LOGGER.info(f"Total daily duration: {hours}h {minutes}m ({total_duration} ms)")
    
    # Debug the get_daily_worked_time method
    daily_worked_time = api.get_daily_worked_time()
    _LOGGER.info("\nResult from get_daily_worked_time:")
    _LOGGER.info(f"  Total duration: {daily_worked_time.get('total_duration')} ms")
    _LOGGER.info(f"  Hours: {daily_worked_time.get('duration_hours')}")
    _LOGGER.info(f"  Minutes: {daily_worked_time.get('duration_minutes')}")
    _LOGGER.info(f"  Entries count: {daily_worked_time.get('entries_count')}")
    
    # Debug weekly time calculation
    _LOGGER.info("\n=== Debugging Weekly Time Calculation ===")
    start_of_week = now - (7 * 86400000)
    _LOGGER.debug(f"Start of week: {format_timestamp(start_of_week)}")
    
    weekly_worked_time = api.get_weekly_worked_time()
    _LOGGER.info("Result from get_weekly_worked_time:")
    _LOGGER.info(f"  Total duration: {weekly_worked_time.get('total_duration')} ms")
    _LOGGER.info(f"  Hours: {weekly_worked_time.get('duration_hours')}")
    _LOGGER.info(f"  Minutes: {weekly_worked_time.get('duration_minutes')}")
    _LOGGER.info(f"  Entries count: {weekly_worked_time.get('entries_count')}")
    
    # Debug monthly time calculation
    _LOGGER.info("\n=== Debugging Monthly Time Calculation ===")
    start_of_month = now - (30 * 86400000)
    _LOGGER.debug(f"Start of month: {format_timestamp(start_of_month)}")
    
    monthly_worked_time = api.get_monthly_worked_time()
    _LOGGER.info("Result from get_monthly_worked_time:")
    _LOGGER.info(f"  Total duration: {monthly_worked_time.get('total_duration')} ms")
    _LOGGER.info(f"  Hours: {monthly_worked_time.get('duration_hours')}")
    _LOGGER.info(f"  Minutes: {monthly_worked_time.get('duration_minutes')}")
    _LOGGER.info(f"  Entries count: {monthly_worked_time.get('entries_count')}")


def main():
    """Run the debug script."""
    parser = argparse.ArgumentParser(description='Debug time calculation logic')
    parser.add_argument('--api-token', required=True, help='Toggl API token')
    parser.add_argument('--workspace-id', required=True, help='Toggl workspace ID')
    parser.add_argument('--user-id', help='Toggl user ID (optional)')
    
    args = parser.parse_args()
    
    debug_time_calculation(args.api_token, args.workspace_id, args.user_id)


if __name__ == "__main__":
    main()