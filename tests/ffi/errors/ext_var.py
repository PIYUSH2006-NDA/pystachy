# error: tests/ffi/errors/ext_var.py:4: error: variable 'limit' is public in extension module 'ext_var', but CPython would not see it (variables cannot cross yet): name it _limit
from ffi import export

limit = 10


@export
def f(n: int) -> int:
    return min(n, limit)
