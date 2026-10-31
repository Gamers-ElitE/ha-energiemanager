"""Constants for sam_energiemanager."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "sam_energiemanager"
ATTRIBUTION = "Calculated by SAM Energiemanager"

EVENT_SESSION_COMPLETED = f"{DOMAIN}_session_completed"

# Configuration keys - Source entities
CONF_GRID_POWER_SENSOR = "grid_power_sensor"
CONF_BATTERY_SOC_SENSOR = "battery_soc_sensor"
CONF_BATTERY_DISCHARGE_LOCK_SWITCH = "battery_discharge_lock_switch"
CONF_EV_POWER_SENSOR = "ev_power_sensor"
CONF_EV_SOC_SENSOR = "ev_soc_sensor"
CONF_EV_PLUGGED_BINARY_SENSOR = "ev_plugged_binary_sensor"
CONF_EV_BLE_CONNECTED_BINARY_SENSOR = "ev_ble_connected_binary_sensor"
CONF_EV_CURRENT_NUMBER = "ev_current_number"
CONF_EV_CHARGING_SWITCH = "ev_charging_switch"
CONF_EV_WAKEUP_BUTTON = "ev_wakeup_button"
CONF_EV_FORCE_UPDATE_BUTTON = "ev_force_update_button"
CONF_EV_AWAKE_BINARY_SENSOR = "ev_awake_binary_sensor"
CONF_CLIMATE_ENTITY = "climate_entity"
CONF_OUTDOOR_TEMP_SENSOR = "outdoor_temp_sensor"
CONF_PV_POWER_SENSOR = "pv_power_sensor"
CONF_BATTERY_POWER_SENSOR = "battery_power_sensor"
CONF_WATER_HEATER_ENTITY = "water_heater_entity"
CONF_WATER_TEMP_SENSOR = "water_temp_sensor"
CONF_SOLAR_PEAK_TIME_SENSOR = "solar_peak_time_sensor"

# Options keys
CONF_UPDATE_INTERVAL_SECONDS = "update_interval_seconds"
CONF_ELECTRICITY_PRICE = "electricity_price_eur_per_kwh"

# Defaults
DEFAULT_UPDATE_INTERVAL_SECONDS = 10
DEFAULT_ELECTRICITY_PRICE = 0.32
DEFAULT_BATTERY_RESERVE_SOC = 60.0
DEFAULT_TESLA_MAX_CURRENT = 13.0
DEFAULT_TESLA_TARGET_SOC = 80.0

# A. Zero-Export & EMA Filtering
EMA_ALPHA = 0.35
DEADBAND_WATTS = 60.0

# B. Thermal AC Buffer & DHW Heat Pump
AC_BUFFER_MIN_SURPLUS_WATTS = 500.0
AC_BUFFER_MAX_SURPLUS_WATTS = 1350.0
AC_BUFFER_TEMP_OFFSET = 2.5
AC_BUFFER_MIN_HOLD_SECONDS = 1200.0
AC_AUTO_HEAT_MAX_OUTDOOR_TEMP = 11.0
AC_AUTO_HEAT_DEFAULT_TEMP = 22.0

DHW_MIN_SURPLUS_WATTS = 500.0
DHW_STOP_GRID_IMPORT_WATTS = 200.0
DHW_TARGET_TEMP = 53.0
DHW_STOP_TEMP = 51.0
DHW_MIN_TEMP = 42.0
DHW_WINDOW_START_HOUR = 10
DHW_WINDOW_END_HOUR = 18

# C. Home Battery Discharge Lock
BATTERY_LOCK_THRESHOLD_WATTS = 250.0
BATTERY_LOCK_RELEASE_SECONDS = 60.0

# D. 1-Phase EV Charging (230 V)
EV_VOLTAGE = 230.0
EV_MIN_CURRENT_A = 3
EV_STOP_BELOW_CURRENT_A = 5
EV_STOP_GRID_IMPORT_WATTS = 300.0
EV_MAX_CURRENT_A = 16
EV_MIN_SURPLUS_WATTS = 1380.0
EV_CLOUD_HYSTERESIS_SECONDS = 300.0
DEFAULT_EV_WAKEUP_DELAY_SECONDS = 10.0
DEFAULT_EV_POLL_INTERVAL_SECONDS = 30.0

CHARGING_MODE_OFF = "off"
CHARGING_MODE_PV_SURPLUS = "pv_surplus"
CHARGING_MODE_FAST = "fast"
CHARGING_MODES: tuple[str, ...] = (
    CHARGING_MODE_OFF,
    CHARGING_MODE_PV_SURPLUS,
    CHARGING_MODE_FAST,
)

# E. Consumer Priority Order
PRIORITY_DHW_EV_AC = "dhw_ev_ac"  # Warmwasser → Auto → Klima (Standard)
PRIORITY_EV_DHW_AC = "ev_dhw_ac"  # Auto → Warmwasser → Klima
PRIORITY_DHW_AC_EV = "dhw_ac_ev"  # Warmwasser → Klima → Auto
PRIORITY_EV_AC_DHW = "ev_ac_dhw"  # Auto → Klima → Warmwasser

PRIORITY_ORDERS: tuple[str, ...] = (
    PRIORITY_DHW_EV_AC,
    PRIORITY_EV_DHW_AC,
    PRIORITY_DHW_AC_EV,
    PRIORITY_EV_AC_DHW,
)
DEFAULT_PRIORITY_ORDER = PRIORITY_DHW_EV_AC

# F. EV Charging Session Tracking
SESSION_ACTIVE_THRESHOLD_WATTS = 200.0

# G. Action Tracing
CONF_ACTION_TRACING_ENABLED = "action_tracing_enabled"
DEFAULT_ACTION_TRACING_ENABLED = False
MAX_ACTION_TRACES = 100
