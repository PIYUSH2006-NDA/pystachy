# A method's first parameter shadows a module-level function, class or import of its name: a
# field __init__ assigns from self(...) is typed by its class's __call__, and from self.m(...) by
# its method m, not by the function, class or import of that name.
import os
from os import fspath


def self() -> str:
    return "the function self"


class Fact:
    def __init__(self, n: int) -> None:
        self.k = n
        self.v = self(1)  # (Fact.__call__'s int, not self()'s str)

    def __call__(self, d: int) -> int:
        return self.k + d


class Box:
    def __init__(self) -> None:
        self.v = 1

    @staticmethod
    def size(n: int) -> str:
        return "Box.size " + str(n)


class Pair:
    def __init__(Box, n: int) -> None:
        Box.k = n
        Box.big = Box(2)  # (Pair.__call__'s bool, not a new Box)
        Box.area = Box.size(3)  # (Pair.size's int, not Box.size's str)

    def __call__(Box, d: int) -> bool:
        return Box.k > d

    def size(Box, d: int) -> int:
        return Box.k * d


class Path:
    def __init__(os, n: int) -> None:
        os.k = n
        os.a = os.fspath("ab")  # (Path.fspath's int, not os.fspath's str)

    def fspath(os, s: str) -> int:
        return os.k + len(s)


class Len:
    def __init__(fspath, n: int) -> None:
        fspath.k = n
        fspath.a = fspath("abc")  # (Len.__call__'s int)

    def __call__(fspath, s: str) -> int:
        return fspath.k * len(s)


f = Fact(41)
print(f.v, f(2), self())
p = Pair(5)
print(p.big, p.area, p(9), p.size(2))
print(Box().v, Box.size(4))
print(Path(3).a, Len(4).a, os.fspath("p"), fspath("q"))
