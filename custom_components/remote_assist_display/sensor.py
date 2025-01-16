"""Remote Asssist Display Sensor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_ADDERS, DOMAIN
from .entities import RADEntity


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Any = None,
) -> None:
    """Set up the sensor platform."""
    hass.data[DOMAIN][DATA_ADDERS]["sensor"] = async_add_entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    await async_setup_platform(hass, {}, async_add_entities)


class RADSensor(RADEntity, SensorEntity):
    def __init__(
        self,
        coordinator,
        display_id,
        parameter,
        name,
        unit_of_measurement=None,
        device_class=None,
        icon=None,
    ):
        """Initialize the sensor."""
        RADEntity.__init__(self, coordinator, display_id, name, icon)
        SensorEntity.__init__(self)
        self.parameter = parameter
        self._device_class = device_class
        self._unit_of_measurement = unit_of_measurement

    @property
    def native_value(self):
        val = self._data.get("display", {}).get(self.parameter, None)
        if len(str(val)) > 255:
            val = str(val)[:250] + "..."
        return val

    @property
    def device_class(self):
        return self._device_class

    @property
    def native_unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return super().extra_state_attributes
