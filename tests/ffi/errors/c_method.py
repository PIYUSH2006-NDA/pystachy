# error: tests/ffi/errors/c_method.py:7: error: unsupported decorator @extern
from ffi import extern, c_int


class C:
    @extern("")
    def abs(self, n: c_int) -> c_int: ...


print(C().abs(-1))
