from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EXPECTED_BOTTLES_PER_TANK,
    CONF_SCAN_COOLDOWN_SECONDS,
    CONF_TAG_ID,
    DEFAULT_EXPECTED_BOTTLES_PER_TANK,
    DEFAULT_SCAN_COOLDOWN_SECONDS,
    DOMAIN,
    EVENT_BOTTLE_FILLED,
    EVENT_TANK_REPLACED,
    PLATFORMS,
)

STORAGE_VERSION = 1
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


@dataclass
class CarbonatorState:
    tank_id: str = ""
    tank_started: str | None = None
    last_bottle_filled: str | None = None
    bottles_current_tank: int = 0
    bottles_lifetime: int = 0
    tanks_completed: int = 0
    last_completed_tank_bottles: int = 0
    completed_tank_bottles_total: int = 0
    last_completed_tank_id: str | None = None
    last_completed_tank_started: str | None = None
    last_completed_tank_ended: str | None = None
    last_scan_at: str | None = None
    expected_bottles_per_tank: int = DEFAULT_EXPECTED_BOTTLES_PER_TANK
    recent_completed_tanks: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "CarbonatorState":
        if not data:
            now = _now_iso()
            return cls(tank_id=_now().strftime("CO2-%Y-%m-%d-%H%M"), tank_started=now)
        defaults = cls()
        clean = {k: data.get(k, getattr(defaults, k)) for k in defaults.__dataclass_fields__}
        return cls(**clean)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tank_id": self.tank_id,
            "tank_started": self.tank_started,
            "last_bottle_filled": self.last_bottle_filled,
            "bottles_current_tank": self.bottles_current_tank,
            "bottles_lifetime": self.bottles_lifetime,
            "tanks_completed": self.tanks_completed,
            "last_completed_tank_bottles": self.last_completed_tank_bottles,
            "completed_tank_bottles_total": self.completed_tank_bottles_total,
            "last_completed_tank_id": self.last_completed_tank_id,
            "last_completed_tank_started": self.last_completed_tank_started,
            "last_completed_tank_ended": self.last_completed_tank_ended,
            "last_scan_at": self.last_scan_at,
            "expected_bottles_per_tank": self.expected_bottles_per_tank,
            "recent_completed_tanks": self.recent_completed_tanks[-20:],
        }


class CarbonatorRuntime:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{entry.entry_id}")
        self.state = CarbonatorState()
        self.unsub_tag_listener = None
        self.unsub_stop_listener = None

    @property
    def name(self) -> str:
        return self.entry.data.get(CONF_NAME, "CO₂ Carbonator")

    @property
    def configured_tag_id(self) -> str:
        return self.entry.data[CONF_TAG_ID]

    @property
    def scan_cooldown_seconds(self) -> int:
        return int(
            self.entry.options.get(
                CONF_SCAN_COOLDOWN_SECONDS,
                self.entry.data.get(CONF_SCAN_COOLDOWN_SECONDS, DEFAULT_SCAN_COOLDOWN_SECONDS),
            )
        )

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": self.name,
            "manufacturer": "Local Home Assistant",
            "model": "Manual NFC CO₂ carbonator tracker",
            "sw_version": "0.1.0",
        }

    async def async_load(self) -> None:
        stored = await self.store.async_load()
        self.state = CarbonatorState.from_dict(stored)
        if not self.state.expected_bottles_per_tank:
            self.state.expected_bottles_per_tank = int(
                self.entry.data.get(
                    CONF_EXPECTED_BOTTLES_PER_TANK,
                    DEFAULT_EXPECTED_BOTTLES_PER_TANK,
                )
            )

    async def async_save(self) -> None:
        await self.store.async_save(self.state.as_dict())
        async_dispatcher_send(self.hass, UPDATE_SIGNAL, self.entry.entry_id)

    async def async_start(self) -> None:
        @callback
        def handle_tag_scanned(event: Event) -> None:
            tag_id = event.data.get("tag_id")
            if tag_id != self.configured_tag_id:
                return
            self.hass.async_create_task(self.async_record_bottle_filled())

        self.unsub_tag_listener = self.hass.bus.async_listen("tag_scanned", handle_tag_scanned)
        self.unsub_stop_listener = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, lambda _event: self.async_stop()
        )

    @callback
    def async_stop(self) -> None:
        if self.unsub_tag_listener:
            self.unsub_tag_listener()
            self.unsub_tag_listener = None
        if self.unsub_stop_listener:
            self.unsub_stop_listener()
            self.unsub_stop_listener = None

    def _scan_in_cooldown(self) -> bool:
        last_scan = _parse_dt(self.state.last_scan_at)
        if last_scan is None:
            return False
        return _now() - last_scan < timedelta(seconds=self.scan_cooldown_seconds)

    async def async_record_bottle_filled(self) -> bool:
        if self._scan_in_cooldown():
            return False
        now = _now_iso()
        self.state.last_scan_at = now
        self.state.last_bottle_filled = now
        self.state.bottles_current_tank += 1
        self.state.bottles_lifetime += 1
        self.hass.bus.async_fire(
            EVENT_BOTTLE_FILLED,
            {
                "config_entry_id": self.entry.entry_id,
                "tank_id": self.state.tank_id,
                "bottle_number_current_tank": self.state.bottles_current_tank,
                "filled_at": now,
            },
        )
        await self.async_save()
        return True

    async def async_initialize_current_tank(self) -> None:
        now = _now_iso()
        self.state.tank_id = _now().strftime("CO2-%Y-%m-%d-%H%M")
        self.state.tank_started = now
        self.state.last_bottle_filled = None
        self.state.bottles_current_tank = 0
        self.state.last_scan_at = None
        await self.async_save()

    async def async_replace_tank(self) -> None:
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
        self.state.recent_completed_tanks.append(completed)
        self.hass.bus.async_fire(EVENT_TANK_REPLACED, {"config_entry_id": self.entry.entry_id, **completed})
        self.state.tank_id = _now().strftime("CO2-%Y-%m-%d-%H%M")
        self.state.tank_started = now
        self.state.bottles_current_tank = 0
        self.state.last_bottle_filled = None
        self.state.last_scan_at = None
        await self.async_save()

    async def async_set_expected_bottles_per_tank(self, value: int) -> None:
        self.state.expected_bottles_per_tank = int(value)
        await self.async_save()

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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = CarbonatorRuntime(hass, entry)
    await runtime.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await runtime.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    runtime: CarbonatorRuntime | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if runtime:
        runtime.async_stop()
        await runtime.async_save()
    return unload_ok
