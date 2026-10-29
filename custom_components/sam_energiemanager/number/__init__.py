"""Number platform for sam_energiemanager."""

from typing import TYPE_CHECKING

from .control_numbers import ENTITY_DESCRIPTIONS, EnergiemanagerNumber

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
    """Set up the number platform."""
    async_add_entities(
        EnergiemanagerNumber(entry.runtime_data.coordinator, description) for description in ENTITY_DESCRIPTIONS
    )
