from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.restore_state import RestoreEntity

from . import CarbonatorRuntime, _parse_dt
from .const import DOMAIN
from .entity import Co2CarbonatorEntity


@dataclass(frozen=True, kw_only=True)
class Co2SensorDescription(SensorEntityDescription):
    value_fn: Callable[[CarbonatorRuntime], int | float | str | object | None]
    restore_snapshot: bool = False


SENSORS: tuple[Co2SensorDescription, ...] = (
    Co2SensorDescription(key="current_tank_bottles", name="Current Tank Bottles", native_unit_of_measurement="bottles", icon="mdi:bottle-soda-classic-outline", state_class=SensorStateClass.MEASUREMENT, restore_snapshot=True, value_fn=lambda r: r.state.bottles_current_tank),
    Co2SensorDescription(key="lifetime_bottles", name="Lifetime Bottles", native_unit_of_measurement="bottles", icon="mdi:counter", state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda r: r.state.bottles_lifetime),
    Co2SensorDescription(key="completed_tanks", name="Completed Tanks", native_unit_of_measurement="tanks", icon="mdi:gas-cylinder", state_class=SensorStateClass.TOTAL_INCREASING, value_fn=lambda r: r.state.tanks_completed),
    Co2SensorDescription(key="last_completed_tank_bottles", name="Last Completed Tank Bottles", native_unit_of_measurement="bottles", icon="mdi:bottle-soda-classic-outline", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.state.last_completed_tank_bottles),
    Co2SensorDescription(key="average_bottles_per_completed_tank", name="Average Bottles Per Completed Tank", native_unit_of_measurement="bottles/tank", icon="mdi:chart-line", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.average_bottles_per_completed_tank),
    Co2SensorDescription(key="estimated_bottles_remaining", name="Estimated Bottles Remaining", native_unit_of_measurement="bottles", icon="mdi:gauge-low", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.estimated_bottles_remaining),
    Co2SensorDescription(key="tank_usage_percent", name="Tank Usage Percent", native_unit_of_measurement=PERCENTAGE, icon="mdi:gauge", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.tank_usage_percent),
    Co2SensorDescription(key="current_tank_age", name="Current Tank Age", native_unit_of_measurement=UnitOfTime.DAYS, icon="mdi:calendar-clock", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.tank_age_days),
    Co2SensorDescription(key="bottles_per_day_current_tank", name="Bottles Per Day Current Tank", native_unit_of_measurement="bottles/day", icon="mdi:chart-timeline-variant", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda r: r.bottles_per_day_current_tank),
    Co2SensorDescription(key="current_tank_id", name="Current Tank ID", icon="mdi:identifier", value_fn=lambda r: r.state.tank_id),
    Co2SensorDescription(key="tank_started", name="Tank Started", device_class=SensorDeviceClass.TIMESTAMP, icon="mdi:calendar-start", value_fn=lambda r: _parse_dt(r.state.tank_started)),
    Co2SensorDescription(key="last_bottle_recorded", name="Last Bottle Recorded", device_class=SensorDeviceClass.TIMESTAMP, icon="mdi:clock-check-outline", value_fn=lambda r: _parse_dt(r.state.last_bottle_recorded)),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    runtime: CarbonatorRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(Co2CarbonatorSensor(runtime, description) for description in SENSORS)


class Co2CarbonatorSensor(Co2CarbonatorEntity, SensorEntity, RestoreEntity):
    entity_description: Co2SensorDescription

    def __init__(self, runtime: CarbonatorRuntime, description: Co2SensorDescription) -> None:
        super().__init__(runtime, description.key, description.name or description.key)
        self.entity_description = description

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if not self.entity_description.restore_snapshot:
            return
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self.runtime.restore_once(dict(last_state.attributes))
            self.async_write_ha_state()

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.runtime)
