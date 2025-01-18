import asyncio
import threading
import socket
from typing import Optional
from flask import Flask
from dataclasses import dataclass

from .listener import event_router
from .auth import fetch_access_token
from .state import DisplayState
from .ha_websocket_client import HAWebSocketClient


@dataclass
class WebSocketConfig:
    """Configuration settings for WebSocket connections."""
    ping_interval: int = 10  # seconds


class WebSocketManager:
    """Manages WebSocket connections with Home Assistant in a separate thread."""

    _instance: Optional['WebSocketManager'] = None

    @classmethod
    def get_instance(cls, app: Optional[Flask] = None) -> 'WebSocketManager':
        """Get or create the singleton instance of WebSocketManager."""
        if cls._instance is None and app is not None:
            cls._instance = cls(app)
        return cls._instance

    def __init__(self, app: Flask):
        """Initialize the WebSocket manager.

        Args:
            app: Flask application instance
        """
        self.app = app
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self.client: Optional[HAWebSocketClient] = None
        self._initialized = False
        self._app_context = app.app_context()
        self.config = WebSocketConfig()
        self.display_state = DisplayState.get_instance()
        self.display_state.set_websocket_manager(self)

    async def initialize(self, url: str) -> None:
        """Initialize the manager with the Home Assistant URL.

        Args:
            url: Home Assistant instance URL
        """
        if self._initialized:
            await self.stop()

        self.url = url
        self.ws_url = url.replace("http", "ws") + "/api/websocket"
        self.app.logger.info(f"Initializing WebSocket connection to {self.ws_url}")

        self.token = await fetch_access_token(url=self.url, app=self.app)
        self._initialized = True
        await self.start()

    async def start(self) -> None:
        """Start the WebSocket connection in a background thread."""
        if not self._running and self._initialized:
            self._running = True
            self.thread = threading.Thread(target=self._run_websocket_loop)
            self.thread.daemon = True
            self.thread.start()

    async def stop(self) -> None:
        """Stop the WebSocket connection and clean up."""
        self._running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join()
        self._initialized = False

    def _run_websocket_loop(self) -> None:
        """Run the WebSocket event loop in a separate thread."""
        self._app_context.push()

        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._manage_client())
        finally:
            self._app_context.pop()

    async def _manage_client(self) -> None:
        """Manage the WebSocket client connection and reconnection."""
        while self._running:
            try:
                async with HAWebSocketClient(self.ws_url, self.token) as client:
                    self.client = client
                    await self._initialize_client()

                    while self._running:
                        await asyncio.sleep(1)
            except Exception as e:
                self.app.logger.error(f"WebSocket error: {e}")
                await asyncio.sleep(5)

    async def _initialize_client(self) -> None:
        """Initialize the client with required registrations and subscriptions."""
        # Register device
        registration = await self.client.send_command(
            "remote_assist_display/register",
            hostname=socket.gethostname(),
            display_id=self.app.config["UNIQUE_ID"]
        )
        self.app.logger.info(f"Registration response: {registration}")

        # Get settings
        response = await self.client.send_command(
            "remote_assist_display/settings",
            display_id=self.app.config["UNIQUE_ID"]
        )
        self.app.logger.info(f"Settings response: {response}")
        self.app.config["default_dashboard"] = response["default_dashboard"]

        # Update display state
        dashboard_url = f'{self.app.config["url"]}/{self.app.config["default_dashboard"]}'
        self.display_state.load_url(dashboard_url)

        # Update HA with current state
        await self.client.send_command(
            "remote_assist_display/update",
            display_id=self.app.config["UNIQUE_ID"],
            data={"display": {"current_url": dashboard_url}}
        )

        # Subscribe to events
        await self.client.subscribe(
            event_router,
            'remote_assist_display/connect',
            display_id=self.app.config["UNIQUE_ID"]
        )