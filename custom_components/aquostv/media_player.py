"""Media player platform for the Sharp Aquos TV integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.media_player import (
    PLATFORM_SCHEMA as MEDIA_PLAYER_PLATFORM_SCHEMA,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_validation as cv, issue_registry as ir
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import AquosConfigEntry
from .const import CONF_POWER_ON_ENABLED, DEFAULT_NAME, DEFAULT_PORT, DOMAIN, SOURCES, SOURCES_REVERSE
from .entity import AquosEntity

_LOGGER = logging.getLogger(__name__)

# Core's original `aquostv` integration's own defaults for fields omitted
# from YAML - NOT this fork's DEFAULT_USERNAME/DEFAULT_PASSWORD/
# DEFAULT_POWER_ON_ENABLED constants, which are deliberately different
# (blank/True) for the interactive UI flow. A faithful import of someone's
# existing YAML has to reproduce what core actually did with it, not this
# fork's newer preferred defaults.
_YAML_DEFAULT_USERNAME = "admin"
_YAML_DEFAULT_PASSWORD = "password"
_YAML_DEFAULT_POWER_ON_ENABLED = False

# Matches core's original `aquostv` PLATFORM_SCHEMA field-for-field, so
# existing `media_player: - platform: aquostv` YAML from that integration
# keeps parsing. `timeout` and `retries` are accepted-and-ignored: this
# implementation doesn't have equivalents for them.
PLATFORM_SCHEMA = MEDIA_PLAYER_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_USERNAME, default=_YAML_DEFAULT_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD, default=_YAML_DEFAULT_PASSWORD): cv.string,
        vol.Optional("timeout"): cv.string,
        vol.Optional("retries"): cv.string,
        vol.Optional(
            CONF_POWER_ON_ENABLED, default=_YAML_DEFAULT_POWER_ON_ENABLED
        ): cv.boolean,
    },
    extra=vol.REMOVE_EXTRA,
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Import a legacy YAML-configured TV into a config entry.

    This platform never adds entities directly - `async_setup_entry` does
    that once the import below lands as a real config entry. This function
    only exists to catch YAML config and migrate it.
    """
    import_data = {
        CONF_HOST: config[CONF_HOST],
        CONF_PORT: config[CONF_PORT],
        CONF_USERNAME: config[CONF_USERNAME],
        CONF_PASSWORD: config[CONF_PASSWORD],
        CONF_NAME: config[CONF_NAME],
        CONF_POWER_ON_ENABLED: config[CONF_POWER_ON_ENABLED],
    }
    issue_id_suffix = f"{config[CONF_HOST]}_{config[CONF_PORT]}"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=import_data,
    )

    if (
        result.get("type") is FlowResultType.ABORT
        and result.get("reason") != "already_configured"
    ):
        ir.async_create_issue(
            hass,
            DOMAIN,
            f"yaml_deprecation_import_issue_{issue_id_suffix}",
            breaks_in_ha_version=None,
            is_fixable=False,
            is_persistent=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="yaml_deprecation_import_issue",
            translation_placeholders={
                "reason": str(result.get("reason")),
                "host": config[CONF_HOST],
            },
        )
        return

    ir.async_create_issue(
        hass,
        DOMAIN,
        f"yaml_deprecation_{issue_id_suffix}",
        breaks_in_ha_version=None,
        is_fixable=False,
        is_persistent=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="yaml_deprecation",
        translation_placeholders={"host": config[CONF_HOST]},
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: AquosConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the media_player entity from a config entry."""
    async_add_entities([AquosMediaPlayer(entry)])


class AquosMediaPlayer(AquosEntity, MediaPlayerEntity):
    """Representation of a Sharp Aquos TV as a media_player."""

    _attr_name = None
    _attr_source_list = list(SOURCES.values())
    _attr_volume_step = 2 / 60

    def __init__(self, entry: AquosConfigEntry) -> None:
        super().__init__(entry.runtime_data, entry.entry_id, entry.data[CONF_NAME])
        self._attr_unique_id = entry.entry_id

        features = (
            MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.PLAY_MEDIA
            | MediaPlayerEntityFeature.NEXT_TRACK
            | MediaPlayerEntityFeature.PREVIOUS_TRACK
        )
        if entry.data.get(CONF_POWER_ON_ENABLED, False):
            features |= MediaPlayerEntityFeature.TURN_ON
        self._attr_supported_features = features

    @property
    def _tv(self):
        return self.coordinator.tv

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.ON if self.coordinator.data.is_on else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        volume = self.coordinator.data.volume
        return volume / 60 if volume is not None else None

    @property
    def is_volume_muted(self) -> bool | None:
        return self.coordinator.data.is_muted

    @property
    def source(self) -> str | None:
        code = self.coordinator.data.source_code
        return SOURCES.get(code) if code is not None else None

    @property
    def media_channel(self) -> str | None:
        channel = self.coordinator.data.channel
        return str(channel) if channel is not None else None

    async def async_turn_on(self) -> None:
        await self._tv.power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self._tv.power(False)
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        await self._tv.volume(round(volume * 60))
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute deterministically (MUTE1/MUTE2), not a blind toggle."""
        await self._tv.mute(mute)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        code = SOURCES_REVERSE.get(source)
        if code is not None:
            await self._tv.input_source(code)
            await self.coordinator.async_request_refresh()

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any) -> None:
        """Direct-tune a channel via play_media(media_type=channel, media_id=<n>)."""
        if media_type == MediaType.CHANNEL:
            await self._tv.channel(int(media_id))
            await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        """Channel up. The TV has no concept of tracks; this is the closest
        standard feature for stepping the tuner, matching how other
        channel-based media players in HA core map this control."""
        await self._tv.channel_up()
        await self.coordinator.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        """Channel down - see async_media_next_track."""
        await self._tv.channel_down()
        await self.coordinator.async_request_refresh()
