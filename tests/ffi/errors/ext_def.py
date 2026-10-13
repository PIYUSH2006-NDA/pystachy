# error: tests/ffi/errors/ext_def.py:6: error: f() is @export: its parameters are positional, with no default values and no *args (as CPython calls it)
from ffi import export


@export
def f(n: int, k: int = 2) -> int:
    return n * k
