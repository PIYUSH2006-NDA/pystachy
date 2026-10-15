# error: 'yield' is not supported (there are no generator functions): __reversed__ can return iter(xs) of a list xs of the items
from typing import Iterator


class Seq:
    def __init__(self) -> None:
        self.xs = [1, 2]

    def __reversed__(self) -> Iterator[int]:
        yield self.xs[1]
        yield self.xs[0]


print(list(reversed(Seq())))
