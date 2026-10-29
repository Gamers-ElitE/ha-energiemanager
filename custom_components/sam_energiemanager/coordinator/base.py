"""Data update coordinator for sam_energiemanager."""

from collections.abc import Callable
from datetime import datetime
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
    DEADBAND_WATTS,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_ELECTRICITY_PRICE,
    DEFAULT_TESLA_MAX_CURRENT,
    DEFAULT_TESLA_TARGET_SOC,
    DOMAIN,
    EMA_ALPHA,
    EV_CLOUD_HYSTERESIS_SECONDS,
    EV_MIN_CURRENT_A,
    EV_MIN_SURPLUS_WATTS,
    EV_STOP_BELOW_CURRENT_A,
    EV_STOP_GRID_IMPORT_WATTS,
    EV_VOLTAGE,
    EVENT_SESSION_COMPLETED,
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
from homeassistant.exceptions import ServiceValidationError
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
        self.ac_buffer_enabled: bool = False
        self.ac_auto_heat_enabled: bool = False

        self.ema_alpha: float = EMA_ALPHA
        self.deadband_watts: float = DEADBAND_WATTS
        self.battery_lock_threshold_watts: float = BATTERY_LOCK_THRESHOLD_WATTS
        self.battery_lock_release_seconds: float = BATTERY_LOCK_RELEASE_SECONDS
        self.ac_buffer_min_surplus_watts: float = AC_BUFFER_MIN_SURPLUS_WATTS
        self.ac_buffer_max_surplus_watts: float = AC_BUFFER_MAX_SURPLUS_WATTS
        self.ac_buffer_temp_offset: float = AC_BUFFER_TEMP_OFFSET
        self.ac_buffer_min_hold_minutes: float = round(AC_BUFFER_MIN_HOLD_SECONDS / 60.0, 1)
        self.ac_auto_heat_max_outdoor_temp: float = AC_AUTO_HEAT_MAX_OUTDOOR_TEMP
        self.ev_min_surplus_watts: float = EV_MIN_SURPLUS_WATTS
        self.ev_cloud_hysteresis_seconds: float = EV_CLOUD_HYSTERESIS_SECONDS
        self.electricity_price: float = float(
            self.config_entry.options.get(CONF_ELECTRICITY_PRICE, DEFAULT_ELECTRICITY_PRICE)
        )

        self._grid_ema: float | None = None
        self._home_ema: float | None = None
        self._grid_window_samples: list[float] = []
        self._last_update_utc: datetime | None = None
        self._battery_lock_active: bool = False
        self._battery_low_power_since: datetime | None = None
        self._ev_low_surplus_since: datetime | None = None
        self._ev_charging_active: bool = False
        self._ev_target_amps: int = 0
        self._ac_buffer_active: bool = False
        self._ac_buffer_activated_at: datetime | None = None
        self._ac_saved_temperature: float | None = None
        self._ac_saved_hvac_mode: str | None = None
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
        return state.state.lower() in (STATE_ON, "true", "connected", "plugged", "charging", "1", "home")

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
        ev_ready_at_home = ev_plugged and ev_ble_connected

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

        await self._async_sync_battery_lock()

        # B. Stage 3: Thermal AC Buffer
        await self._async_update_ac_buffer(
            now_utc=now_utc,
            surplus_power=surplus_power,
            battery_priority_active=battery_priority_active,
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
            battery_priority_active=battery_priority_active,
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
            "electricity_price": self.electricity_price,
        }

    async def _async_update_ac_buffer(
        self,
        *,
        now_utc: datetime,
        surplus_power: float,
        battery_priority_active: bool,
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
            if self._ac_saved_hvac_mode == "off":
                self._ac_saved_hvac_mode = None
                await self.hass.services.async_call(
                    "climate",
                    "set_hvac_mode",
                    {ATTR_ENTITY_ID: climate_id, "hvac_mode": "off"},
                    blocking=False,
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
        battery_priority_active: bool,
        in_deadband: bool,
    ) -> None:
        """Evaluate EV charging mode, hysteresis, BLE wake-up, and current setpoint."""
        max_amps = int(self.tesla_max_current)
        was_charging = self._ev_charging_active

        if self.charging_mode == CHARGING_MODE_FAST and ev_soc is not None and ev_soc >= self.tesla_target_soc:
            self.charging_mode = CHARGING_MODE_OFF

        if self.charging_mode == CHARGING_MODE_OFF or not ev_ready_at_home:
            self._ev_charging_active = False
            self._ev_target_amps = 0
            self._ev_low_surplus_since = None
        elif self.charging_mode == CHARGING_MODE_FAST:
            self._ev_charging_active = True
            self._ev_target_amps = max_amps
            self._ev_low_surplus_since = None
        elif self.charging_mode == CHARGING_MODE_PV_SURPLUS:
            if battery_priority_active:
                self._ev_charging_active = False
                self._ev_target_amps = 0
                self._ev_low_surplus_since = None
            else:
                avail_power = surplus_power + max(0.0, ev_power)
                if not self._ev_charging_active:
                    if avail_power >= self.ev_min_surplus_watts:
                        self._ev_charging_active = True
                        self._ev_low_surplus_since = None
                        self._ev_target_amps = compute_ev_target_current(surplus_power, ev_power, max_amps)
                    else:
                        self._ev_target_amps = 0
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
                        else:
                            self._ev_target_amps = max(EV_MIN_CURRENT_A, self._ev_target_amps)
                    else:
                        self._ev_low_surplus_since = None

        if self._ev_charging_active and not was_charging:
            await self._async_trigger_ev_wakeup()

        await self._async_sync_ev_actuators()

    async def _async_sync_battery_lock(self) -> None:
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
            return
        is_currently_on = self._read_bool(CONF_BATTERY_DISCHARGE_LOCK_SWITCH)
        if self._battery_lock_active and not is_currently_on:
            await self.hass.services.async_call(
                domain,
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: entity_id},
                blocking=False,
            )
        elif not self._battery_lock_active and is_currently_on:
            await self.hass.services.async_call(
                domain,
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: entity_id},
                blocking=False,
            )

    async def _async_trigger_ev_wakeup(self) -> None:
        """Press the BLE wake-up button before starting a charging session."""
        button_id = self.config_entry.data.get(CONF_EV_WAKEUP_BUTTON)
        if button_id and self.hass.states.get(button_id) is not None:
            await self.hass.services.async_call(
                "button",
                "press",
                {ATTR_ENTITY_ID: button_id},
                blocking=False,
            )

    async def _async_sync_ev_actuators(self) -> None:
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
            elif not self._ev_charging_active and is_on:
                await self.hass.services.async_call(
                    "switch",
                    SERVICE_TURN_OFF,
                    {ATTR_ENTITY_ID: switch_id},
                    blocking=False,
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
        self.charging_mode = mode
        await self.async_refresh()

    async def async_set_ac_buffer_enabled(self, *, enabled: bool) -> None:
        """Enable or disable the thermal AC buffer and refresh."""
        self.ac_buffer_enabled = enabled
        await self.async_refresh()

    async def async_set_ac_auto_heat_enabled(self, *, enabled: bool) -> None:
        """Enable or disable automatic climate heating startup when off and outdoor temp is low."""
        self.ac_auto_heat_enabled = enabled
        await self.async_refresh()
