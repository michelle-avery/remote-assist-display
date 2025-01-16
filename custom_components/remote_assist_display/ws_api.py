from datetime import datetime, timezone
import logging

import voluptuous as vol
import time

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api import async_register_command, event_message
from homeassistant.core import callback

from .const import (
    CONNECT_WS_COMMAND,
    DATA_STORE,
    DOMAIN,
    NAVIGATE_URL_SERVICE,
    REGISTER_WS_COMMAND,
    SETTINGS_WS_COMMAND,
    PING_WS_COMMAND,
    UPDATE_WS_COMMAND,
)
from .remote_assist_display import (
    delete_display,
    get_display_by_connection,
    get_or_register_display,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_ws_api(hass):
    @websocket_api.websocket_command(
        {vol.Required("type"): CONNECT_WS_COMMAND, vol.Required("display_id"): str}
    )
    @websocket_api.async_response
    async def handle_connect(hass, connection, msg):
        display_id = msg["display_id"]
        store = hass.data[DOMAIN][DATA_STORE]

        @callback
        def send_update(data):
            connection.send_message(event_message(msg["id"], {"result": data}))

        store_listener = store.add_listener(send_update)

        def close_connection():
            store_listener()
            dev = get_or_register_display(hass, display_id)
            if dev:
                dev.close_connection(hass, connection)

        connection.subscriptions[msg["id"]] = close_connection
        connection.send_result(msg["id"], "registered")

        if store.get_display(display_id).registered:
            dev = get_or_register_display(hass, display_id)
            dev.update_settings(hass, store.get_display(display_id).asdict())
            dev.open_connection(hass, connection, msg["id"])
            await store.async_set_display(
                display_id, last_seen=datetime.now(tz=timezone.utc).isoformat()
            )
        send_update(store.asdict())

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
        store = hass.data[DOMAIN][DATA_STORE]
        display_settings = {"registered": True}
        data = {"hostname": msg["hostname"]}
        dev = get_or_register_display(hass, display_id)
        dev.update_settings(hass, data)
        display_settings.update(data)
        await store.async_set_display(display_id, **display_settings)
        connection.send_result(msg["id"], dev.settings)

    @websocket_api.websocket_command(
        {vol.Required("type"): SETTINGS_WS_COMMAND, vol.Required("display_id"): str}
    )
    def handle_settings(hass, connection, msg):
        display_id = msg["display_id"]
        store = hass.data[DOMAIN][DATA_STORE]
        settings = store.get_display(display_id).asdict()["settings"]
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
        store = hass.data[DOMAIN][DATA_STORE]

        if store.get_display(display_id).registered:
            dev = get_or_register_display(hass, display_id)
            dev.update(hass, msg.get("data", {}))
        connection.send_result(msg["id"])

    async_register_command(hass, handle_connect)
    async_register_command(hass, handle_register)
    async_register_command(hass, handle_settings)
    async_register_command(hass, handle_update)
