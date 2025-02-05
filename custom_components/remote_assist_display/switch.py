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
        value = self._data.get("settings", {}).get("hide_header", None)
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
            "settings": {"hide_header": True},
            "display": {"hide_header": True},
        }
        await self.display.update_settings(self.hass, data)

    async def async_turn_off(self, **kwargs):
        data = {
            "settings": {"hide_header": False},
            "display": {"hide_header": False},
        }
        await self.display.update_settings(self.hass, data)
