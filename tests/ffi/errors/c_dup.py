# error: tests/ffi/errors/c_dup.py:10: error: C function abs is declared again with other types: i64 @abs(i64) at line 6, signext i32 @abs(i32 signext) here
from ffi import extern, c_int, c_int64


@extern("", "abs")
def abs1(n: c_int64) -> c_int64: ...


@extern("", "abs")
def abs2(n: c_int) -> c_int: ...


print(abs1(-5), abs2(-5))
