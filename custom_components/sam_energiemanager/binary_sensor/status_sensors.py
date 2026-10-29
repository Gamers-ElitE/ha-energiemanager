"""Status binary sensors for sam_energiemanager."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.components.binary_sensor.const import BinarySensorDeviceClass


@dataclass(frozen=True, kw_only=True)
class EnergiemanagerBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a binary sensor and how to read it from coordinator data."""

    value_fn: Callable[[dict[str, Any]], bool | None]
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


ENTITY_DESCRIPTIONS: tuple[EnergiemanagerBinarySensorEntityDescription, ...] = (
    EnergiemanagerBinarySensorEntityDescription(
        key="battery_discharge_lock_active",
        translation_key="battery_discharge_lock_active",
        device_class=BinarySensorDeviceClass.LOCK,
        value_fn=lambda data: data.get("battery_discharge_lock_active"),
    ),
    EnergiemanagerBinarySensorEntityDescription(
        key="ac_buffer_active",
        translation_key="ac_buffer_active",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.get("ac_buffer_active"),
        attr_fn=lambda data: {
            "saved_temperature": data.get("ac_saved_temperature"),
            "saved_hvac_mode": data.get("ac_saved_hvac_mode"),
        },
    ),
    EnergiemanagerBinarySensorEntityDescription(
        key="ev_session_active",
        translation_key="ev_session_active",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda data: data.get("ev_session_active"),
        attr_fn=lambda data: {"source_entities": data.get("source_entities", {})},
    ),
)


class EnergiemanagerBinarySensor(BinarySensorEntity, EnergiemanagerEntity):
    """Binary sensor exposing cascade and session status flags."""

    entity_description: EnergiemanagerBinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return the boolean state from coordinator data."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return optional extra state attributes."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data)
