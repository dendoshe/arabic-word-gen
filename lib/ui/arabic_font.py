"""
Arabic bitmap font (glyphs + shared bitmap data).

This is the runtime wrapper; the actual glyph tables are generated into
lib/ui/arabic_font_data.py by tools/gen_arabic_font.py.
"""

from . import arabic_font_data

_GLYPHS = arabic_font_data.GLYPHS
_BITMAP_DATA = arabic_font_data.BITMAP_DATA
_META = arabic_font_data.META


def glyphs():
    return _GLYPHS


def bitmap_data():
    return _BITMAP_DATA


def meta():
    return _META


def register_font(glyphs_dict, bitmap, meta_dict=None) -> None:
    """
    Override the active font at runtime.
    `bitmap` should be a bytearray (writable) so FrameBuffer can reference it.
    """
    global _GLYPHS, _BITMAP_DATA, _META
    _GLYPHS = glyphs_dict or {}
    _BITMAP_DATA = bitmap or bytearray()
    if meta_dict is not None:
        _META = meta_dict
