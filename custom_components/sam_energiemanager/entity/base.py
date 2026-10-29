"""Base entity class for sam_energiemanager."""

from typing import TYPE_CHECKING

from custom_components.sam_energiemanager.const import ATTRIBUTION
from custom_components.sam_energiemanager.coordinator import EnergiemanagerDataUpdateCoordinator
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

if TYPE_CHECKING:
    from homeassistant.helpers.entity import EntityDescription


class EnergiemanagerEntity(CoordinatorEntity[EnergiemanagerDataUpdateCoordinator]):
    """Base entity providing device info, unique ID and attribution."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EnergiemanagerDataUpdateCoordinator,
        entity_description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            name=coordinator.config_entry.title,
            manufacturer="Energiemanager",
            model="PV Cascade & EV Controller",
            serial_number=coordinator.config_entry.entry_id,
            sw_version="0.1.0",
        )
