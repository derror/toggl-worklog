"""The Toggl Worklog integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_SYNC_MONTHS,
    SERVICE_SYNC_TIMESHEET,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Toggl Worklog component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Toggl Worklog from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_SYNC_TIMESHEET):
        async def sync_timesheet_service(call: ServiceCall) -> None:
            """Service to sync timesheet data for a specific period."""
            months = call.data.get(CONF_SYNC_MONTHS, 3)
            _LOGGER.info("Syncing timesheet data for the last %d months", months)

            if not hass.data[DOMAIN]:
                _LOGGER.error("No Toggl Worklog integration configured")
                return

            synced_accounts = 0
            failed_accounts = 0

            for coordinator in hass.data.get(DOMAIN, {}).get("coordinators", []):
                try:
                    workspace_id = coordinator.api.workspace_id
                    _LOGGER.info("Syncing timesheet for workspace %s", workspace_id)
                    await coordinator.async_refresh()
                    synced_accounts += 1
                    _LOGGER.info("Successfully synced workspace %s", workspace_id)
                except Exception as err:
                    _LOGGER.error("Error refreshing coordinator for workspace %s: %s",
                                getattr(coordinator.api, 'workspace_id', 'unknown'), err)
                    failed_accounts += 1

            _LOGGER.info(
                "Timesheet sync completed: %d accounts synced, %d failed",
                synced_accounts,
                failed_accounts
            )

        hass.services.async_register(
            DOMAIN,
            SERVICE_SYNC_TIMESHEET,
            sync_timesheet_service,
            schema=vol.Schema({
                vol.Optional(CONF_SYNC_MONTHS, default=3): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=12)
                ),
            }),
        )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)