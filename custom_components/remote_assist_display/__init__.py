"""The Remote Assist Display integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .http_api import RegistrationsView, ConfigurationView
from .remote_assist_display import RemoteAssistDisplay
from .service import async_setup_services

PLATFORMS = [Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the Remote Assist Display component."""
    hass.http.register_view(RegistrationsView)
    hass.http.register_view(ConfigurationView)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Remote Assist Display from a config entry."""
    dr = device_registry.async_get(hass)
    device = dr.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, entry.unique_id)}
    )

    rad = RemoteAssistDisplay(hass, entry, device)
    if not hass.data.get(DOMAIN):
        hass.data[DOMAIN] = {}
        async_setup_services(hass)

    hass.data[DOMAIN][entry.entry_id] = rad

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
