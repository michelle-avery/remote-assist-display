import asyncio
import json
import webview
from hass_client import HomeAssistantClient

class TokenStorage:
    _access_token = None

    @classmethod
    def set_token(cls, token):
        cls._access_token = token

    @classmethod
    def get_token(cls):
        return cls._access_token

    @classmethod
    def clear_token(cls):
        cls._access_token = None

class WebSocketHelper:
    def __init__(self, url, retry_limit, token_retry_delay=1):
        self.url = url
        self.ws_url = url.replace("http", "ws") + "/api/websocket"
        self.retry_limit = retry_limit
        self.token_retry_delay = token_retry_delay
        self.client = None

    async def fetch_access_token(self):
        """Fetch the  access token from global storage or from the browser's localStorage."""
        token = TokenStorage.get_token()
        if token:
            return token

        for _ in range(self.retry_limit):
            token = webview.windows[0].evaluate_js("""
                        localStorage.getItem("hassTokens")
                    """)
            if token:
                access_token = json.loads(token)["access_token"]
                TokenStorage.set_token(access_token)
                return access_token
            await asyncio.sleep(self.token_retry_delay)
        raise Exception("Unable to fetch token from localStorage")

    async def connect_client(self):
        """Connect to the WebSocket client."""
        if self.client is None:
            access_token = await self.fetch_access_token()
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
