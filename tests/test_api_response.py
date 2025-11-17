#!/usr/bin/env python3
"""Test script for Toggl API response structure."""
import argparse
import json
import logging
import requests
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)


def format_timestamp(timestamp_ms):
    """Format a timestamp in milliseconds to a human-readable string."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def test_time_entries_endpoint(api_token, workspace_id, start_date=None, end_date=None):
    """Test the time entries endpoint directly."""
    _LOGGER.info("Testing time entries endpoint directly...")
    
    headers = {
        "Authorization": api_token,
        "Content-Type": "application/json"
    }
    
    # If no dates provided, use last 24 hours
    if not start_date:
        end_date = int(datetime.now().timestamp() * 1000)
        start_date = end_date - (24 * 60 * 60 * 1000)  # 24 hours ago
    
    params = {
        "start_date": start_date,
        "end_date": end_date
    }
    
    _LOGGER.info(f"Time range: {format_timestamp(start_date)} to {format_timestamp(end_date)}")
    
    url = f"https://api.track.toggl.com/api/v9/me/time_entries"
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        _LOGGER.info(f"Response status code: {response.status_code}")
        
        if "data" in data:
            entries = data["data"]
            _LOGGER.info(f"Found {len(entries)} time entries")
            
            if entries:
                _LOGGER.info("First entry structure:")
                print(json.dumps(entries[0], indent=2))
                
                # Check for key fields
                _LOGGER.info("\nChecking key fields in time entries:")
                for field in ["id", "task", "user", "start", "end", "duration"]:
                    if field in entries[0]:
                        _LOGGER.info(f"✅ Field '{field}' is present")
                    else:
                        _LOGGER.warning(f"❌ Field '{field}' is missing")
                
                # Calculate total duration
                total_duration = sum(entry.get("duration", 0) for entry in entries)
                hours = total_duration // 3600000
                minutes = (total_duration % 3600000) // 60000
                _LOGGER.info(f"\nTotal duration: {hours}h {minutes}m ({total_duration} ms)")
            else:
                _LOGGER.warning("No time entries found in the response")
        else:
            _LOGGER.error("Response does not contain 'data' field")
            _LOGGER.info("Full response:")
            print(json.dumps(data, indent=2))
    
    except requests.exceptions.RequestException as e:
        _LOGGER.error(f"Request failed: {e}")
        if hasattr(e, "response") and e.response:
            _LOGGER.error(f"Response status code: {e.response.status_code}")
            _LOGGER.error(f"Response text: {e.response.text}")
    
    except Exception as e:
        _LOGGER.error(f"Error: {e}")


def main():
    """Run the tests."""
    parser = argparse.ArgumentParser(description='Test Toggl API response structure')
    parser.add_argument('--api-token', required=True, help='Toggl API token')
    parser.add_argument('--workspace-id', required=True, help='Toggl workspace ID')
    parser.add_argument('--start-date', type=int, help='Start date in milliseconds')
    parser.add_argument('--end-date', type=int, help='End date in milliseconds')
    
    args = parser.parse_args()
    
    test_time_entries_endpoint(
        args.api_token,
        args.workspace_id,
        args.start_date,
        args.end_date
    )


if __name__ == "__main__":
    main()