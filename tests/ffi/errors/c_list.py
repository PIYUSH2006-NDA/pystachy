# error: tests/ffi/errors/c_list.py:6: error: C function f() takes list[int]: an @extern function takes a C integer type, float or str
from ffi import extern, c_int


@extern("")
def f(xs: list[int]) -> c_int: ...


print(f([1]))
