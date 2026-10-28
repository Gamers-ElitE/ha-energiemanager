"""Button platform for sam_energiemanager."""

from typing import TYPE_CHECKING

from .reset_filter import ENTITY_DESCRIPTIONS, EnergiemanagerButton

# Acts on the device: the coordinator does not limit outbound calls.
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
    """Set up the button platform."""
    async_add_entities(
        EnergiemanagerButton(entry.runtime_data.coordinator, description) for description in ENTITY_DESCRIPTIONS
    )
