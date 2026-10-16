"""A generic class whose unary operator makes an empty object, leaving out a default argument."""
from typing import Generic, Iterable, Self, TypeVar

T = TypeVar("T")


class Bag(Generic[T]):
    def __init__(self, items: Iterable[T] = ()) -> None:
        self.items: list[T] = list(items)

    def __neg__(self) -> Self:
        result: Bag[T] = Bag()
        result.items = list(reversed(self.items))
        return result
