# error: tests/ffi/errors/c_libnul.py:6: error: @extern's library has a NUL character in it: ctypes raises ValueError: embedded null byte
from ffi import extern


@extern("libm.so.6\0junk")
def cbrt(x: float) -> float: ...


print(cbrt(8.0))
