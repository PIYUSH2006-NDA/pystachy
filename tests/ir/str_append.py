# s += t and s = s + t of a str local append in place (Gen.str_append, runtime.c's pys_str_iadd)
# while only the local holds its str. str_append.calls pins that these functions call
# pys_str_iadd, and pys_str_add where the target is a global, a closure's variable, a field or
# an optional str, and for a prepend.
total = ""


class Box:
    def __init__(self) -> None:
        self.text = ""

    def add(self, t: str) -> None:
        self.text += t  # a field


def loop(n: int) -> int:
    s = ""
    for i in range(n):
        s += str(i)
    return len(s)


def plus(s: str, t: str) -> str:
    s = s + t
    return s


def prepend(s: str, t: str) -> str:
    s = t + s  # (no append)
    return s


def glob(t: str) -> None:
    global total
    total += t


def captured(t: str) -> str:
    s = ""

    def get() -> str:
        return s

    s += t
    return get()


def maybe(s: str | None, t: str) -> str:
    s += t  # (TypeError where s is None)
    return s


b = Box()
b.add("x")
glob("y")
print(loop(3), plus("a", "b"), prepend("c", "d"), total, captured("e"), maybe("f", "g"), b.text)
