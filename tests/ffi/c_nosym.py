# @ffi.extern looks the symbol up when the def runs: a missing one raises AttributeError there
from ffi import extern

print("before")


@extern("libm.so.6")
def no_such_function_here(x: float) -> float: ...


print("not reached")
