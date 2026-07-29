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

Pick ONE of the two paths:

<details open>
<summary><b>Path A — via HACS</b> (recommended: you get update notifications)</summary>

HACS is the community app store for Home Assistant (requires a free
GitHub account). If you don't have it yet, install it first with the
[official HACS guide](https://www.hacs.xyz/docs/use/download/download/) —
choose the instructions matching your Home Assistant installation type.
After installing its files, activate it via Settings → Devices & Services →
Add Integration → "HACS". During its setup, sign in to GitHub fully first —
the HACS device code goes on the "Device activation" page that appears
*after* login (not into any two-factor prompt). Once done, **HACS lives in
the left sidebar** — that's where you use the store from.

1. Open **HACS from the left sidebar** (it appears there once installed and
   activated), then open the **three-dot menu** (top right) → **Custom repositories**
2. Paste `https://github.com/TheSchultz/ha-persona-of-the-day`,
   pick type **Integration**, click **Add**

   [![Open your Home Assistant instance and add this repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=TheSchultz&repository=ha-persona-of-the-day&category=integration)
   *(this badge does steps 1-2 for you)*
3. **Adding the repository only lists it in the store — it is not installed
   yet.** Now search "Persona of the Day" in HACS's main list, open it, and
   click the **Download** button (bottom right)
4. **Restart Home Assistant** (Settings → System → Restart)

</details>

<details>
<summary><b>Path B — manual copy</b> (no HACS, no automatic updates)</summary>

1. [Download this repository as a ZIP](https://github.com/TheSchultz/ha-persona-of-the-day/archive/refs/heads/main.zip) and unpack it
2. Copy the folder `custom_components/persona_rotator` into your Home
   Assistant `config/custom_components/` folder (create
   `custom_components` if it doesn't exist)
3. **Restart Home Assistant** (Settings → System → Restart)

</details>

**Then, on either path:**

5. Go to **Settings → Devices & Services → Add Integration** and search
   "**Persona of the Day**"

   [![Open your Home Assistant instance and start setting up this integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=persona_rotator)
6. Click **Submit** — there is nothing to configure

Done: `sensor.persona_of_the_day` now holds today's persona, and a
**notification** (bell at the bottom of the left sidebar) appears with your
next steps — which are exactly **steps 2-5 below**, so if you dismissed it
or can't find it, just keep reading here. See it and the **Persona re-roll** button on the device
page: Settings → Devices & Services → Persona of the Day → **1 device**.

### 2. Get your (free) Google AI key and add the conversation agent

- Get an API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
  (Google account, free tier, no billing setup)
- Settings → Devices & Services → **Add Integration** → search "**Gemini**" —
  the result is the **Google** brand tile; click it, then pick **Google Gemini**
  from Google's list (named "Google Generative AI" before HA 2026) → paste the key
- A "Name and assign" screen lists the Gemini devices it created (Task,
  Conversation, STT, TTS) — just click **Skip and finish**; nothing there is required

This one integration provides both the conversation agent (the brain) and a
Gemini TTS entity (the voice) — Gemini's TTS is what makes personas *sound*
like personas, because it interprets `[bracketed voice directions]` instead of
reading them aloud.

### 3. Turn on the persona (one checkbox)

Settings → Devices & Services → **Google Gemini** → find the **Google AI
Conversation** service (labeled "Conversation agent") → click **its gear
icon** → under **"Control Home Assistant"**, tick **Persona of the Day**
in the list → Save.

That's it — the daily persona and its voice rules are now injected into
the agent automatically, always current, no copying. It even adds a voice
command: say *"give me a different personality"* and the agent re-rolls
the persona on the spot.

<details>
<summary><b>Manual alternative</b> (for conversation agents without the
"Control Home Assistant" option)</summary>

Paste this into the agent's Instructions/prompt field:

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

</details>

### 4. Wire up your voice pipeline

Settings → Voice assistants → your assistant:
- **Conversation agent**: Google Gemini
- **Text-to-speech**: Google Gemini TTS (try different voices — they
  take the persona directions differently)

**Test it now, before any hardware**: open **Assist** (chat icon, top-right of
the Overview dashboard) and type a question — the reply comes back in today's
persona. Note: until this step 4 is saved, Assist answers everything with
"Sorry, I couldn't understand that" — that's the built-in agent, not a bug.
For *audible* browser testing, a microphone icon appears in the Assist dialog
(requires Chrome-family browser on `localhost` or HTTPS; if it's missing
after a settings change, hard-refresh the page).

### 5. Give it ears (hardware)

A voice assistant needs a device that *listens*. Amazon Echo and Google Home
speakers cannot do this — their microphones only serve their own assistants.
What works:

| Device | Cost | Effort |
|---|---|---|
| [Home Assistant Voice Preview Edition](https://www.home-assistant.io/voice-pe/) | ~$59 | Plug in, assign your assistant, say "Okay Nabu" |
| ESP32-S3-BOX / M5 Atom Echo (DIY satellite) | ~$15-50 | One-click ESPHome flash |
| Spare phone/tablet with the HA Companion app | free | Assist built into the app |

Your existing good speakers (Sonos, Cast, etc.) still matter — as the
*output*. Replies can play through any `media_player`, so the classic setup
is a small listening device on the shelf and answers through the big
speakers. See [docs/speakers.md](docs/speakers.md).

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
