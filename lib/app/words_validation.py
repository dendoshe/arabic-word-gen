"""
Minimal schema validation for words.json entries.
Keep this lightweight for MicroPython and re-use in desktop linting.
"""

REQUIRED_WORD_FIELDS = {
    "translit": str,
    "root_translit": str,
    "root_meaning": str,
    "arabic": str,
    "root_arabic": str,
    "forms": list,
    "sentence_translit": str,
    "sentence_en": str,
}

OPTIONAL_WORD_FIELDS = {
    "animation": (str, dict),
}

REQUIRED_FORM_FIELDS = {
    "translit": str,
    "english": str,
    "arabic": str,
}

ALLOWED_WORD_FIELDS = set(REQUIRED_WORD_FIELDS.keys()) | set(OPTIONAL_WORD_FIELDS.keys())
ALLOWED_FORM_FIELDS = set(REQUIRED_FORM_FIELDS.keys())


def _is_type(value, typ):
    return isinstance(value, typ)


def _iter_arabic_codepoints(text: str):
    # Basic Arabic + Arabic Supplement + Arabic Extended-A.
    for ch in text or "":
        cp = ord(ch)
        if (0x0600 <= cp <= 0x06FF) or (0x0750 <= cp <= 0x077F) or (0x08A0 <= cp <= 0x08FF):
            yield cp


def validate_words_data(data, *, glyphs=None):
    """
    Validate the loaded words mapping.
    Returns (ok: bool, errors: list[str], warnings: list[str]).
    glyphs: optional set/dict of available base codepoints to assert font coverage.
    """
    errors = []
    warnings = []
    glyph_set = None
    if glyphs is not None:
        glyph_set = glyphs if isinstance(glyphs, dict) else set(glyphs)

    if not isinstance(data, dict) or not data:
        errors.append("root: expected non-empty dict of words")
        return False, errors, warnings

    for word_key, entry in data.items():
        if not isinstance(word_key, str):
            errors.append("word key %r: expected string" % (word_key,))
            continue
        if not isinstance(entry, dict):
            errors.append("word '%s': expected dict entry" % word_key)
            continue

        for field, typ in REQUIRED_WORD_FIELDS.items():
            if field not in entry:
                errors.append("word '%s': missing '%s'" % (word_key, field))
                continue
            if not _is_type(entry[field], typ):
                errors.append(
                    "word '%s': field '%s' should be %s"
                    % (word_key, field, typ.__name__)
                )

        for field, typ in OPTIONAL_WORD_FIELDS.items():
            if field in entry and not _is_type(entry[field], typ):
                expected = "/".join(t.__name__ for t in typ) if isinstance(typ, tuple) else typ.__name__
                errors.append(
                    "word '%s': field '%s' should be %s"
                    % (word_key, field, expected)
                )

        if glyph_set is not None:
            for label, text in (("arabic", entry.get("arabic")), ("root_arabic", entry.get("root_arabic"))):
                for cp in _iter_arabic_codepoints(text or ""):
                    if cp not in glyph_set:
                        errors.append(
                            "word '%s': %s uses missing glyph U+%04X" % (word_key, label, cp)
                        )

        extra_word_keys = set(entry.keys()) - ALLOWED_WORD_FIELDS
        for extra in sorted(extra_word_keys):
            warnings.append("word '%s': unknown field '%s'" % (word_key, extra))

        forms = entry.get("forms")
        if not isinstance(forms, list):
            errors.append("word '%s': 'forms' should be a list" % word_key)
            continue

        for idx, form in enumerate(forms):
            if not isinstance(form, dict):
                errors.append("word '%s' form %d: expected dict" % (word_key, idx))
                continue
            for field, typ in REQUIRED_FORM_FIELDS.items():
                if field not in form:
                    errors.append(
                        "word '%s' form %d: missing '%s'" % (word_key, idx, field)
                    )
                    continue
                if not _is_type(form[field], typ):
                    errors.append(
                        "word '%s' form %d: field '%s' should be %s"
                        % (word_key, idx, field, typ.__name__)
                    )

            if glyph_set is not None:
                for cp in _iter_arabic_codepoints(form.get("arabic") or ""):
                    if cp not in glyph_set:
                        errors.append(
                            "word '%s' form %d: arabic uses missing glyph U+%04X" % (word_key, idx, cp)
                        )

            extra_form_keys = set(form.keys()) - ALLOWED_FORM_FIELDS
            for extra in sorted(extra_form_keys):
                warnings.append(
                    "word '%s' form %d: unknown field '%s'" % (word_key, idx, extra)
                )

    return len(errors) == 0, errors, warnings
