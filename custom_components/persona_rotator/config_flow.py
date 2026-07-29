"""Config + options flow for Persona of the Day.

Setup is a single confirmation step (no configuration needed — the
built-in catalog seeds on first boot). The options flow is the paste
target for new personas: it validates inline, imports immediately, and
ends with a result screen showing exactly what happened.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig

from .const import CONF_IMPORT_TEXT, DOMAIN
from .rotator import parse_persona_lines


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
    """Paste box for adding personas — validates and imports in-dialog."""

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            text = user_input.get(CONF_IMPORT_TEXT, "").strip()
            if not text:
                errors["base"] = "empty"
            else:
                valid, rejected = parse_persona_lines(text)
                if not valid:
                    errors["base"] = "no_valid"
                else:
                    rotator = self.hass.data[DOMAIN]
                    added = await rotator.add_many(valid)
                    details = ""
                    if rejected:
                        details = " Rejected: " + "; ".join(rejected[:3])
                        if len(rejected) > 3:
                            details += f" (+{len(rejected) - 3} more)"
                    return self.async_abort(
                        reason="import_result",
                        description_placeholders={
                            "added": str(added),
                            "duplicates": str(len(valid) - added),
                            "rejected": str(len(rejected)),
                            "details": details,
                        },
                    )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_IMPORT_TEXT, default=""): TextSelector(
                        TextSelectorConfig(multiline=True)
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "generator_url": (
                    "https://github.com/TheSchultz/ha-persona-of-the-day"
                    "/blob/main/PERSONA_GENERATOR.md"
                )
            },
        )
