"""sensor.persona_of_the_day — reflects the rotator's current pick."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PersonaOfTheDaySensor(hass.data[DOMAIN])])


class PersonaOfTheDaySensor(SensorEntity):
    _attr_should_poll = False
    _attr_icon = "mdi:drama-masks"
    _attr_name = "Persona of the day"
    _attr_unique_id = "persona_rotator_persona_of_the_day"

    def __init__(self, rotator) -> None:
        self._rotator = rotator

    async def async_added_to_hass(self) -> None:
        # Register AFTER the sensor is in the state machine, then refresh in
        # case load() populated the rotator before this entity attached.
        self._rotator.register_listener(self.async_write_ha_state)
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        self._rotator.remove_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> str:
        return self._rotator.current or "like a friendly assistant"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "history": self._rotator.history,
            "history_count": len(self._rotator.history),
            "catalog": list(self._rotator.catalog),
            "catalog_size": len(self._rotator.catalog),
            "last_rotated": self._rotator.last_rotated_date,
        }
