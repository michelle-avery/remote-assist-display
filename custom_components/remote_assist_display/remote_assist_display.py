"""Remote Assist Display Class."""

import logging

from homeassistant.components.websocket_api import event_message
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry, entity_registry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from packaging.version import parse as parse_version

from .const import DATA_ADDERS, DATA_CONFIG_ENTRY, DATA_DISPLAYS, DOMAIN, MIN_VERSION_BACKLIGHT
from .light import RADBacklightLight
from .select import RADAssistSatelliteSelect
from .sensor import RADIntentSensor, RADSensor
from .switch import RADHideHeaderSwitch, RADHideSidebarSwitch
from .text import DefaultDashboardText, DeviceStorageKeyText

_LOGGER = logging.getLogger(__name__)


class Coordinator(DataUpdateCoordinator):
    """Coordinator class to handle Remote Assist Display data updates."""

    def __init__(self, hass: HomeAssistant, display_id: str) -> None:
        """Initialize the Remote Assist Display Coordinator.

        Args:
            hass: HomeAssistant instance.
            display_id: Identifier for the display.

        """
        super().__init__(hass, _LOGGER, name="Remote Assist Display Coordinator")
        self.display_id = display_id


class RemoteAssistDisplay:
    """Remote Assist Display Class.

    Handles the Home Assistant device corresponding to a Remote Assist Display device.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        display_id: str,
    ) -> None:
        """Initialize the Remote Assist Display device."""
        self.display_id = display_id
        self.coordinator = Coordinator(hass, display_id)
        self.entities = {}
        self.data = {}
        self.settings = {}
        self._connections = []
        self._event_type = hass.data[DOMAIN][DATA_CONFIG_ENTRY].options.get(
            "event_type", None
        )
        self._event_listener = None

        if self._event_type:
            self._set_event_listener()

        self.update_entities(hass)

    def _set_event_listener(self):
        """Set the event listener for the Remote Assist Display device."""

        @callback
        def handle_event(event: Event):
            """Handle the event."""
            if "intent_sensor" not in self.entities:
                return

            event_data = event.data

            # Update the intent sensor for this device if the event came from its corresponding assist satellite
            if (
                event_data.get("device_id")
                == self.entities.get("assist_satellite").satellite_id
            ):
                _LOGGER.debug(
                    "Updating intent sensor for display %s with event data: %s",
                    self.display_id,
                    event_data,
                )
                self.entities.get("intent_sensor").update_from_event(
                    event_data["result"], event_data["device_id"]
                )
            else:
                _LOGGER.debug(
                    "Event from assist satellite %s does not match display %s",
                    event_data.get("device_id"),
                    self.entities.get("assist_satellite").satellite_id,
                )

        # Remove any existing event listener
        if self._event_listener:
            self._event_listener()

        # Set a new event listener
        _LOGGER.debug(
            "Setting event listener for display %s with event type %s",
            self.display_id,
            self._event_type,
        )
        self._event_listener = self.coordinator.hass.bus.async_listen(  # Changed from coordinator.hass to self.hass
            self._event_type, handle_event
        )

    def update(self, hass, new_data):
        """Update the Remote Assist Display device."""
        self.data.update(new_data)
        self.update_entities(hass)
        self.coordinator.async_set_updated_data(self.data)

    def update_settings(self, hass, settings):
        """Update the settings for the Remote Assist Display device."""
        self.settings.update(settings)
        self.update_entities(hass)
        hass.create_task(
            self.send("remote_assist_display/update_settings", settings=self.settings)
        )

    def update_entities(self, hass):
        """Create or update entities for this device."""

        coordinator = self.coordinator
        display_id = self.display_id

        def _assert_display_sensor(type, name, *properties, **kwargs):
            """Create a sensor for this device if needed."""
            if name in self.entities:
                return
            adder = hass.data[DOMAIN][DATA_ADDERS][type]
            cls = {"sensor": RADSensor}[type]
            new = cls(coordinator, display_id, name, *properties, **kwargs)
            adder([new])
            self.entities[name] = new

        _assert_display_sensor("sensor", "current_url", "Current URL", icon="mdi:web")

        if "default_dashboard" not in self.entities:
            adder = hass.data[DOMAIN][DATA_ADDERS]["text"]
            new = DefaultDashboardText(coordinator, display_id, self)
            adder([new])
            self.entities["default_dashboard"] = new

        if "device_storage_key" not in self.entities:
            adder = hass.data[DOMAIN][DATA_ADDERS]["text"]
            new = DeviceStorageKeyText(coordinator, display_id, self)
            adder([new])
            self.entities["device_storage_key"] = new

        if "assist_satellite" not in self.entities:
            adder = hass.data[DOMAIN][DATA_ADDERS]["select"]
            new = RADAssistSatelliteSelect(coordinator, display_id, self)
            adder([new])
            self.entities["assist_satellite"] = new

        if "intent_sensor" not in self.entities:
            adder = hass.data[DOMAIN][DATA_ADDERS]["sensor"]
            new = RADIntentSensor(
                coordinator,
                display_id,
                "intent_sensor",
                "Intent Sensor",
                icon="mdi:message-processing",
            )
            adder([new])
            self.entities["intent_sensor"] = new

        if "hide_header" not in self.entities:
            adder = hass.data[DOMAIN][DATA_ADDERS]["switch"]
            new = RADHideHeaderSwitch(coordinator, display_id, self)
            adder([new])
            self.entities["hide_header"] = new

        if "hide_sidebar" not in self.entities:
            adder = hass.data[DOMAIN][DATA_ADDERS]["switch"]
            new = RADHideSidebarSwitch(coordinator, display_id, self)
            adder([new])
            self.entities["hide_sidebar"] = new

        # Add light entity for backlight control if client version supports it
        client_version = self.data.get("client_version")
        if "light" not in self.entities and client_version and client_version != "unknown":
            try:
                if parse_version(client_version) >= parse_version(MIN_VERSION_BACKLIGHT):
                    _LOGGER.debug(
                        f"Client version {client_version} supports backlight control for {display_id}. Adding light entity."
                    )
                    adder = hass.data[DOMAIN][DATA_ADDERS]["light"]
                    new_light = RADBacklightLight(coordinator, display_id, self)
                    adder([new_light])
                    self.entities["light"] = new_light
                else:
                    _LOGGER.debug(
                        f"Client version {client_version} does not support backlight control for {display_id} (requires {MIN_VERSION_BACKLIGHT})."
                    )
            except Exception as e:
                _LOGGER.error(
                    f"Error parsing client_version for backlight entity for {display_id}: {client_version}, {e}"
                )
        elif "light" in self.entities and \
             (not client_version or client_version == "unknown" or \
              (client_version and parse_version(client_version) < parse_version(MIN_VERSION_BACKLIGHT))):
            _LOGGER.debug(
                f"Client version {client_version} no longer supports backlight for {display_id} or version unknown. Removing light entity."
            )
            er = entity_registry.async_get(hass)
            if self.entities["light"].entity_id:
                er.async_remove(self.entities["light"].entity_id)
            del self.entities["light"]

    @callback
    async def send(self, command, **kwargs):
        """Send a command to the Remote Assist Display device."""
        if self.connection is None:
            return

        for connection, cid in self.connection:
            connection.send_message(event_message(cid, {"command": command, **kwargs}))

    def delete(self, hass):
        """Delete this device."""
        dr = device_registry.async_get(hass)
        er = entity_registry.async_get(hass)

        for e in self.entities.values():
            er.async_remove(e.entity_id)

        self.entities = {}

        device = dr.async_get_device({(DOMAIN, self.display_id)})
        dr.async_remove_device(device.id)

    @property
    def connection(self):
        return self._connections

    def open_connection(self, hass, connection, cid):
        """Open a connection to the Remote Assist Display device."""
        self._connections.append((connection, cid))
        self.update(hass, {"connected": True})

    def close_connection(self, hass, connection):
        """Close a connection to the Remote Assist Display device."""
        self._connections = list(
            filter(lambda v: v[0] != connection, self._connections)
        )
        self.update(hass, {"connected": False})


def get_or_register_display(hass, display_id):
    """Get or create a Remote Assist Display device."""
    displays = hass.data[DOMAIN][DATA_DISPLAYS]
    if display_id in displays:
        return displays[display_id]

    displays[display_id] = RemoteAssistDisplay(hass, display_id)
    return displays[display_id]


def delete_display(hass, display_id):
    """Delete a Remote Assist Display device."""
    display = get_or_register_display(hass, display_id)
    if display:
        display.delete(hass)
        del hass.data[DOMAIN][DATA_DISPLAYS][display_id]
    return display


def get_display_by_connection(hass, connection):
    """Get a Remote Assist Display device by connection."""
    displays = hass.data[DOMAIN][DATA_DISPLAYS]

    for k, v in displays.items():
        if any(c[0] == connection for c in v._connections):
            return v
    return None
