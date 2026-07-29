# Routing voice replies to better speakers

Stock Home Assistant voice pipelines answer on the device that heard you —
a Voice PE, an ESP32 satellite, your phone. If you'd rather hear the persona
on proper speakers, here is what reliably works (learned the hard way on
Sonos hardware).

## The one rule: use `announce: true`

When sending TTS or any clip to a smart speaker via `media_player.play_media`,
set `announce: true`. It uses the speaker's announcement pipeline, which:

- **Preempts** whatever is playing, plays your clip, and hands back —
  instead of fighting the music queue.
- **Bypasses queue managers.** If the same physical speaker is claimed by
  two integrations (e.g. Music Assistant AND a native integration), a normal
  `play_media` gets processed by both and can wedge or play at broken
  volume. Announce mode is a direct command that sidesteps every queue.
- **Required for WAV streams** on Sonos (normal mode rejects them with
  UPnP error 714). MP3 works in either mode.

Trade-off: announce-mode playback is not pauseable (stop works).

Also note: during announce playback, Sonos reports its state as `idle`, not
`playing` — don't build conditions on `state == 'playing'`, they will never
fire.

## Example: forward assist replies to a speaker

A minimal automation that speaks a TTS message on a chosen speaker:

```yaml
service: tts.speak
data:
  media_player_entity_id: media_player.living_room
  message: "{{ your_text }}"
target:
  entity_id: tts.google_ai_tts
```

The `tts.speak` service handles the media routing; for advanced setups
(streaming proxies, custom announcement chimes) announce-mode
`play_media` with a URL is the escape hatch.

## Two integrations, one speaker

If a speaker appears twice (e.g. `media_player.living_room` and
`media_player.living_room_2`) you have two integrations bound to the same
hardware — both observe every `play_media` call. Either remove one
integration or use `announce: true`, which bypasses the conflict.
