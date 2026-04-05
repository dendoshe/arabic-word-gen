#!/usr/bin/env python3
"""
Launch an interactive desktop simulator for the dual OLED UI.
"""

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from lib.app import config, words as words_mod
from lib.desktop.simulator import DEFAULT_SCALE, run_simulator


ALL_VIEWS = ("base", "root", "forms", "use")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Open an interactive OLED simulator without Raspberry Pi hardware."
    )
    parser.add_argument(
        "--word",
        default=None,
        help="Word key from words.json. Defaults to the configured initial word.",
    )
    parser.add_argument(
        "--view",
        choices=ALL_VIEWS,
        default="base",
        help="Initial primary-screen view.",
    )
    parser.add_argument(
        "--form-index",
        type=int,
        default=0,
        help="Initial form index when starting in the forms view.",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=DEFAULT_SCALE,
        help="Pixel scale factor for each OLED window.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=config.FPS,
        help="Refresh rate for the simulator window.",
    )
    return parser.parse_args()


def build_state(word_key, view, *, form_idx=0):
    return {
        "view": view,
        "word_key": word_key,
        "last_pressed": {1: False, 2: False, 3: False},
        "form_idx": max(0, int(form_idx)),
        "now_ms": 0,
        "changed_at": 0,
    }


def main():
    args = parse_args()
    words = words_mod.load_words(config.WORD_PATHS)
    word_key = args.word or words_mod.initial_word_key(words)

    if word_key not in words:
        available = ", ".join(sorted(words.keys()))
        raise SystemExit("Unknown word key '%s'. Available: %s" % (word_key, available))

    initial_state = build_state(
        word_key,
        args.view,
        form_idx=args.form_index,
    )
    ok = run_simulator(
        words,
        initial_state=initial_state,
        fps=args.fps,
        scale=args.scale,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
