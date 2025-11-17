"""Conftest for Toggl Worklog tests."""
import pytest
from unittest.mock import MagicMock

# Mock Home Assistant modules for tests
@pytest.fixture(autouse=True)
def mock_homeassistant_modules():
    """Mock Home Assistant modules."""
    sys_modules = {}
    mock_modules = [
        'homeassistant',
        'homeassistant.config_entries',
        'homeassistant.core',
        'homeassistant.helpers',
        'homeassistant.helpers.config_validation',
        'homeassistant.helpers.update_coordinator',
        'homeassistant.components.sensor',
    ]
    for mod_name in mock_modules:
        sys_modules[mod_name] = MagicMock()
    
    # Mock specific classes/functions if needed
    sys_modules['homeassistant.helpers.update_coordinator'].DataUpdateCoordinator = MagicMock()
    sys_modules['homeassistant.components.sensor'].SensorEntity = MagicMock()
    sys_modules['homeassistant.helpers.entity_platform'].AddEntitiesCallback = MagicMock()
    sys_modules['homeassistant.helpers.typing'].StateType = MagicMock()
    sys_modules['homeassistant.config_entries'].ConfigEntry = MagicMock()
    sys_modules['homeassistant.core'].HomeAssistant = MagicMock()
    sys_modules['homeassistant.core'].callback = lambda f: f # Passthrough decorator

    with pytest.MonkeyPatch().context() as mp:
        for mod_name, mock_obj in sys_modules.items():
            mp.setitem(sys.modules, mod_name, mock_obj)
        yield