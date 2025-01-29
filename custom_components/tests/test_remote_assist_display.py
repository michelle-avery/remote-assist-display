"""Test the Remote Assist Display class."""
from unittest.mock import Mock, patch
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.remote_assist_display.const import (
    DOMAIN,
    DATA_DISPLAYS,
    DATA_ADDERS,
)
from custom_components.remote_assist_display.remote_assist_display import (
    RemoteAssistDisplay,
    get_or_register_display,
    delete_display,
    get_display_by_connection,
)


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
async def registered_display(hass, mock_adders, config_entry):
    """Create a display with registered entities."""
    display = RemoteAssistDisplay(hass, "test_display")

    # Create device registry entry
    device_reg = dr.async_get(hass)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "test_display")},
    )
    
    # Register the entities
    entity_reg = er.async_get(hass)
    for entity_id, entity in display.entities.items():
        entry = entity_reg.async_get_or_create(
            domain=DOMAIN,
            platform="remote_assist_display",
            unique_id=f"test_display-{entity_id}",
            config_entry=config_entry,
            device_id=device_entry.id,
        )
        entity.entity_id = entry.entity_id
    
    return display


async def verify_display_deleted(hass, display):
    """Verify a display and its entities were properly deleted."""
    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)
    
    assert device_reg.async_get_device({(DOMAIN, "test_display")}) is None
    for entity in display.entities.values():
        assert entity_reg.async_get(entity.entity_id) is None


async def test_remote_assist_display_initialization(hass, mock_adders, mock_send):
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
    assert mock_adders["sensor"].call_count == 1
    assert mock_adders["text"].call_count == 2
    assert mock_adders["select"].call_count == 1

    # Verify send was called
    mock_send.assert_called_once()


async def test_update_data(hass, mock_adders, mock_send):
    """Test updating display data."""
    display = RemoteAssistDisplay(hass, "test_display")
    display.coordinator.async_set_updated_data = Mock()
    
    new_data = {"connected": True, "current_url": "http://example.com"}
    display.update(hass, new_data)
    
    assert display.data["connected"] is True
    assert display.data["current_url"] == "http://example.com"
    display.coordinator.async_set_updated_data.assert_called_once_with(display.data)


async def test_update_settings(hass, mock_adders, mock_send):
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


async def test_connection_management(hass, mock_adders, mock_send):
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


async def test_get_or_register_display(hass, mock_adders, displays, mock_send):
    """Test get_or_register_display function."""
    # First call should create new display
    display1 = get_or_register_display(hass, "test_display")
    assert isinstance(display1, RemoteAssistDisplay)
    assert "test_display" in displays
    
    # Second call should return existing display
    display2 = get_or_register_display(hass, "test_display")
    assert display1 is display2


async def test_delete_display_function(hass, mock_adders, displays, config_entry):
    """Test delete_display function."""
    # Create display using the function we're testing
    display = get_or_register_display(hass, "test_display")

    # Create device registry entry
    device_reg = dr.async_get(hass)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "test_display")},
    )
    
    # Register the entities
    entity_reg = er.async_get(hass)
    for entity_id, entity in display.entities.items():
        entry = entity_reg.async_get_or_create(
            domain=DOMAIN,
            platform="remote_assist_display",
            unique_id=f"test_display-{entity_id}",
            config_entry=config_entry,
            device_id=device_entry.id,
        )
        entity.entity_id = entry.entity_id
    
    # Delete display
    deleted_display = delete_display(hass, "test_display")
    
    assert deleted_display is display
    assert "test_display" not in displays
    await verify_display_deleted(hass, display)


async def test_get_display_by_connection(hass, mock_adders, displays, mock_send):
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