"""Remote Assist Display Class."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import (
    DeviceEntry,
    async_get as async_get_device_registry,
)
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry


class RemoteAssistDisplay:
    """Remote Assist Display Class."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
    ) -> None:
        """Initialize the Remote Assist Display device."""
        self._hass = hass
        self._configentry = entry
        self._device = device
        self._assist_entity_id = entry.options.get("assist_entity_id")
        self._assist_device_id = None
        self._name = entry.title
        self._host = entry.data.get("host")
        self._port = entry.data.get("port")
        self._event_type = entry.options.get("event_type")
        self._event_listener = None
        self._intent_sensor = None

        if self._assist_entity_id:
            self._get_assist_device_id()

        if self._event_type:
            self._set_event_listener()

    def _get_assist_device_id(self):
        """Get the device ID for the assist satellite."""
        entity_registry = async_get_entity_registry(self._hass)
        assist_entity = entity_registry.async_get(self._assist_entity_id)
        if assist_entity:
            self._assist_device_id = assist_entity.device_id

    def _set_event_listener(self):
        """Set up an event listener for this device."""

        @callback
        def handle_event(event: Event):
            """Handle the event."""
            if not self._intent_sensor:
                return

            event_data = event.data

            # Update the intent sensor for this device if the event came from its corresponding assist satellite
            if event_data.get("device_id") == self._assist_device_id:
                self._intent_sensor.update_from_event(event_data["result"])

        # Remove any existing event listener
        if self._event_listener:
            self._event_listener()

        # Set up a new event listener
        self._event_listener = self._hass.bus.async_listen(
            self._event_type, handle_event
        )

    def set_intent_sensor(self, sensor):
        """Set the intent sensor for this device."""
        self._intent_sensor = sensor

    def update_event_type(self, event_type: str):
        """Update the event type for this device."""
        self._event_type = event_type
        if self._event_type:
            self._set_event_listener()
        elif self._event_listener:
            self._event_listener()
            self._event_listener = None
