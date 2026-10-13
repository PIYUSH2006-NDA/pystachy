# error: _lru_cache_wrapper.__call__() takes 2 positional arguments but 3 were given (its *args is a tuple[int])
from functools import cache


@cache
def inc(x: int) -> int:
    return x + 1


print(inc(1, 2))
