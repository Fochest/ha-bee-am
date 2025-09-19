import async_timeout
import aiohttp

from .const import API_SITE_STATE, API_SITE_CONFIGURATION, API_THING_STATES


class BeaamApiClient:
    def __init__(self, session: aiohttp.ClientSession, ip: str, token: str):
        self._session = session
        self._base_url = f"http://{ip}"
        self._token = token

    def _headers(self):
        return {"Authorization": f"Bearer {self._token}"}

    async def _get(self, path: str):
        url = f"{self._base_url}{path}"
        async with async_timeout.timeout(15):
            resp = await self._session.get(url, headers=self._headers())
            resp.raise_for_status()
            return await resp.json()

    async def async_get_site_state(self):
        return await self._get(API_SITE_STATE)

    async def async_get_site_configuration(self):
        return await self._get(API_SITE_CONFIGURATION)

    async def async_get_thing_states(self, thing_id: str):
        path = API_THING_STATES.format(thing_id=thing_id)
        return await self._get(path)
