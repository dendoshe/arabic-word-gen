"""
Sanity checks for lib/ui/arabic_font_data.py.

Runs on desktop Python (no external deps).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib.ui import arabic_font_data  # noqa: E402


def mono_vlsb_buf_len(w: int, h: int) -> int:
    return int(w) * ((int(h) + 7) // 8)


def main() -> int:
    glyphs = arabic_font_data.GLYPHS
    bitmap = arabic_font_data.BITMAP_DATA
    if not isinstance(bitmap, (bytearray, bytes)):
        raise SystemExit("BITMAP_DATA must be bytes/bytearray")
    bitmap_len = len(bitmap)

    missing = 0
    bad = 0
    for cp, forms in (glyphs or {}).items():
        if not isinstance(forms, dict):
            bad += 1
            continue
        for form_name, entry in forms.items():
            if not isinstance(entry, dict):
                bad += 1
                continue
            w = int(entry.get("w") or 0)
            h = int(entry.get("h") or 0)
            offset = int(entry.get("buf_offset") or 0)
            n = int(entry.get("buf_len") or 0)
            expected = mono_vlsb_buf_len(w, h)
            if w <= 0 or h <= 0:
                missing += 1
                continue
            if n != expected:
                print("bad buf_len for", hex(int(cp)), form_name, "expected", expected, "got", n)
                bad += 1
            if offset < 0 or offset + n > bitmap_len:
                print("out of range for", hex(int(cp)), form_name, "offset", offset, "len", n, "bitmap", bitmap_len)
                bad += 1

    if missing:
        print("WARNING: missing/empty glyphs:", missing)
    if bad:
        print("FAILED: problems:", bad)
        return 2
    print("OK:", len(glyphs or {}), "base glyphs;", bitmap_len, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
