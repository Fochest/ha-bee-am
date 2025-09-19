from __future__ import annotations

from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN


class NtuityFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle a config flow for Ntuity API."""

    DOMAIN = DOMAIN

    @property
    def logger(self):
        return super().logger
