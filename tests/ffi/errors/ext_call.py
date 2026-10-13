# error: tests/ffi/errors/ext_call.py:7: error: fib() is @export, so Pystachy code may not call it (under CPython each call goes through the export's checks and conversions): call a private function that both use
from ffi import export


@export
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)
