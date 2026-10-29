"""Charging mode select entity for sam_energiemanager."""

from custom_components.sam_energiemanager.const import CHARGING_MODES
from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.restore_state import RestoreEntity

ENTITY_DESCRIPTIONS: tuple[SelectEntityDescription, ...] = (
    SelectEntityDescription(
        key="charging_mode",
        translation_key="charging_mode",
        options=list(CHARGING_MODES),
    ),
)


class EnergiemanagerChargingModeSelect(SelectEntity, RestoreEntity, EnergiemanagerEntity):
    """Select entity for choosing the EV charging mode."""

    async def async_added_to_hass(self) -> None:
        """Restore the previously selected charging mode on startup."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None and last_state.state in CHARGING_MODES:
            self.coordinator.charging_mode = last_state.state
            if self.coordinator.data is not None:
                self.coordinator.data["charging_mode"] = last_state.state

    @property
    def current_option(self) -> str | None:
        """Return the active charging mode from coordinator data."""
        return self.coordinator.data.get("charging_mode")

    async def async_select_option(self, option: str) -> None:
        """Set the charging mode on the coordinator."""
        await self.coordinator.async_set_charging_mode(option)
