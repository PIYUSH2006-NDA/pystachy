# error: tests/ffi/errors/c_rt.py:6: error: C function memchr is declared as ptr(ptr, i64, i64), but Pystachy's runtime calls it as ptr(ptr, i32, i64)
from ffi import extern, c_int, c_int64, c_void_p


@extern("")
def memchr(p: str, c: c_int64, n: c_int64) -> c_void_p: ...


print(memchr("abc", 98, 3) != 0, "abc".find("b"))
