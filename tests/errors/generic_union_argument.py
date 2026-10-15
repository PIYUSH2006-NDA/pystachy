# error: expected float | int, got str
from typing import Generic, TypeVar

T = TypeVar("T")


class Pair(Generic[T]):
    def __init__(self, left: T, right: T) -> None:
        self.left = left
        self.right = right


Pair[int | float](1, "bad")
