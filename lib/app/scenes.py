# lib/app/scenes.py

class Buttons:
    def __init__(self, b1, b2, b3):
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3

    def pressed1(self): return self.b1.is_pressed()
    def pressed2(self): return self.b2.is_pressed()
    def pressed3(self): return self.b3.is_pressed()


class Scene:
    name = "base"

    def enter(self, state):  # called once when scene becomes active
        pass

    def exit(self, state):   # called once when scene is deactivated
        pass

    def tick(self, state, now_ms, buttons):
        pass

    def draw(self, oled, state):
        pass