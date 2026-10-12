# error: tests/ffi/errors/c_noarg.py:6: error: @extern takes the library ("" for the process's own) and an optional symbol name, as string literals
from ffi import extern, c_int


@extern
def abs(n: c_int) -> c_int: ...


print(abs(-1))
