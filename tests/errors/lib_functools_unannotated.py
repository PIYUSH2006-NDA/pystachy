# error: lru_cache() of double() needs its parameters annotated: Pystachy types the cache's keys with them (parameter 'x')
from functools import lru_cache


@lru_cache(maxsize=4)
def double(x) -> int:
    return x * 2


print(double(1))
