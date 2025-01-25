import logging
from typing import Optional

from flask import Flask

from .state import DisplayState

logger = logging.getLogger(__name__)


class EventRouter:
    def __init__(self, app: Flask):
        self.app = app
        self.display_state = DisplayState.get_instance()

    async def __call__(self, event: dict, expire_time: Optional[str] = None) -> None:
        """Route events to the appropriate function."""
        logger.info(f"Received event: {event}")

        try:
            event_data = event.get("event", {})
            command = event_data.get("command")

            if command == "remote_assist_display/update_settings":
                settings = event_data.get("settings", {}).get("settings", {})
                if settings:
                    await self._update_settings(settings)
            elif command == "remote_assist_display/navigate_url":
                await self.display_state.load_url(event_data.get("url"))
            elif command == "remote_assist_display/navigate":
                await self.display_state.load_card(event_data)
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)

    async def _update_settings(self, settings: dict) -> None:
        """Update display settings."""
        if default_dashboard := settings.get("default_dashboard"):
            self.app.config["default_dashboard"] = default_dashboard
            dashboard_url = f"{self.app.config['url']}/{default_dashboard}"
            logger.info(f"Updating default dashboard to: {dashboard_url}")
            await self.display_state.load_url(dashboard_url)
