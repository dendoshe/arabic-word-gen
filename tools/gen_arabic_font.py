"""
Generate a compact Arabic bitmap font:
  - GLYPHS mapping base codepoint -> contextual forms metadata
  - One concatenated BITMAP_DATA bytearray (MONO_VLSB)

Requires (desktop Python):
  pip install pillow arabic-reshaper

Notes:
  - We use arabic_reshaper to obtain the presentation-form codepoints for each
    letter's contextual form, then render that single presentation-form glyph.
  - This produces per-letter bitmaps that can be composed on-device without
    needing arabic_reshaper/python-bidi.

Usage:
  ARABIC_FONT=/path/to/your/arabic.ttf python3 tools/gen_arabic_font.py
  ARABIC_FONT_SIZE=18 python3 tools/gen_arabic_font.py
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as e:  # pragma: no cover - tool script
    raise SystemExit("Pillow is required. Install with `pip install pillow`.") from e

try:
    import arabic_reshaper
except Exception as e:  # pragma: no cover - tool script
    raise SystemExit("arabic-reshaper is required. Install with `pip install arabic-reshaper`.") from e


ROOT = Path(__file__).resolve().parents[1]
WORDS_PATHS = (
    ROOT / "words.json",
    ROOT / "lib" / "app" / "resources" / "words.json",
)
OUTPUT_PATH = ROOT / "lib" / "ui" / "arabic_font_data.py"

DEFAULT_FONT = os.environ.get("ARABIC_FONT") or "SFArabic.ttf"
FONT_SIZE = int(os.environ.get("ARABIC_FONT_SIZE") or "18")

# A strong dual-joining letter used to force contextual forms during reshaping.
_JOINER = "ب"

# Fallback Arabic spellings so you can generate a useful font without adding
# Arabic text into words.json.
ARABIC_TEXT_FALLBACK = {
    "maa": {"base": "ماء", "forms": ["ماء", "الماء", "مياه"]},
    "bayt": {"base": "بيت", "forms": ["بيت", "البيت", "بيوت"]},
    "salam": {"base": "سلام", "forms": ["سلام", "السلام", "سلامة"]},
    "shams": {"base": "شمس", "forms": ["شمس", "الشمس", "شموس"]},
    "qamar": {"base": "قمر", "forms": ["قمر", "القمر", "أقمار"]},
    "rajul": {"base": "رجل", "forms": ["رجل", "رجال", "الرجل"]},
    "imraah": {"base": "امرأة", "forms": ["امرأة", "نساء", "المرأة"]},
    "walad": {"base": "ولد", "forms": ["ولد", "أولاد", "الولد"]},
    "kalb": {"base": "كلب", "forms": ["كلب", "كلاب", "الكلب"]},
    "bint": {"base": "بنت", "forms": ["بنت", "بنات", "البنت"]},
}


def load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(DEFAULT_FONT, size)
    except OSError as e:  # pragma: no cover - tool script
        raise SystemExit(
            f"Could not load font '{DEFAULT_FONT}'. "
            "Set ARABIC_FONT to a valid Arabic-capable TTF/OTF."
        ) from e


def pack_mono_vlsb(img: Image.Image) -> Tuple[int, int, bytearray]:
    w, h = img.size
    buf = bytearray(w * ((h + 7) // 8))
    pixels = img.load()
    for y in range(h):
        byte_row = (y // 8) * w
        bit = 1 << (y & 7)
        for x in range(w):
            if pixels[x, y]:
                buf[byte_row + x] |= bit
    return w, h, buf


def render_glyph(ch: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int, int, int, int, bytearray]:
    """
    Render a single (presentation-form) glyph into MONO_VLSB.

    Returns: (w, h, xAdvance, xOffset, yOffset, buf)
    """
    pad = 10
    img = Image.new("1", (64, 64), 0)
    draw = ImageDraw.Draw(img)
    draw.text((pad, pad), ch, fill=1, font=font)
    bbox = img.getbbox()
    if not bbox:
        return 0, 0, 0, 0, 0, bytearray()
    x0, y0, x1, y1 = bbox
    cropped = img.crop(bbox)

    # Pillow doesn't consistently expose xAdvance for glyphs; approximate using textlength/size.
    try:
        x_adv = int(round(draw.textlength(ch, font=font)))
    except Exception:
        x_adv = int(font.getsize(ch)[0])

    x_off = x0 - pad
    y_off = y0 - pad
    w, h, buf = pack_mono_vlsb(cropped)
    return w, h, x_adv, x_off, y_off, buf


def presentation_forms_for_base(base_char: str) -> Dict[str, str]:
    """
    Use arabic_reshaper to derive the contextual presentation-form codepoints.
    """
    isolated = arabic_reshaper.reshape(base_char)[0]
    initial = arabic_reshaper.reshape(base_char + _JOINER)[0]
    medial = arabic_reshaper.reshape(_JOINER + base_char + _JOINER)[1]
    final = arabic_reshaper.reshape(_JOINER + base_char)[1]
    return {"isolated": isolated, "initial": initial, "medial": medial, "final": final}


def extract_charset(words: Dict) -> List[str]:
    """
    Best-effort charset extraction from words.json.
    Uses arabic spellings if present, otherwise falls back to translit roots only.
    """
    chars = set()
    for _key, entry in (words or {}).items():
        for field in ("arabic", "root_arabic"):
            val = entry.get(field)
            if isinstance(val, str):
                chars.update(val)
        forms = entry.get("forms") or []
        for f in forms:
            if isinstance(f, dict):
                val = f.get("arabic")
                if isinstance(val, str):
                    chars.update(val)
    if not chars:
        for entry in ARABIC_TEXT_FALLBACK.values():
            chars.update(entry.get("base") or "")
            for form_text in entry.get("forms") or []:
                chars.update(form_text)
    # Also include common letters from existing generator defaults.
    # (This is intentionally conservative; you can always add to CHARSET_EXTRA.)
    charset_extra = os.environ.get("ARABIC_CHARSET_EXTRA") or ""
    chars.update(charset_extra)
    # Filter to Arabic letters only; keep joining helper.
    out = [c for c in chars if "\u0600" <= c <= "\u06FF"]
    if _JOINER not in out:
        out.append(_JOINER)
    return sorted(out)


def main():
    words = {}
    for path in WORDS_PATHS:
        try:
            words = json.loads(path.read_text(encoding="utf-8"))
            break
        except Exception:
            continue
    charset = extract_charset(words)
    if not charset:
        raise SystemExit(
            "No Arabic charset found. Provide ARABIC_CHARSET_EXTRA env var with characters to include."
        )

    font = load_font(FONT_SIZE)

    glyphs: Dict[int, Dict[str, Dict]] = {}
    bitmap = bytearray()

    for ch in charset:
        base_cp = ord(ch)
        forms = presentation_forms_for_base(ch)
        glyphs[base_cp] = {}
        for form_name, pres_ch in forms.items():
            w, h, x_adv, x_off, y_off, buf = render_glyph(pres_ch, font)
            offset = len(bitmap)
            bitmap.extend(buf)
            glyphs[base_cp][form_name] = {
                "w": w,
                "h": h,
                "xAdvance": x_adv,
                "xOffset": x_off,
                "yOffset": y_off,
                "buf_offset": offset,
                "buf_len": len(buf),
            }

    meta = {"line_height": FONT_SIZE, "rtl": True, "font": str(DEFAULT_FONT), "size": FONT_SIZE}

    def fmt_bytes(data: bytearray) -> str:
        return ", ".join(str(b) for b in data)

    lines = []
    lines.append("# Auto-generated by tools/gen_arabic_font.py\n")
    lines.append("# Do not edit by hand.\n\n")
    lines.append(f"META = {meta!r}\n\n")
    lines.append("GLYPHS = {\n")
    for cp in sorted(glyphs.keys()):
        forms = glyphs[cp]
        lines.append(f"    {cp}: {{\n")
        for form_name in ("isolated", "initial", "medial", "final"):
            entry = forms[form_name]
            lines.append(f"        {form_name!r}: {entry!r},\n")
        lines.append("    },\n")
    lines.append("}\n\n")
    lines.append(f"BITMAP_DATA = bytearray([{fmt_bytes(bitmap)}])\n")

    OUTPUT_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote font with {len(glyphs)} base glyphs to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
