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

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN
from .rotator import PersonaRotator, parse_persona_lines

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "button"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PERSONA_SCHEMA = vol.Schema({vol.Required("persona"): cv.string})
IMPORT_SCHEMA = vol.Schema({vol.Required("personas"): cv.string})


async def async_setup(hass: HomeAssistant, config) -> bool:
    """YAML setup is not supported; everything happens in async_setup_entry."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    rotator = PersonaRotator(hass)
    hass.data[DOMAIN] = rotator

    await rotator.load()
    await rotator.maybe_rotate()

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

    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Import personas pasted into the options flow, then clear the buffer.

    The options flow stores the pasted text under 'pending_import'; we
    consume it here so re-opening options always shows an empty box.
    """
    pending = entry.options.get("pending_import", "")
    if not pending:
        return
    rotator: PersonaRotator = hass.data[DOMAIN]
    valid, rejected = parse_persona_lines(pending)
    added = await rotator.add_many(valid)
    _LOGGER.info(
        "Options import: %d added, %d duplicates, %d rejected",
        added, len(valid) - added, len(rejected),
    )
    if rejected:
        _LOGGER.warning("Options import rejected: %s", "; ".join(rejected))
    hass.config_entries.async_update_entry(
        entry, options={k: v for k, v in entry.options.items() if k != "pending_import"}
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        for service in ("rotate", "add", "remove", "import_personas", "reset_catalog"):
            hass.services.async_remove(DOMAIN, service)
        hass.data.pop(DOMAIN, None)
    return unload_ok
