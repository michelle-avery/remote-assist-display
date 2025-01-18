import asyncio
import threading
from flask import current_app
import socket

from .listener import event_router
from .auth import fetch_access_token
from .state import DisplayState
from .websocket_client import HomeAssistantWebSocketClient

class WebSocketManager:
    _instance = None

    @classmethod
    def get_instance(cls, app=None):
        if cls._instance is None and app is not None:
            cls._instance = cls(app)
        return cls._instance

    def __init__(self, app):
        self.app = app
        self.thread = None
        self.loop = None
        self._running = False
        self.client = None
        self._initialized = False
        # Create a new app context that we'll push in the background thread
        self._app_context = app.app_context()
        self.last_message_time = 0
        self.ping_interval = 10 # seconds
        self.display_state = DisplayState.get_instance()
        self.display_state.set_websocket_manager(self)


    async def initialize(self, url):
        """Initialize the websocket manager with credentials."""
        if self._initialized:
            await self.stop()

        self.url = url
        self.ws_url = url.replace("http", "ws") + "/api/websocket"
        self.token = await fetch_access_token(url=self.url)
        self._initialized = True
        await self.start()

    async def start(self):
        if not self._running and self._initialized:
            self._running = True
            self.thread = threading.Thread(target=self._run_websocket_loop)
            self.thread.daemon = True
            self.thread.start()

    async def stop(self):
        self._running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join()
        self._initialized = False

    def _run_websocket_loop(self):
        # Push the app context before starting the loop
        self._app_context.push()

        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            async def run_client():
                while self._running:
                    try:
                        async with HomeAssistantWebSocketClient(
                                self.ws_url,
                                self.token,
                                None
                        ) as client:
                            self.client = client
                            # Make sure this device is registered:
                            registration = await client.send_command(
                                "remote_assist_display/register",
                                hostname=socket.gethostname(),
                                display_id=self.app.config["UNIQUE_ID"]
                            )
                            # Get config using the client directly
                            response = await client.send_command(
                                "remote_assist_display/settings",
                                display_id=self.app.config["UNIQUE_ID"]
                            )
                            # Use the app context to update config
                            self.app.config["default_dashboard"] = response["default_dashboard"]
                            # Load the dashboard
                            dashboard_url = f'{self.app.config["url"]}/{self.app.config["default_dashboard"]}'
                            self.display_state.load_url(dashboard_url)
                            data = {"display": {"current_url": dashboard_url}}
                            await client.send_command("remote_assist_display/update", display_id=self.app.config["UNIQUE_ID"], data=data)
                            # Subscribe to future updates
                            await client.subscribe(
                                event_router,
                                'remote_assist_display/connect',
                                display_id=self.app.config["UNIQUE_ID"]
                            )

                            while self._running:
                                await asyncio.sleep(1)
                    except Exception as e:
                        current_app.logger.error(f"WebSocket error: {e}")
                        await asyncio.sleep(5)

            self.loop.run_until_complete(run_client())
        finally:
            # Make sure we pop the context when we're done
            self._app_context.pop()

class WebSocketHelper:
    def __init__(self, url, retry_limit, token_retry_delay=1):
        self.url = url
        self.ws_url = url.replace("http", "ws") + "/api/websocket"
        self.retry_limit = retry_limit
        self.token_retry_delay = token_retry_delay
        self.client = None
        self.listener_task = None

    async def connect_client(self):
        """Connect to the WebSocket client."""
        if self.client is None:
            access_token = await fetch_access_token(self.retry_limit, self.token_retry_delay, url=self.url)
            self.client = HomeAssistantClient(self.ws_url, access_token)
        await self.client.connect()
        self.listener_task = asyncio.create_task(self.client.start_listening())

    async def send_command(self, command, **kwargs):
        """Send a command to the WebSocket client and return the response."""
        if self.client is None:
            await self.connect_client()
        return await self.client.send_command(command, **kwargs)

    async def subscribe_events(self, callback, event_type):
        """Subscribe to WebSocket events."""
        if self.client is None:
            await self.connect_client()
        await self.client.subscribe_events(callback, event_type)

    async def subscribe(self, callback, command, **kwargs):
        """Subscribe to WebSocket commands."""
        if self.client is None:
            await self.connect_client()
        await self.client.subscribe(callback, command, **kwargs)

    async def close(self):
        """Close the WebSocket connection."""
        if self.client:
            await self.client.disconnect()
        self.client = None
        self.listener_task = None