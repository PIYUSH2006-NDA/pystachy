# error: a call of scale(), which lru_cache() wraps, passes a keyword argument (k=), which is not supported yet: pass its arguments by position
from functools import lru_cache


@lru_cache(maxsize=4)
def scale(x: int, k: int) -> int:
    return x * k


print(scale(2, k=3))
