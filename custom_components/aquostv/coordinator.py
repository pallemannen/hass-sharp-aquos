"""Data update coordinator for the Sharp Aquos TV integration.

Polls every field the media_player and sensor platforms need in a single
pass so entities never issue their own redundant TCP round trips.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .aquos import AquosCommandError, AquosConnectionError, AquosTV
from .const import DOMAIN, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


@dataclass
class AquosData:
    """Snapshot of everything we know about the TV right now."""

    is_on: bool
    volume: int | None = None
    is_muted: bool | None = None
    source_code: int | None = None
    aspect_ratio: int | None = None
    audio_selection: int | None = None
    av_mode: int | None = None
    backlight: int | None = None
    channel: int | None = None
    signal_strength: int | None = None
    model: str | None = None


class AquosDataUpdateCoordinator(DataUpdateCoordinator[AquosData]):
    """Polls the TV on an interval and hands entities a shared snapshot."""

    def __init__(self, hass: HomeAssistant, tv: AquosTV, power_on_enabled: bool) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.tv = tv
        self._power_on_enabled = power_on_enabled
        self._model: str | None = None
        self._warned_fields: set[str] = set()

    def _log_field_failure(self, field: str, err: Exception) -> None:
        """Warn once per field, then drop to debug - a command a given TV
        model doesn't support will fail on every single poll forever, and
        that shouldn't turn into permanent log spam. But the first failure
        needs to be visible (not debug-only) or there's no way to tell a
        genuine problem from a field just being None."""
        if field not in self._warned_fields:
            self._warned_fields.add(field)
            _LOGGER.warning("Could not read %s (won't repeat this warning): %s", field, err)
        else:
            _LOGGER.debug("Could not read %s: %s", field, err)

    async def _async_update_data(self) -> AquosData:
        try:
            is_on = await self.tv.power()
        except AquosConnectionError:
            # Treat unreachable as off rather than failing the whole
            # coordinator - a TV that's fully unplugged/asleep will simply
            # not answer, and that's a legitimate (common) state, not an
            # integration error.
            return AquosData(is_on=False)

        # Keep the TV's "accept power-on over TCP/IP" flag in sync with the
        # config option on every poll, same as upstream did.
        try:
            await self.tv.set_power_on_command_settings(self._power_on_enabled)
        except (AquosConnectionError, AquosCommandError) as err:
            self._log_field_failure("power_on_command_settings", err)

        if not is_on:
            return AquosData(is_on=False, model=self._model)

        if self._model is None:
            try:
                self._model = await self.tv.model()
            except (AquosConnectionError, AquosCommandError) as err:
                self._log_field_failure("model", err)

        data = AquosData(is_on=True, model=self._model)
        for attr, coro in (
            ("volume", self.tv.volume()),
            ("is_muted", self.tv.mute()),
            ("source_code", self.tv.input_source()),
            ("aspect_ratio", self.tv.aspect_ratio()),
            ("audio_selection", self.tv.audio_selection()),
            ("av_mode", self.tv.av_mode()),
            ("backlight", self.tv.backlight()),
            ("channel", self.tv.channel()),
            ("signal_strength", self.tv.signal_strength()),
        ):
            try:
                setattr(data, attr, await coro)
            except (AquosConnectionError, AquosCommandError) as err:
                # Not every model supports every command - leave that field
                # as None rather than failing the whole update.
                self._log_field_failure(attr, err)

        return data
