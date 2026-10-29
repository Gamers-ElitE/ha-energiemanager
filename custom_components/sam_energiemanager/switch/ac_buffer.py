"""Thermal AC buffer switch for sam_energiemanager."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from custom_components.sam_energiemanager.entity import EnergiemanagerEntity
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription


@dataclass(frozen=True, kw_only=True)
class EnergiemanagerSwitchEntityDescription(SwitchEntityDescription):
    """Describes a switch and how to read it from coordinator data."""

    value_fn: Callable[[dict[str, Any]], bool | None]


ENTITY_DESCRIPTIONS: tuple[EnergiemanagerSwitchEntityDescription, ...] = (
    EnergiemanagerSwitchEntityDescription(
        key="ac_buffer_enabled",
        translation_key="ac_buffer_enabled",
        value_fn=lambda data: data.get("ac_buffer_enabled"),
    ),
)


class EnergiemanagerSwitch(SwitchEntity, EnergiemanagerEntity):
    """Switch to enable or disable the thermal AC buffer stage."""

    entity_description: EnergiemanagerSwitchEntityDescription

    @property
    def is_on(self) -> bool | None:
        """Return whether the thermal AC buffer is enabled."""
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the thermal AC buffer."""
        await self.coordinator.async_set_ac_buffer_enabled(enabled=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the thermal AC buffer."""
        await self.coordinator.async_set_ac_buffer_enabled(enabled=False)
