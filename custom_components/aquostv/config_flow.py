"""Config flow for the Sharp Aquos TV integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.selector import BooleanSelector

from .aquos import AquosConnectionError, AquosTV
from .const import (
    CONF_POWER_ON_ENABLED,
    DEFAULT_NAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_POWER_ON_ENABLED,
    DEFAULT_USERNAME,
    DOMAIN,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_POWER_ON_ENABLED, default=DEFAULT_POWER_ON_ENABLED): BooleanSelector(),
    }
)


class AquosConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sharp Aquos TV."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()

            if not await self._async_can_connect(user_input):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Handle import of legacy `media_player: - platform: aquostv` YAML config."""
        await self.async_set_unique_id(f"{import_data[CONF_HOST]}:{import_data[CONF_PORT]}")
        self._abort_if_unique_id_configured()

        if not await self._async_can_connect(import_data):
            return self.async_abort(reason="cannot_connect")

        return self.async_create_entry(title=import_data[CONF_NAME], data=import_data)

    async def _async_can_connect(self, data: dict[str, Any]) -> bool:
        """Return True if the TV answers at the given connection details."""
        tv = AquosTV(
            data[CONF_HOST],
            data[CONF_PORT],
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
        )
        try:
            await tv.power()
        except AquosConnectionError:
            return False
        return True
