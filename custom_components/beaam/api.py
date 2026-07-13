import async_timeout
import aiohttp

from .const import (
    API_SITE_STATE,
    API_SITE_CONFIGURATION,
    API_THING_STATES,
    API_THING_SETTINGS,
)


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

    async def _put(self, path: str, payload):
        url = f"{self._base_url}{path}"
        async with async_timeout.timeout(15):
            resp = await self._session.put(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            # Beaam answers PUT /settings with a text/plain body, so don't decode
            # as JSON. The response isn't used; just confirm success and return it raw.
            return await resp.text()

    async def async_get_site_state(self):
        return await self._get(API_SITE_STATE)

    async def async_get_site_configuration(self):
        return await self._get(API_SITE_CONFIGURATION)

    async def async_get_thing_states(self, thing_id: str):
        path = API_THING_STATES.format(thing_id=thing_id)
        return await self._get(path)

    async def async_get_thing_settings(self, thing_id: str):
        path = API_THING_SETTINGS.format(thing_id=thing_id)
        return await self._get(path)

    async def async_set_thing_setting(self, thing_id: str, key: str, value):
        """Write a single thing setting via PUT (body is an array of {key,value})."""
        path = API_THING_SETTINGS.format(thing_id=thing_id)
        return await self._put(path, [{"key": key, "value": value}])
