# Classes that Pystachy leaves uncompiled whose bodies run without raising
# (tests/deftime_class_raises.py)
from typing import Iterable

NAMES = ["x"]
N = 0


class Computed:  # (operations that raise on other values)
    r: float = 1 / 3
    first: str = NAMES[0]
    n: int = int("5") // 2
    top = max(NAMES)
    data = {"a": 1, "b": "x", "c": int("3")}
    xs: Iterable[int]


class Skipped:  # (operations that CPython does not run)
    guarded = 1 // N if N else 0
    either = N and 1 // N
    if N:
        half = 1 // N
    xs: Iterable[int]


class Tenth:  # (Pystachy's int ** negative int is a ValueError: docs/language.md, Deviations)
    tenth = 10**-1
    xs: Iterable[int]


class Mask:  # (Pystachy's int is 64-bit)
    mask = (1 << 64) - 1
    xs: Iterable[int]


class Mixed:  # (which Pystachy rejects)
    pick = max(1, 2.5)
    xs: Iterable[int]


def after() -> str:
    return "calm: imported"
