# Persona of the Day for Home Assistant

**Give your Home Assistant voice assistant a new personality every day.**

One day it's a posh Victorian ghost. The next, a 1940s radio announcer. Then a
conspiracy theorist whispering in a basement. Same smart home, same commands —
a completely different character answers, every single day, picked from a
catalog of **121 built-in personas** (and infinitely extendable with your own).

It works with stock Home Assistant and **one free API key**. No cloud
subscription, no custom hardware, no YAML.

## How it works

This integration provides `sensor.persona_of_the_day` — a daily,
non-repeating persona picked from your catalog (no repeats within the last 30
days, and editing the catalog never reshuffles the schedule). You reference
that sensor in your voice assistant's prompt, and pair it with a TTS engine
that understands voice directions. That's the whole trick.

```
persona_rotator (this integration)
        │  sensor.persona_of_the_day = "like a posh Victorian ghost"
        ▼
conversation agent prompt  ──►  LLM answers IN CHARACTER, prefixed with a
                                voice direction like [posh Victorian ghost,
                                mildly offended]
        ▼
Gemini TTS  ──►  reads the direction, ACTS the line out loud
```

## Setup (about 10 minutes)

### 1. Install this integration

- HACS → three-dot menu → **Custom repositories** → add
  `https://github.com/TheSchultz/ha-persona-of-the-day` (type: Integration)
- Install **Persona of the Day**, restart Home Assistant
- Settings → Devices & Services → **Add Integration** → Persona of the Day

You now have `sensor.persona_of_the_day` and a **Persona re-roll** button.

### 2. Get your (free) Google AI key and add the conversation agent

- Get an API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
  (Google account, free tier, no billing setup)
- Settings → Devices & Services → **Add Integration** → **Google Generative AI**
  → paste the key

This one integration provides both the conversation agent (the brain) and a
Gemini TTS entity (the voice) — Gemini's TTS is what makes personas *sound*
like personas, because it interprets `[bracketed voice directions]` instead of
reading them aloud.

### 3. Paste the persona prompt

Settings → Devices & Services → Google Generative AI → **Configure** (the
conversation agent) → set **Instructions** to:

```
You are a home voice assistant. Today, you speak and act
{{ states('sensor.persona_of_the_day') }} — fully committed, all day.

Rules:
- Answers are SPOKEN: one or two short sentences. No lists, no markdown,
  no emoji.
- Begin every reply with exactly ONE voice direction in square brackets,
  comma-separated: the persona plus your current mood. Example:
  [like a posh Victorian ghost, mildly offended]
- Never write two bracket groups in a row — combine everything into one
  bracket. The bracket is a stage direction for the voice engine, never
  spoken text.
- Stay in character for phrasing and attitude, but never let the persona
  refuse a real answer or a device action.
```

### 4. Wire up your voice pipeline

Settings → Voice assistants → your assistant:
- **Conversation agent**: Google Generative AI
- **Text-to-speech**: Google Generative AI TTS (try different voices — they
  take the persona directions differently)

Say "what time is it?" — then say it again tomorrow. Different character.

## Adding your own personas

Use the [persona generator prompt](PERSONA_GENERATOR.md) with any AI chatbot,
then paste the output into **Settings → Devices & Services → Persona of the
Day → Configure**. One persona per line; entries are validated and duplicates
skipped. Power users can call the `persona_rotator.import_personas` service.

## Entities & services

| Thing | What it does |
|---|---|
| `sensor.persona_of_the_day` | Today's persona. Attributes: full catalog, rotation history, last-rotated date |
| `button.persona_re_roll` | Not feeling today's character? Tap to re-roll |
| `persona_rotator.rotate` | Same as the button, as a service |
| `persona_rotator.add` / `remove` | Single-persona catalog edits |
| `persona_rotator.import_personas` | Bulk paste, one per line |
| `persona_rotator.reset_catalog` | Restore the built-in 121 |

## Routing replies to better speakers

By default, HA voice replies play on the device that heard you. If you want
answers on proper speakers (Sonos etc.), the reliable pattern is a
`media_player.play_media` call with **`announce: true`** — it bypasses queue
managers and plays over whatever else is happening. Full guidance in
[docs/speakers.md](docs/speakers.md).

## FAQ

**Does it work with other conversation agents (Claude, OpenAI, local)?**
Yes — any agent whose prompt can template `{{ states('sensor.persona_of_the_day') }}`.
The bracket voice directions, however, only come alive with Gemini TTS; other
TTS engines will read them aloud, so remove the bracket rule from the prompt
if you use one.

**Why doesn't the persona repeat?**
The last 30 picks are excluded from eligibility. History is tracked by
persona text, not list position, so editing the catalog never causes repeats
or reshuffles.

**Can I force a specific persona?**
Remove everything else, or call `persona_rotator.add` with your pick and
`rotate` until it lands — a "pin persona" feature is on the roadmap.

## License

MIT
