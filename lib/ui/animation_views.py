from lib.ui import views

DEFAULT_ANIMATION_STYLE = "pulse"

WORD_ANIMATION_SCENES = {
    "maa": "water",
    "bayt": "house",
    "salam": "peace",
    "shams": "sun",
    "qamar": "moon",
    "rajul": "man",
    "imraah": "woman",
    "walad": "boy",
    "kalb": "dog",
    "bint": "girl",
}

SCENE_ALIASES = {
    "pulse": "pulse",
    "water": "water",
    "sun": "sun",
    "moon": "moon",
    "house": "house",
    "peace": "peace",
    "walker": "man",
    "man": "man",
    "woman": "woman",
    "boy": "boy",
    "girl": "girl",
    "dog": "dog",
}

MEANING_SCENE_HINTS = (
    ("water", "water"),
    ("sun", "sun"),
    ("moon", "moon"),
    ("house", "house"),
    ("dog", "dog"),
    ("peace", "peace"),
    ("man", "man"),
    ("woman", "woman"),
    ("girl", "girl"),
    ("boy", "boy"),
    ("child", "boy"),
)

ANIMATION_SCENES = {
    "pulse": (
        ("pulse_rects", 64, 38, 24, 12, 10, 5, 130, 16, 3),
        ("text_center", "sentence_en", 54),
    ),
    "water": (
        ("water_rows", 20, 4, 9, 18, 90),
        ("bubble_field", 20, 4, 9),
    ),
    "sun": (
        ("sun", 64, 36, 9, 5, 140, 6),
    ),
    "moon": (
        ("moon", 64, 36, 13, 5, 220, 5),
        ("stars", ((22, 20), (90, 18), (102, 30), (26, 46)), 180),
    ),
    "house": (
        ("house", 34, 24, 60, 28, 220, 4),
    ),
    "peace": (
        ("peace_symbol", 64, 34, 12),
        ("ring", 64, 34, 16, 1, 140, 7),
        ("branch", 42, 50, 1),
        ("branch", 86, 50, -1),
    ),
    "man": (
        ("person_walk", 20, 78, 90, 120, 20, 13, 53),
        ("ground", 10, 55, 108),
    ),
    "woman": (
        ("person_sway", 64, 20, 180, 11, 53, 1),
        ("ground", 18, 55, 92),
    ),
    "boy": (
        ("person_bounce", 42, 24, (0, 2, 5, 2, 0, 1), 100, 9, 54),
        ("ball_bounce", 82, 43, (0, 3, 7, 3, 0, 2), 100, 3),
        ("ground", 10, 56, 108),
    ),
    "girl": (
        ("person_pose", 38, 22, 10, 5, 4, 53, 1, 31, 0, 0),
        ("open_book", 74, 28, (7, 8, 9, 10), 160),
        ("reading_lines", ((43, 33, 64, 34), (43, 35, 66, 40))),
        ("ground", 16, 55, 96),
    ),
    "dog": (
        ("dog", 44, 34, 130, 4),
        ("ground", 20, 56, 88),
    ),
}


def draw_secondary_animation(oled, state, word):
    now_ms = int(state.get("now_ms", 0))
    word_key = state.get("word_key", "")
    scene_key = resolve_animation_scene(word_key, word)
    label = word.get("translit") or word_key or ""

    oled.clear()
    draw_animation_header(oled, label)
    draw_scene(oled, scene_key, now_ms, word)


def draw_animation_header(oled, label):
    views.center_text(oled, views.clamp_text_to_width(label, oled.width - 4), 0)
    oled.hline(0, 10, oled.width, 1)


def resolve_animation_scene(word_key, word):
    animation = word.get("animation")
    if isinstance(animation, dict):
        style = animation.get("scene") or animation.get("style")
        if isinstance(style, str) and style:
            return normalize_scene_key(style)
    elif isinstance(animation, str) and animation:
        return normalize_scene_key(animation)

    if word_key in WORD_ANIMATION_SCENES:
        return WORD_ANIMATION_SCENES[word_key]

    search_text = " ".join(
        (
            word.get("root_meaning", ""),
            word.get("sentence_en", ""),
            ((word.get("forms") or [{}])[0]).get("english", ""),
        )
    ).lower()
    for needle, scene_key in MEANING_SCENE_HINTS:
        if needle in search_text:
            return scene_key
    return DEFAULT_ANIMATION_STYLE


def normalize_scene_key(style):
    return SCENE_ALIASES.get(style, style)


def draw_scene(oled, scene_key, now_ms, word):
    scene = ANIMATION_SCENES.get(scene_key)
    if scene is None:
        scene = ANIMATION_SCENES[DEFAULT_ANIMATION_STYLE]
    for element in scene:
        draw_scene_element(oled, element, now_ms, word)


def draw_scene_element(oled, element, now_ms, word):
    kind = element[0]

    if kind == "pulse_rects":
        draw_pulse_rects(oled, now_ms, element)
    elif kind == "text_center":
        draw_text_center(oled, word, element)
    elif kind == "water_rows":
        draw_water_rows(oled, now_ms, element)
    elif kind == "bubble_field":
        draw_bubble_field(oled, now_ms, element)
    elif kind == "sun":
        draw_sun_element(oled, now_ms, element)
    elif kind == "moon":
        draw_moon_element(oled, now_ms, element)
    elif kind == "stars":
        draw_stars_element(oled, now_ms, element)
    elif kind == "house":
        draw_house_element(oled, now_ms, element)
    elif kind == "peace_symbol":
        draw_peace_symbol(oled, element)
    elif kind == "ring":
        draw_ring_element(oled, now_ms, element)
    elif kind == "branch":
        draw_branch_element(oled, element)
    elif kind == "person_walk":
        draw_person_walk_element(oled, now_ms, element)
    elif kind == "person_sway":
        draw_person_sway_element(oled, now_ms, element)
    elif kind == "person_bounce":
        draw_person_bounce_element(oled, now_ms, element)
    elif kind == "ball_bounce":
        draw_ball_bounce_element(oled, now_ms, element)
    elif kind == "person_pose":
        draw_person_pose_element(oled, element)
    elif kind == "open_book":
        draw_open_book_element(oled, now_ms, element)
    elif kind == "reading_lines":
        draw_reading_lines_element(oled, element)
    elif kind == "dog":
        draw_dog_element(oled, now_ms, element)
    elif kind == "ground":
        draw_ground_element(oled, element)


def cycle_index(now_ms, tick_ms, length):
    if length <= 0:
        return 0
    return (now_ms // max(1, tick_ms)) % length


def cycle_value(now_ms, tick_ms, values):
    return values[cycle_index(now_ms, tick_ms, len(values))]


def fill_circle(oled, cx, cy, radius, color=1):
    x = 0
    y = radius
    err = 1 - radius

    while x <= y:
        oled.hline(cx - x, cy + y, 2 * x + 1, color)
        oled.hline(cx - x, cy - y, 2 * x + 1, color)
        oled.hline(cx - y, cy + x, 2 * y + 1, color)
        oled.hline(cx - y, cy - x, 2 * y + 1, color)
        x += 1
        if err < 0:
            err += 2 * x + 1
        else:
            y -= 1
            err += 2 * (x - y) + 1


def draw_circle(oled, cx, cy, radius, color=1):
    x = radius
    y = 0
    err = 1 - radius

    while x >= y:
        oled.pixel(cx + x, cy + y, color)
        oled.pixel(cx + y, cy + x, color)
        oled.pixel(cx - y, cy + x, color)
        oled.pixel(cx - x, cy + y, color)
        oled.pixel(cx - x, cy - y, color)
        oled.pixel(cx - y, cy - x, color)
        oled.pixel(cx + y, cy - x, color)
        oled.pixel(cx + x, cy - y, color)
        y += 1
        if err < 0:
            err += 2 * y + 1
        else:
            x -= 1
            err += 2 * (y - x) + 1


def draw_branch(oled, start_x, start_y, direction=1):
    oled.line(start_x, start_y, start_x + direction * 10, start_y - 10, 1)
    oled.line(start_x + direction * 3, start_y - 4, start_x + direction * 7, start_y - 8, 1)
    oled.line(start_x + direction * 3, start_y - 4, start_x + direction * 7, start_y - 2, 1)
    oled.line(start_x + direction * 7, start_y - 8, start_x + direction * 11, start_y - 12, 1)
    oled.line(start_x + direction * 7, start_y - 8, start_x + direction * 11, start_y - 6, 1)


def draw_open_book(oled, x, y, spread=8):
    oled.line(x, y, x - spread, y + 4, 1)
    oled.line(x, y, x - spread, y + 12, 1)
    oled.line(x, y, x + spread, y + 4, 1)
    oled.line(x, y, x + spread, y + 12, 1)
    oled.line(x - spread, y + 4, x - spread, y + 12, 1)
    oled.line(x + spread, y + 4, x + spread, y + 12, 1)
    oled.line(x, y, x, y + 12, 1)


def draw_window(oled, x, y, lit=False):
    oled.rect(x, y, 10, 10, 1)
    if lit:
        oled.fill_rect(x + 2, y + 2, 6, 6, 1)
    else:
        oled.line(x + 4, y + 1, x + 4, y + 8, 1)
        oled.line(x + 1, y + 4, x + 8, y + 4, 1)


def draw_ground(oled, x, y, width):
    oled.hline(x, y, width, 1)


def draw_stick_person(
    oled,
    x,
    head_y,
    *,
    body_len=12,
    arm_left_dx=5,
    arm_right_dx=5,
    leg_left_dx=5,
    leg_right_dx=5,
    body_dx=0,
    ground_y=52,
    dress=False,
    arm_y=None,
    hair=False,
):
    fill_circle(oled, x, head_y, 4, 1)
    shoulder_y = head_y + 9
    hip_y = shoulder_y + body_len
    hip_x = x + body_dx
    arm_y = arm_y if arm_y is not None else shoulder_y + 3

    if hair:
        oled.line(x - 7, head_y + 2, x - 3, head_y - 2, 1)
        oled.line(x + 7, head_y + 2, x + 3, head_y - 2, 1)

    oled.line(x, shoulder_y, hip_x, hip_y, 1)
    oled.line(x, arm_y, x - arm_left_dx, arm_y + 5, 1)
    oled.line(x, arm_y, x + arm_right_dx, arm_y + 5, 1)

    if dress:
        skirt_y = hip_y + 4
        oled.line(hip_x, hip_y, hip_x - 6, skirt_y, 1)
        oled.line(hip_x, hip_y, hip_x + 6, skirt_y, 1)
        oled.line(hip_x - 6, skirt_y, hip_x + 6, skirt_y, 1)
        oled.line(hip_x - 3, skirt_y, hip_x - leg_left_dx, ground_y, 1)
        oled.line(hip_x + 3, skirt_y, hip_x + leg_right_dx, ground_y, 1)
        return

    oled.line(hip_x, hip_y, hip_x - leg_left_dx, ground_y, 1)
    oled.line(hip_x, hip_y, hip_x + leg_right_dx, ground_y, 1)


def draw_pulse_rects(oled, now_ms, element):
    _, cx, cy, base_w, base_h, inset_w, inset_h, tick_ms, phase_count, rect_count = element
    phase = cycle_index(now_ms, tick_ms, phase_count)

    for idx in range(rect_count):
        width = max(8, base_w + phase * 2 - idx * inset_w)
        height = max(6, base_h + phase - idx * inset_h)
        x = cx - width // 2
        y = cy - height // 2
        oled.rect(x, y, width, height, 1)


def draw_text_center(oled, word, element):
    _, field, y = element
    text = word.get(field, "")
    views.center_text(oled, views.clamp_text_to_width(text, oled.width - 4), y)


def draw_water_rows(oled, now_ms, element):
    _, start_y, rows, row_gap, wave_period, tick_ms = element
    shift = cycle_index(now_ms, tick_ms, wave_period)

    for row in range(rows):
        y = start_y + row * row_gap
        row_shift = (shift + row * 4) % wave_period
        for start in range(-wave_period, oled.width + wave_period, wave_period):
            x = start - row_shift
            oled.hline(x, y, 8, 1)
            oled.hline(x + 8, y + 1, 8, 1)
            oled.hline(x + 2, y + 3, 8, 1)


def draw_bubble_field(oled, now_ms, element):
    _, start_y, rows, row_gap = element
    for row in range(rows):
        y = start_y + row * row_gap
        bubble_x = (now_ms // (70 + row * 20) + row * 17) % oled.width
        bubble_y = y - ((now_ms // (90 + row * 10)) % 6)
        oled.rect(bubble_x, bubble_y, 3, 3, 1)


def draw_sun_element(oled, now_ms, element):
    _, cx, cy, radius, ray, tick_ms, phase_count = element
    phase = cycle_index(now_ms, tick_ms, phase_count)
    sun_radius = radius + (phase % 2)
    ray_len = ray + phase

    fill_circle(oled, cx, cy, sun_radius, 1)
    oled.line(cx - sun_radius - 2, cy, cx - sun_radius - 2 - ray_len, cy, 1)
    oled.line(cx + sun_radius + 2, cy, cx + sun_radius + 2 + ray_len, cy, 1)
    oled.line(cx, cy - sun_radius - 2, cx, cy - sun_radius - 2 - ray_len, 1)
    oled.line(cx, cy + sun_radius + 2, cx, cy + sun_radius + 2 + ray_len, 1)
    oled.line(cx - sun_radius, cy - sun_radius, cx - sun_radius - ray_len, cy - sun_radius - ray_len, 1)
    oled.line(cx + sun_radius, cy - sun_radius, cx + sun_radius + ray_len, cy - sun_radius - ray_len, 1)
    oled.line(cx - sun_radius, cy + sun_radius, cx - sun_radius - ray_len, cy + sun_radius + ray_len, 1)
    oled.line(cx + sun_radius, cy + sun_radius, cx + sun_radius + ray_len, cy + sun_radius + ray_len, 1)


def draw_moon_element(oled, now_ms, element):
    _, cx, cy, radius, cutout_x, tick_ms, drift_steps = element
    drift = cycle_index(now_ms, tick_ms, drift_steps) - (drift_steps // 2)

    fill_circle(oled, cx, cy, radius, 1)
    fill_circle(oled, cx + cutout_x + drift, cy - 1, max(1, radius - 2), 0)


def draw_stars_element(oled, now_ms, element):
    _, points, tick_ms = element
    twinkle = cycle_index(now_ms, tick_ms, len(points))
    for idx, point in enumerate(points):
        x, y = point
        if idx == twinkle:
            oled.line(x - 2, y, x + 2, y, 1)
            oled.line(x, y - 2, x, y + 2, 1)
        else:
            oled.pixel(x, y, 1)


def draw_house_element(oled, now_ms, element):
    _, left, top, width, height, tick_ms, phase_count = element
    phase = cycle_index(now_ms, tick_ms, phase_count)
    lit_left = (phase % 2) == 0

    oled.rect(left, top, width, height, 1)
    oled.line(left, top, left + width // 2, top - 14, 1)
    oled.line(left + width, top, left + width // 2, top - 14, 1)
    oled.rect(left + 24, top + 12, 12, 16, 1)
    draw_window(oled, left + 8, top + 8, lit=lit_left)
    draw_window(oled, left + 44, top + 8, lit=not lit_left)


def draw_peace_symbol(oled, element):
    _, cx, cy, radius = element
    draw_circle(oled, cx, cy, radius, 1)
    oled.line(cx, cy - 9, cx, cy + 9, 1)
    oled.line(cx, cy, cx - 7, cy + 8, 1)
    oled.line(cx, cy, cx + 7, cy + 8, 1)


def draw_ring_element(oled, now_ms, element):
    _, cx, cy, base_radius, step, tick_ms, phase_count = element
    radius = base_radius + cycle_index(now_ms, tick_ms, phase_count) * step
    draw_circle(oled, cx, cy, radius, 1)


def draw_branch_element(oled, element):
    _, start_x, start_y, direction = element
    draw_branch(oled, start_x, start_y, direction)


def draw_person_walk_element(oled, now_ms, element):
    _, base_x, travel, move_tick_ms, gait_tick_ms, head_y, body_len, ground_y = element
    x = base_x + ((now_ms // move_tick_ms) % travel)
    gait_phase = cycle_index(now_ms, gait_tick_ms, 4)

    if gait_phase in (0, 2):
        arm_left_dx, arm_right_dx = 6, 2
        leg_left_dx, leg_right_dx = 2, 6
    else:
        arm_left_dx, arm_right_dx = 2, 6
        leg_left_dx, leg_right_dx = 6, 2

    draw_stick_person(
        oled,
        x,
        head_y + (1 if gait_phase in (1, 3) else 0),
        body_len=body_len,
        arm_left_dx=arm_left_dx,
        arm_right_dx=arm_right_dx,
        leg_left_dx=leg_left_dx,
        leg_right_dx=leg_right_dx,
        ground_y=ground_y,
    )


def draw_person_sway_element(oled, now_ms, element):
    _, base_x, head_y, sway_tick_ms, body_len, ground_y, hair = element
    sway = cycle_index(now_ms, sway_tick_ms, 5) - 2

    draw_stick_person(
        oled,
        base_x + sway,
        head_y,
        body_len=body_len,
        arm_left_dx=4 + max(0, sway),
        arm_right_dx=4 + max(0, -sway),
        leg_left_dx=4,
        leg_right_dx=4,
        body_dx=sway // 2,
        ground_y=ground_y,
        dress=True,
        arm_y=head_y + 11,
        hair=bool(hair),
    )


def draw_person_bounce_element(oled, now_ms, element):
    _, x, head_y, jump_steps, tick_ms, body_len, ground_y = element
    jump = cycle_value(now_ms, tick_ms, jump_steps)
    phase = cycle_index(now_ms, tick_ms, len(jump_steps))

    draw_stick_person(
        oled,
        x,
        head_y - jump,
        body_len=body_len,
        arm_left_dx=6,
        arm_right_dx=5,
        leg_left_dx=5 + (phase % 2),
        leg_right_dx=5 + ((phase + 1) % 2),
        ground_y=ground_y - jump,
        arm_y=head_y + 9 - jump,
    )


def draw_ball_bounce_element(oled, now_ms, element):
    _, x, y, offsets, tick_ms, radius = element
    fill_circle(oled, x, y - cycle_value(now_ms, tick_ms, offsets), radius, 1)


def draw_person_pose_element(oled, element):
    _, x, head_y, body_len, arm_dx, leg_dx, ground_y, dress, arm_y, body_dx, hair = element
    draw_stick_person(
        oled,
        x,
        head_y,
        body_len=body_len,
        arm_left_dx=arm_dx,
        arm_right_dx=arm_dx,
        leg_left_dx=leg_dx,
        leg_right_dx=leg_dx,
        body_dx=body_dx,
        ground_y=ground_y,
        dress=bool(dress),
        arm_y=arm_y,
        hair=bool(hair),
    )


def draw_open_book_element(oled, now_ms, element):
    _, x, y, spreads, tick_ms = element
    draw_open_book(oled, x, y, spread=cycle_value(now_ms, tick_ms, spreads))


def draw_reading_lines_element(oled, element):
    _, lines = element
    for line in lines:
        oled.line(line[0], line[1], line[2], line[3], 1)


def draw_dog_element(oled, now_ms, element):
    _, x, y, tick_ms, phase_count = element
    phase = cycle_index(now_ms, tick_ms, phase_count)
    tail_y = y + (phase - 1)

    oled.fill_rect(x, y, 28, 12, 1)
    oled.fill_rect(x + 24, y - 6, 10, 10, 1)
    oled.fill_rect(x + 4, y + 12, 3, 8, 1)
    oled.fill_rect(x + 18, y + 12, 3, 8, 1)
    oled.line(x - 8, tail_y, x, y + 3, 1)
    oled.pixel(x + 30, y - 3, 0)
    oled.pixel(x + 30, y - 1, 0)
    oled.pixel(x + 31, y - 3, 0)


def draw_ground_element(oled, element):
    _, x, y, width = element
    draw_ground(oled, x, y, width)
