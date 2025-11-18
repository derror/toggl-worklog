"""Constants for the Toggl Worklog integration."""

# Base component constants
DOMAIN = "toggl_worklog"
NAME = "Toggl Worklog"
VERSION = "1.0.0"

# Configuration and options
CONF_API_TOKEN = "api_token"
CONF_WORKSPACE_ID = "workspace_id"
CONF_SYNC_MONTHS = "sync_months"
CONF_SCAN_INTERVAL = "scan_interval"

# Services
SERVICE_SYNC_TIMESHEET = "sync_timesheet"

# Defaults
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour

# Scan interval options (in minutes)
SCAN_INTERVAL_OPTIONS = {
    "5": "5 minutes",
    "15": "15 minutes",
    "30": "30 minutes",
    "60": "1 hour",
    "120": "2 hours",
    "180": "3 hours",
}

# Sync months options
SYNC_MONTHS_OPTIONS = {
    "1": "1 month",
    "3": "3 months",
    "6": "6 months",
    "12": "12 months",
}

# Sensor names
SENSOR_DAILY_WORKED_TIME = "daily_worked_time"
SENSOR_WEEKLY_WORKED_TIME = "weekly_worked_time"
SENSOR_MONTHLY_WORKED_TIME = "monthly_worked_time"

# Calendar-based sensor names
SENSOR_CURRENT_DAY_WORKED_TIME = "current_day_worked_time"
SENSOR_CURRENT_WEEK_WORKED_TIME = "current_week_worked_time"
SENSOR_CURRENT_MONTH_WORKED_TIME = "current_month_worked_time"

# API endpoints
API_BASE_URL = "https://api.track.toggl.com"
API_REPORTS_URL = f"{API_BASE_URL}/reports/api/v3"
API_V9_URL = f"{API_BASE_URL}/api/v9"
API_ME_ENDPOINT = f"{API_V9_URL}/me"
API_TIME_ENTRIES_ENDPOINT = f"{API_REPORTS_URL}/workspace/{{workspace_id}}/search/time_entries"
API_V9_TIME_ENTRIES_ENDPOINT = f"{API_V9_URL}/me/time_entries"


# Sensor attributes
ATTR_TOTAL_DURATION = "total_duration"
ATTR_DURATION_HOURS = "duration_hours"
ATTR_DURATION_MINUTES = "duration_minutes"
ATTR_ENTRIES_COUNT = "entries_count"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_TASKS = "tasks"