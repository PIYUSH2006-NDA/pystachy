# error: TypeError: Expected first argument to be an integer, a callable, or None
from functools import lru_cache


@lru_cache("big")
def scale(x: int) -> int:
    return x * 2


print(scale(2))
