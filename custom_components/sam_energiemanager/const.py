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
CONF_CLIMATE_ENTITY = "climate_entity"

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

# B. Thermal AC Buffer
AC_BUFFER_MIN_SURPLUS_WATTS = 500.0
AC_BUFFER_MAX_SURPLUS_WATTS = 1350.0
AC_BUFFER_TEMP_OFFSET = 2.5
AC_BUFFER_MIN_HOLD_SECONDS = 1200.0

# C. Home Battery Discharge Lock
BATTERY_LOCK_THRESHOLD_WATTS = 250.0
BATTERY_LOCK_RELEASE_SECONDS = 60.0

# D. 1-Phase EV Charging (230 V)
EV_VOLTAGE = 230.0
EV_MIN_CURRENT_A = 6
EV_MAX_CURRENT_A = 16
EV_MIN_SURPLUS_WATTS = 1380.0
EV_CLOUD_HYSTERESIS_SECONDS = 180.0

CHARGING_MODE_OFF = "off"
CHARGING_MODE_PV_SURPLUS = "pv_surplus"
CHARGING_MODE_FAST = "fast"
CHARGING_MODES: tuple[str, ...] = (
    CHARGING_MODE_OFF,
    CHARGING_MODE_PV_SURPLUS,
    CHARGING_MODE_FAST,
)

# E. WashData Session Tracking
SESSION_ACTIVE_THRESHOLD_WATTS = 200.0
