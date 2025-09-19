import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class NtuityDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, update_interval=60):
        super().__init__(
            hass,
            _LOGGER,
            name="Ntuity API Coordinator",
            update_interval=timedelta(seconds=update_interval),
        )
        self.api = api

    async def _async_update_data(self):
        try:
            sites = await self.api.async_get_sites()
            results = {}
            for site in sites:
                site_id = site["id"]
                details = await self.api.async_get_site_details(site_id)
                energy_flow = await self.api.async_get_latest_energy_flow(site_id)
                results[site_id] = {
                    "site": details,
                    "energy_flow": energy_flow,
                }
            return results
        except Exception as err:
            raise UpdateFailed(f"Error fetching Ntuity data: {err}")
