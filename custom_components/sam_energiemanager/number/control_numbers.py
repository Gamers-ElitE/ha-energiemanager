"""Control number entities for sam_energiemanager."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from custom_components.sam_energiemanager.const import EV_MAX_CURRENT_A, EV_MIN_CURRENT_A
from custom_components.sam_energiemanager.coordinator import EnergiemanagerDataUpdateCoordinator
from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent


@dataclass(frozen=True, kw_only=True)
class EnergiemanagerNumberEntityDescription(NumberEntityDescription):
    """Describes a configurable number entity for Energiemanager."""

    value_fn: Callable[[dict[str, Any]], float | None]
    set_fn: Callable[[EnergiemanagerDataUpdateCoordinator, float], Awaitable[None]]


ENTITY_DESCRIPTIONS: tuple[EnergiemanagerNumberEntityDescription, ...] = (
    EnergiemanagerNumberEntityDescription(
        key="battery_reserve_soc",
        translation_key="battery_reserve_soc",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("battery_reserve_soc"),
        set_fn=lambda coord, val: coord.async_set_battery_reserve_soc(val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="tesla_max_current",
        translation_key="tesla_max_current",
        device_class=NumberDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=EV_MIN_CURRENT_A,
        native_max_value=EV_MAX_CURRENT_A,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("tesla_max_current"),
        set_fn=lambda coord, val: coord.async_set_tesla_max_current(val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="tesla_target_soc",
        translation_key="tesla_target_soc",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=50,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("tesla_target_soc"),
        set_fn=lambda coord, val: coord.async_set_tesla_target_soc(val),
    ),
)


class EnergiemanagerNumber(NumberEntity, EnergiemanagerEntity):
    """Number entity for configuring cascade and EV charging thresholds."""

    entity_description: EnergiemanagerNumberEntityDescription

    @property
    def native_value(self) -> float | None:
        """Return the current number value from coordinator data."""
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        """Update the setting on the coordinator."""
        await self.entity_description.set_fn(self.coordinator, value)
