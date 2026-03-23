import utime


class OledApp:
    def __init__(self, display):
        self.display = display

    def _render_entry(self, *, lines, clear_only, draw_overlay, overlay_state):
        """
        Shared renderer for a single page.
        """
        if not self.display.is_ready():
            raise RuntimeError("OLED not initialized (no address found at 0x3C/0x3D).")

        o = self.display
        o.clear()

        if not clear_only:
            for i, s in enumerate(lines):
                o.text(s, 0, i * 8)

        if draw_overlay:
            draw_overlay(o, overlay_state)
        o.show()

    def _show(self, lines=(), draw_overlay=None, overlay_state=None):
        """
        Simple one-shot draw helper (used in non-frame-loop mode).
        """
        self._render_entry(
            lines=lines,
            clear_only=False,
            draw_overlay=draw_overlay,
            overlay_state=overlay_state,
        )

    def _run_frames(self, entry, *, tick=None, draw_overlay=None, overlay_state=None,
                    fps=30, button_is_pressed=None, wait_next=None, stop_requested=None):
        """
        Frame-based renderer for a single page entry.
        Loops until main button press is detected (via button_is_pressed).
        """
        frame_ms = 1000 // max(1, int(fps)) if fps else 0
        lines = entry.get("lines", ())
        clear_only = entry.get("clear_only", False)

        while True:
            t0 = utime.ticks_ms()

            if stop_requested and stop_requested():
                return False

            if tick:
                tick(overlay_state, t0)

            if stop_requested and stop_requested():
                return False

            self._render_entry(
                lines=lines,
                clear_only=clear_only,
                draw_overlay=draw_overlay,
                overlay_state=overlay_state,
            )

            # Exit on button press (GP18)
            if button_is_pressed and button_is_pressed():
                if wait_next:
                    wait_next()  # debounced press+release
                return True

            now = utime.ticks_ms()
            elapsed = utime.ticks_diff(now, t0)
            if frame_ms > elapsed:
                utime.sleep_ms(frame_ms - elapsed)

    def run(self, *, sda_pin=None, scl_pin=None, i2c_id=0, display_configs=None,
            pages, wait_next=None, button_is_pressed=None,
            verbose=False, strict=False,
            tick=None, fps=30, frame_loop=False,
            draw_overlay=None, overlay_state=None,
            stop_requested=None, loop_pages=False):

        if not pages:
            raise ValueError("pages must be non-empty")
        use_frame_loop = frame_loop or (tick is not None) or (draw_overlay is not None)

        if not use_frame_loop and wait_next is None:
            raise ValueError("wait_next must be provided")
        if use_frame_loop and not button_is_pressed:
            raise ValueError("button_is_pressed required for frame loop exit")

        if display_configs is not None:
            if not hasattr(self.display, "init_many"):
                raise ValueError("display_configs requires a grouped display backend")
            ok = self.display.init_many(
                display_configs,
                verbose=verbose,
                strict=strict,
            )
        else:
            if sda_pin is None or scl_pin is None:
                raise ValueError("sda_pin and scl_pin are required when display_configs is not set")
            ok = self.display.init(
                sda_pin=sda_pin,
                scl_pin=scl_pin,
                i2c_id=i2c_id,
                verbose=verbose,
                strict=strict,
            )
        if not ok:
            return False

        if use_frame_loop:
            return self._play_frames(
                pages,
                wait_next,
                button_is_pressed,
                draw_overlay,
                overlay_state,
                tick,
                fps,
                stop_requested,
                loop_pages,
            )
        return self._play(pages, wait_next, button_is_pressed, draw_overlay, overlay_state, fps)

    def safe_off(self):
        self.display.safe_off()

    def _play(self, pages, wait_next, is_pressed, draw_overlay, overlay_state, fps):
        for f in pages:
            self._render_entry(
                lines=f.get("lines", ()),
                clear_only=f.get("clear_only", False),
                draw_overlay=draw_overlay,
                overlay_state=overlay_state,
            )
            wait_next()
        return True

    def _play_frames(self, pages, wait_next, is_pressed, draw_overlay, overlay_state, tick, fps,
                     stop_requested, loop_pages):
        idx = 0
        total = len(pages)
        while True:
            entry = pages[idx]
            keep_running = self._run_frames(
                entry,
                tick=tick,
                draw_overlay=draw_overlay,
                overlay_state=overlay_state,
                fps=fps,
                button_is_pressed=is_pressed,
                wait_next=wait_next,
                stop_requested=stop_requested,
            )
            if keep_running is False:
                return True
            idx += 1
            if idx >= total:
                if not loop_pages:
                    return True
                idx = 0
