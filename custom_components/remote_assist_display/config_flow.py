from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import EntitySelector

from .const import DOMAIN


def remote_assist_display_config_option_schema(
    hass: HomeAssistant,
    options: dict[str, Any] | MappingProxyType[str, Any],
) -> vol.Schema:
    """Return the options schema for Remote Assist Display."""
    return vol.Schema(
        {
            vol.Optional(
                "assist_entity_id", default=options.get("assist_entity_name", None)
            ): EntitySelector({"domain": "assist_satellite"}),
            vol.Optional("event_type", default=options.get("event_type", None)): str,
        }
    )


def remote_assist_display_config_schema(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> vol.Schema:
    """Return the config schema for Remote Assist Display."""
    data = {}
    if hasattr(entry, "data"):
        data = entry.data
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): str,
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

    async def async_step_registration(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by registration."""
        await self.async_set_unique_id(user_input["id"])
        self._abort_if_unique_id_configured(updates={CONF_HOST: user_input["hostname"]})
        self._name = user_input["hostname"]
        self._host = user_input["hostname"]
        return self.async_create_entry(title=self._name, data={CONF_HOST: self._host})

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> RemoteAssistDisplayOptionsFlowHandler:
        """Create the options flow."""
        return RemoteAssistDisplayOptionsFlowHandler()

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration."""
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        assert config_entry is not None
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            options: dict[str, Any] = {}
            if hasattr(self, "config_entry"):
                options = self.config_entry.data
            return self.async_show_form(
                step_id="user",
                data_schema=remote_assist_display_config_schema(self.hass, options),
            )
        return self.async_create_entry(
            title=user_input[CONF_HOST],
            data=user_input,
        )
