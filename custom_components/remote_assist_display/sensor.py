"""Remote Asssist Display Sensor."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    rad = hass.data[DOMAIN][config_entry.entry_id]
    sensor = RemoteAssistDisplayIntentSensor(config_entry)
    rad.set_intent_sensor(sensor)
    async_add_entities([sensor])


class RemoteAssistDisplayIntentSensor(SensorEntity):
    """Entity to represent the intent of the most recent conversation event received for this device."""

    entity_description = SensorEntityDescription(
        key="intent",
        icon="mdi:comment-question",
    )

    def __init__(self, config_entry) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        if config_entry.unique_id:
            self._attr_unique_id = (
                f"{config_entry.unique_id}-{self.entity_description.key}"
            )
        else:
            self._attr_unique_id = f"{config_entry.title}-{self.entity_description.key}"
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}
        self._state = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.unique_id)}
        )

    @callback
    def update_from_event(self, result: dict[str, Any]) -> None:
        """Update the sensor state from the event data."""
        self._attr_extra_state_attributes = {"intent_output": result}
        if "speech" in result["response"] and "plain" in result["response"]["speech"]:
            self._attr_native_value = result["response"]["speech"]["plain"].get(
                "speech", ""
            )
        self.async_write_ha_state()
