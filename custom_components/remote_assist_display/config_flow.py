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

from .const import (
    DEFAULT_DEVICE_NAME_STORAGE_KEY,
    DEFAULT_HOME_ASSISTANT_DASHBOARD,
    DOMAIN,
)


def empty_str_to_default(default_value: str) -> Any:
    """Convert empty string to default value."""

    def _convert(value: Any) -> Any:
        if str(value).strip() == "":
            return default_value
        return value

    return _convert


def remote_assist_display_config_option_schema(
    hass: HomeAssistant,
    options: dict[str, Any] | MappingProxyType[str, Any],
) -> vol.Schema:
    """Return the options schema for Remote Assist Display."""
    return vol.Schema(
        {
            vol.Optional(
                "event_type",
                default=options.get("event_type", ""),
            ): str,
            vol.Optional(
                "default_dashboard_path",
                default=options.get(
                    "default_dashboard_path", DEFAULT_HOME_ASSISTANT_DASHBOARD
                ),
            ): str,
            vol.Optional(
                "device_name_storage_key",
                default=options.get(
                    "device_name_storage_key", DEFAULT_DEVICE_NAME_STORAGE_KEY
                ),
            ): str,
            vol.Required(
                "hide_header",
                default=options.get("hide_header", False),
            ): bool,
            vol.Required(
                "hide_sidebar",
                default=options.get("hide_sidebar", False),
            ): bool,
        }
    )


class RemoteAssistDisplayOptionsFlowHandler(OptionsFlow):
    """Remote Assist Display config flow options handler."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""

        if user_input is not None:
            # Transform empty strings to defaults
            if not user_input.get("default_dashboard_path", "").strip():
                user_input["default_dashboard_path"] = DEFAULT_HOME_ASSISTANT_DASHBOARD
            if not user_input.get("device_name_storage_key", "").strip():
                user_input["device_name_storage_key"] = DEFAULT_DEVICE_NAME_STORAGE_KEY

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
