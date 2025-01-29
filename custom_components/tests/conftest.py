"""Fixtures for Remote Assist Display integration tests."""
import pytest
from homeassistant.const import CONF_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from unittest.mock import Mock
from custom_components.remote_assist_display.const import DOMAIN, DATA_CONFIG_ENTRY


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for testing."""
    yield


@pytest.fixture
def hass(hass: HomeAssistant):
    """Return an initialized Home Assistant instance."""
    hass.data.update({DOMAIN: {}})
    return hass


@pytest.fixture
async def config_entry(hass):
    """Create a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Remote Assist Display",
        data={},
        options={},
    )
    entry.add_to_hass(hass)
    return entry

@pytest.fixture
def mock_coordinator(config_entry, hass):
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.hass = hass
    coordinator.hass.data[DOMAIN][DATA_CONFIG_ENTRY] = config_entry
    return coordinator

@pytest.fixture
def mock_display():
    """Create a mock display."""
    display = Mock()
    display.send = Mock()
    return display

@pytest.fixture
async def init_integration(hass, config_entry):
    """Set up the Remote Assist Display integration for testing."""
    await async_setup_component(hass, DOMAIN, {CONF_DOMAIN: {}})
    await hass.async_block_till_done()
    return config_entry
