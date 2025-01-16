import logging
import attr

from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "remote_assist_display.storage"


@attr.s
class SettingsStoreData:
    """Class to hold settings data."""

    default_dashboard = attr.ib(type=str, default=None)

    @classmethod
    def from_dict(cls, data: dict):
        """Create Settings Store instance from a dictionary."""
        return cls(**data)

    def asdict(self):
        """Convert the Settings Store instance to a dictionary."""
        return attr.asdict(self)


@attr.s
class DisplayStoreData:
    """Class to hold display data."""

    last_seen = attr.ib(type=int, default=0)
    registered = attr.ib(type=bool, default=False)
    settings = attr.ib(type=SettingsStoreData, factory=SettingsStoreData)

    @classmethod
    def from_dict(cls, data: dict):
        """Create Display Store instance from a dictionary."""
        settings = SettingsStoreData.from_dict(data.get("settings", {}))
        return cls(**(data | {"settings": settings}))

    def asdict(self):
        """Convert the Display Store instance to a dictionary."""
        return attr.asdict(self)


@attr.s
class ConfigStoreData:
    displays = attr.ib(type=dict[str:DisplayStoreData], factory=dict)
    version = attr.ib(type=str, default="1.0")
    settings = attr.ib(type=SettingsStoreData, factory=SettingsStoreData)

    @classmethod
    def from_dict(cls, data={}):
        """Create Config Store instance from a dictionary."""
        displays = {
            k: DisplayStoreData.from_dict(v)
            for k, v in data.get("displays", {}).items()
        }
        settings = SettingsStoreData.from_dict(data.get("settings", {}))
        return cls(**(data | {"displays": displays, "settings": settings}))

    def asdict(self):
        """Convert the Config Store instance to a dictionary."""
        return attr.asdict(self)


class RADStore:
    def __init__(self, hass):
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.listeners = []
        self.data = None
        self.dirty = False

    async def async_save(self):
        """Save the data."""
        if self.dirty:
            await self.store.async_save(attr.asdict(self.data))
            self.dirty = False

    async def async_load(self):
        """Load the data."""
        stored = await self.store.async_load()
        if stored:
            self.data = ConfigStoreData.from_dict(stored)
        if not self.data:
            self.data = ConfigStoreData()
            await self.async_save()
        self.dirty = False

    async def async_update(self):
        """Update the data."""
        self.dirty = True
        for listener in self.listeners:
            listener(attr.asdict(self.data))
        await self.async_save()

    def asdict(self):
        """Return the data as a dictionary."""
        return self.data.asdict()

    def add_listener(self, callback):
        """Add a listener."""
        self.listeners.append(callback)

        def remove_listener():
            self.listeners.remove(callback)

        return remove_listener

    def get_display(self, display_id):
        """Get a display."""
        return self.data.displays.get(display_id, DisplayStoreData())

    async def async_set_display(self, display_id, **data):
        """Set a display."""
        display = self.data.displays.get(display_id, DisplayStoreData())
        display.__dict__.update(data)
        self.data.displays[display_id] = display
        await self.async_update()

    async def delete_display(self, display_id):
        """Delete a display."""
        del self.data.displays[display_id]
        await self.async_update()

    def get_global_settings(self):
        """Get global settings."""
        return self.data.settings

    async def async_set_global_settings(self, **data):
        """Set global settings."""
        self.data.settings.__dict__.update(data)
        await self.async_update()
