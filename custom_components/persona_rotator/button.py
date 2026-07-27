"""button.persona_re_roll — force an immediate persona re-roll."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PersonaReRollButton(hass.data[DOMAIN])])


class PersonaReRollButton(ButtonEntity):
    _attr_icon = "mdi:dice-multiple"
    _attr_name = "Persona re-roll"
    _attr_unique_id = "persona_rotator_re_roll"

    def __init__(self, rotator) -> None:
        self._rotator = rotator

    async def async_press(self) -> None:
        await self._rotator.maybe_rotate(force=True)
