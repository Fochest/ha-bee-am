from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
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
                return self.async_create_entry(
                    title=f"Beaam @ {ip}",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required("beaam_ip"): str,
                vol.Required("api_token"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

