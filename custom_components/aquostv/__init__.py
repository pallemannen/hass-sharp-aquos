"""The Sharp Aquos TV integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant

from .aquos import AquosTV
from .const import CONF_POWER_ON_ENABLED
from .coordinator import AquosDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER, Platform.SENSOR]

type AquosConfigEntry = ConfigEntry[AquosDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: AquosConfigEntry) -> bool:
    """Set up Sharp Aquos TV from a config entry."""
    tv = AquosTV(
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = AquosDataUpdateCoordinator(
        hass, tv, entry.data.get(CONF_POWER_ON_ENABLED, False)
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: AquosConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
