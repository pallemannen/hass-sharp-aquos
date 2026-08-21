"""Constants for the Sharp Aquos TV integration."""

DOMAIN = "aquostv"

CONF_POWER_ON_ENABLED = "power_on_enabled"

DEFAULT_PORT = 10002
DEFAULT_USERNAME = ""
DEFAULT_PASSWORD = ""
DEFAULT_NAME = "Sharp Aquos TV"
DEFAULT_POWER_ON_ENABLED = False

# Poll cadence. The TV is reached over a fresh TCP connection per command, so a
# full update can be several sequential round trips - keep this well above the
# per-command timeout.
UPDATE_INTERVAL_SECONDS = 15

SOURCE_TV_ANTENNA = "TV / Antenna"
SOURCE_HDMI_1 = "HDMI 1"
SOURCE_HDMI_2 = "HDMI 2"
SOURCE_HDMI_3 = "HDMI 3"
SOURCE_HDMI_4 = "HDMI 4"
SOURCE_COMPONENT = "Component"

# IAVD<n> value -> source name. 0 is special-cased to the ITVD command.
SOURCES = {
    0: SOURCE_TV_ANTENNA,
    1: SOURCE_HDMI_1,
    2: SOURCE_HDMI_2,
    3: SOURCE_HDMI_3,
    4: SOURCE_HDMI_4,
    5: SOURCE_COMPONENT,
}
SOURCES_REVERSE = {v: k for k, v in SOURCES.items()}

# AVMD picture-preset codes, as documented against the user's own TV.
AV_MODES = {
    1: "Standard",
    2: "Movie",
    3: "Game",
    4: "User",
    5: "Dynamic",
}

# WIDE / aspect-ratio codes. Sharp's manuals list more values than any one
# model actually supports - unknown codes are shown as their raw number
# rather than guessed at.
ASPECT_RATIOS = {
    1: "Side Bar",
    2: "S.Stretch",
    3: "Zoom",
    4: "Stretch",
    5: "Normal",
    6: "Zoom (PC)",
    7: "Stretch (PC)",
    8: "Dot by Dot",
    9: "Full Screen",
    10: "Auto",
    11: "Original",
}
