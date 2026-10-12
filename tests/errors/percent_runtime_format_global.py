# error: percent_runtime_format_global.py:9: error: % formatting with a format string computed at run time is not supported (only a string literal: "%d" % x)
# a module's format string, Final too, is a value read when the function runs, not a literal
from typing import Final

FMT: Final = "%d items"


def count(n: int) -> str:
    return FMT % n


print(count(3))
