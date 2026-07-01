from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_EXPECTED_BOTTLES_PER_TANK,
    DEFAULT_EXPECTED_BOTTLES_PER_TANK,
    DOMAIN,
)


class Co2CarbonatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="CO₂ Carbonator"): str,
                vol.Optional(
                    CONF_EXPECTED_BOTTLES_PER_TANK,
                    default=DEFAULT_EXPECTED_BOTTLES_PER_TANK,
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return Co2CarbonatorOptionsFlow(config_entry)


class Co2CarbonatorOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({})
        return self.async_show_form(step_id="init", data_schema=schema)
