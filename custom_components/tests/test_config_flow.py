"""Test the Remote Assist Display config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.remote_assist_display.const import DOMAIN


async def test_single_instance_only(hass: HomeAssistant) -> None:
    """Test that config flow enforces single instance."""
    # First setup should succeed
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Remote Assist Display"
    assert result["data"] == {}

    # Second attempt should be aborted
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result2["type"] == "abort"
    assert result2["reason"] == "single_instance_allowed"


async def test_options_flow_init(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test options flow initialization."""
    # Test with no existing options
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == "form"
    assert result["step_id"] == "init"
    
    # Verify schema
    schema = result["data_schema"].schema
    assert "default_dashboard_path" in schema


async def test_options_flow_set_path(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test setting dashboard path in options flow."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    
    # Set a dashboard path
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"default_dashboard_path": "/lovelace/0"}
    )
    assert result2["type"] == "create_entry"
    assert result2["data"]["default_dashboard_path"] == "/lovelace/0"


async def test_options_flow_update_path(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test updating existing dashboard path."""
    # First set initial options
    hass.config_entries.async_update_entry(
        entry=config_entry,
        options={"default_dashboard_path": "/lovelace/0"}
    )
    
    # Update to new path
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"default_dashboard_path": "/lovelace/1"}
    )
    assert result2["type"] == "create_entry"
    assert result2["data"]["default_dashboard_path"] == "/lovelace/1"


async def test_options_flow_remove_path(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test removing dashboard path."""
    # First set initial options
    hass.config_entries.async_update_entry(
        entry=config_entry,
        options={"default_dashboard_path": "/lovelace/0"}
    )
    
    # Remove path by setting empty string
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"default_dashboard_path": ""}
    )
    assert result2["type"] == "create_entry"
    assert result2["data"]["default_dashboard_path"] == ""


async def test_options_flow_none_input(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    """Test options flow with None input."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    
    # Test form shows with None input
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=None
    )
    assert result2["type"] == "form"
    assert result2["step_id"] == "init"
