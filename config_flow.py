import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN  # ✅ Ensure DOMAIN is imported!

class VandebronConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handles UI-based setup for the integration."""
    
    VERSION = 1
    
    """
    async def async_step_reconfigure(
        "Handle reconfiguration of the integration."
        errors = {}

        if user_input is not None:
            if user_input["setup_mode"] == "advanced":
                return await self.async_step_options()
            return await self.async_step_confirm(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("setup_mode", default="default"): vol.In({
                    "default": "Default Setup",
                    "advanced": "Advanced Setup"
                })
            }),
            errors=errors,
        )
    """

    async def async_step_user(self, user_input=None):
        """Initial step: Allow user to choose setup mode."""
        errors = {}

        if user_input is not None:
            if user_input["setup_mode"] == "advanced":
                return await self.async_step_options()
            return await self.async_step_confirm(user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("setup_mode", default="default"): vol.In({
                    "default": "Default Setup",
                    "advanced": "Advanced Setup"
                })
            }),
            errors=errors,
        )

    async def async_step_options(self, user_input=None):
        """Advanced configuration step."""
        errors = {}

        if user_input is not None:
            return await self.async_step_confirm(user_input)

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema({
                vol.Required("day_offset", default=1): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=7)
                )
            }),
            errors=errors,
            description_placeholders={"day_offset_label": "Number of days to retrieve data for"},
        )

    async def async_step_confirm(self, user_input):
        """Final confirmation before entry is created."""
        return self.async_create_entry(title="Vandebron Green Energy", data=user_input)
