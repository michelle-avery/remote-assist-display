"""The Remote Assist Display integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DATA_ADDERS, DATA_DISPLAYS, DOMAIN
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
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_setup_services(hass)
    await async_setup_ws_api(hass)

    return True
