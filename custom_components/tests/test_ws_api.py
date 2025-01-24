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


@pytest.mark.xfail(reason="Multiple connections are not properly handled yet - connections should be replaced rather than added")
async def test_connect_command(
    hass: HomeAssistant,
    init_integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test connect websocket command."""
    client = await hass_ws_client(hass)

    with patch("custom_components.remote_assist_display.ws_api.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2025, 1, 23, 12, 0, 0)
        mock_datetime.timezone = timezone

        # Send connect command
        await client.send_json({
            "id": 1,
            "type": CONNECT_WS_COMMAND,
            "display_id": "test-display-id"
        })

        # Verify response
        msg = await client.receive_json()
        assert msg["success"]
        assert msg["result"] == "registered"

        # Verify display state
        display = get_or_register_display(hass, "test-display-id")
        assert len(display.connection) == 1
        assert display.data.get("connected") is True

        # Test connection replacement
        client2 = await hass_ws_client(hass)
        await client2.send_json({
            "id": 2,
            "type": CONNECT_WS_COMMAND,
            "display_id": "test-display-id"
        })
        msg = await client2.receive_json()
        assert msg["success"]

        # Verify only second connection exists
        display = get_or_register_display(hass, "test-display-id")
        assert len(display.connection) == 1
        assert display.data.get("connected") is True


async def test_register_command(
    hass: HomeAssistant,
    init_integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test register websocket command."""
    client = await hass_ws_client(hass)

    # Test initial registration
    await client.send_json({
        "id": 1,
        "type": REGISTER_WS_COMMAND,
        "display_id": "test-display-id",
        "hostname": "test-hostname"
    })

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["registered"] is True
    assert msg["result"]["hostname"] == "test-hostname"

    display = get_or_register_display(hass, "test-display-id")
    assert display.settings["registered"] is True
    assert display.settings["hostname"] == "test-hostname"

    # Test hostname update
    await client.send_json({
        "id": 2,
        "type": REGISTER_WS_COMMAND,
        "display_id": "test-display-id",
        "hostname": "new-hostname"
    })

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["hostname"] == "new-hostname"

    display = get_or_register_display(hass, "test-display-id")
    assert display.settings["hostname"] == "new-hostname"
    assert display.settings["registered"] is True


async def test_settings_command(
    hass: HomeAssistant,
    init_integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test settings websocket command."""
    client = await hass_ws_client(hass)

    # Test with custom dashboard
    display = get_or_register_display(hass, "test-display-id")
    display.entities["default_dashboard"] = MagicMock()
    display.entities["default_dashboard"].native_value = "custom-dashboard"

    await client.send_json({
        "id": 1,
        "type": SETTINGS_WS_COMMAND,
        "display_id": "test-display-id"
    })

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["settings"]["default_dashboard"] == "custom-dashboard"

    # Test with no dashboard value
    display.entities["default_dashboard"].native_value = None

    await client.send_json({
        "id": 2,
        "type": SETTINGS_WS_COMMAND,
        "display_id": "test-display-id"
    })

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"]["settings"]["default_dashboard"] is None


async def test_update_command(
    hass: HomeAssistant,
    init_integration,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test update websocket command."""
    client = await hass_ws_client(hass)

    # Test updating current URL
    await client.send_json({
        "id": 1,
        "type": UPDATE_WS_COMMAND,
        "display_id": "test-display-id",
        "data": {
            "display": {
                "current_url": "http://localhost:8123/dashboard-viewassist/clock?kiosk"
            }
        }
    })

    msg = await client.receive_json()
    assert msg["success"]

    display = get_or_register_display(hass, "test-display-id")
    assert display.data["display"]["current_url"] == "http://localhost:8123/dashboard-viewassist/clock?kiosk"

    # Test data merging
    display.update(hass, {"existing_key": "existing_value"})

    await client.send_json({
        "id": 2,
        "type": UPDATE_WS_COMMAND,
        "display_id": "test-display-id",
        "data": {
            "display": {
                "current_url": "http://localhost:8123/dashboard-viewassist/clock?kiosk"
            }
        }
    })

    msg = await client.receive_json()
    assert msg["success"]

    assert display.data["existing_key"] == "existing_value"
    assert display.data["display"]["current_url"] == "http://localhost:8123/dashboard-viewassist/clock?kiosk"
