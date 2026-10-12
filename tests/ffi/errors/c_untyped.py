# error: tests/ffi/errors/c_untyped.py:6: error: C function abs() (@extern) needs an annotation on every parameter, and no *args
from ffi import extern, c_int


@extern("")
def abs(n) -> c_int: ...


print(abs(-1))
