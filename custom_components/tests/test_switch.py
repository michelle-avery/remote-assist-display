"""Test the Remote Assist Display switch platform."""
from unittest.mock import patch

from custom_components.remote_assist_display.switch import RADHideHeaderSwitch, RADHideSidebarSwitch


async def test_header_switch_initialization(mock_coordinator, mock_display):
    """Test RADHideHeaderSwitch initialization."""
    entity = RADHideHeaderSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    assert entity.name == "Hide Header"
    assert entity.unique_id == "test_display-Hide_Header"
    assert entity.display == mock_display

async def test_header_switch_native_value_from_settings(mock_coordinator, mock_display):
    """Test native_value when value is in settings."""
    entity = RADHideHeaderSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )

    entity.coordinator.data = {"hide_header": True}

    assert entity.is_on

async def test_header_switch_native_value_fallback_to_attr(mock_coordinator, mock_display):
    """Test native_value falls back to _attr_is_on when no settings."""
    entity = RADHideHeaderSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    entity.coordinator.data = {}
    entity._attr_is_on = True
    
    assert entity.is_on

async def test_header_switch_native_value_fallback_to_default_options(mock_coordinator, mock_display):
    """Test native_value falls back to default_display_options."""
    entity = RADHideHeaderSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    entity.coordinator.data = {}
    
    assert not entity.is_on

async def test_header_switch_turn_on(mock_coordinator, mock_display):
    """Test turning on the switch."""
    entity = RADHideHeaderSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    with patch.object(entity, 'async_write_ha_state') as mock_write_state:
        with patch.object(entity, 'schedule_update_ha_state') as mock_schedule_update:
            await entity.async_turn_on()
            
            mock_display.update_settings.assert_called_once_with(
                entity.hass,
                {
                    "hide_header": True,
                    "display": {"hide_header": True},
                }
            )
            
            assert entity.is_on
            
            mock_write_state.assert_called_once()
            mock_schedule_update.assert_called_once()

async def test_header_switch_turn_off(mock_coordinator, mock_display):
    """Test turning off the switch."""
    entity = RADHideHeaderSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    with patch.object(entity, 'async_write_ha_state') as mock_write_state:
        with patch.object(entity, 'schedule_update_ha_state') as mock_schedule_update:
            await entity.async_turn_off()
            
            mock_display.update_settings.assert_called_once_with(
                entity.hass,
                {
                    "hide_header": False,
                    "display": {"hide_header": False},
                }
            )
            
            mock_write_state.assert_called_once()
            mock_schedule_update.assert_called_once()

async def test_sidebar_switch_initialization(mock_coordinator, mock_display):
    """Test RADHideSidebarSwitch initialization."""
    entity = RADHideSidebarSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    assert entity.name == "Hide Sidebar"
    assert entity.unique_id == "test_display-Hide_Sidebar"
    assert entity.display == mock_display

async def test_sidebar_switch_native_value_from_settings(mock_coordinator, mock_display):
    """Test native_value when value is in settings."""
    entity = RADHideSidebarSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )

    entity.coordinator.data = {"hide_sidebar": True}

    assert entity.is_on

async def test_sidebar_switch_native_value_fallback_to_attr(mock_coordinator, mock_display):
    """Test native_value falls back to _attr_is_on when no settings."""
    entity = RADHideSidebarSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    entity.coordinator.data = {}
    entity._attr_is_on = True
    
    assert entity.is_on

async def test_sidebar_switch_native_value_fallback_to_default_options(mock_coordinator, mock_display):
    """Test native_value falls back to default_display_options."""
    entity = RADHideSidebarSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    entity.coordinator.data = {}
    
    assert not entity.is_on

async def test_sidebar_switch_turn_on(mock_coordinator, mock_display):
    """Test turning on the switch."""
    entity = RADHideSidebarSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    with patch.object(entity, 'async_write_ha_state') as mock_write_state:
        await entity.async_turn_on()
        
        mock_display.update_settings.assert_called_once_with(
            entity.hass,
            {
                "hide_sidebar": True,
                "display": {"hide_sidebar": True},
            }
        )
        
        assert entity.is_on
        
        mock_write_state.assert_called_once()

async def test_sidebar_switch_turn_off(mock_coordinator, mock_display):
    """Test turning off the switch."""
    entity = RADHideSidebarSwitch(
        coordinator=mock_coordinator,
        display_id="test_display",
        display=mock_display,
    )
    
    with patch.object(entity, 'async_write_ha_state') as mock_write_state:
        await entity.async_turn_off()
        
        mock_display.update_settings.assert_called_once_with(
            entity.hass,
            {
                "hide_sidebar": False,
                "display": {"hide_sidebar": False},
            }
        )
        
        mock_write_state.assert_called_once()


