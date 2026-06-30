from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_EXPECTED_BOTTLES_PER_TANK,
    CONF_SCAN_COOLDOWN_SECONDS,
    CONF_TAG_ID,
    DEFAULT_EXPECTED_BOTTLES_PER_TANK,
    DEFAULT_SCAN_COOLDOWN_SECONDS,
    DOMAIN,
)


class Co2CarbonatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            tag_id = user_input[CONF_TAG_ID].strip()
            if not tag_id:
                errors[CONF_TAG_ID] = "required"
            else:
                await self.async_set_unique_id(tag_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={**user_input, CONF_TAG_ID: tag_id},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="CO₂ Carbonator"): str,
                vol.Required(CONF_TAG_ID): str,
                vol.Optional(CONF_SCAN_COOLDOWN_SECONDS, default=DEFAULT_SCAN_COOLDOWN_SECONDS): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=3600)
                ),
                vol.Optional(CONF_EXPECTED_BOTTLES_PER_TANK, default=DEFAULT_EXPECTED_BOTTLES_PER_TANK): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=1000)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

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

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_COOLDOWN_SECONDS,
                    default=self.config_entry.options.get(
                        CONF_SCAN_COOLDOWN_SECONDS,
                        self.config_entry.data.get(CONF_SCAN_COOLDOWN_SECONDS, DEFAULT_SCAN_COOLDOWN_SECONDS),
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=3600)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
