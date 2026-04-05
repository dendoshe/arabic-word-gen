from lib.ui import views

DEFAULT_ANIMATION = "pulse"
ANIMATION_ALIASES = {
    "walker": "man",
}


def draw_secondary_animation(oled, state, word):
    now_ms = int(state.get("now_ms", 0))
    word_key = state.get("word_key", "")
    animation_name = resolve_animation_name(word)
    label = word.get("translit") or word_key or ""

    oled.clear()
    draw_animation_header(oled, label)
    draw_animation(oled, animation_name, now_ms, word)


def resolve_animation_name(word):
    animation_name = word.get("animation")
    if not isinstance(animation_name, str) or not animation_name:
        return DEFAULT_ANIMATION

    resolved = ANIMATION_ALIASES.get(animation_name, animation_name)
    if resolved in ANIMATIONS:
        return resolved
    return DEFAULT_ANIMATION


def draw_animation(oled, animation_name, now_ms, word):
    drawer = ANIMATIONS.get(animation_name) or ANIMATIONS[DEFAULT_ANIMATION]
    drawer(oled, now_ms, word)


def draw_animation_header(oled, label):
    views.center_text(oled, views.clamp_text_to_width(label, oled.width - 4), 0)
    oled.hline(0, 10, oled.width, 1)


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


def draw_pulse_rects(
    oled,
    now_ms,
    *,
    cx=64,
    cy=38,
    base_w=24,
    base_h=12,
    inset_w=10,
    inset_h=5,
    tick_ms=130,
    phase_count=16,
    rect_count=3,
):
    phase = cycle_index(now_ms, tick_ms, phase_count)

    for idx in range(rect_count):
        width = max(8, base_w + phase * 2 - idx * inset_w)
        height = max(6, base_h + phase - idx * inset_h)
        x = cx - width // 2
        y = cy - height // 2
        oled.rect(x, y, width, height, 1)


def draw_text_center(oled, word, *, field="sentence_en", y=54):
    text = word.get(field, "")
    views.center_text(oled, views.clamp_text_to_width(text, oled.width - 4), y)


def draw_water_rows(
    oled,
    now_ms,
    *,
    start_y=20,
    rows=4,
    row_gap=9,
    wave_period=18,
    tick_ms=90,
):
    shift = cycle_index(now_ms, tick_ms, wave_period)

    for row in range(rows):
        y = start_y + row * row_gap
        row_shift = (shift + row * 4) % wave_period
        for start in range(-wave_period, oled.width + wave_period, wave_period):
            x = start - row_shift
            oled.hline(x, y, 8, 1)
            oled.hline(x + 8, y + 1, 8, 1)
            oled.hline(x + 2, y + 3, 8, 1)


def draw_bubble_field(oled, now_ms, *, start_y=20, rows=4, row_gap=9):
    for row in range(rows):
        y = start_y + row * row_gap
        bubble_x = (now_ms // (70 + row * 20) + row * 17) % oled.width
        bubble_y = y - ((now_ms // (90 + row * 10)) % 6)
        oled.rect(bubble_x, bubble_y, 3, 3, 1)


def draw_sun_icon(oled, now_ms, *, cx=64, cy=36, radius=9, ray=5, tick_ms=140, phase_count=6):
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


def draw_moon_icon(oled, now_ms, *, cx=64, cy=36, radius=13, cutout_x=5, tick_ms=220, drift_steps=5):
    drift = cycle_index(now_ms, tick_ms, drift_steps) - (drift_steps // 2)
    fill_circle(oled, cx, cy, radius, 1)
    fill_circle(oled, cx + cutout_x + drift, cy - 1, max(1, radius - 2), 0)


def draw_stars(oled, now_ms, *, points=((22, 20), (90, 18), (102, 30), (26, 46)), tick_ms=180):
    twinkle = cycle_index(now_ms, tick_ms, len(points))
    for idx, point in enumerate(points):
        x, y = point
        if idx == twinkle:
            oled.line(x - 2, y, x + 2, y, 1)
            oled.line(x, y - 2, x, y + 2, 1)
        else:
            oled.pixel(x, y, 1)


def draw_house(oled, now_ms, *, left=34, top=24, width=60, height=28, tick_ms=220, phase_count=4):
    phase = cycle_index(now_ms, tick_ms, phase_count)
    lit_left = (phase % 2) == 0

    oled.rect(left, top, width, height, 1)
    oled.line(left, top, left + width // 2, top - 14, 1)
    oled.line(left + width, top, left + width // 2, top - 14, 1)
    oled.rect(left + 24, top + 12, 12, 16, 1)
    draw_window(oled, left + 8, top + 8, lit=lit_left)
    draw_window(oled, left + 44, top + 8, lit=not lit_left)


def draw_peace_symbol(oled, *, cx=64, cy=34, radius=12):
    draw_circle(oled, cx, cy, radius, 1)
    oled.line(cx, cy - 9, cx, cy + 9, 1)
    oled.line(cx, cy, cx - 7, cy + 8, 1)
    oled.line(cx, cy, cx + 7, cy + 8, 1)


def draw_ring(oled, now_ms, *, cx=64, cy=34, base_radius=16, step=1, tick_ms=140, phase_count=7):
    radius = base_radius + cycle_index(now_ms, tick_ms, phase_count) * step
    draw_circle(oled, cx, cy, radius, 1)


def draw_walking_person(
    oled,
    now_ms,
    *,
    base_x=20,
    travel=78,
    move_tick_ms=90,
    gait_tick_ms=120,
    head_y=20,
    body_len=13,
    ground_y=53,
):
    x = base_x + ((now_ms // max(1, move_tick_ms)) % max(1, travel))
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


def draw_swaying_person(
    oled,
    now_ms,
    *,
    base_x=64,
    head_y=20,
    sway_tick_ms=180,
    body_len=11,
    ground_y=53,
    hair=True,
):
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
        hair=hair,
    )


def draw_bouncing_person(
    oled,
    now_ms,
    *,
    x=42,
    head_y=24,
    jump_steps=(0, 2, 5, 2, 0, 1),
    tick_ms=100,
    body_len=9,
    ground_y=54,
):
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


def draw_bouncing_ball(oled, now_ms, *, x=82, y=43, offsets=(0, 3, 7, 3, 0, 2), tick_ms=100, radius=3):
    fill_circle(oled, x, y - cycle_value(now_ms, tick_ms, offsets), radius, 1)


def draw_person_pose(
    oled,
    *,
    x=38,
    head_y=22,
    body_len=10,
    arm_dx=5,
    leg_dx=4,
    ground_y=53,
    dress=False,
    arm_y=None,
    body_dx=0,
    hair=False,
):
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
        dress=dress,
        arm_y=arm_y,
        hair=hair,
    )


def draw_book(oled, now_ms, *, x=74, y=28, spreads=(7, 8, 9, 10), tick_ms=160):
    draw_open_book(oled, x, y, spread=cycle_value(now_ms, tick_ms, spreads))


def draw_reading_lines(oled, *, lines=((43, 33, 64, 34), (43, 35, 66, 40))):
    for line in lines:
        oled.line(line[0], line[1], line[2], line[3], 1)


def draw_dog(oled, now_ms, *, x=44, y=34, tick_ms=130, phase_count=4):
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


def draw_pulse_animation(oled, now_ms, word):
    draw_pulse_rects(oled, now_ms)
    draw_text_center(oled, word)


def draw_water_animation(oled, now_ms, word):
    draw_water_rows(oled, now_ms)
    draw_bubble_field(oled, now_ms)


def draw_sun_animation(oled, now_ms, word):
    draw_sun_icon(oled, now_ms)


def draw_moon_animation(oled, now_ms, word):
    draw_moon_icon(oled, now_ms)
    draw_stars(oled, now_ms)


def draw_house_animation(oled, now_ms, word):
    draw_house(oled, now_ms)


def draw_peace_animation(oled, now_ms, word):
    draw_peace_symbol(oled)
    draw_ring(oled, now_ms)
    draw_branch(oled, 42, 50, 1)
    draw_branch(oled, 86, 50, -1)


def draw_man_animation(oled, now_ms, word):
    draw_walking_person(oled, now_ms)
    draw_ground(oled, 10, 55, 108)


def draw_woman_animation(oled, now_ms, word):
    draw_swaying_person(oled, now_ms)
    draw_ground(oled, 18, 55, 92)


def draw_boy_animation(oled, now_ms, word):
    draw_bouncing_person(oled, now_ms)
    draw_bouncing_ball(oled, now_ms)
    draw_ground(oled, 10, 56, 108)


def draw_girl_animation(oled, now_ms, word):
    draw_person_pose(oled, dress=True, arm_y=31)
    draw_book(oled, now_ms)
    draw_reading_lines(oled)
    draw_ground(oled, 16, 55, 96)


def draw_dog_animation(oled, now_ms, word):
    draw_dog(oled, now_ms)
    draw_ground(oled, 20, 56, 88)


ANIMATIONS = {
    "pulse": draw_pulse_animation,
    "water": draw_water_animation,
    "sun": draw_sun_animation,
    "moon": draw_moon_animation,
    "house": draw_house_animation,
    "peace": draw_peace_animation,
    "man": draw_man_animation,
    "woman": draw_woman_animation,
    "boy": draw_boy_animation,
    "girl": draw_girl_animation,
    "dog": draw_dog_animation,
}
