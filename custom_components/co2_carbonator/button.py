from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import CarbonatorRuntime
from .const import DOMAIN
from .entity import Co2CarbonatorEntity


@dataclass(frozen=True, kw_only=True)
class Co2ButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[CarbonatorRuntime], Awaitable[None]]


BUTTONS: tuple[Co2ButtonDescription, ...] = (
    Co2ButtonDescription(key="record_bottle", name="Record Bottle", icon="mdi:bottle-soda-classic-outline", press_fn=lambda r: r.async_record_bottle()),
    Co2ButtonDescription(key="replace_tank", name="Replace Tank", icon="mdi:gas-cylinder", press_fn=lambda r: r.async_replace_tank()),
    Co2ButtonDescription(key="initialize_current_tank", name="Initialize Current Tank", icon="mdi:restart", press_fn=lambda r: r.async_initialize_tank()),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    runtime: CarbonatorRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(Co2CarbonatorButton(runtime, description) for description in BUTTONS)


class Co2CarbonatorButton(Co2CarbonatorEntity, ButtonEntity):
    entity_description: Co2ButtonDescription

    def __init__(self, runtime: CarbonatorRuntime, description: Co2ButtonDescription) -> None:
        super().__init__(runtime, description.key, description.name or description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        await self.entity_description.press_fn(self.runtime)
