/* tests/ffi/c_lib.py's library (tests/ffi/run.sh builds it as libpystachy-ffitest.so): functions named
   as functions of libraries that lli's process has loaded already (libz's, libzstd's), which an
   @extern of this library must still find here, as ctypes does */
const char *zlibVersion(void) { return "ffitest"; }
unsigned ZSTD_versionNumber(void) { return 42; }
