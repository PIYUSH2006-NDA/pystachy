# := and starred targets in an imported module: its globals, a function's global and nonlocal
# names, a lambda's local, and a name that shadows a builtin
items = [4, 8, 15]
if (count := len(items)) > 2:
    big = [h for i in items if (h := i // 2) > 2]
else:
    big = []
level = 0
head, *rest = [(1, "a"), (2, "b")]
input = 3
print("module", (input := 4), count, big, h)


def bump() -> int:
    global level
    if (level := level + 5) > 3:
        return level
    return -1


def twice() -> str:
    seen = ""

    def inner() -> None:
        nonlocal seen
        if (seen := seen + "x") == "xx":
            print("twice")

    inner()
    inner()
    return seen


def scan(xs: list[str]) -> list[str]:
    return [m for x in xs if (m := x.strip())]


square_sum = lambda v: (sq := v * v) + sq
