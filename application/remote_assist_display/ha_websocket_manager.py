import asyncio
import socket
import threading
from operator import ge
from typing import Optional

from flask import g

from .auth import fetch_access_token
from .home_assistant_ws_client import HomeAssistantWebSocketClient
from .listener import EventRouter


# Import DisplayState lazily to avoid circular imports
def get_display_state():
    from .state import DisplayState

    return DisplayState.get_instance()


def run_event_loop_in_thread(loop: asyncio.AbstractEventLoop):
    """Run the event loop in a separate thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


class WebSocketManager:
    _instance = None

    def __init__(self, app):
        if WebSocketManager._instance is not None:
            raise RuntimeError("WebSocketManager is a singleton. Use get_instance().")

        self.app = app
        self.token: Optional[str] = None
        self.hass_url: Optional[str] = None
        self.ws_url: Optional[str] = None
        self.client: Optional[HomeAssistantWebSocketClient] = None
        self.display_state = get_display_state()
        self.display_state.set_websocket_manager(self)
        self.logger = app.logger
        self._listener_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._closing = False

        # Create a new event loop for WebSocket operations
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=run_event_loop_in_thread, args=(self._loop,), daemon=True
        )
        self._thread.start()

    @classmethod
    def get_instance(cls, app):
        if cls._instance is None:
            cls._instance = cls(app)
        return cls._instance

    def _run_coroutine(self, coro):
        """Run a coroutine in the WebSocket event loop."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def initialize(self, url):

        async def _initialize():
            try:
                self.hass_url = url
                self.ws_url = url.replace("http", "ws") + "/api/websocket"
                self.token = await fetch_access_token(url=url, app=self.app)

                if not isinstance(self.ws_url, str) or not isinstance(self.token, str):
                    raise ValueError("Invalid URL or token")

                # Create and connect the client with validated credentials
                self.client = HomeAssistantWebSocketClient(self.ws_url, self.token)
                await self.client.connect()
                await self.register()

                # Store reference to the listener task
                self._listener_task = self.client._listener_task

                # Create a background task to monitor the connection
                self._monitor_task = asyncio.create_task(self._monitor_connection())

                self.logger.info("WebSocket connection initialized with monitoring")
            except Exception as e:
                self.logger.error(
                    f"Failed to initialize WebSocket connection: {str(e)}",
                    exc_info=True,
                )
                raise

        return self._run_coroutine(_initialize())

    async def _monitor_connection(self):
        """Monitor the WebSocket connection and reconnect if needed."""
        while True:
            try:
                if self._listener_task:
                    # Wait for the listener task to complete
                    await self._listener_task
                    # If we get here, the listener has stopped unexpectedly
                if not self._closing and self.ws_url and self.token:
                    self.logger.warning(
                        "WebSocket connection lost, attempting to reconnect"
                    )
                    # Recreate the client and reconnect with validated credentials
                    self.client = HomeAssistantWebSocketClient(
                        str(self.ws_url), str(self.token)
                    )
                    await self.client.connect()
                    await self.register()
                    self._listener_task = self.client._listener_task
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Error in connection monitor: {str(e)}", exc_info=True
                )
                if "Authentication failed" in str(e):
                    # Force a re-authentication
                    self.logger.warning("Forcing re-authentication")
                    self.token = await fetch_access_token(url=self.hass_url, app=self.app, force=True)

                await asyncio.sleep(5)  # Wait before retrying

    async def register(self):
        if not self.client:
            self.logger.error("Cannot register: WebSocket client is not initialized")
            raise RuntimeError("WebSocket client is not initialized")

        try:
            # Register the display
            hostname = self.app.config["HOSTNAME"]
            self.logger.debug(f"Hostname is: {hostname}")
            display_id = self.app.config["UNIQUE_ID"]
            self.logger.debug(f"Display ID is: {display_id}")
            register_message = {
                "type": "remote_assist_display/register",
                "hostname": hostname,
                "display_id": display_id,
            }
            register_response = await self.client.send_command(register_message)
            self.logger.debug(f"Registered display: {register_response}")

            # Fetch initial settings
            settings_message = {
                "type": "remote_assist_display/settings",
                "display_id": display_id,
            }
            self.logger.debug(f"Fetching settings for display: {display_id}")
            settings_response = await self.client.send_command(settings_message)
            self.logger.debug(f"Settings response: {settings_response}")
            if not settings_response or "settings" not in settings_response:
                raise ValueError("Invalid settings response from server")

            default_dashboard = settings_response["settings"]["default_dashboard"]
            self.logger.debug(f"Default dashboard: {default_dashboard}")
            self.app.config["default_dashboard"] = default_dashboard

            # Update display state
            self.logger.debug("Updating the display state with default dashboard")
            dashboard_url = f"{self.app.config['url']}/{default_dashboard}"
            await self.display_state.load_url(dashboard_url)

            # Create event router and subscribe to updates
            self.logger.debug("Creating event router and subscribing to updates")
            event_router = EventRouter(self.app)
            await self.client.subscribe(
                event_router, "remote_assist_display/connect", display_id=display_id
            )
        except Exception as e:
            self.logger.error(f"Registration failed: {str(e)}", exc_info=True)
            raise

    def shutdown(self):
        """Shutdown the WebSocket connection and monitoring."""

        async def _shutdown():
            self._closing = True
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None
            if self.client:
                try:
                    await self.client.disconnect()
                finally:
                    self._listener_task = None
                    self.client = None

            # Stop the event loop
            self._loop.call_soon_threadsafe(self._loop.stop)

        return self._run_coroutine(_shutdown())
