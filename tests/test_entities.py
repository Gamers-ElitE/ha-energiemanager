"""Tests for the Energiemanager entities, cascade logic, and charging session tracking."""

from datetime import UTC, datetime, timedelta

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.sam_energiemanager.const import (
    CHARGING_MODE_FAST,
    CHARGING_MODE_OFF,
    CONF_GRID_POWER_SENSOR,
    DOMAIN,
    EVENT_SESSION_COMPLETED,
)
from custom_components.sam_energiemanager.coordinator.cascade import (
    SessionTracker,
    compute_ema,
    compute_ev_target_current,
    compute_surplus_watts,
    is_within_deadband,
    split_ev_power,
)
from custom_components.sam_energiemanager.utils.dashboard import DASHBOARD_URL_PATH, build_dashboard_config
from homeassistant.components.number import ATTR_VALUE, DOMAIN as NUMBER_DOMAIN, SERVICE_SET_VALUE
from homeassistant.components.select import ATTR_OPTION, DOMAIN as SELECT_DOMAIN, SERVICE_SELECT_OPTION
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Event, HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError


async def test_entities_read_the_coordinator_payload(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Every entity takes its state from the coordinator payload."""
    assert hass.states.get("sensor.energiemanager_grid_power_filtered").state == "-2000.0"
    assert hass.states.get("sensor.energiemanager_pv_surplus_power").state == "2000.0"
    assert hass.states.get("sensor.energiemanager_ev_target_current").state == "8"
    assert hass.states.get("select.energiemanager_ev_charging_mode").state == "pv_surplus"
    assert hass.states.get("switch.energiemanager_thermal_ac_buffer_enabled").state == "off"
    assert hass.states.get("number.energiemanager_battery_priority_reserve_soc").state == "60.0"
    assert hass.states.get("number.energiemanager_tesla_maximum_charging_current").state == "13.0"
    assert hass.states.get("number.energiemanager_tesla_fast_charge_target_soc").state == "80.0"


async def test_battery_priority_blocks_ev_charging(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """When home battery SOC is below reserve SOC, EV surplus charging stays paused."""
    hass.states.async_set("sensor.battery_soc", "40")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("sensor.energiemanager_ev_target_current").state == "0"


async def test_fast_charging_mode_and_auto_stop_at_target_soc(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Fast charge sets max current and automatically switches to off once target SOC is reached."""
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.energiemanager_ev_charging_mode", ATTR_OPTION: CHARGING_MODE_FAST},
        blocking=True,
    )
    assert hass.states.get("sensor.energiemanager_ev_target_current").state == "13"

    hass.states.async_set("sensor.tesla_soc", "80")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("select.energiemanager_ev_charging_mode").state == CHARGING_MODE_OFF
    assert hass.states.get("sensor.energiemanager_ev_target_current").state == "0"


async def test_number_and_switch_controls_update_coordinator(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Changing number and switch entities updates the coordinator state."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.energiemanager_battery_priority_reserve_soc", ATTR_VALUE: 0},
        blocking=True,
    )
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.energiemanager_thermal_ac_buffer_enabled"},
        blocking=True,
    )

    assert hass.states.get("number.energiemanager_battery_priority_reserve_soc").state == "0.0"
    assert hass.states.get("switch.energiemanager_thermal_ac_buffer_enabled").state == "on"


async def test_invalid_charging_mode_raises_translated_error(
    init_integration: MockConfigEntry,
) -> None:
    """Selecting an invalid mode directly on the coordinator raises a translated ServiceValidationError."""
    with pytest.raises(ServiceValidationError) as err:
        await init_integration.runtime_data.coordinator.async_set_charging_mode("turbo")

    assert err.value.translation_key == "invalid_charging_mode"


async def test_config_flow_user_and_reconfigure(hass: HomeAssistant) -> None:
    """Test user setup flow and reconfiguration flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_GRID_POWER_SENSOR: "sensor.main_grid_power"},
    )
    assert result2["type"] == "create_entry"
    assert result2["title"] == "Energiemanager"
    assert result2["data"][CONF_GRID_POWER_SENSOR] == "sensor.main_grid_power"


def test_cascade_math_and_session_tracker() -> None:
    """Verify EMA, deadband, 1-phase current calculation, and charging session completion."""
    ema1 = compute_ema(-1000.0, None)
    assert ema1 == -1000.0
    ema2 = compute_ema(-2000.0, ema1)
    assert ema2 == pytest.approx(-1350.0)

    assert is_within_deadband(-60.0) is True
    assert is_within_deadband(61.0) is False
    assert compute_surplus_watts(-1500.0) == 1500.0
    assert compute_surplus_watts(200.0) == 0.0

    # 1-phase 230 V: (690 + 0) / 230 = 3 A; (1380 + 0) / 230 = 6 A; (4000 + 0) / 230 = 17 -> clamped to 13 A
    assert compute_ev_target_current(690.0, 0.0, 13) == 3
    assert compute_ev_target_current(1380.0, 0.0, 13) == 6
    assert compute_ev_target_current(4000.0, 0.0, 13) == 13

    # Power split: EV drawing 2300 W while grid imports 500 W -> 1800 W solar, 500 W grid
    solar_w, grid_w = split_ev_power(2300.0, 500.0)
    assert solar_w == 1800.0
    assert grid_w == 500.0

    # Session tracker lifecycle
    tracker = SessionTracker()
    t0 = datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(hours=1)
    t2 = t1 + timedelta(minutes=30)

    _, _, event0 = tracker.update(
        ev_watts=2300.0,
        grid_raw_watts=300.0,
        ev_soc=40.0,
        dt_hours=0.5,
        price_eur_per_kwh=0.30,
        now_utc=t0,
    )
    assert event0 is None
    assert tracker.active is True

    _, _, event1 = tracker.update(
        ev_watts=2300.0,
        grid_raw_watts=300.0,
        ev_soc=50.0,
        dt_hours=1.0,
        price_eur_per_kwh=0.30,
        now_utc=t1,
    )
    assert event1 is None

    _, _, event2 = tracker.update(
        ev_watts=0.0,
        grid_raw_watts=-500.0,
        ev_soc=55.0,
        dt_hours=0.5,
        price_eur_per_kwh=0.30,
        now_utc=t2,
    )
    assert event2 is not None
    assert tracker.active is False
    assert event2["start_soc"] == 40.0
    assert event2["end_soc"] == 55.0
    assert event2["energy_solar_kwh"] == pytest.approx(3.0)
    assert event2["energy_grid_kwh"] == pytest.approx(0.45)
    assert event2["energy_total_kwh"] == pytest.approx(3.45)


async def test_session_completed_event_fired(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Completing a charging session fires the sam_energiemanager_session_completed event."""
    events: list[Event] = []
    hass.bus.async_listen(EVENT_SESSION_COMPLETED, events.append)

    hass.states.async_set("sensor.tesla_charging_power", "2300")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    hass.states.async_set("sensor.tesla_charging_power", "0")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(events) == 1
    assert "energy_total_kwh" in events[0].data
    assert "solar_percentage" in events[0].data


async def test_kw_power_sensor_auto_converts_to_watts(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Power sensors reporting in kW (like Tesla BLE charger_power) are converted to W."""
    hass.states.async_set(
        "sensor.tesla_charging_power",
        "2.3",
        {"unit_of_measurement": "kW"},
    )
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("sensor.energiemanager_ev_charging_power").state == "2300.0"


async def test_ac_buffer_shifts_and_restores_climate_temperature(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Thermal AC buffer shifts climate target temp by +2.5 °C in heat mode and restores it when disabled."""
    calls: list[ServiceCall] = []
    hass.services.async_register("climate", "set_temperature", calls.append)
    hass.states.async_set(
        "climate.multisplit",
        "heat",
        {"temperature": 20.0, "min_temp": 10.0, "max_temp": 31.0},
    )
    # From initial -2000 W, a 0 W reading yields EMA = -1300 W (1300 W surplus, inside 500-1350 W window)
    hass.states.async_set("sensor.grid_power", "0")

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.energiemanager_thermal_ac_buffer_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data["temperature"] == 22.5
    assert init_integration.runtime_data.coordinator.data["ac_saved_temperature"] == 20.0

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.energiemanager_thermal_ac_buffer_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(calls) == 2
    assert calls[1].data["temperature"] == 20.0
    assert init_integration.runtime_data.coordinator.data["ac_saved_temperature"] is None


async def test_threshold_numbers_status_binary_sensors_and_dashboard(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Verify threshold number entities, status binary sensors, and built-in dashboard generation."""
    assert hass.states.get("number.energiemanager_ema_smoothing_factor").state == "0.35"
    assert hass.states.get("number.energiemanager_symmetric_deadband").state == "60.0"
    assert hass.states.get("number.energiemanager_ac_buffer_temperature_offset").state == "2.5"
    assert hass.states.get("binary_sensor.energiemanager_battery_discharge_lock_active").state == "off"
    assert hass.states.get("binary_sensor.energiemanager_thermal_ac_buffer_active").state == "off"
    assert hass.states.get("binary_sensor.energiemanager_ev_charging_session_active").state == "off"

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.energiemanager_symmetric_deadband", ATTR_VALUE: 100},
        blocking=True,
    )
    assert hass.states.get("number.energiemanager_symmetric_deadband").state == "100.0"

    dashboard_cfg = build_dashboard_config(hass, init_integration)
    assert dashboard_cfg["title"] == "Energiemanager"
    assert len(dashboard_cfg["views"]) == 3
    assert DASHBOARD_URL_PATH == "sam-energiemanager"


async def test_ev_unplugged_or_away_blocks_charging(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """When the Tesla is unplugged or away (BLE disconnected), EV charging is blocked."""
    hass.states.async_set("binary_sensor.tesla_plugged", "off")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("sensor.energiemanager_ev_target_current").state == "0"


async def test_ac_auto_heat_starts_when_off_and_cold_outside_and_restores_off(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """When climate is off and outdoor temp <= threshold, auto-heat turns it on in heat mode and restores off."""
    hvac_calls: list[ServiceCall] = []
    temp_calls: list[ServiceCall] = []
    hass.services.async_register("climate", "set_hvac_mode", hvac_calls.append)
    hass.services.async_register("climate", "set_temperature", temp_calls.append)

    hass.states.async_set(
        "climate.multisplit",
        "off",
        {"temperature": 21.0, "min_temp": 10.0, "max_temp": 31.0},
    )
    hass.states.async_set("sensor.multisplit_outdoor", "8.0")
    hass.states.async_set("sensor.grid_power", "0")

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.energiemanager_ac_auto_start_heating_when_off"},
        blocking=True,
    )
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.energiemanager_thermal_ac_buffer_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(hvac_calls) == 1
    assert hvac_calls[0].data["hvac_mode"] == "heat"
    assert len(temp_calls) == 1
    assert temp_calls[0].data["temperature"] == 23.5
    assert init_integration.runtime_data.coordinator.data["ac_saved_hvac_mode"] == "off"

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.energiemanager_thermal_ac_buffer_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(hvac_calls) == 2
    assert hvac_calls[1].data["hvac_mode"] == "off"
    assert init_integration.runtime_data.coordinator.data["ac_saved_hvac_mode"] is None


async def test_home_power_calculation_synchronizes_fast_grid_with_10s_inverter_and_battery(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Rapid Tasmota updates are averaged over the 10s window and combined with inverter and Anker battery power."""
    hass.states.async_set("sensor.inverter_wirkleistung", "2800")
    hass.states.async_set("sensor.anker_solix_solarbank_max_ac_345_batterieladeleistung", "1600")
    hass.states.async_set("sensor.anker_solix_solarbank_max_ac_345_batterieentladeleistung", "0")

    # Simulate multiple rapid Tasmota grid updates within the 10-second window (-100 W, +100 W, 0 W -> mean 0 W)
    hass.states.async_set("sensor.grid_power", "-100")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.grid_power", "100")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.grid_power", "0")
    await hass.async_block_till_done()

    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    home_state = hass.states.get("sensor.energiemanager_home_power_consumption")
    assert home_state is not None
    # Initial home_ema was 0.0; new raw = 2800 + 0 - 1600 = 1200 W -> EMA(0.35) = 420.0 W
    assert float(home_state.state) == pytest.approx(420.0)
    assert home_state.attributes["pv_power_watts"] == 2800.0
    assert home_state.attributes["battery_power_watts"] == -1600.0
    assert home_state.attributes["home_power_total_watts"] == 1200.0
