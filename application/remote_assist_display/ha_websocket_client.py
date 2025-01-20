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
        self._command_responses: Dict[int, asyncio.Future] = {}
        self._running = True

    async def __aenter__(self):
        await self.connect()
        self._loop = asyncio.get_running_loop()
        self._loop.create_task(self._message_handler())
        return self

    async def __aexit__(self, *exc_details):
        self._running = False
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

        response_future = self._loop.create_future()
        self._command_responses[cmd_id] = response_future

        await self.websocket.send(json.dumps(message))

        try:
            response = await response_future
            if "error" in response:
                raise ConnectionError(f"Command error: {response['error']}")
            return response.get("result")
        finally:
            self._command_responses.pop(cmd_id, None)

    async def subscribe(self, callback: Callable[[dict], None], command: str, **kwargs) -> Callable:
        self.id_counter += 1
        message_id = self.id_counter

        message = {
            "id": message_id,
            "type": command,
            **kwargs
        }

        # Store subscription details for message handling
        self._subscriptions[message_id] = (message, callback)

        response_future = self._loop.create_future()
        self._command_responses[message_id] = response_future

        await self.websocket.send(json.dumps(message))

        try:
            response = await response_future
            if "error" in response:
                self._subscriptions.pop(message_id)
                raise ConnectionError(f"Subscription error: {response['error']}")
            return lambda: self._subscriptions.pop(message_id, None)
        finally:
            self._command_responses.pop(message_id, None)

    async def _message_handler(self):
        """Central message handling loop."""
        current_app.logger.debug("Starting message handler")

        while self._running and self.websocket:
            try:
                raw_message = await self.websocket.recv()
                current_app.logger.debug(f"Received message: {raw_message}")
                message = json.loads(raw_message)

                msg_id = message.get("id")

                # Handle command responses
                if msg_id in self._command_responses:
                    future = self._command_responses[msg_id]
                    if not future.done():
                        future.set_result(message)

                # Handle subscription messages
                elif message.get("type") == "event":
                    event_id = message.get("id")
                    if event_id in self._subscriptions:
                        _, callback = self._subscriptions[event_id]
                        if asyncio.iscoroutinefunction(callback):
                            self._loop.create_task(callback(message))
                        else:
                            self._loop.call_soon(callback, message)

            except Exception as e:
                current_app.logger.error(f"Message handler error: {e}")
                current_app.logger.debug("Exception details:", exc_info=True)
                if not self._running:
                    break
                await asyncio.sleep(1)