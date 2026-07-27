"""Core rotation engine — daily non-repeating persona picker.

Picks one persona from a stored catalog each day, avoiding the most
recently used (HISTORY_CAP entries). Tracking is by persona TEXT, not by
index, so:
  - Adding entries never causes recently-used personas to re-surface.
  - Removing entries doesn't break the rotation — they're filtered out of
    eligibility on the next roll.
  - History AND catalog persist across restarts via the Store API.

A deterministic day-formula approach (hash of the date modulo catalog
size) was rejected: any length-changing catalog edit reshuffles the
day-to-slot mapping for every future day.
"""

from __future__ import annotations

import datetime
import logging
import random

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import HISTORY_CAP, MAX_PERSONA_LENGTH, STORAGE_KEY, STORAGE_VERSION
from .default_catalog import DEFAULT_CATALOG

_LOGGER = logging.getLogger(__name__)


def parse_persona_lines(text: str) -> tuple[list[str], list[str]]:
    """Parse pasted persona text into (valid, rejected_with_reason) lists.

    Accepts one persona per line. Tolerates common paste formats: leading
    list markers ("-", "*", numbers) and surrounding quotes are stripped.
    """
    valid: list[str] = []
    rejected: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Strip list markers: "- persona", "* persona", "3. persona"
        line = line.lstrip("-*").strip()
        if line and line[0].isdigit():
            head, _, tail = line.partition(".")
            if head.isdigit() and tail.strip():
                line = tail.strip()
        # Strip matched surrounding quotes
        if len(line) >= 2 and line[0] == line[-1] and line[0] in "'\"":
            line = line[1:-1].strip()
        if not line:
            continue
        if len(line) > MAX_PERSONA_LENGTH:
            rejected.append(f"{line[:40]}… (too long, max {MAX_PERSONA_LENGTH} chars)")
            continue
        if "[" in line or "]" in line:
            rejected.append(f"{line[:40]}… (brackets are added by the prompt, not the persona)")
            continue
        valid.append(line)
    return valid, rejected


class PersonaRotator:
    """Holds catalog + persistent rotation state."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.catalog: list[str] = []
        self._store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._current = ""
        self._date = ""
        self._history: list[str] = []
        self._listeners: list = []

    async def load(self) -> None:
        data = await self._store.async_load() or {}
        self._current = data.get("current", "")
        self._date = data.get("date", "")
        self._history = data.get("history", [])
        # Seed from the built-in catalog on first boot only. A stored empty
        # list means "user deliberately emptied the catalog" and is honored;
        # a missing key means "never initialized".
        stored_catalog = data.get("catalog")
        if stored_catalog is None:
            self.catalog = list(DEFAULT_CATALOG)
            _LOGGER.info(
                "First boot — seeding catalog with %d built-in personas",
                len(self.catalog),
            )
            await self._save()
        else:
            self.catalog = list(stored_catalog)
        self._notify_listeners()

    async def _save(self) -> None:
        await self._store.async_save(
            {
                "current": self._current,
                "date": self._date,
                "history": self._history,
                "catalog": self.catalog,
            }
        )

    def _notify_listeners(self) -> None:
        for cb in self._listeners:
            try:
                cb()
            except Exception as err:  # pragma: no cover - defensive
                _LOGGER.warning("Persona listener raised: %s", err)

    async def add_many(self, personas: list[str]) -> int:
        """Add multiple personas; returns how many were actually new."""
        added = 0
        for persona in personas:
            persona = persona.strip()
            if persona and persona not in self.catalog:
                self.catalog.append(persona)
                added += 1
        if added:
            await self._save()
            self._notify_listeners()
            _LOGGER.info("Added %d personas (catalog now %d)", added, len(self.catalog))
        return added

    async def add_to_catalog(self, persona: str) -> bool:
        return (await self.add_many([persona])) == 1

    async def remove_from_catalog(self, persona: str) -> bool:
        persona = persona.strip()
        if persona not in self.catalog:
            return False
        self.catalog.remove(persona)
        await self._save()
        self._notify_listeners()
        _LOGGER.info("Removed %r (catalog now %d)", persona, len(self.catalog))
        return True

    async def reset_catalog(self) -> int:
        """Reset the catalog to the built-in default. Returns new size."""
        self.catalog = list(DEFAULT_CATALOG)
        await self._save()
        self._notify_listeners()
        _LOGGER.info("Catalog reset to built-in default (%d entries)", len(self.catalog))
        return len(self.catalog)

    async def maybe_rotate(self, force: bool = False) -> bool:
        """Pick a new persona for today if not already set (or force=True)."""
        today = datetime.date.today().isoformat()
        if not force and self._date == today and self._current:
            return False
        eligible = [p for p in self.catalog if p not in self._history]
        if not eligible:
            _LOGGER.info("History exhausted the catalog — resetting history")
            eligible = list(self.catalog)
            self._history = []
        if not eligible:
            _LOGGER.warning("Catalog is empty — keeping current persona")
            return False
        new_persona = random.choice(eligible)
        self._history = ([new_persona] + self._history)[:HISTORY_CAP]
        self._current = new_persona
        self._date = today
        await self._save()
        self._notify_listeners()
        _LOGGER.info("Rotated → %r", new_persona)
        return True

    @property
    def current(self) -> str:
        return self._current

    @property
    def history(self) -> list[str]:
        return list(self._history)

    @property
    def last_rotated_date(self) -> str:
        return self._date

    def register_listener(self, cb) -> None:
        self._listeners.append(cb)

    def remove_listener(self, cb) -> None:
        if cb in self._listeners:
            self._listeners.remove(cb)
