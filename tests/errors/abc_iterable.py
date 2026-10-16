# error: abc_iterable.py:5: error: unsupported type annotation
from collections.abc import Iterable


def first(it: Iterable[int]) -> int:
    return 0
