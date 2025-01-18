import asyncio
import json
import websockets
from flask import current_app


class HomeAssistantWebSocketClient:
    def __init__(self, url, token, session=None):
        self.url = url
        self.token = token
        self.websocket = None
        self.id_counter = 0
        self.event_listeners = {}
        self.command_listeners = {}
        self._message_handlers = {}
        self._command_results = {}

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self):
        self.websocket = await websockets.connect(self.url)
        # Handle auth phase
        auth_ok = False
        msg = await self.websocket.recv()
        if json.loads(msg)["type"] == "auth_required":
            await self.websocket.send(json.dumps({
                "type": "auth",
                "access_token": self.token
            }))
            msg = await self.websocket.recv()
            auth_ok = json.loads(msg)["type"] == "auth_ok"
        if not auth_ok:
            raise Exception("Authentication failed")
        return auth_ok

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def send_command(self, command, **kwargs):
        self.id_counter += 1
        cmd_id = self.id_counter

        message = {
            "id": cmd_id,
            "type": command
        }
        if kwargs:
            message.update(kwargs)

        await self.websocket.send(json.dumps(message))

        # Wait for response
        while True:
            response = json.loads(await self.websocket.recv())
            if response.get("id") == cmd_id:
                if "error" in response:
                    raise Exception(f"Command error: {response['error']}")
                return response.get("result")

    async def subscribe(self, callback, command, **kwargs):
        self.id_counter += 1
        sub_id = self.id_counter

        message = {
            "id": sub_id,
            "type": "subscribe_events",
            "event_type": command
        }
        if kwargs:
            message["event_filter"] = kwargs

        self.command_listeners[sub_id] = callback
        await self.websocket.send(json.dumps(message))

        # Wait for subscription confirmation
        while True:
            response = json.loads(await self.websocket.recv())
            if response.get("id") == sub_id:
                if "error" in response:
                    raise Exception(f"Subscription error: {response['error']}")
                return response.get("success", False)

    async def start_listening(self):
        while True:
            try:
                message = json.loads(await self.websocket.recv())
                if "type" in message and message["type"] == "event":
                    event_data = message.get("event", {})
                    if event_data:
                        for callback in self.command_listeners.values():
                            await callback(event_data)
            except Exception as e:
                current_app.logger.error(f"WebSocket listener error: {e}")
                await asyncio.sleep(1)