import asyncio
import logging
from typing import Optional

import webview
from flask import current_app

logger = logging.getLogger(__name__)


class DisplayState:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.websocket_manager = None
        self.load_card_timer: Optional[asyncio.Task] = None

    def set_websocket_manager(self, manager):
        self.websocket_manager = manager

    async def update_current_url(self, url):
        """Send the current URL to the server."""
        if self.websocket_manager and self.websocket_manager.client:
            data = {"display": {"current_url": url}}
            display_id = current_app.config["UNIQUE_ID"]
            command_type = "remote_assist_display/update"
            message = {"type": command_type, "display_id": display_id, "data": data}

            response = await self.websocket_manager.client.send_command(message)
            logger.debug(f"Update current URL response: {response}")

    async def load_url(self, url):
        """Load a URL in the webview and update server."""
        # Update the webview immediately
        webview.windows[0].load_url(url)
        self.set_local_storage()
        # Queue the server update as a separate task
        if self.websocket_manager and self.websocket_manager.client:
            asyncio.create_task(self.update_current_url(url))

    def set_local_storage(self):
        key = current_app.config["DEVICE_NAME_KEY"]
        value = current_app.config["UNIQUE_ID"]
        webview.windows[0].evaluate_js(f"""
            localStorage.setItem("{key}", "{value}")
        """)

    async def load_card(self, event, expire_time=None):
        card_path = event.get("path")
        if card_path and card_path.startswith("/"):
            card_path = card_path[1:]
        hass_url = current_app.config["url"]

        if card_path:
            new_url = f"{hass_url}/{card_path}"
            default_dashboard_url = (
                f"{hass_url}/{current_app.config.get('default_dashboard')}"
            )
            await self.load_url(new_url)
            self.set_local_storage()

            # Cancel any existing timer
            if self.load_card_timer and not self.load_card_timer.done():
                self.load_card_timer.cancel()

            # Start a new async timer if expire_time is set
            if expire_time:

                async def timer_callback():
                    try:
                        await asyncio.sleep(expire_time)
                        await self.load_url(default_dashboard_url)
                    except asyncio.CancelledError:
                        pass

                self.load_card_timer = asyncio.create_task(timer_callback())
