# error: tests/ffi/errors/c_kwnolib.py:6: error: extern() missing 1 required positional argument: 'lib'
from ffi import extern, c_int


@extern(symbol="abs")
def c_abs(n: c_int) -> c_int: ...


print(c_abs(-1))
