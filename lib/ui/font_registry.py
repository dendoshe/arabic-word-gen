"""
Runtime wrapper for the generated Arabic bitmap font.

Glyph-based font stored as (GLYPHS, BITMAP_DATA).
"""

from . import arabic_font
from . import bitmap_font


def glyphs():
    return arabic_font.glyphs()


def is_ready() -> bool:
    g = arabic_font.glyphs()
    data = arabic_font.bitmap_data()
    return bool(g) and bool(data)


def bitmap_size() -> int:
    data = arabic_font.bitmap_data()
    try:
        return len(data) if data else 0
    except Exception:
        return 0


def has_glyph(codepoint: int) -> bool:
    return int(codepoint) in arabic_font.glyphs()


def measure(text: str) -> int:
    return bitmap_font.measure_text(arabic_font.glyphs(), text)


def draw(oled, text: str, x: int, y: int, *, rtl: bool = True) -> int:
    return bitmap_font.draw_text(oled, arabic_font.glyphs(), arabic_font.bitmap_data(), text, x, y, rtl=rtl)


def center(oled, text: str, y: int, *, rtl: bool = True) -> bool:
    return bitmap_font.center_text(oled, arabic_font.glyphs(), arabic_font.bitmap_data(), text, y, rtl=rtl)


def register_font(glyphs_dict, bitmap, meta_dict=None) -> None:
    arabic_font.register_font(glyphs_dict, bitmap, meta_dict)
