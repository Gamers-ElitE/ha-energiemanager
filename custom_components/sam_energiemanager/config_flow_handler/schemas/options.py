"""Options flow schemas."""

from collections.abc import Mapping
from typing import Any

import probatio

from custom_components.sam_energiemanager.const import (
    CONF_ELECTRICITY_PRICE,
    CONF_UPDATE_INTERVAL_SECONDS,
    DEFAULT_ELECTRICITY_PRICE,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
)
from homeassistant.helpers import selector


def get_options_schema(defaults: Mapping[str, Any] | None = None) -> probatio.Schema:
    """
    Build the options form schema.

    Args:
        defaults: The entry's current options, used to pre-fill the form.

    Returns:
        The schema for the options form.

    """
    defaults = defaults or {}
    return probatio.Schema(
        {
            probatio.Optional(
                CONF_UPDATE_INTERVAL_SECONDS,
                default=defaults.get(CONF_UPDATE_INTERVAL_SECONDS, DEFAULT_UPDATE_INTERVAL_SECONDS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=60,
                    step=1,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                ),
            ),
            probatio.Optional(
                CONF_ELECTRICITY_PRICE,
                default=defaults.get(CONF_ELECTRICITY_PRICE, DEFAULT_ELECTRICITY_PRICE),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.0,
                    max=2.0,
                    step=0.01,
                    unit_of_measurement="EUR/kWh",
                    mode=selector.NumberSelectorMode.BOX,
                ),
            ),
        },
    )


__all__ = ["get_options_schema"]
