# Persona Generator

Want more personas? Paste the prompt below into any AI chatbot (Claude,
ChatGPT, Gemini — all work). Then paste its output into Home Assistant:
**Settings → Devices & Services → Persona of the Day → Configure**, or call
the `persona_rotator.import_personas` service.

---

## The prompt

Copy everything in the block below:

```
Generate 15 personas for my home voice assistant. Every day it adopts one
persona and answers all my questions in that voice.

Format — STRICT:
- One persona per line, no numbering, no bullets, no quotes.
- Each line starts with "like " and describes a VOICE and ATTITUDE,
  e.g.: like a noir detective narrating his own coffee break
- Maximum 100 characters per line.
- Never use square brackets [ ] — those are reserved for the voice engine.

What makes a good persona:
- It must be AUDIBLE: a listener should recognize it from sound alone —
  delivery, rhythm, vocabulary, attitude. "like a chess grandmaster" is
  weak (how does that SOUND?); "like a chess grandmaster who treats every
  question as a losing position" is strong.
- Specific beats generic: "like a 1940s radio announcer with crackling
  delivery" beats "like an old-timey announcer".
- It must survive mundane content: this voice will announce timers and
  weather. Personas that only work for drama fall flat.
- Family-friendly, and funny through delivery rather than insult.

Mix these flavors across the 15: fictional archetypes, historical or
professional voices, absurd contradictions (a pirate doing customer
service), emotional registers (barely containing excitement about
everything), and delivery quirks (speaks only in questions).
```

---

## Tips

- Ask for a different mix ("more villains", "make them Australian", "all
  cooking-themed") — the format rules keep the output importable.
- Paste the assistant's current catalog into the chat and add "avoid
  anything similar to these" to push into fresh territory.
- Entries that break the rules (too long, contains brackets) are rejected
  with a clear error on import — fix the line and paste again.
