# error: lru_cache() of double() needs its return annotated: Pystachy types the cache's results with it
from functools import cache


@cache
def double(x: int):
    return x * 2


print(double(1))
