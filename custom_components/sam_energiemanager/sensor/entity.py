"""Sensor entity for sam_energiemanager."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.typing import StateType


@dataclass(frozen=True, kw_only=True)
class EnergiemanagerSensorEntityDescription(SensorEntityDescription):
    """Describes a sensor and how to read it from coordinator data."""

    value_fn: Callable[[dict[str, Any]], StateType]
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


class EnergiemanagerSensor(SensorEntity, EnergiemanagerEntity):
    """Sensor backed by one value in the coordinator payload."""

    entity_description: EnergiemanagerSensorEntityDescription
    _unrecorded_attributes = frozenset({"session_id", "start_soc", "end_soc", "duration_minutes"})

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
