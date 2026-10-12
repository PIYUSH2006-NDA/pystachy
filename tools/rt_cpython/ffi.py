"""CPython's version of Pystachy's ffi module, so that a program that declares C functions with
@extern runs under CPython too (put this directory on PYTHONPATH): ctypes calls the same C
function, with the checks Pystachy's stubs make. A str goes in as its UTF-8 bytes (const char *,
NUL-terminated; a NUL in it is a ValueError) and a returned char * comes back as a str (NULL:
None, or a ValueError for -> str); C integers are range-checked (OverflowError), as Pystachy
checks them."""
import ctypes
import inspect as _inspect
import typing


class c_int(int):
    """C's int (32 bits) in an @extern function's signature; an int everywhere else"""


class c_uint(int):
    """C's unsigned int"""


class c_int64(int):
    """int64_t (long long)"""


class c_ssize_t(int):
    """ssize_t / Py_ssize_t"""


class c_uint64(int):
    """uint64_t"""


class c_size_t(int):
    """size_t"""


class c_buf(str):
    """a str's UTF-8 bytes (NULs allowed) for a C function that also takes their length"""


class c_void_p(int):
    """a pointer, as an int (NULL is 0)"""


_C = {c_int: ctypes.c_int, c_uint: ctypes.c_uint, c_int64: ctypes.c_int64, c_ssize_t: ctypes.c_ssize_t,
      c_uint64: ctypes.c_uint64, c_size_t: ctypes.c_size_t, c_void_p: ctypes.c_void_p,
      c_buf: ctypes.c_char_p, float: ctypes.c_double, str: ctypes.c_char_p, type(None): None, typing.Optional[str]: ctypes.c_char_p}


def _check(t, v):
    if t is str:
        if "\0" in v:
            raise ValueError("embedded null character")
        return v.encode("utf-8", "surrogatepass")
    if t is c_buf:
        return v.encode("utf-8", "surrogatepass")
    if t is float:
        return float(v)
    if t is c_int and not -2**31 <= v < 2**31:
        raise OverflowError("Python int too large to convert to C int")
    if t in (c_uint, c_uint64, c_size_t) and v < 0:
        raise OverflowError("can't convert negative int to unsigned")
    if t is c_uint and v >= 2**32:
        raise OverflowError("Python int too large to convert to C unsigned int")
    if t in (c_int64, c_ssize_t, c_uint64, c_size_t, c_void_p) and not -2**63 <= v < 2**63:
        raise OverflowError("int too big to convert")  # (Pystachy's int is 64-bit: checked where it was made)
    return v


def _s(b):
    return None if b is None else b.decode("utf-8", "surrogatepass")


def extern(lib, symbol=""):
    # the def's own signature binds a call's arguments (keywords and defaults as for any def), then
    # ctypes calls the C function, found when the def runs, as Pystachy finds it then
    def deco(f):
        hints = typing.get_type_hints(f)
        ret = hints.pop("return")
        sig = _inspect.signature(f)
        ts = [hints[p] for p in sig.parameters]
        for t in ts + [ret]:
            if t is int:
                raise TypeError(f"C function {f.__name__}() takes or returns int: say which C integer type")
        cf = getattr(ctypes.CDLL(lib or None), symbol or f.__name__)
        cf.argtypes = [_C[t] for t in ts]
        cf.restype = _C[ret]

        def call(*args, **kwargs):
            b = sig.bind(*args, **kwargs)
            b.apply_defaults()
            r = cf(*[_check(t, b.arguments[p]) for t, p in zip(ts, sig.parameters)])
            if ret is str and r is None:
                raise ValueError("a C function declared -> str returned NULL")
            if ret is c_void_p:
                return r or 0  # (ctypes gives None for NULL)
            if ret in (c_uint64, c_size_t) and r >= 2**63:
                raise OverflowError("C unsigned result is too large for int")
            return _s(r) if ret in (str, typing.Optional[str]) else r

        call.__name__ = f.__name__
        return call

    return deco


def string_at(addr, n):
    if n < 0:
        raise ValueError("ffi.string_at() takes a length >= 0")  # (ctypes reads up to a NUL)
    return _s(ctypes.string_at(addr, n))
