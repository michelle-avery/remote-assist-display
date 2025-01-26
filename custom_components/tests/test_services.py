"""Test the Remote Assist Display services."""
from unittest.mock import Mock
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from custom_components.remote_assist_display.const import DOMAIN, NAVIGATE_SERVICE, NAVIGATE_URL_SERVICE
from custom_components.remote_assist_display.service import async_setup_services


class MockDisplay:
    """Mock display class for testing."""
    def __init__(self):
        self.send = Mock()

@pytest.fixture
async def mock_device(hass: HomeAssistant, config_entry):
    """Create a mock device for testing."""
    dev_reg = dr.async_get(hass)
    return dev_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "test-device")},
        name="test-device"
    )

@pytest.fixture
async def setup_services(hass: HomeAssistant):
    """Set up services for testing."""
    async_setup_services(hass)
    await hass.async_block_till_done()

async def test_service_call_with_device_id_target(hass: HomeAssistant, mock_device, setup_services):
    """Test service call fails when using device_id target."""
    display = MockDisplay()
    hass.data[DOMAIN] = {"displays": {mock_device.name: display}}

    await hass.services.async_call(
            DOMAIN,
            NAVIGATE_SERVICE,
            service_data={"path": "/test"},
            target={"device_id": mock_device.id}
        )
    
    display.send.assert_called_once_with("remote_assist_display/navigate", path="/test")



async def test_service_call_with_correct_target_succeeds(hass: HomeAssistant, mock_device, setup_services):
    """Test service call succeeds with proper target in service data."""
    display = MockDisplay()
    hass.data[DOMAIN] = {"displays": {mock_device.name: display}}
    
    await hass.services.async_call(
        DOMAIN,
        NAVIGATE_SERVICE,
        service_data={
            "target": [mock_device.id],
            "path": "/test"
        }
    )
    
    display.send.assert_called_once_with("remote_assist_display/navigate", path="/test")

async def test_service_call_with_invalid_target_fails(hass: HomeAssistant, setup_services):
    """Test service call fails with invalid target."""
    
    hass.data[DOMAIN] = {"displays": {}}
    
    response = await hass.services.async_call(
        DOMAIN,
        NAVIGATE_SERVICE,
        service_data={
            "target": ["invalid-device"],
            "path": "/test"
        },
        blocking=True,
        return_response=True 
    )
    
    assert response["success"] is False

async def test_url_service_call_with_device_id_target(hass: HomeAssistant, mock_device, setup_services):
    """Test service call fails when using device_id target."""
    display = MockDisplay()
    hass.data[DOMAIN] = {"displays": {mock_device.name: display}}

    await hass.services.async_call(
            DOMAIN,
            NAVIGATE_URL_SERVICE,
            service_data={"url": "http://test.com"},
            target={"device_id": mock_device.id}
        )
    
    display.send.assert_called_once_with("remote_assist_display/navigate_url", url="http://test.com")

async def test_url_service_call_with_correct_target_succeeds(hass: HomeAssistant, mock_device, setup_services):
    """Test service call succeeds with proper target in service data."""
    display = MockDisplay()
    hass.data[DOMAIN] = {"displays": {mock_device.name: display}}
    
    await hass.services.async_call(
        DOMAIN,
        NAVIGATE_URL_SERVICE,
        service_data={
            "target": [mock_device.id],
            "url": "http://test.com"
        }
    )
    
    display.send.assert_called_once_with("remote_assist_display/navigate_url", url="http://test.com")

async def test_url_service_call_with_invalid_target_fails(hass: HomeAssistant, setup_services):
    """Test service call fails with invalid target."""
    
    hass.data[DOMAIN] = {"displays": {}}

    response = await hass.services.async_call(
        DOMAIN,
        NAVIGATE_URL_SERVICE,
        service_data={
            "target": ["invalid-device"],
            "url": "http://test.com"
        },
        blocking=True,
        return_response=True 
    )

    assert response["success"] is False