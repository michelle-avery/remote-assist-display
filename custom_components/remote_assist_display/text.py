from typing import Any

from homeassistant.components.text import RestoreText
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_ADDERS,
    DOMAIN,
    DEFAULT_DISPLAY_OPTIONS,
    DEFAULT_HOME_ASSISTANT_DASHBOARD,
)
from .entities import RADEntity


async def async_setup_platform(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Any = None,
) -> None:
    """Set up the text platform."""
    hass.data[DOMAIN][DATA_ADDERS]["text"] = async_add_entities
    hass.data[DOMAIN][DEFAULT_DISPLAY_OPTIONS] = dict(config_entry.options)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up text entities."""
    await async_setup_platform(hass, config_entry, async_add_entities)


class DefaultDashboardText(RADEntity, RestoreText):
    def __init__(
        self,
        coordinator,
        display_id,
        display,
    ):
        """Initialize the text."""
        RADEntity.__init__(self, coordinator, display_id, "Default Dashboard")
        RestoreText.__init__(self)
        self.display = display

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        if (last_text_data := await self.async_get_last_text_data()) is None:
            self._attr_native_value = None
            return
        else:
            self._attr_native_value = last_text_data.native_value

    @property
    def native_value(self):
        val = self._data.get("settings", {}).get("default_dashboard", None)
        if not val:
            try:
                val = self._attr_native_value
            except AttributeError:
                val = self.coordinator.hass.data[DOMAIN][DEFAULT_DISPLAY_OPTIONS].get(
                    "default_dashboard_path", DEFAULT_HOME_ASSISTANT_DASHBOARD
                )
        if len(str(val)) > 255:
            val = str(val)[:250] + "..."
        return val

    async def async_set_value(self, value: str) -> None:
        """Set the default dashboard."""
        self._value = value
        data = {
            "settings": {"default_dashboard": value},
            "display": {"default_dashboard": value},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()
