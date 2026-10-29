"""Thermal AC buffer switches for sam_energiemanager."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from custom_components.sam_energiemanager.coordinator import EnergiemanagerDataUpdateCoordinator
from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import STATE_ON
from homeassistant.helpers.restore_state import RestoreEntity


@dataclass(frozen=True, kw_only=True)
class EnergiemanagerSwitchEntityDescription(SwitchEntityDescription):
    """Describes a switch and how to read and update it on the coordinator."""

    value_fn: Callable[[dict[str, Any]], bool | None]
    set_fn: Callable[[EnergiemanagerDataUpdateCoordinator, bool], Awaitable[None]]


ENTITY_DESCRIPTIONS: tuple[EnergiemanagerSwitchEntityDescription, ...] = (
    EnergiemanagerSwitchEntityDescription(
        key="ac_buffer_enabled",
        translation_key="ac_buffer_enabled",
        value_fn=lambda data: data.get("ac_buffer_enabled"),
        set_fn=lambda coord, val: coord.async_set_ac_buffer_enabled(enabled=val),
    ),
    EnergiemanagerSwitchEntityDescription(
        key="ac_auto_heat_enabled",
        translation_key="ac_auto_heat_enabled",
        value_fn=lambda data: data.get("ac_auto_heat_enabled"),
        set_fn=lambda coord, val: coord.async_set_ac_auto_heat_enabled(enabled=val),
    ),
    EnergiemanagerSwitchEntityDescription(
        key="dhw_enabled",
        translation_key="dhw_enabled",
        value_fn=lambda data: data.get("dhw_enabled"),
        set_fn=lambda coord, val: coord.async_set_dhw_enabled(enabled=val),
    ),
)


class EnergiemanagerSwitch(SwitchEntity, RestoreEntity, EnergiemanagerEntity):
    """Switch to enable or disable thermal AC buffer options."""

    entity_description: EnergiemanagerSwitchEntityDescription

    async def async_added_to_hass(self) -> None:
        """Restore the switch toggle state on startup."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None and last_state.state in (STATE_ON, "off"):
            enabled = last_state.state == STATE_ON
            key = self.entity_description.key
            setattr(self.coordinator, key, enabled)
            if self.coordinator.data is not None:
                self.coordinator.data[key] = enabled

    @property
    def is_on(self) -> bool | None:
        """Return whether the switch is enabled."""
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the switch option."""
        await self.entity_description.set_fn(self.coordinator, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the switch option."""
        await self.entity_description.set_fn(self.coordinator, False)
