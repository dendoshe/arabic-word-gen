try:
    import ujson as json
except ImportError:  # desktop testing fallback
    import json

from lib.app import config
from lib.app.words_validation import validate_words_data

# Fallback data if words.json is missing or invalid
DEFAULT_WORDS = {
    "kitab": {
        "translit": "kitāb",
        "arabic": "كتاب",
        "root_translit": "k-t-b",
        "root_meaning": "write / book",
        "root_arabic": "كتب",
        "forms": [
            {
                "translit": "kitāb",
                "english": "book",
                "arabic": "كتاب",
            },
            {
                "translit": "kutub",
                "english": "books",
                "arabic": "كتب",
            },
            {
                "translit": "al-kitāb",
                "english": "the book",
                "arabic": "الكتاب",
            },
        ],
        "sentence_translit": "hadha kitāb",
        "sentence_en": "This is a book",
    },
}


def load_words(paths=None, *, glyphs=None):
    """
    Load words.json from the first existing path, validating shape (and optionally glyph coverage).
    """
    paths = paths or config.WORD_PATHS
    for path in paths:
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except Exception as exc:
            print("failed to load words file at", path, ":", exc)
            continue
        ok, errors, warnings = validate_words_data(data, glyphs=glyphs)
        if not ok:
            print("words file invalid at", path)
            for err in errors:
                print(" -", err)
            continue
        for warn in warnings:
            print("words file warning at %s: %s" % (path, warn))
        return data
    print("words file not found/invalid; using defaults")
    return DEFAULT_WORDS


def initial_word_key(words):
    if config.DEFAULT_WORD_KEY in words:
        return config.DEFAULT_WORD_KEY
    if words:
        return next(iter(words.keys()))
    return config.DEFAULT_WORD_KEY


def get_word(state, words):
    key = state.get("word_key", config.DEFAULT_WORD_KEY)
    if key not in words:
        key = next(iter(words.keys())) if words else config.DEFAULT_WORD_KEY
        state["word_key"] = key
    return words.get(key, DEFAULT_WORDS[config.DEFAULT_WORD_KEY])


def get_form_entry(word: dict, idx: int):
    forms = word.get("forms") or []
    if not forms or idx < 0:
        return None
    if idx >= len(forms):
        return forms[-1]
    return forms[idx]


ARABIC_TEXT_FIELDS = {"base": "arabic", "root": "root_arabic"}


def get_word_arabic_text(word: dict, variant: str, form_idx: int = 0):
    """
    Centralized Arabic text lookup for the glyph-font renderer.
    """
    if variant == "form":
        forms = word.get("forms") or []
        if 0 <= form_idx < len(forms):
            return forms[form_idx].get("arabic")
        return None
    field = ARABIC_TEXT_FIELDS.get(variant)
    return word.get(field) if field else None
