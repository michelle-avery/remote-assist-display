"""Support for Remote Assist Display services."""

import voluptuous as vol

from homeassistant.core import callback, SupportsResponse
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
    {
        vol.Optional("target"): cv.ensure_list,
        vol.Optional("device_id"): cv.ensure_list,
        vol.Required("path"): cv.string,
    }
)


async def _get_display_for_target(hass, target):
    """Get a display instance for a target device.

    Args:
        hass: HomeAssistant instance
        target: Target device identifier

    Returns:
        tuple: (display_id, display) if successful

    Raises:
        ValueError: If device is invalid or display not found

    """
    displays = hass.data[DOMAIN][DATA_DISPLAYS]
    dr = device_registry.async_get(hass)
    device = dr.async_get(target)
    if device is None:
        raise ValueError(f"Invalid target device: {target}")

    display_id = list(device.identifiers)[0][1]
    display = displays.get(display_id)

    if display is None:
        raise ValueError(f"Display not found for device: {target}")

    return display_id, display


async def _process_targets(hass, targets, command, **command_args):
    """Process multiple targets with a given command.

    Args:
        hass: HomeAssistant instance
        targets: List of target device identifiers
        command: WebSocket command to send
        command_args: Additional arguments for the command

    Returns:
        dict: Response containing success status and results
    """
    results = []

    for target in targets:
        try:
            display_id, display = await _get_display_for_target(hass, target)

            # Create the task for the command
            hass.create_task(display.send(command, **command_args))

            results.append(
                {"target": target, "status": "success", "display_id": display_id}
            )

        except ValueError as e:
            results.append({"target": target, "status": "error", "error": str(e)})

    return {
        "success": all(r["status"] == "success" for r in results),
        "results": results,
    }

@callback
def async_setup_services(hass) -> None:
    """Set up the Remote Assist Display services."""

    async def async_call_rad_service(service_call):
        """Call a Remote Assist Display service."""
        service = service_call.service

        try:
            if service == NAVIGATE_URL_SERVICE:
                return await navigate_url(service_call)
            if service == NAVIGATE_SERVICE:
                return await navigate(service_call)
        except ValueError as e:
            return {"success": False, "error": str(e)}

    async def navigate_url(service_call):
        """Make specific devices navigate to the specified URL."""
        return await _process_targets(
            hass=hass,
            targets=service_call.data.get("target", service_call.data.get("device_id")),
            command=NAVIGATE_URL_WS_COMMAND,
            url=service_call.data.get("url"),
        )

    async def navigate(service_call):
        """Make specific devices navigate to the specified path."""
        return await _process_targets(
            hass=hass,
            targets=service_call.data.get("target", service_call.data.get("device_id")),
            command=NAVIGATE_WS_COMMAND,
            path=service_call.data.get("path"),
        )

    hass.services.async_register(
        DOMAIN, NAVIGATE_URL_SERVICE, async_call_rad_service, schema=NAVIGATE_URL_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )

    hass.services.async_register(
        DOMAIN, NAVIGATE_SERVICE, async_call_rad_service, schema=NAVIGATE_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )