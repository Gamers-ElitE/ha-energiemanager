"""Sensor entity for sam_energiemanager."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.sensor import RestoreSensor, SensorEntityDescription
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.typing import StateType


@dataclass(frozen=True, kw_only=True)
class EnergiemanagerSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor and how to read it from coordinator data."""

    value_fn: Callable[[dict[str, Any]], StateType]
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


_RESTORABLE_KEYS = frozenset(
    {
        "ev_solar_lifetime_kwh",
        "ev_grid_lifetime_kwh",
        "last_session_summary",
        "daily_home_kwh",
        "daily_pv_kwh",
        "daily_grid_import_kwh",
        "daily_grid_export_kwh",
    }
)


class EnergiemanagerSensor(RestoreSensor, EnergiemanagerEntity):
    """Sensor backed by one value in the coordinator payload."""

    entity_description: EnergiemanagerSensorEntityDescription
    _unrecorded_attributes = frozenset({"session_id", "start_soc", "end_soc", "duration_minutes"})

    async def async_added_to_hass(self) -> None:
        """Restore lifetime and daily energy counters across Home Assistant restarts."""
        await super().async_added_to_hass()
        key = self.entity_description.key
        if key not in _RESTORABLE_KEYS:
            return
        last_state = await self.async_get_last_state()
        if last_state is None or last_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return
        if key == "last_session_summary":
            self.coordinator.restore_sensor_value(
                key,
                last_state.state,
                attributes=dict(last_state.attributes),
                last_updated=last_state.last_updated,
            )
            return
        try:
            num_val = float(last_state.state)
        except TypeError, ValueError:
            return
        self.coordinator.restore_sensor_value(key, num_val, last_updated=last_state.last_updated)

    @property
    def native_value(self) -> StateType:
        """Return the value read from coordinator data."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return optional extra state attributes for the sensor."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data)
