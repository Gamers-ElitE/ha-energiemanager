"""Tests for the active home battery regulation and master control switches."""

from datetime import UTC, datetime

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.number import ATTR_VALUE, DOMAIN as NUMBER_DOMAIN, SERVICE_SET_VALUE
from homeassistant.components.select import ATTR_OPTION, DOMAIN as SELECT_DOMAIN, SERVICE_SELECT_OPTION
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall


async def test_battery_and_master_switches_toggle(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Master control and battery control switches are created and toggle coordinator state."""
    coordinator = init_integration.runtime_data.coordinator

    master_switch = "switch.energiemanager_energiemanager_master_control"
    battery_switch = "switch.energiemanager_battery_zero_feed_in_regulation"

    assert hass.states.get(master_switch) is not None
    assert hass.states.get(master_switch).state == "on"
    assert coordinator.master_control_enabled is True

    assert hass.states.get(battery_switch) is not None
    assert hass.states.get(battery_switch).state == "on"
    assert coordinator.battery_control_enabled is True

    # Turn off master control
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: master_switch},
        blocking=True,
    )
    assert coordinator.master_control_enabled is False
    assert hass.states.get(master_switch).state == "off"

    # Turn back on
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: master_switch},
        blocking=True,
    )
    assert coordinator.master_control_enabled is True
    assert hass.states.get(master_switch).state == "on"

    # Turn off battery control
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: battery_switch},
        blocking=True,
    )
    assert coordinator.battery_control_enabled is False
    assert hass.states.get(battery_switch).state == "off"


async def test_active_battery_charge_regulation_on_surplus(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Coordinator detects surplus and sets battery to charge with calculated watts."""
    coordinator = init_integration.runtime_data.coordinator

    # Set up simulated Anker Solarbank entities
    flow_select = "select.anker_solix_solarbank_max_ac_345_leistungsfluss"
    power_number = "number.anker_solix_solarbank_max_ac_345_leistungssteuerung"
    charge_sensor = "sensor.anker_solix_solarbank_max_ac_345_batterieladeleistung"
    discharge_sensor = "sensor.anker_solix_solarbank_max_ac_345_batterieentladeleistung"

    hass.states.async_set(flow_select, "discharge")
    hass.states.async_set(power_number, "0", {"max": 3200, "max_discharge_power": 3000})
    hass.states.async_set(charge_sensor, "0")
    hass.states.async_set(discharge_sensor, "0")

    flow_calls: list[ServiceCall] = []
    power_calls: list[ServiceCall] = []

    async def mock_flow_call(call: ServiceCall) -> None:
        flow_calls.append(call)
        hass.states.async_set(flow_select, call.data[ATTR_OPTION])

    async def mock_power_call(call: ServiceCall) -> None:
        power_calls.append(call)
        hass.states.async_set(power_number, str(call.data[ATTR_VALUE]), {"max": 3200, "max_discharge_power": 3000})

    hass.services.async_register(SELECT_DOMAIN, SERVICE_SELECT_OPTION, mock_flow_call)
    hass.services.async_register(NUMBER_DOMAIN, SERVICE_SET_VALUE, mock_power_call)

    # Grid export: -1000 W (surplus)
    hass.states.async_set("sensor.grid_power", "-1000")
    hass.states.async_set("sensor.battery_soc", "50")

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Flow should be switched to "charge"
    assert any(c.data.get(ATTR_OPTION) == "charge" for c in flow_calls)

    # Target power = 1000 - 20 (charge puffer) = 980 W
    assert any(c.data.get(ATTR_VALUE) == 980.0 for c in power_calls)
    assert coordinator.data.get("battery_target_mode") == "charge"
    assert coordinator.data.get("battery_target_power") == 980.0


async def test_active_battery_discharge_regulation_on_import(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Coordinator detects grid import and commands battery to discharge covering the load."""
    coordinator = init_integration.runtime_data.coordinator

    flow_select = "select.anker_solix_solarbank_max_ac_345_leistungsfluss"
    power_number = "number.anker_solix_solarbank_max_ac_345_leistungssteuerung"

    hass.states.async_set(flow_select, "charge")
    hass.states.async_set(power_number, "0", {"max": 3200, "max_discharge_power": 3000})

    flow_calls: list[ServiceCall] = []
    power_calls: list[ServiceCall] = []

    async def mock_flow_call(call: ServiceCall) -> None:
        flow_calls.append(call)
        hass.states.async_set(flow_select, call.data[ATTR_OPTION])

    async def mock_power_call(call: ServiceCall) -> None:
        power_calls.append(call)
        hass.states.async_set(power_number, str(call.data[ATTR_VALUE]), {"max": 3200, "max_discharge_power": 3000})

    hass.services.async_register(SELECT_DOMAIN, SERVICE_SELECT_OPTION, mock_flow_call)
    hass.services.async_register(NUMBER_DOMAIN, SERVICE_SET_VALUE, mock_power_call)

    # Grid import: +500 W (demand)
    hass.states.async_set("sensor.grid_power", "500")
    hass.states.async_set("sensor.battery_soc", "50")

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # Flow should be switched to "discharge"
    assert any(c.data.get(ATTR_OPTION) == "discharge" for c in flow_calls)

    # Target power = 500 - 15 (discharge puffer) = 485 W
    assert any(c.data.get(ATTR_VALUE) == 485.0 for c in power_calls)
    assert coordinator.data.get("battery_target_mode") == "discharge"
    assert coordinator.data.get("battery_target_power") == 485.0


async def test_battery_deadband_convergence_after_30s(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Within deadband, periodic 30s fine-tuning adjusts power to converge closer to 0 W."""
    coordinator = init_integration.runtime_data.coordinator

    power_number = "number.anker_solix_solarbank_max_ac_345_leistungssteuerung"
    flow_select = "select.anker_solix_solarbank_max_ac_345_leistungsfluss"

    hass.states.async_set(flow_select, "discharge")
    hass.states.async_set(power_number, "300", {"max": 3200, "max_discharge_power": 3000})

    power_calls: list[ServiceCall] = []

    async def mock_power_call(call: ServiceCall) -> None:
        power_calls.append(call)
        hass.states.async_set(power_number, str(call.data[ATTR_VALUE]), {"max": 3200, "max_discharge_power": 3000})

    hass.services.async_register(NUMBER_DOMAIN, SERVICE_SET_VALUE, mock_power_call)

    # Grid import is 20 W (within +-25 W deadband)
    hass.states.async_set("sensor.grid_power", "20")
    hass.states.async_set("sensor.battery_soc", "50")

    # Set last adjustment to 10 seconds ago -> should not trigger within deadband
    now_utc = datetime(2026, 11, 1, 12, 0, 10, tzinfo=UTC)
    coordinator._last_battery_adjustment = datetime(2026, 11, 1, 12, 0, 0, tzinfo=UTC)  # noqa: SLF001

    await coordinator._async_update_battery_power(now_utc=now_utc, grid_raw=20.0, battery_soc=50.0)  # noqa: SLF001
    assert len(power_calls) == 0

    # Advance time to 35 seconds after last adjustment -> should trigger fine-tune!
    later_utc = datetime(2026, 11, 1, 12, 0, 35, tzinfo=UTC)
    await coordinator._async_update_battery_power(now_utc=later_utc, grid_raw=20.0, battery_soc=50.0)  # noqa: SLF001
    assert len(power_calls) == 1


async def test_master_control_disabled_prevents_actuator_calls(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """When master control is disabled, no actuator commands are sent."""
    coordinator = init_integration.runtime_data.coordinator

    # Turn off master control
    coordinator.master_control_enabled = False

    power_number = "number.anker_solix_solarbank_max_ac_345_leistungssteuerung"
    flow_select = "select.anker_solix_solarbank_max_ac_345_leistungsfluss"

    hass.states.async_set(flow_select, "discharge")
    hass.states.async_set(power_number, "0", {"max": 3200, "max_discharge_power": 3000})

    calls: list[ServiceCall] = []

    async def mock_call(call: ServiceCall) -> None:
        calls.append(call)

    hass.services.async_register(SELECT_DOMAIN, SERVICE_SELECT_OPTION, mock_call)
    hass.services.async_register(NUMBER_DOMAIN, SERVICE_SET_VALUE, mock_call)

    hass.states.async_set("sensor.grid_power", "-2000")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    # No calls sent
    assert len(calls) == 0
