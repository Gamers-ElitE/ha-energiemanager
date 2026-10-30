"""Handler for the clear_traces service action."""

from typing import TYPE_CHECKING

from custom_components.sam_energiemanager.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ServiceValidationError

if TYPE_CHECKING:
    from custom_components.sam_energiemanager.data import EnergiemanagerConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse

ATTR_CONFIG_ENTRY_ID = "config_entry_id"


async def async_handle_clear_traces(hass: HomeAssistant, call: ServiceCall) -> ServiceResponse:
    """
    Clear recorded action traces from the targeted config entry coordinator.

    Returns:
        Confirmation and remaining trace count (0).

    Raises:
        ServiceValidationError: If the targeted entry does not exist or is not loaded.

    """
    entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
    entry = _async_get_loaded_entry(hass, entry_id)
    coordinator = entry.runtime_data.coordinator

    coordinator.clear_traces()
    await coordinator.async_refresh()

    return {
        "success": True,
        "trace_count": 0,
    }


def _async_get_loaded_entry(hass: HomeAssistant, entry_id: str | None) -> EnergiemanagerConfigEntry:
    """
    Resolve a config entry id or pick the first loaded entry if none provided.

    Returns:
        The loaded config entry.

    Raises:
        ServiceValidationError: If the entry is unknown or not loaded.

    """
    if not entry_id:
        entries = hass.config_entries.async_entries(DOMAIN)
        for e in entries:
            if e.state is ConfigEntryState.LOADED:
                return e  # type: ignore[return-value]
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_found",
            translation_placeholders={"target": "default"},
        )

    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_found",
            translation_placeholders={"target": entry_id},
        )
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
            translation_placeholders={"target": entry.title},
        )
    return entry  # type: ignore[return-value]
