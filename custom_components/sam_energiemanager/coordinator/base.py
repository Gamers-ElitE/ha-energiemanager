"""Data update coordinator for sam_energiemanager."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from custom_components.sam_energiemanager.const import (
    AC_BUFFER_MAX_SURPLUS_WATTS,
    AC_BUFFER_MIN_HOLD_SECONDS,
    AC_BUFFER_MIN_SURPLUS_WATTS,
    BATTERY_LOCK_RELEASE_SECONDS,
    BATTERY_LOCK_THRESHOLD_WATTS,
    CHARGING_MODE_FAST,
    CHARGING_MODE_OFF,
    CHARGING_MODE_PV_SURPLUS,
    CHARGING_MODES,
    CONF_BATTERY_DISCHARGE_LOCK_SWITCH,
    CONF_BATTERY_SOC_SENSOR,
    CONF_ELECTRICITY_PRICE,
    CONF_EV_BLE_CONNECTED_BINARY_SENSOR,
    CONF_EV_CHARGING_SWITCH,
    CONF_EV_CURRENT_NUMBER,
    CONF_EV_POWER_SENSOR,
    CONF_EV_SOC_SENSOR,
    CONF_EV_WAKEUP_BUTTON,
    CONF_GRID_POWER_SENSOR,
    DEFAULT_BATTERY_RESERVE_SOC,
    DEFAULT_ELECTRICITY_PRICE,
    DEFAULT_TESLA_MAX_CURRENT,
    DEFAULT_TESLA_TARGET_SOC,
    DOMAIN,
    EV_CLOUD_HYSTERESIS_SECONDS,
    EV_MIN_CURRENT_A,
    EV_MIN_SURPLUS_WATTS,
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
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .cascade import SessionTracker, compute_ema, compute_ev_target_current, compute_surplus_watts, is_within_deadband

if TYPE_CHECKING:
    from custom_components.sam_energiemanager.data import EnergiemanagerConfigEntry


class EnergiemanagerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate zero-export filtering, priority cascade, EV charging, and WashData tracking."""

    config_entry: EnergiemanagerConfigEntry

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the Energiemanager coordinator state."""
        super().__init__(*args, **kwargs)
        self.battery_reserve_soc: float = DEFAULT_BATTERY_RESERVE_SOC
        self.tesla_max_current: float = DEFAULT_TESLA_MAX_CURRENT
        self.tesla_target_soc: float = DEFAULT_TESLA_TARGET_SOC
        self.charging_mode: str = CHARGING_MODE_PV_SURPLUS
        self.ac_buffer_enabled: bool = False

        self._grid_ema: float | None = None
        self._last_update_utc: datetime | None = None
        self._battery_lock_active: bool = False
        self._battery_low_power_since: datetime | None = None
        self._ev_low_surplus_since: datetime | None = None
        self._ev_charging_active: bool = False
        self._ev_target_amps: int = 0
        self._ac_buffer_active: bool = False
        self._ac_buffer_activated_at: datetime | None = None
        self.session_tracker = SessionTracker()

    def _read_float(self, conf_key: str, default: float | None = None) -> float | None:
        """Read a numeric state from a configured entity ID."""
        entity_id = self.config_entry.data.get(conf_key)
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return default
        try:
            return float(state.state)
        except TypeError, ValueError:
            return default

    def _read_bool(self, conf_key: str, *, default: bool = False) -> bool:
        """Read a boolean state from a configured entity ID."""
        entity_id = self.config_entry.data.get(conf_key)
        if not entity_id:
            return default
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return default
        return state.state.lower() in (STATE_ON, "true", "connected", "plugged", "charging", "1")

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

        grid_raw = self._read_float(CONF_GRID_POWER_SENSOR, 0.0) or 0.0
        battery_soc = self._read_float(CONF_BATTERY_SOC_SENSOR)
        ev_power = self._read_float(CONF_EV_POWER_SENSOR, 0.0) or 0.0
        ev_soc = self._read_float(CONF_EV_SOC_SENSOR)
        ev_ble_connected = self._read_bool(CONF_EV_BLE_CONNECTED_BINARY_SENSOR, default=True)

        # A. EMA Filter & Deadband
        self._grid_ema = compute_ema(grid_raw, self._grid_ema)
        grid_filtered = round(self._grid_ema, 1)
        in_deadband = is_within_deadband(grid_filtered)
        surplus_power = round(compute_surplus_watts(grid_filtered), 1)

        # B. Stage 2: Home Battery Priority
        battery_priority_active = (
            self.battery_reserve_soc > 0.0 and battery_soc is not None and battery_soc < self.battery_reserve_soc
        )

        # C. Home Battery Hardware Discharge Lock (>250 W immediate lock, <=250 W for 60 s unlock)
        if ev_power > BATTERY_LOCK_THRESHOLD_WATTS:
            self._battery_lock_active = True
            self._battery_low_power_since = None
        elif self._battery_lock_active:
            if self._battery_low_power_since is None:
                self._battery_low_power_since = now_utc
            elif (now_utc - self._battery_low_power_since).total_seconds() >= BATTERY_LOCK_RELEASE_SECONDS:
                self._battery_lock_active = False
                self._battery_low_power_since = None

        await self._async_sync_battery_lock()

        # B. Stage 3: Thermal AC Buffer (500 W - 1350 W, 20 min minimum hold)
        self._update_ac_buffer(
            now_utc=now_utc,
            surplus_power=surplus_power,
            battery_priority_active=battery_priority_active,
            in_deadband=in_deadband,
        )

        # D. Stage 4: 1-Phase Tesla Charging Control
        await self._async_update_ev_charging(
            now_utc=now_utc,
            surplus_power=surplus_power,
            ev_power=ev_power,
            ev_soc=ev_soc,
            ev_ble_connected=ev_ble_connected,
            battery_priority_active=battery_priority_active,
            in_deadband=in_deadband,
        )

        # E. WashData Session Tracking & Energy Split
        price = float(self.config_entry.options.get(CONF_ELECTRICITY_PRICE, DEFAULT_ELECTRICITY_PRICE))
        ev_solar_w, ev_grid_w, completed_session = self.session_tracker.update(
            ev_watts=ev_power,
            grid_raw_watts=grid_raw,
            ev_soc=ev_soc,
            dt_hours=dt_hours,
            price_eur_per_kwh=price,
            now_utc=now_utc,
        )
        if completed_session is not None:
            self.hass.bus.async_fire(EVENT_SESSION_COMPLETED, completed_session)

        return {
            "grid_power_filtered": grid_filtered,
            "surplus_power": surplus_power,
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
            "ac_buffer_active": self._ac_buffer_active,
            "battery_discharge_lock_active": self._battery_lock_active,
        }

    def _update_ac_buffer(
        self,
        *,
        now_utc: datetime,
        surplus_power: float,
        battery_priority_active: bool,
        in_deadband: bool,
    ) -> None:
        """Update the thermal AC buffer state with 20-minute compressor protection."""
        if not self.ac_buffer_enabled:
            self._ac_buffer_active = False
            self._ac_buffer_activated_at = None
            return

        if self._ac_buffer_active and self._ac_buffer_activated_at is not None:
            elapsed = (now_utc - self._ac_buffer_activated_at).total_seconds()
            if elapsed < AC_BUFFER_MIN_HOLD_SECONDS:
                return

        if in_deadband:
            return

        in_window = AC_BUFFER_MIN_SURPLUS_WATTS <= surplus_power <= AC_BUFFER_MAX_SURPLUS_WATTS
        if not battery_priority_active and in_window:
            if not self._ac_buffer_active:
                self._ac_buffer_active = True
                self._ac_buffer_activated_at = now_utc
        else:
            self._ac_buffer_active = False
            self._ac_buffer_activated_at = None

    async def _async_update_ev_charging(
        self,
        *,
        now_utc: datetime,
        surplus_power: float,
        ev_power: float,
        ev_soc: float | None,
        ev_ble_connected: bool,
        battery_priority_active: bool,
        in_deadband: bool,
    ) -> None:
        """Evaluate EV charging mode, hysteresis, BLE wake-up, and current setpoint."""
        max_amps = int(self.tesla_max_current)
        was_charging = self._ev_charging_active

        if self.charging_mode == CHARGING_MODE_FAST and ev_soc is not None and ev_soc >= self.tesla_target_soc:
            self.charging_mode = CHARGING_MODE_OFF

        if self.charging_mode == CHARGING_MODE_OFF or not ev_ble_connected:
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
                if avail_power >= EV_MIN_SURPLUS_WATTS:
                    self._ev_low_surplus_since = None
                    if not (in_deadband and self._ev_charging_active):
                        self._ev_target_amps = compute_ev_target_current(surplus_power, ev_power, max_amps)
                    self._ev_charging_active = True
                elif self._ev_charging_active:
                    if self._ev_low_surplus_since is None:
                        self._ev_low_surplus_since = now_utc
                    elapsed = (now_utc - self._ev_low_surplus_since).total_seconds()
                    if elapsed < EV_CLOUD_HYSTERESIS_SECONDS:
                        self._ev_target_amps = EV_MIN_CURRENT_A
                    else:
                        self._ev_charging_active = False
                        self._ev_target_amps = 0
                        self._ev_low_surplus_since = None
                else:
                    self._ev_target_amps = 0

        if self._ev_charging_active and not was_charging:
            await self._async_trigger_ev_wakeup()

        await self._async_sync_ev_actuators()

    async def _async_sync_battery_lock(self) -> None:
        """Synchronize the physical home battery discharge lock switch if configured."""
        switch_id = self.config_entry.data.get(CONF_BATTERY_DISCHARGE_LOCK_SWITCH)
        if not switch_id or self.hass.states.get(switch_id) is None:
            return
        is_currently_on = self._read_bool(CONF_BATTERY_DISCHARGE_LOCK_SWITCH)
        if self._battery_lock_active and not is_currently_on:
            await self.hass.services.async_call(
                "switch",
                SERVICE_TURN_ON,
                {ATTR_ENTITY_ID: switch_id},
                blocking=False,
            )
        elif not self._battery_lock_active and is_currently_on:
            await self.hass.services.async_call(
                "switch",
                SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: switch_id},
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
        """Propagate target current and charging switch state to BLE/MQTT entities."""
        number_id = self.config_entry.data.get(CONF_EV_CURRENT_NUMBER)
        if number_id and self._ev_target_amps >= EV_MIN_CURRENT_A and self.hass.states.get(number_id) is not None:
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

    async def async_set_battery_reserve_soc(self, value: float) -> None:
        """Update the home battery reserve SOC threshold and refresh."""
        self.battery_reserve_soc = max(0.0, min(100.0, float(value)))
        await self.async_refresh()

    async def async_set_tesla_max_current(self, value: float) -> None:
        """Update the maximum 1-phase charging current and refresh."""
        self.tesla_max_current = max(float(EV_MIN_CURRENT_A), min(16.0, round(value)))
        await self.async_refresh()

    async def async_set_tesla_target_soc(self, value: float) -> None:
        """Update the fast-charging target SOC and refresh."""
        self.tesla_target_soc = max(50.0, min(100.0, float(value)))
        await self.async_refresh()

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
