from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging

_LOGGER = logging.getLogger(__name__)


class BeaamDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, update_interval=30):
        super().__init__(
            hass,
            _LOGGER,
            name="Beaam API",
            update_interval=timedelta(seconds=update_interval),
        )
        self.api = api

    async def _async_update_data(self):
        try:
            site_state = await self.api.async_get_site_state()
            site_config = await self.api.async_get_site_configuration()
            return {
                "site_state": site_state,
                "site_config": site_config,
            }
        except Exception as err:
            raise UpdateFailed(f"Error fetching Beaam data: {err}") from err
