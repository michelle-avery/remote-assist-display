from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_ADDERS,
    DOMAIN,
    DATA_CONFIG_ENTRY,
)

from .entities import RADEntity


async def async_setup_platform(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Any = None,
) -> None:
    """Set up the switch platform."""
    hass.data[DOMAIN][DATA_ADDERS]["switch"] = async_add_entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    await async_setup_platform(hass, config_entry, async_add_entities)


class RADHideHeaderSwitch(RADEntity, SwitchEntity):
    def __init__(
        self,
        coordinator,
        display_id,
        display,
    ):
        """Initialize the switch."""
        RADEntity.__init__(self, coordinator, display_id, "Hide Header")
        SwitchEntity.__init__(self)
        self.display = display

    @property
    def is_on(self):
        value = self._data.get("hide_header", None)
        if not value:
            try:
                value = self._attr_is_on
            except AttributeError:
                value = self.coordinator.hass.data[DOMAIN][
                    DATA_CONFIG_ENTRY
                ].options.get("hide_header", False)
            if not value:
                value = self.coordinator.hass.data[DOMAIN][
                    DATA_CONFIG_ENTRY
                ].options.get("hide_header", False)
        return value

    async def async_turn_on(self, **kwargs):
        data = {
            "hide_header": True,
            "display": {"hide_header": True},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        data = {
            "hide_header": False,
            "display": {"hide_header": False},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()


class RADHideSidebarSwitch(RADEntity, SwitchEntity):
    def __init__(
        self,
        coordinator,
        display_id,
        display,
    ):
        """Initialize the switch."""
        RADEntity.__init__(self, coordinator, display_id, "Hide Sidebar")
        SwitchEntity.__init__(self)
        self.display = display

    @property
    def is_on(self):
        value = self._data.get("hide_sidebar", None)
        if not value:
            try:
                value = self._attr_is_on
            except AttributeError:
                value = self.coordinator.hass.data[DOMAIN][
                    DATA_CONFIG_ENTRY
                ].options.get("hide_sidebar", False)
            if not value:
                value = self.coordinator.hass.data[DOMAIN][
                    DATA_CONFIG_ENTRY
                ].options.get("hide_sidebar", False)
        return value

    async def async_turn_on(self, **kwargs):
        data = {
            "hide_sidebar": True,
            "display": {"hide_sidebar": True},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        data = {
            "hide_sidebar": False,
            "display": {"hide_sidebar": False},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()
