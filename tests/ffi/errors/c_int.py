# error: tests/ffi/errors/c_int.py:6: error: C function atoi() returns int: say which C integer type (ffi.c_int, c_uint, c_int64, c_uint64, c_size_t, c_ssize_t or c_void_p)
from ffi import extern


@extern("")
def atoi(s: str) -> int: ...


print(atoi("-5"))
