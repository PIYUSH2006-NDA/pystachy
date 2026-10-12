# error: tests/ffi/errors/c_kwtwice.py:6: error: extern() got multiple values for argument 'lib'
from ffi import extern, c_int


@extern("", lib="libc.so.6")
def abs(n: c_int) -> c_int: ...


print(abs(-1))
