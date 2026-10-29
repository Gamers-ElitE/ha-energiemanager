"""Config flow for sam_energiemanager — user setup and reconfigure."""

from typing import Any

from custom_components.sam_energiemanager.const import CONF_GRID_POWER_SENSOR, DOMAIN
from homeassistant import config_entries
from homeassistant.loader import async_get_loaded_integration
from homeassistant.util import slugify

from .options_flow import EnergiemanagerOptionsFlow
from .schemas import get_user_schema


class EnergiemanagerConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for sam_energiemanager."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EnergiemanagerOptionsFlow:
        """
        Return the options flow for this handler.

        Returns:
            The options flow instance.

        """
        return EnergiemanagerOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Handle a flow started by the user.

        Returns:
            The form, or the created config entry.

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            grid_sensor = str(user_input.get(CONF_GRID_POWER_SENSOR, "")).strip()
            if not grid_sensor or "." not in grid_sensor:
                errors[CONF_GRID_POWER_SENSOR] = "invalid_entity"
            else:
                await self.async_set_unique_id(slugify(grid_sensor))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Energiemanager",
                    data=user_input,
                )

        integration = async_get_loaded_integration(self.hass, DOMAIN)

        return self.async_show_form(
            step_id="user",
            data_schema=get_user_schema(user_input),
            errors=errors,
            description_placeholders={
                "documentation_url": integration.documentation or "",
            },
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Handle reconfiguration of an existing entry.

        Returns:
            The form, or the abort that follows the entry update.

        """
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            grid_sensor = str(user_input.get(CONF_GRID_POWER_SENSOR, "")).strip()
            if not grid_sensor or "." not in grid_sensor:
                errors[CONF_GRID_POWER_SENSOR] = "invalid_entity"
            else:
                return self.async_update_reload_and_abort(entry, data_updates=user_input)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                get_user_schema(),
                entry.data,
            ),
            errors=errors,
        )


__all__ = ["EnergiemanagerConfigFlowHandler"]
