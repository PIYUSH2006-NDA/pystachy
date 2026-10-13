def note(s: str) -> int:
    print("note:", s)
    return 1


class Table:
    width = note("width")

    def __init__(self, i):
        self.i = i
