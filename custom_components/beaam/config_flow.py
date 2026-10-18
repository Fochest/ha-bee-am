from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BeaamApiClient
from .const import DOMAIN


class BeaamConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Beaam."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            ip = user_input["beaam_ip"].strip()
            token = user_input["api_token"].strip()

            if not ip:
                errors["beaam_ip"] = "invalid_ip"
            elif not token:
                errors["api_token"] = "invalid_token"
            else:
                await self.async_set_unique_id(ip)
                self._abort_if_unique_id_configured()

                api = BeaamApiClient(async_get_clientsession(self.hass), ip, token)
                try:
                    await api.async_get_site_state()
                except aiohttp.ClientResponseError as err:
                    if err.status in (401, 403):
                        errors["api_token"] = "invalid_auth"
                    else:
                        errors["base"] = "cannot_connect"
                except (aiohttp.ClientError, TimeoutError):
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=f"Beaam @ {ip}",
                        data={"beaam_ip": ip, "api_token": token},
                    )

        schema = vol.Schema(
            {
                vol.Required("beaam_ip"): str,
                vol.Required("api_token"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
