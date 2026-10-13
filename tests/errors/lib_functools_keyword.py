# error: _lru_cache_wrapper.__call__() got an unexpected keyword argument 'k'
from functools import lru_cache


@lru_cache(maxsize=4)
def scale(x: int, k: int) -> int:
    return x * k


print(scale(2, k=3))
