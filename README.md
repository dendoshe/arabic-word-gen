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

If you do not have the Pico/OLED hardware with you, you can run the desktop simulator:

- `python3 tools/simulate_display.py`
- `python3 tools/simulate_display.py --word kitab`
- `python3 tools/simulate_display.py --view forms --form-index 1`

This opens a small window with two OLED-style screens and three virtual buttons. You can
click the buttons or press keys `1`, `2`, and `3` to move through the same views as the
hardware version. If you want a larger desktop view, add `--scale 3` or `--scale 4`.

## Hardware vs Simulator

The project has two entrypoints:

- `main.py`: real Pico hardware path
- `python3 tools/simulate_display.py`: desktop simulator path

They share the same app state and UI drawing code, especially `lib/ui/dual_screen.py`.
The difference is the display backend:

- hardware uses `lib/hardware/oled_display.py` to send draw calls to real SSD1306 OLEDs
- simulation uses `lib/display/recording.py` to record draw calls into frame data, then
  `lib/desktop/simulator.py` paints that recorded frame into Tk canvases

This keeps the simulator detached from Pico-specific rendering code while avoiding a second
copy of the UI renderer.

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

The app loads words from `words.json` at the repo root.
If that file is missing or invalid, it falls back to the in-code `DEFAULT_WORDS`
mapping in `lib/app/words.py`.

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

Each word can set its animation directly in `words.json` with an optional `animation` field:

```json
"maa": {
  "animation": "water"
}
```

The wiring is:

1. `words.json` defines the current word data and its `animation` name
2. `lib/ui/dual_screen.py` sends the active word to the secondary screen renderer
3. `lib/ui/animation_views.py` resolves `word["animation"]`
4. the `ANIMATIONS` registry picks the matching draw function
5. that draw function renders the secondary display for the current frame

`lib/ui/animation_views.py` keeps the whole animation skeleton:

- one animation name per word
- one `ANIMATIONS` registry mapping animation name to draw function
- one render call for the current word

If a word has no `animation`, or uses an unknown one, the renderer falls back to `pulse`.

Supported animation ids are `water`, `sun`, `moon`, `house`, `peace`, `man`, `woman`, `boy`,
`girl`, `dog`, and `pulse`. `walker` is still accepted as a legacy alias for `man`.
