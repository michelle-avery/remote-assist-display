"""Provides an HTTP API for the Remote Assist Display integration."""

from http import HTTPStatus

from aiohttp.web import Request, Response
import voluptuous as vol

from homeassistant.components.http import KEY_HASS, HomeAssistantView
from homeassistant.components.http.data_validator import RequestDataValidator
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.util import slugify

from .const import DOMAIN


class RegistrationsView(HomeAssistantView):
    """A view that accepts registration requests from Remote Assist Display devices."""

    url = "/api/remote_assist_display/register"
    name = "api:remote_assist_display:register"

    @RequestDataValidator(
        vol.Schema(
            {
                vol.Required("hostname"): cv.string,
                vol.Required("id"): cv.string,
            }
        )
    )
    async def post(self, request: Request, data: dict) -> Response:
        """Handle the POST request for the registration view."""
        hass = request.app[KEY_HASS]
        hostname = data["hostname"]
        device_id = data["id"]
        device_name = slugify(hostname)

        response = await hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "registration"},
                data={
                    "hostname": hostname,
                    "id": device_id,
                    "name": device_name,
                },
            )
        )
        if response["type"] == "abort" and response["reason"] == "already_configured":
            return self.json(
                {"info": "Device already registered"},
                HTTPStatus.OK,
            )
        if response["type"] == "create_entry":
            return self.json(
                {"info": "Device registered"},
                HTTPStatus.CREATED,
            )
        return self.json(
            {},
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class ConfigurationView(HomeAssistantView):
    """A view that returns the configuration options for a Remote Assist Display device."""

    url = "/api/remote_assist_display/config/{device_id}"
    name = "api:remote_assist_display:config"

    async def get(self, request: Request, device_id: str) -> Response:
        """Return the options for the specified Remote Assist Display device."""
        hass = request.app[KEY_HASS]
        config_entry = hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN, device_id
        )
        if not config_entry:
            return self.json(
                {"error": "Device not found"},
                HTTPStatus.NOT_FOUND,
            )
        return self.json(dict(config_entry.options), HTTPStatus.OK)
