from lib.ui import animation_config, views


def draw_secondary_animation(oled, state, word):
    now_ms = int(state.get("now_ms", 0))
    word_key = state.get("word_key", "")
    scene_key = animation_config.resolve_animation_scene(word_key, word)
    label = word.get("translit") or word_key or ""

    oled.clear()
    draw_animation_header(oled, label)
    draw_scene(oled, scene_key, now_ms, word)


def draw_animation_header(oled, label):
    views.center_text(oled, views.clamp_text_to_width(label, oled.width - 4), 0)
    oled.hline(0, 10, oled.width, 1)


def draw_scene(oled, scene_key, now_ms, word):
    scene = animation_config.get_scene_definition(scene_key)
    for element in scene.get("elements", ()):
        draw_scene_element(oled, element, now_ms, word)


def draw_scene_element(oled, element, now_ms, word):
    kind = element.get("kind") if isinstance(element, dict) else None
    drawer = ELEMENT_DRAWERS.get(kind)
    if drawer:
        drawer(oled, now_ms, element, word)


def cycle_index(now_ms, tick_ms, length):
    if length <= 0:
        return 0
    return (now_ms // max(1, tick_ms)) % length


def cycle_value(now_ms, tick_ms, values):
    if not values:
        return 0
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


def draw_pulse_rects(oled, now_ms, element, word):
    cx = element.get("x", oled.width // 2)
    cy = element.get("y", 38)
    base_w = element.get("base_w", 24)
    base_h = element.get("base_h", 12)
    inset_w = element.get("inset_w", 10)
    inset_h = element.get("inset_h", 5)
    phase_count = element.get("phase_count", 16)
    rect_count = element.get("rect_count", 3)
    phase = cycle_index(now_ms, element.get("tick_ms", 130), phase_count)

    for idx in range(rect_count):
        width = max(8, base_w + phase * 2 - idx * inset_w)
        height = max(6, base_h + phase - idx * inset_h)
        x = cx - width // 2
        y = cy - height // 2
        oled.rect(x, y, width, height, 1)


def draw_text_center(oled, now_ms, element, word):
    field = element.get("field", "sentence_en")
    y = element.get("y", 54)
    text = word.get(field, "")
    views.center_text(oled, views.clamp_text_to_width(text, oled.width - 4), y)


def draw_water_rows(oled, now_ms, element, word):
    start_y = element.get("start_y", 20)
    rows = element.get("rows", 4)
    row_gap = element.get("row_gap", 9)
    wave_period = element.get("wave_period", 18)
    shift = cycle_index(now_ms, element.get("tick_ms", 90), wave_period)

    for row in range(rows):
        y = start_y + row * row_gap
        row_shift = (shift + row * 4) % wave_period
        for start in range(-wave_period, oled.width + wave_period, wave_period):
            x = start - row_shift
            oled.hline(x, y, 8, 1)
            oled.hline(x + 8, y + 1, 8, 1)
            oled.hline(x + 2, y + 3, 8, 1)


def draw_bubble_field(oled, now_ms, element, word):
    start_y = element.get("start_y", 20)
    rows = element.get("rows", 4)
    row_gap = element.get("row_gap", 9)

    for row in range(rows):
        y = start_y + row * row_gap
        bubble_x = (now_ms // (70 + row * 20) + row * 17) % oled.width
        bubble_y = y - ((now_ms // (90 + row * 10)) % 6)
        oled.rect(bubble_x, bubble_y, 3, 3, 1)


def draw_sun_element(oled, now_ms, element, word):
    cx = element.get("x", oled.width // 2)
    cy = element.get("y", 36)
    radius = element.get("radius", 9)
    ray = element.get("ray", 5)
    phase = cycle_index(now_ms, element.get("tick_ms", 140), element.get("phase_count", 6))
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


def draw_moon_element(oled, now_ms, element, word):
    cx = element.get("x", oled.width // 2)
    cy = element.get("y", 36)
    radius = element.get("radius", 13)
    cutout_x = element.get("cutout_x", 5)
    drift_steps = element.get("drift_steps", 5)
    drift = cycle_index(now_ms, element.get("tick_ms", 220), drift_steps) - (drift_steps // 2)

    fill_circle(oled, cx, cy, radius, 1)
    fill_circle(oled, cx + cutout_x + drift, cy - 1, max(1, radius - 2), 0)


def draw_stars_element(oled, now_ms, element, word):
    points = element.get("points", ())
    twinkle = cycle_index(now_ms, element.get("tick_ms", 180), len(points))
    for idx, point in enumerate(points):
        x, y = point
        if idx == twinkle:
            oled.line(x - 2, y, x + 2, y, 1)
            oled.line(x, y - 2, x, y + 2, 1)
        else:
            oled.pixel(x, y, 1)


def draw_house_element(oled, now_ms, element, word):
    left = element.get("left", 34)
    top = element.get("top", 24)
    width = element.get("width", 60)
    height = element.get("height", 28)
    phase = cycle_index(now_ms, element.get("tick_ms", 220), element.get("phase_count", 4))
    lit_left = (phase % 2) == 0

    oled.rect(left, top, width, height, 1)
    oled.line(left, top, left + width // 2, top - 14, 1)
    oled.line(left + width, top, left + width // 2, top - 14, 1)
    oled.rect(left + 24, top + 12, 12, 16, 1)
    draw_window(oled, left + 8, top + 8, lit=lit_left)
    draw_window(oled, left + 44, top + 8, lit=not lit_left)


def draw_peace_symbol(oled, now_ms, element, word):
    cx = element.get("x", oled.width // 2)
    cy = element.get("y", 34)
    radius = element.get("radius", 12)

    draw_circle(oled, cx, cy, radius, 1)
    oled.line(cx, cy - 9, cx, cy + 9, 1)
    oled.line(cx, cy, cx - 7, cy + 8, 1)
    oled.line(cx, cy, cx + 7, cy + 8, 1)


def draw_ring_element(oled, now_ms, element, word):
    cx = element.get("x", oled.width // 2)
    cy = element.get("y", 34)
    base_radius = element.get("base_radius", 16)
    step = element.get("step", 1)
    radius = base_radius + cycle_index(now_ms, element.get("tick_ms", 140), element.get("phase_count", 7)) * step
    draw_circle(oled, cx, cy, radius, 1)


def draw_branch_element(oled, now_ms, element, word):
    draw_branch(
        oled,
        element.get("start_x", 42),
        element.get("start_y", 50),
        element.get("direction", 1),
    )


def draw_person_walk_element(oled, now_ms, element, word):
    base_x = element.get("base_x", 20)
    travel = element.get("travel", 78)
    x = base_x + ((now_ms // max(1, element.get("move_tick_ms", 90))) % max(1, travel))
    gait_phase = cycle_index(now_ms, element.get("gait_tick_ms", 120), 4)

    if gait_phase in (0, 2):
        arm_left_dx, arm_right_dx = 6, 2
        leg_left_dx, leg_right_dx = 2, 6
    else:
        arm_left_dx, arm_right_dx = 2, 6
        leg_left_dx, leg_right_dx = 6, 2

    draw_stick_person(
        oled,
        x,
        element.get("head_y", 20) + (1 if gait_phase in (1, 3) else 0),
        body_len=element.get("body_len", 13),
        arm_left_dx=arm_left_dx,
        arm_right_dx=arm_right_dx,
        leg_left_dx=leg_left_dx,
        leg_right_dx=leg_right_dx,
        ground_y=element.get("ground_y", 53),
    )


def draw_person_sway_element(oled, now_ms, element, word):
    sway = cycle_index(now_ms, element.get("sway_tick_ms", 180), 5) - 2

    draw_stick_person(
        oled,
        element.get("base_x", oled.width // 2) + sway,
        element.get("head_y", 20),
        body_len=element.get("body_len", 11),
        arm_left_dx=4 + max(0, sway),
        arm_right_dx=4 + max(0, -sway),
        leg_left_dx=4,
        leg_right_dx=4,
        body_dx=sway // 2,
        ground_y=element.get("ground_y", 53),
        dress=True,
        arm_y=element.get("arm_y", element.get("head_y", 20) + 11),
        hair=bool(element.get("hair", False)),
    )


def draw_person_bounce_element(oled, now_ms, element, word):
    jump_steps = element.get("jump_steps", (0,))
    jump = cycle_value(now_ms, element.get("tick_ms", 100), jump_steps)
    phase = cycle_index(now_ms, element.get("tick_ms", 100), len(jump_steps))
    head_y = element.get("head_y", 24) - jump

    draw_stick_person(
        oled,
        element.get("x", 42),
        head_y,
        body_len=element.get("body_len", 9),
        arm_left_dx=6,
        arm_right_dx=5,
        leg_left_dx=5 + (phase % 2),
        leg_right_dx=5 + ((phase + 1) % 2),
        ground_y=element.get("ground_y", 54) - jump,
        arm_y=element.get("head_y", 24) + 9 - jump,
    )


def draw_ball_bounce_element(oled, now_ms, element, word):
    offsets = element.get("offsets", (0,))
    fill_circle(
        oled,
        element.get("x", 82),
        element.get("y", 43) - cycle_value(now_ms, element.get("tick_ms", 100), offsets),
        element.get("radius", 3),
        1,
    )


def draw_person_pose_element(oled, now_ms, element, word):
    draw_stick_person(
        oled,
        element.get("x", 38),
        element.get("head_y", 22),
        body_len=element.get("body_len", 10),
        arm_left_dx=element.get("arm_dx", 5),
        arm_right_dx=element.get("arm_dx", 5),
        leg_left_dx=element.get("leg_dx", 4),
        leg_right_dx=element.get("leg_dx", 4),
        body_dx=element.get("body_dx", 0),
        ground_y=element.get("ground_y", 53),
        dress=bool(element.get("dress", False)),
        arm_y=element.get("arm_y"),
        hair=bool(element.get("hair", False)),
    )


def draw_open_book_element(oled, now_ms, element, word):
    spreads = element.get("spreads", (8,))
    draw_open_book(
        oled,
        element.get("x", 74),
        element.get("y", 28),
        spread=cycle_value(now_ms, element.get("tick_ms", 160), spreads),
    )


def draw_reading_lines_element(oled, now_ms, element, word):
    for line in element.get("lines", ()):
        oled.line(line[0], line[1], line[2], line[3], 1)


def draw_dog_element(oled, now_ms, element, word):
    x = element.get("x", 44)
    y = element.get("y", 34)
    phase = cycle_index(now_ms, element.get("tick_ms", 130), element.get("phase_count", 4))
    tail_y = y + (phase - 1)

    oled.fill_rect(x, y, 28, 12, 1)
    oled.fill_rect(x + 24, y - 6, 10, 10, 1)
    oled.fill_rect(x + 4, y + 12, 3, 8, 1)
    oled.fill_rect(x + 18, y + 12, 3, 8, 1)
    oled.line(x - 8, tail_y, x, y + 3, 1)
    oled.pixel(x + 30, y - 3, 0)
    oled.pixel(x + 30, y - 1, 0)
    oled.pixel(x + 31, y - 3, 0)


def draw_ground_element(oled, now_ms, element, word):
    draw_ground(oled, element.get("x", 0), element.get("y", 55), element.get("width", oled.width))


ELEMENT_DRAWERS = {
    "pulse_rects": draw_pulse_rects,
    "text_center": draw_text_center,
    "water_rows": draw_water_rows,
    "bubble_field": draw_bubble_field,
    "sun": draw_sun_element,
    "moon": draw_moon_element,
    "stars": draw_stars_element,
    "house": draw_house_element,
    "peace_symbol": draw_peace_symbol,
    "ring": draw_ring_element,
    "branch": draw_branch_element,
    "person_walk": draw_person_walk_element,
    "person_sway": draw_person_sway_element,
    "person_bounce": draw_person_bounce_element,
    "ball_bounce": draw_ball_bounce_element,
    "person_pose": draw_person_pose_element,
    "open_book": draw_open_book_element,
    "reading_lines": draw_reading_lines_element,
    "dog": draw_dog_element,
    "ground": draw_ground_element,
}
