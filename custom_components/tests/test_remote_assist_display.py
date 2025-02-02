"""Test the Remote Assist Display class."""
from unittest.mock import Mock, patch
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.remote_assist_display.const import (
    DOMAIN,
    DATA_DISPLAYS,
    DATA_ADDERS,
    DATA_CONFIG_ENTRY,
)
from custom_components.remote_assist_display.remote_assist_display import (
    RemoteAssistDisplay,
    get_or_register_display,
    delete_display,
    get_display_by_connection,
)

# Base Fixtures

@pytest.fixture
def mock_adders(hass):
    """Create mock entity adders."""
    hass.data[DOMAIN][DATA_ADDERS] = {
        "sensor": Mock(),
        "text": Mock(),
        "select": Mock(),
    }
    return hass.data[DOMAIN][DATA_ADDERS]

@pytest.fixture
def displays(hass):
    """Initialize the displays dict."""
    hass.data[DOMAIN][DATA_DISPLAYS] = {}
    return hass.data[DOMAIN][DATA_DISPLAYS]

@pytest.fixture
def mock_send():
    """Mock the send method."""
    with patch('custom_components.remote_assist_display.remote_assist_display.RemoteAssistDisplay.send') as mock_send:
        yield mock_send

@pytest.fixture
def setup_config_entry(hass, config_entry):
    """Set up the config entry in hass data."""
    hass.config_entries.async_update_entry(
        config_entry,
        options={}
    )
    hass.data[DOMAIN][DATA_CONFIG_ENTRY] = config_entry
    return config_entry

@pytest.fixture
def setup_config_entry_with_event(hass, setup_config_entry):
    """Set up the config entry in hass data with event type."""
    hass.config_entries.async_update_entry(
        setup_config_entry,
        options={"event_type": "test_event"}
    )
    return setup_config_entry

# Compound Fixtures

@pytest.fixture
async def registered_display(hass, mock_adders, setup_config_entry):
    """Create a display with registered entities."""
    display = RemoteAssistDisplay(hass, "test_display")

    # Create device registry entry
    device_reg = dr.async_get(hass)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=setup_config_entry.entry_id,
        identifiers={(DOMAIN, "test_display")},
    )
    
    # Register the entities
    entity_reg = er.async_get(hass)
    for entity_id, entity in display.entities.items():
        entry = entity_reg.async_get_or_create(
            domain=DOMAIN,
            platform="remote_assist_display",
            unique_id=f"test_display-{entity_id}",
            config_entry=setup_config_entry,
            device_id=device_entry.id,
        )
        entity.entity_id = entry.entity_id
    
    return display

# Helper Functions

async def verify_display_deleted(hass, display):
    """Verify a display and its entities were properly deleted."""
    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)
    
    assert device_reg.async_get_device({(DOMAIN, "test_display")}) is None
    for entity in display.entities.values():
        assert entity_reg.async_get(entity.entity_id) is None

# Tests

async def test_remote_assist_display_initialization(hass, mock_adders, mock_send, setup_config_entry):
    """Test RemoteAssistDisplay initialization."""
    display = RemoteAssistDisplay(hass, "test_display")

    assert display.display_id == "test_display"
    assert display.data == {}
    assert display.settings == {}
    assert display._connections == []

    # Verify entities were created
    assert "current_url" in display.entities
    assert "default_dashboard" in display.entities
    assert "device_storage_key" in display.entities
    assert "assist_satellite" in display.entities

    # Verify entity adders were called
    assert mock_adders["sensor"].call_count == 2
    assert mock_adders["text"].call_count == 2
    assert mock_adders["select"].call_count == 1

async def test_update_data(hass, mock_adders, mock_send, setup_config_entry):
    """Test updating display data."""
    display = RemoteAssistDisplay(hass, "test_display")
    display.coordinator.async_set_updated_data = Mock()
    
    new_data = {"connected": True, "current_url": "http://example.com"}
    display.update(hass, new_data)
    
    assert display.data["connected"] is True
    assert display.data["current_url"] == "http://example.com"
    display.coordinator.async_set_updated_data.assert_called_once_with(display.data)

async def test_update_settings(hass, mock_adders, mock_send, setup_config_entry):
    """Test updating display settings."""
    display = RemoteAssistDisplay(hass, "test_display")
    
    settings = {
        "settings": {"default_dashboard": "/lovelace/0"},
        "display": {"default_dashboard": "/lovelace/0"},
    }
    
    display.update_settings(hass, settings)
    
    assert display.settings == settings
    mock_send.assert_called_with(
        "remote_assist_display/update_settings", 
        settings=settings
    )

async def test_connection_management(hass, mock_adders, mock_send, setup_config_entry):
    """Test connection management."""
    display = RemoteAssistDisplay(hass, "test_display")
    mock_connection = Mock()
    
    # Test opening connection
    display.open_connection(hass, mock_connection, "connection_id")
    
    assert len(display._connections) == 1
    assert display._connections[0] == (mock_connection, "connection_id")
    assert display.data["connected"] is True
    
    # Test closing connection
    display.close_connection(hass, mock_connection)
    
    assert len(display._connections) == 0
    assert display.data["connected"] is False

async def test_delete_display(hass, registered_display):
    """Test deleting a display."""
    registered_display.delete(hass)
    await verify_display_deleted(hass, registered_display)

async def test_get_or_register_display(hass, mock_adders, displays, mock_send, setup_config_entry):
    """Test get_or_register_display function."""
    # First call should create new display
    display1 = get_or_register_display(hass, "test_display")
    assert isinstance(display1, RemoteAssistDisplay)
    assert "test_display" in displays
    
    # Second call should return existing display
    display2 = get_or_register_display(hass, "test_display")
    assert display1 is display2

async def test_delete_display_function(hass, mock_adders, displays, registered_display):
    """Test delete_display function."""
    # Add our registered display to the displays dict (which is what get_or_register_display would do)
    displays[registered_display.display_id] = registered_display
    
    # Delete display
    deleted_display = delete_display(hass, "test_display")
    
    assert deleted_display is registered_display
    assert "test_display" not in displays
    await verify_display_deleted(hass, registered_display)

async def test_get_display_by_connection(hass, mock_adders, displays, setup_config_entry):
    """Test get_display_by_connection function."""
    display = get_or_register_display(hass, "test_display")
    
    # Test with connected connection
    mock_connection = Mock()
    display.open_connection(hass, mock_connection, "connection_id")
    
    found_display = get_display_by_connection(hass, mock_connection)
    assert found_display is display
    
    # Test with non-connected connection
    other_connection = Mock()
    found_display = get_display_by_connection(hass, other_connection)
    assert found_display is None

# Event-related tests

async def test_event_listener_initialization(hass, mock_adders, setup_config_entry_with_event):
    """Test event listener is set up when event_type is configured."""
    display = RemoteAssistDisplay(hass, "test_display")
    assert display._event_listener is not None

async def test_event_listener_not_initialized_without_event_type(hass, mock_adders, setup_config_entry):
    """Test event listener is not set up when event_type is not configured."""
    display = RemoteAssistDisplay(hass, "test_display")
    assert display._event_listener is None

async def test_event_handling(hass, mock_adders, setup_config_entry_with_event, mock_send):
    """Test handling of events updates the intent sensor."""
    mock_satellite = Mock()
    mock_satellite.satellite_id = "test_device_id"
    
    # Create a display
    display = RemoteAssistDisplay(hass, "test_display")
    display.entities["assist_satellite"] = mock_satellite

    # Mock the intent sensor's update method
    intent_sensor = display.entities.get("intent_sensor")
    intent_sensor.update_from_event = Mock()

    # Create and fire a test event
    event_data = {
        "device_id": "test_device_id",
        "result": {
            "response": {
                "speech": {
                    "plain": {
                        "speech": "Test response",
                    }
                }
            }
        }
    }
    
    hass.bus.async_fire("test_event", event_data)
    await hass.async_block_till_done()
    
    # Verify intent sensor was updated
    intent_sensor.update_from_event.assert_called_once_with(event_data["result"])

async def test_event_handling_wrong_device(hass, mock_adders, setup_config_entry_with_event, mock_send):
    """Test events from wrong device are ignored."""
    mock_satellite = Mock()
    mock_satellite.satellite_id = "test_device_id"
    
    display = RemoteAssistDisplay(hass, "test_display")
    display.entities["assist_satellite"] = mock_satellite

    intent_sensor = display.entities.get("intent_sensor")
    intent_sensor.update_from_event = Mock()

    event_data = {
        "device_id": "wrong_device_id",
        "result": {
            "response": {
                "speech": {
                    "plain": {
                        "speech": "Test response",
                    }
                }
            }
        }
    }
    
    hass.bus.async_fire("test_event", event_data)
    await hass.async_block_till_done()
    
    intent_sensor.update_from_event.assert_not_called()

async def test_event_listener_cleanup(hass, mock_adders, setup_config_entry_with_event):
    """Test event listener is cleaned up when new one is set."""
    old_listener = Mock()
    
    with patch('homeassistant.core.EventBus.async_listen', return_value=old_listener):
        display = RemoteAssistDisplay(hass, "test_display")
        assert display._event_listener == old_listener
        display._set_event_listener()
        old_listener.assert_called_once()