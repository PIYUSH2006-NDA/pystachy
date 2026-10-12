# error: tests/ffi/errors/c_kwunknown.py:6: error: extern() got an unexpected keyword argument 'name'
from ffi import extern, c_int


@extern("", name="abs")
def c_abs(n: c_int) -> c_int: ...


print(c_abs(-1))
