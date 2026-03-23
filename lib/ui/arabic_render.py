"""
Single, readable entry-point for rendering Arabic in the UI.

Arabic is rendered via the glyph-based bitmap font:
  - `lib/ui/arabic_font_data.py` provides (GLYPHS, BITMAP_DATA)
  - `lib/ui/font_registry.py` renders strings onto the SSD1306
"""

from . import font_registry
from . import bitmap_font

_WARNED_MISSING_FONT = False
_WARNED_RENDER_ERROR = False


def _is_arabic_letter(cp: int) -> bool:
    return (0x0600 <= cp <= 0x06FF) or (0x0750 <= cp <= 0x077F) or (0x08A0 <= cp <= 0x08FF)


def center(oled, text: str, y: int, *, rtl: bool = True) -> bool:
    """
    Draw Arabic text centered on the OLED.
    Returns False if the font/glyphs are missing.
    """
    if not text:
        return False
    if not font_registry.is_ready():
        global _WARNED_MISSING_FONT
        if not _WARNED_MISSING_FONT:
            _WARNED_MISSING_FONT = True
            print(
                "Arabic font not generated (lib/ui/arabic_font_data.py has no glyphs). "
                "Run: ARABIC_FONT=/path/to/font.ttf python3 tools/gen_arabic_font.py"
            )
        return False
    try:
        return font_registry.center(oled, text, y, rtl=rtl)
    except Exception as exc:
        global _WARNED_RENDER_ERROR
        if not _WARNED_RENDER_ERROR:
            _WARNED_RENDER_ERROR = True
            print("Arabic render error:", repr(exc))
        return False


def center_root(oled, root_text: str, y: int, *, hyphen_adv: int = 8, hyphen_len: int = 6) -> bool:
    """
    Center-render an Arabic root with hyphens between letters (e.g. ك-ت-ب).

    This draws each letter as an isolated glyph (no joining across separators) and
    draws hyphens as a thin horizontal line.
    """
    if not root_text:
        return False
    if not font_registry.is_ready():
        # Trigger the same warning path as normal text rendering.
        return center(oled, root_text, y, rtl=True)

    letters = [ch for ch in root_text if _is_arabic_letter(ord(ch))]
    if not letters:
        return False

    glyphs = font_registry.glyphs()

    entries = []
    total_w = 0
    min_top = None
    max_bottom = None
    for ch in letters:
        cp = ord(ch)
        entry = bitmap_font.get_glyph(glyphs, cp, "isolated")
        if not entry:
            return False
        adv = int(entry.get("xAdvance") or entry.get("w") or 0)
        total_w += adv
        entries.append((ch, entry, adv))

        top = int(y) + int(entry.get("yOffset") or 0)
        bottom = top + int(entry.get("h") or 0)
        min_top = top if min_top is None else min(min_top, top)
        max_bottom = bottom if max_bottom is None else max(max_bottom, bottom)

    if len(entries) > 1:
        total_w += int(hyphen_adv) * (len(entries) - 1)

    if total_w <= 0:
        return False

    x0 = max(0, (oled.width - total_w) // 2)
    cursor_x = int(x0) + int(total_w)

    # Place hyphens around the vertical middle of the glyph span.
    hyphen_y = int(y)
    if min_top is not None and max_bottom is not None and max_bottom > min_top:
        hyphen_y = (min_top + max_bottom) // 2

    for idx, (ch, _entry, adv) in enumerate(entries):
        cursor_x -= int(adv)
        # Draw as a single isolated glyph (rtl doesn't matter for 1 char).
        font_registry.draw(oled, ch, cursor_x, y, rtl=True)

        if idx < len(entries) - 1:
            cursor_x -= int(hyphen_adv)
            start_x = int(cursor_x) + max(0, (int(hyphen_adv) - int(hyphen_len)) // 2)
            try:
                oled.hline(start_x, int(hyphen_y), int(hyphen_len), 1)
            except Exception:
                # If hline isn't available for some reason, just skip separators.
                pass

    return True
