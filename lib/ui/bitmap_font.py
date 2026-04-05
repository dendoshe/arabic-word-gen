"""
Bitmap-font helpers for SSD1306 (framebuf.MONO_VLSB).

This supports a compact "real" font layout:
  - One contiguous bitmap bytearray
  - Per-glyph metadata contains buf_offset into that bytearray

Designed to run on MicroPython (Pico) but also import on desktop for linting.
"""

try:
    import framebuf
except ImportError:  # desktop linting fallback
    class _DummyFrameBuffer:
        MONO_VLSB = 4

        def __init__(self, buffer, width, height, fmt):
            self.buffer = buffer
            self.width = int(width)
            self.height = int(height)
            self.format = int(fmt)

        def pixel(self, x, y, color=None):
            x = int(x)
            y = int(y)
            if x < 0 or y < 0 or x >= self.width or y >= self.height:
                return 0
            idx = x + (y // 8) * self.width
            bit = 1 << (y % 8)
            if color is None:
                return 1 if (self.buffer[idx] & bit) else 0
            if color:
                self.buffer[idx] |= bit
            else:
                self.buffer[idx] &= ~bit

    class _DummyFrameBufModule:
        FrameBuffer = _DummyFrameBuffer
        MONO_VLSB = _DummyFrameBuffer.MONO_VLSB

    framebuf = _DummyFrameBufModule()


def mono_vlsb_buf_len(w: int, h: int) -> int:
    return int(w) * ((int(h) + 7) // 8)


def _is_arabic_letter(cp: int) -> bool:
    # Basic Arabic + Arabic Supplement + Arabic Extended-A.
    # (We keep this broad; actual availability is gated by font glyphs.)
    return (0x0600 <= cp <= 0x06FF) or (0x0750 <= cp <= 0x077F) or (0x08A0 <= cp <= 0x08FF)


# Letters that DO NOT connect to the next letter on the left (i.e. they break joining).
# This is a pragmatic subset for common Arabic text on small displays.
_ARABIC_NO_JOIN_NEXT = {
    0x0627,  # ا ALEF
    0x0622,  # آ ALEF WITH MADDA ABOVE
    0x0623,  # أ ALEF WITH HAMZA ABOVE
    0x0625,  # إ ALEF WITH HAMZA BELOW
    0x062F,  # د DAL
    0x0630,  # ذ THAL
    0x0631,  # ر REH
    0x0632,  # ز ZAIN
    0x0648,  # و WAW
    0x0671,  # ٱ ALEF WASLA
    0x0672,  # ٲ ALEF WITH WAVY HAMZA ABOVE
    0x0673,  # ٳ ALEF WITH WAVY HAMZA BELOW
    0x0675,  # ٵ HIGH HAMZA ALEF
    0x0621,  # ء HAMZA (non-joining)
}


def _can_join_prev(cp: int) -> bool:
    if cp in _ARABIC_NO_JOIN_NEXT and cp != 0x0621:
        # These join to previous (right-joining), but not to next.
        return True
    if cp == 0x0621:
        return False
    return _is_arabic_letter(cp)


def _can_join_next(cp: int) -> bool:
    if cp in _ARABIC_NO_JOIN_NEXT:
        return False
    if cp == 0x0621:
        return False
    return _is_arabic_letter(cp)


def shape_arabic(text: str, *, keep_non_arabic: bool = True):
    """
    Minimal Arabic shaping to select isolated/initial/medial/final forms.

    Returns a list of (codepoint, form_str, original_char).
    form_str is one of: isolated, initial, medial, final.
    """
    if not text:
        return []
    cps = [ord(ch) for ch in text]

    out = []
    for i, cp in enumerate(cps):
        ch = text[i]
        if not _is_arabic_letter(cp):
            if keep_non_arabic:
                out.append((cp, "isolated", ch))
            continue

        # Find previous/next Arabic letters (skip non-letters like spaces).
        prev_cp = None
        j = i - 1
        while j >= 0:
            if _is_arabic_letter(cps[j]):
                prev_cp = cps[j]
                break
            if cps[j] == 0x20:  # space breaks joining
                break
            j -= 1

        next_cp = None
        j = i + 1
        while j < len(cps):
            if _is_arabic_letter(cps[j]):
                next_cp = cps[j]
                break
            if cps[j] == 0x20:  # space breaks joining
                break
            j += 1

        join_prev = bool(prev_cp is not None and _can_join_next(prev_cp) and _can_join_prev(cp))
        join_next = bool(next_cp is not None and _can_join_next(cp) and _can_join_prev(next_cp))

        if join_prev and join_next:
            form = "medial"
        elif join_prev and not join_next:
            form = "final"
        elif not join_prev and join_next:
            form = "initial"
        else:
            form = "isolated"

        out.append((cp, form, ch))
    return out


def glyph_entry_buf_len(entry: dict) -> int:
    w = int(entry.get("w") or 0)
    h = int(entry.get("h") or 0)
    return mono_vlsb_buf_len(w, h)


def get_glyph(font_glyphs: dict, cp: int, form: str):
    """
    Fetch a glyph entry dict for a base codepoint and form.
    """
    forms = font_glyphs.get(cp)
    if not forms:
        return None
    entry = forms.get(form) or forms.get("isolated")
    return entry


def get_glyph_fb(font_glyphs: dict, bitmap_data, cp: int, form: str):
    """
    Returns (entry, framebuffer) or (None, None) if missing.
    Caches the FrameBuffer on the entry dict to avoid re-instantiating.
    """
    entry = get_glyph(font_glyphs, cp, form)
    if not entry:
        return None, None
    fb = entry.get("fb")
    if fb is None:
        w = int(entry.get("w") or 0)
        h = int(entry.get("h") or 0)
        offset = int(entry.get("buf_offset") or 0)
        n = int(entry.get("buf_len") or mono_vlsb_buf_len(w, h))
        view = memoryview(bitmap_data)[offset : offset + n]
        fb = framebuf.FrameBuffer(view, w, h, framebuf.MONO_VLSB)
        entry["fb"] = fb
    return entry, fb


def measure_text(font_glyphs: dict, text: str) -> int:
    """
    Returns total xAdvance for shaped Arabic text.
    """
    width = 0
    for cp, form, _ch in shape_arabic(text, keep_non_arabic=False):
        entry = get_glyph(font_glyphs, cp, form)
        if not entry:
            continue
        width += int(entry.get("xAdvance") or entry.get("w") or 0)
    return width


def draw_text(oled, font_glyphs: dict, bitmap_data, text: str, x: int, y: int, *, rtl: bool = True) -> int:
    """
    Draw Arabic text using a glyph mapping + shared bitmap data.

    Returns the pixel width advanced (positive).
    """
    shaped = shape_arabic(text, keep_non_arabic=False)
    if not shaped:
        return 0

    if rtl:
        total_w = 0
        for cp, form, _ch in shaped:
            entry = get_glyph(font_glyphs, cp, form)
            if entry:
                total_w += int(entry.get("xAdvance") or entry.get("w") or 0)
        cursor_x = int(x) + total_w
        for cp, form, _ch in shaped:
            entry, fb = get_glyph_fb(font_glyphs, bitmap_data, cp, form)
            if not entry or not fb:
                continue
            x_adv = int(entry.get("xAdvance") or entry.get("w") or 0)
            cursor_x -= x_adv
            x_off = int(entry.get("xOffset") or 0)
            y_off = int(entry.get("yOffset") or 0)
            oled.blit(fb, cursor_x + x_off, int(y) + y_off)
        return total_w

    cursor_x = int(x)
    total_w = 0
    for cp, form, _ch in shaped:
        entry, fb = get_glyph_fb(font_glyphs, bitmap_data, cp, form)
        if not entry or not fb:
            continue
        x_off = int(entry.get("xOffset") or 0)
        y_off = int(entry.get("yOffset") or 0)
        oled.blit(fb, cursor_x + x_off, int(y) + y_off)
        x_adv = int(entry.get("xAdvance") or entry.get("w") or 0)
        cursor_x += x_adv
        total_w += x_adv
    return total_w


def center_text(oled, font_glyphs: dict, bitmap_data, text: str, y: int, *, rtl: bool = True) -> bool:
    width = measure_text(font_glyphs, text)
    if width <= 0:
        return False
    x = max(0, (oled.width - width) // 2)
    draw_text(oled, font_glyphs, bitmap_data, text, x, y, rtl=rtl)
    return True
