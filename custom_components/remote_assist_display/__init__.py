"""The Remote Assist Display integration."""

import json
import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    DATA_ADDERS,
    DATA_CONFIG_ENTRY,
    DATA_DISPLAYS,
    DOMAIN,
    FRONTEND_SCRIPT_URL,
)
from .service import async_setup_services
from .ws_api import async_setup_ws_api

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

PLATFORMS = [Platform.SELECT, Platform.SENSOR, Platform.SWITCH, Platform.TEXT]


def get_version(hass: HomeAssistant):
    """Get the version of the Remote Assist Display integration."""
    path = Path(
        hass.config.path("custom_components/remote_assist_display/manifest.json")
    )
    with path.open(encoding="utf-8") as fp:
        manifest = json.load(fp)
        return manifest["version"]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Remote Assist Display component."""

    hass.data[DOMAIN] = {
        DATA_DISPLAYS: {},
        DATA_ADDERS: {},
    }

    version = await hass.async_add_executor_job(get_version, hass)

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                FRONTEND_SCRIPT_URL,
                hass.config.path(
                    "custom_components/remote_assist_display/remote_assist_display.js"
                ),
                True,
            )
        ]
    )
    add_extra_js_url(hass, FRONTEND_SCRIPT_URL + "?" + version)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Remote Assist Display Controller from a config entry."""
    hass.data[DOMAIN][DATA_CONFIG_ENTRY] = entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_setup_services(hass)
    await async_setup_ws_api(hass)

    async def _handle_config_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle options update."""
        displays = hass.data[DOMAIN][DATA_DISPLAYS]
        # Update all active displays with new settings
        for display in displays.values():
            display.update(hass, {"settings": entry.options})

    entry.async_on_unload(entry.add_update_listener(_handle_config_update))
    return True


async def async_remove_config_entry_device(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    device_entry: dr.DeviceEntry,
) -> bool:
    """Remove a device from the Remote Assist Display integration."""
    dr.async_get(hass).async_remove_device(device_entry.id)
    return True
