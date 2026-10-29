"""Shared fixtures for the sam_energiemanager tests."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sam_energiemanager.const import (
    CONF_BATTERY_DISCHARGE_LOCK_SWITCH,
    CONF_BATTERY_SOC_SENSOR,
    CONF_CLIMATE_ENTITY,
    CONF_EV_BLE_CONNECTED_BINARY_SENSOR,
    CONF_EV_CHARGING_SWITCH,
    CONF_EV_CURRENT_NUMBER,
    CONF_EV_PLUGGED_BINARY_SENSOR,
    CONF_EV_POWER_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_WAKEUP_BUTTON,
    CONF_GRID_POWER_SENSOR,
    DOMAIN,
)
from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Load custom integrations in every test."""


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a config entry for this integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Energiemanager",
        unique_id="sensor_grid_power",
        data={
            CONF_GRID_POWER_SENSOR: "sensor.grid_power",
            CONF_BATTERY_SOC_SENSOR: "sensor.battery_soc",
            CONF_BATTERY_DISCHARGE_LOCK_SWITCH: "switch.anker_discharge_disabled",
            CONF_EV_POWER_SENSOR: "sensor.tesla_charging_power",
            CONF_EV_SOC_SENSOR: "sensor.tesla_soc",
            CONF_EV_PLUGGED_BINARY_SENSOR: "binary_sensor.tesla_plugged",
            CONF_EV_BLE_CONNECTED_BINARY_SENSOR: "binary_sensor.tesla_ble_connected",
            CONF_EV_CURRENT_NUMBER: "number.tesla_charging_amps",
            CONF_EV_CHARGING_SWITCH: "switch.tesla_charger",
            CONF_EV_WAKEUP_BUTTON: "button.tesla_wake_up",
            CONF_CLIMATE_ENTITY: "climate.multisplit",
        },
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> MockConfigEntry:
    """
    Set up the integration from a config entry with initial source entity states.

    Returns:
        The config entry, now loaded.

    """
    hass.states.async_set("sensor.grid_power", "-2000")
    hass.states.async_set("sensor.battery_soc", "75")
    hass.states.async_set("switch.anker_discharge_disabled", "off")
    hass.states.async_set("sensor.tesla_charging_power", "0")
    hass.states.async_set("sensor.tesla_soc", "55")
    hass.states.async_set("binary_sensor.tesla_plugged", "on")
    hass.states.async_set("binary_sensor.tesla_ble_connected", "on")

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
