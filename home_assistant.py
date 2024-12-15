import  websockets
import json
import asyncio

class HomeAssistantClient:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.event_callback = None

    async def connect(self):
        async with websockets.connect(self.url) as websocket:
            await websocket.send(json.dumps({"type": "auth", "access_token": self.token}))
            response = await websocket.recv()

            await websocket.send(json.dumps({"id": 1, "type": "subscribe_events", "event_type": "custom_conversation_conversation_ended"}))
            response = await websocket.recv()

            while True:
                event = await websocket.recv()
                if self.event_callback:
                    self.event_callback(event)
    def set_event_callback(self, callback):
        self.event_callback = callback

    def start(self):
        asyncio.run(self.connect())
