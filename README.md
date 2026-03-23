# Pico OLED Blink (MicroPython)

Copies to a Raspberry Pi Pico/Pico W and blinks an I2C OLED (typically SSD1306).

## Wiring

### Primary OLED

- `VCC` → `3V3`
- `GND` → `GND`
- `SDA` → `GP0`
- `SCL` → `GP1`

### Secondary OLED

- `VCC` → `3V3`
- `GND` → `GND`
- `SDA` → `GP2`
- `SCL` → `GP3`

## Run

1. Copy these files onto the Pico filesystem: `main.py`, `ssd1306.py`, `words.json`, and the `lib/` folder
2. Reset / power cycle the Pico
3. (Optional) Open a serial/REPL to see debug prints

Note: this is MicroPython code (it won't run under desktop Python).

The code now reads `DISPLAY_CONFIGS` in `lib/app/config.py` and initializes each OLED separately.
Each bus tries SoftI2C first (more tolerant) and then hardware I2C, looking for an OLED at
`0x3C`/`0x3D`.

Current behavior:

- `primary` shows the vocab UI
- `secondary` shows a paired animation for the active word
- if only one OLED is connected, the vocab UI still works on that screen

If no OLED is found on either bus, it blinks the onboard LED instead (so you know the script is running).

If you wire a button to `GP18` (pull-up), you can press it to advance the page early.

## Vocabulary Data (words.json)

The app loads words from the first valid file in `lib/app/config.py#WORD_PATHS`:

- `words.json` (top-level, easiest to edit)
- `lib/app/resources/words.json` (fallback default)

To validate a file on your computer:

- `python3 tools/validate_words.py words.json`

## Arabic Rendering Assets

Arabic is drawn via a glyph-based bitmap font stored as:

- `lib/ui/arabic_font_data.py`: `GLYPHS` metadata + one `BITMAP_DATA` blob (MONO_VLSB)
- `tools/gen_arabic_font.py`: generator that creates/overwrites that file (desktop only)
- `lib/ui/arabic_render.py`: UI entry-point used by views

Note: the repo ships with an empty `arabic_font_data.py` stub; generate real data
before copying to the Pico if you want Arabic text to appear.

## If your OLED doesn't blink

Edit `DISPLAY_CONFIGS` in `lib/app/config.py` to match your wiring.

## Word Animation Hook

The secondary screen uses a descriptor-driven scene renderer in `lib/ui/animation_views.py`.
Each animation is built from a small set of reusable primitives and scene elements, so adding
new words usually means mapping a word to a scene id instead of writing a new draw function.

The animation is chosen by word key / meaning, and you can override it per word
with an optional `animation` field in `words.json`:

```json
"maa": {
  "animation": "water"
}
```

or:

```json
"bint": {
  "animation": {
    "scene": "girl"
  }
}
```

Supported scene ids are `water`, `sun`, `moon`, `house`, `peace`, `man`, `woman`, `boy`,
`girl`, `dog`, and `pulse`. `walker` is still accepted as a legacy alias for `man`.
