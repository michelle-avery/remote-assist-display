import asyncio
import json
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

            await self.websocket_manager.client.send_command(message)

    async def load_url(self, url, local_storage=True):
        """Load a URL in the webview and update server."""
        # Update the webview immediately
        webview.windows[0].load_url(url)
        if local_storage:
            self.set_local_storage()
        # Queue the server update as a separate task
        if self.websocket_manager and self.websocket_manager.client:
            asyncio.create_task(self.update_current_url(url))

    async def load_hass_path(self, path, local_storage=True):
        """Load a Home Assistant path."""
        push_state = f"""
            async function browser_navigate(path) {{
                if (!path) return;
                history.pushState(null, "", path);
                window.dispatchEvent(new CustomEvent("location-changed"));
            }}
            browser_navigate("/{path}");
            """
        webview.windows[0].evaluate_js(push_state)
        if local_storage:
            self.set_local_storage()
        if self.websocket_manager and self.websocket_manager.client:
            asyncio.create_task(self.update_current_url(f"{current_app.config['url']}/{path}"))

    def set_local_storage(self):
        key = current_app.config["DEVICE_NAME_KEY"]
        value = current_app.config["UNIQUE_ID"]
        rad_key = current_app.config["RAD_DISPLAY_NAME_KEY"]

        settings = {
            "hideHeader": current_app.config.get("hide_header", False),
            "hideSidebar": current_app.config.get("hide_sidebar", False),
        }

        webview.windows[0].evaluate_js(f"""
            localStorage.setItem("{key}", "{value}")
            localStorage.setItem("{rad_key}", "{value}")
            localstorage.setItem("remote_assist_display_settings", '{json.dumps(settings)})
        """)

    async def load_card(self, event, expire_time=None):
        card_path = event.get("path")
        if not card_path:
            return
        if card_path.startswith("/"):
            card_path = card_path[1:]
        hass_url = current_app.config["url"]
        current_url = webview.windows[0].get_current_url()
        # If we're already on home assistant, navigate via js
        if current_url and  current_url.startswith(hass_url):
            current_app.logger.debug(f"Current URL: {current_url}")
            current_app.logger.debug(f"Loading card {card_path} via js")
            await self.load_hass_path(card_path)
        else:
            current_app.logger.debug(f"Current URL: {current_url}")
            current_app.logger.debug(f"Loading card {card_path} via url")
            await self.load_url(f"{hass_url}/{card_path}")

        default_dashboard_url = (
            f"{hass_url}/{current_app.config.get('default_dashboard')}"
        )

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
