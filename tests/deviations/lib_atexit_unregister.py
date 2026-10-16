# atexit.unregister() raises NotImplementedError: Pystachy keeps each callback as a closure that
# calls the function, and no function compares equal to it, where CPython removes the callbacks
# of a function that compares equal to its argument (lib/compatibility.md)
import atexit


def f() -> None:
    print("f")


atexit.register(f)
try:
    atexit.unregister(f)
except NotImplementedError as e:
    print("NotImplementedError:", e)
