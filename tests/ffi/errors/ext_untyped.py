# error: tests/ffi/errors/ext_untyped.py:6: error: twice() cannot be called from CPython: it takes or returns an untyped value (an extension module's function takes int, float, bool or str and returns one or None); name it _twice to keep it private
from ffi import export


@export
def twice(n):
    return 2 * n
