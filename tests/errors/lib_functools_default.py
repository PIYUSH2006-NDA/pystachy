# error: a call of scale(), which lru_cache() wraps, leaves out an argument that has a default value ('k'), which is not supported yet: pass every argument
from functools import lru_cache


@lru_cache(maxsize=4)
def scale(x: int, k: int = 2) -> int:
    return x * k


print(scale(2))
