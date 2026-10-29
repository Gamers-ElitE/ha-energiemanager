"""Binary sensor platform for sam_energiemanager."""

from typing import TYPE_CHECKING

from .status_sensors import ENTITY_DESCRIPTIONS, EnergiemanagerBinarySensor

# Coordinator-powered platform: updates are pushed from the coordinator.
PARALLEL_UPDATES = 0

if TYPE_CHECKING:
    from custom_components.sam_energiemanager.data import EnergiemanagerConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EnergiemanagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        EnergiemanagerBinarySensor(entry.runtime_data.coordinator, description) for description in ENTITY_DESCRIPTIONS
    )
