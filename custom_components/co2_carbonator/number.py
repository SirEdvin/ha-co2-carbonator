from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import CarbonatorRuntime
from .const import DOMAIN
from .entity import Co2CarbonatorEntity


DESCRIPTION = NumberEntityDescription(
    key="expected_bottles_per_tank",
    name="Expected Bottles Per Tank",
    icon="mdi:chart-bell-curve",
    native_min_value=0,
    native_max_value=1000,
    native_step=1,
    native_unit_of_measurement="bottles",
    mode=NumberMode.BOX,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    runtime: CarbonatorRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([Co2ExpectedBottlesNumber(runtime)])


class Co2ExpectedBottlesNumber(Co2CarbonatorEntity, NumberEntity):
    entity_description = DESCRIPTION

    def __init__(self, runtime: CarbonatorRuntime) -> None:
        super().__init__(runtime, DESCRIPTION.key, DESCRIPTION.name or DESCRIPTION.key)

    @property
    def native_value(self) -> float:
        return float(self.runtime.state.expected_bottles_per_tank)

    async def async_set_native_value(self, value: float) -> None:
        await self.runtime.async_set_expected_bottles_per_tank(int(value))
