#!/usr/bin/env python3
"""
Offline validator for words.json.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib.app.words_validation import validate_words_data


def main():
    parser = argparse.ArgumentParser(description="Validate words.json against schema (and optionally glyph coverage).")
    parser.add_argument("path", nargs="?", default=None, help="Path to words.json")
    parser.add_argument(
        "--check-glyphs",
        action="store_true",
        help="Validate that Arabic strings only use glyphs present in lib/ui/arabic_font_data.py.",
    )
    args = parser.parse_args()

    path = args.path
    if path is None:
        for candidate in ("words.json",):
            if Path(candidate).exists():
                path = candidate
                break
        else:
            path = "words.json"

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception as exc:
        print("Failed to read %s: %s" % (path, exc))
        return 1

    glyphs = None
    if args.check_glyphs:
        from lib.ui import font_registry

        glyphs = font_registry.glyphs()

    ok, errors, warnings = validate_words_data(data, glyphs=glyphs)

    for warn in warnings:
        print("WARN:", warn)

    if not ok:
        print("ERROR: %d validation error(s)" % len(errors))
        for err in errors:
            print(" -", err)
        return 1

    print("OK: %s is valid (%d warning(s))" % (path, len(warnings)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
