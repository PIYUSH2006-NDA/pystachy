"""Dataclasses deriving from a module's dataclass, and classes with property setters, that
Pystachy cannot compile, unused: a module that defines them still compiles."""
from dataclasses import dataclass


@dataclass
class Point:
    x: int
    name: str = "p"

    @staticmethod
    def origin() -> int:
        return 0

    def norm(self) -> int:
        return abs(self.x)


@dataclass
class Retyped(Point):
    x: str = "r"  # (a field declared again with another type)


@dataclass
class Below(Retyped):  # (and a class deriving from that one)
    z: int = 0


@dataclass
class Constant(Point):
    K = 3  # (a class attribute without an annotation)
    y: int = 0


@dataclass
class Static(Point):
    def origin(self) -> int:  # (a static method overridden by an instance method)
        return 1


@dataclass
class Shadow(Point):
    norm: int = 0  # (a field named as a method of the base)


@dataclass
class Labeled(Point):
    label: str = "é"


class Odd:
    def __init__(self) -> None:
        self._v = 0

    @property
    def v(self) -> int:
        return self._v

    @v.setter
    def set_v(self, x: int) -> None:  # (a property set_v with v's getter)
        self._v = x

    @v.setter
    def v(self, x: int) -> None:
        self._v = x

    @v.setter
    def v(self, x: int) -> None:  # (a second setter)
        self._v = x + 1
