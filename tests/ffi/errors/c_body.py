# error: tests/ffi/errors/c_body.py:6: error: f() is a C function (@extern): its body must be ...
from ffi import extern, c_int


@extern("")
def f(n: c_int) -> c_int:
    return n


print(f(1))
