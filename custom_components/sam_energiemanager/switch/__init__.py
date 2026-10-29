"""Switch platform for sam_energiemanager."""

from typing import TYPE_CHECKING

from .ac_buffer import ENTITY_DESCRIPTIONS, EnergiemanagerSwitch

# Acts on the coordinator/actuators: serialize outbound writes.
PARALLEL_UPDATES = 1

if TYPE_CHECKING:
    from custom_components.sam_energiemanager.data import EnergiemanagerConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EnergiemanagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        EnergiemanagerSwitch(entry.runtime_data.coordinator, description) for description in ENTITY_DESCRIPTIONS
    )
