"""Test the Remote Assist Display text platform."""
from unittest.mock import Mock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.remote_assist_display.const import DOMAIN, DEFAULT_HOME_ASSISTANT_DASHBOARD
from custom_components.remote_assist_display.text import DefaultDashboardText


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.hass = Mock()
    coordinator.hass.data = {
        DOMAIN: {
            "default_display_options": {
                "default_dashboard_path": "/test-dashboard"
            }
        }
    }
    return coordinator


@pytest.fixture
def mock_display():
    """Create a mock display."""
    display = Mock()
    display.update_settings = Mock()
    return display


async def test_text_initialization(mock_coordinator, mock_display):
    """Test DefaultDashboardText initialization."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    assert entity.name == "Default Dashboard"
    assert entity.unique_id == "test_display-Default_Dashboard"
    assert entity.display == mock_display


async def test_native_value_from_settings(mock_coordinator, mock_display):
    """Test native_value when value is in settings."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    # Mock the _data property
    entity.coordinator.data = {
        "settings": {
            "default_dashboard": "/lovelace/test"
        }
    }
    
    assert entity.native_value == "/lovelace/test"


async def test_native_value_fallback_to_attr(mock_coordinator, mock_display):
    """Test native_value falls back to _attr_native_value when no settings."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    # Set up empty data and a fallback value
    entity.coordinator.data = {}
    entity._attr_native_value = "/lovelace/fallback"
    
    assert entity.native_value == "/lovelace/fallback"


async def test_native_value_fallback_to_default_options(mock_coordinator, mock_display):
    """Test native_value falls back to default_display_options."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    # Set up empty data and no attr_native_value
    entity.coordinator.data = {}
    
    # The mock_coordinator fixture already sets up default_display_options with "/test-dashboard"
    assert entity.native_value == "/test-dashboard"


async def test_native_value_truncation(mock_coordinator, mock_display):
    """Test native_value truncates long strings."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    # Create a string longer than 255 characters
    long_path = "/lovelace/" + "x" * 300
    
    entity.coordinator.data = {
        "settings": {
            "default_dashboard": long_path
        }
    }
    
    result = entity.native_value
    assert len(result) <= 255
    assert result.endswith("...")
    assert result.startswith("/lovelace/")


async def test_async_set_value(hass, mock_coordinator, mock_display):
    """Test setting a new dashboard value."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    # Set up hass on both coordinator and entity
    mock_coordinator.hass = hass
    entity.hass = hass
    
    # Mock async_write_ha_state
    with patch.object(entity, 'async_write_ha_state') as mock_write_state:
        await entity.async_set_value("/lovelace/new")
        
        # Verify display settings were updated
        mock_display.update_settings.assert_called_once_with(
            hass,
            {
                "settings": {"default_dashboard": "/lovelace/new"},
                "display": {"default_dashboard": "/lovelace/new"},
            }
        )
        
        # Verify data was updated
        assert entity._data == {
            "settings": {"default_dashboard": "/lovelace/new"},
            "display": {"default_dashboard": "/lovelace/new"},
        }
        
        # Verify state was written
        assert entity._value == "/lovelace/new"
        
        # Verify async_write_ha_state was called
        mock_write_state.assert_called_once()
