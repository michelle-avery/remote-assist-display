from hass_client import HomeAssistantClient

from application.remote_display.auth import fetch_access_token


class WebSocketHelper:
    def __init__(self, url, retry_limit, token_retry_delay=1):
        self.url = url
        self.ws_url = url.replace("http", "ws") + "/api/websocket"
        self.retry_limit = retry_limit
        self.token_retry_delay = token_retry_delay
        self.client = None

    async def connect_client(self):
        """Connect to the WebSocket client."""
        if self.client is None:
            access_token = await fetch_access_token(self.retry_limit, self.token_retry_delay)
            self.client = HomeAssistantClient(self.ws_url, access_token)
        await self.client.connect()

    async def send_command(self, command):
        """Send a command to the WebSocket client and return the response."""
        if self.client is None:
            await self.connect_client()
        return await self.client.send_command(command)

    async def subscribe_events(self, callback, event_type):
        """Subscribe to WebSocket events."""
        if self.client is None:
            await self.connect_client()
        await self.client.subscribe_events(callback, event_type)
