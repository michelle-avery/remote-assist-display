"""Test websockets."""
import logging
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from homeassistant.core import HomeAssistant

from custom_components.remote_assist_display.const import (
    CONNECT_WS_COMMAND,
    REGISTER_WS_COMMAND,
    SETTINGS_WS_COMMAND,
    UPDATE_WS_COMMAND,
)
from custom_components.remote_assist_display.remote_assist_display import (
    get_or_register_display,
)

_LOGGER = logging.getLogger(__name__)


@pytest.fixture
async def ws_client(hass: HomeAssistant, hass_ws_client: WebSocketGenerator):
    """Create a websocket client."""
    return await hass_ws_client(hass)


@pytest.fixture
def mock_datetime():
    """Create a mock datetime."""
    with patch("custom_components.remote_assist_display.ws_api.datetime") as mock:
        mock.now.return_value = datetime(2025, 1, 23, 12, 0, 0)
        mock.timezone = timezone
        yield mock

# Connect Command Tests
async def test_connect_command_registers_new_display(
    hass: HomeAssistant,
    init_integration,
    ws_client,
    mock_datetime,
) -> None:
    """Test connect command successfully registers a new display."""
    await ws_client.send_json({
        "id": 1,
        "type": CONNECT_WS_COMMAND,
        "display_id": "test-display-id"
    })

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"] == "registered"

    display = get_or_register_display(hass, "test-display-id")
    assert len(display.connection) == 1
    assert display.data.get("connected") is True


@pytest.mark.xfail(reason="Multiple connections are not properly handled yet - connections should be replaced rather than added")
async def test_connect_command_replaces_existing_connection(
    hass: HomeAssistant,
    init_integration,
    ws_client,
    mock_datetime,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test connect command replaces existing connection for same display ID."""
    # First connection
    await ws_client.send_json({
        "id": 1,
        "type": CONNECT_WS_COMMAND,
        "display_id": "test-display-id"
    })
    await ws_client.receive_json()

    # Second connection
    client2 = await hass_ws_client(hass)
    await client2.send_json({
        "id": 2,
        "type": CONNECT_WS_COMMAND,
        "display_id": "test-display-id"
    })
    msg = await client2.receive_json()
    assert msg["success"]

    display = get_or_register_display(hass, "test-display-id")
    assert len(display.connection) == 1
    assert display.data.get("connected") is True


# Register Command Tests
async def test_register_command_initial_registration(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test initial display registration with hostname."""
    await ws_client.send_json({
        "id": 1,
        "type": REGISTER_WS_COMMAND,
        "display_id": "test-display-id",
        "hostname": "test-hostname"
    })

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["registered"] is True
    assert msg["result"]["hostname"] == "test-hostname"

    display = get_or_register_display(hass, "test-display-id")
    assert display.settings["registered"] is True
    assert display.settings["hostname"] == "test-hostname"


async def test_register_command_updates_hostname(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test updating hostname of registered display."""
    # Initial registration
    await ws_client.send_json({
        "id": 1,
        "type": REGISTER_WS_COMMAND,
        "display_id": "test-display-id",
        "hostname": "test-hostname"
    })
    await ws_client.receive_json()

    # Update hostname
    await ws_client.send_json({
        "id": 2,
        "type": REGISTER_WS_COMMAND,
        "display_id": "test-display-id",
        "hostname": "new-hostname"
    })

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["hostname"] == "new-hostname"

    display = get_or_register_display(hass, "test-display-id")
    assert display.settings["hostname"] == "new-hostname"
    assert display.settings["registered"] is True


# Settings Command Tests
async def test_settings_command_returns_custom_dashboard(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test settings command returns custom dashboard when set."""
    display = get_or_register_display(hass, "test-display-id")
    display.entities["default_dashboard"] = MagicMock()
    display.entities["default_dashboard"].native_value = "custom-dashboard"

    await ws_client.send_json({
        "id": 1,
        "type": SETTINGS_WS_COMMAND,
        "display_id": "test-display-id"
    })

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["settings"]["default_dashboard"] == "custom-dashboard"

async def test_settings_command_returns_custom_device_storage_key(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test settings command returns custom device storage key when set."""
    display = get_or_register_display(hass, "test-display-id")
    display.entities["device_storage_key"] = MagicMock()
    display.entities["device_storage_key"].native_value = "custom-device-storage-key"

    await ws_client.send_json({
        "id": 1,
        "type": SETTINGS_WS_COMMAND,
        "display_id": "test-display-id"
    })

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["settings"]["device_storage_key"] == "custom-device-storage-key"

async def test_settings_command_returns_none_dashboard(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test settings command returns None when no dashboard is set."""
    display = get_or_register_display(hass, "test-display-id")
    display.entities["default_dashboard"] = MagicMock()
    display.entities["default_dashboard"].native_value = None

    await ws_client.send_json({
        "id": 1,
        "type": SETTINGS_WS_COMMAND,
        "display_id": "test-display-id"
    })

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["settings"]["default_dashboard"] is None

async def test_settings_command_returns_none_device_storage_key(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test settings command returns None when no device storage key is set."""
    display = get_or_register_display(hass, "test-display-id")
    display.entities["device_storage_key"] = MagicMock()
    display.entities["device_storage_key"].native_value = None

    await ws_client.send_json({
        "id": 1,
        "type": SETTINGS_WS_COMMAND,
        "display_id": "test-display-id"
    })

    msg = await ws_client.receive_json()
    assert msg["success"]
    assert msg["result"]["settings"]["device_storage_key"] is None

    
# Update Command Tests
async def test_update_command_sets_current_url(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test update command sets current URL."""
    test_url = "http://localhost:8123/dashboard-viewassist/clock?kiosk"
    await ws_client.send_json({
        "id": 1,
        "type": UPDATE_WS_COMMAND,
        "display_id": "test-display-id",
        "data": {
            "display": {
                "current_url": test_url
            }
        }
    })

    msg = await ws_client.receive_json()
    assert msg["success"]

    display = get_or_register_display(hass, "test-display-id")
    assert display.data["display"]["current_url"] == test_url


async def test_update_command_merges_data(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test update command merges new data with existing data."""
    display = get_or_register_display(hass, "test-display-id")
    display.update(hass, {"existing_key": "existing_value"})

    test_url = "http://localhost:8123/dashboard-viewassist/clock?kiosk"
    await ws_client.send_json({
        "id": 1,
        "type": UPDATE_WS_COMMAND,
        "display_id": "test-display-id",
        "data": {
            "display": {
                "current_url": test_url
            }
        }
    })

    msg = await ws_client.receive_json()
    assert msg["success"]

    assert display.data["existing_key"] == "existing_value"
    assert display.data["display"]["current_url"] == test_url

async def test_update_command_updates_client_version(
    hass: HomeAssistant,
    init_integration,
    ws_client,
) -> None:
    """Test update command updates client version."""
    test_version = "1.0.0"
    await ws_client.send_json({
        "id": 1,
        "type": UPDATE_WS_COMMAND,
        "display_id": "test-display-id",
        "data": {
            "client_version": test_version
        }
    })

    msg = await ws_client.receive_json()
    assert msg["success"]

    display = get_or_register_display(hass, "test-display-id")
    assert display.data["client_version"] == test_version