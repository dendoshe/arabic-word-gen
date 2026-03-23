"""
View navigation and button handling.
"""

VIEWS = ("base", "root", "forms", "use")

VIEW_TRANSITIONS = {
    "base": {1: "root", 2: "forms", 3: "use"},
    "root": {1: "base", 2: "forms", 3: "use"},
    "forms": {1: "root", 2: "base", 3: "use"},
    "use": {1: "root", 2: "forms", 3: "base"},
}


def advance_forms(state, word):
    """
    Move to the next form, or return to home after the last form.
    """
    forms = word.get("forms") or []
    if not forms:
        state["view"] = "base"
        state["form_idx"] = 0
        return

    next_idx = state.get("form_idx", 0) + 1
    if next_idx >= len(forms):
        state["form_idx"] = 0
        state["view"] = "base"
    else:
        state["form_idx"] = next_idx


def handle_buttons(state, now_ms, buttons, word_lookup, view_transitions=VIEW_TRANSITIONS):
    """
    Consume debounced button press events and move between card views.
    buttons: dict {1: Button, 2: Button, 3: Button}
    word_lookup: callable(state) -> current word dict (for forms advance)
    """
    pressed = {
        1: buttons[1].consume_press(now_ms),
        2: buttons[2].consume_press(now_ms),
        3: buttons[3].consume_press(now_ms),
    }
    current_view = state["view"]

    for idx in (1, 2, 3):
        if pressed[idx]:
            if current_view == "forms" and idx == 2:
                advance_forms(state, word_lookup(state))
                state["changed_at"] = now_ms
            else:
                next_view = view_transitions.get(current_view, {}).get(idx, current_view)
                if next_view != current_view:
                    if next_view == "forms":
                        state["form_idx"] = 0
                    elif current_view == "forms":
                        state["form_idx"] = 0
                    state["view"] = next_view
                state["changed_at"] = now_ms
            break
