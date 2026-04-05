"""
Tkinter-based OLED simulator for desktop use.
"""

import time

try:
    import tkinter as tk
except Exception:  # pragma: no cover - depends on local desktop environment
    tk = None

from lib.app import config, navigation, words as words_mod
from lib.display.recording import RecordingDisplayGroup
from lib.ui import dual_screen

OLED_WIDTH = 128
OLED_HEIGHT = 64
DEFAULT_SCALE = 2


def _ticks_ms():
    return int(time.monotonic() * 1000)


def _title_case_view(name):
    return str(name or "").replace("_", " ").title()


class VirtualButton:
    def __init__(self):
        self._pressed = False
        self._press_latched = False

    def press(self):
        if not self._pressed:
            self._press_latched = True
        self._pressed = True

    def release(self):
        self._pressed = False

    def is_pressed(self):
        return self._pressed

    def consume_press(self, _now_ms=None):
        latched = self._press_latched
        self._press_latched = False
        return latched


class CanvasDisplayRenderer:
    def __init__(self, canvas, *, width=OLED_WIDTH, height=OLED_HEIGHT, scale=DEFAULT_SCALE):
        self.canvas = canvas
        self._width = int(width)
        self._height = int(height)
        self.scale = max(1, int(scale))
        self._bg_off = "#07120c"
        self._bg_on = "#d6ffdd"
        self._fg_on = "#d6ffdd"
        self._fg_off = "#07120c"
        self._text_font = ("Courier", max(8, self.scale * 3), "normal")

    def render(self, background_color, ops):
        self.canvas.delete("all")
        self.canvas.create_rectangle(
            0,
            0,
            self._width * self.scale,
            self._height * self.scale,
            fill=self._bg_for(background_color),
            outline=self._bg_for(background_color),
        )

        for op in ops:
            kind = op["op"]
            if kind == "text":
                self._draw_text(op)
            elif kind == "fill_rect":
                self._draw_fill_rect(op)
            elif kind == "rect":
                self._draw_rect(op)
            elif kind == "hline":
                self._draw_hline(op)
            elif kind == "vline":
                self._draw_vline(op)
            elif kind == "line":
                self._draw_line(op)
            elif kind == "pixel":
                self._draw_pixel(op["x"], op["y"], op["color"])
            elif kind == "blit":
                self._draw_blit(op)

    def _bg_for(self, color):
        return self._bg_on if int(color) else self._bg_off

    def _fg_for(self, color):
        return self._fg_on if int(color) else self._fg_off

    def _sx(self, x):
        return int(x) * self.scale

    def _sy(self, y):
        return int(y) * self.scale

    def _draw_pixel(self, x, y, color):
        sx = self._sx(x)
        sy = self._sy(y)
        self.canvas.create_rectangle(
            sx,
            sy,
            sx + self.scale,
            sy + self.scale,
            fill=self._fg_for(color),
            outline=self._fg_for(color),
        )

    def _draw_text(self, op):
        self.canvas.create_text(
            self._sx(op["x"]) + 1,
            self._sy(op["y"]),
            anchor="nw",
            text=op["text"],
            fill=self._fg_for(op["color"]),
            font=self._text_font,
        )

    def _draw_fill_rect(self, op):
        self.canvas.create_rectangle(
            self._sx(op["x"]),
            self._sy(op["y"]),
            self._sx(op["x"] + op["w"]),
            self._sy(op["y"] + op["h"]),
            fill=self._fg_for(op["color"]),
            outline=self._fg_for(op["color"]),
        )

    def _draw_rect(self, op):
        self.canvas.create_rectangle(
            self._sx(op["x"]),
            self._sy(op["y"]),
            self._sx(op["x"] + op["w"]),
            self._sy(op["y"] + op["h"]),
            outline=self._fg_for(op["color"]),
            width=max(1, self.scale // 2),
        )

    def _draw_hline(self, op):
        self.canvas.create_line(
            self._sx(op["x"]),
            self._sy(op["y"]),
            self._sx(op["x"] + op["w"]),
            self._sy(op["y"]),
            fill=self._fg_for(op["color"]),
            width=max(1, self.scale // 2),
        )

    def _draw_vline(self, op):
        self.canvas.create_line(
            self._sx(op["x"]),
            self._sy(op["y"]),
            self._sx(op["x"]),
            self._sy(op["y"] + op["h"]),
            fill=self._fg_for(op["color"]),
            width=max(1, self.scale // 2),
        )

    def _draw_line(self, op):
        self.canvas.create_line(
            self._sx(op["x1"]),
            self._sy(op["y1"]),
            self._sx(op["x2"]),
            self._sy(op["y2"]),
            fill=self._fg_for(op["color"]),
            width=max(1, self.scale // 2),
        )

    def _draw_blit(self, op):
        buffer = op.get("buffer")
        width = int(getattr(buffer, "width", 0) or 0)
        height = int(getattr(buffer, "height", 0) or 0)
        if width <= 0 or height <= 0:
            return

        origin_x = int(op["x"])
        origin_y = int(op["y"])
        for y in range(height):
            run_start = None
            for x in range(width):
                pixel_on = self._framebuffer_pixel(buffer, x, y)
                if pixel_on and run_start is None:
                    run_start = x
                elif not pixel_on and run_start is not None:
                    self._draw_run(origin_x + run_start, origin_y + y, x - run_start)
                    run_start = None
            if run_start is not None:
                self._draw_run(origin_x + run_start, origin_y + y, width - run_start)

    def _draw_run(self, x, y, width):
        self.canvas.create_rectangle(
            self._sx(x),
            self._sy(y),
            self._sx(x + width),
            self._sy(y + 1),
            fill=self._fg_on,
            outline=self._fg_on,
        )

    def _framebuffer_pixel(self, buffer, x, y):
        pixel = getattr(buffer, "pixel", None)
        if callable(pixel):
            try:
                return 1 if pixel(x, y) else 0
            except TypeError:
                pass

        raw = getattr(buffer, "buffer", None)
        width = int(getattr(buffer, "width", 0) or 0)
        if raw is None or width <= 0:
            return 0
        idx = x + (y // 8) * width
        bit = 1 << (y % 8)
        return 1 if (raw[idx] & bit) else 0


class SimulatorWindow:
    def __init__(self, words, *, initial_state=None, fps=30, scale=DEFAULT_SCALE, title=None):
        if tk is None:
            raise RuntimeError("tkinter is not available in this Python environment.")

        self.words = words
        self.fps = max(1, int(fps or 30))
        self.frame_delay_ms = max(1, 1000 // self.fps)
        self.scale = max(1, int(scale))
        self.root = tk.Tk()
        self.root.title(title or "Arabic Word Gen Simulator")
        self.root.resizable(False, False)
        self.root.configure(bg="#111111")

        default_state = {
            "view": "base",
            "word_key": words_mod.initial_word_key(words),
            "last_pressed": {1: False, 2: False, 3: False},
            "form_idx": 0,
            "now_ms": 0,
            "changed_at": 0,
        }
        self.state = default_state
        if initial_state:
            self.state.update(initial_state)

        self.buttons = {
            1: VirtualButton(),
            2: VirtualButton(),
            3: VirtualButton(),
        }
        self.power_off_requested = False
        self.power_off_started_at = None
        self._running = True
        self._button_widgets = {}
        self._renderers = {}
        self._status_var = tk.StringVar()

        self._build_layout()
        self._bind_events()
        self.root.focus_set()
        self._refresh_button_labels()
        self._update_status()

    def run(self):
        self.root.after(0, self._step)
        self.root.mainloop()

    def _build_layout(self):
        outer = tk.Frame(self.root, bg="#151515", padx=10, pady=10)
        outer.pack()

        display_row = tk.Frame(outer, bg="#151515")
        display_row.pack()

        canvases = {}
        for name in ("primary", "secondary"):
            panel = tk.Frame(display_row, bg="#0f0f0f", bd=0, padx=0, pady=0)
            panel.pack(side="left", padx=5)

            board = tk.Frame(panel, bg="#174a7a", padx=10, pady=10)
            board.pack()

            header = tk.Frame(board, bg="#174a7a", height=12)
            header.pack(fill="x")

            header.pack_propagate(False)
            label = tk.Label(
                header,
                text=name.upper(),
                fg="#d9eefc",
                bg="#174a7a",
                font=("Helvetica", 8, "bold"),
            )
            label.pack(side="left")

            bezel = tk.Frame(board, bg="#243024", padx=4, pady=4)
            bezel.pack()

            canvas = tk.Canvas(
                bezel,
                width=OLED_WIDTH * self.scale,
                height=OLED_HEIGHT * self.scale,
                bg="#07120c",
                highlightthickness=0,
            )
            canvas.pack()
            canvases[name] = canvas

        self.display = RecordingDisplayGroup(canvases.keys(), width=OLED_WIDTH, height=OLED_HEIGHT)
        self._renderers = {
            name: CanvasDisplayRenderer(
                canvas,
                width=OLED_WIDTH,
                height=OLED_HEIGHT,
                scale=self.scale,
            )
            for name, canvas in canvases.items()
        }

        controls = tk.Frame(outer, bg="#151515", pady=8)
        controls.pack(fill="x")

        for idx in (1, 2, 3):
            button = tk.Button(
                controls,
                text="",
                width=10,
                font=("Helvetica", 9, "bold"),
                relief="raised",
                bg="#e7e7e7",
                activebackground="#d5d5d5",
                padx=4,
                pady=3,
            )
            button.pack(side="left", padx=4)
            button.bind("<ButtonPress-1>", lambda _event, button_idx=idx: self._press(button_idx))
            button.bind("<ButtonRelease-1>", lambda _event, button_idx=idx: self._release(button_idx))
            button.bind("<Leave>", lambda _event, button_idx=idx: self._release(button_idx))
            self._button_widgets[idx] = button

        status = tk.Label(
            outer,
            textvariable=self._status_var,
            justify="left",
            anchor="w",
            fg="#d8d8d8",
            bg="#151515",
            font=("Helvetica", 9),
        )
        status.pack(fill="x")

    def _bind_events(self):
        self.root.bind_all("<KeyPress-1>", lambda _event: self._press(1))
        self.root.bind_all("<KeyRelease-1>", lambda _event: self._release(1))
        self.root.bind_all("<KeyPress-2>", lambda _event: self._press(2))
        self.root.bind_all("<KeyRelease-2>", lambda _event: self._release(2))
        self.root.bind_all("<KeyPress-3>", lambda _event: self._press(3))
        self.root.bind_all("<KeyRelease-3>", lambda _event: self._release(3))
        self.root.bind_all("<Escape>", lambda _event: self._close())
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _press(self, idx):
        self.buttons[idx].press()
        self._set_button_relief(idx, pressed=True)

    def _release(self, idx):
        self.buttons[idx].release()
        self._set_button_relief(idx, pressed=False)

    def _set_button_relief(self, idx, *, pressed):
        widget = self._button_widgets[idx]
        widget.configure(relief="sunken" if pressed else "raised")

    def _close(self):
        self._running = False
        self.display.safe_off()
        self.root.destroy()

    def _step(self):
        if not self._running:
            return

        now_ms = _ticks_ms()
        self.state["now_ms"] = now_ms
        self._update_power_off(now_ms)
        navigation.handle_buttons(
            self.state,
            now_ms,
            self.buttons,
            word_lookup=lambda state: words_mod.get_word(state, self.words),
        )

        if self.power_off_requested:
            self._close()
            return

        self.display.clear()
        dual_screen.draw_displays(self.display, self.state, self.words)
        self.display.show()
        self._render_frames()
        self._refresh_button_labels()
        self._update_status()
        self.root.after(self.frame_delay_ms, self._step)

    def _render_frames(self):
        for name, renderer in self._renderers.items():
            background, ops = self.display.screen(name).frame()
            renderer.render(background, ops)

    def _update_power_off(self, now_ms):
        if self.power_off_requested:
            return

        if self.buttons[3].is_pressed():
            if self.power_off_started_at is None:
                self.power_off_started_at = now_ms
            elif now_ms - self.power_off_started_at >= config.FACE_OFF_HOLD_MS:
                self.power_off_requested = True
        else:
            self.power_off_started_at = None

    def _refresh_button_labels(self):
        current_word = words_mod.get_word(self.state, self.words)
        view = self.state.get("view", "base")
        transitions = navigation.VIEW_TRANSITIONS.get(view, {})

        labels = {}
        for idx in (1, 2, 3):
            next_view = transitions.get(idx, view)
            labels[idx] = "B%d %s" % (idx, _title_case_view(next_view))

        if view == "forms":
            forms = current_word.get("forms") or []
            if forms and self.state.get("form_idx", 0) < len(forms) - 1:
                labels[2] = "B2 Next Form"
            else:
                labels[2] = "B2 Home"

        for idx, widget in self._button_widgets.items():
            widget.configure(text=labels[idx])

    def _update_status(self):
        word = words_mod.get_word(self.state, self.words)
        hold_ms = 0
        if self.power_off_started_at is not None and self.buttons[3].is_pressed():
            hold_ms = max(0, _ticks_ms() - self.power_off_started_at)

        self._status_var.set(
            "Word: %s   View: %s   Form: %d   Keys: 1, 2, 3   Hold B3 for %.1fs to close"
            % (
                word.get("translit") or self.state.get("word_key"),
                _title_case_view(self.state.get("view", "base")),
                int(self.state.get("form_idx", 0)) + 1,
                max(0.0, (config.FACE_OFF_HOLD_MS - hold_ms) / 1000.0),
            )
        )


def run_simulator(words, *, initial_state=None, fps=30, scale=DEFAULT_SCALE, title=None):
    if tk is None:
        print("tkinter is unavailable; cannot open the desktop simulator.")
        return False

    try:
        app = SimulatorWindow(
            words,
            initial_state=initial_state,
            fps=fps,
            scale=scale,
            title=title,
        )
    except tk.TclError as exc:  # pragma: no cover - depends on local desktop environment
        print("failed to start desktop simulator:", exc)
        return False

    app.run()
    return True
