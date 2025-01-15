from homeassistant.components.text import RestoreText
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from typing import Any
from .entities import RADEntity
from .const import DOMAIN, DATA_ADDERS, DATA_STORE


async def async_setup_platform(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Any = None,
) -> None:
    """Set up the text platform."""
    hass.data[DOMAIN][DATA_ADDERS]["text"] = async_add_entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up text entities."""
    await async_setup_platform(hass, {}, async_add_entities)


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
            return
        # If the entity state was last unknown, the native value here will still be None,
        # so restore it from settings.
        if not last_text_data.native_value:
            self._attr_native_value = (
                self.hass.data[DOMAIN][DATA_STORE]
                .get_display(self.display_id)
                .asdict()
                .get("settings", {})
                .get("default_dashboard", None)
            )
        else:
            self._attr_native_value = last_text_data.native_value

    @property
    def native_value(self):
        val = self._data.get("display", {}).get("default_dashboard", None)
        if not val:
            val = self._attr_native_value
        if len(str(val)) > 255:
            val = str(val)[:250] + "..."
        return val

    async def async_set_value(self, value: str) -> None:
        """Set the default dashboard both in the entities value and in the settings store."""
        self._value = value
        data = {
            "settings": {"default_dashboard": value},
            "display": {"default_dashboard": value},
        }
        # self.display.update_settings(self.hass, data)
        store = self.hass.data[DOMAIN][DATA_STORE]
        await store.async_set_display(self.display.display_id, **data)
        self._data.update(data)
        self.async_write_ha_state()
