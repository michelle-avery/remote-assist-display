from datetime import datetime, timezone
import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import async_register_command, event_message
from homeassistant.core import callback

from .const import (
    CONNECT_WS_COMMAND,
    REGISTER_WS_COMMAND,
    SETTINGS_WS_COMMAND,
    UPDATE_WS_COMMAND,
)
from .remote_assist_display import get_or_register_display

_LOGGER = logging.getLogger(__name__)


async def async_setup_ws_api(hass):
    @websocket_api.websocket_command(
        {vol.Required("type"): CONNECT_WS_COMMAND, vol.Required("display_id"): str}
    )
    @websocket_api.async_response
    async def handle_connect(hass, connection, msg):
        display_id = msg["display_id"]

        @callback
        def send_update(data):
            connection.send_message(event_message(msg["id"], {"result": data}))

        def close_connection():
            dev = get_or_register_display(hass, display_id)
            if dev:
                dev.close_connection(hass, connection)

        connection.subscriptions[msg["id"]] = close_connection
        connection.send_result(msg["id"], "registered")

        dev = get_or_register_display(hass, display_id)
        settings = {"last_seen": datetime.now(tz=timezone.utc).isoformat()}
        dev.update_settings(hass, settings)
        dev.open_connection(hass, connection, msg["id"])
        dev.update(hass, dev.data)
        send_update(dev.data)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): REGISTER_WS_COMMAND,
            vol.Required("display_id"): str,
            vol.Required("hostname"): str,
        }
    )
    @websocket_api.async_response
    async def handle_register(hass, connection, msg):
        display_id = msg["display_id"]
        display_settings = {"registered": True, "hostname": msg["hostname"]}
        dev = get_or_register_display(hass, display_id)
        dev.update_settings(hass, display_settings)
        connection.send_result(msg["id"], dev.settings)

    @websocket_api.websocket_command(
        {vol.Required("type"): SETTINGS_WS_COMMAND, vol.Required("display_id"): str}
    )
    def handle_settings(hass, connection, msg):
        display_id = msg["display_id"]
        display = get_or_register_display(hass, display_id)
        default_dashboard = display.entities.get("default_dashboard", None)
        if default_dashboard:
            default_dashboard = default_dashboard.native_value
        else:
            default_dashboard = None
        settings = {"settings": {"default_dashboard": default_dashboard}}
        connection.send_message(websocket_api.result_message(msg["id"], settings))

    @websocket_api.websocket_command(
        {
            vol.Required("type"): UPDATE_WS_COMMAND,
            vol.Required("display_id"): str,
            vol.Optional("data"): dict,
        }
    )
    @websocket_api.async_response
    async def handle_update(hass, connection, msg):
        """Update the current sensors for the display."""
        display_id = msg["display_id"]

        dev = get_or_register_display(hass, display_id)
        dev.update(hass, msg.get("data", {}))
        connection.send_result(msg["id"])

    async_register_command(hass, handle_connect)
    async_register_command(hass, handle_register)
    async_register_command(hass, handle_settings)
    async_register_command(hass, handle_update)
