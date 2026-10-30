"""Service action registration for sam_energiemanager."""

from typing import TYPE_CHECKING

import probatio

from custom_components.sam_energiemanager.const import DOMAIN
from homeassistant.core import SupportsResponse
from homeassistant.helpers import config_validation as cv

from .clear_traces import async_handle_clear_traces
from .refresh_data import ATTR_CONFIG_ENTRY_ID, async_handle_refresh_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse

SERVICE_REFRESH_DATA = "refresh_data"
SERVICE_CLEAR_TRACES = "clear_traces"

REFRESH_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
    },
)

CLEAR_TRACES_SCHEMA = probatio.Schema(
    {
        probatio.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    },
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration's service actions once, at component level."""

    async def handle_refresh_data(call: ServiceCall) -> ServiceResponse:
        """
        Run the refresh_data action.

        Returns:
            The handler's response data.

        """
        return await async_handle_refresh_data(hass, call)

    async def handle_clear_traces(call: ServiceCall) -> ServiceResponse:
        """
        Run the clear_traces action.

        Returns:
            The handler's response data.

        """
        return await async_handle_clear_traces(hass, call)

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_DATA):
        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_DATA,
            handle_refresh_data,
            schema=REFRESH_DATA_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_TRACES):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CLEAR_TRACES,
            handle_clear_traces,
            schema=CLEAR_TRACES_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )
