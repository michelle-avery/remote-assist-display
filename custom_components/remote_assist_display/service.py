"""Support for Remote Assist Display services."""

from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv


import voluptuous as vol

from .const import DOMAIN, NAVIGATE_EVENT, NAVIGATE_SERVICE


NAVIGATE_SCHEMA = vol.Schema(
    {vol.Required("target_device"): cv.string, vol.Required("url"): cv.string}
)


@callback
def async_setup_services(hass) -> None:
    """Set up the Remote Assist Display services."""

    async def async_call_rad_service(service_call):
        """Call a Remote Assist Display service."""
        service = service_call.service

        if service == NAVIGATE_SERVICE:
            await navigate(service_call)

    hass.services.async_register(
        DOMAIN, NAVIGATE_SERVICE, async_call_rad_service, schema=NAVIGATE_SCHEMA
    )

    async def navigate(service_call):
        """Make a specific device navigate to the specified URL."""
        device = service_call.data.get("target_device")
        url = service_call.data.get("url")
        event = NAVIGATE_EVENT
        hass.bus.async_fire(event, event_data={"target_device": device, "url": url})
