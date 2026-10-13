# error: lru_cache() of half() is not supported: its parameter 'x' is float, and the cache's keys hold ints, bools, strs, str | None and tuples of those
from functools import lru_cache


@lru_cache(maxsize=4)
def half(x: float) -> float:
    return x / 2


print(half(1.0))
