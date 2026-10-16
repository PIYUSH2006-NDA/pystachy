"""allow programmer to define multiple exit functions to be executed
upon normal program termination.

Two public functions, register and unregister, are defined.
"""
# atexit for Pystachy: CPython builds atexit into its interpreter (Modules/atexitmodule.c), so
# Pystachy loads this port of it for import atexit (specs.STANDINS). The callbacks are Callables,
# each a closure that calls a registered function with its arguments. The program's main
# function gives the runtime the address of _hook (Gen.lower_module), and pys_finish calls it at the
# end of the program, as CPython's finalization calls the callbacks: after the program's code,
# also where it ends with sys.exit() or an exception that nothing catches, whose message comes
# first. The docstrings are CPython 3.13.16's.
import sys
from typing import Callable

__all__ = ["register", "unregister", "_clear", "_run_exitfuncs", "_ncallbacks"]

_callbacks: list[Callable[[], None]] = []


def register(func, /, *args, **kwargs):
    """Register a function to be executed upon normal program termination

    func - function to be called at exit
    args - optional arguments to pass to func
    kwargs - optional keyword arguments to pass to func

    func is returned to facilitate usage as a decorator."""
    def call() -> None:
        func(*args, **kwargs)
    _callbacks.append(call)
    return func


def unregister(func, /) -> None:
    """Unregister an exit function which was previously registered using
atexit.register

    func - function to be unregistered"""
    raise NotImplementedError("atexit.unregister() is not supported: Pystachy keeps the callbacks as closures, which no function compares equal to")


def _clear() -> None:
    """Clear the list of previously registered exit functions."""
    _callbacks.clear()


def _run_exitfuncs() -> None:
    """Run all registered exit functions.

If a callback raises an exception, it is logged with sys.unraisablehook."""
    # the last registered first, as CPython's, which leaves out those registered meanwhile and
    # stops where a callback clears the list; an exception is reported and the next one runs
    i = len(_callbacks) - 1
    while i >= 0:
        if i < len(_callbacks):
            cb = _callbacks[i]
            try:
                cb()
            except BaseException as e:
                # (CPython's report names the function and shows the traceback; this shows the
                # exception's last line, as Pystachy shows an exception that nothing catches)
                m = str(e)
                print("Exception ignored in atexit callback:", file=sys.stderr)
                print(type(e).__name__ + (": " + m if m != "" else ""), file=sys.stderr)
        i -= 1
    _callbacks.clear()


def _ncallbacks() -> int:
    """Return the number of registered exit functions."""
    return len(_callbacks)


# (what the runtime calls at the end of the program: Gen.lower_module)
_hook: Callable[[], None] = _run_exitfuncs
