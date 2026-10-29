"""Charging mode select entity for sam_energiemanager."""

from custom_components.sam_energiemanager.const import CHARGING_MODES
from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription

ENTITY_DESCRIPTIONS: tuple[SelectEntityDescription, ...] = (
    SelectEntityDescription(
        key="charging_mode",
        translation_key="charging_mode",
        options=list(CHARGING_MODES),
    ),
)


class EnergiemanagerChargingModeSelect(SelectEntity, EnergiemanagerEntity):
    """Select entity for choosing the EV charging mode."""

    @property
    def current_option(self) -> str | None:
        """Return the active charging mode from coordinator data."""
        return self.coordinator.data.get("charging_mode")

    async def async_select_option(self, option: str) -> None:
        """Set the charging mode on the coordinator."""
        await self.coordinator.async_set_charging_mode(option)
