# @ffi.extern: C functions of a library named by its soname, found in its handle when the def runs
from ffi import extern, c_int


@extern("libm.so.6")
def cbrt(x: float) -> float: ...


@extern("libm.so.6")
def hypot(x: float, y: float) -> float: ...


@extern("libm.so.6")
def ilogb(x: float) -> c_int: ...


@extern("libm.so.6", "nextafter")
def after(x: float, y: float) -> float: ...


@extern("libm.so.6")
def copysign(x: float, y: float) -> float: ...


@extern("libm.so.6")
def atan2(y: float, x: float) -> float: ...


@extern("libm.so.6")
def ldexp(x: float, e: c_int = 2) -> float: ...


# extern(lib, symbol="") takes its arguments by keyword too, as the twin's signature does; an empty
# symbol is the function's own name (the twin's symbol or f.__name__)
@extern(lib="libm.so.6")
def fmax(x: float, y: float) -> float: ...


@extern("libm.so.6", symbol="fmin")
def smaller(x: float, y: float) -> float: ...


@extern(symbol="", lib="libm.so.6")
def fdim(x: float, y: float) -> float: ...


@extern("libm.so.6", "")
def scalbn(x: float, n: c_int) -> float: ...


print(cbrt(27.0), hypot(3.0, 4.0), ilogb(1024.0), ilogb(0.75), after(1.0, 2.0) - 1.0)
# a float goes as it is: the sign of zero, infinities and NaN
print(copysign(1.0, -0.0), atan2(0.0, -0.0), atan2(-0.0, -1.0), cbrt(-0.0), cbrt(float("-inf")), cbrt(float("nan")))
# arguments bind as the def's own parameters do: by keyword, and with defaults
print(ldexp(1.5, 3), ldexp(x=1.5, e=4), ldexp(1.5), ldexp(e=1, x=0.25))
print(fmax(1.5, -2.0), smaller(1.5, -2.0), fdim(5.0, 3.0), fdim(3.0, 5.0), scalbn(0.75, 4))
