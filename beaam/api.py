import async_timeout

API_BASE = "https://api.ntuity.io/v1"


class NtuityApiClient:
    def __init__(self, session, oauth_session):
        self._session = session
        self._oauth_session = oauth_session

    async def async_get_sites(self):
        url = f"{API_BASE}/sites"
        async with async_timeout.timeout(15):
            resp = await self._oauth_session.request("GET", url)
            resp.raise_for_status()
            return await resp.json()

    async def async_get_site_details(self, site_id):
        url = f"{API_BASE}/sites/{site_id}"
        async with async_timeout.timeout(15):
            resp = await self._oauth_session.request("GET", url)
            resp.raise_for_status()
            return await resp.json()

    async def async_get_latest_energy_flow(self, site_id):
        url = f"{API_BASE}/sites/{site_id}/energy-flow/latest"
        async with async_timeout.timeout(15):
            resp = await self._oauth_session.request("GET", url)
            if resp.status == 404:
                return None
            resp.raise_for_status()
            return await resp.json()
