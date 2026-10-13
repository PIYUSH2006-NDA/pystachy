# error: tests/ffi/errors/ext_cls.py:5: error: class TooBig is public in extension module 'ext_cls', but classes cannot cross to CPython yet: name it _TooBig
from ffi import export


class TooBig(Exception):
    pass


@export
def f(n: int) -> int:
    if n > 3:
        raise TooBig("big")
    return n
