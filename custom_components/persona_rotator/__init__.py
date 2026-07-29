"""Persona of the Day — a new personality for your voice assistant, daily.

Config-entry based integration. The entities:
  - sensor.persona_of_the_day  — today's persona text (+ catalog/history attrs)
  - button.persona_re_roll     — force an immediate re-roll

Services:
  - persona_rotator.rotate           — force immediate re-roll
  - persona_rotator.add              — add one persona
  - persona_rotator.remove           — remove one persona
  - persona_rotator.import_personas  — bulk-add pasted personas (validated)
  - persona_rotator.reset_catalog    — restore the built-in catalog
"""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import llm
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN
from .llm_api import PersonaAPI
from .rotator import PersonaRotator, parse_persona_lines

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PERSONA_SCHEMA = vol.Schema({vol.Required("persona"): cv.string})
IMPORT_SCHEMA = vol.Schema({vol.Required("personas"): cv.string})

_REPO = "https://github.com/TheSchultz/ha-persona-of-the-day"

# Shown once, right after first setup — the "now what?" hand-holding.
# Setup succeeds silently otherwise, and a new user is left on the
# integrations page with a working sensor and no idea how to wire it
# into their voice assistant.
WELCOME_MESSAGE = f"""**Persona of the Day is running.** Today's persona lives in
`sensor.persona_of_the_day` — check it in
[Developer Tools → States](/developer-tools/state).

**To make your voice assistant use it (about 5 minutes):**

1. Get a free Google AI key at
   [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. [Add an integration](/config/integrations/dashboard): search "Gemini",
   click the **Google** brand tile, pick **Google Gemini**, paste the key
   (click *Skip and finish* on the "Name and assign" screen that follows)
3. In the Gemini conversation agent's settings, find **"Control Home
   Assistant"** and tick **Persona of the Day** in the list
4. In [Settings → Voice assistants](/config/voice-assistants/assistants),
   set both the conversation agent and text-to-speech to Google Gemini

**Growing your catalog:** use the
[persona generator prompt]({_REPO}/blob/main/PERSONA_GENERATOR.md) with any
AI chatbot, then paste the results via **Configure** on the
[Persona of the Day integration](/config/integrations/integration/persona_rotator).

Not feeling today's persona? Press the **Persona re-roll** button on the
device page."""


async def async_setup(hass: HomeAssistant, config) -> bool:
    """YAML setup is not supported; everything happens in async_setup_entry."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    rotator = PersonaRotator(hass)
    hass.data[DOMAIN] = rotator

    await rotator.load()
    await rotator.maybe_rotate()

    # Register the LLM API: makes "Persona of the Day" a checkbox in every
    # LLM conversation agent's settings — the zero-paste setup path.
    try:
        unregister = llm.async_register_api(hass, PersonaAPI(hass))
        if callable(unregister):
            entry.async_on_unload(unregister)
    except HomeAssistantError as err:
        _LOGGER.warning("Could not register LLM API (already registered?): %s", err)

    # One-time welcome with guided next steps (first setup only).
    if not entry.data.get("welcomed"):
        persistent_notification.async_create(
            hass,
            WELCOME_MESSAGE,
            title="Persona of the Day — next steps",
            notification_id="persona_rotator_welcome",
        )
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "welcomed": True}
        )

    # Daily rotation at 00:00:01 local time. @callback is mandatory here:
    # without it HA dispatches via a worker thread and the thread-safety
    # check silently drops the callback.
    @callback
    def _on_midnight(_now) -> None:
        hass.async_create_task(rotator.maybe_rotate())

    entry.async_on_unload(
        async_track_time_change(hass, _on_midnight, hour=0, minute=0, second=1)
    )

    async def handle_rotate(_call: ServiceCall) -> None:
        await rotator.maybe_rotate(force=True)

    async def handle_add(call: ServiceCall) -> None:
        await rotator.add_to_catalog(call.data["persona"])

    async def handle_remove(call: ServiceCall) -> None:
        await rotator.remove_from_catalog(call.data["persona"])

    async def handle_import(call: ServiceCall) -> None:
        valid, rejected = parse_persona_lines(call.data["personas"])
        if rejected and not valid:
            raise ServiceValidationError(
                f"No valid personas found. Rejected: {'; '.join(rejected[:5])}"
            )
        added = await rotator.add_many(valid)
        _LOGGER.info(
            "Import: %d added, %d duplicates, %d rejected",
            added, len(valid) - added, len(rejected),
        )
        if rejected:
            _LOGGER.warning("Import rejected entries: %s", "; ".join(rejected))

    async def handle_reset(_call: ServiceCall) -> None:
        await rotator.reset_catalog()

    hass.services.async_register(DOMAIN, "rotate", handle_rotate)
    hass.services.async_register(DOMAIN, "add", handle_add, schema=PERSONA_SCHEMA)
    hass.services.async_register(DOMAIN, "remove", handle_remove, schema=PERSONA_SCHEMA)
    hass.services.async_register(
        DOMAIN, "import_personas", handle_import, schema=IMPORT_SCHEMA
    )
    hass.services.async_register(DOMAIN, "reset_catalog", handle_reset)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        for service in ("rotate", "add", "remove", "import_personas", "reset_catalog"):
            hass.services.async_remove(DOMAIN, service)
        hass.data.pop(DOMAIN, None)
    return unload_ok
