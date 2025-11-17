# Toggl Worklog Integration Tests

This directory contains test scripts to help diagnose issues with the Toggl Worklog integration.

## Available Tests

1. **test_toggl_api.py** - (Work in Progress) Tests the Toggl API integration.
2. **standalone_api_test.py** - A standalone script to test Toggl API functionality outside of Home Assistant.

## Running the Tests

### 1. Standalone API Test

This test verifies the API connection and fetches time entries. It's the best way to check your credentials and basic API communication.

```bash
python3 tests/standalone_api_test.py --api-token YOUR_API_TOKEN --workspace-id YOUR_WORKSPACE_ID
```

## Troubleshooting

If the tests reveal issues, here are some common problems and solutions:

1. **API Connection Issues**:
   - Verify your API token is correct and has the necessary permissions.
   - Check your internet connection.
   - Ensure the workspace ID is correct.

2. **Empty Time Entries**:
   - Verify you have time entries in the specified time periods.
   - Check the date ranges being used in the API calls.