# error: dict keys must be int or str, or tuples of int, bool, str and str | None items, not tuple[Box] (specializing functools._lru_cache_wrapper(<function unbox
from functools import cache


class Box:
    def __init__(self, v: int) -> None:
        self.v = v


@cache
def unbox(b: Box) -> int:
    return b.v


print(unbox(Box(1)))
