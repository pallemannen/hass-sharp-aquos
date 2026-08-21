"""Media player platform for the Sharp Aquos TV integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AquosConfigEntry
from .const import CONF_POWER_ON_ENABLED, SOURCES, SOURCES_REVERSE
from .entity import AquosEntity


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
