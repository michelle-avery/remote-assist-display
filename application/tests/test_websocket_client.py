import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
import websockets
from websockets import frames

from remote_assist_display.home_assistant_ws_client import HomeAssistantWebSocketClient


@pytest_asyncio.fixture
async def mock_websocket():
    """Mock websockets connection."""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


@pytest_asyncio.fixture(autouse=True)
async def cleanup():
    """Cleanup any pending tasks after each test."""
    yield
    # Cancel all tasks at the end of each test
    for task in asyncio.all_tasks():
        if not task.done() and task != asyncio.current_task():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass


@pytest.fixture
def mock_app():
    """Mock Flask app with logger."""
    mock = Mock()
    mock.logger = Mock()
    return mock


@pytest_asyncio.fixture
async def client(mock_app):
    """Create a test client with mocked app."""
    with patch("remote_assist_display.home_assistant_ws_client.current_app", mock_app):
        client = HomeAssistantWebSocketClient("ws://test:8123", "test_token")
        return client


@pytest.mark.asyncio
async def test_connect_and_authenticate(client, mock_websocket):
    """Test successful connection and authentication."""
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        mock_websocket.recv.side_effect = [
            json.dumps({"type": "auth_required"}),
            json.dumps({"type": "auth_ok"}),
        ]

        await client.connect()

        assert client.connection == mock_websocket

        auth_message = json.loads(mock_websocket.send.call_args_list[0][0][0])
        assert auth_message["type"] == "auth"
        assert auth_message["access_token"] == "test_token"


@pytest.mark.asyncio
async def test_connect_auth_failure(client, mock_websocket):
    """Test authentication failure."""
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        mock_websocket.recv.side_effect = [
            json.dumps({"type": "auth_required"}),
            json.dumps({"type": "auth_invalid", "error": {"message": "Invalid token"}}),
        ]

        with pytest.raises(ValueError, match="Authentication failed: Invalid token"):
            await client.connect()


@pytest.mark.asyncio
async def test_send_command(client, mock_websocket):
    """Test sending a command and receiving a result."""
    client.connection = mock_websocket
    client._closing = False

    result_future = asyncio.Future()
    client._result_futures["1"] = result_future

    client._listener_task = asyncio.create_task(client._listen())

    mock_websocket.recv.side_effect = [
        json.dumps(
            {"id": 1, "type": "result", "success": True, "result": {"data": "test"}}
        ),
        websockets.exceptions.ConnectionClosed(
            frames.Close(1000, "Normal closure"), None
        ),
    ]
    asyncio.create_task(client.send_command({"type": "test_command"}))
    result = await result_future

    # Verify command was sent with correct format
    sent_message = json.loads(mock_websocket.send.call_args[0][0])
    assert sent_message["type"] == "test_command"
    assert "id" in sent_message

    # Verify result was processed correctly
    assert result == {"data": "test"}


@pytest.mark.asyncio
async def test_send_command_failure(client, mock_websocket):
    """Test sending a command that results in an error."""
    client.connection = mock_websocket
    client._closing = False

    client._message_id = 0

    client._listener_task = asyncio.create_task(client._listen())

    mock_websocket.recv.side_effect = [
        json.dumps(
            {
                "id": 1,
                "type": "result",
                "success": False,
                "error": {"message": "Command failed"},
            }
        ),
    ]

    # Send command and expect it to fail
    with pytest.raises(Exception, match="Command failed"):
        await client.send_command({"type": "test_command"})

    # Clean up listener task
    if client._listener_task and not client._listener_task.done():
        client._listener_task.cancel()
        try:
            await client._listener_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_subscription(client, mock_websocket):
    """Test subscribing to events."""
    client.connection = mock_websocket
    client._closing = False

    client._message_id = 0

    client._listener_task = asyncio.create_task(client._listen())
    mock_websocket.recv.side_effect = [
        json.dumps({"id": 1, "type": "result", "success": True, "result": None}),
    ]
    callback = AsyncMock()
    subscription_id = await client.subscribe(callback, "test_event", param="value")

    # Verify subscription message was sent
    sent_message = json.loads(mock_websocket.send.call_args[0][0])
    assert sent_message["type"] == "test_event"
    assert sent_message["param"] == "value"

    # Verify callback was stored
    assert str(subscription_id) in client.subscriptions
    assert client.subscriptions[str(subscription_id)] == callback


@pytest.mark.asyncio
async def test_message_listener_handles_events(client, mock_websocket):
    """Test that the message listener properly handles incoming events."""
    client.connection = mock_websocket
    callback = AsyncMock()
    client.subscriptions["1"] = callback
    event_message = {"id": 1, "type": "event", "event": {"data": "test_data"}}
    mock_websocket.recv.side_effect = [
        json.dumps(event_message),
        websockets.exceptions.ConnectionClosed(
            frames.Close(1000, "Normal closure"), None
        ),
    ]
    client._closing = False
    try:
        await client._listen()
    except websockets.exceptions.ConnectionClosed:
        pass

    callback.assert_called_once_with(event_message)


@pytest.mark.asyncio
async def test_disconnect(client, mock_websocket):
    """Test clean disconnection."""
    client.connection = mock_websocket
    client._listener_task = asyncio.create_task(asyncio.sleep(0))

    await client.disconnect()

    assert client._closing is True
    assert client.connection is None
    mock_websocket.close.assert_called_once()
