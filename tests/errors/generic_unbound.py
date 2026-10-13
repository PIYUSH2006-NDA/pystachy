# error: Stack() does not bind its type variable 'T': Pystachy binds a generic class's type variables from the arguments of the call that makes an object (C[int]() is not supported), and no argument's type gives it
from typing import Generic, TypeVar

T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self, top: T | None) -> None:
        self.items: list[T] = []
        if top is not None:
            self.items.append(top)


print(Stack(None).items)
