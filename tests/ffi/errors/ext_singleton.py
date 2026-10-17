# error: tests/ffi/errors/ext_singleton.py:8: error: variable 'Mode' is public in extension module 'ext_singleton', but CPython would not see it (variables cannot cross yet): name it _Mode
from ffi import export


class Mode:
    def __repr__(self) -> str:
        return "<mode>"
Mode = Mode()


@export
def f(n: int) -> int:
    return n
