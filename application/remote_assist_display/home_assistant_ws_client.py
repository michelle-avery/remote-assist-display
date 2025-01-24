import asyncio
import json
import ssl
from typing import Any, Dict, Optional

import certifi
import websockets
from flask import current_app


class HomeAssistantWebSocketClient:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self._message_id = 1
        self.connection = None  # websockets will handle the connection type
        self.logger = current_app.logger
        self.subscriptions: Dict[str, Any] = {}
        self._msg_id_lock = asyncio.Lock()
        self._result_futures: Dict[str, asyncio.Future] = {}
        self._listener_task: Optional[asyncio.Task] = None
        self._closing = False

    async def _get_message_id(self):
        """Generate and increment a unique message ID."""
        async with self._msg_id_lock:
            self._message_id += 1
            return self._message_id

    async def connect(self):
        """Establish a WebSocket connection."""
        try:
            self.logger.info(
                f"Attempting to connect to Home Assistant WebSocket API at {self.url}"
            )
            ssl_context = ssl.create_default_context(cafile=certifi.where()) if self.url.startswith('wss://') else None
            self.connection = await websockets.connect(self.url, ssl=ssl_context)
            self.logger.info("WebSocket connection established successfully")
            await self._authenticate()
            self.logger.info("Starting message listener task")
            self._closing = False
            self._listener_task = asyncio.create_task(self._listen())
        except websockets.exceptions.InvalidURI as e:
            self.logger.error(f"Invalid WebSocket URI: {self.url} - {str(e)}")
            raise
        except ssl.SSLCertVerificationError as e:
            self.logger.error(f"SSL certificate verification failed: {str(e)}")
            raise
        except websockets.exceptions.InvalidHandshake as e:
            self.logger.error(f"WebSocket handshake failed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to connect: {str(e)}", exc_info=True)
            raise

    async def _authenticate(self):
        """Authenticate using the provided token."""
        self.logger.info("Starting authentication process")
        connect_response = await self.receive_message()
        self.logger.debug(f"Initial connection response: {connect_response}")

        if connect_response.get("type") == "auth_required":
            self.logger.info("Authentication required, sending auth token")
            auth_message = {"type": "auth", "access_token": self.token}
            await self.send_json(auth_message)
            response = await self.receive_message()
            self.logger.debug(f"Authentication response: {response}")

            if response.get("type") == "auth_ok":
                self.logger.info("Authentication successful")
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                self.logger.error(f"Authentication failed: {error_msg}")
                raise ValueError(f"Authentication failed: {error_msg}")
        else:
            self.logger.error(f"Unexpected initial response: {connect_response}")
            raise ValueError("Unexpected response during authentication attempt")

    async def send_json(self, message):
        """Send a message over the websocket connection."""
        if self.connection is None:
            self.logger.error("Attempted to send message with no connection")
            raise RuntimeError("Connection is not established")

        try:
            message_str = json.dumps(message)
            await self.connection.send(message_str)
            self.logger.debug(f"Sent message: {message}")
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.error(f"Failed to send message - connection closed: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}", exc_info=True)
            raise

    async def send_command(self, message: Dict[str, Any], **kwargs):
        """Send a message over the WebSocket connection with an added message ID."""
        if isinstance(message, str):
            message = {"type": message}

        # Get or generate message ID (as integer)
        if "message_id" in kwargs:
            msg_id = kwargs.pop("message_id")
        elif "id" not in message:
            msg_id = await self._get_message_id()
        else:
            msg_id = message["id"]

        # Use integer ID in message
        message["id"] = msg_id
        # Use string ID for dictionary key
        str_id = str(msg_id)

        future = asyncio.Future()
        self._result_futures[str_id] = future

        try:
            await self.send_json(message)
            result = await future
            return result
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.error(
                f"Connection lost during command: {str(e)}", exc_info=True
            )
            if not self._closing:
                self.logger.warning("Attempting to reconnect")
                try:
                    await self.connect()
                except Exception as reconnect_error:
                    self.logger.error(
                        f"Failed to reconnect: {str(reconnect_error)}", exc_info=True
                    )
            raise
        except Exception as e:
            self.logger.error(f"Error in send_command: {str(e)}", exc_info=True)
            raise
        finally:
            self._result_futures.pop(str_id, None)

    async def receive_message(self):
        """Receive a message from the WebSocket connection."""
        if self.connection is None:
            self.logger.error("Attempted to receive message with no connection")
            raise RuntimeError("Connection is not established")

        try:
            response_str = await self.connection.recv()
            response = json.loads(response_str)
            self.logger.debug(f"Received message: {response}")
            return response
        except websockets.exceptions.ConnectionClosed as e:
            if not self._closing:
                self.logger.error("Connection closed by server.")
            raise e

    async def _listen(self):
        """Listen for incoming messages and route them appropriately."""
        self.logger.info("Message listener started")
        try:
            while not self._closing:
                try:
                    message = await self.receive_message()
                    message_type = message.get("type")
                    msg_id = message.get("id")

                    self.logger.debug(
                        f"Processing message type '{message_type}' with ID {msg_id}"
                    )

                    if message_type == "result":
                        # Handle command results
                        str_id = str(
                            msg_id
                        )  # Convert ID to string for dictionary lookup
                        future = self._result_futures.get(str_id)
                        if future:
                            if message.get("success"):
                                result = message.get("result")
                                self.logger.debug(
                                    f"Command succeeded - ID {msg_id}: {result}"
                                )
                                future.set_result(result)
                            else:
                                error = message.get("error", {})
                                error_msg = error.get("message", "Command failed")
                                self.logger.error(
                                    f"Command failed - ID {msg_id}: {error_msg}"
                                )
                                future.set_exception(Exception(error_msg))
                        else:
                            self.logger.warning(
                                f"Received result for unknown message ID: {msg_id} (str_id: {str_id})"
                            )

                    elif message_type == "event":
                        # Handle subscription events
                        subscription_id = message.get("id")
                        str_id = str(
                            subscription_id
                        )  # Convert to string for dictionary lookup
                        if str_id in self.subscriptions:
                            callback = self.subscriptions[str_id]
                            self.logger.debug(
                                f"Processing event for subscription {subscription_id}"
                            )
                            try:
                                # Always await the callback since EventRouter.__call__ is a coroutine
                                await callback(message)
                                self.logger.debug(
                                    f"Successfully processed event for subscription {subscription_id}"
                                )
                            except Exception as e:
                                self.logger.error(
                                    f"Error in subscription callback for ID {subscription_id}: {str(e)}",
                                    exc_info=True,
                                )
                        else:
                            self.logger.warning(
                                f"Received event for unknown subscription: {subscription_id} (str_id: {str_id})"
                            )

                except websockets.exceptions.ConnectionClosed as e:
                    if not self._closing:
                        self.logger.warning(
                            f"WebSocket connection closed unexpectedly: {str(e)}"
                        )
                        if e.code == 1000:  # Normal closure
                            self.logger.info("Connection closed normally")
                            break
                        else:
                            self.logger.error(
                                f"Abnormal connection closure: code={e.code}, reason={e.reason}"
                            )
                            # Try to reconnect
                            try:
                                self.logger.info("Attempting to reconnect...")
                                await self.connect()
                                # Continue listening after reconnection
                            except Exception as reconnect_error:
                                self.logger.error(
                                    f"Failed to reconnect: {str(reconnect_error)}",
                                    exc_info=True,
                                )
                                break
                    else:
                        break

        except asyncio.CancelledError:
            self.logger.info("Message listener cancelled")
            raise
        except Exception as e:
            if not self._closing:
                self.logger.error(f"Error in message listener: {str(e)}", exc_info=True)
        finally:
            if not self._closing:
                self.logger.info("Message listener stopped unexpectedly")
            else:
                self.logger.info("Message listener stopped")

    async def subscribe(self, callback, command: str, **kwargs):
        """Subscribe to events and return the subscription id."""
        message_id = await self._get_message_id()
        message = {"type": command, **kwargs}

        self.logger.info(
            f"Creating subscription for command '{command}' with ID {message_id}"
        )

        str_id = str(message_id)
        try:
            # Store callback before sending command to handle immediate events
            self.subscriptions[str_id] = callback
            self.logger.debug(f"Registered callback for subscription {message_id}")

            # Send subscription command
            await self.send_command(message, message_id=message_id)
            self.logger.info(
                f"Successfully subscribed to '{command}' with ID {message_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to create subscription: {str(e)}", exc_info=True)
            # Clean up subscription if command fails
            self.subscriptions.pop(str_id, None)
            raise

        return message_id

    async def unsubscribe(self, subscription_id):
        """Unsubscribe from a subscription."""
        str_id = str(subscription_id)
        if str_id in self.subscriptions:
            await self.send_command(
                {"type": "unsubscribe_events", "subscription": subscription_id}
            )
            self.subscriptions.pop(str_id, None)

    async def disconnect(self):
        """Close the websocket connection."""
        if self.connection:
            self.logger.info("Closing WebSocket connection")
            self._closing = True
            if self._listener_task:
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass
                self._listener_task = None
            await self.connection.close()
            self.connection = None
            self.logger.info("WebSocket connection closed")
