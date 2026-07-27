"""Config + options flow for Persona of the Day.

Setup is a single confirmation step (no configuration needed — the
built-in catalog seeds on first boot). The options flow is the paste
target for AI-generated personas: text goes into 'pending_import' and
the update listener in __init__ validates and imports it.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig

from .const import CONF_IMPORT_TEXT, DOMAIN


class PersonaRotatorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-instance, zero-configuration setup."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="Persona of the Day", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> "PersonaRotatorOptionsFlow":
        return PersonaRotatorOptionsFlow()


class PersonaRotatorOptionsFlow(OptionsFlow):
    """Paste box for adding personas (one per line)."""

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            pasted = user_input.get(CONF_IMPORT_TEXT, "").strip()
            options = dict(self.config_entry.options)
            if pasted:
                options["pending_import"] = pasted
            return self.async_create_entry(title="", data=options)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_IMPORT_TEXT, default=""): TextSelector(
                        TextSelectorConfig(multiline=True)
                    ),
                }
            ),
        )
