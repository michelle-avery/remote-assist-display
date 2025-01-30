"""Remote Asssist Display Sensor."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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


class RADIntentSensor(RADSensor):
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
        super().__init__(
            coordinator,
            display_id,
            parameter,
            name,
            unit_of_measurement,
            device_class,
            icon,
        )

    @callback
    def update_from_event(self, result: dict[str, Any]) -> None:
        """Update the sensor from an event data."""
        self._attr_extra_state_attributes = {"intent_output": result}
        if "speech" in result["response"] and "plain" in result["response"]["speech"]:
            self._attr_native_value = result["response"]["speech"]["plain"].get(
                "speech", ""
            )
            self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the state of the sensor normall, as opposed to the normal RADSensor."""
        return self._attr_native_value

    @property
    def extra_state_attributes(self):
        """Return the state attributes from this sensor in addition to the ones from its RADSensor parent."""
        super_attributes = super().extra_state_attributes
        intent_sensor_attributes = {}
        if hasattr(self, "_attr_extra_state_attributes"):
            intent_sensor_attributes = self._attr_extra_state_attributes
        return {**super_attributes, **intent_sensor_attributes}
