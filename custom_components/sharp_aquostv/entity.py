"""Shared base entity for the Sharp Aquos TV integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AquosDataUpdateCoordinator


class AquosEntity(CoordinatorEntity[AquosDataUpdateCoordinator]):
    """Base entity tying media_player/sensor entities to one TV device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: AquosDataUpdateCoordinator, entry_id: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            manufacturer="Sharp",
            model=coordinator.data.model if coordinator.data else None,
        )

    def _handle_coordinator_update(self) -> None:
        """Keep the device's model in sync as the coordinator learns it.

        The model is only queried once the TV is confirmed on (see
        AquosDataUpdateCoordinator), so it's commonly still unknown on the
        very first refresh that built _attr_device_info above. Without this,
        a later successful read would update coordinator.data.model but
        never make it back into the entity's device info.
        """
        if self.coordinator.data and self.coordinator.data.model:
            self._attr_device_info["model"] = self.coordinator.data.model
        super()._handle_coordinator_update()
