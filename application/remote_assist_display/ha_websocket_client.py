import asyncio
import json
from typing import Any, Callable, Dict, Optional, Tuple
from websockets import connect
from flask import current_app


class HAWebSocketClient:
    """Low-level Home Assistant WebSocket client."""

    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.websocket = None
        self.id_counter = 0
        self._subscriptions: Dict[int, Tuple[dict, Callable]] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def __aenter__(self):
        await self.connect()
        self._loop = asyncio.get_running_loop()
        self._loop.create_task(self.start_listening())  # Start the listener
        return self

    async def __aexit__(self, *exc_details):
        await self.disconnect()

    async def connect(self) -> bool:
        """Connect and authenticate with Home Assistant."""
        self.websocket = await connect(self.url)

        msg = await self.websocket.recv()
        auth_msg = json.loads(msg)

        if auth_msg["type"] != "auth_required":
            raise ConnectionError("Unexpected initial message type")

        await self.websocket.send(json.dumps({
            "type": "auth",
            "access_token": self.token
        }))

        response = json.loads(await self.websocket.recv())
        if response["type"] != "auth_ok":
            raise ConnectionError("Authentication failed")

        return True

    async def disconnect(self) -> None:
        """Disconnect from Home Assistant."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def send_command(self, command: str, **kwargs) -> Any:
        """Send a command and wait for its response."""
        self.id_counter += 1
        cmd_id = self.id_counter

        message = {
            "id": cmd_id,
            "type": command,
            **kwargs
        }

        await self.websocket.send(json.dumps(message))

        while True:
            response = json.loads(await self.websocket.recv())
            if response.get("id") == cmd_id:
                if "error" in response:
                    raise ConnectionError(f"Command error: {response['error']}")
                return response.get("result")

    async def subscribe(self, callback: Callable[[dict], None], command: str, **kwargs) -> Callable:
        """Subscribe to a command with ongoing updates.

        Args:
            callback: Function to call when messages are received
            command: Command to subscribe to
            **kwargs: Additional arguments for the command

        Returns:
            Callable that can be used to unsubscribe
        """
        self.id_counter += 1
        message_id = self.id_counter

        message = {
            "id": message_id,
            "type": command,
            **kwargs
        }

        # Store subscription details for message handling
        self._subscriptions[message_id] = (message, callback)

        # Send initial subscription command
        await self.websocket.send(json.dumps(message))

        # Wait for and handle the initial response
        response = json.loads(await self.websocket.recv())
        if "error" in response:
            self._subscriptions.pop(message_id)  # Clean up failed subscription
            current_app.logger.error(f"Subscription failed: {response['error']}")
            raise ConnectionError(f"Subscription error: {response['error']}")

        def remove_listener():
            if message_id in self._subscriptions:
                self._subscriptions.pop(message_id)

        return remove_listener

    async def start_listening(self):
        """Listen for messages and handle subscriptions."""
        self._loop = asyncio.get_running_loop()
        current_app.logger.debug("Starting WebSocket listener")

        while True:
            try:
                raw_message = await self.websocket.recv()
                current_app.logger.debug(f"Received WebSocket message: {raw_message}")

                message = json.loads(raw_message)

                # Handle subscription messages
                if message.get("type") == "event":
                    current_app.logger.debug("Processing event message")
                    msg_id = message.get("id")
                    if msg_id in self._subscriptions:
                        current_app.logger.debug(f"Found subscription for id {msg_id}")
                        _, callback = self._subscriptions[msg_id]
                        if asyncio.iscoroutinefunction(callback):
                            self._loop.create_task(callback(message))
                        else:
                            self._loop.call_soon(callback, message)
                    else:
                        current_app.logger.debug(f"No subscription found for id {msg_id}")
                else:
                    current_app.logger.debug(f"Non-event message type: {message.get('type')}")

            except Exception as e:
                current_app.logger.error(f"WebSocket listener error: {e}")
                current_app.logger.debug(f"Exception details:", exc_info=True)
                await asyncio.sleep(1)