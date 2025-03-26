"""Switch platform for Remote Assist Display integration."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DATA_ADDERS, DATA_CONFIG_ENTRY, DOMAIN
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


class RADHideHeaderSwitch(RADEntity, SwitchEntity, RestoreEntity):
    """Representation of a switch to hide the header on the display."""

    def __init__(
        self,
        coordinator,
        display_id,
        display,
    ) -> None:
        """Initialize the switch."""
        RADEntity.__init__(self, coordinator, display_id, "Hide Header")
        SwitchEntity.__init__(self)
        RestoreEntity.__init__(self)
        self.display = display
        self._attr_is_on = None

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            restored_state = last_state.state == "on"
            # Sync the restored state with display
            self.display.settings.update(
                {
                    "hide_header": restored_state,
                    "display": {"hide_header": restored_state},
                },
            )
            self._attr_is_on = restored_state
        else:
            # If no previous state, use the config entry default
            config_default = self.coordinator.hass.data[DOMAIN][
                DATA_CONFIG_ENTRY
            ].options.get("hide_header", False)
            self.display.update_settings(
                self.hass,
                {
                    "hide_header": config_default,
                    "display": {"hide_header": config_default},
                },
            )
            self._attr_is_on = config_default
        self.schedule_update_ha_state()

    @property
    def is_on(self):
        """Return the state of the switch."""
        value = self._data.get("hide_header", None)
        if value is not None:
            return value

        try:
            return self._attr_is_on
        except AttributeError:
            return self.coordinator.hass.data[DOMAIN][DATA_CONFIG_ENTRY].options.get(
                "hide_header", False
            )

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        self._attr_is_on = True
        data = {
            "hide_header": True,
            "display": {"hide_header": True},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()
        self.schedule_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        self._attr_is_on = False
        data = {
            "hide_header": False,
            "display": {"hide_header": False},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()
        self.schedule_update_ha_state()


class RADHideSidebarSwitch(RADEntity, SwitchEntity, RestoreEntity):
    """Representation of a switch to hide the sidebar on the display."""

    def __init__(
        self,
        coordinator,
        display_id,
        display,
    ) -> None:
        """Initialize the switch."""
        RADEntity.__init__(self, coordinator, display_id, "Hide Sidebar")
        SwitchEntity.__init__(self)
        RestoreEntity.__init__(self)
        self.display = display
        self._attr_is_on = None

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            restored_state = last_state.state == "on"
            # Sync the restored state with display
            self.display.settings.update(
                {
                    "hide_sidebar": restored_state,
                    "display": {"hide_sidebar": restored_state},
                },
            )
            self._attr_is_on = restored_state
        else:
            # If no previous state, use the config entry default
            config_default = self.coordinator.hass.data[DOMAIN][
                DATA_CONFIG_ENTRY
            ].options.get("hide_sidebar", False)
            self.display.update_settings(
                self.hass,
                {
                    "hide_sidebar": config_default,
                    "display": {"hide_sidebar": config_default},
                },
            )
            self._attr_is_on = config_default

    @property
    def is_on(self):
        """Return the state of the switch."""
        value = self._data.get("hide_sidebar", None)
        if value is not None:
            return value

        try:
            return self._attr_is_on
        except AttributeError:
            return self.coordinator.hass.data[DOMAIN][DATA_CONFIG_ENTRY].options.get(
                "hide_sidebar", False
            )

    async def async_turn_on(self, **kwargs):
        """Turn on the switch."""
        data = {
            "hide_sidebar": True,
            "display": {"hide_sidebar": True},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the switch."""
        data = {
            "hide_sidebar": False,
            "display": {"hide_sidebar": False},
        }
        self.display.update_settings(self.hass, data)
        self._data.update(data)
        self.async_write_ha_state()
