# error: tests/ffi/errors/ext_ret.py:6: error: evens() cannot be called from CPython: it takes or returns list[int] (an extension module's function takes int, float, bool or str and returns one or None); name it _evens to keep it private
from ffi import export


@export
def evens(n: int) -> list[int]:
    return [2 * i for i in range(n)]
