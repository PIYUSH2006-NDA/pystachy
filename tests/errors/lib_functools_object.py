# error: lru_cache() of unbox() is not supported: its parameter 'b' is Box
from functools import cache


class Box:
    def __init__(self, v: int) -> None:
        self.v = v


@cache
def unbox(b: Box) -> int:
    return b.v


print(unbox(Box(1)))
