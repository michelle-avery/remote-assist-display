"""Remote Assist Display Select Entities."""

from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, restore_state
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_ADDERS, DOMAIN
from .entities import RADEntity


async def async_setup_platform(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Any = None,
) -> None:
    """Set up the select platform."""
    hass.data[DOMAIN][DATA_ADDERS]["select"] = async_add_entities


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    await async_setup_platform(hass, config_entry, async_add_entities)


class RADAssistSatelliteSelect(RADEntity, SelectEntity, restore_state.RestoreEntity):
    """Select Entity representing the associated assist satellite."""

    def __init__(
        self,
        coordinator,
        display_id,
        display,
    ):
        """Initialize the select."""
        description = SelectEntityDescription(
            key="satellite",
            entity_category=EntityCategory.CONFIG,
            name="Assist Satellite",
        )
        RADEntity.__init__(self, coordinator, display_id, description.name)
        SelectEntity.__init__(self)
        restore_state.RestoreEntity.__init__(self)
        self.display = display
        self._attr_options = []

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        registry = er.async_get(self.hass)

        satellite_entitites = [
            entity_id
            for entity_id, entity in registry.entities.items()
            if entity.domain == "assist_satellite"
        ]

        self._attr_options = sorted(satellite_entitites)

        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state in self._attr_options:
                self._attr_current_option = last_state.state
            else:
                self._attr_current_option = None
        else:
            self._attr_current_option = None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option
        await self.async_write_ha_state()

    @property
    def satellite_id(self):
        """Return the device id matching the assigned assist satellite."""
        if hasattr(self, "_attr_current_option"):
            entity_id = self._attr_current_option
            entity_registry = er.async_get(self.hass)
            assist_entity = entity_registry.entities.get(entity_id)
            if assist_entity:
                return assist_entity.device_id
            return None
        return None
