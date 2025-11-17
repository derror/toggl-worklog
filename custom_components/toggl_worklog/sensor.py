"""Sensor platform for Toggl Worklog integration."""
import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import TogglApi
from .const import (
    CONF_API_TOKEN,
    CONF_WORKSPACE_ID,
    CONF_SCAN_INTERVAL,
    CONF_SYNC_MONTHS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SENSOR_DAILY_WORKED_TIME,
    SENSOR_WEEKLY_WORKED_TIME,
    SENSOR_MONTHLY_WORKED_TIME,
    SENSOR_CURRENT_DAY_WORKED_TIME,
    SENSOR_CURRENT_WEEK_WORKED_TIME,
    SENSOR_CURRENT_MONTH_WORKED_TIME,
    ATTR_TOTAL_DURATION,
    ATTR_DURATION_HOURS,
    ATTR_DURATION_MINUTES,
    ATTR_ENTRIES_COUNT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Toggl Worklog sensors based on a config entry."""
    _LOGGER.info(
        "Setting up Toggl Worklog sensors for workspace_id=%s",
        entry.data[CONF_WORKSPACE_ID]
    )

    sync_months = entry.options.get(CONF_SYNC_MONTHS, 3) # Default to 3 months
    api = TogglApi(
        api_token=entry.data[CONF_API_TOKEN],
        workspace_id=entry.data[CONF_WORKSPACE_ID],
        sync_months=sync_months,
    )

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = TogglWorklogDataUpdateCoordinator(
        hass,
        _LOGGER,
        api=api,
        name=f"{DOMAIN}_{entry.data[CONF_WORKSPACE_ID]}",
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {}).setdefault("coordinators", []).append(coordinator)

    entities = [
        TogglWorklogSensor(
            coordinator,
            entry,
            SENSOR_DAILY_WORKED_TIME,
            "Daily Worked Time (Last 24h)",
            "mdi:clock-outline",
            "h",
        ),
        TogglWorklogSensor(
            coordinator,
            entry,
            SENSOR_WEEKLY_WORKED_TIME,
            "Weekly Worked Time (Last 7d)",
            "mdi:calendar-week",
            "h",
        ),
        TogglWorklogSensor(
            coordinator,
            entry,
            SENSOR_MONTHLY_WORKED_TIME,
            "Monthly Worked Time (Last 30d)",
            "mdi:calendar-month",
            "h",
        ),
        TogglWorklogSensor(
            coordinator,
            entry,
            SENSOR_CURRENT_DAY_WORKED_TIME,
            "Today's Worked Time",
            "mdi:clock-time-eight",
            "h",
        ),
        TogglWorklogSensor(
            coordinator,
            entry,
            SENSOR_CURRENT_WEEK_WORKED_TIME,
            "This Week's Worked Time",
            "mdi:calendar-week-begin",
            "h",
        ),
        TogglWorklogSensor(
            coordinator,
            entry,
            SENSOR_CURRENT_MONTH_WORKED_TIME,
            "This Month's Worked Time",
            "mdi:calendar-today",
            "h",
        ),
    ]

    async_add_entities(entities)


class TogglWorklogDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Toggl Worklog data."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        api: TogglApi,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Toggl API."""
        try:
            _LOGGER.info("Updating Toggl Worklog data")

            # Fetch all data concurrently
            daily_data = await self.hass.async_add_executor_job(self.api.get_daily_worked_time)
            weekly_data = await self.hass.async_add_executor_job(self.api.get_weekly_worked_time)
            monthly_data = await self.hass.async_add_executor_job(self.api.get_monthly_worked_time)
            current_day_data = await self.hass.async_add_executor_job(self.api.get_current_day_worked_time)
            current_week_data = await self.hass.async_add_executor_job(self.api.get_current_week_worked_time)
            current_month_data = await self.hass.async_add_executor_job(self.api.get_current_month_worked_time)

            _LOGGER.info("Successfully updated Toggl Worklog data - Today: %s entries, This Week: %s entries, This Month: %s entries",
                        current_day_data.get("entries_count", 0),
                        current_week_data.get("entries_count", 0),
                        current_month_data.get("entries_count", 0))

            return {
                SENSOR_DAILY_WORKED_TIME: daily_data,
                SENSOR_WEEKLY_WORKED_TIME: weekly_data,
                SENSOR_MONTHLY_WORKED_TIME: monthly_data,
                SENSOR_CURRENT_DAY_WORKED_TIME: current_day_data,
                SENSOR_CURRENT_WEEK_WORKED_TIME: current_week_data,
                SENSOR_CURRENT_MONTH_WORKED_TIME: current_month_data,
            }
        except TogglApiError as err:
            _LOGGER.error("Error fetching Toggl Worklog data: %s", err)
            raise UpdateFailed(f"Error communicating with Toggl API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error fetching Toggl Worklog data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err


class TogglWorklogSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Toggl Worklog sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TogglWorklogDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name: str,
        icon: str,
        unit_of_measurement: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"Toggl Worklog ({config_entry.data[CONF_WORKSPACE_ID]})",
            "manufacturer": "Toggl",
            "model": "Worklog",
        }
        _LOGGER.debug("Created sensor: %s with unique_id: %s", name, self._attr_unique_id)

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data and self._sensor_type in self.coordinator.data:
            data = self.coordinator.data[self._sensor_type]
            hours = data.get(ATTR_DURATION_HOURS, 0)
            minutes = data.get(ATTR_DURATION_MINUTES, 0)
            return round(hours + (minutes / 60), 2)
        return 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data and self._sensor_type in self.coordinator.data:
            data = self.coordinator.data[self._sensor_type]
            return {
                ATTR_TOTAL_DURATION: data.get(ATTR_TOTAL_DURATION, 0),
                ATTR_DURATION_HOURS: data.get(ATTR_DURATION_HOURS, 0),
                ATTR_DURATION_MINUTES: data.get(ATTR_DURATION_MINUTES, 0),
                ATTR_ENTRIES_COUNT: data.get(ATTR_ENTRIES_COUNT, 0),
            }
        return {}