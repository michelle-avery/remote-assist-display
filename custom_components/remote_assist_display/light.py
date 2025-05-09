"""Light platform for Remote Assist Display integration."""

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_ADDERS, DOMAIN, LOGGER
from .entities import RADEntity

async def async_setup_platform(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: Any = None,
) -> None:
    """Set up the light platform."""
    hass.data[DOMAIN][DATA_ADDERS]["light"] = async_add_entities
    LOGGER.debug("Remote Assist Display light platform setup")

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: dict,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light entities."""
    await async_setup_platform(hass, config_entry, async_add_entities)

class RADBacklightLight(RADEntity, LightEntity):
    """Representation of a light to control the display's backlight."""

    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(
        self,
        coordinator,
        display_id,
        display,
    ) -> None:
        """Initialize the light."""
        RADEntity.__init__(self, coordinator, display_id, "Backlight")
        LightEntity.__init__(self)
        self.display = display
        LOGGER.debug(f"RADBacklightLight initialized for {display_id}")

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        brightness_val = self._data.get("brightness")
        if brightness_val is None:
            return None 
        return float(brightness_val) > 0

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255.
        
        The client sends brightness as a float between 0.0 and 1.0.
        Home Assistant expects an int between 0 and 255.
        """
        client_brightness = self._data.get("brightness")
        if client_brightness is None:
            return None 
        return round(float(client_brightness) * 255)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        # Determine the brightness for optimistic local state update
        # If ATTR_BRIGHTNESS is provided, use it; otherwise, default to full brightness (255 for HA scale)
        ha_brightness_for_optimistic_update = kwargs.get(ATTR_BRIGHTNESS, 255)
        optimistic_client_brightness_value = ha_brightness_for_optimistic_update / 255.0

        payload_to_client = {}
        if ATTR_BRIGHTNESS in kwargs:
            # Specific brightness requested by HA
            ha_brightness_to_send = kwargs[ATTR_BRIGHTNESS]
            client_brightness_to_send = ha_brightness_to_send / 255.0
            payload_to_client = {"brightness": client_brightness_to_send}
            LOGGER.debug(
                f"Turning on backlight for {self.display_id} to specific HA brightness {ha_brightness_to_send} (client value: {client_brightness_to_send})"
            )
        else:
            # Generic "on" command, client will restore its previous brightness or turn on fully
            payload_to_client = {"brightness": "on"}
            LOGGER.debug(
                f"Turning on backlight for {self.display_id} with generic 'on' command. Optimistic client brightness set to: {optimistic_client_brightness_value}"
            )
            
        self.display.update_settings(self.hass, payload_to_client)
        
        # Optimistically update local state so HA UI reflects the change immediately
        self._data["brightness"] = optimistic_client_brightness_value
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        LOGGER.debug(f"Turning off backlight for {self.display_id}")
        
        data_to_send = {"brightness": "off"}
        self.display.update_settings(self.hass, data_to_send)
        
        # Optimistically update local state
        self._data["brightness"] = 0.0
        self.async_write_ha_state()
