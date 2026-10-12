# error: tests/ffi/errors/c_res.py:6: error: C function pys_len is reserved for Pystachy's runtime and extension modules
from ffi import extern, c_int64


@extern("")
def pys_len(x: c_int64) -> c_int64: ...


print(pys_len(3))
