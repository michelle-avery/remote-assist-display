"""Test the Remote Assist Display select platform."""
from unittest.mock import Mock, patch

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.remote_assist_display.const import DOMAIN, DATA_CONFIG_ENTRY
from custom_components.remote_assist_display.select import RADAssistSatelliteSelect


@pytest.fixture
def rad_satellite_select(hass, mock_coordinator, mock_display):
    """Create a test RADAssistSatelliteSelect entity."""
    entity = RADAssistSatelliteSelect(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    entity.hass = hass
    return entity


async def test_satellite_select_initialization(rad_satellite_select):
    """Test RADAssistSatelliteSelect initialization."""
    assert rad_satellite_select.name == "Assist Satellite"
    assert rad_satellite_select.unique_id == "test_display-Assist_Satellite"
    assert rad_satellite_select.display == rad_satellite_select.display
    assert rad_satellite_select._attr_options == []


async def test_satellite_select_added_to_hass(hass, rad_satellite_select):
    """Test async_added_to_hass populates options correctly."""
    registry = er.async_get(hass)
    
    # Create some mock assist satellite entities
    registry.async_get_or_create(
        domain="assist_satellite",
        platform="assist",
        unique_id="satellite1",
        suggested_object_id="kitchen",
    )
    registry.async_get_or_create(
        domain="assist_satellite",
        platform="assist",
        unique_id="satellite2",
        suggested_object_id="living_room",
    )

    # Add a non-satellite entity to ensure filtering works
    registry.async_get_or_create(
        domain="light",
        platform="test",
        unique_id="test_light",
    )

    await rad_satellite_select.async_added_to_hass()

    assert len(rad_satellite_select._attr_options) == 2
    assert "assist_satellite.kitchen" in rad_satellite_select._attr_options
    assert "assist_satellite.living_room" in rad_satellite_select._attr_options


async def test_satellite_select_state_restoration(hass, rad_satellite_select):
    """Test state restoration behavior."""
    registry = er.async_get(hass)
    registry.async_get_or_create(
        domain="assist_satellite",
        platform="assist",
        unique_id="satellite1",
        suggested_object_id="kitchen",
    )

    # Test with no previous state
    await rad_satellite_select.async_added_to_hass()
    assert rad_satellite_select._attr_current_option is None

    # Test with invalid previous state
    with patch('homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state') as mock_state:
        mock_state.return_value = Mock(state="invalid_satellite")
        await rad_satellite_select.async_added_to_hass()
        assert rad_satellite_select._attr_current_option is None

    # Test with valid previous state
    with patch('homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state') as mock_state:
        mock_state.return_value = Mock(state="assist_satellite.kitchen")
        await rad_satellite_select.async_added_to_hass()
        assert rad_satellite_select._attr_current_option == "assist_satellite.kitchen"


async def test_satellite_select_option(rad_satellite_select):
    """Test selecting an option."""
    with patch.object(rad_satellite_select, 'async_update_ha_state') as mock_update:
        await rad_satellite_select.async_select_option("assist_satellite.kitchen")
        
        assert rad_satellite_select._attr_current_option == "assist_satellite.kitchen"
        mock_update.assert_called