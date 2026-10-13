# error: tests/ffi/errors/ext_pub.py:10: error: g() is public in extension module 'ext_pub' but not @export: CPython would not see it; export it or name it _g
from ffi import export


@export
def f(n: int) -> int:
    return n


def g(n: int) -> int:
    return n
