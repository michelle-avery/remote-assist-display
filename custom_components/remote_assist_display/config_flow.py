from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN


def remote_assist_display_config_option_schema(
    hass: HomeAssistant,
    options: dict[str, Any] | MappingProxyType[str, Any],
) -> vol.Schema:
    """Return the options schema for Remote Assist Display."""
    return vol.Schema(
        {
            vol.Optional(
                "default_dashboard_path",
                default=options.get("default_dashboard_path", None),
            ): str,
            vol.Optional(
                "default_timeout_seconds",
                default=options.get("default_timeout_seconds", None),
            ): int,
            vol.Optional(
                "default_event_type",
                default=options.get("default_event_type", None),
            ): str,
        }
    )


class RemoteAssistDisplayOptionsFlowHandler(OptionsFlow):
    """Remote Assist Display config flow options handler."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""

        if user_input is not None:
            return self.async_create_entry(
                title="Remote Assist Display",
                data=user_input,
            )
        options: dict[str, Any] = self.config_entry.options
        schema = remote_assist_display_config_option_schema(self.hass, options)
        return self.async_show_form(step_id="init", data_schema=schema)


class RemoteAssistDisplayConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Remote Assist Display."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> RemoteAssistDisplayOptionsFlowHandler:
        """Create the options flow."""
        return RemoteAssistDisplayOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="Remote Assist Display", data={})
