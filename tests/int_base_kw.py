# int(x, base=b) is int(x, b): CPython's values and errors, also for a base that may be None
def maybe(n: int, none: bool) -> int | None:
    return None if none else n


def text(s: str, none: bool) -> str | None:
    return None if none else s


print(int("ff", base=16), int("FF", 16), int("0x1f", base=0), int("0b101", base=0), int("z", base=36))
print(int(" 12 ", base=3), int("-0o17", base=8), int("1_000", base=10), int("7", base=maybe(8, False)))
for s, b in [("9", 8), ("12", 37), ("12", -1), ("12", 1), ("", 10), ("0x", 16)]:
    try:
        print(int(s, base=b))
    except ValueError as e:
        print("ValueError:", e)
try:
    print(int("5", base=maybe(10, True)))
except TypeError as e:
    print("TypeError:", e)
try:
    print(int("5", maybe(10, True)))
except TypeError as e:
    print("TypeError:", e)
try:
    print(int(text("5", True), base=10))
except TypeError as e:
    print("TypeError:", e)
print(int(text("101", False), base=2))
