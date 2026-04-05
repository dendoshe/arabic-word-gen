class NamedDisplayGroup:
    """
    Shared named-display wrapper used by both hardware and simulator backends.
    """

    def __init__(self, displays=None, order=()):
        self._displays = {}
        self._order = ()
        if displays:
            self.set_displays(displays, order=order)

    def set_displays(self, displays, *, order=()):
        self._displays = dict(displays or {})
        if order:
            self._order = tuple(order)
        else:
            self._order = tuple(self._displays.keys())

    def screen(self, name):
        display = self._displays.get(name)
        if display is None:
            raise KeyError("Unknown display: %s" % name)
        return display

    def _ordered_displays(self):
        ordered = []
        for name in self._order:
            display = self._displays.get(name)
            if display is not None:
                ordered.append(display)
        return ordered

    def _ready_displays(self):
        ready = []
        for display in self._ordered_displays():
            if display.is_ready():
                ready.append(display)
        if not ready:
            raise RuntimeError("OLED not initialized (no address found at 0x3C/0x3D).")
        return ready

    def is_ready(self):
        for display in self._ordered_displays():
            if display.is_ready():
                return True
        return False

    def clear(self, color=0):
        for display in self._ready_displays():
            display.clear(color)

    def text(self, msg, x, y, color=1):
        for display in self._ready_displays():
            display.text(msg, x, y, color)

    def fill_rect(self, x, y, w, h, color=1):
        for display in self._ready_displays():
            display.fill_rect(x, y, w, h, color)

    def rect(self, x, y, w, h, color=1):
        for display in self._ready_displays():
            display.rect(x, y, w, h, color)

    def hline(self, x, y, w, color=1):
        for display in self._ready_displays():
            display.hline(x, y, w, color)

    def vline(self, x, y, h, color=1):
        for display in self._ready_displays():
            display.vline(x, y, h, color)

    def line(self, x1, y1, x2, y2, color=1):
        for display in self._ready_displays():
            display.line(x1, y1, x2, y2, color)

    def pixel(self, x, y, color=1):
        for display in self._ready_displays():
            display.pixel(x, y, color)

    def blit(self, buffer, x, y):
        for display in self._ready_displays():
            display.blit(buffer, x, y)

    def show(self):
        for display in self._ready_displays():
            display.show()

    def safe_off(self):
        for display in self._ordered_displays():
            display.safe_off()

    @property
    def width(self):
        return self._ready_displays()[0].width

    @property
    def height(self):
        return self._ready_displays()[0].height
