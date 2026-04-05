from machine import Pin, I2C, SoftI2C
import ssd1306

from lib.display.group import NamedDisplayGroup


class OledDisplay:
    """
    Thin wrapper around SSD1306_I2C that owns I2C/Pins and exposes basic drawing helpers.
    """

    def __init__(self, w=128, h=64, addrs=(0x3C, 0x3D), soft_freq=100_000, hw_freq=400_000):
        self.w, self.h, self.addrs = w, h, addrs
        self.soft_freq = soft_freq
        self.hw_freq = hw_freq
        self.oled = None
        self._verbose = False

    def _init_on(self, i2c, label=None):
        found = i2c.scan()           # let this throw if bus is broken
        if self._verbose:
            where = f" ({label})" if label else ""
            print(f"I2C scan{where}:", found)
        addr = next((a for a in self.addrs if a in found), None)
        if addr is None:
            return False
        self.oled = ssd1306.SSD1306_I2C(self.w, self.h, i2c, addr=addr)
        return True

    def init(self, *, sda_pin, scl_pin, i2c_id=0, verbose=False, strict=False):
        """
        Initialize the display on the given pins. Returns True if an OLED was found.
        """
        self._verbose = verbose
        self.oled = None
        sda, scl = Pin(sda_pin), Pin(scl_pin)
        errors = []

        # SoftI2C first
        try:
            ok = self._init_on(SoftI2C(sda=sda, scl=scl, freq=self.soft_freq), "SoftI2C")
            if verbose:
                print("OLED:", "SoftI2C OK" if ok else "SoftI2C: not found")
            if ok:
                return True
        except Exception as e:
            errors.append(("SoftI2C", e))
            if verbose:
                print("SoftI2C error:", repr(e))

        # HW I2C fallback
        try:
            ok = self._init_on(I2C(i2c_id, sda=sda, scl=scl, freq=self.hw_freq), f"I2C{i2c_id}")
            if verbose:
                print("OLED:", f"I2C{i2c_id} OK" if ok else f"I2C{i2c_id}: not found")
            if ok:
                return True
        except Exception as e:
            errors.append((f"I2C{i2c_id}", e))
            if verbose:
                print("HW I2C error:", repr(e))

        if strict and errors:
            where, e = errors[-1]
            raise OSError("OLED init failed on %s: %r" % (where, e))

        return False

    def _require(self):
        if not self.oled:
            raise RuntimeError("OLED not initialized (no address found at 0x3C/0x3D).")
        return self.oled

    def is_ready(self) -> bool:
        return self.oled is not None

    def clear(self, color: int = 0) -> None:
        self._require().fill(color)

    def text(self, msg: str, x: int, y: int, color: int = 1) -> None:
        self._require().text(msg, x, y, color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: int = 1) -> None:
        self._require().fill_rect(x, y, w, h, color)

    def rect(self, x: int, y: int, w: int, h: int, color: int = 1) -> None:
        self._require().rect(x, y, w, h, color)

    def hline(self, x: int, y: int, w: int, color: int = 1) -> None:
        self._require().hline(x, y, w, color)

    def vline(self, x: int, y: int, h: int, color: int = 1) -> None:
        self._require().vline(x, y, h, color)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: int = 1) -> None:
        self._require().line(x1, y1, x2, y2, color)

    def pixel(self, x: int, y: int, color: int = 1) -> None:
        self._require().pixel(x, y, color)

    def blit(self, buffer, x: int, y: int) -> None:
        self._require().blit(buffer, x, y)

    def show(self) -> None:
        self._require().show()

    def safe_off(self) -> None:
        o = self.oled
        if not o:
            return
        try:
            o.fill(0)
            o.show()
        except Exception:
            pass
        try:
            o.poweroff()
        except Exception:
            pass

    @property
    def width(self) -> int:
        o = self._require()
        return getattr(o, "width", self.w)

    @property
    def height(self) -> int:
        o = self._require()
        return getattr(o, "height", self.h)


class OledDisplayGroup(NamedDisplayGroup):
    """
    Broadcast drawing operations to multiple OLEDs while keeping named access
    available for future screen-specific layouts.
    """

    def __init__(self, w=128, h=64, addrs=(0x3C, 0x3D), soft_freq=100_000, hw_freq=400_000):
        NamedDisplayGroup.__init__(self)
        self.w, self.h, self.addrs = w, h, addrs
        self.soft_freq = soft_freq
        self.hw_freq = hw_freq

    def init_many(self, display_configs, *, verbose=False, strict=False):
        displays = {}
        order = []
        ready_count = 0

        for idx, cfg in enumerate(display_configs):
            name = cfg.get("name") or "display_%d" % idx
            order.append(name)
            display = OledDisplay(
                w=self.w,
                h=self.h,
                addrs=self.addrs,
                soft_freq=self.soft_freq,
                hw_freq=self.hw_freq,
            )
            displays[name] = display
            if display.init(
                sda_pin=cfg["sda_pin"],
                scl_pin=cfg["scl_pin"],
                i2c_id=cfg.get("i2c_id", idx),
                verbose=verbose,
                strict=False,
            ):
                ready_count += 1

        self.set_displays(displays, order=order)

        if strict and not ready_count:
            raise OSError("No OLED displays initialized.")
        return ready_count > 0
