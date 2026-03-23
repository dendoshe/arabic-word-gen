from lib.app import words as words_mod
from lib.ui import animation_views, views

PRIMARY_SCREEN = "primary"
SECONDARY_SCREEN = "secondary"


def draw_displays(display, state, words):
    if hasattr(display, "screen"):
        draw_grouped_displays(display, state, words)
        return
    views.draw_overlay(display, state, words)


def draw_grouped_displays(display_group, state, words):
    word = words_mod.get_word(state, words)
    primary = safe_screen(display_group, PRIMARY_SCREEN)
    secondary = safe_screen(display_group, SECONDARY_SCREEN)
    primary_ready = primary and primary.is_ready()
    secondary_ready = secondary and secondary.is_ready()
    ui_screen = primary if primary_ready else secondary

    if ui_screen and ui_screen.is_ready():
        views.draw_overlay(ui_screen, state, words)
    if secondary_ready and secondary is not ui_screen:
        animation_views.draw_secondary_animation(secondary, state, word)


def safe_screen(display_group, name):
    try:
        return display_group.screen(name)
    except Exception:
        return None
