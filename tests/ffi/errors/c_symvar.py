# error: tests/ffi/errors/c_symvar.py:8: error: @extern takes the library ("" for the process's own) and an optional symbol name, as string literals
from ffi import extern, c_int

NAME = "abs"


@extern("", symbol=NAME)
def c_abs(n: c_int) -> c_int: ...


print(c_abs(-1))
