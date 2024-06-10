"""Config flow for Imazu Wall Pad integration."""

import logging
from typing import Any

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.xiaomi_miio import CONF_FLOW_TYPE
from homeassistant.components.xiaomi_miio.config_flow import XiaomiMiioFlowHandler
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_TOKEN, CONF_MODEL, CONF_DEVICE, CONF_MAC
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_MODEL, default="nwt.derh.wdh318efw1"): cv.string,
    }
)


class XiaomiMiioDhFlowHandler(XiaomiMiioFlowHandler, domain=DOMAIN):

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get the options flow."""
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await super().async_step_user(user_input)
        # return await self.async_step_manual()

    async def async_step_connect(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        result = await super().async_step_connect(user_input)
        errors = result.get("errors", {})
        if "base" not in errors or errors["base"] != "unknown_device":
            return result
        if not self.model.startswith("nwt.derh"):
            return result
        return self.async_create_entry(
            title=self.name,
            data={
                CONF_FLOW_TYPE: CONF_DEVICE,
                CONF_HOST: self.host,
                CONF_TOKEN: self.token,
                CONF_MODEL: self.model,
                CONF_MAC: self.mac,
            },
        )
