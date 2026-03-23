from lib.app import words as words_mod
from lib.ui import arabic_render

# Map transliteration diacritics to ASCII the SSD1306 font can render.
OLED_CHAR_MAP = {
    "ā": "a",
    "ī": "i",
    "ū": "u",
    "ʾ": "'",
    "ʿ": "'",
    "ḍ": "d",
    "ḥ": "h",
    "ṭ": "t",
    "Ā": "A",
    "Ī": "I",
    "Ū": "U",
    "Ḍ": "D",
    "Ḥ": "H",
    "Ṭ": "T",
}

def text_width(text: str) -> int:
    return len(text) * 8


def oled_safe_text(text: str) -> str:
    if not text:
        return ""
    parts = []
    for ch in text:
        if ch in OLED_CHAR_MAP:
            parts.append(OLED_CHAR_MAP[ch])
        elif ord(ch) < 128:
            parts.append(ch)
        else:
            parts.append("?")
    return "".join(parts)


def oled_text(oled, text: str, x: int, y: int, color: int = 1) -> None:
    oled.text(oled_safe_text(text), x, y, color)


def clamp_text_to_width(text: str, max_width: int) -> str:
    """
    Trim text to fit within a pixel width, using "..." when truncating.
    """
    safe = oled_safe_text(text)
    if max_width <= 0:
        return ""
    if text_width(safe) <= max_width:
        return safe
    max_chars = max_width // 8
    if max_chars <= 0:
        return ""
    if max_chars <= 3:
        return safe[:max_chars]
    return safe[: max_chars - 3] + "..."


def center_text(oled, text: str, y: int) -> None:
    safe = oled_safe_text(text)
    x = max(0, (oled.width - text_width(safe)) // 2)
    oled.text(safe, x, y)


def wrap_oled_text(text: str, max_chars: int) -> list:
    """
    Word-wrap for the tiny 128px display. Uses hyphenation when a word
    doesn't fit the remaining space on the current line.
    """
    safe = oled_safe_text(text)
    if not safe:
        return [""]
    words = safe.split(" ")
    lines = []
    line = ""
    for word in words:
        if not line:
            while len(word) > max_chars:
                lines.append(word[: max_chars - 1] + "-")
                word = word[max_chars - 1 :]
            line = word
            continue

        # normal fit
        if len(line) + 1 + len(word) <= max_chars:
            line = line + " " + word
            continue

        # try hyphenating onto current line
        remaining = max_chars - len(line) - 1  # space before the next word
        if remaining > 1:
            take = remaining - 1  # leave room for hyphen
            lines.append(line + " " + word[:take] + "-")
            word = word[take:]
        else:
            lines.append(line)

        while len(word) > max_chars:
            lines.append(word[: max_chars - 1] + "-")
            word = word[max_chars - 1 :]
        line = word

    if line:
        lines.append(line)
    return lines


def draw_wrapped_center(oled, text: str, start_y: int, *, line_height: int = 10) -> int:
    max_chars = max(1, oled.width // 8)
    y = start_y
    for line in wrap_oled_text(text, max_chars):
        center_text(oled, line, y)
        y += line_height
    return y


def draw_hints(oled):
    hint_y1 = oled.height - 16
    hint_y2 = oled.height - 8
    oled_text(oled, "B1 Use B2 Forms", 0, hint_y1)
    center_text(oled, "B3 Root", hint_y2)


def draw_base_view(oled, word):
    center_text(oled, word["translit"], 4)
    base_ar = words_mod.get_word_arabic_text(word, "base") or ""
    if not arabic_render.center(oled, base_ar, 22, rtl=True):
        center_text(oled, word["translit"], 22)
    draw_hints(oled)


def draw_root_view(oled, word):
    center_text(oled, "ROOT", 0)
    center_text(oled, word["root_translit"], 12)
    root_ar = words_mod.get_word_arabic_text(word, "root") or ""
    if not arabic_render.center_root(oled, root_ar, 24):
        center_text(oled, word["root_translit"], 24)
    center_text(oled, word["root_meaning"], 46)


def draw_forms_view(oled, state, word):
    forms = word.get("forms") or []
    if not forms:
        center_text(oled, "FORMS", 0)
        center_text(oled, "No forms", 20)
        return

    idx = min(state.get("form_idx", 0), len(forms) - 1)
    state["form_idx"] = idx  # clamp in state
    form = words_mod.get_form_entry(word, idx)

    header = "FORMS"
    if len(forms) > 1:
        header = f"FORMS {idx + 1}/{len(forms)}"
    center_text(oled, header, 0)

    y = 16
    line_gap = 12

    translit = form["translit"]
    english = form.get("english", "")
    form_ar = words_mod.get_word_arabic_text(word, "form", idx) or ""
    fallback = english or translit

    translit_text = clamp_text_to_width(translit, oled.width - 4)
    center_text(oled, translit_text, y)

    y += line_gap
    english_text = clamp_text_to_width(english, oled.width - 4)
    if english_text:
        center_text(oled, english_text, y)

    y += line_gap
    if not arabic_render.center(oled, form_ar, y, rtl=True):
        center_text(oled, fallback, y)


def draw_use_view(oled, word):
    center_text(oled, "USE", 0)
    next_y = draw_wrapped_center(oled, word["sentence_translit"], 12)
    draw_wrapped_center(oled, word["sentence_en"], next_y + 2)


def draw_overlay(oled, state, words):
    word = words_mod.get_word(state, words)
    view = state.get("view", "base")
    if view == "root":
        draw_root_view(oled, word)
    elif view == "forms":
        draw_forms_view(oled, state, word)
    elif view == "use":
        draw_use_view(oled, word)
    else:
        draw_base_view(oled, word)
