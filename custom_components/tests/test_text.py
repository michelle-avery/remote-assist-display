"""Test the Remote Assist Display text platform."""
from unittest.mock import Mock, patch

import pytest

from custom_components.remote_assist_display.const import DOMAIN, DEFAULT_HOME_ASSISTANT_DASHBOARD, DEFAULT_DEVICE_NAME_STORAGE_KEY, DATA_CONFIG_ENTRY
from custom_components.remote_assist_display.text import DefaultDashboardText, DeviceStorageKeyText


async def test_dashboard_text_initialization(mock_coordinator, mock_display):
    """Test DefaultDashboardText initialization."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    assert entity.name == "Default Dashboard"
    assert entity.unique_id == "test_display-Default_Dashboard"
    assert entity.display == mock_display


async def test_dashboard_native_value_from_settings(mock_coordinator, mock_display):
    """Test native_value when value is in settings."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )

    entity.coordinator.data = {"default_dashboard": "/lovelace/test"}

    assert entity.native_value == "/lovelace/test"


async def test_dashboard_native_value_fallback_to_attr(mock_coordinator, mock_display):
    """Test native_value falls back to _attr_native_value when no settings."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    entity.coordinator.data = {}
    entity._attr_native_value = "/lovelace/fallback"
    
    assert entity.native_value == "/lovelace/fallback"


async def test_dashboard_native_value_fallback_to_default_options(mock_coordinator, mock_display):
    """Test native_value falls back to default_display_options."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    entity.coordinator.data = {}
    
    assert entity.native_value == DEFAULT_HOME_ASSISTANT_DASHBOARD


async def test_dashboard_native_value_truncation(mock_coordinator, mock_display):
    """Test native_value truncates long strings."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    long_path = "/lovelace/" + "x" * 300
    
    entity.coordinator.data = {"default_dashboard": long_path }
    
    result = entity.native_value
    assert len(result) <= 255
    assert result.endswith("...")
    assert result.startswith("/lovelace/")


async def test_dashboard_async_set_value(hass, mock_coordinator, mock_display):
    """Test setting a new dashboard value."""
    entity = DefaultDashboardText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    mock_coordinator.hass = hass
    entity.hass = hass
    mock_coordinator.data = {}
    
    with patch.object(entity, 'async_write_ha_state') as mock_write_state:
        await entity.async_set_value("/lovelace/new")
        
        mock_display.update_settings.assert_called_once_with(
            hass,
            {
                "default_dashboard": "/lovelace/new",
                "display": {"default_dashboard": "/lovelace/new"},
            }
        )
        
        assert entity._value == "/lovelace/new"
        
        mock_write_state.assert_called_once()

async def test_device_storage_key_text_initialization(mock_coordinator, mock_display):
    """Test DeviceStorageKeyText initialization."""
    entity = DeviceStorageKeyText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )

    assert entity.name == "Device Storage Key"
    assert entity.unique_id == "test_display-Device_Storage_Key"
    assert entity.display == mock_display

async def test_device_storage_key_native_value_from_settings(mock_coordinator, mock_display):
    """Test native_value when value is in settings."""
    entity = DeviceStorageKeyText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )

    entity.coordinator.data = {"device_name_storage_key": "test-key"}

    assert entity.native_value == "test-key"

async def test_device_storage_key_native_value_fallback_to_attr(mock_coordinator, mock_display):
    """Test native_value falls back to _attr_native_value when no settings."""
    entity = DeviceStorageKeyText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )

    entity.coordinator.data = {}
    entity._attr_native_value = "fallback-key"

    assert entity.native_value == "fallback-key"

async def test_device_storage_key_native_value_fallback_to_default_options(mock_coordinator, mock_display):
    """Test native_value falls back to default_display_options."""
    entity = DeviceStorageKeyText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )

    entity.coordinator.data = {}

    assert entity.native_value == DEFAULT_DEVICE_NAME_STORAGE_KEY

async def test_device_storage_key_async_set_value(hass, mock_coordinator, mock_display):
    """Test setting a new device storage key value."""
    entity = DeviceStorageKeyText(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )

    mock_coordinator.hass = hass
    entity.hass = hass
    mock_coordinator.data = {}

    with patch.object(entity, 'async_write_ha_state') as mock_write_state:
        await entity.async_set_value("new-key")

        mock_display.update_settings.assert_called_once_with(
            hass,
            {
                "device_name_storage_key": "new-key",
                "display": {"device_name_storage_key": "new-key"},
            }
        )

        assert entity._value == "new-key"

        mock_write_state.assert_called_once()