# error: lru_cache() of total() is not supported: it takes *args or **kwargs, and a cache's keys have one type
from functools import cache


@cache
def total(*xs: int) -> int:
    return sum(xs)


print(total(1, 2))
