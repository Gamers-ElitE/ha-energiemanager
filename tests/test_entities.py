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
from homeassistant.util import dt as dt_util


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
    # EV unplugged so AC buffer gets surplus without EV taking priority
    hass.states.async_set("binary_sensor.tesla_plugged", "off")
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
    hass.states.async_set("binary_sensor.tesla_plugged", "off")
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


async def test_dhw_heat_pump_pv_surplus_and_min_temp_winter_boost(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DHW heat pump turns on with PV surplus (10-18h) and forces heat_pump below 42°C at solar peak."""
    wh_calls: list[ServiceCall] = []
    hass.services.async_register("water_heater", "set_operation_mode", wh_calls.append)

    # Set up both LG water heater variants (one with 'vacation', one with 'off')
    hass.states.async_set(
        "water_heater.wassererhitzer_2",
        "vacation",
        {
            "operation_list": ["heat_pump", "eco", "performance", "vacation"],
            "operation_mode": "vacation",
            "current_temperature": 46.0,
        },
    )
    hass.states.async_set(
        "water_heater.wassererhitzer",
        "off",
        {
            "operation_list": ["eco", "heat_pump", "performance", "off"],
            "operation_mode": "off",
            "current_temperature": 46.0,
        },
    )
    hass.states.async_set("sensor.wassererhitzer_hot_water_temperature", "46.0")
    hass.states.async_set("sensor.wassererhitzer_energy_current", "480")

    daytime = datetime(2026, 6, 15, 12, 30, 0, tzinfo=UTC)
    monkeypatch.setattr(dt_util, "utcnow", lambda: daytime)
    monkeypatch.setattr(dt_util, "as_local", lambda dt: dt)

    # Surplus starts at 850 W (> 500 W threshold) and water temp is 46 °C (< 53 °C target)
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.energiemanager_hot_water_heat_pump_active").state == "on"
    assert len(wh_calls) == 2
    assert {c.data["operation_mode"] for c in wh_calls} == {"heat_pump"}

    # Simulate water heaters now in heat_pump mode, then grid import > 200 W with water temp > 51 °C -> turns off
    wh_calls.clear()
    hass.states.async_set(
        "water_heater.wassererhitzer_2",
        "heat_pump",
        {"operation_list": ["heat_pump", "eco", "performance", "vacation"], "operation_mode": "heat_pump"},
    )
    hass.states.async_set(
        "water_heater.wassererhitzer",
        "heat_pump",
        {"operation_list": ["eco", "heat_pump", "performance", "off"], "operation_mode": "heat_pump"},
    )
    hass.states.async_set("sensor.wassererhitzer_hot_water_temperature", "52.0")
    await init_integration.runtime_data.coordinator.async_set_parameter("ema_alpha", 1.0, refresh=False)
    hass.states.async_set("sensor.grid_power", "350")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.energiemanager_hot_water_heat_pump_active").state == "off"
    modes_by_entity = {c.data[ATTR_ENTITY_ID]: c.data["operation_mode"] for c in wh_calls}
    assert modes_by_entity["water_heater.wassererhitzer_2"] == "vacation"
    assert modes_by_entity["water_heater.wassererhitzer"] == "off"

    # Winter minimum-temperature boost (< 42 °C at/after solar peak time) forces heating even during grid import
    wh_calls.clear()
    hass.states.async_set("sensor.wassererhitzer_hot_water_temperature", "39.5")
    hass.states.async_set("sensor.power_highest_peak_time_today", "2026-06-15T12:00:00+00:00")
    hass.states.async_set(
        "water_heater.wassererhitzer_2",
        "vacation",
        {"operation_list": ["heat_pump", "eco", "performance", "vacation"], "operation_mode": "vacation"},
    )
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    dhw_bs = hass.states.get("binary_sensor.energiemanager_hot_water_heat_pump_active")
    assert dhw_bs.state == "on"
    assert dhw_bs.attributes["dhw_forced_min_temp"] is True
    assert dhw_bs.attributes["dhw_reason"] == "min_temp_boost"


async def test_consumer_priority_order_select_and_cascade_yielding(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """EV has priority over AC buffer in default dhw_ev_ac order, and priority order can be changed via select."""
    prio_select = hass.states.get("select.energiemanager_surplus_consumer_priority_order")
    assert prio_select is not None
    assert prio_select.state == "dhw_ev_ac"

    # Turn on AC buffer and auto-heat
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.energiemanager_thermal_ac_buffer_enabled"},
        blocking=True,
    )

    # In default dhw_ev_ac order: EV can charge at 1400 W surplus (>= 1380 W threshold),
    # so AC buffer yields and stays off!
    await init_integration.runtime_data.coordinator.async_set_parameter(
        "ac_buffer_max_surplus_watts", 1500.0, refresh=False
    )
    await init_integration.runtime_data.coordinator.async_set_parameter("ema_alpha", 1.0, refresh=False)
    hass.states.async_set("sensor.grid_power", "-1400")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    # AC buffer yielded to EV
    assert hass.states.get("binary_sensor.energiemanager_thermal_ac_buffer_active").state == "off"

    # Switch priority order to dhw_ac_ev (where AC has priority over EV)
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {
            ATTR_ENTITY_ID: "select.energiemanager_surplus_consumer_priority_order",
            ATTR_OPTION: "dhw_ac_ev",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    assert init_integration.runtime_data.coordinator.priority_order == "dhw_ac_ev"
    # Now in dhw_ac_ev, AC buffer does not yield to EV and turns on in 500-1500 W surplus window
    assert hass.states.get("binary_sensor.energiemanager_thermal_ac_buffer_active").state == "on"


async def test_action_tracing_switch_sensor_and_clear_service(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Action tracing records actuator actions and can be enabled, inspected, and cleared."""
    tracing_switch = hass.states.get("switch.energiemanager_action_tracing")
    assert tracing_switch is not None
    assert tracing_switch.state == "off"

    trace_sensor = hass.states.get("sensor.energiemanager_last_action_trace")
    assert trace_sensor is not None
    assert trace_sensor.state == "Keine Aktionen"
    assert trace_sensor.attributes["trace_count"] == 0
    assert trace_sensor.attributes["tracing_enabled"] is False

    # Turn on action tracing
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.energiemanager_action_tracing"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert init_integration.runtime_data.coordinator.action_tracing_enabled is True
    trace_sensor = hass.states.get("sensor.energiemanager_last_action_trace")
    assert trace_sensor is not None
    assert trace_sensor.attributes["tracing_enabled"] is True
    assert trace_sensor.attributes["trace_count"] >= 1  # System activation trace

    # Trigger an actuator action: AC buffer shift
    hass.services.async_register("climate", "set_temperature", lambda call: None)
    hass.services.async_register("climate", "set_hvac_mode", lambda call: None)
    hass.states.async_set("climate.multisplit", "heat", {"temperature": 20.0, "min_temp": 10.0, "max_temp": 31.0})
    hass.states.async_set("binary_sensor.tesla_plugged", "off")
    hass.states.async_set("sensor.grid_power", "0")
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.energiemanager_thermal_ac_buffer_enabled"},
        blocking=True,
    )
    await hass.async_block_till_done()

    trace_sensor = hass.states.get("sensor.energiemanager_last_action_trace")
    assert trace_sensor is not None
    assert trace_sensor.attributes["trace_count"] >= 2
    recent_traces = trace_sensor.attributes["recent_traces"]
    categories = [t["category"] for t in recent_traces]
    assert "ac" in categories

    # Call clear_traces service action
    await hass.services.async_call(
        DOMAIN,
        "clear_traces",
        {"config_entry_id": init_integration.entry_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    trace_sensor = hass.states.get("sensor.energiemanager_last_action_trace")
    assert trace_sensor is not None
    assert trace_sensor.attributes["trace_count"] == 0
    assert trace_sensor.state == "Keine Aktionen"


async def test_ev_wakeup_delay_and_awake_detection(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """EV charging handles wake-up delay and verifies awake state before sending commands."""
    coord = init_integration.runtime_data.coordinator

    # 1. Verify number entity exists and defaults to 10.0
    wakeup_num = hass.states.get("number.energiemanager_ev_wake_up_delay")
    assert wakeup_num is not None
    assert wakeup_num.state == "10.0"

    # 2. Update value via number service call
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.energiemanager_ev_wake_up_delay", ATTR_VALUE: 5},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert coord.ev_wakeup_delay_seconds == 5.0
    assert hass.states.get("number.energiemanager_ev_wake_up_delay").state == "5.0"

    # 3. Test wake-up logic when starting charging from asleep state
    # First ensure charging is off so we test the transition to charging
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.energiemanager_ev_charging_mode", ATTR_OPTION: CHARGING_MODE_OFF},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get("select.energiemanager_ev_charging_mode").state == CHARGING_MODE_OFF

    wakeup_called = []
    charger_switched = []
    current_set = []

    hass.services.async_register(
        "button",
        "press",
        lambda call: wakeup_called.append(call.data),
    )
    hass.services.async_register(
        "switch",
        "turn_on",
        lambda call: charger_switched.append(call.data),
    )
    hass.services.async_register(
        "number",
        "set_value",
        lambda call: current_set.append(call.data),
    )

    # Set awake sensor to off and set a short delay for fast test execution
    coord.ev_wakeup_delay_seconds = 0.05
    hass.states.async_set("button.tesla_wake_up", "2026-10-30T09:00:00+00:00")
    hass.states.async_set("switch.tesla_charger", "off")
    hass.states.async_set("number.tesla_charging_amps", "0")
    hass.states.async_set("binary_sensor.tesla_awake", "off")
    hass.states.async_set("sensor.tesla_charging_power", "0")

    # Turn on action tracing to inspect traces
    coord.action_tracing_enabled = True

    # Call select_option to start fast charging mode
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.energiemanager_ev_charging_mode", ATTR_OPTION: CHARGING_MODE_FAST},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify wakeup button was pressed
    assert len(wakeup_called) == 1
    assert wakeup_called[0][ATTR_ENTITY_ID] == "button.tesla_wake_up"

    # Verify charger was activated
    assert len(charger_switched) == 1
    assert charger_switched[0][ATTR_ENTITY_ID] == "switch.tesla_charger"

    # Verify action traces
    trace_sensor = hass.states.get("sensor.energiemanager_last_action_trace")
    assert trace_sensor is not None
    traces = trace_sensor.attributes["recent_traces"]
    ev_traces = [t for t in traces if t["category"] == "ev"]
    assert any("Wake-Up" in t["action"] for t in ev_traces)
    assert any("Warte auf Aufwachen" in t["action"] for t in ev_traces)

    # 4. Test auto-discovery of awake sensor from ref entities
    assert coord.resolve_ev_awake_entity() == "binary_sensor.tesla_awake"

    # Test auto-discovery from button name pattern
    hass.states.async_set("binary_sensor.my_car_awake", "on")
    hass.config_entries.async_update_entry(
        coord.config_entry,
        data={
            **coord.config_entry.data,
            "ev_awake_binary_sensor": None,
            "ev_wakeup_button": "button.my_car_wake_up_car",
        },
    )
    assert coord.resolve_ev_awake_entity() == "binary_sensor.my_car_awake"

    # Test auto-discovery of telemetry refresh button
    assert coord.resolve_ev_force_update_button() is None
    hass.states.async_set("button.my_car_force_update_all", "unknown")
    assert coord.resolve_ev_force_update_button() == "button.my_car_force_update_all"


async def test_ev_fast_charging_not_blocked_by_dhw_priority_and_cable_types(
    init_integration: MockConfigEntry,
    hass: HomeAssistant,
) -> None:
    """Test that EV fast charging is never blocked by DHW priority, and IEC cable is recognized."""
    # Setup car plugged via IEC cable state
    hass.states.async_set("binary_sensor.tesla_plugged", "IEC")
    hass.states.async_set("sensor.tesla_soc", "30")

    # Set DHW temperature to low (needs heating)
    hass.states.async_set("water_heater.wassererhitzer", "heat_pump", {"current_temperature": 45, "temperature": 53})

    # Set EMA alpha to 1.0 (instantaneous) and grid power to 1500 W import (no PV surplus)
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: "number.energiemanager_ema_smoothing_factor", ATTR_VALUE: 1.0},
        blocking=True,
    )
    hass.states.async_set("sensor.grid_power", "1500")

    # Turn mode to off, then surplus: car should not start charging without surplus
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.energiemanager_ev_charging_mode", ATTR_OPTION: CHARGING_MODE_OFF},
        blocking=True,
    )
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.energiemanager_ev_charging_mode", ATTR_OPTION: "pv_surplus"},
        blocking=True,
    )
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    # In PV surplus mode with no surplus, EV target current should be 0
    assert hass.states.get("sensor.energiemanager_ev_target_current").state == "0"

    # Now switch to FAST charging mode
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.energiemanager_ev_charging_mode", ATTR_OPTION: CHARGING_MODE_FAST},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Fast charging must NOT yield to DHW!
    assert hass.states.get("select.energiemanager_ev_charging_mode").state == CHARGING_MODE_FAST
    assert hass.states.get("sensor.energiemanager_ev_target_current").state == "13"

    # If the user manually changes the current on the car/app side (e.g. to 10 A),
    # Energiemanager adopts it and does NOT overwrite it back to 13 A!
    hass.states.async_set("number.tesla_charging_amps", "10")
    await init_integration.runtime_data.coordinator.async_refresh()
    await hass.async_block_till_done()

    assert hass.states.get("sensor.energiemanager_ev_target_current").state == "10"
