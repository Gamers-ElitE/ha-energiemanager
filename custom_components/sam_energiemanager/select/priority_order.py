"""Priority order select entity for sam_energiemanager."""

from custom_components.sam_energiemanager.const import PRIORITY_ORDERS
from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.restore_state import RestoreEntity

ENTITY_DESCRIPTIONS: tuple[SelectEntityDescription, ...] = (
    SelectEntityDescription(
        key="priority_order",
        translation_key="priority_order",
        options=list(PRIORITY_ORDERS),
    ),
)


class EnergiemanagerPriorityOrderSelect(SelectEntity, RestoreEntity, EnergiemanagerEntity):
    """Select entity for choosing the surplus consumer priority cascade order."""

    async def async_added_to_hass(self) -> None:
        """Restore the previously selected priority order on startup."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None and last_state.state in PRIORITY_ORDERS:
            self.coordinator.priority_order = last_state.state
            if self.coordinator.data is not None:
                self.coordinator.data["priority_order"] = last_state.state

    @property
    def current_option(self) -> str | None:
        """Return the active priority order from coordinator data."""
        return self.coordinator.data.get("priority_order")

    async def async_select_option(self, option: str) -> None:
        """Set the priority order on the coordinator."""
        await self.coordinator.async_set_priority_order(option)
