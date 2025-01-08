"""Provides an HTTP API for the Remote Assist Display integration."""

from http import HTTPStatus

from aiohttp.web import Request, Response
import voluptuous as vol

from homeassistant.components.http import KEY_HASS, HomeAssistantView
from homeassistant.components.http.data_validator import RequestDataValidator
from homeassistant.helpers import config_validation as cv
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

        await hass.async_create_task(
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
        return self.json(
            {},
            status=HTTPStatus.CREATED,
        )
