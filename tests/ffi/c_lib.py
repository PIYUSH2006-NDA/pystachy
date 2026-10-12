# @ffi.extern finds a C function in its own library's handle, as ctypes does: a function of the same
# name in another library of the process (lli's libz and libzstd under pystachy run) does not stand in
from ffi import extern, c_uint


@extern("libpystachy-ffitest.so")
def zlibVersion() -> str: ...


@extern("libpystachy-ffitest.so")
def ZSTD_versionNumber() -> c_uint: ...


print(zlibVersion(), ZSTD_versionNumber())
