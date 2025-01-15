import asyncio
import webview
from flask import current_app
import threading


class DisplayState:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.websocket_manager = None
        self.load_card_timer = None

    def set_websocket_manager(self, manager):
        self.websocket_manager = manager

    async def update_current_url(self, url):
        """Send the current URL to the server."""
        if self.websocket_manager and self.websocket_manager.client:
            data = {"display": {"current_url": url}}
            await self.websocket_manager.client.send_command(
                "remote_assist_display/update",
                display_id=current_app.config["UNIQUE_ID"],
                data=data
            )
            self.websocket_manager.record_message_sent()

    def load_url(self, url):
        """Load a URL in the webview and update server."""
        webview.windows[0].load_url(url)
        # Use the event loop from websocket manager to send the update
        if self.websocket_manager and self.websocket_manager.loop:
            asyncio.run_coroutine_threadsafe(
                self.update_current_url(url),
                self.websocket_manager.loop
            )

    def set_local_storage(self):
        key = current_app.config["DEVICE_NAME_KEY"]
        value = current_app.config["UNIQUE_ID"]
        webview.windows[0].evaluate_js(f"""
            localStorage.setItem("{key}", "{value}")
        """)

    def load_card(self, event, expire_time=None):
        card_url = event.get("data", {}).get("url")
        target_device_id = event.get("data", {}).get("target_device")
        device_id = current_app.config["UNIQUE_ID"]
        hass_url = current_app.config["url"]

        if target_device_id != device_id:
            return

        if card_url:
            new_url = f"{hass_url}/{card_url}"
            default_dashboard_url = f"{hass_url}/{current_app.config.get('default_dashboard')}"
            self.load_url(new_url)

            # Cancel the timer if it's already running
            if self.load_card_timer:
                self.load_card_timer.cancel()

            # Start a new timer
            if expire_time:
                self.load_card_timer = threading.Timer(
                    expire_time,
                    self.load_url,
                    args=[default_dashboard_url]
                )
                self.load_card_timer.start()