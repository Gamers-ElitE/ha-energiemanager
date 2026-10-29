"""Custom Web Component sidebar panel registration for sam_energiemanager."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

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
    LOGGER,
)
from homeassistant.components import frontend
from homeassistant.components.http.server import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

if TYPE_CHECKING:
    from custom_components.sam_energiemanager.data import EnergiemanagerConfigEntry

DASHBOARD_URL_PATH = "sam-energiemanager"
DASHBOARD_TITLE = "Energiemanager"
DASHBOARD_ICON = "mdi:home-lightning-bolt"
PANEL_ELEMENT_NAME = "sam-energiemanager-panel"
PANEL_JS_URL = f"/{DOMAIN}/sam-energiemanager-panel.js"
PANEL_JS_PATH = Path(__file__).parent / "sam-energiemanager-panel.js"


def _resolve_entity_id(
    ent_reg: er.EntityRegistry,
    entry_id: str,
    platform: str,
    key: str,
    fallback_slug: str,
) -> str:
    """Resolve an integration entity ID from the entity registry with a fallback."""
    resolved = ent_reg.async_get_entity_id(platform, DOMAIN, f"{entry_id}_{key}")
    return resolved or f"{platform}.energiemanager_{fallback_slug}"


def build_dashboard_config(hass: HomeAssistant, entry: EnergiemanagerConfigEntry) -> dict[str, Any]:
    """
    Build the metadata and entity mapping summary for the Energiemanager custom panel.

    Returns:
        A configuration dictionary describing the panel views, controls, and resolved entities.

    """
    ent_reg = er.async_get(hass)
    eid = entry.entry_id

    def ent(platform: str, key: str, slug: str) -> str:
        return _resolve_entity_id(ent_reg, eid, platform, key, slug)

    source_keys = (
        CONF_GRID_POWER_SENSOR,
        CONF_BATTERY_SOC_SENSOR,
        CONF_BATTERY_DISCHARGE_LOCK_SWITCH,
        CONF_EV_POWER_SENSOR,
        CONF_EV_SOC_SENSOR,
        CONF_EV_PLUGGED_BINARY_SENSOR,
        CONF_EV_BLE_CONNECTED_BINARY_SENSOR,
        CONF_EV_CURRENT_NUMBER,
        CONF_EV_CHARGING_SWITCH,
        CONF_EV_WAKEUP_BUTTON,
        CONF_CLIMATE_ENTITY,
    )
    source_entities = [entry.data[k] for k in source_keys if entry.data.get(k)]

    return {
        "title": DASHBOARD_TITLE,
        "panel_element": PANEL_ELEMENT_NAME,
        "module_url": PANEL_JS_URL,
        "source_entities": source_entities,
        "views": [
            {
                "title": "Übersicht & Kaskade",
                "path": "overview",
                "entities": [
                    ent("select", "charging_mode", "ev_charging_mode"),
                    ent("number", "battery_reserve_soc", "battery_priority_reserve_soc"),
                    ent("number", "tesla_max_current", "tesla_maximum_charging_current"),
                    ent("number", "tesla_target_soc", "tesla_fast_charge_target_soc"),
                    ent("switch", "ac_buffer_enabled", "thermal_ac_buffer_enabled"),
                ],
            },
            {
                "title": "Ladebilanz & Sitzungen",
                "path": "sessions",
                "entities": [
                    ent("sensor", "ev_solar_lifetime_kwh", "ev_solar_lifetime_energy"),
                    ent("sensor", "ev_grid_lifetime_kwh", "ev_grid_lifetime_energy"),
                    ent("sensor", "last_session_summary", "last_ev_charging_session"),
                ],
            },
            {
                "title": "Schwellenwerte & Feintuning",
                "path": "settings",
                "entities": [
                    ent("number", "ema_alpha", "ema_smoothing_factor"),
                    ent("number", "deadband_watts", "symmetric_deadband"),
                    ent("number", "battery_lock_threshold_watts", "battery_lock_power_threshold"),
                    ent("number", "battery_lock_release_seconds", "battery_lock_release_delay"),
                    ent("number", "ac_buffer_min_surplus_watts", "ac_buffer_minimum_surplus"),
                    ent("number", "ac_buffer_max_surplus_watts", "ac_buffer_maximum_surplus"),
                    ent("number", "ac_buffer_temp_offset", "ac_buffer_temperature_offset"),
                    ent("number", "ac_buffer_min_hold_minutes", "ac_buffer_minimum_hold_time"),
                    ent("number", "ev_min_surplus_watts", "ev_minimum_surplus_power"),
                    ent("number", "ev_cloud_hysteresis_seconds", "ev_cloud_hysteresis_delay"),
                    ent("number", "electricity_price", "electricity_tariff_price"),
                ],
            },
        ],
    }


async def async_register_dashboard(hass: HomeAssistant, entry: EnergiemanagerConfigEntry) -> None:
    """Register the custom Web Component sidebar panel for Energiemanager."""
    if getattr(hass, "http", None) is not None and PANEL_JS_PATH.is_file():
        await hass.http.async_register_static_paths(
            [StaticPathConfig(PANEL_JS_URL, str(PANEL_JS_PATH), cache_headers=False)]
        )

    version = entry.runtime_data.integration.version or "0.1.0"
    try:
        mtime = int(PANEL_JS_PATH.stat().st_mtime)
        panel_version = f"{version}-{mtime}"
    except OSError:
        panel_version = str(version)

    try:
        frontend.async_register_built_in_panel(
            hass,
            component_name="custom",
            sidebar_title=DASHBOARD_TITLE,
            sidebar_icon=DASHBOARD_ICON,
            frontend_url_path=DASHBOARD_URL_PATH,
            config={
                "_panel_custom": {
                    "name": PANEL_ELEMENT_NAME,
                    "module_url": f"{PANEL_JS_URL}?v={panel_version}",
                    "embed_iframe": False,
                    "trust_external": False,
                }
            },
            require_admin=False,
            update=True,
        )
        LOGGER.debug("Registered Energiemanager custom panel at /%s", DASHBOARD_URL_PATH)
    except Exception:  # noqa: BLE001
        LOGGER.debug("Skipping custom panel registration (frontend unavailable)")


def async_unregister_dashboard(hass: HomeAssistant) -> None:
    """Remove the Energiemanager sidebar panel when the integration unloads."""
    if frontend.async_panel_exists(hass, DASHBOARD_URL_PATH):
        frontend.async_remove_panel(hass, DASHBOARD_URL_PATH)
