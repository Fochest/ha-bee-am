import asyncio
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging

_LOGGER = logging.getLogger(__name__)

CHARGING_POINT_TYPE = "CHARGING_POINT_AC"


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

            charging_point_ids = [
                thing_id
                for thing_id, thing in site_config.get("things", {}).items()
                if thing.get("type") == CHARGING_POINT_TYPE
            ]

            charging_points = {}
            if charging_point_ids:
                results = await asyncio.gather(
                    *(self.api.async_get_thing_states(tid) for tid in charging_point_ids),
                    return_exceptions=True,
                )
                for tid, result in zip(charging_point_ids, results):
                    if isinstance(result, Exception):
                        _LOGGER.warning(
                            "Failed to fetch states for charging point %s: %s", tid, result
                        )
                        continue
                    charging_points[tid] = result

            return {
                "site_state": site_state,
                "site_config": site_config,
                "charging_points": charging_points,
            }
        except Exception as err:
            raise UpdateFailed(f"Error fetching Beaam data: {err}") from err
