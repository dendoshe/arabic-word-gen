from lib.display.group import NamedDisplayGroup


class RecordingDisplay:
    """
    Display-like surface that records draw operations and snapshots them on show().
    """

    def __init__(self, *, name="display", width=128, height=64):
        self.name = name
        self._width = int(width)
        self._height = int(height)
        self._ops = []
        self._frame_background = 0
        self._frame_ops = ()

    def reset(self):
        self._ops = []

    def is_ready(self):
        return True

    def clear(self, color=0):
        self._ops.append({"op": "clear", "color": int(color)})

    def text(self, msg, x, y, color=1):
        self._ops.append(
            {
                "op": "text",
                "text": str(msg),
                "x": int(x),
                "y": int(y),
                "color": int(color),
            }
        )

    def fill_rect(self, x, y, w, h, color=1):
        self._shape("fill_rect", x=x, y=y, w=w, h=h, color=color)

    def rect(self, x, y, w, h, color=1):
        self._shape("rect", x=x, y=y, w=w, h=h, color=color)

    def hline(self, x, y, w, color=1):
        self._shape("hline", x=x, y=y, w=w, color=color)

    def vline(self, x, y, h, color=1):
        self._shape("vline", x=x, y=y, h=h, color=color)

    def line(self, x1, y1, x2, y2, color=1):
        self._shape("line", x1=x1, y1=y1, x2=x2, y2=y2, color=color)

    def pixel(self, x, y, color=1):
        self._shape("pixel", x=x, y=y, color=color)

    def blit(self, buffer, x, y):
        self._ops.append(
            {
                "op": "blit",
                "buffer": buffer,
                "x": int(x),
                "y": int(y),
            }
        )

    def show(self):
        background, ops = self._normalized_ops()
        self._frame_background = background
        self._frame_ops = tuple(ops)
        self._ops = []

    def safe_off(self):
        self._ops = [{"op": "clear", "color": 0}]
        self.show()

    def frame(self):
        return self._frame_background, self._frame_ops

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def _shape(self, name, **values):
        entry = {"op": name}
        for key, value in values.items():
            entry[key] = int(value)
        self._ops.append(entry)

    def _normalized_ops(self):
        background = self._frame_background
        draw_ops = list(self._frame_ops)
        if not self._ops:
            return background, draw_ops

        for op in self._ops:
            if op["op"] == "clear":
                background = int(op["color"])
                draw_ops = []
            else:
                draw_ops.append(op)
        return background, draw_ops


class RecordingDisplayGroup(NamedDisplayGroup):
    def __init__(self, names, *, width=128, height=64):
        displays = {}
        order = []
        for name in names:
            order.append(name)
            displays[name] = RecordingDisplay(name=name, width=width, height=height)
        NamedDisplayGroup.__init__(self, displays, order=order)
