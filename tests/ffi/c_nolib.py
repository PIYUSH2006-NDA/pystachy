# @ffi.extern looks the library up when the def runs, as ctypes.CDLL does: a missing one raises
# OSError there (dlerror's text)
from ffi import extern

print("before")


@extern("libpystachy-no-such-library.so.9")
def nothing() -> None: ...


print("not reached")
