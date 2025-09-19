from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, PLATFORMS
from .api import NtuityApiClient
from .coordinator import NtuityDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Ntuity from a config entry."""

    # Register OAuth2 implementation
    config_entry_oauth2_flow.async_register_implementation(
        hass,
        DOMAIN,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            client_id=entry.data.get("client_id", ""),
            client_secret=entry.data.get("client_secret", ""),
            authorize_url="https://api.ntuity.io/oauth/authorize",
            token_url="https://api.ntuity.io/oauth/token",
        ),
    )

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    oauth_session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    session = hass.helpers.aiohttp_client.async_get_clientsession()

    api = NtuityApiClient(session, oauth_session)
    coordinator = NtuityDataUpdateCoordinator(hass, api, update_interval=60)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
