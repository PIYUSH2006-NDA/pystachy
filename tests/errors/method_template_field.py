# error: expected int, got str (compiling S.setw(str) for the call at
class S:
    def __init__(self, w: int) -> None:
        self.w = w

    def setw(self, v):
        self.w = v


s = S(1)
s.setw(2)
s.setw("x")
