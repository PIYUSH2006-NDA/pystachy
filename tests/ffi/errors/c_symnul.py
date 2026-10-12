# error: tests/ffi/errors/c_symnul.py:6: error: @extern's symbol has a NUL character in it: C would look up only the name before it
from ffi import extern


@extern("libm.so.6", symbol="cbrt\0f")
def cbrt(x: float) -> float: ...


print(cbrt(8.0))
