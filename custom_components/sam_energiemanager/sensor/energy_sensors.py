"""Energy, power, current and WashData session sensors for sam_energiemanager."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower

from .entity import EnergiemanagerSensorEntityDescription

ENTITY_DESCRIPTIONS: tuple[EnergiemanagerSensorEntityDescription, ...] = (
    EnergiemanagerSensorEntityDescription(
        key="grid_power_filtered",
        translation_key="grid_power_filtered",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("grid_power_filtered"),
    ),
    EnergiemanagerSensorEntityDescription(
        key="surplus_power",
        translation_key="surplus_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("surplus_power"),
    ),
    EnergiemanagerSensorEntityDescription(
        key="ev_charging_power",
        translation_key="ev_charging_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("ev_charging_power"),
    ),
    EnergiemanagerSensorEntityDescription(
        key="ev_solar_power",
        translation_key="ev_solar_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("ev_solar_power"),
    ),
    EnergiemanagerSensorEntityDescription(
        key="ev_grid_power",
        translation_key="ev_grid_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("ev_grid_power"),
    ),
    EnergiemanagerSensorEntityDescription(
        key="ev_target_current",
        translation_key="ev_target_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("ev_target_current"),
    ),
    EnergiemanagerSensorEntityDescription(
        key="ev_solar_lifetime_kwh",
        translation_key="ev_solar_lifetime_kwh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        value_fn=lambda data: data.get("ev_solar_lifetime_kwh"),
    ),
    EnergiemanagerSensorEntityDescription(
        key="ev_grid_lifetime_kwh",
        translation_key="ev_grid_lifetime_kwh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        value_fn=lambda data: data.get("ev_grid_lifetime_kwh"),
    ),
    EnergiemanagerSensorEntityDescription(
        key="last_session_summary",
        translation_key="last_session_summary",
        value_fn=lambda data: data.get("last_session_summary"),
        attr_fn=lambda data: data.get("last_session_data", {}),
    ),
)

