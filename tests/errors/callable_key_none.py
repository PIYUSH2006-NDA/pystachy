# error: callable_key_none.py:10: error: a key that may be None (Callable[[int], int] | None) is not supported (the key of sorted()): test it with 'is not None' first
from typing import Callable


def neg(x: int) -> int:
    return -x


k: Callable[[int], int] | None = neg
print(sorted([3, 1, 2], key=k))
