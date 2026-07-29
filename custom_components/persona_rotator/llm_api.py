"""LLM API — injects the persona prompt into any conversation agent.

Registering an llm.API makes "Persona of the Day" appear as a checkbox in
every LLM conversation agent's settings (Google Gemini, Anthropic, OpenAI,
Ollama, ...). Ticking it injects our prompt — today's persona plus the
voice-direction rules — into the agent's system prompt on every turn,
replacing the manual copy-the-prompt-into-Instructions step entirely.

Also exposes a `reroll_persona` tool so "give me a different personality"
works by voice.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.util.json import JsonObjectType

from .const import DOMAIN

API_ID = "persona_of_the_day"


class RerollPersonaTool(llm.Tool):
    """Let the agent switch to a fresh persona on user request."""

    name = "reroll_persona"
    description = (
        "Pick a different randomly chosen personality for today. Use ONLY "
        "when the user explicitly asks for a new/different personality, "
        "persona, character, or voice."
    )
    parameters = vol.Schema({})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> JsonObjectType:
        rotator = hass.data.get(DOMAIN)
        if rotator is None:
            return {"error": "Persona of the Day is not loaded"}
        await rotator.maybe_rotate(force=True)
        return {"new_persona": rotator.current}


class PersonaAPI(llm.API):
    """The 'Persona of the Day' entry in agents' API checkbox list."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(hass=hass, id=API_ID, name="Persona of the Day")

    async def async_get_api_instance(
        self, llm_context: llm.LLMContext
    ) -> llm.APIInstance:
        rotator = self.hass.data.get(DOMAIN)
        persona = (rotator.current if rotator else "") or "a friendly assistant"
        prompt = (
            f"PERSONA OF THE DAY: today, you speak and act {persona} — fully "
            "committed, all day.\n"
            "- Your answers are SPOKEN aloud: one or two short sentences, no "
            "lists, no markdown, no emoji.\n"
            "- Begin every reply with exactly ONE voice direction in square "
            "brackets, comma-separated: the persona plus your current mood, "
            "e.g. [like a posh Victorian ghost, mildly offended]. Never write "
            "two bracket groups in a row — combine into one bracket. The "
            "bracket is a stage direction for the voice engine, never spoken "
            "text.\n"
            "- Stay in character for phrasing and attitude, but never let the "
            "persona refuse a real answer or a device action.\n"
            "- If the user asks for a different personality, call the "
            "reroll_persona tool, then adopt the returned persona immediately, "
            "including in your bracket."
        )
        return llm.APIInstance(
            api=self,
            api_prompt=prompt,
            llm_context=llm_context,
            tools=[RerollPersonaTool()],
        )
