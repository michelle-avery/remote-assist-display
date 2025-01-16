"""Support for Remote Assist Display services."""

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv, device_registry

from .const import (
    DATA_DISPLAYS,
    DOMAIN,
    NAVIGATE_SERVICE,
    NAVIGATE_URL_SERVICE,
    NAVIGATE_URL_WS_COMMAND,
    NAVIGATE_WS_COMMAND,
)

NAVIGATE_URL_SCHEMA = vol.Schema(
    {vol.Required("target"): cv.ensure_list, vol.Required("url"): cv.string}
)

NAVIGATE_SCHEMA = vol.Schema(
    {vol.Required("target"): cv.ensure_list, vol.Required("path"): cv.string}
)


@callback
def async_setup_services(hass) -> None:
    """Set up the Remote Assist Display services."""

    async def async_call_rad_service(service_call):
        """Call a Remote Assist Display service."""
        service = service_call.service

        if service == NAVIGATE_URL_SERVICE:
            await navigate_url(service_call)

        elif service == NAVIGATE_SERVICE:
            await navigate(service_call)

    hass.services.async_register(
        DOMAIN, NAVIGATE_URL_SERVICE, async_call_rad_service, schema=NAVIGATE_URL_SCHEMA
    )

    hass.services.async_register(
        DOMAIN, NAVIGATE_SERVICE, async_call_rad_service, schema=NAVIGATE_SCHEMA
    )

    async def navigate_url(service_call):
        """Make a specific device navigate to the specified URL."""
        displays = hass.data[DOMAIN][DATA_DISPLAYS]
        dr = device_registry.async_get(hass)
        for target in service_call.data.get("target"):
            display_id = list(dr.async_get(target).identifiers)[0][1]
            display = displays.get(display_id)
            hass.create_task(
                display.send(NAVIGATE_URL_WS_COMMAND, url=service_call.data.get("url"))
            )

    async def navigate(service_call):
        """Make a specific device navigate to the specified path."""
        displays = hass.data[DOMAIN][DATA_DISPLAYS]
        dr = device_registry.async_get(hass)
        for target in service_call.data.get("target"):
            display_id = list(dr.async_get(target).identifiers)[0][1]
            display = displays.get(display_id)
            hass.create_task(
                display.send(NAVIGATE_WS_COMMAND, path=service_call.data.get("path"))
            )
