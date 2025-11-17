"""Config flow for Toggl Worklog integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import TogglApi, TogglApiError
from .const import (
    DOMAIN,
    CONF_API_TOKEN,
    CONF_WORKSPACE_ID,
    CONF_SYNC_MONTHS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    SCAN_INTERVAL_OPTIONS,
    SYNC_MONTHS_OPTIONS,
    SERVICE_SYNC_TIMESHEET,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_TOKEN): str,
        vol.Required(CONF_WORKSPACE_ID): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect to Toggl."""
    api = TogglApi(
        api_token=data[CONF_API_TOKEN],
        workspace_id=data[CONF_WORKSPACE_ID],
    )

    try:
        valid = await hass.async_add_executor_job(api.validate_api_token)
        if not valid:
            raise InvalidAuth
    except TogglApiError as err:
        raise CannotConnect from err
    finally:
        await hass.async_add_executor_job(api.close)

    return {"title": f"Toggl Worklog ({data[CONF_WORKSPACE_ID]})"}


class TogglWorklogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Toggl Worklog."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_WORKSPACE_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return TogglWorklogOptionsFlow(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class TogglWorklogOptionsFlow(config_entries.OptionsFlow):
    """Handle options for the Toggl Worklog integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            options = {}
            try:
                # Process scan interval
                scan_interval_minutes = int(user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL // 60))
                options[CONF_SCAN_INTERVAL] = scan_interval_minutes * 60
            except (ValueError, TypeError) as err:
                _LOGGER.error("Invalid scan interval value: %s", err)
                # Fallback to current value if invalid
                options[CONF_SCAN_INTERVAL] = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            try:
                # Process sync months
                sync_months = int(user_input.get(CONF_SYNC_MONTHS, 3))
                options[CONF_SYNC_MONTHS] = sync_months
            except (ValueError, TypeError) as err:
                _LOGGER.error("Invalid sync months value: %s", err)
                # Fallback to current value if invalid
                options[CONF_SYNC_MONTHS] = self.config_entry.options.get(CONF_SYNC_MONTHS, 3)

            return self.async_create_entry(title="", data=options)

        current_interval_seconds = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        current_interval_minutes = str(current_interval_seconds // 60)
        current_sync_months = str(self.config_entry.options.get(CONF_SYNC_MONTHS, 3))

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current_interval_minutes): vol.In(
                    SCAN_INTERVAL_OPTIONS
                ),
                vol.Optional(CONF_SYNC_MONTHS, default=current_sync_months): vol.In(
                    SYNC_MONTHS_OPTIONS
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )