"""Entities for Remote Assist Display integration."""

import logging

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RADEntity(CoordinatorEntity):
    """Entity class for Remote Assist Display integration."""

    def __init__(self, coordinator, display_id, name, icon=None) -> None:
        """Initialize the Remote Assist Display entity."""
        super().__init__(coordinator)
        self.display_id = display_id
        self._name = name
        self._icon = icon

    @property
    def _data(self):
        return self.coordinator.data or {}

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self.display_id)},
            "name": self.display_id,
        }

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "type": "remote_assist_display",
            "display_id": self.display_id,
        }

    @property
    def available(self):
        """Return if entity is available."""
        return self._data.get("connected", False)

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    @property
    def has_entity_name(self):
        """Return if entity has a name."""
        return True

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self.display_id}-{self._name.replace(' ', '_')}"

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return self._icon
