"""Tests for the TogglApi class."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date

# Adjust path to import from custom_components
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_components.toggl_worklog.api import TogglApi, TogglApiError

@pytest.fixture
def mock_api_token():
    """Fixture for a mock API token."""
    return "test_api_token"

@pytest.fixture
def mock_workspace_id():
    """Fixture for a mock workspace ID."""
    return "1234567"

@pytest.fixture
def toggl_api(mock_api_token, mock_workspace_id):
    """Fixture for a TogglApi instance."""
    with patch('requests.Session') as mock_session:
        api = TogglApi(mock_api_token, mock_workspace_id)
        api.session = mock_session.return_value
        yield api

def test_toggl_api_init(mock_api_token, mock_workspace_id):
    """Test TogglApi initialization."""
    api = TogglApi(mock_api_token, mock_workspace_id)
    assert api.api_token == mock_api_token
    assert api.workspace_id == mock_workspace_id
    assert api.sync_months == 3 # Default value

def test_toggl_api_init_empty_token():
    """Test TogglApi initialization with an empty token."""
    with pytest.raises(ValueError, match="API token cannot be empty"):
        TogglApi("", "123")

@pytest.mark.parametrize("api_response, expected_result", [
    # Case 1: New structure with "me" object, workspace found
    ({"me": {"id": 1, "workspaces": [{"id": 1234567, "name": "Test"}]}}, True),
    # Case 1: New structure with "me" object, workspace not found
    ({"me": {"id": 1, "workspaces": [{"id": 7654321, "name": "Other"}]}}, False),
    # Case 2: Old structure with a list of users, workspace found
    ([{"id": 1, "workspaces": [{"workspace_id": 1234567, "name": "Test"}]}], True),
    # Case 2: Old structure with a list of users, workspace not found
    ([{"id": 1, "workspaces": [{"workspace_id": 7654321, "name": "Other"}]}], False),
    # Case 3: Flat structure with default_workspace_id, workspace found
    ({"id": 1, "default_workspace_id": 1234567}, True),
    # Case 3: Flat structure with default_workspace_id, workspace not found
    ({"id": 1, "default_workspace_id": 7654321}, False),
    # No user data
    ({}, False),
    ({"me": {}}, False),
    ([], False),
])
def test_validate_api_token(toggl_api, api_response, expected_result):
    """Test validate_api_token method with various API responses."""
    toggl_api.session.request.return_value.status_code = 200
    toggl_api.session.request.return_value.json.return_value = api_response
    toggl_api.session.request.return_value.raise_for_status.return_value = None
    toggl_api.session.request.return_value.content = b'{}' # Simulate content for json()

    assert toggl_api.validate_api_token() == expected_result

def test_validate_api_token_api_error(toggl_api):
    """Test validate_api_token method with an API error."""
    toggl_api.session.request.side_effect = TogglApiError("API error")
    with pytest.raises(TogglApiError): # The _make_request will raise it, validate_api_token catches and returns False
        assert toggl_api.validate_api_token() == False

@pytest.mark.parametrize("flattened_entries, expected_total_duration", [
    # Single entry
    ([{"seconds": 3600}], 3600000),
    # Multiple entries
    ([{"seconds": 1800}, {"seconds": 1800}], 3600000),
    # Multiple entries
    ([{"seconds": 100}, {"seconds": 200}], 300000),
    # No entries
    ([], 0),
    # Entries with None seconds
    ([{"seconds": None}], 0),
    # Mixed entries
    ([{"seconds": 60}, {"seconds": None}, {"seconds": 120}], 180000),
])
def test_calculate_total_duration(toggl_api, flattened_entries, expected_total_duration):
    """Test calculate_total_duration method with flattened entries."""
    assert toggl_api.calculate_total_duration(flattened_entries) == expected_total_duration

def test_get_time_entries_flattens_response(toggl_api):
    """Test that get_time_entries flattens the raw response."""
    mock_raw_response = [
        {"time_entries": [{"id": 1, "seconds": 100}]},
        {"time_entries": [{"id": 2, "seconds": 200}, {"id": 3, "seconds": 300}]},
        {"time_entries": []},
    ]
    with patch.object(toggl_api, '_fetch_raw_time_entries', return_value=mock_raw_response):
        flattened_entries = toggl_api.get_time_entries(date(2025, 1, 1), date(2025, 1, 1))
        assert len(flattened_entries) == 3
        assert flattened_entries[0]['id'] == 1
        assert flattened_entries[1]['id'] == 2
        assert flattened_entries[2]['id'] == 3

def test_filter_entries_by_date(toggl_api):
    """Test _filter_entries_by_date method."""
    entries = [
        {"start": "2025-01-01T10:00:00Z"},
        {"start": "2025-01-02T10:00:00Z"},
        {"start": "2025-01-03T10:00:00Z"},
    ]
    filtered = toggl_api._filter_entries_by_date(entries, date(2025, 1, 1), date(2025, 1, 2))
    assert len(filtered) == 2
    assert filtered[0]['start'].startswith("2025-01-01")
    assert filtered[1]['start'].startswith("2025-01-02")

def test_get_all_entries_for_sync_period_caches(toggl_api):
    """Test that _get_all_entries_for_sync_period caches its result."""
    mock_entries = [{"id": 1, "seconds": 100}]
    with patch.object(toggl_api, 'get_time_entries', return_value=mock_entries) as mock_get_time_entries:
        toggl_api.sync_months = 1
        result1 = toggl_api._get_all_entries_for_sync_period()
        result2 = toggl_api._get_all_entries_for_sync_period()
        
        assert result1 == mock_entries
        assert result2 == mock_entries
        mock_get_time_entries.assert_called_once() # Should only be called once due to caching
