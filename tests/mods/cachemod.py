"""lru_cache() in an imported module (lib_functools_mod.py): the decorators run when the module is
imported, through `functools.lru_cache` as an attribute of the module too."""

import functools
from functools import cache

CALLS: list[str] = []


@functools.lru_cache(maxsize=2)
def label(n: int, unit: str) -> str:
    CALLS.append(f"label {n} {unit}")
    return f"{n} {unit}{'s' if n != 1 else ''}"


@cache
def depth(n: int) -> int:
    CALLS.append(f"depth {n}")
    return 0 if n == 0 else 1 + depth(n - 1)

