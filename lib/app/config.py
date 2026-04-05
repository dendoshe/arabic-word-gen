"""
Shared configuration constants for the OLED vocab app.
"""

FACE_OFF_HOLD_MS = 2000

PRIMARY_DISPLAY = {
    "name": "primary",
    "sda_pin": 0,
    "scl_pin": 1,
    "i2c_id": 0,
}

SECONDARY_DISPLAY = {
    "name": "secondary",
    "sda_pin": 2,
    "scl_pin": 3,
    "i2c_id": 1,
}

DISPLAY_CONFIGS = (
    PRIMARY_DISPLAY,
    SECONDARY_DISPLAY,
)

SDA_PIN = PRIMARY_DISPLAY["sda_pin"]
SCL_PIN = PRIMARY_DISPLAY["scl_pin"]
I2C_ID = PRIMARY_DISPLAY["i2c_id"]

# Button wiring
BUTTON1_PIN = 18
BUTTON2_PIN = 19
BUTTON3_PIN = 20

DEFAULT_WORD_KEY = "kitab"

# Editable vocab source of truth
WORD_PATHS = ("words.json",)

# Display refresh
FPS = 30

# Frame pages config
PAGES = [{"clear_only": True}]
