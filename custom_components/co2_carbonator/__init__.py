from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_AMOUNT,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_CURRENT_BOTTLES,
    ATTR_TANK_ID,
    CONF_EXPECTED_BOTTLES_PER_TANK,
    DEFAULT_EXPECTED_BOTTLES_PER_TANK,
    DOMAIN,
    EVENT_BOTTLE_RECORDED,
    EVENT_BOTTLE_UNRECORDED,
    EVENT_TANK_REPLACED,
    PLATFORMS,
    SERVICE_INITIALIZE_TANK,
    SERVICE_RECORD_BOTTLE,
    SERVICE_REPLACE_TANK,
    SERVICE_UNRECORD_BOTTLE,
)

UPDATE_SIGNAL = f"{DOMAIN}_updated"


def _now() -> datetime:
    return dt_util.utcnow().replace(tzinfo=timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = dt_util.parse_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _new_tank_id() -> str:
    return _now().strftime("CO2-%Y-%m-%d-%H%M")


@dataclass
class CarbonatorState:
    tank_id: str = field(default_factory=_new_tank_id)
    tank_started: str = field(default_factory=_now_iso)
    last_bottle_recorded: str | None = None
    bottles_current_tank: int = 0
    bottles_lifetime: int = 0
    tanks_completed: int = 0
    last_completed_tank_bottles: int = 0
    completed_tank_bottles_total: int = 0
    last_completed_tank_id: str | None = None
    last_completed_tank_started: str | None = None
    last_completed_tank_ended: str | None = None
    expected_bottles_per_tank: int = DEFAULT_EXPECTED_BOTTLES_PER_TANK

    def snapshot(self) -> dict[str, Any]:
        return {
            "tank_id": self.tank_id,
            "tank_started": self.tank_started,
            "last_bottle_recorded": self.last_bottle_recorded,
            "bottles_current_tank": self.bottles_current_tank,
            "bottles_lifetime": self.bottles_lifetime,
            "tanks_completed": self.tanks_completed,
            "last_completed_tank_bottles": self.last_completed_tank_bottles,
            "completed_tank_bottles_total": self.completed_tank_bottles_total,
            "last_completed_tank_id": self.last_completed_tank_id,
            "last_completed_tank_started": self.last_completed_tank_started,
            "last_completed_tank_ended": self.last_completed_tank_ended,
            "expected_bottles_per_tank": self.expected_bottles_per_tank,
        }

    def apply_snapshot(self, data: dict[str, Any]) -> None:
        for key in self.snapshot():
            if key in data and data[key] is not None:
                setattr(self, key, data[key])
        self.bottles_current_tank = int(self.bottles_current_tank)
        self.bottles_lifetime = int(self.bottles_lifetime)
        self.tanks_completed = int(self.tanks_completed)
        self.last_completed_tank_bottles = int(self.last_completed_tank_bottles)
        self.completed_tank_bottles_total = int(self.completed_tank_bottles_total)
        self.expected_bottles_per_tank = int(self.expected_bottles_per_tank)


class CarbonatorRuntime:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.state = CarbonatorState(
            expected_bottles_per_tank=int(
                entry.data.get(CONF_EXPECTED_BOTTLES_PER_TANK, DEFAULT_EXPECTED_BOTTLES_PER_TANK)
            )
        )
        self._restored = False

    @property
    def name(self) -> str:
        return self.entry.data.get(CONF_NAME, "CO₂ Carbonator")

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.name,
            "manufacturer": "Local Home Assistant",
            "model": "Manual CO₂ carbonator tracker",
            "sw_version": "0.1.0",
        }

    def restore_once(self, data: dict[str, Any]) -> None:
        if self._restored:
            return
        self.state.apply_snapshot(data)
        self._restored = True

    async def async_record_bottle(self, amount: int = 1) -> None:
        amount = int(amount)
        if amount < 1:
            raise HomeAssistantError("amount must be at least 1")
        now = _now_iso()
        self.state.last_bottle_recorded = now
        self.state.bottles_current_tank += amount
        self.state.bottles_lifetime += amount
        self.hass.bus.async_fire(
            EVENT_BOTTLE_RECORDED,
            {
                "config_entry_id": self.entry.entry_id,
                "tank_id": self.state.tank_id,
                "amount": amount,
                "bottles_current_tank": self.state.bottles_current_tank,
                "recorded_at": now,
            },
        )
        self.async_write_updates()

    async def async_unrecord_bottle(self, amount: int = 1) -> None:
        amount = int(amount)
        if amount < 1:
            raise HomeAssistantError("amount must be at least 1")
        removed = min(amount, self.state.bottles_current_tank, self.state.bottles_lifetime)
        self.state.bottles_current_tank -= removed
        self.state.bottles_lifetime -= removed
        self.hass.bus.async_fire(
            EVENT_BOTTLE_UNRECORDED,
            {
                "config_entry_id": self.entry.entry_id,
                "tank_id": self.state.tank_id,
                "amount": amount,
                "removed": removed,
                "bottles_current_tank": self.state.bottles_current_tank,
                "bottles_lifetime": self.state.bottles_lifetime,
                "unrecorded_at": _now_iso(),
            },
        )
        self.async_write_updates()

    async def async_initialize_tank(self, tank_id: str | None = None, current_bottles: int = 0) -> None:
        now = _now_iso()
        self.state.tank_id = tank_id or _new_tank_id()
        self.state.tank_started = now
        self.state.last_bottle_recorded = None
        self.state.bottles_current_tank = int(current_bottles)
        self.async_write_updates()

    async def async_replace_tank(self, tank_id: str | None = None) -> None:
        now = _now_iso()
        completed = {
            "tank_id": self.state.tank_id,
            "started": self.state.tank_started,
            "ended": now,
            "bottles": self.state.bottles_current_tank,
        }
        self.state.last_completed_tank_id = self.state.tank_id
        self.state.last_completed_tank_started = self.state.tank_started
        self.state.last_completed_tank_ended = now
        self.state.last_completed_tank_bottles = self.state.bottles_current_tank
        self.state.completed_tank_bottles_total += self.state.bottles_current_tank
        self.state.tanks_completed += 1
        self.hass.bus.async_fire(EVENT_TANK_REPLACED, {"config_entry_id": self.entry.entry_id, **completed})
        self.state.tank_id = tank_id or _new_tank_id()
        self.state.tank_started = now
        self.state.bottles_current_tank = 0
        self.state.last_bottle_recorded = None
        self.async_write_updates()

    async def async_set_expected_bottles_per_tank(self, value: int) -> None:
        self.state.expected_bottles_per_tank = int(value)
        self.async_write_updates()

    @property
    def tank_age_days(self) -> float:
        started = _parse_dt(self.state.tank_started)
        if started is None:
            return 0.0
        return round(max((_now() - started).total_seconds(), 0) / 86400, 1)

    @property
    def bottles_per_day_current_tank(self) -> float:
        age_days = self.tank_age_days
        if age_days <= 0:
            return float(self.state.bottles_current_tank)
        return round(self.state.bottles_current_tank / age_days, 2)

    @property
    def average_bottles_per_completed_tank(self) -> float:
        if self.state.tanks_completed <= 0:
            return 0.0
        return round(self.state.completed_tank_bottles_total / self.state.tanks_completed, 1)

    @property
    def estimated_bottles_remaining(self) -> int:
        expected = self.state.expected_bottles_per_tank
        if expected <= 0:
            return 0
        return max(expected - self.state.bottles_current_tank, 0)

    @property
    def tank_usage_percent(self) -> float:
        expected = self.state.expected_bottles_per_tank
        if expected <= 0:
            return 0.0
        return round((self.state.bottles_current_tank / expected) * 100, 1)

    def async_write_updates(self) -> None:
        async_dispatcher_send(self.hass, UPDATE_SIGNAL, self.entry.entry_id)


def _get_runtime(hass: HomeAssistant, config_entry_id: str | None = None) -> CarbonatorRuntime:
    runtimes: dict[str, CarbonatorRuntime] = hass.data.get(DOMAIN, {})
    if config_entry_id:
        if config_entry_id not in runtimes:
            raise HomeAssistantError(f"Unknown CO₂ Carbonator config_entry_id: {config_entry_id}")
        return runtimes[config_entry_id]
    if len(runtimes) == 1:
        return next(iter(runtimes.values()))
    if not runtimes:
        raise HomeAssistantError("No CO₂ Carbonator devices are configured")
    raise HomeAssistantError("Multiple CO₂ Carbonator devices exist; pass config_entry_id")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def record_bottle(call: ServiceCall) -> None:
        runtime = _get_runtime(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        await runtime.async_record_bottle(call.data.get(ATTR_AMOUNT, 1))

    async def unrecord_bottle(call: ServiceCall) -> None:
        runtime = _get_runtime(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        await runtime.async_unrecord_bottle(call.data.get(ATTR_AMOUNT, 1))

    async def replace_tank(call: ServiceCall) -> None:
        runtime = _get_runtime(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        await runtime.async_replace_tank(call.data.get(ATTR_TANK_ID))

    async def initialize_tank(call: ServiceCall) -> None:
        runtime = _get_runtime(hass, call.data.get(ATTR_CONFIG_ENTRY_ID))
        await runtime.async_initialize_tank(
            tank_id=call.data.get(ATTR_TANK_ID),
            current_bottles=call.data.get(ATTR_CURRENT_BOTTLES, 0),
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_BOTTLE,
        record_bottle,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_CONFIG_ENTRY_ID): str,
                vol.Optional(ATTR_AMOUNT, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UNRECORD_BOTTLE,
        unrecord_bottle,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_CONFIG_ENTRY_ID): str,
                vol.Optional(ATTR_AMOUNT, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_REPLACE_TANK,
        replace_tank,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_CONFIG_ENTRY_ID): str,
                vol.Optional(ATTR_TANK_ID): str,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_INITIALIZE_TANK,
        initialize_tank,
        schema=vol.Schema(
            {
                vol.Optional(ATTR_CONFIG_ENTRY_ID): str,
                vol.Optional(ATTR_TANK_ID): str,
                vol.Optional(ATTR_CURRENT_BOTTLES, default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=10000)),
            }
        ),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = CarbonatorRuntime(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
