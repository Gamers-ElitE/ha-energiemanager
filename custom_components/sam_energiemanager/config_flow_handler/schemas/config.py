"""Config flow schemas for user setup and reconfiguration."""

from collections.abc import Mapping
from typing import Any

import probatio

from custom_components.sam_energiemanager.const import (
    CONF_BATTERY_DISCHARGE_LOCK_SWITCH,
    CONF_BATTERY_POWER_SENSOR,
    CONF_BATTERY_SOC_SENSOR,
    CONF_CLIMATE_ENTITY,
    CONF_EV_AWAKE_BINARY_SENSOR,
    CONF_EV_BLE_CONNECTED_BINARY_SENSOR,
    CONF_EV_CHARGING_SWITCH,
    CONF_EV_CURRENT_NUMBER,
    CONF_EV_PLUGGED_BINARY_SENSOR,
    CONF_EV_POWER_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_WAKEUP_BUTTON,
    CONF_GRID_POWER_SENSOR,
    CONF_OUTDOOR_TEMP_SENSOR,
    CONF_PV_POWER_SENSOR,
    CONF_SOLAR_PEAK_TIME_SENSOR,
    CONF_WATER_HEATER_ENTITY,
    CONF_WATER_TEMP_SENSOR,
)
from homeassistant.helpers import selector

_POWER_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor"),
)
_TEMP_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="temperature"),
)
_BATTERY_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="battery"),
)
_SWITCH_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["switch", "input_boolean", "select"]),
)
_WATER_HEATER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["water_heater", "select"]),
)
_BINARY_OR_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain=["binary_sensor", "sensor", "input_boolean", "device_tracker"]),
)
_NUMBER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="number"),
)
_BUTTON_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="button"),
)
_CLIMATE_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="climate"),
)

_OPTIONAL_ENTITY_SELECTORS: tuple[tuple[str, selector.EntitySelector], ...] = (
    (CONF_BATTERY_SOC_SENSOR, _BATTERY_SENSOR_SELECTOR),
    (CONF_BATTERY_DISCHARGE_LOCK_SWITCH, _SWITCH_SELECTOR),
    (CONF_EV_POWER_SENSOR, _POWER_SENSOR_SELECTOR),
    (CONF_EV_SOC_SENSOR, _BATTERY_SENSOR_SELECTOR),
    (CONF_EV_PLUGGED_BINARY_SENSOR, _BINARY_OR_SENSOR_SELECTOR),
    (CONF_EV_BLE_CONNECTED_BINARY_SENSOR, _BINARY_OR_SENSOR_SELECTOR),
    (CONF_EV_CURRENT_NUMBER, _NUMBER_SELECTOR),
    (CONF_EV_CHARGING_SWITCH, _SWITCH_SELECTOR),
    (CONF_EV_WAKEUP_BUTTON, _BUTTON_SELECTOR),
    (CONF_EV_AWAKE_BINARY_SENSOR, _BINARY_OR_SENSOR_SELECTOR),
    (CONF_CLIMATE_ENTITY, _CLIMATE_SELECTOR),
    (CONF_OUTDOOR_TEMP_SENSOR, _TEMP_SENSOR_SELECTOR),
    (CONF_PV_POWER_SENSOR, _POWER_SENSOR_SELECTOR),
    (CONF_BATTERY_POWER_SENSOR, _POWER_SENSOR_SELECTOR),
    (CONF_WATER_HEATER_ENTITY, _WATER_HEATER_SELECTOR),
    (CONF_WATER_TEMP_SENSOR, _TEMP_SENSOR_SELECTOR),
    (CONF_SOLAR_PEAK_TIME_SENSOR, _POWER_SENSOR_SELECTOR),
)


def get_user_schema(defaults: Mapping[str, Any] | None = None) -> probatio.Schema:
    """
    Build the schema for selecting source entities.

    Args:
        defaults: Previously submitted values used to pre-fill the form.

    Returns:
        The schema for the setup/reconfigure form.

    """
    defaults = defaults or {}
    schema_dict: dict[Any, Any] = {
        probatio.Required(
            CONF_GRID_POWER_SENSOR,
            default=defaults.get(CONF_GRID_POWER_SENSOR, probatio.UNDEFINED),
        ): _POWER_SENSOR_SELECTOR,
    }
    for key, entity_selector in _OPTIONAL_ENTITY_SELECTORS:
        if defaults.get(key):
            schema_dict[probatio.Optional(key, default=defaults[key])] = entity_selector
        else:
            schema_dict[probatio.Optional(key)] = entity_selector

    return probatio.Schema(schema_dict)


__all__ = ["get_user_schema"]
