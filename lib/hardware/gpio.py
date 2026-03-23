from machine import Pin
import utime


def onboard_led() -> Pin:
    """
    Return the onboard LED pin (fallback to GP25 if alias is missing).
    """
    try:
        return Pin("LED", Pin.OUT)
    except Exception:
        return Pin(25, Pin.OUT)


def blink_led_forever(period_ms: int = 250) -> None:
    """
    Blink the onboard LED indefinitely with the given period.
    """
    led = onboard_led()
    while True:
        led.toggle()
        utime.sleep_ms(period_ms)


class Button:
    """
    Button helper with latched press events for slow render loops.
    """

    def __init__(self, pin_no: int, *, pull=Pin.PULL_UP, active_low: bool = True, debounce_ms: int = 30):
        self.pin = Pin(pin_no, Pin.IN, pull) if pull is not None else Pin(pin_no, Pin.IN)
        self.active_low = active_low
        self.debounce_ms = debounce_ms
        self._press_latched = False
        self._last_event_ms = utime.ticks_ms()
        self._fallback_pressed = self.is_pressed()
        self._irq_enabled = False

        try:
            trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING
            self.pin.irq(trigger=trigger, handler=self._handle_irq)
            self._irq_enabled = True
        except Exception:
            self._irq_enabled = False

    def is_pressed(self) -> bool:
        v = self.pin.value()
        return (v == 0) if self.active_low else (v == 1)

    def consume_press(self, now_ms=None) -> bool:
        if self._irq_enabled:
            latched = self._press_latched
            self._press_latched = False
            return latched

        now_ms = now_ms if now_ms is not None else utime.ticks_ms()
        pressed = self.is_pressed()
        if pressed != self._fallback_pressed:
            if utime.ticks_diff(now_ms, self._last_event_ms) >= self.debounce_ms:
                self._fallback_pressed = pressed
                self._last_event_ms = now_ms
                return pressed
        return False

    def wait_press(self) -> None:
        self._wait_for_state(True)

    def wait_release(self) -> None:
        self._wait_for_state(False)

    def wait_press_and_release(self) -> None:
        self.wait_press()
        self.wait_release()

    def _wait_for_state(self, want_pressed: bool) -> None:
        # Wait until state matches, then debounce to ensure stability.
        while self.is_pressed() != want_pressed:
            utime.sleep_ms(5)
        utime.sleep_ms(self.debounce_ms)
        while self.is_pressed() != want_pressed:
            utime.sleep_ms(5)

    def _handle_irq(self, pin) -> None:
        now_ms = utime.ticks_ms()
        if utime.ticks_diff(now_ms, self._last_event_ms) < self.debounce_ms:
            return
        self._last_event_ms = now_ms
        if self.is_pressed():
            self._press_latched = True
