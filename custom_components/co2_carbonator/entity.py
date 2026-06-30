from __future__ import annotations

from typing import Any

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from . import UPDATE_SIGNAL, CarbonatorRuntime


class Co2CarbonatorEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, runtime: CarbonatorRuntime, key: str, name: str) -> None:
        self.runtime = runtime
        self._attr_unique_id = f"{runtime.entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = runtime.device_info

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                UPDATE_SIGNAL,
                self._handle_update_signal,
            )
        )

    def _handle_update_signal(self, entry_id: str) -> None:
        if entry_id == self.runtime.entry.entry_id:
            self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "tank_id": self.runtime.state.tank_id,
            "tank_started": self.runtime.state.tank_started,
            "last_bottle_filled": self.runtime.state.last_bottle_filled,
        }
