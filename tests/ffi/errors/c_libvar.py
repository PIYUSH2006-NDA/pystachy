# error: tests/ffi/errors/c_libvar.py:8: error: @extern takes the library ("" for the process's own) and an optional symbol name, as string literals
from ffi import extern, c_int

LIB = ""


@extern(LIB)
def abs(n: c_int) -> c_int: ...


print(abs(-1))
