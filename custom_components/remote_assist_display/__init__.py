"""The Remote Assist Display integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DATA_ADDERS, DATA_DISPLAYS, DOMAIN, DATA_CONFIG_ENTRY
from .service import async_setup_services
from .ws_api import async_setup_ws_api

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

PLATFORMS = [Platform.SENSOR, Platform.TEXT]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Remote Assist Display component."""

    hass.data[DOMAIN] = {
        DATA_DISPLAYS: {},
        DATA_ADDERS: {},
    }

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
