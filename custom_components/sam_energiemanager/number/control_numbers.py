"""Control number entities for sam_energiemanager."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from custom_components.sam_energiemanager.const import EV_MAX_CURRENT_A, EV_MIN_CURRENT_A
from custom_components.sam_energiemanager.coordinator import EnergiemanagerDataUpdateCoordinator
from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.number import NumberDeviceClass, NumberEntityDescription, NumberMode, RestoreNumber
from homeassistant.const import (
    CURRENCY_EURO,
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)


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
    EnergiemanagerNumberEntityDescription(
        key="ema_alpha",
        translation_key="ema_alpha",
        entity_category=EntityCategory.CONFIG,
        native_min_value=0.05,
        native_max_value=1.0,
        native_step=0.05,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ema_alpha"),
        set_fn=lambda coord, val: coord.async_set_parameter("ema_alpha", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="deadband_watts",
        translation_key="deadband_watts",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=10,
        native_max_value=300,
        native_step=10,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("deadband_watts"),
        set_fn=lambda coord, val: coord.async_set_parameter("deadband_watts", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="battery_lock_threshold_watts",
        translation_key="battery_lock_threshold_watts",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=100,
        native_max_value=1000,
        native_step=50,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("battery_lock_threshold_watts"),
        set_fn=lambda coord, val: coord.async_set_parameter("battery_lock_threshold_watts", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="battery_lock_release_seconds",
        translation_key="battery_lock_release_seconds",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=0,
        native_max_value=600,
        native_step=10,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("battery_lock_release_seconds"),
        set_fn=lambda coord, val: coord.async_set_parameter("battery_lock_release_seconds", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="ac_buffer_min_surplus_watts",
        translation_key="ac_buffer_min_surplus_watts",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=200,
        native_max_value=2000,
        native_step=50,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ac_buffer_min_surplus_watts"),
        set_fn=lambda coord, val: coord.async_set_parameter("ac_buffer_min_surplus_watts", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="ac_buffer_max_surplus_watts",
        translation_key="ac_buffer_max_surplus_watts",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=500,
        native_max_value=3000,
        native_step=50,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ac_buffer_max_surplus_watts"),
        set_fn=lambda coord, val: coord.async_set_parameter("ac_buffer_max_surplus_watts", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="ac_buffer_temp_offset",
        translation_key="ac_buffer_temp_offset",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=0.5,
        native_max_value=5.0,
        native_step=0.5,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ac_buffer_temp_offset"),
        set_fn=lambda coord, val: coord.async_set_parameter("ac_buffer_temp_offset", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="ac_buffer_min_hold_minutes",
        translation_key="ac_buffer_min_hold_minutes",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=5,
        native_max_value=60,
        native_step=5,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ac_buffer_min_hold_minutes"),
        set_fn=lambda coord, val: coord.async_set_parameter("ac_buffer_min_hold_minutes", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="ac_auto_heat_max_outdoor_temp",
        translation_key="ac_auto_heat_max_outdoor_temp",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=0.0,
        native_max_value=20.0,
        native_step=0.5,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ac_auto_heat_max_outdoor_temp"),
        set_fn=lambda coord, val: coord.async_set_parameter("ac_auto_heat_max_outdoor_temp", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="dhw_min_surplus_watts",
        translation_key="dhw_min_surplus_watts",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=200,
        native_max_value=1500,
        native_step=50,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("dhw_min_surplus_watts"),
        set_fn=lambda coord, val: coord.async_set_parameter("dhw_min_surplus_watts", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="dhw_target_temp",
        translation_key="dhw_target_temp",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=45.0,
        native_max_value=60.0,
        native_step=1.0,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("dhw_target_temp"),
        set_fn=lambda coord, val: coord.async_set_parameter("dhw_target_temp", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="dhw_stop_temp",
        translation_key="dhw_stop_temp",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=40.0,
        native_max_value=58.0,
        native_step=1.0,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("dhw_stop_temp"),
        set_fn=lambda coord, val: coord.async_set_parameter("dhw_stop_temp", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="dhw_min_temp",
        translation_key="dhw_min_temp",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=35.0,
        native_max_value=50.0,
        native_step=1.0,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("dhw_min_temp"),
        set_fn=lambda coord, val: coord.async_set_parameter("dhw_min_temp", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="ev_min_surplus_watts",
        translation_key="ev_min_surplus_watts",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=600,
        native_max_value=2500,
        native_step=20,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ev_min_surplus_watts"),
        set_fn=lambda coord, val: coord.async_set_parameter("ev_min_surplus_watts", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="ev_cloud_hysteresis_seconds",
        translation_key="ev_cloud_hysteresis_seconds",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=0,
        native_max_value=900,
        native_step=30,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ev_cloud_hysteresis_seconds"),
        set_fn=lambda coord, val: coord.async_set_parameter("ev_cloud_hysteresis_seconds", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="ev_wakeup_delay_seconds",
        translation_key="ev_wakeup_delay_seconds",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=1,
        native_max_value=60,
        native_step=1,
        mode=NumberMode.SLIDER,
        value_fn=lambda data: data.get("ev_wakeup_delay_seconds"),
        set_fn=lambda coord, val: coord.async_set_parameter("ev_wakeup_delay_seconds", val),
    ),
    EnergiemanagerNumberEntityDescription(
        key="electricity_price",
        translation_key="electricity_price",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.MONETARY,
        native_unit_of_measurement=f"{CURRENCY_EURO}/kWh",
        native_min_value=0.0,
        native_max_value=1.0,
        native_step=0.01,
        mode=NumberMode.BOX,
        value_fn=lambda data: data.get("electricity_price"),
        set_fn=lambda coord, val: coord.async_set_parameter("electricity_price", val),
    ),
)


class EnergiemanagerNumber(RestoreNumber, EnergiemanagerEntity):
    """Number entity for configuring cascade and EV charging thresholds."""

    entity_description: EnergiemanagerNumberEntityDescription

    async def async_added_to_hass(self) -> None:
        """Restore the last user-configured value across Home Assistant restarts."""
        await super().async_added_to_hass()
        if (last_data := await self.async_get_last_number_data()) is not None and last_data.native_value is not None:
            await self.coordinator.async_set_parameter(
                self.entity_description.key,
                float(last_data.native_value),
                refresh=False,
            )

    @property
    def native_value(self) -> float | None:
        """Return the current number value from coordinator data."""
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        """Update the setting on the coordinator."""
        await self.entity_description.set_fn(self.coordinator, value)
