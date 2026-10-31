"""Data update coordinator for sam_energiemanager."""

import asyncio
from collections.abc import Callable
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from custom_components.sam_energiemanager.const import (
    AC_AUTO_HEAT_DEFAULT_TEMP,
    AC_AUTO_HEAT_MAX_OUTDOOR_TEMP,
    AC_BUFFER_MAX_SURPLUS_WATTS,
    AC_BUFFER_MIN_HOLD_SECONDS,
    AC_BUFFER_MIN_SURPLUS_WATTS,
    AC_BUFFER_TEMP_OFFSET,
    BATTERY_LOCK_RELEASE_SECONDS,
    BATTERY_LOCK_THRESHOLD_WATTS,
    CHARGING_MODE_FAST,
    CHARGING_MODE_OFF,
    CHARGING_MODE_PV_SURPLUS,
    CHARGING_MODES,
    CONF_BATTERY_DISCHARGE_LOCK_SWITCH,
    CONF_BATTERY_POWER_SENSOR,
    CONF_BATTERY_SOC_SENSOR,
    CONF_CLIMATE_ENTITY,
    CONF_ELECTRICITY_PRICE,
    CONF_EV_AWAKE_BINARY_SENSOR,
    CONF_EV_BLE_CONNECTED_BINARY_SENSOR,
    CONF_EV_CHARGING_SWITCH,
    CONF_EV_CURRENT_NUMBER,
    CONF_EV_FORCE_UPDATE_BUTTON,
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
    DEADBAND_WATTS,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_ELECTRICITY_PRICE,
    DEFAULT_EV_POLL_INTERVAL_SECONDS,
    DEFAULT_EV_WAKEUP_DELAY_SECONDS,
    DEFAULT_PRIORITY_ORDER,
    DEFAULT_TESLA_MAX_CURRENT,
    DEFAULT_TESLA_TARGET_SOC,
    DHW_MIN_SURPLUS_WATTS,
    DHW_MIN_TEMP,
    DHW_STOP_GRID_IMPORT_WATTS,
    DHW_STOP_TEMP,
    DHW_TARGET_TEMP,
    DHW_WINDOW_END_HOUR,
    DHW_WINDOW_START_HOUR,
    DOMAIN,
    EMA_ALPHA,
    EV_CLOUD_HYSTERESIS_SECONDS,
    EV_MIN_CURRENT_A,
    EV_MIN_SURPLUS_WATTS,
    EV_STOP_BELOW_CURRENT_A,
    EV_STOP_GRID_IMPORT_WATTS,
    EV_VOLTAGE,
    EVENT_SESSION_COMPLETED,
    LOGGER,
    MAX_ACTION_TRACES,
    PRIORITY_DHW_AC_EV,
    PRIORITY_DHW_EV_AC,
    PRIORITY_EV_AC_DHW,
    PRIORITY_EV_DHW_AC,
    PRIORITY_ORDERS,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .cascade import SessionTracker, compute_ema, compute_ev_target_current, compute_surplus_watts, is_within_deadband

if TYPE_CHECKING:
    from custom_components.sam_energiemanager.data import EnergiemanagerConfigEntry


class EnergiemanagerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate zero-export filtering, priority cascade, EV charging, and session tracking."""

    config_entry: EnergiemanagerConfigEntry

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Energiemanager coordinator state."""
        super().__init__(*args, **kwargs)
        self.battery_reserve_soc: float = DEFAULT_BATTERY_RESERVE_SOC
        self.tesla_max_current: float = DEFAULT_TESLA_MAX_CURRENT
        self.tesla_target_soc: float = DEFAULT_TESLA_TARGET_SOC
        self.charging_mode: str = CHARGING_MODE_PV_SURPLUS
        self.priority_order: str = DEFAULT_PRIORITY_ORDER
        self.ac_buffer_enabled: bool = False
        self.ac_auto_heat_enabled: bool = False
        self.dhw_enabled: bool = True

        self.ema_alpha: float = EMA_ALPHA
        self.deadband_watts: float = DEADBAND_WATTS
        self.battery_lock_threshold_watts: float = BATTERY_LOCK_THRESHOLD_WATTS
        self.battery_lock_release_seconds: float = BATTERY_LOCK_RELEASE_SECONDS
        self.dhw_min_surplus_watts: float = DHW_MIN_SURPLUS_WATTS
        self.dhw_target_temp: float = DHW_TARGET_TEMP
        self.dhw_stop_temp: float = DHW_STOP_TEMP
        self.dhw_min_temp: float = DHW_MIN_TEMP
        self.ac_buffer_min_surplus_watts: float = AC_BUFFER_MIN_SURPLUS_WATTS
        self.ac_buffer_max_surplus_watts: float = AC_BUFFER_MAX_SURPLUS_WATTS
        self.ac_buffer_temp_offset: float = AC_BUFFER_TEMP_OFFSET
        self.ac_buffer_min_hold_minutes: float = round(AC_BUFFER_MIN_HOLD_SECONDS / 60.0, 1)
        self.ac_auto_heat_max_outdoor_temp: float = AC_AUTO_HEAT_MAX_OUTDOOR_TEMP
        self.ev_min_surplus_watts: float = EV_MIN_SURPLUS_WATTS
        self.ev_cloud_hysteresis_seconds: float = EV_CLOUD_HYSTERESIS_SECONDS
        self.ev_wakeup_delay_seconds: float = DEFAULT_EV_WAKEUP_DELAY_SECONDS
        self.ev_poll_interval_seconds: float = DEFAULT_EV_POLL_INTERVAL_SECONDS
        self.electricity_price: float = float(
            self.config_entry.options.get(CONF_ELECTRICITY_PRICE, DEFAULT_ELECTRICITY_PRICE)
        )

        self._grid_ema: float | None = None
        self._home_ema: float | None = None
        self._grid_window_samples: list[float] = []
        self._last_update_utc: datetime | None = None
        self._last_ev_poll_utc: datetime | None = None
        self._battery_lock_active: bool = False
        self._battery_low_power_since: datetime | None = None
        self._ev_low_surplus_since: datetime | None = None
        self._ev_charging_active: bool = False
        self._ev_target_amps: int = 0
        self._ev_fast_charge_target_amps: int | None = None
        self._ev_stop_reason: str | None = None
        self._dhw_active: bool = False
        self._dhw_forced_min_temp: bool = False
        self._dhw_reason: str = "idle"
        self._ac_buffer_active: bool = False
        self._ac_buffer_activated_at: datetime | None = None
        self._ac_saved_temperature: float | None = None
        self._ac_saved_hvac_mode: str | None = None
        self._daily_date: date | None = None
        self._daily_home_kwh: float = 0.0
        self._daily_pv_kwh: float = 0.0
        self._daily_grid_import_kwh: float = 0.0
        self._daily_grid_export_kwh: float = 0.0
        self.action_tracing_enabled: bool = False
        self._recent_traces: list[dict[str, Any]] = []
        self.session_tracker = SessionTracker()

    def async_setup_listeners(self) -> Callable[[], None]:
        """Track high-frequency Tasmota grid power changes to compute a 10s window average."""
        grid_entity = self.config_entry.data.get(CONF_GRID_POWER_SENSOR)
        if not grid_entity:
            return lambda: None

        @callback
        def _handle_grid_change(event: Event[EventStateChangedData]) -> None:
            new_state = event.data.get("new_state")
            if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                return
            try:
                val = float(new_state.state)
            except TypeError, ValueError:
                return
            if str(new_state.attributes.get("unit_of_measurement", "")).lower() == "kw":
                val *= 1000.0
            self._grid_window_samples.append(val)
            if len(self._grid_window_samples) > 120:
                self._grid_window_samples = self._grid_window_samples[-120:]

        return async_track_state_change_event(self.hass, [grid_entity], _handle_grid_change)

    def _read_entity_watts(self, entity_id: str | None) -> float | None:
        """Read a numeric power state from an entity ID, converting kW to W if needed."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        try:
            val = float(state.state)
        except TypeError, ValueError:
            return None
        if str(state.attributes.get("unit_of_measurement", "")).lower() == "kw":
            return val * 1000.0
        return val

    def _read_pv_power(self) -> float:
        """Read PV inverter AC power from configured sensor or auto-discovered inverter sensor."""
        configured = self._read_float(CONF_PV_POWER_SENSOR, as_watts=True)
        if configured is not None:
            return max(0.0, configured)
        for candidate in (
            "sensor.inverter_wirkleistung",
            "sensor.anker_solix_solarbank_max_ac_345_solarstrom",
            "sensor.sim_pv_power",
        ):
            val = self._read_entity_watts(candidate)
            if val is not None:
                return max(0.0, val)
        return 0.0

    def _read_battery_signed_power(self) -> float:
        """
        Read signed net home battery power in Watts.

        Returns:
            Negative Watts when charging (absorbing power), positive Watts when discharging.

        """
        configured = self._read_float(CONF_BATTERY_POWER_SENSOR, as_watts=True)
        if configured is not None:
            return configured
        charge_w = self._read_entity_watts("sensor.anker_solix_solarbank_max_ac_345_batterieladeleistung")
        discharge_w = self._read_entity_watts("sensor.anker_solix_solarbank_max_ac_345_batterieentladeleistung")
        if charge_w is not None or discharge_w is not None:
            c_abs = abs(charge_w or 0.0)
            d_abs = abs(discharge_w or 0.0)
            if c_abs > 10.0:
                return -c_abs
            if d_abs > 10.0:
                return d_abs
            return 0.0
        for candidate in (
            "sensor.energy_battery_anker_solix_solarbank_max_ac_345_batterieentladeleistung_anker_solix_solarbank_max_ac_345_batterieladeleistung_net_power",
            "sensor.sim_battery_power",
        ):
            val = self._read_entity_watts(candidate)
            if val is not None:
                return val
        return 0.0

    def _read_float(self, conf_key: str, default: float | None = None, *, as_watts: bool = False) -> float | None:
        """Read a numeric state from a configured entity ID, converting kW to W when requested."""
        entity_id = self.config_entry.data.get(conf_key)
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return default
        try:
            val = float(state.state)
        except TypeError, ValueError:
            return default
        if as_watts and str(state.attributes.get("unit_of_measurement", "")).lower() == "kw":
            return val * 1000.0
        return val

    def _read_bool(self, conf_key: str, *, default: bool = False) -> bool:
        """Read a boolean state from a configured entity ID."""
        entity_id = self.config_entry.data.get(conf_key)
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return default
        val = state.state.lower().strip()
        if val in ("off", "false", "disconnected", "unplugged", "none", "not_home", "away", "0"):
            return False
        if val in (
            STATE_ON,
            "true",
            "connected",
            "plugged",
            "charging",
            "stopped",
            "complete",
            "iec",
            "iec_type2",
            "sae",
            "standard",
            "home",
            "present",
            "online",
            "1",
        ):
            return True
        return default

    async def _async_update_data(self) -> dict[str, Any]:
        """
        Execute one cycle of the zero-export filter, priority cascade, and session tracker.

        Returns:
            Dictionary of calculated states consumed by all platform entities.

        """
        now_utc = dt_util.utcnow()
        dt_hours = (
            max(0.0, (now_utc - self._last_update_utc).total_seconds() / 3600.0)
            if self._last_update_utc is not None
            else 0.0
        )
        self._last_update_utc = now_utc

        grid_raw = self._read_float(CONF_GRID_POWER_SENSOR, 0.0, as_watts=True) or 0.0
        samples = [*self._grid_window_samples, grid_raw]
        self._grid_window_samples.clear()
        grid_10s_mean = sum(samples) / len(samples)

        pv_power = self._read_pv_power()
        battery_signed_power = self._read_battery_signed_power()
        battery_soc = self._read_float(CONF_BATTERY_SOC_SENSOR)
        ev_power = self._read_float(CONF_EV_POWER_SENSOR, 0.0, as_watts=True) or 0.0
        if ev_power <= 0.0 and self._read_bool(CONF_EV_CHARGING_SWITCH):
            ev_power = (self._read_float(CONF_EV_CURRENT_NUMBER, 0.0) or 0.0) * EV_VOLTAGE
        ev_soc = self._read_float(CONF_EV_SOC_SENSOR)
        ev_plugged = self._read_bool(CONF_EV_PLUGGED_BINARY_SENSOR, default=True)
        ev_ble_connected = self._read_bool(CONF_EV_BLE_CONNECTED_BINARY_SENSOR, default=True)
        has_wakeup = bool(self.config_entry.data.get(CONF_EV_WAKEUP_BUTTON))
        ev_ready_at_home = ev_plugged and (ev_ble_connected or has_wakeup)

        # A. EMA Filter, Deadband & Synchronized Home Power Consumption
        self._grid_ema = compute_ema(grid_raw, self._grid_ema, alpha=self.ema_alpha)
        grid_filtered = round(self._grid_ema, 1)
        in_deadband = is_within_deadband(grid_filtered, deadband=self.deadband_watts)
        surplus_power = round(compute_surplus_watts(grid_filtered), 1)

        # Synchronize fast Tasmota (10s window mean) with 10s Inverter & Anker Modbus readings
        home_total_raw = max(0.0, pv_power + grid_10s_mean + battery_signed_power)
        home_pure_raw = max(0.0, home_total_raw - max(0.0, ev_power))
        self._home_ema = compute_ema(home_pure_raw, self._home_ema, alpha=self.ema_alpha)
        home_power_watts = round(self._home_ema, 1)

        # Daily Energy Summary (resets at local midnight)
        now_local = dt_util.as_local(now_utc)
        today_date = now_local.date()
        if self._daily_date != today_date:
            self._daily_date = today_date
            self._daily_home_kwh = 0.0
            self._daily_pv_kwh = 0.0
            self._daily_grid_import_kwh = 0.0
            self._daily_grid_export_kwh = 0.0
        if 0.0 < dt_hours < 0.25:
            self._daily_home_kwh += (home_total_raw / 1000.0) * dt_hours
            self._daily_pv_kwh += (max(0.0, pv_power) / 1000.0) * dt_hours
            self._daily_grid_import_kwh += (max(0.0, grid_10s_mean) / 1000.0) * dt_hours
            self._daily_grid_export_kwh += (max(0.0, -grid_10s_mean) / 1000.0) * dt_hours
        inverter_daily = self._read_entity_watts("sensor.inverter_tagesertrag")
        daily_pv_kwh = round(max(self._daily_pv_kwh, inverter_daily or 0.0), 2)
        daily_home_kwh = round(self._daily_home_kwh, 2)
        daily_grid_import_kwh = round(self._daily_grid_import_kwh, 2)
        daily_grid_export_kwh = round(self._daily_grid_export_kwh, 2)
        daily_autarky_pct = (
            round(max(0.0, min(100.0, (1.0 - self._daily_grid_import_kwh / self._daily_home_kwh) * 100.0)), 1)
            if self._daily_home_kwh > 0.01
            else 100.0
        )

        # B. Stage 2: Home Battery Priority
        battery_priority_active = (
            self.battery_reserve_soc > 0.0 and battery_soc is not None and battery_soc < self.battery_reserve_soc
        )

        # C. Home Battery Hardware Discharge Lock
        if ev_power > self.battery_lock_threshold_watts:
            self._battery_lock_active = True
            self._battery_low_power_since = None
        elif self._battery_lock_active:
            if self._battery_low_power_since is None:
                self._battery_low_power_since = now_utc
            elif (now_utc - self._battery_low_power_since).total_seconds() >= self.battery_lock_release_seconds:
                self._battery_lock_active = False
                self._battery_low_power_since = None

        await self._async_sync_battery_lock(ev_power=ev_power)

        # Pre-read hot water state for priority determination
        water_temp = self._read_water_temperature()
        dhw_power = self._read_dhw_power()

        # Readiness of controllable downstream consumers
        ev_ready_to_charge = (
            self.charging_mode == CHARGING_MODE_PV_SURPLUS
            and ev_ready_at_home
            and (ev_soc is None or ev_soc < self.tesla_target_soc)
        )
        dhw_ready_to_heat = (
            self.dhw_enabled
            and bool(self._resolve_water_heater_entities())
            and (water_temp is None or water_temp < self.dhw_target_temp)
        )
        ev_can_or_is_charging = ev_ready_to_charge and (
            self._ev_charging_active or surplus_power >= self.ev_min_surplus_watts
        )

        # Consumer priority cascade yielding
        dhw_yield = False
        ev_yield = False
        ac_yield = False

        if self.priority_order == PRIORITY_DHW_EV_AC:
            # Prio 3: DHW -> Prio 4: EV -> Prio 5: AC
            # EV yields to DHW only if DHW is ready to heat and surplus is sufficient for DHW but not enough for both
            ev_yield = (
                dhw_ready_to_heat
                and surplus_power >= self.dhw_min_surplus_watts
                and surplus_power < (self.dhw_min_surplus_watts + self.ev_min_surplus_watts)
                and not self._ev_charging_active
            )
            ac_yield = ev_can_or_is_charging and (
                not self._ev_charging_active or self._ev_target_amps < self.tesla_max_current
            )
        elif self.priority_order == PRIORITY_EV_DHW_AC:
            # Prio 3: EV -> Prio 4: DHW -> Prio 5: AC
            dhw_yield = ev_can_or_is_charging and surplus_power < (
                self.ev_min_surplus_watts + self.dhw_min_surplus_watts
            )
            ac_yield = (
                ev_can_or_is_charging
                and (not self._ev_charging_active or self._ev_target_amps < self.tesla_max_current)
            ) or dhw_ready_to_heat
        elif self.priority_order == PRIORITY_DHW_AC_EV:
            # Prio 3: DHW -> Prio 4: AC -> Prio 5: EV
            ev_yield = self.ac_buffer_enabled and (
                self.ac_buffer_min_surplus_watts <= surplus_power <= self.ac_buffer_max_surplus_watts
            )
        elif self.priority_order == PRIORITY_EV_AC_DHW:
            # Prio 3: EV -> Prio 4: AC -> Prio 5: DHW
            ac_yield = ev_can_or_is_charging and (
                not self._ev_charging_active or self._ev_target_amps < self.tesla_max_current
            )
            dhw_yield = ev_can_or_is_charging or self._ac_buffer_active

        # C2. Stage 2b: Domestic Hot Water (DHW) Heat Pump Control
        await self._async_update_dhw(
            now_local=now_local,
            grid_filtered=grid_filtered,
            surplus_power=surplus_power,
            battery_priority_active=battery_priority_active,
            yield_to_higher_priority=dhw_yield,
            water_temp=water_temp,
        )

        # B. Stage 3: Thermal AC Buffer
        await self._async_update_ac_buffer(
            now_utc=now_utc,
            surplus_power=surplus_power,
            battery_priority_active=battery_priority_active,
            yield_to_higher_priority=ac_yield,
            in_deadband=in_deadband,
        )

        # D. Stage 4: 1-Phase Tesla Charging Control
        await self._async_update_ev_charging(
            now_utc=now_utc,
            grid_filtered=grid_filtered,
            surplus_power=surplus_power,
            ev_power=ev_power,
            ev_soc=ev_soc,
            ev_ready_at_home=ev_ready_at_home,
            ev_plugged=ev_plugged,
            battery_priority_active=battery_priority_active,
            battery_soc=battery_soc,
            yield_to_higher_priority=ev_yield,
            in_deadband=in_deadband,
        )

        # E. EV Charging Session Tracking & Energy Split
        ev_solar_w, ev_grid_w, completed_session = self.session_tracker.update(
            ev_watts=ev_power,
            grid_raw_watts=grid_raw,
            ev_soc=ev_soc,
            dt_hours=dt_hours,
            price_eur_per_kwh=self.electricity_price,
            now_utc=now_utc,
        )
        if completed_session is not None:
            self.hass.bus.async_fire(EVENT_SESSION_COMPLETED, completed_session)

        return {
            "source_entities": dict(self.config_entry.data),
            "grid_power_filtered": grid_filtered,
            "grid_10s_mean_watts": round(grid_10s_mean, 1),
            "surplus_power": surplus_power,
            "pv_power_watts": round(pv_power, 1),
            "battery_power_watts": round(battery_signed_power, 1),
            "home_power_watts": home_power_watts,
            "home_power_total_watts": round(home_total_raw, 1),
            "daily_home_kwh": daily_home_kwh,
            "daily_pv_kwh": daily_pv_kwh,
            "daily_grid_import_kwh": daily_grid_import_kwh,
            "daily_grid_export_kwh": daily_grid_export_kwh,
            "daily_autarky_pct": daily_autarky_pct,
            "priority_order": self.priority_order,
            "dhw_enabled": self.dhw_enabled,
            "dhw_active": self._dhw_active,
            "dhw_forced_min_temp": self._dhw_forced_min_temp,
            "dhw_reason": self._dhw_reason,
            "water_temp": water_temp,
            "dhw_power_watts": round(dhw_power, 1),
            "dhw_min_surplus_watts": self.dhw_min_surplus_watts,
            "dhw_target_temp": self.dhw_target_temp,
            "dhw_stop_temp": self.dhw_stop_temp,
            "dhw_min_temp": self.dhw_min_temp,
            "ev_charging_power": round(ev_power, 1),
            "ev_solar_power": ev_solar_w,
            "ev_grid_power": ev_grid_w,
            "ev_target_current": self._ev_target_amps,
            "ev_solar_lifetime_kwh": round(self.session_tracker.solar_lifetime_kwh, 3),
            "ev_grid_lifetime_kwh": round(self.session_tracker.grid_lifetime_kwh, 3),
            "last_session_summary": self.session_tracker.last_summary,
            "last_session_data": self.session_tracker.last_session_data,
            "battery_reserve_soc": self.battery_reserve_soc,
            "tesla_max_current": self.tesla_max_current,
            "tesla_target_soc": self.tesla_target_soc,
            "charging_mode": self.charging_mode,
            "ac_buffer_enabled": self.ac_buffer_enabled,
            "ac_auto_heat_enabled": self.ac_auto_heat_enabled,
            "ac_buffer_active": self._ac_buffer_active,
            "ac_saved_temperature": self._ac_saved_temperature,
            "ac_saved_hvac_mode": self._ac_saved_hvac_mode,
            "battery_discharge_lock_active": self._battery_lock_active,
            "ev_session_active": self.session_tracker.active,
            "ema_alpha": self.ema_alpha,
            "deadband_watts": self.deadband_watts,
            "battery_lock_threshold_watts": self.battery_lock_threshold_watts,
            "battery_lock_release_seconds": self.battery_lock_release_seconds,
            "ac_buffer_min_surplus_watts": self.ac_buffer_min_surplus_watts,
            "ac_buffer_max_surplus_watts": self.ac_buffer_max_surplus_watts,
            "ac_buffer_temp_offset": self.ac_buffer_temp_offset,
            "ac_buffer_min_hold_minutes": self.ac_buffer_min_hold_minutes,
            "ac_auto_heat_max_outdoor_temp": self.ac_auto_heat_max_outdoor_temp,
            "ev_min_surplus_watts": self.ev_min_surplus_watts,
            "ev_cloud_hysteresis_seconds": self.ev_cloud_hysteresis_seconds,
            "ev_wakeup_delay_seconds": self.ev_wakeup_delay_seconds,
            "electricity_price": self.electricity_price,
            "action_tracing_enabled": self.action_tracing_enabled,
            "action_traces": list(self._recent_traces),
            "trace_count": len(self._recent_traces),
            "last_action_trace": self._recent_traces[-1] if self._recent_traces else None,
        }

    def _resolve_water_heater_entities(self) -> list[str]:
        """Return configured and auto-discovered LG water heater entities."""
        result: list[str] = []
        configured = self.config_entry.data.get(CONF_WATER_HEATER_ENTITY)
        for candidate in (configured, "water_heater.wassererhitzer_2", "water_heater.wassererhitzer"):
            if candidate and candidate not in result and self.hass.states.get(candidate) is not None:
                result.append(candidate)
        return result

    def _read_water_temperature(self) -> float | None:
        """Read hot water temperature from configured sensor, LG sensor, or water_heater attributes."""
        configured = self._read_float(CONF_WATER_TEMP_SENSOR)
        if configured is not None:
            return configured
        for sensor_id in ("sensor.wassererhitzer_hot_water_temperature", "sensor.sim_water_temperature"):
            val = self._read_entity_watts(sensor_id)
            if val is not None:
                return val
        for entity_id in self._resolve_water_heater_entities():
            st = self.hass.states.get(entity_id)
            if st is not None:
                raw_temp = st.attributes.get("current_temperature")
                if raw_temp is not None:
                    try:
                        return float(raw_temp)
                    except TypeError, ValueError:
                        continue
        return None

    def _read_dhw_power(self) -> float:
        """Read current power draw of the hot water heat pump in Watts."""
        for sensor_id in ("sensor.wassererhitzer_energy_current", "sensor.sim_dhw_power"):
            val = self._read_entity_watts(sensor_id)
            if val is not None:
                return max(0.0, val)
        return 450.0 if self._dhw_active else 0.0

    def _is_past_solar_peak(self, now_local: datetime) -> bool:
        """Check if current time is at or past today's solar peak time for winter minimum-temp boost."""
        peak_id = self.config_entry.data.get(CONF_SOLAR_PEAK_TIME_SENSOR) or "sensor.power_highest_peak_time_today"
        st = self.hass.states.get(peak_id)
        if st is not None and st.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            parsed = dt_util.parse_datetime(st.state)
            if parsed is not None:
                return now_local >= dt_util.as_local(parsed)
        return now_local.hour >= 13

    async def _async_update_dhw(
        self,
        *,
        now_local: datetime,
        grid_filtered: float,
        surplus_power: float,
        battery_priority_active: bool,
        yield_to_higher_priority: bool = False,
        water_temp: float | None,
    ) -> None:
        """Control the domestic hot water heat pump via PV surplus and minimum temperature protection."""
        targets = self._resolve_water_heater_entities()
        if not self.dhw_enabled or not targets:
            if self._dhw_active:
                self._dhw_active = False
                self._dhw_forced_min_temp = False
                self._dhw_reason = "disabled"
            return

        in_daytime = DHW_WINDOW_START_HOUR <= now_local.hour < DHW_WINDOW_END_HOUR

        # 1. Winter minimum temperature boost (< 42 °C at/after solar peak during daytime)
        if (
            in_daytime
            and water_temp is not None
            and water_temp < self.dhw_min_temp
            and self._is_past_solar_peak(now_local)
        ):
            self._dhw_forced_min_temp = True

        if self._dhw_forced_min_temp:
            if not in_daytime or (water_temp is not None and water_temp >= self.dhw_stop_temp):
                self._dhw_forced_min_temp = False
            else:
                self._dhw_active = True
                self._dhw_reason = "min_temp_boost"
                await self._async_set_dhw_mode(targets, heating=True)
                return

        # 2. Yield to higher-priority consumers (e.g. EV first) if requested
        if yield_to_higher_priority and not self._dhw_forced_min_temp:
            if self._dhw_active:
                self._dhw_active = False
                self._dhw_reason = "yield_to_higher_priority"
                await self._async_set_dhw_mode(targets, heating=False)
            return

        # 3. Normal PV surplus heating (10:00 - 18:00) and smart turn-off
        if not in_daytime:
            if self._dhw_active or DHW_WINDOW_END_HOUR <= now_local.hour < 20:
                self._dhw_active = False
                self._dhw_reason = "evening_off"
                await self._async_set_dhw_mode(targets, heating=False)
            return

        if not self._dhw_active:
            below_target = water_temp is None or water_temp < self.dhw_target_temp
            if not battery_priority_active and surplus_power >= self.dhw_min_surplus_watts and below_target:
                self._dhw_active = True
                self._dhw_reason = "pv_surplus"
                await self._async_set_dhw_mode(targets, heating=True)
        else:
            target_reached = water_temp is not None and water_temp >= self.dhw_target_temp
            grid_import_stop = grid_filtered > DHW_STOP_GRID_IMPORT_WATTS and (
                water_temp is None or water_temp > self.dhw_stop_temp
            )
            if target_reached or grid_import_stop:
                self._dhw_active = False
                self._dhw_reason = "target_reached" if target_reached else "grid_import_stop"
                await self._async_set_dhw_mode(targets, heating=False)
            else:
                await self._async_set_dhw_mode(targets, heating=True)

    async def _async_set_dhw_mode(self, targets: list[str], *, heating: bool) -> None:
        """Set operation mode on water_heater or select entities ('heat_pump' vs 'vacation'/'off')."""
        for entity_id in targets:
            st = self.hass.states.get(entity_id)
            if st is None or st.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                continue
            domain = entity_id.split(".", 1)[0]
            options: list[str] = list(st.attributes.get("operation_list") or st.attributes.get("options") or [])
            if heating:
                desired = "heat_pump"
            elif "vacation" in options:
                desired = "vacation"
            elif "off" in options:
                desired = "off"
            else:
                desired = "vacation"

            current_mode = st.attributes.get("operation_mode") or st.state
            if current_mode == desired:
                continue
            try:
                if domain == "select":
                    await self.hass.services.async_call(
                        "select",
                        "select_option",
                        {ATTR_ENTITY_ID: entity_id, "option": desired},
                        blocking=False,
                    )
                elif domain == "water_heater":
                    await self.hass.services.async_call(
                        "water_heater",
                        "set_operation_mode",
                        {ATTR_ENTITY_ID: entity_id, "operation_mode": desired},
                        blocking=False,
                    )
            except HomeAssistantError as err:
                LOGGER.warning("Konnte Warmwassermodus für %s nicht setzen: %s", entity_id, err)
                continue

            reason_map = {
                "min_temp_boost": "Winter-Mindestschutz: Wassertemperatur < 42 °C beim Solar-Peak",
                "pv_surplus": "PV-Überschuss ausreichend (Heizfenster 10:00–18:00 Uhr)",
                "yield_to_higher_priority": f"Weicht Vorrang-Verbraucher (Kaskade: {self.priority_order})",
                "target_reached": f"Zieltemperatur ({self.dhw_target_temp:.0f} °C) erreicht",
                "grid_import_stop": "Netzbezug zu hoch (Heizen beendet)",
                "evening_off": "Heizfenster beendet (nach 18:00 Uhr)",
            }
            reason_str = reason_map.get(self._dhw_reason, self._dhw_reason or "Regelung")

            self.record_trace(
                category="dhw",
                action=f"Warmwasser-Modus auf '{desired}' gesetzt",
                reason=reason_str,
                target=entity_id,
                value=desired,
                details={"mode": desired, "reason": self._dhw_reason},
            )

    async def _async_update_ac_buffer(
        self,
        *,
        now_utc: datetime,
        surplus_power: float,
        battery_priority_active: bool,
        yield_to_higher_priority: bool = False,
        in_deadband: bool,
    ) -> None:
        """Update the thermal AC buffer state with 20-minute compressor protection and temperature shift."""
        was_active = self._ac_buffer_active

        if not self.ac_buffer_enabled:
            self._ac_buffer_active = False
            self._ac_buffer_activated_at = None
            if was_active:
                await self._async_apply_ac_buffer_offset(activate=False)
            return

        if yield_to_higher_priority:
            if was_active and self._ac_buffer_activated_at is not None:
                elapsed = (now_utc - self._ac_buffer_activated_at).total_seconds()
                if elapsed < self.ac_buffer_min_hold_minutes * 60.0:
                    return
            self._ac_buffer_active = False
            self._ac_buffer_activated_at = None
            if was_active:
                await self._async_apply_ac_buffer_offset(activate=False)
            return

        if self._ac_buffer_active and self._ac_buffer_activated_at is not None:
            elapsed = (now_utc - self._ac_buffer_activated_at).total_seconds()
            if elapsed < self.ac_buffer_min_hold_minutes * 60.0:
                return

        if in_deadband:
            return

        in_window = self.ac_buffer_min_surplus_watts <= surplus_power <= self.ac_buffer_max_surplus_watts
        if not battery_priority_active and in_window:
            if not self._ac_buffer_active:
                self._ac_buffer_active = True
                self._ac_buffer_activated_at = now_utc
                await self._async_apply_ac_buffer_offset(activate=True)
        elif self._ac_buffer_active:
            self._ac_buffer_active = False
            self._ac_buffer_activated_at = None
            await self._async_apply_ac_buffer_offset(activate=False)

    def _read_outdoor_temperature(self, climate_id: str) -> float | None:
        """Read outdoor temperature from configured sensor or auto-discovered sibling climate sensor."""
        configured = self._read_float(CONF_OUTDOOR_TEMP_SENSOR)
        if configured is not None:
            return configured
        slug = climate_id.split(".", 1)[-1]
        for candidate in (f"sensor.{slug}_outdoor", "sensor.sim_outdoor_temperature"):
            st = self.hass.states.get(candidate)
            if st is not None and st.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                try:
                    return float(st.state)
                except TypeError, ValueError:
                    continue
        return None

    async def _async_apply_ac_buffer_offset(self, *, activate: bool) -> None:
        """Shift the configured climate target temperature or restore the previous setpoint and mode."""
        climate_id = self.config_entry.data.get(CONF_CLIMATE_ENTITY)
        if not climate_id:
            return
        state = self.hass.states.get(climate_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        if activate:
            if state.state == "off":
                if not self.ac_auto_heat_enabled:
                    return
                outdoor_temp = self._read_outdoor_temperature(climate_id)
                if outdoor_temp is not None and outdoor_temp > self.ac_auto_heat_max_outdoor_temp:
                    return
                self._ac_saved_hvac_mode = "off"
                raw_target = state.attributes.get("temperature")
                try:
                    base_temp = float(raw_target) if raw_target is not None else AC_AUTO_HEAT_DEFAULT_TEMP
                except TypeError, ValueError:
                    base_temp = AC_AUTO_HEAT_DEFAULT_TEMP
                self._ac_saved_temperature = base_temp
                max_temp = float(state.attributes.get("max_temp", 31.0))
                target_temp = min(max_temp, base_temp + self.ac_buffer_temp_offset)
                await self.hass.services.async_call(
                    "climate",
                    "set_hvac_mode",
                    {ATTR_ENTITY_ID: climate_id, "hvac_mode": "heat"},
                    blocking=False,
                )
                await self.hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {ATTR_ENTITY_ID: climate_id, "temperature": target_temp},
                    blocking=False,
                )
                self.record_trace(
                    category="ac",
                    action=f"Klimaanlage automatisch gestartet (Heizen auf {target_temp:.1f} °C)",
                    reason=f"Klima war aus; Außentemp ({outdoor_temp:.1f} °C) <= {self.ac_auto_heat_max_outdoor_temp:.1f} °C bei PV-Überschuss",
                    target=climate_id,
                    value=f"{target_temp:.1f} °C",
                    details={"target_temp": target_temp, "outdoor_temp": outdoor_temp},
                )
                return

            current_target = state.attributes.get("temperature")
            if current_target is None:
                return
            try:
                base_temp = float(current_target)
            except TypeError, ValueError:
                return
            self._ac_saved_hvac_mode = state.state
            self._ac_saved_temperature = base_temp
            min_temp = float(state.attributes.get("min_temp", 10.0))
            max_temp = float(state.attributes.get("max_temp", 31.0))
            if state.state == "cool":
                target_temp = max(min_temp, base_temp - self.ac_buffer_temp_offset)
            else:
                target_temp = min(max_temp, base_temp + self.ac_buffer_temp_offset)
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {ATTR_ENTITY_ID: climate_id, "temperature": target_temp},
                blocking=False,
            )
            self.record_trace(
                category="ac",
                action=f"Klima-Sollwert verschoben ({base_temp:.1f} °C → {target_temp:.1f} °C)",
                reason=f"Pufferbetrieb aktiv (+{self.ac_buffer_temp_offset} °C bei PV-Überschuss)",
                target=climate_id,
                value=f"{target_temp:.1f} °C",
                details={"base_temp": base_temp, "target_temp": target_temp},
            )
        else:
            if self._ac_saved_temperature is not None:
                restore_temp = self._ac_saved_temperature
                self._ac_saved_temperature = None
                await self.hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {ATTR_ENTITY_ID: climate_id, "temperature": restore_temp},
                    blocking=False,
                )
                self.record_trace(
                    category="ac",
                    action=f"Klima-Sollwert zurückgestellt ({restore_temp:.1f} °C)",
                    reason="Pufferbetrieb beendet",
                    target=climate_id,
                    value=f"{restore_temp:.1f} °C",
                )
            if self._ac_saved_hvac_mode == "off":
                self._ac_saved_hvac_mode = None
                await self.hass.services.async_call(
                    "climate",
                    "set_hvac_mode",
                    {ATTR_ENTITY_ID: climate_id, "hvac_mode": "off"},
                    blocking=False,
                )
                self.record_trace(
                    category="ac",
                    action="Klimaanlage wieder ausgeschaltet",
                    reason="Auto-Heat Pufferbetrieb beendet",
                    target=climate_id,
                    value="off",
                )
            else:
                self._ac_saved_hvac_mode = None

    async def _async_update_ev_charging(
        self,
        *,
        now_utc: datetime,
        grid_filtered: float,
        surplus_power: float,
        ev_power: float,
        ev_soc: float | None,
        ev_ready_at_home: bool,
        ev_plugged: bool,
        battery_priority_active: bool,
        battery_soc: float | None,
        yield_to_higher_priority: bool = False,
        in_deadband: bool,
    ) -> None:
        """Evaluate EV charging mode, hysteresis, BLE wake-up, and current setpoint."""
        max_amps = int(self.tesla_max_current)
        was_charging = self._ev_charging_active

        if self.charging_mode == CHARGING_MODE_FAST and ev_soc is not None and ev_soc >= self.tesla_target_soc:
            self.charging_mode = CHARGING_MODE_OFF
            self._ev_fast_charge_target_amps = None
            self._ev_stop_reason = (
                f"Schnellladen beendet: Ziel-SoC erreicht ({ev_soc:.0f}% ≥ {self.tesla_target_soc:.0f}%)"
            )

        if self.charging_mode == CHARGING_MODE_OFF:
            self._ev_charging_active = False
            self._ev_target_amps = 0
            self._ev_fast_charge_target_amps = None
            self._ev_low_surplus_since = None
            if not self._ev_stop_reason:
                self._ev_stop_reason = "Lademodus ist 'Aus'"
        elif not ev_ready_at_home:
            self._ev_charging_active = False
            self._ev_target_amps = 0
            self._ev_fast_charge_target_amps = None
            self._ev_low_surplus_since = None
            if not ev_plugged:
                self._ev_stop_reason = "Fahrzeug nicht angesteckt (Ladekabel getrennt)"
            else:
                self._ev_stop_reason = "Fahrzeug nicht zuhause / BLE nicht erreichbar"
        elif self.charging_mode == CHARGING_MODE_FAST:
            self._ev_charging_active = True
            self._ev_low_surplus_since = None
            self._ev_stop_reason = None
            if not was_charging or self._ev_fast_charge_target_amps is None:
                self._ev_fast_charge_target_amps = max_amps
                self._ev_target_amps = max_amps
            else:
                current_amps = self._read_float(CONF_EV_CURRENT_NUMBER)
                if current_amps is not None and current_amps >= EV_MIN_CURRENT_A:
                    self._ev_target_amps = round(current_amps)
                else:
                    self._ev_target_amps = self._ev_fast_charge_target_amps
        elif self.charging_mode == CHARGING_MODE_PV_SURPLUS:
            self._ev_fast_charge_target_amps = None
            if yield_to_higher_priority:
                self._ev_charging_active = False
                self._ev_target_amps = 0
                self._ev_low_surplus_since = None
                self._ev_stop_reason = "Warmwasser-Wärmepumpe hat Vorrang (Prio-Kaskade)"
            elif battery_priority_active:
                self._ev_charging_active = False
                self._ev_target_amps = 0
                self._ev_low_surplus_since = None
                soc_str = f"{battery_soc:.0f}%" if battery_soc is not None else "?"
                self._ev_stop_reason = (
                    f"Heimspeicher-Priorität aktiv (Akku {soc_str} < Reserve {self.battery_reserve_soc:.0f}%)"
                )
            else:
                avail_power = surplus_power + max(0.0, ev_power)
                if not self._ev_charging_active:
                    if avail_power >= self.ev_min_surplus_watts:
                        self._ev_charging_active = True
                        self._ev_low_surplus_since = None
                        self._ev_stop_reason = None
                        self._ev_target_amps = compute_ev_target_current(surplus_power, ev_power, max_amps)
                    else:
                        self._ev_target_amps = 0
                        self._ev_stop_reason = (
                            f"Zu wenig PV-Überschuss ({avail_power:.0f} W < {self.ev_min_surplus_watts:.0f} W)"
                        )
                else:
                    if not in_deadband:
                        self._ev_target_amps = compute_ev_target_current(surplus_power, ev_power, max_amps)
                    # Stop timer when charging below 5 A while importing power from the grid
                    low_current_grid_import = (
                        self._ev_target_amps < EV_STOP_BELOW_CURRENT_A and grid_filtered > EV_STOP_GRID_IMPORT_WATTS
                    ) or avail_power < (EV_MIN_CURRENT_A * EV_VOLTAGE)
                    if low_current_grid_import:
                        if self._ev_low_surplus_since is None:
                            self._ev_low_surplus_since = now_utc
                        elapsed = (now_utc - self._ev_low_surplus_since).total_seconds()
                        if elapsed >= self.ev_cloud_hysteresis_seconds:
                            self._ev_charging_active = False
                            self._ev_target_amps = 0
                            self._ev_low_surplus_since = None
                            self._ev_stop_reason = f"Wolkenpuffer ({self.ev_cloud_hysteresis_seconds:.0f}s) abgelaufen bei Netzbezug ({grid_filtered:.0f} W)"
                        else:
                            self._ev_target_amps = max(EV_MIN_CURRENT_A, self._ev_target_amps)
                    else:
                        self._ev_low_surplus_since = None

        if self._ev_charging_active and not was_charging:
            await self._async_trigger_ev_wakeup()
            await self._async_wait_for_ev_awake()
            await self._async_poll_ev_telemetry(now_utc, force=True)

        await self._async_sync_ev_actuators(was_charging=was_charging)
        await self._async_poll_ev_telemetry(now_utc)

    async def _async_sync_battery_lock(self, *, ev_power: float = 0.0) -> None:
        """Synchronize the physical home battery discharge lock entity if configured."""
        entity_id = self.config_entry.data.get(CONF_BATTERY_DISCHARGE_LOCK_SWITCH)
        if not entity_id or self.hass.states.get(entity_id) is None:
            return
        domain = entity_id.split(".", 1)[0]
        if domain == "select":
            state = self.hass.states.get(entity_id)
            target_option = "charge" if self._battery_lock_active else "discharge"
            if state is not None and state.state != target_option:
                await self.hass.services.async_call(
                    "select",
                    "select_option",
                    {ATTR_ENTITY_ID: entity_id, "option": target_option},
                    blocking=False,
                )
                self.record_trace(
                    category="battery",
                    action=f"Speichermodus auf '{target_option}' gesetzt",
                    reason=f"EV-Ladeleistung ({ev_power:.0f} W) > Schwelle"
                    if target_option == "charge"
                    else "Nachlaufzeit abgelaufen",
                    target=entity_id,
                    value=target_option,
                )
            return
        is_currently_on = self._read_bool(CONF_BATTERY_DISCHARGE_LOCK_SWITCH)
        if self._battery_lock_active and not is_currently_on:
            await self.hass.services.async_call(
                domain,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: entity_id},
                blocking=False,
            )
            self.record_trace(
                category="battery",
                action="Batterie-Entladesperre aktiviert",
                reason=f"EV-Ladeleistung ({ev_power:.0f} W) > Schwelle ({self.battery_lock_threshold_watts:.0f} W)",
                target=entity_id,
                value="on",
                details={"ev_power_watts": ev_power, "threshold_watts": self.battery_lock_threshold_watts},
            )
        elif not self._battery_lock_active and is_currently_on:
            await self.hass.services.async_call(
                domain,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: entity_id},
                blocking=False,
            )
            self.record_trace(
                category="battery",
                action="Batterie-Entladesperre aufgehoben",
                reason=f"EV-Leistung niedrig; Nachlaufzeit ({self.battery_lock_release_seconds:.0f}s) abgelaufen",
                target=entity_id,
                value="off",
                details={"ev_power_watts": ev_power},
            )

    async def _async_trigger_ev_wakeup(self) -> None:
        """Press the BLE wake-up button before starting a charging session."""
        button_id = self.config_entry.data.get(CONF_EV_WAKEUP_BUTTON)
        if button_id and self.hass.states.get(button_id) is not None:
            if not self.hass.services.has_service("button", "press"):
                return
            await self.hass.services.async_call(
                "button",
                "press",
                {ATTR_ENTITY_ID: button_id},
                blocking=False,
            )
            self.record_trace(
                category="ev",
                action="Tesla Wake-Up ausgelöst",
                reason="Ladevorgang beginnt (Fahrzeug wird aufgeweckt)",
                target=button_id,
                value="press",
            )

    def resolve_ev_awake_entity(self) -> str | None:
        """Return configured or auto-discovered EV awake binary sensor."""
        configured = self.config_entry.data.get(CONF_EV_AWAKE_BINARY_SENSOR)
        if configured and self.hass.states.get(configured) is not None:
            return configured

        # Try to infer from wakeup button or charger switch entity ID
        for ref_key in (CONF_EV_WAKEUP_BUTTON, CONF_EV_CHARGING_SWITCH):
            ref_entity = self.config_entry.data.get(ref_key)
            if not ref_entity:
                continue
            base = ref_entity.split(".", 1)[-1]
            for suffix in ("_wake_up_car", "_wakeup_button", "_charger", "_charging"):
                if base.endswith(suffix):
                    base = base[: -len(suffix)]
                    break
            candidate = f"binary_sensor.{base}_awake"
            if self.hass.states.get(candidate) is not None:
                return candidate

        # Fallback check for test / standard entity
        for fallback in ("binary_sensor.tesla_awake", "binary_sensor.ev_awake"):
            if self.hass.states.get(fallback) is not None:
                return fallback

        return None

    def resolve_ev_force_update_button(self) -> str | None:
        """Return configured or auto-discovered EV telemetry refresh button."""
        configured = self.config_entry.data.get(CONF_EV_FORCE_UPDATE_BUTTON)
        if configured and self.hass.states.get(configured) is not None:
            return configured

        # Try to infer from wakeup button or charger switch entity ID
        for ref_key in (CONF_EV_WAKEUP_BUTTON, CONF_EV_CHARGING_SWITCH):
            ref_entity = self.config_entry.data.get(ref_key)
            if not ref_entity:
                continue
            base = ref_entity.split(".", 1)[-1]
            for suffix in ("_wake_up_car", "_wakeup_button", "_charger", "_charging"):
                if base.endswith(suffix):
                    base = base[: -len(suffix)]
                    break
            for candidate in (
                f"button.{base}_force_update_env",
                f"button.{base}_refresh",
            ):
                if self.hass.states.get(candidate) is not None:
                    return candidate

        for fallback in ("button.tesla_force_update_env", "button.ev_force_update_env"):
            if self.hass.states.get(fallback) is not None:
                return fallback

        return None

    async def _async_poll_ev_telemetry(self, now_utc: datetime, *, force: bool = False) -> None:
        """Periodically refresh Tesla BLE telemetry during active charging without keeping it awake when idle."""
        # Never poll when vehicle is idle / not actively charging (to prevent phantom drain & preserve deep sleep)
        if not self._ev_charging_active and not force:
            self._last_ev_poll_utc = None
            return

        button_id = self.resolve_ev_force_update_button()
        if not button_id or self.hass.states.get(button_id) is None:
            return

        if not force and self._last_ev_poll_utc is not None:
            elapsed = (now_utc - self._last_ev_poll_utc).total_seconds()
            if elapsed < self.ev_poll_interval_seconds:
                return

        self._last_ev_poll_utc = now_utc
        try:
            if self.hass.services.has_service("button", "press"):
                await self.hass.services.async_call(
                    "button",
                    "press",
                    {ATTR_ENTITY_ID: button_id},
                    blocking=False,
                )
                self.record_trace(
                    category="ev",
                    action="Tesla BLE Telemetrie aktualisiert",
                    reason="Startabfrage nach Aufwachen"
                    if force
                    else f"Zyklische Abfrage während Ladevorgang ({self.ev_poll_interval_seconds:.0f}s Intervall)",
                    target=button_id,
                    value="press",
                    details={"interval_seconds": self.ev_poll_interval_seconds},
                )
        except HomeAssistantError as err:
            LOGGER.warning("Konnte Tesla BLE Update-Button %s nicht auslösen: %s", button_id, err)

    def _is_ev_awake(self, awake_entity: str | None = None) -> bool:
        """Check whether the EV is currently awake."""
        entity_id = awake_entity or self.resolve_ev_awake_entity()
        if entity_id:
            state = self.hass.states.get(entity_id)
            if state is not None:
                if state.state.lower() in ("on", "true", "1"):
                    return True
                if state.state.lower() in ("off", "false", "0"):
                    return False

        # If no awake sensor, or state unknown, check if car is already actively drawing charging power
        ev_power = self._read_float(CONF_EV_POWER_SENSOR)
        if ev_power is not None and ev_power > 100.0:
            return True

        return False

    async def _async_wait_for_ev_awake(self) -> None:
        """Wait for the EV to wake up after a wake-up command, up to ev_wakeup_delay_seconds."""
        awake_entity = self.resolve_ev_awake_entity()
        max_wait = max(0.0, float(self.ev_wakeup_delay_seconds))
        if max_wait <= 0:
            return

        # If already awake, proceed immediately
        if self._is_ev_awake(awake_entity):
            return

        self.record_trace(
            category="ev",
            action=f"Warte auf Aufwachen des Fahrzeugs (max. {max_wait:.0f}s)",
            reason="Fahrzeug schläft noch; Ladebefehle werden verzögert",
            target=awake_entity or "timer",
            value=f"{max_wait:.0f}s",
        )

        poll_interval = 0.5
        elapsed = 0.0
        while elapsed < max_wait:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            if awake_entity and self._is_ev_awake(awake_entity):
                await asyncio.sleep(0.5)
                self.record_trace(
                    category="ev",
                    action=f"Fahrzeug ist wach ({elapsed:.1f}s)",
                    reason="Awake-Sensor meldet 'on'; Ladevorgang wird freigegeben",
                    target=awake_entity,
                    value="on",
                )
                return

        if not awake_entity:
            self.record_trace(
                category="ev",
                action="Aufwach-Verzögerung abgelaufen",
                reason=f"Feste Wartezeit ({max_wait:.0f}s) beendet; starte Ladevorgang",
                target="timer",
                value="done",
            )

    async def _async_sync_ev_actuators(self, *, was_charging: bool = False) -> None:
        """Propagate target current and charging switch state to BLE/MQTT entities only on change."""
        number_id = self.config_entry.data.get(CONF_EV_CURRENT_NUMBER)
        if number_id and self._ev_target_amps >= EV_MIN_CURRENT_A and self.hass.states.get(number_id) is not None:
            current_amps = self._read_float(CONF_EV_CURRENT_NUMBER)
            if current_amps is None or round(current_amps) != self._ev_target_amps:
                await self.hass.services.async_call(
                    "number",
                    "set_value",
                    {ATTR_ENTITY_ID: number_id, "value": self._ev_target_amps},
                    blocking=False,
                )
                self.record_trace(
                    category="ev",
                    action=f"Tesla Ladestrom angepasst: {round(current_amps) if current_amps is not None else 0} A → {self._ev_target_amps} A",
                    reason="Schnellladen aktiv"
                    if self.charging_mode == CHARGING_MODE_FAST
                    else f"PV-Überschuss-Regelung (Sollwert: {self._ev_target_amps} A)",
                    target=number_id,
                    value=f"{self._ev_target_amps} A",
                    details={"target_amps": self._ev_target_amps},
                )

        switch_id = self.config_entry.data.get(CONF_EV_CHARGING_SWITCH)
        if switch_id and self.hass.states.get(switch_id) is not None:
            is_on = self._read_bool(CONF_EV_CHARGING_SWITCH)
            if self._ev_charging_active and not is_on:
                await self.hass.services.async_call(
                    "switch",
                    SERVICE_TURN_ON,
                    {ATTR_ENTITY_ID: switch_id},
                    blocking=False,
                )
                self.record_trace(
                    category="ev",
                    action=f"Tesla Ladevorgang gestartet ({self._ev_target_amps} A)",
                    reason="PV-Überschuss verfügbar"
                    if self.charging_mode == CHARGING_MODE_PV_SURPLUS
                    else "Schnellladen aktiv",
                    target=switch_id,
                    value="on",
                    details={"amps": self._ev_target_amps, "mode": self.charging_mode},
                )
            elif not self._ev_charging_active and is_on:
                if self.charging_mode != CHARGING_MODE_OFF or was_charging:
                    await self.hass.services.async_call(
                        "switch",
                        SERVICE_TURN_OFF,
                        {ATTR_ENTITY_ID: switch_id},
                        blocking=False,
                    )
                    self.record_trace(
                        category="ev",
                        action="Tesla Ladevorgang gestoppt",
                        reason=self._ev_stop_reason or "Ladebedingungen nicht mehr erfüllt",
                        target=switch_id,
                        value="off",
                    )

    async def async_set_parameter(self, key: str, value: float, *, refresh: bool = True) -> None:
        """Update a numeric parameter or threshold on the coordinator and optionally refresh."""
        setattr(self, key, float(value))
        if refresh:
            await self.async_refresh()
        elif self.data is not None:
            self.data[key] = float(value)

    async def async_set_battery_reserve_soc(self, value: float) -> None:
        """Update the home battery reserve SOC threshold and refresh."""
        await self.async_set_parameter("battery_reserve_soc", max(0.0, min(100.0, float(value))))

    async def async_set_tesla_max_current(self, value: float) -> None:
        """Update the maximum 1-phase charging current and refresh."""
        self._ev_fast_charge_target_amps = None
        await self.async_set_parameter("tesla_max_current", max(float(EV_MIN_CURRENT_A), min(16.0, round(value))))

    async def async_set_tesla_target_soc(self, value: float) -> None:
        """Update the fast-charging target SOC and refresh."""
        await self.async_set_parameter("tesla_target_soc", max(50.0, min(100.0, float(value))))

    async def async_set_charging_mode(self, mode: str) -> None:
        """Update the EV charging mode and refresh."""
        if mode not in CHARGING_MODES:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_charging_mode",
                translation_placeholders={"mode": mode},
            )
        if mode != CHARGING_MODE_FAST:
            self._ev_fast_charge_target_amps = None
        self.charging_mode = mode
        await self.async_refresh()

    async def async_set_priority_order(self, order: str) -> None:
        """Update the surplus consumer priority cascade order and refresh."""
        if order not in PRIORITY_ORDERS:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_priority_order",
                translation_placeholders={"order": order},
            )
        self.priority_order = order
        await self.async_refresh()

    async def async_set_ac_buffer_enabled(self, *, enabled: bool) -> None:
        """Enable or disable the thermal AC buffer and refresh."""
        self.ac_buffer_enabled = enabled
        await self.async_refresh()

    async def async_set_ac_auto_heat_enabled(self, *, enabled: bool) -> None:
        """Enable or disable automatic climate heating startup when off and outdoor temp is low."""
        self.ac_auto_heat_enabled = enabled
        await self.async_refresh()

    async def async_set_dhw_enabled(self, *, enabled: bool) -> None:
        """Enable or disable automatic domestic hot water heat pump control and refresh."""
        self.dhw_enabled = enabled
        await self.async_refresh()

    def record_trace(
        self,
        *,
        category: str,
        action: str,
        reason: str,
        target: str | None = None,
        value: Any = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record an action trace in memory and log it when action tracing is enabled."""
        if not self.action_tracing_enabled:
            return

        now = dt_util.now()
        trace_entry = {
            "timestamp": now.isoformat(timespec="seconds"),
            "time": now.strftime("%H:%M:%S"),
            "category": category,
            "action": action,
            "reason": reason,
            "target": target,
            "value": str(value) if value is not None else None,
            "details": details or {},
        }
        self._recent_traces.append(trace_entry)
        if len(self._recent_traces) > MAX_ACTION_TRACES:
            self._recent_traces.pop(0)

        LOGGER.info(
            "[Trace][%s] %s%s -> %s (Grund: %s)",
            category.upper(),
            f"{target} " if target else "",
            f"[{value}]" if value is not None else "",
            action,
            reason,
        )

    def clear_traces(self) -> None:
        """Clear all in-memory action traces."""
        self._recent_traces.clear()

    async def async_set_action_tracing_enabled(self, *, enabled: bool) -> None:
        """Enable or disable action tracing and refresh."""
        self.action_tracing_enabled = enabled
        if enabled:
            self.record_trace(
                category="system",
                action="Aktions-Tracing aktiviert",
                reason="Benutzer hat Tracing-Schalter eingeschaltet",
            )
        await self.async_refresh()

    def restore_sensor_value(
        self,
        key: str,
        value: Any,
        *,
        attributes: dict[str, Any] | None = None,
        last_updated: datetime | None = None,
    ) -> None:
        """Restore lifetime and same-day energy counters across Home Assistant restarts."""
        if key == "ev_solar_lifetime_kwh":
            self.session_tracker.solar_lifetime_kwh = max(self.session_tracker.solar_lifetime_kwh, float(value))
        elif key == "ev_grid_lifetime_kwh":
            self.session_tracker.grid_lifetime_kwh = max(self.session_tracker.grid_lifetime_kwh, float(value))
        elif key == "last_session_summary" and isinstance(value, str) and value:
            self.session_tracker.last_summary = value
            if attributes:
                self.session_tracker.last_session_data = dict(attributes)
        elif key in ("daily_home_kwh", "daily_pv_kwh", "daily_grid_import_kwh", "daily_grid_export_kwh"):
            today = dt_util.as_local(dt_util.utcnow()).date()
            if last_updated is None or dt_util.as_local(last_updated).date() == today:
                self._daily_date = today
                attr_name = f"_{key}"
                setattr(self, attr_name, max(getattr(self, attr_name, 0.0), float(value)))
        if self.data is not None and key in self.data:
            self.data[key] = value
