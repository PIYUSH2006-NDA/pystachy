# error: _lru_cache_wrapper.__call__() takes 3 positional arguments but 2 were given (its *args is a tuple[int,int])
from functools import lru_cache


@lru_cache(maxsize=4)
def scale(x: int, k: int = 2) -> int:
    return x * k


print(scale(2))
