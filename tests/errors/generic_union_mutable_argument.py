# error: expected dict[str,int] | list[float | int], got list[int]
from typing import Generic, TypeVar

T = TypeVar("T")


class Box(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value


ints = [1]
Box[list[int | float] | dict[str, int]](ints)
