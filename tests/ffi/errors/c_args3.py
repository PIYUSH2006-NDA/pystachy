# error: tests/ffi/errors/c_args3.py:6: error: extern() takes from 1 to 2 positional arguments but 3 were given
from ffi import extern, c_int


@extern("", "abs", "libc.so.6")
def c_abs(n: c_int) -> c_int: ...


print(c_abs(-1))
