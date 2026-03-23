import utime

from lib.app import config, navigation, words
from lib.hardware.gpio import blink_led_forever, Button
from lib.hardware.oled_display import OledDisplayGroup
from lib.app.oled_app import OledApp
from lib.ui import dual_screen, font_registry

# Load data and instantiate hardware
_glyphs = font_registry.glyphs()
WORDS = words.load_words(config.WORD_PATHS, glyphs=_glyphs if _glyphs else None)

buttons = {
    1: Button(config.BUTTON1_PIN, debounce_ms=30),
    2: Button(config.BUTTON2_PIN, debounce_ms=30),
    3: Button(config.BUTTON3_PIN, debounce_ms=30),
}

power_off_requested = False
power_off_started_at = None


def tick(state, now_ms):
    state["now_ms"] = now_ms
    update_power_off(now_ms)
    navigation.handle_buttons(
        state,
        now_ms,
        buttons,
        word_lookup=lambda s: words.get_word(s, WORDS),
    )


def update_power_off(now_ms):
    global power_off_requested, power_off_started_at
    if power_off_requested:
        return

    if buttons[3].is_pressed():
        if power_off_started_at is None:
            power_off_started_at = now_ms
        elif utime.ticks_diff(now_ms, power_off_started_at) >= config.FACE_OFF_HOLD_MS:
            power_off_requested = True
    else:
        power_off_started_at = None


def should_power_off():
    return power_off_requested


def draw_overlay(oled, state):
    dual_screen.draw_displays(oled, state, WORDS)


def main():
    global power_off_requested, power_off_started_at
    power_off_requested = False
    power_off_started_at = None
    display = OledDisplayGroup()
    overlay_state = {
        "view": "base",
        "word_key": words.initial_word_key(WORDS),
        "last_pressed": {1: False, 2: False, 3: False},
        "form_idx": 0,
        "now_ms": 0,
        "changed_at": 0,
    }
    app = OledApp(display)
    ok = False
    interrupted = False
    try:
        ok = app.run(
            display_configs=config.DISPLAY_CONFIGS,
            wait_next=None,
            button_is_pressed=lambda: False,  # frame loop never advances automatically
            pages=config.PAGES,
            verbose=True,
            strict=False,
            tick=tick,
            fps=config.FPS,
            loop_pages=True,
            stop_requested=should_power_off,
            draw_overlay=draw_overlay,
            overlay_state=overlay_state,
        )
    except KeyboardInterrupt:
        interrupted = True
    finally:
        app.safe_off()

    if interrupted:
        return
    if not ok:
        blink_led_forever()


main()
