# @ffi.extern: C functions of the C library (""), with each C integer's width named
from ffi import extern, string_at, c_int, c_int64, c_uint64, c_size_t, c_void_p, c_buf


@extern("")
def strdup(s: str) -> c_void_p: ...


@extern("")
def free(p: c_void_p) -> None: ...


@extern("")
def strlen(s: str) -> c_size_t: ...


@extern("")
def strnlen(s: c_buf, n: c_size_t) -> c_size_t: ...


@extern("")
def strcmp(a: str, b: str) -> c_int: ...


@extern("")
def atoi(s: str) -> c_int: ...


@extern("")
def abs(n: c_int) -> c_int: ...


@extern("")
def labs(n: c_int64) -> c_int64: ...


@extern("", "strtoull")
def to_u64(s: str, end: c_void_p, base: c_int) -> c_uint64: ...


@extern("")
def getenv(name: str) -> str | None: ...


@extern("")
def memchr(s: str, c: c_int, n: c_size_t) -> c_void_p: ...  # (the runtime's own, with the same types)


p = strdup("Wikipedia")
s = string_at(p, strlen("Wikipedia"))
free(p)
print(s, strlen(s), strnlen("a\0b", 3), strcmp("a", "b"), strcmp("b", "a"), atoi("-5"), abs(-7), labs(-2**62))
print(to_u64("9223372036854775807", 0, 10), getenv("PYSTACHY_FFI_TEST_UNSET"), memchr("abc", 98, 3) != 0, "abc".find("b"))
for k in range(6):
    try:
        if k == 0:
            print(abs(2**31))
        elif k == 1:
            print(strlen("a\0b"))
        elif k == 2:
            print(to_u64("18446744073709551615", 0, 10))
        elif k == 3:
            print(strnlen("ab", -1))
        elif k == 4:
            print(string_at(0, -1))
        else:
            print(abs(-2**31 - 1))
    except (OverflowError, ValueError) as e:
        print(type(e).__name__, e)
