"""Constants for Persona of the Day."""

DOMAIN = "persona_rotator"

STORAGE_KEY = "persona_rotator.state"
STORAGE_VERSION = 1

HISTORY_CAP = 30

# Options-flow / service import limits. Personas are short spoken-style
# descriptors ("like a noir detective narrating his own coffee break");
# anything longer than this is almost certainly a pasted prompt, not a
# persona.
MAX_PERSONA_LENGTH = 120

CONF_IMPORT_TEXT = "personas"
